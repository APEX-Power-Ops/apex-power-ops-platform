"""
Ops Router — Schedule Health View Unit Tests
============================================

Covers the read-only ``GET /api/v1/ops/schedule-health`` surface at the
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
            "project_number": "LASNAP16",
            "project_name": "LASNAP Foods - Annual Maintenance Testing 2016",
            "project_due": date(2026, 6, 5),
            "scope_name": "Main Substation Testing",
            "scope_due": date(2026, 5, 28),
            "percent_complete": 42.5,
            "overdue_items": 3,
            "on_hold_items": 2,
            "not_available_items": 5,
            "health_status": "At Risk",
        }
    ]
    fake_db = _FakeDB(fake_rows)

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app), fake_db
    app.dependency_overrides.clear()


class TestOpsScheduleHealthEndpointMounting:
    def test_endpoint_responds_200(self, client):
        test_client, _ = client
        response = test_client.get("/api/v1/ops/schedule-health")
        assert response.status_code == 200

    def test_endpoint_not_under_work_prefix(self, client):
        test_client, _ = client
        response = test_client.get("/api/v1/work/schedule-health")
        assert response.status_code == 404

    def test_endpoint_is_get_only(self, client):
        test_client, _ = client
        response = test_client.post("/api/v1/ops/schedule-health")
        assert response.status_code == 405


class TestOpsScheduleHealthShape:
    def test_response_returns_expected_fields(self, client):
        test_client, _ = client
        body = test_client.get("/api/v1/ops/schedule-health").json()
        assert len(body) == 1
        assert set(body[0].keys()) == {
            "project_number",
            "project_name",
            "project_due",
            "scope_name",
            "scope_due",
            "percent_complete",
            "overdue_items",
            "on_hold_items",
            "not_available_items",
            "health_status",
        }

    def test_limit_parameter_is_forwarded_to_query(self, client):
        test_client, fake_db = client
        response = test_client.get("/api/v1/ops/schedule-health?limit=9")
        assert response.status_code == 200
        assert fake_db.calls[-1][1] == {"limit": 9}


class TestOpsScheduleHealthScopeGuards:
    def test_non_get_verbs_are_rejected(self, client):
        test_client, _ = client
        for method in ("post", "put", "patch", "delete"):
            response = getattr(test_client, method)("/api/v1/ops/schedule-health")
            assert response.status_code == 405