"""Tests for the ETU breaker-half cascade route."""

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


class FakeBreakerCascadeDb:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def execute(self, _statement, _params=None):
        self.calls.append({"statement": str(_statement), "params": _params or {}})
        if not self._results:
            raise AssertionError("Unexpected SQL execution in breaker-cascade test")
        return self._results.pop(0)


@pytest.fixture
def client():
    return TestClient(app)


def test_breaker_cascade_returns_cross_filtered_breaker_options(client):
    app.dependency_overrides[get_db] = lambda: FakeBreakerCascadeDb([
        FakeResult(scalar_value=3),
        FakeResult(rows=[
            {"manufacturer_id": 9, "manufacturer_name": "GE", "breaker_count": 2},
        ]),
        FakeResult(rows=[
            {"breaker_class": "ICCB", "breaker_count": 2},
            {"breaker_class": "PCB", "breaker_count": 1},
        ]),
        FakeResult(rows=[
            {
                "breaker_id": 101,
                "breaker_name": "AKR",
                "breaker_class": "ICCB",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "style_count": 2,
            },
        ]),
        FakeResult(rows=[
            {
                "breaker_style_id": 301,
                "breaker_style_name": "AKR-7D",
                "breaker_id": 101,
                "breaker_name": "AKR",
                "breaker_class": "ICCB",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
            },
            {
                "breaker_style_id": 302,
                "breaker_style_name": "AKR-8D",
                "breaker_id": 101,
                "breaker_name": "AKR",
                "breaker_class": "ICCB",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
            },
        ]),
    ])

    try:
        resp = client.get(
            "/api/v1/neta/etu/breaker-cascade",
            params={"manufacturer_id": 9, "breaker_class": "ICCB", "breaker_id": 101},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["level"] == "breaker_styles"
        assert body["count"] == 3
        assert body["manufacturers"][0]["manufacturer_name"] == "GE"
        assert body["breaker_classes"][0]["breaker_class"] == "ICCB"
        assert body["breakers"][0]["breaker_name"] == "AKR"
        assert body["breaker_styles"][1]["breaker_style_name"] == "AKR-8D"
    finally:
        app.dependency_overrides.clear()


def test_breaker_cascade_rejects_invalid_breaker_class(client):
    resp = client.get("/api/v1/neta/etu/breaker-cascade", params={"breaker_class": "foo"})
    assert resp.status_code == 422
    assert "breaker_class must be one of" in resp.json()["detail"]


def test_breaker_cascade_accepts_trip_unit_cross_filters(client):
    fake_db = FakeBreakerCascadeDb([
        FakeResult(scalar_value=1),
        FakeResult(rows=[
            {"manufacturer_id": 9, "manufacturer_name": "GE", "breaker_count": 1},
        ]),
        FakeResult(rows=[
            {"breaker_class": "ICCB", "breaker_count": 1},
        ]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get("/api/v1/neta/etu/breaker-cascade", params={"trip_type_id": 75})
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 1
        assert body["scope"]["trip_type_id"] == 75
        assert any(call["params"].get("xh_trip_type_id") == 75 for call in fake_db.calls)
    finally:
        app.dependency_overrides.clear()


def test_breaker_cascade_bridge_xfilter_narrows_by_compatibility_not_manufacturer(client):
    # A trip-unit selection must narrow breakers to bridge-COMPATIBLE styles, not the
    # trip unit's whole manufacturer (the old manufacturer-only cross-filter).
    fake_db = FakeBreakerCascadeDb([
        FakeResult(scalar_value=4),
        FakeResult(rows=[{"manufacturer_id": 1, "manufacturer_name": "ABB", "breaker_count": 4}]),
        FakeResult(rows=[{"breaker_class": "ICCB", "breaker_count": 4}]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get(
            "/api/v1/neta/etu/breaker-cascade",
            params={"trip_style_id": 1230, "bridge_xfilter": "true"},
        )
        assert resp.status_code == 200
        assert all("vw_breaker_sst_bridge" in c["statement"] for c in fake_db.calls)
        assert any("(breaker_class, breaker_style_id) IN" in c["statement"] for c in fake_db.calls)
        # legacy manufacturer-only narrowing must NOT be used when bridge_xfilter is on
        assert not any(
            "manufacturer_id IN (SELECT DISTINCT manufacturer_id FROM vw_trip_unit_cascade" in c["statement"]
            for c in fake_db.calls
        )
    finally:
        app.dependency_overrides.clear()


def test_breaker_cascade_bridge_only_filters_to_etu_capable(client):
    fake_db = FakeBreakerCascadeDb([
        FakeResult(scalar_value=130),
        FakeResult(rows=[{"manufacturer_id": 9, "manufacturer_name": "GE", "breaker_count": 1}]),
        FakeResult(rows=[{"breaker_class": "MCCB", "breaker_count": 1}]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get("/api/v1/neta/etu/breaker-cascade", params={"bridge_only": "true"})
        assert resp.status_code == 200
        # Every cascade query must restrict to (class, style) pairs present in the bridge view.
        assert all("vw_breaker_sst_bridge" in call["statement"] for call in fake_db.calls)
        assert any("(breaker_class, breaker_style_id) IN" in call["statement"] for call in fake_db.calls)
    finally:
        app.dependency_overrides.clear()