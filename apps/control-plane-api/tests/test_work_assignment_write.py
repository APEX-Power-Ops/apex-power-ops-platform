"""
PM/Work Domain — Assignment Write API Tests
============================================
Packet: 2026-04-15-pm-schema-015

These tests verify:
  1. POST /api/v1/work/assignments creates an assignment with valid
     intra-work FK references (at least one of work_package_id /
     task_id required by the AssignmentCreate Pydantic contract, both
     are optional identity FKs employee_id / crew_id)
  2. POST rejects invalid work_package_id with 422 and field-level errors
  3. POST rejects invalid task_id with 422
  4. POST rejects invalid employee_id with 422
  5. POST rejects invalid crew_id with 422
  6. POST rejects multiple invalid references with merged error dict
  7. POST rejects missing parent (neither work_package_id nor task_id)
     with 422 (Pydantic model_validator)
  8. POST rejects empty payload / invalid enum values with 422
  9. POST rejects negative planned_hours / actual_hours with 422
 10. PATCH /api/v1/work/assignments/{id} updates with valid references
 11. PATCH rejects invalid intra-work or identity FKs with 422
 12. PATCH returns 404 for non-existent assignment
 13. PATCH with empty body returns the unchanged assignment
 14. Read endpoints remain functional under the write-mock DB
 15. Non-assignment PM mutation scope remains read-only (dependencies,
     execution issues, progress snapshots still 405)

Tests use a mock database session.  The mock simulates db.get() across
work (Assignment, WorkPackage, Task) and identity (Employee, Crew)
models to exercise the full merged intra-work + identity FK-validation
surface.
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
VALID_TASK_ID = UUID("77777777-0000-0000-0000-000000000001")
VALID_EMPLOYEE_ID = UUID("aaaaaaaa-0000-0000-0000-000000000001")
VALID_CREW_ID = UUID("bbbbbbbb-0000-0000-0000-000000000001")

INVALID_WORK_PACKAGE_ID = UUID("ffffffff-0000-0000-0000-000000000099")
INVALID_TASK_ID = UUID("eeeeeeee-0000-0000-0000-000000000099")
INVALID_EMPLOYEE_ID = UUID("dddddddd-0000-0000-0000-000000000099")
INVALID_CREW_ID = UUID("cccccccc-0000-0000-0000-000000000099")

EXISTING_ASSIGNMENT_ID = UUID("99999999-0000-0000-0000-000000000001")
NONEXISTENT_ASSIGNMENT_ID = UUID("00000000-0000-0000-0000-000000000099")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_mock_assignment(**overrides):
    """Create a mock Assignment ORM instance with all AssignmentRead fields populated."""
    from datetime import datetime, timezone
    defaults = {
        "assignment_id": EXISTING_ASSIGNMENT_ID,
        "work_package_id": VALID_WORK_PACKAGE_ID,
        "task_id": None,
        "employee_id": None,
        "crew_id": VALID_CREW_ID,
        "employee_name": None,
        "crew_name": None,
        "assignment_role": "primary",
        "planned_hours": None,
        "actual_hours": None,
        "start_at": None,
        "end_at": None,
        "p6_task_resource_id": None,
        "p6_resource_id": None,
        "is_actual_participation": False,
        "created_from_source": "manual",
        "created_at": datetime(2026, 4, 15, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 4, 15, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _make_mock_work_package(pk):
    mock = MagicMock()
    mock.work_package_id = pk
    mock.title = "Parent Work Package"
    return mock


def _make_mock_task(pk):
    mock = MagicMock()
    mock.task_id = pk
    mock.title = "Parent Task"
    return mock


def _make_mock_employee(pk):
    mock = MagicMock()
    mock.employee_id = pk
    mock.name = "Test Employee"
    return mock


def _make_mock_crew(pk):
    mock = MagicMock()
    mock.crew_id = pk
    mock.name = "Test Crew"
    return mock


def _mock_db_for_assignment_writes():
    """Mock DB supporting FK lookups across work + identity models."""
    from models.work import Assignment, WorkPackage, Task
    from models.identity import Employee, Crew

    mock_db = MagicMock()
    created_assignment = [None]

    def mock_get(model_class, pk):
        if model_class is WorkPackage:
            if pk == VALID_WORK_PACKAGE_ID:
                return _make_mock_work_package(pk)
            return None
        if model_class is Task:
            if pk == VALID_TASK_ID:
                return _make_mock_task(pk)
            return None
        if model_class is Employee:
            if pk == VALID_EMPLOYEE_ID:
                return _make_mock_employee(pk)
            return None
        if model_class is Crew:
            if pk == VALID_CREW_ID:
                return _make_mock_crew(pk)
            return None
        if model_class is Assignment:
            if pk == EXISTING_ASSIGNMENT_ID:
                return _make_mock_assignment()
            return None
        return None

    mock_db.get = mock_get

    def mock_add(obj):
        created_assignment[0] = obj

    def mock_commit():
        from datetime import datetime, timezone
        if created_assignment[0] is not None:
            # Auto-populate server-managed fields on commit
            if (not hasattr(created_assignment[0], "assignment_id")
                    or created_assignment[0].assignment_id is None):
                created_assignment[0].assignment_id = uuid4()
            if (not hasattr(created_assignment[0], "created_at")
                    or created_assignment[0].created_at is None):
                created_assignment[0].created_at = datetime(
                    2026, 4, 15, tzinfo=timezone.utc
                )
            if (not hasattr(created_assignment[0], "updated_at")
                    or created_assignment[0].updated_at is None):
                created_assignment[0].updated_at = datetime(
                    2026, 4, 15, tzinfo=timezone.utc
                )
            # Null out optional read fields that aren't set by the create path
            for attr in [
                "employee_name", "crew_name",
                "p6_task_resource_id", "p6_resource_id",
            ]:
                if not hasattr(created_assignment[0], attr):
                    setattr(created_assignment[0], attr, None)

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
    mock_db = _mock_db_for_assignment_writes()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Minimal valid create payloads
# ---------------------------------------------------------------------------

# Work-package-anchored assignment (most common)
VALID_WP_ASSIGNMENT_PAYLOAD = {
    "work_package_id": str(VALID_WORK_PACKAGE_ID),
    "crew_id": str(VALID_CREW_ID),
}

# Task-anchored assignment
VALID_TASK_ASSIGNMENT_PAYLOAD = {
    "task_id": str(VALID_TASK_ID),
    "employee_id": str(VALID_EMPLOYEE_ID),
}


# ---------------------------------------------------------------------------
# POST /api/v1/work/assignments
# ---------------------------------------------------------------------------

class TestCreateAssignment:
    """Tests for POST /api/v1/work/assignments."""

    def test_create_valid_wp_assignment(self, client_write):
        resp = client_write.post(
            "/api/v1/work/assignments",
            json=VALID_WP_ASSIGNMENT_PAYLOAD,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["work_package_id"] == str(VALID_WORK_PACKAGE_ID)
        assert data["crew_id"] == str(VALID_CREW_ID)
        # Server-defaulted fields
        assert data["assignment_role"] == "primary"
        assert data["is_actual_participation"] is False
        assert data["created_from_source"] == "manual"

    def test_create_valid_task_assignment(self, client_write):
        resp = client_write.post(
            "/api/v1/work/assignments",
            json=VALID_TASK_ASSIGNMENT_PAYLOAD,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["task_id"] == str(VALID_TASK_ID)
        assert data["employee_id"] == str(VALID_EMPLOYEE_ID)

    def test_create_with_both_parents(self, client_write):
        """Supplying both work_package_id and task_id is permitted by the
        DDL constraint (which only requires at least one)."""
        payload = {
            "work_package_id": str(VALID_WORK_PACKAGE_ID),
            "task_id": str(VALID_TASK_ID),
            "employee_id": str(VALID_EMPLOYEE_ID),
        }
        resp = client_write.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 201

    def test_create_with_all_optional_fields(self, client_write):
        payload = {
            **VALID_WP_ASSIGNMENT_PAYLOAD,
            "employee_id": str(VALID_EMPLOYEE_ID),
            "assignment_role": "lead",
            "planned_hours": 16.0,
            "actual_hours": 14.5,
            "start_at": "2026-05-01T08:00:00Z",
            "end_at": "2026-05-01T17:00:00Z",
            "is_actual_participation": True,
        }
        resp = client_write.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["assignment_role"] == "lead"
        assert data["is_actual_participation"] is True

    def test_create_rejects_missing_both_parents(self, client_write):
        """AssignmentCreate model_validator requires at least one of
        work_package_id / task_id.  Pydantic raises 422 before the
        request reaches the mutation service."""
        payload = {"employee_id": str(VALID_EMPLOYEE_ID)}
        resp = client_write.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422

    def test_create_rejects_empty_payload(self, client_write):
        resp = client_write.post("/api/v1/work/assignments", json={})
        assert resp.status_code == 422

    def test_create_invalid_work_package_id(self, client_write):
        payload = {
            "work_package_id": str(INVALID_WORK_PACKAGE_ID),
            "crew_id": str(VALID_CREW_ID),
        }
        resp = client_write.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "errors" in data
        assert "work_package_id" in data["errors"]

    def test_create_invalid_task_id(self, client_write):
        payload = {
            "task_id": str(INVALID_TASK_ID),
            "employee_id": str(VALID_EMPLOYEE_ID),
        }
        resp = client_write.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "task_id" in data["errors"]

    def test_create_invalid_employee_id(self, client_write):
        payload = {
            "work_package_id": str(VALID_WORK_PACKAGE_ID),
            "employee_id": str(INVALID_EMPLOYEE_ID),
        }
        resp = client_write.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "employee_id" in data["errors"]

    def test_create_invalid_crew_id(self, client_write):
        payload = {
            "work_package_id": str(VALID_WORK_PACKAGE_ID),
            "crew_id": str(INVALID_CREW_ID),
        }
        resp = client_write.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "crew_id" in data["errors"]

    def test_create_multiple_invalid_refs_merged(self, client_write):
        """All four FKs invalid → merged 422 with all four field names."""
        payload = {
            "work_package_id": str(INVALID_WORK_PACKAGE_ID),
            "task_id": str(INVALID_TASK_ID),
            "employee_id": str(INVALID_EMPLOYEE_ID),
            "crew_id": str(INVALID_CREW_ID),
        }
        resp = client_write.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "work_package_id" in data["errors"]
        assert "task_id" in data["errors"]
        assert "employee_id" in data["errors"]
        assert "crew_id" in data["errors"]

    def test_create_invalid_assignment_role(self, client_write):
        payload = {**VALID_WP_ASSIGNMENT_PAYLOAD, "assignment_role": "not_a_role"}
        resp = client_write.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422

    def test_create_negative_planned_hours(self, client_write):
        payload = {**VALID_WP_ASSIGNMENT_PAYLOAD, "planned_hours": -1.0}
        resp = client_write.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422

    def test_create_negative_actual_hours(self, client_write):
        payload = {**VALID_WP_ASSIGNMENT_PAYLOAD, "actual_hours": -5.0}
        resp = client_write.post("/api/v1/work/assignments", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/v1/work/assignments/{assignment_id}
# ---------------------------------------------------------------------------

class TestUpdateAssignment:
    """Tests for PATCH /api/v1/work/assignments/{assignment_id}."""

    def test_update_assignment_role(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{EXISTING_ASSIGNMENT_ID}",
            json={"assignment_role": "lead"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["assignment_id"] == str(EXISTING_ASSIGNMENT_ID)
        assert data["assignment_role"] == "lead"

    def test_update_with_valid_task_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{EXISTING_ASSIGNMENT_ID}",
            json={"task_id": str(VALID_TASK_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_valid_employee_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{EXISTING_ASSIGNMENT_ID}",
            json={"employee_id": str(VALID_EMPLOYEE_ID)},
        )
        assert resp.status_code == 200

    def test_update_hours_and_participation(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{EXISTING_ASSIGNMENT_ID}",
            json={
                "planned_hours": 24.0,
                "actual_hours": 22.5,
                "is_actual_participation": True,
            },
        )
        assert resp.status_code == 200

    def test_update_with_invalid_work_package(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{EXISTING_ASSIGNMENT_ID}",
            json={"work_package_id": str(INVALID_WORK_PACKAGE_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "work_package_id" in data["errors"]

    def test_update_with_invalid_task_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{EXISTING_ASSIGNMENT_ID}",
            json={"task_id": str(INVALID_TASK_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "task_id" in data["errors"]

    def test_update_with_invalid_employee_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{EXISTING_ASSIGNMENT_ID}",
            json={"employee_id": str(INVALID_EMPLOYEE_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "employee_id" in data["errors"]

    def test_update_with_invalid_crew_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{EXISTING_ASSIGNMENT_ID}",
            json={"crew_id": str(INVALID_CREW_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "crew_id" in data["errors"]

    def test_update_multiple_invalid_refs_merged(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{EXISTING_ASSIGNMENT_ID}",
            json={
                "work_package_id": str(INVALID_WORK_PACKAGE_ID),
                "task_id": str(INVALID_TASK_ID),
                "employee_id": str(INVALID_EMPLOYEE_ID),
                "crew_id": str(INVALID_CREW_ID),
            },
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "work_package_id" in data["errors"]
        assert "task_id" in data["errors"]
        assert "employee_id" in data["errors"]
        assert "crew_id" in data["errors"]

    def test_update_nonexistent_assignment(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{NONEXISTENT_ASSIGNMENT_ID}",
            json={"assignment_role": "lead"},
        )
        assert resp.status_code == 404

    def test_update_empty_body(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{EXISTING_ASSIGNMENT_ID}",
            json={},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["assignment_id"] == str(EXISTING_ASSIGNMENT_ID)

    def test_update_negative_planned_hours_rejected(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{EXISTING_ASSIGNMENT_ID}",
            json={"planned_hours": -2.5},
        )
        assert resp.status_code == 422

    def test_update_negative_actual_hours_rejected(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/assignments/{EXISTING_ASSIGNMENT_ID}",
            json={"actual_hours": -10.0},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Read endpoints still work (regression safety-net)
# ---------------------------------------------------------------------------

class TestReadEndpointsUnaffected:
    """Verify existing GET endpoints remain functional under the write-mock DB."""

    def test_list_assignments_still_works(self, client_write):
        resp = client_write.get("/api/v1/work/assignments")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Non-assignment PM mutation scope remains read-only
# ---------------------------------------------------------------------------

class TestReadOnlyBoundaryUnchanged:
    """Only WBS nodes remain read-only after packet 018.  Dependencies
    POST/PATCH was opened by packet 016, execution-issues POST/PATCH by
    packet 017, and progress-snapshots POST/PATCH by packet 018; those
    boundaries are no longer asserted here — see
    test_work_dependency_write.py, test_work_execution_issue_write.py,
    and test_work_progress_snapshot_write.py for those surfaces.
    """

    def test_wbs_nodes_post_still_405(self, client_write):
        resp = client_write.post("/api/v1/work/wbs-nodes", json={})
        assert resp.status_code == 405
