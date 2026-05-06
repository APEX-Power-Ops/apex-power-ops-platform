"""
Ops Router — Master Operations View Unit Tests
==============================================

Covers the read-only ``GET /api/v1/ops/master-operations`` surface at the
FastAPI TestClient level without requiring a live PostgreSQL. The route is
dependency-overridden with a fake session so the test only validates routing,
shape, and bounded query behavior.
"""

from __future__ import annotations

import os
import sys
from datetime import date

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
            "project_id": "11111111-1111-1111-1111-111111111111",
            "project_number": "LASNAP16",
            "project_name": "LASNAP16 Modernization",
            "project_status": "Active",
            "client_name": "RESA Power",
            "resa_location": "Phoenix",
            "site_city": "Mesa",
            "project_due": date(2026, 5, 30),
            "scope_count": 3,
            "total_apparatus": 47,
            "completed": 12,
            "remaining": 35,
            "completion_percent": 25.53,
            "ready_to_work": 18,
            "on_hold": 4,
            "not_available": 13,
            "issues": 2,
            "overdue": 1,
            "due_today": 0,
            "due_this_week": 5,
            "ready_hours": 96.0,
            "remaining_hours": 224.0,
            "health_status": "AT RISK",
        }
    ]
    fake_db = _FakeDB(fake_rows)

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app), fake_db
    app.dependency_overrides.clear()


class TestOpsMasterOperationsEndpointMounting:
    def test_endpoint_responds_200(self, client):
        test_client, _ = client
        response = test_client.get("/api/v1/ops/master-operations")
        assert response.status_code == 200

    def test_endpoint_not_under_work_prefix(self, client):
        test_client, _ = client
        response = test_client.get("/api/v1/work/master-operations")
        assert response.status_code == 404

    def test_endpoint_is_get_only(self, client):
        test_client, _ = client
        response = test_client.post("/api/v1/ops/master-operations")
        assert response.status_code == 405


class TestOpsMasterOperationsShape:
    def test_response_returns_expected_fields(self, client):
        test_client, _ = client
        body = test_client.get("/api/v1/ops/master-operations").json()
        assert len(body) == 1
        assert set(body[0].keys()) == {
            "project_id",
            "project_number",
            "project_name",
            "project_status",
            "client_name",
            "resa_location",
            "site_city",
            "project_due",
            "scope_count",
            "total_apparatus",
            "completed",
            "remaining",
            "completion_percent",
            "ready_to_work",
            "on_hold",
            "not_available",
            "issues",
            "overdue",
            "due_today",
            "due_this_week",
            "ready_hours",
            "remaining_hours",
            "health_status",
        }

    def test_limit_parameter_is_forwarded_to_query(self, client):
        test_client, fake_db = client
        response = test_client.get("/api/v1/ops/master-operations?limit=7")
        assert response.status_code == 200
        assert fake_db.calls[-1][1] == {"limit": 7}


class TestOpsMasterOperationsScopeGuards:
    def test_non_get_verbs_are_rejected(self, client):
        test_client, _ = client
        for method in ("post", "put", "patch", "delete"):
            response = getattr(test_client, method)("/api/v1/ops/master-operations")
            assert response.status_code == 405