"""Tests for the ETU browse/search route."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

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


class FakeSearchDb:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def execute(self, _statement, _params=None):
        self.calls.append({"statement": str(_statement), "params": _params or {}})
        if not self._results:
            raise AssertionError("Unexpected SQL execution in ETU search test")
        return self._results.pop(0)


@pytest.fixture
def client():
    return TestClient(app)


def test_etu_search_returns_matches_with_compatible_plugs(client):
    fake_db = FakeSearchDb([
        FakeResult(scalar_value=1),
        FakeResult(rows=[
            {
                "sensor_id": 25,
                "sensor_rating": 800,
                "sensor_desc": "800",
                "trip_style_id": 3,
                "trip_style_name": "ICCB",
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
            },
        ]),
        FakeResult(rows=[
            {"sensor_id": 25, "value": 800},
            {"sensor_id": 25, "value": 1200},
        ]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get(
            "/api/v1/neta/etu/search",
            params={"trip_style_id": 3, "plug_value": 800, "q": "rms", "limit": 25},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 1
        assert body["results"][0]["manufacturer_name"] == "GE"
        assert body["results"][0]["compatible_plug_values"] == [800.0, 1200.0]
        assert any(call["params"].get("plug_value") == 800.0 for call in fake_db.calls)
        assert any(call["params"].get("q") == "%rms%" for call in fake_db.calls)
        assert any(call["params"].get("limit") == 25 for call in fake_db.calls)
    finally:
        app.dependency_overrides.clear()