"""
Supabase/Postgres-backed data store for the mutation seam.
Drop-in replacement for MemoryStore — provides the same dict-like
interface but persists all state to the `seam` schema in Postgres.

Packet: UI-001e — Bounded persistence migration.
"""
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Tuple

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Connection factory
# ---------------------------------------------------------------------------

_DEFAULT_DSN = "host=127.0.0.1 port=5432 dbname=apex_pm_stage user=apex_pm_stage_user"


def _get_dsn() -> str:
    """Return Postgres DSN from env or default."""
    return os.getenv("SEAM_DATABASE_URL", _DEFAULT_DSN)


def _get_conn():
    """Create a new psycopg2 connection with autocommit."""
    conn = psycopg2.connect(_get_dsn())
    conn.autocommit = True
    psycopg2.extras.register_default_jsonb(conn)
    return conn


# Singleton connection — reused across the process lifetime.
_conn: Optional[Any] = None


def _conn_get():
    """Lazy singleton connection."""
    global _conn
    if _conn is None or _conn.closed:
        _conn = _get_conn()
    return _conn


# ---------------------------------------------------------------------------
# PgDict — dict-like proxy backed by a Postgres table
# ---------------------------------------------------------------------------

class PgDict:
    """
    A dict-like object backed by a single table in the `seam` schema.
    Supports __getitem__, __setitem__, __contains__, __delitem__,
    keys(), values(), items(), get(), pop(), and __len__.

    Each table must have a TEXT primary-key column (default 'id').

    Two storage shapes are supported:

    1. Wide-table shape (default, payload_col=None): the table has typed
       columns for well-known keys (created_at, updated_at, etc.) plus a
       JSONB `data` column that catches everything else as overflow. Used
       by apparatus, tasks, workpackages, projects, etc.

    2. Narrow-table shape (payload_col="<colname>"): the table has a PK
       column, an optional created_at, and a single named JSONB column
       (the payload column) that stores the entire value dict as opaque
       JSON. Used by seam.idempotency_keys, whose governed schema is
       (key, response JSONB, created_at) — a write-once cache where the
       cached response is stored verbatim, not split across typed columns.
       PM-SEAM-DB-HYGIENE-001 added this shape so PgDict can correctly
       back narrow seam tables without inventing columns they don't own.
    """

    def __init__(self, table: str, pk_col: str = "id",
                 payload_col: Optional[str] = None):
        self._table = f"seam.{table}"
        self._pk = pk_col
        self._payload_col = payload_col

    # -- helpers --

    def _cur(self):
        return _conn_get().cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _row_to_dict(self, row: dict) -> dict:
        """Convert a Postgres row (RealDictRow) to a plain dict,
        merging the JSONB `data` overflow column into top-level keys
        and converting datetimes to ISO strings.

        When payload_col is declared, the payload column IS the returned
        dict — other columns (PK, created_at) are storage metadata, not
        application data, and are omitted. This matches the in-memory
        store semantics where `store[key] = value; assert store[key] == value`.
        """
        # PM-SEAM-DB-HYGIENE-001: narrow-table / payload-column shape.
        if self._payload_col and self._payload_col in row:
            v = row[self._payload_col]
            return dict(v) if isinstance(v, dict) else {}

        out = {}
        for k, v in row.items():
            if k == "data":
                if isinstance(v, dict):
                    out.update(v)
            elif isinstance(v, datetime):
                out[k] = v.isoformat()
            else:
                out[k] = v
        return out

    def _split_for_write(self, value: dict, columns: List[str]) -> Tuple[dict, dict]:
        """Split a value dict into known-column values and overflow JSONB."""
        known = {}
        overflow = {}
        for k, v in value.items():
            if k in columns:
                known[k] = v
            elif k != "data":  # don't nest data inside data
                overflow[k] = v
        return known, overflow

    def _table_columns(self) -> List[str]:
        """Return column names for this table (cached per table on first call)."""
        if not hasattr(self, "_cols_cache"):
            schema, tbl = self._table.split(".")
            with self._cur() as cur:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = %s AND table_name = %s",
                    (schema, tbl),
                )
                self._cols_cache = [r["column_name"] for r in cur.fetchall()]
        return self._cols_cache

    # -- dict interface --

    def __contains__(self, key: str) -> bool:
        with self._cur() as cur:
            cur.execute(f"SELECT 1 FROM {self._table} WHERE {self._pk} = %s", (key,))
            return cur.fetchone() is not None

    def __getitem__(self, key: str) -> dict:
        with self._cur() as cur:
            cur.execute(f"SELECT * FROM {self._table} WHERE {self._pk} = %s", (key,))
            row = cur.fetchone()
        if row is None:
            raise KeyError(key)
        return self._row_to_dict(dict(row))

    def __setitem__(self, key: str, value: dict) -> None:
        cols = self._table_columns()

        # PM-SEAM-DB-HYGIENE-001: select storage strategy for the dict.
        # Priority:
        #   (1) payload_col declared AND present in cols → serialize the
        #       entire value into that single JSONB column. Used by
        #       narrow tables like seam.idempotency_keys whose governed
        #       schema is (pk, <payload JSONB>, created_at).
        #   (2) otherwise split into known/overflow; write overflow to
        #       the `data` JSONB column. Used by the wide seam.*
        #       tables (apparatus, tasks, workpackages, etc.).
        #   (3) if a narrow table has neither a payload_col nor a `data`
        #       column, raise — silently dropping keys would mask bugs.
        if self._payload_col and self._payload_col in cols:
            known: Dict[str, Any] = {self._payload_col: json.dumps(value)}
        else:
            known, overflow = self._split_for_write(value, cols)
            if "data" in cols:
                known["data"] = json.dumps(overflow)
            elif overflow:
                raise KeyError(
                    f"PgDict({self._table}): value contains keys not in schema "
                    f"and table has no `data` overflow column: {sorted(overflow)}"
                )

        # Ensure PK is set
        known[self._pk] = key

        # Ensure timestamps — but ONLY for tables that actually own them.
        # seam.idempotency_keys has created_at (DEFAULT now()) but no
        # updated_at by design (write-once cache). Every other seam.*
        # table carries the (created_at, updated_at) pair.
        now = datetime.now(timezone.utc)
        if "created_at" in cols:
            if "created_at" not in known or known["created_at"] is None:
                known["created_at"] = now
            elif isinstance(known["created_at"], str):
                pass  # keep string as-is; Postgres will cast
        if "updated_at" in cols:
            if "updated_at" not in known:
                known["updated_at"] = now
            elif isinstance(known["updated_at"], str):
                pass

        # Build UPSERT
        col_names = [c for c in known.keys()]
        placeholders = ["%s"] * len(col_names)
        updates = ", ".join(
            f"{c} = EXCLUDED.{c}" for c in col_names if c != self._pk
        )
        sql = (
            f"INSERT INTO {self._table} ({', '.join(col_names)}) "
            f"VALUES ({', '.join(placeholders)}) "
            f"ON CONFLICT ({self._pk}) DO UPDATE SET {updates}"
        )
        vals = [known[c] for c in col_names]
        with self._cur() as cur:
            cur.execute(sql, vals)

    def __delitem__(self, key: str) -> None:
        with self._cur() as cur:
            cur.execute(f"DELETE FROM {self._table} WHERE {self._pk} = %s", (key,))
            if cur.rowcount == 0:
                raise KeyError(key)

    def __len__(self) -> int:
        with self._cur() as cur:
            cur.execute(f"SELECT count(*) FROM {self._table}")
            return cur.fetchone()["count"]

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

    def get(self, key: str, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self) -> List[str]:
        with self._cur() as cur:
            cur.execute(f"SELECT {self._pk} FROM {self._table}")
            return [r[self._pk] for r in cur.fetchall()]

    def values(self) -> List[dict]:
        with self._cur() as cur:
            cur.execute(f"SELECT * FROM {self._table}")
            return [self._row_to_dict(dict(r)) for r in cur.fetchall()]

    def items(self) -> List[Tuple[str, dict]]:
        with self._cur() as cur:
            cur.execute(f"SELECT * FROM {self._table}")
            rows = cur.fetchall()
        return [(dict(r)[self._pk], self._row_to_dict(dict(r))) for r in rows]

    def pop(self, key: str, *args):
        try:
            val = self[key]
            del self[key]
            return val
        except KeyError:
            if args:
                return args[0]
            raise

    def update(self, other: dict) -> None:
        for k, v in other.items():
            self[k] = v

    def clear(self) -> None:
        with self._cur() as cur:
            cur.execute(f"DELETE FROM {self._table}")
        # Bust column cache
        if hasattr(self, "_cols_cache"):
            del self._cols_cache


# ---------------------------------------------------------------------------
# PgList — list-like proxy for the audit_log table
# ---------------------------------------------------------------------------

class PgList:
    """List-like proxy for seam.audit_log."""

    _table = "seam.audit_log"

    def _cur(self):
        return _conn_get().cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _row_to_dict(self, row: dict) -> dict:
        out = {}
        for k, v in row.items():
            if k == "from_state" or k == "to_state":
                out[k] = v if isinstance(v, dict) else {}
            elif isinstance(v, datetime):
                out[k] = v.isoformat()
            else:
                out[k] = v
        return out

    def append(self, event: dict) -> None:
        """Insert an audit event."""
        col_map = {
            "id": event.get("id"),
            "mutation_id": event.get("mutation_id"),
            "actor_id": event.get("actor_id"),
            "actor_role": event.get("actor_role"),
            "entity_type": event.get("entity_type"),
            "entity_id": event.get("entity_id"),
            "action_type": event.get("action_type"),
            "from_state": json.dumps(event.get("from_state", {})),
            "to_state": json.dumps(event.get("to_state", {})),
            "reason": event.get("reason"),
            "timestamp": event.get("server_timestamp") or datetime.now(timezone.utc),
        }
        cols = list(col_map.keys())
        placeholders = ["%s"] * len(cols)
        sql = f"INSERT INTO {self._table} ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
        with self._cur() as cur:
            cur.execute(sql, [col_map[c] for c in cols])

    def __iter__(self):
        with self._cur() as cur:
            cur.execute(f"SELECT * FROM {self._table} ORDER BY timestamp")
            return iter([self._row_to_dict(dict(r)) for r in cur.fetchall()])

    def __len__(self) -> int:
        with self._cur() as cur:
            cur.execute(f"SELECT count(*) FROM {self._table}")
            return cur.fetchone()["count"]

    def __getitem__(self, idx):
        items = list(self)
        return items[idx]

    def clear(self) -> None:
        with self._cur() as cur:
            cur.execute(f"DELETE FROM {self._table}")


# ---------------------------------------------------------------------------
# SupabaseStore — drop-in replacement for MemoryStore
# ---------------------------------------------------------------------------

class SupabaseStore:
    """Postgres-backed store with the same interface as MemoryStore."""

    def __init__(self):
        self.apparatus = PgDict("apparatus")
        self.checklist_items = PgDict("checklist_items")
        self.hours = PgDict("hours")
        self.issues = PgDict("issues")
        self.assignments = PgDict("assignments")
        self.tasks = PgDict("tasks")
        self.workpackages = PgDict("workpackages")
        self.snapshots = PgDict("snapshots")
        self.idempotency_keys = PgDict("idempotency_keys", pk_col="key", payload_col="response")
        self.audit_log = PgList()
        self.projects = PgDict("projects")

    def seed_demo_data(self):
        """Populate the store with demo data (same data as MemoryStore)."""
        now = datetime.now(timezone.utc).isoformat()

        # Project
        self.projects["proj-001"] = {
            "id": "proj-001",
            "name": "Stack Data Center",
            "created_at": now,
            "updated_at": now,
        }

        # Workpackages
        self.workpackages["wp-001"] = {
            "id": "wp-001",
            "project_id": "proj-001",
            "name": "Electrical Systems",
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }
        self.workpackages["wp-002"] = {
            "id": "wp-002",
            "project_id": "proj-001",
            "name": "Safety & Controls",
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }

        # Tasks
        tasks_data = [
            ("task-001", "wp-001", "Ground Testing", 1.0),
            ("task-002", "wp-001", "Insulation Testing", 0.8),
            ("task-003", "wp-002", "Arc Flash Analysis", 0.6),
            ("task-004", "wp-002", "Controls Documentation", 0.4),
        ]
        for task_id, wp_id, name, priority in tasks_data:
            self.tasks[task_id] = {
                "id": task_id,
                "workpackage_id": wp_id,
                "project_id": "proj-001",
                "name": name,
                "status": "not_started",
                "priority": priority,
                "assigned_to": None,
                "created_at": now,
                "updated_at": now,
            }

        # Apparatus
        apparatus_data = [
            ("app-001", "task-001", "Main Breaker 480V", "ATS", "not_started", None),
            ("app-002", "task-001", "Distribution Panel", "MTS", "ready", "tech-001"),
            ("app-003", "task-002", "Cable Assembly A", "ATS", "active", "tech-001"),
            ("app-004", "task-002", "Cable Assembly B", "ATS", "not_started", None),
            ("app-005", "task-003", "Control Transformer", "MTS", "not_started", None),
            ("app-006", "task-004", "Safety Switch", "MTS", "ready", None),
        ]
        for app_id, task_id, name, standard, status, assigned_to in apparatus_data:
            self.apparatus[app_id] = {
                "id": app_id,
                "task_id": task_id,
                "project_id": "proj-001",
                "name": name,
                "neta_standard": standard,
                "status": status,
                "assigned_to": assigned_to,
                "created_at": now,
                "updated_at": now,
            }

        # Checklist items
        checklist_names = ["Visual inspection", "Continuity test"]
        item_counter = 1
        for app_id in ["app-001", "app-002", "app-003", "app-004", "app-005", "app-006"]:
            app = self.apparatus[app_id]
            for cname in checklist_names:
                item_id = f"item-{item_counter:03d}"
                self.checklist_items[item_id] = {
                    "id": item_id,
                    "apparatus_id": app_id,
                    "task_id": app["task_id"],
                    "project_id": "proj-001",
                    "name": cname,
                    "completed": False,
                    "created_at": now,
                    "updated_at": now,
                }
                item_counter += 1

        # Assignments
        self.assignments["assign-001"] = {
            "id": "assign-001",
            "apparatus_id": "app-002",
            "task_id": "task-001",
            "project_id": "proj-001",
            "assigned_to": "tech-001",
            "assigned_by": "lead-001",
            "created_at": now,
            "updated_at": now,
        }
        self.assignments["assign-002"] = {
            "id": "assign-002",
            "apparatus_id": "app-003",
            "task_id": "task-002",
            "project_id": "proj-001",
            "assigned_to": "tech-001",
            "assigned_by": "lead-001",
            "created_at": now,
            "updated_at": now,
        }

        # Snapshots
        self.snapshots["snap-001"] = {
            "id": "snap-001",
            "workpackage_id": "wp-001",
            "project_id": "proj-001",
            "period_start": "2026-04-01",
            "period_end": "2026-04-15",
            "status": "submitted",
            "percent_complete": 45,
            "hours_reported": 120,
            "submitted_by": "lead-001",
            "created_at": now,
            "updated_at": now,
        }
        self.snapshots["snap-002"] = {
            "id": "snap-002",
            "workpackage_id": "wp-002",
            "project_id": "proj-001",
            "period_start": "2026-04-01",
            "period_end": "2026-04-15",
            "status": "draft",
            "percent_complete": 20,
            "hours_reported": 40,
            "submitted_by": "lead-001",
            "created_at": now,
            "updated_at": now,
        }

        # Issues
        self.issues["issue-001"] = {
            "id": "issue-001",
            "apparatus_id": "app-003",
            "task_id": "task-002",
            "project_id": "proj-001",
            "title": "Insulation resistance out of range",
            "severity": "medium",
            "status": "open",
            "blocks_completion": False,
            "reported_by": "tech-001",
            "created_at": now,
            "updated_at": now,
        }
        self.issues["issue-002"] = {
            "id": "issue-002",
            "apparatus_id": "app-001",
            "task_id": "task-001",
            "project_id": "proj-001",
            "title": "Ground rod connection loose",
            "severity": "high",
            "status": "open",
            "blocks_completion": True,
            "reported_by": "tech-001",
            "created_at": now,
            "updated_at": now,
        }

    def reset(self):
        """Clear all data and reseed from Postgres."""
        # Truncate in FK-safe order
        tables = [
            "seam.idempotency_keys",
            "seam.audit_log",
            "seam.checklist_items",
            "seam.hours",
            "seam.assignments",
            "seam.issues",
            "seam.snapshots",
            "seam.apparatus",
            "seam.tasks",
            "seam.workpackages",
            "seam.projects",
        ]
        conn = _conn_get()
        with conn.cursor() as cur:
            for t in tables:
                cur.execute(f"DELETE FROM {t}")
        # Re-init collection proxies (bust column caches)
        self.__init__()
        self.seed_demo_data()


# ---------------------------------------------------------------------------
# Singleton (matches MemoryStore pattern)
# ---------------------------------------------------------------------------
store = SupabaseStore()
store.seed_demo_data()
