from types import SimpleNamespace
from unittest.mock import MagicMock

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

