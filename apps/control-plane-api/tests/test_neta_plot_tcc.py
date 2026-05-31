"""
Route-level contract tests for POST /api/v1/neta/plot-tcc.

Strategy:
  - Uses FastAPI TestClient against the real app (no standing server).
  - Monkeypatches Session.execute so SQL functions return deterministic JSON.
  - Monkeypatches calc-engine collaborators (ETUPickupCalculator, ETULTDCalculator,
    IEEEInverseTimeSolver) so we can assert call arguments directly.
  - Focuses on semantic call correctness for the three recently fixed issues
    (plug_id wiring, delay-setting ordinals, evaluate-warning merge) plus
    basic response-shape validation and delay-marker enrichment.
"""

import sys
import os
import math
from dataclasses import dataclass
from typing import Optional
from unittest.mock import MagicMock, patch, call

import pytest

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from config import get_db


# ──────────────────────────────────────────────────
# Deterministic mock payloads
# ──────────────────────────────────────────────────

SENSOR_ID = 777
PLUG_RATING = 1200.0

CALC_DATA = {
    "sensor_desc": "Test Sensor 777",
    "manufacturer": "TestMfr",
    "trip_type": "Electronic",
    "trip_style": "LS-ETU-777",
    "maint_mode": False,
    "maint_capable": True,
    "maint_support_level": "partial_inst_gfpu",
    "warnings": ["calc warning A"],
    "ltpu": {
        "test_current": 960.0,
        "limit_low": 864.0,
        "limit_high": 1056.0,
        "test_multiplier": 1,
        "calc_method": 1,
        "setting": 0.8,
    },
    "ltd": {
        "test_current": 2880.0,
        "test_multiplier": 3.0,
        "calc_method": 1,
        "delay_opening": 5.0,
    },
    "stpu": {
        "test_current": 4800.0,
        "limit_low": 4320.0,
        "limit_high": 5280.0,
        "test_multiplier": 1,
        "calc_method": 0,
        "setting": 4.0,
    },
    "std": {
        "test_current": 7200.0,
        "test_multiplier": 1.5,
        "calc_method": 0,
    },
    "inst": {
        "test_current": 12000.0,
        "limit_low": 10800.0,
        "limit_high": 13200.0,
        "test_multiplier": 1,
        "calc_method": 0,
        "setting": 10.0,
        "delay_opening": 0.05,
        "delay_clearing": 0.08,
    },
    "gfpu": {
        "test_current": 480.0,
        "limit_low": 432.0,
        "limit_high": 528.0,
        "test_multiplier": 1,
        "calc_method": 0,
        "setting": 0.4,
    },
    "gfd": {
        "test_current": 720.0,
        "test_multiplier": 1.5,
        "calc_method": 0,
    },
}

EVAL_DATA = {
    "sensor_desc": "Test Sensor 777",
    "maint_mode": False,
    "maint_capable": True,
    "maint_support_level": "partial_inst_gfpu",
    "overall_pass": True,
    "warnings": ["eval warning B", "maint note C"],
    "ltpu": {
        "expected": 960.0,
        "measured": 950.0,
        "limit_low": 864.0,
        "limit_high": 1056.0,
        "pass": True,
        "deviation_pct": -1.04,
    },
    "stpu": {
        "expected": 4800.0,
        "measured": 4850.0,
        "limit_low": 4320.0,
        "limit_high": 5280.0,
        "pass": True,
        "deviation_pct": 1.04,
    },
    "inst": None,
    "gfpu": None,
}


# ──────────────────────────────────────────────────
# Mock dataclass stand-ins for calc-engine types
# ──────────────────────────────────────────────────

@dataclass
class FakePickupResult:
    current: float
    min_limit: float
    max_limit: float
    method: int
    method_name: str


@dataclass
class FakeAllPickupResults:
    sensor_id: int
    rating: int
    ltpu: Optional[FakePickupResult]
    stpu: Optional[FakePickupResult]
    inst: Optional[FakePickupResult]
    gfpu: Optional[FakePickupResult]
    maint_profile: dict


@dataclass
class FakeLTDCurvePoint:
    amps: float
    seconds: float


@dataclass
class FakeCurvePoint:
    amps: float
    seconds: float


FAKE_PICKUPS = FakeAllPickupResults(
    sensor_id=SENSOR_ID,
    rating=int(PLUG_RATING),
    ltpu=FakePickupResult(960.0, 864.0, 1056.0, 1, "PLUGTAP"),
    stpu=FakePickupResult(4800.0, 4320.0, 5280.0, 0, "SENSORFRAME"),
    inst=FakePickupResult(12000.0, 10800.0, 13200.0, 0, "SENSORFRAME"),
    gfpu=FakePickupResult(480.0, 432.0, 528.0, 0, "SENSORFRAME"),
    maint_profile={
        "capable": True,
        "support_level": "partial_inst_gfpu",
        "gf_delay_opening": None,
        "gf_delay_clearing": None,
    },
)

FAKE_LTD_CURVE = [
    FakeLTDCurvePoint(1500.0, 20.0),
    FakeLTDCurvePoint(2880.0, 5.5),
    FakeLTDCurvePoint(5000.0, 1.2),
    FakeLTDCurvePoint(10000.0, 0.3),
]

FAKE_STD_CURVE = [
    FakeCurvePoint(5000.0, 8.0),
    FakeCurvePoint(7200.0, 3.2),
    FakeCurvePoint(10000.0, 1.0),
]

FAKE_GFD_CURVE = [
    FakeCurvePoint(500.0, 6.0),
    FakeCurvePoint(720.0, 2.8),
    FakeCurvePoint(1000.0, 1.1),
]


# ──────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────

def _make_fake_execute(calc_data=CALC_DATA, eval_data=EVAL_DATA):
    """Return a side_effect function for Session.execute that returns
    deterministic payloads for the two SQL function calls."""
    call_count = {"n": 0}

    def fake_execute(stmt, params=None):
        sql_text = str(stmt) if not isinstance(stmt, str) else stmt
        result = MagicMock()
        if "vw_sensor_calc_context" in sql_text:
            row = MagicMock()
            row._mapping = {"rating": PLUG_RATING}
            result.fetchone.return_value = row
        elif "fn_calculate_test_currents" in sql_text:
            row = MagicMock()
            row.result = calc_data
            result.fetchone.return_value = row
        elif "fn_evaluate_test_results" in sql_text:
            row = MagicMock()
            row.result = eval_data
            result.fetchone.return_value = row
        elif "tcc.etu_ltd_bands" in sql_text:
            setting = (params or {}).get("setting")
            if "AND ltd_setting = :setting" in sql_text and setting != 3.5:
                result.fetchone.return_value = None
            else:
                row = MagicMock()
                row._mapping = {"open_time": 3.5, "clear_time": 3.0, "ordinal": 2, "is_default": False}
                result.fetchone.return_value = row
        elif "tcc.etu_std_bands" in sql_text:
            setting = (params or {}).get("setting")
            if "AND std_open = :setting" in sql_text and setting != 2.0:
                result.fetchone.return_value = None
            else:
                row = MagicMock()
                row._mapping = {"open_time": 2.0, "clear_time": 2.5, "ordinal": 1, "is_default": True}
                result.fetchone.return_value = row
        elif "tcc.etu_gfd_bands" in sql_text:
            setting = (params or {}).get("setting")
            if "AND gfd_open = :setting" in sql_text and setting != 1.5:
                result.fetchone.return_value = None
            else:
                row = MagicMock()
                row._mapping = {"open_time": 1.5, "clear_time": 1.8, "ordinal": 1, "is_default": True}
                result.fetchone.return_value = row
        else:
            result.fetchone.return_value = None
        return result

    return fake_execute


def _last_sql_params(mock_session, function_name: str):
    matching = [
        call_args.args[1]
        for call_args in mock_session.execute.call_args_list
        if len(call_args.args) >= 2 and function_name in str(call_args.args[0])
    ]
    assert matching, f"No SQL execute call captured for {function_name}"
    return matching[-1]


def _sql_call_count(mock_session, function_name: str) -> int:
    return sum(
        1
        for call_args in mock_session.execute.call_args_list
        if len(call_args.args) >= 1 and function_name in str(call_args.args[0])
    )


@pytest.fixture
def client():
    """FastAPI test client with mocked DB dependency."""
    mock_session = MagicMock()
    mock_session.execute = MagicMock(side_effect=_make_fake_execute())

    def override_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_db
    yield TestClient(app), mock_session
    app.dependency_overrides.clear()


@pytest.fixture
def base_request():
    """Minimal valid request payload."""
    return {
        "sensor_id": SENSOR_ID,
        "plug_rating": PLUG_RATING,
        "ltpu_setting": 0.8,
        "ltd_setting": 3.5,
        "stpu_setting": 4.0,
        "std_setting": 2.0,
        "inst_setting": 10.0,
        "gfpu_setting": 0.4,
        "gfd_setting": 1.5,
        "maint_mode": False,
        "include_nominal_curve": True,
        "include_expected_markers": True,
        "include_measured_markers": True,
    }


# ──────────────────────────────────────────────────
# Helper to patch all three calc-engine classes
# ──────────────────────────────────────────────────

def _patch_calc_engine(
    plug_list=None,
    pickups=None,
    ltd_info=None,
    ltd_bands=None,
    ltd_curve=None,
    std_eqs=None,
    std_curve=None,
    gfd_eqs=None,
    gfd_curve=None,
):
    """Return a context manager that patches ETUPickupCalculator,
    ETULTDCalculator, and IEEEInverseTimeSolver in the router module,
    returning references for call-argument inspection."""

    if plug_list is None:
        plug_list = [
            {"id": 101, "value": 800},
            {"id": 102, "value": 1200},
            {"id": 103, "value": 1600},
        ]
    if pickups is None:
        pickups = FAKE_PICKUPS
    if ltd_info is None:
        ltd_info = [{"ordinal": 2, "method": 1, "curve_name": "I²t Inverse",
                     "tol_hi": 10.0, "tol_lo": -10.0, "delay_priority": 1}]
    if ltd_bands is None:
        ltd_bands = [
            {"ordinal": 1, "band": "A", "band_label": "Min CB",
             "open_time": 2.0, "clear_time": 1.5, "curve_id": None, "is_default": True},
            {"ordinal": 2, "band": "B", "band_label": "Mid",
             "open_time": 3.5, "clear_time": 3.0, "curve_id": None, "is_default": False},
            {"ordinal": 3, "band": "C", "band_label": "Max",
             "open_time": 6.0, "clear_time": 5.0, "curve_id": None, "is_default": False},
        ]
    if ltd_curve is None:
        ltd_curve = FAKE_LTD_CURVE
    if std_eqs is None:
        std_eqs = [{"ordinal": 3, "label": "Very Inverse", "in_out": 0}]
    if std_curve is None:
        std_curve = FAKE_STD_CURVE
    if gfd_eqs is None:
        gfd_eqs = [{"ordinal": 5, "label": "Extremely Inverse", "in_out": 0}]
    if gfd_curve is None:
        gfd_curve = FAKE_GFD_CURVE

    # Build mock pickup calculator
    mock_pickup_cls = MagicMock()
    mock_pickup_inst = MagicMock()
    mock_pickup_cls.return_value = mock_pickup_inst
    mock_pickup_inst.get_plugs_for_style.return_value = plug_list
    mock_pickup_inst.calculate.return_value = pickups

    # Build mock LTD calculator
    mock_ltd_cls = MagicMock()
    mock_ltd_inst = MagicMock()
    mock_ltd_cls.return_value = mock_ltd_inst
    mock_ltd_inst.get_ltd_info.return_value = ltd_info
    mock_ltd_inst.get_band_info.return_value = ltd_bands
    mock_ltd_inst.generate_curve.return_value = ltd_curve

    # Build mock IEEE solver
    mock_ieee_cls = MagicMock()
    mock_ieee_inst = MagicMock()
    mock_ieee_cls.return_value = mock_ieee_inst
    mock_ieee_inst.get_equation_info.side_effect = lambda sid, eq_type='std': (
        std_eqs if eq_type == 'std' else gfd_eqs
    )

    def _ieee_generate_curve(sensor_id, ordinal, variant, pickup_current,
                             time_dial=1.0, tolerance_pct=0.0,
                             min_time=None, max_amps=100000.0,
                             equation_type='std'):
        if equation_type == 'gfd':
            return gfd_curve
        return std_curve

    mock_ieee_inst.generate_curve.side_effect = _ieee_generate_curve

    patches = {
        "pickup": patch(
            "apex_calc_engine.services.calc_engine.ETUPickupCalculator", mock_pickup_cls
        ),
        "ltd": patch(
            "apex_calc_engine.services.calc_engine.ETULTDCalculator", mock_ltd_cls
        ),
        "ieee": patch(
            "apex_calc_engine.services.calc_engine.IEEEInverseTimeSolver", mock_ieee_cls
        ),
    }

    return patches, {
        "pickup_cls": mock_pickup_cls,
        "pickup_inst": mock_pickup_inst,
        "ltd_cls": mock_ltd_cls,
        "ltd_inst": mock_ltd_inst,
        "ieee_cls": mock_ieee_cls,
        "ieee_inst": mock_ieee_inst,
    }


# ──────────────────────────────────────────────────
# Test 1: Expected-only payload — response shape
# ──────────────────────────────────────────────────

class TestExpectedOnlyShape:
    """When no measurements are provided, the response must include meta,
    curves, expected_markers, table_rows, and zero measured markers."""

    def test_shape_no_measurements(self, client, base_request):
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        body = resp.json()

        # Meta
        assert body["meta"]["sensor_id"] == SENSOR_ID
        assert body["meta"]["sensor_desc"] == "Test Sensor 777"
        assert body["meta"]["breaker_context_label"] == "LS-ETU-777"
        assert body["meta"]["breaker_context_source"] == "trip_style_fallback"
        assert body["meta"]["maint_capable"] is True
        assert body["meta"]["maint_support_level"] == "partial_inst_gfpu"
        assert body["meta"]["overall_pass"] is None  # no eval path
        assert body["meta"]["trip_unit_manufacturer"] == "TestMfr"
        assert body["meta"]["trip_unit_type"] == "Electronic"
        assert body["meta"]["trip_unit_style"] == "LS-ETU-777"

        # Markers
        assert len(body["expected_markers"]) > 0
        assert len(body["measured_markers"]) == 0

        # Table rows: 4 pickup + 3 delay = 7
        assert len(body["table_rows"]) == 7

        # Curves: LTD(open+clear) + STD(open+clear) + INST(open+clear) + GFD(open+clear)
        curve_ids = {c["id"] for c in body["curves"]}
        assert "ltd_open" in curve_ids
        assert "std_open" in curve_ids
        assert "inst_open" in curve_ids
        assert "gfd_open" in curve_ids

        # Warnings from calc only
        assert "calc warning A" in body["warnings"]


# ──────────────────────────────────────────────────
# Test 2: Measured path — overall_pass + warning merge
# ──────────────────────────────────────────────────

class TestMeasuredPathWarnings:
    """When measurements are provided, overall_pass must be populated and
    in-process evaluation should populate pass/fail markers without reviving
    the old SQL-eval warning surface."""

    def test_eval_warnings_merged(self, client, base_request):
        tc, _ = client
        req = {
            **base_request,
            "measurements": [
                {"element": "LTPU", "measured_current": 950.0},
                {"element": "STPU", "measured_current": 4850.0},
            ],
        }

        patches, mocks = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        body = resp.json()

        # overall_pass set
        assert body["meta"]["overall_pass"] is True

        # Measured markers present
        assert len(body["measured_markers"]) == 2
        ltpu_m = next(m for m in body["measured_markers"] if m["element"] == "LTPU")
        assert ltpu_m["passed"] is True
        assert ltpu_m["measured_current"] == 950.0

        # Only calculate warnings survive; the in-process evaluator does not
        # emit the old SQL warning strings.
        assert body["warnings"] == ["calc warning A"]

    def test_plot_does_not_call_sql_evaluate_helper(self, client, base_request):
        tc, mock_session = client
        req = {
            **base_request,
            "measurements": [
                {"element": "LTPU", "measured_current": 950.0},
                {"element": "STPU", "measured_current": 4850.0},
            ],
        }

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        assert _sql_call_count(mock_session, "fn_evaluate_test_results") == 0


# ──────────────────────────────────────────────────
# Test 3: Direct /calculate and /evaluate parity
# ──────────────────────────────────────────────────

class TestCalculateEvaluateParity:
    """Direct calculate/evaluate endpoints should expose the same
    pickup-vs-delay split already used by plot-tcc."""

    def test_calculate_includes_delay_elements(self, client):
        tc, _ = client
        req = {
            "sensor_id": SENSOR_ID,
            "plug_rating": PLUG_RATING,
            "ltpu_setting": 0.8,
            "ltd_setting": 3.5,
            "stpu_setting": 4.0,
            "std_setting": 2.0,
            "inst_setting": 10.0,
            "gfpu_setting": 0.4,
            "gfd_setting": 1.5,
            "maint_mode": False,
        }

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/calculate", json=req)

        assert resp.status_code == 200
        body = resp.json()
        elements = {e["element"]: e for e in body["elements"]}
        assert set(elements) == {"LTPU", "LTD", "STPU", "STD", "INST", "GFPU", "GFD"}

        ltd = elements["LTD"]
        assert ltd["kind"] == "delay"
        assert ltd["limit_low"] is None
        assert ltd["limit_high"] is None
        assert ltd["delay_seconds"] == 3.5
        assert ltd["time_limit_low"] == 3.0
        assert ltd["time_limit_high"] == 3.5
        assert ltd["notes"] == "timing_source=band_table"

        inst = elements["INST"]
        assert inst["kind"] == "pickup"
        assert inst["limit_low"] == 10800.0
        assert inst["delay_seconds"] == 0.05

    def test_evaluate_includes_delay_time_results(self):
        eval_data = {
            **EVAL_DATA,
            "ltpu": {
                "expected": 960.0,
                "measured": 950.0,
                "limit_low": 864.0,
                "limit_high": 1056.0,
                "pass": True,
                "deviation_pct": -1.04,
            },
            "stpu": None,
            "inst": None,
            "gfpu": None,
        }

        mock_session = MagicMock()
        mock_session.execute = MagicMock(
            side_effect=_make_fake_execute(calc_data=CALC_DATA, eval_data=eval_data)
        )

        def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            tc = TestClient(app)
            req = {
                "sensor_id": SENSOR_ID,
                "plug_rating": PLUG_RATING,
                "ltpu_setting": 0.8,
                "ltd_setting": 3.5,
                "stpu_setting": 4.0,
                "std_setting": 2.0,
                "inst_setting": 10.0,
                "gfpu_setting": 0.4,
                "gfd_setting": 1.5,
                "maint_mode": False,
                "measurements": [
                    {"element": "LTPU", "measured_current": 950.0},
                    {"element": "LTD", "measured_time": 3.2},
                    {"element": "STD", "measured_time": 3.2},
                ],
            }

            patches, _ = _patch_calc_engine()
            with patches["pickup"], patches["ltd"], patches["ieee"]:
                resp = tc.post("/api/v1/neta/evaluate", json=req)

            assert resp.status_code == 200
            body = resp.json()
            elements = {e["element"]: e for e in body["elements"]}

            assert body["overall_pass"] is False
            assert body["tested_count"] == 3
            assert body["passed_count"] == 2
            assert body["failed_count"] == 1

            ltd = elements["LTD"]
            assert ltd["kind"] == "delay"
            assert ltd["measured_time"] == 3.2
            assert ltd["time_limit_low"] == 3.0
            assert ltd["time_limit_high"] == 3.5
            assert ltd["passed"] is True
            assert ltd["notes"] == "timing_source=band_table"

            std = elements["STD"]
            assert std["kind"] == "delay"
            assert std["measured_time"] == 3.2
            assert std["time_limit_low"] == 2.0
            assert std["time_limit_high"] == 2.5
            assert std["passed"] is False

            ltpu = elements["LTPU"]
            assert ltpu["kind"] == "pickup"
            assert ltpu["measured_current"] == 950.0
            assert ltpu["passed"] is True
            assert _sql_call_count(mock_session, "fn_evaluate_test_results") == 0
        finally:
            app.dependency_overrides.clear()

    def test_evaluate_rounds_pickup_deviation_like_sql_helper(self):
        mock_session = MagicMock()
        mock_session.execute = MagicMock(
            side_effect=_make_fake_execute(calc_data=GE_PRESET_CLEAN_CALC_DATA, eval_data=EVAL_DATA)
        )

        def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            tc = TestClient(app)
            req = {
                "sensor_id": 25,
                "plug_rating": 800.0,
                "ltpu_setting": 0.8,
                "ltd_setting": 6.0,
                "stpu_setting": 4.0,
                "std_setting": 0.21,
                "inst_setting": 10.0,
                "gfpu_setting": 0.4,
                "gfd_setting": 0.21,
                "maint_mode": False,
                "measurements": [
                    {"element": "LTPU", "measured_current": 650.0},
                    {"element": "STPU", "measured_current": 3100.0},
                    {"element": "GFPU", "measured_current": 310.0},
                ],
            }

            patches, _ = _patch_calc_engine()
            with patches["pickup"], patches["ltd"], patches["ieee"]:
                resp = tc.post("/api/v1/neta/evaluate", json=req)

            assert resp.status_code == 200
            body = resp.json()
            elements = {e["element"]: e for e in body["elements"]}
            assert elements["GFPU"]["deviation_pct"] == -3.13
        finally:
            app.dependency_overrides.clear()


# ──────────────────────────────────────────────────
# Test 4: Plug-aware curve generation
# ──────────────────────────────────────────────────

class TestPlugIdResolution:
    """Verify req.plug_rating is resolved to the matching plug_id and
    passed into ETUPickupCalculator.calculate()."""

    def test_plug_rating_resolves_to_plug_id(self, client, base_request):
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine(
            plug_list=[
                {"id": 201, "value": 800},
                {"id": 202, "value": 1200},  # matches PLUG_RATING=1200
                {"id": 203, "value": 1600},
            ]
        )
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200

        # Assert plug_id=202 was passed to calculate()
        mocks["pickup_inst"].calculate.assert_called_once()
        call_kwargs = mocks["pickup_inst"].calculate.call_args
        assert call_kwargs.kwargs.get("plug_id") == 202

    def test_plug_rating_no_match_still_calls_calculate(self, client, base_request):
        """When plug_rating doesn't match any plug, calculate is still called
        with plug_id=None and a warning is logged."""
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine(
            plug_list=[
                {"id": 301, "value": 800},
                {"id": 302, "value": 1600},
                # No 1200 — so PLUG_RATING won't match
            ]
        )
        with patches["pickup"], patches["ltd"], patches["ieee"], \
             patch("services.neta.router.logger") as mock_logger:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        call_kwargs = mocks["pickup_inst"].calculate.call_args
        assert call_kwargs.kwargs.get("plug_id") is None

        # Verify the route logged a warning about the unmatched plug_rating
        mock_logger.warning.assert_any_call(
            "plug_rating %s not found for sensor %s; "
            "PLUGTAP curves may be incorrect",
            PLUG_RATING, SENSOR_ID,
        )


class TestFactorizedInputPassThrough:
    def test_calculate_route_passes_factor_inputs_to_sql(self, client, base_request):
        tc, mock_session = client
        req = {
            **base_request,
            "multiplier_value": 4.0,
            "c_factor": 2.0,
        }

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/calculate", json=req)

        assert resp.status_code == 200
        params = _last_sql_params(mock_session, "fn_calculate_test_currents")
        assert params["p_multiplier_value"] == 4.0
        assert params["p_c_factor"] == 2.0

    def test_evaluate_route_passes_factor_inputs_to_sql(self, client, base_request):
        tc, mock_session = client
        req = {
            **base_request,
            "multiplier_value": 8.0,
            "c_factor": 4.0,
            "measurements": [
                {"element": "LTPU", "measured_current": 950.0},
                {"element": "STPU", "measured_current": 4850.0},
            ],
        }

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/evaluate", json=req)

        assert resp.status_code == 200
        params = _last_sql_params(mock_session, "fn_calculate_test_currents")
        assert params["p_multiplier_value"] == 8.0
        assert params["p_c_factor"] == 4.0

    def test_plot_route_passes_factor_inputs_to_curve_helper(self, client, base_request):
        tc, _ = client
        req = {
            **base_request,
            "multiplier_value": 6.0,
            "c_factor": 3.0,
            "measurements": None,
            "include_measured_markers": False,
        }

        patches, mocks = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        call_kwargs = mocks["pickup_inst"].calculate.call_args.kwargs
        assert call_kwargs.get("multiplier_value") == 6.0
        assert call_kwargs.get("c_factor") == 3.0


# ──────────────────────────────────────────────────
# Test 5: LTD band selection from req.ltd_setting
# ──────────────────────────────────────────────────

class TestLTDBandSelection:
    """Verify req.ltd_setting selects the matching LTD band ordinal
    rather than defaulting blindly."""

    def test_ltd_setting_selects_correct_band_ordinal(self, client, base_request):
        tc, _ = client
        # req.ltd_setting = 3.5 should match band ordinal 2 (open_time=3.5)
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine(
            ltd_bands=[
                {"ordinal": 1, "band": "A", "band_label": "Min",
                 "open_time": 2.0, "clear_time": 1.5, "curve_id": None, "is_default": True},
                {"ordinal": 2, "band": "B", "band_label": "Mid",
                 "open_time": 3.5, "clear_time": 3.0, "curve_id": None, "is_default": False},
                {"ordinal": 3, "band": "C", "band_label": "Max",
                 "open_time": 6.0, "clear_time": 5.0, "curve_id": None, "is_default": False},
            ],
            ltd_info=[{"ordinal": 7, "method": 2, "curve_name": "IEEE",
                       "tol_hi": 10, "tol_lo": -10, "delay_priority": 1}],
        )
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200

        # generate_curve should have been called with ltd_param_ordinal=7 (from ltd_info)
        # and ltd_band_ordinal=2 (the band whose open_time matches 3.5)
        calls = mocks["ltd_inst"].generate_curve.call_args_list
        assert len(calls) == 2  # open + clear

        for c in calls:
            assert c.kwargs["ltd_param_ordinal"] == 7
            assert c.kwargs["ltd_band_ordinal"] == 2

    def test_ltd_setting_no_match_falls_back_to_first_band(self, client, base_request):
        """When ltd_setting doesn't match any band's open_time, use first band."""
        tc, _ = client
        req = {**base_request, "ltd_setting": 99.9,
               "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine(
            ltd_bands=[
                {"ordinal": 10, "band": "X", "band_label": "Only",
                 "open_time": 4.0, "clear_time": 3.0, "curve_id": None, "is_default": True},
            ],
        )
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        for c in mocks["ltd_inst"].generate_curve.call_args_list:
            assert c.kwargs["ltd_band_ordinal"] == 10  # fell back to first


# ──────────────────────────────────────────────────
# Test 5: STD/GFD ordinal + time_dial selection
# ──────────────────────────────────────────────────

class TestSTDGFDSelection:
    """Verify req.std_setting and req.gfd_setting are passed through as
    time_dial, and the first available equation ordinal is used."""

    def test_std_ordinal_and_time_dial(self, client, base_request):
        tc, _ = client
        req = {**base_request, "std_setting": 2.5,
               "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine(
            std_eqs=[{"ordinal": 4, "label": "Very Inverse", "in_out": 0}],
        )
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200

        # Inspect IEEE generate_curve calls for STD (equation_type defaults to 'std')
        std_calls = [
            c for c in mocks["ieee_inst"].generate_curve.call_args_list
            if c.kwargs.get("equation_type", "std") == "std"
        ]
        assert len(std_calls) == 2  # open + clear
        for c in std_calls:
            assert c.kwargs["ordinal"] == 4
            assert c.kwargs["time_dial"] == 2.5

    def test_gfd_ordinal_and_time_dial(self, client, base_request):
        tc, _ = client
        req = {**base_request, "gfd_setting": 1.8,
               "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine(
            gfd_eqs=[{"ordinal": 6, "label": "GFD Curve", "in_out": 0}],
        )
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200

        gfd_calls = [
            c for c in mocks["ieee_inst"].generate_curve.call_args_list
            if c.kwargs.get("equation_type") == "gfd"
        ]
        assert len(gfd_calls) == 2
        for c in gfd_calls:
            assert c.kwargs["ordinal"] == 6
            assert c.kwargs["time_dial"] == 1.8

    def test_std_null_setting_defaults_time_dial_to_1(self, client, base_request):
        """When std_setting is None, time_dial should default to 1.0."""
        tc, _ = client
        req = {**base_request, "std_setting": None,
               "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        std_calls = [
            c for c in mocks["ieee_inst"].generate_curve.call_args_list
            if c.kwargs.get("equation_type", "std") == "std"
        ]
        for c in std_calls:
            assert c.kwargs["time_dial"] == 1.0


class TestSeparatedDelayInputs:
    """Delay band selection must be independent from NETA test multiples."""

    def test_explicit_delay_fields_keep_test_multiples_for_sql(self, client, base_request):
        tc, mock_session = client
        req = {
            **base_request,
            "ltd_delay_setting": 3.5,
            "ltd_test_multiple": 3.0,
            "std_delay_setting": 2.0,
            "std_test_multiple": 1.5,
            "gfd_delay_setting": 1.5,
            "gfd_test_multiple": 1.5,
            "measurements": None,
            "include_measured_markers": False,
        }

        patches, mocks = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        params = _last_sql_params(mock_session, "fn_calculate_test_currents")
        assert params["p_ltd_setting"] == 3.0
        assert params["p_std_setting"] == 1.5
        assert params["p_gfd_setting"] == 1.5

        std_calls = [
            c for c in mocks["ieee_inst"].generate_curve.call_args_list
            if c.kwargs.get("equation_type", "std") == "std"
        ]
        for c in std_calls:
            assert c.kwargs["time_dial"] == 2.0

    def test_legacy_band_open_time_uses_default_test_multiple(self, client, base_request):
        tc, mock_session = client
        req = {
            **base_request,
            "std_setting": 2.0,
            "gfd_setting": 1.5,
            "measurements": None,
            "include_measured_markers": False,
        }

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        params = _last_sql_params(mock_session, "fn_calculate_test_currents")
        assert params["p_std_setting"] == 1.5
        assert params["p_gfd_setting"] == 1.5


# ──────────────────────────────────────────────────
# Test 6: Delay marker enrichment from curve interpolation
# ──────────────────────────────────────────────────

class TestDelayMarkerEnrichment:
    """Verify delay expected markers use selected band timing surfaces."""

    def test_ltd_marker_gets_reference_window(self, client, base_request):
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        body = resp.json()

        ltd_marker = next(
            (m for m in body["expected_markers"]
             if m["element"] == "LTD" and m["kind"] == "delay"),
            None,
        )
        assert ltd_marker is not None
        assert ltd_marker["expected_time"] is not None
        assert ltd_marker["expected_time"] == 14.0

        # Table row should also be enriched
        ltd_row = next(
            (r for r in body["table_rows"] if r["element"] == "LTD"), None
        )
        assert ltd_row is not None
        assert ltd_row["expected_time"] is not None
        assert ltd_row["expected_time"] == 14.0
        assert ltd_row["time_limit_low"] == pytest.approx(9.8)
        assert ltd_row["time_limit_high"] == 14.0

    def test_ltd_reference_window_wins_even_if_curve_is_narrow(self, client, base_request):
        """LTD reference timing should still populate the marker even when the
        nominal curve would not support interpolation."""
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine(
            ltd_curve=[
                FakeLTDCurvePoint(100.0, 50.0),
                FakeLTDCurvePoint(200.0, 40.0),
            ]
        )
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        body = resp.json()

        ltd_marker = next(
            (m for m in body["expected_markers"]
             if m["element"] == "LTD" and m["kind"] == "delay"),
            None,
        )
        assert ltd_marker is not None
        assert ltd_marker["expected_time"] == 14.0


# ══════════════════════════════════════════════════
# Golden Scenarios — Canonical semantic contract tests
# ══════════════════════════════════════════════════
#
# Each golden scenario locks a distinct semantic path through
# calculate → evaluate → plot-tcc. Scenario names are stable
# references for future audit and review work.

# ── Golden Scenario Data ──

GOLDEN_MAINT_CALC_DATA = {
    **CALC_DATA,
    "maint_mode": True,
    "maint_capable": True,
    "maint_support_level": "partial_inst_gfpu",
    "warnings": [
        "Reduction factors not available — using 1.0",
        "GFPU maint calc inactive (-1) — using normal GFPU",
    ],
    "inst": {
        **CALC_DATA["inst"],
        "limit_low": 10800.0,
        "limit_high": 13200.0,
        "delay_opening": 0.01,
        "delay_clearing": 0.05,
        "calc_method": 1,  # PLUGTAP method in maint
    },
}

GOLDEN_MAINT_EVAL_DATA = {
    **EVAL_DATA,
    "maint_mode": True,
    "maint_capable": True,
    "maint_support_level": "partial_inst_gfpu",
    "overall_pass": True,
    "warnings": [
        "MAINT mode: INST tolerances from maint table (±10%)",
        "MAINT mode: GFPU using normal tolerances (maint_gfpu_calc inactive)",
    ],
    "inst": {
        "expected": 12000.0,
        "measured": 11500.0,
        "limit_low": 10800.0,
        "limit_high": 13200.0,
        "pass": True,
        "deviation_pct": -4.17,
    },
}

GOLDEN_DEGRADED_CALC_DATA = {
    **CALC_DATA,
    "warnings": ["calc warning A", "plug_rating mismatch: using nominal curves only"],
}

GE_PRESET_CLEAN_CALC_DATA = {
    "sensor_desc": "800",
    "manufacturer": "GE",
    "trip_type": "MVT RMS-9",
    "trip_style": "ICCB",
    "maint_mode": False,
    "maint_capable": False,
    "maint_support_level": "none",
    "warnings": [],
    "ltpu": {
        "test_current": 640.0,
        "limit_low": 640.0,
        "limit_high": 768.0,
        "test_multiplier": 1,
        "calc_method": 1,
        "setting": 0.8,
    },
    "ltd": {
        "test_current": 3840.0,
        "test_multiplier": 3.0,
        "calc_method": 0,
    },
    "stpu": {
        "test_current": 2560.0,
        "limit_low": 2304.0,
        "limit_high": 2816.0,
        "test_multiplier": 1,
        "calc_method": 4,
        "setting": 4.0,
    },
    "std": {
        "test_current": 537.6,
        "test_multiplier": 1.5,
        "calc_method": 0,
    },
    "inst": {
        "test_current": 8000.0,
        "limit_low": 7200.0,
        "limit_high": 8800.0,
        "test_multiplier": 1,
        "calc_method": 1,
        "setting": 10.0,
        "delay_opening": 0.01,
        "delay_clearing": 0.08,
    },
    "gfpu": {
        "test_current": 320.0,
        "limit_low": 288.0,
        "limit_high": 352.0,
        "test_multiplier": 1,
        "calc_method": 0,
        "setting": 0.4,
    },
    "gfd": {
        "test_current": 67.2,
        "test_multiplier": 1.5,
        "calc_method": 0,
    },
}


class TestGoldenNormalSST:
    """GOLDEN: Normal SST — full 4-element pickup + delay coordination.

    Locks the baseline semantic contract for a non-MAINT run:
    - calculate returns all 7 elements (4 pickup + 3 delay)
    - evaluate merges overall_pass and warnings
    - plot-tcc meta has no disclaimer, no MAINT badge
    - expected markers placed for all elements
    - measured markers placed with pass/fail state
    """

    def test_calculate_element_structure(self, client, base_request):
        """Calculate returns 4 pickup + 3 delay elements with correct
        current/timing for the normal SST path."""
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        body = resp.json()
        elements = {r["element"] for r in body["table_rows"]}
        assert elements == {"LTPU", "LTD", "STPU", "STD", "INST", "GFPU", "GFD"}

        # Pickup table rows have expected_current
        ltpu_row = next(r for r in body["table_rows"] if r["element"] == "LTPU")
        assert ltpu_row["expected_current"] == 960.0

        # Pickup expected markers have tolerance bands
        ltpu_marker = next(m for m in body["expected_markers"]
                           if m["element"] == "LTPU" and m["kind"] == "pickup")
        assert ltpu_marker["limit_low"] == 864.0
        assert ltpu_marker["limit_high"] == 1056.0


class TestGEPresetNoWarningContract:
    """Lock the local demo GE preset route behavior without depending on the
    full live smoke script.

    This contract should stay aligned with sensor 25 after the ETU cleanup:
    calculate and plot-tcc emit no warnings, and measured evaluation remains
    red only on STPU.
    """

    def test_sensor_25_ge_preset_stays_warning_free_except_real_stpu_fail(self):
        mock_session = MagicMock()

        def fake_execute(stmt, params=None):
            sql_text = str(stmt) if not isinstance(stmt, str) else stmt
            result = MagicMock()
            if "vw_sensor_calc_context" in sql_text:
                row = MagicMock()
                row._mapping = {"rating": 800.0}
                result.fetchone.return_value = row
            elif "fn_calculate_test_currents" in sql_text:
                row = MagicMock()
                row.result = GE_PRESET_CLEAN_CALC_DATA
                result.fetchone.return_value = row
            elif "FROM tcc.etu_ltd_bands" in sql_text:
                row = MagicMock()
                row._mapping = {"open_time": 6.0, "clear_time": None, "ordinal": 4, "is_default": False}
                result.fetchone.return_value = row
            elif "FROM tcc.etu_std_bands" in sql_text:
                row = MagicMock()
                row._mapping = {"open_time": 0.21, "clear_time": 0.31, "ordinal": 2, "is_default": False}
                result.fetchone.return_value = row
            elif "FROM tcc.etu_gfd_bands" in sql_text:
                row = MagicMock()
                row._mapping = {"open_time": 0.21, "clear_time": 0.31, "ordinal": 2, "is_default": False}
                result.fetchone.return_value = row
            else:
                result.fetchone.return_value = None
            return result

        mock_session.execute = MagicMock(side_effect=fake_execute)

        def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            tc = TestClient(app)
            req = {
                "sensor_id": 25,
                "plug_rating": 800.0,
                "ltpu_setting": 0.8,
                "ltd_setting": 6.0,
                "stpu_setting": 4.0,
                "std_setting": 0.21,
                "inst_setting": 10.0,
                "gfpu_setting": 0.4,
                "gfd_setting": 0.21,
                "maint_mode": False,
                "measurements": [
                    {"element": "LTPU", "measured_current": 650.0},
                    {"element": "STPU", "measured_current": 3100.0},
                    {"element": "GFPU", "measured_current": 310.0},
                ],
                "include_nominal_curve": True,
                "include_expected_markers": True,
                "include_measured_markers": True,
            }

            patches, _ = _patch_calc_engine()
            with patches["pickup"], patches["ltd"], patches["ieee"]:
                calc_resp = tc.post("/api/v1/neta/calculate", json={k: v for k, v in req.items() if k != "measurements" and not k.startswith("include_")})
                plot_resp = tc.post("/api/v1/neta/plot-tcc", json=req)

            assert calc_resp.status_code == 200
            calc_body = calc_resp.json()
            assert calc_body["sensor_id"] == 25
            assert calc_body["sensor_desc"] == "800"
            assert calc_body["warnings"] == []
            calc_elements = {element["element"]: element for element in calc_body["elements"]}
            assert calc_elements["LTPU"]["test_current"] == 640.0
            assert calc_elements["STPU"]["test_current"] == 2560.0
            assert calc_elements["GFPU"]["test_current"] == 320.0
            assert calc_elements["LTD"]["delay_seconds"] == 6.0
            assert calc_elements["LTD"]["notes"] == "timing_source=band_table"

            assert plot_resp.status_code == 200
            plot_body = plot_resp.json()
            assert plot_body["warnings"] == []
            assert plot_body["meta"]["sensor_desc"] == "800"
            assert plot_body["meta"]["manufacturer"] == "GE"
            assert plot_body["meta"]["trip_type"] == "MVT RMS-9"
            assert plot_body["meta"]["trip_style"] == "ICCB"
            assert plot_body["meta"]["overall_pass"] is False
            assert len(plot_body["curves"]) == 8

            measured = {marker["element"]: marker for marker in plot_body["measured_markers"]}
            assert measured["LTPU"]["passed"] is True
            assert measured["STPU"]["passed"] is False
            assert measured["GFPU"]["passed"] is True
        finally:
            app.dependency_overrides.clear()

    def test_evaluate_pass_fail_propagation(self, client, base_request):
        """Evaluate overall_pass and per-element pass state propagate
        through to plot-tcc measured markers."""
        tc, _ = client
        req = {
            **base_request,
            "measurements": [
                {"element": "LTPU", "measured_current": 950.0},
                {"element": "STPU", "measured_current": 4850.0},
            ],
        }

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        body = resp.json()
        assert body["meta"]["overall_pass"] is True
        assert body["meta"]["maint_mode"] is False
        assert body["meta"]["plot_disclaimer"] is None
        assert body["meta"]["resolved_equipment"]["family"] == "etu"
        assert body["meta"]["resolved_equipment"]["resolved_id"] == f"sensor:{SENSOR_ID}"
        assert body["meta"]["resolved_equipment"]["trip_unit"]["label"] == "TestMfr · Electronic · LS-ETU-777"
        assert body["meta"]["resolved_equipment"]["rating_context"]["sensor_desc"] == "Test Sensor 777"

        # Per-element measured markers carry pass state
        ltpu_m = next(m for m in body["measured_markers"] if m["element"] == "LTPU")
        assert ltpu_m["passed"] is True
        assert ltpu_m["measured_current"] == 950.0

    def test_no_maint_disclaimer(self, client, base_request):
        """Normal mode must not produce MAINT disclaimer or badge."""
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        body = resp.json()
        assert body["meta"]["maint_mode"] is False
        assert body["meta"]["plot_disclaimer"] is None


class TestGoldenMaintSST:
    """GOLDEN: MAINT SST — maintenance mode with tolerance overrides.

    Locks the MAINT contract:
    - maint_mode = true in meta
    - plot_disclaimer present when maint_capable
    - maint_support_level propagated
    - MAINT-specific warnings survive merge
    - INST tolerances reflect maint overrides
    """

    def _make_maint_client(self):
        mock_session = MagicMock()
        mock_session.execute = MagicMock(
            side_effect=_make_fake_execute(
                calc_data=GOLDEN_MAINT_CALC_DATA,
                eval_data=GOLDEN_MAINT_EVAL_DATA,
            )
        )

        def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        return TestClient(app), mock_session

    def test_maint_disclaimer_present(self, base_request):
        """MAINT + maint_capable must produce the nominal-curve disclaimer."""
        tc, _ = self._make_maint_client()
        try:
            req = {**base_request, "maint_mode": True,
                   "measurements": None, "include_measured_markers": False}
            patches, _ = _patch_calc_engine()
            with patches["pickup"], patches["ltd"], patches["ieee"]:
                resp = tc.post("/api/v1/neta/plot-tcc", json=req)

            body = resp.json()
            assert body["meta"]["maint_mode"] is True
            assert body["meta"]["maint_capable"] is True
            assert body["meta"]["maint_support_level"] == "partial_inst_gfpu"
            assert body["meta"]["plot_disclaimer"] == \
                "Nominal curve shown; markers reflect maint-mode calculations"
        finally:
            app.dependency_overrides.clear()

    def test_maint_warnings_propagated(self, base_request):
        """MAINT plot warnings should reflect the calculate path only; the
        in-process evaluator should not reintroduce stale SQL warning text."""
        tc, _ = self._make_maint_client()
        try:
            req = {
                **base_request, "maint_mode": True,
                "measurements": [
                    {"element": "LTPU", "measured_current": 950.0},
                    {"element": "STPU", "measured_current": 4850.0},
                    {"element": "INST", "measured_current": 11500.0},
                ],
            }
            patches, _ = _patch_calc_engine()
            with patches["pickup"], patches["ltd"], patches["ieee"]:
                resp = tc.post("/api/v1/neta/plot-tcc", json=req)

            body = resp.json()
            # Calc warnings
            assert "Reduction factors not available — using 1.0" in body["warnings"]
            assert "GFPU maint calc inactive (-1) — using normal GFPU" in body["warnings"]
            assert "MAINT mode: INST tolerances from maint table (±10%)" not in body["warnings"]
        finally:
            app.dependency_overrides.clear()

    def test_maint_eval_pass_with_inst(self, base_request):
        """MAINT evaluate must propagate per-element pass for INST using
        maint tolerances."""
        tc, _ = self._make_maint_client()
        try:
            req = {
                **base_request, "maint_mode": True,
                "measurements": [
                    {"element": "INST", "measured_current": 11500.0},
                ],
            }
            patches, _ = _patch_calc_engine()
            with patches["pickup"], patches["ltd"], patches["ieee"]:
                resp = tc.post("/api/v1/neta/plot-tcc", json=req)

            body = resp.json()
            assert body["meta"]["overall_pass"] is True
            inst_m = next(m for m in body["measured_markers"] if m["element"] == "INST")
            assert inst_m["passed"] is True
            assert inst_m["measured_current"] == 11500.0
        finally:
            app.dependency_overrides.clear()


class TestGoldenDegradedPlugMismatch:
    """GOLDEN: Degraded — unmatched plug_rating warning propagation.

    Locks the degraded path:
    - Unmatched plug_rating produces a logged warning
    - Response still succeeds (200)
    - Additional warnings from calc data propagate
    """

    def test_plug_mismatch_warns_and_succeeds(self, client, base_request):
        """When plug_rating doesn't match any plug in the style,
        the route logs a warning and calc proceeds with plug_id=None."""
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        # calc data includes an extra degraded warning
        mock_session = MagicMock()
        mock_session.execute = MagicMock(
            side_effect=_make_fake_execute(calc_data=GOLDEN_DEGRADED_CALC_DATA)
        )

        def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            patches, mocks = _patch_calc_engine(
                plug_list=[{"id": 301, "value": 800}]  # No 1200 match
            )
            with patches["pickup"], patches["ltd"], patches["ieee"], \
                 patch("services.neta.router.logger") as mock_logger:
                resp = tc.post("/api/v1/neta/plot-tcc", json=req)

            assert resp.status_code == 200
            body = resp.json()

            # Route-level warning logged
            mock_logger.warning.assert_any_call(
                "plug_rating %s not found for sensor %s; "
                "PLUGTAP curves may be incorrect",
                PLUG_RATING, SENSOR_ID,
            )

            # Calc-level degraded warning propagated
            assert "plug_rating mismatch: using nominal curves only" in body["warnings"]

            # Response still has elements (graceful degradation, not failure)
            assert len(body["table_rows"]) > 0
        finally:
            app.dependency_overrides.clear()


class TestGoldenGFDRouting:
    """GOLDEN: GFD routing — ground fault delay uses distinct equation set.

    Locks the GFD contract:
    - GFD curves use equation_type='gfd', not 'std'
    - GFD ordinal comes from get_equation_info(sensor_id, 'gfd')
    - GFD time_dial comes from req.gfd_setting
    """

    def test_gfd_uses_distinct_equation_type(self, client, base_request):
        """GFD generate_curve calls must use equation_type='gfd' and
        the GFD-specific ordinal, not the STD equation set."""
        tc, _ = client
        req = {**base_request, "gfd_setting": 2.5,
               "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine(
            std_eqs=[{"ordinal": 3, "label": "Very Inverse", "in_out": 0}],
            gfd_eqs=[{"ordinal": 8, "label": "GFD Definite", "in_out": 0}],
        )
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200

        # STD calls use ordinal=3, GFD calls use ordinal=8
        all_calls = mocks["ieee_inst"].generate_curve.call_args_list
        std_calls = [c for c in all_calls
                     if c.kwargs.get("equation_type", "std") == "std"]
        gfd_calls = [c for c in all_calls
                     if c.kwargs.get("equation_type") == "gfd"]

        assert len(std_calls) == 2  # open + clear
        assert len(gfd_calls) == 2  # open + clear

        for c in std_calls:
            assert c.kwargs["ordinal"] == 3

        for c in gfd_calls:
            assert c.kwargs["ordinal"] == 8
            assert c.kwargs["time_dial"] == 2.5

    def test_gfd_curve_present_in_response(self, client, base_request):
        """GFD curve segment must appear as a distinct curve in the response."""
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        body = resp.json()
        gfd_curves = [c for c in body["curves"] if c["element"] == "GFD"]
        assert len(gfd_curves) == 2  # open + clear
        phases = {c["phase"] for c in gfd_curves}
        assert phases == {"open", "clear"}


class TestGoldenInverseDelay:
    """GOLDEN: Inverse delay — non-default STD time_dial routing.

    Locks the inverse-time contract:
    - STD time_dial flows from req.std_setting
    - Different time_dial values produce different curve calls
    - Default time_dial = 1.0 when std_setting is None
    """

    def test_nondefault_std_time_dial(self, client, base_request):
        """A high STD time_dial value (5.0) must flow through to curve
        generation, producing the correct slow-trip behavior."""
        tc, _ = client
        req = {**base_request, "std_setting": 5.0,
               "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        std_calls = [c for c in mocks["ieee_inst"].generate_curve.call_args_list
                     if c.kwargs.get("equation_type", "std") == "std"]
        for c in std_calls:
            assert c.kwargs["time_dial"] == 5.0

    def test_default_time_dial_is_1(self, client, base_request):
        """When std_setting is None, time_dial defaults to 1.0."""
        tc, _ = client
        req = {**base_request, "std_setting": None,
               "measurements": None, "include_measured_markers": False}

        patches, mocks = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        std_calls = [c for c in mocks["ieee_inst"].generate_curve.call_args_list
                     if c.kwargs.get("equation_type", "std") == "std"]
        for c in std_calls:
            assert c.kwargs["time_dial"] == 1.0


# ──────────────────────────────────────────────────────────────────
# Phase 4 Integration Tests — Tolerance Fields + Table Row Contract
# ──────────────────────────────────────────────────────────────────

class TestPhase4TableRowTolerances:
    """Phase 4: table_rows must carry explicit tolerance columns for both
    pickup (current limits) and delay (time limits) elements."""

    def test_pickup_rows_have_current_tolerance(self, client, base_request):
        """Pickup table rows must include limit_low and limit_high from calc data."""
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        body = resp.json()
        ltpu_row = next(r for r in body["table_rows"] if r["element"] == "LTPU")
        assert ltpu_row["kind"] == "pickup"
        assert ltpu_row["limit_low"] == 864.0
        assert ltpu_row["limit_high"] == 1056.0
        assert ltpu_row["setting"] == 0.8

        stpu_row = next(r for r in body["table_rows"] if r["element"] == "STPU")
        assert stpu_row["kind"] == "pickup"
        assert stpu_row["limit_low"] == 4320.0
        assert stpu_row["limit_high"] == 5280.0

        inst_row = next(r for r in body["table_rows"] if r["element"] == "INST")
        assert inst_row["kind"] == "pickup"
        assert inst_row["limit_low"] == 10800.0
        assert inst_row["limit_high"] == 13200.0

    def test_delay_rows_have_time_tolerance(self, client, base_request):
        """Delay table rows should carry time_limit_low/time_limit_high
        as ordered bounds around the expected delay time."""
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        body = resp.json()
        ltd_row = next(r for r in body["table_rows"] if r["element"] == "LTD")
        assert ltd_row["kind"] == "delay"
        if ltd_row["expected_time"] is not None:
            assert ltd_row["time_limit_low"] <= ltd_row["expected_time"]
            if ltd_row["time_limit_high"] is not None:
                assert ltd_row["time_limit_high"] >= ltd_row["time_limit_low"]
                assert ltd_row["time_limit_high"] >= ltd_row["expected_time"]

    def test_delay_rows_have_correct_kind(self, client, base_request):
        """All delay element rows must have kind='delay'."""
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        body = resp.json()
        delay_elements = {"LTD", "STD", "GFD"}
        for row in body["table_rows"]:
            if row["element"] in delay_elements:
                assert row["kind"] == "delay", f"{row['element']} should have kind='delay'"
            else:
                assert row["kind"] == "pickup", f"{row['element']} should have kind='pickup'"

    def test_measured_deviation_in_table_rows(self, client, base_request):
        """When measurements are provided, table rows carry deviation_pct."""
        tc, _ = client
        req = {
            **base_request,
            "measurements": [
                {"element": "LTPU", "measured_current": 950.0},
                {"element": "STPU", "measured_current": 4850.0},
            ],
        }

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        body = resp.json()
        ltpu_row = next(r for r in body["table_rows"] if r["element"] == "LTPU")
        assert ltpu_row["measured_current"] == 950.0
        assert ltpu_row["deviation_pct"] is not None
        assert ltpu_row["passed"] is True

    def test_calc_method_as_string(self, client, base_request):
        """calc_method should be a string even when the underlying value is an int."""
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        body = resp.json()
        ltpu_row = next(r for r in body["table_rows"] if r["element"] == "LTPU")
        assert ltpu_row["calc_method"] is not None
        assert isinstance(ltpu_row["calc_method"], str)
