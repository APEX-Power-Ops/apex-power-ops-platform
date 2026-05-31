from __future__ import annotations

import csv
import contextlib
import io
import json
import math
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from sqlalchemy import inspect, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

with contextlib.redirect_stdout(io.StringIO()):
    from config import engine


VARIANT_KEYWORDS = (
    "earth leakage",
    "earth-leakage",
    "source ground return",
    "ground return",
    "residual",
    "zero sequence",
    "zero-sequence",
    "leakage",
)

MAX_NAME_SAMPLES = 15
MAX_SENSOR_SAMPLES = 12
MAX_RUNTIME_SAMPLES = 20
MAX_RUNTIME_PROBE_PER_NAME = 3
MAX_RUNTIME_PROBE_TOTAL = 120

CSV_MATRIX_NAME = "audit_etu_ground_variants_calc7_matrix.csv"
MARKDOWN_MATRIX_NAME = "audit_etu_ground_variants_calc7_matrix.md"


def decimal_to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def clean_text(value: object) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def normalize_name(value: object) -> str:
    cleaned = clean_text(value)
    return cleaned or "<null>"


def is_variant_name(value: object) -> bool:
    cleaned = clean_text(value)
    if not cleaned:
        return False
    lowered = cleaned.lower()
    return any(keyword in lowered for keyword in VARIANT_KEYWORDS)


def to_number_list(csv_text: str | None) -> list[float]:
    if not csv_text:
        return []
    values: list[float] = []
    for item in csv_text.split(","):
        text_value = item.strip()
        if not text_value:
            continue
        values.append(float(text_value))
    return values


def format_sensor(row: dict[str, object]) -> dict[str, object]:
    return {
        "sensor_id": row["sensor_id"],
        "manufacturer": row["manufacturer_name"],
        "trip_type": row["trip_type_name"],
        "trip_style": row["trip_style_name"],
        "rating": decimal_to_float(row.get("rating")),
        "gfpu_name": row.get("gfpu_name"),
        "gfpu_calc": row.get("gfpu_calc"),
        "pickup_count": row.get("pickup_count"),
        "min_setting": decimal_to_float(row.get("min_setting")),
        "max_setting": decimal_to_float(row.get("max_setting")),
        "gfpu_pickup_max": decimal_to_float(row.get("gfpu_pickup_max")),
        "min_valid_plug": decimal_to_float(row.get("min_valid_plug")),
        "max_valid_plug": decimal_to_float(row.get("max_valid_plug")),
    }


def distinct_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def build_calc7_family_matrix(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str, str], dict[str, object]] = {}

    for row in rows:
        if row.get("gfpu_calc") != 7:
            continue

        key = (
            str(row.get("manufacturer_name") or "<null>"),
            str(row.get("trip_type_name") or "<null>"),
            str(row.get("trip_style_name") or "<null>"),
            normalize_name(row.get("gfpu_name")),
        )

        group = grouped.setdefault(
            key,
            {
                "manufacturer": key[0],
                "trip_type": key[1],
                "trip_style": key[2],
                "gfpu_name": key[3],
                "variant_name": is_variant_name(key[3]),
                "sensor_count": 0,
                "rating_min": None,
                "rating_max": None,
                "pickup_min": None,
                "pickup_max": None,
                "plug_min": None,
                "plug_max": None,
                "sensor_pickup_max_populated": 0,
                "maint_pickup_max_populated": 0,
                "sensor_ids": [],
            },
        )

        group["sensor_count"] += 1
        group["sensor_ids"].append(int(row["sensor_id"]))

        rating = decimal_to_float(row.get("rating"))
        if rating is not None:
            group["rating_min"] = rating if group["rating_min"] is None else min(group["rating_min"], rating)
            group["rating_max"] = rating if group["rating_max"] is None else max(group["rating_max"], rating)

        min_setting = decimal_to_float(row.get("min_setting"))
        max_setting = decimal_to_float(row.get("max_setting"))
        if min_setting is not None:
            group["pickup_min"] = min_setting if group["pickup_min"] is None else min(group["pickup_min"], min_setting)
        if max_setting is not None:
            group["pickup_max"] = max_setting if group["pickup_max"] is None else max(group["pickup_max"], max_setting)

        min_plug = decimal_to_float(row.get("min_valid_plug"))
        max_plug = decimal_to_float(row.get("max_valid_plug"))
        if min_plug is not None:
            group["plug_min"] = min_plug if group["plug_min"] is None else min(group["plug_min"], min_plug)
        if max_plug is not None:
            group["plug_max"] = max_plug if group["plug_max"] is None else max(group["plug_max"], max_plug)

        if row.get("gfpu_pickup_max") is not None:
            group["sensor_pickup_max_populated"] += 1
        if row.get("maint_gfpu_pickup_max") is not None:
            group["maint_pickup_max_populated"] += 1

    matrix_rows: list[dict[str, object]] = []
    for group in grouped.values():
        sensor_ids = sorted(group["sensor_ids"])
        matrix_rows.append(
            {
                "manufacturer": group["manufacturer"],
                "trip_type": group["trip_type"],
                "trip_style": group["trip_style"],
                "gfpu_name": group["gfpu_name"],
                "variant_name": group["variant_name"],
                "sensor_count": group["sensor_count"],
                "rating_min": group["rating_min"],
                "rating_max": group["rating_max"],
                "pickup_min": group["pickup_min"],
                "pickup_max": group["pickup_max"],
                "plug_min": group["plug_min"],
                "plug_max": group["plug_max"],
                "sensor_pickup_max_populated": group["sensor_pickup_max_populated"],
                "maint_pickup_max_populated": group["maint_pickup_max_populated"],
                "sensor_ids_sample": ", ".join(str(sensor_id) for sensor_id in sensor_ids[:8]),
            }
        )

    matrix_rows.sort(
        key=lambda item: (
            item["manufacturer"],
            item["trip_type"],
            item["trip_style"],
            item["gfpu_name"],
        )
    )
    return matrix_rows


def write_calc7_matrix_artifacts(matrix_rows: list[dict[str, object]]) -> dict[str, object]:
    csv_path = Path(__file__).with_name(CSV_MATRIX_NAME)
    markdown_path = Path(__file__).with_name(MARKDOWN_MATRIX_NAME)

    fieldnames = [
        "manufacturer",
        "trip_type",
        "trip_style",
        "gfpu_name",
        "variant_name",
        "sensor_count",
        "rating_min",
        "rating_max",
        "pickup_min",
        "pickup_max",
        "plug_min",
        "plug_max",
        "sensor_pickup_max_populated",
        "maint_pickup_max_populated",
        "sensor_ids_sample",
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in matrix_rows:
            writer.writerow(row)

    lines = [
        "# ETU GFPU Calc=7 Family Matrix",
        "",
        f"Rows: {len(matrix_rows)}",
        "",
        "This matrix groups all ETU sensors where `gfpu_calc = 7` by manufacturer, trip type, trip style, and GFPU name.",
        "",
        "| Manufacturer | Trip Type | Trip Style | GFPU Name | Variant | Sensors | Rating Range | Pickup Range | Plug Range | Sensor Pickup Max Rows | Maint Pickup Max Rows | Sensor Sample |",
        "|---|---|---|---|---|---:|---|---|---|---:|---:|---|",
    ]

    for row in matrix_rows:
        rating_range = f"{row['rating_min']}–{row['rating_max']}" if row["rating_min"] is not None else "—"
        pickup_range = f"{row['pickup_min']}–{row['pickup_max']}" if row["pickup_min"] is not None else "—"
        plug_range = f"{row['plug_min']}–{row['plug_max']}" if row["plug_min"] is not None else "—"
        lines.append(
            "| {manufacturer} | {trip_type} | {trip_style} | {gfpu_name} | {variant_name} | {sensor_count} | {rating_range} | {pickup_range} | {plug_range} | {sensor_pickup_max_populated} | {maint_pickup_max_populated} | {sensor_ids_sample} |".format(
                manufacturer=row["manufacturer"],
                trip_type=row["trip_type"],
                trip_style=row["trip_style"],
                gfpu_name=row["gfpu_name"],
                variant_name="yes" if row["variant_name"] else "no",
                sensor_count=row["sensor_count"],
                rating_range=rating_range,
                pickup_range=pickup_range,
                plug_range=plug_range,
                sensor_pickup_max_populated=row["sensor_pickup_max_populated"],
                maint_pickup_max_populated=row["maint_pickup_max_populated"],
                sensor_ids_sample=row["sensor_ids_sample"],
            )
        )

    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "csv_path": str(csv_path),
        "markdown_path": str(markdown_path),
        "row_count": len(matrix_rows),
    }


def load_sensor_rows() -> tuple[list[dict[str, object]], dict[str, bool]]:
    inspector = inspect(engine)
    sensor_columns = {column["name"] for column in inspector.get_columns("etu_sensors", schema="tcc")}
    maint_columns = set()
    if "etu_sensor_maint" in inspector.get_table_names(schema="tcc"):
        maint_columns = {column["name"] for column in inspector.get_columns("etu_sensor_maint", schema="tcc")}

    has_pickup_max = "gfpu_pickup_max" in sensor_columns
    has_gfpu_func = "gfpu_func" in sensor_columns
    has_gfpu_step = "gfpu_step" in sensor_columns
    has_maint_pickup_max = "maint_gfpu_pickup_max" in maint_columns

    select_columns = [
        "s.id AS sensor_id",
        "s.trip_style_id",
        "s.rating",
        "s.description",
        "s.gfpu_name",
        "s.gfpu_calc",
        f"s.gfpu_func AS gfpu_func" if has_gfpu_func else "NULL::integer AS gfpu_func",
        f"s.gfpu_step AS gfpu_step" if has_gfpu_step else "NULL::numeric AS gfpu_step",
        f"s.gfpu_pickup_max AS gfpu_pickup_max" if has_pickup_max else "NULL::numeric AS gfpu_pickup_max",
        (
            "mtn.maint_gfpu_pickup_max AS maint_gfpu_pickup_max"
            if has_maint_pickup_max
            else "NULL::numeric AS maint_gfpu_pickup_max"
        ),
        "m.id AS manufacturer_id",
        "m.mfr_name AS manufacturer_name",
        "tt.id AS trip_type_id",
        "tt.name AS trip_type_name",
        "ts.id AS trip_style_id_joined",
        "ts.style AS trip_style_name",
        "COALESCE(pu.pickup_count, 0) AS pickup_count",
        "pu.min_setting",
        "pu.max_setting",
        "pu.settings_csv",
        "COALESCE(vp.valid_plug_count, 0) AS valid_plug_count",
        "vp.min_valid_plug",
        "vp.max_valid_plug",
    ]

    maint_join = ""
    if has_maint_pickup_max:
        maint_join = "LEFT JOIN tcc.etu_sensor_maint mtn ON mtn.sensor_id = s.id"

    query = f"""
        SELECT
            {', '.join(select_columns)}
        FROM tcc.etu_sensors s
        JOIN tcc.trip_styles ts ON ts.id = s.trip_style_id
        JOIN tcc.trip_types tt ON tt.manufacturer_id = ts.mfg_id AND tt.name = ts.type
        JOIN tcc.manufacturers m ON m.id = ts.mfg_id
        LEFT JOIN (
            SELECT
                sensor_id,
                COUNT(*) AS pickup_count,
                MIN(value) AS min_setting,
                MAX(value) AS max_setting,
                STRING_AGG(value::text, ', ' ORDER BY value) AS settings_csv
            FROM tcc.etu_gfpu_pickups
            GROUP BY sensor_id
        ) pu ON pu.sensor_id = s.id
        LEFT JOIN (
            SELECT
                s_inner.id AS sensor_id,
                COUNT(*) AS valid_plug_count,
                MIN(p.value) AS min_valid_plug,
                MAX(p.value) AS max_valid_plug
            FROM tcc.etu_sensors s_inner
            JOIN tcc.etu_plugs p
              ON p.trip_style_id = s_inner.trip_style_id
             AND p.value <= s_inner.rating
            GROUP BY s_inner.id
        ) vp ON vp.sensor_id = s.id
        {maint_join}
        WHERE s.gfpu_name IS NOT NULL OR s.gfpu_calc IS NOT NULL
        ORDER BY m.mfr_name, tt.name, ts.style, s.rating, s.id
    """

    with engine.connect() as connection:
        rows = [dict(row) for row in connection.execute(text(query)).mappings().all()]

    return rows, {
        "has_gfpu_pickup_max": has_pickup_max,
        "has_gfpu_func": has_gfpu_func,
        "has_gfpu_step": has_gfpu_step,
        "has_maint_gfpu_pickup_max": has_maint_pickup_max,
    }


def build_name_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}

    for row in rows:
        name = normalize_name(row.get("gfpu_name"))
        group = grouped.setdefault(
            name,
            {
                "gfpu_name": name,
                "sensor_count": 0,
                "variant_name": is_variant_name(name),
                "calc_counts": Counter(),
            },
        )
        group["sensor_count"] += 1
        group["calc_counts"][str(row.get("gfpu_calc"))] += 1

    summaries: list[dict[str, object]] = []
    for group in grouped.values():
        calc_counts = dict(sorted(group["calc_counts"].items(), key=lambda item: item[0]))
        summaries.append(
            {
                "gfpu_name": group["gfpu_name"],
                "sensor_count": group["sensor_count"],
                "variant_name": group["variant_name"],
                "calc_counts": calc_counts,
            }
        )

    summaries.sort(key=lambda item: (-item["sensor_count"], item["gfpu_name"]))
    return summaries


def build_metadata_flags(rows: list[dict[str, object]]) -> dict[str, object]:
    flags: dict[str, list[dict[str, object]]] = defaultdict(list)

    for row in rows:
        variant = is_variant_name(row.get("gfpu_name"))
        calc_method = row.get("gfpu_calc")
        pickup_count = int(row.get("pickup_count") or 0)
        max_setting = row.get("max_setting")
        pickup_max = row.get("gfpu_pickup_max")
        maint_pickup_max = row.get("maint_gfpu_pickup_max")

        if row.get("gfpu_name") is not None and pickup_count == 0:
            flags["active_gf_without_pickups"].append(format_sensor(row))

        if calc_method == 7 and not variant:
            flags["amps_routed_without_variant_name"].append(format_sensor(row))

        if variant and calc_method not in (7, None):
            flags["variant_named_but_not_amp_routed"].append(format_sensor(row))

        if pickup_max is not None and max_setting is not None and float(max_setting) > float(pickup_max):
            sample = format_sensor(row)
            sample["pickup_max_source"] = "sensor"
            flags["pickup_values_exceed_sensor_pickup_max"].append(sample)

        if maint_pickup_max is not None and max_setting is not None and float(max_setting) > float(maint_pickup_max):
            sample = format_sensor(row)
            sample["pickup_max_source"] = "maint"
            flags["pickup_values_exceed_maint_pickup_max"].append(sample)

    return {
        key: {
            "count": len(values),
            "samples": values[:MAX_SENSOR_SAMPLES],
        }
        for key, values in sorted(flags.items())
    }


def probe_amp_runtime(rows: list[dict[str, object]]) -> dict[str, object]:
    available_candidates = [
        row
        for row in rows
        if row.get("gfpu_calc") == 7
        and (row.get("pickup_count") or 0) > 0
        and (row.get("valid_plug_count") or 0) > 1
        and row.get("min_valid_plug") is not None
        and row.get("max_valid_plug") is not None
    ]

    grouped_candidates: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in available_candidates:
        grouped_candidates[normalize_name(row.get("gfpu_name"))].append(row)

    candidates: list[dict[str, object]] = []
    for name in sorted(grouped_candidates):
        candidates.extend(grouped_candidates[name][:MAX_RUNTIME_PROBE_PER_NAME])
        if len(candidates) >= MAX_RUNTIME_PROBE_TOTAL:
            candidates = candidates[:MAX_RUNTIME_PROBE_TOTAL]
            break

    mismatches: list[dict[str, object]] = []
    probe_errors: list[dict[str, object]] = []

    sql = text(
        """
        SELECT fn_calculate_test_currents(
            p_sensor_id := :sensor_id,
            p_plug_rating := :plug_rating,
            p_gfpu_setting := :gfpu_setting
        ) AS result
        """
    )

    with engine.connect() as connection:
        for row in candidates:
            setting = float(row["max_setting"])
            min_plug = float(row["min_valid_plug"])
            max_plug = float(row["max_valid_plug"])

            try:
                min_result = connection.execute(
                    sql,
                    {
                        "sensor_id": row["sensor_id"],
                        "plug_rating": min_plug,
                        "gfpu_setting": setting,
                    },
                ).mappings().one()["result"]
                max_result = connection.execute(
                    sql,
                    {
                        "sensor_id": row["sensor_id"],
                        "plug_rating": max_plug,
                        "gfpu_setting": setting,
                    },
                ).mappings().one()["result"]
            except Exception as exc:  # noqa: BLE001
                probe_errors.append(
                    {
                        "sensor_id": row["sensor_id"],
                        "manufacturer": row["manufacturer_name"],
                        "trip_type": row["trip_type_name"],
                        "trip_style": row["trip_style_name"],
                        "gfpu_name": row.get("gfpu_name"),
                        "error": str(exc),
                    }
                )
                continue

            min_current = min_result.get("gfpu", {}).get("test_current") if min_result else None
            max_current = max_result.get("gfpu", {}).get("test_current") if max_result else None

            if min_current is None or max_current is None:
                probe_errors.append(
                    {
                        "sensor_id": row["sensor_id"],
                        "manufacturer": row["manufacturer_name"],
                        "trip_type": row["trip_type_name"],
                        "trip_style": row["trip_style_name"],
                        "gfpu_name": row.get("gfpu_name"),
                        "error": "GFPU result missing from fn_calculate_test_currents output",
                    }
                )
                continue

            if not math.isclose(float(min_current), float(max_current), rel_tol=0.0, abs_tol=1e-9):
                mismatches.append(
                    {
                        "sensor_id": row["sensor_id"],
                        "manufacturer": row["manufacturer_name"],
                        "trip_type": row["trip_type_name"],
                        "trip_style": row["trip_style_name"],
                        "rating": decimal_to_float(row.get("rating")),
                        "gfpu_name": row.get("gfpu_name"),
                        "gfpu_setting": setting,
                        "min_valid_plug": min_plug,
                        "max_valid_plug": max_plug,
                        "min_current": decimal_to_float(min_current),
                        "max_current": decimal_to_float(max_current),
                    }
                )

    mismatch_names = distinct_preserve_order(
        [normalize_name(item.get("gfpu_name")) for item in mismatches]
    )

    return {
        "available_candidate_count": len(available_candidates),
        "tested_sensor_count": len(candidates),
        "mismatch_count": len(mismatches),
        "error_count": len(probe_errors),
        "mismatch_name_samples": mismatch_names[:MAX_NAME_SAMPLES],
        "mismatch_samples": mismatches[:MAX_RUNTIME_SAMPLES],
        "error_samples": probe_errors[:MAX_SENSOR_SAMPLES],
    }


def main() -> int:
    rows, schema_flags = load_sensor_rows()

    gfpu_active_rows = [row for row in rows if clean_text(row.get("gfpu_name")) is not None]
    variant_rows = [row for row in gfpu_active_rows if is_variant_name(row.get("gfpu_name"))]
    amp_rows = [row for row in gfpu_active_rows if row.get("gfpu_calc") == 7]
    amp_variant_rows = [row for row in amp_rows if is_variant_name(row.get("gfpu_name"))]

    name_summary = build_name_summary(gfpu_active_rows)
    metadata_flags = build_metadata_flags(gfpu_active_rows)
    runtime_probe = probe_amp_runtime(gfpu_active_rows)
    calc7_matrix = build_calc7_family_matrix(gfpu_active_rows)
    matrix_artifacts = write_calc7_matrix_artifacts(calc7_matrix)

    calc_counter = Counter(str(row.get("gfpu_calc")) for row in gfpu_active_rows)
    variant_names = distinct_preserve_order(
        [normalize_name(row.get("gfpu_name")) for row in variant_rows]
    )

    report = {
        "audit_name": "etu_ground_variant_audit",
        "schema_flags": schema_flags,
        "totals": {
            "gfpu_active_sensor_count": len(gfpu_active_rows),
            "variant_named_sensor_count": len(variant_rows),
            "amp_routed_sensor_count": len(amp_rows),
            "amp_routed_variant_named_sensor_count": len(amp_variant_rows),
        },
        "distinct_calc_methods": dict(sorted(calc_counter.items(), key=lambda item: item[0])),
        "variant_name_samples": variant_names[:MAX_NAME_SAMPLES],
        "gfpu_name_summary": name_summary[:MAX_NAME_SAMPLES],
        "metadata_flags": metadata_flags,
        "runtime_probe": runtime_probe,
        "calc7_family_matrix": {
            "group_count": len(calc7_matrix),
            "artifacts": matrix_artifacts,
            "samples": calc7_matrix[:MAX_NAME_SAMPLES],
        },
    }

    print(json.dumps(report, indent=2, default=decimal_to_float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
