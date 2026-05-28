"""
Browser-level end-to-end workflow test for the NETA TCC demo page.

Uses Playwright to drive a real browser through the full technician workflow:
  Load page → Load preset → Calculate → View Results on TCC → verify sections

Requires:
  pip install playwright
  playwright install chromium

Skipped automatically when Playwright browsers are not installed, so this
test will not break CI environments that lack browser binaries.

Run locally:
  pytest tests/test_demo_browser.py -v --headed   (to watch the browser)
  pytest tests/test_demo_browser.py -v             (headless)
"""

import socket
import sys
import os
import subprocess
import threading
import time
import json
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

# ── Skip if Playwright, uvicorn, or browser binaries are not available ──
try:
    from playwright.sync_api import sync_playwright, Error as PlaywrightError
    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False

try:
    import uvicorn as _uvicorn_check  # noqa: F401
    _HAS_UVICORN = True
except ImportError:
    _HAS_UVICORN = False

# Check if Chromium binary is actually installed (import ≠ browser available)
_HAS_BROWSER = False
if _HAS_PLAYWRIGHT:
    try:
        _pw = sync_playwright().start()
        _br = _pw.chromium.launch(headless=True)
        _br.close()
        _pw.stop()
        _HAS_BROWSER = True
    except Exception:
        pass

_SKIP_REASON_PARTS = []
if not _HAS_PLAYWRIGHT:
    _SKIP_REASON_PARTS.append("Playwright not installed")
if not _HAS_UVICORN:
    _SKIP_REASON_PARTS.append("uvicorn not installed")
if _HAS_PLAYWRIGHT and not _HAS_BROWSER:
    _SKIP_REASON_PARTS.append("Playwright browser binaries not installed")

pytestmark = pytest.mark.skipif(
    not (_HAS_PLAYWRIGHT and _HAS_UVICORN and _HAS_BROWSER),
    reason=" and ".join(_SKIP_REASON_PARTS) if _SKIP_REASON_PARTS else "",
)


# ── Fixtures ──

def _free_port() -> int:
    """Bind to port 0 and let the OS assign an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server():
    """Start a real uvicorn server on a dynamic port for browser tests.

    Startup failures are raised as errors, not silently skipped —
    a crash here means the app has a real regression.
    """
    uvicorn = pytest.importorskip("uvicorn")
    from main import app

    port = _free_port()
    startup_error: list[Exception] = []

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    srv = uvicorn.Server(config)

    def _run():
        try:
            srv.run()
        except Exception as exc:
            startup_error.append(exc)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    # Wait for server to be ready
    import httpx
    for _ in range(30):
        if startup_error:
            raise startup_error[0]
        try:
            r = httpx.get(f"http://127.0.0.1:{port}/health", timeout=1.0)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.2)
    else:
        pytest.fail(
            f"Server did not start on port {port} within 6 s. "
            "Check for import errors or app startup failures."
        )

    yield f"http://127.0.0.1:{port}"
    srv.should_exit = True


@pytest.fixture(scope="module")
def browser_context():
    """Launch a Playwright browser. Skip if browsers aren't installed."""
    try:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context()
        yield context
        context.close()
        browser.close()
        pw.stop()
    except Exception as e:
        if "Executable doesn't exist" in str(e) or "browserType.launch" in str(e):
            pytest.skip(f"Playwright browsers not installed: {e}")
        raise


@pytest.fixture
def page(browser_context):
    page = browser_context.new_page()
    yield page
    page.close()


def _fulfill_json(route, payload, status=200):
    route.fulfill(
        status=status,
        content_type="application/json",
        body=json.dumps(payload),
    )


def _mock_demo_bootstrap(page, catalog="fallback", manufacturer_count=0, sensor_count=0):
    page.route(
        "**/api/v1/auth/config",
        lambda route: _fulfill_json(
            route,
            {
                "enabled": False,
                "supabase_enabled": False,
                "supabase_url": None,
                "supabase_anon_key": None,
                "email_redirect_to": "http://127.0.0.1/demo/neta-tcc",
                "test_auth": {
                    "enabled": False,
                    "users": [],
                    "storage_key": "neta_test_auth_session",
                },
            },
        ),
    )
    page.route(
        "**/api/v1/neta/catalog/status",
        lambda route: _fulfill_json(
            route,
            {
                "catalog": catalog,
                "manufacturer_count": manufacturer_count,
                "sensor_count": sensor_count,
            },
        ),
    )


def _mock_etu_phase_c_routes(page):
    def cascade_payload(url: str):
        params = parse_qs(urlparse(url).query)
        manufacturer_id = params.get("manufacturer_id", [None])[0]
        trip_type_id = params.get("trip_type_id", [None])[0]
        trip_style_id = params.get("trip_style_id", [None])[0]
        return {
            "level": "sensors" if trip_style_id == "3" else "manufacturers",
            "count": 2,
            "manufacturers": [
                {"manufacturer_id": 9, "manufacturer_name": "GE", "trip_type_count": 1},
            ],
            "trip_types": [
                {
                    "trip_type_id": 75,
                    "trip_type_name": "MVT RMS-9",
                    "manufacturer_id": 9,
                    "manufacturer_name": "GE",
                    "trip_style_count": 1,
                }
            ] if manufacturer_id == "9" or trip_type_id == "75" or trip_style_id == "3" else [],
            "trip_styles": [
                {
                    "trip_style_id": 3,
                    "trip_style_name": "ICCB",
                    "trip_type_id": 75,
                    "trip_type_name": "MVT RMS-9",
                    "manufacturer_id": 9,
                    "manufacturer_name": "GE",
                    "sensor_count": 2,
                }
            ] if trip_type_id == "75" or trip_style_id == "3" else [],
            "plug_values": [
                {"plug_value": 800, "sensor_count": 2},
                {"plug_value": 1200, "sensor_count": 1},
            ] if trip_style_id == "3" or params.get("sensor_id", [None])[0] == "25" else [],
            "sensors": [
                {
                    "sensor_id": 25,
                    "sensor_rating": 800,
                    "sensor_desc": "800",
                    "trip_style_id": 3,
                    "trip_style_name": "ICCB",
                    "trip_type_id": 75,
                    "trip_type_name": "MVT RMS-9",
                    "manufacturer_id": 9,
                    "manufacturer_name": "GE",
                    "has_ltpu": True,
                    "has_stpu": True,
                    "has_inst": True,
                    "has_gfpu": True,
                },
                {
                    "sensor_id": 26,
                    "sensor_rating": 1200,
                    "sensor_desc": "1200",
                    "trip_style_id": 3,
                    "trip_style_name": "ICCB",
                    "trip_type_id": 75,
                    "trip_type_name": "MVT RMS-9",
                    "manufacturer_id": 9,
                    "manufacturer_name": "GE",
                    "has_ltpu": True,
                    "has_stpu": True,
                    "has_inst": True,
                    "has_gfpu": True,
                },
            ] if trip_style_id == "3" else [],
        }

    def breaker_cascade_payload(url: str):
        params = parse_qs(urlparse(url).query)
        manufacturer_id = params.get("manufacturer_id", [None])[0]
        breaker_id = params.get("breaker_id", [None])[0]
        return {
            "count": 1,
            "manufacturers": [
                {"manufacturer_id": 9, "manufacturer_name": "GE", "breaker_count": 1},
            ],
            "breaker_classes": [
                {"breaker_class": "ICCB", "breaker_count": 1},
            ],
            "breakers": [
                {"breaker_id": 501, "breaker_name": "AKR-9", "manufacturer_name": "GE", "style_count": 1},
            ] if manufacturer_id == "9" else [],
            "breaker_styles": [
                {"breaker_style_id": 701, "breaker_style_name": "Compartment Switch"},
            ] if breaker_id == "501" else [],
        }

    def etu_search_payload(url: str):
        params = parse_qs(urlparse(url).query)
        plug_value = params.get("plug_value", [None])[0]
        all_results = [
            {
                "sensor_id": 25,
                "sensor_rating": 800,
                "sensor_desc": "800",
                "trip_style_id": 3,
                "trip_style_name": "ICCB",
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "compatible_plug_values": [800.0],
            },
            {
                "sensor_id": 26,
                "sensor_rating": 1200,
                "sensor_desc": "1200",
                "trip_style_id": 3,
                "trip_style_name": "ICCB",
                "trip_type_id": 75,
                "trip_type_name": "MVT RMS-9",
                "manufacturer_id": 9,
                "manufacturer_name": "GE",
                "compatible_plug_values": [800.0, 1200.0],
            },
        ]
        results = [all_results[1]] if plug_value == "1200" else all_results
        return {
            "count": len(results),
            "results": results,
        }

    page.route(
        "**/api/v1/neta/cascade*",
        lambda route: _fulfill_json(route, cascade_payload(route.request.url)),
    )
    page.route(
        "**/api/v1/neta/etu/breaker-cascade*",
        lambda route: _fulfill_json(route, breaker_cascade_payload(route.request.url)),
    )
    page.route(
        "**/api/v1/neta/settings/25",
        lambda route: _fulfill_json(
            route,
            {
                "plug_values": [800, 1200],
                "ltpu_settings": [0.8, 1.0],
                "ltd_settings": [{"label": "6x", "open_time": 0.5, "band": "6x"}],
                "stpu_settings": [4.0],
                "std_settings": [{"label": "I2T", "open_time": 0.21, "band": "I2T"}],
                "inst_settings": [8.0, 10.0],
                "gfpu_settings": [0.2, 0.4],
                "gfd_settings": [{"label": "I2T", "open_time": 0.21, "band": "I2T"}],
            },
        ),
    )
    page.route(
        "**/api/v1/neta/context/25",
        lambda route: _fulfill_json(
            route,
            {
                "sensor_id": 25,
                "sensor_desc": "800",
                "rating": 800,
                "has_ltpu": True,
                "has_stpu": True,
                "has_inst": True,
                "has_gfpu": True,
                "maint_capable": True,
                "resolved_equipment": {
                    "family": "etu",
                    "family_label": "ETU",
                    "resolved_id": "sensor:25",
                    "primary_label": "GE MVT RMS-9",
                    "secondary_label": "ICCB · 800A",
                    "breaker_context": {
                        "label": "ICCB · 800A",
                        "source": "trip_style_sensor_rating",
                        "manufacturer_name": "GE",
                        "breaker_class": "ICCB",
                        "breaker_name": None,
                        "breaker_style_name": "ICCB",
                    },
                    "trip_unit": {
                        "manufacturer_name": "GE",
                        "trip_type_name": "MVT RMS-9",
                        "trip_style_name": "ICCB",
                        "label": "GE MVT RMS-9 ICCB",
                    },
                    "rating_context": {
                        "label": "Sensor 800",
                        "sensor_id": 25,
                        "sensor_desc": "800",
                        "sensor_rating": 800,
                    },
                },
            },
        ),
    )
    page.route(
        "**/api/v1/neta/etu/search*",
        lambda route: _fulfill_json(route, etu_search_payload(route.request.url)),
    )


# ── Tests ──

class TestDemoBrowserWorkflow:
    """Full browser-level workflow: preset → calculate → evaluate → TCC plot."""

    def test_full_workflow_with_preset(self, server, page):
        """A presenter can load the demo scenario and complete the full
        calculate → evaluate → plot-tcc workflow in the browser."""

        # Step 1: Load the page
        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")

        # Verify the page loaded
        assert "NETA ETT" in page.title()

        # Verify preset selector is visible
        preset_select = page.locator("#preset-select")
        assert preset_select.is_visible()

        # Step 2: Select and load the demo preset
        preset_select.select_option(index=1)  # first preset
        load_btn = page.locator("#btn-load-preset")
        assert load_btn.is_enabled()
        load_btn.click()

        # Wait for settings to load (settings section becomes visible)
        page.locator("#settings-section").wait_for(state="visible", timeout=10000)

        # Verify plug rating was populated
        plug_val = page.locator("#set-plug").input_value()
        assert plug_val == "800"

        # Verify measured values were populated
        ltpu_meas = page.locator("#meas-ltpu").input_value()
        assert ltpu_meas == "650"

        # Step 3: Click Calculate
        calc_btn = page.locator("#btn-calc")
        assert calc_btn.is_enabled()
        calc_btn.click()

        # Wait for calc results to appear
        page.locator("#calc-section").wait_for(state="visible", timeout=10000)

        # Verify calc table has rows
        calc_rows = page.locator("#calc-table tbody tr")
        assert calc_rows.count() > 0, "Calculate should produce element rows"

        # Step 4: Click View Results on TCC
        tcc_btn = page.locator("#btn-tcc")
        assert tcc_btn.is_enabled()
        tcc_btn.click()

        # Wait for evaluate section first (two-step flow)
        page.locator("#eval-section").wait_for(state="visible", timeout=15000)

        # Verify evaluate results rendered
        eval_rows = page.locator("#eval-table tbody tr")
        assert eval_rows.count() > 0, "Evaluate should produce element rows"

        # Verify overall pass/fail tag is present
        eval_meta = page.locator("#eval-meta").inner_text()
        assert "PASS" in eval_meta or "FAIL" in eval_meta

        # Verify TCC plot section appeared
        page.locator("#tcc-section").wait_for(state="visible", timeout=15000)

        # Verify Plotly rendered something in the plot container
        plot_traces = page.locator("#tcc-plot .plot-container")
        assert plot_traces.count() > 0, "Plotly should render a plot container"

        # Verify summary table has rows
        tcc_rows = page.locator("#tcc-table tbody tr")
        assert tcc_rows.count() > 0, "TCC summary table should have rows"

        # Verify warnings container exists even when it has no rendered content
        assert page.locator("#tcc-warnings").count() == 1

    def test_preset_populates_cascade_dropdowns(self, server, page):
        """After loading a preset, cascade dropdowns should show the
        selected values without requiring manual drill-down."""
        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")

        page.locator("#preset-select").select_option(index=1)
        page.locator("#btn-load-preset").click()
        page.locator("#settings-section").wait_for(state="visible", timeout=10000)

        # Cascade dropdowns should show preset values
        mfr_text = page.locator("#sel-mfr option:checked").inner_text()
        assert "GE" in mfr_text

        type_text = page.locator("#sel-type option:checked").inner_text()
        assert "MVT RMS-9" in type_text

        sensor_text = page.locator("#sel-sensor option:checked").inner_text()
        assert "800" in sensor_text

    def test_no_measurements_skips_eval_section(self, server, page):
        """When no measured values are entered, View Results on TCC should
        skip the evaluate section and go straight to the plot."""
        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")

        # Load preset then clear measured values
        page.locator("#preset-select").select_option(index=1)
        page.locator("#btn-load-preset").click()
        page.locator("#settings-section").wait_for(state="visible", timeout=10000)

        # Clear all measured inputs
        page.locator("#meas-ltpu").fill("")
        page.locator("#meas-stpu").fill("")
        page.locator("#meas-inst").fill("")
        page.locator("#meas-gfpu").fill("")

        # Click View Results on TCC
        page.locator("#btn-tcc").click()

        # TCC section should appear
        page.locator("#tcc-section").wait_for(state="visible", timeout=15000)

        # Eval section should stay hidden
        assert not page.locator("#eval-section").is_visible()

        # Meta should show "No eval"
        meta_text = page.locator("#tcc-meta").inner_text()
        assert "No eval" in meta_text

    def test_maint_preset_full_workflow(self, server, page):
        """Loading the MAINT preset should show the MAINT banner before
        execution, then produce MAINT-specific metadata in calc, eval,
        and TCC sections after the workflow completes."""

        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")

        # Step 1: MAINT banner should be hidden initially
        assert not page.locator("#maint-banner").is_visible()

        # Step 2: Select and load the MAINT preset (index=2, second preset)
        page.locator("#preset-select").select_option(index=2)
        page.locator("#btn-load-preset").click()
        page.locator("#settings-section").wait_for(state="visible", timeout=10000)

        # Step 3: Verify MAINT state is visible BEFORE execution
        assert page.locator("#chk-maint").is_checked(), \
            "MAINT checkbox must be checked after loading MAINT preset"
        assert page.locator("#maint-banner").is_visible(), \
            "MAINT banner must be visible after loading MAINT preset"
        banner_text = page.locator("#maint-banner").inner_text()
        assert "MAINT MODE ACTIVE" in banner_text

        # Verify INST measured value was populated (MAINT exercises INST path)
        inst_val = page.locator("#meas-inst").input_value()
        assert inst_val == "7800"

        # Step 4: Click Calculate
        page.locator("#btn-calc").click()
        page.locator("#calc-section").wait_for(state="visible", timeout=10000)

        # Verify calc meta shows MAINT badge
        calc_meta = page.locator("#calc-meta").inner_text()
        assert "MAINT" in calc_meta, \
            "Calculate meta should show MAINT badge"

        # Step 5: Click View Results on TCC
        page.locator("#btn-tcc").click()

        # Wait for evaluate section (has measurements, so evaluate runs)
        page.locator("#eval-section").wait_for(state="visible", timeout=15000)

        # Verify eval meta shows MAINT badge
        eval_meta = page.locator("#eval-meta").inner_text()
        assert "MAINT" in eval_meta, \
            "Evaluate meta should show MAINT badge"

        # Wait for TCC section
        page.locator("#tcc-section").wait_for(state="visible", timeout=15000)

        # Verify TCC meta shows MAINT badge
        tcc_meta = page.locator("#tcc-meta").inner_text()
        assert "MAINT" in tcc_meta, \
            "TCC meta should show MAINT badge"

        # Verify the disclaimer, when emitted, is MAINT-specific
        disclaimer = page.locator("#tcc-disclaimer").inner_text()
        if disclaimer.strip():
            assert "maint" in disclaimer.lower() or "maintenance" in disclaimer.lower(), \
            "TCC disclaimer should mention maint when present"

        # Verify plot rendered
        plot_traces = page.locator("#tcc-plot .plot-container")
        assert plot_traces.count() > 0, "Plotly should render a plot container"

    def test_export_button_enabled_after_workflow(self, server, page):
        """The Export Report button must be disabled initially and
        enabled only after the full workflow completes."""
        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")

        # Export button should be disabled initially
        assert page.locator("#btn-export").is_disabled()

        # Load normal preset and run workflow
        page.locator("#preset-select").select_option(index=1)
        page.locator("#btn-load-preset").click()
        page.locator("#settings-section").wait_for(state="visible", timeout=10000)

        # Still disabled before View Results
        assert page.locator("#btn-export").is_disabled()

        # Click View Results on TCC
        page.locator("#btn-tcc").click()
        page.locator("#tcc-section").wait_for(state="visible", timeout=15000)

        # Now export should be enabled
        assert page.locator("#btn-export").is_enabled(), \
            "Export button must be enabled after TCC renders"

    def test_export_produces_json_download(self, server, page):
        """Clicking Export Report after a completed workflow should
        trigger a JSON file download with the expected report structure."""
        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")

        # Load preset and run full workflow
        page.locator("#preset-select").select_option(index=1)
        page.locator("#btn-load-preset").click()
        page.locator("#settings-section").wait_for(state="visible", timeout=10000)
        page.locator("#btn-tcc").click()
        page.locator("#tcc-section").wait_for(state="visible", timeout=15000)

        # Intercept the download
        with page.expect_download() as download_info:
            page.locator("#btn-export").click()

        download = download_info.value
        assert "neta-tcc-report_" in download.suggested_filename
        assert download.suggested_filename.endswith(".json")

        # Read and validate the report content
        import json
        content = json.loads(download.path().read_text())

        assert "report_version" in content
        assert "generated_at" in content
        assert "scenario" in content
        assert "breaker_selection" in content
        assert "settings" in content
        assert "maint_state" in content
        assert "plot_tcc" in content

        # Normal preset — maint_mode should be false in settings
        assert content["settings"]["maint_mode"] is False

    def test_maint_export_includes_maint_state(self, server, page):
        """MAINT preset export must include maint_mode=true in both
        settings and maint_state, and include warnings."""
        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")

        # Load MAINT preset (index=2)
        page.locator("#preset-select").select_option(index=2)
        page.locator("#btn-load-preset").click()
        page.locator("#settings-section").wait_for(state="visible", timeout=10000)
        page.locator("#btn-tcc").click()
        page.locator("#tcc-section").wait_for(state="visible", timeout=15000)

        # Intercept the download
        with page.expect_download() as download_info:
            page.locator("#btn-export").click()

        download = download_info.value
        assert "_MAINT" in download.suggested_filename, \
            "MAINT export filename must include _MAINT"

        import json
        content = json.loads(download.path().read_text())

        assert content["settings"]["maint_mode"] is True
        assert content["maint_state"]["maint_mode"] is True

    def test_data_mode_badge_visible(self, server, page):
        """The data-mode status badge must appear after page load,
        indicating either LIVE or FALLBACK mode."""
        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")

        badge = page.locator("#data-mode-badge")
        assert badge.is_visible(), "Data-mode badge must be visible"

        label = page.locator("#data-mode-label").inner_text()
        # Should show either LIVE or FALLBACK — not still "Checking..."
        assert "LIVE" in label or "FALLBACK" in label, \
            f"Data-mode label should resolve to LIVE or FALLBACK, got: {label}"

    def test_save_plan_button_exists(self, server, page):
        """The save-plan button must be present and initially disabled."""
        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")
        btn = page.locator("#btn-save-plan")
        assert btn.count() == 1, "Save Plan button must exist"
        assert btn.is_disabled(), "Save Plan button should be disabled before settings load"

    def test_saved_plans_panel_visibility(self, server, page):
        """Saved plans visibility should follow live mode and current auth state."""
        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")
        panel = page.locator("#saved-plans-panel")
        label = page.locator("#data-mode-label").inner_text()
        if "LIVE" in label:
            auth_test_user = page.locator("#auth-test-user")
            auth_status = page.locator("#auth-status-banner").inner_text().lower()
            if auth_test_user.count() and auth_test_user.is_visible():
                assert not panel.is_visible(), "Saved plans panel should stay hidden until sign-in"
                auth_test_user.select_option("neta-test-a@example.com")
                page.locator("#btn-test-sign-in").click()
                page.wait_for_function(
                    "() => !document.querySelector('#saved-plans-panel')?.classList.contains('hidden')",
                    timeout=10000,
                )
                assert panel.is_visible(), "Saved plans panel should be visible after local test sign-in"
            elif "signed in as" in auth_status:
                assert panel.is_visible(), "Saved plans panel should be visible for authenticated sessions"
            else:
                assert not panel.is_visible(), "Saved plans panel should stay hidden until auth is satisfied"
        else:
            assert not panel.is_visible(), "Saved plans panel should be hidden in FALLBACK mode"

    def test_saved_plan_restore_revalidates_live_etU_cascade_and_skips_stale_values(self, server, page):
        """Saved ETU plans must re-enter through the live cascade and keep unsupported
        stored values from leaking back into the active UI when current capability has narrowed."""
        _mock_demo_bootstrap(page, catalog="live", manufacturer_count=1, sensor_count=1)

        resolved_equipment = {
            "family": "etu",
            "family_label": "ETU",
            "resolved_id": "sensor:26",
            "primary_label": "GE MVT RMS-9 ICCB",
            "secondary_label": "ICCB · 1200A",
            "breaker_context": {
                "label": "ICCB · 1200A",
                "source": "trip_style_sensor_rating",
                "manufacturer_name": "GE",
                "breaker_style_name": "ICCB",
            },
            "trip_unit": {
                "manufacturer_name": "GE",
                "trip_type_name": "MVT RMS-9",
                "trip_style_name": "ICCB",
                "label": "GE MVT RMS-9 ICCB",
            },
            "rating_context": {
                "label": "Sensor 1200",
                "sensor_id": 26,
                "sensor_desc": "1200",
                "sensor_rating": 1200.0,
                "amp_ratings": [],
            },
        }

        def cascade_payload(url: str):
            params = parse_qs(urlparse(url).query)
            manufacturer_id = params.get("manufacturer_id", [None])[0]
            trip_type_id = params.get("trip_type_id", [None])[0]
            trip_style_id = params.get("trip_style_id", [None])[0]
            return {
                "level": "trip_styles" if trip_style_id == "3" else "manufacturers",
                "count": 1,
                "manufacturers": [
                    {"manufacturer_id": 9, "manufacturer_name": "GE", "trip_type_count": 1},
                ],
                "trip_types": [
                    {
                        "trip_type_id": 75,
                        "trip_type_name": "MVT RMS-9",
                        "manufacturer_id": 9,
                        "manufacturer_name": "GE",
                        "trip_style_count": 1,
                    }
                ] if manufacturer_id == "9" else [],
                "trip_styles": [
                    {
                        "trip_style_id": 3,
                        "trip_style_name": "ICCB",
                        "trip_type_id": 75,
                        "trip_type_name": "MVT RMS-9",
                        "manufacturer_id": 9,
                        "manufacturer_name": "GE",
                        "sensor_count": 1,
                    }
                ] if trip_type_id == "75" else [],
                "sensors": [
                    {
                        "sensor_id": 26,
                        "sensor_rating": 1200,
                        "sensor_desc": "1200",
                        "trip_style_id": 3,
                        "trip_style_name": "ICCB",
                        "trip_type_id": 75,
                        "trip_type_name": "MVT RMS-9",
                        "manufacturer_id": 9,
                        "manufacturer_name": "GE",
                        "has_ltpu": True,
                        "has_stpu": False,
                        "has_inst": False,
                        "has_gfpu": False,
                    }
                ] if trip_style_id == "3" else [],
            }

        page.route(
            "**/api/v1/neta/cascade*",
            lambda route: _fulfill_json(route, cascade_payload(route.request.url)),
        )
        page.route(
            "**/api/v1/neta/context/26",
            lambda route: _fulfill_json(
                route,
                {
                    "sensor_id": 26,
                    "sensor_desc": "1200",
                    "rating": 1200,
                    "has_ltpu": True,
                    "has_stpu": False,
                    "has_inst": False,
                    "has_gfpu": False,
                    "maint_capable": False,
                    "resolved_equipment": resolved_equipment,
                },
            ),
        )
        page.route(
            "**/api/v1/neta/settings/26",
            lambda route: _fulfill_json(
                route,
                {
                    "sensor_id": 26,
                    "plug_values": [1200],
                    "ltpu_settings": [1.0],
                    "ltd_settings": [{"band": "C-3", "label": "C-3", "open_time": 12.0, "is_default": True}],
                    "std_settings": [],
                    "gfd_settings": [],
                    "ltd_multipliers": [],
                    "stpu_settings": [],
                    "inst_settings": [],
                    "gfpu_settings": [],
                },
            ),
        )
        page.route(
            "**/api/v1/neta/plans",
            lambda route: _fulfill_json(
                route,
                [
                    {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "family": "etu",
                        "name": "Restore Sensor 26",
                        "sensor_id": 26,
                        "cascade_state": {
                            "family": "etu",
                            "manufacturer_id": 9,
                            "trip_type_id": 75,
                            "trip_style_id": 3,
                            "sensor_id": 26,
                            "resolved_id": "sensor:26",
                        },
                        "breaker_context_label": "ICCB · 1200A",
                        "sensor_desc": "1200",
                        "resolved_equipment": resolved_equipment,
                        "maint_mode": True,
                        "created_at": "2026-03-24T12:00:00",
                        "updated_at": None,
                    }
                ],
            ),
        )
        page.route(
            "**/api/v1/neta/plans/11111111-1111-1111-1111-111111111111",
            lambda route: _fulfill_json(
                route,
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "family": "etu",
                    "name": "Restore Sensor 26",
                    "sensor_id": 26,
                    "cascade_state": {
                        "family": "etu",
                        "manufacturer_id": 9,
                        "trip_type_id": 75,
                        "trip_style_id": 3,
                        "sensor_id": 26,
                        "resolved_id": "sensor:26",
                    },
                    "manufacturer_id": 9,
                    "manufacturer_name": "GE",
                    "trip_type_id": 75,
                    "trip_type_name": "MVT RMS-9",
                    "trip_style_id": 3,
                    "trip_style_name": "ICCB",
                    "breaker_context_label": "ICCB · 1200A",
                    "breaker_context_source": "trip_style_sensor_rating",
                    "sensor_desc": "1200",
                    "resolved_equipment": resolved_equipment,
                    "settings": {
                        "plug_rating": 1200,
                        "ltpu_setting": 1.0,
                        "ltd_setting": 12.0,
                        "stpu_setting": 4.0,
                        "std_setting": 0.21,
                        "inst_setting": 10.0,
                        "gfpu_setting": 0.4,
                        "gfd_setting": 0.21,
                        "maint_mode": True,
                    },
                    "measurements": {
                        "ltpu": 980.0,
                        "ltd": 3.2,
                        "stpu": 3100.0,
                        "std": 0.42,
                        "inst": 7800.0,
                        "gfpu": 310.0,
                        "gfd": 0.18,
                    },
                    "result_count": 0,
                    "created_at": "2026-03-24T12:00:00",
                    "updated_at": None,
                },
            ),
        )

        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")
        page.locator("#saved-plans-list .saved-plan-item button").click()
        page.locator("#active-plan-bar").wait_for(state="visible", timeout=10000)

        assert page.locator("#sel-mfr").input_value() == "9"
        assert page.locator("#sel-type").input_value() == "75"
        assert page.locator("#sel-style").input_value() == "3"
        assert page.locator("#sel-sensor").input_value() == "26"
        assert page.locator("#sensor-summary").is_visible()
        assert page.locator("#active-plan-tag").inner_text() == "Restore Sensor 26"
        assert page.locator("#save-plan-name").input_value() == "Restore Sensor 26"
        assert not page.locator("#etu-row-stpu").is_visible()
        assert not page.locator("#etu-row-gfpu").is_visible()
        assert not page.locator("#etu-row-maint-toggle").is_visible()
        assert page.locator("#meas-stpu").input_value() == ""
        assert page.locator("#meas-gfpu").input_value() == ""
        assert "were skipped" in page.locator("#saved-plan-status").inner_text()

    def test_saved_plan_restore_surfaces_stale_sensor_path_without_fake_success(self, server, page):
        """If the live ETU catalog no longer supports the saved sensor, restore should
        stop at the highest valid cascade level and report the mismatch honestly."""
        _mock_demo_bootstrap(page, catalog="live", manufacturer_count=1, sensor_count=0)

        def cascade_payload(url: str):
            params = parse_qs(urlparse(url).query)
            manufacturer_id = params.get("manufacturer_id", [None])[0]
            trip_type_id = params.get("trip_type_id", [None])[0]
            trip_style_id = params.get("trip_style_id", [None])[0]
            return {
                "level": "trip_styles" if trip_style_id == "3" else "manufacturers",
                "count": 1,
                "manufacturers": [
                    {"manufacturer_id": 9, "manufacturer_name": "GE", "trip_type_count": 1},
                ],
                "trip_types": [
                    {
                        "trip_type_id": 75,
                        "trip_type_name": "MVT RMS-9",
                        "manufacturer_id": 9,
                        "manufacturer_name": "GE",
                        "trip_style_count": 1,
                    }
                ] if manufacturer_id == "9" else [],
                "trip_styles": [
                    {
                        "trip_style_id": 3,
                        "trip_style_name": "ICCB",
                        "trip_type_id": 75,
                        "trip_type_name": "MVT RMS-9",
                        "manufacturer_id": 9,
                        "manufacturer_name": "GE",
                        "sensor_count": 0,
                    }
                ] if trip_type_id == "75" else [],
                "sensors": [] if trip_style_id == "3" else [],
            }

        page.route(
            "**/api/v1/neta/cascade*",
            lambda route: _fulfill_json(route, cascade_payload(route.request.url)),
        )
        page.route(
            "**/api/v1/neta/plans",
            lambda route: _fulfill_json(
                route,
                [
                    {
                        "id": "22222222-2222-2222-2222-222222222222",
                        "family": "etu",
                        "name": "Stale Sensor 25",
                        "sensor_id": 25,
                        "cascade_state": {
                            "family": "etu",
                            "manufacturer_id": 9,
                            "trip_type_id": 75,
                            "trip_style_id": 3,
                            "sensor_id": 25,
                            "resolved_id": "sensor:25",
                        },
                        "breaker_context_label": "ICCB · 800A",
                        "sensor_desc": "800",
                        "resolved_equipment": {
                            "family": "etu",
                            "family_label": "ETU",
                            "resolved_id": "sensor:25",
                            "primary_label": "GE MVT RMS-9 ICCB",
                            "secondary_label": "ICCB · 800A",
                        },
                        "maint_mode": False,
                        "created_at": "2026-03-24T12:00:00",
                        "updated_at": None,
                    }
                ],
            ),
        )
        page.route(
            "**/api/v1/neta/plans/22222222-2222-2222-2222-222222222222",
            lambda route: _fulfill_json(
                route,
                {
                    "id": "22222222-2222-2222-2222-222222222222",
                    "family": "etu",
                    "name": "Stale Sensor 25",
                    "sensor_id": 25,
                    "cascade_state": {
                        "family": "etu",
                        "manufacturer_id": 9,
                        "trip_type_id": 75,
                        "trip_style_id": 3,
                        "sensor_id": 25,
                        "resolved_id": "sensor:25",
                    },
                    "manufacturer_id": 9,
                    "manufacturer_name": "GE",
                    "trip_type_id": 75,
                    "trip_type_name": "MVT RMS-9",
                    "trip_style_id": 3,
                    "trip_style_name": "ICCB",
                    "breaker_context_label": "ICCB · 800A",
                    "breaker_context_source": "trip_style_sensor_rating",
                    "sensor_desc": "800",
                    "resolved_equipment": {
                        "family": "etu",
                        "family_label": "ETU",
                        "resolved_id": "sensor:25",
                        "primary_label": "GE MVT RMS-9 ICCB",
                        "secondary_label": "ICCB · 800A",
                    },
                    "settings": {
                        "plug_rating": 800,
                        "ltpu_setting": 0.8,
                        "ltd_setting": 6.0,
                        "stpu_setting": 4.0,
                        "std_setting": 0.21,
                        "inst_setting": 10.0,
                        "gfpu_setting": 0.4,
                        "gfd_setting": 0.21,
                        "maint_mode": False,
                    },
                    "measurements": {
                        "ltpu": 650.0,
                        "stpu": 3100.0,
                    },
                    "result_count": 0,
                    "created_at": "2026-03-24T12:00:00",
                    "updated_at": None,
                },
            ),
        )

        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")
        page.locator("#saved-plans-list .saved-plan-item button").click()
        page.wait_for_function(
            "() => document.querySelector('#saved-plan-status')?.textContent.includes('could not be fully revalidated')",
            timeout=10000,
        )

        assert page.locator("#sel-mfr").input_value() == "9"
        assert page.locator("#sel-type").input_value() == "75"
        assert page.locator("#sel-style").input_value() == "3"
        assert page.locator("#sel-sensor").input_value() == ""
        assert not page.locator("#settings-section").is_visible()
        assert not page.locator("#sensor-summary").is_visible()
        assert not page.locator("#active-plan-bar").is_visible()
        assert "could not be fully revalidated" in page.locator("#saved-plan-status").inner_text()

    def test_etu_sensor_change_hides_non_applicable_rows_and_clears_stale_values(self, server, page):
        """Changing ETU sensors should trim the settings and measured rows down to
        the newly resolved device capability instead of keeping stale ETU-only values alive."""
        _mock_demo_bootstrap(page)
        page.route(
            "**/api/v1/neta/catalog/status",
            lambda route: _fulfill_json(
                route,
                {
                    "catalog": "live",
                    "manufacturer_count": 1,
                    "sensor_count": 2,
                },
            ),
        )

        sensor_25 = {
            "sensor_id": 25,
            "sensor_rating": 800,
            "sensor_desc": "800",
            "trip_style_id": 3,
            "trip_style_name": "ICCB",
            "trip_type_id": 75,
            "trip_type_name": "MVT RMS-9",
            "manufacturer_id": 9,
            "manufacturer_name": "GE",
            "has_ltpu": True,
            "has_stpu": True,
            "has_inst": True,
            "has_gfpu": True,
        }
        sensor_26 = {
            "sensor_id": 26,
            "sensor_rating": 1200,
            "sensor_desc": "1200",
            "trip_style_id": 3,
            "trip_style_name": "ICCB",
            "trip_type_id": 75,
            "trip_type_name": "MVT RMS-9",
            "manufacturer_id": 9,
            "manufacturer_name": "GE",
            "has_ltpu": True,
            "has_stpu": False,
            "has_inst": False,
            "has_gfpu": False,
        }

        def cascade_payload(url: str):
            params = parse_qs(urlparse(url).query)
            manufacturer_id = params.get("manufacturer_id", [None])[0]
            trip_type_id = params.get("trip_type_id", [None])[0]
            trip_style_id = params.get("trip_style_id", [None])[0]
            sensors = [sensor_25, sensor_26] if trip_style_id == "3" else []
            return {
                "level": "trip_styles" if trip_style_id == "3" else "manufacturers",
                "count": len(sensors) or 2,
                "manufacturers": [
                    {"manufacturer_id": 9, "manufacturer_name": "GE", "trip_type_count": 1},
                ],
                "trip_types": [
                    {
                        "trip_type_id": 75,
                        "trip_type_name": "MVT RMS-9",
                        "manufacturer_id": 9,
                        "manufacturer_name": "GE",
                        "trip_style_count": 1,
                    }
                ] if manufacturer_id == "9" else [],
                "trip_styles": [
                    {
                        "trip_style_id": 3,
                        "trip_style_name": "ICCB",
                        "trip_type_id": 75,
                        "trip_type_name": "MVT RMS-9",
                        "manufacturer_id": 9,
                        "manufacturer_name": "GE",
                        "sensor_count": 2,
                    }
                ] if trip_type_id == "75" else [],
                "sensors": sensors,
            }

        page.route(
            "**/api/v1/neta/cascade*",
            lambda route: _fulfill_json(route, cascade_payload(route.request.url)),
        )
        page.route(
            "**/api/v1/neta/context/25",
            lambda route: _fulfill_json(
                route,
                {
                    "sensor_id": 25,
                    "sensor_desc": "800",
                    "rating": 800,
                    "has_ltpu": True,
                    "has_stpu": True,
                    "has_inst": True,
                    "has_gfpu": True,
                    "maint_capable": True,
                    "resolved_equipment": {
                        "family": "etu",
                        "family_label": "ETU",
                        "resolved_id": "sensor:25",
                        "primary_label": "GE · MVT RMS-9",
                        "secondary_label": "ICCB · Sensor 800",
                    },
                },
            ),
        )
        page.route(
            "**/api/v1/neta/context/26",
            lambda route: _fulfill_json(
                route,
                {
                    "sensor_id": 26,
                    "sensor_desc": "1200",
                    "rating": 1200,
                    "has_ltpu": True,
                    "has_stpu": False,
                    "has_inst": False,
                    "has_gfpu": False,
                    "maint_capable": False,
                    "resolved_equipment": {
                        "family": "etu",
                        "family_label": "ETU",
                        "resolved_id": "sensor:26",
                        "primary_label": "GE · MVT RMS-9",
                        "secondary_label": "ICCB · Sensor 1200",
                    },
                },
            ),
        )
        page.route(
            "**/api/v1/neta/settings/25",
            lambda route: _fulfill_json(
                route,
                {
                    "plug_values": [800],
                    "ltpu_settings": [0.8],
                    "ltd_settings": [{"band": "C-2", "label": "C-2", "open_time": 6.0, "is_default": True}],
                    "stpu_settings": [4.0],
                    "std_settings": [{"band": "I2T Min", "label": "Min", "open_time": 0.21, "is_default": True}],
                    "inst_settings": [10.0],
                    "gfpu_settings": [0.4],
                    "gfd_settings": [{"band": "GF Min", "label": "Min", "open_time": 0.21, "is_default": True}],
                },
            ),
        )
        page.route(
            "**/api/v1/neta/settings/26",
            lambda route: _fulfill_json(
                route,
                {
                    "plug_values": [1200],
                    "ltpu_settings": [1.0],
                    "ltd_settings": [{"band": "C-3", "label": "C-3", "open_time": 12.0, "is_default": True}],
                    "stpu_settings": [],
                    "std_settings": [],
                    "inst_settings": [],
                    "gfpu_settings": [],
                    "gfd_settings": [],
                },
            ),
        )

        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")
        page.wait_for_function(
            "() => !document.querySelector('#sel-mfr')?.disabled",
            timeout=10000,
        )

        page.locator("#sel-mfr").select_option("9")
        page.wait_for_function(
            "() => document.querySelector('#sel-type option[value=\"75\"]') !== null",
            timeout=10000,
        )
        page.locator("#sel-type").select_option("75")
        page.wait_for_function(
            "() => document.querySelector('#sel-style option[value=\"3\"]') !== null",
            timeout=10000,
        )
        page.locator("#sel-style").select_option("3")
        page.wait_for_function(
            "() => document.querySelector('#sel-sensor option[value=\"25\"]') !== null",
            timeout=10000,
        )
        page.locator("#sel-sensor").select_option("25")
        page.locator("#settings-section").wait_for(state="visible", timeout=10000)

        assert page.locator("#etu-row-gfpu").is_visible()
        assert page.locator("#etu-row-gfd").is_visible()
        assert page.locator("#etu-row-maint-toggle").is_visible()

        page.locator("#set-gfpu").select_option("0.4")
        page.locator("#meas-gfpu").fill("310")
        page.locator("#chk-maint").check()

        page.locator("#sel-sensor").select_option("26")
        page.wait_for_function(
            "() => document.querySelector('#etu-row-gfpu')?.classList.contains('hidden')",
            timeout=10000,
        )

        assert page.locator("#sensor-summary").is_visible()
        assert not page.locator("#etu-row-stpu").is_visible()
        assert not page.locator("#etu-row-inst").is_visible()
        assert not page.locator("#etu-row-gfpu").is_visible()
        assert not page.locator("#etu-row-gfd").is_visible()
        assert not page.locator("#etu-row-meas-gfpu").is_visible()
        assert not page.locator("#etu-row-maint-toggle").is_visible()
        assert page.locator("#set-gfpu").input_value() == ""
        assert page.locator("#meas-gfpu").input_value() == ""
        assert not page.locator("#chk-maint").is_checked()
        assert page.locator("#etu-row-ltpu").is_visible()
        assert page.locator("#etu-row-ltd").is_visible()

    def test_etu_upstream_sensor_change_clears_stale_execution_sections(self, server, page):
        """Changing the resolved ETU sensor after execution should clear stale
        calculate, evaluate, and TCC results instead of leaving the old branch visible."""
        _mock_demo_bootstrap(page, catalog="live", manufacturer_count=1, sensor_count=2)

        sensor_25 = {
            "sensor_id": 25,
            "sensor_rating": 800,
            "sensor_desc": "800",
            "trip_style_id": 3,
            "trip_style_name": "ICCB",
            "trip_type_id": 75,
            "trip_type_name": "MVT RMS-9",
            "manufacturer_id": 9,
            "manufacturer_name": "GE",
            "has_ltpu": True,
            "has_stpu": True,
            "has_inst": True,
            "has_gfpu": True,
        }
        sensor_26 = {
            "sensor_id": 26,
            "sensor_rating": 1200,
            "sensor_desc": "1200",
            "trip_style_id": 3,
            "trip_style_name": "ICCB",
            "trip_type_id": 75,
            "trip_type_name": "MVT RMS-9",
            "manufacturer_id": 9,
            "manufacturer_name": "GE",
            "has_ltpu": True,
            "has_stpu": False,
            "has_inst": False,
            "has_gfpu": False,
        }

        def cascade_payload(url: str):
            params = parse_qs(urlparse(url).query)
            manufacturer_id = params.get("manufacturer_id", [None])[0]
            trip_type_id = params.get("trip_type_id", [None])[0]
            trip_style_id = params.get("trip_style_id", [None])[0]
            sensors = [sensor_25, sensor_26] if trip_style_id == "3" else []
            return {
                "level": "trip_styles" if trip_style_id == "3" else "manufacturers",
                "count": len(sensors) or 2,
                "manufacturers": [
                    {"manufacturer_id": 9, "manufacturer_name": "GE", "trip_type_count": 1},
                ],
                "trip_types": [
                    {
                        "trip_type_id": 75,
                        "trip_type_name": "MVT RMS-9",
                        "manufacturer_id": 9,
                        "manufacturer_name": "GE",
                        "trip_style_count": 1,
                    }
                ] if manufacturer_id == "9" else [],
                "trip_styles": [
                    {
                        "trip_style_id": 3,
                        "trip_style_name": "ICCB",
                        "trip_type_id": 75,
                        "trip_type_name": "MVT RMS-9",
                        "manufacturer_id": 9,
                        "manufacturer_name": "GE",
                        "sensor_count": 2,
                    }
                ] if trip_type_id == "75" else [],
                "sensors": sensors,
            }

        page.route(
            "**/api/v1/neta/cascade*",
            lambda route: _fulfill_json(route, cascade_payload(route.request.url)),
        )
        page.route(
            "**/api/v1/neta/context/25",
            lambda route: _fulfill_json(
                route,
                {
                    "sensor_id": 25,
                    "sensor_desc": "800",
                    "rating": 800,
                    "has_ltpu": True,
                    "has_stpu": True,
                    "has_inst": True,
                    "has_gfpu": True,
                    "maint_capable": True,
                    "resolved_equipment": {
                        "family": "etu",
                        "family_label": "ETU",
                        "resolved_id": "sensor:25",
                        "primary_label": "GE · MVT RMS-9",
                        "secondary_label": "ICCB · Sensor 800",
                    },
                },
            ),
        )
        page.route(
            "**/api/v1/neta/context/26",
            lambda route: _fulfill_json(
                route,
                {
                    "sensor_id": 26,
                    "sensor_desc": "1200",
                    "rating": 1200,
                    "has_ltpu": True,
                    "has_stpu": False,
                    "has_inst": False,
                    "has_gfpu": False,
                    "maint_capable": False,
                    "resolved_equipment": {
                        "family": "etu",
                        "family_label": "ETU",
                        "resolved_id": "sensor:26",
                        "primary_label": "GE · MVT RMS-9",
                        "secondary_label": "ICCB · Sensor 1200",
                    },
                },
            ),
        )
        page.route(
            "**/api/v1/neta/settings/25",
            lambda route: _fulfill_json(
                route,
                {
                    "plug_values": [800],
                    "ltpu_settings": [0.8],
                    "ltd_settings": [{"band": "C-2", "label": "C-2", "open_time": 6.0, "is_default": True}],
                    "stpu_settings": [4.0],
                    "std_settings": [{"band": "I2T Min", "label": "Min", "open_time": 0.21, "is_default": True}],
                    "inst_settings": [10.0],
                    "gfpu_settings": [0.4],
                    "gfd_settings": [{"band": "GF Min", "label": "Min", "open_time": 0.21, "is_default": True}],
                },
            ),
        )
        page.route(
            "**/api/v1/neta/settings/26",
            lambda route: _fulfill_json(
                route,
                {
                    "plug_values": [1200],
                    "ltpu_settings": [1.0],
                    "ltd_settings": [{"band": "C-3", "label": "C-3", "open_time": 12.0, "is_default": True}],
                    "stpu_settings": [],
                    "std_settings": [],
                    "inst_settings": [],
                    "gfpu_settings": [],
                    "gfd_settings": [],
                },
            ),
        )
        page.route(
            "**/api/v1/neta/calculate",
            lambda route: _fulfill_json(
                route,
                {
                    "sensor_desc": "800",
                    "maint_mode": False,
                    "resolved_equipment": {
                        "family": "etu",
                        "family_label": "ETU",
                        "resolved_id": "sensor:25",
                    },
                    "elements": [
                        {
                            "element": "LTPU",
                            "test_current": 640.0,
                            "limit_low": 576.0,
                            "limit_high": 704.0,
                            "multiplier": 0.8,
                            "calc_method": "pickup",
                        }
                    ],
                    "warnings": [],
                },
            ),
        )
        page.route(
            "**/api/v1/neta/evaluate",
            lambda route: _fulfill_json(
                route,
                {
                    "overall_pass": True,
                    "tested_count": 1,
                    "passed_count": 1,
                    "failed_count": 0,
                    "maint_mode": False,
                    "elements": [
                        {
                            "element": "LTPU",
                            "test_current": 640.0,
                            "expected_current": 640.0,
                            "measured_current": 650.0,
                            "limit_low": 576.0,
                            "limit_high": 704.0,
                            "passed": True,
                            "deviation_pct": 1.6,
                        }
                    ],
                    "warnings": [],
                },
            ),
        )
        page.route(
            "**/api/v1/neta/plot-tcc",
            lambda route: _fulfill_json(
                route,
                {
                    "meta": {
                        "sensor_desc": "800",
                        "breaker_context_label": "ICCB · 800A",
                        "trip_unit_manufacturer": "GE",
                        "trip_unit_type": "MVT RMS-9",
                        "trip_unit_style": "ICCB",
                        "plug_rating": 800.0,
                        "overall_pass": True,
                        "maint_mode": False,
                        "maint_capable": True,
                        "maint_support_level": "full",
                        "plot_disclaimer": "",
                        "resolved_equipment": {
                            "family": "etu",
                            "family_label": "ETU",
                            "resolved_id": "sensor:25",
                        },
                    },
                    "warnings": [],
                    "curves": [
                        {
                            "id": "LTPU_open",
                            "curve_family": "ETU",
                            "line_style": "solid",
                            "points": [
                                {"amps": 576.0, "seconds": 30.0},
                                {"amps": 704.0, "seconds": 5.0},
                            ],
                        }
                    ],
                    "expected_markers": [
                        {
                            "element": "LTPU",
                            "kind": "pickup",
                            "expected_current": 640.0,
                            "limit_low": 576.0,
                            "limit_high": 704.0,
                            "expected_time": None,
                        }
                    ],
                    "measured_markers": [
                        {
                            "element": "LTPU",
                            "kind": "pickup",
                            "measured_current": 650.0,
                            "measured_time": None,
                        }
                    ],
                    "table_rows": [
                        {
                            "element": "LTPU",
                            "kind": "pickup",
                            "test_multiple": 0.8,
                            "expected_current": 640.0,
                            "limit_low": 576.0,
                            "limit_high": 704.0,
                            "expected_time": None,
                            "time_limit_low": None,
                            "time_limit_high": None,
                            "measured_current": 650.0,
                            "measured_time": None,
                            "passed": True,
                            "deviation_pct": 1.6,
                        }
                    ],
                },
            ),
        )

        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")
        page.wait_for_function(
            "() => !document.querySelector('#sel-mfr')?.disabled",
            timeout=10000,
        )

        page.locator("#sel-mfr").select_option("9")
        page.wait_for_function(
            "() => document.querySelector('#sel-type option[value=\"75\"]') !== null",
            timeout=10000,
        )
        page.locator("#sel-type").select_option("75")
        page.wait_for_function(
            "() => document.querySelector('#sel-style option[value=\"3\"]') !== null",
            timeout=10000,
        )
        page.locator("#sel-style").select_option("3")
        page.wait_for_function(
            "() => document.querySelector('#sel-sensor option[value=\"25\"]') !== null",
            timeout=10000,
        )
        page.locator("#sel-sensor").select_option("25")
        page.locator("#settings-section").wait_for(state="visible", timeout=10000)

        page.locator("#set-plug").select_option("800")
        page.locator("#meas-ltpu").fill("650")
        page.locator("#btn-calc").click()
        page.locator("#calc-section").wait_for(state="visible", timeout=10000)
        page.locator("#btn-tcc").click()
        page.locator("#eval-section").wait_for(state="visible", timeout=10000)
        page.locator("#tcc-section").wait_for(state="visible", timeout=10000)

        assert page.locator("#calc-section").is_visible()
        assert page.locator("#eval-section").is_visible()
        assert page.locator("#tcc-section").is_visible()

        page.locator("#sel-sensor").select_option("26")
        page.wait_for_function(
            "() => document.querySelector('#calc-section')?.classList.contains('hidden')",
            timeout=10000,
        )

        assert page.locator("#sensor-summary").is_visible()
        assert not page.locator("#calc-section").is_visible()
        assert not page.locator("#eval-section").is_visible()
        assert not page.locator("#tcc-section").is_visible()
        assert page.locator("#btn-export").is_disabled()
        assert page.locator("#btn-save-result").is_disabled()

    def test_tmt_settings_hide_empty_optional_rows(self, server, page):
        """TMT should keep its bounded frame-rooted plot flow while hiding empty optional setting rows."""
        _mock_demo_bootstrap(page)

        page.route(
            "**/api/v1/neta/tmt/frames*",
            lambda route: _fulfill_json(
                route,
                {
                    "count": 1,
                    "frames": [
                        {
                            "frame_id": 101,
                            "breaker_style_id": 501,
                            "breaker_class": "MCCB",
                            "frame_size": "600AF",
                            "manufacturer_name": "Square D",
                            "breaker_name": "PowerPact",
                            "breaker_style_name": "PXR",
                            "standard": 600.0,
                            "matched_amp_rating": None,
                        }
                    ],
                },
            ),
        )
        page.route(
            "**/api/v1/neta/tmt/context/101",
            lambda route: _fulfill_json(
                route,
                {
                    "frame_id": 101,
                    "breaker_style_id": 501,
                    "breaker_class": "MCCB",
                    "frame_size": "600AF",
                    "manufacturer_name": "Square D",
                    "breaker_name": "PowerPact",
                    "breaker_style_name": "PXR",
                    "standard": 600.0,
                    "available_trip_classes": [2],
                    "amp_rating_count": 1,
                    "setting_count": 0,
                    "thermal_adjustment_count": 0,
                    "resolved_equipment": {
                        "family": "tmt",
                        "family_label": "TMT",
                        "resolved_id": "tmt_frame:101",
                        "primary_label": "Square D · PowerPact",
                        "secondary_label": "PXR · MCCB · 600AF",
                    },
                },
            ),
        )
        page.route(
            "**/api/v1/neta/tmt/settings/101",
            lambda route: _fulfill_json(
                route,
                {
                    "frame_id": 101,
                    "available_trip_classes": [2],
                    "amp_ratings": [{"rating": 600.0, "max_override": None}],
                    "settings": [],
                    "thermal_adjustments": [],
                },
            ),
        )

        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")
        page.locator('[data-family="tmt"]').click()
        page.locator("#btn-tmt-search").click()
        page.locator("#tmt-frame-select").select_option("101")
        page.locator("#tmt-settings-section").wait_for(state="visible", timeout=10000)

        assert page.locator("#tmt-row-amp-rating").is_visible()
        assert not page.locator("#tmt-row-setting-value").is_visible()
        assert not page.locator("#tmt-row-thermal-adjustment").is_visible()
        assert page.locator("#btn-tmt-plot").is_disabled()

        page.locator("#tmt-trip-class").select_option("2")
        assert page.locator("#btn-tmt-plot").is_enabled()

    def test_tmt_refresh_retains_valid_frame_and_clears_stale_plot(self, server, page):
        """Refreshing TMT search results should retain a still-valid frame selection,
        but changing a downstream plot-driving choice must invalidate the old plot."""
        _mock_demo_bootstrap(page)

        resolved_equipment = {
            "family": "tmt",
            "family_label": "TMT",
            "resolved_id": "tmt_frame:101",
            "primary_label": "Square D · PowerPact",
            "secondary_label": "PXR · MCCB · 600AF",
            "breaker_context": {
                "label": "MCCB · 600AF",
                "source": "tmt_frame_context",
                "manufacturer_name": "Square D",
                "breaker_class": "MCCB",
                "breaker_name": "PowerPact",
                "breaker_style_name": "PXR",
            },
            "rating_context": {
                "label": "Frame · 600AF",
                "frame_id": 101,
                "frame_size": "600AF",
            },
        }

        page.route(
            "**/api/v1/neta/tmt/frames*",
            lambda route: _fulfill_json(
                route,
                {
                    "count": 1,
                    "frames": [
                        {
                            "frame_id": 101,
                            "breaker_style_id": 501,
                            "breaker_class": "MCCB",
                            "frame_size": "600AF",
                            "manufacturer_name": "Square D",
                            "breaker_name": "PowerPact",
                            "breaker_style_name": "PXR",
                            "standard": 600.0,
                            "matched_amp_rating": None,
                        }
                    ],
                },
            ),
        )
        page.route(
            "**/api/v1/neta/tmt/context/101",
            lambda route: _fulfill_json(
                route,
                {
                    "frame_id": 101,
                    "breaker_style_id": 501,
                    "breaker_class": "MCCB",
                    "frame_size": "600AF",
                    "manufacturer_name": "Square D",
                    "breaker_name": "PowerPact",
                    "breaker_style_name": "PXR",
                    "standard": 600.0,
                    "available_trip_classes": [1, 2],
                    "amp_rating_count": 2,
                    "setting_count": 2,
                    "thermal_adjustment_count": 2,
                    "resolved_equipment": resolved_equipment,
                },
            ),
        )
        page.route(
            "**/api/v1/neta/tmt/settings/101",
            lambda route: _fulfill_json(
                route,
                {
                    "frame_id": 101,
                    "available_trip_classes": [1, 2],
                    "amp_ratings": [
                        {"rating": 400.0, "max_override": None},
                        {"rating": 600.0, "max_override": 700.0},
                    ],
                    "settings": [
                        {"value": 0.8, "label": "Low", "tol_lo": 0.75, "tol_hi": 0.85},
                        {"value": 1.0, "label": "Full", "tol_lo": 0.95, "tol_hi": 1.05},
                    ],
                    "thermal_adjustments": [0.9, 1.0],
                },
            ),
        )
        page.route(
            "**/api/v1/neta/tmt/plot-tcc",
            lambda route: _fulfill_json(
                route,
                {
                    "meta": {
                        "frame_id": 101,
                        "breaker_style_id": 501,
                        "breaker_class": "MCCB",
                        "frame_size": "600AF",
                        "manufacturer_name": "Square D",
                        "breaker_name": "PowerPact",
                        "breaker_style_name": "PXR",
                        "standard": 600.0,
                        "selected_trip_class": 2,
                        "selected_amp_rating": 600.0,
                        "selected_max_override": 700.0,
                        "selected_setting": 1.0,
                        "selected_setting_label": "Full",
                        "selected_setting_tol_lo": 0.95,
                        "selected_setting_tol_hi": 1.05,
                        "selected_thermal_adjustment": 1.0,
                        "selections_applied_to_curve": False,
                        "plot_disclaimer": "Nominal TMT curve only.",
                        "resolved_equipment": resolved_equipment,
                    },
                    "warnings": [],
                    "curves": [
                        {
                            "id": "tmt_class_2",
                            "curve_family": "TMT",
                            "trip_class": 2,
                            "line_style": "solid",
                            "points": [
                                {"amps": 1000.0, "seconds": 1.0},
                                {"amps": 2000.0, "seconds": 0.1},
                            ],
                        }
                    ],
                    "raw_points": [],
                },
            ),
        )

        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")
        page.locator('[data-family="tmt"]').click()
        page.locator("#btn-tmt-search").click()
        page.locator("#tmt-frame-select").select_option("101")
        page.locator("#tmt-summary").wait_for(state="visible", timeout=10000)

        page.locator("#tmt-trip-class").select_option("2")
        page.locator("#tmt-amp-rating").select_option("600")
        page.locator("#tmt-setting-value").select_option("1")
        page.locator("#tmt-thermal-adjustment").select_option("1")
        page.locator("#btn-tmt-plot").click()
        page.locator("#tmt-plot-section").wait_for(state="visible", timeout=10000)

        page.locator("#btn-tmt-search").click()
        assert page.locator("#tmt-frame-select").input_value() == "101"
        assert page.locator("#tmt-trip-class").input_value() == "2"
        assert page.locator("#tmt-amp-rating").input_value() == "600"
        assert page.locator("#tmt-summary").is_visible()
        assert page.locator("#tmt-plot-section").is_visible()

        page.locator("#tmt-trip-class").select_option("1")
        assert not page.locator("#tmt-plot-section").is_visible(), \
            "Changing the TMT trip class should invalidate the stale nominal plot"
        assert page.locator("#tmt-summary").is_visible(), \
            "Resolved TMT summary should stay visible while downstream state changes"

    def test_etu_summary_discloses_breaker_context_provenance(self, server, page):
        """The ETU summary should disclose whether breaker context is derived or based on an active breaker-half selection."""
        _mock_demo_bootstrap(page, catalog="live", manufacturer_count=1, sensor_count=2)
        _mock_etu_phase_c_routes(page)

        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")
        page.locator("#preset-select").select_option(index=1)
        page.locator("#btn-load-preset").click()
        page.locator("#sensor-summary").wait_for(state="visible", timeout=10000)

        provenance_tag = page.locator("#sensor-summary .provenance-tag")
        assert provenance_tag.inner_text() == "(derived)"
        assert provenance_tag.get_attribute("data-source") == "trip_style_sensor_rating"

        page.locator("#sel-brk-mfr").select_option("9")
        page.locator("#sel-brk-class").select_option("ICCB")
        page.wait_for_function(
            "() => document.querySelector('#sel-brk-name option[value=\"501\"]') !== null",
            timeout=10000,
        )
        page.locator("#sel-brk-name").select_option("501")
        page.wait_for_function(
            "() => document.querySelector('#sel-brk-style option[value=\"701\"]') !== null",
            timeout=10000,
        )
        page.locator("#sel-brk-style").select_option("701")

        assert provenance_tag.inner_text() == "(selected)"
        assert provenance_tag.get_attribute("data-source") == "breaker_half_selection"
        assert "AKR-9" in page.locator("#sensor-summary").inner_text()

    def test_etu_plug_compatibility_check_reuses_search_contract_and_explains_scope_impact(self, server, page):
        """The bounded plug-compatibility workflow should reuse ETU search and explain how a plug change narrows the ETU browse space."""
        _mock_demo_bootstrap(page, catalog="live", manufacturer_count=1, sensor_count=2)
        _mock_etu_phase_c_routes(page)

        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")
        page.locator("#preset-select").select_option(index=1)
        page.locator("#btn-load-preset").click()
        page.locator("#settings-section").wait_for(state="visible", timeout=10000)

        compat_button = page.locator("#btn-plug-compat-check")
        assert compat_button.is_enabled()
        compat_button.click()
        page.locator("#plug-compat-result").wait_for(state="visible", timeout=10000)
        assert "2 compatible sensors" in page.locator("#plug-compat-result").inner_text()

        page.locator("#set-plug").select_option("1200")
        page.locator("#etu-plug-impact").wait_for(state="visible", timeout=10000)
        assert "narrowed the ETU space" in page.locator("#etu-plug-impact").inner_text()
        assert "Validate plug 1200A" in page.locator("#plug-compat-summary").inner_text()

        compat_button.click()
        page.locator("#plug-compat-result").wait_for(state="visible", timeout=10000)
        compat_result = page.locator("#plug-compat-result").inner_text()
        assert "1 compatible sensor" in compat_result
        assert "1200" in compat_result

    def test_emt_settings_hide_non_applicable_section_controls(self, server, page):
        """EMT should show only the section controls that the selected band context actually supports."""
        _mock_demo_bootstrap(page)

        page.route(
            "**/api/v1/neta/emt/frames*",
            lambda route: _fulfill_json(
                route,
                {
                    "count": 1,
                    "frames": [
                        {
                            "emt_id": 42,
                            "frame_id": 201,
                            "manufacturer_id": 10,
                            "manufacturer_name": "ABB",
                            "type_name": "EMT Type A",
                            "style_name": "Style 1",
                            "tcc_number": "EMT-42",
                            "trip_char": 7,
                            "trip_plug": 0,
                            "frame_size": 800.0,
                            "frame_desc": "Frame A",
                            "amp_rating_count": 1,
                            "section_count": 1,
                        }
                    ],
                },
            ),
        )
        page.route(
            "**/api/v1/neta/emt/context/201",
            lambda route: _fulfill_json(
                route,
                {
                    "emt_id": 42,
                    "frame_id": 201,
                    "manufacturer_id": 10,
                    "manufacturer_name": "ABB",
                    "type_name": "EMT Type A",
                    "style_name": "Style 1",
                    "tcc_number": "EMT-42",
                    "trip_char": 7,
                    "trip_plug": 0,
                    "frame_size": 800.0,
                    "frame_desc": "Frame A",
                    "amp_ratings": [800.0],
                    "sections": [
                        {
                            "section_id": 301,
                            "name": "Main",
                            "sec_char": 1,
                            "curve_type": 2,
                            "pickup_calc": 3,
                            "pickup_setting": 1,
                            "step_size": 0.5,
                            "current_calc": 4,
                            "pickup_count": 0,
                            "band_count": 1,
                        }
                    ],
                    "resolved_equipment": {
                        "family": "emt",
                        "family_label": "EMT",
                        "resolved_id": "emt_frame:201",
                        "primary_label": "ABB · EMT Type A · Style 1",
                        "secondary_label": "Frame A · Main",
                    },
                },
            ),
        )
        page.route(
            "**/api/v1/neta/emt/settings/301",
            lambda route: _fulfill_json(
                route,
                {
                    "section_id": 301,
                    "pickups": [],
                    "bands": [
                        {
                            "band_id": 401,
                            "band_name": "Band A",
                            "curve_classes": [],
                        }
                    ],
                },
            ),
        )

        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")
        page.locator('[data-family="emt"]').click()
        page.locator("#btn-emt-search").click()
        page.locator("#emt-frame-select").select_option("201")
        page.wait_for_function(
            "() => document.querySelector('#emt-section-select option[value=\"301\"]') !== null",
            timeout=10000,
        )
        page.locator("#emt-section-select").select_option("301")
        page.locator("#emt-settings-section").wait_for(state="visible", timeout=10000)

        assert not page.locator("#emt-row-pickup").is_visible()
        assert page.locator("#emt-row-band").is_visible()
        assert not page.locator("#emt-row-curve-class").is_visible()
        assert page.locator("#btn-emt-plot").is_disabled()

        page.locator("#emt-band-select").select_option("401")
        assert not page.locator("#emt-row-curve-class").is_visible()
        assert page.locator("#btn-emt-plot").is_enabled()

    def test_emt_refresh_retains_valid_frame_and_invalidates_band_specific_plot(self, server, page):
        """Refreshing EMT search results should retain a still-valid frame and section,
        while a band change must clear a stale plot and drop an invalid curve-class selection."""
        _mock_demo_bootstrap(page)

        resolved_equipment = {
            "family": "emt",
            "family_label": "EMT",
            "resolved_id": "emt_frame:201",
            "primary_label": "ABB · EMT Type A · Style 1",
            "secondary_label": "Frame A · Main",
            "breaker_context": {
                "label": "ABB · EMT Type A · Style 1",
                "source": "emt_frame_context",
                "manufacturer_name": "ABB",
                "type_name": "EMT Type A",
                "style_name": "Style 1",
                "tcc_number": "EMT-42",
            },
            "rating_context": {
                "label": "Frame A · Main",
                "frame_id": 201,
                "frame_desc": "Frame A",
                "section_id": 301,
                "section_name": "Main",
            },
        }

        page.route(
            "**/api/v1/neta/emt/frames*",
            lambda route: _fulfill_json(
                route,
                {
                    "count": 1,
                    "frames": [
                        {
                            "emt_id": 42,
                            "frame_id": 201,
                            "manufacturer_id": 10,
                            "manufacturer_name": "ABB",
                            "type_name": "EMT Type A",
                            "style_name": "Style 1",
                            "tcc_number": "EMT-42",
                            "trip_char": 7,
                            "trip_plug": 0,
                            "frame_size": 800.0,
                            "frame_desc": "Frame A",
                            "amp_rating_count": 2,
                            "section_count": 2,
                        }
                    ],
                },
            ),
        )
        page.route(
            "**/api/v1/neta/emt/context/201",
            lambda route: _fulfill_json(
                route,
                {
                    "emt_id": 42,
                    "frame_id": 201,
                    "manufacturer_id": 10,
                    "manufacturer_name": "ABB",
                    "type_name": "EMT Type A",
                    "style_name": "Style 1",
                    "tcc_number": "EMT-42",
                    "trip_char": 7,
                    "trip_plug": 0,
                    "frame_size": 800.0,
                    "frame_desc": "Frame A",
                    "amp_ratings": [400.0, 800.0],
                    "sections": [
                        {
                            "section_id": 301,
                            "name": "Main",
                            "sec_char": 1,
                            "curve_type": 2,
                            "pickup_calc": 3,
                            "pickup_setting": 1,
                            "step_size": 0.5,
                            "current_calc": 4,
                            "pickup_tol_lo": 0.9,
                            "pickup_tol_hi": 1.1,
                            "band_count": 2,
                            "pickup_count": 2,
                        },
                        {
                            "section_id": 302,
                            "name": "Short Delay",
                            "sec_char": 2,
                            "curve_type": 3,
                            "pickup_calc": 4,
                            "pickup_setting": 1,
                            "step_size": 0.5,
                            "current_calc": 5,
                            "pickup_tol_lo": 0.9,
                            "pickup_tol_hi": 1.1,
                            "band_count": 1,
                            "pickup_count": 1,
                        },
                    ],
                    "resolved_equipment": resolved_equipment,
                },
            ),
        )
        page.route(
            "**/api/v1/neta/emt/settings/301",
            lambda route: _fulfill_json(
                route,
                {
                    "section_id": 301,
                    "name": "Main",
                    "sec_char": 1,
                    "curve_type": 2,
                    "pickup_calc": 3,
                    "pickup_setting": 1,
                    "step_size": 0.5,
                    "current_calc": 4,
                    "pickup_tol_lo": 0.9,
                    "pickup_tol_hi": 1.1,
                    "pickups": [
                        {"setting": 8.0, "description": "Pickup 8"},
                        {"setting": 10.0, "description": "Pickup 10"},
                    ],
                    "bands": [
                        {"band_id": 401, "band_name": "Band A", "ordinal": 1, "current_at": 6.0, "curve_point_count": 2, "curve_classes": [1, 2]},
                        {"band_id": 402, "band_name": "Band B", "ordinal": 2, "current_at": 8.0, "curve_point_count": 2, "curve_classes": [3]},
                    ],
                },
            ),
        )
        page.route(
            "**/api/v1/neta/emt/plot-tcc",
            lambda route: _fulfill_json(
                route,
                {
                    "meta": {
                        "emt_id": 42,
                        "frame_id": 201,
                        "section_id": 301,
                        "band_id": 401,
                        "manufacturer_id": 10,
                        "manufacturer_name": "ABB",
                        "type_name": "EMT Type A",
                        "style_name": "Style 1",
                        "tcc_number": "EMT-42",
                        "frame_size": 800.0,
                        "frame_desc": "Frame A",
                        "section_name": "Main",
                        "sec_char": 1,
                        "curve_type": 2,
                        "pickup_calc": 3,
                        "pickup_setting": 1,
                        "current_calc": 4,
                        "band_name": "Band A",
                        "band_ordinal": 1,
                        "current_at": 6.0,
                        "available_curve_classes": [1, 2],
                        "selected_curve_class": 2,
                        "selections_applied_to_curve": False,
                        "plot_disclaimer": "Raw EMT point-data plot only.",
                        "resolved_equipment": resolved_equipment,
                    },
                    "warnings": [],
                    "curves": [
                        {
                            "id": "emt_band_401_class_2",
                            "curve_family": "EMT",
                            "band_id": 401,
                            "curve_class": 2,
                            "class_label": "Class 2",
                            "line_style": "solid",
                            "points": [
                                {"amps": 1200.0, "seconds": 0.8},
                                {"amps": 2000.0, "seconds": 0.2},
                            ],
                        }
                    ],
                },
            ),
        )

        page.goto(f"{server}/demo/neta-tcc")
        page.wait_for_load_state("networkidle")
        page.locator('[data-family="emt"]').click()
        page.locator("#btn-emt-search").click()
        page.locator("#emt-frame-select").select_option("201")
        page.locator("#emt-summary").wait_for(state="visible", timeout=10000)
        page.locator("#emt-section-select").select_option("301")
        page.locator("#emt-settings-section").wait_for(state="visible", timeout=10000)
        page.locator("#emt-band-select").select_option("401")
        page.locator("#emt-curve-class-select").select_option("2")
        page.locator("#btn-emt-plot").click()
        page.locator("#emt-plot-section").wait_for(state="visible", timeout=10000)

        page.locator("#btn-emt-search").click()
        assert page.locator("#emt-frame-select").input_value() == "201"
        assert page.locator("#emt-section-select").input_value() == "301"
        assert page.locator("#emt-summary").is_visible()
        assert page.locator("#emt-plot-section").is_visible()

        page.locator("#emt-band-select").select_option("402")
        assert page.locator("#emt-curve-class-select").input_value() == "", \
            "Curve class should clear when the previous EMT class is not legal for the new band"
        assert not page.locator("#emt-plot-section").is_visible(), \
            "Changing the EMT band should invalidate the stale raw-point plot"
        assert page.locator("#emt-summary").is_visible(), \
            "Resolved EMT summary should stay visible while downstream state changes"
