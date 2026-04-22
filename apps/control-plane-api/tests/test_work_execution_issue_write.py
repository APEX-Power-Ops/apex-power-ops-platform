"""
PM/Work Domain — Execution-Issue Write API Tests
=================================================
Packet: 2026-04-15-pm-schema-017

These tests verify:
  1. POST /api/v1/work/execution-issues creates an execution-issue with
     a valid work_package_id parent (task_id null)
  2. POST creates with a valid task_id parent (work_package_id null)
  3. POST creates with both FKs set to valid values
  4. POST accepts each IssueType enum value
  5. POST accepts each Severity enum value
  6. POST accepts each IssueStatus enum value
  7. POST accepts a full payload with every optional field populated,
     including resolution_type + resolved_at + closed_at + assigned_to
     + reported_by + blocks_completion
  8. POST rejects empty payload with 422
  9. POST rejects missing issue_type with 422
 10. POST rejects missing severity with 422
 11. POST rejects missing summary with 422
 12. POST rejects empty string summary (min_length=1) with 422
 13. POST rejects invalid enum values (issue_type, severity, status,
     resolution_type, created_from_source) with 422
 14. POST rejects at-least-one-parent violation (both work_package_id
     and task_id null) at the Pydantic model_validator layer — mirrors
     the DDL ``ck_execution_issues_at_least_one_parent`` check
     constraint — before any db.get() round-trip
 15. POST rejects invalid work_package_id with 422 and a field-level
     error keyed ``work_package_id``
 16. POST rejects invalid task_id with 422 and a field-level error
     keyed ``task_id``
 17. POST rejects both FKs invalid with a merged error dict containing
     both field names
 18. PATCH /api/v1/work/execution-issues/{id} updates status
 19. PATCH updates severity, resolution_type, blocks_completion
 20. PATCH updates resolved_at, closed_at, assigned_to
 21. PATCH updates summary and details
 22. PATCH with a valid FK patch on one side only is accepted
 23. PATCH rejects invalid work_package_id and task_id individually
 24. PATCH rejects both FKs invalid with merged error dict
 25. PATCH returns 404 for non-existent execution_issue_id
 26. PATCH with empty body returns the unchanged execution-issue
 27. PATCH rejects invalid enum values
 28. Read endpoints remain functional under the write-mock DB
 29. Non-execution-issue mutation scope remains read-only (progress
     snapshots and WBS nodes still 405); POST/PATCH for projects, work
     packages, tasks, assignments, and dependencies remain open from
     earlier packets and are not re-asserted here.

Tests use a mock database session.  The mock simulates db.get() across
work.WorkPackage, work.Task, and work.ExecutionIssue to exercise the
merged two-FK validation surface and the at-least-one-parent Pydantic
guard.
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

VALID_WORK_PACKAGE_ID = UUID("88888888-1111-0000-0000-000000000001")
VALID_TASK_ID = UUID("88888888-2222-0000-0000-000000000002")
VALID_OTHER_WORK_PACKAGE_ID = UUID("88888888-3333-0000-0000-000000000003")
VALID_OTHER_TASK_ID = UUID("88888888-4444-0000-0000-000000000004")

INVALID_WORK_PACKAGE_ID = UUID("eeeeeeee-1111-0000-0000-000000000099")
INVALID_TASK_ID = UUID("eeeeeeee-2222-0000-0000-000000000099")

EXISTING_EXECUTION_ISSUE_ID = UUID("aaaaaaaa-0000-0000-0000-000000000001")
NONEXISTENT_EXECUTION_ISSUE_ID = UUID("00000000-0000-0000-0000-000000000099")

# Sentinel identity refs used as passthrough values on the write path —
# these are not validated against identity by packet 017 (the minimal
# lane keeps reported_by / assigned_to FK validation out of scope)
SENTINEL_REPORTED_BY = UUID("88888888-aaaa-0000-0000-00000000000a")
SENTINEL_ASSIGNED_TO = UUID("88888888-bbbb-0000-0000-00000000000b")
SENTINEL_APPARATUS_REF = UUID("88888888-cccc-0000-0000-00000000000c")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_mock_execution_issue(**overrides):
    """Create a mock ExecutionIssue ORM instance with all
    ExecutionIssueRead fields populated."""
    from datetime import datetime, timezone
    defaults = {
        "execution_issue_id": EXISTING_EXECUTION_ISSUE_ID,
        "work_package_id": VALID_WORK_PACKAGE_ID,
        "task_id": None,
        "apparatus_ref": None,
        "issue_type": "equipment_not_ready",
        "severity": "major",
        "status": "open",
        "blocks_completion": False,
        "summary": "Mock execution issue",
        "details": None,
        "reported_by": None,
        "assigned_to": None,
        "reported_by_name": None,
        "assigned_to_name": None,
        "resolution_type": None,
        "opened_at": datetime(2026, 4, 15, tzinfo=timezone.utc),
        "resolved_at": None,
        "closed_at": None,
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


def _mock_db_for_execution_issue_writes():
    """Mock DB supporting FK lookups across work.WorkPackage, work.Task,
    and work.ExecutionIssue."""
    from models.work import ExecutionIssue, Task, WorkPackage

    mock_db = MagicMock()
    created_issue = [None]

    def mock_get(model_class, pk):
        if model_class is WorkPackage:
            if pk in (VALID_WORK_PACKAGE_ID, VALID_OTHER_WORK_PACKAGE_ID):
                return _make_mock_work_package(pk)
            return None
        if model_class is Task:
            if pk in (VALID_TASK_ID, VALID_OTHER_TASK_ID):
                return _make_mock_task(pk)
            return None
        if model_class is ExecutionIssue:
            if pk == EXISTING_EXECUTION_ISSUE_ID:
                return _make_mock_execution_issue()
            return None
        return None

    mock_db.get = mock_get

    def mock_add(obj):
        created_issue[0] = obj

    def mock_commit():
        from datetime import datetime, timezone
        if created_issue[0] is not None:
            # Auto-populate server-managed fields on commit
            if (not hasattr(created_issue[0], "execution_issue_id")
                    or created_issue[0].execution_issue_id is None):
                created_issue[0].execution_issue_id = uuid4()
            if (not hasattr(created_issue[0], "opened_at")
                    or created_issue[0].opened_at is None):
                created_issue[0].opened_at = datetime(
                    2026, 4, 15, tzinfo=timezone.utc
                )
            if (not hasattr(created_issue[0], "created_at")
                    or created_issue[0].created_at is None):
                created_issue[0].created_at = datetime(
                    2026, 4, 15, tzinfo=timezone.utc
                )
            if (not hasattr(created_issue[0], "updated_at")
                    or created_issue[0].updated_at is None):
                created_issue[0].updated_at = datetime(
                    2026, 4, 15, tzinfo=timezone.utc
                )

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
    mock_db = _mock_db_for_execution_issue_writes()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Minimal valid create payload
# ---------------------------------------------------------------------------

VALID_ISSUE_PAYLOAD_WP = {
    "work_package_id": str(VALID_WORK_PACKAGE_ID),
    "issue_type": "equipment_not_ready",
    "severity": "major",
    "summary": "Pump pre-test ground grid missing",
}


VALID_ISSUE_PAYLOAD_TASK = {
    "task_id": str(VALID_TASK_ID),
    "issue_type": "test_failure",
    "severity": "critical",
    "summary": "Hi-pot test failed on phase A",
}


# ---------------------------------------------------------------------------
# POST /api/v1/work/execution-issues
# ---------------------------------------------------------------------------

class TestCreateExecutionIssue:
    """Tests for POST /api/v1/work/execution-issues."""

    def test_create_with_work_package_parent_only(self, client_write):
        resp = client_write.post(
            "/api/v1/work/execution-issues",
            json=VALID_ISSUE_PAYLOAD_WP,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["work_package_id"] == str(VALID_WORK_PACKAGE_ID)
        assert data["task_id"] is None
        assert data["issue_type"] == "equipment_not_ready"
        assert data["severity"] == "major"
        assert data["status"] == "open"
        assert data["blocks_completion"] is False
        assert data["summary"] == "Pump pre-test ground grid missing"
        assert data["created_from_source"] == "manual"

    def test_create_with_task_parent_only(self, client_write):
        resp = client_write.post(
            "/api/v1/work/execution-issues",
            json=VALID_ISSUE_PAYLOAD_TASK,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["work_package_id"] is None
        assert data["task_id"] == str(VALID_TASK_ID)
        assert data["severity"] == "critical"

    def test_create_with_both_parents(self, client_write):
        payload = {
            "work_package_id": str(VALID_WORK_PACKAGE_ID),
            "task_id": str(VALID_TASK_ID),
            "issue_type": "safety_hold",
            "severity": "critical",
            "summary": "LOTO not verified",
        }
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["work_package_id"] == str(VALID_WORK_PACKAGE_ID)
        assert data["task_id"] == str(VALID_TASK_ID)

    @pytest.mark.parametrize(
        "issue_type",
        [
            "equipment_not_ready",
            "test_failure",
            "settings_incorrect",
            "access_blocked",
            "safety_hold",
            "material_missing",
            "documentation_gap",
            "other",
        ],
    )
    def test_create_accepts_all_issue_types(self, client_write, issue_type):
        payload = {**VALID_ISSUE_PAYLOAD_WP, "issue_type": issue_type}
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 201
        assert resp.json()["issue_type"] == issue_type

    @pytest.mark.parametrize(
        "severity", ["critical", "major", "minor", "info"],
    )
    def test_create_accepts_all_severities(self, client_write, severity):
        payload = {**VALID_ISSUE_PAYLOAD_WP, "severity": severity}
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 201
        assert resp.json()["severity"] == severity

    @pytest.mark.parametrize(
        "status", ["open", "in_review", "escalated", "resolved", "closed"],
    )
    def test_create_accepts_all_statuses(self, client_write, status):
        payload = {**VALID_ISSUE_PAYLOAD_WP, "status": status}
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 201
        assert resp.json()["status"] == status

    def test_create_with_all_optional_fields(self, client_write):
        payload = {
            "work_package_id": str(VALID_WORK_PACKAGE_ID),
            "task_id": str(VALID_TASK_ID),
            "apparatus_ref": str(SENTINEL_APPARATUS_REF),
            "issue_type": "test_failure",
            "severity": "major",
            "status": "resolved",
            "blocks_completion": True,
            "summary": "Breaker overshot trip setpoint",
            "details": "Retest required after settings update.",
            "reported_by": str(SENTINEL_REPORTED_BY),
            "assigned_to": str(SENTINEL_ASSIGNED_TO),
            "resolution_type": "retested_passed",
            "resolved_at": "2026-04-15T12:00:00+00:00",
            "closed_at": "2026-04-15T13:00:00+00:00",
            "created_from_source": "automation",
        }
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["blocks_completion"] is True
        assert data["resolution_type"] == "retested_passed"
        assert data["status"] == "resolved"
        assert data["details"] == "Retest required after settings update."
        assert data["created_from_source"] == "automation"

    def test_create_rejects_empty_payload(self, client_write):
        resp = client_write.post("/api/v1/work/execution-issues", json={})
        assert resp.status_code == 422

    def test_create_rejects_missing_issue_type(self, client_write):
        payload = {
            "work_package_id": str(VALID_WORK_PACKAGE_ID),
            "severity": "major",
            "summary": "x",
        }
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422

    def test_create_rejects_missing_severity(self, client_write):
        payload = {
            "work_package_id": str(VALID_WORK_PACKAGE_ID),
            "issue_type": "equipment_not_ready",
            "summary": "x",
        }
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422

    def test_create_rejects_missing_summary(self, client_write):
        payload = {
            "work_package_id": str(VALID_WORK_PACKAGE_ID),
            "issue_type": "equipment_not_ready",
            "severity": "major",
        }
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422

    def test_create_rejects_empty_summary(self, client_write):
        payload = {**VALID_ISSUE_PAYLOAD_WP, "summary": ""}
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422

    def test_create_rejects_at_least_one_parent_violation(self, client_write):
        """Neither work_package_id nor task_id supplied → Pydantic
        model_validator raises 422 before any db.get() round-trip."""
        payload = {
            "issue_type": "equipment_not_ready",
            "severity": "major",
            "summary": "x",
        }
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422
        body = resp.json()
        assert "detail" in body
        rendered = str(body).lower()
        assert "at least one" in rendered
        assert (
            "work_package_id" in rendered or "task_id" in rendered
        )

    def test_create_rejects_at_least_one_parent_when_both_null(
        self, client_write,
    ):
        """Explicit nulls for both parents must also 422 at the Pydantic
        layer (model_validator runs after the field-level parse)."""
        payload = {
            "work_package_id": None,
            "task_id": None,
            "issue_type": "equipment_not_ready",
            "severity": "major",
            "summary": "x",
        }
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422
        rendered = str(resp.json()).lower()
        assert "at least one" in rendered

    def test_create_invalid_work_package_id(self, client_write):
        payload = {
            "work_package_id": str(INVALID_WORK_PACKAGE_ID),
            "issue_type": "equipment_not_ready",
            "severity": "major",
            "summary": "x",
        }
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "errors" in data
        assert "work_package_id" in data["errors"]

    def test_create_invalid_task_id(self, client_write):
        payload = {
            "task_id": str(INVALID_TASK_ID),
            "issue_type": "equipment_not_ready",
            "severity": "major",
            "summary": "x",
        }
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "task_id" in data["errors"]

    def test_create_both_fks_invalid_merged(self, client_write):
        """Both supplied FKs invalid → merged 422 with both field names
        present in the error dict (parity with dependency packet 016)."""
        payload = {
            "work_package_id": str(INVALID_WORK_PACKAGE_ID),
            "task_id": str(INVALID_TASK_ID),
            "issue_type": "equipment_not_ready",
            "severity": "major",
            "summary": "x",
        }
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "work_package_id" in data["errors"]
        assert "task_id" in data["errors"]

    def test_create_invalid_issue_type(self, client_write):
        payload = {**VALID_ISSUE_PAYLOAD_WP, "issue_type": "NOT_A_TYPE"}
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422

    def test_create_invalid_severity(self, client_write):
        payload = {**VALID_ISSUE_PAYLOAD_WP, "severity": "catastrophic"}
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422

    def test_create_invalid_status(self, client_write):
        payload = {**VALID_ISSUE_PAYLOAD_WP, "status": "pending"}
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422

    def test_create_invalid_resolution_type(self, client_write):
        payload = {
            **VALID_ISSUE_PAYLOAD_WP,
            "resolution_type": "not_a_resolution",
        }
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422

    def test_create_invalid_created_from_source(self, client_write):
        payload = {
            **VALID_ISSUE_PAYLOAD_WP,
            "created_from_source": "not_a_source",
        }
        resp = client_write.post("/api/v1/work/execution-issues", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/v1/work/execution-issues/{execution_issue_id}
# ---------------------------------------------------------------------------

class TestUpdateExecutionIssue:
    """Tests for PATCH /api/v1/work/execution-issues/{execution_issue_id}."""

    def test_update_status(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"status": "resolved"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["execution_issue_id"] == str(EXISTING_EXECUTION_ISSUE_ID)
        assert data["status"] == "resolved"

    def test_update_severity(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"severity": "critical"},
        )
        assert resp.status_code == 200
        assert resp.json()["severity"] == "critical"

    def test_update_resolution_type(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"resolution_type": "repaired"},
        )
        assert resp.status_code == 200
        assert resp.json()["resolution_type"] == "repaired"

    def test_update_blocks_completion(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"blocks_completion": True},
        )
        assert resp.status_code == 200
        assert resp.json()["blocks_completion"] is True

    def test_update_resolved_at_and_closed_at(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={
                "resolved_at": "2026-04-15T14:00:00+00:00",
                "closed_at": "2026-04-15T15:00:00+00:00",
            },
        )
        assert resp.status_code == 200

    def test_update_assigned_to(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"assigned_to": str(SENTINEL_ASSIGNED_TO)},
        )
        assert resp.status_code == 200

    def test_update_summary_and_details(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={
                "summary": "Revised summary text",
                "details": "Revised detail narrative",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"] == "Revised summary text"
        assert data["details"] == "Revised detail narrative"

    def test_update_empty_summary_rejected(self, client_write):
        """min_length=1 still applies when summary is supplied on update."""
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"summary": ""},
        )
        assert resp.status_code == 422

    def test_update_with_valid_work_package_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"work_package_id": str(VALID_OTHER_WORK_PACKAGE_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_valid_task_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"task_id": str(VALID_OTHER_TASK_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_invalid_work_package_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"work_package_id": str(INVALID_WORK_PACKAGE_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "work_package_id" in data["errors"]

    def test_update_with_invalid_task_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"task_id": str(INVALID_TASK_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "task_id" in data["errors"]

    def test_update_both_fks_invalid_merged(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={
                "work_package_id": str(INVALID_WORK_PACKAGE_ID),
                "task_id": str(INVALID_TASK_ID),
            },
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "work_package_id" in data["errors"]
        assert "task_id" in data["errors"]

    def test_update_nonexistent_execution_issue(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{NONEXISTENT_EXECUTION_ISSUE_ID}",
            json={"status": "resolved"},
        )
        assert resp.status_code == 404

    def test_update_empty_body(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["execution_issue_id"] == str(EXISTING_EXECUTION_ISSUE_ID)

    def test_update_invalid_status(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"status": "not_a_status"},
        )
        assert resp.status_code == 422

    def test_update_invalid_severity(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"severity": "not_a_severity"},
        )
        assert resp.status_code == 422

    def test_update_invalid_resolution_type(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/execution-issues/{EXISTING_EXECUTION_ISSUE_ID}",
            json={"resolution_type": "not_a_resolution"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Read endpoints still work (regression safety-net)
# ---------------------------------------------------------------------------

class TestReadEndpointsUnaffected:
    """Verify existing GET endpoints remain functional under the
    write-mock DB."""

    def test_list_execution_issues_still_works(self, client_write):
        resp = client_write.get("/api/v1/work/execution-issues")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_execution_issues_filter_by_work_package(self, client_write):
        resp = client_write.get(
            f"/api/v1/work/execution-issues?work_package_id={VALID_WORK_PACKAGE_ID}"
        )
        assert resp.status_code == 200

    def test_list_execution_issues_filter_by_task(self, client_write):
        resp = client_write.get(
            f"/api/v1/work/execution-issues?task_id={VALID_TASK_ID}"
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Non-execution-issue PM mutation scope remains read-only
# ---------------------------------------------------------------------------

class TestReadOnlyBoundaryUnchanged:
    """Only WBS nodes remain read-only after packet 018 opened the
    progress-snapshot write surface.  Projects, work packages, tasks,
    assignments, dependencies, execution-issues, and progress-snapshots
    are open for writes; those boundaries are asserted in their own
    write modules."""

    def test_wbs_nodes_post_still_405(self, client_write):
        resp = client_write.post("/api/v1/work/wbs-nodes", json={})
        assert resp.status_code == 405
