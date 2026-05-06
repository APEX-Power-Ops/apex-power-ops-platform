"""
Ops Router — Project Apparatus Summary View Unit Tests
======================================================

Covers the read-only ``GET /api/v1/ops/project-apparatus-summary`` surface at
the FastAPI TestClient level without requiring a live PostgreSQL. The route is
dependency-overridden with a fake session so the test only validates routing,
shape, and bounded query behavior.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from config import get_db  # noqa: E402


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _FakeDB:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, statement, params):
        self.calls.append((str(statement), params))
        return _FakeResult(self.rows)


@pytest.fixture
def client():
    os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
    from main import app

    fake_rows = [
        {
            "project_id": "33333333-0000-0000-0000-000000000001",
            "project_number": "LASNAP16",
            "project_name": "LASNAP Foods - Annual Maintenance Testing 2016",
            "scope_id": "44444444-0000-0000-0000-000000000001",
            "scope_name": "Main Substation Testing",
            "total_apparatus": 15,
            "total_completed": 0,
            "total_remaining": 15,
            "completion_percent": 0.0,
            "ready_to_work": 0,
            "blocked": 15,
            "issues_failed": 0,
            "past_due": 0,
            "due_this_week": 0,
            "total_quoted_hours": 96.0,
            "total_actual_hours": 0.0,
            "remaining_hours": 96.0,
        }
    ]
    fake_db = _FakeDB(fake_rows)

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app), fake_db
    app.dependency_overrides.clear()


class TestOpsProjectApparatusSummaryEndpointMounting:
    def test_endpoint_responds_200(self, client):
        test_client, _ = client
        response = test_client.get("/api/v1/ops/project-apparatus-summary")
        assert response.status_code == 200

    def test_endpoint_not_under_work_prefix(self, client):
        test_client, _ = client
        response = test_client.get("/api/v1/work/project-apparatus-summary")
        assert response.status_code == 404

    def test_endpoint_is_get_only(self, client):
        test_client, _ = client
        response = test_client.post("/api/v1/ops/project-apparatus-summary")
        assert response.status_code == 405


class TestOpsProjectApparatusSummaryShape:
    def test_response_returns_expected_fields(self, client):
        test_client, _ = client
        body = test_client.get("/api/v1/ops/project-apparatus-summary").json()
        assert len(body) == 1
        assert set(body[0].keys()) == {
            "project_id",
            "project_number",
            "project_name",
            "scope_id",
            "scope_name",
            "total_apparatus",
            "total_completed",
            "total_remaining",
            "completion_percent",
            "ready_to_work",
            "blocked",
            "issues_failed",
            "past_due",
            "due_this_week",
            "total_quoted_hours",
            "total_actual_hours",
            "remaining_hours",
        }

    def test_limit_parameter_is_forwarded_to_query(self, client):
        test_client, fake_db = client
        response = test_client.get("/api/v1/ops/project-apparatus-summary?limit=11")
        assert response.status_code == 200
        assert fake_db.calls[-1][1] == {"limit": 11}


class TestOpsProjectApparatusSummaryScopeGuards:
    def test_non_get_verbs_are_rejected(self, client):
        test_client, _ = client
        for method in ("post", "put", "patch", "delete"):
            response = getattr(test_client, method)("/api/v1/ops/project-apparatus-summary")
            assert response.status_code == 405