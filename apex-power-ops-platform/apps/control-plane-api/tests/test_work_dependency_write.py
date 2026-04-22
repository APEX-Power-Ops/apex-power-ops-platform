"""
PM/Work Domain — Dependency Write API Tests
===========================================
Packet: 2026-04-15-pm-schema-016

These tests verify:
  1. POST /api/v1/work/dependencies creates a dependency with valid
     intra-work FK references (both predecessor_task_id and
     successor_task_id are required by the DependencyCreate Pydantic
     contract and both target work.tasks)
  2. POST rejects invalid predecessor_task_id with 422 and field-level
     errors
  3. POST rejects invalid successor_task_id with 422
  4. POST rejects both FKs invalid with merged error dict
  5. POST rejects self-cycle (predecessor_task_id == successor_task_id)
     with 422 via the @model_validator(mode="after") guard, before the
     mutation service is reached
  6. POST rejects invalid relationship_type enum values with 422
  7. POST accepts each DependencyType (FS / SS / SF / FF)
  8. PATCH /api/v1/work/dependencies/{id} updates with valid references
  9. PATCH rejects invalid intra-work FKs with 422
 10. PATCH rejects merged invalid predecessor + successor with 422
 11. PATCH returns 404 for non-existent dependency
 12. PATCH with empty body returns the unchanged dependency
 13. PATCH rejects an effective-pair self-cycle (one side patched to
     match the stored other side) via the service-layer merged check
 14. Read endpoints remain functional under the write-mock DB
 15. Non-dependency PM mutation scope remains read-only (execution
     issues and progress snapshots still 405); POST/PATCH for projects,
     work packages, tasks, and assignments remain open from earlier
     packets

Tests use a mock database session.  The mock simulates db.get() across
work.Dependency and work.Task to exercise the merged two-FK validation
surface and the no-self-cycle guard at both the Pydantic and service
boundaries.
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

VALID_PREDECESSOR_TASK_ID = UUID("77777777-1111-0000-0000-000000000001")
VALID_SUCCESSOR_TASK_ID = UUID("77777777-2222-0000-0000-000000000002")
VALID_THIRD_TASK_ID = UUID("77777777-3333-0000-0000-000000000003")

INVALID_PREDECESSOR_TASK_ID = UUID("eeeeeeee-1111-0000-0000-000000000099")
INVALID_SUCCESSOR_TASK_ID = UUID("eeeeeeee-2222-0000-0000-000000000099")

EXISTING_DEPENDENCY_ID = UUID("66666666-0000-0000-0000-000000000001")
NONEXISTENT_DEPENDENCY_ID = UUID("00000000-0000-0000-0000-000000000099")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_mock_dependency(**overrides):
    """Create a mock Dependency ORM instance with all DependencyRead fields populated."""
    from datetime import datetime, timezone
    from decimal import Decimal
    defaults = {
        "dependency_id": EXISTING_DEPENDENCY_ID,
        "predecessor_task_id": VALID_PREDECESSOR_TASK_ID,
        "successor_task_id": VALID_SUCCESSOR_TASK_ID,
        "relationship_type": "FS",
        "lag_hours": Decimal("0"),
        "source_system": "manual",
        "p6_relationship_id": None,
        "is_active": True,
        "created_from_source": "manual",
        "created_at": datetime(2026, 4, 15, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 4, 15, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _make_mock_task(pk):
    mock = MagicMock()
    mock.task_id = pk
    mock.title = "Parent Task"
    return mock


def _mock_db_for_dependency_writes():
    """Mock DB supporting FK lookups across work.Task + work.Dependency."""
    from models.work import Dependency, Task

    mock_db = MagicMock()
    created_dependency = [None]

    def mock_get(model_class, pk):
        if model_class is Task:
            if pk in (
                VALID_PREDECESSOR_TASK_ID,
                VALID_SUCCESSOR_TASK_ID,
                VALID_THIRD_TASK_ID,
            ):
                return _make_mock_task(pk)
            return None
        if model_class is Dependency:
            if pk == EXISTING_DEPENDENCY_ID:
                return _make_mock_dependency()
            return None
        return None

    mock_db.get = mock_get

    def mock_add(obj):
        created_dependency[0] = obj

    def mock_commit():
        from datetime import datetime, timezone
        from decimal import Decimal
        if created_dependency[0] is not None:
            # Auto-populate server-managed fields on commit
            if (not hasattr(created_dependency[0], "dependency_id")
                    or created_dependency[0].dependency_id is None):
                created_dependency[0].dependency_id = uuid4()
            if (not hasattr(created_dependency[0], "created_at")
                    or created_dependency[0].created_at is None):
                created_dependency[0].created_at = datetime(
                    2026, 4, 15, tzinfo=timezone.utc
                )
            if (not hasattr(created_dependency[0], "updated_at")
                    or created_dependency[0].updated_at is None):
                created_dependency[0].updated_at = datetime(
                    2026, 4, 15, tzinfo=timezone.utc
                )
            # Null out optional read fields not set by the create path
            if not hasattr(created_dependency[0], "p6_relationship_id"):
                created_dependency[0].p6_relationship_id = None

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
    mock_db = _mock_db_for_dependency_writes()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Minimal valid create payload
# ---------------------------------------------------------------------------

VALID_DEPENDENCY_PAYLOAD = {
    "predecessor_task_id": str(VALID_PREDECESSOR_TASK_ID),
    "successor_task_id": str(VALID_SUCCESSOR_TASK_ID),
}


# ---------------------------------------------------------------------------
# POST /api/v1/work/dependencies
# ---------------------------------------------------------------------------

class TestCreateDependency:
    """Tests for POST /api/v1/work/dependencies."""

    def test_create_valid_dependency_defaults(self, client_write):
        resp = client_write.post(
            "/api/v1/work/dependencies",
            json=VALID_DEPENDENCY_PAYLOAD,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["predecessor_task_id"] == str(VALID_PREDECESSOR_TASK_ID)
        assert data["successor_task_id"] == str(VALID_SUCCESSOR_TASK_ID)
        # Server-defaulted fields
        assert data["relationship_type"] == "FS"
        assert data["source_system"] == "manual"
        assert data["is_active"] is True
        assert data["created_from_source"] == "manual"

    @pytest.mark.parametrize("rel_type", ["FS", "SS", "SF", "FF"])
    def test_create_accepts_all_dependency_types(self, client_write, rel_type):
        payload = {
            **VALID_DEPENDENCY_PAYLOAD,
            "relationship_type": rel_type,
        }
        resp = client_write.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 201
        assert resp.json()["relationship_type"] == rel_type

    def test_create_with_all_optional_fields(self, client_write):
        payload = {
            **VALID_DEPENDENCY_PAYLOAD,
            "relationship_type": "SS",
            "lag_hours": 2.5,
            "source_system": "p6_import",
            "is_active": False,
            "created_from_source": "p6_import",
        }
        resp = client_write.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["relationship_type"] == "SS"
        assert data["source_system"] == "p6_import"
        assert data["is_active"] is False

    def test_create_rejects_empty_payload(self, client_write):
        resp = client_write.post("/api/v1/work/dependencies", json={})
        assert resp.status_code == 422

    def test_create_rejects_missing_predecessor(self, client_write):
        payload = {"successor_task_id": str(VALID_SUCCESSOR_TASK_ID)}
        resp = client_write.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 422

    def test_create_rejects_missing_successor(self, client_write):
        payload = {"predecessor_task_id": str(VALID_PREDECESSOR_TASK_ID)}
        resp = client_write.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 422

    def test_create_invalid_predecessor_task_id(self, client_write):
        payload = {
            "predecessor_task_id": str(INVALID_PREDECESSOR_TASK_ID),
            "successor_task_id": str(VALID_SUCCESSOR_TASK_ID),
        }
        resp = client_write.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "errors" in data
        assert "predecessor_task_id" in data["errors"]

    def test_create_invalid_successor_task_id(self, client_write):
        payload = {
            "predecessor_task_id": str(VALID_PREDECESSOR_TASK_ID),
            "successor_task_id": str(INVALID_SUCCESSOR_TASK_ID),
        }
        resp = client_write.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "successor_task_id" in data["errors"]

    def test_create_both_fks_invalid_merged(self, client_write):
        """Both FKs invalid → merged 422 with both field names."""
        payload = {
            "predecessor_task_id": str(INVALID_PREDECESSOR_TASK_ID),
            "successor_task_id": str(INVALID_SUCCESSOR_TASK_ID),
        }
        resp = client_write.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "predecessor_task_id" in data["errors"]
        assert "successor_task_id" in data["errors"]

    def test_create_rejects_self_cycle(self, client_write):
        """Predecessor == successor must 422 at the Pydantic layer
        (model_validator) before any db.get() round-trip."""
        same_task = str(VALID_PREDECESSOR_TASK_ID)
        payload = {
            "predecessor_task_id": same_task,
            "successor_task_id": same_task,
        }
        resp = client_write.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 422
        # FastAPI serializes Pydantic model_validator errors in the
        # "detail" list, not the OrgValidationError "errors" dict.
        body = resp.json()
        assert "detail" in body
        # Message from the validator propagates verbatim
        rendered = str(body).lower()
        assert "different tasks" in rendered

    def test_create_rejects_self_cycle_even_when_task_unknown(self, client_write):
        """Pydantic self-cycle guard runs before FK validation — a self-
        referential payload with an unknown task still 422s with the
        self-cycle message, not an FK-not-found message."""
        same_unknown = str(INVALID_PREDECESSOR_TASK_ID)
        payload = {
            "predecessor_task_id": same_unknown,
            "successor_task_id": same_unknown,
        }
        resp = client_write.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 422
        rendered = str(resp.json()).lower()
        assert "different tasks" in rendered

    def test_create_invalid_relationship_type(self, client_write):
        payload = {
            **VALID_DEPENDENCY_PAYLOAD,
            "relationship_type": "NOT_A_REL_TYPE",
        }
        resp = client_write.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 422

    def test_create_invalid_source_system(self, client_write):
        payload = {
            **VALID_DEPENDENCY_PAYLOAD,
            "source_system": "not_a_source",
        }
        resp = client_write.post("/api/v1/work/dependencies", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/v1/work/dependencies/{dependency_id}
# ---------------------------------------------------------------------------

class TestUpdateDependency:
    """Tests for PATCH /api/v1/work/dependencies/{dependency_id}."""

    def test_update_relationship_type(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={"relationship_type": "SS"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["dependency_id"] == str(EXISTING_DEPENDENCY_ID)
        assert data["relationship_type"] == "SS"

    def test_update_lag_hours(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={"lag_hours": 4.0},
        )
        assert resp.status_code == 200

    def test_update_is_active(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={"is_active": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_update_with_valid_predecessor(self, client_write):
        """Patch predecessor to a different valid task — stored successor
        remains VALID_SUCCESSOR_TASK_ID, so the effective pair is
        (VALID_THIRD_TASK_ID, VALID_SUCCESSOR_TASK_ID), which is distinct
        and must succeed."""
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={"predecessor_task_id": str(VALID_THIRD_TASK_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_valid_successor(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={"successor_task_id": str(VALID_THIRD_TASK_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_invalid_predecessor_task_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={"predecessor_task_id": str(INVALID_PREDECESSOR_TASK_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "predecessor_task_id" in data["errors"]

    def test_update_with_invalid_successor_task_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={"successor_task_id": str(INVALID_SUCCESSOR_TASK_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "successor_task_id" in data["errors"]

    def test_update_both_fks_invalid_merged(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={
                "predecessor_task_id": str(INVALID_PREDECESSOR_TASK_ID),
                "successor_task_id": str(INVALID_SUCCESSOR_TASK_ID),
            },
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "predecessor_task_id" in data["errors"]
        assert "successor_task_id" in data["errors"]

    def test_update_effective_pair_self_cycle_predecessor(self, client_write):
        """Stored successor is VALID_SUCCESSOR_TASK_ID; patching the
        predecessor to that same task yields a self-referential effective
        pair.  The service-layer merged check must 422 both fields."""
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={"predecessor_task_id": str(VALID_SUCCESSOR_TASK_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "predecessor_task_id" in data["errors"]
        assert "successor_task_id" in data["errors"]
        rendered = str(data).lower()
        assert "different tasks" in rendered

    def test_update_effective_pair_self_cycle_successor(self, client_write):
        """Mirror of the above: stored predecessor is
        VALID_PREDECESSOR_TASK_ID; patching the successor to that same
        task yields a self-referential effective pair."""
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={"successor_task_id": str(VALID_PREDECESSOR_TASK_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "predecessor_task_id" in data["errors"]
        assert "successor_task_id" in data["errors"]

    def test_update_effective_pair_self_cycle_both_sides_patched(self, client_write):
        """Patch both sides to the same valid task → 422 self-cycle."""
        same_task = str(VALID_THIRD_TASK_ID)
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={
                "predecessor_task_id": same_task,
                "successor_task_id": same_task,
            },
        )
        assert resp.status_code == 422

    def test_update_nonexistent_dependency(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{NONEXISTENT_DEPENDENCY_ID}",
            json={"relationship_type": "SS"},
        )
        assert resp.status_code == 404

    def test_update_empty_body(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["dependency_id"] == str(EXISTING_DEPENDENCY_ID)

    def test_update_invalid_relationship_type(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/dependencies/{EXISTING_DEPENDENCY_ID}",
            json={"relationship_type": "not_a_type"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Read endpoints still work (regression safety-net)
# ---------------------------------------------------------------------------

class TestReadEndpointsUnaffected:
    """Verify existing GET endpoints remain functional under the write-mock DB."""

    def test_list_dependencies_still_works(self, client_write):
        resp = client_write.get("/api/v1/work/dependencies")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_dependencies_filter_by_predecessor(self, client_write):
        resp = client_write.get(
            f"/api/v1/work/dependencies?predecessor_task_id={VALID_PREDECESSOR_TASK_ID}"
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Non-dependency PM mutation scope remains read-only
# ---------------------------------------------------------------------------

class TestReadOnlyBoundaryUnchanged:
    """Only WBS nodes remain read-only after packet 018.  Projects,
    work packages, tasks, assignments, dependencies, execution-issues
    (packet 017), and progress-snapshots (packet 018) are open for
    writes; those boundaries are not re-asserted here — see
    test_work_execution_issue_write.py and
    test_work_progress_snapshot_write.py for those surfaces."""

    def test_wbs_nodes_post_still_405(self, client_write):
        resp = client_write.post("/api/v1/work/wbs-nodes", json={})
        assert resp.status_code == 405
