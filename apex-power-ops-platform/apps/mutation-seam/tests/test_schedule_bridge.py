"""
Tests for the packet UI-002a schedule-context read bridge.

These tests run in the sandbox and therefore cannot reach the host Postgres.
They patch the `app.schedule.queries` helpers so the router contract can be
exercised end-to-end without a live database. A separate host-side runner
(`apps/mutation-seam/run_schedule_bootstrap.py`) performs the persisted-mode
validation.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "schedule"
    / "fixtures"
    / "stack_data_center.json"
)


@pytest.fixture
def fixture_payload():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def auth_header(field_tech_token):
    # Reuse the existing field_tech_token fixture from conftest.
    return {"Authorization": field_tech_token}


# ---------------------------------------------------------------------------
# Router contract tests — every query helper is patched so no DB is touched.
# ---------------------------------------------------------------------------

def test_list_projects_returns_fixture_shape(client, auth_header, fixture_payload):
    with patch("app.routers.schedule.sched_q.list_projects",
               return_value=fixture_payload["projects"]):
        r = client.get("/api/v1/schedule/projects", headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) == 1
    assert data[0]["id"] == "sched-proj-001"
    assert data[0]["scope_project_id"] == "proj-001"


def test_get_project_404_when_missing(client, auth_header):
    with patch("app.routers.schedule.sched_q.get_project", return_value=None):
        r = client.get("/api/v1/schedule/projects/does-not-exist", headers=auth_header)
    assert r.status_code == 404
    assert r.json()["detail"] == "schedule_project_not_found"


def test_get_project_returns_single(client, auth_header, fixture_payload):
    p = fixture_payload["projects"][0]
    with patch("app.routers.schedule.sched_q.get_project", return_value=p):
        r = client.get(f"/api/v1/schedule/projects/{p['id']}", headers=auth_header)
    assert r.status_code == 200
    assert r.json()["p6_project_id"] == p["p6_project_id"]


def test_list_wbs_returns_hierarchy(client, auth_header, fixture_payload):
    with patch("app.routers.schedule.sched_q.list_wbs",
               return_value=fixture_payload["wbs_nodes"]):
        r = client.get("/api/v1/schedule/projects/sched-proj-001/wbs",
                       headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    # Root has no parent; children point at the root
    roots = [w for w in data if w["parent_wbs_id"] is None]
    children = [w for w in data if w["parent_wbs_id"] == "sched-wbs-root"]
    assert len(roots) == 1
    assert len(children) == 2


def test_list_tasks_filters_critical_only(client, auth_header, fixture_payload):
    crit = [t for t in fixture_payload["tasks"] if t["critical_flag"]]
    with patch("app.routers.schedule.sched_q.list_tasks", return_value=crit):
        r = client.get("/api/v1/schedule/tasks?critical_only=true",
                       headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert all(t["critical_flag"] for t in data)
    # Fixture has 2 critical tasks (sched-task-002, sched-task-004)
    assert {t["id"] for t in data} == {"sched-task-002", "sched-task-004"}


def test_list_relationships_filters_by_task(client, auth_header, fixture_payload):
    rels = [r for r in fixture_payload["relationships"]
            if r["predecessor_task_id"] == "sched-task-001"
            or r["successor_task_id"] == "sched-task-001"]
    with patch("app.routers.schedule.sched_q.list_relationships", return_value=rels):
        r = client.get("/api/v1/schedule/relationships?task_id=sched-task-001",
                       headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["rel_type"] == "FS"
    assert data[0]["lag_hours"] == 8


def test_bridge_returns_503_when_dsn_missing(client, auth_header):
    with patch("app.routers.schedule.sched_q.list_projects",
               side_effect=RuntimeError("SEAM_DATABASE_URL is not set")):
        r = client.get("/api/v1/schedule/projects", headers=auth_header)
    assert r.status_code == 503
    assert "SEAM_DATABASE_URL" in r.json()["detail"]


def test_list_tasks_surfaces_baseline_fields_when_present(client, auth_header):
    """UI-002d: the GET /tasks response must carry baseline_* fields when the
    underlying row has them. NULL baseline stays NULL in the response — the
    router MUST NOT fabricate."""
    payload = [
        {
            "id": "sched-task-001", "task_name": "MV SWGR V+M",
            "planned_start":   "2026-04-20T07:00:00Z",
            "planned_finish":  "2026-04-24T17:00:00Z",
            "baseline_start_at": "2026-04-20T07:00:00Z",
            "baseline_end_at":   "2026-04-24T17:00:00Z",
            "baseline_name": "Original Baseline (SDCX 2026 Kickoff)",
            "baseline_source": "p6_import",
            "baselined_at": "2026-03-01T00:00:00Z",
            "baseline_event_id": "blev-fixture-original",
            "critical_flag": False,
        },
        {
            # Task whose baseline has not been captured — baseline fields null.
            "id": "sched-task-999", "task_name": "Late-arrival",
            "planned_start":  "2026-06-01T07:00:00Z",
            "planned_finish": "2026-06-04T17:00:00Z",
            "baseline_start_at": None,
            "baseline_end_at":   None,
            "baseline_name":     None,
            "baseline_source":   None,
            "baselined_at":      None,
            "baseline_event_id": None,
            "critical_flag": False,
        },
    ]
    with patch("app.routers.schedule.sched_q.list_tasks", return_value=payload):
        r = client.get("/api/v1/schedule/tasks", headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    # First row surfaces baseline
    assert data[0]["baseline_source"] == "p6_import"
    assert data[0]["baseline_event_id"] == "blev-fixture-original"
    assert data[0]["baseline_name"].startswith("Original Baseline")
    # Second row has no baseline — fields must remain null
    assert data[1]["baseline_start_at"] is None
    assert data[1]["baseline_end_at"] is None
    assert data[1]["baseline_source"] is None
    assert data[1]["baseline_event_id"] is None


def test_list_tasks_with_scope_carries_baseline_alongside_seam_status(client, auth_header):
    """UI-002d: the LEFT-joined view must preserve baseline fields + still
    tolerate a null seam match simultaneously."""
    payload = [
        {
            "schedule_task_id": "sched-task-001",
            "task_code": "A1010",
            "task_name": "MV SWGR V+M",
            "planned_start":  "2026-04-20T07:00:00Z",
            "planned_finish": "2026-04-24T17:00:00Z",
            "baseline_start_at": "2026-04-20T07:00:00Z",
            "baseline_end_at":   "2026-04-24T17:00:00Z",
            "baseline_name": "Original",
            "baseline_source": "p6_import",
            "baselined_at": "2026-03-01T00:00:00Z",
            "baseline_event_id": "blev-fixture-original",
            "critical_flag": False,
            "seam_status": "not_started",   # present
            "seam_workpackage_id": "wp-001",
        },
        {
            "schedule_task_id": "sched-task-unscoped",
            "task_code": "A9999",
            "task_name": "Unscoped baseline",
            "planned_start":  "2026-07-01T07:00:00Z",
            "planned_finish": "2026-07-04T17:00:00Z",
            "baseline_start_at": "2026-07-01T07:00:00Z",
            "baseline_end_at":   "2026-07-04T17:00:00Z",
            "baseline_name": "Original",
            "baseline_source": "p6_import",
            "baselined_at": "2026-03-01T00:00:00Z",
            "baseline_event_id": "blev-fixture-original",
            "critical_flag": False,
            "seam_status": None,            # absent — LEFT join behavior preserved
            "seam_workpackage_id": None,
        },
    ]
    with patch("app.routers.schedule.sched_q.list_tasks_with_scope", return_value=payload):
        r = client.get("/api/v1/schedule/tasks-with-scope?project_id=sched-proj-001",
                       headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    # Baseline fields flow through even when the seam join doesn't.
    for row in data:
        assert row["baseline_source"] == "p6_import"
        assert row["baseline_event_id"] == "blev-fixture-original"
    # LEFT join semantics for seam still preserved.
    assert data[0]["seam_status"] == "not_started"
    assert data[1]["seam_status"] is None


def test_tasks_with_scope_is_left_join_shape(client, auth_header):
    """The joined read must tolerate a NULL seam match (LEFT join)."""
    payload = [
        {
            "schedule_task_id":     "sched-task-001",
            "p6_task_id":           "SDCX-2026.T1010",
            "task_code":            "A1010",
            "task_name":            "MV SWGR Visual+Mech",
            "schedule_project_id":  "sched-proj-001",
            "schedule_wbs_id":      "sched-wbs-001",
            "scope_id":             "task-001",
            "schedule_apex_status": "not_started",
            "planned_start":        "2026-04-20T07:00:00Z",
            "planned_finish":       "2026-04-24T17:00:00Z",
            "total_float_hours":    16,
            "critical_flag":        False,
            "seam_status":          "not_started",
            "seam_workpackage_id":  "wp-001",
        },
        {
            # A schedule task whose scope_id doesn't resolve — seam columns must be null
            "schedule_task_id":     "sched-task-999",
            "p6_task_id":           "SDCX-2026.T9999",
            "task_code":            "A9999",
            "task_name":            "Unresolved seam match",
            "schedule_project_id":  "sched-proj-001",
            "schedule_wbs_id":      None,
            "scope_id":             "task-missing",
            "schedule_apex_status": "not_started",
            "planned_start":        None,
            "planned_finish":       None,
            "total_float_hours":    None,
            "critical_flag":        False,
            "seam_status":          None,
            "seam_workpackage_id":  None,
        },
    ]
    with patch("app.routers.schedule.sched_q.list_tasks_with_scope", return_value=payload):
        r = client.get("/api/v1/schedule/tasks-with-scope?project_id=sched-proj-001",
                       headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[1]["seam_status"] is None
    assert data[1]["seam_workpackage_id"] is None


# ---------------------------------------------------------------------------
# Read-only posture tests — assert the router surface does not expose writes.
# ---------------------------------------------------------------------------

def test_schedule_router_is_get_only():
    """No POST, PUT, PATCH, or DELETE endpoints should exist under /api/v1/schedule."""
    from app.main import app

    sched_routes = [r for r in app.routes
                    if getattr(r, "path", "").startswith("/api/v1/schedule")]
    assert sched_routes, "schedule router has no routes mounted"
    for r in sched_routes:
        disallowed = r.methods - {"GET", "HEAD"}
        assert not disallowed, f"{r.path} exposes non-GET methods: {disallowed}"


def test_post_against_schedule_endpoint_is_405(client, auth_header):
    """A POST attempt against any schedule endpoint must return 405 Method Not Allowed."""
    r = client.post("/api/v1/schedule/projects",
                    json={"id": "sched-proj-999", "name": "x"},
                    headers=auth_header)
    assert r.status_code == 405


# ---------------------------------------------------------------------------
# Loader tests — dry-run only (no DB).
# ---------------------------------------------------------------------------

def test_loader_dry_run_against_fixture():
    from app.schedule.loader import run_load
    result = run_load(dry_run=True)
    assert result["dry_run"] is True
    assert result["source_type"] == "json-fixture"
    assert result["source_file"] == "stack_data_center.json"
    # Core UI-002a counts. Later packets (e.g., 020c added `baseline_events`)
    # are allowed to extend this stats shape with additional keys.
    stats = result["stats"]
    assert stats["projects"] == 1
    assert stats["wbs_nodes"] == 3
    assert stats["tasks"] == 4
    assert stats["relationships"] == 3


def test_loader_translates_xer_status():
    from app.schedule.loader import translate_xer_status
    assert translate_xer_status("TK_NotStart") == "not_started"
    assert translate_xer_status("TK_Active")   == "active"
    assert translate_xer_status("TK_Complete") == "complete"
    assert translate_xer_status(None)          is None
    assert translate_xer_status("TK_Unknown")  is None


# ---------------------------------------------------------------------------
# Fixture integrity — guards against future edits to stack_data_center.json
# that would silently break the bridge's shape expectations.
# ---------------------------------------------------------------------------

def test_fixture_invariants(fixture_payload):
    projects  = {p["id"] for p in fixture_payload["projects"]}
    wbs_ids   = {w["id"] for w in fixture_payload["wbs_nodes"]}
    tasks_ids = {t["id"] for t in fixture_payload["tasks"]}
    for w in fixture_payload["wbs_nodes"]:
        assert w["schedule_project_id"] in projects
        if w["parent_wbs_id"] is not None:
            assert w["parent_wbs_id"] in wbs_ids
    for t in fixture_payload["tasks"]:
        assert t["schedule_project_id"] in projects
        if t["schedule_wbs_id"] is not None:
            assert t["schedule_wbs_id"] in wbs_ids
    for rel in fixture_payload["relationships"]:
        assert rel["predecessor_task_id"] in tasks_ids
        assert rel["successor_task_id"]   in tasks_ids
        assert rel["rel_type"] in {"FS", "SS", "FF", "SF"}
