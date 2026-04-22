"""
PM/Work Domain — Progress-Snapshot Write API Tests
===================================================
Packet: 2026-04-15-pm-schema-018

These tests verify:
  1. POST /api/v1/work/progress-snapshots creates a snapshot with only
     the required fields (project_id + snapshot_period_start/end)
  2. POST creates with every optional FK populated (work_package_id,
     task_id, supersedes_snapshot_id, approved_by)
  3. POST accepts each SnapshotStatus enum value
  4. POST accepts each ProvenanceSource enum value on
     ``created_from_source``
  5. POST accepts a full payload with every optional field populated
  6. POST rejects empty payload with 422
  7. POST rejects missing project_id with 422
  8. POST rejects missing snapshot_period_start / end with 422
  9. POST rejects period_end < period_start at the Pydantic
     model_validator layer (mirrors DDL
     ``ck_progress_snapshots_period``) before any db.get() round-trip
 10. POST rejects negative completed/total apparatus counts (ge=0)
 11. POST rejects percent_complete outside [0, 100]
 12. POST rejects negative actual_labor_hours / billable_amount
 13. POST rejects invalid enum values (snapshot_status,
     created_from_source)
 14. POST rejects invalid project_id with 422 keyed ``project_id``
 15. POST rejects invalid work_package_id, task_id,
     supersedes_snapshot_id, approved_by individually
 16. POST rejects a fully invalid FK set with a merged error dict
     containing all five field names (parity with packet 015)
 17. PATCH /api/v1/work/progress-snapshots/{id} updates
     snapshot_status
 18. PATCH updates percent_complete, billable_amount, billing_reference
 19. PATCH updates completed/total apparatus counts
 20. PATCH updates approved_by / approved_at
 21. PATCH updates snapshot_period_start and snapshot_period_end
 22. PATCH with a valid FK patch on one side only is accepted
 23. PATCH rejects invalid FKs individually and merged
 24. PATCH rejects self-reference (supersedes_snapshot_id ==
     progress_snapshot_id) — service-layer effective-pair guard
 25. PATCH rejects period_end < period_start using effective pair —
     service-layer guard with existing row's bound filling in the
     unsupplied end
 26. PATCH returns 404 for non-existent progress_snapshot_id
 27. PATCH with empty body returns the unchanged snapshot
 28. PATCH rejects invalid enum values
 29. Read endpoints remain functional under the write-mock DB
 30. Non-progress-snapshot mutation scope remains read-only — after
     packet 018 only WBS nodes remain read-only; POST /progress-snapshots
     is NO LONGER 405 (now a valid write surface)

Tests use a mock database session.  The mock simulates db.get() across
work.Project, work.WorkPackage, work.Task, work.ProgressSnapshot (for
both the supersedes self-reference and the existing-row lookup on
update), and identity.User (for ``approved_by``) to exercise the merged
five-FK validation surface and the Pydantic / service-layer guards.
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

VALID_PROJECT_ID = UUID("99999999-1111-0000-0000-000000000001")
VALID_OTHER_PROJECT_ID = UUID("99999999-1111-0000-0000-000000000002")
VALID_WORK_PACKAGE_ID = UUID("99999999-2222-0000-0000-000000000001")
VALID_OTHER_WORK_PACKAGE_ID = UUID("99999999-2222-0000-0000-000000000002")
VALID_TASK_ID = UUID("99999999-3333-0000-0000-000000000001")
VALID_OTHER_TASK_ID = UUID("99999999-3333-0000-0000-000000000002")
VALID_SUPERSEDES_SNAPSHOT_ID = UUID("99999999-4444-0000-0000-000000000001")
VALID_APPROVER_ID = UUID("99999999-5555-0000-0000-000000000001")

INVALID_PROJECT_ID = UUID("eeeeeeee-1111-0000-0000-000000000099")
INVALID_WORK_PACKAGE_ID = UUID("eeeeeeee-2222-0000-0000-000000000099")
INVALID_TASK_ID = UUID("eeeeeeee-3333-0000-0000-000000000099")
INVALID_SUPERSEDES_SNAPSHOT_ID = UUID("eeeeeeee-4444-0000-0000-000000000099")
INVALID_APPROVER_ID = UUID("eeeeeeee-5555-0000-0000-000000000099")

EXISTING_SNAPSHOT_ID = UUID("aaaaaaaa-0000-0000-0000-000000000018")
NONEXISTENT_SNAPSHOT_ID = UUID("00000000-0000-0000-0000-000000000099")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_mock_snapshot(**overrides):
    """Create a mock ProgressSnapshot ORM instance with all
    ProgressSnapshotRead fields populated."""
    from datetime import date, datetime, timezone
    from decimal import Decimal
    defaults = {
        "progress_snapshot_id": EXISTING_SNAPSHOT_ID,
        "project_id": VALID_PROJECT_ID,
        "work_package_id": None,
        "task_id": None,
        "snapshot_period_start": date(2026, 4, 1),
        "snapshot_period_end": date(2026, 4, 14),
        "snapshot_status": "draft",
        "completed_apparatus_count": None,
        "total_apparatus_count": None,
        "percent_complete": None,
        "actual_labor_hours": None,
        "billable_amount": None,
        "billing_reference": None,
        "approved_by": None,
        "approved_by_name": None,
        "approved_at": None,
        "supersedes_snapshot_id": None,
        "source_data_date": None,
        "created_from_source": "manual",
        "created_at": datetime(2026, 4, 15, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 4, 15, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _make_mock_project(pk):
    mock = MagicMock()
    mock.project_id = pk
    mock.title = "Mock Project"
    return mock


def _make_mock_work_package(pk):
    mock = MagicMock()
    mock.work_package_id = pk
    mock.title = "Mock Work Package"
    return mock


def _make_mock_task(pk):
    mock = MagicMock()
    mock.task_id = pk
    mock.title = "Mock Task"
    return mock


def _make_mock_user(pk):
    mock = MagicMock()
    mock.user_id = pk
    mock.display_name = "Mock Approver"
    return mock


def _mock_db_for_progress_snapshot_writes():
    """Mock DB supporting FK lookups across work.Project, work.WorkPackage,
    work.Task, work.ProgressSnapshot, and identity.User."""
    from models.work import (
        Project,
        ProgressSnapshot,
        Task,
        WorkPackage,
    )
    from models.identity import User

    mock_db = MagicMock()
    created_snapshot = [None]

    def mock_get(model_class, pk):
        if model_class is Project:
            if pk in (VALID_PROJECT_ID, VALID_OTHER_PROJECT_ID):
                return _make_mock_project(pk)
            return None
        if model_class is WorkPackage:
            if pk in (VALID_WORK_PACKAGE_ID, VALID_OTHER_WORK_PACKAGE_ID):
                return _make_mock_work_package(pk)
            return None
        if model_class is Task:
            if pk in (VALID_TASK_ID, VALID_OTHER_TASK_ID):
                return _make_mock_task(pk)
            return None
        if model_class is ProgressSnapshot:
            if pk == EXISTING_SNAPSHOT_ID:
                return _make_mock_snapshot()
            if pk == VALID_SUPERSEDES_SNAPSHOT_ID:
                return _make_mock_snapshot(
                    progress_snapshot_id=VALID_SUPERSEDES_SNAPSHOT_ID,
                )
            return None
        if model_class is User:
            if pk == VALID_APPROVER_ID:
                return _make_mock_user(pk)
            return None
        return None

    mock_db.get = mock_get

    def mock_add(obj):
        created_snapshot[0] = obj

    def mock_commit():
        from datetime import datetime, timezone
        if created_snapshot[0] is not None:
            if (not hasattr(created_snapshot[0], "progress_snapshot_id")
                    or created_snapshot[0].progress_snapshot_id is None):
                created_snapshot[0].progress_snapshot_id = uuid4()
            if (not hasattr(created_snapshot[0], "created_at")
                    or created_snapshot[0].created_at is None):
                created_snapshot[0].created_at = datetime(
                    2026, 4, 15, tzinfo=timezone.utc,
                )
            if (not hasattr(created_snapshot[0], "updated_at")
                    or created_snapshot[0].updated_at is None):
                created_snapshot[0].updated_at = datetime(
                    2026, 4, 15, tzinfo=timezone.utc,
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
    mock_db = _mock_db_for_progress_snapshot_writes()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Minimal valid create payload
# ---------------------------------------------------------------------------

MINIMAL_SNAPSHOT_PAYLOAD = {
    "project_id": str(VALID_PROJECT_ID),
    "snapshot_period_start": "2026-04-01",
    "snapshot_period_end": "2026-04-14",
}


# ---------------------------------------------------------------------------
# POST /api/v1/work/progress-snapshots
# ---------------------------------------------------------------------------

class TestCreateProgressSnapshot:
    """Tests for POST /api/v1/work/progress-snapshots."""

    def test_create_minimal_payload(self, client_write):
        resp = client_write.post(
            "/api/v1/work/progress-snapshots",
            json=MINIMAL_SNAPSHOT_PAYLOAD,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["project_id"] == str(VALID_PROJECT_ID)
        assert data["snapshot_period_start"] == "2026-04-01"
        assert data["snapshot_period_end"] == "2026-04-14"
        assert data["snapshot_status"] == "draft"
        assert data["created_from_source"] == "manual"
        assert data["work_package_id"] is None
        assert data["task_id"] is None
        assert data["supersedes_snapshot_id"] is None
        assert data["approved_by"] is None

    def test_create_with_all_optional_fks(self, client_write):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "work_package_id": str(VALID_WORK_PACKAGE_ID),
            "task_id": str(VALID_TASK_ID),
            "supersedes_snapshot_id": str(VALID_SUPERSEDES_SNAPSHOT_ID),
            "approved_by": str(VALID_APPROVER_ID),
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["work_package_id"] == str(VALID_WORK_PACKAGE_ID)
        assert data["task_id"] == str(VALID_TASK_ID)
        assert data["supersedes_snapshot_id"] == str(VALID_SUPERSEDES_SNAPSHOT_ID)
        assert data["approved_by"] == str(VALID_APPROVER_ID)

    @pytest.mark.parametrize(
        "snapshot_status",
        ["draft", "submitted", "approved", "rejected"],
    )
    def test_create_accepts_all_snapshot_statuses(
        self, client_write, snapshot_status,
    ):
        payload = {**MINIMAL_SNAPSHOT_PAYLOAD, "snapshot_status": snapshot_status}
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 201
        assert resp.json()["snapshot_status"] == snapshot_status

    @pytest.mark.parametrize(
        "created_from_source",
        ["manual", "p6_import", "api", "automation", "migration", "bulk_upload"],
    )
    def test_create_accepts_all_provenance_sources(
        self, client_write, created_from_source,
    ):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "created_from_source": created_from_source,
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 201
        assert resp.json()["created_from_source"] == created_from_source

    def test_create_with_all_optional_fields(self, client_write):
        payload = {
            "project_id": str(VALID_PROJECT_ID),
            "work_package_id": str(VALID_WORK_PACKAGE_ID),
            "task_id": str(VALID_TASK_ID),
            "snapshot_period_start": "2026-04-01",
            "snapshot_period_end": "2026-04-14",
            "snapshot_status": "approved",
            "completed_apparatus_count": 12,
            "total_apparatus_count": 20,
            "percent_complete": "60.00",
            "actual_labor_hours": "240.50",
            "billable_amount": "15000.75",
            "billing_reference": "INV-2026-018-001",
            "approved_by": str(VALID_APPROVER_ID),
            "approved_at": "2026-04-15T08:00:00+00:00",
            "supersedes_snapshot_id": str(VALID_SUPERSEDES_SNAPSHOT_ID),
            "source_data_date": "2026-04-14T23:59:59+00:00",
            "created_from_source": "p6_import",
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["snapshot_status"] == "approved"
        assert data["completed_apparatus_count"] == 12
        assert data["total_apparatus_count"] == 20
        assert data["billing_reference"] == "INV-2026-018-001"
        assert data["created_from_source"] == "p6_import"

    def test_create_rejects_empty_payload(self, client_write):
        resp = client_write.post("/api/v1/work/progress-snapshots", json={})
        assert resp.status_code == 422

    def test_create_rejects_missing_project_id(self, client_write):
        payload = {
            "snapshot_period_start": "2026-04-01",
            "snapshot_period_end": "2026-04-14",
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422

    def test_create_rejects_missing_period_start(self, client_write):
        payload = {
            "project_id": str(VALID_PROJECT_ID),
            "snapshot_period_end": "2026-04-14",
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422

    def test_create_rejects_missing_period_end(self, client_write):
        payload = {
            "project_id": str(VALID_PROJECT_ID),
            "snapshot_period_start": "2026-04-01",
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422

    def test_create_rejects_period_end_before_period_start(self, client_write):
        """Pydantic model_validator mirrors DDL ``ck_progress_snapshots_period``
        and raises 422 before any db.get() round-trip."""
        payload = {
            "project_id": str(VALID_PROJECT_ID),
            "snapshot_period_start": "2026-04-14",
            "snapshot_period_end": "2026-04-01",
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422
        rendered = str(resp.json()).lower()
        assert "snapshot_period_end" in rendered
        assert "on or after" in rendered

    def test_create_accepts_period_end_equals_period_start(self, client_write):
        """Single-day period is allowed (end >= start)."""
        payload = {
            "project_id": str(VALID_PROJECT_ID),
            "snapshot_period_start": "2026-04-14",
            "snapshot_period_end": "2026-04-14",
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 201

    def test_create_rejects_negative_completed_apparatus_count(
        self, client_write,
    ):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "completed_apparatus_count": -1,
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422

    def test_create_rejects_negative_total_apparatus_count(self, client_write):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "total_apparatus_count": -5,
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422

    def test_create_rejects_percent_complete_above_100(self, client_write):
        payload = {**MINIMAL_SNAPSHOT_PAYLOAD, "percent_complete": "100.01"}
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422

    def test_create_rejects_percent_complete_below_zero(self, client_write):
        payload = {**MINIMAL_SNAPSHOT_PAYLOAD, "percent_complete": "-0.01"}
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422

    def test_create_rejects_negative_actual_labor_hours(self, client_write):
        payload = {**MINIMAL_SNAPSHOT_PAYLOAD, "actual_labor_hours": "-0.25"}
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422

    def test_create_rejects_negative_billable_amount(self, client_write):
        payload = {**MINIMAL_SNAPSHOT_PAYLOAD, "billable_amount": "-1.00"}
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422

    def test_create_rejects_invalid_snapshot_status(self, client_write):
        payload = {**MINIMAL_SNAPSHOT_PAYLOAD, "snapshot_status": "pending"}
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422

    def test_create_rejects_invalid_created_from_source(self, client_write):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "created_from_source": "not_a_source",
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422

    def test_create_invalid_project_id(self, client_write):
        payload = {**MINIMAL_SNAPSHOT_PAYLOAD, "project_id": str(INVALID_PROJECT_ID)}
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "errors" in data
        assert "project_id" in data["errors"]

    def test_create_invalid_work_package_id(self, client_write):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "work_package_id": str(INVALID_WORK_PACKAGE_ID),
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422
        assert "work_package_id" in resp.json()["errors"]

    def test_create_invalid_task_id(self, client_write):
        payload = {**MINIMAL_SNAPSHOT_PAYLOAD, "task_id": str(INVALID_TASK_ID)}
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422
        assert "task_id" in resp.json()["errors"]

    def test_create_invalid_supersedes_snapshot_id(self, client_write):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "supersedes_snapshot_id": str(INVALID_SUPERSEDES_SNAPSHOT_ID),
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422
        assert "supersedes_snapshot_id" in resp.json()["errors"]

    def test_create_invalid_approved_by(self, client_write):
        payload = {
            **MINIMAL_SNAPSHOT_PAYLOAD,
            "approved_by": str(INVALID_APPROVER_ID),
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422
        assert "approved_by" in resp.json()["errors"]

    def test_create_all_five_fks_invalid_merged(self, client_write):
        """All five supplied FKs invalid → merged 422 error dict contains
        every field name (parity with packet 015 assignments merged lane)."""
        payload = {
            "project_id": str(INVALID_PROJECT_ID),
            "work_package_id": str(INVALID_WORK_PACKAGE_ID),
            "task_id": str(INVALID_TASK_ID),
            "supersedes_snapshot_id": str(INVALID_SUPERSEDES_SNAPSHOT_ID),
            "approved_by": str(INVALID_APPROVER_ID),
            "snapshot_period_start": "2026-04-01",
            "snapshot_period_end": "2026-04-14",
        }
        resp = client_write.post(
            "/api/v1/work/progress-snapshots", json=payload,
        )
        assert resp.status_code == 422
        errors = resp.json()["errors"]
        assert "project_id" in errors
        assert "work_package_id" in errors
        assert "task_id" in errors
        assert "supersedes_snapshot_id" in errors
        assert "approved_by" in errors


# ---------------------------------------------------------------------------
# PATCH /api/v1/work/progress-snapshots/{progress_snapshot_id}
# ---------------------------------------------------------------------------

class TestUpdateProgressSnapshot:
    """Tests for PATCH /api/v1/work/progress-snapshots/{progress_snapshot_id}."""

    def test_update_snapshot_status(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"snapshot_status": "submitted"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["progress_snapshot_id"] == str(EXISTING_SNAPSHOT_ID)
        assert data["snapshot_status"] == "submitted"

    def test_update_percent_complete(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"percent_complete": "42.50"},
        )
        assert resp.status_code == 200

    def test_update_billable_amount_and_reference(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={
                "billable_amount": "9999.99",
                "billing_reference": "INV-2026-018-042",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["billing_reference"] == "INV-2026-018-042"

    def test_update_apparatus_counts(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={
                "completed_apparatus_count": 7,
                "total_apparatus_count": 10,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed_apparatus_count"] == 7
        assert data["total_apparatus_count"] == 10

    def test_update_approved_by_and_approved_at(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={
                "approved_by": str(VALID_APPROVER_ID),
                "approved_at": "2026-04-15T09:30:00+00:00",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["approved_by"] == str(VALID_APPROVER_ID)

    def test_update_snapshot_period_both_ends(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={
                "snapshot_period_start": "2026-05-01",
                "snapshot_period_end": "2026-05-15",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["snapshot_period_start"] == "2026-05-01"
        assert data["snapshot_period_end"] == "2026-05-15"

    def test_update_snapshot_period_start_only(self, client_write):
        """Only supply a new start — the effective end is the existing
        row's end (2026-04-14).  Start 2026-04-10 <= end 2026-04-14 is
        valid."""
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"snapshot_period_start": "2026-04-10"},
        )
        assert resp.status_code == 200

    def test_update_snapshot_period_end_only(self, client_write):
        """Only supply a new end — the effective start is the existing
        row's start (2026-04-01).  End 2026-04-30 >= start is valid."""
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"snapshot_period_end": "2026-04-30"},
        )
        assert resp.status_code == 200

    def test_update_rejects_period_end_before_existing_start(
        self, client_write,
    ):
        """Effective-pair monotonicity: supply only a new end that falls
        before the existing row's start → service-layer guard raises 422
        with ``snapshot_period_end`` error key."""
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"snapshot_period_end": "2026-03-01"},
        )
        assert resp.status_code == 422
        assert "snapshot_period_end" in resp.json()["errors"]

    def test_update_rejects_period_start_after_existing_end(
        self, client_write,
    ):
        """Effective-pair monotonicity: supply only a new start that falls
        after the existing row's end → service-layer guard raises 422."""
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"snapshot_period_start": "2026-05-01"},
        )
        assert resp.status_code == 422
        assert "snapshot_period_end" in resp.json()["errors"]

    def test_update_rejects_period_end_before_supplied_start(
        self, client_write,
    ):
        """Both ends supplied but end < start → service-layer guard 422."""
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={
                "snapshot_period_start": "2026-06-15",
                "snapshot_period_end": "2026-06-01",
            },
        )
        assert resp.status_code == 422
        assert "snapshot_period_end" in resp.json()["errors"]

    def test_update_rejects_self_reference(self, client_write):
        """A progress snapshot cannot supersede itself — service-layer
        effective-pair guard raises 422 on ``supersedes_snapshot_id``."""
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"supersedes_snapshot_id": str(EXISTING_SNAPSHOT_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "supersedes_snapshot_id" in data["errors"]
        assert "itself" in data["errors"]["supersedes_snapshot_id"].lower()

    def test_update_valid_supersedes_snapshot(self, client_write):
        """Different valid snapshot id is accepted."""
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"supersedes_snapshot_id": str(VALID_SUPERSEDES_SNAPSHOT_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_valid_project_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"project_id": str(VALID_OTHER_PROJECT_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_valid_work_package_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"work_package_id": str(VALID_OTHER_WORK_PACKAGE_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_valid_task_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"task_id": str(VALID_OTHER_TASK_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_invalid_project_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"project_id": str(INVALID_PROJECT_ID)},
        )
        assert resp.status_code == 422
        assert "project_id" in resp.json()["errors"]

    def test_update_with_invalid_work_package_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"work_package_id": str(INVALID_WORK_PACKAGE_ID)},
        )
        assert resp.status_code == 422
        assert "work_package_id" in resp.json()["errors"]

    def test_update_with_invalid_task_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"task_id": str(INVALID_TASK_ID)},
        )
        assert resp.status_code == 422
        assert "task_id" in resp.json()["errors"]

    def test_update_with_invalid_supersedes_snapshot_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={
                "supersedes_snapshot_id": str(INVALID_SUPERSEDES_SNAPSHOT_ID),
            },
        )
        assert resp.status_code == 422
        assert "supersedes_snapshot_id" in resp.json()["errors"]

    def test_update_with_invalid_approved_by(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"approved_by": str(INVALID_APPROVER_ID)},
        )
        assert resp.status_code == 422
        assert "approved_by" in resp.json()["errors"]

    def test_update_all_five_fks_invalid_merged(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={
                "project_id": str(INVALID_PROJECT_ID),
                "work_package_id": str(INVALID_WORK_PACKAGE_ID),
                "task_id": str(INVALID_TASK_ID),
                "supersedes_snapshot_id": str(INVALID_SUPERSEDES_SNAPSHOT_ID),
                "approved_by": str(INVALID_APPROVER_ID),
            },
        )
        assert resp.status_code == 422
        errors = resp.json()["errors"]
        assert "project_id" in errors
        assert "work_package_id" in errors
        assert "task_id" in errors
        assert "supersedes_snapshot_id" in errors
        assert "approved_by" in errors

    def test_update_nonexistent_progress_snapshot(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{NONEXISTENT_SNAPSHOT_ID}",
            json={"snapshot_status": "approved"},
        )
        assert resp.status_code == 404

    def test_update_empty_body(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["progress_snapshot_id"] == str(EXISTING_SNAPSHOT_ID)

    def test_update_invalid_snapshot_status(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"snapshot_status": "not_a_status"},
        )
        assert resp.status_code == 422

    def test_update_rejects_percent_complete_above_100(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"percent_complete": "101.00"},
        )
        assert resp.status_code == 422

    def test_update_rejects_negative_completed_apparatus_count(
        self, client_write,
    ):
        resp = client_write.patch(
            f"/api/v1/work/progress-snapshots/{EXISTING_SNAPSHOT_ID}",
            json={"completed_apparatus_count": -1},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Read endpoints still work (regression safety-net)
# ---------------------------------------------------------------------------

class TestReadEndpointsUnaffected:
    """Verify existing GET endpoints remain functional under the
    write-mock DB."""

    def test_list_progress_snapshots_still_works(self, client_write):
        resp = client_write.get("/api/v1/work/progress-snapshots")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_progress_snapshots_filter_by_project(self, client_write):
        resp = client_write.get(
            f"/api/v1/work/progress-snapshots?project_id={VALID_PROJECT_ID}",
        )
        assert resp.status_code == 200

    def test_list_progress_snapshots_filter_by_work_package(self, client_write):
        resp = client_write.get(
            "/api/v1/work/progress-snapshots"
            f"?work_package_id={VALID_WORK_PACKAGE_ID}",
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Read-only boundary — only WBS nodes remain read-only after packet 018
# ---------------------------------------------------------------------------

class TestReadOnlyBoundaryUnchanged:
    """After packet 018 the progress-snapshot write surface is OPEN,
    so POST /progress-snapshots must NO LONGER return 405.  Only WBS
    nodes remain read-only.  Other write-open surfaces (projects, work
    packages, tasks, assignments, dependencies, execution-issues) are
    asserted in their own write modules."""

    def test_progress_snapshots_post_is_open(self, client_write):
        """Sanity check: posting a minimal valid payload succeeds (201),
        confirming the endpoint is no longer blocked (405)."""
        resp = client_write.post(
            "/api/v1/work/progress-snapshots",
            json=MINIMAL_SNAPSHOT_PAYLOAD,
        )
        assert resp.status_code == 201

    def test_wbs_nodes_post_still_405(self, client_write):
        resp = client_write.post("/api/v1/work/wbs-nodes", json={})
        assert resp.status_code == 405
