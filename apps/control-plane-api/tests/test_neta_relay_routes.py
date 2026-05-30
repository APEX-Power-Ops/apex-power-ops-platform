"""Route-level contract tests for bounded relay endpoints in services.neta.router."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_db
from main import app


TD_SECTION_SOURCE_ID = 30154


@pytest.fixture
def client():
    mock_session = MagicMock()

    def override_db():
        yield mock_session

    with patch("services.neta.router._relay_work_schema_tables_available", return_value=True):
        app.dependency_overrides[get_db] = override_db
        yield TestClient(app)
        app.dependency_overrides.clear()


def _relay_search_rows():
    return [
        {
            "manufacturer_source_id": 42,
            "relay_type": "DT-3000",
            "relay_device_source_id": 4169,
            "device_function": "51/50/50 IEC",
            "device_ordinal": 20,
            "standard_code": 1,
            "dftype_code": 3,
            "voltage_restraint_kind": "none",
            "td_section_source_id": TD_SECTION_SOURCE_ID,
            "td_section_name": "Time Dial",
            "family_code": 2,
            "family_name": "iec",
            "storage_kind": "constants",
            "supported": True,
        }
    ]


def _resolved_equipment():
    return {
        "family": "relay",
        "family_label": "Relay",
        "resolved_id": f"relay_td_section:{TD_SECTION_SOURCE_ID}",
        "primary_label": "DT-3000 · 51/50/50 IEC",
        "secondary_label": "Time Dial · IEC",
        "breaker_context": {
            "label": "DT-3000 · 51/50/50 IEC",
            "source": "relay_catalog",
            "type_name": "DT-3000",
        },
        "rating_context": {
            "label": "Section · Time Dial",
            "section_name": "Time Dial",
        },
    }


def _relay_context_bundle():
    return {
        **_relay_search_rows()[0],
        "unsupported_reason": None,
        "line_section_count": 2,
        "range_count": 1,
        "curve_parent_count": 1,
        "preview_option_count": 4,
        "line_sections": [
            {
                "line_section_source_id": 88001,
                "section_number": 1,
                "section_name": "I>",
                "pickup": 2.0,
                "secondary_i_code": 0,
                "amps_calc_mode": 0,
                "use_toc_multiplier": False,
            },
            {
                "line_section_source_id": 88002,
                "section_number": 4,
                "section_name": "Time Delay",
                "pickup": 0.0,
                "secondary_i_code": 0,
                "amps_calc_mode": 0,
                "use_toc_multiplier": False,
            },
        ],
        "resolved_equipment": _resolved_equipment(),
    }


def _relay_settings_bundle():
    return {
        **_relay_context_bundle(),
        "ranges": [
            {
                "range_source_id": 99001,
                "source_parent_id": TD_SECTION_SOURCE_ID,
                "parent_kind": "td_section",
                "parent_label": "Time Dial",
                "aux_key": 1002,
                "ordinal": 1,
                "min_value": 0.1,
                "max_value": 1.0,
                "step_value": 0.1,
                "relative_unit_code": 0,
                "use_range": True,
                "scales_with_time_multiplier": False,
                "discrete_values": [],
            }
        ],
        "curve_parents": [
            {
                "curve_parent_source_id": 34480,
                "storage_kind": "constants",
                "curve_name": None,
                "curve_parent_ordinal": None,
                "min_pickup": 1.03,
                "max_pickup": 40.0,
                "is_discrete": None,
                "step_size": None,
                "horizontal_amps_code": None,
                "preview_option_count": 4,
            }
        ],
        "preview_options": [
            {
                "curve_parent_source_id": 34480,
                "storage_kind": "constants",
                "curve_name": "NI",
                "curve_ordinal": 10,
                "source_ordinal": None,
                "time_dial": None,
                "td_desc": None,
                "point_count": None,
                "current_min": 1.03,
                "current_max": 40.0,
                "coefficients": {
                    "v_k": 0.14,
                    "v_e": 0.02,
                    "dt_after": 20.0,
                    "dt_min_time": 0.06,
                },
            }
        ],
    }


def _relay_preview_bundle():
    return {
        **_relay_settings_bundle(),
        "status": "supported",
        "warnings": [],
        "selected_option": _relay_settings_bundle()["preview_options"][0],
        "result": type(
            "RelayResult",
            (),
            {
                "curve_name": "NI",
                "time_dial": 1.0,
                "points": [
                    type("Point", (), {"current_multiple": 2.0, "trip_time_seconds": 10.029027020046872})(),
                    type("Point", (), {"current_multiple": 10.0, "trip_time_seconds": 2.9705986243944098})(),
                ],
            },
        )(),
    }


def _relay_unsupported_preview_bundle():
    return {
        **_relay_context_bundle(),
        "family_code": 7,
        "family_name": "rxd",
        "storage_kind": "unsupported",
        "supported": False,
        "unsupported_reason": "rxd relay family remains explicitly unsupported in Tranche 4.",
        "status": "unsupported",
        "warnings": ["rxd relay family remains explicitly unsupported in Tranche 4."],
        "selected_option": None,
        "result": None,
    }


def test_relay_section_search_returns_bounded_rows(client):
    with patch("services.neta.router._search_relay_sections", return_value=_relay_search_rows()):
        resp = client.get("/api/v1/neta/relay/sections", params={"supported_only": True, "limit": 5})

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert body["sections"][0]["td_section_source_id"] == TD_SECTION_SOURCE_ID
    assert body["sections"][0]["family_name"] == "iec"
    assert body["sections"][0]["supported"] is True


def test_relay_context_returns_metadata_and_counts(client):
    with patch("services.neta.router._load_relay_context_bundle", return_value=_relay_context_bundle()):
        resp = client.get(f"/api/v1/neta/relay/context/{TD_SECTION_SOURCE_ID}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["td_section_source_id"] == TD_SECTION_SOURCE_ID
    assert body["relay_device_source_id"] == 4169
    assert body["family_code"] == 2
    assert body["family_name"] == "iec"
    assert body["line_section_count"] == 2
    assert body["preview_option_count"] == 4
    assert body["resolved_equipment"]["family"] == "relay"
    assert body["resolved_equipment"]["resolved_id"] == f"relay_td_section:{TD_SECTION_SOURCE_ID}"


def test_relay_settings_returns_ranges_and_preview_options(client):
    with patch("services.neta.router._load_relay_settings_bundle", return_value=_relay_settings_bundle()):
        resp = client.get(f"/api/v1/neta/relay/settings/{TD_SECTION_SOURCE_ID}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["td_section_source_id"] == TD_SECTION_SOURCE_ID
    assert body["supported"] is True
    assert body["ranges"][0]["parent_kind"] == "td_section"
    assert body["curve_parents"][0]["curve_parent_source_id"] == 34480
    assert body["preview_options"][0]["curve_name"] == "NI"
    assert body["preview_options"][0]["coefficients"]["v_k"] == 0.14


def test_relay_plot_returns_preview_curve(client):
    with patch("services.neta.router._load_relay_preview_bundle", return_value=_relay_preview_bundle()):
        resp = client.post(
            "/api/v1/neta/relay/plot-tcc",
            json={
                "td_section_source_id": TD_SECTION_SOURCE_ID,
                "curve_ordinal": 10,
                "time_dial": 1.0,
                "current_multiples": [2.0, 10.0],
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["td_section_source_id"] == TD_SECTION_SOURCE_ID
    assert body["meta"]["status"] == "supported"
    assert body["meta"]["selected_curve_ordinal"] == 10
    assert body["curves"][0]["curve_name"] == "NI"
    assert body["curves"][0]["points"][0]["current_multiple"] == 2.0
    assert body["curves"][0]["points"][1]["seconds"] == pytest.approx(2.9705986243944098)


@pytest.mark.parametrize(
    ("method", "path", "json_payload"),
    [
        ("get", "/api/v1/neta/relay/sections", None),
        ("get", f"/api/v1/neta/relay/context/{TD_SECTION_SOURCE_ID}", None),
        ("get", f"/api/v1/neta/relay/settings/{TD_SECTION_SOURCE_ID}", None),
        (
            "post",
            "/api/v1/neta/relay/plot-tcc",
            {
                "td_section_source_id": TD_SECTION_SOURCE_ID,
                "current_multiples": [2.0, 10.0],
            },
        ),
    ],
)
def test_relay_routes_return_503_when_work_schema_tables_are_absent(client, method, path, json_payload):
    with patch("services.neta.router._relay_work_schema_tables_available", return_value=False):
        request_method = getattr(client, method)
        resp = request_method(path, json=json_payload) if json_payload is not None else request_method(path)

    assert resp.status_code == 503
    assert resp.json() == {"detail": "relay catalog unavailable: work-schema tables not present"}


def test_relay_plot_candidate_overrides_are_stateless_route_extension(client):
    baseline_payload = {
        "td_section_source_id": TD_SECTION_SOURCE_ID,
        "curve_parent_source_id": 34480,
        "curve_ordinal": 10,
        "time_dial": 1.0,
        "current_multiples": [2.0, 10.0],
    }

    with patch("services.neta.router._load_relay_settings_bundle", return_value=_relay_settings_bundle()):
        baseline_resp = client.post("/api/v1/neta/relay/plot-tcc", json=baseline_payload)
        candidate_resp = client.post(
            "/api/v1/neta/relay/plot-tcc",
            json={
                **baseline_payload,
                "candidate_overrides": {
                    "pickup_multiplier": 1.25,
                    "time_dial": 1.2,
                    "voltage_threshold_multiplier": 1.0,
                },
            },
        )

    assert baseline_resp.status_code == 200
    assert candidate_resp.status_code == 200
    baseline_body = baseline_resp.json()
    candidate_body = candidate_resp.json()

    assert baseline_body["meta"]["candidate_applied"] is False
    assert candidate_body["meta"]["candidate_applied"] is True
    assert candidate_body["meta"]["candidate_pickup_multiplier"] == pytest.approx(1.25)
    assert candidate_body["meta"]["candidate_time_dial"] == pytest.approx(1.2)
    assert candidate_body["curves"][0]["points"][1]["current_multiple"] == pytest.approx(10.0)
    assert candidate_body["curves"][0]["points"][1]["evaluated_current_multiple"] == pytest.approx(8.0)
    assert candidate_body["curves"][0]["points"][1]["seconds"] != pytest.approx(
        baseline_body["curves"][0]["points"][1]["seconds"]
    )


def test_relay_plot_invalid_candidate_override_returns_validation_error(client):
    resp = client.post(
        "/api/v1/neta/relay/plot-tcc",
        json={
            "td_section_source_id": TD_SECTION_SOURCE_ID,
            "curve_parent_source_id": 34480,
            "curve_ordinal": 10,
            "time_dial": 1.0,
            "current_multiples": [2.0, 10.0],
            "candidate_overrides": {"pickup_multiplier": 0},
        },
    )

    assert resp.status_code == 422


def test_relay_plot_returns_explicit_unsupported_outcome(client):
    with patch("services.neta.router._load_relay_preview_bundle", return_value=_relay_unsupported_preview_bundle()):
        resp = client.post(
            "/api/v1/neta/relay/plot-tcc",
            json={
                "td_section_source_id": TD_SECTION_SOURCE_ID,
                "current_multiples": [2.0, 10.0],
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["status"] == "unsupported"
    assert body["meta"]["supported"] is False
    assert body["meta"]["unsupported_reason"] is not None
    assert body["curves"] == []
    assert body["warnings"] == ["rxd relay family remains explicitly unsupported in Tranche 4."]
