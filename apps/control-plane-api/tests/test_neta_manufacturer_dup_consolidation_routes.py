"""Manufacturer duplicate-consolidation contracts for NETA selector routes."""

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


class FakeDb:
    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def execute(self, statement, params=None):
        self.calls.append({"statement": str(statement), "params": params or {}})
        if not self._results:
            raise AssertionError("Unexpected SQL execution in manufacturer dup-consolidation test")
        return self._results.pop(0)


@pytest.fixture
def client():
    return TestClient(app)


def _with_db(fake_db):
    app.dependency_overrides[get_db] = lambda: fake_db
    return fake_db


def _clear_db():
    app.dependency_overrides.clear()


def test_etu_breaker_manufacturer_list_consolidates_square_d(client):
    fake_db = _with_db(
        FakeDb(
            [
                FakeResult(scalar_value=6),
                FakeResult(
                    rows=[
                        {
                            "manufacturer_id": 17,
                            "manufacturer_ids": [17, 35, 235],
                            "manufacturer_name": "SQD",
                            "manufacturer_display": "Square-D",
                            "breaker_count": 6,
                        },
                        {
                            "manufacturer_id": 4,
                            "manufacturer_ids": [4, 11, 125, 173],
                            "manufacturer_name": "Brown Boveri",
                            "manufacturer_display": "ITE (BBC)",
                            "breaker_count": 4,
                        },
                        {
                            "manufacturer_id": 1,
                            "manufacturer_ids": [1, 43],
                            "manufacturer_name": "ABB",
                            "manufacturer_display": "ABB",
                            "breaker_count": 2,
                        },
                    ]
                ),
                FakeResult(rows=[]),
            ]
        )
    )

    try:
        resp = client.get("/api/v1/neta/etu/breaker-cascade", params={"bridge_only": "true"})
        assert resp.status_code == 200
        manufacturers = resp.json()["manufacturers"]
        square_d_rows = [row for row in manufacturers if row["manufacturer_display"] == "Square-D"]
        assert len(square_d_rows) == 1
        assert square_d_rows[0]["manufacturer_ids"] == [17, 35, 235]
        assert square_d_rows[0]["manufacturer_id"] == 17
        assert square_d_rows[0]["manufacturer_name"] == "SQD"
        assert square_d_rows[0]["breaker_count"] == 6
        assert set(manufacturers[1]["manufacturer_ids"]).issubset({4, 11, 125, 173})
        assert set(manufacturers[2]["manufacturer_ids"]).issubset({1, 43})

        manufacturer_sql = fake_db.calls[1]["statement"]
        assert "ARRAY_AGG" in manufacturer_sql
        assert "SUM(breaker_count)" in manufacturer_sql
        assert "GROUP BY manufacturer_display" in manufacturer_sql
    finally:
        _clear_db()


def test_etu_trip_manufacturer_list_consolidates_display_rows(client):
    fake_db = _with_db(
        FakeDb(
            [
                FakeResult(scalar_value=3),
                FakeResult(
                    rows=[
                        {
                            "manufacturer_id": 1,
                            "manufacturer_ids": [1, 43],
                            "manufacturer_name": "ABB",
                            "manufacturer_display": "ABB",
                            "trip_type_count": 3,
                        }
                    ]
                ),
                FakeResult(rows=[]),
                FakeResult(rows=[]),
                FakeResult(rows=[]),
            ]
        )
    )

    try:
        resp = client.get("/api/v1/neta/cascade")
        assert resp.status_code == 200
        manufacturers = resp.json()["manufacturers"]
        assert manufacturers == [
            {
                "manufacturer_id": 1,
                "manufacturer_ids": [1, 43],
                "manufacturer_name": "ABB",
                "manufacturer_display": "ABB",
                "trip_type_count": 3,
            }
        ]
        manufacturer_sql = fake_db.calls[1]["statement"]
        assert "ARRAY_AGG" in manufacturer_sql
        assert "SUM(trip_type_count)" in manufacturer_sql
        assert "GROUP BY manufacturer_display" in manufacturer_sql
    finally:
        _clear_db()


def test_downstream_breaker_cascade_accepts_manufacturer_id_sets_and_keeps_single_id(client):
    fake_db = _with_db(
        FakeDb(
            [
                FakeResult(scalar_value=4),
                FakeResult(rows=[]),
                FakeResult(rows=[]),
                FakeResult(
                    rows=[
                        {
                            "breaker_id": 100,
                            "breaker_name": "QO",
                            "breaker_class": "MCCB",
                            "manufacturer_id": 17,
                            "manufacturer_name": "SQD",
                            "style_count": 1,
                        },
                        {
                            "breaker_id": 101,
                            "breaker_name": "PowerPact",
                            "breaker_class": "MCCB",
                            "manufacturer_id": 35,
                            "manufacturer_name": "Square D",
                            "style_count": 3,
                        },
                    ]
                ),
            ]
        )
    )

    try:
        resp = client.get(
            "/api/v1/neta/etu/breaker-cascade",
            params=[
                ("manufacturer_ids", "17"),
                ("manufacturer_ids", "35"),
                ("manufacturer_ids", "235"),
            ],
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["level"] == "breakers"
        assert {row["manufacturer_id"] for row in body["breakers"]} == {17, 35}
        assert fake_db.calls[0]["params"]["manufacturer_ids"] == [17, 35, 235]
        assert "manufacturer_id = ANY(:manufacturer_ids)" in fake_db.calls[0]["statement"]
    finally:
        _clear_db()

    fake_db = _with_db(
        FakeDb(
            [
                FakeResult(scalar_value=1),
                FakeResult(rows=[]),
                FakeResult(rows=[]),
                FakeResult(rows=[]),
            ]
        )
    )

    try:
        resp = client.get("/api/v1/neta/etu/breaker-cascade", params={"manufacturer_id": 17})
        assert resp.status_code == 200
        assert fake_db.calls[0]["params"]["manufacturer_id"] == 17
        assert "manufacturer_id = :manufacturer_id" in fake_db.calls[0]["statement"]
        assert "manufacturer_ids" not in fake_db.calls[0]["params"]
    finally:
        _clear_db()


def test_tmt_manufacturer_list_consolidates_display_rows(client):
    fake_db = _with_db(
        FakeDb(
            [
                FakeResult(
                    rows=[
                        {
                            "manufacturer_id": 17,
                            "manufacturer_ids": [17, 35, 235],
                            "manufacturer_name": "SQD",
                            "manufacturer_display": "Square-D",
                            "frame_count": 8,
                        }
                    ]
                )
            ]
        )
    )

    try:
        resp = client.get("/api/v1/neta/tmt/manufacturers", params={"breaker_class": "mccb"})
        assert resp.status_code == 200
        assert resp.json()["manufacturers"] == [
            {
                "manufacturer_id": 17,
                "manufacturer_ids": [17, 35, 235],
                "manufacturer_name": "SQD",
                "manufacturer_display": "Square-D",
                "frame_count": 8,
            }
        ]
        manufacturer_sql = fake_db.calls[0]["statement"]
        assert "ARRAY_AGG" in manufacturer_sql
        assert "SUM(frame_count)" in manufacturer_sql
        assert "GROUP BY manufacturer_display" in manufacturer_sql
    finally:
        _clear_db()


def test_dual_axis_cross_filters_thread_manufacturer_id_sets(client):
    trip_axis_db = _with_db(
        FakeDb(
            [
                FakeResult(scalar_value=5),
                FakeResult(rows=[]),
                FakeResult(rows=[]),
                FakeResult(rows=[]),
                FakeResult(rows=[]),
            ]
        )
    )

    try:
        resp = client.get(
            "/api/v1/neta/cascade",
            params=[
                ("manufacturer_ids", "1"),
                ("manufacturer_ids", "43"),
                ("breaker_manufacturer_ids", "17"),
                ("breaker_manufacturer_ids", "35"),
                ("bridge_xfilter", "true"),
            ],
        )
        assert resp.status_code == 200
        assert trip_axis_db.calls[0]["params"]["manufacturer_ids"] == [1, 43]
        assert trip_axis_db.calls[0]["params"]["xh_breaker_manufacturer_ids"] == [17, 35]
        assert "v.manufacturer_id = ANY(:manufacturer_ids)" in trip_axis_db.calls[0]["statement"]
        assert "vw_breaker_sst_bridge" in trip_axis_db.calls[0]["statement"]
        assert "manufacturer_id = ANY(:xh_breaker_manufacturer_ids)" in trip_axis_db.calls[0]["statement"]
    finally:
        _clear_db()

    breaker_axis_db = _with_db(
        FakeDb(
            [
                FakeResult(scalar_value=5),
                FakeResult(rows=[]),
                FakeResult(rows=[]),
                FakeResult(rows=[]),
            ]
        )
    )

    try:
        resp = client.get(
            "/api/v1/neta/etu/breaker-cascade",
            params=[
                ("manufacturer_ids", "17"),
                ("manufacturer_ids", "35"),
                ("trip_manufacturer_ids", "1"),
                ("trip_manufacturer_ids", "43"),
                ("bridge_xfilter", "true"),
            ],
        )
        assert resp.status_code == 200
        assert breaker_axis_db.calls[0]["params"]["manufacturer_ids"] == [17, 35]
        assert breaker_axis_db.calls[0]["params"]["xh_trip_manufacturer_ids"] == [1, 43]
        assert "manufacturer_id = ANY(:manufacturer_ids)" in breaker_axis_db.calls[0]["statement"]
        assert "vw_breaker_sst_bridge" in breaker_axis_db.calls[0]["statement"]
        assert "manufacturer_id = ANY(:xh_trip_manufacturer_ids)" in breaker_axis_db.calls[0]["statement"]
    finally:
        _clear_db()
