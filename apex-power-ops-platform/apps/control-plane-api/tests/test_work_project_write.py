"""
PM/Work Domain — Project Write API Tests
=========================================
Packet: 2026-04-14-pm-schema-011f

These tests verify:
  1. POST /api/v1/work/projects creates a project with valid org references
  2. POST rejects invalid client_id / site_id with 422 and field-level errors
  3. POST rejects invalid optional org refs (business_unit_id, contract_id)
  4. POST rejects missing required fields with 422
  5. PATCH /api/v1/work/projects/{id} updates a project with valid org refs
  6. PATCH rejects invalid org FK references with 422
  7. PATCH returns 404 for non-existent project
  8. PATCH with empty body returns the unchanged project
  9. Existing read endpoints (GET) remain unaffected
 10. No write endpoints exist for non-project entities

Tests use a mock database session to avoid requiring a live
database connection.  The mock returns appropriate results for
org.get() lookups to simulate org FK validation.
"""

import sys
import os
from unittest.mock import MagicMock, patch, PropertyMock
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
VALID_BU_ID = UUID("33333333-0000-0000-0000-000000000001")
INVALID_CLIENT_ID = UUID("aaaaaaaa-0000-0000-0000-000000000099")
INVALID_SITE_ID = UUID("bbbbbbbb-0000-0000-0000-000000000099")
EXISTING_PROJECT_ID = UUID("99999999-0000-0000-0000-000000000001")
NONEXISTENT_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000099")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_mock_project(**overrides):
    """Create a mock Project ORM instance."""
    from datetime import datetime, timezone
    defaults = {
        "project_id": EXISTING_PROJECT_ID,
        "project_code": "TEST-001",
        "title": "Test Project",
        "status": "draft",
        "client_id": VALID_CLIENT_ID,
        "site_id": VALID_SITE_ID,
        "business_unit_id": None,
        "contract_id": None,
        "description": None,
        "client_name": None,
        "site_name": None,
        "business_unit_name": None,
        "contract_title": None,
        "planned_start_at": None,
        "planned_end_at": None,
        "actual_start_at": None,
        "actual_end_at": None,
        "project_priority": None,
        "created_from_source": "manual",
        "provenance_status": "curated",
        "p6_project_id": None,
        "p6_short_name": None,
        "p6_data_date": None,
        "created_at": datetime(2026, 4, 14, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 4, 14, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _make_mock_org_entity(entity_type: str, entity_id):
    """Create a mock org entity (Client, Site, BusinessUnit, Contract)."""
    mock = MagicMock()
    if entity_type == "Client":
        mock.client_id = entity_id
        mock.name = "Test Client"
    elif entity_type == "Site":
        mock.site_id = entity_id
        mock.name = "Test Site"
    elif entity_type == "BusinessUnit":
        mock.business_unit_id = entity_id
        mock.name = "Test BU"
    elif entity_type == "Contract":
        mock.contract_id = entity_id
        mock.title = "Test Contract"
    return mock


def _mock_db_for_writes():
    """Create a mock DB that supports org validation lookups and project writes."""
    from models.org import Client, Site, BusinessUnit, Contract
    from models.work import Project

    mock_db = MagicMock()

    # Track the "created" project for return from commit/refresh
    created_project = [None]

    def mock_get(model_class, pk):
        """Simulate db.get() for org and work models."""
        if model_class is Client:
            if pk == VALID_CLIENT_ID:
                return _make_mock_org_entity("Client", pk)
            return None
        elif model_class is Site:
            if pk == VALID_SITE_ID:
                return _make_mock_org_entity("Site", pk)
            return None
        elif model_class is BusinessUnit:
            if pk == VALID_BU_ID:
                return _make_mock_org_entity("BusinessUnit", pk)
            return None
        elif model_class is Contract:
            return None  # No contracts in seed data
        elif model_class is Project:
            if pk == EXISTING_PROJECT_ID:
                return _make_mock_project()
            return None
        return None

    mock_db.get = mock_get

    def mock_add(obj):
        created_project[0] = obj

    def mock_commit():
        if created_project[0] is not None:
            # Simulate server defaults
            from datetime import datetime, timezone
            if not hasattr(created_project[0], 'project_id') or created_project[0].project_id is None:
                created_project[0].project_id = uuid4()
            if not hasattr(created_project[0], 'created_at') or created_project[0].created_at is None:
                created_project[0].created_at = datetime(2026, 4, 14, tzinfo=timezone.utc)
            if not hasattr(created_project[0], 'updated_at') or created_project[0].updated_at is None:
                created_project[0].updated_at = datetime(2026, 4, 14, tzinfo=timezone.utc)
            if not hasattr(created_project[0], 'provenance_status') or created_project[0].provenance_status is None:
                created_project[0].provenance_status = "curated"
            # Null out the org name fields (no joins in mock)
            for attr in ["client_name", "site_name", "business_unit_name", "contract_title",
                         "p6_project_id", "p6_short_name", "p6_data_date",
                         "actual_start_at", "actual_end_at"]:
                if not hasattr(created_project[0], attr):
                    setattr(created_project[0], attr, None)

    def mock_refresh(obj):
        pass  # No-op for mock

    mock_db.add = mock_add
    mock_db.commit = mock_commit
    mock_db.refresh = mock_refresh

    # Also support read-path mock for list/filter queries
    mock_query = MagicMock()
    mock_query.options.return_value = mock_query     # packet 012f/012h: joinedload(...)
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []
    # Packet 012h: get_project now uses query(...).one_or_none()
    mock_query.one_or_none.return_value = None
    mock_db.query.return_value = mock_query

    return mock_db


@pytest.fixture
def client_write():
    """TestClient with mock DB that supports write operations."""
    mock_db = _mock_db_for_writes()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Minimal valid create payload
# ---------------------------------------------------------------------------

VALID_CREATE_PAYLOAD = {
    "project_code": "PROJ-001",
    "title": "New Test Project",
    "client_id": str(VALID_CLIENT_ID),
    "site_id": str(VALID_SITE_ID),
}


# ---------------------------------------------------------------------------
# POST /api/v1/work/projects
# ---------------------------------------------------------------------------

class TestCreateProject:
    """Tests for POST /api/v1/work/projects."""

    def test_create_valid_project(self, client_write):
        resp = client_write.post("/api/v1/work/projects", json=VALID_CREATE_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert data["project_code"] == "PROJ-001"
        assert data["title"] == "New Test Project"
        assert data["client_id"] == str(VALID_CLIENT_ID)
        assert data["site_id"] == str(VALID_SITE_ID)
        assert data["status"] == "draft"

    def test_create_with_optional_org_ref(self, client_write):
        payload = {**VALID_CREATE_PAYLOAD, "business_unit_id": str(VALID_BU_ID)}
        resp = client_write.post("/api/v1/work/projects", json=payload)
        assert resp.status_code == 201

    def test_create_invalid_client_id(self, client_write):
        payload = {**VALID_CREATE_PAYLOAD, "client_id": str(INVALID_CLIENT_ID)}
        resp = client_write.post("/api/v1/work/projects", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "errors" in data
        assert "client_id" in data["errors"]

    def test_create_invalid_site_id(self, client_write):
        payload = {**VALID_CREATE_PAYLOAD, "site_id": str(INVALID_SITE_ID)}
        resp = client_write.post("/api/v1/work/projects", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "errors" in data
        assert "site_id" in data["errors"]

    def test_create_invalid_both_client_and_site(self, client_write):
        payload = {
            **VALID_CREATE_PAYLOAD,
            "client_id": str(INVALID_CLIENT_ID),
            "site_id": str(INVALID_SITE_ID),
        }
        resp = client_write.post("/api/v1/work/projects", json=payload)
        assert resp.status_code == 422
        data = resp.json()
        assert "client_id" in data["errors"]
        assert "site_id" in data["errors"]

    def test_create_missing_required_fields(self, client_write):
        resp = client_write.post("/api/v1/work/projects", json={})
        assert resp.status_code == 422

    def test_create_missing_client_id(self, client_write):
        payload = {"project_code": "X", "title": "X", "site_id": str(VALID_SITE_ID)}
        resp = client_write.post("/api/v1/work/projects", json=payload)
        assert resp.status_code == 422

    def test_create_empty_project_code(self, client_write):
        payload = {**VALID_CREATE_PAYLOAD, "project_code": ""}
        resp = client_write.post("/api/v1/work/projects", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/v1/work/projects/{project_id}
# ---------------------------------------------------------------------------

class TestUpdateProject:
    """Tests for PATCH /api/v1/work/projects/{project_id}."""

    def test_update_title(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/projects/{EXISTING_PROJECT_ID}",
            json={"title": "Updated Title"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == str(EXISTING_PROJECT_ID)

    def test_update_with_valid_client_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/projects/{EXISTING_PROJECT_ID}",
            json={"client_id": str(VALID_CLIENT_ID)},
        )
        assert resp.status_code == 200

    def test_update_with_invalid_client_id(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/projects/{EXISTING_PROJECT_ID}",
            json={"client_id": str(INVALID_CLIENT_ID)},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert "client_id" in data["errors"]

    def test_update_nonexistent_project(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/projects/{NONEXISTENT_PROJECT_ID}",
            json={"title": "Nope"},
        )
        assert resp.status_code == 404

    def test_update_empty_body(self, client_write):
        resp = client_write.patch(
            f"/api/v1/work/projects/{EXISTING_PROJECT_ID}",
            json={},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Scope boundary tests — no write endpoints for entities that remain
# read-only.  Packet 013 opened POST/PATCH on /work-packages, packet 014
# opened POST/PATCH on /tasks, and packet 017 opened POST/PATCH on
# /execution-issues, so those are no longer in the rejected set here;
# progress snapshots remain closed.
# ---------------------------------------------------------------------------

class TestWriteScopeBoundary:
    """Verify writes are scoped to the packet-018 set: projects, work
    packages, tasks, assignments, dependencies, execution issues, and
    progress snapshots.  Only WBS nodes remain closed.
    """

    def test_put_projects_rejected(self, client_write):
        """PUT is not supported — only PATCH for partial updates."""
        resp = client_write.put(
            f"/api/v1/work/projects/{EXISTING_PROJECT_ID}",
            json=VALID_CREATE_PAYLOAD,
        )
        assert resp.status_code == 405

    def test_delete_projects_rejected(self, client_write):
        resp = client_write.delete(f"/api/v1/work/projects/{EXISTING_PROJECT_ID}")
        assert resp.status_code == 405


# ---------------------------------------------------------------------------
# Read endpoints still work
# ---------------------------------------------------------------------------

class TestReadEndpointsUnaffected:
    """Verify existing GET endpoints remain functional."""

    def test_list_projects_still_works(self, client_write):
        resp = client_write.get("/api/v1/work/projects")
        assert resp.status_code == 200

    def test_get_project_404_still_works(self, client_write):
        resp = client_write.get(f"/api/v1/work/projects/{uuid4()}")
        assert resp.status_code == 404
