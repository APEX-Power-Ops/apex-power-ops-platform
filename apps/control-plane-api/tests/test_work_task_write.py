"""
PM/Work Domain — Task Write API Tests
=======================================
Packet: 2026-04-14-pm-schema-014

These tests verify:
  1. POST /api/v1/work/tasks creates a task with valid intra-work FK
     references (work_package_id required, primary_wbs_node_id optional)
  2. POST rejects invalid work_package_id with 422 and field-level errors
  3. POST rejects invalid primary_wbs_node_id with 422
  4. POST rejects multiple invalid references with merged error dict
  5. POST rejects missing required fields with 422
  6. POST rejects empty title / empty task_code with 422
  7. POST rejects negative duration / labor hours with 422
  8. PATCH /api/v1/work/tasks/{id} updates with valid references
  9. PATCH rejects invalid intra-work references with 422
 10. PATCH returns 404 for non-existent task
 11. PATCH with empty body returns the unchanged task
 12. Read endpoints remain functional under the write-mock DB

Tests use a mock database session.  The mock simulates db.get() across
work (Task, WorkPackage, WBSNode) models to exercise the full
intra-work FK-validation surface.

Scope note: tasks have no direct org or identity FKs at this level —
those relationships are inherited transitively through the parent work
package.  Packet 014 therefore validates only work_package_id and
primary_wbs_node_id.
"""

import sys
import os
from unittest.mock import MagicMock
from uuid import uuid4, UUID

import pytest

# Ensure the app root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from config import get_db
from main import app


# ---------------------------------------------------------------------------
# Constants — well-known test UUIDs
# ---------------------------------------------------------------------------

VALID_WORK_PACKAGE_ID = UUID("88888888-0000-0000-0000-000000000001")
VALID_WBS_NODE_ID = UUID("44444444-0000-0000-0000-000000000001")

INVALID_WORK_PACKAGE_ID = UUID("ffffffff-0000-0000-0000-000000000099")
INVALID_WBS_NODE_ID = UUID("dddddddd-0000-0000-0000-000000000099")

EXISTING_TASK_ID = UUID("77777777-0000-0000-0000-000000000001")
NONEXISTENT_TASK_ID = UUID("00000000-0000-0000-0000-000000000099")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_mock_task(**overrides):
    """Create a mock Task ORM instance with all TaskRead fields populated."""
    from datetime import datetime, timezone
    defaults = {
        "task_id": EXISTING_TASK_ID,
        "work_package_id": VALID_WORK_PACKAGE_ID,
        "task_code": "TASK-EXISTING-001",
        "title": "Existing Task",
        "task_type": "task",
        "lifecycle_state": "not_started",
        "planned_start_at": None,
        "planned_end_at": None,
        "actual_start_at": None,
        "actual_end_at": None,
        "early_start_at": None,
        "early_end_at": None,
        "late_start_at": None,
        "late_end_at": None,
        "duration_hours": None,
        "remaining_duration_hours": None,
        "estimated_labor_hours": None,
        "actual_labor_hours": None,
        "total_float_hours": None,
        "schedule_priority_override": None,
        "primary_wbs_node_id": None,
        "p6_task_id": None,
        "p6_activity_id": None,
        "p6_calendar_id": None,
        "created_from_source": "manual",
        "provenance_status": "curated",
        "created_at": datetime(2026, 4, 14, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 4, 14, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _make_mock_work_package(pk):
    from datetime import datetime, timezone
    mock = MagicMock()
    mock.work_package_id = pk
    mock.work_package_code = "WP-TASK-PARENT"
    mock.title = "Parent Work Package"
    mock.created_at = datetime(2026, 4, 14, tzinfo=timezone.utc)
    mock.updated_at = datetime(2026, 4, 14, tzinfo=timezone.utc)
    return mock


def _make_mock_wbs_node(pk):
    mock = MagicMock()
    mock.wbs_node_id = pk
    mock.wbs_code = "WBS-1"
    mock.title = "WBS Node"
    return mock


def _mock_db_for_task_writes():
    """Mock DB supporting FK lookups across work models for task writes."""
    from models.work import Task, WorkPackage, WBSNode

    mock_db = MagicMock()
    created_task = [None]

    def mock_get(model_class, pk):
        if model_class is WorkPackage:
            if pk == VALID_WORK_PACKAGE_ID:
                return _make_mock_work_package(pk)
            return None
        if model_class is WBSNode:
            if pk == VALID_WBS_NODE_ID:
                return _make_mock_wbs_node(pk)
            return None
        if model_class is Task:
            if pk == EXISTING_TASK_ID:
                return _make_mock_task()
            return None
        return None

    mock_db.get = mock_get

    def mock_add(obj):
        created_task[0] = obj

    def mock_commit():
        from datetime import datetime, timezone
        if created_task[0] is not None:
            # Auto-populate server-managed fields on commit
            if (not hasattr(created_task[0], "task_id")
                    or created_task[0].task_id is None):
                created_task[0].task_id = uuid4()
            if (not hasattr(created_task[0], "created_at")
                    or created_task[0].created_at is None):
                created_task[0].created_at = datetime(
                    2026, 4, 14, tzinfo=timezone.utc
                )
            if (not hasattr(created_task[0], "updated_at")
                    or created_task[0].updated_at is None):
                created_task[0].updated_at = datetime(
                    2026, 4, 14, tzinfo=timezone.utc
                )
            if (not hasattr(created_task[0], "provenance_status")
                    or created_task[0].provenance_status is None):
                created_task[0].provenance_status = "curated"
            # Null out optional read fields that aren't set by the create path
            for attr in [
                "task_code", "planned_start_at", "planned_end_at",
                "actual_start_at", "actual_end_at",
                "early_start_at", "early_end_at",
                "late_start_at", "late_end_at",
                "duration_hours", "remaining_duration_hours",
                "estimated_labor_hours", "actual_labor_hours",
                "total_float_hours", "schedule_priority_override",
                "primary_wbs_node_id",
                "p6_task_id", "p6_activity_id", "p6_calendar_id",
            ]:
                if not hasattr(created_task[0], attr):
                    setattr(created_task[0], attr, None)

    def mock_refresh(obj):
        pass

    mock_db.add = mock_add
    mock_db.commit = mock_commit
    mock_db.refresh = mock_refresh

    # Read-path chain for list/filter queries
    mock_query = MagicMock()
    mock_query.options.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []
    mock_query.one_or_none.return_value = None
    mock_db.query.return_value = mock_query

    return mock_db


@pytest.fixture
def client_write():
    mock_db = _mock_db_for_task_writes()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Minimal valid create payload
# ---------------------------------------------------------------------------

VALID_TASK_CREATE_PAYLOAD = {
    "work_package_id": str(VALID_WORK_PACKAGE_ID),
    "title": "New Task",
}


# ---------------------------------------------------------------------------
# POST /api/v1/work/tasks
# ---------------------------------------------------------------------------

class TestCreateTask:
    """Tests for POST /api/v1/work/tasks."""

    def test_create_valid_task(self, client_write):
        resp = client_write.post(
            "/api/v1/work/tasks",
            json=VALID_TASK_CREATE_PAYLOAD,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "New Task"
        assert data["work_package_id"] == str(VALID_WORK_PACKAGE_ID)
        # Server-defaulted fields
        assert data["task_type"] == "task"
        assert data["lifecycle_state"] == "not_started"
        assert data["created_from_source"] == "manual"
        assert data["provenance_status"] == "curated"

    def test_create_with_optional_wbs_node(self, client_write):
        payload = {
            **VALID_TASK_CREATE_PAYLOAD,
            "primary_wbs_node_id": str(VALID_WBS_NODE_ID),
        }
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["primary_wbs_node_id"] == str(VALID_WBS_NODE_ID)

    def test_create_with_all_optional_fields(self, client_write):
        payload = {
            **VALID_TASK_CREATE_PAYLOAD,
            "task_code": "T-001",
            "task_type": "milestone",
            "lifecycle_state": "ready",
            "planned_start_at": "2026-05-01T08:00:00Z",
            "planned_end_at": "2026-05-01T17:00:00Z",
            "duration_hours": 8.0,
            "remaining_duration_hours": 8.0,
            "estimated_labor_hours": 16.0,
            "schedule_priority_override": "high",
            "primary_wbs_node_id": str(VALID_WBS_NODE_ID),
        }
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["task_code"] == "T-001"
        assert data["task_type"] == "milestone"
        assert data["lifecycle_state"] == "ready"
        assert data["schedule_priority_override"] == "high"

    def test_create_invalid_work_package_id(self, client_write):
        payload = {
            **VALID_TASK_CREATE_PAYLOAD,
            "work_package_id": str(INVALID_WORK_PACKAGE_ID),
        }
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "errors" in data
        assert "work_package_id" in data["errors"]

    def test_create_invalid_wbs_node_id(self, client_write):
        payload = {
            **VALID_TASK_CREATE_PAYLOAD,
            "primary_wbs_node_id": str(INVALID_WBS_NODE_ID),
        }
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "primary_wbs_node_id" in data["errors"]

    def test_create_multiple_invalid_refs_merged(self, client_write):
        payload = {
            **VALID_TASK_CREATE_PAYLOAD,
            "work_package_id": str(INVALID_WORK_PACKAGE_ID),
            "primary_wbs_node_id": str(INVALID_WBS_NODE_ID),
        }
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "work_package_id" in data["errors"]
        assert "primary_wbs_node_id" in data["errors"]

    def test_create_missing_required_fields(self, client_write):
        resp = client_write.post("/api/v1/work/tasks", json={})
        assert resp.status_code == 422

    def test_create_missing_work_package_id(self, client_write):
        payload = {k: v for k, v in VALID_TASK_CREATE_PAYLOAD.items()
                   if k != "work_package_id"}
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422

    def test_create_missing_title(self, client_write):
        payload = {k: v for k, v in VALID_TASK_CREATE_PAYLOAD.items()
                   if k != "title"}
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422

    def test_create_empty_title(self, client_write):
        payload = {**VALID_TASK_CREATE_PAYLOAD, "title": ""}
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422

    def test_create_empty_task_code(self, client_write):
        payload = {**VALID_TASK_CREATE_PAYLOAD, "task_code": ""}
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422

    def test_create_negative_duration_hours(self, client_write):
        payload = {**VALID_TASK_CREATE_PAYLOAD, "duration_hours": -1.0}
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422

    def test_create_negative_estimated_labor_hours(self, client_write):
        payload = {**VALID_TASK_CREATE_PAYLOAD, "estimated_labor_hours": -5.0}
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422

    def test_create_invalid_task_type(self, client_write):
        payload = {**VALID_TASK_CREATE_PAYLOAD, "task_type": "not_a_type"}
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422

    def test_create_invalid_lifecycle_state(self, client_write):
        payload = {**VALID_TASK_CREATE_PAYLOAD, "lifecycle_state": "bogus"}
        resp = client_write.post("/api/v1/work/tasks", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/v1/work/tasks/{task_id}
# ---------------------------------------------------------------------------

class TestUpdateTask:
    """Tests for PATCH /api/v1/work/tasks/{task_id}."""

    def test_update_title(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/tasks/{EXISTING_TASK_ID}",
            json={"title": "Updated Task Title"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == str(EXISTING_TASK_ID)
        assert data["title"] == "Updated Task Title"

    def test_update_with_valid_wbs_node(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/tasks/{EXISTING_TASK_ID}",
            json={"primary_wbs_node_id": str(VALID_WBS_NODE_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_valid_work_package(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/tasks/{EXISTING_TASK_ID}",
            json={"work_package_id": str(VALID_WORK_PACKAGE_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_invalid_work_package(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/tasks/{EXISTING_TASK_ID}",
            json={"work_package_id": str(INVALID_WORK_PACKAGE_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "work_package_id" in data["errors"]

    def test_update_with_invalid_wbs_node(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/tasks/{EXISTING_TASK_ID}",
            json={"primary_wbs_node_id": str(INVALID_WBS_NODE_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "primary_wbs_node_id" in data["errors"]

    def test_update_nonexistent_task(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/tasks/{NONEXISTENT_TASK_ID}",
            json={"title": "Nope"},
        )
        assert resp.status_code == 404

    def test_update_empty_body(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/tasks/{EXISTING_TASK_ID}",
            json={},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == str(EXISTING_TASK_ID)

    def test_update_lifecycle_transition(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/tasks/{EXISTING_TASK_ID}",
            json={"lifecycle_state": "active"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["lifecycle_state"] == "active"

    def test_update_negative_duration_rejected(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/tasks/{EXISTING_TASK_ID}",
            json={"duration_hours": -2.5},
        )
        assert resp.status_code == 422

    def test_update_negative_actual_labor_hours_rejected(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/tasks/{EXISTING_TASK_ID}",
            json={"actual_labor_hours": -10.0},
        )
        assert resp.status_code == 422

    def test_update_multiple_invalid_refs_merged(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/tasks/{EXISTING_TASK_ID}",
            json={
                "work_package_id": str(INVALID_WORK_PACKAGE_ID),
                "primary_wbs_node_id": str(INVALID_WBS_NODE_ID),
            },
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "work_package_id" in data["errors"]
        assert "primary_wbs_node_id" in data["errors"]


# ---------------------------------------------------------------------------
# Read endpoints still work (regression safety-net)
# ---------------------------------------------------------------------------

class TestReadEndpointsUnaffected:
    """Verify existing GET endpoints remain functional under the write-mock DB."""

    def test_list_tasks_still_works(self, client_write):
        resp = client_write.get("/api/v1/work/tasks")
        assert resp.status_code == 200

    def test_get_task_404_still_works(self, client_write):
        resp = client_write.get(f"/api/v1/work/tasks/{uuid4()}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Non-task PM mutation scope remains read-only
# ---------------------------------------------------------------------------

class TestReadOnlyBoundaryUnchanged:
    """Only WBS nodes remain read-only after packet 018.  Assignments
    POST/PATCH was opened by packet 015, dependencies POST/PATCH by
    packet 016, execution-issues POST/PATCH by packet 017, and
    progress-snapshots POST/PATCH by packet 018; those boundaries are
    no longer asserted here — see test_work_assignment_write.py,
    test_work_dependency_write.py, test_work_execution_issue_write.py,
    and test_work_progress_snapshot_write.py for those surfaces.
    """

    def test_wbs_nodes_post_still_405(self, client_write):
        resp = client_write.post("/api/v1/work/wbs-nodes", json={})
        assert resp.status_code == 405
