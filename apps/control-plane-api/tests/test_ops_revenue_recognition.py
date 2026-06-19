"""Ops Router — Revenue Recognition view unit tests (mocked DB).

Validates routing, GET-only, response shape, and limit forwarding without a
live database, mirroring tests/test_ops_master_operations.py.
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
            "project_id": "11111111-1111-1111-1111-111111111111",
            "project_number": "P-001",
            "project_name": "Test Project A",
            "scope_id": "22222222-2222-2222-2222-222222222221",
            "scope_name": "Scope One",
            "quoted_revenue": 6000.0,
            "recognized_revenue": 3000.0,
            "recognition_percent": 50.0,
            "billable_now": 3000.0,
            "total_apparatus": 3,
            "completed_apparatus": 2,
        }
    ]
    fake_db = _FakeDB(fake_rows)

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app), fake_db
    app.dependency_overrides.clear()


def test_endpoint_responds_200(client):
    test_client, _ = client
    assert test_client.get("/api/v1/ops/revenue-recognition").status_code == 200


def test_endpoint_not_under_work_prefix(client):
    test_client, _ = client
    assert test_client.get("/api/v1/work/revenue-recognition").status_code == 404


def test_response_shape(client):
    test_client, _ = client
    body = test_client.get("/api/v1/ops/revenue-recognition").json()
    assert len(body) == 1
    assert set(body[0].keys()) == {
        "project_id", "project_number", "project_name", "scope_id", "scope_name",
        "quoted_revenue", "recognized_revenue", "recognition_percent", "billable_now",
        "total_apparatus", "completed_apparatus",
    }


def test_limit_is_forwarded(client):
    test_client, fake_db = client
    assert test_client.get("/api/v1/ops/revenue-recognition?limit=7").status_code == 200
    assert fake_db.calls[-1][1] == {"limit": 7}


def test_non_get_verbs_rejected(client):
    test_client, _ = client
    for method in ("post", "put", "patch", "delete"):
        assert getattr(test_client, method)("/api/v1/ops/revenue-recognition").status_code == 405
