"""Tests for the ETU alt-trip (retrofit/upgrade) route (/etu/breaker-alt-trips).

This serves the alternative-trip set for a breaker (tcc.breaker_alt_trip_bridge, migration
017) so the picker can tag a trip as a retrofit/upgrade and show its protection-element
class without re-querying the main SST bridge.
"""

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
    def __init__(self, rows=None):
        self._rows = [FakeRow(row) for row in (rows or [])]

    def fetchall(self):
        return self._rows


class FakeDb:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def execute(self, _statement, _params=None):
        self.calls.append({"statement": str(_statement), "params": _params or {}})
        if not self._results:
            raise AssertionError("Unexpected SQL execution in alt-trips test")
        return self._results.pop(0)


@pytest.fixture
def client():
    return TestClient(app)


# WavePro (PCB, breaker_id 18) -> EntelliGuard TU retrofits: 1073 (LSIG) + 1566 (LIG).
_WAVEPRO_ALT_TRIPS = [
    {"trip_style_id": 1073, "relation": "retrofit", "protection_class": "LSIG"},
    {"trip_style_id": 1566, "relation": "retrofit", "protection_class": "LIG"},
]


def test_alt_trips_returns_set(client):
    fake_db = FakeDb([FakeResult(rows=_WAVEPRO_ALT_TRIPS)])
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get(
            "/api/v1/neta/etu/breaker-alt-trips",
            params={"breaker_id": 18, "breaker_class": "PCB"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 2
        assert body["breaker_id"] == 18
        first = body["alt_trips"][0]
        assert first["trip_style_id"] == 1073
        assert first["relation"] == "retrofit"
        assert first["protection_class"] == "LSIG"
        assert body["alt_trips"][1]["protection_class"] == "LIG"
        # Reads the alt-trip bridge table, schema-qualified (search_path-robust).
        stmt = fake_db.calls[0]["statement"]
        assert "tcc.breaker_alt_trip_bridge" in stmt
        assert fake_db.calls[0]["params"].get("bid") == 18
        assert fake_db.calls[0]["params"].get("bclass") == "PCB"
    finally:
        app.dependency_overrides.clear()


def test_alt_trips_empty_when_no_alt_trips(client):
    fake_db = FakeDb([FakeResult(rows=[])])
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get(
            "/api/v1/neta/etu/breaker-alt-trips",
            params={"breaker_id": 999999, "breaker_class": "PCB"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0
        assert body["alt_trips"] == []
    finally:
        app.dependency_overrides.clear()


def test_alt_trips_accepts_breaker_style_id(client):
    fake_db = FakeDb([FakeResult(rows=_WAVEPRO_ALT_TRIPS)])
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        resp = client.get(
            "/api/v1/neta/etu/breaker-alt-trips",
            params={"breaker_style_id": 1032, "breaker_class": "PCB"},
        )
        assert resp.status_code == 200
        assert fake_db.calls[0]["params"].get("bsid") == 1032
    finally:
        app.dependency_overrides.clear()


def test_alt_trips_requires_a_selector(client):
    resp = client.get("/api/v1/neta/etu/breaker-alt-trips")
    assert resp.status_code == 422
    assert "breaker_id or breaker_style_id" in resp.json()["detail"]


def test_alt_trips_rejects_invalid_breaker_class(client):
    resp = client.get(
        "/api/v1/neta/etu/breaker-alt-trips",
        params={"breaker_id": 18, "breaker_class": "foo"},
    )
    assert resp.status_code == 422
    assert "breaker_class must be one of" in resp.json()["detail"]
