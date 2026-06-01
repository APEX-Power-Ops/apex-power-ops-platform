import math
from types import SimpleNamespace
from unittest.mock import MagicMock

from apex_calc_engine.services.calc_engine.etu_curves import Coefficients
from apex_calc_engine.services.calc_engine.etu_curves import IEEEInverseTimeSolver
from apex_calc_engine.services.calc_engine.etu_ltd import ETULTDCalculator


def _mock_result(*, rows=None, row=None):
    result = MagicMock()
    if rows is not None:
        result.fetchall.return_value = rows
    if row is not None:
        result.fetchone.return_value = row
    return result


def test_ieee_solver_reads_source_faithful_equation_rows():
    session = MagicMock()
    session.execute.return_value = _mock_result(rows=[
        {
            "label": "0.0",
            "in_out": 2,
            "fd_open_1": 0.1,
            "fd_open_2": 1.0,
            "fd_open_3": 0.01,
        },
        {
            "label": "0.4",
            "in_out": 2,
            "fd_open_1": 0.35,
            "fd_open_2": 2.0,
            "fd_open_3": 0.014,
        },
    ])

    solver = IEEEInverseTimeSolver(session)

    assert solver.get_equation_info(25, "std") == [
        {"ordinal": 1, "label": "0.0", "in_out": 2},
        {"ordinal": 2, "label": "0.4", "in_out": 2},
    ]
    coeff = solver._load_coefficients(25, 2, "fd_open", "std")
    assert coeff.c1 == 0.35
    assert coeff.c2 == 2.0
    assert coeff.c3 == 0.014


def test_ieee_solver_uses_recovered_native_therm_formula_when_c4_c5_present():
    coeff = Coefficients(c1=0.08, c2=2.0, c3=0.08, c4=10.0, c5=0.9, c6=0.0)

    seconds = IEEEInverseTimeSolver._evaluate(
        coeff,
        I_norm=2.0,
        time_dial=1.0,
        tolerance_pct=0.0,
    )

    assert seconds is not None
    assert math.isclose(seconds, 2.2257362438248176, rel_tol=1e-12)


def test_ieee_solver_native_therm_honors_riref_and_rm_floor():
    gf_coeff = Coefficients(c1=0.08, c2=2.0, c3=0.08, c4=1.0, c5=0.9, c6=0.0)

    seconds = IEEEInverseTimeSolver._evaluate(
        gf_coeff,
        I_norm=2.0,
        time_dial=1.0,
        tolerance_pct=0.0,
    )

    assert seconds == 0.08


def test_ieee_solver_keeps_legacy_ieee_fallback_without_native_therm_shape():
    coeff = Coefficients(c1=0.08, c2=2.0, c3=0.08, c4=0.0, c5=0.0, c6=0.0)

    seconds = IEEEInverseTimeSolver._evaluate(
        coeff,
        I_norm=2.0,
        time_dial=1.0,
        tolerance_pct=0.0,
    )

    assert seconds is not None
    assert math.isclose(seconds, (0.08 / (2.0**2.0 - 1.0)) + 0.08, rel_tol=1e-12)


def test_ltd_calculator_reads_source_faithful_ltd_param_rows():
    session = MagicMock()
    session.execute.return_value = _mock_result(rows=[
        {
            "curve_name": "I2T",
            "curve_id": 3,
            "ordinal": 1,
            "method": 2,
            "tol_hi": 10.0,
            "tol_lo": -10.0,
            "delay_priority": 4,
        }
    ])

    calc = ETULTDCalculator.__new__(ETULTDCalculator)
    calc.session = session
    calc.sensor = SimpleNamespace(id=25)

    assert calc.get_ltd_info() == [
        {
            "ordinal": 1,
            "method": 2,
            "curve_name": "I2T",
            "tol_hi": 10.0,
            "tol_lo": -10.0,
            "delay_priority": 4,
        }
    ]
    assert calc._get_ltd_param(1).curve_name == "I2T"


def test_ltd_calculator_reads_sensor_param_rows_without_surrogate_id():
    session = MagicMock()
    session.execute.return_value = _mock_result(rows=[
        {"sensor_id": 25, "section": 2, "curve_id": None, "idx": 0, "value": 1.5},
        {"sensor_id": 25, "section": 2, "curve_id": 7, "idx": 3, "value": 9.25},
    ])

    calc = ETULTDCalculator.__new__(ETULTDCalculator)
    calc.session = session
    calc.sensor = SimpleNamespace(id=25)
    calc._params = {}
    calc._params_by_curve = {}

    calc._load_sensor_params()

    sql_text = str(session.execute.call_args.args[0])
    assert "SELECT sensor_id, section, curve_id, idx, value" in sql_text
    assert "tcc_etu_sensor_params.id" not in sql_text
    assert calc._params == {0: 1.5, 3: 9.25}
    assert calc._params_by_curve == {0: {0: 1.5}, 7: {3: 9.25}}


def test_ltd_calculator_supports_legacy_ltd_band_and_std_band_rows():
    session = MagicMock()
    session.rollback = MagicMock()
    session.execute.side_effect = [
        RuntimeError("column band does not exist"),
        _mock_result(rows=[
            {"curve_id": 7, "band_label": "Min", "open_time": 3.0},
            {"curve_id": 7, "band_label": "Max", "open_time": 6.0},
        ]),
        RuntimeError("column open_time does not exist"),
        _mock_result(row={"min_time": 0.12}),
    ]

    calc = ETULTDCalculator.__new__(ETULTDCalculator)
    calc.session = session
    calc.sensor = SimpleNamespace(id=25)

    assert calc.get_band_info(curve_id=7) == [
        {
            "ordinal": 1,
            "band": "Min",
            "band_label": "Min",
            "open_time": 3.0,
            "clear_time": 3.0,
            "curve_id": 7,
            "is_default": True,
        },
        {
            "ordinal": 2,
            "band": "Max",
            "band_label": "Max",
            "open_time": 6.0,
            "clear_time": 6.0,
            "curve_id": 7,
            "is_default": False,
        },
    ]
    assert calc._get_min_stdb_time(is_clear=False) == 0.12
    assert session.rollback.call_count == 2
