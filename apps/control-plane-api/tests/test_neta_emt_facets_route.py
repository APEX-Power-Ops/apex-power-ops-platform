"""Tests for the EMT facet route."""

import os
import sys
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost/test")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_db
from main import app


class FakeRow:
    def __init__(self, mapping):
        self._mapping = mapping


class FakeResult:
    def __init__(self, rows=None, scalar_value=None):
        self._rows = [FakeRow(row) for row in (rows or [])]
        self._scalar_value = scalar_value

    def fetchall(self):
        return self._rows

    def scalar(self):
        return self._scalar_value


class FakeEmtFacetDb:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def execute(self, statement, params=None):
        self.calls.append({"statement": str(statement), "params": params or {}})
        if not self._results:
            raise AssertionError("Unexpected SQL execution in EMT facets test")
        return self._results.pop(0)


@pytest.fixture
def client():
    return TestClient(app)


def test_emt_facets_returns_cross_filtered_values(client):
    fake_db = FakeEmtFacetDb([
        FakeResult(scalar_value=3),
        FakeResult(rows=[{"value": 9}, {"value": 11}]),
        FakeResult(rows=[{"value": 7}, {"value": 8}]),
        FakeResult(rows=[{"value": 0}, {"value": 1}]),
        FakeResult(rows=[{"value": "800A Frame"}, {"value": "1200A Frame"}]),
        FakeResult(rows=[{"value": "Digitrip 520"}, {"value": "Digitrip 1150"}]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    resolved_columns = {
        "emt": {
            "manufacturer_id": "manufacturer_id",
            "type_name": "type_name",
            "trip_char": "trip_char",
            "trip_plug": "trip_plug",
        },
        "frames": {
            "emt_id": "emt_id",
            "frame_desc": "frame_desc",
        },
    }

    try:
        with patch("services.neta.router._resolve_emt_contract_columns", return_value=resolved_columns):
            resp = client.get(
                "/api/v1/neta/emt/facets",
                params={
                    "manufacturer_id": 9,
                    "trip_char": 7,
                    "type_name": "Digitrip 520",
                },
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_matching_frames"] == 3
        assert body["active_filters"] == {
            "manufacturer_id": 9,
            "trip_char": 7,
            "type_name": "Digitrip 520",
        }
        assert body["facets"][0] == {
            "name": "manufacturer_id",
            "values": [9, 11],
            "cardinality": 2,
        }
        assert body["facets"][3] == {
            "name": "frame_desc",
            "values": ["800A Frame", "1200A Frame"],
            "cardinality": 2,
        }
        assert body["facets"][4] == {
            "name": "type_name",
            "values": ["Digitrip 520", "Digitrip 1150"],
            "cardinality": 2,
        }
        assert any(call["params"].get("manufacturer_id") == 9 for call in fake_db.calls)
        assert any(call["params"].get("trip_char") == 7 for call in fake_db.calls)
        assert any(call["params"].get("type_name") == "Digitrip 520" for call in fake_db.calls)
    finally:
        app.dependency_overrides.clear()


def test_emt_facets_surface_migration_gated_error(client):
    with patch(
        "services.neta.router._resolve_emt_contract_columns",
        side_effect=HTTPException(status_code=503, detail="EMT catalog tables are not available in the current database."),
    ):
        resp = client.get("/api/v1/neta/emt/facets")

    assert resp.status_code == 503
    assert "EMT catalog tables are not available" in resp.json()["detail"]