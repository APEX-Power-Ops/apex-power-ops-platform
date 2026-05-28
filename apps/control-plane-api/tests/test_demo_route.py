"""
Smoke test for the demo page route.

Verifies GET /demo/neta-tcc serves the HTML page and that the page source
wires all five expected API paths in the correct workflow order.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def demo_body(client):
    """Fetch the demo page body once for multiple assertions."""
    resp = client.get("/demo/neta-tcc")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    return resp.text


def test_demo_neta_tcc_returns_html(client):
    """GET /demo/neta-tcc should return 200 with an HTML page."""
    resp = client.get("/demo/neta-tcc")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_demo_contains_workflow_sections(demo_body):
    """The page must expose the family selector and bounded family workflows."""
    assert "Family Workflow" in demo_body
    assert "ETU Equipment Match" in demo_body
    assert "TMT Frame Selection" in demo_body
    assert "EMT Frame And Section Selection" in demo_body
    assert "Settings" in demo_body
    assert "Calculated Test Currents" in demo_body
    assert "Evaluation Results" in demo_body
    assert "TCC Overlay Plot" in demo_body
    assert "TMT Nominal Plot" in demo_body
    assert "EMT Raw Point-Data Plot" in demo_body


def test_demo_uses_delay_band_selectors_for_section_two_td_controls(demo_body):
    """STD and GFD settings must use strict band selectors rather than freeform numeric inputs."""
    assert "Short-Time Delay Band (STD)" in demo_body
    assert "Ground-Fault Delay Band (GFD)" in demo_body
    assert '<select id="set-std"></select>' in demo_body
    assert '<select id="set-gfd"></select>' in demo_body
    assert 'input type="number" id="set-std"' not in demo_body
    assert 'input type="number" id="set-gfd"' not in demo_body


def test_demo_uses_equipment_match_labels_for_etu_selection(demo_body):
    """The ETU selection surface must distinguish trip-unit labels and bounded breaker context."""
    assert "Breaker-Half Identity" in demo_body
    assert "etu-step-indicator" in demo_body
    assert "etu-cross-half-advisory" in demo_body
    assert "Breaker Manufacturer" in demo_body
    assert "Breaker Class" in demo_body
    assert "sel-brk-name" in demo_body
    assert "sel-brk-style" in demo_body
    assert "Trip Unit Manufacturer" in demo_body
    assert "Trip Unit Type" in demo_body
    assert "Trip Unit Style" in demo_body
    assert "Sensor / Rating" in demo_body
    assert "Plug Compatibility Lens" in demo_body
    assert "ETU Browse / Search" in demo_body
    assert "etu-browse-results" in demo_body
    assert "Breaker Context:" in demo_body
    assert "getCurrentEtuIdentity" in demo_body


def test_demo_wires_all_five_api_paths(demo_body):
    """The page must reference ETU, TMT, and EMT workflow endpoints."""
    assert "/api/v1/neta/cascade" in demo_body
    assert "/api/v1/neta/etu/breaker-cascade" in demo_body
    assert "/api/v1/neta/etu/search" in demo_body
    assert "/api/v1/neta/settings/" in demo_body
    assert "/api/v1/neta/calculate" in demo_body
    assert "/api/v1/neta/evaluate" in demo_body
    assert "/api/v1/neta/plot-tcc" in demo_body
    assert "/api/v1/neta/tmt/frames" in demo_body
    assert "/api/v1/neta/tmt/context/" in demo_body
    assert "/api/v1/neta/tmt/settings/" in demo_body
    assert "/api/v1/neta/tmt/plot-tcc" in demo_body
    assert "/api/v1/neta/emt/frames" in demo_body
    assert "/api/v1/neta/emt/context/" in demo_body
    assert "/api/v1/neta/emt/settings/" in demo_body
    assert "/api/v1/neta/emt/plot-tcc" in demo_body


def test_demo_evaluate_called_before_plot_tcc(demo_body):
    """The evaluate call must appear before the plot-tcc call in the JS,
    ensuring the two-step workflow: evaluate first, then plot."""
    eval_pos = demo_body.index("/api/v1/neta/evaluate")
    plot_pos = demo_body.index("/api/v1/neta/plot-tcc")
    assert eval_pos < plot_pos, (
        "/evaluate must be called before /plot-tcc in the workflow JS"
    )


def test_demo_loads_plotly(demo_body):
    """Plotly.js must be loaded via CDN."""
    assert "plotly" in demo_body.lower()
    assert "Plotly.newPlot" in demo_body


def test_demo_has_preset_mechanism(demo_body):
    """The page must include a demo scenario loader with at least one preset."""
    assert "DEMO_PRESETS" in demo_body
    assert "Load Demo Scenario" in demo_body
    assert "preset-select" in demo_body
    assert "btn-load-preset" in demo_body


def test_demo_preset_contains_real_sensor(demo_body):
    """The built-in preset must reference a real sensor with cascade IDs
    and complete settings, not placeholder data."""
    # Sensor 25: GE MVT RMS-9 ICCB 800A
    assert "sensor_id: 25" in demo_body
    assert "manufacturer_id: 9" in demo_body
    assert "plug_rating: 800" in demo_body
    assert "ltpu_setting:" in demo_body
    assert "stpu_setting:" in demo_body
    assert "inst_setting:" in demo_body
    assert "gfpu_setting:" in demo_body


def test_demo_preset_bypasses_cascade(demo_body):
    """The preset loader must call loadSettings directly rather than
    requiring manual cascade drill-down."""
    # The preset JS should apply the full ETU selection directly
    assert "applyEtuCascadeSelection(preset.cascade)" in demo_body


# ── MAINT-mode preset tests ──

def test_demo_has_maint_preset(demo_body):
    """The page must include at least two presets: one normal and one MAINT."""
    assert "Normal Mode" in demo_body
    assert "MAINT Mode" in demo_body
    assert "maint_mode: false" in demo_body
    assert "maint_mode: true" in demo_body


def test_demo_maint_preset_uses_real_sensor(demo_body):
    """The MAINT preset must reference a real sensor, not placeholder data."""
    # The MAINT preset reuses sensor 25 with maint_mode: true
    # Verify it has complete settings and measurements including INST measured
    maint_idx = demo_body.index("MAINT Mode")
    after_maint = demo_body[maint_idx:]
    assert "sensor_id: 25" in after_maint
    assert "maint_mode: true" in after_maint
    assert "inst: 7800" in after_maint  # MAINT exercises INST measured


def test_demo_maint_banner_exists(demo_body):
    """A MAINT banner element must exist to show MAINT state before execution."""
    assert "maint-banner" in demo_body
    assert "MAINT MODE ACTIVE" in demo_body


def test_demo_maint_banner_wired_to_checkbox(demo_body):
    """The MAINT banner must toggle with the checkbox, not only on preset load."""
    assert "updateMaintBanner" in demo_body
    assert "chk-maint" in demo_body
    # The checkbox change listener must be wired
    assert "addEventListener('change', updateMaintBanner)" in demo_body


# ── Export report tests ──

def test_demo_has_export_button(demo_body):
    """The page must include an export report button."""
    assert "btn-export" in demo_body
    assert "Export Report" in demo_body


def test_demo_export_builds_report_structure(demo_body):
    """The export builder must construct a report with the required fields:
    scenario, breaker_selection, settings, maint_state, calculate,
    evaluate, plot_tcc, and generated_at."""
    assert "report_version" in demo_body
    assert "generated_at" in demo_body
    assert "resolved_equipment" in demo_body
    assert "breaker_selection" in demo_body
    assert "maint_state" in demo_body
    assert "maint_support_level" in demo_body
    assert "plot_disclaimer" in demo_body
    assert "measurements_provided" in demo_body


def test_demo_export_includes_maint_state(demo_body):
    """The export report must include MAINT mode, capability, support level,
    and disclaimer — not just a checkbox value."""
    # Verify the export captures maint_state from server meta, not form
    export_idx = demo_body.index("btn-export")
    after_export = demo_body[export_idx:]
    assert "meta.maint_mode" in after_export
    assert "meta.maint_capable" in after_export
    assert "meta.maint_support_level" in after_export
    assert "meta.plot_disclaimer" in after_export


def test_demo_formats_maint_support_levels_for_display(demo_body):
    """The page should map API support-level tokens to user-facing labels."""
    assert "formatMaintSupportLevel" in demo_body
    assert "INST/GFPU only" in demo_body
    assert "Full branch data" in demo_body
    assert "No MAINT branch data" in demo_body


def test_demo_export_includes_warnings(demo_body):
    """The export report must preserve warnings from calculate, evaluate,
    and plot_tcc — not drop them between steps."""
    export_idx = demo_body.index("btn-export")
    after_export = demo_body[export_idx:]
    assert "lastCalcResponse.warnings" in after_export
    assert "lastEvalResponse.warnings" in after_export
    assert "lastPlotTccResponse.warnings" in after_export


def test_demo_export_disabled_until_workflow_complete(demo_body):
    """The export button must start disabled and only enable after
    the TCC section renders."""
    assert 'id="btn-export" disabled' in demo_body
    # Enabled inside the View Results handler after plot-tcc returns
    assert "btn-export').disabled = false" in demo_body


def test_demo_export_filename_includes_maint(demo_body):
    """When MAINT mode is active, the export filename must include _MAINT
    so the file is visually distinguishable."""
    assert "_MAINT" in demo_body
    assert "neta-tcc-report_" in demo_body


# ── Data-mode visibility tests ──

def test_demo_has_data_mode_badge(demo_body):
    """The page must include a data-mode status badge for live/fallback indication."""
    assert "data-mode-badge" in demo_body
    assert "data-mode-label" in demo_body


def test_demo_checks_catalog_status(demo_body):
    """The page must call the catalog status endpoint on load."""
    assert "/api/v1/neta/catalog/status" in demo_body
    assert "checkCatalogStatus" in demo_body


def test_demo_has_live_and_fallback_modes(demo_body):
    """The page must handle both live and fallback data modes."""
    assert "data-mode-live" in demo_body
    assert "data-mode-fallback" in demo_body
    assert "catalogMode" in demo_body


def test_demo_fallback_disables_cascade(demo_body):
    """When catalog is unavailable, the cascade should show a clear message."""
    assert "Database unavailable" in demo_body


# ── Plan persistence UI tests ──

def test_demo_has_save_plan_button(demo_body):
    """The page must include an ETU save-plan button."""
    assert 'id="btn-save-plan"' in demo_body
    assert "family: 'etu'" in demo_body

def test_demo_has_save_result_button(demo_body):
    """The page must include a save-result button."""
    assert 'id="btn-save-result"' in demo_body

def test_demo_has_saved_plans_panel(demo_body):
    """The page must include a saved-plans panel for loading."""
    assert 'id="saved-plans-panel"' in demo_body
    assert 'saved-plans-list' in demo_body

def test_demo_has_active_plan_indicator(demo_body):
    """The page must include an active-plan indicator bar."""
    assert 'id="active-plan-bar"' in demo_body
    assert 'active-plan-tag' in demo_body

def test_demo_wires_plan_api_paths(demo_body):
    """The page must call the plan persistence API endpoints."""
    assert '/api/v1/neta/plans' in demo_body
    assert 'loadSavedPlan' in demo_body
    assert 'refreshSavedPlans' in demo_body

def test_demo_save_plan_uses_structured_payload(demo_body):
    """Save plan must send structured settings, not opaque blobs."""
    assert 'currentFamily !== \'etu\'' in demo_body
    assert 'plug_rating' in demo_body
    assert 'maint_mode' in demo_body
    assert 'sensor_id' in demo_body


def test_demo_has_family_tabs_and_description(demo_body):
    """The page must include family tabs and family-mode messaging."""
    assert 'id="family-tabs"' in demo_body
    assert 'data-family="etu"' in demo_body
    assert 'data-family="tmt"' in demo_body
    assert 'data-family="emt"' in demo_body
    assert 'family-mode-note' in demo_body


def test_demo_plan_panel_is_gated_to_etu(demo_body):
    """Saved plans must remain ETU-only in the current bounded contract."""
    assert "currentFamily !== 'etu' || catalogMode !== 'live'" in demo_body
    assert "plan.family || 'etu'" in demo_body
