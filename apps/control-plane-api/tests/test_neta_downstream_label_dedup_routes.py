"""Downstream exact-label dedupe contracts for NETA selector routes."""

import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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
            raise AssertionError("Unexpected SQL execution in downstream dedupe test")
        return self._results.pop(0)


@pytest.fixture
def client():
    return TestClient(app)


def _with_db(fake_db):
    app.dependency_overrides[get_db] = lambda: fake_db
    return fake_db


def _clear_db():
    app.dependency_overrides.clear()


def _tmt_bundle(frame_id: int, style_id: int, *, settings=None):
    return {
        "frame_id": frame_id,
        "breaker_style_id": style_id,
        "breaker_class": "MCCB",
        "frame_size": "600AF",
        "manufacturer_name": "Square D",
        "breaker_name": "PowerPact",
        "breaker_style_name": "H Frame",
        "standard": 65.0,
        "available_trip_classes": [0, 1, 2],
        "amp_ratings": [{"rating": 600.0, "max_override": None}],
        "settings": settings
        if settings is not None
        else [{"value": 10.0, "label": "Inst 10x", "tol_lo": -10.0, "tol_hi": 10.0}],
        "thermal_adjustments": [1.0],
    }


def test_etu_breaker_names_dedupe_by_label_and_expose_style_ids(client):
    fake_db = _with_db(
        FakeDb(
            [
                FakeResult(scalar_value=3),
                FakeResult(rows=[]),
                FakeResult(rows=[]),
                FakeResult(
                    rows=[
                        {
                            "breaker_id": 500,
                            "breaker_ids": [500, 501],
                            "style_ids": [7000, 7001],
                            "breaker_name": "(Std)",
                            "breaker_class": "MCCB",
                            "manufacturer_id": 17,
                            "manufacturer_name": "SQD",
                            "style_count": 2,
                            "dedupe_divergence_count": 0,
                        },
                        {
                            "breaker_id": 502,
                            "breaker_ids": [502],
                            "style_ids": [7002],
                            "breaker_name": "MP NW UL489",
                            "breaker_class": "MCCB",
                            "manufacturer_id": 17,
                            "manufacturer_name": "SQD",
                            "style_count": 1,
                            "dedupe_divergence_count": 0,
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
                ("breaker_class", "MCCB"),
            ],
        )
        assert resp.status_code == 200
        breakers = resp.json()["breakers"]
        assert [row["breaker_name"] for row in breakers].count("(Std)") == 1
        assert [row["breaker_name"] for row in breakers].count("MP NW UL489") == 1
        std = next(row for row in breakers if row["breaker_name"] == "(Std)")
        assert std["breaker_id"] == 500
        assert std["breaker_ids"] == [500, 501]
        assert std["style_ids"] == [7000, 7001]
        assert std["style_count"] == 2

        breaker_sql = fake_db.calls[3]["statement"]
        assert "ARRAY_AGG" in breaker_sql
        assert "COUNT(DISTINCT breaker_style_id)" in breaker_sql
        assert "GROUP BY manufacturer_display, breaker_class, breaker_name" in breaker_sql
    finally:
        _clear_db()


def test_trip_types_dedupe_by_label_and_expose_downstream_style_ids(client):
    fake_db = _with_db(
        FakeDb(
            [
                FakeResult(scalar_value=4),
                FakeResult(rows=[]),
                FakeResult(
                    rows=[
                        {
                            "trip_type_id": 75,
                            "trip_type_ids": [75, 176],
                            "style_ids": [900, 901, 902],
                            "trip_type_name": "Power Shield",
                            "manufacturer_id": 4,
                            "manufacturer_ids": [4, 11, 125, 173],
                            "manufacturer_name": "Brown Boveri",
                            "trip_style_count": 3,
                            "dedupe_divergence_count": 0,
                        }
                    ]
                ),
                FakeResult(rows=[]),
                FakeResult(rows=[]),
            ]
        )
    )

    try:
        resp = client.get(
            "/api/v1/neta/cascade",
            params=[
                ("manufacturer_ids", "4"),
                ("manufacturer_ids", "11"),
                ("manufacturer_ids", "125"),
                ("manufacturer_ids", "173"),
            ],
        )
        assert resp.status_code == 200
        types = resp.json()["trip_types"]
        assert [row["trip_type_name"] for row in types].count("Power Shield") == 1
        power_shield = types[0]
        assert power_shield["trip_type_id"] == 75
        assert power_shield["trip_type_ids"] == [75, 176]
        assert power_shield["style_ids"] == [900, 901, 902]
        assert power_shield["trip_style_count"] == 3

        trip_type_sql = fake_db.calls[2]["statement"]
        assert "ARRAY_AGG" in trip_type_sql
        assert "COUNT(DISTINCT trip_style_id)" in trip_type_sql
        assert "GROUP BY manufacturer_display, trip_model_display" in trip_type_sql
    finally:
        _clear_db()


def test_bridge_sensors_accepts_deduped_breaker_style_id_sets(client):
    fake_db = _with_db(
        FakeDb(
            [
                FakeResult(
                    rows=[
                        {
                            "breaker_class": "MCCB",
                            "breaker_id": 101,
                            "breaker_style_id": 7000,
                            "breaker_style_frame": "H Frame",
                            "tmt_sst_mfr": "Square D",
                            "tmt_sst_type": "PowerPact",
                            "tmt_sst_style": "Micrologic",
                            "trip_style_id": 900,
                            "sensor_id": 15000,
                            "sensor_rating": 600,
                            "sensor_description": "600A",
                            "r_cont_current": None,
                        },
                        {
                            "breaker_class": "MCCB",
                            "breaker_id": 102,
                            "breaker_style_id": 7001,
                            "breaker_style_frame": "H Frame",
                            "tmt_sst_mfr": "Square D",
                            "tmt_sst_type": "PowerPact",
                            "tmt_sst_style": "Micrologic",
                            "trip_style_id": 901,
                            "sensor_id": 15001,
                            "sensor_rating": 800,
                            "sensor_description": "800A",
                            "r_cont_current": None,
                        },
                    ]
                )
            ]
        )
    )

    try:
        resp = client.get(
            "/api/v1/neta/etu/bridge-sensors",
            params=[
                ("breaker_style_ids", "7000"),
                ("breaker_style_ids", "7001"),
                ("breaker_class", "MCCB"),
            ],
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["breaker_style_ids"] == [7000, 7001]
        assert body["count"] == 2
        assert {sensor["sensor_id"] for sensor in body["sensors"]} == {15000, 15001}
        assert fake_db.calls[0]["params"]["bsids"] == [7000, 7001]
        assert "breaker_style_id = ANY(:bsids)" in fake_db.calls[0]["statement"]
    finally:
        _clear_db()


def test_tmt_frame_search_dedupes_exact_frame_labels_and_exposes_frame_sets():
    mock_session = MagicMock()
    query = MagicMock()
    query.filter.return_value = query
    query.join.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.all.return_value = [
        SimpleNamespace(id=42000, breaker_class="MCCB", breaker_style_id=7000, size="600AF"),
        SimpleNamespace(id=42001, breaker_class="MCCB", breaker_style_id=7001, size="600AF"),
    ]
    mock_session.query.return_value = query

    def override_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            with patch(
                "services.neta.router._load_tmt_contract_bundle",
                side_effect=[
                    _tmt_bundle(42000, 7000),
                    _tmt_bundle(42001, 7001),
                ],
            ):
                resp = test_client.get(
                    "/api/v1/neta/tmt/frames",
                    params=[
                        ("breaker_class", "MCCB"),
                        ("manufacturer_ids", "17"),
                        ("manufacturer_ids", "35"),
                        ("manufacturer_ids", "235"),
                        ("limit", "200"),
                    ],
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["dedupe_divergence_count"] == 0
    frame = body["frames"][0]
    assert frame["frame_id"] == 42000
    assert frame["frame_ids"] == [42000, 42001]
    assert frame["style_ids"] == [7000, 7001]
    assert frame["breaker_name"] == "PowerPact"
    assert frame["breaker_style_name"] == "H Frame"


def test_tmt_frame_search_reports_divergent_duplicate_frame_labels_without_crashing():
    mock_session = MagicMock()
    query = MagicMock()
    query.filter.return_value = query
    query.join.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.all.return_value = [
        SimpleNamespace(id=43000, breaker_class="MCCB", breaker_style_id=7100, size="600AF"),
        SimpleNamespace(id=43001, breaker_class="MCCB", breaker_style_id=7101, size="600AF"),
    ]
    mock_session.query.return_value = query

    def override_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            with patch(
                "services.neta.router._load_tmt_contract_bundle",
                side_effect=[
                    _tmt_bundle(
                        43000,
                        7100,
                        settings=[
                            {"value": 5.0, "label": "Inst 5x", "tol_lo": -10.0, "tol_hi": 10.0}
                        ],
                    ),
                    _tmt_bundle(
                        43001,
                        7101,
                        settings=[
                            {"value": 10.0, "label": "Inst 10x", "tol_lo": -10.0, "tol_hi": 10.0}
                        ],
                    ),
                ],
            ):
                resp = test_client.get(
                    "/api/v1/neta/tmt/frames",
                    params={"breaker_class": "MCCB", "manufacturer_id": 17, "limit": 200},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["dedupe_divergence_count"] == 1
    frame = body["frames"][0]
    assert frame["dedupe_divergence_count"] == 1
    assert frame["frame_ids"] == [43000, 43001]
    assert frame["style_ids"] == [7100, 7101]
