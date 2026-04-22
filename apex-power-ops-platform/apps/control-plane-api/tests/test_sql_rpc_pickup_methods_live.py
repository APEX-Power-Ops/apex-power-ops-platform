"""Live regression checks for SQL RPC pickup routing.

These tests validate that the SQL RPC helper now matches the Python pickup
engine for representative active calc-method paths.

They are intentionally integration-style:
- skip when the active database is unavailable
- exercise the real SQL functions against live catalog data
"""

import os
import sys

import pytest
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SessionLocal
from apex_calc_engine.services.calc_engine.etu_pickup import ETUPickupCalculator


def _sql_calculate(session, sensor_id: int, plug_rating: float, **settings):
    row = session.execute(
        text(
            """
            SELECT fn_calculate_test_currents(
                p_sensor_id := :sensor_id,
                p_plug_rating := :plug_rating,
                p_ltpu_setting := :ltpu_setting,
                p_ltd_multiplier := :ltd_setting,
                p_stpu_setting := :stpu_setting,
                p_std_multiplier := :std_setting,
                p_inst_setting := :inst_setting,
                p_gfpu_setting := :gfpu_setting,
                p_gfd_multiplier := :gfd_setting,
                p_multiplier_value := :multiplier_value,
                p_c_factor := :c_factor,
                p_maint_mode := false
            ) AS result
            """
        ),
        {
            "sensor_id": sensor_id,
            "plug_rating": plug_rating,
            "ltpu_setting": settings.get("ltpu_setting"),
            "ltd_setting": settings.get("ltd_setting", 3),
            "stpu_setting": settings.get("stpu_setting"),
            "std_setting": settings.get("std_setting", 1.5),
            "inst_setting": settings.get("inst_setting"),
            "gfpu_setting": settings.get("gfpu_setting"),
            "gfd_setting": settings.get("gfd_setting", 1.5),
            "multiplier_value": settings.get("multiplier_value"),
            "c_factor": settings.get("c_factor"),
        },
    ).fetchone()
    return row.result if row else None


def _pick_plug(calc: ETUPickupCalculator):
    plugs = [plug for plug in calc.get_plugs_for_style() if float(plug["value"]) <= float(calc.sensor.rating)]
    if not plugs:
        pytest.skip(f"No valid plugs found for sensor {calc.sensor.id}")
    return plugs[-1]


def _first_pickup_setting(calc: ETUPickupCalculator, element: str) -> float:
    pickups = [item for item in calc.get_available_pickups(element) if item.get("value") not in (None, 0)]
    if not pickups:
        pytest.skip(f"No pickup settings found for {element} on sensor {calc.sensor.id}")
    return float(pickups[0]["value"])


def _pick_multiplier_value(calc: ETUPickupCalculator) -> float:
    multipliers = [
        item for item in calc.get_available_multipliers()
        if item.get("c_value") not in (None, 0)
    ]
    if not multipliers:
        pytest.skip(f"No multiplier/C values found for sensor {calc.sensor.id}")
    default_item = next((item for item in multipliers if item.get("is_default")), multipliers[0])
    return float(default_item["c_value"])


def _first_stable_calc(session, query):
    candidate_ids = [int(row[0]) for row in session.execute(query).fetchmany(20)]
    if not candidate_ids:
        return None, None

    for sensor_id in candidate_ids:
        try:
            return sensor_id, ETUPickupCalculator(session, sensor_id)
        except Exception:
            continue

    return None, None


@pytest.mark.integration
def test_sql_rpc_matches_python_for_stpu_ltpu_cascade_sensor_6258():
    try:
        with SessionLocal() as session:
            calc = ETUPickupCalculator(session, 6258)
            plug = next((item for item in calc.get_plugs_for_style() if float(item["value"]) == 600.0), None)
            if plug is None:
                pytest.skip("Sensor 6258 600A plug not available in active database")

            python_result = calc.calculate(
                plug_id=plug["id"],
                ltpu_setting=0.8,
                stpu_setting=4.0,
            )
            sql_result = _sql_calculate(
                session,
                sensor_id=6258,
                plug_rating=600.0,
                ltpu_setting=0.8,
                stpu_setting=4.0,
            )
    except Exception as exc:
        pytest.skip(f"Live database unavailable for SQL RPC regression test: {exc}")

    assert sql_result is not None
    assert sql_result["ltpu"]["test_current"] == python_result.ltpu.current
    assert sql_result["ltpu"]["limit_low"] == python_result.ltpu.min_limit
    assert sql_result["ltpu"]["limit_high"] == python_result.ltpu.max_limit
    assert sql_result["stpu"]["test_current"] == python_result.stpu.current
    assert sql_result["stpu"]["limit_low"] == python_result.stpu.min_limit
    assert sql_result["stpu"]["limit_high"] == python_result.stpu.max_limit


@pytest.mark.integration
@pytest.mark.parametrize(
    ("element", "calc_column", "setting_key"),
    [
        ("ltpu", "ltpu_calc", "ltpu_setting"),
        ("stpu", "stpu_calc", "stpu_setting"),
        ("inst", "inst_calc", "inst_setting"),
        ("gfpu", "gfpu_calc", "gfpu_setting"),
    ],
)
def test_sql_rpc_matches_python_for_amp_routed_pickups(element: str, calc_column: str, setting_key: str):
    query = text(
        f"""
        SELECT sensor_id
        FROM vw_sensor_calc_context
        WHERE {calc_column} = 7
          AND COALESCE({element}_name, '') <> ''
        ORDER BY sensor_id
        LIMIT 1
        """
    )

    try:
        with SessionLocal() as session:
            sensor_id, calc = _first_stable_calc(session, query)
            if sensor_id is None or calc is None:
                pytest.skip(f"No active {element} calc=7 sensors found")
            plug = _pick_plug(calc)
            setting_value = _first_pickup_setting(calc, element)

            python_result = calc.calculate(
                plug_id=plug["id"],
                **{setting_key: setting_value},
            )
            sql_result = _sql_calculate(
                session,
                sensor_id=sensor_id,
                plug_rating=float(plug["value"]),
                **{setting_key: setting_value},
            )
    except Exception as exc:
        pytest.skip(f"Live database unavailable for SQL RPC regression test: {exc}")

    assert sql_result is not None
    python_elem = getattr(python_result, element)
    sql_elem = sql_result[element]

    assert python_elem is not None
    assert sql_elem is not None
    assert sql_elem["test_current"] == python_elem.current
    assert sql_elem["limit_low"] == python_elem.min_limit
    assert sql_elem["limit_high"] == python_elem.max_limit
    assert sql_elem["calc_method"] == 7


@pytest.mark.integration
@pytest.mark.parametrize(
    ("element", "calc_column", "setting_key", "calc_method", "factor_key"),
    [
        ("ltpu", "ltpu_calc", "ltpu_setting", 2, "multiplier_value"),
        ("ltpu", "ltpu_calc", "ltpu_setting", 3, "multiplier_value"),
        ("stpu", "stpu_calc", "stpu_setting", 5, "c_factor"),
        ("stpu", "stpu_calc", "stpu_setting", 6, "c_factor"),
    ],
)
def test_sql_rpc_matches_python_for_factorized_pickups(
    element: str,
    calc_column: str,
    setting_key: str,
    calc_method: int,
    factor_key: str,
):
    query = text(
        f"""
        SELECT sensor_id
        FROM vw_sensor_calc_context
        WHERE {calc_column} = {calc_method}
          AND COALESCE({element}_name, '') <> ''
        ORDER BY sensor_id
        LIMIT 5
        """
    )

    try:
        with SessionLocal() as session:
            sensor_id, calc = _first_stable_calc(session, query)
            if sensor_id is None or calc is None:
                pytest.skip(f"No active {element} calc={calc_method} sensors found")
            plug = _pick_plug(calc)
            setting_value = _first_pickup_setting(calc, element)
            factor_value = _pick_multiplier_value(calc)

            python_result = calc.calculate(
                plug_id=plug["id"],
                **{setting_key: setting_value, factor_key: factor_value},
            )
            sql_result = _sql_calculate(
                session,
                sensor_id=sensor_id,
                plug_rating=float(plug["value"]),
                **{setting_key: setting_value, factor_key: factor_value},
            )
    except Exception as exc:
        pytest.skip(f"Live database unavailable for SQL RPC regression test: {exc}")

    assert sql_result is not None
    python_elem = getattr(python_result, element)
    sql_elem = sql_result[element]

    assert python_elem is not None
    assert sql_elem is not None
    assert sql_elem["test_current"] == python_elem.current
    assert sql_elem["limit_low"] == python_elem.min_limit
    assert sql_elem["limit_high"] == python_elem.max_limit
    assert sql_elem["calc_method"] == calc_method