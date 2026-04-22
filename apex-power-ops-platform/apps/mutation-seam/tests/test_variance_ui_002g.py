"""
Focused sandbox tests for packet UI-002g — comparative schedule analytics.

Scope: prove the `list_variance_rows()` query helper + the `/variance` route
behave read-only, expose only schedule-derived variance fields, never
fabricate variance for a task with no persisted baseline, and do not take
any input from the degraded third-party add/delete delta export.

The tests never touch a real Postgres; `psycopg2.connect` is monkeypatched
to a recording fake that captures every SQL statement + its parameters and
returns a canned row set shaped like what the SELECT's output columns carry.

Disposition: sandbox-complete. Host-browser evidence is deferred to a
dedicated successor per packet UI-002g validation step 4, which the packet
explicitly authorizes when a real host session is not available.

Run:
    python -m pytest apps/mutation-seam/tests/test_variance_ui_002g.py \
        -v --noconftest
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest


HERE = Path(__file__).resolve().parent
APP_ROOT = HERE.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


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
# Canned row set — three tasks:
#   A10: baselined, slipping (finish_variance_hours = +48)
#   A20: baselined, on plan  (finish_variance_hours = 0)
#   A90: no baseline         (every variance field NULL; has_baseline=False)
# ---------------------------------------------------------------------------

_VARIANCE_COLUMNS = [
    "schedule_task_id", "p6_task_id", "schedule_project_id",
    "task_code", "task_name",
    "p6_status", "apex_status",
    "planned_start", "planned_finish",
    "actual_start", "actual_finish",
    "duration_hours",
    "total_float_hours", "free_float_hours", "critical_flag",
    "baseline_start_at", "baseline_end_at",
    "baseline_name", "baseline_source", "baselined_at",
    "start_variance_hours", "finish_variance_hours",
    "duration_variance_hours", "has_baseline",
]


def _fixture_rows() -> List[Tuple]:
    return [
        # A10 — slipping: planned_finish 2026-04-16, baseline 2026-04-14 → +48h
        (
            "task-A10", "p6-7001", "proj-001",
            "A10", "Energize bus",
            "Active", "in_progress",
            "2026-04-10T00:00:00Z", "2026-04-16T00:00:00Z",
            None, None,
            72.0,
            0, 0, True,
            "2026-04-10T00:00:00Z", "2026-04-14T00:00:00Z",
            "Stack DC — Original Baseline R01", "p6_import",
            "2026-04-17T00:00:00Z",
            0.0, 48.0, 48.0, True,
        ),
        # A20 — on plan: identical current and baseline pair → 0/0
        (
            "task-A20", "p6-7002", "proj-001",
            "A20", "Commission relay",
            "Active", "planned",
            "2026-04-12T00:00:00Z", "2026-04-14T00:00:00Z",
            None, None,
            48.0,
            0, 0, True,
            "2026-04-12T00:00:00Z", "2026-04-14T00:00:00Z",
            "Stack DC — Original Baseline R01", "p6_import",
            "2026-04-17T00:00:00Z",
            0.0, 0.0, 0.0, True,
        ),
        # A90 — no baseline: every variance NULL, has_baseline False
        (
            "task-A90", "p6-7090", "proj-001",
            "A90", "Late-add scope",
            "Active", "planned",
            "2026-04-20T00:00:00Z", "2026-04-22T00:00:00Z",
            None, None,
            48.0,
            40, 40, False,
            None, None,
            None, None, None,
            None, None, None, False,
        ),
    ]


@pytest.fixture
def queries_module(monkeypatch):
    os.environ.setdefault("SEAM_DATABASE_URL", "postgres://unused-in-sandbox")
    from app.schedule import queries as q  # noqa: WPS433

    captured: Dict[str, Any] = {"conn": None}

    def _fake_connect(_dsn: str):
        conn = _FakeConn(_fixture_rows(), _VARIANCE_COLUMNS)
        captured["conn"] = conn
        return conn

    assert q.psycopg2 is not None
    monkeypatch.setattr(q.psycopg2, "connect", _fake_connect)
    return q, captured


# ---------------------------------------------------------------------------
# Query-helper tests
# ---------------------------------------------------------------------------


def test_list_variance_rows_uses_readonly_session_setup(queries_module):
    q, captured = queries_module
    q.list_variance_rows()
    conn = captured["conn"]
    assert conn is not None
    assert len(conn._cursor.executed) == 2
    setup_sql, _ = conn._cursor.executed[0]
    assert "default_transaction_read_only = on" in setup_sql.lower(), (
        "variance helper must open a read-only session before the SELECT"
    )


def test_list_variance_rows_is_readonly_by_construction(queries_module):
    q, captured = queries_module
    q.list_variance_rows()
    conn = captured["conn"]
    for sql, _ in conn._cursor.executed:
        upper = sql.upper()
        for verb in (" INSERT ", " UPDATE ", " DELETE ", " MERGE ", " TRUNCATE "):
            assert verb not in f" {upper} ", (
                f"variance SQL must not contain write verb {verb.strip()}: {sql!r}"
            )


def test_list_variance_rows_derives_variance_from_persisted_baseline_only(queries_module):
    """The SQL must compute start/finish/duration variance from the persisted
    baseline columns on ``schedule.tasks`` — never from any external delta."""
    q, captured = queries_module
    q.list_variance_rows()
    _, select_sql_and_params = captured["conn"]._cursor.executed[1]
    select_sql = captured["conn"]._cursor.executed[1][0]

    # Derives from persisted baseline columns (not a delta export).
    assert "st.baseline_start_at" in select_sql
    assert "st.baseline_end_at"   in select_sql
    assert "st.planned_start"     in select_sql
    assert "st.planned_finish"    in select_sql

    # NULL-preserving CASE wrappers are present for every variance field.
    # We deliberately do not collapse NULL baseline → 0 variance.
    assert "start_variance_hours"    in select_sql
    assert "finish_variance_hours"   in select_sql
    assert "duration_variance_hours" in select_sql
    # The CASE guards must name the baseline columns so they fall through
    # to NULL for tasks whose baseline was never persisted.
    assert "WHEN st.planned_start    IS NULL" in select_sql or \
           "WHEN st.planned_start  IS NULL"   in select_sql or \
           "WHEN st.planned_start IS NULL"    in select_sql
    assert "st.baseline_start_at IS NULL" in select_sql
    assert "st.baseline_end_at" in select_sql and "IS NULL" in select_sql

    # Reads exclusively from schedule.tasks — never from any delta/import
    # staging surface.
    assert "FROM schedule.tasks" in select_sql
    for bad_source in (
        "delta_export", "third_party_delta", "apex_delta",
        "FROM schedule.delta", "FROM apex_delta",
    ):
        assert bad_source not in select_sql, (
            f"variance helper must not read from any delta export surface: {bad_source}"
        )


def test_list_variance_rows_returns_joined_dicts_with_null_preservation(queries_module):
    q, _captured = queries_module
    rows = q.list_variance_rows()

    assert all(isinstance(r, dict) for r in rows)
    assert [r["task_code"] for r in rows] == ["A10", "A20", "A90"]

    # A10 slipping — positive finish variance preserved.
    assert rows[0]["has_baseline"]            is True
    assert rows[0]["finish_variance_hours"]   == 48.0
    assert rows[0]["start_variance_hours"]    == 0.0

    # A20 on plan — both variance fields exactly 0 (server told us so).
    assert rows[1]["has_baseline"]            is True
    assert rows[1]["finish_variance_hours"]   == 0.0

    # A90 no baseline — every variance field is NULL (the contract).
    assert rows[2]["has_baseline"]            is False
    assert rows[2]["baseline_start_at"]       is None
    assert rows[2]["baseline_end_at"]         is None
    assert rows[2]["start_variance_hours"]    is None
    assert rows[2]["finish_variance_hours"]   is None
    assert rows[2]["duration_variance_hours"] is None


def test_list_variance_rows_applies_project_filter_via_parameters(queries_module):
    q, captured = queries_module
    q.list_variance_rows(schedule_project_id="proj-001")
    _, params = captured["conn"]._cursor.executed[1]
    # (project, project, with_baseline_only, only_slipping)
    assert params == ("proj-001", "proj-001", False, False)


def test_list_variance_rows_applies_baseline_only_filter(queries_module):
    q, captured = queries_module
    q.list_variance_rows(with_baseline_only=True)
    _, params = captured["conn"]._cursor.executed[1]
    assert params == (None, None, True, False)

    select_sql = captured["conn"]._cursor.executed[1][0]
    # The WHERE clause must gate on persisted baseline columns, not on a
    # client-fabricated "has_baseline" flag that the caller could trick.
    assert "baseline_start_at IS NOT NULL" in select_sql
    assert "baseline_end_at IS NOT NULL"   in select_sql


def test_list_variance_rows_applies_only_slipping_filter(queries_module):
    q, captured = queries_module
    q.list_variance_rows(only_slipping=True)
    _, params = captured["conn"]._cursor.executed[1]
    assert params == (None, None, False, True)

    select_sql = captured["conn"]._cursor.executed[1][0]
    # Slip is defined as planned_finish strictly AFTER baseline_end_at —
    # never as an external delta's "add" marker.
    assert "st.planned_finish > st.baseline_end_at" in select_sql


def test_list_variance_rows_closes_connection_even_on_error(monkeypatch):
    os.environ.setdefault("SEAM_DATABASE_URL", "postgres://unused-in-sandbox")
    from app.schedule import queries as q

    class _BoomCursor(_FakeCursor):
        def execute(self, sql, params=None):
            super().execute(sql, params)
            if "finish_variance_hours" in sql:
                raise RuntimeError("variance boom")

    class _BoomConn(_FakeConn):
        def __init__(self):
            super().__init__([], _VARIANCE_COLUMNS)
            self._cursor = _BoomCursor([], _VARIANCE_COLUMNS)

    conn_container: Dict[str, _BoomConn] = {}

    def _boom_connect(_dsn):
        c = _BoomConn()
        conn_container["c"] = c
        return c

    monkeypatch.setattr(q.psycopg2, "connect", _boom_connect)
    with pytest.raises(RuntimeError, match="variance boom"):
        q.list_variance_rows()
    assert conn_container["c"].closed is True


# ---------------------------------------------------------------------------
# Route-wiring tests — /variance is GET-only, wired to the helper, and
# still leaves the schedule router free of write verbs.
# ---------------------------------------------------------------------------


def test_variance_route_is_get_only_and_wired_to_helper():
    from app.routers import schedule as sched_router
    from fastapi.routing import APIRoute

    variance_routes = [
        r for r in sched_router.router.routes
        if isinstance(r, APIRoute) and r.path.endswith("/variance")
    ]
    assert variance_routes, "expected a /variance route under the schedule router"
    assert len(variance_routes) == 1

    route = variance_routes[0]
    assert route.methods == {"GET"}, (
        f"/variance must be GET-only per UI-002g; found methods {route.methods}"
    )

    import inspect
    src = inspect.getsource(route.endpoint)
    assert "list_variance_rows" in src, (
        "/variance handler must delegate to list_variance_rows, not a fresh query"
    )


def test_variance_route_exposes_expected_query_params():
    """Inspect the endpoint source for the three authored query parameters —
    project_id (aliased), with_baseline_only, only_slipping. Source-level
    assertion is the stable surface because FastAPI's Query default stashes
    constraint metadata whose shape varies across Pydantic versions (same
    reason the drivers/tracer tests inspect source, not defaults)."""
    from app.routers import schedule as sched_router
    from fastapi.routing import APIRoute
    import inspect

    route = next(
        r for r in sched_router.router.routes
        if isinstance(r, APIRoute) and r.path.endswith("/variance")
    )
    src = inspect.getsource(route.endpoint)
    assert 'alias="project_id"'   in src
    assert "with_baseline_only"   in src
    assert "only_slipping"        in src


def test_schedule_router_still_has_no_write_verbs_after_variance_addition():
    """Regression guard: UI-002g must not introduce POST/PUT/PATCH/DELETE
    anywhere under /api/v1/schedule."""
    from app.routers import schedule as sched_router
    from fastapi.routing import APIRoute

    write_verbs = {"POST", "PUT", "PATCH", "DELETE"}
    for r in sched_router.router.routes:
        if not isinstance(r, APIRoute):
            continue
        assert not (r.methods & write_verbs), (
            f"UI-002g must not introduce write verbs; found {r.methods} on {r.path}"
        )
