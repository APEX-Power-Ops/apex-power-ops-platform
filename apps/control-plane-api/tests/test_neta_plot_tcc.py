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

def _avail_band_row(open_time=0.06, clear_time=0.13):
    """One delay-band row for the Screen-2-style availability list query
    (``_load_delay_band_settings``). Only ``open_time`` presence matters for the
    plot's delay-availability gate."""
    r = MagicMock()
    r._mapping = {
        "band": "x", "label": "x", "open_time": open_time,
        "clear_time": clear_time, "is_default": False,
    }
    return r


def _inveq_option_row(label):
    """One InvEq payload-row option for the ``_load_inveq_delay_settings`` query
    (``tcc.etu_{std,gfd}_equations``, in_out=2 rows): label = eq_desc, value = its
    numeric cast."""
    r = MagicMock()
    r._mapping = {"label": str(label), "value": float(label)}
    return r


def _make_fake_execute(calc_data=CALC_DATA, eval_data=EVAL_DATA, ltd_tol_rows=None,
                       avail_bands=("ltd", "std", "gfd"), inveq_payload=None,
                       trip_style_db=None, delay_routes=None, sensor_ltd_tol=None):
    """Return a side_effect function for Session.execute that returns
    deterministic payloads for the two SQL function calls.

    ``ltd_tol_rows`` mocks the per-sensor LTD time-tolerance query
    (``tcc.etu_ltd_params``); each row is a dict with ``curve_name``/``tol_lo``/
    ``tol_hi``. Default empty → no DB tol → the flagged generic window.

    ``sensor_ltd_tol`` mocks the sensor-level DS2_TOL pair query
    (``tcc.etu_sensors.ltd_tol_lo/hi`` — the native single-curve "LT Delay
    Tolerance Band", punch-list L11) as a ``(lo, hi)`` tuple or None.

    ``avail_bands`` controls the per-sensor delay-band *availability* list query
    (``_load_delay_band_settings``) that drives the plot's delay-availability gate:
    a delay element absent from this set returns an empty band list (the Screen-2
    "Not available" state), so the plot must not draw it even though the
    equation/param mocks would otherwise yield a curve.

    ``inveq_payload`` mocks the route-2 InvEq dial-option query against the
    equation tables: a dict like ``{"std": ["0.1", "0.2"], "gfd": [...]}`` whose
    labels become payload-row options (#119). Default None → no InvEq rows.

    ``trip_style_db`` mocks the sensor's DB trip-style label
    (``_sensor_trip_style_name``), which drives the Micrologic-6.0 carve-outs.

    ``delay_routes`` mocks the per-sensor SSTDelayCalc route-byte query
    (std_route / gfd_route / gfd_is_ansi). Defaults to direct-band routes
    (0/0/False) — the truthful model for the fake's band-table rows."""
    avail_bands = set(avail_bands or ())
    if delay_routes is None:
        delay_routes = {"std_route": 0, "gfd_route": 0, "gfd_is_ansi": False}
    call_count = {"n": 0}

    def fake_execute(stmt, params=None):
        sql_text = str(stmt) if not isinstance(stmt, str) else stmt
        result = MagicMock()
        if "tcc.etu_ltd_params" in sql_text:
            result.fetchall.return_value = list(ltd_tol_rows or [])
        elif "ltd_tol_lo" in sql_text:
            # Sensor-level DS2_TOL pair (tcc.etu_sensors.ltd_tol_lo/hi, L11).
            if sensor_ltd_tol is None:
                result.fetchone.return_value = None
            else:
                row = MagicMock()
                row._mapping = {
                    "ltd_tol_lo": sensor_ltd_tol[0],
                    "ltd_tol_hi": sensor_ltd_tol[1],
                }
                result.fetchone.return_value = row
        elif "vw_sensor_calc_context" in sql_text:
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
            if "AND ltd_setting = :setting" not in sql_text:
                # Screen-2 availability list query (drives the delay-availability gate).
                result.fetchall.return_value = (
                    [_avail_band_row(3.5, None)] if "ltd" in avail_bands else []
                )
            else:
                setting = (params or {}).get("setting")
                if setting != 3.5:
                    result.fetchone.return_value = None
                else:
                    row = MagicMock()
                    row._mapping = {"open_time": 3.5, "clear_time": 3.0, "ordinal": 2, "is_default": False}
                    result.fetchone.return_value = row
        elif "stpu_delay_calc_code" in sql_text:
            # Per-sensor SSTDelayCalc route bytes (G4 trust classification).
            row = MagicMock()
            row._mapping = dict(delay_routes)
            result.fetchone.return_value = row
        elif "tcc.etu_std_equations" in sql_text:
            result.fetchall.return_value = [
                _inveq_option_row(lbl)
                for lbl in (inveq_payload or {}).get("std", [])
            ]
        elif "tcc.etu_gfd_equations" in sql_text:
            result.fetchall.return_value = [
                _inveq_option_row(lbl)
                for lbl in (inveq_payload or {}).get("gfd", [])
            ]
        elif "FROM tcc.etu_sensors" in sql_text and "trip_styles" in sql_text:
            if trip_style_db is None:
                result.fetchone.return_value = None
            else:
                row = MagicMock()
                row._mapping = {"style": trip_style_db}
                result.fetchone.return_value = row
        elif "tcc.etu_std_bands" in sql_text:
            if "AND std_open = :setting" not in sql_text:
                result.fetchall.return_value = (
                    [_avail_band_row(0.06, 0.13)] if "std" in avail_bands else []
                )
            else:
                setting = (params or {}).get("setting")
                if setting != 2.0:
                    result.fetchone.return_value = None
                else:
                    row = MagicMock()
                    row._mapping = {"open_time": 2.0, "clear_time": 2.5, "ordinal": 1, "is_default": True}
                    result.fetchone.return_value = row
        elif "tcc.etu_gfd_bands" in sql_text:
            if "AND gfd_open = :setting" not in sql_text:
                result.fetchall.return_value = (
                    [_avail_band_row(0.06, 0.13)] if "gfd" in avail_bands else []
                )
            else:
                setting = (params or {}).get("setting")
                if setting != 1.5:
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
                             equation_type='std', gf_basis_ratio=None):
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
        # LTD time is the I2t long-time characteristic anchored at 6x Ir (the stored
        # band setting = the trip time at 6x). At the NETA default 3x the bands table
        # now agrees with the Screen-3 curve: t = setting * (6/3)^2 = 3.5 * 4 = 14.0 s.
        assert ltd["multiplier"] == 3.0
        assert ltd["delay_seconds"] == 14.0
        # No per-sensor LTD tolerance is mocked here, so the band is the flagged
        # generic −30%/+0% estimate (9.8 = 0.7·14, 14.0 = nominal).
        assert ltd["time_limit_low"] == pytest.approx(9.8)
        assert ltd["time_limit_high"] == 14.0
        assert ltd["notes"] == "timing_source=ltd_reference_window_generic"

        inst = elements["INST"]
        assert inst["kind"] == "pickup"
        assert inst["limit_low"] == 10800.0
        assert inst["delay_seconds"] == 0.05

    def test_calculate_bigger_delay_test_multiple_scales_i2t_and_inject(self, client):
        """The operator-selectable 'bigger delay test current' option: a larger LTD
        test multiple shortens the expected trip time by the I2t law and scales the
        inject current. At 6x Ir (the band reference) the expected time == the stored
        dial setting; at 3x it is 4x longer. The inject current = multiple x pickup."""
        tc, _ = client

        def _calc(ltd_mult):
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
                "ltd_test_multiple": ltd_mult,
                "maint_mode": False,
            }
            patches, _ = _patch_calc_engine()
            with patches["pickup"], patches["ltd"], patches["ieee"]:
                resp = tc.post("/api/v1/neta/calculate", json=req)
            assert resp.status_code == 200
            return {e["element"]: e for e in resp.json()["elements"]}

        # 6x = the long-time band reference: expected time equals the dial setting.
        ltd6 = _calc(6.0)["LTD"]
        assert ltd6["multiplier"] == 6.0
        assert ltd6["delay_seconds"] == pytest.approx(3.5)            # 3.5 * (6/6)^2
        assert ltd6["test_current"] == pytest.approx(5760.0)         # 6 * 960 LTPU pickup
        assert ltd6["time_limit_low"] == pytest.approx(2.45)          # 0.7 * 3.5 (generic)
        assert ltd6["time_limit_high"] == pytest.approx(3.5)
        assert ltd6["notes"] == "timing_source=ltd_reference_window_generic"
        assert ltd6["trust"] == "db"

        # 3x trips 4x slower (I2t), and injects half the 6x current.
        ltd3 = _calc(3.0)["LTD"]
        assert ltd3["delay_seconds"] == pytest.approx(14.0)          # 3.5 * (6/3)^2
        assert ltd3["test_current"] == pytest.approx(2880.0)         # 3 * 960
        assert ltd3["delay_seconds"] == pytest.approx(ltd6["delay_seconds"] * 4)

    def _calc_ltd_with_tol(self, ltd_tol_rows, sensor_ltd_tol=None):
        mock_session = MagicMock()
        mock_session.execute = MagicMock(
            side_effect=_make_fake_execute(
                ltd_tol_rows=ltd_tol_rows, sensor_ltd_tol=sensor_ltd_tol
            )
        )

        def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            tc = TestClient(app)
            req = {
                "sensor_id": SENSOR_ID, "plug_rating": PLUG_RATING,
                "ltpu_setting": 0.8, "ltd_setting": 3.5, "stpu_setting": 4.0,
                "std_setting": 2.0, "inst_setting": 10.0, "gfpu_setting": 0.4,
                "gfd_setting": 1.5, "maint_mode": False,
            }
            patches, _ = _patch_calc_engine()
            with patches["pickup"], patches["ltd"], patches["ieee"]:
                resp = tc.post("/api/v1/neta/calculate", json=req)
            assert resp.status_code == 200
            return {e["element"]: e for e in resp.json()["elements"]}["LTD"]
        finally:
            app.dependency_overrides.clear()

    def test_calculate_ltd_uses_db_tolerance_band(self):
        """A per-sensor LTD tolerance (tcc.etu_ltd_params) yields a real
        nominal·(1±tol) band — not the generic −30/+0 — and an unflagged source.
        nominal = 3.5·(6/3)² = 14.0 s; tol −20/+0 → 11.2 .. 14.0 s."""
        ltd = self._calc_ltd_with_tol(
            [{"curve_name": "I^2T", "tol_lo": -20.0, "tol_hi": 0.0}]
        )
        assert ltd["delay_seconds"] == pytest.approx(14.0)
        assert ltd["time_limit_low"] == pytest.approx(11.2)   # 14 · 0.80
        assert ltd["time_limit_high"] == pytest.approx(14.0)  # 14 · 1.00
        assert ltd["notes"] == "timing_source=ltd_reference_window"

    def test_calculate_ltd_tolerance_prefers_i2t_curve_row(self):
        """LTD tolerance is per curve TYPE; the I²t reference window must pair
        with the I^2T row, not the IEEE/IEC ±10% rows that share the sensor."""
        ltd = self._calc_ltd_with_tol([
            {"curve_name": "IEEE V Inv", "tol_lo": -10.0, "tol_hi": 10.0},
            {"curve_name": "I^2T", "tol_lo": -20.0, "tol_hi": 0.0},
            {"curve_name": "IEC-A (N Inv)", "tol_lo": -10.0, "tol_hi": 10.0},
        ])
        # I^2T (−20/+0) chosen, not IEEE ±10 (which would give 12.6 .. 15.4).
        assert ltd["time_limit_low"] == pytest.approx(11.2)
        assert ltd["time_limit_high"] == pytest.approx(14.0)
        assert ltd["notes"] == "timing_source=ltd_reference_window"

    def test_calculate_ltd_sensor_level_tolerance_band(self):
        """L11: a sensor with NO per-curve LTD params rows serves its
        sensor-level DS2_TOL pair (``etu_sensors.ltd_tol_lo/hi`` — the native
        single-curve "LT Delay Tolerance Band") as a REAL band, not the flagged
        generic −30/+0. nominal = 3.5·(6/3)² = 14.0 s; −20/+0 → 11.2 .. 14.0 s."""
        ltd = self._calc_ltd_with_tol([], sensor_ltd_tol=(-20.0, 0.0))
        assert ltd["delay_seconds"] == pytest.approx(14.0)
        assert ltd["time_limit_low"] == pytest.approx(11.2)
        assert ltd["time_limit_high"] == pytest.approx(14.0)
        assert ltd["notes"] == "timing_source=ltd_reference_window"

    def test_calculate_ltd_curve_rows_outrank_sensor_level_pair(self):
        """Per-curve params rows (the finer DatSensorSec2 grain) keep
        precedence over the sensor-level inline pair: −26.83/+0 from the I^2T
        row wins over the sensor's −20/+0."""
        ltd = self._calc_ltd_with_tol(
            [{"curve_name": "I^2T", "tol_lo": -26.83, "tol_hi": 0.0}],
            sensor_ltd_tol=(-20.0, 0.0),
        )
        assert ltd["time_limit_low"] == pytest.approx(14.0 * (1 - 0.2683))
        assert ltd["time_limit_high"] == pytest.approx(14.0)
        assert ltd["notes"] == "timing_source=ltd_reference_window"

    def test_calculate_ltd_disagreeing_curve_rows_do_not_fall_to_sensor_pair(self):
        """Disagreeing multi-curve rows without an I^2T row stay GENERIC: the
        sensor-level inline pair is stale-prone on multi-curve sensors (the
        per-curve grain governs natively) and must not paper over the ambiguity."""
        ltd = self._calc_ltd_with_tol(
            [
                {"curve_name": "IEEE V Inv", "tol_lo": -10.0, "tol_hi": 10.0},
                {"curve_name": "I^4T", "tol_lo": -38.81, "tol_hi": 9.7},
            ],
            sensor_ltd_tol=(-20.0, 0.0),
        )
        assert ltd["time_limit_low"] == pytest.approx(9.8)   # 0.7 · 14 (generic)
        assert ltd["time_limit_high"] == pytest.approx(14.0)
        assert ltd["notes"] == "timing_source=ltd_reference_window_generic"

    def test_load_ltd_time_tolerance_branches(self):
        """Helper: prefer I^2T row; else accept only an unambiguous sensor-wide
        value; else (no rows at all) the sensor-level DS2_TOL pair; else None
        (→ generic window)."""
        from services.neta.router import _load_ltd_time_tolerance

        def _db(rows, sensor_row=None):
            s = MagicMock()

            def _exec(stmt, params=None):
                res = MagicMock()
                if "etu_ltd_params" in str(stmt):
                    res.fetchall.return_value = rows
                else:
                    if sensor_row is None:
                        res.fetchone.return_value = None
                    else:
                        r = MagicMock()
                        r._mapping = {
                            "ltd_tol_lo": sensor_row[0],
                            "ltd_tol_hi": sensor_row[1],
                        }
                        res.fetchone.return_value = r
                return res

            s.execute = MagicMock(side_effect=_exec)
            return s

        # prefers the I^2T curve type over IEEE rows
        assert _load_ltd_time_tolerance(_db([
            {"curve_name": "IEEE V Inv", "tol_lo": -10.0, "tol_hi": 10.0},
            {"curve_name": "I^2T", "tol_lo": -26.83, "tol_hi": 0.0},
        ]), 1) == pytest.approx((-26.83, 0.0))
        # no I^2T, all rows agree → that value
        assert _load_ltd_time_tolerance(_db([
            {"curve_name": "IEEE V Inv", "tol_lo": -10.0, "tol_hi": 10.0},
            {"curve_name": "IEC-A", "tol_lo": -10.0, "tol_hi": 10.0},
        ]), 1) == pytest.approx((-10.0, 10.0))
        # no I^2T, rows disagree → None even when a sensor-level pair exists
        # (the inline pair is stale-prone on multi-curve sensors)
        assert _load_ltd_time_tolerance(_db([
            {"curve_name": "IEEE V Inv", "tol_lo": -10.0, "tol_hi": 10.0},
            {"curve_name": "I^4T", "tol_lo": -38.81, "tol_hi": 9.7},
        ], sensor_row=(-20.0, 0.0)), 1) is None
        # no rows at all + no sensor pair → None
        assert _load_ltd_time_tolerance(_db([]), 1) is None

    def test_load_ltd_time_tolerance_sensor_level_fallback(self):
        """L11: with NO per-curve rows, the sensor-level DS2_TOL pair governs
        (native single-curve layout), subject to hygiene gates."""
        from services.neta.router import _load_ltd_time_tolerance

        def _db(sensor_row):
            s = MagicMock()

            def _exec(stmt, params=None):
                res = MagicMock()
                if "etu_ltd_params" in str(stmt):
                    res.fetchall.return_value = []
                else:
                    if sensor_row is None:
                        res.fetchone.return_value = None
                    else:
                        r = MagicMock()
                        r._mapping = {
                            "ltd_tol_lo": sensor_row[0],
                            "ltd_tol_hi": sensor_row[1],
                        }
                        res.fetchone.return_value = r
                return res

            s.execute = MagicMock(side_effect=_exec)
            return s

        # the modal real pair → served
        assert _load_ltd_time_tolerance(_db((-20.0, 0.0)), 1) == pytest.approx((-20.0, 0.0))
        # a one-sided-positive band is legitimate (cf. the 0/+50 population)
        assert _load_ltd_time_tolerance(_db((0.0, 50.0)), 1) == pytest.approx((0.0, 50.0))
        # hygiene gates: (0,0) means "no band entered"; inverted pair invalid;
        # a lo ≤ −100% factor is no longer a multiplicative band; nulls invalid
        assert _load_ltd_time_tolerance(_db((0.0, 0.0)), 1) is None
        assert _load_ltd_time_tolerance(_db((10.0, -5.0)), 1) is None
        assert _load_ltd_time_tolerance(_db((-100.0, 0.0)), 1) is None
        assert _load_ltd_time_tolerance(_db((None, 0.0)), 1) is None
        assert _load_ltd_time_tolerance(_db(None), 1) is None

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


class TestPlugRatingPlugTruncationBug:
    """§110 regression: rating plugs that exceed the *nominal* sensor rating are
    still valid — EasyPower's per-sensor ``tcc.etu_plugs`` (sourced 1:1 from
    ``DatPlugs``) is authoritative. e.g. sensor 17223 is "6000(I^4T)" (nominal
    rating 6000 A) yet legitimately offers a 6300 A rating plug. Such plugs must
    not be dropped from the served list, nor 422'd on /calculate."""

    def test_settings_endpoint_serves_rating_plug_above_nominal(self):
        # Serving must trust the authoritative plug table, not clamp by nominal rating.
        def fake(stmt, params=None):
            sql = str(stmt)
            result = MagicMock()
            if "tcc.etu_plugs" in sql:
                rows = []
                for v in (5000.0, 6000.0, 6300.0):
                    r = MagicMock()
                    r._mapping = {"value": v}
                    rows.append(r)
                result.fetchall.return_value = rows
            elif "vw_sensor_calc_context" in sql:
                row = MagicMock()
                row._mapping = {
                    "rating": 6000.0,
                    "trip_style_id": 1419,
                    "ltpu_calc": 1,
                    "stpu_calc": 1,
                    "inst_calc": 1,
                    "gfpu_calc": 7,
                }
                result.fetchone.return_value = row
            else:
                result.fetchall.return_value = []
                result.fetchone.return_value = None
            return result

        mock_session = MagicMock()
        mock_session.execute = MagicMock(side_effect=fake)

        def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            with patch(
                "services.neta.router._expand_pickup_values",
                side_effect=lambda db, sid, ctx, kind, vals: vals,
            ), patch(
                "services.neta.router.setting_catalog.lookup", return_value=None
            ):
                tc = TestClient(app)
                resp = tc.get("/api/v1/neta/settings/17223")
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200, resp.text
        plug_values = resp.json()["plug_values"]
        assert 6300.0 in plug_values, plug_values
        assert plug_values == [5000.0, 6000.0, 6300.0]

    def _enforce_db(self, rating, max_plug):
        def fake(stmt, params=None):
            sql = str(stmt)
            result = MagicMock()
            if "vw_sensor_calc_context" in sql:
                row = MagicMock()
                row._mapping = {"rating": rating}
                result.fetchone.return_value = row
            elif "tcc.etu_plugs" in sql:
                row = MagicMock()
                row._mapping = {"max_plug": max_plug}
                result.fetchone.return_value = row
            else:
                result.fetchone.return_value = None
            return result

        db = MagicMock()
        db.execute = MagicMock(side_effect=fake)
        return db

    def test_enforce_allows_rating_plug_above_nominal(self):
        from services.neta.router import _enforce_plug_within_sensor_rating

        db = self._enforce_db(rating=6000.0, max_plug=6300.0)
        # 6300 A is the sensor's max valid plug → must NOT raise though > nominal 6000.
        _enforce_plug_within_sensor_rating(17223, 6300.0, db)

    def test_enforce_rejects_plug_above_max_valid_plug(self):
        from fastapi import HTTPException
        from services.neta.router import _enforce_plug_within_sensor_rating

        db = self._enforce_db(rating=6000.0, max_plug=6300.0)
        with pytest.raises(HTTPException) as exc:
            _enforce_plug_within_sensor_rating(17223, 9999.0, db)
        assert exc.value.status_code == 422

    def test_enforce_no_plugs_falls_back_to_nominal_rating(self):
        from fastapi import HTTPException
        from services.neta.router import _enforce_plug_within_sensor_rating

        db = self._enforce_db(rating=6000.0, max_plug=None)
        # No plug set on file → fall back to the nominal rating bound.
        _enforce_plug_within_sensor_rating(17223, 5000.0, db)
        with pytest.raises(HTTPException) as exc:
            _enforce_plug_within_sensor_rating(17223, 7000.0, db)
        assert exc.value.status_code == 422


class TestBridgeRatingWarning:
    """Interim safety flag for the SST-bridge scramble bug: when a breaker frame's
    nameplate rating is clearly inconsistent with the sensor ratings the bridge maps
    it to (e.g. a 2500 A frame offered only 60-225 A sensors), warn the tech rather
    than let them unknowingly test against the wrong sensor. Conservative — only
    flags clear mismatches; skips frames whose name carries no parseable amp rating."""

    def test_flags_sensors_far_below_frame_rating(self):
        from services.neta.router import _bridge_rating_warning
        # PDG6-P PXR 2500 frame, but bridge maps it to 60-225 A sensors (the live bug).
        w = _bridge_rating_warning("PDG6-P PXR 2500", [60.0, 100.0, 150.0, 225.0])
        assert w is not None
        assert "2500" in w and "225" in w

    def test_flags_sensors_far_above_frame_rating(self):
        from services.neta.router import _bridge_rating_warning
        # PDG3-F PXR 600A frame mapped to NRX 800-4000 A sensors.
        w = _bridge_rating_warning("PDG3-F PXR 600A", [800.0, 1600.0, 4000.0])
        assert w is not None
        assert "600" in w

    def test_consistent_mapping_no_warning(self):
        from services.neta.router import _bridge_rating_warning
        # PDG2 ~250 A frame with 60-225 A sensors — physically consistent.
        assert _bridge_rating_warning("PDG2-F PXR 250", [60.0, 100.0, 225.0]) is None

    def test_unparseable_frame_rating_no_warning(self):
        from services.neta.router import _bridge_rating_warning
        # No amp >= 50 in the name (poles only) -> cannot judge -> no false flag.
        assert _bridge_rating_warning("PDG2-F PXR 2/3P", [60.0, 225.0]) is None
        assert _bridge_rating_warning(None, [60.0, 225.0]) is None
        assert _bridge_rating_warning("PDG6-P PXR 2500", []) is None


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
# Test 5b: Delay-availability gating (plot ⇄ Screen-2 consistency)
# ──────────────────────────────────────────────────

class TestDelayAvailabilityGating:
    """The TCC plot must match Screen-2 availability: a delay element (LTD/STD/GFD)
    whose per-sensor delay-band inventory is empty must NOT be drawn — neither as a
    swept curve nor as a test-point marker/table row — even though the independent
    equation/param tables may still carry coefficients for it.

    Real case: Square D Micrologic sensors carry STD/GFD *equations* (so the engine
    would gladly draw an STD/GFD curve) but no STD/GFD *band settings*, so Screen 2
    reports them "Not available". The plot was drawing them anyway — the operator's
    "don't plot elements that are disabled by default"."""

    def _plot_with_avail(self, base_request, avail_bands):
        mock_session = MagicMock()
        mock_session.execute = MagicMock(
            side_effect=_make_fake_execute(avail_bands=avail_bands)
        )

        def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            tc = TestClient(app)
            req = {**base_request, "measurements": None, "include_measured_markers": False}
            patches, _ = _patch_calc_engine()
            with patches["pickup"], patches["ltd"], patches["ieee"]:
                resp = tc.post("/api/v1/neta/plot-tcc", json=req)
            assert resp.status_code == 200, resp.text
            return resp.json()
        finally:
            app.dependency_overrides.clear()

    def test_std_gfd_suppressed_when_bands_absent(self, base_request):
        # Micrologic-like sensor: only LTD has band settings; STD/GFD "Not available".
        body = self._plot_with_avail(base_request, avail_bands={"ltd"})

        curve_els = {c["element"] for c in body["curves"]}
        assert "STD" not in curve_els, curve_els
        assert "GFD" not in curve_els, curve_els
        assert "INST" in curve_els  # pickup-driven element, unaffected

        marker_els = {m["element"] for m in body["expected_markers"]}
        assert "STD" not in marker_els, marker_els
        assert "GFD" not in marker_els, marker_els
        assert "LTD" in marker_els  # LTD bands present → still shown

        row_els = {r["element"] for r in body["table_rows"]}
        assert "STD" not in row_els
        assert "GFD" not in row_els

    def test_all_delays_shown_when_bands_present(self, base_request):
        body = self._plot_with_avail(base_request, avail_bands={"ltd", "std", "gfd"})

        curve_els = {c["element"] for c in body["curves"]}
        assert {"LTD", "STD", "GFD", "INST"} <= curve_els, curve_els

        marker_els = {m["element"] for m in body["expected_markers"]}
        assert {"LTD", "STD", "GFD"} <= marker_els, marker_els

    def test_available_delay_elements_helper(self):
        from services.neta.router import _available_delay_elements

        db = MagicMock()
        db.execute = MagicMock(side_effect=_make_fake_execute(avail_bands={"ltd", "gfd"}))
        assert _available_delay_elements(db, SENSOR_ID) == {"ltd", "gfd"}


# ──────────────────────────────────────────────────
# Test 5c: Micrologic validated I²t long-time synthesis ("curves per the PXR2")
# ──────────────────────────────────────────────────

class TestMicrologicLongtimeI2t:
    """Square D Micrologic (and any trip unit with LTD bands but no
    ``etu_ltd_params`` curve method) must still render the long-time sweep — the
    published I²t characteristic t(I) = tr·(6·Ir/I)² (the validated §111
    reference-window law, native-CIxt-oracle bit-exact). Per the Eaton-PXR2
    pattern: serve the validated characteristic where EasyPower's record lacks the
    curve method; cited, nothing fabricated. Only when no DB LTD curve was produced
    and only for the Micrologic family (the validated I²t long-time)."""

    def test_synthesize_longtime_i2t_obeys_i2t_law(self):
        from services.neta.router import _synthesize_longtime_i2t

        pts = _synthesize_longtime_i2t(2000.0, 0.5, 8000.0)
        assert len(pts) >= 8
        # Monotonic: trip time falls as current rises.
        times = [p.seconds for p in pts]
        assert times == sorted(times, reverse=True)
        # I²t invariant t·I² = tr·(6·Ir)² away from any min-time clamp.
        ref = 0.5 * (6 * 2000.0) ** 2
        for p in pts:
            if p.seconds > 0.01:
                assert p.seconds * p.amps ** 2 == pytest.approx(ref, rel=1e-6)
        # All points within the swept current band [>Ir, upper].
        assert all(2000.0 < p.amps <= 8000.0 + 1e-6 for p in pts)

    def test_synthesize_longtime_i2t_guards(self):
        from services.neta.router import _synthesize_longtime_i2t
        assert _synthesize_longtime_i2t(0.0, 0.5, 8000.0) == []
        assert _synthesize_longtime_i2t(2000.0, 0.0, 8000.0) == []
        assert _synthesize_longtime_i2t(2000.0, 0.5, 1000.0) == []  # upper below pickup

    def test_plot_synthesizes_ltd_for_micrologic_without_params(self, client, base_request):
        tc, _ = client
        req = {**base_request, "trip_unit_style_name": "Micrologic 6.0A",
               "measurements": None, "include_measured_markers": False}
        # No DB curve method (Micrologic: etu_ltd_params empty) but LTD bands exist.
        patches, _ = _patch_calc_engine(ltd_info=[])
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        body = resp.json()
        ltd = [c for c in body["curves"] if c["element"] == "LTD"]
        assert ltd, body["curves"]
        pts = ltd[0]["points"]
        assert len(pts) >= 8
        ts = [p["seconds"] for p in pts]
        assert ts == sorted(ts, reverse=True)

    def test_no_synthesis_for_non_micrologic_without_params(self, client, base_request):
        tc, _ = client
        req = {**base_request, "trip_unit_style_name": "Generic PCB",
               "measurements": None, "include_measured_markers": False}
        patches, _ = _patch_calc_engine(ltd_info=[])
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        body = resp.json()
        assert not [c for c in body["curves"] if c["element"] == "LTD"]

    def test_resolve_longtime_tr_clear(self):
        """The clear-side reference time = the matched band's clear_time (the LTD
        dial IS the band's open_time). No matching band / no clear_time → None
        (no clear basis — honest, don't guess another band's)."""
        from services.neta.router import _resolve_longtime_tr_clear
        bands = [
            {"open_time": 2.0, "clear_time": 2.6, "is_default": True},
            {"open_time": 4.0, "clear_time": 5.2, "is_default": False},
            {"open_time": 8.0, "clear_time": None, "is_default": False},
        ]
        assert _resolve_longtime_tr_clear(4.0, bands) == 5.2
        assert _resolve_longtime_tr_clear(None, bands) == 2.6  # default band
        assert _resolve_longtime_tr_clear(3.0, bands) is None  # unmatched dial
        assert _resolve_longtime_tr_clear(8.0, bands) is None  # band has no clear
        assert _resolve_longtime_tr_clear(None, []) is None

        # SAME-BAND law (adversarial review, #123): with no dial and no default,
        # the clear basis must come from the band that supplied tr (the first
        # usable open_time — mirroring _resolve_longtime_tr), NEVER from a later
        # band that happens to carry a clear (a cross-band pair is a band that
        # does not exist in the data).
        nodef = [
            {"open_time": 2.0, "clear_time": None, "is_default": False},
            {"open_time": 4.0, "clear_time": 5.2, "is_default": False},
        ]
        assert _resolve_longtime_tr_clear(None, nodef) is None
        nodef2 = [
            {"open_time": None, "clear_time": 9.9, "is_default": False},
            {"open_time": 4.0, "clear_time": 5.2, "is_default": False},
        ]
        assert _resolve_longtime_tr_clear(None, nodef2) == 5.2  # tr's own band

        # Legacy-shim guard: prod etu_ltd_bands is the legacy shape and
        # _normalize_ltd_band_rows(legacy=True) DUPLICATES open_time into
        # clear_time — equality means no independent clear basis; serving it
        # would draw a fabricated coincident boundary and suppress the
        # open-only honesty note.
        shim = [{"open_time": 4.0, "clear_time": 4.0, "is_default": True}]
        assert _resolve_longtime_tr_clear(4.0, shim) is None
        assert _resolve_longtime_tr_clear(None, shim) is None

    def test_plot_synthesizes_ltd_clear_for_micrologic(self, client, base_request):
        """The synthesized long-time serves BOTH boundaries: open at tr (the dial)
        and clear at the matched band's clear_time, same I²t law."""
        tc, _ = client
        req = {**base_request, "trip_unit_style_name": "Micrologic 6.0A",
               "measurements": None, "include_measured_markers": False}
        patches, _ = _patch_calc_engine(ltd_info=[])
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        body = resp.json()
        ids = [c["id"] for c in body["curves"] if c["element"] == "LTD"]
        assert ids == ["ltd_open", "ltd_clear"], ids
        clear = next(c for c in body["curves"] if c["id"] == "ltd_clear")
        assert clear["phase"] == "clear" and clear["line_style"] == "dashed"
        opn = next(c for c in body["curves"] if c["id"] == "ltd_open")
        # base_request dials tr=3.5 → fixture band B (open 3.5 / clear 3.0): the
        # clear curve is the same I²t law at the band's clear_time, so away from
        # the min-time clamp the pointwise ratio is clear/open = 3.0/3.5.
        for po, pc in zip(opn["points"], clear["points"]):
            if po["seconds"] > 0.01 and pc["seconds"] > 0.01:
                assert pc["seconds"] / po["seconds"] == pytest.approx(3.0 / 3.5, rel=1e-6)

    def test_no_double_ltd_when_db_params_present(self, client, base_request):
        # Micrologic-labelled but DB params present → use the DB curve, don't also synthesize.
        tc, _ = client
        req = {**base_request, "trip_unit_style_name": "Micrologic 6.0A",
               "measurements": None, "include_measured_markers": False}
        patches, _ = _patch_calc_engine()  # default ltd_info present + ltd_curve
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        body = resp.json()
        assert len([c for c in body["curves"] if c["id"] == "ltd_open"]) == 1


# ──────────────────────────────────────────────────
# Test 5d: Micrologic STD/GFD route-1 (I2X) composite curve ("both delays built in")
# ──────────────────────────────────────────────────

class TestMicrologicI2XComposite:
    """Micrologic STD and GFD are NOT pure definite-time — each has an I²t-ON ramp
    AND an I²t-OFF definite floor (the dial's `I²t on/off`). The composite is the
    validated etu_ixt rule t = max(Iˣt ramp, floor), swept across current. M
    references Ir for STD (×Ir datasheet axis) and In for GFD (×In axis); the band's
    i_open anchor is where the ramp meets the floor (10×Ir / 1×In on the 6.0A)."""

    def test_synthesize_i2x_composite_ramp_then_floor(self):
        from services.neta.router import _synthesize_i2x_delay_curve

        band = {"i2x": 2, "i_open": 10, "t_open": 0.16, "floor_open": 0.14}
        # STD: M = I/Ir, Ir=2000, sweep Isd=8000 .. 24000 (past the 10×Ir=20000 knee).
        pts = _synthesize_i2x_delay_curve(band, 2.0, 2000.0, 8000.0, 24000.0)
        assert len(pts) >= 16
        times = [p.seconds for p in pts]
        assert times == sorted(times, reverse=True)  # ramp descends, then flat
        for p in pts:
            ramp = 0.16 * (10.0 * 2000.0 / p.amps) ** 2
            assert p.seconds == pytest.approx(max(ramp, 0.14), rel=1e-6)
        assert pts[-1].seconds == pytest.approx(0.14)  # clamped to the floor at high current

    def test_synthesize_i2x_flat_band_is_definite_time(self):
        from services.neta.router import _synthesize_i2x_delay_curve
        band = {"i2x": 0, "i_open": None, "t_open": None, "floor_open": 0.1}  # I²t OFF
        pts = _synthesize_i2x_delay_curve(band, 2.0, 2000.0, 8000.0, 16000.0)
        assert pts and all(p.seconds == pytest.approx(0.1) for p in pts)

    def test_synthesize_i2x_clear_phase_uses_clear_anchors(self):
        """phase="clear" sweeps the band's CLEAR block (i_clear/t_clear anchor +
        floor_clear) through the same native CIxt kernel — open and clear are
        symmetric blocks (SetSTDB_*Delay{Open,Clear}), so the clear boundary is
        max(clear ramp, clear floor). Gives the composite band real width."""
        from services.neta.router import _synthesize_i2x_delay_curve

        band = {"i2x": 2, "i_open": 10, "t_open": 0.16, "floor_open": 0.14,
                "i_clear": 10, "t_clear": 0.20, "floor_clear": 0.20}
        open_pts = _synthesize_i2x_delay_curve(band, 2.0, 2000.0, 8000.0, 24000.0)
        clear_pts = _synthesize_i2x_delay_curve(
            band, 2.0, 2000.0, 8000.0, 24000.0, phase="clear")
        assert len(clear_pts) == len(open_pts) >= 16
        for p in clear_pts:
            ramp = 0.20 * (10.0 * 2000.0 / p.amps) ** 2
            assert p.seconds == pytest.approx(max(ramp, 0.20), rel=1e-6)
        # Total-clear sits above min-trip pointwise — the band has real width.
        for po, pc in zip(open_pts, clear_pts):
            assert pc.seconds > po.seconds

    def test_synthesize_i2x_clear_phase_withheld_without_anchors(self):
        """A band with no clear-side data serves NO clear curve (honest zero-width
        — the open-only legend note), never a copy of the open block."""
        from services.neta.router import _synthesize_i2x_delay_curve
        band = {"i2x": 2, "i_open": 10, "t_open": 0.16, "floor_open": 0.14,
                "i_clear": None, "t_clear": None, "floor_clear": None}
        assert _synthesize_i2x_delay_curve(
            band, 2.0, 2000.0, 8000.0, 24000.0, phase="clear") == []

    def test_synthesize_i2x_clear_flat_band(self):
        from services.neta.router import _synthesize_i2x_delay_curve
        band = {"i2x": 0, "floor_open": 0.02, "floor_clear": 0.08}  # GF "Off" dial
        pts = _synthesize_i2x_delay_curve(
            band, 2.0, 2000.0, 8000.0, 16000.0, phase="clear")
        assert pts and all(p.seconds == pytest.approx(0.08) for p in pts)

    def test_synthesize_i2x_clear_composite_partial_data_withheld(self):
        """A composite (i2x=2) band whose CLEAR side has a floor but no ramp anchors
        (282 STD + 211 GFD prod rows) must serve NO clear curve: evaluating only the
        floor would draw a flat clear boundary BELOW the open ramp at low current —
        a malformed inverted band, not the native render. Same for ramp-no-floor."""
        from services.neta.router import _synthesize_i2x_delay_curve

        floor_no_ramp = {"i2x": 2, "i_open": 10, "t_open": 0.16, "floor_open": 0.14,
                         "i_clear": None, "t_clear": None, "floor_clear": 0.2}
        assert _synthesize_i2x_delay_curve(
            floor_no_ramp, 2.0, 2000.0, 8000.0, 24000.0, phase="clear") == []

        ramp_no_floor = {"i2x": 2, "i_open": 10, "t_open": 0.16, "floor_open": 0.14,
                         "i_clear": 10, "t_clear": 0.2, "floor_clear": None}
        assert _synthesize_i2x_delay_curve(
            ramp_no_floor, 2.0, 2000.0, 8000.0, 24000.0, phase="clear") == []

    def test_synthesize_i2x_guards(self):
        from services.neta.router import _synthesize_i2x_delay_curve
        assert _synthesize_i2x_delay_curve(None, 2.0, 2000.0, 8000.0, 16000.0) == []
        assert _synthesize_i2x_delay_curve({"i2x": 2}, 2.0, 0.0, 8000.0, 16000.0) == []
        assert _synthesize_i2x_delay_curve({"i2x": 2}, 2.0, 2000.0, 8000.0, 4000.0) == []

    def test_load_i2x_curve_band_matches_floor_setting(self):
        from services.neta.router import _load_i2x_curve_band

        def fake(stmt, params=None):
            r = MagicMock()
            rows = []
            for o, (fo, io, to) in enumerate([(0.08, 10, 0.08), (0.14, 10, 0.16), (0.23, 10, 0.24)]):
                m = MagicMock()
                m._mapping = {"i2x": 2, "i_open": io, "t_open": to, "i_clear": io,
                              "t_clear": to, "floor_open": fo, "floor_clear": fo, "ordinal": o}
                rows.append(m)
            r.fetchall.return_value = rows
            return r

        db = MagicMock(); db.execute = MagicMock(side_effect=fake)
        assert _load_i2x_curve_band(db, "tcc.etu_std_bands", "std_open", "std_clear", 1, 0.14)["floor_open"] == 0.14
        assert _load_i2x_curve_band(db, "tcc.etu_std_bands", "std_open", "std_clear", 1, None)["floor_open"] == 0.08

    def test_i2x_field_delay_composite_time_and_shape(self):
        """I2X-6: the route-1 field expected-time = the validated etu_ixt surface,
        with the shape that gates the trust (composite → db since the #72
        native-primitive spot-check)."""
        from services.neta.router import _i2x_field_delay

        def fake(stmt, params=None):
            sql = str(stmt); r = MagicMock()
            if "i_open" in sql:  # _load_i2x_curve_band
                m = MagicMock()
                m._mapping = {"i2x": 2, "i_open": 10, "t_open": 0.16, "i_clear": 10,
                              "t_clear": 0.2, "floor_open": 0.14, "floor_clear": 0.2, "ordinal": 1}
                r.fetchall.return_value = [m]
            elif "stpu_i2t_val" in sql:  # _sensor_i2x_exponent
                row = MagicMock(); row._mapping = {"x": 2.0}; r.fetchone.return_value = row
            else:
                r.fetchall.return_value = []; r.fetchone.return_value = None
            return r

        db = MagicMock(); db.execute = MagicMock(side_effect=fake)
        # STD inject 12000 A, Ir=2000 → M=6; composite max(ramp, floor)=max(0.16·(10/6)², 0.14).
        t, lo, hi, shape, ok = _i2x_field_delay(db, 1, "std", 12000.0, 2000.0, 0.14, False)
        assert ok and shape == "composite"
        assert t == pytest.approx(0.16 * (10 / 6) ** 2)
        # Degenerate ref → not supported (caller withholds).
        _, _, _, _, ok2 = _i2x_field_delay(db, 1, "std", 12000.0, 0.0, 0.14, False)
        assert ok2 is False

    def test_sensor_i2x_exponent_default_2(self):
        from services.neta.router import _sensor_i2x_exponent

        def fake_x(stmt, params=None):
            r = MagicMock(); row = MagicMock(); row._mapping = {"x": 4.0}; r.fetchone.return_value = row; return r
        db = MagicMock(); db.execute = MagicMock(side_effect=fake_x)
        assert _sensor_i2x_exponent(db, 1, "stpu_i2t_val") == 4.0

        def fake_none(stmt, params=None):
            r = MagicMock(); r.fetchone.return_value = None; return r
        db2 = MagicMock(); db2.execute = MagicMock(side_effect=fake_none)
        assert _sensor_i2x_exponent(db2, 1, "stpu_i2t_val") == 2.0


class TestMicrologicBandlessFallback:
    """Band-less Micrologic 6.0A style records (load gap, tcc styles 238/1919) serve
    the cited canonical I2X bands so the plot composite + Screen 2 still render the
    full LSIG (the same device; style 246 carries the bands)."""

    def test_canonical_module_spec(self):
        from services.neta import micrologic_curves as mc
        assert mc.is_micrologic_6_0("MICROLOGIC 6.0A")
        assert mc.is_micrologic_6_0("Micrologic 6.0H")
        assert not mc.is_micrologic_6_0("MICROLOGIC 5.0A")
        assert not mc.is_micrologic_6_0("Micrologic 7.2E")
        assert not mc.is_micrologic_6_0(None)

        std = mc.canonical_i2x_bands("std")
        assert std and all(b["i2x"] == 2 and b["i_open"] == 10 for b in std)
        gfd = mc.canonical_i2x_bands("gfd")
        assert gfd and gfd[0]["i2x"] is None  # the "Off" flat band
        assert any(b["i2x"] == 2 and b["i_open"] == 1 for b in gfd)

        s = mc.delay_bands_as_settings("std")
        assert s and s[0]["is_default"] is True and "open_time" in s[0]

    def test_load_i2x_curve_band_canonical_fallback(self):
        from services.neta.router import _load_i2x_curve_band

        def empty(stmt, params=None):
            r = MagicMock(); r.fetchall.return_value = []; return r
        db = MagicMock(); db.execute = MagicMock(side_effect=empty)

        # No DB bands + no canonical → None.
        assert _load_i2x_curve_band(db, "tcc.etu_std_bands", "std_open", "std_clear", 1, None) is None
        # No DB bands + canonical "std" → the canonical band matching the setting.
        b = _load_i2x_curve_band(db, "tcc.etu_std_bands", "std_open", "std_clear", 1, 0.14, canonical_element="std")
        assert b and b["i2x"] == 2 and b["floor_open"] == 0.14

    def test_available_delay_elements_micrologic_6_0_adds_std_gfd(self):
        from services.neta.router import _available_delay_elements
        db = MagicMock(); db.execute = MagicMock(side_effect=_make_fake_execute(avail_bands=set()))
        assert _available_delay_elements(db, SENSOR_ID, micrologic_6_0=True) >= {"std", "gfd"}
        assert _available_delay_elements(db, SENSOR_ID, micrologic_6_0=False) == set()


# ──────────────────────────────────────────────────
# Test 5e: Route-2 (InvEq) delay availability from equation payload rows (#119)
# ──────────────────────────────────────────────────

class TestInvEqDelayAvailability:
    """Route-2 (InvEq) sensors carry their delay "bands" as equation payload rows
    (in_out=2, eq_desc = the dial label, e.g. '0.1'–'0.4') in
    ``tcc.etu_{std,gfd}_equations`` — they have NO ``etu_*_bands`` rows at all.
    The delay-availability gate and the band-input resolution must source those
    labels, or the validated InvEq render (G4 §5/§3f) stays dormant for every
    band-less route-2 sensor (#119). The probe is structurally safe: only route-2
    Therm sensors have in_out=2 rows (the GF ANSI family is in_out=1 only and the
    stub is in_out=0), verified against prod 2026-06-09."""

    DIALS = ["0.1", "0.2", "0.3", "0.4"]

    def _db(self, **kwargs):
        db = MagicMock()
        db.execute = MagicMock(side_effect=_make_fake_execute(**kwargs))
        return db

    def test_load_inveq_delay_settings_shapes_options(self):
        from services.neta.router import _load_inveq_delay_settings

        db = self._db(avail_bands=set(), inveq_payload={"std": self.DIALS})
        opts = _load_inveq_delay_settings(db, "std", SENSOR_ID)
        assert [o["open_time"] for o in opts] == [0.1, 0.2, 0.3, 0.4]
        assert [o["label"] for o in opts] == self.DIALS
        assert all(o["band"] == o["label"] for o in opts)
        assert all(o["clear_time"] is None for o in opts)
        assert all(o["is_default"] is False for o in opts)

    def test_load_inveq_delay_settings_non_delay_element_is_empty(self):
        from services.neta.router import _load_inveq_delay_settings

        db = self._db(avail_bands=set(), inveq_payload={"std": self.DIALS})
        assert _load_inveq_delay_settings(db, "ltd", SENSOR_ID) == []
        db.execute.assert_not_called()

    def test_available_delay_elements_sources_inveq_payload(self):
        from services.neta.router import _available_delay_elements

        # Band-less route-2 sensor: both elements available via payload rows.
        db = self._db(avail_bands=set(),
                      inveq_payload={"std": self.DIALS, "gfd": self.DIALS})
        assert _available_delay_elements(db, SENSOR_ID) == {"std", "gfd"}

        # Payload on one element only — the other stays unavailable (the 25-sensor
        # GF ANSI family has no in_out=2 rows and must NOT be exposed).
        db2 = self._db(avail_bands=set(), inveq_payload={"std": self.DIALS})
        assert _available_delay_elements(db2, SENSOR_ID) == {"std"}

    def test_available_delay_elements_band_rows_still_win(self):
        from services.neta.router import _available_delay_elements

        db = self._db(avail_bands={"ltd", "std"}, inveq_payload={"gfd": self.DIALS})
        assert _available_delay_elements(db, SENSOR_ID) == {"ltd", "std", "gfd"}

    def test_resolve_legacy_setting_matches_inveq_label(self):
        from services.neta.router import _resolve_plot_delay_inputs

        db = self._db(avail_bands=set(), inveq_payload={"std": self.DIALS})
        # Legacy value equal to an InvEq dial label = a band selection.
        assert _resolve_plot_delay_inputs(
            db, SENSOR_ID, "std", legacy_setting=0.2, delay_setting=None,
            test_multiple=None, default_test_multiple=1.5,
        ) == (0.2, 1.5, 0.2)
        # A non-matching legacy value keeps the old test-multiple meaning.
        assert _resolve_plot_delay_inputs(
            db, SENSOR_ID, "std", legacy_setting=7.7, delay_setting=None,
            test_multiple=None, default_test_multiple=1.5,
        ) == (None, 7.7, 7.7)

    # ── route-level: the plot draws the InvEq curves for band-less route-2 sensors ──

    def _plot(self, base_request, *, avail_bands, inveq_payload=None,
              trip_style_db=None, extra_request=None):
        mock_session = MagicMock()
        mock_session.execute = MagicMock(
            side_effect=_make_fake_execute(
                avail_bands=avail_bands, inveq_payload=inveq_payload,
                trip_style_db=trip_style_db,
            )
        )

        def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            tc = TestClient(app)
            req = {**base_request, "measurements": None,
                   "include_measured_markers": False, **(extra_request or {})}
            patches, _ = _patch_calc_engine()
            with patches["pickup"], patches["ltd"], patches["ieee"]:
                resp = tc.post("/api/v1/neta/plot-tcc", json=req)
            assert resp.status_code == 200, resp.text
            return resp.json()
        finally:
            app.dependency_overrides.clear()

    def test_plot_draws_inveq_curves_when_bandless(self, base_request):
        body = self._plot(
            base_request, avail_bands=set(),
            inveq_payload={"std": self.DIALS, "gfd": self.DIALS},
        )
        curve_els = {c["element"] for c in body["curves"]}
        assert {"STD", "GFD"} <= curve_els, curve_els
        assert "LTD" not in curve_els  # still band-gated (no LTD inventory)

        marker_els = {m["element"] for m in body["expected_markers"]}
        assert {"STD", "GFD"} <= marker_els, marker_els

    def test_plot_micrologic_styled_route2_falls_through_to_inveq(self, base_request):
        # Micrologic-styled (NOT 6.0) route-2 sensor: the composite branch finds no
        # band row and must fall through to the sensor's own InvEq payload curves
        # (the 1,274-sensor STD cohort sized 2026-06-09).
        body = self._plot(
            base_request, avail_bands=set(),
            inveq_payload={"std": self.DIALS, "gfd": self.DIALS},
            extra_request={"trip_unit_style_name": "MICROLOGIC 5.0"},
        )
        curve_els = {c["element"] for c in body["curves"]}
        assert {"STD", "GFD"} <= curve_els, curve_els

    def test_plot_no_inveq_double_draw_when_composite_succeeds(self, base_request):
        # A 6.0-styled sensor whose composite renders must NOT also draw the InvEq
        # pair on top of it (canonical fallback path; composite serves open+clear
        # from the band's symmetric anchor blocks — the route-1 clear edge, #123).
        body = self._plot(
            base_request, avail_bands=set(), inveq_payload=None,
            trip_style_db="MICROLOGIC 6.0A",
            extra_request={"trip_unit_style_name": "Micrologic 6.0A",
                           "std_delay_setting": 0.14, "gfd_delay_setting": 0.4},
        )
        std_ids = [c["id"] for c in body["curves"] if c["element"] == "STD"]
        assert std_ids == ["std_open", "std_clear"], std_ids
        gfd_ids = [c["id"] for c in body["curves"] if c["element"] == "GFD"]
        assert gfd_ids == ["gfd_open", "gfd_clear"], gfd_ids

        # The clear boundary sits at/above the open boundary pointwise (canonical
        # 6.0A band: t_clear/floor_clear ≥ t_open/floor_open) — real band width.
        std_open = next(c for c in body["curves"] if c["id"] == "std_open")
        std_clear = next(c for c in body["curves"] if c["id"] == "std_clear")
        assert std_clear["line_style"] == "dashed" and std_clear["phase"] == "clear"
        for po, pc in zip(std_open["points"], std_clear["points"]):
            assert pc["seconds"] >= po["seconds"]

        # And the composite phase band therefore no longer flags STD open-only.
        phase_band = next(
            (b for b in body["composite_bands"] if b["id"] == "phase_band"), None)
        assert phase_band is not None
        assert "STD" not in phase_band["open_only_elements"]
        gf_band = next(
            (b for b in body["composite_bands"] if b["id"] == "gf_band"), None)
        assert gf_band is not None
        assert "GFD" not in gf_band["open_only_elements"]


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


# ──────────────────────────────────────────────────
# Test 6b: Plot delay-trust parity with /calculate (G4 §6 / #121)
# ──────────────────────────────────────────────────

class TestPlotDelayTrustParity:
    """The plot's delay surface must withhold exactly what Screen 2 withholds
    (the #67 consistency law on the TIME axis): a not-implemented / hard-excluded
    route's fall-through band value is NOT a certified time. The payload carries
    per-element trust + reason + the timing source so Screen 3 can label each
    curve/marker with the same G4 badges and the tolerance BASIS (per-mfr DB
    value vs flagged generic estimate — NETA acceptance = mfr tolerances)."""

    def _plot(self, base_request, *, delay_routes=None, measurements=None):
        mock_session = MagicMock()
        mock_session.execute = MagicMock(
            side_effect=_make_fake_execute(delay_routes=delay_routes)
        )

        def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            tc = TestClient(app)
            req = {**base_request, "measurements": measurements,
                   "include_measured_markers": measurements is not None}
            patches, _ = _patch_calc_engine()
            with patches["pickup"], patches["ltd"], patches["ieee"]:
                resp = tc.post("/api/v1/neta/plot-tcc", json=req)
            assert resp.status_code == 200, resp.text
            return resp.json()
        finally:
            app.dependency_overrides.clear()

    @staticmethod
    def _row(body, element):
        return next(r for r in body["table_rows"] if r["element"] == element)

    @staticmethod
    def _marker(body, element):
        return next(
            m for m in body["expected_markers"]
            if m["element"] == element and m["kind"] == "delay"
        )

    def test_direct_band_routes_serve_time_with_db_trust(self, base_request):
        body = self._plot(base_request)  # default routes 0/0 = direct band
        for el, t in (("STD", 2.0), ("GFD", 1.5)):
            marker = self._marker(body, el)
            assert marker["trust"] == "db", marker
            assert marker["expected_time"] == t
            row = self._row(body, el)
            assert row["trust"] == "db"
            assert row["expected_time"] == t
            assert "band_table" in (row["notes"] or "")
        ltd = self._marker(body, "LTD")
        assert ltd["trust"] == "db"  # LTD always db (G4 row 5)
        assert "ltd_reference_window" in (self._row(body, "LTD")["notes"] or "")

    def test_unsupported_routes_withhold_time_but_keep_inject_current(self, base_request):
        # GE-TU fall-through routes (STD 3 / GFD 4) — Screen 2 withholds, so must we.
        body = self._plot(base_request, delay_routes={
            "std_route": 3, "gfd_route": 4, "gfd_is_ansi": False,
        })
        for el in ("STD", "GFD"):
            marker = self._marker(body, el)
            assert marker["trust"] == "unsupported", marker
            assert marker["expected_time"] is None
            assert marker["expected_current"] > 0  # the test point stays valid
            row = self._row(body, el)
            assert row["trust"] == "unsupported"
            assert row["expected_time"] is None
            assert row["time_limit_low"] is None and row["time_limit_high"] is None
            assert row["trust_reason"]
        # LTD is not route-governed — stays served.
        assert self._marker(body, "LTD")["expected_time"] == 14.0

    def test_gfd_ansi_route2_now_served(self, base_request):
        # #120: GF-INVEQ ANSI is no longer hard-excluded — CalcAnsiEqGF is
        # validated bit-exact, so route-2 ANSI GFD is "db" like Therm, with a
        # served time and a reason that cites the ANSI kernel.
        body = self._plot(base_request, delay_routes={
            "std_route": 2, "gfd_route": 2, "gfd_is_ansi": True,
        })
        assert self._marker(body, "STD")["trust"] == "db"
        assert self._marker(body, "STD")["expected_time"] == 2.0
        gfd = self._marker(body, "GFD")
        assert gfd["trust"] == "db"
        assert gfd["expected_time"] is not None
        reason = self._row(body, "GFD")["trust_reason"] or ""
        assert "ANSI" in reason and "CalcAnsiEqGF" in reason

    def test_withheld_element_measured_time_is_not_graded(self, base_request):
        # A measured delay time on a withheld element must not be graded PASS
        # against an empty (withheld) acceptance band.
        body = self._plot(
            base_request,
            delay_routes={"std_route": 3, "gfd_route": 4, "gfd_is_ansi": False},
            measurements=[{"element": "STD", "measured_time": 2.1}],
        )
        assert not [m for m in body["measured_markers"]
                    if m["element"] == "STD" and m["kind"] == "delay"]
        assert self._row(body, "STD")["passed"] is None

    def test_pickup_rows_and_markers_are_db_trust(self, base_request):
        body = self._plot(base_request)
        for el in ("LTPU", "STPU", "INST", "GFPU"):
            row = self._row(body, el)
            assert row["trust"] == "db", row
            marker = next(m for m in body["expected_markers"]
                          if m["element"] == el and m["kind"] == "pickup")
            assert marker["trust"] == "db"


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
                result.fetchall.return_value = [_avail_band_row(6.0, None)]  # delay available
            elif "FROM tcc.etu_std_bands" in sql_text:
                row = MagicMock()
                row._mapping = {"open_time": 0.21, "clear_time": 0.31, "ordinal": 2, "is_default": False}
                result.fetchone.return_value = row
                result.fetchall.return_value = [_avail_band_row(0.21, 0.31)]  # delay available
            elif "FROM tcc.etu_gfd_bands" in sql_text:
                row = MagicMock()
                row._mapping = {"open_time": 0.21, "clear_time": 0.31, "ordinal": 2, "is_default": False}
                result.fetchone.return_value = row
                result.fetchall.return_value = [_avail_band_row(0.21, 0.31)]  # delay available
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
            # LTD time is the I2t long-time characteristic (setting = trip time at 6x Ir).
            # At the NETA default 3x: 6.0 * (6/3)^2 = 24.0 s (agrees with the Screen-3 curve).
            assert calc_elements["LTD"]["delay_seconds"] == 24.0
            assert calc_elements["LTD"]["notes"] == "timing_source=ltd_reference_window_generic"

            assert plot_resp.status_code == 200
            plot_body = plot_resp.json()
            # The one DELIBERATE disclosure (#124): this fixture's route
            # bytes resolve to None → the GFD time is G4-withheld while its
            # curve serves, and GFD is the gf family's only element, so the
            # envelope honesty warning is the disclosure carrier. Anything
            # else here is still a spurious warning.
            assert plot_body["warnings"] == [
                "GFD acceptance envelope withheld (G4 field-trust)"
            ]
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


# ──────────────────────────────────────────────────
# Composite-boundary bands (#122, G4 §3g)
# ──────────────────────────────────────────────────

class TestCompositeBands:
    """/plot-tcc serves the native-faithful composite boundary bands
    (phase_band + gf_band) assembled from the per-element curves."""

    def test_bands_present_and_shaped(self, client, base_request):
        tc, _ = client
        req = {**base_request, "measurements": None, "include_measured_markers": False}

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        body = resp.json()
        bands = body["composite_bands"]
        assert [b["id"] for b in bands] == ["phase_band", "gf_band"]

        phase = bands[0]
        assert phase["family"] == "phase"
        # Vertical asymptote anchor at the LT curve's start current (1500 A).
        first = phase["open_points"][0]
        assert first["amps"] == 1500.0 and first["seconds"] == 1_000_000.0
        # INST floor extended to the right edge: open 0.05 s, clear 0.08 s.
        last_open = phase["open_points"][-1]
        assert last_open["amps"] == 100_000.0 and last_open["seconds"] == 0.05
        last_clear = phase["clear_points"][-1]
        assert last_clear["amps"] == 100_000.0 and last_clear["seconds"] == 0.08
        # Every element in the default fake serves open+clear.
        assert phase["open_only_elements"] == []
        assert phase["right_edge_amps"] == 100_000.0

        gf = bands[1]
        assert gf["family"] == "gf"
        first_gf = gf["open_points"][0]
        # GF band: own vertical at the GF curve start, native 1000 s top anchor.
        assert first_gf["amps"] == 500.0 and first_gf["seconds"] == 1_000.0

    def test_no_bands_without_nominal_curve(self, client, base_request):
        tc, _ = client
        req = {
            **base_request,
            "measurements": None,
            "include_measured_markers": False,
            "include_nominal_curve": False,
        }

        patches, _ = _patch_calc_engine()
        with patches["pickup"], patches["ltd"], patches["ieee"]:
            resp = tc.post("/api/v1/neta/plot-tcc", json=req)

        assert resp.status_code == 200
        assert resp.json()["composite_bands"] == []


# ──────────────────────────────────────────────────
# Tolerance envelope bands (#124)
# ──────────────────────────────────────────────────

class TestToleranceEnvelope:
    """/plot-tcc serves the field-acceptance tolerance envelope (#124):
    the served curves transformed by the SAME tolerance bases the whiskers
    grade against (PU pcts from the pickup marker limits; LTD time pcts from
    the served delay row), assembled into min/max boundaries."""

    # A reference-window-consistent LTD sweep (t = 3.5·(5760/I)², the §111
    # I²t law through the 3× marker point (2880 A, 14.0 s)). The envelope's
    # LTD anchor-consistency guard rightly withholds the default
    # FAKE_LTD_CURVE (5.5 s @ 2880 A vs the graded 14.0 s) — these tests use
    # a curve that IS the graded surface, as the prod I²t paths are.
    WINDOW_LTD_CURVE = [
        FakeLTDCurvePoint(1500.0, 51.6096),
        FakeLTDCurvePoint(2880.0, 14.0),
        FakeLTDCurvePoint(5760.0, 3.5),
        FakeLTDCurvePoint(10000.0, 1.161216),
    ]

    def _plot(self, base_request, *, ltd_tol_rows=None, delay_routes=None,
              extra_request=None, ltd_curve=None, calc_data=None):
        mock_session = MagicMock()
        mock_session.execute = MagicMock(
            side_effect=_make_fake_execute(
                calc_data=calc_data if calc_data is not None else CALC_DATA,
                ltd_tol_rows=ltd_tol_rows, delay_routes=delay_routes,
            )
        )

        def override_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_db
        try:
            tc = TestClient(app)
            req = {**base_request, "measurements": None,
                   "include_measured_markers": False, **(extra_request or {})}
            patches, _ = _patch_calc_engine(
                ltd_curve=ltd_curve if ltd_curve is not None else self.WINDOW_LTD_CURVE,
            )
            with patches["pickup"], patches["ltd"], patches["ieee"]:
                resp = tc.post("/api/v1/neta/plot-tcc", json=req)
            assert resp.status_code == 200, resp.text
            return resp.json()
        finally:
            app.dependency_overrides.clear()

    @staticmethod
    def _secs_at(points, amps):
        """Curve seconds at an amps breakpoint (min over the stacked pickup
        asymptote, like the unit-test helper)."""
        matches = [p["seconds"] for p in points
                   if abs(p["amps"] - amps) <= 1e-6 * max(abs(amps), 1.0)]
        return min(matches) if matches else None

    @staticmethod
    def _basis(env, element):
        return next((b for b in env["element_basis"] if b["element"] == element), None)

    def test_envelope_bands_present_with_derived_bases(self, base_request):
        body = self._plot(base_request)
        envs = {b["id"]: b for b in body["envelope_bands"]}
        assert set(envs) == {"phase_envelope", "gf_envelope"}

        phase = envs["phase_envelope"]
        assert phase["family"] == "phase"
        # PU pcts derive from the served pickup marker limits (864/1056 over
        # 960 → −10/+10) — whisker↔envelope identity by construction.
        ltd = self._basis(phase, "LTD")
        assert ltd is not None
        assert ltd["pu_tol_lo_pct"] == pytest.approx(-10.0)
        assert ltd["pu_tol_hi_pct"] == pytest.approx(10.0)
        assert ltd["pu_source"] == "db_sensor_tolerance"
        # No DB LTD tolerance in the default fake → the flagged generic
        # window (−30/+0), estimated=True (the est marker law).
        assert ltd["time_tol_lo_pct"] == pytest.approx(-30.0)
        assert ltd["time_tol_hi_pct"] == pytest.approx(0.0)
        assert ltd["time_source"] == "ltd_generic_estimate"
        assert ltd["estimated"] is True

        std = self._basis(phase, "STD")
        assert std is not None
        assert std["time_source"] == "published_band"
        assert std["pu_tol_lo_pct"] == pytest.approx(-10.0)  # 4320/4800
        inst = self._basis(phase, "INST")
        assert inst is not None
        assert inst["time_source"] == "published_band"

        gf = envs["gf_envelope"]
        gfd = self._basis(gf, "GFD")
        assert gfd is not None
        assert gfd["pu_tol_lo_pct"] == pytest.approx(-10.0)  # 432/480
        assert gfd["pu_tol_hi_pct"] == pytest.approx(10.0)
        assert gfd["time_source"] == "published_band"

    def test_envelope_geometry_scales_served_curves(self, base_request):
        body = self._plot(base_request)
        envs = {b["id"]: b for b in body["envelope_bands"]}
        phase = envs["phase_envelope"]
        # Min boundary starts at the LTD curve start shifted by LTPU tol_lo
        # (1500 × 0.9), max boundary at 1500 × 1.1 — the pickup verticals move.
        assert phase["min_points"][0]["amps"] == pytest.approx(1350.0)
        assert phase["max_points"][0]["amps"] == pytest.approx(1650.0)
        # Acceptance-window law on the LTD segment: seconds scale by the
        # generic −30% on the min edge (14.0 s @ 2880 A → 9.8 s @ 2592 A) —
        # and because the curve IS the graded window, the envelope edge at
        # the marker amps equals the whisker band exactly.
        assert self._secs_at(phase["min_points"], 2880.0 * 0.9) == pytest.approx(9.8)
        # Max edge seconds unchanged (tol_hi = 0): 14.0 s @ 3168 A.
        assert self._secs_at(phase["max_points"], 2880.0 * 1.1) == pytest.approx(14.0)

        gf = envs["gf_envelope"]
        # GFD published-band mode: pickup shifts (500 → 450 / 550), the GF
        # curve's own start current carrying the 1000 s top anchor.
        assert gf["min_points"][0]["amps"] == pytest.approx(450.0)
        assert gf["max_points"][0]["amps"] == pytest.approx(550.0)
        assert gf["min_points"][0]["seconds"] == pytest.approx(1000.0)

    def test_ltd_db_tolerance_unflags_estimate(self, base_request):
        body = self._plot(
            base_request,
            ltd_tol_rows=[{"curve_name": "I^2T", "tol_lo": -20.0, "tol_hi": 0.0}],
        )
        phase = next(b for b in body["envelope_bands"] if b["id"] == "phase_envelope")
        ltd = self._basis(phase, "LTD")
        assert ltd is not None
        assert ltd["time_tol_lo_pct"] == pytest.approx(-20.0)
        assert ltd["time_tol_hi_pct"] == pytest.approx(0.0)
        assert ltd["time_source"] == "ltd_curve_tol"
        assert ltd["estimated"] is False

    def test_withheld_route_gets_no_envelope(self, base_request):
        # Route 3 (TUSTD, not implemented) withholds the STD time (G4) — the
        # envelope must withhold STD too, surfaced honestly, never fabricated.
        body = self._plot(
            base_request,
            delay_routes={"std_route": 3, "gfd_route": 0, "gfd_is_ansi": False},
        )
        phase = next(b for b in body["envelope_bands"] if b["id"] == "phase_envelope")
        assert self._basis(phase, "STD") is None
        std_served = any(
            c["element"] == "STD" and c["phase"] == "open" for c in body["curves"])
        if std_served:
            assert "STD" in phase["no_envelope_elements"]
        # The trusted elements keep their envelope.
        assert self._basis(phase, "LTD") is not None

    def test_withheld_gfd_route_gets_no_gf_envelope(self, base_request):
        # Route 4 (TUG, not implemented) withholds the GFD time (G4) — the
        # GFD envelope must withhold too. GFD is the GF family's ONLY
        # element, so the gf_envelope band disappears entirely
        # (both-boundaries-or-nothing law), never a fabricated corridor.
        body = self._plot(
            base_request,
            delay_routes={"std_route": 0, "gfd_route": 4, "gfd_is_ansi": False},
        )
        gfd_served = any(
            c["element"] == "GFD" and c["phase"] == "open" for c in body["curves"])
        for env in body["envelope_bands"]:
            assert self._basis(env, "GFD") is None
            # Were a gf envelope ever assembled despite the withhold, it
            # would at minimum have to disclose GFD as no-envelope.
            if env["family"] == "gf" and gfd_served:
                assert "GFD" in env["no_envelope_elements"]
        assert not any(b["id"] == "gf_envelope" for b in body["envelope_bands"])
        # The trusted phase family keeps its envelope untouched.
        phase = next(b for b in body["envelope_bands"] if b["id"] == "phase_envelope")
        assert self._basis(phase, "LTD") is not None
        assert self._basis(phase, "STD") is not None

    def test_no_envelope_without_nominal_curve(self, base_request):
        body = self._plot(base_request, extra_request={"include_nominal_curve": False})
        assert body["envelope_bands"] == []

    def test_maint_mode_withholds_envelope(self, base_request):
        # Review finding (#124): in maint mode the markers/grading reflect
        # the maint configuration while the served curves are nominal — an
        # envelope would mix the two bases and contradict the whiskers
        # (Law 1). Withhold + warn instead.
        body = self._plot(
            base_request,
            calc_data={**CALC_DATA, "maint_mode": True},
            extra_request={"maint_mode": True},
        )
        assert body["envelope_bands"] == []
        assert any("maintenance mode" in w for w in body["warnings"])

    def test_ltd_anchor_inconsistent_curve_withholds_ltd(self, base_request):
        # Review finding (#124): the LTD acceptance-window pcts grade
        # against the §111 reference window. The default FAKE_LTD_CURVE
        # passes 5.5 s at the 3× marker where the graded window says 14.0 s
        # — scaling that curve would draw a corridor contradicting the
        # grading row, so the LTD envelope must withhold.
        body = self._plot(base_request, ltd_curve=FAKE_LTD_CURVE)
        phase = next(b for b in body["envelope_bands"] if b["id"] == "phase_envelope")
        assert self._basis(phase, "LTD") is None
        assert "LTD" in phase["no_envelope_elements"]
        # A leading withhold: the corridor still serves for STD/INST.
        assert self._basis(phase, "STD") is not None
        assert self._basis(phase, "INST") is not None

    def test_gfd_ansi_route2_gets_gf_envelope(self, base_request):
        # #120: GF-INVEQ ANSI is promoted to "db" (CalcAnsiEqGF parity), so a
        # served ANSI GFD now carries a published-band envelope like any other
        # trusted route-2 element — no longer force-withheld.
        body = self._plot(
            base_request,
            delay_routes={"std_route": 0, "gfd_route": 2, "gfd_is_ansi": True},
        )
        gf = next((b for b in body["envelope_bands"] if b["id"] == "gf_envelope"), None)
        assert gf is not None
        gfd = self._basis(gf, "GFD")
        assert gfd is not None
        assert gfd["time_source"] == "published_band"

    def test_family_total_withhold_surfaces_a_warning(self, base_request):
        # Review finding (#124): when a whole family's envelope vanishes
        # (GFD is the gf family's only element), the no_envelope_elements
        # honesty list has no band to ride on — a response warning carries
        # the disclosure instead.
        body = self._plot(
            base_request,
            delay_routes={"std_route": 0, "gfd_route": 4, "gfd_is_ansi": False},
        )
        gfd_served = any(
            c["element"] == "GFD" and c["phase"] == "open" for c in body["curves"])
        assert not any(b["id"] == "gf_envelope" for b in body["envelope_bands"])
        if gfd_served:
            assert any(
                "GFD" in w and "envelope withheld" in w for w in body["warnings"]
            ), body["warnings"]

    def test_ltd_non_reference_window_source_is_withheld(self):
        # The acceptance-window transform (multiplicative along the open
        # curve) is only proven for the reference-window law. An LTD row
        # whose timing came from the band table (or curve interpolation)
        # must NOT be dressed up as a DS2 tolerance — withhold instead.
        from dataclasses import dataclass
        from typing import Optional as _Opt
        from services.neta.router import _build_envelope_basis_map

        @dataclass
        class _M:
            id: str
            kind: str
            limit_low: _Opt[float]
            limit_high: _Opt[float]
            expected_current: float

        @dataclass
        class _R:
            element: str
            kind: str
            trust: _Opt[str]
            expected_time: _Opt[float]
            time_limit_low: _Opt[float]
            time_limit_high: _Opt[float]
            notes: _Opt[str]

        markers = [_M("ltpu_expected", "pickup", 864.0, 1056.0, 960.0)]
        rows = [_R("LTD", "delay", "db", 3.5, 3.0, 3.5,
                   "timing_source=band_table")]
        bases = _build_envelope_basis_map(markers, rows)
        assert "LTD" not in bases

        # The reference-window sources keep the basis (with the est flag
        # tracking the generic suffix).
        rows_ok = [_R("LTD", "delay", "db", 14.0, 9.8, 14.0,
                      "timing_source=ltd_reference_window")]
        bases_ok = _build_envelope_basis_map(markers, rows_ok)
        assert bases_ok["LTD"].time_source == "ltd_curve_tol"
        assert bases_ok["LTD"].estimated is False

        # GFD mirror of the STD withhold law: a TIME_WITHHELD GFD row must
        # delete the GFD basis (the gf family's only element).
        gf_markers = [_M("gfpu_expected", "pickup", 432.0, 528.0, 480.0)]
        gf_rows = [_R("GFD", "delay", "unsupported", None, None, None,
                      "timing_source=band_table")]
        assert "GFD" not in _build_envelope_basis_map(gf_markers, gf_rows)
        gf_rows_ok = [_R("GFD", "delay", "db", 0.14, 0.14, 0.2,
                         "timing_source=band_table")]
        assert _build_envelope_basis_map(gf_markers, gf_rows_ok)[
            "GFD"].time_source == "published_band"

    def test_ltd_anchor_consistency_probes_inside_a_clipped_sweep(self):
        # Live-caught on 3833 (Micrologic 6.0A, STPU 1.5×Ir): the long-time
        # sweep ends at the STD handoff (1800 A) BEFORE the 3× marker
        # (2880 A here). The guard must prove consistency against the I²t
        # window THROUGH the marker anchor at probes INSIDE the served
        # sweep — a window-law curve clipped short keeps its envelope.
        clipped_window_curve = [
            FakeLTDCurvePoint(1320.0, 66.6446280992),  # 14·(2880/1320)²
            FakeLTDCurvePoint(1800.0, 35.84),          # 14·(2880/1800)²
        ]
        body = self._plot(
            type(self).BASE_REQUEST if hasattr(type(self), "BASE_REQUEST") else {
                "sensor_id": SENSOR_ID, "plug_rating": PLUG_RATING,
                "ltpu_setting": 0.8, "ltd_setting": 3.5, "stpu_setting": 4.0,
                "std_setting": 2.0, "inst_setting": 10.0, "gfpu_setting": 0.4,
                "gfd_setting": 1.5, "maint_mode": False,
                "include_nominal_curve": True, "include_expected_markers": True,
                "include_measured_markers": False,
            },
            ltd_curve=clipped_window_curve,
        )
        phase = next(b for b in body["envelope_bands"] if b["id"] == "phase_envelope")
        ltd = self._basis(phase, "LTD")
        assert ltd is not None, phase["no_envelope_elements"]
        assert "LTD" not in phase["no_envelope_elements"]
