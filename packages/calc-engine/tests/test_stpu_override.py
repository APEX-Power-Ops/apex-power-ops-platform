from types import SimpleNamespace
from unittest.mock import MagicMock

from apex_calc_engine.services.calc_engine.etu_pickup import (
    ETUCalcMethod,
    ETUPickupCalculator,
)


OVERRIDE_AMPS = 12000.0
OVERRIDE_OPEN_TIME = 0.025
OVERRIDE_CLEAR_TIME = 0.067
OVERRIDE_TOL_LO_PCT = -9.0917
OVERRIDE_TOL_HI_PCT = 11.1083


def _mock_result(*, row=None):
    result = MagicMock()
    result.fetchone.return_value = row
    return result


def _stub_calculator() -> ETUPickupCalculator:
    calc = ETUPickupCalculator.__new__(ETUPickupCalculator)
    calc.session = MagicMock()
    calc.sensor = SimpleNamespace(id=16671, rating=1000)
    calc.maint_record = None
    calc.stpu_override = {
        "applied": True,
        "amps": OVERRIDE_AMPS,
        "tolerance_low": OVERRIDE_TOL_LO_PCT,
        "tolerance_high": OVERRIDE_TOL_HI_PCT,
        "open_time": OVERRIDE_OPEN_TIME,
        "clear_time": OVERRIDE_CLEAR_TIME,
    }
    return calc


def test_load_stpu_override_reads_flat_source_faithful_row():
    calc = ETUPickupCalculator.__new__(ETUPickupCalculator)
    calc.session = MagicMock()
    calc.session.execute.return_value = _mock_result(row={
        "ovr_amps": OVERRIDE_AMPS,
        "ovr_toler_low_pct": OVERRIDE_TOL_LO_PCT,
        "ovr_toler_high_pct": OVERRIDE_TOL_HI_PCT,
        "ovr_open_sec": OVERRIDE_OPEN_TIME,
        "ovr_clear_sec": OVERRIDE_CLEAR_TIME,
    })

    result = calc._load_stpu_override(sensor_id=16671)

    assert result["applied"] is True
    assert result["amps"] == OVERRIDE_AMPS
    assert result["open_time"] == OVERRIDE_OPEN_TIME
    assert result["clear_time"] == OVERRIDE_CLEAR_TIME
    assert result["tolerance_low"] == OVERRIDE_TOL_LO_PCT
    assert result["tolerance_high"] == OVERRIDE_TOL_HI_PCT


def test_load_stpu_override_falls_back_to_existing_eav_model_shape():
    calc = ETUPickupCalculator.__new__(ETUPickupCalculator)
    calc.session = MagicMock()
    calc.session.execute.side_effect = RuntimeError("flat columns unavailable")
    calc.session.query.return_value.filter.return_value.all.return_value = [
        SimpleNamespace(type_="amps", value=OVERRIDE_AMPS),
        SimpleNamespace(type_="tolerance_low", value=OVERRIDE_TOL_LO_PCT),
        SimpleNamespace(type_="tolerance_high", value=OVERRIDE_TOL_HI_PCT),
        SimpleNamespace(type_="open_time", value=OVERRIDE_OPEN_TIME),
        SimpleNamespace(type_="clear_time", value=OVERRIDE_CLEAR_TIME),
    ]

    result = calc._load_stpu_override(sensor_id=16671)

    assert result["applied"] is True
    assert result["amps"] == OVERRIDE_AMPS
    assert result["open_time"] == OVERRIDE_OPEN_TIME


def test_build_override_stpu_result_uses_override_amps_and_asymmetric_tolerance():
    calc = _stub_calculator()
    result = calc._build_override_stpu_result(maint_mode=False)

    assert result.current == round(OVERRIDE_AMPS, 2)
    assert result.min_limit == round(OVERRIDE_AMPS * (1.0 + OVERRIDE_TOL_LO_PCT / 100.0), 2)
    assert result.max_limit == round(OVERRIDE_AMPS * (1.0 + OVERRIDE_TOL_HI_PCT / 100.0), 2)
    assert result.method == int(ETUCalcMethod.AMPS)
    assert result.method_name == "OVERRIDE"
    assert result.override_applied is True
    assert result.override_open_time == OVERRIDE_OPEN_TIME
    assert result.override_clear_time == OVERRIDE_CLEAR_TIME


def test_build_override_stpu_result_handles_missing_tolerance_as_zero_band():
    calc = _stub_calculator()
    calc.stpu_override = {
        "applied": True,
        "amps": OVERRIDE_AMPS,
        "tolerance_low": None,
        "tolerance_high": None,
        "open_time": OVERRIDE_OPEN_TIME,
        "clear_time": OVERRIDE_CLEAR_TIME,
    }

    result = calc._build_override_stpu_result(maint_mode=True)

    assert result.current == round(OVERRIDE_AMPS, 2)
    assert result.min_limit == round(OVERRIDE_AMPS, 2)
    assert result.max_limit == round(OVERRIDE_AMPS, 2)
    assert result.maint_mode is True

