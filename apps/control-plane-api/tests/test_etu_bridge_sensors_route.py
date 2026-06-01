"""Tests for the ETU SST-bridge sensor-narrowing route (/etu/bridge-sensors)."""

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


class FakeBridgeDb:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def execute(self, _statement, _params=None):
        self.calls.append({"statement": str(_statement), "params": _params or {}})
        if not self._results:
            raise AssertionError("Unexpected SQL execution in bridge-sensors test")
        return self._results.pop(0)


@pytest.fixture
def client():
    return TestClient(app)


# The canonical D1 example: T8V-1600 (ICCB) -> ABB PR332/P -> 5 sensors.
_T8V_1600_SENSORS = [
    {
        "breaker_class": "iccb",
        "breaker_id": 4001,
        "breaker_style_id": 7777,
        "breaker_style_frame": "T8V-1600",
        "tmt_sst_mfr": "ABB",
        "tmt_sst_type": "PR332/P",
        "tmt_sst_style": "ICCB-LSIG",
        "trip_style_id": 1230,
        "sensor_id": 15240,
        "sensor_rating": 1000,
        "sensor_description": "1600(1000-1600)",
    },
    {
        "breaker_class": "iccb",
        "breaker_id": 4001,
        "breaker_style_id": 7777,
        "breaker_style_frame": "T8V-1600",
        "tmt_sst_mfr": "ABB",
        "tmt_sst_type": "PR332/P",
        "tmt_sst_style": "ICCB-LSIG",
        "trip_style_id": 1230,
        "sensor_id": 15241,
        "sensor_rating": 1200,
        "sensor_description": "2000(1000-2000)",
    },
]


def test_bridge_sensors_returns_matched_sensor_set(client):
    fake_db = FakeBridgeDb([FakeResult(rows=_T8V_1600_SENSORS)])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get("/api/v1/neta/etu/bridge-sensors", params={"breaker_style_id": 7777})
        assert resp.status_code == 200
        body = resp.json()
        assert body["bridge_match_status"] == "matched"
        assert body["count"] == 2
        assert body["breaker_style_id"] == 7777
        first = body["sensors"][0]
        assert first["tmt_sst_mfr"] == "ABB"
        assert first["tmt_sst_type"] == "PR332/P"
        assert first["sensor_id"] == 15240
        assert first["sensor_rating"] == 1000
        # The view name must be schema-qualified (search_path-robust).
        assert "tcc.vw_breaker_sst_bridge" in fake_db.calls[0]["statement"]
        assert fake_db.calls[0]["params"].get("bsid") == 7777
    finally:
        app.dependency_overrides.clear()


def test_bridge_sensors_unmatched_when_no_rows(client):
    fake_db = FakeBridgeDb([FakeResult(rows=[])])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get("/api/v1/neta/etu/bridge-sensors", params={"breaker_style_id": 999999})
        assert resp.status_code == 200
        body = resp.json()
        assert body["bridge_match_status"] == "unmatched"
        assert body["count"] == 0
        assert body["sensors"] == []
    finally:
        app.dependency_overrides.clear()


def test_bridge_sensors_requires_a_selector(client):
    resp = client.get("/api/v1/neta/etu/bridge-sensors")
    assert resp.status_code == 422
    assert "breaker_style_id or breaker_id" in resp.json()["detail"]


def test_bridge_sensors_disambiguates_by_breaker_class(client):
    # style ids are per-class serials that overlap; the class filter prevents foreign-class bleed-in.
    fake_db = FakeBridgeDb([FakeResult(rows=_T8V_1600_SENSORS)])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get(
            "/api/v1/neta/etu/bridge-sensors",
            params={"breaker_style_id": 1510, "breaker_class": "MCCB"},
        )
        assert resp.status_code == 200
        stmt = fake_db.calls[0]["statement"]
        assert "lower(breaker_class) = lower(:bclass)" in stmt
        assert fake_db.calls[0]["params"].get("bclass") == "MCCB"
    finally:
        app.dependency_overrides.clear()


def test_bridge_sensors_rejects_invalid_breaker_class(client):
    resp = client.get(
        "/api/v1/neta/etu/bridge-sensors",
        params={"breaker_style_id": 1510, "breaker_class": "foo"},
    )
    assert resp.status_code == 422
    assert "breaker_class must be one of" in resp.json()["detail"]
