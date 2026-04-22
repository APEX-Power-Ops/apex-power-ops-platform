"""Live EMT integration checks.

These tests are intentionally conditional:
- skip if the active database does not yet have EMT tables
- skip if the EMT tables exist but have no catalog data

Once EMT data is loaded, they validate the bounded discovery/context/settings surface
against the real configured database rather than patched helpers.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import engine
from main import app


EMT_TABLES = [
    "tcc_emt",
    "tcc_emt_frames",
    "tcc_emt_frame_amps",
    "tcc_emt_sections",
    "tcc_emt_band_names",
    "tcc_emt_pickups",
    "tcc_emt_curves",
]


def _emt_tables_available() -> bool:
    try:
        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
        return all(table in existing for table in EMT_TABLES)
    except Exception:
        return False


@pytest.mark.integration
def test_emt_live_discovery_context_settings_surface():
    if not _emt_tables_available():
        pytest.skip("EMT tables are not present in the active database")

    with TestClient(app) as client:
        frames_resp = client.get("/api/v1/neta/emt/frames", params={"limit": 1})

        if frames_resp.status_code == 503:
            pytest.skip(frames_resp.json().get("detail", "EMT catalog still migration-gated"))

        assert frames_resp.status_code == 200
        frames_body = frames_resp.json()

        if frames_body["count"] == 0:
            pytest.skip("EMT tables exist but no EMT frame data is loaded yet")

        frame = frames_body["frames"][0]
        frame_id = frame["frame_id"]

        context_resp = client.get(f"/api/v1/neta/emt/context/{frame_id}")
        assert context_resp.status_code == 200
        context_body = context_resp.json()
        assert context_body["frame_id"] == frame_id
        assert isinstance(context_body["amp_ratings"], list)
        assert isinstance(context_body["sections"], list)

        if not context_body["sections"]:
            pytest.skip(f"EMT frame {frame_id} has no section rows loaded yet")

        section_id = context_body["sections"][0]["section_id"]

        settings_resp = client.get(f"/api/v1/neta/emt/settings/{section_id}")
        assert settings_resp.status_code == 200
        settings_body = settings_resp.json()
        assert settings_body["section_id"] == section_id
        assert isinstance(settings_body["pickups"], list)
        assert isinstance(settings_body["bands"], list)

        if not settings_body["bands"]:
            pytest.skip(f"EMT section {section_id} has no band rows loaded yet")

        band_id = settings_body["bands"][0]["band_id"]
        plot_resp = client.post(
            "/api/v1/neta/emt/plot-tcc",
            json={"section_id": section_id, "band_id": band_id},
        )
        assert plot_resp.status_code == 200
        plot_body = plot_resp.json()
        assert plot_body["meta"]["section_id"] == section_id
        assert plot_body["meta"]["band_id"] == band_id
        assert isinstance(plot_body["curves"], list)
        assert plot_body["curves"]