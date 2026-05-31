from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import inspect, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import engine


ETU_REQUIRED_TABLES = {
    "tcc.etu_sensors",
    "tcc.trip_styles",
    "tcc.trip_types",
    "tcc.manufacturers",
}
ETU_REQUIRED_VIEWS = {"vw_sensor_calc_context"}

MAINT_REQUIRED_TABLES = {"tcc.etu_sensor_maint"}

TMT_REQUIRED_TABLES = {
    "tcc.tmt_frames",
    "tcc.tmt_amps",
    "tcc.tmt_settings",
    "tcc.tmt_curves",
    "tcc.tmt_thermal_adj",
    "tcc.brk_iccb",
    "tcc.brk_mccb",
    "tcc.brk_pcb",
    "tcc.brk_iccb_styles",
    "tcc.brk_mccb_styles",
    "tcc.brk_pcb_styles",
    "tcc.manufacturers",
}

EMT_REQUIRED_TABLES = {
    "tcc.emt",
    "tcc.emt_frames",
    "tcc.emt_frame_amps",
    "tcc.emt_sections",
    "tcc.emt_band_names",
    "tcc.emt_pickups",
    "tcc.emt_curves",
}


ETU_SUMMARY_SQL = """
SELECT
    COUNT(*) AS sensor_count,
    COUNT(DISTINCT s.trip_style_id) AS trip_style_count,
    COUNT(DISTINCT ts.mfg_id) AS manufacturer_count
FROM tcc.etu_sensors s
JOIN tcc.trip_styles ts ON ts.id = s.trip_style_id
"""

ETU_METHOD_SQL = """
SELECT
    COUNT(*) FILTER (WHERE ltpu_calc IS NOT NULL) AS ltpu_calc_rows,
    COUNT(*) FILTER (WHERE stpu_calc IS NOT NULL) AS stpu_calc_rows,
    COUNT(*) FILTER (WHERE inst_calc IS NOT NULL) AS inst_calc_rows,
    COUNT(*) FILTER (WHERE gfpu_calc IS NOT NULL) AS gfpu_calc_rows
FROM vw_sensor_calc_context
"""

MAINT_SUMMARY_SQL = """
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE maint_ltpu_reduction IS NOT NULL) AS ltpu_non_null,
    COUNT(*) FILTER (WHERE maint_stpu_reduction IS NOT NULL) AS stpu_non_null,
    COUNT(*) FILTER (WHERE maint_available IS TRUE) AS maint_available_true,
    COUNT(*) FILTER (
        WHERE POSITION('ltpu_reduction' IN COALESCE(params_json::text, '')) > 0
    ) AS params_has_ltpu_key,
    COUNT(*) FILTER (
        WHERE POSITION('stpu_reduction' IN COALESCE(params_json::text, '')) > 0
    ) AS params_has_stpu_key,
    COUNT(*) FILTER (
        WHERE POSITION('reduction' IN COALESCE(params_json::text, '')) > 0
    ) AS params_has_any_reduction_text
FROM tcc.etu_sensor_maint
"""

TMT_SUMMARY_SQL = """
SELECT
    (SELECT COUNT(*) FROM tcc.tmt_frames) AS frame_count,
    (SELECT COUNT(*) FROM tcc.tmt_amps) AS amp_row_count,
    (SELECT COUNT(*) FROM tcc.tmt_settings) AS setting_row_count,
    (SELECT COUNT(*) FROM tcc.tmt_curves) AS curve_row_count,
    (SELECT COUNT(*) FROM tcc.tmt_thermal_adj) AS thermal_row_count
"""

TMT_CLASS_SQL = """
SELECT
    UPPER(COALESCE(breaker_class, '<null>')) AS breaker_class,
    COUNT(*) AS frame_count
FROM tcc.tmt_frames
GROUP BY UPPER(COALESCE(breaker_class, '<null>'))
ORDER BY breaker_class
"""

EMT_SUMMARY_SQL = """
SELECT
    (SELECT COUNT(*) FROM tcc.emt) AS emt_root_count,
    (SELECT COUNT(*) FROM tcc.emt_frames) AS frame_count,
    (SELECT COUNT(*) FROM tcc.emt_frame_amps) AS frame_amp_row_count,
    (SELECT COUNT(*) FROM tcc.emt_sections) AS section_count,
    (SELECT COUNT(*) FROM tcc.emt_band_names) AS band_count,
    (SELECT COUNT(*) FROM tcc.emt_pickups) AS pickup_count,
    (SELECT COUNT(*) FROM tcc.emt_curves) AS curve_count
"""


def decimal_to_number(value):
    if isinstance(value, Decimal):
        if value == value.to_integral():
            return int(value)
        return float(value)
    return value


def format_names(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def fetch_one(connection, sql: str) -> dict[str, object]:
    row = connection.execute(text(sql)).mappings().one()
    return {key: decimal_to_number(value) for key, value in dict(row).items()}


def fetch_all(connection, sql: str) -> list[dict[str, object]]:
    rows = connection.execute(text(sql)).mappings().all()
    return [
        {key: decimal_to_number(value) for key, value in dict(row).items()}
        for row in rows
    ]


def validate_required_surfaces(
    family_name: str,
    existing_tables: set[str],
    existing_views: set[str],
    required_tables: set[str],
    required_views: set[str] | None = None,
) -> list[str]:
    failures: list[str] = []
    missing_tables = sorted(required_tables - existing_tables)
    if missing_tables:
        failures.append(f"{family_name}: missing tables: {format_names(missing_tables)}")

    required_views = required_views or set()
    missing_views = sorted(required_views - existing_views)
    if missing_views:
        failures.append(f"{family_name}: missing views: {format_names(missing_views)}")

    return failures


def validate_positive_counts(family_name: str, summary: dict[str, object], required_keys: list[str]) -> list[str]:
    failures: list[str] = []
    for key in required_keys:
        if int(summary.get(key, 0) or 0) <= 0:
            failures.append(f"{family_name}: expected {key} > 0, got {summary.get(key, 0)}")
    return failures


def main() -> int:
    inspector = inspect(engine)
    existing_tables = {f"tcc.{table}" for table in inspector.get_table_names(schema="tcc")}
    existing_views = set(inspector.get_view_names())

    failures: list[str] = []

    failures.extend(
        validate_required_surfaces("etu", existing_tables, existing_views, ETU_REQUIRED_TABLES, ETU_REQUIRED_VIEWS)
    )
    failures.extend(
        validate_required_surfaces("maint", existing_tables, existing_views, MAINT_REQUIRED_TABLES)
    )
    failures.extend(
        validate_required_surfaces("tmt", existing_tables, existing_views, TMT_REQUIRED_TABLES)
    )
    failures.extend(
        validate_required_surfaces("emt", existing_tables, existing_views, EMT_REQUIRED_TABLES)
    )

    with engine.connect() as connection:
        etu_summary = fetch_one(connection, ETU_SUMMARY_SQL)
        etu_methods = fetch_one(connection, ETU_METHOD_SQL)
        maint_summary = fetch_one(connection, MAINT_SUMMARY_SQL)
        tmt_summary = fetch_one(connection, TMT_SUMMARY_SQL)
        tmt_classes = fetch_all(connection, TMT_CLASS_SQL)
        emt_summary = fetch_one(connection, EMT_SUMMARY_SQL)

    failures.extend(validate_positive_counts("etu", etu_summary, ["sensor_count", "trip_style_count", "manufacturer_count"]))
    failures.extend(
        validate_positive_counts(
            "etu",
            etu_methods,
            ["ltpu_calc_rows", "stpu_calc_rows", "inst_calc_rows", "gfpu_calc_rows"],
        )
    )
    failures.extend(validate_positive_counts("maint", maint_summary, ["total_rows"]))
    if int(maint_summary.get("ltpu_non_null", 0) or 0) != 0:
        failures.append(
            "maint: expected maint_ltpu_reduction evidence to remain null across the active population"
        )
    if int(maint_summary.get("stpu_non_null", 0) or 0) != 0:
        failures.append(
            "maint: expected maint_stpu_reduction evidence to remain null across the active population"
        )
    if int(maint_summary.get("maint_available_true", 0) or 0) != 0:
        failures.append("maint: expected maint_available to remain false across the active population")
    if int(maint_summary.get("params_has_any_reduction_text", 0) or 0) != 0:
        failures.append("maint: expected params_json to contain no reduction keys in the active population")

    failures.extend(
        validate_positive_counts(
            "tmt",
            tmt_summary,
            ["frame_count", "amp_row_count", "setting_row_count", "curve_row_count", "thermal_row_count"],
        )
    )
    if not tmt_classes:
        failures.append("tmt: expected at least one breaker_class group in tcc.tmt_frames")

    failures.extend(
        validate_positive_counts(
            "emt",
            emt_summary,
            [
                "emt_root_count",
                "frame_count",
                "frame_amp_row_count",
                "section_count",
                "band_count",
                "pickup_count",
                "curve_count",
            ],
        )
    )

    report = {
        "validation_name": "lv_breaker_phase3_family_validation",
        "forward_migration_lane": "supabase/migrations",
        "rollback_boundary_policy": "documentary_only",
        "families": {
            "etu": {
                "required_tables": sorted(ETU_REQUIRED_TABLES),
                "required_views": sorted(ETU_REQUIRED_VIEWS),
                "summary": etu_summary,
                "calc_method_presence": etu_methods,
            },
            "maint": {
                "required_tables": sorted(MAINT_REQUIRED_TABLES),
                "summary": maint_summary,
            },
            "tmt": {
                "required_tables": sorted(TMT_REQUIRED_TABLES),
                "summary": tmt_summary,
                "breaker_classes": tmt_classes,
            },
            "emt": {
                "required_tables": sorted(EMT_REQUIRED_TABLES),
                "summary": emt_summary,
            },
        },
        "failures": failures,
        "result": "PASS" if not failures else "FAIL",
    }

    print(json.dumps(report, indent=2, default=decimal_to_number))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
