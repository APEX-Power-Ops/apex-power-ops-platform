"""
Ops Router — Apparatus By Category View Unit Tests
==================================================

Covers the read-only ``GET /api/v1/ops/apparatus-by-category`` surface at the
FastAPI TestClient level without requiring a live PostgreSQL. The route is
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
            "scope_id": "44444444-0000-0000-0000-000000000001",
            "scope_name": "Main Substation Testing",
            "apparatus_category": "Circuit Breaker",
            "total_count": 6,
            "completed": 0,
            "remaining": 6,
            "percent_complete": 0.0,
            "ready_to_work": 0,
            "blocked": 6,
        }
    ]
    fake_db = _FakeDB(fake_rows)

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app), fake_db
    app.dependency_overrides.clear()


class TestOpsApparatusByCategoryEndpointMounting:
    def test_endpoint_responds_200(self, client):
        test_client, _ = client
        response = test_client.get("/api/v1/ops/apparatus-by-category")
        assert response.status_code == 200

    def test_endpoint_not_under_work_prefix(self, client):
        test_client, _ = client
        response = test_client.get("/api/v1/work/apparatus-by-category")
        assert response.status_code == 404

    def test_endpoint_is_get_only(self, client):
        test_client, _ = client
        response = test_client.post("/api/v1/ops/apparatus-by-category")
        assert response.status_code == 405


class TestOpsApparatusByCategoryShape:
    def test_response_returns_expected_fields(self, client):
        test_client, _ = client
        body = test_client.get("/api/v1/ops/apparatus-by-category").json()
        assert len(body) == 1
        assert set(body[0].keys()) == {
            "project_id",
            "project_number",
            "scope_id",
            "scope_name",
            "apparatus_category",
            "total_count",
            "completed",
            "remaining",
            "percent_complete",
            "ready_to_work",
            "blocked",
        }

    def test_limit_parameter_is_forwarded_to_query(self, client):
        test_client, fake_db = client
        response = test_client.get("/api/v1/ops/apparatus-by-category?limit=13")
        assert response.status_code == 200
        assert fake_db.calls[-1][1] == {"limit": 13}


class TestOpsApparatusByCategoryScopeGuards:
    def test_non_get_verbs_are_rejected(self, client):
        test_client, _ = client
        for method in ("post", "put", "patch", "delete"):
            response = getattr(test_client, method)("/api/v1/ops/apparatus-by-category")
            assert response.status_code == 405