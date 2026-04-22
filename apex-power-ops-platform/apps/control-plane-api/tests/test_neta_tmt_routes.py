"""Route-level contract tests for bounded TMT endpoints in services.neta.router."""

import os
import sys
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_db
from main import app


FRAME_ID = 42069


@dataclass
class FakeCurvePoint:
    amps: float
    seconds: float


class FakeGenerator:
    def generate_curve(self, trip_class: int, num_output_points=None):
        assert trip_class == 2
        assert num_output_points == 12
        return [
            FakeCurvePoint(100.0, 10.0),
            FakeCurvePoint(200.0, 2.5),
            FakeCurvePoint(400.0, 0.7),
        ]

    def get_raw_points(self, trip_class: int):
        assert trip_class == 2
        return [
            FakeCurvePoint(110.0, 11.0),
            FakeCurvePoint(410.0, 0.8),
        ]


@pytest.fixture
def client():
    mock_session = MagicMock()

    def override_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _bundle():
    return {
        "generator": FakeGenerator(),
        "frame_id": FRAME_ID,
        "breaker_style_id": 9001,
        "breaker_class": "MCCB",
        "frame_size": "600AF",
        "manufacturer_name": "Square D",
        "breaker_name": "PowerPact",
        "breaker_style_name": "PXR",
        "standard": 65.0,
        "available_trip_classes": [0, 1, 2],
        "amp_ratings": [
            {"rating": 400.0, "max_override": None},
            {"rating": 600.0, "max_override": 720.0},
        ],
        "settings": [
            {"value": 5.0, "label": "Inst 5x", "tol_lo": -10.0, "tol_hi": 10.0},
            {"value": 10.0, "label": "Inst 10x", "tol_lo": -5.0, "tol_hi": 5.0},
        ],
        "thermal_adjustments": [0.8, 1.0],
    }


def test_tmt_context_returns_frame_metadata_and_counts(client):
    with patch("services.neta.router._load_tmt_contract_bundle", return_value=_bundle()):
        resp = client.get(f"/api/v1/neta/tmt/context/{FRAME_ID}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["frame_id"] == FRAME_ID
    assert body["breaker_class"] == "MCCB"
    assert body["frame_size"] == "600AF"
    assert body["manufacturer_name"] == "Square D"
    assert body["available_trip_classes"] == [0, 1, 2]
    assert body["amp_rating_count"] == 2
    assert body["setting_count"] == 2
    assert body["thermal_adjustment_count"] == 2
    assert body["resolved_equipment"]["family"] == "tmt"
    assert body["resolved_equipment"]["resolved_id"] == f"tmt_frame:{FRAME_ID}"
    assert body["resolved_equipment"]["primary_label"] == "Square D · PowerPact"
    assert body["resolved_equipment"]["breaker_context"]["label"] == "MCCB · 600AF"
    assert body["resolved_equipment"]["rating_context"]["frame_size"] == "600AF"


def test_tmt_settings_returns_selection_surface(client):
    with patch("services.neta.router._load_tmt_contract_bundle", return_value=_bundle()):
        resp = client.get(f"/api/v1/neta/tmt/settings/{FRAME_ID}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["frame_id"] == FRAME_ID
    assert body["available_trip_classes"] == [0, 1, 2]
    assert body["amp_ratings"][1] == {"rating": 600.0, "max_override": 720.0}
    assert body["settings"][0]["label"] == "Inst 5x"
    assert body["thermal_adjustments"] == [0.8, 1.0]


def test_tmt_plot_returns_nominal_curve_and_raw_points(client):
    with patch("services.neta.router._load_tmt_contract_bundle", return_value=_bundle()):
        resp = client.post(
            "/api/v1/neta/tmt/plot-tcc",
            json={
                "frame_id": FRAME_ID,
                "trip_class": 2,
                "amp_rating": 600.0,
                "setting_value": 10.0,
                "thermal_adjustment": 0.8,
                "include_raw_points": True,
                "num_output_points": 12,
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["frame_id"] == FRAME_ID
    assert body["meta"]["selected_trip_class"] == 2
    assert body["meta"]["selected_amp_rating"] == 600.0
    assert body["meta"]["selected_max_override"] == 720.0
    assert body["meta"]["selected_setting"] == 10.0
    assert body["meta"]["selected_setting_label"] == "Inst 10x"
    assert body["meta"]["selected_setting_tol_lo"] == -5.0
    assert body["meta"]["selected_setting_tol_hi"] == 5.0
    assert body["meta"]["selected_thermal_adjustment"] == 0.8
    assert body["meta"]["selections_applied_to_curve"] is False
    assert body["meta"]["resolved_equipment"]["family"] == "tmt"
    assert body["meta"]["resolved_equipment"]["secondary_label"] == "PXR · MCCB · 600AF"
    assert body["curves"][0]["id"] == "tmt_class_2"
    assert body["curves"][0]["curve_family"] == "TMT"
    assert body["curves"][0]["points"][1] == {"amps": 200.0, "seconds": 2.5}
    assert body["raw_points"][0] == {"amps": 110.0, "seconds": 11.0}
    assert "not yet applied to the plot" in body["meta"]["plot_disclaimer"]
    assert body["warnings"] == [
        "TMT selections validated and surfaced in metadata; the plotted curve remains the nominal class curve."
    ]


def test_tmt_frame_search_returns_matching_frames():
    mock_session = MagicMock()
    query = MagicMock()
    frame = SimpleNamespace(id=FRAME_ID, breaker_class="MCCB", breaker_style_id=9001, size="600AF")
    query.filter.return_value = query
    query.join.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.all.return_value = [frame]
    mock_session.query.return_value = query

    def override_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            with patch("services.neta.router._load_tmt_contract_bundle", return_value=_bundle()):
                resp = test_client.get(
                    "/api/v1/neta/tmt/frames",
                    params={
                        "breaker_class": "MCCB",
                        "manufacturer_name": "Square",
                        "breaker_name": "Power",
                        "frame_size": "600",
                        "amp_rating": 600.0,
                    },
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["frames"][0]["frame_id"] == FRAME_ID
    assert body["frames"][0]["manufacturer_name"] == "Square D"
    assert body["frames"][0]["matched_amp_rating"] == 600.0


def test_tmt_plot_rejects_invalid_selected_setting(client):
    with patch("services.neta.router._load_tmt_contract_bundle", return_value=_bundle()):
        resp = client.post(
            "/api/v1/neta/tmt/plot-tcc",
            json={
                "frame_id": FRAME_ID,
                "trip_class": 2,
                "setting_value": 99.0,
            },
        )

    assert resp.status_code == 400
    assert "Setting 99.0 is not available" in resp.json()["detail"]


def test_tmt_plot_rejects_invalid_thermal_adjustment(client):
    with patch("services.neta.router._load_tmt_contract_bundle", return_value=_bundle()):
        resp = client.post(
            "/api/v1/neta/tmt/plot-tcc",
            json={
                "frame_id": FRAME_ID,
                "trip_class": 2,
                "thermal_adjustment": 0.9,
            },
        )

    assert resp.status_code == 400
    assert "Thermal adjustment 0.9 is not available" in resp.json()["detail"]


def test_tmt_plot_rejects_unavailable_class(client):
    with patch("services.neta.router._load_tmt_contract_bundle", return_value=_bundle()):
        resp = client.post(
            "/api/v1/neta/tmt/plot-tcc",
            json={
                "frame_id": FRAME_ID,
                "trip_class": 9,
            },
        )

    assert resp.status_code == 400
    assert "Trip class 9 is not available" in resp.json()["detail"]