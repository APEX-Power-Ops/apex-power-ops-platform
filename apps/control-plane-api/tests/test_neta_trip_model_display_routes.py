"""Trip-unit model-display contracts for the NETA ETU cascade route."""

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
            raise AssertionError("Unexpected SQL execution in trip-model-display test")
        return self._results.pop(0)


@pytest.fixture
def client():
    return TestClient(app)


def _trip_type_row(
    trip_type_id=420,
    trip_type_name="Raw Trip Type",
    *,
    style_ids=None,
    trip_model_display=None,
):
    return {
        "trip_type_id": trip_type_id,
        "trip_type_ids": [trip_type_id],
        "style_ids": style_ids or [238],
        "trip_type_name": trip_type_name,
        "trip_model_display": trip_model_display or trip_type_name,
        "manufacturer_id": 17,
        "manufacturer_ids": [17],
        "manufacturer_name": "SQD",
        "trip_style_count": len(style_ids or [238]),
        "dedupe_divergence_count": 0,
    }


def _trip_style_row(
    trip_style_id,
    trip_style_name,
    *,
    style_ids=None,
    trip_type_ids=None,
    trip_model_display=None,
):
    return {
        "trip_style_id": trip_style_id,
        "style_ids": style_ids or [trip_style_id],
        "trip_style_name": trip_style_name,
        "trip_model_display": trip_model_display or trip_style_name,
        "trip_type_id": 420,
        "trip_type_ids": trip_type_ids or [420],
        "trip_type_name": "Raw Trip Type",
        "manufacturer_id": 17,
        "manufacturer_ids": [17],
        "manufacturer_name": "SQD",
        "sensor_count": 1,
        "dedupe_divergence_count": 0,
    }


def _fake_cascade_db(*, trip_type_rows=None, trip_style_rows=None, count=1):
    return FakeDb(
        [
            FakeResult(scalar_value=count),
            FakeResult(rows=[]),
            FakeResult(rows=trip_type_rows or []),
            FakeResult(rows=trip_style_rows or []),
            FakeResult(rows=[]),
        ]
    )


def _with_db(fake_db):
    app.dependency_overrides[get_db] = lambda: fake_db
    return fake_db


def _clear_db():
    app.dependency_overrides.clear()


def test_trip_model_aliases_surface_for_known_seed_spot_checks(client):
    fake_db = _with_db(
        _fake_cascade_db(
            trip_style_rows=[
                _trip_style_row(238, "MICROLOGIC 6.0A", trip_model_display="MICROLOGIC 6.0"),
                _trip_style_row(871, "STR53UP", trip_model_display="STR53UP"),
            ],
            count=2,
        )
    )

    try:
        resp = client.get("/api/v1/neta/cascade")
        assert resp.status_code == 200
        styles = {row["trip_style_id"]: row for row in resp.json()["trip_styles"]}
        assert styles[238]["trip_model_display"] == "MICROLOGIC 6.0"
        assert styles[871]["trip_model_display"] == "STR53UP"

        trip_style_sql = fake_db.calls[3]["statement"]
        assert "tcc.trip_model_aliases" in trip_style_sql
    finally:
        _clear_db()


def test_authoritative_exact_or_core_alias_wins_before_trip_model_aliases(client):
    fake_db = _with_db(
        _fake_cascade_db(
            trip_style_rows=[
                _trip_style_row(
                    1200,
                    "EP Raw Alias Candidate",
                    trip_model_display="AUTHORITATIVE ETAP ALIAS",
                )
            ],
        )
    )

    try:
        resp = client.get("/api/v1/neta/cascade")
        assert resp.status_code == 200
        style = resp.json()["trip_styles"][0]
        assert style["trip_model_display"] == "AUTHORITATIVE ETAP ALIAS"

        trip_style_sql = fake_db.calls[3]["statement"]
        assert "tcc.trip_style_aliases" in trip_style_sql
        assert "tsa.match_tier IN ('exact', 'core')" in trip_style_sql
        assert "ORDER BY CASE tsa.match_tier" in trip_style_sql
        assert "LIMIT 1" in trip_style_sql
    finally:
        _clear_db()


def test_trip_model_display_falls_back_to_ep_label_when_no_alias_rows(client):
    fake_db = _with_db(
        _fake_cascade_db(
            trip_style_rows=[
                _trip_style_row(2600, "EP FALLBACK STYLE", trip_model_display="EP FALLBACK STYLE")
            ],
        )
    )

    try:
        resp = client.get("/api/v1/neta/cascade")
        assert resp.status_code == 200
        style = resp.json()["trip_styles"][0]
        assert style["trip_model_display"] == "EP FALLBACK STYLE"

        trip_style_sql = fake_db.calls[3]["statement"]
        assert "COALESCE(tsa.alias_name, tma.etap_model, v.trip_style_name)" in trip_style_sql
    finally:
        _clear_db()


def test_frame_tier_aliases_are_withheld_from_display_resolution(client):
    fake_db = _with_db(
        _fake_cascade_db(
            trip_style_rows=[
                _trip_style_row(
                    2456,
                    "Micrologic 4.2",
                    trip_model_display="MICROLOGIC 2.0",
                )
            ],
        )
    )

    try:
        resp = client.get("/api/v1/neta/cascade")
        assert resp.status_code == 200
        style = resp.json()["trip_styles"][0]
        assert style["trip_model_display"] == "MICROLOGIC 2.0"

        trip_style_sql = fake_db.calls[3]["statement"]
        assert "tsa.match_tier IN ('exact', 'core')" in trip_style_sql
        assert "'frame'" not in trip_style_sql.lower()
    finally:
        _clear_db()


def test_trip_style_dedup_rekeys_on_trip_model_display_and_unions_style_ids(client):
    fake_db = _with_db(
        _fake_cascade_db(
            trip_type_rows=[
                _trip_type_row(
                    trip_type_id=700,
                    trip_type_name="Raw Type A",
                    style_ids=[610, 611],
                    trip_model_display="SHARED ETAP MODEL",
                )
            ],
            trip_style_rows=[
                _trip_style_row(
                    610,
                    "Raw Style A",
                    style_ids=[610, 611],
                    trip_type_ids=[700, 701],
                    trip_model_display="SHARED ETAP MODEL",
                )
            ],
            count=2,
        )
    )

    try:
        resp = client.get("/api/v1/neta/cascade", params={"manufacturer_id": 17})
        assert resp.status_code == 200
        body = resp.json()
        assert [row["trip_model_display"] for row in body["trip_styles"]] == ["SHARED ETAP MODEL"]
        merged = body["trip_styles"][0]
        assert merged["trip_style_id"] == 610
        assert merged["style_ids"] == [610, 611]
        assert merged["trip_type_ids"] == [700, 701]

        assert body["trip_types"][0]["trip_model_display"] == "SHARED ETAP MODEL"
        assert body["trip_types"][0]["style_ids"] == [610, 611]

        trip_type_sql = fake_db.calls[2]["statement"]
        trip_style_sql = fake_db.calls[3]["statement"]
        assert "GROUP BY manufacturer_display, trip_model_display" in trip_type_sql
        assert "GROUP BY manufacturer_display, trip_model_display" in trip_style_sql
        assert "GROUP BY manufacturer_display, trip_type_name, trip_style_name" not in trip_style_sql
    finally:
        _clear_db()
