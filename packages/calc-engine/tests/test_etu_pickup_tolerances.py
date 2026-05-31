from types import SimpleNamespace

from apex_calc_engine.services.calc_engine.etu_pickup import (
    ETUCalcMethod,
    ETUPickupCalculator,
)


def _stub_calculator() -> ETUPickupCalculator:
    calc = ETUPickupCalculator.__new__(ETUPickupCalculator)
    calc.sensor = SimpleNamespace(id=1, rating=1000)
    return calc


def test_absent_pickup_element_returns_no_result_before_tolerance_band():
    calc = _stub_calculator()

    result = calc._calc_element(
        calc_method=ETUCalcMethod.NONE,
        setting=1.0,
        plug_value=1000,
        multiplier=None,
        c_factor=None,
        tol_lo=None,
        tol_hi=None,
        cascade_current=None,
        element_name="STPU",
    )

    assert result is None


def test_null_pickup_tolerance_is_zero_width_when_defensively_evaluated():
    min_limit, max_limit = ETUPickupCalculator._calc_tolerance(
        current=1200.0,
        tol_lo=None,
        tol_hi=None,
    )

    assert min_limit == 1200.0
    assert max_limit == 1200.0
