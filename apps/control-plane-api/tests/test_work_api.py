"""
PM/Work Domain — Read-Only API Tests
=====================================
Packet: 2026-04-13-pm-schema-010b

These tests verify:
  1. All 11 read-only endpoints are mounted and respond correctly
  2. GET-by-ID returns 404 for non-existent resources
  3. List endpoints return empty lists when the work schema has no data
  4. No write endpoints exist (POST/PUT/PATCH/DELETE return 405)
  5. Pagination parameters are validated (limit, offset bounds)
  6. Router is correctly mounted at /api/v1/work/ prefix

Tests use a mock database session to avoid requiring a live
database connection.  The mock returns empty results for list queries
and None for get-by-id queries, verifying the endpoints serialize
correctly and handle missing resources appropriately.
"""

import sys
import os
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

# Ensure the app root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from config import get_db
from main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _mock_db_empty():
    """Create a mock DB session that returns empty query results."""
    mock_db = MagicMock()
    # Chain: db.query(Model).options(...).filter(...).order_by(...).offset(...).limit(...).all() → []
    mock_query = MagicMock()
    mock_query.options.return_value = mock_query     # packet 012f: joinedload(...)
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []
    # Packet 012f: get_work_package now uses query(...).one_or_none()
    mock_query.one_or_none.return_value = None
    mock_db.query.return_value = mock_query
    # db.get(Model, pk) → None
    mock_db.get.return_value = None
    return mock_db


@pytest.fixture
def client():
    """TestClient with mocked empty database."""
    mock_db = _mock_db_empty()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. Router Mount Verification
# ---------------------------------------------------------------------------

class TestRouterMount:
    """Verify the work router is mounted and discoverable."""

    def test_work_routes_exist(self, client):
        """Work routes should appear in the OpenAPI schema."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        paths = resp.json()["paths"]
        work_paths = [p for p in paths if p.startswith("/api/v1/work")]
        # 13 distinct paths expected (packet 016 adds /dependencies/{id})
        assert len(work_paths) >= 13, f"Expected >=13 work paths, got {len(work_paths)}: {work_paths}"

    def test_work_tag_on_endpoints(self, client):
        """The 'work' tag should be present on work endpoints in the OpenAPI spec."""
        resp = client.get("/openapi.json")
        paths = resp.json()["paths"]
        # Check that at least one work endpoint has the 'work' tag
        found_work_tag = False
        for path, methods in paths.items():
            if path.startswith("/api/v1/work"):
                for method, spec in methods.items():
                    if "work" in spec.get("tags", []):
                        found_work_tag = True
                        break
        assert found_work_tag, "No work endpoints found with 'work' tag"


# ---------------------------------------------------------------------------
# 2. List Endpoints — Empty Results (Happy Path)
# ---------------------------------------------------------------------------

class TestListEndpointsEmpty:
    """Verify list endpoints return empty arrays when no data exists."""

    def test_list_projects(self, client):
        resp = client.get("/api/v1/work/projects")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_wbs_nodes(self, client):
        resp = client.get("/api/v1/work/wbs-nodes")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_work_packages(self, client):
        resp = client.get("/api/v1/work/work-packages")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_tasks(self, client):
        resp = client.get("/api/v1/work/tasks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_dependencies(self, client):
        resp = client.get("/api/v1/work/dependencies")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_assignments(self, client):
        resp = client.get("/api/v1/work/assignments")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_execution_issues(self, client):
        resp = client.get("/api/v1/work/execution-issues")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_progress_snapshots(self, client):
        resp = client.get("/api/v1/work/progress-snapshots")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# 3. Get-by-ID — 404 for Non-Existent Resources
# ---------------------------------------------------------------------------

class TestGetByIdNotFound:
    """Verify get-by-id endpoints return 404 when the resource doesn't exist."""

    def test_project_not_found(self, client):
        resp = client.get(f"/api/v1/work/projects/{uuid4()}")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_work_package_not_found(self, client):
        resp = client.get(f"/api/v1/work/work-packages/{uuid4()}")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_task_not_found(self, client):
        resp = client.get(f"/api/v1/work/tasks/{uuid4()}")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 4. Filter Parameters — Query Strings Accepted
# ---------------------------------------------------------------------------

class TestFilterParameters:
    """Verify filter query parameters are accepted without error."""

    def test_wbs_nodes_filter_by_project(self, client):
        resp = client.get(f"/api/v1/work/wbs-nodes?project_id={uuid4()}")
        assert resp.status_code == 200

    def test_work_packages_filter_by_project(self, client):
        resp = client.get(f"/api/v1/work/work-packages?project_id={uuid4()}")
        assert resp.status_code == 200

    def test_tasks_filter_by_work_package(self, client):
        resp = client.get(f"/api/v1/work/tasks?work_package_id={uuid4()}")
        assert resp.status_code == 200

    def test_dependencies_filter_by_predecessor(self, client):
        resp = client.get(f"/api/v1/work/dependencies?predecessor_task_id={uuid4()}")
        assert resp.status_code == 200

    def test_assignments_filter_by_task(self, client):
        resp = client.get(f"/api/v1/work/assignments?task_id={uuid4()}")
        assert resp.status_code == 200

    def test_execution_issues_filter_by_wp(self, client):
        resp = client.get(f"/api/v1/work/execution-issues?work_package_id={uuid4()}")
        assert resp.status_code == 200

    def test_progress_snapshots_filter_by_project(self, client):
        resp = client.get(f"/api/v1/work/progress-snapshots?project_id={uuid4()}")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 5. Pagination Parameter Validation
# ---------------------------------------------------------------------------

class TestPaginationValidation:
    """Verify pagination bounds are enforced."""

    def test_negative_offset_rejected(self, client):
        resp = client.get("/api/v1/work/projects?offset=-1")
        assert resp.status_code == 422

    def test_zero_limit_rejected(self, client):
        resp = client.get("/api/v1/work/projects?limit=0")
        assert resp.status_code == 422

    def test_excessive_limit_rejected(self, client):
        resp = client.get("/api/v1/work/projects?limit=999")
        assert resp.status_code == 422

    def test_valid_pagination_accepted(self, client):
        resp = client.get("/api/v1/work/projects?limit=10&offset=5")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 6. Read-Only Enforcement — No Write Methods
# ---------------------------------------------------------------------------

class TestReadOnlyEnforcement:
    """Verify write methods are rejected for entities that remain read-only.

    Note:
      - POST /projects and PATCH /projects/{id} are allowed (packet 011f)
      - POST /work-packages and PATCH /work-packages/{id} are allowed
        (packet 013)
      - POST /tasks and PATCH /tasks/{id} are allowed (packet 014)
      - POST /assignments and PATCH /assignments/{id} are allowed
        (packet 015)
      - POST /dependencies and PATCH /dependencies/{id} are allowed
        (packet 016)
      - POST /execution-issues and PATCH /execution-issues/{id} are
        allowed (packet 017)
    This test verifies progress-snapshot entities remain read-only and
    that PUT/DELETE are rejected everywhere.
    """

    # Entities that must remain read-only (packet 018 keeps WBS nodes
    # closed; progress-snapshots POST/PATCH was opened by packet 018 so
    # /wbs-nodes is the only remaining read-only PM write target)
    READ_ONLY_TARGETS = [
        "/api/v1/work/wbs-nodes",
    ]

    # Paths now open to writes (must continue to support those methods
    # but reject all non-allowed write methods)
    WRITE_OPEN_TARGETS = [
        "/api/v1/work/projects",
        "/api/v1/work/work-packages",
        "/api/v1/work/tasks",
        "/api/v1/work/assignments",
        "/api/v1/work/dependencies",
        "/api/v1/work/execution-issues",
        "/api/v1/work/progress-snapshots",
    ]

    def test_post_rejected(self, client):
        for path in self.READ_ONLY_TARGETS:
            resp = client.post(path, json={})
            assert resp.status_code == 405, f"POST {path} should be 405, got {resp.status_code}"

    def test_put_rejected(self, client):
        all_targets = self.WRITE_OPEN_TARGETS + self.READ_ONLY_TARGETS
        for path in all_targets:
            resp = client.put(path, json={})
            assert resp.status_code == 405, f"PUT {path} should be 405, got {resp.status_code}"

    def test_delete_rejected(self, client):
        all_targets = self.WRITE_OPEN_TARGETS + self.READ_ONLY_TARGETS
        for path in all_targets:
            resp = client.delete(path)
            assert resp.status_code == 405, f"DELETE {path} should be 405, got {resp.status_code}"

    def test_patch_rejected(self, client):
        for path in self.READ_ONLY_TARGETS:
            resp = client.patch(path, json={})
            assert resp.status_code == 405, f"PATCH {path} should be 405, got {resp.status_code}"


# ---------------------------------------------------------------------------
# 7. Endpoint Count Verification
# ---------------------------------------------------------------------------

class TestEndpointInventory:
    """Verify the exact endpoint inventory matches the packet spec."""

    EXPECTED_ENDPOINTS = [
        ("GET", "/api/v1/work/projects"),
        ("GET", "/api/v1/work/projects/{project_id}"),
        ("POST", "/api/v1/work/projects"),                   # packet 011f
        ("PATCH", "/api/v1/work/projects/{project_id}"),     # packet 011f
        ("GET", "/api/v1/work/wbs-nodes"),
        ("GET", "/api/v1/work/work-packages"),
        ("GET", "/api/v1/work/work-packages/{work_package_id}"),
        ("POST", "/api/v1/work/work-packages"),                              # packet 013
        ("PATCH", "/api/v1/work/work-packages/{work_package_id}"),           # packet 013
        ("GET", "/api/v1/work/tasks"),
        ("GET", "/api/v1/work/tasks/{task_id}"),
        ("POST", "/api/v1/work/tasks"),                                      # packet 014
        ("PATCH", "/api/v1/work/tasks/{task_id}"),                           # packet 014
        ("GET", "/api/v1/work/dependencies"),
        ("POST", "/api/v1/work/dependencies"),                               # packet 016
        ("PATCH", "/api/v1/work/dependencies/{dependency_id}"),              # packet 016
        ("GET", "/api/v1/work/assignments"),
        ("POST", "/api/v1/work/assignments"),                                # packet 015
        ("PATCH", "/api/v1/work/assignments/{assignment_id}"),               # packet 015
        ("GET", "/api/v1/work/execution-issues"),
        ("POST", "/api/v1/work/execution-issues"),                           # packet 017
        ("PATCH", "/api/v1/work/execution-issues/{execution_issue_id}"),     # packet 017
        ("GET", "/api/v1/work/progress-snapshots"),
        ("POST", "/api/v1/work/progress-snapshots"),                                  # packet 018
        ("PATCH", "/api/v1/work/progress-snapshots/{progress_snapshot_id}"),          # packet 018
    ]

    def test_all_expected_endpoints_exist(self, client):
        resp = client.get("/openapi.json")
        paths = resp.json()["paths"]
        for method, path in self.EXPECTED_ENDPOINTS:
            assert path in paths, f"Missing path: {path}"
            assert method.lower() in paths[path], (
                f"Missing method {method} on {path}"
            )

    def test_no_write_endpoints_on_non_project_entities(self, client):
        """Ensure no write endpoints exist on entities that should remain
        read-only.

        Projects are allowed POST and PATCH (packet 011f).
        Work packages are allowed POST and PATCH (packet 013).
        Tasks are allowed POST and PATCH (packet 014).
        Assignments are allowed POST and PATCH (packet 015).
        Dependencies are allowed POST and PATCH (packet 016).
        Execution issues are allowed POST and PATCH (packet 017).
        Progress snapshots are allowed POST and PATCH (packet 018).
        Only WBS nodes remain read-only.
        """
        resp = client.get("/openapi.json")
        paths = resp.json()["paths"]
        write_methods = {"post", "put", "patch", "delete"}
        # Paths that are allowed to have write methods
        write_allowed = {
            "/api/v1/work/projects": {"post"},                                      # packet 011f
            "/api/v1/work/projects/{project_id}": {"patch"},                        # packet 011f
            "/api/v1/work/work-packages": {"post"},                                 # packet 013
            "/api/v1/work/work-packages/{work_package_id}": {"patch"},              # packet 013
            "/api/v1/work/tasks": {"post"},                                         # packet 014
            "/api/v1/work/tasks/{task_id}": {"patch"},                              # packet 014
            "/api/v1/work/assignments": {"post"},                                   # packet 015
            "/api/v1/work/assignments/{assignment_id}": {"patch"},                  # packet 015
            "/api/v1/work/dependencies": {"post"},                                  # packet 016
            "/api/v1/work/dependencies/{dependency_id}": {"patch"},                 # packet 016
            "/api/v1/work/execution-issues": {"post"},                              # packet 017
            "/api/v1/work/execution-issues/{execution_issue_id}": {"patch"},        # packet 017
            "/api/v1/work/progress-snapshots": {"post"},                            # packet 018
            "/api/v1/work/progress-snapshots/{progress_snapshot_id}": {"patch"},    # packet 018
        }
        for path, methods in paths.items():
            if path.startswith("/api/v1/work"):
                allowed = write_allowed.get(path, set())
                for m in write_methods:
                    if m not in allowed:
                        assert m not in methods, (
                            f"Unexpected write method {m.upper()} found on {path}"
                        )
