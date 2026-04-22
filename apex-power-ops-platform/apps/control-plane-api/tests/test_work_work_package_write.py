"""
PM/Work Domain — Work Package Write API Tests
==============================================
Packet: 2026-04-14-pm-schema-013

These tests verify:
  1. POST /api/v1/work/work-packages creates a work package with valid
     org, identity, and intra-work FK references
  2. POST rejects invalid client_id / site_id with 422 and field-level errors
  3. POST rejects invalid project_id (intra-work) with 422
  4. POST rejects invalid primary_wbs_node_id (intra-work) with 422
  5. POST rejects invalid assigned_crew_id (identity) with 422
  6. POST rejects multiple invalid references with merged error dict
  7. POST rejects missing required fields with 422
  8. POST rejects empty work_package_code / title with 422
  9. POST rejects progress_percent out of range with 422
 10. PATCH /api/v1/work/work-packages/{id} updates with valid references
 11. PATCH rejects invalid org, identity, or intra-work references with 422
 12. PATCH returns 404 for non-existent work package
 13. PATCH with empty body returns the unchanged work package

Tests use a mock database session.  The mock simulates db.get() across
work (Project, WorkPackage, WBSNode), org (Client, Site), and identity
(Crew) models to exercise the full FK-validation surface.
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

VALID_CLIENT_ID = UUID("11111111-0000-0000-0000-000000000001")
VALID_SITE_ID = UUID("22222222-0000-0000-0000-000000000001")
VALID_PROJECT_ID = UUID("99999999-0000-0000-0000-000000000001")
VALID_WBS_NODE_ID = UUID("44444444-0000-0000-0000-000000000001")
VALID_CREW_ID = UUID("55555555-0000-0000-0000-000000000001")

INVALID_CLIENT_ID = UUID("aaaaaaaa-0000-0000-0000-000000000099")
INVALID_SITE_ID = UUID("bbbbbbbb-0000-0000-0000-000000000099")
INVALID_PROJECT_ID = UUID("cccccccc-0000-0000-0000-000000000099")
INVALID_WBS_NODE_ID = UUID("dddddddd-0000-0000-0000-000000000099")
INVALID_CREW_ID = UUID("eeeeeeee-0000-0000-0000-000000000099")

EXISTING_WP_ID = UUID("88888888-0000-0000-0000-000000000001")
NONEXISTENT_WP_ID = UUID("00000000-0000-0000-0000-000000000099")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_mock_work_package(**overrides):
    """Create a mock WorkPackage ORM instance."""
    from datetime import datetime, timezone
    defaults = {
        "work_package_id": EXISTING_WP_ID,
        "project_id": VALID_PROJECT_ID,
        "work_package_code": "WP-EXISTING-001",
        "title": "Existing Work Package",
        "work_type": "maintenance",
        "lifecycle_state": "draft",
        "priority": "normal",
        "client_id": VALID_CLIENT_ID,
        "site_id": VALID_SITE_ID,
        "client_name": None,
        "site_name": None,
        "primary_wbs_node_id": None,
        "scope_source_ref": None,
        "asset_class_id": None,
        "apparatus_cluster_ref": None,
        "assigned_crew_id": None,
        "assigned_crew_name": None,
        "scheduled_start_at": None,
        "scheduled_end_at": None,
        "actual_start_at": None,
        "actual_end_at": None,
        "progress_percent": None,
        "billing_state": None,
        "execution_summary": None,
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


def _make_mock_org_entity(entity_type: str, entity_id):
    mock = MagicMock()
    if entity_type == "Client":
        mock.client_id = entity_id
        mock.name = "Test Client"
    elif entity_type == "Site":
        mock.site_id = entity_id
        mock.name = "Test Site"
    return mock


def _make_mock_project(pk):
    from datetime import datetime, timezone
    mock = MagicMock()
    mock.project_id = pk
    mock.project_code = "PRJ-WP-PARENT"
    mock.title = "Parent Project"
    mock.created_at = datetime(2026, 4, 14, tzinfo=timezone.utc)
    mock.updated_at = datetime(2026, 4, 14, tzinfo=timezone.utc)
    return mock


def _make_mock_wbs_node(pk):
    mock = MagicMock()
    mock.wbs_node_id = pk
    mock.wbs_code = "WBS-1"
    mock.title = "WBS Node"
    return mock


def _make_mock_crew(pk):
    mock = MagicMock()
    mock.crew_id = pk
    mock.crew_code = "CREW-1"
    mock.name = "Test Crew"
    mock.is_active = True
    return mock


def _mock_db_for_wp_writes():
    """Mock DB supporting FK lookups across work/org/identity and WP writes."""
    from models.org import Client, Site, BusinessUnit, Contract
    from models.work import Project, WorkPackage, WBSNode
    from models.identity import Crew

    mock_db = MagicMock()
    created_wp = [None]

    def mock_get(model_class, pk):
        if model_class is Client:
            if pk == VALID_CLIENT_ID:
                return _make_mock_org_entity("Client", pk)
            return None
        if model_class is Site:
            if pk == VALID_SITE_ID:
                return _make_mock_org_entity("Site", pk)
            return None
        if model_class is BusinessUnit:
            return None
        if model_class is Contract:
            return None
        if model_class is Project:
            if pk == VALID_PROJECT_ID:
                return _make_mock_project(pk)
            return None
        if model_class is WBSNode:
            if pk == VALID_WBS_NODE_ID:
                return _make_mock_wbs_node(pk)
            return None
        if model_class is Crew:
            if pk == VALID_CREW_ID:
                return _make_mock_crew(pk)
            return None
        if model_class is WorkPackage:
            if pk == EXISTING_WP_ID:
                return _make_mock_work_package()
            return None
        return None

    mock_db.get = mock_get

    def mock_add(obj):
        created_wp[0] = obj

    def mock_commit():
        from datetime import datetime, timezone
        if created_wp[0] is not None:
            if (not hasattr(created_wp[0], "work_package_id")
                    or created_wp[0].work_package_id is None):
                created_wp[0].work_package_id = uuid4()
            if (not hasattr(created_wp[0], "created_at")
                    or created_wp[0].created_at is None):
                created_wp[0].created_at = datetime(
                    2026, 4, 14, tzinfo=timezone.utc
                )
            if (not hasattr(created_wp[0], "updated_at")
                    or created_wp[0].updated_at is None):
                created_wp[0].updated_at = datetime(
                    2026, 4, 14, tzinfo=timezone.utc
                )
            if (not hasattr(created_wp[0], "provenance_status")
                    or created_wp[0].provenance_status is None):
                created_wp[0].provenance_status = "curated"
            # Null out optional read fields that have no join
            for attr in [
                "client_name", "site_name", "assigned_crew_name",
                "scope_source_ref", "asset_class_id", "apparatus_cluster_ref",
                "assigned_crew_id", "primary_wbs_node_id",
                "scheduled_start_at", "scheduled_end_at",
                "actual_start_at", "actual_end_at",
                "progress_percent", "billing_state", "execution_summary",
            ]:
                if not hasattr(created_wp[0], attr):
                    setattr(created_wp[0], attr, None)

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
    mock_db = _mock_db_for_wp_writes()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Minimal valid create payload
# ---------------------------------------------------------------------------

VALID_WP_CREATE_PAYLOAD = {
    "project_id": str(VALID_PROJECT_ID),
    "work_package_code": "WP-001",
    "title": "New Work Package",
    "work_type": "maintenance",
    "client_id": str(VALID_CLIENT_ID),
    "site_id": str(VALID_SITE_ID),
}


# ---------------------------------------------------------------------------
# POST /api/v1/work/work-packages
# ---------------------------------------------------------------------------

class TestCreateWorkPackage:
    """Tests for POST /api/v1/work/work-packages."""

    def test_create_valid_work_package(self, client_write):
        resp = client_write.post(
            "/api/v1/work/work-packages",
            json=VALID_WP_CREATE_PAYLOAD,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["work_package_code"] == "WP-001"
        assert data["title"] == "New Work Package"
        assert data["project_id"] == str(VALID_PROJECT_ID)
        assert data["client_id"] == str(VALID_CLIENT_ID)
        assert data["site_id"] == str(VALID_SITE_ID)
        assert data["work_type"] == "maintenance"
        assert data["lifecycle_state"] == "draft"
        assert data["priority"] == "normal"

    def test_create_with_optional_crew(self, client_write):
        payload = {
            **VALID_WP_CREATE_PAYLOAD,
            "assigned_crew_id": str(VALID_CREW_ID),
        }
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 201

    def test_create_with_optional_wbs_node(self, client_write):
        payload = {
            **VALID_WP_CREATE_PAYLOAD,
            "primary_wbs_node_id": str(VALID_WBS_NODE_ID),
        }
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 201

    def test_create_invalid_client_id(self, client_write):
        payload = {**VALID_WP_CREATE_PAYLOAD, "client_id": str(INVALID_CLIENT_ID)}
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "errors" in data
        assert "client_id" in data["errors"]

    def test_create_invalid_site_id(self, client_write):
        payload = {**VALID_WP_CREATE_PAYLOAD, "site_id": str(INVALID_SITE_ID)}
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "site_id" in data["errors"]

    def test_create_invalid_project_id(self, client_write):
        payload = {**VALID_WP_CREATE_PAYLOAD, "project_id": str(INVALID_PROJECT_ID)}
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "project_id" in data["errors"]

    def test_create_invalid_wbs_node_id(self, client_write):
        payload = {
            **VALID_WP_CREATE_PAYLOAD,
            "primary_wbs_node_id": str(INVALID_WBS_NODE_ID),
        }
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "primary_wbs_node_id" in data["errors"]

    def test_create_invalid_crew_id(self, client_write):
        payload = {
            **VALID_WP_CREATE_PAYLOAD,
            "assigned_crew_id": str(INVALID_CREW_ID),
        }
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "assigned_crew_id" in data["errors"]

    def test_create_multiple_invalid_refs_merged(self, client_write):
        payload = {
            **VALID_WP_CREATE_PAYLOAD,
            "client_id": str(INVALID_CLIENT_ID),
            "project_id": str(INVALID_PROJECT_ID),
            "assigned_crew_id": str(INVALID_CREW_ID),
        }
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "client_id" in data["errors"]
        assert "project_id" in data["errors"]
        assert "assigned_crew_id" in data["errors"]

    def test_create_missing_required_fields(self, client_write):
        resp = client_write.post("/api/v1/work/work-packages", json={})
        assert resp.status_code == 422

    def test_create_missing_project_id(self, client_write):
        payload = {k: v for k, v in VALID_WP_CREATE_PAYLOAD.items()
                   if k != "project_id"}
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422

    def test_create_missing_work_type(self, client_write):
        payload = {k: v for k, v in VALID_WP_CREATE_PAYLOAD.items()
                   if k != "work_type"}
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422

    def test_create_empty_work_package_code(self, client_write):
        payload = {**VALID_WP_CREATE_PAYLOAD, "work_package_code": ""}
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422

    def test_create_empty_title(self, client_write):
        payload = {**VALID_WP_CREATE_PAYLOAD, "title": ""}
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422

    def test_create_progress_percent_over_100(self, client_write):
        payload = {**VALID_WP_CREATE_PAYLOAD, "progress_percent": 150.0}
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422

    def test_create_progress_percent_negative(self, client_write):
        payload = {**VALID_WP_CREATE_PAYLOAD, "progress_percent": -5.0}
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/v1/work/work-packages/{work_package_id}
# ---------------------------------------------------------------------------

class TestUpdateWorkPackage:
    """Tests for PATCH /api/v1/work/work-packages/{work_package_id}."""

    def test_update_title(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{EXISTING_WP_ID}",
            json={"title": "Updated WP Title"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["work_package_id"] == str(EXISTING_WP_ID)

    def test_update_with_valid_crew(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{EXISTING_WP_ID}",
            json={"assigned_crew_id": str(VALID_CREW_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_invalid_crew(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{EXISTING_WP_ID}",
            json={"assigned_crew_id": str(INVALID_CREW_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "assigned_crew_id" in data["errors"]

    def test_update_with_invalid_project(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{EXISTING_WP_ID}",
            json={"project_id": str(INVALID_PROJECT_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "project_id" in data["errors"]

    def test_update_with_invalid_wbs_node(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{EXISTING_WP_ID}",
            json={"primary_wbs_node_id": str(INVALID_WBS_NODE_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "primary_wbs_node_id" in data["errors"]

    def test_update_with_invalid_client(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{EXISTING_WP_ID}",
            json={"client_id": str(INVALID_CLIENT_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "client_id" in data["errors"]

    def test_update_nonexistent_work_package(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{NONEXISTENT_WP_ID}",
            json={"title": "Nope"},
        )
        assert resp.status_code == 404

    def test_update_empty_body(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{EXISTING_WP_ID}",
            json={},
        )
        assert resp.status_code == 200

    def test_update_progress_percent_in_range(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{EXISTING_WP_ID}",
            json={"progress_percent": 42.5},
        )
        assert resp.status_code == 200

    def test_update_progress_percent_out_of_range(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{EXISTING_WP_ID}",
            json={"progress_percent": 250.0},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Read endpoints still work (regression safety-net)
# ---------------------------------------------------------------------------

class TestReadEndpointsUnaffected:
    """Verify existing GET endpoints remain functional under the write-mock DB."""

    def test_list_work_packages_still_works(self, client_write):
        resp = client_write.get("/api/v1/work/work-packages")
        assert resp.status_code == 200

    def test_get_work_package_404_still_works(self, client_write):
        resp = client_write.get(f"/api/v1/work/work-packages/{uuid4()}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Packet 013j — Write response crew/org name enrichment
# ---------------------------------------------------------------------------

class TestWorkPackageResponseEnrichment:
    """POST/PATCH responses expose assigned_crew_name / client_name /
    site_name, sourced from the same identity- and org-joined name
    contracts the read path already exposes (packets 012e / 012h).

    Enrichment uses db.get() lookups against the mock's FK-aware
    dispatcher — identical to the real PG behavior because SQLAlchemy
    caches via its identity map.
    """

    def test_create_without_crew_sets_assigned_crew_name_none(self, client_write):
        resp = client_write.post(
            "/api/v1/work/work-packages",
            json=VALID_WP_CREATE_PAYLOAD,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["assigned_crew_name"] is None
        # client_name and site_name hydrate from the valid org FKs
        assert data["client_name"] == "Test Client"
        assert data["site_name"] == "Test Site"

    def test_create_with_crew_surfaces_assigned_crew_name(self, client_write):
        payload = {
            **VALID_WP_CREATE_PAYLOAD,
            "assigned_crew_id": str(VALID_CREW_ID),
        }
        resp = client_write.post("/api/v1/work/work-packages", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["assigned_crew_id"] == str(VALID_CREW_ID)
        assert data["assigned_crew_name"] == "Test Crew"
        assert data["client_name"] == "Test Client"
        assert data["site_name"] == "Test Site"

    def test_patch_with_new_crew_surfaces_updated_crew_name(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{EXISTING_WP_ID}",
            json={"assigned_crew_id": str(VALID_CREW_ID)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["assigned_crew_id"] == str(VALID_CREW_ID)
        assert data["assigned_crew_name"] == "Test Crew"

    def test_patch_title_only_still_hydrates_org_names(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{EXISTING_WP_ID}",
            json={"title": "New Title Only"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # No crew assigned on the existing mock WP → name stays None
        assert data["assigned_crew_name"] is None
        # Client / site hydrate from the mock's existing FKs
        assert data["client_name"] == "Test Client"
        assert data["site_name"] == "Test Site"

    def test_patch_empty_body_still_hydrates_response(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/work-packages/{EXISTING_WP_ID}",
            json={},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["assigned_crew_name"] is None
        assert data["client_name"] == "Test Client"
        assert data["site_name"] == "Test Site"
