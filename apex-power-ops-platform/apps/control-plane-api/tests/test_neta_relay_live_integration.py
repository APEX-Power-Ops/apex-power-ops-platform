"""Live relay integration checks.

These tests are intentionally conditional:
- skip if the active database does not yet have the governed relay work-schema tables
- skip if the relay tables exist but expose no searchable supported TD-sections

Once relay data is available, they validate the bounded read-only discovery ->
context -> settings -> preview path against the real configured database.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import engine
from main import app


RELAY_TABLES = [
    "tcc_relays",
    "tcc_relay_devices",
    "tcc_relay_line_sections",
    "tcc_relay_td_sections",
    "tcc_relay_ranges",
    "tcc_relay_curves_iec",
    "tcc_relay_curve_rows_iec",
    "tcc_relay_curves_tcp",
    "tcc_relay_curve_points_tcp",
]


def _relay_tables_available() -> bool:
    try:
        inspector = inspect(engine)
        schemas = set(inspector.get_schema_names())
        if "work" not in schemas:
            return False
        existing = set(inspector.get_table_names(schema="work"))
        return all(table in existing for table in RELAY_TABLES)
    except Exception:
        return False


@pytest.mark.integration
def test_relay_live_discovery_context_settings_preview_surface():
    if not _relay_tables_available():
        pytest.skip("Relay work-schema tables are not present in the active database")

    with TestClient(app) as client:
        search_resp = client.get("/api/v1/neta/relay/sections", params={"supported_only": True, "limit": 5})
        assert search_resp.status_code == 200
        search_body = search_resp.json()

        if search_body["count"] == 0:
            pytest.skip("Relay tables exist but no supported relay TD-sections are loaded yet")

        section = search_body["sections"][0]
        td_section_source_id = section["td_section_source_id"]

        context_resp = client.get(f"/api/v1/neta/relay/context/{td_section_source_id}")
        assert context_resp.status_code == 200
        context_body = context_resp.json()
        assert context_body["td_section_source_id"] == td_section_source_id
        assert context_body["supported"] is True
        assert isinstance(context_body["line_sections"], list)

        settings_resp = client.get(f"/api/v1/neta/relay/settings/{td_section_source_id}")
        assert settings_resp.status_code == 200
        settings_body = settings_resp.json()
        assert settings_body["td_section_source_id"] == td_section_source_id
        assert settings_body["supported"] is True
        assert isinstance(settings_body["curve_parents"], list)
        assert isinstance(settings_body["preview_options"], list)

        if not settings_body["preview_options"]:
            pytest.skip(f"Relay TD-section {td_section_source_id} has no stored preview options loaded yet")

        preview_option = settings_body["preview_options"][0]
        payload = {
            "td_section_source_id": td_section_source_id,
            "current_multiples": [2.0, 5.0, 10.0],
        }
        if preview_option.get("curve_parent_source_id") is not None:
            payload["curve_parent_source_id"] = preview_option["curve_parent_source_id"]
        if preview_option.get("curve_ordinal") is not None:
            payload["curve_ordinal"] = preview_option["curve_ordinal"]
            payload["time_dial"] = 1.0
        if preview_option.get("source_ordinal") is not None:
            payload["source_ordinal"] = preview_option["source_ordinal"]

        preview_resp = client.post("/api/v1/neta/relay/plot-tcc", json=payload)
        assert preview_resp.status_code == 200
        preview_body = preview_resp.json()
        assert preview_body["meta"]["td_section_source_id"] == td_section_source_id
        assert preview_body["meta"]["status"] == "supported"
        assert isinstance(preview_body["curves"], list)
        assert preview_body["curves"]