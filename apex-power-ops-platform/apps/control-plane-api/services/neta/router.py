"""
FastAPI router for NETA ETT Testing Service.

Endpoints:
  GET  /api/v1/neta/cascade              — Cascade drill-down selection
  GET  /api/v1/neta/context/{sensor_id}  — Full sensor calculation context
  GET  /api/v1/neta/settings/{sensor_id} — Available settings for dropdowns
  POST /api/v1/neta/calculate            — Calculate test currents + tolerance bands
  POST /api/v1/neta/evaluate             — Evaluate measured values → pass/fail

All endpoints consume PostgreSQL views/functions via raw SQL (not ORM),
since the views and functions live in Supabase and are decoupled from
the SQLAlchemy model layer.
"""

import json
import logging
from collections import Counter
from decimal import Decimal
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from sqlalchemy.exc import NoResultFound

from apex_calc_engine.services.calc_engine import TMTCurveGenerator
from config import get_db
from models.breakers import BrkICCBStyle, BrkMCCBStyle, BrkPCBStyle
from models.tmt import TMTFrame
from .schemas import (
    CascadeQuery,
    CascadeManufacturer,
    CascadeTripType,
    CascadeTripStyle,
    CascadeSensor,
    CascadeResponse,
    SensorCalcContext,
    AvailableSettingsResponse,
    ApparatusStudyResource,
    ApparatusStudyResourcesResponse,
    CalculateRequest,
    CalculateResponse,
    TestCurrentElement,
    EvaluateRequest,
    EvaluateResponse,
    ElementResult,
    PlotTccRequest,
    PlotTccResponse,
    PlotMeta,
    PlotCurve,
    PlotCurvePoint,
    PlotExpectedMarker,
    PlotMeasuredMarker,
    PlotTableRow,
    TMTAmpOption,
    TMTFrameContext,
    TMTFrameSearchResponse,
    TMTFrameSearchResult,
    EMTBandOption,
    EMTFrameContext,
    EMTPlotCurve,
    EMTPlotCurvePoint,
    EMTPlotMeta,
    EMTPlotRequest,
    EMTPlotResponse,
    EMTFrameSearchResponse,
    EMTFrameSearchResult,
    EMTPickupOption,
    EMTSectionSettingsResponse,
    EMTSectionSummary,
    TMTPlotCurve,
    TMTPlotCurvePoint,
    TMTPlotMeta,
    TMTPlotRequest,
    TMTPlotResponse,
    TMTSettingsResponse,
    TMTSettingOption,
    ResolvedBreakerContext,
    ResolvedEquipmentSummary,
    ResolvedRatingContext,
    ResolvedTripUnitIdentity,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/neta", tags=["neta"])


_PICKUP_TABLES = {
    "ltpu": "tcc_etu_ltpu_pickups",
    "stpu": "tcc_etu_stpu_pickups",
    "inst": "tcc_etu_inst_pickups",
    "gfpu": "tcc_etu_gfpu_pickups",
}


def _row_mapping(row):
    return dict(row._mapping) if row is not None else {}


def _join_summary_label(*parts: object) -> Optional[str]:
    cleaned = [str(part).strip() for part in parts if part not in (None, "") and str(part).strip()]
    return " · ".join(cleaned) if cleaned else None


def _format_amp_label(value: object) -> Optional[str]:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return f"{int(number)}A"
    return f"{number:g}A"


def _build_etu_resolved_equipment_summary(
    *,
    sensor_id: int,
    sensor_desc: Optional[str],
    sensor_rating: Optional[float],
    manufacturer_name: Optional[str],
    trip_type_name: Optional[str],
    trip_style_name: Optional[str],
    breaker_context_label: Optional[str],
    breaker_context_source: Optional[str],
) -> ResolvedEquipmentSummary:
    trip_unit_label = _join_summary_label(manufacturer_name, trip_type_name, trip_style_name)
    fallback_breaker_context = _join_summary_label(trip_style_name, _format_amp_label(sensor_rating))
    rating_label = _join_summary_label("Sensor", sensor_desc or _format_amp_label(sensor_rating))
    breaker_label = breaker_context_label or fallback_breaker_context
    return ResolvedEquipmentSummary(
        family="etu",
        family_label="ETU",
        resolved_id=f"sensor:{sensor_id}",
        primary_label=trip_unit_label or rating_label,
        secondary_label=breaker_label or rating_label,
        breaker_context=ResolvedBreakerContext(
            label=breaker_label,
            source=breaker_context_source or ("trip_style_sensor_rating" if fallback_breaker_context else None),
            manufacturer_name=manufacturer_name,
            breaker_style_name=trip_style_name,
        ),
        trip_unit=ResolvedTripUnitIdentity(
            manufacturer_name=manufacturer_name,
            trip_type_name=trip_type_name,
            trip_style_name=trip_style_name,
            label=trip_unit_label,
        ),
        rating_context=ResolvedRatingContext(
            label=rating_label,
            sensor_id=sensor_id,
            sensor_desc=sensor_desc,
            sensor_rating=sensor_rating,
        ),
    )


def _build_tmt_resolved_equipment_summary(bundle: dict[str, object]) -> ResolvedEquipmentSummary:
    breaker_label = _join_summary_label(bundle.get("breaker_class"), bundle.get("frame_size"))
    primary_label = _join_summary_label(bundle.get("manufacturer_name"), bundle.get("breaker_name"))
    secondary_label = _join_summary_label(bundle.get("breaker_style_name"), breaker_label)
    rating_label = _join_summary_label("Frame", bundle.get("frame_size"))
    return ResolvedEquipmentSummary(
        family="tmt",
        family_label="TMT",
        resolved_id=f"tmt_frame:{bundle['frame_id']}",
        primary_label=primary_label or bundle.get("breaker_style_name") or breaker_label,
        secondary_label=secondary_label or rating_label,
        breaker_context=ResolvedBreakerContext(
            label=breaker_label,
            source="tmt_frame_context",
            manufacturer_name=bundle.get("manufacturer_name"),
            breaker_class=bundle.get("breaker_class"),
            breaker_name=bundle.get("breaker_name"),
            breaker_style_name=bundle.get("breaker_style_name"),
        ),
        rating_context=ResolvedRatingContext(
            label=rating_label,
            frame_id=int(bundle["frame_id"]),
            frame_size=str(bundle.get("frame_size")) if bundle.get("frame_size") is not None else None,
        ),
    )


def _build_emt_resolved_equipment_summary(bundle: dict[str, object]) -> ResolvedEquipmentSummary:
    breaker_label = _join_summary_label(bundle.get("manufacturer_name"), bundle.get("type_name"), bundle.get("style_name"))
    rating_label = _join_summary_label(bundle.get("frame_desc") or bundle.get("frame_size"), bundle.get("section_name"))
    return ResolvedEquipmentSummary(
        family="emt",
        family_label="EMT",
        resolved_id=f"emt_frame:{bundle['frame_id']}",
        primary_label=breaker_label,
        secondary_label=rating_label,
        breaker_context=ResolvedBreakerContext(
            label=breaker_label,
            source="emt_frame_context",
            manufacturer_name=bundle.get("manufacturer_name"),
            type_name=bundle.get("type_name"),
            style_name=bundle.get("style_name"),
            tcc_number=bundle.get("tcc_number"),
        ),
        rating_context=ResolvedRatingContext(
            label=rating_label,
            frame_id=int(bundle["frame_id"]),
            frame_size=str(bundle.get("frame_size")) if bundle.get("frame_size") is not None else None,
            frame_desc=bundle.get("frame_desc"),
            amp_ratings=[float(value) for value in bundle.get("amp_ratings", []) if value is not None],
            section_id=int(bundle["section_id"]) if bundle.get("section_id") is not None else None,
            section_name=bundle.get("section_name"),
        ),
    )


def _decimal_to_number(value: Decimal):
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return int(normalized)
    return float(normalized)


def _step_decimal(step_value) -> Decimal | None:
    if step_value in (None, 0, 0.0):
        return None

    rounded = round(float(step_value), 6)
    if rounded <= 0:
        return None

    return Decimal(str(rounded)).normalize()


def _expand_numeric_range(values: list[float], step_value) -> list[float]:
    """Expand min/max endpoint pairs into a discrete option list when step metadata exists."""
    if len(values) != 2:
        return values

    step = _step_decimal(step_value)
    if step is None:
        return values

    lower, upper = sorted(Decimal(str(v)) for v in values)
    expanded: list[float] = []
    current = lower
    max_points = 2000

    while current <= upper + (step / Decimal("1000")) and len(expanded) < max_points:
        expanded.append(_decimal_to_number(current))
        current += step

    upper_num = _decimal_to_number(upper)
    if not expanded or expanded[-1] != upper_num:
        expanded.append(upper_num)

    return expanded


def _recover_catalog_pickup_values(
    db: Session,
    sensor_id: int,
    ctx: dict,
    pickup_name: str,
    boundary_values: list[float],
) -> list[float]:
    table_name = _PICKUP_TABLES.get(pickup_name)
    if table_name is None or len(boundary_values) != 2:
        return boundary_values

    lower, upper = sorted(Decimal(str(value)) for value in boundary_values)

    def _query_candidates(same_trip_style: bool) -> list[list[float]]:
        where_clause = "p.sensor_id <> :sensor_id"
        params: dict[str, object] = {
            "sensor_id": sensor_id,
            "lower": lower,
            "upper": upper,
        }

        if same_trip_style:
            trip_style_id = ctx.get("trip_style_id")
            if trip_style_id is None:
                return []
            where_clause += " AND s.trip_style_id = :trip_style_id"
            params["trip_style_id"] = trip_style_id

        rows = db.execute(
            text(
                f"""
                SELECT array_agg(p.value ORDER BY p.value) AS values
                FROM {table_name} p
                JOIN tcc_etu_sensors s ON s.id = p.sensor_id
                WHERE {where_clause}
                GROUP BY p.sensor_id
                HAVING count(*) > 2 AND min(p.value) = :lower AND max(p.value) = :upper
                """
            ),
            params,
        ).fetchall()

        candidates: list[list[float]] = []
        for row in rows:
            values = [float(value) for value in (row.values or [])]
            if values:
                candidates.append(values)
        return candidates

    for same_trip_style in (True, False):
        candidates = _query_candidates(same_trip_style)
        if not candidates:
            continue

        most_common, _ = Counter(tuple(candidate) for candidate in candidates).most_common(1)[0]
        return list(most_common)

    return boundary_values


def _expand_pickup_values(
    db: Session,
    sensor_id: int,
    ctx: dict,
    pickup_name: str,
    values: list[float],
) -> list[float]:
    expanded = _expand_numeric_range(values, _pickup_step(ctx, pickup_name))
    if len(expanded) != 2:
        return expanded
    return _recover_catalog_pickup_values(db, sensor_id, ctx, pickup_name, expanded)


def _dedupe_delay_settings(bands: list[dict] | None) -> list[dict]:
    """Collapse duplicate delay-band rows that map to the same effective setting."""
    if not bands:
        return []

    deduped: list[dict] = []
    seen: set[tuple[object, ...]] = set()

    for band in bands:
        if not isinstance(band, dict):
            continue

        open_time = band.get("open_time")
        label = band.get("label")
        band_name = band.get("band")

        key = (open_time,) if open_time is not None else (label, band_name)
        if key in seen:
            continue

        seen.add(key)
        deduped.append(band)

    return deduped


def _load_delay_band_settings(db: Session, table_name: str, sensor_id: int) -> list[dict]:
    rows = db.execute(
        text(
            f"""
            SELECT band,
                   band_label AS label,
                   open_time,
                   clear_time,
                   COALESCE(is_default, false) AS is_default
            FROM {table_name}
            WHERE sensor_id = :sensor_id
            ORDER BY sort_order NULLS LAST,
                     ordinal NULLS LAST,
                     open_time NULLS LAST,
                     id
            """
        ),
        {"sensor_id": sensor_id},
    ).fetchall()

    return [
        {
            "band": row._mapping.get("band") or "",
            "label": row._mapping.get("label") or row._mapping.get("band") or "",
            "open_time": float(row._mapping.get("open_time")),
            "clear_time": (
                float(row._mapping.get("clear_time"))
                if row._mapping.get("clear_time") is not None else None
            ),
            "is_default": bool(row._mapping.get("is_default")),
        }
        for row in rows
        if row._mapping.get("open_time") is not None
    ]


def _pickup_step(ctx: dict, pickup_name: str):
    primary = ctx.get(f"{pickup_name}_step")
    if primary not in (None, 0, 0.0):
        return primary
    return ctx.get(f"maint_{pickup_name}_step")


def _sensor_rating_limit(ctx: dict) -> float | None:
    rating = ctx.get("rating")
    if rating in (None, ""):
        return None
    try:
        return float(rating)
    except (TypeError, ValueError):
        return None


def _filter_valid_plug_values(values: list[float], sensor_rating: float | None) -> list[float]:
    if sensor_rating is None:
        return values
    return [value for value in values if float(value) <= sensor_rating]


def _enforce_plug_within_sensor_rating(sensor_id: int, plug_rating: float, db: Session) -> None:
    ctx_row = db.execute(
        text("SELECT rating FROM vw_sensor_calc_context WHERE sensor_id = :sid"),
        {"sid": sensor_id},
    ).fetchone()
    if not ctx_row:
        raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} not found")

    sensor_rating = _sensor_rating_limit(_row_mapping(ctx_row))
    if sensor_rating is None:
        return
    if plug_rating > sensor_rating:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Plug rating {plug_rating:g} exceeds sensor rating {sensor_rating:g}. "
                "Plug rating must be less than or equal to the selected sensor rating."
            ),
        )


def _load_direct_delay_band(
    db: Session,
    table_name: str,
    sensor_id: int,
    setting: Optional[float],
):
    if setting is not None:
        matched_row = db.execute(
            text(f"""
                SELECT open_time, clear_time, ordinal, is_default
                FROM {table_name}
                WHERE sensor_id = :sensor_id AND open_time = :setting
                ORDER BY ordinal
                LIMIT 1
            """),
            {"sensor_id": sensor_id, "setting": setting},
        ).fetchone()
        if matched_row is not None:
            return matched_row

    default_row = db.execute(
        text(f"""
            SELECT open_time, clear_time, ordinal, is_default
            FROM {table_name}
            WHERE sensor_id = :sensor_id AND is_default = TRUE
            ORDER BY ordinal
            LIMIT 1
        """),
        {"sensor_id": sensor_id},
    ).fetchone()
    if default_row is not None:
        return default_row

    return db.execute(
        text(f"""
            SELECT open_time, clear_time, ordinal, is_default
            FROM {table_name}
            WHERE sensor_id = :sensor_id
            ORDER BY ordinal
            LIMIT 1
        """),
        {"sensor_id": sensor_id},
    ).fetchone()


def _band_row_to_delay_surface(band_row) -> tuple[Optional[float], Optional[float], Optional[float]]:
    if band_row is None:
        return None, None, None

    mapping = band_row._mapping if hasattr(band_row, "_mapping") else band_row
    open_time = mapping.get("open_time") if isinstance(mapping, dict) else getattr(band_row, "open_time", None)
    clear_time = mapping.get("clear_time") if isinstance(mapping, dict) else getattr(band_row, "clear_time", None)

    expected_time = float(open_time) if open_time is not None else None
    clear_value = float(clear_time) if clear_time is not None else None

    if expected_time is not None and clear_value is not None:
        time_low = min(expected_time, clear_value)
        time_high = max(expected_time, clear_value)
    else:
        time_low = expected_time
        time_high = clear_value

    return expected_time, time_low, time_high


def _build_cascade_where(filters: dict[str, Optional[int]], exclude: set[str] | None = None) -> tuple[str, dict[str, int]]:
    exclude = exclude or set()
    clauses: list[str] = []
    params: dict[str, int] = {}

    for field in ("manufacturer_id", "trip_type_id", "trip_style_id", "sensor_id"):
        if field in exclude:
            continue
        value = filters.get(field)
        if value is None:
            continue
        clauses.append(f"{field} = :{field}")
        params[field] = value

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_sql, params


def _cascade_level(filters: dict[str, Optional[int]]) -> str:
    if filters.get("sensor_id") is not None:
        return "sensors"
    if filters.get("trip_style_id") is not None:
        return "trip_styles"
    if filters.get("trip_type_id") is not None:
        return "trip_types"
    if filters.get("manufacturer_id") is not None:
        return "manufacturers"
    return "manufacturers"


_DELAY_ELEMENT_SPECS = [
    ("ltd", "LTD", "ltd_open", 3.0),
    ("std", "STD", "std_open", 1.5),
    ("gfd", "GFD", "gfd_open", 1.5),
]


def _generate_nominal_plot_curves(
    db: Session,
    sensor_id: int,
    plug_rating: float,
    ltpu_setting: Optional[float],
    ltd_setting: Optional[float],
    stpu_setting: Optional[float],
    std_setting: Optional[float],
    inst_setting: Optional[float],
    gfpu_setting: Optional[float],
    gfd_setting: Optional[float],
    multiplier_value: Optional[float] = None,
    c_factor: Optional[float] = None,
) -> tuple[list[PlotCurve], list[str], Optional[dict[str, object]]]:
    """Generate the nominal curves used for delay-band interpolation."""
    curves: list[PlotCurve] = []
    warnings: list[str] = []
    maint_profile: Optional[dict[str, object]] = None

    try:
        from apex_calc_engine.services.calc_engine import ETUPickupCalculator
        from apex_calc_engine.services.calc_engine import ETULTDCalculator
        from apex_calc_engine.services.calc_engine import IEEEInverseTimeSolver

        pickup_calc = ETUPickupCalculator(db, sensor_id)
        plug_id = None
        if plug_rating:
            for plug in pickup_calc.get_plugs_for_style():
                if plug["value"] == int(plug_rating):
                    plug_id = plug["id"]
                    break
            if plug_id is None:
                logger.warning(
                    "plug_rating %s not found for sensor %s; "
                    "PLUGTAP curves may be incorrect",
                    plug_rating, sensor_id,
                )

        pickups = pickup_calc.calculate(
            plug_id=plug_id,
            ltpu_setting=ltpu_setting,
            stpu_setting=stpu_setting,
            inst_setting=inst_setting,
            gfpu_setting=gfpu_setting,
            multiplier_value=multiplier_value,
            c_factor=c_factor,
        )
        maint_profile = pickups.maint_profile

        ltpu_i = pickups.ltpu.current if pickups.ltpu else 0.0
        stpu_i = pickups.stpu.current if pickups.stpu else 0.0
        inst_i = pickups.inst.current if pickups.inst else 0.0
        gfpu_i = pickups.gfpu.current if pickups.gfpu else 0.0

        try:
            ltd_calc = ETULTDCalculator(db, sensor_id)
            ltd_info = ltd_calc.get_ltd_info()
            if ltd_info and ltpu_i > 0:
                ltd_param_ord = ltd_info[0]["ordinal"]
                bands = ltd_calc.get_band_info()
                band_ord = bands[0]["ordinal"] if bands else 1
                if ltd_setting is not None and bands:
                    matched = [
                        band for band in bands
                        if band["open_time"] is not None
                        and abs(band["open_time"] - ltd_setting) < 1e-6
                    ]
                    if matched:
                        band_ord = matched[0]["ordinal"]
                    else:
                        logger.warning(
                            "ltd_setting %s not matched to any band for sensor %s; "
                            "using first available band (ordinal %s)",
                            ltd_setting, sensor_id, band_ord,
                        )

                for is_clear, phase in [(False, "open"), (True, "clear")]:
                    points = ltd_calc.generate_curve(
                        ltd_param_ordinal=ltd_param_ord,
                        ltd_band_ordinal=band_ord,
                        pickup_current=ltpu_i,
                        is_clear=is_clear,
                    )
                    if points:
                        curves.append(PlotCurve(
                            id=f"ltd_{phase}",
                            element="LTD",
                            phase=phase,
                            line_style="solid" if phase == "open" else "dashed",
                            points=[PlotCurvePoint(amps=p.amps, seconds=p.seconds) for p in points],
                        ))
        except Exception as exc:
            logger.warning("LTD curve generation failed: %s", exc)
            warnings.append(f"LTD curve unavailable: {exc}")

        try:
            ieee = IEEEInverseTimeSolver(db)
            std_pickup = stpu_i if stpu_i > 0 else ltpu_i
            if std_pickup > 0:
                std_eqs = ieee.get_equation_info(sensor_id, "std")
                std_ord = std_eqs[0]["ordinal"] if std_eqs else 1
                std_time_dial = float(std_setting) if std_setting else 1.0

                for variant, phase in [("fd_open", "open"), ("fd_clear", "clear")]:
                    points = ieee.generate_curve(
                        sensor_id=sensor_id,
                        ordinal=std_ord,
                        variant=variant,
                        pickup_current=std_pickup,
                        time_dial=std_time_dial,
                    )
                    if points:
                        curves.append(PlotCurve(
                            id=f"std_{phase}",
                            element="STD",
                            phase=phase,
                            line_style="solid" if phase == "open" else "dashed",
                            points=[PlotCurvePoint(amps=p.amps, seconds=p.seconds) for p in points],
                        ))

            if inst_i > 0:
                inst_open_t = 0.05
                inst_clear_t = 0.08
                max_amps = inst_i * 5
                for phase, seconds in [("open", inst_open_t), ("clear", inst_clear_t)]:
                    curves.append(PlotCurve(
                        id=f"inst_{phase}",
                        element="INST",
                        phase=phase,
                        line_style="solid" if phase == "open" else "dashed",
                        points=[
                            PlotCurvePoint(amps=inst_i, seconds=seconds),
                            PlotCurvePoint(amps=max_amps, seconds=seconds),
                        ],
                    ))

            if gfpu_i > 0:
                gfd_eqs = ieee.get_equation_info(sensor_id, "gfd")
                gfd_ord = gfd_eqs[0]["ordinal"] if gfd_eqs else 1
                gfd_time_dial = float(gfd_setting) if gfd_setting else 1.0

                for variant, phase in [("fd_open", "open"), ("fd_clear", "clear")]:
                    points = ieee.generate_curve(
                        sensor_id=sensor_id,
                        ordinal=gfd_ord,
                        variant=variant,
                        pickup_current=gfpu_i,
                        time_dial=gfd_time_dial,
                        equation_type="gfd",
                    )
                    if points:
                        curves.append(PlotCurve(
                            id=f"gfd_{phase}",
                            element="GFD",
                            phase=phase,
                            line_style="solid" if phase == "open" else "dashed",
                            points=[PlotCurvePoint(amps=p.amps, seconds=p.seconds) for p in points],
                        ))
        except Exception as exc:
            logger.warning("IEEE curve generation failed: %s", exc)
            warnings.append(f"Curve generation unavailable: {exc}")
    except Exception as exc:
        logger.warning("Curve generation failed: %s", exc)
        warnings.append(f"Curve generation unavailable: {exc}")

    return curves, warnings, maint_profile


def _resolve_delay_surface(
    curves: list[PlotCurve],
    curve_ref: str,
    expected_current: float,
    fallback_open: Optional[float] = None,
    fallback_clear: Optional[float] = None,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    expected_time = fallback_open
    time_low = fallback_open
    time_high = fallback_clear

    ref_curve = next((curve for curve in curves if curve.id == curve_ref), None)
    if ref_curve and ref_curve.points:
        interpolated_open = _interpolate_time(ref_curve.points, expected_current)
        if interpolated_open is not None:
            expected_time = interpolated_open
            time_low = interpolated_open

    clear_ref = curve_ref.replace("_open", "_clear")
    clear_curve = next((curve for curve in curves if curve.id == clear_ref), None)
    if clear_curve and clear_curve.points:
        interpolated_clear = _interpolate_time(clear_curve.points, expected_current)
        if interpolated_clear is not None:
            time_high = interpolated_clear

    return expected_time, time_low, time_high


def _authoritative_delay_surface(
    db: Session,
    sensor_id: int,
    element_key: str,
    setting: Optional[float],
    curves: list[PlotCurve],
    expected_current: float,
    maint_mode: bool = False,
    maint_profile: Optional[dict[str, object]] = None,
    fallback_open: Optional[float] = None,
    fallback_clear: Optional[float] = None,
) -> tuple[Optional[float], Optional[float], Optional[float], str]:
    if element_key == "ltd":
        band_row = _load_direct_delay_band(db, "tcc_etu_ltd_bands", sensor_id, setting)
        if band_row is not None:
            expected_time, time_low, time_high = _band_row_to_delay_surface(band_row)
            return expected_time, time_low, time_high, "band_table"

    if element_key == "std":
        band_row = _load_direct_delay_band(db, "tcc_etu_std_bands", sensor_id, setting)
        if band_row is not None:
            expected_time, time_low, time_high = _band_row_to_delay_surface(band_row)
            return expected_time, time_low, time_high, "band_table"

    if element_key == "gfd":
        if maint_mode and maint_profile:
            direct_open = maint_profile.get("gf_delay_opening")
            direct_clear = maint_profile.get("gf_delay_clearing")
            if direct_open is not None or direct_clear is not None:
                expected_time = direct_open
                if direct_open is not None and direct_clear is not None:
                    time_low = min(direct_open, direct_clear)
                    time_high = max(direct_open, direct_clear)
                else:
                    time_low = direct_open
                    time_high = direct_clear
                return expected_time, time_low, time_high, "maint_profile"

        band_row = _load_direct_delay_band(db, "tcc_etu_gfd_bands", sensor_id, setting)
        if band_row is not None:
            expected_time, time_low, time_high = _band_row_to_delay_surface(band_row)
            return expected_time, time_low, time_high, "band_table"

    expected_time, time_low, time_high = _resolve_delay_surface(
        curves=curves,
        curve_ref=f"{element_key}_open",
        expected_current=expected_current,
        fallback_open=fallback_open,
        fallback_clear=fallback_clear,
    )
    return expected_time, time_low, time_high, "curve_interpolation"


_TMT_STYLE_MODELS = {
    "ICCB": BrkICCBStyle,
    "MCCB": BrkMCCBStyle,
    "PCB": BrkPCBStyle,
}


def _float_matches(left: Optional[float], right: Optional[float], tolerance: float = 1e-6) -> bool:
    if left is None or right is None:
        return False
    return abs(float(left) - float(right)) <= tolerance


def _resolve_tmt_breaker_context(db: Session, frame: TMTFrame) -> dict[str, object]:
    breaker_class = (frame.breaker_class or "").upper() or None
    style_model = _TMT_STYLE_MODELS.get(breaker_class) if breaker_class else None
    style = None

    if style_model is not None:
        style = db.query(style_model).filter(style_model.id == frame.breaker_style_id).one_or_none()
    else:
        for fallback_model in _TMT_STYLE_MODELS.values():
            style = db.query(fallback_model).filter(fallback_model.id == frame.breaker_style_id).one_or_none()
            if style is not None:
                break

    breaker = getattr(style, "breaker", None) if style is not None else None
    manufacturer = getattr(breaker, "manufacturer", None) if breaker is not None else None
    standard = getattr(style, "standard", None) if style is not None else None

    return {
        "manufacturer_name": getattr(manufacturer, "name", None),
        "breaker_name": getattr(breaker, "name", None),
        "breaker_style_name": getattr(style, "frame", None),
        "standard": float(standard) if standard is not None else None,
    }


def _load_tmt_contract_bundle(db: Session, frame_id: int) -> dict[str, object]:
    try:
        generator = TMTCurveGenerator(db, frame_id=frame_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail=f"TMT frame {frame_id} not found") from exc

    frame = generator.frame
    breaker_context = _resolve_tmt_breaker_context(db, frame)
    available_trip_classes = generator.get_available_classes()
    amp_ratings = generator.get_amps()
    settings = generator.get_settings()
    thermal_adjustments = generator.get_thermal_adjustments()

    return {
        "generator": generator,
        "frame_id": frame.id,
        "breaker_style_id": frame.breaker_style_id,
        "breaker_class": frame.breaker_class,
        "frame_size": frame.size,
        "manufacturer_name": breaker_context["manufacturer_name"],
        "breaker_name": breaker_context["breaker_name"],
        "breaker_style_name": breaker_context["breaker_style_name"],
        "standard": breaker_context["standard"],
        "available_trip_classes": available_trip_classes,
        "amp_ratings": amp_ratings,
        "settings": settings,
        "thermal_adjustments": thermal_adjustments,
    }


def _resolve_tmt_selected_options(
    bundle: dict[str, object],
    amp_rating: Optional[float],
    setting_value: Optional[float],
    thermal_adjustment: Optional[float],
) -> tuple[Optional[dict[str, object]], Optional[dict[str, object]], Optional[float], list[str]]:
    warnings: list[str] = []

    matched_amp = None
    if amp_rating is not None:
        matched_amp = next(
            (amp for amp in bundle["amp_ratings"] if _float_matches(amp.get("rating"), amp_rating)),
            None,
        )
        if matched_amp is None:
            raise HTTPException(
                status_code=400,
                detail=f"Amp rating {amp_rating} is not available for TMT frame {bundle['frame_id']}",
            )

    matched_setting = None
    if setting_value is not None:
        matched_setting = next(
            (
                setting for setting in bundle["settings"]
                if _float_matches(setting.get("value"), setting_value)
            ),
            None,
        )
        if matched_setting is None:
            raise HTTPException(
                status_code=400,
                detail=f"Setting {setting_value} is not available for TMT frame {bundle['frame_id']}",
            )

    matched_thermal_adjustment = None
    if thermal_adjustment is not None:
        matched_thermal_adjustment = next(
            (
                adjustment for adjustment in bundle["thermal_adjustments"]
                if _float_matches(adjustment, thermal_adjustment)
            ),
            None,
        )
        if matched_thermal_adjustment is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Thermal adjustment {thermal_adjustment} is not available for "
                    f"TMT frame {bundle['frame_id']}"
                ),
            )

    if any(value is not None for value in (amp_rating, setting_value, thermal_adjustment)):
        warnings.append(
            "TMT selections validated and surfaced in metadata; the plotted curve remains the nominal class curve."
        )

    return matched_amp, matched_setting, matched_thermal_adjustment, warnings


def _normalize_scalar(value):
    if isinstance(value, Decimal):
        return _decimal_to_number(value)
    return value


def _normalize_mapping(data: dict[str, object]) -> dict[str, object]:
    return {key: _normalize_scalar(value) for key, value in data.items()}


def _get_table_columns(db: Session, table_name: str) -> set[str]:
    rows = db.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table_name
            """
        ),
        {"table_name": table_name},
    ).fetchall()
    return {row[0] for row in rows}


def _pick_required_column(table_name: str, columns: set[str], label: str, candidates: tuple[str, ...]) -> str:
    for candidate in candidates:
        if candidate in columns:
            return candidate

    raise HTTPException(
        status_code=503,
        detail=(
            f"EMT catalog table {table_name} is present but missing a usable {label} column. "
            "This EMT surface remains migration-gated in the current environment."
        ),
    )


def _pick_optional_column(columns: set[str], candidates: tuple[str, ...]) -> Optional[str]:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _select_expr(table_alias: str, column_name: Optional[str], result_alias: str) -> str:
    if column_name:
        return f"{table_alias}.{column_name} AS {result_alias}"
    return f"NULL AS {result_alias}"


def _resolve_emt_contract_columns(db: Session) -> dict[str, dict[str, Optional[str]]]:
    table_columns = {
        "tcc_emt": _get_table_columns(db, "tcc_emt"),
        "tcc_emt_frames": _get_table_columns(db, "tcc_emt_frames"),
        "tcc_emt_frame_amps": _get_table_columns(db, "tcc_emt_frame_amps"),
        "tcc_emt_sections": _get_table_columns(db, "tcc_emt_sections"),
        "tcc_emt_pickups": _get_table_columns(db, "tcc_emt_pickups"),
        "tcc_emt_band_names": _get_table_columns(db, "tcc_emt_band_names"),
        "tcc_emt_curves": _get_table_columns(db, "tcc_emt_curves"),
    }

    if any(not columns for columns in table_columns.values()):
        raise HTTPException(
            status_code=503,
            detail=(
                "EMT catalog tables are not available in the current database. "
                "The EMT route surface is implemented but remains migration-gated."
            ),
        )

    emt_cols = table_columns["tcc_emt"]
    frame_cols = table_columns["tcc_emt_frames"]
    amp_cols = table_columns["tcc_emt_frame_amps"]
    section_cols = table_columns["tcc_emt_sections"]
    pickup_cols = table_columns["tcc_emt_pickups"]
    band_cols = table_columns["tcc_emt_band_names"]
    curve_cols = table_columns["tcc_emt_curves"]

    return {
        "emt": {
            "manufacturer_id": _pick_required_column("tcc_emt", emt_cols, "manufacturer id", ("manufacturer_id", "mfr_id")),
            "type_name": _pick_required_column("tcc_emt", emt_cols, "type name", ("type_name", "type")),
            "style_name": _pick_required_column("tcc_emt", emt_cols, "style name", ("style_name", "style")),
            "tcc_number": _pick_required_column("tcc_emt", emt_cols, "TCC number", ("tcc_number", "tcc_no", "tccnumber")),
            "trip_char": _pick_required_column("tcc_emt", emt_cols, "trip characteristic", ("trip_char",)),
            "trip_plug": _pick_required_column("tcc_emt", emt_cols, "trip plug", ("trip_plug",)),
        },
        "frames": {
            "emt_id": _pick_required_column("tcc_emt_frames", frame_cols, "EMT parent", ("emt_id", "style_id")),
            "frame_size": _pick_required_column("tcc_emt_frames", frame_cols, "frame size", ("frame_size", "size", "framesize")),
            "frame_desc": _pick_required_column("tcc_emt_frames", frame_cols, "frame description", ("frame_desc", "frame_description", "framedesc")),
        },
        "amps": {
            "frame_id": _pick_required_column("tcc_emt_frame_amps", amp_cols, "frame parent", ("frame_id", "frameid")),
            "rating": _pick_required_column("tcc_emt_frame_amps", amp_cols, "amp rating", ("rating", "trip_amp", "tripamp")),
        },
        "sections": {
            "frame_id": _pick_required_column("tcc_emt_sections", section_cols, "frame parent", ("frame_id", "frameid")),
            "name": _pick_optional_column(section_cols, ("name", "section_name")),
            "sec_char": _pick_optional_column(section_cols, ("sec_char", "section_char")),
            "curve_type": _pick_optional_column(section_cols, ("curve_type", "curvetype")),
            "pickup_calc": _pick_optional_column(section_cols, ("pickup_calc", "pickupcalc")),
            "pickup_setting": _pick_optional_column(section_cols, ("pickup_setting", "pickupsetting")),
            "step_size": _pick_optional_column(section_cols, ("step_size", "stepsize")),
            "current_calc": _pick_optional_column(section_cols, ("current_calc", "currentcalc")),
            "pickup_tol_lo": _pick_optional_column(section_cols, ("pickup_tol_lo", "pickup_toler_low", "pickuptolerlow")),
            "pickup_tol_hi": _pick_optional_column(section_cols, ("pickup_tol_hi", "pickup_toler_high", "pickuptolerhigh")),
        },
        "pickups": {
            "section_id": _pick_required_column("tcc_emt_pickups", pickup_cols, "section parent", ("section_id", "sec_id", "secid")),
            "setting": _pick_optional_column(pickup_cols, ("setting",)),
            "description": _pick_optional_column(pickup_cols, ("description", "label")),
        },
        "bands": {
            "section_id": _pick_required_column("tcc_emt_band_names", band_cols, "section parent", ("section_id", "sec_id", "secid")),
            "band_name": _pick_optional_column(band_cols, ("band_name", "name")),
            "ordinal": _pick_optional_column(band_cols, ("ordinal",)),
            "current_at": _pick_optional_column(band_cols, ("current_at", "currentat")),
        },
        "curves": {
            "band_id": _pick_required_column("tcc_emt_curves", curve_cols, "band parent", ("band_id", "parent_id", "parentid")),
            "class": _pick_optional_column(curve_cols, ("class", "class_")),
        },
    }


def _search_emt_frames(
    db: Session,
    manufacturer_id: Optional[int] = None,
    trip_char: Optional[int] = None,
    trip_plug: Optional[int] = None,
    q: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, object]]:
    cols = _resolve_emt_contract_columns(db)
    params: dict[str, object] = {"limit": limit}
    conditions: list[str] = []

    if manufacturer_id is not None:
        conditions.append(f"e.{cols['emt']['manufacturer_id']} = :manufacturer_id")
        params["manufacturer_id"] = manufacturer_id

    if trip_char is not None:
        conditions.append(f"e.{cols['emt']['trip_char']} = :trip_char")
        params["trip_char"] = trip_char

    if trip_plug is not None:
        conditions.append(f"e.{cols['emt']['trip_plug']} = :trip_plug")
        params["trip_plug"] = trip_plug

    if q:
        conditions.append(
            "(" 
            f"LOWER(COALESCE(CAST(e.{cols['emt']['type_name']} AS TEXT), '')) LIKE :q OR "
            f"LOWER(COALESCE(CAST(e.{cols['emt']['style_name']} AS TEXT), '')) LIKE :q OR "
            f"LOWER(COALESCE(CAST(f.{cols['frames']['frame_desc']} AS TEXT), '')) LIKE :q"
            ")"
        )
        params["q"] = f"%{q.lower()}%"

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = text(
        f"""
        SELECT
            e.id AS emt_id,
            f.id AS frame_id,
            e.{cols['emt']['manufacturer_id']} AS manufacturer_id,
            m.name AS manufacturer_name,
            e.{cols['emt']['type_name']} AS type_name,
            e.{cols['emt']['style_name']} AS style_name,
            e.{cols['emt']['tcc_number']} AS tcc_number,
            e.{cols['emt']['trip_char']} AS trip_char,
            e.{cols['emt']['trip_plug']} AS trip_plug,
            f.{cols['frames']['frame_size']} AS frame_size,
            f.{cols['frames']['frame_desc']} AS frame_desc,
            COALESCE(amp_counts.amp_rating_count, 0) AS amp_rating_count,
            COALESCE(sec_counts.section_count, 0) AS section_count
        FROM tcc_emt_frames f
        INNER JOIN tcc_emt e ON f.{cols['frames']['emt_id']} = e.id
        LEFT JOIN tcc_manufacturers m ON m.id = e.{cols['emt']['manufacturer_id']}
        LEFT JOIN (
            SELECT {cols['amps']['frame_id']} AS frame_id, COUNT(*) AS amp_rating_count
            FROM tcc_emt_frame_amps
            GROUP BY {cols['amps']['frame_id']}
        ) amp_counts ON amp_counts.frame_id = f.id
        LEFT JOIN (
            SELECT {cols['sections']['frame_id']} AS frame_id, COUNT(*) AS section_count
            FROM tcc_emt_sections
            GROUP BY {cols['sections']['frame_id']}
        ) sec_counts ON sec_counts.frame_id = f.id
        {where_sql}
        ORDER BY m.name NULLS LAST, e.{cols['emt']['type_name']}, e.{cols['emt']['style_name']}, f.id
        LIMIT :limit
        """
    )

    rows = db.execute(sql, params).fetchall()
    return [_normalize_mapping(dict(row._mapping)) for row in rows]


def _load_emt_frame_context_bundle(db: Session, frame_id: int) -> dict[str, object]:
    cols = _resolve_emt_contract_columns(db)

    frame_row = db.execute(
        text(
            f"""
            SELECT
                e.id AS emt_id,
                f.id AS frame_id,
                e.{cols['emt']['manufacturer_id']} AS manufacturer_id,
                m.name AS manufacturer_name,
                e.{cols['emt']['type_name']} AS type_name,
                e.{cols['emt']['style_name']} AS style_name,
                e.{cols['emt']['tcc_number']} AS tcc_number,
                e.{cols['emt']['trip_char']} AS trip_char,
                e.{cols['emt']['trip_plug']} AS trip_plug,
                f.{cols['frames']['frame_size']} AS frame_size,
                f.{cols['frames']['frame_desc']} AS frame_desc
            FROM tcc_emt_frames f
            INNER JOIN tcc_emt e ON f.{cols['frames']['emt_id']} = e.id
            LEFT JOIN tcc_manufacturers m ON m.id = e.{cols['emt']['manufacturer_id']}
            WHERE f.id = :frame_id
            """
        ),
        {"frame_id": frame_id},
    ).fetchone()

    if frame_row is None:
        raise HTTPException(status_code=404, detail=f"EMT frame {frame_id} not found")

    amp_rows = db.execute(
        text(
            f"""
            SELECT {cols['amps']['rating']} AS rating
            FROM tcc_emt_frame_amps
            WHERE {cols['amps']['frame_id']} = :frame_id
            ORDER BY {cols['amps']['rating']}
            """
        ),
        {"frame_id": frame_id},
    ).fetchall()

    section_rows = db.execute(
        text(
            f"""
            SELECT
                s.id AS section_id,
                {_select_expr('s', cols['sections']['name'], 'name')},
                {_select_expr('s', cols['sections']['sec_char'], 'sec_char')},
                {_select_expr('s', cols['sections']['curve_type'], 'curve_type')},
                {_select_expr('s', cols['sections']['pickup_calc'], 'pickup_calc')},
                {_select_expr('s', cols['sections']['pickup_setting'], 'pickup_setting')},
                {_select_expr('s', cols['sections']['step_size'], 'step_size')},
                {_select_expr('s', cols['sections']['current_calc'], 'current_calc')},
                {_select_expr('s', cols['sections']['pickup_tol_lo'], 'pickup_tol_lo')},
                {_select_expr('s', cols['sections']['pickup_tol_hi'], 'pickup_tol_hi')},
                COALESCE(band_counts.band_count, 0) AS band_count,
                COALESCE(pickup_counts.pickup_count, 0) AS pickup_count
            FROM tcc_emt_sections s
            LEFT JOIN (
                SELECT {cols['bands']['section_id']} AS section_id, COUNT(*) AS band_count
                FROM tcc_emt_band_names
                GROUP BY {cols['bands']['section_id']}
            ) band_counts ON band_counts.section_id = s.id
            LEFT JOIN (
                SELECT {cols['pickups']['section_id']} AS section_id, COUNT(*) AS pickup_count
                FROM tcc_emt_pickups
                GROUP BY {cols['pickups']['section_id']}
            ) pickup_counts ON pickup_counts.section_id = s.id
            WHERE s.{cols['sections']['frame_id']} = :frame_id
            ORDER BY s.id
            """
        ),
        {"frame_id": frame_id},
    ).fetchall()

    return {
        **_normalize_mapping(dict(frame_row._mapping)),
        "amp_ratings": [_normalize_scalar(row._mapping["rating"]) for row in amp_rows],
        "sections": [_normalize_mapping(dict(row._mapping)) for row in section_rows],
    }


def _load_emt_section_settings_bundle(db: Session, section_id: int) -> dict[str, object]:
    cols = _resolve_emt_contract_columns(db)

    section_row = db.execute(
        text(
            f"""
            SELECT
                s.id AS section_id,
                {_select_expr('s', cols['sections']['name'], 'name')},
                {_select_expr('s', cols['sections']['sec_char'], 'sec_char')},
                {_select_expr('s', cols['sections']['curve_type'], 'curve_type')},
                {_select_expr('s', cols['sections']['pickup_calc'], 'pickup_calc')},
                {_select_expr('s', cols['sections']['pickup_setting'], 'pickup_setting')},
                {_select_expr('s', cols['sections']['step_size'], 'step_size')},
                {_select_expr('s', cols['sections']['current_calc'], 'current_calc')},
                {_select_expr('s', cols['sections']['pickup_tol_lo'], 'pickup_tol_lo')},
                {_select_expr('s', cols['sections']['pickup_tol_hi'], 'pickup_tol_hi')}
            FROM tcc_emt_sections s
            WHERE s.id = :section_id
            """
        ),
        {"section_id": section_id},
    ).fetchone()

    if section_row is None:
        raise HTTPException(status_code=404, detail=f"EMT section {section_id} not found")

    pickups = db.execute(
        text(
            f"""
            SELECT
                {_select_expr('p', cols['pickups']['setting'], 'setting')},
                {_select_expr('p', cols['pickups']['description'], 'description')}
            FROM tcc_emt_pickups p
            WHERE p.{cols['pickups']['section_id']} = :section_id
            ORDER BY p.{cols['pickups']['setting']} NULLS LAST, p.{cols['pickups']['description']} NULLS LAST
            """
        ),
        {"section_id": section_id},
    ).fetchall()

    band_rows = db.execute(
        text(
            f"""
            SELECT
                b.id AS band_id,
                {_select_expr('b', cols['bands']['band_name'], 'band_name')},
                {_select_expr('b', cols['bands']['ordinal'], 'ordinal')},
                {_select_expr('b', cols['bands']['current_at'], 'current_at')}
            FROM tcc_emt_band_names b
            WHERE b.{cols['bands']['section_id']} = :section_id
            ORDER BY b.id
            """
        ),
        {"section_id": section_id},
    ).fetchall()

    bands: list[dict[str, object]] = []
    for band_row in band_rows:
        band = _normalize_mapping(dict(band_row._mapping))
        curve_stats = db.execute(
            text(
                f"""
                SELECT
                    COUNT(*) AS curve_point_count,
                    ARRAY_AGG(DISTINCT {cols['curves']['class']} ORDER BY {cols['curves']['class']})
                        FILTER (WHERE {cols['curves']['class']} IS NOT NULL) AS curve_classes
                FROM tcc_emt_curves
                WHERE {cols['curves']['band_id']} = :band_id
                """
            ),
            {"band_id": band["band_id"]},
        ).fetchone()

        curve_data = dict(curve_stats._mapping) if curve_stats is not None else {}
        classes = curve_data.get("curve_classes") or []
        band["curve_point_count"] = int(curve_data.get("curve_point_count") or 0)
        band["curve_classes"] = [int(value) for value in classes]
        bands.append(band)

    return {
        **_normalize_mapping(dict(section_row._mapping)),
        "pickups": [_normalize_mapping(dict(row._mapping)) for row in pickups],
        "bands": bands,
    }


def _emt_curve_class_label(curve_class: Optional[int]) -> Optional[str]:
    if curve_class == 0:
        return "opening"
    if curve_class == 1:
        return "clearing"
    if curve_class is None:
        return None
    return f"class_{curve_class}"


def _emt_curve_line_style(curve_class: Optional[int]) -> str:
    if curve_class == 1:
        return "dashed"
    return "solid"


def _load_emt_plot_bundle(db: Session, section_id: int, band_id: int) -> dict[str, object]:
    cols = _resolve_emt_contract_columns(db)

    band_row = db.execute(
        text(
            f"""
            SELECT
                e.id AS emt_id,
                f.id AS frame_id,
                s.id AS section_id,
                b.id AS band_id,
                e.{cols['emt']['manufacturer_id']} AS manufacturer_id,
                m.name AS manufacturer_name,
                e.{cols['emt']['type_name']} AS type_name,
                e.{cols['emt']['style_name']} AS style_name,
                e.{cols['emt']['tcc_number']} AS tcc_number,
                f.{cols['frames']['frame_size']} AS frame_size,
                f.{cols['frames']['frame_desc']} AS frame_desc,
                {_select_expr('s', cols['sections']['name'], 'section_name')},
                {_select_expr('s', cols['sections']['sec_char'], 'sec_char')},
                {_select_expr('s', cols['sections']['curve_type'], 'curve_type')},
                {_select_expr('s', cols['sections']['pickup_calc'], 'pickup_calc')},
                {_select_expr('s', cols['sections']['pickup_setting'], 'pickup_setting')},
                {_select_expr('s', cols['sections']['current_calc'], 'current_calc')},
                {_select_expr('b', cols['bands']['band_name'], 'band_name')},
                {_select_expr('b', cols['bands']['ordinal'], 'band_ordinal')},
                {_select_expr('b', cols['bands']['current_at'], 'current_at')}
            FROM tcc_emt_band_names b
            INNER JOIN tcc_emt_sections s ON b.{cols['bands']['section_id']} = s.id
            INNER JOIN tcc_emt_frames f ON s.{cols['sections']['frame_id']} = f.id
            INNER JOIN tcc_emt e ON f.{cols['frames']['emt_id']} = e.id
            LEFT JOIN tcc_manufacturers m ON m.id = e.{cols['emt']['manufacturer_id']}
            WHERE s.id = :section_id AND b.id = :band_id
            """
        ),
        {"section_id": section_id, "band_id": band_id},
    ).fetchone()

    if band_row is None:
        raise HTTPException(
            status_code=404,
            detail=f"EMT band {band_id} was not found for EMT section {section_id}",
        )

    curve_rows = db.execute(
        text(
            f"""
            SELECT
                {_select_expr('c', cols['curves']['class'], 'curve_class')},
                c.current_amp AS current_amp,
                c.time_sec AS time_sec
            FROM tcc_emt_curves c
            WHERE c.{cols['curves']['band_id']} = :band_id
            ORDER BY c.{cols['curves']['class']} NULLS FIRST, c.current_amp, c.time_sec
            """
        ),
        {"band_id": band_id},
    ).fetchall()

    if not curve_rows:
        raise HTTPException(status_code=404, detail=f"No EMT curve points found for band {band_id}")

    grouped_curves: dict[Optional[int], list[dict[str, object]]] = {}
    for row in curve_rows:
        normalized = _normalize_mapping(dict(row._mapping))
        curve_class = normalized.get("curve_class")
        if curve_class is not None:
            curve_class = int(curve_class)
            normalized["curve_class"] = curve_class
        grouped_curves.setdefault(curve_class, []).append(normalized)

    available_curve_classes = [curve_class for curve_class in grouped_curves.keys() if curve_class is not None]
    available_curve_classes.sort()

    return {
        **_normalize_mapping(dict(band_row._mapping)),
        "available_curve_classes": available_curve_classes,
        "grouped_curves": grouped_curves,
    }


# ──────────────────────────────────────────────
# GET /catalog/status — Live Catalog Availability
# ──────────────────────────────────────────────

@router.get("/catalog/status")
def get_catalog_status(db: Session = Depends(get_db)):
    """Report whether the Supabase-backed catalog is available for live browsing.

    Returns a compact status object the demo UI can use to decide whether
    to enable live cascade browsing or fall back to built-in presets.
    """
    try:
        row = db.execute(
            text(
                "SELECT "
                "  COUNT(DISTINCT manufacturer_id) AS manufacturer_count, "
                "  COUNT(DISTINCT sensor_id)       AS sensor_count "
                "FROM vw_trip_unit_cascade"
            )
        ).fetchone()
        data = dict(row._mapping) if row else {}
        return {
            "catalog": "live",
            "manufacturer_count": data.get("manufacturer_count", 0),
            "sensor_count": data.get("sensor_count", 0),
        }
    except Exception as exc:
        logger.warning("Catalog status check failed: %s", exc)
        return {
            "catalog": "unavailable",
            "manufacturer_count": 0,
            "sensor_count": 0,
            "error": str(exc),
        }


# ──────────────────────────────────────────────
# GET /cascade — Cascade Drill-Down Selection
# ──────────────────────────────────────────────

@router.get("/cascade", response_model=CascadeResponse)
def get_cascade(
    manufacturer_id: Optional[int] = Query(None, description="Filter by manufacturer"),
    trip_type_id: Optional[int] = Query(None, description="Filter by trip type"),
    trip_style_id: Optional[int] = Query(None, description="Filter by trip style"),
    sensor_id: Optional[int] = Query(None, description="Filter to specific sensor"),
    db: Session = Depends(get_db),
):
    """
    DLL-style cross-filtered ETU selection packet.

    The original Access and DLL lookup queries filter the manufacturer, type,
    style, and sensor path against one another rather than only allowing a
    single forward drill-down. This endpoint mirrors that behavior by returning
    filtered option lists for the entire ETU selection path based on the
    current selection state.
    """
    filters = {
        "manufacturer_id": manufacturer_id,
        "trip_type_id": trip_type_id,
        "trip_style_id": trip_style_id,
        "sensor_id": sensor_id,
    }

    full_where, full_params = _build_cascade_where(filters)
    match_count = db.execute(
        text(
            f"""
            SELECT COUNT(DISTINCT sensor_id)
            FROM vw_trip_unit_cascade
            {full_where}
            """
        ),
        full_params,
    ).scalar() or 0

    manufacturer_where, manufacturer_params = _build_cascade_where(filters, {"manufacturer_id"})
    manufacturer_rows = db.execute(
        text(
            f"""
            SELECT
                manufacturer_id,
                manufacturer_name,
                COUNT(DISTINCT trip_type_id) AS trip_type_count
            FROM vw_trip_unit_cascade
            {manufacturer_where}
            GROUP BY manufacturer_id, manufacturer_name
            ORDER BY manufacturer_name
            """
        ),
        manufacturer_params,
    ).fetchall()

    trip_type_where, trip_type_params = _build_cascade_where(filters, {"trip_type_id"})
    trip_type_rows = db.execute(
        text(
            f"""
            SELECT
                trip_type_id,
                trip_type_name,
                manufacturer_id,
                manufacturer_name,
                COUNT(DISTINCT trip_style_id) AS trip_style_count
            FROM vw_trip_unit_cascade
            {trip_type_where}
            GROUP BY trip_type_id, trip_type_name,
                     manufacturer_id, manufacturer_name
            ORDER BY manufacturer_name, trip_type_name
            """
        ),
        trip_type_params,
    ).fetchall()

    trip_style_where, trip_style_params = _build_cascade_where(filters, {"trip_style_id"})
    trip_style_rows = db.execute(
        text(
            f"""
            SELECT
                trip_style_id,
                trip_style_name,
                trip_type_id,
                trip_type_name,
                manufacturer_id,
                manufacturer_name,
                COUNT(DISTINCT sensor_id) AS sensor_count
            FROM vw_trip_unit_cascade
            {trip_style_where}
            GROUP BY trip_style_id, trip_style_name,
                     trip_type_id, trip_type_name,
                     manufacturer_id, manufacturer_name
            ORDER BY manufacturer_name, trip_type_name, trip_style_name
            """
        ),
        trip_style_params,
    ).fetchall()

    sensors: list[CascadeSensor] = []
    if trip_style_id is not None or sensor_id is not None:
        sensor_where, sensor_params = _build_cascade_where(filters, {"sensor_id"})
        sensor_rows = db.execute(
            text(
                f"""
                SELECT DISTINCT
                    sensor_id,
                    sensor_rating,
                    sensor_desc,
                    trip_style_id,
                    trip_style_name,
                    trip_type_id,
                    trip_type_name,
                    manufacturer_id,
                    manufacturer_name,
                    has_ltpu,
                    has_stpu,
                    has_inst,
                    has_gfpu
                FROM vw_trip_unit_cascade
                {sensor_where}
                ORDER BY sensor_rating NULLS LAST, sensor_desc
                """
            ),
            sensor_params,
        ).fetchall()
        sensors = [CascadeSensor(**dict(row._mapping)) for row in sensor_rows]

    return CascadeResponse(
        level=_cascade_level(filters),
        count=match_count,
        manufacturers=[CascadeManufacturer(**dict(row._mapping)) for row in manufacturer_rows],
        trip_types=[CascadeTripType(**dict(row._mapping)) for row in trip_type_rows],
        trip_styles=[CascadeTripStyle(**dict(row._mapping)) for row in trip_style_rows],
        sensors=sensors,
    )


# ──────────────────────────────────────────────
# GET /context/{sensor_id} — Sensor Calc Context
# ──────────────────────────────────────────────

@router.get("/context/{sensor_id}", response_model=SensorCalcContext)
def get_sensor_context(sensor_id: int, db: Session = Depends(get_db)):
    """
    Return the complete calculation context for a sensor.

    Includes DVL flags, tolerance values, step sizes, and parent chain.
    Data comes from vw_sensor_calc_context view.
    """
    row = db.execute(
        text("SELECT * FROM vw_sensor_calc_context WHERE sensor_id = :sid"),
        {"sid": sensor_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} not found")

    data = dict(row._mapping)
    # Derive has_* flags from *_calc columns (*_calc == -1 means element absent)
    # Note: calc=0 is valid (SENSORFRAME method), so we can't use `or -1` which
    # would treat Python-falsy 0 as absent.
    data["has_ltpu"] = data.get("ltpu_calc") not in (None, -1)
    data["has_stpu"] = data.get("stpu_calc") not in (None, -1)
    data["has_inst"] = data.get("inst_calc") not in (None, -1)
    data["has_gfpu"] = data.get("gfpu_calc") not in (None, -1)
    data["resolved_equipment"] = _build_etu_resolved_equipment_summary(
        sensor_id=sensor_id,
        sensor_desc=data.get("sensor_desc"),
        sensor_rating=data.get("rating"),
        manufacturer_name=data.get("manufacturer_name"),
        trip_type_name=data.get("trip_type_name"),
        trip_style_name=data.get("trip_style_name"),
        breaker_context_label=data.get("breaker_context_label"),
        breaker_context_source=data.get("breaker_context_source"),
    )

    return SensorCalcContext(**data)


# ──────────────────────────────────────────────
# GET /settings/{sensor_id} — Available Settings
# ──────────────────────────────────────────────

@router.get("/settings/{sensor_id}", response_model=AvailableSettingsResponse)
def get_available_settings(sensor_id: int, db: Session = Depends(get_db)):
    """
    Return available dropdown/slider values for each protection element.

    Calls fn_sensor_available_settings(p_sensor_id) which queries the
    section tables (DatSection1, DatSection3, DatSection4, DatSection1GF)
    and plug table to return valid setting arrays.
    """
    row = db.execute(
        text("SELECT fn_sensor_available_settings(:sid) AS result"),
        {"sid": sensor_id},
    ).fetchone()

    if not row or row.result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No settings found for sensor {sensor_id}",
        )

    data = row.result

    # Some catalog families store only boundary pickup rows and rely on step metadata
    # from the calc-context view, sometimes only on the maintenance columns. Expand
    # those min/max pairs here so the UI receives the full usable option list.
    ctx_row = db.execute(
        text("SELECT * FROM vw_sensor_calc_context WHERE sensor_id = :sid"),
        {"sid": sensor_id},
    ).fetchone()
    ctx = _row_mapping(ctx_row)

    ltpu_settings = data.get("ltpu_settings", [])
    stpu_settings = data.get("stpu_settings", [])
    inst_settings = data.get("inst_settings", [])
    gfpu_settings = data.get("gfpu_settings", [])

    ltpu_settings = _expand_pickup_values(db, sensor_id, ctx, "ltpu", ltpu_settings)
    stpu_settings = _expand_pickup_values(db, sensor_id, ctx, "stpu", stpu_settings)
    inst_settings = _expand_pickup_values(db, sensor_id, ctx, "inst", inst_settings)
    gfpu_settings = _expand_pickup_values(db, sensor_id, ctx, "gfpu", gfpu_settings)

    sensor_rating = _sensor_rating_limit(ctx)
    plug_values = _filter_valid_plug_values(data.get("plug_values", []), sensor_rating)

    std_settings = _load_delay_band_settings(db, "tcc_etu_std_bands", sensor_id)
    gfd_settings = _load_delay_band_settings(db, "tcc_etu_gfd_bands", sensor_id)

    # fn_sensor_available_settings returns JSON with keys:
    # plug_values, ltpu_settings, ltd_settings (objects), ltd_multipliers,
    # stpu_settings, inst_settings, gfpu_settings. STD/GFD band rows are
    # loaded directly here so the UI can use strict per-sensor delay options.
    return AvailableSettingsResponse(
        sensor_id=sensor_id,
        plug_values=plug_values,
        ltpu_settings=ltpu_settings,
        ltd_settings=_dedupe_delay_settings(data.get("ltd_settings", [])),
        std_settings=_dedupe_delay_settings(std_settings),
        gfd_settings=_dedupe_delay_settings(gfd_settings),
        ltd_multipliers=data.get("ltd_multipliers", []),
        stpu_settings=stpu_settings,
        inst_settings=inst_settings,
        gfpu_settings=gfpu_settings,
    )


# ──────────────────────────────────────────────
# GET /apparatus/{apparatus_id}/resources — Derived Study Resource Surface
# ──────────────────────────────────────────────

@router.get("/apparatus/{apparatus_id}/resources", response_model=ApparatusStudyResourcesResponse)
def get_apparatus_study_resources(apparatus_id: UUID, db: Session = Depends(get_db)):
    """Return the bounded apparatus-linked study resource surface.

    This route intentionally keeps the study-content boundary behind the
    governed backend app. If the underlying SQL function has not been applied
    in the current database, the route reports that the surface is still
    migration-gated instead of implying browser-direct availability.
    """
    migration_gated_detail = (
        "Apparatus study-resource surface is unavailable in the current database. "
        "This route remains migration-gated."
    )

    try:
        apparatus_row = db.execute(
            text("SELECT EXISTS(SELECT 1 FROM apparatus WHERE id = :apparatus_id) AS found"),
            {"apparatus_id": apparatus_id},
        ).fetchone()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=migration_gated_detail) from exc

    if apparatus_row is None or not bool(apparatus_row._mapping.get("found")):
        raise HTTPException(status_code=404, detail=f"Apparatus {apparatus_id} not found")

    try:
        rows = db.execute(
            text("SELECT * FROM get_apparatus_resources(:apparatus_id)"),
            {"apparatus_id": apparatus_id},
        ).fetchall()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=migration_gated_detail) from exc

    resources = [ApparatusStudyResource(**dict(row._mapping)) for row in rows]
    return ApparatusStudyResourcesResponse(
        apparatus_id=apparatus_id,
        count=len(resources),
        resources=resources,
    )


# ──────────────────────────────────────────────
# GET /tmt/context/{frame_id} — TMT Frame Context
# ──────────────────────────────────────────────

@router.get("/tmt/frames", response_model=TMTFrameSearchResponse)
def search_tmt_frames(
    breaker_class: Optional[str] = Query(None, description="Filter by ICCB, MCCB, or PCB"),
    manufacturer_name: Optional[str] = Query(None, description="Filter by manufacturer name"),
    breaker_name: Optional[str] = Query(None, description="Filter by breaker name"),
    breaker_style_name: Optional[str] = Query(None, description="Filter by breaker style frame name"),
    frame_size: Optional[str] = Query(None, description="Filter by TMT frame size"),
    amp_rating: Optional[float] = Query(None, description="Filter by supported amp rating"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of matching frames"),
    db: Session = Depends(get_db),
):
    """Search TMT frames using the same hardware-linked concepts exposed in the legacy TMT lookup path."""
    class_filter = breaker_class.upper() if breaker_class else None
    if class_filter is not None and class_filter not in _TMT_STYLE_MODELS:
        raise HTTPException(status_code=400, detail="breaker_class must be one of ICCB, MCCB, or PCB")

    candidate_classes = [class_filter] if class_filter else list(_TMT_STYLE_MODELS.keys())
    frames: list[TMTFrameSearchResult] = []
    seen_frame_ids: set[int] = set()

    for class_key in candidate_classes:
        if len(frames) >= limit:
            break

        style_model = _TMT_STYLE_MODELS[class_key]
        query = (
            db.query(TMTFrame)
            .filter(func.upper(TMTFrame.breaker_class) == class_key)
            .join(style_model, style_model.id == TMTFrame.breaker_style_id)
        )

        if frame_size:
            query = query.filter(TMTFrame.size.ilike(f"%{frame_size}%"))
        if breaker_style_name:
            query = query.filter(style_model.frame.ilike(f"%{breaker_style_name}%"))

        candidate_rows = query.order_by(TMTFrame.id).limit(limit * 4).all()
        for frame in candidate_rows:
            if frame.id in seen_frame_ids:
                continue

            bundle = _load_tmt_contract_bundle(db, frame.id)
            if manufacturer_name and not (
                bundle["manufacturer_name"] and manufacturer_name.lower() in bundle["manufacturer_name"].lower()
            ):
                continue
            if breaker_name and not (
                bundle["breaker_name"] and breaker_name.lower() in bundle["breaker_name"].lower()
            ):
                continue

            matched_amp = None
            if amp_rating is not None:
                matched_amp = next(
                    (
                        amp for amp in bundle["amp_ratings"]
                        if _float_matches(amp.get("rating"), amp_rating)
                    ),
                    None,
                )
                if matched_amp is None:
                    continue

            frames.append(TMTFrameSearchResult(
                frame_id=bundle["frame_id"],
                breaker_style_id=bundle["breaker_style_id"],
                breaker_class=bundle["breaker_class"],
                frame_size=bundle["frame_size"],
                manufacturer_name=bundle["manufacturer_name"],
                breaker_name=bundle["breaker_name"],
                breaker_style_name=bundle["breaker_style_name"],
                standard=bundle["standard"],
                matched_amp_rating=matched_amp.get("rating") if matched_amp else None,
            ))
            seen_frame_ids.add(frame.id)

            if len(frames) >= limit:
                break

    return TMTFrameSearchResponse(count=len(frames), frames=frames)

@router.get("/tmt/context/{frame_id}", response_model=TMTFrameContext)
def get_tmt_context(frame_id: int, db: Session = Depends(get_db)):
    """Return frame-level metadata and option counts for a TMT breaker family."""
    bundle = _load_tmt_contract_bundle(db, frame_id)

    return TMTFrameContext(
        frame_id=bundle["frame_id"],
        breaker_style_id=bundle["breaker_style_id"],
        breaker_class=bundle["breaker_class"],
        frame_size=bundle["frame_size"],
        manufacturer_name=bundle["manufacturer_name"],
        breaker_name=bundle["breaker_name"],
        breaker_style_name=bundle["breaker_style_name"],
        standard=bundle["standard"],
        available_trip_classes=bundle["available_trip_classes"],
        amp_rating_count=len(bundle["amp_ratings"]),
        setting_count=len(bundle["settings"]),
        thermal_adjustment_count=len(bundle["thermal_adjustments"]),
        resolved_equipment=_build_tmt_resolved_equipment_summary(bundle),
    )


# ──────────────────────────────────────────────
# GET /tmt/settings/{frame_id} — TMT Selection Surface
# ──────────────────────────────────────────────

@router.get("/tmt/settings/{frame_id}", response_model=TMTSettingsResponse)
def get_tmt_settings(frame_id: int, db: Session = Depends(get_db)):
    """Return selectable classes, amp ratings, settings, and thermal adjustments for a TMT frame."""
    bundle = _load_tmt_contract_bundle(db, frame_id)

    return TMTSettingsResponse(
        frame_id=bundle["frame_id"],
        available_trip_classes=bundle["available_trip_classes"],
        amp_ratings=[TMTAmpOption(**amp) for amp in bundle["amp_ratings"]],
        settings=[TMTSettingOption(**setting) for setting in bundle["settings"]],
        thermal_adjustments=bundle["thermal_adjustments"],
    )


# ──────────────────────────────────────────────
# POST /tmt/plot-tcc — TMT Plot Contract
# ──────────────────────────────────────────────

@router.post("/tmt/plot-tcc", response_model=TMTPlotResponse)
def plot_tmt_tcc(req: TMTPlotRequest, db: Session = Depends(get_db)):
    """Return a frontend-ready nominal TMT curve payload for a selected frame and class."""
    bundle = _load_tmt_contract_bundle(db, req.frame_id)

    if req.trip_class not in bundle["available_trip_classes"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Trip class {req.trip_class} is not available for TMT frame {req.frame_id}"
            ),
        )

    generator: TMTCurveGenerator = bundle["generator"]
    matched_amp, matched_setting, matched_thermal_adjustment, warnings = _resolve_tmt_selected_options(
        bundle=bundle,
        amp_rating=req.amp_rating,
        setting_value=req.setting_value,
        thermal_adjustment=req.thermal_adjustment,
    )
    curve_points = generator.generate_curve(
        trip_class=req.trip_class,
        num_output_points=req.num_output_points,
    )
    if not curve_points:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No TMT curve points found for frame {req.frame_id} class {req.trip_class}"
            ),
        )

    raw_points = generator.get_raw_points(req.trip_class) if req.include_raw_points else []

    return TMTPlotResponse(
        meta=TMTPlotMeta(
            frame_id=bundle["frame_id"],
            breaker_style_id=bundle["breaker_style_id"],
            breaker_class=bundle["breaker_class"],
            frame_size=bundle["frame_size"],
            manufacturer_name=bundle["manufacturer_name"],
            breaker_name=bundle["breaker_name"],
            breaker_style_name=bundle["breaker_style_name"],
            standard=bundle["standard"],
            selected_trip_class=req.trip_class,
            selected_amp_rating=matched_amp.get("rating") if matched_amp else None,
            selected_max_override=matched_amp.get("max_override") if matched_amp else None,
            selected_setting=matched_setting.get("value") if matched_setting else None,
            selected_setting_label=matched_setting.get("label") if matched_setting else None,
            selected_setting_tol_lo=matched_setting.get("tol_lo") if matched_setting else None,
            selected_setting_tol_hi=matched_setting.get("tol_hi") if matched_setting else None,
            selected_thermal_adjustment=matched_thermal_adjustment,
            selections_applied_to_curve=False,
            plot_disclaimer=(
                "Nominal TMT curve only. Validated amp-rating, setting, and thermal-adjustment "
                "selections are surfaced in metadata and are not yet applied to the plot."
            ),
            resolved_equipment=_build_tmt_resolved_equipment_summary(bundle),
        ),
        warnings=warnings,
        curves=[
            TMTPlotCurve(
                id=f"tmt_class_{req.trip_class}",
                trip_class=req.trip_class,
                points=[
                    TMTPlotCurvePoint(amps=point.amps, seconds=point.seconds)
                    for point in curve_points
                ],
            )
        ],
        raw_points=[
            TMTPlotCurvePoint(amps=point.amps, seconds=point.seconds)
            for point in raw_points
        ],
    )


# ──────────────────────────────────────────────
# GET /emt/frames — EMT Frame Search
# ──────────────────────────────────────────────

@router.get("/emt/frames", response_model=EMTFrameSearchResponse)
def search_emt_frames(
    manufacturer_id: Optional[int] = Query(None, description="Filter by manufacturer id"),
    trip_char: Optional[int] = Query(None, description="Filter by EMT TripChar value"),
    trip_plug: Optional[int] = Query(None, description="Filter by EMT TripPlug value"),
    q: Optional[str] = Query(None, description="Free-text match against EMT type, style, or frame description"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of matching frames"),
    db: Session = Depends(get_db),
):
    """Return the bounded EMT frame discovery surface."""
    frames = _search_emt_frames(
        db=db,
        manufacturer_id=manufacturer_id,
        trip_char=trip_char,
        trip_plug=trip_plug,
        q=q,
        limit=limit,
    )
    return EMTFrameSearchResponse(
        count=len(frames),
        frames=[EMTFrameSearchResult(**frame) for frame in frames],
    )


# ──────────────────────────────────────────────
# GET /emt/context/{frame_id} — EMT Frame Context
# ──────────────────────────────────────────────

@router.get("/emt/context/{frame_id}", response_model=EMTFrameContext)
def get_emt_context(frame_id: int, db: Session = Depends(get_db)):
    """Return frame-level EMT context plus section inventory and amp ratings."""
    bundle = _load_emt_frame_context_bundle(db, frame_id)
    return EMTFrameContext(
        emt_id=bundle["emt_id"],
        frame_id=bundle["frame_id"],
        manufacturer_id=bundle.get("manufacturer_id"),
        manufacturer_name=bundle.get("manufacturer_name"),
        type_name=bundle.get("type_name"),
        style_name=bundle.get("style_name"),
        tcc_number=bundle.get("tcc_number"),
        trip_char=bundle.get("trip_char"),
        trip_plug=bundle.get("trip_plug"),
        frame_size=bundle.get("frame_size"),
        frame_desc=bundle.get("frame_desc"),
        amp_ratings=bundle.get("amp_ratings", []),
        sections=[EMTSectionSummary(**section) for section in bundle.get("sections", [])],
        resolved_equipment=_build_emt_resolved_equipment_summary(bundle),
    )


# ──────────────────────────────────────────────
# GET /emt/settings/{section_id} — EMT Section Settings Surface
# ──────────────────────────────────────────────

@router.get("/emt/settings/{section_id}", response_model=EMTSectionSettingsResponse)
def get_emt_settings(section_id: int, db: Session = Depends(get_db)):
    """Return a bounded EMT section settings surface with pickup rows and band inventory."""
    bundle = _load_emt_section_settings_bundle(db, section_id)
    return EMTSectionSettingsResponse(
        section_id=bundle["section_id"],
        name=bundle.get("name"),
        sec_char=bundle.get("sec_char"),
        curve_type=bundle.get("curve_type"),
        pickup_calc=bundle.get("pickup_calc"),
        pickup_setting=bundle.get("pickup_setting"),
        step_size=bundle.get("step_size"),
        current_calc=bundle.get("current_calc"),
        pickup_tol_lo=bundle.get("pickup_tol_lo"),
        pickup_tol_hi=bundle.get("pickup_tol_hi"),
        pickups=[EMTPickupOption(**pickup) for pickup in bundle.get("pickups", [])],
        bands=[EMTBandOption(**band) for band in bundle.get("bands", [])],
    )


# ──────────────────────────────────────────────
# POST /emt/plot-tcc — EMT Raw Point-Data Plot Surface
# ──────────────────────────────────────────────

@router.post("/emt/plot-tcc", response_model=EMTPlotResponse)
def plot_emt_tcc(req: EMTPlotRequest, db: Session = Depends(get_db)):
    """Return raw EMT band point data without claiming calculated runtime parity."""
    bundle = _load_emt_plot_bundle(db, req.section_id, req.band_id)

    if req.curve_class is not None and req.curve_class not in bundle["grouped_curves"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Curve class {req.curve_class} is not available for EMT band {req.band_id}"
            ),
        )

    selected_classes = [req.curve_class] if req.curve_class is not None else list(bundle["grouped_curves"].keys())
    warnings: list[str] = []
    if req.curve_class is None and len(bundle["grouped_curves"]) > 1:
        warnings.append(
            "Multiple stored EMT curve classes returned for the selected band. This surface exposes raw point data and does not resolve runtime branch selection."
        )

    curves = []
    for curve_class in selected_classes:
        points = bundle["grouped_curves"][curve_class]
        curves.append(
            EMTPlotCurve(
                id=f"emt_band_{req.band_id}_class_{curve_class if curve_class is not None else 'raw'}",
                band_id=req.band_id,
                curve_class=curve_class,
                class_label=_emt_curve_class_label(curve_class),
                line_style=_emt_curve_line_style(curve_class),
                points=[
                    EMTPlotCurvePoint(amps=point["current_amp"], seconds=point["time_sec"])
                    for point in points
                ],
            )
        )

    return EMTPlotResponse(
        meta=EMTPlotMeta(
            emt_id=bundle["emt_id"],
            frame_id=bundle["frame_id"],
            section_id=bundle["section_id"],
            band_id=bundle["band_id"],
            manufacturer_id=bundle.get("manufacturer_id"),
            manufacturer_name=bundle.get("manufacturer_name"),
            type_name=bundle.get("type_name"),
            style_name=bundle.get("style_name"),
            tcc_number=bundle.get("tcc_number"),
            frame_size=bundle.get("frame_size"),
            frame_desc=bundle.get("frame_desc"),
            section_name=bundle.get("section_name"),
            sec_char=bundle.get("sec_char"),
            curve_type=bundle.get("curve_type"),
            pickup_calc=bundle.get("pickup_calc"),
            pickup_setting=bundle.get("pickup_setting"),
            current_calc=bundle.get("current_calc"),
            band_name=bundle.get("band_name"),
            band_ordinal=bundle.get("band_ordinal"),
            current_at=bundle.get("current_at"),
            available_curve_classes=bundle.get("available_curve_classes", []),
            selected_curve_class=req.curve_class,
            selections_applied_to_curve=False,
            plot_disclaimer=(
                "Raw EMT point-data plot only. Returned bands and class slices reflect stored EMT_BandNames and EMT_Curves rows and do not claim DLL/runtime parity."
            ),
            resolved_equipment=_build_emt_resolved_equipment_summary(bundle),
        ),
        warnings=warnings,
        curves=curves,
    )


# ──────────────────────────────────────────────
# POST /calculate — NETA Test Current Calculation
# ──────────────────────────────────────────────

@router.post("/calculate", response_model=CalculateResponse)
def calculate_test_currents(req: CalculateRequest, db: Session = Depends(get_db)):
    """
    Calculate NETA test currents and tolerance bands for all 8 protection elements.

    Calls fn_calculate_test_currents() which implements the full NETA workflow:
      1. Look up sensor calc context (DVL flags, tolerances)
      2. Route each element through appropriate calc method
      3. Apply test multipliers (1x pickup, 3x LTD, 1.5x STD, etc.)
      4. Compute asymmetric tolerance bands

    Returns test currents with limit_low / limit_high for each active element.
    """
    _enforce_plug_within_sensor_rating(req.sensor_id, req.plug_rating, db)

    row = db.execute(
        text("""
            SELECT fn_calculate_test_currents(
                p_sensor_id    := :p_sensor_id,
                p_plug_rating  := :p_plug_rating,
                p_ltpu_setting := :p_ltpu_setting,
                p_ltd_multiplier := :p_ltd_setting,
                p_stpu_setting := :p_stpu_setting,
                p_std_multiplier := :p_std_setting,
                p_inst_setting := :p_inst_setting,
                p_gfpu_setting := :p_gfpu_setting,
                p_gfd_multiplier := :p_gfd_setting,
                p_multiplier_value := :p_multiplier_value,
                p_c_factor := :p_c_factor,
                p_maint_mode   := :p_maint_mode
            ) AS result
        """),
        {
            "p_sensor_id": req.sensor_id,
            "p_plug_rating": req.plug_rating,
            "p_ltpu_setting": req.ltpu_setting,
            "p_ltd_setting": req.ltd_setting,
            "p_stpu_setting": req.stpu_setting,
            "p_std_setting": req.std_setting,
            "p_inst_setting": req.inst_setting,
            "p_gfpu_setting": req.gfpu_setting,
            "p_gfd_setting": req.gfd_setting,
            "p_multiplier_value": req.multiplier_value,
            "p_c_factor": req.c_factor,
            "p_maint_mode": req.maint_mode,
        },
    ).fetchone()

    if not row or row.result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Calculation failed for sensor {req.sensor_id}",
        )

    data = row.result

    # SQL function returns flat per-element keys (ltpu, ltd, stpu, std, inst, gfpu, gfd),
    # each either a JSON object or null.  Map to TestCurrentElement list.
    _CALC_ELEMENT_KEYS = ["ltpu", "ltd", "stpu", "std", "inst", "gfpu", "gfd"]
    elements = []
    warnings = list(data.get("warnings", []))

    curves, curve_warnings, maint_profile = _generate_nominal_plot_curves(
        db=db,
        sensor_id=req.sensor_id,
        plug_rating=req.plug_rating,
        ltpu_setting=req.ltpu_setting,
        ltd_setting=req.ltd_setting,
        stpu_setting=req.stpu_setting,
        std_setting=req.std_setting,
        inst_setting=req.inst_setting,
        gfpu_setting=req.gfpu_setting,
        gfd_setting=req.gfd_setting,
        multiplier_value=req.multiplier_value,
        c_factor=req.c_factor,
    )
    warnings.extend(curve_warnings)

    for key in _CALC_ELEMENT_KEYS:
        elem = data.get(key)
        if elem is None:
            continue
        if key in {"ltd", "std", "gfd"}:
            continue
        elements.append(TestCurrentElement(
            element=key.upper(),
            kind="pickup",
            test_current=elem["test_current"],
            limit_low=elem["limit_low"],
            limit_high=elem["limit_high"],
            multiplier=elem.get("test_multiplier", 1.0),
            calc_method=(
                str(elem["calc_method"]) if elem.get("calc_method") is not None else None
            ),
            delay_seconds=elem.get("delay_opening"),  # INST delay; None for others
        ))

    for key, element_name, curve_ref, default_mult in _DELAY_ELEMENT_SPECS:
        elem = data.get(key)
        if elem is None:
            continue
        delay_setting = {
            "ltd": req.ltd_setting,
            "std": req.std_setting,
            "gfd": req.gfd_setting,
        }[key]
        expected_time, time_low, time_high, timing_source = _authoritative_delay_surface(
            db=db,
            sensor_id=req.sensor_id,
            element_key=key,
            setting=delay_setting,
            curves=curves,
            expected_current=elem["test_current"],
            maint_mode=bool(data.get("maint_mode", False)),
            maint_profile=maint_profile,
            fallback_open=elem.get("delay_opening"),
            fallback_clear=elem.get("delay_clearing"),
        )
        elements.append(TestCurrentElement(
            element=element_name,
            kind="delay",
            test_current=elem["test_current"],
            limit_low=None,
            limit_high=None,
            multiplier=elem.get("test_multiplier", default_mult),
            calc_method=(
                str(elem["calc_method"]) if elem.get("calc_method") is not None else None
            ),
            time_limit_low=time_low,
            time_limit_high=time_high,
            delay_seconds=expected_time,
            notes=f"timing_source={timing_source}",
        ))

    return CalculateResponse(
        sensor_id=req.sensor_id,
        sensor_desc=data.get("sensor_desc", ""),
        plug_rating=req.plug_rating,
        maint_mode=data.get("maint_mode", False),
        maint_capable=data.get("maint_capable", False),
        maint_support_level=data.get("maint_support_level", "none"),
        resolved_equipment=_build_etu_resolved_equipment_summary(
            sensor_id=req.sensor_id,
            sensor_desc=data.get("sensor_desc", ""),
            sensor_rating=None,
            manufacturer_name=req.trip_unit_manufacturer_name or data.get("manufacturer"),
            trip_type_name=req.trip_unit_type_name or data.get("trip_type"),
            trip_style_name=req.trip_unit_style_name or data.get("trip_style"),
            breaker_context_label=req.breaker_context_label or data.get("breaker_context_label"),
            breaker_context_source=req.breaker_context_source,
        ),
        elements=elements,
        warnings=list(dict.fromkeys(warnings)),
    )


# ──────────────────────────────────────────────
# POST /evaluate — Pass/Fail Evaluation
# ──────────────────────────────────────────────

@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_test_results(req: EvaluateRequest, db: Session = Depends(get_db)):
    """
    Evaluate measured values from current injection testing against calculated
    tolerance bands. Returns per-element pass/fail with deviation percentages.

    Calls fn_evaluate_test_results() which:
      1. Recalculates expected test currents (same as /calculate)
      2. Compares each measurement against limit_low / limit_high
      3. Computes deviation percentage from expected
      4. Returns overall_pass (all elements must pass)
    """
    _enforce_plug_within_sensor_rating(req.sensor_id, req.plug_rating, db)

    # Extract individual measured values from measurements list
    measured = {m.element.upper(): m for m in req.measurements}

    row = db.execute(
        text("""
            SELECT fn_evaluate_test_results(
                p_sensor_id     := :p_sensor_id,
                p_plug_rating   := :p_plug_rating,
                p_ltpu_setting  := :p_ltpu_setting,
                p_stpu_setting  := :p_stpu_setting,
                p_inst_setting  := :p_inst_setting,
                p_gfpu_setting  := :p_gfpu_setting,
                p_multiplier_value := :p_multiplier_value,
                p_c_factor      := :p_c_factor,
                p_ltpu_measured := :p_ltpu_measured,
                p_stpu_measured := :p_stpu_measured,
                p_inst_measured := :p_inst_measured,
                p_gfpu_measured := :p_gfpu_measured,
                p_ltd_trip_time := :p_ltd_trip_time,
                p_std_trip_time := :p_std_trip_time,
                p_gfd_trip_time := :p_gfd_trip_time,
                p_maint_mode    := :p_maint_mode
            ) AS result
        """),
        {
            "p_sensor_id": req.sensor_id,
            "p_plug_rating": req.plug_rating,
            "p_ltpu_setting": req.ltpu_setting,
            "p_stpu_setting": req.stpu_setting,
            "p_inst_setting": req.inst_setting,
            "p_gfpu_setting": req.gfpu_setting,
            "p_multiplier_value": req.multiplier_value,
            "p_c_factor": req.c_factor,
            "p_ltpu_measured": measured["LTPU"].measured_current if "LTPU" in measured else None,
            "p_stpu_measured": measured["STPU"].measured_current if "STPU" in measured else None,
            "p_inst_measured": measured["INST"].measured_current if "INST" in measured else None,
            "p_gfpu_measured": measured["GFPU"].measured_current if "GFPU" in measured else None,
            "p_ltd_trip_time": measured["LTD"].measured_time if "LTD" in measured else None,
            "p_std_trip_time": measured["STD"].measured_time if "STD" in measured else None,
            "p_gfd_trip_time": measured["GFD"].measured_time if "GFD" in measured else None,
            "p_maint_mode": req.maint_mode,
        },
    ).fetchone()

    if not row or row.result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation failed for sensor {req.sensor_id}",
        )

    data = row.result

    calc_row = db.execute(
        text("""
            SELECT fn_calculate_test_currents(
                p_sensor_id    := :p_sensor_id,
                p_plug_rating  := :p_plug_rating,
                p_ltpu_setting := :p_ltpu_setting,
                p_ltd_multiplier := :p_ltd_setting,
                p_stpu_setting := :p_stpu_setting,
                p_std_multiplier := :p_std_setting,
                p_inst_setting := :p_inst_setting,
                p_gfpu_setting := :p_gfpu_setting,
                p_gfd_multiplier := :p_gfd_setting,
                p_multiplier_value := :p_multiplier_value,
                p_c_factor := :p_c_factor,
                p_maint_mode   := :p_maint_mode
            ) AS result
        """),
        {
            "p_sensor_id": req.sensor_id,
            "p_plug_rating": req.plug_rating,
            "p_ltpu_setting": req.ltpu_setting,
            "p_ltd_setting": req.ltd_setting,
            "p_stpu_setting": req.stpu_setting,
            "p_std_setting": req.std_setting,
            "p_inst_setting": req.inst_setting,
            "p_gfpu_setting": req.gfpu_setting,
            "p_gfd_setting": req.gfd_setting,
            "p_multiplier_value": req.multiplier_value,
            "p_c_factor": req.c_factor,
            "p_maint_mode": req.maint_mode,
        },
    ).fetchone()
    calc_data = calc_row.result if calc_row and calc_row.result is not None else None

    # SQL function returns flat per-element keys (ltpu, stpu, inst, gfpu),
    # each either a JSON object with {expected, measured, limit_low, limit_high, pass, deviation_pct} or null.
    _EVAL_ELEMENT_KEYS = ["ltpu", "stpu", "inst", "gfpu"]
    elements = []
    warnings = list(data.get("warnings", []))
    for key in _EVAL_ELEMENT_KEYS:
        elem = data.get(key)
        if elem is None:
            continue
        elements.append(ElementResult(
            element=key.upper(),
            kind="pickup",
            passed=elem["pass"],
            test_current=elem["expected"],
            delay_seconds=None,
            limit_low=elem["limit_low"],
            limit_high=elem["limit_high"],
            measured_current=elem.get("measured"),
            measured_time=None,  # trip times not returned per-element by SQL
            deviation_pct=elem.get("deviation_pct"),
        ))

    if calc_data is not None:
        curves, curve_warnings, maint_profile = _generate_nominal_plot_curves(
            db=db,
            sensor_id=req.sensor_id,
            plug_rating=req.plug_rating,
            ltpu_setting=req.ltpu_setting,
            ltd_setting=req.ltd_setting,
            stpu_setting=req.stpu_setting,
            std_setting=req.std_setting,
            inst_setting=req.inst_setting,
            gfpu_setting=req.gfpu_setting,
            gfd_setting=req.gfd_setting,
            multiplier_value=req.multiplier_value,
            c_factor=req.c_factor,
        )
        warnings.extend(curve_warnings)

        for key, element_name, curve_ref, default_mult in _DELAY_ELEMENT_SPECS:
            measurement = measured.get(element_name)
            if measurement is None or measurement.measured_time is None:
                continue

            calc_elem = calc_data.get(key)
            if calc_elem is None:
                continue

            delay_setting = {
                "ltd": req.ltd_setting,
                "std": req.std_setting,
                "gfd": req.gfd_setting,
            }[key]
            expected_time, time_low, time_high, timing_source = _authoritative_delay_surface(
                db=db,
                sensor_id=req.sensor_id,
                element_key=key,
                setting=delay_setting,
                curves=curves,
                expected_current=calc_elem["test_current"],
                maint_mode=bool(calc_data.get("maint_mode", False)),
                maint_profile=maint_profile,
                fallback_open=calc_elem.get("delay_opening"),
                fallback_clear=calc_elem.get("delay_clearing"),
            )
            measured_time = measurement.measured_time
            lower_ok = True if time_low is None else measured_time >= time_low
            upper_ok = True if time_high is None else measured_time <= time_high
            passed = bool(lower_ok and upper_ok)

            deviation_pct = None
            if expected_time not in (None, 0):
                deviation_pct = round(((measured_time - expected_time) / expected_time) * 100, 2)

            elements.append(ElementResult(
                element=element_name,
                kind="delay",
                passed=passed,
                test_current=calc_elem["test_current"],
                delay_seconds=expected_time,
                limit_low=None,
                limit_high=None,
                time_limit_low=time_low,
                time_limit_high=time_high,
                measured_current=None,
                measured_time=measured_time,
                deviation_pct=deviation_pct,
                notes=f"timing_source={timing_source}",
            ))

    passed_count = sum(1 for e in elements if e.passed)
    failed_count = sum(1 for e in elements if not e.passed)
    overall_pass = all(e.passed for e in elements) if elements else data.get("overall_pass", False)

    return EvaluateResponse(
        sensor_id=req.sensor_id,
        sensor_desc=data.get("sensor_desc", ""),
        maint_mode=data.get("maint_mode", False),
        maint_capable=data.get("maint_capable", False),
        maint_support_level=data.get("maint_support_level", "none"),
        resolved_equipment=_build_etu_resolved_equipment_summary(
            sensor_id=req.sensor_id,
            sensor_desc=data.get("sensor_desc", ""),
            sensor_rating=None,
            manufacturer_name=req.trip_unit_manufacturer_name or data.get("manufacturer"),
            trip_type_name=req.trip_unit_type_name or data.get("trip_type"),
            trip_style_name=req.trip_unit_style_name or data.get("trip_style"),
            breaker_context_label=req.breaker_context_label or data.get("breaker_context_label"),
            breaker_context_source=req.breaker_context_source,
        ),
        overall_pass=overall_pass,
        elements=elements,
        tested_count=len(elements),
        passed_count=passed_count,
        failed_count=failed_count,
        warnings=list(dict.fromkeys(warnings)),
    )


# ──────────────────────────────────────────────
# POST /plot-tcc — TCC Plot Data Payload
# ──────────────────────────────────────────────

@router.post("/plot-tcc", response_model=PlotTccResponse)
def plot_tcc(req: PlotTccRequest, db: Session = Depends(get_db)):
    """
    Return a single, frontend-ready TCC plot payload.

    Combines:
      - Breaker curve segments from the calc engine (LTD, STD, INST, GFD)
      - Expected test markers from fn_calculate_test_currents
      - Measured result markers from fn_evaluate_test_results (when measurements provided)
      - Companion summary table for the numeric sidebar

    This endpoint reuses existing NETA calculate/evaluate SQL functions for
    marker and tolerance data, and calc engine services for curve generation.
    """

    _enforce_plug_within_sensor_rating(req.sensor_id, req.plug_rating, db)

    warnings: list[str] = []

    # ── Step 1: Call fn_calculate_test_currents for expected markers ──
    calc_row = db.execute(
        text("""
            SELECT fn_calculate_test_currents(
                p_sensor_id    := :p_sensor_id,
                p_plug_rating  := :p_plug_rating,
                p_ltpu_setting := :p_ltpu_setting,
                p_ltd_multiplier := :p_ltd_setting,
                p_stpu_setting := :p_stpu_setting,
                p_std_multiplier := :p_std_setting,
                p_inst_setting := :p_inst_setting,
                p_gfpu_setting := :p_gfpu_setting,
                p_gfd_multiplier := :p_gfd_setting,
                p_multiplier_value := :p_multiplier_value,
                p_c_factor := :p_c_factor,
                p_maint_mode   := :p_maint_mode
            ) AS result
        """),
        {
            "p_sensor_id": req.sensor_id,
            "p_plug_rating": req.plug_rating,
            "p_ltpu_setting": req.ltpu_setting,
            "p_ltd_setting": req.ltd_setting,
            "p_stpu_setting": req.stpu_setting,
            "p_std_setting": req.std_setting,
            "p_inst_setting": req.inst_setting,
            "p_gfpu_setting": req.gfpu_setting,
            "p_gfd_setting": req.gfd_setting,
            "p_multiplier_value": req.multiplier_value,
            "p_c_factor": req.c_factor,
            "p_maint_mode": req.maint_mode,
        },
    ).fetchone()

    if not calc_row or calc_row.result is None:
        raise HTTPException(status_code=404, detail=f"Sensor {req.sensor_id} not found")

    calc_data = calc_row.result
    if "error" in calc_data:
        raise HTTPException(status_code=404, detail=calc_data["error"])

    warnings.extend(calc_data.get("warnings", []))

    # ── Step 2: Call fn_evaluate_test_results if measurements provided ──
    eval_data = None
    overall_pass = None
    if req.measurements and req.include_measured_markers:
        meas_map = {m.element.upper(): m for m in req.measurements}
        eval_row = db.execute(
            text("""
                SELECT fn_evaluate_test_results(
                    p_sensor_id     := :sid, p_plug_rating := :pr,
                    p_ltpu_setting  := :ls, p_ltd_trip_time := :ltd_tm,
                    p_stpu_setting  := :ss, p_std_trip_time := :std_tm,
                    p_inst_setting  := :is, p_gfpu_setting := :gs,
                    p_multiplier_value := :mv, p_c_factor := :cf,
                    p_gfd_trip_time := :gfd_tm,
                    p_ltpu_measured := :lm, p_stpu_measured := :sm,
                    p_inst_measured := :im, p_gfpu_measured := :gm,
                    p_maint_mode    := :mm
                ) AS result
            """),
            {
                "sid": req.sensor_id, "pr": req.plug_rating,
                "ls": req.ltpu_setting, "ss": req.stpu_setting,
                "is": req.inst_setting, "gs": req.gfpu_setting,
                "mv": req.multiplier_value, "cf": req.c_factor,
                "ltd_tm": meas_map["LTD"].measured_time if "LTD" in meas_map else None,
                "std_tm": meas_map["STD"].measured_time if "STD" in meas_map else None,
                "gfd_tm": meas_map["GFD"].measured_time if "GFD" in meas_map else None,
                "lm": meas_map["LTPU"].measured_current if "LTPU" in meas_map else None,
                "sm": meas_map["STPU"].measured_current if "STPU" in meas_map else None,
                "im": meas_map["INST"].measured_current if "INST" in meas_map else None,
                "gm": meas_map["GFPU"].measured_current if "GFPU" in meas_map else None,
                "mm": req.maint_mode,
            },
        ).fetchone()
        if eval_row and eval_row.result:
            eval_data = eval_row.result
            overall_pass = eval_data.get("overall_pass")
            # Merge evaluate-path warnings (MAINT degradation, tolerance notes, etc.)
            warnings.extend(eval_data.get("warnings", []))

    # ── Step 3: Build meta ──
    maint_mode = calc_data.get("maint_mode", False)
    maint_capable = calc_data.get("maint_capable", False)
    maint_support_level = calc_data.get("maint_support_level", "none")

    plot_disclaimer = None
    if maint_mode and maint_capable:
        plot_disclaimer = "Nominal curve shown; markers reflect maint-mode calculations"

    trip_unit_manufacturer = req.trip_unit_manufacturer_name or calc_data.get("manufacturer")
    trip_unit_type = req.trip_unit_type_name or calc_data.get("trip_type")
    trip_unit_style = req.trip_unit_style_name or calc_data.get("trip_style")
    breaker_context_label = req.breaker_context_label or calc_data.get("breaker_context_label") or trip_unit_style
    breaker_context_source = req.breaker_context_source or (
        "plot_request" if req.breaker_context_label else ("trip_style_fallback" if breaker_context_label else None)
    )

    meta = PlotMeta(
        sensor_id=req.sensor_id,
        sensor_desc=calc_data.get("sensor_desc", ""),
        breaker_context_label=breaker_context_label,
        breaker_context_source=breaker_context_source,
        manufacturer=trip_unit_manufacturer,
        trip_type=trip_unit_type,
        trip_style=trip_unit_style,
        trip_unit_manufacturer=trip_unit_manufacturer,
        trip_unit_type=trip_unit_type,
        trip_unit_style=trip_unit_style,
        plug_rating=req.plug_rating,
        maint_mode=maint_mode,
        maint_capable=maint_capable,
        maint_support_level=maint_support_level,
        overall_pass=overall_pass,
        plot_disclaimer=plot_disclaimer,
        resolved_equipment=_build_etu_resolved_equipment_summary(
            sensor_id=req.sensor_id,
            sensor_desc=calc_data.get("sensor_desc", ""),
            sensor_rating=None,
            manufacturer_name=trip_unit_manufacturer,
            trip_type_name=trip_unit_type,
            trip_style_name=trip_unit_style,
            breaker_context_label=breaker_context_label,
            breaker_context_source=breaker_context_source,
        ),
    )

    # ── Step 4: Build expected markers + table rows ──
    expected_markers: list[PlotExpectedMarker] = []
    table_rows: list[PlotTableRow] = []

    # Pickup elements: LTPU, STPU, INST, GFPU
    _PICKUP_KEYS = [
        ("ltpu", "LTPU", "LTPU 1x", 1.0),
        ("stpu", "STPU", "STPU 1x", 1.0),
        ("inst", "INST", "INST 1x", 1.0),
        ("gfpu", "GFPU", "GFPU 1x", 1.0),
    ]
    for key, elem_name, label, mult in _PICKUP_KEYS:
        elem = calc_data.get(key)
        if elem is None:
            continue
        if req.include_expected_markers:
            expected_markers.append(PlotExpectedMarker(
                id=f"{key}_expected",
                element=elem_name,
                kind="pickup",
                render_hint="vertical_marker",
                test_multiple=mult,
                expected_current=elem["test_current"],
                expected_time=None,
                limit_low=elem.get("limit_low"),
                limit_high=elem.get("limit_high"),
                label=label,
            ))
        table_rows.append(PlotTableRow(
            element=elem_name,
            kind="pickup",
            setting=elem.get("setting"),
            test_multiple=mult,
            expected_current=elem["test_current"],
            limit_low=elem.get("limit_low"),
            limit_high=elem.get("limit_high"),
            calc_method=str(elem["calc_method"]) if elem.get("calc_method") is not None else None,
        ))

    # Delay elements: LTD, STD, GFD
    _DELAY_KEYS = [
        ("ltd", "LTD", "LTD", "ltd_open", 3.0),
        ("std", "STD", "STD", "std_open", 1.5),
        ("gfd", "GFD", "GFD", "gfd_open", 1.5),
    ]
    for key, elem_name, label_prefix, curve_ref, default_mult in _DELAY_KEYS:
        elem = calc_data.get(key)
        if elem is None:
            continue
        test_mult = elem.get("test_multiplier", default_mult)
        if req.include_expected_markers:
            expected_markers.append(PlotExpectedMarker(
                id=f"{key}_expected",
                element=elem_name,
                kind="delay",
                render_hint="point",
                test_multiple=test_mult,
                expected_current=elem["test_current"],
                expected_time=None,  # will be enriched by curve interpolation below
                curve_ref=curve_ref,
                label=f"{label_prefix} {test_mult}x",
            ))
        table_rows.append(PlotTableRow(
            element=elem_name,
            kind="delay",
            test_multiple=test_mult,
            expected_current=elem["test_current"],
        ))

    # ── Step 5: Build measured markers + enrich table rows ──
    measured_markers: list[PlotMeasuredMarker] = []
    if eval_data and req.include_measured_markers:
        _EVAL_KEYS = ["ltpu", "stpu", "inst", "gfpu"]
        for key in _EVAL_KEYS:
            elem = eval_data.get(key)
            if elem is None:
                continue
            elem_name = key.upper()
            measured_markers.append(PlotMeasuredMarker(
                id=f"{key}_measured",
                element=elem_name,
                kind="pickup",
                render_hint="vertical_marker",
                measured_current=elem.get("measured"),
                passed=elem["pass"],
                deviation_pct=elem.get("deviation_pct"),
                label=f"{elem_name} measured",
            ))
            # Enrich table row with measured data
            for tr in table_rows:
                if tr.element == elem_name:
                    tr.measured_current = elem.get("measured")
                    tr.passed = elem["pass"]
                    tr.deviation_pct = elem.get("deviation_pct")
                    break

    # ── Step 6: Generate curves from calc engine ──
    curves: list[PlotCurve] = []
    if req.include_nominal_curve:
        curves, curve_warnings, maint_profile = _generate_nominal_plot_curves(
            db=db,
            sensor_id=req.sensor_id,
            plug_rating=req.plug_rating,
            ltpu_setting=req.ltpu_setting,
            ltd_setting=req.ltd_setting,
            stpu_setting=req.stpu_setting,
            std_setting=req.std_setting,
            inst_setting=req.inst_setting,
            gfpu_setting=req.gfpu_setting,
            gfd_setting=req.gfd_setting,
            multiplier_value=req.multiplier_value,
            c_factor=req.c_factor,
        )
        warnings.extend(curve_warnings)

        for marker in expected_markers:
            if marker.kind != "delay" or marker.expected_time is not None:
                continue
            delay_setting = {
                "LTD": req.ltd_setting,
                "STD": req.std_setting,
                "GFD": req.gfd_setting,
            }.get(marker.element)
            expected_time, time_low, time_high, _timing_source = _authoritative_delay_surface(
                db=db,
                sensor_id=req.sensor_id,
                element_key=marker.element.lower(),
                setting=delay_setting,
                curves=curves,
                expected_current=marker.expected_current,
                maint_mode=maint_mode,
                maint_profile=maint_profile,
            )
            marker.expected_time = expected_time
            for tr in table_rows:
                if tr.element == marker.element:
                    tr.expected_time = expected_time
                    tr.time_limit_low = time_low
                    tr.time_limit_high = time_high
                    break

        if req.measurements and req.include_measured_markers:
            meas_map = {m.element.upper(): m for m in req.measurements}
            for elem_name in ("LTD", "STD", "GFD"):
                measurement = meas_map.get(elem_name)
                if measurement is None or measurement.measured_time is None:
                    continue
                for tr in table_rows:
                    if tr.element != elem_name:
                        continue
                    tr.measured_time = measurement.measured_time
                    lower_ok = True if tr.time_limit_low is None else measurement.measured_time >= tr.time_limit_low
                    upper_ok = True if tr.time_limit_high is None else measurement.measured_time <= tr.time_limit_high
                    tr.passed = bool(lower_ok and upper_ok)
                    if tr.expected_time not in (None, 0):
                        tr.deviation_pct = round(((measurement.measured_time - tr.expected_time) / tr.expected_time) * 100, 2)
                    measured_markers.append(PlotMeasuredMarker(
                        id=f"{elem_name.lower()}_measured",
                        element=elem_name,
                        kind="delay",
                        render_hint="point",
                        measured_current=tr.expected_current,
                        measured_time=measurement.measured_time,
                        passed=bool(tr.passed),
                        deviation_pct=tr.deviation_pct,
                        label=f"{elem_name} measured",
                    ))
                    break

    evaluated_rows = [row for row in table_rows if row.passed is not None]
    if evaluated_rows:
        meta.overall_pass = all(bool(row.passed) for row in evaluated_rows)

    return PlotTccResponse(
        meta=meta,
        warnings=warnings,
        curves=curves,
        expected_markers=expected_markers,
        measured_markers=measured_markers,
        table_rows=table_rows,
    )


def _interpolate_time(
    points: list[PlotCurvePoint], target_amps: float
) -> Optional[float]:
    """
    Log-log interpolate a trip time from a curve at the given current.
    Returns None if the target is outside the curve range.
    """
    import math
    # Sort by amps ascending
    sorted_pts = sorted(points, key=lambda p: p.amps)
    if not sorted_pts or target_amps <= 0:
        return None
    if target_amps < sorted_pts[0].amps or target_amps > sorted_pts[-1].amps:
        return None

    for i in range(len(sorted_pts) - 1):
        p1, p2 = sorted_pts[i], sorted_pts[i + 1]
        if p1.amps <= target_amps <= p2.amps:
            if p1.amps <= 0 or p2.amps <= 0 or p1.seconds <= 0 or p2.seconds <= 0:
                return None
            # Linear interpolation in log-log space
            log_a1, log_a2 = math.log10(p1.amps), math.log10(p2.amps)
            log_t1, log_t2 = math.log10(p1.seconds), math.log10(p2.seconds)
            if log_a2 == log_a1:
                return p1.seconds
            frac = (math.log10(target_amps) - log_a1) / (log_a2 - log_a1)
            log_t = log_t1 + frac * (log_t2 - log_t1)
            return round(10 ** log_t, 4)

    return None
