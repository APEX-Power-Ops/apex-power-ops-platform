"""
Focused sandbox tests for packet UI-002e — schedule drivers read surface.

Scope: prove the `list_driver_edges()` query helper and the `/drivers` route
behave read-only and only expose critical-path driving edges. The test never
touches a real Postgres; `psycopg2.connect` is monkeypatched to a recording
fake that captures the SQL, the parameters, and the read-only session-setup
statement, and returns a canned row set.

Disposition: sandbox-complete. Host-browser evidence is deferred to a
dedicated successor per packet UI-002e validation step 4, which the packet
explicitly authorizes when a real host session is not available.

Run:
    python -m pytest apps/mutation-seam/tests/test_drivers_ui_002e.py \
        -v --noconftest
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest


HERE = Path(__file__).resolve().parent
APP_ROOT = HERE.parent            # apps/mutation-seam
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


# ---------------------------------------------------------------------------
# Recording fake for psycopg2 — hermetic, captures SQL + params.
# ---------------------------------------------------------------------------


class _FakeCursor:
    def __init__(self, rows: List[Tuple], columns: List[str]):
        self._rows = rows
        self._columns = columns
        self.executed: List[Tuple[str, Optional[Tuple]]] = []
        self.description = [type("Col", (), {"name": c}) for c in columns]

    def execute(self, sql: str, params: Optional[Tuple] = None) -> None:
        self.executed.append((sql, params))

    def fetchall(self) -> List[Tuple]:
        return list(self._rows)

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *_exc) -> None:
        pass


class _FakeConn:
    def __init__(self, rows: List[Tuple], columns: List[str]):
        self._cursor = _FakeCursor(rows, columns)
        self.autocommit = True
        self.committed = False
        self.closed = False

    def cursor(self) -> _FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.committed = True

    def close(self) -> None:
        self.closed = True


# ---------------------------------------------------------------------------
# Canned row set — two driving edges against a single project.
# ---------------------------------------------------------------------------

_DRIVER_EDGE_COLUMNS = [
    "relationship_id", "p6_taskpred_id", "schedule_project_id",
    "rel_type", "lag_hours",
    "driver_task_id", "driver_p6_task_id", "driver_task_code",
    "driver_task_name", "driver_planned_start", "driver_planned_finish",
    "driver_total_float_hours", "driver_critical_flag",
    "driven_task_id", "driven_p6_task_id", "driven_task_code",
    "driven_task_name", "driven_planned_start", "driven_planned_finish",
    "driven_total_float_hours", "driven_critical_flag",
]


def _fixture_rows() -> List[Tuple]:
    # Edge 1: A10(crit) → A20(crit), FS, 0h
    # Edge 2: A10(crit) → A30(non-crit), FS, +8h lag
    return [
        (
            "rel-001", "taskpred-001", "proj-001",
            "FS", 0,
            "task-A10", "p6-7001", "A10", "Energize bus",
            "2026-04-10T00:00:00Z", "2026-04-12T00:00:00Z", 0, True,
            "task-A20", "p6-7002", "A20", "Commission relay",
            "2026-04-12T00:00:00Z", "2026-04-14T00:00:00Z", 0, True,
        ),
        (
            "rel-002", "taskpred-002", "proj-001",
            "FS", 8,
            "task-A10", "p6-7001", "A10", "Energize bus",
            "2026-04-10T00:00:00Z", "2026-04-12T00:00:00Z", 0, True,
            "task-A30", "p6-7003", "A30", "Document commissioning",
            "2026-04-13T00:00:00Z", "2026-04-17T00:00:00Z", 40, False,
        ),
    ]


@pytest.fixture
def queries_module(monkeypatch):
    """Load the queries module with a fake psycopg2.connect installed."""
    os.environ.setdefault("SEAM_DATABASE_URL", "postgres://unused-in-sandbox")

    # Import after ensuring sys.path is set.
    from app.schedule import queries as q  # noqa: WPS433 (late import is intentional)

    captured: Dict[str, Any] = {"conn": None}

    def _fake_connect(_dsn: str):
        conn = _FakeConn(_fixture_rows(), _DRIVER_EDGE_COLUMNS)
        captured["conn"] = conn
        return conn

    # psycopg2 is already imported by queries.py at module-load time; patch it
    # there so _open_readonly's `psycopg2.connect` call picks up the fake.
    assert q.psycopg2 is not None, "psycopg2 must be importable for these tests"
    monkeypatch.setattr(q.psycopg2, "connect", _fake_connect)
    return q, captured


# ---------------------------------------------------------------------------
# Query-helper tests
# ---------------------------------------------------------------------------


def test_list_driver_edges_applies_critical_flag_filter(queries_module):
    """The SQL must filter drivers by `d.critical_flag = TRUE`.

    This is the first-slice lock in packet UI-002e: the initial driver
    surface MUST expose critical-path driving edges only, NOT the full
    dependency graph.
    """
    q, captured = queries_module
    rows = q.list_driver_edges(schedule_project_id="proj-001")
    assert len(rows) == 2, "fake returns two rows; helper must pass them through"
    conn = captured["conn"]
    assert conn is not None
    # Two executes: (1) the read-only session setup, (2) the SELECT.
    assert len(conn._cursor.executed) == 2
    setup_sql, _ = conn._cursor.executed[0]
    select_sql, select_params = conn._cursor.executed[1]

    # (1) Defensive read-only posture is established BEFORE the SELECT.
    assert "default_transaction_read_only = on" in setup_sql.lower()

    # (2) The SELECT must filter drivers by critical_flag.
    assert "d.critical_flag = TRUE" in select_sql, (
        "list_driver_edges must restrict to predecessor critical_flag=TRUE "
        "— this is the UI-002e first-slice scope lock"
    )
    # (3) And must JOIN schedule.tasks twice under the `d` / `s` aliases.
    assert "schedule.relationships r" in select_sql
    assert "JOIN schedule.tasks d ON d.id = r.predecessor_task_id" in select_sql
    assert "JOIN schedule.tasks s ON s.id = r.successor_task_id" in select_sql

    # (4) And must respect the project_id filter pattern used elsewhere.
    assert "r.schedule_project_id = %s" in select_sql
    assert select_params == ("proj-001", "proj-001")


def test_list_driver_edges_is_readonly_by_construction(queries_module):
    """The SQL executed MUST contain NO write verbs.

    This is defense-in-depth: the router is GET-only and the session is set
    to `default_transaction_read_only = on`, but the SQL shape itself must
    also be read-only so it could never accidentally be reused by a write
    caller.
    """
    q, captured = queries_module
    q.list_driver_edges()
    conn = captured["conn"]
    for sql, _ in conn._cursor.executed:
        upper = sql.upper()
        for verb in (" INSERT ", " UPDATE ", " DELETE ", " MERGE ", " TRUNCATE "):
            assert verb not in f" {upper} ", (
                f"SQL must not contain write verb {verb.strip()}: {sql!r}"
            )


def test_list_driver_edges_without_project_passes_nulls(queries_module):
    """Omitting the project filter MUST pass (None, None) so the SQL wildcard
    kicks in. The helper must never default-inject a project id."""
    q, captured = queries_module
    q.list_driver_edges()
    conn = captured["conn"]
    _, select_params = conn._cursor.executed[1]
    assert select_params == (None, None)


def test_list_driver_edges_returns_dicts_with_joined_shape(queries_module):
    """Every returned row must be a dict carrying both driver_* and
    driven_* context, so the PM review surface never has to join back on
    the client."""
    q, _captured = queries_module
    rows = q.list_driver_edges(schedule_project_id="proj-001")

    assert all(isinstance(r, dict) for r in rows)
    expected_keys = {
        "relationship_id", "p6_taskpred_id", "schedule_project_id",
        "rel_type", "lag_hours",
        "driver_task_id", "driver_task_code", "driver_planned_finish",
        "driver_critical_flag",
        "driven_task_id", "driven_task_code", "driven_planned_start",
        "driven_critical_flag",
    }
    for r in rows:
        missing = expected_keys - r.keys()
        assert not missing, f"driver-edge row missing keys: {missing}"

    first, second = rows
    assert first["rel_type"] == "FS" and first["lag_hours"] == 0
    assert first["driver_critical_flag"] is True
    assert first["driven_critical_flag"] is True
    assert second["lag_hours"] == 8
    assert second["driven_critical_flag"] is False  # one driven off-critical OK


def test_list_driver_edges_closes_connection_even_on_error(monkeypatch):
    """Connection-hygiene: the helper must close the connection even if the
    cursor raises. This matters because the module opens a fresh conn per
    call and a leak during an error would quickly exhaust the pool."""
    os.environ.setdefault("SEAM_DATABASE_URL", "postgres://unused-in-sandbox")
    from app.schedule import queries as q

    class _BoomCursor(_FakeCursor):
        def execute(self, sql, params=None):
            # Let the readonly-setup execute succeed; fail only on the SELECT
            # by counting prior calls.
            super().execute(sql, params)
            if "SELECT" in sql:
                raise RuntimeError("boom")

    class _BoomConn(_FakeConn):
        def __init__(self):
            super().__init__([], _DRIVER_EDGE_COLUMNS)
            self._cursor = _BoomCursor([], _DRIVER_EDGE_COLUMNS)

    conn_container: Dict[str, _BoomConn] = {}

    def _boom_connect(_dsn):
        c = _BoomConn()
        conn_container["c"] = c
        return c

    monkeypatch.setattr(q.psycopg2, "connect", _boom_connect)
    with pytest.raises(RuntimeError, match="boom"):
        q.list_driver_edges()
    assert conn_container["c"].closed is True, (
        "list_driver_edges must close its connection even when the SELECT raises"
    )


# ---------------------------------------------------------------------------
# Route-wiring tests — assert the /drivers endpoint exists, is GET-only, and
# is wired to list_driver_edges. No HTTP roundtrip is made; the router is
# introspected directly so the test stays hermetic.
# ---------------------------------------------------------------------------


def test_drivers_route_is_get_only_and_wired_to_helper():
    from app.routers import schedule as sched_router
    from fastapi.routing import APIRoute

    drivers_routes = [
        r for r in sched_router.router.routes
        if isinstance(r, APIRoute) and r.path.endswith("/drivers")
    ]
    assert drivers_routes, "expected a /drivers route to exist under the schedule router"
    assert len(drivers_routes) == 1, (
        "there must be exactly one /drivers route; no duplicate PUT/POST siblings"
    )

    drivers = drivers_routes[0]
    assert drivers.methods == {"GET"}, (
        f"/drivers must be GET-only per UI-002e; found methods {drivers.methods}"
    )
    # The endpoint callable must delegate to sched_q.list_driver_edges via
    # _safe_call. The simplest way to assert this in isolation is to confirm
    # the handler's source references `list_driver_edges`.
    import inspect
    src = inspect.getsource(drivers.endpoint)
    assert "list_driver_edges" in src, (
        "handler must delegate to list_driver_edges, not a fresh query"
    )


def test_drivers_route_does_not_introduce_write_verbs():
    """No POST/PUT/PATCH/DELETE routes may be introduced to the schedule
    router by UI-002e — packet validation step 3."""
    from app.routers import schedule as sched_router
    from fastapi.routing import APIRoute

    write_verbs = {"POST", "PUT", "PATCH", "DELETE"}
    for r in sched_router.router.routes:
        if not isinstance(r, APIRoute):
            continue
        assert not (r.methods & write_verbs), (
            f"UI-002e must not introduce write verbs; found {r.methods} on {r.path}"
        )
