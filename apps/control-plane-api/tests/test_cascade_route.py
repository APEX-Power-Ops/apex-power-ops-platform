"""Tests for the ETU cross-filtered cascade route."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost/test")

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


class FakeCascadeDb:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def execute(self, _statement, _params=None):
        self.calls.append({"statement": str(_statement), "params": _params or {}})
        if not self._results:
            raise AssertionError("Unexpected SQL execution in cascade test")
        return self._results.pop(0)


@pytest.fixture
def client():
    return TestClient(app)


def test_cascade_returns_cross_filtered_option_sets(client):
    app.dependency_overrides[get_db] = lambda: FakeCascadeDb([
        FakeResult(scalar_value=2),
        FakeResult(rows=[
            {"manufacturer_id": 9, "manufacturer_name": "GE", "trip_type_count": 1},
        ]),
        FakeResult(rows=[
            {
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "trip_style_count": 1,
            },
        ]),
        FakeResult(rows=[
            {
                "trip_style_id": 3,
                "trip_style_name": "ICCB",
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "sensor_count": 2,
            },
        ]),
        FakeResult(rows=[
            {"plug_value": 800, "sensor_count": 2},
            {"plug_value": 1200, "sensor_count": 1},
        ]),
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
                "has_ltpu": True,
                "has_stpu": True,
                "has_inst": True,
                "has_gfpu": True,
            },
            {
                "sensor_id": 26,
                "sensor_rating": 1200,
                "sensor_desc": "1200",
                "trip_style_id": 3,
                "trip_style_name": "ICCB",
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "has_ltpu": True,
                "has_stpu": True,
                "has_inst": True,
                "has_gfpu": False,
            },
        ]),
    ])

    try:
        resp = client.get("/api/v1/neta/cascade", params={"trip_style_id": 3})
        assert resp.status_code == 200
        body = resp.json()
        assert body["level"] == "trip_styles"
        assert body["count"] == 2
        assert body["manufacturers"][0]["manufacturer_name"] == "GE"
        assert body["trip_types"][0]["trip_type_name"] == "MVT RMS-9"
        assert body["trip_styles"][0]["sensor_count"] == 2
        assert body["plug_values"][0]["plug_value"] == 800
        assert body["sensors"][0]["sensor_rating"] == 800
        assert body["sensors"][1]["sensor_desc"] == "1200"
    finally:
        app.dependency_overrides.clear()


def test_cascade_qualifies_sensor_count_when_plug_filter_and_cross_half_filters_are_active(client):
    fake_db = FakeCascadeDb([
        FakeResult(scalar_value=1),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get(
            "/api/v1/neta/cascade",
            params={
                "manufacturer_id": 9,
                "trip_type_id": 75,
                "trip_style_id": 3,
                "sensor_id": 25,
                "plug_value": 300,
                "breaker_id": 24,
                "breaker_style_id": 327,
            },
        )
        assert resp.status_code == 200
        first_call = fake_db.calls[0]
        assert "COUNT(DISTINCT v.sensor_id)" in first_call["statement"]
        assert "v.sensor_id = :sensor_id" in first_call["statement"]
        assert first_call["params"]["plug_value"] == 300.0
        assert first_call["params"]["xh_breaker_id"] == 24
        assert first_call["params"]["xh_breaker_style_id"] == 327
    finally:
        app.dependency_overrides.clear()


def test_cascade_leaves_sensor_options_empty_until_style_selected(client):
    app.dependency_overrides[get_db] = lambda: FakeCascadeDb([
        FakeResult(scalar_value=4),
        FakeResult(rows=[
            {"manufacturer_id": 9, "manufacturer_name": "GE", "trip_type_count": 2},
        ]),
        FakeResult(rows=[
            {
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "trip_style_count": 2,
            },
        ]),
        FakeResult(rows=[
            {
                "trip_style_id": 3,
                "trip_style_name": "ICCB",
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "sensor_count": 4,
            },
        ]),
        FakeResult(rows=[
            {"plug_value": 800, "sensor_count": 4},
        ]),
    ])

    try:
        resp = client.get("/api/v1/neta/cascade", params={"manufacturer_id": 9})
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 4
        assert body["trip_types"][0]["trip_style_count"] == 2
        assert body["trip_styles"][0]["sensor_count"] == 4
        assert body["plug_values"] == [{"plug_value": 800.0, "sensor_count": 4}]
        assert body["sensors"] == []
    finally:
        app.dependency_overrides.clear()


def test_cascade_sensor_filter_revalidates_exact_path(client):
    app.dependency_overrides[get_db] = lambda: FakeCascadeDb([
        FakeResult(scalar_value=1),
        FakeResult(rows=[
            {"manufacturer_id": 9, "manufacturer_name": "GE", "trip_type_count": 1},
        ]),
        FakeResult(rows=[
            {
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "trip_style_count": 1,
            },
        ]),
        FakeResult(rows=[
            {
                "trip_style_id": 3,
                "trip_style_name": "ICCB",
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "sensor_count": 1,
            },
        ]),
        FakeResult(rows=[
            {"plug_value": 800, "sensor_count": 1},
        ]),
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
                "has_ltpu": True,
                "has_stpu": True,
                "has_inst": True,
                "has_gfpu": True,
            },
        ]),
    ])

    try:
        resp = client.get("/api/v1/neta/cascade", params={"sensor_id": 25})
        assert resp.status_code == 200
        body = resp.json()
        assert body["level"] == "sensors"
        assert body["count"] == 1
        assert body["manufacturers"][0]["manufacturer_id"] == 9
        assert body["trip_types"][0]["trip_type_id"] == 75
        assert body["trip_styles"][0]["trip_style_id"] == 3
        assert body["trip_styles"][0]["sensor_count"] == 1
        assert body["plug_values"] == [{"plug_value": 800.0, "sensor_count": 1}]
        assert body["sensors"] == [
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
                "has_ltpu": True,
                "has_stpu": True,
                "has_inst": True,
                "has_gfpu": True,
            }
        ]
    finally:
        app.dependency_overrides.clear()


def test_cascade_surfaces_zero_match_empty_state(client):
    app.dependency_overrides[get_db] = lambda: FakeCascadeDb([
        FakeResult(scalar_value=0),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
    ])

    try:
        resp = client.get("/api/v1/neta/cascade", params={"trip_style_id": 999, "sensor_id": 12345})
        assert resp.status_code == 200
        body = resp.json()
        assert body["level"] == "sensors"
        assert body["count"] == 0
        assert body["manufacturers"] == []
        assert body["trip_types"] == []
        assert body["trip_styles"] == []
        assert body["plug_values"] == []
        assert body["sensors"] == []
    finally:
        app.dependency_overrides.clear()


def test_cascade_accepts_breaker_half_cross_filters(client):
    fake_db = FakeCascadeDb([
        FakeResult(scalar_value=2),
        FakeResult(rows=[
            {"manufacturer_id": 9, "manufacturer_name": "GE", "trip_type_count": 1},
        ]),
        FakeResult(rows=[
            {
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "trip_style_count": 1,
            },
        ]),
        FakeResult(rows=[
            {
                "trip_style_id": 3,
                "trip_style_name": "ICCB",
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "sensor_count": 2,
            },
        ]),
        FakeResult(rows=[
            {"plug_value": 800, "sensor_count": 2},
        ]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get("/api/v1/neta/cascade", params={"breaker_class": "ICCB", "breaker_id": 101})
        assert resp.status_code == 200
        assert resp.json()["count"] == 2
        assert any(call["params"].get("xh_breaker_class") == "ICCB" for call in fake_db.calls)
        assert any(call["params"].get("xh_breaker_id") == 101 for call in fake_db.calls)
    finally:
        app.dependency_overrides.clear()


def test_cascade_rejects_invalid_breaker_class(client):
    resp = client.get("/api/v1/neta/cascade", params={"breaker_class": "BAD"})

    assert resp.status_code == 422
    assert resp.json()["detail"] == "breaker_class must be one of 'ICCB', 'MCCB', 'PCB'."


def test_cascade_count_query_combines_cross_half_cte_and_plug_join(client):
    fake_db = FakeCascadeDb([
        FakeResult(scalar_value=1),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get(
            "/api/v1/neta/cascade",
            params={
                "manufacturer_id": 9,
                "trip_type_id": 75,
                "trip_style_id": 3,
                "sensor_id": 25,
                "plug_value": 800,
                "breaker_class": "ICCB",
                "breaker_id": 24,
                "breaker_style_id": 327,
            },
        )
        assert resp.status_code == 200
        first_call = fake_db.calls[0]
        assert "etu_breaker_combined" in first_call["statement"]
        assert "SELECT DISTINCT manufacturer_id FROM etu_breaker_combined" in first_call["statement"]
        assert "JOIN tcc.etu_plugs p_filter ON p_filter.sensor_id = v.sensor_id AND p_filter.value = :plug_value" in first_call["statement"]
        assert "COUNT(DISTINCT v.sensor_id)" in first_call["statement"]
        assert first_call["params"] == {
            "manufacturer_id": 9,
            "trip_type_id": 75,
            "trip_style_id": 3,
            "sensor_id": 25,
            "plug_value": 800.0,
            "xh_breaker_class": "ICCB",
            "xh_breaker_id": 24,
            "xh_breaker_style_id": 327,
        }
    finally:
        app.dependency_overrides.clear()


def test_cascade_accepts_plug_filter_and_returns_scope_plug_values(client):
    fake_db = FakeCascadeDb([
        FakeResult(scalar_value=1),
        FakeResult(rows=[
            {"manufacturer_id": 9, "manufacturer_name": "GE", "trip_type_count": 1},
        ]),
        FakeResult(rows=[
            {
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "trip_style_count": 1,
            },
        ]),
        FakeResult(rows=[
            {
                "trip_style_id": 3,
                "trip_style_name": "ICCB",
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "sensor_count": 1,
            },
        ]),
        FakeResult(rows=[
            {"plug_value": 800, "sensor_count": 2},
            {"plug_value": 1200, "sensor_count": 1},
        ]),
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
                "has_ltpu": True,
                "has_stpu": True,
                "has_inst": True,
                "has_gfpu": True,
            },
        ]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get("/api/v1/neta/cascade", params={"trip_style_id": 3, "plug_value": 800})
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 1
        assert body["plug_values"] == [
            {"plug_value": 800.0, "sensor_count": 2},
            {"plug_value": 1200.0, "sensor_count": 1},
        ]
        assert any(call["params"].get("plug_value") == 800.0 for call in fake_db.calls)
    finally:
        app.dependency_overrides.clear()


def test_cascade_plug_scope_query_stays_independent_from_selected_plug(client):
    fake_db = FakeCascadeDb([
        FakeResult(scalar_value=1),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
        FakeResult(rows=[]),
        FakeResult(rows=[{"plug_value": 800, "sensor_count": 2}]),
        FakeResult(rows=[]),
    ])
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        resp = client.get("/api/v1/neta/cascade", params={"trip_style_id": 3, "plug_value": 800})
        assert resp.status_code == 200
        count_call = fake_db.calls[0]
        plug_scope_call = fake_db.calls[4]
        assert "p_filter.value = :plug_value" in count_call["statement"]
        assert count_call["params"]["plug_value"] == 800.0
        assert "JOIN tcc.etu_plugs p ON p.sensor_id = v.sensor_id" in plug_scope_call["statement"]
        assert "p_filter" not in plug_scope_call["statement"]
        assert "plug_value" not in plug_scope_call["params"]
        assert plug_scope_call["params"] == {"trip_style_id": 3}
    finally:
        app.dependency_overrides.clear()


def test_etu_search_count_query_reuses_plug_join_and_scope_filters(client):
    fake_db = FakeCascadeDb([
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
            params={"trip_style_id": 3, "sensor_id": 25, "plug_value": 800, "q": "rms", "limit": 25},
        )
        assert resp.status_code == 200
        count_call = fake_db.calls[0]
        results_call = fake_db.calls[1]
        plug_map_call = fake_db.calls[2]
        assert "COUNT(DISTINCT v.sensor_id)" in count_call["statement"]
        assert "JOIN tcc.etu_plugs p_filter ON p_filter.sensor_id = v.sensor_id AND p_filter.value = :plug_value" in count_call["statement"]
        assert "v.trip_style_id = :trip_style_id" in count_call["statement"]
        assert "v.sensor_id = :sensor_id" in count_call["statement"]
        assert count_call["params"] == {
            "trip_style_id": 3,
            "sensor_id": 25,
            "q": "%rms%",
            "plug_value": 800.0,
        }
        assert "LIMIT :limit" in results_call["statement"]
        assert results_call["params"]["limit"] == 25
        assert "WHERE sensor_id IN (:sensor_id_0)" in plug_map_call["statement"]
        assert plug_map_call["params"] == {"sensor_id_0": 25}
    finally:
        app.dependency_overrides.clear()