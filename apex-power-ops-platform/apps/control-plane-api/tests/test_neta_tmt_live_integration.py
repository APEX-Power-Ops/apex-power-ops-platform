"""Live TMT integration checks.

These tests are intentionally conditional:
- skip if the active database does not yet have the required TMT tables
- skip if the tables exist but do not yet expose searchable TMT frames

Once TMT data is available, they validate the bounded search -> context ->
settings -> nominal plot path against the real configured database rather than
patched helper bundles.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import engine
from main import app


TMT_TABLES = [
    "tcc_tmt_frames",
    "tcc_tmt_amps",
    "tcc_tmt_settings",
    "tcc_tmt_curves",
    "tcc_tmt_thermal_adj",
    "tcc_brk_iccb",
    "tcc_brk_mccb",
    "tcc_brk_pcb",
    "tcc_brk_iccb_styles",
    "tcc_brk_mccb_styles",
    "tcc_brk_pcb_styles",
    "tcc_manufacturers",
]


def _tmt_tables_available() -> bool:
    try:
        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
        return all(table in existing for table in TMT_TABLES)
    except Exception:
        return False


@pytest.mark.integration
def test_tmt_live_search_context_settings_plot_surface():
    if not _tmt_tables_available():
        pytest.skip("TMT tables are not present in the active database")

    with TestClient(app) as client:
        frames_resp = client.get("/api/v1/neta/tmt/frames", params={"limit": 5})
        assert frames_resp.status_code == 200
        frames_body = frames_resp.json()

        if frames_body["count"] == 0:
            pytest.skip("TMT tables exist but no searchable TMT frame data is loaded yet")

        frame = frames_body["frames"][0]
        frame_id = frame["frame_id"]

        context_resp = client.get(f"/api/v1/neta/tmt/context/{frame_id}")
        assert context_resp.status_code == 200
        context_body = context_resp.json()
        assert context_body["frame_id"] == frame_id
        assert isinstance(context_body["available_trip_classes"], list)
        assert context_body["available_trip_classes"]

        settings_resp = client.get(f"/api/v1/neta/tmt/settings/{frame_id}")
        assert settings_resp.status_code == 200
        settings_body = settings_resp.json()
        assert settings_body["frame_id"] == frame_id
        assert isinstance(settings_body["available_trip_classes"], list)
        assert settings_body["available_trip_classes"]
        assert isinstance(settings_body["amp_ratings"], list)
        assert isinstance(settings_body["settings"], list)
        assert isinstance(settings_body["thermal_adjustments"], list)

        trip_class = settings_body["available_trip_classes"][0]
        amp_rating = settings_body["amp_ratings"][0]["rating"] if settings_body["amp_ratings"] else None
        setting_value = settings_body["settings"][0]["value"] if settings_body["settings"] else None
        thermal_adjustment = settings_body["thermal_adjustments"][0] if settings_body["thermal_adjustments"] else None

        plot_payload = {
            "frame_id": frame_id,
            "trip_class": trip_class,
        }
        if amp_rating is not None:
            plot_payload["amp_rating"] = amp_rating
        if setting_value is not None:
            plot_payload["setting_value"] = setting_value
        if thermal_adjustment is not None:
            plot_payload["thermal_adjustment"] = thermal_adjustment

        plot_resp = client.post("/api/v1/neta/tmt/plot-tcc", json=plot_payload)
        assert plot_resp.status_code == 200
        plot_body = plot_resp.json()
        assert plot_body["meta"]["frame_id"] == frame_id
        assert plot_body["meta"]["selected_trip_class"] == trip_class
        assert plot_body["meta"]["selections_applied_to_curve"] is False
        assert isinstance(plot_body["curves"], list)
        assert plot_body["curves"]