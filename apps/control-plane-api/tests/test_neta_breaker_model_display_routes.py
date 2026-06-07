"""Breaker model-display contracts for the NETA breaker routes."""

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
            raise AssertionError("Unexpected SQL execution in breaker-model-display test")
        return self._results.pop(0)


@pytest.fixture
def client():
    return TestClient(app)


def _with_db(fake_db):
    app.dependency_overrides[get_db] = lambda: fake_db
    return fake_db


def _clear_db():
    app.dependency_overrides.clear()


def _style_row(
    style_id,
    raw_frame,
    display,
    *,
    breaker_class="PCB",
    breaker_id=900,
    breaker_name="Masterpact",
):
    return {
        "breaker_style_id": style_id,
        "style_ids": [style_id],
        "breaker_style_name": raw_frame,
        "breaker_model_display": display,
        "breaker_id": breaker_id,
        "breaker_ids": [breaker_id],
        "breaker_name": breaker_name,
        "breaker_class": breaker_class,
        "manufacturer_id": 17,
        "manufacturer_ids": [17],
        "manufacturer_name": "SQD",
        "dedupe_divergence_count": 0,
    }


def _breaker_cascade_db(*, style_rows=None, count=1):
    return FakeDb(
        [
            FakeResult(scalar_value=count),
            FakeResult(rows=[]),
            FakeResult(rows=[]),
            FakeResult(rows=[]),
            FakeResult(rows=style_rows or []),
        ]
    )


def _tmt_bundle(
    frame_id,
    style_id,
    raw_frame,
    display,
    *,
    settings=None,
    breaker_class="PCB",
):
    return {
        "frame_id": frame_id,
        "breaker_style_id": style_id,
        "breaker_class": breaker_class,
        "frame_size": "1600AF",
        "manufacturer_name": "Square D",
        "breaker_name": "Masterpact",
        "breaker_style_name": raw_frame,
        "breaker_model_display": display,
        "standard": 65.0,
        "available_trip_classes": [0, 1, 2],
        "amp_ratings": [{"rating": 1600.0, "max_override": None}],
        "settings": settings
        if settings is not None
        else [{"value": 10.0, "label": "Inst 10x", "tol_lo": -10.0, "tol_hi": 10.0}],
        "thermal_adjustments": [1.0],
    }


def test_breaker_model_aliases_surface_for_all_seeded_class_spot_checks(client):
    fake_db = _with_db(
        _breaker_cascade_db(
            style_rows=[
                _style_row(19, "75HL-3 (1600A)", "75HL-3"),
                _style_row(2370, "M12 H1 (1200A)", "M12 H1"),
                _style_row(3125, "NW12H1 (1200A)", "NW12H1"),
                _style_row(
                    36,
                    "S4N (600A)",
                    "S4N",
                    breaker_class="MCCB",
                    breaker_id=901,
                    breaker_name="Tmax",
                ),
                _style_row(
                    2585,
                    "S250-NJ (250A)",
                    "S250-NJ",
                    breaker_class="MCCB",
                    breaker_id=902,
                    breaker_name="SENTRON",
                ),
                _style_row(
                    62,
                    "MP16 H1 (1600A)",
                    "MP16 H1",
                    breaker_class="ICCB",
                    breaker_id=903,
                    breaker_name="Masterpact",
                ),
            ],
            count=6,
        )
    )

    try:
        resp = client.get(
            "/api/v1/neta/etu/breaker-cascade",
            params={"breaker_id": 900},
        )
        assert resp.status_code == 200
        styles = {
            (row["breaker_class"], row["breaker_style_id"]): row
            for row in resp.json()["breaker_styles"]
        }
        assert styles[("PCB", 19)]["breaker_model_display"] == "75HL-3"
        assert styles[("PCB", 2370)]["breaker_model_display"] == "M12 H1"
        assert styles[("PCB", 3125)]["breaker_model_display"] == "NW12H1"
        assert styles[("MCCB", 36)]["breaker_model_display"] == "S4N"
        assert styles[("MCCB", 2585)]["breaker_model_display"] == "S250-NJ"
        assert styles[("ICCB", 62)]["breaker_model_display"] == "MP16 H1"

        style_sql = fake_db.calls[4]["statement"]
        assert "tcc.breaker_style_aliases" in style_sql
        assert "bsa.breaker_class = etu_breaker_combined.breaker_class" in style_sql
        assert "bsa.breaker_style_id = etu_breaker_combined.breaker_style_id" in style_sql
    finally:
        _clear_db()


def test_breaker_model_display_falls_back_to_ep_frame_when_no_alias_row(client):
    fake_db = _with_db(
        _breaker_cascade_db(
            style_rows=[
                _style_row(4000, "EP RAW FRAME (600A)", "EP RAW FRAME (600A)"),
            ],
        )
    )

    try:
        resp = client.get(
            "/api/v1/neta/etu/breaker-cascade",
            params={"breaker_class": "PCB", "breaker_style_id": 4000},
        )
        assert resp.status_code == 200
        style = resp.json()["breaker_styles"][0]
        assert style["breaker_model_display"] == "EP RAW FRAME (600A)"

        style_sql = fake_db.calls[4]["statement"]
        assert "COALESCE(bsa.etap_model, etu_breaker_combined.breaker_style_name)" in style_sql
    finally:
        _clear_db()


def test_breaker_model_display_class_filter_qualifies_style_sql_after_alias_join(client):
    fake_db = _with_db(
        _breaker_cascade_db(
            style_rows=[
                _style_row(3125, "NW12H1 (1200A)", "NW12H1"),
            ],
        )
    )

    try:
        resp = client.get(
            "/api/v1/neta/etu/breaker-cascade",
            params={"breaker_class": "PCB", "breaker_id": 900},
        )
        assert resp.status_code == 200
        assert resp.json()["breaker_styles"][0]["breaker_model_display"] == "NW12H1"

        style_sql = fake_db.calls[4]["statement"]
        assert "WHERE etu_breaker_combined.breaker_class = :breaker_class" in style_sql
        assert "etu_breaker_combined.breaker_id = :breaker_id" in style_sql
        assert "WHERE breaker_class = :breaker_class" not in style_sql
    finally:
        _clear_db()


def test_breaker_model_alias_join_uses_composite_class_and_style_key(client):
    fake_db = _with_db(
        _breaker_cascade_db(
            style_rows=[
                _style_row(19, "PCB Raw", "75HL-3", breaker_class="PCB"),
                _style_row(
                    19,
                    "MCCB Raw",
                    "MCCB Raw",
                    breaker_class="MCCB",
                    breaker_id=901,
                    breaker_name="Different MCCB",
                ),
            ],
            count=2,
        )
    )

    try:
        resp = client.get(
            "/api/v1/neta/etu/breaker-cascade",
            params=[("breaker_style_ids", "19")],
        )
        assert resp.status_code == 200
        displays = {
            (row["breaker_class"], row["breaker_style_id"]): row["breaker_model_display"]
            for row in resp.json()["breaker_styles"]
        }
        assert displays[("PCB", 19)] == "75HL-3"
        assert displays[("MCCB", 19)] == "MCCB Raw"

        style_sql = fake_db.calls[4]["statement"]
        assert "bsa.breaker_class = etu_breaker_combined.breaker_class" in style_sql
        assert "bsa.breaker_style_id = etu_breaker_combined.breaker_style_id" in style_sql
    finally:
        _clear_db()


def test_breaker_style_dedup_rekeys_on_breaker_model_display(client):
    fake_db = _with_db(
        _breaker_cascade_db(
            style_rows=[
                {
                    **_style_row(3125, "NW12H1 (1200A)", "NW12H1"),
                    "style_ids": [3125, 3126],
                }
            ],
            count=2,
        )
    )

    try:
        resp = client.get(
            "/api/v1/neta/etu/breaker-cascade",
            params={"breaker_class": "PCB", "breaker_id": 900},
        )
        assert resp.status_code == 200
        styles = resp.json()["breaker_styles"]
        assert [row["breaker_model_display"] for row in styles] == ["NW12H1"]
        assert styles[0]["style_ids"] == [3125, 3126]

        style_sql = fake_db.calls[4]["statement"]
        assert "GROUP BY manufacturer_display, breaker_class, breaker_name, breaker_model_display" in style_sql
        assert "GROUP BY manufacturer_display, breaker_class, breaker_name, breaker_style_name" not in style_sql
    finally:
        _clear_db()


def test_tmt_frame_search_dedupes_on_breaker_model_display():
    mock_session = MagicMock()
    query = MagicMock()
    query.filter.return_value = query
    query.join.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.all.return_value = [
        SimpleNamespace(id=52000, breaker_class="PCB", breaker_style_id=3125, size="1600AF"),
        SimpleNamespace(id=52001, breaker_class="PCB", breaker_style_id=3126, size="1600AF"),
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
                    _tmt_bundle(52000, 3125, "NW12H1 (1200A)", "NW12H1"),
                    _tmt_bundle(52001, 3126, "NW12H1 1200", "NW12H1"),
                ],
            ):
                resp = test_client.get(
                    "/api/v1/neta/tmt/frames",
                    params={"breaker_class": "PCB", "manufacturer_id": 17, "limit": 200},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["dedupe_divergence_count"] == 0
    frame = body["frames"][0]
    assert frame["breaker_model_display"] == "NW12H1"
    assert frame["frame_ids"] == [52000, 52001]
    assert frame["style_ids"] == [3125, 3126]


def test_tmt_frame_search_keeps_distinct_breaker_model_displays_split():
    mock_session = MagicMock()
    query = MagicMock()
    query.filter.return_value = query
    query.join.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.all.return_value = [
        SimpleNamespace(id=53000, breaker_class="PCB", breaker_style_id=2370, size="1200AF"),
        SimpleNamespace(id=53001, breaker_class="PCB", breaker_style_id=3125, size="1200AF"),
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
                    _tmt_bundle(53000, 2370, "Shared raw frame", "M12 H1"),
                    _tmt_bundle(53001, 3125, "Shared raw frame", "NW12H1"),
                ],
            ):
                resp = test_client.get(
                    "/api/v1/neta/tmt/frames",
                    params={"breaker_class": "PCB", "manufacturer_id": 17, "limit": 200},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    assert body["dedupe_divergence_count"] == 0
    assert [row["breaker_model_display"] for row in body["frames"]] == ["M12 H1", "NW12H1"]
