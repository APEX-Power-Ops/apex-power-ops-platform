"""Tests for the bounded apparatus study-resource route."""

import os
import sys
from uuid import uuid4

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost/test")

from config import get_db
from main import app


class _Row:
    def __init__(self, mapping):
        self._mapping = mapping


class _Result:
    def __init__(self, rows=None, row=None):
        self._rows = [_Row(item) for item in (rows or [])]
        self._row = _Row(row) if row is not None else None

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _FakeApparatusResourcesDb:
    def __init__(self, *, apparatus_exists=True, resource_rows=None, raise_on_resources=False):
        self.apparatus_exists = apparatus_exists
        self.resource_rows = resource_rows or []
        self.raise_on_resources = raise_on_resources

    def execute(self, statement, params=None):
        sql = str(statement)
        if "SELECT EXISTS(SELECT 1 FROM apparatus" in sql:
            return _Result(row={"found": self.apparatus_exists})
        if "SELECT * FROM get_apparatus_resources" in sql:
            if self.raise_on_resources:
                raise RuntimeError("function get_apparatus_resources does not exist")
            return _Result(rows=self.resource_rows)
        raise AssertionError(f"Unexpected SQL: {sql}")


def test_apparatus_resources_route_returns_bounded_resource_payload():
    client = TestClient(app)
    apparatus_id = uuid4()
    resource_id = uuid4()
    fake_db = _FakeApparatusResourcesDb(
        resource_rows=[
            {
                "resource_id": resource_id,
                "title": "Transformer Study Guide",
                "resource_type": "study_guide",
                "source_table": "study_content",
                "level": "III",
                "description": "Field-ready study surface",
                "url_slug": "transformer-study-guide",
                "estimated_minutes": 18,
            }
        ]
    )
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get(f"/api/v1/neta/apparatus/{apparatus_id}/resources")
        assert resp.status_code == 200
        data = resp.json()
        assert data["apparatus_id"] == str(apparatus_id)
        assert data["count"] == 1
        assert data["resources"][0]["resource_id"] == str(resource_id)
        assert data["resources"][0]["resource_type"] == "study_guide"
        assert data["resources"][0]["source_table"] == "study_content"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_apparatus_resources_route_returns_404_for_unknown_apparatus():
    client = TestClient(app)
    apparatus_id = uuid4()
    fake_db = _FakeApparatusResourcesDb(apparatus_exists=False)
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get(f"/api/v1/neta/apparatus/{apparatus_id}/resources")
        assert resp.status_code == 404
        assert resp.json()["detail"] == f"Apparatus {apparatus_id} not found"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_apparatus_resources_route_returns_503_when_sql_surface_is_unavailable():
    client = TestClient(app)
    apparatus_id = uuid4()
    fake_db = _FakeApparatusResourcesDb(raise_on_resources=True)
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get(f"/api/v1/neta/apparatus/{apparatus_id}/resources")
        assert resp.status_code == 503
        assert "migration-gated" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)