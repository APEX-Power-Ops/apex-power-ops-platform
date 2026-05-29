"""Tests for the TMT facet route."""

import os
import sys

import pytest
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


class FakeTmtFacetDb:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def execute(self, statement, params=None):
        self.calls.append({"statement": str(statement), "params": params or {}})
        if not self._results:
            raise AssertionError("Unexpected SQL execution in TMT facets test")
        return self._results.pop(0)


@pytest.fixture
def client():
    return TestClient(app)


def test_tmt_facets_returns_cross_filtered_values(client):
    fake_db = FakeTmtFacetDb([
        FakeResult(scalar_value=2),
        FakeResult(rows=[{"value": "ICCB"}, {"value": "PCB"}]),
        FakeResult(rows=[{"value": 9}, {"value": 11}]),
        FakeResult(rows=[{"value": 101}, {"value": 205}]),
        FakeResult(rows=[{"value": 301}, {"value": 302}]),
        FakeResult(rows=[{"value": "800AF"}, {"value": "1200AF"}]),
        FakeResult(rows=[{"value": 800.0}, {"value": 1200.0}]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get(
            "/api/v1/neta/tmt/facets",
            params={
                "breaker_class": "iccb",
                "manufacturer_id": 9,
                "amp_rating": 800.0,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_matching_frames"] == 2
        assert body["active_filters"] == {
            "breaker_class": "ICCB",
            "manufacturer_id": 9,
            "amp_rating": 800.0,
        }
        assert body["facets"][0] == {
            "name": "breaker_class",
            "values": ["ICCB", "PCB"],
            "cardinality": 2,
        }
        assert body["facets"][4] == {
            "name": "frame_size",
            "values": ["800AF", "1200AF"],
            "cardinality": 2,
        }
        assert body["facets"][5] == {
            "name": "amp_rating",
            "values": [800.0, 1200.0],
            "cardinality": 2,
        }
        assert any(call["params"].get("breaker_class") == "ICCB" for call in fake_db.calls)
        assert any(call["params"].get("manufacturer_id") == 9 for call in fake_db.calls)
        assert any(call["params"].get("amp_rating") == 800.0 for call in fake_db.calls)
    finally:
        app.dependency_overrides.clear()


def test_tmt_facets_reject_invalid_breaker_class(client):
    resp = client.get("/api/v1/neta/tmt/facets", params={"breaker_class": "fuse"})
    assert resp.status_code == 400
    assert "breaker_class must be one of ICCB, MCCB, or PCB" in resp.json()["detail"]