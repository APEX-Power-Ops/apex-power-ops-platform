"""Route-level contract tests for bounded EMT endpoints in services.neta.router."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_db
from main import app


FRAME_ID = 456
SECTION_ID = 9001
BAND_ID = 777


@pytest.fixture
def client():
    mock_session = MagicMock()

    def override_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _frames():
    return [
        {
            "emt_id": 123,
            "frame_id": FRAME_ID,
            "manufacturer_id": 10,
            "manufacturer_name": "Example Electric",
            "type_name": "EMT Type",
            "style_name": "EMT Style",
            "tcc_number": "TCC-001",
            "trip_char": 7,
            "trip_plug": 0,
            "frame_size": 800.0,
            "frame_desc": "800A Frame",
            "amp_rating_count": 4,
            "section_count": 3,
        }
    ]


def _context_bundle():
    return {
        "emt_id": 123,
        "frame_id": FRAME_ID,
        "manufacturer_id": 10,
        "manufacturer_name": "Example Electric",
        "type_name": "EMT Type",
        "style_name": "EMT Style",
        "tcc_number": "TCC-001",
        "trip_char": 7,
        "trip_plug": 0,
        "frame_size": 800.0,
        "frame_desc": "800A Frame",
        "amp_ratings": [400.0, 600.0, 800.0],
        "sections": [
            {
                "section_id": SECTION_ID,
                "name": "Long Time",
                "sec_char": 1,
                "curve_type": 0,
                "pickup_calc": 0,
                "pickup_setting": 0,
                "step_size": None,
                "current_calc": 0,
                "pickup_tol_lo": -10.0,
                "pickup_tol_hi": 10.0,
                "band_count": 3,
                "pickup_count": 8,
            }
        ],
    }


def _settings_bundle():
    return {
        "section_id": SECTION_ID,
        "name": "Long Time",
        "sec_char": 1,
        "curve_type": 0,
        "pickup_calc": 0,
        "pickup_setting": 0,
        "step_size": None,
        "current_calc": 0,
        "pickup_tol_lo": -10.0,
        "pickup_tol_hi": 10.0,
        "pickups": [
            {"setting": 1.0, "description": "1x"},
            {"setting": 1.25, "description": "1.25x"},
        ],
        "bands": [
            {
                "band_id": 777,
                "band_name": "Band A",
                "ordinal": 1,
                "current_at": 1.0,
                "curve_point_count": 24,
                "curve_classes": [0, 1],
            }
        ],
    }


def _plot_bundle():
    return {
        "emt_id": 123,
        "frame_id": FRAME_ID,
        "section_id": SECTION_ID,
        "band_id": BAND_ID,
        "manufacturer_id": 10,
        "manufacturer_name": "Example Electric",
        "type_name": "EMT Type",
        "style_name": "EMT Style",
        "tcc_number": "TCC-001",
        "frame_size": 800.0,
        "frame_desc": "800A Frame",
        "section_name": "Long Time",
        "sec_char": 1,
        "curve_type": 0,
        "pickup_calc": 0,
        "pickup_setting": 0,
        "current_calc": 0,
        "band_name": "Band A",
        "band_ordinal": 1,
        "current_at": 1.0,
        "available_curve_classes": [0, 1],
        "grouped_curves": {
            0: [
                {"curve_class": 0, "current_amp": 100.0, "time_sec": 10.0},
                {"curve_class": 0, "current_amp": 200.0, "time_sec": 2.5},
            ],
            1: [
                {"curve_class": 1, "current_amp": 100.0, "time_sec": 12.0},
                {"curve_class": 1, "current_amp": 200.0, "time_sec": 3.0},
            ],
        },
    }


def test_emt_frame_search_returns_bounded_discovery_surface(client):
    with patch("services.neta.router._search_emt_frames", return_value=_frames()):
        resp = client.get(
            "/api/v1/neta/emt/frames",
            params={"manufacturer_id": 10, "trip_char": 7, "trip_plug": 0, "q": "EMT"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["frames"][0]["frame_id"] == FRAME_ID
    assert body["frames"][0]["manufacturer_name"] == "Example Electric"
    assert body["frames"][0]["amp_rating_count"] == 4
    assert body["frames"][0]["section_count"] == 3


def test_emt_context_returns_frame_inventory_surface(client):
    with patch("services.neta.router._load_emt_frame_context_bundle", return_value=_context_bundle()):
        resp = client.get(f"/api/v1/neta/emt/context/{FRAME_ID}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["frame_id"] == FRAME_ID
    assert body["manufacturer_name"] == "Example Electric"
    assert body["amp_ratings"] == [400.0, 600.0, 800.0]
    assert body["sections"][0]["section_id"] == SECTION_ID
    assert body["sections"][0]["band_count"] == 3
    assert body["resolved_equipment"]["family"] == "emt"
    assert body["resolved_equipment"]["resolved_id"] == f"emt_frame:{FRAME_ID}"
    assert body["resolved_equipment"]["primary_label"] == "Example Electric · EMT Type · EMT Style"
    assert body["resolved_equipment"]["rating_context"]["amp_ratings"] == [400.0, 600.0, 800.0]


def test_emt_settings_returns_pickups_and_band_inventory(client):
    with patch("services.neta.router._load_emt_section_settings_bundle", return_value=_settings_bundle()):
        resp = client.get(f"/api/v1/neta/emt/settings/{SECTION_ID}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["section_id"] == SECTION_ID
    assert body["pickups"][0] == {"setting": 1.0, "description": "1x"}
    assert body["bands"][0]["band_name"] == "Band A"
    assert body["bands"][0]["curve_classes"] == [0, 1]


def test_emt_routes_surface_migration_gated_errors(client):
    with patch(
        "services.neta.router._load_emt_frame_context_bundle",
        side_effect=HTTPException(status_code=503, detail="EMT catalog tables are not available in the current database."),
    ):
        resp = client.get(f"/api/v1/neta/emt/context/{FRAME_ID}")

    assert resp.status_code == 503
    assert "EMT catalog tables are not available" in resp.json()["detail"]


def test_emt_plot_returns_raw_band_point_data(client):
    with patch("services.neta.router._load_emt_plot_bundle", return_value=_plot_bundle()):
        resp = client.post(
            "/api/v1/neta/emt/plot-tcc",
            json={"section_id": SECTION_ID, "band_id": BAND_ID},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["section_id"] == SECTION_ID
    assert body["meta"]["band_id"] == BAND_ID
    assert body["meta"]["available_curve_classes"] == [0, 1]
    assert body["meta"]["selected_curve_class"] is None
    assert body["meta"]["selections_applied_to_curve"] is False
    assert body["meta"]["resolved_equipment"]["family"] == "emt"
    assert body["meta"]["resolved_equipment"]["secondary_label"] == "800A Frame · Long Time"
    assert body["meta"]["resolved_equipment"]["breaker_context"]["tcc_number"] == "TCC-001"
    assert len(body["curves"]) == 2
    assert body["curves"][0]["curve_family"] == "EMT"
    assert body["curves"][0]["class_label"] == "opening"
    assert body["curves"][1]["class_label"] == "clearing"
    assert body["curves"][0]["points"][1] == {"amps": 200.0, "seconds": 2.5}
    assert "raw emt point-data" in body["meta"]["plot_disclaimer"].lower()
    assert "Multiple stored EMT curve classes returned" in body["warnings"][0]


def test_emt_plot_rejects_unavailable_curve_class(client):
    with patch("services.neta.router._load_emt_plot_bundle", return_value=_plot_bundle()):
        resp = client.post(
            "/api/v1/neta/emt/plot-tcc",
            json={"section_id": SECTION_ID, "band_id": BAND_ID, "curve_class": 9},
        )

    assert resp.status_code == 400
    assert "Curve class 9 is not available" in resp.json()["detail"]