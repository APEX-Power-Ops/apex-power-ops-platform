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

from app.pm_lane_seed import build_pm_lane_seed

# ---------------------------------------------------------------------------
# Connection factory
# ---------------------------------------------------------------------------

_DEFAULT_DSN = "host=127.0.0.1 port=5432 dbname=apex_pm_stage user=apex_pm_stage_user"


def _get_dsn() -> str:
    """Return Postgres DSN from env or default."""
    return os.getenv("SEAM_DATABASE_URL", _DEFAULT_DSN)


def _should_seed_demo_data() -> bool:
    """Only seed demo fixtures when explicitly requested."""
    return os.getenv("SEAM_AUTO_SEED_DEMO", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


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

    def _json_columns(self) -> List[str]:
        """Return JSON/JSONB column names for this table."""
        if not hasattr(self, "_json_cols_cache"):
            schema, tbl = self._table.split(".")
            with self._cur() as cur:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = %s AND table_name = %s "
                    "AND data_type IN ('json', 'jsonb')",
                    (schema, tbl),
                )
                self._json_cols_cache = [r["column_name"] for r in cur.fetchall()]
        return self._json_cols_cache

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

        # psycopg2 does not adapt plain dict/list values for typed JSONB
        # columns in this generic path; overflow `data` is handled above.
        json_columns = set(self._json_columns())
        for column in json_columns.intersection(known):
            if isinstance(known[column], (dict, list)):
                known[column] = json.dumps(known[column])

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
# ApprovalPersistenceStore — insert-only adapter target for PM import approvals
# ---------------------------------------------------------------------------

class ApprovalPersistenceStore:
    """Insert-only table adapter for seam.pm_import_candidate_approvals."""

    _table = "seam.pm_import_candidate_approvals"
    _pk = "approval_record_id"

    def _cur(self):
        return _conn_get().cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _row_to_dict(self, row: dict) -> dict:
        out = {}
        for k, v in row.items():
            if isinstance(v, datetime):
                out[k] = v.isoformat()
            else:
                out[k] = v
        return out

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

    def _approval_columns(self) -> List[str]:
        return [
            "approval_record_id",
            "mutation_id",
            "audit_event_id",
            "candidate_id",
            "candidate_version",
            "source_stat_fingerprint",
            "candidate_shape_fingerprint",
            "idempotency_key",
            "decision",
            "approved_by_actor_id",
            "approved_at_utc",
            "accepted_warning_codes",
            "accepted_no_go_overrides",
            "review_notes",
            "approval_payload",
            "validation_result",
            "created_at",
        ]

    def _approval_values(self, record: dict, cols: List[str]) -> List[Any]:
        values = []
        for col in cols:
            value = record.get(col)
            if col in {
                "accepted_warning_codes",
                "accepted_no_go_overrides",
                "approval_payload",
                "validation_result",
            }:
                value = json.dumps(value)
            values.append(value)
        return values

    def insert(self, record: dict) -> None:
        cols = self._approval_columns()
        values = self._approval_values(record, cols)
        placeholders = ", ".join(["%s"] * len(cols))
        sql = f"INSERT INTO {self._table} ({', '.join(cols)}) VALUES ({placeholders})"
        with self._cur() as cur:
            cur.execute(sql, values)

    def insert_with_audit(self, record: dict, audit_event: dict) -> None:
        conn = _conn_get()
        previous_autocommit = conn.autocommit
        conn.autocommit = False
        try:
            with conn.cursor() as cur:
                approval_cols = self._approval_columns()
                approval_values = self._approval_values(record, approval_cols)
                approval_placeholders = ", ".join(["%s"] * len(approval_cols))
                cur.execute(
                    f"INSERT INTO {self._table} ({', '.join(approval_cols)}) VALUES ({approval_placeholders})",
                    approval_values,
                )

                audit_cols = [
                    "id",
                    "mutation_id",
                    "actor_id",
                    "actor_role",
                    "entity_type",
                    "entity_id",
                    "action_type",
                    "from_state",
                    "to_state",
                    "reason",
                    "timestamp",
                ]
                audit_values = [
                    audit_event.get("id"),
                    audit_event.get("mutation_id"),
                    audit_event.get("actor_id"),
                    audit_event.get("actor_role"),
                    audit_event.get("entity_type"),
                    audit_event.get("entity_id"),
                    audit_event.get("action_type"),
                    json.dumps(audit_event.get("from_state", {})),
                    json.dumps(audit_event.get("to_state", {})),
                    audit_event.get("reason"),
                    audit_event.get("server_timestamp"),
                ]
                audit_placeholders = ", ".join(["%s"] * len(audit_cols))
                cur.execute(
                    f"INSERT INTO seam.audit_log ({', '.join(audit_cols)}) VALUES ({audit_placeholders})",
                    audit_values,
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.autocommit = previous_autocommit

    def values(self) -> List[dict]:
        with self._cur() as cur:
            cur.execute(f"SELECT * FROM {self._table} ORDER BY created_at")
            return [self._row_to_dict(dict(row)) for row in cur.fetchall()]


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
        self.durable_field_records = PgDict("durable_field_records")
        self.production_tracking_records = PgDict("production_tracking_records")
        self.customer_completion_records = PgDict("customer_completion_records")
        self.tasks = PgDict("tasks")
        self.workpackages = PgDict("workpackages")
        self.snapshots = PgDict("snapshots")
        self.idempotency_keys = PgDict("idempotency_keys", pk_col="key", payload_col="response")
        self.pm_import_candidate_approvals = ApprovalPersistenceStore()
        self.audit_log = PgList()
        self.projects = PgDict("projects")

    def seed_demo_data(self):
        """Populate the store with demo data (same data as MemoryStore)."""
        now = datetime.now(timezone.utc).isoformat()
        seed = build_pm_lane_seed(now)

        self.projects[seed["project"]["id"]] = seed["project"]
        for row in seed["workpackages"]:
            self.workpackages[row["id"]] = row
        for row in seed["tasks"]:
            self.tasks[row["id"]] = row
        for row in seed["apparatus"]:
            self.apparatus[row["id"]] = row
        for row in seed["checklist_items"]:
            self.checklist_items[row["id"]] = row
        for row in seed["assignments"]:
            self.assignments[row["id"]] = row
        for row in seed["hours"]:
            self.hours[row["id"]] = row
        for row in seed["snapshots"]:
            self.snapshots[row["id"]] = row
        for row in seed["issues"]:
            self.issues[row["id"]] = row

    def reset(self):
        """Clear all data and reseed from Postgres."""
        # Truncate in FK-safe order
        tables = [
            "seam.idempotency_keys",
            "seam.pm_import_candidate_approvals",
            "seam.audit_log",
            "seam.checklist_items",
            "seam.hours",
            "seam.customer_completion_records",
            "seam.production_tracking_records",
            "seam.durable_field_records",
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
if _should_seed_demo_data():
    store.seed_demo_data()
