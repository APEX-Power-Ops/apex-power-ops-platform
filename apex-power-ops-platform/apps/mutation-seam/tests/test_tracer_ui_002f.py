"""
Focused sandbox tests for packet UI-002f — schedule tracer read surface.

Scope: prove the `list_tracer_chain()` query helper + the `/tracer` route
behave read-only, are depth-bounded and cycle-guarded, and only expose
persisted `schedule.relationships` edges. The tests never touch a real
Postgres; `psycopg2.connect` is monkeypatched to a recording fake that
captures the SQL text, the parameters, and the read-only session-setup
statement, and returns a canned row set.

Disposition: sandbox-complete. Host-browser evidence is deferred to a
dedicated successor per packet UI-002f validation step 4, which the packet
explicitly authorizes when a real host session is not available.

Run:
    python -m pytest apps/mutation-seam/tests/test_tracer_ui_002f.py \
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
# Canned row set — two-hop upstream chain from task-A30 back through A20→A10.
# ---------------------------------------------------------------------------

_TRACER_COLUMNS = [
    "seed_task_id", "depth", "relationship_id", "rel_type", "lag_hours",
    "parent_task_id", "parent_p6_task_id", "parent_task_code",
    "parent_task_name", "parent_planned_start", "parent_planned_finish",
    "parent_total_float_hours", "parent_critical_flag",
    "child_task_id", "child_p6_task_id", "child_task_code",
    "child_task_name", "child_planned_start", "child_planned_finish",
    "child_total_float_hours", "child_critical_flag",
]


def _fixture_rows() -> List[Tuple]:
    return [
        # depth 1: A20 (parent) -> A30 (child, the seed task)
        (
            "task-A30", 1, "rel-002", "FS", 0,
            "task-A20", "p6-7002", "A20", "Commission relay",
            "2026-04-12T00:00:00Z", "2026-04-14T00:00:00Z", 0, True,
            "task-A30", "p6-7003", "A30", "Document commissioning",
            "2026-04-14T00:00:00Z", "2026-04-17T00:00:00Z", 40, False,
        ),
        # depth 2: A10 (parent) -> A20 (child — one hop above the seed)
        (
            "task-A30", 2, "rel-001", "FS", 0,
            "task-A10", "p6-7001", "A10", "Energize bus",
            "2026-04-10T00:00:00Z", "2026-04-12T00:00:00Z", 0, True,
            "task-A20", "p6-7002", "A20", "Commission relay",
            "2026-04-12T00:00:00Z", "2026-04-14T00:00:00Z", 0, True,
        ),
    ]


@pytest.fixture
def queries_module(monkeypatch):
    os.environ.setdefault("SEAM_DATABASE_URL", "postgres://unused-in-sandbox")
    from app.schedule import queries as q  # noqa: WPS433

    captured: Dict[str, Any] = {"conn": None}

    def _fake_connect(_dsn: str):
        conn = _FakeConn(_fixture_rows(), _TRACER_COLUMNS)
        captured["conn"] = conn
        return conn

    assert q.psycopg2 is not None
    monkeypatch.setattr(q.psycopg2, "connect", _fake_connect)
    return q, captured


# ---------------------------------------------------------------------------
# Query-helper tests
# ---------------------------------------------------------------------------


def test_list_tracer_chain_requires_task_id(queries_module):
    q, _captured = queries_module
    with pytest.raises(ValueError, match="task_id is required"):
        q.list_tracer_chain(task_id="")


def test_list_tracer_chain_uses_recursive_cte_and_cycle_guard(queries_module):
    """The SQL must be a WITH RECURSIVE CTE with a walked-id cycle guard.

    This is the first-slice lock: traversal MUST be bounded and MUST
    terminate even on pathological P6 imports that contain cycles.
    """
    q, captured = queries_module
    q.list_tracer_chain(task_id="task-A30")
    conn = captured["conn"]
    assert conn is not None
    assert len(conn._cursor.executed) == 2
    setup_sql, _ = conn._cursor.executed[0]
    select_sql, select_params = conn._cursor.executed[1]

    assert "default_transaction_read_only = on" in setup_sql.lower()
    assert "WITH RECURSIVE trace_chain" in select_sql, (
        "tracer must use a WITH RECURSIVE CTE so depth is bounded at query time"
    )
    assert "NOT (r.predecessor_task_id = ANY(t.visited_chain))" in select_sql, (
        "tracer must cycle-guard via a walked-id array — pathological P6 "
        "imports can contain cycles"
    )
    assert "JOIN schedule.relationships r" in select_sql
    assert "r.successor_task_id = t.parent_task_id" in select_sql, (
        "recursion must walk BACKWARDS through predecessors, not forwards"
    )
    # Three params: task_id seed (for seed column), task_id filter, depth cap.
    assert select_params == ("task-A30", "task-A30", 10)


def test_list_tracer_chain_is_readonly_by_construction(queries_module):
    q, captured = queries_module
    q.list_tracer_chain(task_id="task-A30")
    conn = captured["conn"]
    for sql, _ in conn._cursor.executed:
        upper = sql.upper()
        for verb in (" INSERT ", " UPDATE ", " DELETE ", " MERGE ", " TRUNCATE "):
            assert verb not in f" {upper} ", (
                f"SQL must not contain write verb {verb.strip()}: {sql!r}"
            )


def test_list_tracer_chain_caps_max_depth_at_hard_limit(queries_module):
    """Callers MUST NOT be able to set unbounded recursion depth."""
    q, captured = queries_module
    q.list_tracer_chain(task_id="task-A30", max_depth=999)
    conn = captured["conn"]
    _, select_params = conn._cursor.executed[1]
    # Helper-level hard cap is _TRACER_HARD_MAX_DEPTH (25).
    assert select_params[2] == 25


def test_list_tracer_chain_falls_back_when_depth_nonpositive(queries_module):
    q, captured = queries_module
    q.list_tracer_chain(task_id="task-A30", max_depth=0)
    _, select_params_0 = captured["conn"]._cursor.executed[1]
    assert select_params_0[2] == 10

    # reset and try negative
    captured["conn"] = None
    q.list_tracer_chain(task_id="task-A30", max_depth=-5)
    _, select_params_neg = captured["conn"]._cursor.executed[1]
    assert select_params_neg[2] == 10


def test_list_tracer_chain_returns_dicts_with_joined_shape(queries_module):
    q, _captured = queries_module
    rows = q.list_tracer_chain(task_id="task-A30")

    assert all(isinstance(r, dict) for r in rows)
    assert [r["depth"] for r in rows] == [1, 2]
    assert [r["parent_task_code"] for r in rows] == ["A20", "A10"]
    assert [r["child_task_code"]  for r in rows] == ["A30", "A20"]
    # Parent A20 is critical, parent A10 is critical, seed child A30 is not.
    assert rows[0]["parent_critical_flag"] is True
    assert rows[0]["child_critical_flag"]  is False
    assert rows[1]["parent_critical_flag"] is True
    assert rows[1]["child_critical_flag"]  is True


def test_list_tracer_chain_closes_connection_even_on_error(monkeypatch):
    os.environ.setdefault("SEAM_DATABASE_URL", "postgres://unused-in-sandbox")
    from app.schedule import queries as q

    class _BoomCursor(_FakeCursor):
        def execute(self, sql, params=None):
            super().execute(sql, params)
            if "WITH RECURSIVE" in sql:
                raise RuntimeError("tracer boom")

    class _BoomConn(_FakeConn):
        def __init__(self):
            super().__init__([], _TRACER_COLUMNS)
            self._cursor = _BoomCursor([], _TRACER_COLUMNS)

    conn_container: Dict[str, _BoomConn] = {}

    def _boom_connect(_dsn):
        c = _BoomConn()
        conn_container["c"] = c
        return c

    monkeypatch.setattr(q.psycopg2, "connect", _boom_connect)
    with pytest.raises(RuntimeError, match="tracer boom"):
        q.list_tracer_chain(task_id="task-A30")
    assert conn_container["c"].closed is True


# ---------------------------------------------------------------------------
# Route-wiring tests — assert /tracer is GET-only, requires task_id, and
# is wired to list_tracer_chain. Hermetic router introspection only.
# ---------------------------------------------------------------------------


def test_tracer_route_is_get_only_and_wired_to_helper():
    from app.routers import schedule as sched_router
    from fastapi.routing import APIRoute

    tracer_routes = [
        r for r in sched_router.router.routes
        if isinstance(r, APIRoute) and r.path.endswith("/tracer")
    ]
    assert tracer_routes, "expected a /tracer route under the schedule router"
    assert len(tracer_routes) == 1

    tracer = tracer_routes[0]
    assert tracer.methods == {"GET"}, (
        f"/tracer must be GET-only per UI-002f; found methods {tracer.methods}"
    )

    import inspect
    src = inspect.getsource(tracer.endpoint)
    assert "list_tracer_chain" in src, (
        "handler must delegate to list_tracer_chain, not a fresh query"
    )


def test_tracer_route_caps_max_depth_at_router_level():
    """The router-level Query(..., le=25) gate must match the helper's hard
    cap so clients get a clean validation error before the SQL runs.

    The gate lives in the endpoint's source literal because FastAPI's Query
    object stashes constraints in internal metadata the shape of which varies
    across Pydantic versions; source-level assertion is the stable surface.
    """
    from app.routers import schedule as sched_router
    from fastapi.routing import APIRoute
    import inspect

    tracer = next(
        r for r in sched_router.router.routes
        if isinstance(r, APIRoute) and r.path.endswith("/tracer")
    )
    src = inspect.getsource(tracer.endpoint)
    assert "max_depth" in src, "/tracer must expose a max_depth query param"
    assert "le=25" in src, (
        "/tracer max_depth must be capped at le=25 so the router rejects "
        "oversize depths before the SQL runs; source missing le=25"
    )
    assert "ge=1" in src, (
        "/tracer max_depth must be floored at ge=1 to prevent zero-depth requests"
    )


def test_schedule_router_still_has_no_write_verbs():
    """Regression guard: UI-002f must not introduce POST/PUT/PATCH/DELETE
    anywhere under /api/v1/schedule."""
    from app.routers import schedule as sched_router
    from fastapi.routing import APIRoute

    write_verbs = {"POST", "PUT", "PATCH", "DELETE"}
    for r in sched_router.router.routes:
        if not isinstance(r, APIRoute):
            continue
        assert not (r.methods & write_verbs), (
            f"UI-002f must not introduce write verbs; found {r.methods} on {r.path}"
        )
