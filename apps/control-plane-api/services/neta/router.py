"""
FastAPI router for NETA ETT Testing Service.

Endpoints:
    GET  /api/v1/neta/cascade              — Cascade drill-down selection
    GET  /api/v1/neta/context/{sensor_id}  — Full sensor calculation context
    GET  /api/v1/neta/settings/{sensor_id} — Available settings for dropdowns
    POST /api/v1/neta/calculate            — Calculate test currents + tolerance bands
    POST /api/v1/neta/evaluate             — Evaluate measured values → pass/fail

The router uses raw SQL against Supabase-backed views/functions where that is
the stable contract, while keeping ETU settings expansion and measured pickup
evaluation in-process so the API surface stays deterministic even if the live
SQL helper functions evolve independently.
"""

import json
import logging
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import case, func, inspect as sqlalchemy_inspect, text
from sqlalchemy.exc import NoResultFound

from apex_calc_engine.services.calc_engine import (
    RelayCurveDefinition,
    RelayCurvePoint,
    RelayEvaluationStatus,
    RelayFormulaCode,
    TMTCurveGenerator,
    evaluate_curve_definition,
    family_from_model_code,
)
from config import get_db
from models.breakers import BrkICCBStyle, BrkMCCBStyle, BrkPCBStyle
from models.reference import Manufacturer
from models.tmt import TMTFrame
from .schemas import (
    CascadeQuery,
    CascadeManufacturer,
    CascadeTripType,
    CascadeTripStyle,
    CascadeSensor,
    CascadePlugOption,
    CascadeResponse,
    EtuBreakerCascadeResponse,
    EtuBreakerClassOption,
    EtuBreakerManufacturer,
    EtuBreakerOption,
    EtuBreakerStyleOption,
    EtuSearchResult,
    EtuSearchResponse,
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
    TMTFacet,
    TMTFacetsResponse,
    TMTFrameSearchResponse,
    TMTFrameSearchResult,
    EMTFacet,
    EMTFacetsResponse,
    EMTBandOption,
    EMTFrameContext,
    EMTPlotCurve,
    EMTPlotCurvePoint,
    EMTPlotMeta,
    EMTPlotRequest,
    EMTPlotResponse,
    RelayContext,
    RelayCurveParentOption,
    RelayLineSectionSummary,
    RelayPlotCurve,
    RelayPlotCurvePoint,
    RelayPlotMeta,
    RelayPlotRequest,
    RelayPlotResponse,
    RelayCandidateOverrides,
    RelayPreviewOption,
    RelayRangeDiscreteValue,
    RelayRangeOption,
    RelaySectionSearchResponse,
    RelaySectionSearchResult,
    RelaySettingsResponse,
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
    "ltpu": "tcc.etu_ltpu_pickups",
    "stpu": "tcc.etu_stpu_pickups",
    "inst": "tcc.etu_inst_pickups",
    "gfpu": "tcc.etu_gfpu_pickups",
}

_RELAY_SUPPORTED_MODEL_CODES = {1, 2, 3, 4, 5, 6}
_RELAY_UNSUPPORTED_MODEL_CODES = {7, 8, 9}
_RELAY_FAMILY_NAMES = {
    0: "unknown",
    1: "tcp",
    2: "iec",
    3: "meq",
    4: "bsl",
    5: "swz",
    6: "pcd",
    7: "rxd",
    8: "lrm",
    9: "egc",
}
_RELAY_STORAGE_KINDS = {
    0: "unknown",
    1: "points",
    2: "constants",
    3: "constants",
    4: "constants",
    5: "constants",
    6: "constants",
    7: "unsupported",
    8: "unsupported",
    9: "unsupported",
}
_RELAY_ANALYTICAL_FAMILY_CONFIG = {
    2: {
        "parent_table": "tcc.relay_curves_iec",
        "row_table": "tcc.relay_curve_rows_iec",
        "parent_pk": "relay_curve_iec_id",
        "coefficients": ("v_k", "v_e", "dt_after", "dt_min_time"),
    },
    3: {
        "parent_table": "tcc.relay_curves_meq",
        "row_table": "tcc.relay_curve_rows_meq",
        "parent_pk": "relay_curve_meq_id",
        "coefficients": ("v_a", "v_b", "v_c", "v_d", "v_e"),
    },
    4: {
        "parent_table": "tcc.relay_curves_bsl",
        "row_table": "tcc.relay_curve_rows_bsl",
        "parent_pk": "relay_curve_bsl_id",
        "coefficients": ("v_a", "v_b", "v_c", "v_d", "v_n", "v_k", "v_r"),
    },
    5: {
        "parent_table": "tcc.relay_curves_swz",
        "row_table": "tcc.relay_curve_rows_swz",
        "parent_pk": "relay_curve_swz_id",
        "coefficients": ("v_a", "v_b", "v_e"),
    },
    6: {
        "parent_table": "tcc.relay_curves_pcd",
        "row_table": "tcc.relay_curve_rows_pcd",
        "parent_pk": "relay_curve_pcd_id",
        "coefficients": ("v_a", "v_b", "v_c"),
    },
}
_RELAY_TCC_SCHEMA_TABLES = [
    "relays",
    "relay_devices",
    "relay_line_sections",
    "relay_td_sections",
    "relay_ranges",
    "relay_discrete_values",
    "relay_curves_iec",
    "relay_curves_swz",
    "relay_curves_bsl",
    "relay_curves_meq",
    "relay_curves_pcd",
    "relay_curves_lrm",
    "relay_curves_rxd",
    "relay_curves_egc",
    "relay_curves_tcp",
    "relay_curve_rows_iec",
    "relay_curve_rows_swz",
    "relay_curve_rows_bsl",
    "relay_curve_rows_meq",
    "relay_curve_rows_pcd",
    "relay_curve_points_tcp",
]
_RELAY_CATALOG_UNAVAILABLE_DETAIL = "relay catalog unavailable: tcc-schema tables not present"


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


def _relay_family_name(model_code: int) -> str:
    return _RELAY_FAMILY_NAMES.get(int(model_code), f"model_{model_code}")


def _relay_storage_kind(model_code: int) -> str:
    return _RELAY_STORAGE_KINDS.get(int(model_code), "unknown")


def _relay_is_supported(model_code: int) -> bool:
    return int(model_code) in _RELAY_SUPPORTED_MODEL_CODES


def _relay_work_schema_tables_available(db_or_bind: object) -> bool:
    try:
        bind = db_or_bind.get_bind() if hasattr(db_or_bind, "get_bind") else db_or_bind
        inspector = sqlalchemy_inspect(bind)
        schemas = set(inspector.get_schema_names())
        if "tcc" not in schemas:
            return False
        existing = set(inspector.get_table_names(schema="tcc")) | set(inspector.get_view_names(schema="tcc"))
        return all(table in existing for table in _RELAY_TCC_SCHEMA_TABLES)
    except Exception:
        return False


def _ensure_relay_catalog_available(db: Session) -> None:
    if not _relay_work_schema_tables_available(db):
        raise HTTPException(status_code=503, detail=_RELAY_CATALOG_UNAVAILABLE_DETAIL)


def _relay_unsupported_reason(model_code: int) -> Optional[str]:
    family_name = _relay_family_name(model_code)
    if int(model_code) in _RELAY_UNSUPPORTED_MODEL_CODES:
        return f"{family_name} relay family remains explicitly unsupported in Tranche 4."
    if int(model_code) == 0:
        return "Relay TD-section model code 0 does not identify a previewable curve family."
    return None


def _build_relay_resolved_equipment_summary(bundle: dict[str, object]) -> ResolvedEquipmentSummary:
    primary_label = _join_summary_label(bundle.get("relay_type"), bundle.get("device_function"))
    secondary_label = _join_summary_label(bundle.get("td_section_name"), _relay_family_name(int(bundle["family_code"])).upper())
    rating_label = _join_summary_label("Section", bundle.get("td_section_name"))
    return ResolvedEquipmentSummary(
        family="relay",
        family_label="Relay",
        resolved_id=f"relay_td_section:{bundle['td_section_source_id']}",
        primary_label=primary_label or rating_label,
        secondary_label=secondary_label or rating_label,
        breaker_context=ResolvedBreakerContext(
            label=primary_label,
            source="relay_catalog",
            type_name=bundle.get("relay_type"),
        ),
        rating_context=ResolvedRatingContext(
            label=rating_label,
            section_name=bundle.get("td_section_name"),
        ),
    )


def _load_relay_base_bundle(db: Session, td_section_source_id: int) -> dict[str, object]:
    row = db.execute(
        text(
            """
            SELECT
                r.manufacturer_source_id,
                r.relay_type,
                d.relay_device_id,
                d.source_row_id AS relay_device_source_id,
                d.device_function,
                d.ordinal AS device_ordinal,
                d.standard_code,
                d.dftype_code,
                d.voltage_restraint_kind::text AS voltage_restraint_kind,
                t.source_row_id AS td_section_source_id,
                t.section_name AS td_section_name,
                t.model_code AS family_code
            FROM tcc.relay_td_sections t
            JOIN tcc.relay_devices d ON d.relay_device_id = t.relay_device_id
            JOIN tcc.relays r ON r.relay_id = d.relay_id
            WHERE t.source_row_id = :td_section_source_id
            """
        ),
        {"td_section_source_id": td_section_source_id},
    ).one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Relay TD-section {td_section_source_id} not found")

    bundle = _normalize_mapping(_row_mapping(row))
    bundle["family_name"] = _relay_family_name(int(bundle["family_code"]))
    bundle["storage_kind"] = _relay_storage_kind(int(bundle["family_code"]))
    bundle["supported"] = _relay_is_supported(int(bundle["family_code"]))
    bundle["unsupported_reason"] = _relay_unsupported_reason(int(bundle["family_code"]))
    bundle["resolved_equipment"] = _build_relay_resolved_equipment_summary(bundle)
    return bundle


def _load_relay_line_sections(db: Session, relay_device_id: str) -> list[dict[str, object]]:
    rows = db.execute(
        text(
            """
            SELECT
                source_row_id AS line_section_source_id,
                section_number,
                section_name,
                pickup,
                secondary_i_code,
                amps_calc_mode,
                use_toc_multiplier
            FROM tcc.relay_line_sections
            WHERE relay_device_id = :relay_device_id
            ORDER BY section_number, source_row_id
            """
        ),
        {"relay_device_id": relay_device_id},
    ).fetchall()
    return [_normalize_mapping(_row_mapping(row)) for row in rows]


def _load_relay_ranges(db: Session, relay_device_id: str, td_section_source_id: int) -> list[dict[str, object]]:
    rows = db.execute(
        text(
            """
            SELECT
                r.source_row_id AS range_source_id,
                r.source_parent_id,
                r.parent_kind::text AS parent_kind,
                COALESCE(ls.section_name, ts.section_name) AS parent_label,
                r.aux_key,
                r.ordinal,
                r.min_value,
                r.max_value,
                r.step_value,
                r.relative_unit_code,
                r.use_range,
                r.scales_with_time_multiplier
            FROM tcc.relay_ranges r
            LEFT JOIN tcc.relay_line_sections ls ON ls.source_row_id = r.line_section_source_id
            LEFT JOIN tcc.relay_td_sections ts ON ts.source_row_id = r.td_section_source_id
            WHERE r.td_section_source_id = :td_section_source_id
               OR r.line_section_source_id IN (
                    SELECT source_row_id
                    FROM tcc.relay_line_sections
                    WHERE relay_device_id = :relay_device_id
               )
            ORDER BY r.parent_kind, r.source_parent_id, r.aux_key, r.ordinal
            """
        ),
        {
            "relay_device_id": relay_device_id,
            "td_section_source_id": td_section_source_id,
        },
    ).fetchall()
    range_rows = [_normalize_mapping(_row_mapping(row)) for row in rows]
    discrete_rows = db.execute(
        text(
            """
            SELECT
                r.source_row_id AS range_source_id,
                d.discrete_value,
                d.discrete_description
            FROM tcc.relay_ranges r
            JOIN tcc.relay_discrete_values d ON d.relay_range_id = r.relay_range_id
            WHERE r.td_section_source_id = :td_section_source_id
               OR r.line_section_source_id IN (
                    SELECT source_row_id
                    FROM tcc.relay_line_sections
                    WHERE relay_device_id = :relay_device_id
               )
            ORDER BY r.source_row_id, d.discrete_value NULLS LAST, d.discrete_description
            """
        ),
        {
            "relay_device_id": relay_device_id,
            "td_section_source_id": td_section_source_id,
        },
    ).fetchall()
    discrete_by_range: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row in discrete_rows:
        payload = _normalize_mapping(_row_mapping(row))
        discrete_by_range[int(payload["range_source_id"])] .append(
            {
                "value": payload.get("discrete_value"),
                "description": payload.get("discrete_description"),
            }
        )

    for range_row in range_rows:
        range_row["discrete_values"] = discrete_by_range.get(int(range_row["range_source_id"]), [])
    return range_rows


def _load_relay_analytical_preview_surface(db: Session, td_section_source_id: int, family_code: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    config = _RELAY_ANALYTICAL_FAMILY_CONFIG[int(family_code)]
    coefficient_columns = ",\n                ".join(f"rows.{column}" for column in config["coefficients"])
    rows = db.execute(
        text(
            f"""
            SELECT
                parents.source_row_id AS curve_parent_source_id,
                parents.min_pickup,
                parents.max_pickup,
                rows.curve_name,
                rows.ordinal AS curve_ordinal,
                {coefficient_columns}
            FROM {config['parent_table']} parents
            JOIN {config['row_table']} rows ON rows.{config['parent_pk']} = parents.{config['parent_pk']}
            WHERE parents.relay_td_section_source_id = :td_section_source_id
            ORDER BY parents.source_row_id, rows.ordinal
            """
        ),
        {"td_section_source_id": td_section_source_id},
    ).fetchall()

    preview_rows = [_normalize_mapping(_row_mapping(row)) for row in rows]
    parent_rows: dict[int, dict[str, object]] = {}
    parent_counts: Counter[int] = Counter()
    for preview_row in preview_rows:
        parent_source_id = int(preview_row["curve_parent_source_id"])
        parent_counts[parent_source_id] += 1
        parent_rows.setdefault(
            parent_source_id,
            {
                "curve_parent_source_id": parent_source_id,
                "storage_kind": "constants",
                "curve_name": None,
                "curve_parent_ordinal": None,
                "min_pickup": preview_row.get("min_pickup"),
                "max_pickup": preview_row.get("max_pickup"),
                "is_discrete": None,
                "step_size": None,
                "horizontal_amps_code": None,
                "preview_option_count": 0,
            },
        )
        preview_row["storage_kind"] = "constants"
        preview_row["source_ordinal"] = None
        preview_row["time_dial"] = None
        preview_row["td_desc"] = None
        preview_row["point_count"] = None
        preview_row["current_min"] = preview_row.get("min_pickup")
        preview_row["current_max"] = preview_row.get("max_pickup")
        preview_row["coefficients"] = {
            column: preview_row.get(column)
            for column in config["coefficients"]
        }
    for parent_source_id, count in parent_counts.items():
        parent_rows[parent_source_id]["preview_option_count"] = count
    return list(parent_rows.values()), preview_rows


def _load_relay_tcp_preview_surface(db: Session, td_section_source_id: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows = db.execute(
        text(
            """
            WITH grouped AS (
                SELECT
                    relay_curve_tcp_id,
                    source_ordinal,
                    time_dial,
                    td_desc,
                    COUNT(*) AS point_count,
                    MIN(current_value) AS current_min,
                    MAX(current_value) AS current_max
                FROM tcc.relay_curve_points_tcp
                GROUP BY relay_curve_tcp_id, source_ordinal, time_dial, td_desc
            )
            SELECT
                parents.source_row_id AS curve_parent_source_id,
                parents.curve_name,
                parents.ordinal AS curve_parent_ordinal,
                parents.is_discrete,
                parents.step_size,
                parents.horizontal_amps_code,
                grouped.source_ordinal,
                grouped.time_dial,
                grouped.td_desc,
                grouped.point_count,
                grouped.current_min,
                grouped.current_max
            FROM tcc.relay_curves_tcp parents
            JOIN grouped ON grouped.relay_curve_tcp_id = parents.relay_curve_tcp_id
            WHERE parents.relay_td_section_source_id = :td_section_source_id
            ORDER BY parents.ordinal, grouped.source_ordinal
            """
        ),
        {"td_section_source_id": td_section_source_id},
    ).fetchall()

    preview_rows = [_normalize_mapping(_row_mapping(row)) for row in rows]
    parent_rows: dict[int, dict[str, object]] = {}
    parent_counts: Counter[int] = Counter()
    for preview_row in preview_rows:
        parent_source_id = int(preview_row["curve_parent_source_id"])
        parent_counts[parent_source_id] += 1
        parent_rows.setdefault(
            parent_source_id,
            {
                "curve_parent_source_id": parent_source_id,
                "storage_kind": "points",
                "curve_name": preview_row.get("curve_name"),
                "curve_parent_ordinal": preview_row.get("curve_parent_ordinal"),
                "min_pickup": None,
                "max_pickup": None,
                "is_discrete": preview_row.get("is_discrete"),
                "step_size": preview_row.get("step_size"),
                "horizontal_amps_code": preview_row.get("horizontal_amps_code"),
                "preview_option_count": 0,
            },
        )
        preview_row["storage_kind"] = "points"
        preview_row["curve_ordinal"] = None
        preview_row["coefficients"] = {}
    for parent_source_id, count in parent_counts.items():
        parent_rows[parent_source_id]["preview_option_count"] = count
    return list(parent_rows.values()), preview_rows


def _load_relay_settings_bundle(db: Session, td_section_source_id: int) -> dict[str, object]:
    bundle = _load_relay_base_bundle(db, td_section_source_id)
    line_sections = _load_relay_line_sections(db, str(bundle["relay_device_id"]))
    ranges = _load_relay_ranges(db, str(bundle["relay_device_id"]), td_section_source_id)

    family_code = int(bundle["family_code"])
    if family_code == 1:
        curve_parents, preview_options = _load_relay_tcp_preview_surface(db, td_section_source_id)
    elif family_code in _RELAY_ANALYTICAL_FAMILY_CONFIG:
        curve_parents, preview_options = _load_relay_analytical_preview_surface(db, td_section_source_id, family_code)
    else:
        curve_parents, preview_options = [], []

    return {
        **bundle,
        "line_sections": line_sections,
        "ranges": ranges,
        "curve_parents": curve_parents,
        "preview_options": preview_options,
    }


def _load_relay_context_bundle(db: Session, td_section_source_id: int) -> dict[str, object]:
    settings_bundle = _load_relay_settings_bundle(db, td_section_source_id)
    return {
        **settings_bundle,
        "line_section_count": len(settings_bundle["line_sections"]),
        "range_count": len(settings_bundle["ranges"]),
        "curve_parent_count": len(settings_bundle["curve_parents"]),
        "preview_option_count": len(settings_bundle["preview_options"]),
    }


def _search_relay_sections(
    db: Session,
    *,
    relay_type: Optional[str],
    device_function: Optional[str],
    family_code: Optional[int],
    q: Optional[str],
    supported_only: bool,
    limit: int,
) -> list[dict[str, object]]:
    rows = db.execute(
        text(
            """
            SELECT
                r.manufacturer_source_id,
                r.relay_type,
                d.source_row_id AS relay_device_source_id,
                d.device_function,
                d.ordinal AS device_ordinal,
                d.standard_code,
                d.dftype_code,
                d.voltage_restraint_kind::text AS voltage_restraint_kind,
                t.source_row_id AS td_section_source_id,
                t.section_name AS td_section_name,
                t.model_code AS family_code
            FROM tcc.relay_td_sections t
            JOIN tcc.relay_devices d ON d.relay_device_id = t.relay_device_id
            JOIN tcc.relays r ON r.relay_id = d.relay_id
            WHERE (:relay_type IS NULL OR r.relay_type ILIKE '%' || :relay_type || '%')
              AND (:device_function IS NULL OR d.device_function ILIKE '%' || :device_function || '%')
              AND (:family_code IS NULL OR t.model_code = :family_code)
              AND (
                    :q IS NULL OR r.relay_type ILIKE '%' || :q || '%'
                    OR d.device_function ILIKE '%' || :q || '%'
                    OR COALESCE(t.section_name, '') ILIKE '%' || :q || '%'
                  )
              AND (:supported_only = FALSE OR t.model_code IN (1, 2, 3, 4, 5, 6))
            ORDER BY d.source_row_id, t.source_row_id
            LIMIT :limit
            """
        ),
        {
            "relay_type": relay_type,
            "device_function": device_function,
            "family_code": family_code,
            "q": q,
            "supported_only": supported_only,
            "limit": limit,
        },
    ).fetchall()

    sections = []
    for row in rows:
        payload = _normalize_mapping(_row_mapping(row))
        family_code_value = int(payload["family_code"])
        payload["family_name"] = _relay_family_name(family_code_value)
        payload["storage_kind"] = _relay_storage_kind(family_code_value)
        payload["supported"] = _relay_is_supported(family_code_value)
        sections.append(payload)
    return sections


def _select_relay_preview_option(
    *,
    settings_bundle: dict[str, object],
    curve_parent_source_id: Optional[int],
    curve_ordinal: Optional[int],
    source_ordinal: Optional[int],
    time_dial: Optional[float],
) -> tuple[Optional[dict[str, object]], list[str]]:
    warnings: list[str] = []
    preview_options = list(settings_bundle["preview_options"])
    if curve_parent_source_id is not None:
        preview_options = [
            option for option in preview_options
            if int(option["curve_parent_source_id"]) == curve_parent_source_id
        ]
        if not preview_options:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Curve parent {curve_parent_source_id} is not available for relay TD-section "
                    f"{settings_bundle['td_section_source_id']}"
                ),
            )

    family_code = int(settings_bundle["family_code"])
    if family_code == 1:
        if source_ordinal is not None:
            selected = next(
                (option for option in preview_options if int(option["source_ordinal"]) == source_ordinal),
                None,
            )
            if selected is None:
                raise HTTPException(status_code=400, detail=f"TCP source_ordinal {source_ordinal} is not available")
            return selected, warnings

        if time_dial is not None:
            selected = next(
                (option for option in preview_options if _float_matches(option.get("time_dial"), time_dial)),
                None,
            )
            if selected is None:
                raise HTTPException(status_code=400, detail=f"TCP time_dial {time_dial} is not available")
            return selected, warnings

        if preview_options:
            warnings.append("No TCP time-dial row was selected; the first stored relay preview row was used.")
            return preview_options[0], warnings
        return None, warnings

    if curve_ordinal is not None:
        selected = next(
            (option for option in preview_options if int(option["curve_ordinal"]) == curve_ordinal),
            None,
        )
        if selected is None:
            raise HTTPException(status_code=400, detail=f"Curve ordinal {curve_ordinal} is not available")
        return selected, warnings

    if preview_options:
        warnings.append("No analytical relay curve ordinal was selected; the first stored curve row was used.")
        return preview_options[0], warnings
    return None, warnings


def _load_tcp_stored_points(db: Session, curve_parent_source_id: int, source_ordinal: int) -> list[dict[str, object]]:
    rows = db.execute(
        text(
            """
            SELECT
                p.source_ordinal,
                p.time_dial,
                p.td_desc,
                p.current_index,
                p.current_value,
                p.trip_time_seconds
            FROM tcc.relay_curve_points_tcp p
            JOIN tcc.relay_curves_tcp c ON c.relay_curve_tcp_id = p.relay_curve_tcp_id
            WHERE c.source_row_id = :curve_parent_source_id
              AND p.source_ordinal = :source_ordinal
            ORDER BY p.current_index
            """
        ),
        {
            "curve_parent_source_id": curve_parent_source_id,
            "source_ordinal": source_ordinal,
        },
    ).fetchall()
    return [_normalize_mapping(_row_mapping(row)) for row in rows]


def _relay_candidate_values(candidate_overrides: Optional[RelayCandidateOverrides]) -> dict[str, float]:
    if candidate_overrides is None:
        return {}

    values = candidate_overrides.model_dump(exclude_none=True)
    normalized: dict[str, float] = {}
    for key, value in values.items():
        numeric_value = float(value)
        if numeric_value <= 0:
            raise HTTPException(status_code=422, detail=f"{key} must be greater than 0")
        normalized[key] = numeric_value
    return normalized


def _relay_effective_current_multiples(
    current_multiples: list[float],
    candidate_values: dict[str, float],
) -> list[float]:
    pickup_multiplier = candidate_values.get("pickup_multiplier", 1.0)
    voltage_threshold_multiplier = candidate_values.get("voltage_threshold_multiplier", 1.0)
    normalization_multiplier = pickup_multiplier * voltage_threshold_multiplier
    return [float(current_multiple) / normalization_multiplier for current_multiple in current_multiples]


def _load_relay_preview_bundle(
    db: Session,
    *,
    td_section_source_id: int,
    curve_parent_source_id: Optional[int],
    curve_ordinal: Optional[int],
    source_ordinal: Optional[int],
    time_dial: Optional[float],
    current_multiples: list[float],
    candidate_overrides: Optional[RelayCandidateOverrides] = None,
) -> dict[str, object]:
    settings_bundle = _load_relay_settings_bundle(db, td_section_source_id)
    candidate_values = _relay_candidate_values(candidate_overrides)
    effective_current_multiples = _relay_effective_current_multiples(current_multiples, candidate_values)
    bundle = {
        **settings_bundle,
        "warnings": [],
        "candidate_values": candidate_values,
        "requested_current_multiples": list(current_multiples),
        "evaluated_current_multiples": effective_current_multiples,
    }
    family_code = int(bundle["family_code"])
    unsupported_reason = bundle.get("unsupported_reason")
    family = family_from_model_code(family_code)

    if not bundle["supported"]:
        bundle["status"] = RelayEvaluationStatus.UNSUPPORTED.value
        bundle["warnings"] = [unsupported_reason] if unsupported_reason else []
        bundle["result"] = None
        bundle["selected_option"] = None
        return bundle

    selected_option, warnings = _select_relay_preview_option(
        settings_bundle=settings_bundle,
        curve_parent_source_id=curve_parent_source_id,
        curve_ordinal=curve_ordinal,
        source_ordinal=source_ordinal,
        time_dial=time_dial,
    )
    bundle["warnings"] = warnings
    if selected_option is None:
        message = "No stored relay preview option is available for the selected TD-section."
        bundle["status"] = RelayEvaluationStatus.UNSUPPORTED.value
        bundle["warnings"].append(message)
        bundle["result"] = None
        bundle["selected_option"] = None
        bundle["unsupported_reason"] = message
        return bundle

    try:
        if family == RelayFormulaCode.TCP:
            selected_time_dial = float(selected_option["time_dial"])
            candidate_time_dial = candidate_values.get("time_dial")
            if candidate_time_dial is not None and not _float_matches(candidate_time_dial, selected_time_dial):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "TCP candidate time_dial cannot be evaluated against a stored point row; "
                        "select a stored TCP time-dial row or omit the candidate time_dial override."
                    ),
                )
            stored_points = _load_tcp_stored_points(
                db,
                int(selected_option["curve_parent_source_id"]),
                int(selected_option["source_ordinal"]),
            )
            definition = RelayCurveDefinition(
                family=family,
                curve_name=selected_option.get("curve_name") or f"tcp_{selected_option['curve_parent_source_id']}",
                source_row_id=int(selected_option["curve_parent_source_id"]),
                parent_source_id=int(td_section_source_id),
                ordinal=int(selected_option["source_ordinal"]),
                points=tuple(
                    RelayCurvePoint(
                        current_multiple=float(point["current_value"]),
                        trip_time_seconds=float(point["trip_time_seconds"]),
                        source_ordinal=int(point["source_ordinal"]),
                        time_dial=float(point["time_dial"]),
                        label=point.get("td_desc"),
                    )
                    for point in stored_points
                ),
                metadata={
                    "time_dial": float(selected_option["time_dial"]),
                    "source_ordinal": int(selected_option["source_ordinal"]),
                    "td_desc": selected_option.get("td_desc"),
                },
            )
            evaluated = evaluate_curve_definition(
                definition,
                effective_current_multiples,
                time_dial=selected_time_dial,
            )
        else:
            baseline_time_dial = float(time_dial) if time_dial is not None else 1.0
            analytical_time_dial = candidate_values.get("time_dial", baseline_time_dial)
            definition = RelayCurveDefinition(
                family=family,
                curve_name=selected_option.get("curve_name") or f"curve_{selected_option['curve_ordinal']}",
                source_row_id=int(selected_option["curve_parent_source_id"]),
                parent_source_id=int(td_section_source_id),
                ordinal=int(selected_option["curve_ordinal"]),
                coefficients={
                    key: value
                    for key, value in selected_option.get("coefficients", {}).items()
                },
            )
            evaluated = evaluate_curve_definition(definition, effective_current_multiples, time_dial=analytical_time_dial)
        bundle["status"] = evaluated.status.value
        bundle["result"] = evaluated
        bundle["selected_option"] = selected_option
        return bundle
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
                JOIN tcc.etu_sensors s ON s.id = p.sensor_id
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
    if table_name == "tcc.etu_ltd_bands":
        rows = db.execute(
            text(
                """
                SELECT
                    ltd_desc AS band,
                    ltd_desc AS label,
                    ltd_setting AS open_time,
                    NULL::numeric AS clear_time,
                    false AS is_default
                FROM tcc.etu_ltd_bands
                WHERE sensor_id = :sensor_id
                ORDER BY ltd_setting NULLS LAST, id
                """
            ),
            {"sensor_id": sensor_id},
        ).fetchall()
    elif table_name == "tcc.etu_std_bands":
        rows = db.execute(
            text(
                """
                SELECT
                    std_desc AS band,
                    std_desc AS label,
                    std_open AS open_time,
                    std_clear AS clear_time,
                    false AS is_default
                FROM tcc.etu_std_bands
                WHERE sensor_id = :sensor_id
                ORDER BY ordinal NULLS LAST, std_open NULLS LAST
                """
            ),
            {"sensor_id": sensor_id},
        ).fetchall()
    elif table_name == "tcc.etu_gfd_bands":
        rows = db.execute(
            text(
                """
                SELECT
                    gfd_desc AS band,
                    gfd_desc AS label,
                    gfd_open AS open_time,
                    gfd_clear AS clear_time,
                    false AS is_default
                FROM tcc.etu_gfd_bands
                WHERE sensor_id = :sensor_id
                ORDER BY ordinal NULLS LAST, gfd_open NULLS LAST
                """
            ),
            {"sensor_id": sensor_id},
        ).fetchall()
    else:
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


def _load_direct_numeric_settings(db: Session, table_name: str, value_column: str, sensor_id: int) -> list[float]:
    rows = db.execute(
        text(
            f"""
            SELECT DISTINCT {value_column} AS value
            FROM {table_name}
            WHERE sensor_id = :sensor_id
              AND {value_column} IS NOT NULL
            ORDER BY {value_column}
            """
        ),
        {"sensor_id": sensor_id},
    ).fetchall()

    return [float(row._mapping["value"]) for row in rows]


def _load_direct_available_settings(db: Session, sensor_id: int) -> dict[str, object]:
    return {
        "plug_values": _load_direct_numeric_settings(db, "tcc.etu_plugs", "value", sensor_id),
        "ltpu_settings": _load_direct_numeric_settings(db, "tcc.etu_ltpu_pickups", "ltd_setting", sensor_id),
        "ltd_settings": _load_delay_band_settings(db, "tcc.etu_ltd_bands", sensor_id),
        "ltd_multipliers": _load_direct_numeric_settings(db, "tcc.etu_ltpu_multipliers", "ltd_c", sensor_id),
        "stpu_settings": _load_direct_numeric_settings(db, "tcc.etu_stpu_pickups", "stp_setting", sensor_id),
        "inst_settings": _load_direct_numeric_settings(db, "tcc.etu_inst_pickups", "ip_setting", sensor_id),
        "gfpu_settings": _load_direct_numeric_settings(db, "tcc.etu_gfpu_pickups", "gfp_setting", sensor_id),
    }


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
    allow_fallback: bool = True,
):
    if table_name == "tcc.etu_ltd_bands":
        if setting is not None:
            matched_row = db.execute(
                text(
                    """
                    SELECT ltd_setting AS open_time,
                           NULL::numeric AS clear_time,
                           id AS ordinal,
                           false AS is_default
                    FROM tcc.etu_ltd_bands
                    WHERE sensor_id = :sensor_id AND ltd_setting = :setting
                    ORDER BY id
                    LIMIT 1
                    """
                ),
                {"sensor_id": sensor_id, "setting": setting},
            ).fetchone()
            if matched_row is not None:
                return matched_row
        if not allow_fallback:
            return None

        return db.execute(
            text(
                """
                SELECT ltd_setting AS open_time,
                       NULL::numeric AS clear_time,
                       id AS ordinal,
                       false AS is_default
                FROM tcc.etu_ltd_bands
                WHERE sensor_id = :sensor_id
                ORDER BY ltd_setting, id
                LIMIT 1
                """
            ),
            {"sensor_id": sensor_id},
        ).fetchone()

    if table_name == "tcc.etu_std_bands":
        if setting is not None:
            matched_row = db.execute(
                text(
                    """
                    SELECT std_open AS open_time,
                           std_clear AS clear_time,
                           ordinal,
                           false AS is_default
                    FROM tcc.etu_std_bands
                    WHERE sensor_id = :sensor_id AND std_open = :setting
                    ORDER BY ordinal
                    LIMIT 1
                    """
                ),
                {"sensor_id": sensor_id, "setting": setting},
            ).fetchone()
            if matched_row is not None:
                return matched_row
        if not allow_fallback:
            return None

        return db.execute(
            text(
                """
                SELECT std_open AS open_time,
                       std_clear AS clear_time,
                       ordinal,
                       false AS is_default
                FROM tcc.etu_std_bands
                WHERE sensor_id = :sensor_id
                ORDER BY ordinal, std_open
                LIMIT 1
                """
            ),
            {"sensor_id": sensor_id},
        ).fetchone()

    if table_name == "tcc.etu_gfd_bands":
        if setting is not None:
            matched_row = db.execute(
                text(
                    """
                    SELECT gfd_open AS open_time,
                           gfd_clear AS clear_time,
                           ordinal,
                           false AS is_default
                    FROM tcc.etu_gfd_bands
                    WHERE sensor_id = :sensor_id AND gfd_open = :setting
                    ORDER BY ordinal
                    LIMIT 1
                    """
                ),
                {"sensor_id": sensor_id, "setting": setting},
            ).fetchone()
            if matched_row is not None:
                return matched_row
        if not allow_fallback:
            return None

        return db.execute(
            text(
                """
                SELECT gfd_open AS open_time,
                       gfd_clear AS clear_time,
                       ordinal,
                       false AS is_default
                FROM tcc.etu_gfd_bands
                WHERE sensor_id = :sensor_id
                ORDER BY ordinal, gfd_open
                LIMIT 1
                """
            ),
            {"sensor_id": sensor_id},
        ).fetchone()

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
    if not allow_fallback:
        return None

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


def _delay_band_table_name(element_key: str) -> str:
    if element_key == "ltd":
        return "tcc.etu_ltd_bands"
    if element_key == "std":
        return "tcc.etu_std_bands"
    if element_key == "gfd":
        return "tcc.etu_gfd_bands"
    raise ValueError(f"Unsupported delay element {element_key!r}")


def _resolve_plot_delay_inputs(
    db: Session,
    sensor_id: int,
    element_key: str,
    legacy_setting: Optional[float],
    delay_setting: Optional[float],
    test_multiple: Optional[float],
    default_test_multiple: float,
) -> tuple[Optional[float], float, Optional[float]]:
    """Resolve backward-compatible delay band and test-multiple inputs.

    The legacy request fields used one number for two concepts. If a legacy value
    matches a live delay-band open time, treat it as the selected band and use the
    NETA default multiple. Otherwise keep treating it as the old test multiple.
    Explicit new fields always win.
    """
    explicit_delay = delay_setting is not None
    explicit_multiple = test_multiple is not None
    if explicit_delay or explicit_multiple:
        selected_delay = delay_setting if explicit_delay else legacy_setting
        selected_multiple = test_multiple if explicit_multiple else default_test_multiple
        return selected_delay, selected_multiple, selected_delay

    if legacy_setting is None:
        return None, default_test_multiple, None

    matched_band = _load_direct_delay_band(
        db,
        _delay_band_table_name(element_key),
        sensor_id,
        legacy_setting,
        allow_fallback=False,
    )
    if matched_band is not None:
        return legacy_setting, default_test_multiple, legacy_setting

    return None, legacy_setting, legacy_setting


def _ltd_reference_delay_surface(
    delay_setting: Optional[float],
    test_multiple: Optional[float],
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    if delay_setting is None or test_multiple in (None, 0):
        return None, None, None

    nominal = float(delay_setting) * (6.0 / float(test_multiple)) ** 2
    return nominal, 0.7 * nominal, nominal


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


def _round_deviation_pct(measured_value: float, expected_value: float) -> Optional[float]:
    if expected_value in (None, 0):
        return None

    deviation = (
        (Decimal(str(measured_value)) - Decimal(str(expected_value)))
        / Decimal(str(expected_value))
    ) * Decimal("100")
    return float(deviation.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _build_python_pickup_eval_data(
    calc_data: dict[str, object],
    measured: dict[str, object],
    warning: Optional[str] = None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "sensor_desc": calc_data.get("sensor_desc", ""),
        "maint_mode": calc_data.get("maint_mode", False),
        "maint_capable": calc_data.get("maint_capable", False),
        "maint_support_level": calc_data.get("maint_support_level", "none"),
        "manufacturer": calc_data.get("manufacturer"),
        "trip_type": calc_data.get("trip_type"),
        "trip_style": calc_data.get("trip_style"),
        "breaker_context_label": calc_data.get("breaker_context_label"),
        "warnings": [warning] if warning else [],
    }

    pickup_results: list[bool] = []
    for key in ("ltpu", "stpu", "inst", "gfpu"):
        calc_elem = calc_data.get(key)
        measurement = measured.get(key.upper())
        if calc_elem is None or measurement is None or measurement.measured_current is None:
            continue

        measured_current = measurement.measured_current
        limit_low = calc_elem.get("limit_low")
        limit_high = calc_elem.get("limit_high")
        lower_ok = True if limit_low is None else measured_current >= limit_low
        upper_ok = True if limit_high is None else measured_current <= limit_high
        passed = bool(lower_ok and upper_ok)
        expected = calc_elem.get("test_current")
        deviation_pct = None
        if expected not in (None, 0):
            deviation_pct = _round_deviation_pct(measured_current, expected)

        data[key] = {
            "expected": expected,
            "measured": measured_current,
            "limit_low": limit_low,
            "limit_high": limit_high,
            "pass": passed,
            "deviation_pct": deviation_pct,
        }
        pickup_results.append(passed)

    data["overall_pass"] = all(pickup_results) if pickup_results else False
    return data

    return expected_time, time_low, time_high


def _build_cascade_where(
    filters: dict[str, Optional[int]],
    exclude: set[str] | None = None,
    prefix: str = "",
) -> tuple[str, dict[str, int]]:
    exclude = exclude or set()
    clauses: list[str] = []
    params: dict[str, int] = {}

    for field in ("manufacturer_id", "trip_type_id", "trip_style_id", "sensor_id"):
        if field in exclude:
            continue
        value = filters.get(field)
        if value is None:
            continue
        clauses.append(f"{prefix}{field} = :{field}")
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


_ETU_BREAKER_CASCADE_CTE = """
WITH etu_breaker_combined AS (
    SELECT
        'ICCB'::text AS breaker_class,
        m.id AS manufacturer_id,
        m.mfr_name AS manufacturer_name,
        b.id AS breaker_id,
        b.name AS breaker_name,
        s.id AS breaker_style_id,
        s.frame AS breaker_style_name
    FROM tcc.brk_iccb b
    INNER JOIN tcc.brk_iccb_styles s ON s.breaker_id = b.id
    INNER JOIN tcc.manufacturers m ON m.id = b.manufacturer_id
    UNION ALL
    SELECT
        'MCCB'::text,
        m.id,
        m.mfr_name,
        b.id,
        b.name,
        s.id,
        s.frame
    FROM tcc.brk_mccb b
    INNER JOIN tcc.brk_mccb_styles s ON s.breaker_id = b.id
    INNER JOIN tcc.manufacturers m ON m.id = b.manufacturer_id
    UNION ALL
    SELECT
        'PCB'::text,
        m.id,
        m.mfr_name,
        b.id,
        b.name,
        s.id,
        s.frame
    FROM tcc.brk_pcb b
    INNER JOIN tcc.brk_pcb_styles s ON s.breaker_id = b.id
    INNER JOIN tcc.manufacturers m ON m.id = b.manufacturer_id
)
"""

_ETU_BREAKER_CASCADE_CLASSES = ("ICCB", "MCCB", "PCB")


def _build_cross_half_breaker_filter(
    breaker_class: Optional[str],
    breaker_id: Optional[int],
    breaker_style_id: Optional[int],
) -> tuple[str, dict[str, object], str]:
    parts: list[str] = []
    params: dict[str, object] = {}
    if breaker_class is not None:
        parts.append("breaker_class = :xh_breaker_class")
        params["xh_breaker_class"] = breaker_class
    if breaker_id is not None:
        parts.append("breaker_id = :xh_breaker_id")
        params["xh_breaker_id"] = breaker_id
    if breaker_style_id is not None:
        parts.append("breaker_style_id = :xh_breaker_style_id")
        params["xh_breaker_style_id"] = breaker_style_id
    if not parts:
        return "", {}, ""

    inner_where = " AND ".join(parts)
    clause = (
        " AND v.manufacturer_id IN ("
        "SELECT DISTINCT manufacturer_id FROM etu_breaker_combined "
        f"WHERE {inner_where})"
    )
    return clause, params, _ETU_BREAKER_CASCADE_CTE


def _build_cross_half_trip_unit_filter(
    trip_type_id: Optional[int],
    trip_style_id: Optional[int],
    sensor_id: Optional[int],
) -> tuple[str, dict[str, object]]:
    parts: list[str] = []
    params: dict[str, object] = {}
    if trip_type_id is not None:
        parts.append("trip_type_id = :xh_trip_type_id")
        params["xh_trip_type_id"] = trip_type_id
    if trip_style_id is not None:
        parts.append("trip_style_id = :xh_trip_style_id")
        params["xh_trip_style_id"] = trip_style_id
    if sensor_id is not None:
        parts.append("sensor_id = :xh_sensor_id")
        params["xh_sensor_id"] = sensor_id
    if not parts:
        return "", {}

    inner_where = " AND ".join(parts)
    clause = (
        " AND manufacturer_id IN ("
        "SELECT DISTINCT manufacturer_id FROM vw_trip_unit_cascade "
        f"WHERE {inner_where})"
    )
    return clause, params


def _build_cascade_plug_join(
    plug_value: Optional[float],
    *,
    alias: str = "",
) -> tuple[str, dict[str, object]]:
    if plug_value is None:
        return "", {}

    qualified_sensor_id = f"{alias}.sensor_id" if alias else "sensor_id"
    return (
        f"JOIN tcc.etu_plugs p_filter ON p_filter.sensor_id = {qualified_sensor_id} AND p_filter.value = :plug_value",
        {"plug_value": float(plug_value)},
    )


def _build_etu_search_where(
    scope_filters: dict[str, Optional[int]],
    *,
    q: Optional[str] = None,
    prefix: str = "v.",
) -> tuple[str, dict[str, object]]:
    where_sql, params = _build_cascade_where(scope_filters, prefix=prefix)
    if q and q.strip():
        stripped_query = q.strip()
        query_sql = (
            f"({prefix}manufacturer_name ILIKE :q "
            f"OR {prefix}trip_type_name ILIKE :q "
            f"OR {prefix}trip_style_name ILIKE :q "
            f"OR {prefix}sensor_desc ILIKE :q)"
        )
        if where_sql:
            where_sql = f"{where_sql} AND {query_sql}"
        else:
            where_sql = f"WHERE {query_sql}"
        params["q"] = f"%{stripped_query}%"
        params["q_exact"] = stripped_query
        params["q_prefix"] = f"{stripped_query}%"
    return where_sql, params


def _etu_search_rank_sql(q: Optional[str], *, prefix: str = "v.") -> str:
    if not q or not q.strip():
        return "0"

    return (
        "CASE "
        f"WHEN LOWER(COALESCE({prefix}manufacturer_name, '')) = LOWER(:q_exact) THEN 0 "
        f"WHEN {prefix}manufacturer_name ILIKE :q_prefix THEN 1 "
        f"WHEN {prefix}manufacturer_name ILIKE :q THEN 2 "
        f"WHEN {prefix}trip_type_name ILIKE :q THEN 3 "
        f"WHEN {prefix}trip_style_name ILIKE :q THEN 4 "
        f"WHEN {prefix}sensor_desc ILIKE :q THEN 5 "
        "ELSE 6 END"
    )


def _etu_search_order_by() -> str:
    return (
        "search_rank, v.manufacturer_name, v.trip_type_name, v.trip_style_name, "
        "v.sensor_rating NULLS LAST, v.sensor_desc"
    )


def _load_etu_plug_value_map_sql(db: Session, sensor_ids: list[int]) -> dict[int, list[float]]:
    if not sensor_ids:
        return {}

    placeholder_names = [f"sensor_id_{index}" for index, _ in enumerate(sensor_ids)]
    in_clause = ", ".join(f":{name}" for name in placeholder_names)
    params: dict[str, object] = {
        name: sensor_id for name, sensor_id in zip(placeholder_names, sensor_ids)
    }
    rows = db.execute(
        text(
            f"""
            SELECT sensor_id, value
            FROM tcc.etu_plugs
            WHERE sensor_id IN ({in_clause})
            ORDER BY sensor_id, value
            """
        ),
        params,
    ).fetchall()

    plug_map: dict[int, list[float]] = {}
    seen_pairs: set[tuple[int, float]] = set()
    for row in rows:
        mapping = row._mapping if hasattr(row, "_mapping") else row
        sensor_id = mapping.get("sensor_id")
        value = mapping.get("value")
        if sensor_id is None or value is None:
            continue
        sensor_id = int(sensor_id)
        plug_value = float(value)
        pair = (sensor_id, plug_value)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        plug_map.setdefault(sensor_id, []).append(plug_value)

    return plug_map


def _build_etu_breaker_cascade_where(
    scope: dict[str, Optional[object]],
    excluded: set[str] | None = None,
) -> tuple[str, dict[str, object]]:
    excluded = excluded or set()
    clauses: list[str] = []
    params: dict[str, object] = {}

    if scope.get("manufacturer_id") is not None and "manufacturer_id" not in excluded:
        clauses.append("manufacturer_id = :manufacturer_id")
        params["manufacturer_id"] = scope["manufacturer_id"]
    if scope.get("breaker_class") is not None and "breaker_class" not in excluded:
        clauses.append("breaker_class = :breaker_class")
        params["breaker_class"] = scope["breaker_class"]
    if scope.get("breaker_id") is not None and "breaker_id" not in excluded:
        clauses.append("breaker_id = :breaker_id")
        params["breaker_id"] = scope["breaker_id"]
    if scope.get("breaker_style_id") is not None and "breaker_style_id" not in excluded:
        clauses.append("breaker_style_id = :breaker_style_id")
        params["breaker_style_id"] = scope["breaker_style_id"]

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_sql, params


def _etu_breaker_cascade_level(scope: dict[str, Optional[object]]) -> str:
    if scope.get("breaker_id") is not None or scope.get("breaker_style_id") is not None:
        return "breaker_styles"
    if scope.get("manufacturer_id") is not None or scope.get("breaker_class") is not None:
        return "breakers"
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
            rollback = getattr(db, "rollback", None)
            if callable(rollback):
                rollback()
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
            rollback = getattr(db, "rollback", None)
            if callable(rollback):
                rollback()
            logger.warning("IEEE curve generation failed: %s", exc)
            warnings.append(f"Curve generation unavailable: {exc}")
    except Exception as exc:
        rollback = getattr(db, "rollback", None)
        if callable(rollback):
            rollback()
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
    test_multiple: Optional[float],
    curves: list[PlotCurve],
    expected_current: float,
    maint_mode: bool = False,
    maint_profile: Optional[dict[str, object]] = None,
    fallback_open: Optional[float] = None,
    fallback_clear: Optional[float] = None,
    use_ltd_reference_window: bool = False,
) -> tuple[Optional[float], Optional[float], Optional[float], str]:
    if element_key == "ltd":
        if use_ltd_reference_window and setting is not None and test_multiple not in (None, 0):
            expected_time, time_low, time_high = _ltd_reference_delay_surface(setting, test_multiple)
            return expected_time, time_low, time_high, "ltd_reference_window"

        band_row = _load_direct_delay_band(db, "tcc.etu_ltd_bands", sensor_id, setting)
        if band_row is not None:
            expected_time, time_low, time_high = _band_row_to_delay_surface(band_row)
            return expected_time, time_low, time_high, "band_table"

    if element_key == "std":
        band_row = _load_direct_delay_band(db, "tcc.etu_std_bands", sensor_id, setting)
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

        band_row = _load_direct_delay_band(db, "tcc.etu_gfd_bands", sensor_id, setting)
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

_TMT_FACET_NAMES = (
    "breaker_class",
    "manufacturer_id",
    "breaker_id",
    "breaker_style_id",
    "frame_size",
    "amp_rating",
)

_TMT_FACET_CTE = """
WITH tmt_catalog AS (
    SELECT
        f.id AS frame_id,
        UPPER(f.breaker_class) AS breaker_class,
        b.manufacturer_id AS manufacturer_id,
        b.id AS breaker_id,
        s.id AS breaker_style_id,
        f.size AS frame_size,
        a.rating AS amp_rating
    FROM tcc.tmt_frames f
    INNER JOIN tcc.brk_iccb_styles s ON s.id = f.breaker_style_id
    INNER JOIN tcc.brk_iccb b ON b.id = s.breaker_id
    LEFT JOIN tcc.tmt_amps a ON a.frame_id = f.id
    WHERE UPPER(f.breaker_class) = 'ICCB'

    UNION ALL

    SELECT
        f.id AS frame_id,
        UPPER(f.breaker_class) AS breaker_class,
        b.manufacturer_id AS manufacturer_id,
        b.id AS breaker_id,
        s.id AS breaker_style_id,
        f.size AS frame_size,
        a.rating AS amp_rating
    FROM tcc.tmt_frames f
    INNER JOIN tcc.brk_mccb_styles s ON s.id = f.breaker_style_id
    INNER JOIN tcc.brk_mccb b ON b.id = s.breaker_id
    LEFT JOIN tcc.tmt_amps a ON a.frame_id = f.id
    WHERE UPPER(f.breaker_class) = 'MCCB'

    UNION ALL

    SELECT
        f.id AS frame_id,
        UPPER(f.breaker_class) AS breaker_class,
        b.manufacturer_id AS manufacturer_id,
        b.id AS breaker_id,
        s.id AS breaker_style_id,
        f.size AS frame_size,
        a.rating AS amp_rating
    FROM tcc.tmt_frames f
    INNER JOIN tcc.brk_pcb_styles s ON s.id = f.breaker_style_id
    INNER JOIN tcc.brk_pcb b ON b.id = s.breaker_id
    LEFT JOIN tcc.tmt_amps a ON a.frame_id = f.id
    WHERE UPPER(f.breaker_class) = 'PCB'
)
"""


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


def _build_tmt_facet_where(
    filters: dict[str, object],
    *,
    excluded: tuple[str, ...] = (),
) -> tuple[str, dict[str, object]]:
    clauses: list[str] = []
    params: dict[str, object] = {}

    if filters.get("breaker_class") is not None and "breaker_class" not in excluded:
        clauses.append("c.breaker_class = :breaker_class")
        params["breaker_class"] = filters["breaker_class"]

    for key in ("manufacturer_id", "breaker_id", "breaker_style_id"):
        if filters.get(key) is not None and key not in excluded:
            clauses.append(f"c.{key} = :{key}")
            params[key] = filters[key]

    if filters.get("frame_size") is not None and "frame_size" not in excluded:
        clauses.append("c.frame_size = :frame_size")
        params["frame_size"] = filters["frame_size"]

    if filters.get("amp_rating") is not None and "amp_rating" not in excluded:
        clauses.append("c.amp_rating = :amp_rating")
        params["amp_rating"] = filters["amp_rating"]

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where_sql, params


def _load_tmt_facets(db: Session, filters: dict[str, object]) -> dict[str, object]:
    where_sql, params = _build_tmt_facet_where(filters)
    total_matching_frames = db.execute(
        text(
            f"""
            {_TMT_FACET_CTE}
            SELECT COUNT(DISTINCT c.frame_id) AS total_matching_frames
            FROM tmt_catalog c
            {where_sql}
            """
        ),
        params,
    ).scalar() or 0

    facets: list[TMTFacet] = []
    for facet_name in _TMT_FACET_NAMES:
        facet_where_sql, facet_params = _build_tmt_facet_where(filters, excluded=(facet_name,))
        rows = db.execute(
            text(
                f"""
                {_TMT_FACET_CTE}
                SELECT DISTINCT c.{facet_name} AS value
                FROM tmt_catalog c
                {facet_where_sql}
                {'AND' if facet_where_sql else 'WHERE'} c.{facet_name} IS NOT NULL
                ORDER BY c.{facet_name}
                """
            ),
            facet_params,
        ).fetchall()

        values = [_normalize_scalar(row._mapping["value"]) for row in rows]
        facets.append(TMTFacet(name=facet_name, values=values, cardinality=len(values)))

    return {
        "facets": facets,
        "total_matching_frames": int(total_matching_frames),
        "active_filters": {
            key: _normalize_scalar(value)
            for key, value in filters.items()
            if value is not None
        },
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
    table_schema, bare_table_name = (
        table_name.split(".", 1) if "." in table_name else (None, table_name)
    )
    rows = db.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table_name
              AND (:table_schema IS NULL OR table_schema = :table_schema)
            """
        ),
        {"table_schema": table_schema, "table_name": bare_table_name},
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
        "tcc.emt": _get_table_columns(db, "tcc.emt"),
        "tcc.emt_frames": _get_table_columns(db, "tcc.emt_frames"),
        "tcc.emt_frame_amps": _get_table_columns(db, "tcc.emt_frame_amps"),
        "tcc.emt_sections": _get_table_columns(db, "tcc.emt_sections"),
        "tcc.emt_pickups": _get_table_columns(db, "tcc.emt_pickups"),
        "tcc.emt_band_names": _get_table_columns(db, "tcc.emt_band_names"),
        "tcc.emt_curves": _get_table_columns(db, "tcc.emt_curves"),
    }

    if any(not columns for columns in table_columns.values()):
        raise HTTPException(
            status_code=503,
            detail=(
                "EMT catalog tables are not available in the current database. "
                "The EMT route surface is implemented but remains migration-gated."
            ),
        )

    emt_cols = table_columns["tcc.emt"]
    frame_cols = table_columns["tcc.emt_frames"]
    amp_cols = table_columns["tcc.emt_frame_amps"]
    section_cols = table_columns["tcc.emt_sections"]
    pickup_cols = table_columns["tcc.emt_pickups"]
    band_cols = table_columns["tcc.emt_band_names"]
    curve_cols = table_columns["tcc.emt_curves"]

    return {
        "emt": {
            "manufacturer_id": _pick_required_column("tcc.emt", emt_cols, "manufacturer id", ("manufacturer_id", "mfr_id")),
            "type_name": _pick_required_column("tcc.emt", emt_cols, "type name", ("type_name", "type")),
            "style_name": _pick_required_column("tcc.emt", emt_cols, "style name", ("style_name", "style")),
            "tcc_number": _pick_required_column("tcc.emt", emt_cols, "TCC number", ("tcc_number", "tcc_no", "tccnumber")),
            "trip_char": _pick_required_column("tcc.emt", emt_cols, "trip characteristic", ("trip_char",)),
            "trip_plug": _pick_required_column("tcc.emt", emt_cols, "trip plug", ("trip_plug",)),
        },
        "frames": {
            "emt_id": _pick_required_column("tcc.emt_frames", frame_cols, "EMT parent", ("emt_id", "style_id")),
            "frame_size": _pick_required_column("tcc.emt_frames", frame_cols, "frame size", ("frame_size", "size", "framesize")),
            "frame_desc": _pick_required_column("tcc.emt_frames", frame_cols, "frame description", ("frame_desc", "frame_description", "framedesc")),
        },
        "amps": {
            "frame_id": _pick_required_column("tcc.emt_frame_amps", amp_cols, "frame parent", ("frame_id", "frameid")),
            "rating": _pick_required_column("tcc.emt_frame_amps", amp_cols, "amp rating", ("rating", "trip_amp", "tripamp")),
        },
        "sections": {
            "frame_id": _pick_required_column("tcc.emt_sections", section_cols, "frame parent", ("frame_id", "frameid")),
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
            "section_id": _pick_required_column("tcc.emt_pickups", pickup_cols, "section parent", ("section_id", "sec_id", "secid")),
            "setting": _pick_optional_column(pickup_cols, ("setting",)),
            "description": _pick_optional_column(pickup_cols, ("description", "label")),
        },
        "bands": {
            "section_id": _pick_required_column("tcc.emt_band_names", band_cols, "section parent", ("section_id", "sec_id", "secid")),
            "band_name": _pick_optional_column(band_cols, ("band_name", "name")),
            "ordinal": _pick_optional_column(band_cols, ("ordinal",)),
            "current_at": _pick_optional_column(band_cols, ("current_at", "currentat")),
        },
        "curves": {
            "band_id": _pick_required_column("tcc.emt_curves", curve_cols, "band parent", ("band_id", "parent_id", "parentid")),
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
            m.mfr_name AS manufacturer_name,
            e.{cols['emt']['type_name']} AS type_name,
            e.{cols['emt']['style_name']} AS style_name,
            e.{cols['emt']['tcc_number']} AS tcc_number,
            e.{cols['emt']['trip_char']} AS trip_char,
            e.{cols['emt']['trip_plug']} AS trip_plug,
            f.{cols['frames']['frame_size']} AS frame_size,
            f.{cols['frames']['frame_desc']} AS frame_desc,
            COALESCE(amp_counts.amp_rating_count, 0) AS amp_rating_count,
            COALESCE(sec_counts.section_count, 0) AS section_count
        FROM tcc.emt_frames f
        INNER JOIN tcc.emt e ON f.{cols['frames']['emt_id']} = e.id
        LEFT JOIN tcc.manufacturers m ON m.id = e.{cols['emt']['manufacturer_id']}
        LEFT JOIN (
            SELECT {cols['amps']['frame_id']} AS frame_id, COUNT(*) AS amp_rating_count
            FROM tcc.emt_frame_amps
            GROUP BY {cols['amps']['frame_id']}
        ) amp_counts ON amp_counts.frame_id = f.id
        LEFT JOIN (
            SELECT {cols['sections']['frame_id']} AS frame_id, COUNT(*) AS section_count
            FROM tcc.emt_sections
            GROUP BY {cols['sections']['frame_id']}
        ) sec_counts ON sec_counts.frame_id = f.id
        {where_sql}
        ORDER BY m.mfr_name NULLS LAST, e.{cols['emt']['type_name']}, e.{cols['emt']['style_name']}, f.id
        LIMIT :limit
        """
    )

    rows = db.execute(sql, params).fetchall()
    return [_normalize_mapping(dict(row._mapping)) for row in rows]


def _load_emt_facets(
    db: Session,
    filters: dict[str, object],
) -> dict[str, object]:
    cols = _resolve_emt_contract_columns(db)
    facet_specs = (
        ("manufacturer_id", f"e.{cols['emt']['manufacturer_id']}"),
        ("trip_char", f"e.{cols['emt']['trip_char']}"),
        ("trip_plug", f"e.{cols['emt']['trip_plug']}"),
        ("frame_desc", f"f.{cols['frames']['frame_desc']}"),
        ("type_name", f"e.{cols['emt']['type_name']}"),
    )

    def build_where(excluded: tuple[str, ...] = ()) -> tuple[str, dict[str, object]]:
        clauses: list[str] = []
        params: dict[str, object] = {}
        for facet_name, sql_expr in facet_specs:
            if filters.get(facet_name) is None or facet_name in excluded:
                continue
            clauses.append(f"{sql_expr} = :{facet_name}")
            params[facet_name] = filters[facet_name]
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return where_sql, params

    from_sql = (
        "FROM tcc.emt_frames f "
        f"INNER JOIN tcc.emt e ON f.{cols['frames']['emt_id']} = e.id"
    )

    where_sql, params = build_where()
    total_matching_frames = db.execute(
        text(
            f"""
            SELECT COUNT(DISTINCT f.id) AS total_matching_frames
            {from_sql}
            {where_sql}
            """
        ),
        params,
    ).scalar() or 0

    facets: list[EMTFacet] = []
    for facet_name, sql_expr in facet_specs:
        facet_where_sql, facet_params = build_where((facet_name,))
        rows = db.execute(
            text(
                f"""
                SELECT DISTINCT {sql_expr} AS value
                {from_sql}
                {facet_where_sql}
                {'AND' if facet_where_sql else 'WHERE'} {sql_expr} IS NOT NULL
                ORDER BY {sql_expr}
                """
            ),
            facet_params,
        ).fetchall()
        values = [_normalize_scalar(row._mapping["value"]) for row in rows]
        facets.append(EMTFacet(name=facet_name, values=values, cardinality=len(values)))

    return {
        "facets": facets,
        "total_matching_frames": int(total_matching_frames),
        "active_filters": {
            key: _normalize_scalar(value)
            for key, value in filters.items()
            if value is not None
        },
    }


def _load_emt_frame_context_bundle(db: Session, frame_id: int) -> dict[str, object]:
    cols = _resolve_emt_contract_columns(db)

    frame_row = db.execute(
        text(
            f"""
            SELECT
                e.id AS emt_id,
                f.id AS frame_id,
                e.{cols['emt']['manufacturer_id']} AS manufacturer_id,
                m.mfr_name AS manufacturer_name,
                e.{cols['emt']['type_name']} AS type_name,
                e.{cols['emt']['style_name']} AS style_name,
                e.{cols['emt']['tcc_number']} AS tcc_number,
                e.{cols['emt']['trip_char']} AS trip_char,
                e.{cols['emt']['trip_plug']} AS trip_plug,
                f.{cols['frames']['frame_size']} AS frame_size,
                f.{cols['frames']['frame_desc']} AS frame_desc
            FROM tcc.emt_frames f
            INNER JOIN tcc.emt e ON f.{cols['frames']['emt_id']} = e.id
            LEFT JOIN tcc.manufacturers m ON m.id = e.{cols['emt']['manufacturer_id']}
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
            FROM tcc.emt_frame_amps
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
            FROM tcc.emt_sections s
            LEFT JOIN (
                SELECT {cols['bands']['section_id']} AS section_id, COUNT(*) AS band_count
                FROM tcc.emt_band_names
                GROUP BY {cols['bands']['section_id']}
            ) band_counts ON band_counts.section_id = s.id
            LEFT JOIN (
                SELECT {cols['pickups']['section_id']} AS section_id, COUNT(*) AS pickup_count
                FROM tcc.emt_pickups
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
            FROM tcc.emt_sections s
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
            FROM tcc.emt_pickups p
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
            FROM tcc.emt_band_names b
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
                FROM tcc.emt_curves
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
                m.mfr_name AS manufacturer_name,
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
            FROM tcc.emt_band_names b
            INNER JOIN tcc.emt_sections s ON b.{cols['bands']['section_id']} = s.id
            INNER JOIN tcc.emt_frames f ON s.{cols['sections']['frame_id']} = f.id
            INNER JOIN tcc.emt e ON f.{cols['frames']['emt_id']} = e.id
            LEFT JOIN tcc.manufacturers m ON m.id = e.{cols['emt']['manufacturer_id']}
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
            FROM tcc.emt_curves c
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
    plug_value: Optional[float] = Query(None, description="Optional compatible-plug lens"),
    breaker_class: Optional[str] = Query(None, description="Cross-half filter by breaker class"),
    breaker_id: Optional[int] = Query(None, description="Cross-half filter by breaker"),
    breaker_style_id: Optional[int] = Query(None, description="Cross-half filter by breaker style"),
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
    if breaker_class is not None and breaker_class not in _ETU_BREAKER_CASCADE_CLASSES:
        raise HTTPException(
            status_code=422,
            detail="breaker_class must be one of 'ICCB', 'MCCB', 'PCB'.",
        )

    filters = {
        "manufacturer_id": manufacturer_id,
        "trip_type_id": trip_type_id,
        "trip_style_id": trip_style_id,
        "sensor_id": sensor_id,
    }

    xh_clause, xh_params, xh_cte = _build_cross_half_breaker_filter(
        breaker_class,
        breaker_id,
        breaker_style_id,
    )
    plug_join, plug_params = _build_cascade_plug_join(plug_value, alias="v")

    def _apply_xh(where_sql: str) -> str:
        if not xh_clause:
            return where_sql
        if where_sql:
            return where_sql + xh_clause
        return "WHERE 1=1" + xh_clause

    full_where, full_params = _build_cascade_where(filters, prefix="v.")
    match_count = db.execute(
        text(
            f"""
            {xh_cte}
            SELECT COUNT(DISTINCT v.sensor_id)
            FROM vw_trip_unit_cascade v
            {plug_join}
            {_apply_xh(full_where)}
            """
        ),
        {**full_params, **plug_params, **xh_params},
    ).scalar() or 0

    manufacturer_where, manufacturer_params = _build_cascade_where(filters, {"manufacturer_id"}, prefix="v.")
    manufacturer_rows = db.execute(
        text(
            f"""
            {xh_cte}
            SELECT
                v.manufacturer_id AS manufacturer_id,
                v.manufacturer_name AS manufacturer_name,
                COUNT(DISTINCT v.trip_type_id) AS trip_type_count
            FROM vw_trip_unit_cascade v
            {plug_join}
            {_apply_xh(manufacturer_where)}
            GROUP BY v.manufacturer_id, v.manufacturer_name
            ORDER BY v.manufacturer_name
            """
        ),
        {**manufacturer_params, **plug_params, **xh_params},
    ).fetchall()

    trip_type_where, trip_type_params = _build_cascade_where(filters, {"trip_type_id"}, prefix="v.")
    trip_type_rows = db.execute(
        text(
            f"""
            {xh_cte}
            SELECT
                v.trip_type_id AS trip_type_id,
                v.trip_type_name AS trip_type_name,
                v.manufacturer_id AS manufacturer_id,
                v.manufacturer_name AS manufacturer_name,
                COUNT(DISTINCT v.trip_style_id) AS trip_style_count
            FROM vw_trip_unit_cascade v
            {plug_join}
            {_apply_xh(trip_type_where)}
            GROUP BY v.trip_type_id, v.trip_type_name,
                     v.manufacturer_id, v.manufacturer_name
            ORDER BY v.manufacturer_name, v.trip_type_name
            """
        ),
        {**trip_type_params, **plug_params, **xh_params},
    ).fetchall()

    trip_style_where, trip_style_params = _build_cascade_where(filters, {"trip_style_id"}, prefix="v.")
    trip_style_rows = db.execute(
        text(
            f"""
            {xh_cte}
            SELECT
                v.trip_style_id AS trip_style_id,
                v.trip_style_name AS trip_style_name,
                v.trip_type_id AS trip_type_id,
                v.trip_type_name AS trip_type_name,
                v.manufacturer_id AS manufacturer_id,
                v.manufacturer_name AS manufacturer_name,
                COUNT(DISTINCT v.sensor_id) AS sensor_count
            FROM vw_trip_unit_cascade v
            {plug_join}
            {_apply_xh(trip_style_where)}
            GROUP BY v.trip_style_id, v.trip_style_name,
                     v.trip_type_id, v.trip_type_name,
                     v.manufacturer_id, v.manufacturer_name
            ORDER BY v.manufacturer_name, v.trip_type_name, v.trip_style_name
            """
        ),
        {**trip_style_params, **plug_params, **xh_params},
    ).fetchall()

    plug_scope_where, plug_scope_params = _build_cascade_where(filters, prefix="v.")
    plug_rows = db.execute(
        text(
            f"""
            {xh_cte}
            SELECT
                p.value AS plug_value,
                COUNT(DISTINCT v.sensor_id) AS sensor_count
            FROM vw_trip_unit_cascade v
            JOIN tcc.etu_plugs p ON p.sensor_id = v.sensor_id
            {_apply_xh(plug_scope_where)}
            GROUP BY p.value
            ORDER BY p.value
            """
        ),
        {**plug_scope_params, **xh_params},
    ).fetchall()

    sensors: list[CascadeSensor] = []
    if trip_style_id is not None or sensor_id is not None:
        sensor_where, sensor_params = _build_cascade_where(filters, {"sensor_id"}, prefix="v.")
        sensor_rows = db.execute(
            text(
                f"""
                {xh_cte}
                SELECT DISTINCT
                    v.sensor_id AS sensor_id,
                    v.sensor_rating AS sensor_rating,
                    v.sensor_desc AS sensor_desc,
                    v.trip_style_id AS trip_style_id,
                    v.trip_style_name AS trip_style_name,
                    v.trip_type_id AS trip_type_id,
                    v.trip_type_name AS trip_type_name,
                    v.manufacturer_id AS manufacturer_id,
                    v.manufacturer_name AS manufacturer_name,
                    v.has_ltpu AS has_ltpu,
                    v.has_stpu AS has_stpu,
                    v.has_inst AS has_inst,
                    v.has_gfpu AS has_gfpu
                FROM vw_trip_unit_cascade v
                {plug_join}
                {_apply_xh(sensor_where)}
                ORDER BY v.sensor_rating NULLS LAST, v.sensor_desc
                """
            ),
            {**sensor_params, **plug_params, **xh_params},
        ).fetchall()
        sensors = [CascadeSensor(**dict(row._mapping)) for row in sensor_rows]

    return CascadeResponse(
        level=_cascade_level(filters),
        count=match_count,
        manufacturers=[CascadeManufacturer(**dict(row._mapping)) for row in manufacturer_rows],
        trip_types=[CascadeTripType(**dict(row._mapping)) for row in trip_type_rows],
        trip_styles=[CascadeTripStyle(**dict(row._mapping)) for row in trip_style_rows],
        sensors=sensors,
        plug_values=[CascadePlugOption(**dict(row._mapping)) for row in plug_rows],
    )


@router.get("/etu/search", response_model=EtuSearchResponse)
def search_etu(
    manufacturer_id: Optional[int] = Query(None, description="Optional manufacturer filter"),
    trip_type_id: Optional[int] = Query(None, description="Optional trip-type filter"),
    trip_style_id: Optional[int] = Query(None, description="Optional trip-style filter"),
    sensor_id: Optional[int] = Query(None, description="Optional sensor filter"),
    plug_value: Optional[float] = Query(None, description="Optional plug-compatibility filter"),
    q: Optional[str] = Query(None, description="Case-insensitive search within the current ETU scope"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of ETU matches to return"),
    db: Session = Depends(get_db),
):
    scope_filters = {
        "manufacturer_id": manufacturer_id,
        "trip_type_id": trip_type_id,
        "trip_style_id": trip_style_id,
        "sensor_id": sensor_id,
    }
    where_sql, params = _build_etu_search_where(scope_filters, q=q)
    plug_join, plug_params = _build_cascade_plug_join(plug_value, alias="v")
    rank_sql = _etu_search_rank_sql(q)
    order_sql = _etu_search_order_by()

    count = db.execute(
        text(
            f"""
            SELECT COUNT(DISTINCT v.sensor_id)
            FROM vw_trip_unit_cascade v
            {plug_join}
            {where_sql}
            """
        ),
        {**params, **plug_params},
    ).scalar() or 0

    rows = db.execute(
        text(
            f"""
            SELECT DISTINCT
                v.sensor_id AS sensor_id,
                v.sensor_rating AS sensor_rating,
                v.sensor_desc AS sensor_desc,
                v.trip_style_id AS trip_style_id,
                v.trip_style_name AS trip_style_name,
                v.trip_type_id AS trip_type_id,
                v.trip_type_name AS trip_type_name,
                v.manufacturer_id AS manufacturer_id,
                v.manufacturer_name AS manufacturer_name,
                {rank_sql} AS search_rank
            FROM vw_trip_unit_cascade v
            {plug_join}
            {where_sql}
            ORDER BY {order_sql}
            LIMIT :limit
            """
        ),
        {**params, **plug_params, "limit": limit},
    ).fetchall()

    sensor_ids = [int(row._mapping["sensor_id"]) for row in rows]
    plug_map = _load_etu_plug_value_map_sql(db, sensor_ids)

    return EtuSearchResponse(
        count=count,
        results=[
            EtuSearchResult(
                **{key: value for key, value in dict(row._mapping).items() if key != "search_rank"},
                compatible_plug_values=plug_map.get(int(row._mapping["sensor_id"]), []),
            )
            for row in rows
        ],
    )


@router.get("/etu/breaker-cascade", response_model=EtuBreakerCascadeResponse)
def get_etu_breaker_cascade(
    manufacturer_id: Optional[int] = Query(None, description="Optional manufacturer filter"),
    breaker_class: Optional[str] = Query(None, description="Optional breaker class: ICCB, MCCB, or PCB"),
    breaker_id: Optional[int] = Query(None, description="Optional breaker filter"),
    breaker_style_id: Optional[int] = Query(None, description="Optional breaker-style filter"),
    trip_type_id: Optional[int] = Query(None, description="Cross-half filter by trip type"),
    trip_style_id: Optional[int] = Query(None, description="Cross-half filter by trip style"),
    sensor_id: Optional[int] = Query(None, description="Cross-half filter by sensor"),
    db: Session = Depends(get_db),
):
    if breaker_class is not None and breaker_class not in _ETU_BREAKER_CASCADE_CLASSES:
        raise HTTPException(
            status_code=422,
            detail="breaker_class must be one of 'ICCB', 'MCCB', 'PCB'.",
        )

    scope: dict[str, Optional[object]] = {
        "manufacturer_id": manufacturer_id,
        "breaker_class": breaker_class,
        "breaker_id": breaker_id,
        "breaker_style_id": breaker_style_id,
    }

    xh_clause, xh_params = _build_cross_half_trip_unit_filter(
        trip_type_id,
        trip_style_id,
        sensor_id,
    )

    def _apply_xh(where_sql: str) -> str:
        if not xh_clause:
            return where_sql
        if where_sql:
            return where_sql + xh_clause
        return "WHERE 1=1" + xh_clause

    full_where, full_params = _build_etu_breaker_cascade_where(scope)
    count_value = db.execute(
        text(
            f"""
            {_ETU_BREAKER_CASCADE_CTE}
            SELECT COUNT(*)
            FROM etu_breaker_combined
            {_apply_xh(full_where)}
            """
        ),
        {**full_params, **xh_params},
    ).scalar() or 0

    manufacturer_where, manufacturer_params = _build_etu_breaker_cascade_where(scope, {"manufacturer_id"})
    manufacturer_rows = db.execute(
        text(
            f"""
            {_ETU_BREAKER_CASCADE_CTE}
            SELECT
                manufacturer_id,
                manufacturer_name,
                COUNT(DISTINCT breaker_id) AS breaker_count
            FROM etu_breaker_combined
            {_apply_xh(manufacturer_where)}
            GROUP BY manufacturer_id, manufacturer_name
            ORDER BY manufacturer_name
            """
        ),
        {**manufacturer_params, **xh_params},
    ).fetchall()

    class_where, class_params = _build_etu_breaker_cascade_where(scope, {"breaker_class"})
    class_rows = db.execute(
        text(
            f"""
            {_ETU_BREAKER_CASCADE_CTE}
            SELECT
                breaker_class,
                COUNT(DISTINCT breaker_id) AS breaker_count
            FROM etu_breaker_combined
            {_apply_xh(class_where)}
            GROUP BY breaker_class
            ORDER BY breaker_class
            """
        ),
        {**class_params, **xh_params},
    ).fetchall()

    breakers: list[EtuBreakerOption] = []
    if manufacturer_id is not None or breaker_class is not None or breaker_id is not None or breaker_style_id is not None:
        breaker_where, breaker_params = _build_etu_breaker_cascade_where(scope, {"breaker_id"})
        breaker_rows = db.execute(
            text(
                f"""
                {_ETU_BREAKER_CASCADE_CTE}
                SELECT
                    breaker_id,
                    breaker_name,
                    breaker_class,
                    manufacturer_id,
                    manufacturer_name,
                    COUNT(DISTINCT breaker_style_id) AS style_count
                FROM etu_breaker_combined
                {_apply_xh(breaker_where)}
                GROUP BY breaker_id, breaker_name, breaker_class,
                         manufacturer_id, manufacturer_name
                ORDER BY manufacturer_name, breaker_class, breaker_name
                """
            ),
            {**breaker_params, **xh_params},
        ).fetchall()
        breakers = [EtuBreakerOption(**dict(row._mapping)) for row in breaker_rows]

    breaker_styles: list[EtuBreakerStyleOption] = []
    if breaker_id is not None or breaker_style_id is not None:
        style_where, style_params = _build_etu_breaker_cascade_where(scope, {"breaker_style_id"})
        style_rows = db.execute(
            text(
                f"""
                {_ETU_BREAKER_CASCADE_CTE}
                SELECT DISTINCT
                    breaker_style_id,
                    breaker_style_name,
                    breaker_id,
                    breaker_name,
                    breaker_class,
                    manufacturer_id,
                    manufacturer_name
                FROM etu_breaker_combined
                {_apply_xh(style_where)}
                ORDER BY manufacturer_name, breaker_class, breaker_name, breaker_style_name
                """
            ),
            {**style_params, **xh_params},
        ).fetchall()
        breaker_styles = [EtuBreakerStyleOption(**dict(row._mapping)) for row in style_rows]

    return EtuBreakerCascadeResponse(
        level=_etu_breaker_cascade_level(scope),
        count=int(count_value),
        scope={
            "manufacturer_id": manufacturer_id,
            "breaker_class": breaker_class,
            "breaker_id": breaker_id,
            "breaker_style_id": breaker_style_id,
            "trip_type_id": trip_type_id,
            "trip_style_id": trip_style_id,
            "sensor_id": sensor_id,
        },
        manufacturers=[EtuBreakerManufacturer(**dict(row._mapping)) for row in manufacturer_rows],
        breaker_classes=[EtuBreakerClassOption(**dict(row._mapping)) for row in class_rows],
        breakers=breakers,
        breaker_styles=breaker_styles,
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

    Read directly from the active ETU tables and expand the persisted boundary
    rows into full UI-facing option sets. The SQL helper function can now be
    repaired independently, but the route keeps its direct-table contract so the
    UI receives the same expanded option inventory the app validates locally.
    """
    data = _load_direct_available_settings(db, sensor_id)
    if not any(data.get(key) for key in (
        "plug_values",
        "ltpu_settings",
        "ltd_settings",
        "ltd_multipliers",
        "stpu_settings",
        "inst_settings",
        "gfpu_settings",
    )):
        raise HTTPException(
            status_code=404,
            detail=f"No settings found for sensor {sensor_id}",
        )

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

    std_settings = _load_delay_band_settings(db, "tcc.etu_std_bands", sensor_id)
    gfd_settings = _load_delay_band_settings(db, "tcc.etu_gfd_bands", sensor_id)

    # The direct ETU loader returns pickup arrays plus LTD settings. STD/GFD band
    # rows are loaded separately here so the UI can use strict per-sensor delay
    # options without relying on stale RPC wiring.
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

@router.get("/tmt/facets", response_model=TMTFacetsResponse)
def get_tmt_facets(
    breaker_class: Optional[str] = Query(None, description="Filter by ICCB, MCCB, or PCB"),
    manufacturer_id: Optional[int] = Query(None, description="Filter by manufacturer id"),
    breaker_id: Optional[int] = Query(None, description="Filter by breaker id"),
    breaker_style_id: Optional[int] = Query(None, description="Filter by breaker style id"),
    frame_size: Optional[str] = Query(None, description="Filter by exact TMT frame size"),
    amp_rating: Optional[float] = Query(None, description="Filter by exact supported amp rating"),
    db: Session = Depends(get_db),
):
    """Return cross-filtered TMT facet values for the current selection state."""
    class_filter = breaker_class.upper() if breaker_class else None
    if class_filter is not None and class_filter not in _TMT_STYLE_MODELS:
        raise HTTPException(status_code=400, detail="breaker_class must be one of ICCB, MCCB, or PCB")

    return TMTFacetsResponse(
        **_load_tmt_facets(
            db,
            {
                "breaker_class": class_filter,
                "manufacturer_id": manufacturer_id,
                "breaker_id": breaker_id,
                "breaker_style_id": breaker_style_id,
                "frame_size": frame_size,
                "amp_rating": amp_rating,
            },
        )
    )

@router.get("/tmt/frames", response_model=TMTFrameSearchResponse)
def search_tmt_frames(
    breaker_class: Optional[str] = Query(None, description="Filter by ICCB, MCCB, or PCB"),
    manufacturer_id: Optional[int] = Query(None, description="Filter by manufacturer id"),
    breaker_id: Optional[int] = Query(None, description="Filter by breaker id"),
    breaker_style_id: Optional[int] = Query(None, description="Filter by breaker style id"),
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
        breaker_model = style_model.breaker.property.mapper.class_
        query = (
            db.query(TMTFrame)
            .filter(func.upper(TMTFrame.breaker_class) == class_key)
            .join(style_model, style_model.id == TMTFrame.breaker_style_id)
            .join(breaker_model, breaker_model.id == style_model.breaker_id)
            .join(Manufacturer, Manufacturer.id == breaker_model.manufacturer_id)
        )

        if frame_size:
            query = query.filter(TMTFrame.size.ilike(f"%{frame_size}%"))
        if manufacturer_id is not None:
            query = query.filter(breaker_model.manufacturer_id == manufacturer_id)
        if breaker_id is not None:
            query = query.filter(breaker_model.id == breaker_id)
        if breaker_style_id is not None:
            query = query.filter(TMTFrame.breaker_style_id == breaker_style_id)
        if manufacturer_name:
            query = query.filter(Manufacturer.name.ilike(f"%{manufacturer_name}%"))
        if breaker_name:
            query = query.filter(breaker_model.name.ilike(f"%{breaker_name}%"))
        if breaker_style_name:
            query = query.filter(style_model.frame.ilike(f"%{breaker_style_name}%"))

        order_by = []
        if manufacturer_name:
            normalized_manufacturer_name = manufacturer_name.lower()
            order_by.append(
                case(
                    (func.lower(Manufacturer.name) == normalized_manufacturer_name, 0),
                    (Manufacturer.name.ilike(f"{manufacturer_name}%"), 1),
                    else_=2,
                )
            )

        candidate_rows = query.order_by(*order_by, TMTFrame.id).limit(limit * 4).all()
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

@router.get("/emt/facets", response_model=EMTFacetsResponse)
def get_emt_facets(
    manufacturer_id: Optional[int] = Query(None, description="Filter by manufacturer id"),
    trip_char: Optional[int] = Query(None, description="Filter by EMT TripChar value"),
    trip_plug: Optional[int] = Query(None, description="Filter by EMT TripPlug value"),
    frame_desc: Optional[str] = Query(None, description="Filter by exact EMT frame description"),
    type_name: Optional[str] = Query(None, description="Filter by exact EMT type name"),
    db: Session = Depends(get_db),
):
    """Return cross-filtered EMT facet values for the current selection state."""
    return EMTFacetsResponse(
        **_load_emt_facets(
            db,
            {
                "manufacturer_id": manufacturer_id,
                "trip_char": trip_char,
                "trip_plug": trip_plug,
                "frame_desc": frame_desc,
                "type_name": type_name,
            },
        )
    )

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
# GET /relay/sections — Relay Section Search
# ──────────────────────────────────────────────

@router.get("/relay/sections", response_model=RelaySectionSearchResponse)
def search_relay_sections(
    relay_type: Optional[str] = Query(None, description="Filter by relay type"),
    device_function: Optional[str] = Query(None, description="Filter by source device function"),
    family_code: Optional[int] = Query(None, description="Filter by relay family / model code"),
    q: Optional[str] = Query(None, description="Free-text match against relay type, device function, or TD-section name"),
    supported_only: bool = Query(False, description="Limit results to supported preview families only"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of matching relay sections"),
    db: Session = Depends(get_db),
):
    _ensure_relay_catalog_available(db)
    sections = _search_relay_sections(
        db,
        relay_type=relay_type,
        device_function=device_function,
        family_code=family_code,
        q=q,
        supported_only=supported_only,
        limit=limit,
    )
    return RelaySectionSearchResponse(
        count=len(sections),
        sections=[RelaySectionSearchResult(**section) for section in sections],
    )


# ──────────────────────────────────────────────
# GET /relay/context/{td_section_source_id} — Relay Section Context
# ──────────────────────────────────────────────

@router.get("/relay/context/{td_section_source_id}", response_model=RelayContext)
def get_relay_context(td_section_source_id: int, db: Session = Depends(get_db)):
    _ensure_relay_catalog_available(db)
    bundle = _load_relay_context_bundle(db, td_section_source_id)
    return RelayContext(
        manufacturer_source_id=int(bundle["manufacturer_source_id"]),
        relay_type=bundle.get("relay_type"),
        relay_device_source_id=int(bundle["relay_device_source_id"]),
        device_function=bundle.get("device_function"),
        device_ordinal=int(bundle["device_ordinal"]),
        standard_code=bundle.get("standard_code"),
        dftype_code=bundle.get("dftype_code"),
        voltage_restraint_kind=bundle.get("voltage_restraint_kind"),
        td_section_source_id=int(bundle["td_section_source_id"]),
        td_section_name=bundle.get("td_section_name"),
        family_code=int(bundle["family_code"]),
        family_name=str(bundle["family_name"]),
        storage_kind=str(bundle["storage_kind"]),
        supported=bool(bundle["supported"]),
        unsupported_reason=bundle.get("unsupported_reason"),
        line_section_count=int(bundle["line_section_count"]),
        range_count=int(bundle["range_count"]),
        curve_parent_count=int(bundle["curve_parent_count"]),
        preview_option_count=int(bundle["preview_option_count"]),
        line_sections=[RelayLineSectionSummary(**section) for section in bundle["line_sections"]],
        resolved_equipment=bundle.get("resolved_equipment"),
    )


# ──────────────────────────────────────────────
# GET /relay/settings/{td_section_source_id} — Relay Settings Surface
# ──────────────────────────────────────────────

@router.get("/relay/settings/{td_section_source_id}", response_model=RelaySettingsResponse)
def get_relay_settings(td_section_source_id: int, db: Session = Depends(get_db)):
    _ensure_relay_catalog_available(db)
    bundle = _load_relay_settings_bundle(db, td_section_source_id)
    return RelaySettingsResponse(
        td_section_source_id=int(bundle["td_section_source_id"]),
        family_code=int(bundle["family_code"]),
        family_name=str(bundle["family_name"]),
        storage_kind=str(bundle["storage_kind"]),
        supported=bool(bundle["supported"]),
        unsupported_reason=bundle.get("unsupported_reason"),
        line_sections=[RelayLineSectionSummary(**section) for section in bundle["line_sections"]],
        ranges=[
            RelayRangeOption(
                **{
                    **range_row,
                    "discrete_values": [RelayRangeDiscreteValue(**item) for item in range_row["discrete_values"]],
                }
            )
            for range_row in bundle["ranges"]
        ],
        curve_parents=[RelayCurveParentOption(**parent) for parent in bundle["curve_parents"]],
        preview_options=[RelayPreviewOption(**option) for option in bundle["preview_options"]],
    )


# ──────────────────────────────────────────────
# POST /relay/plot-tcc — Relay Preview Contract
# ──────────────────────────────────────────────

@router.post("/relay/plot-tcc", response_model=RelayPlotResponse)
def plot_relay_tcc(req: RelayPlotRequest, db: Session = Depends(get_db)):
    _ensure_relay_catalog_available(db)
    preview_bundle = _load_relay_preview_bundle(
        db,
        td_section_source_id=req.td_section_source_id,
        curve_parent_source_id=req.curve_parent_source_id,
        curve_ordinal=req.curve_ordinal,
        source_ordinal=req.source_ordinal,
        time_dial=req.time_dial,
        current_multiples=req.current_multiples,
        candidate_overrides=req.candidate_overrides,
    )

    meta = RelayPlotMeta(
        td_section_source_id=int(preview_bundle["td_section_source_id"]),
        relay_device_source_id=int(preview_bundle["relay_device_source_id"]),
        manufacturer_source_id=int(preview_bundle["manufacturer_source_id"]),
        relay_type=preview_bundle.get("relay_type"),
        device_function=preview_bundle.get("device_function"),
        td_section_name=preview_bundle.get("td_section_name"),
        family_code=int(preview_bundle["family_code"]),
        family_name=str(preview_bundle["family_name"]),
        storage_kind=str(preview_bundle["storage_kind"]),
        supported=bool(preview_bundle["supported"]),
        status=str(preview_bundle["status"]),
        unsupported_reason=preview_bundle.get("unsupported_reason"),
        selected_curve_parent_source_id=(
            int(preview_bundle["selected_option"]["curve_parent_source_id"])
            if preview_bundle.get("selected_option") is not None
            else None
        ),
        selected_curve_name=(preview_bundle["selected_option"].get("curve_name") if preview_bundle.get("selected_option") else None),
        selected_curve_ordinal=(
            int(preview_bundle["selected_option"]["curve_ordinal"])
            if preview_bundle.get("selected_option") and preview_bundle["selected_option"].get("curve_ordinal") is not None
            else None
        ),
        selected_source_ordinal=(
            int(preview_bundle["selected_option"]["source_ordinal"])
            if preview_bundle.get("selected_option") and preview_bundle["selected_option"].get("source_ordinal") is not None
            else None
        ),
        selected_time_dial=(preview_bundle["selected_option"].get("time_dial") if preview_bundle.get("selected_option") else None),
        selected_td_desc=(preview_bundle["selected_option"].get("td_desc") if preview_bundle.get("selected_option") else None),
        candidate_applied=bool(preview_bundle.get("candidate_values")),
        candidate_pickup_multiplier=preview_bundle.get("candidate_values", {}).get("pickup_multiplier"),
        candidate_time_dial=preview_bundle.get("candidate_values", {}).get("time_dial"),
        candidate_voltage_threshold_multiplier=preview_bundle.get("candidate_values", {}).get("voltage_threshold_multiplier"),
        plot_disclaimer=(
            "Read-only relay preview. Stored analytical constants or normalized TCP points are evaluated through the shared calc package; candidate overrides are ephemeral and no write path is opened."
        ),
        resolved_equipment=preview_bundle.get("resolved_equipment"),
    )

    result = preview_bundle.get("result")
    if result is None:
        return RelayPlotResponse(
            meta=meta,
            warnings=list(preview_bundle["warnings"]),
            curves=[],
        )

    selected_option = preview_bundle["selected_option"]
    requested_current_multiples = preview_bundle.get("requested_current_multiples") or [
        point.current_multiple for point in result.points
    ]
    curve = RelayPlotCurve(
        id=(
            f"relay_{preview_bundle['family_name']}_{selected_option['curve_parent_source_id']}_"
            f"{selected_option.get('curve_ordinal') or selected_option.get('source_ordinal') or 'default'}"
        ),
        family_name=str(preview_bundle["family_name"]),
        storage_kind=str(preview_bundle["storage_kind"]),
        curve_name=result.curve_name,
        curve_parent_source_id=int(selected_option["curve_parent_source_id"]),
        curve_ordinal=(
            int(selected_option["curve_ordinal"])
            if selected_option.get("curve_ordinal") is not None
            else None
        ),
        source_ordinal=(
            int(selected_option["source_ordinal"])
            if selected_option.get("source_ordinal") is not None
            else None
        ),
        time_dial=selected_option.get("time_dial") if selected_option.get("time_dial") is not None else result.time_dial,
        td_desc=selected_option.get("td_desc"),
        points=[
            RelayPlotCurvePoint(
                current_multiple=float(requested_current_multiples[index]),
                seconds=point.trip_time_seconds,
                evaluated_current_multiple=(
                    point.current_multiple
                    if not _float_matches(
                        point.current_multiple,
                        float(requested_current_multiples[index]),
                    )
                    else None
                ),
            )
            for index, point in enumerate(result.points)
        ],
    )

    return RelayPlotResponse(
        meta=meta,
        warnings=list(preview_bundle["warnings"]),
        curves=[curve],
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
            test_multiple=elem.get("test_multiplier", default_mult),
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

        Reuses the authoritative pickup calculations from /calculate and performs
        pickup pass/fail comparison in-process. That keeps the route aligned with
        the delay-aware API contract even when the live SQL evaluation helper is
        repaired or revised on its own cadence.
    """
    _enforce_plug_within_sensor_rating(req.sensor_id, req.plug_rating, db)

    # Extract individual measured values from measurements list
    measured = {m.element.upper(): m for m in req.measurements}

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
    if calc_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Calculation failed for sensor {req.sensor_id}",
        )

    data = _build_python_pickup_eval_data(calc_data, measured)

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
                test_multiple=calc_elem.get("test_multiplier", default_mult),
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
                deviation_pct = _round_deviation_pct(measured_time, expected_time)

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
            - Measured result markers from in-process pickup evaluation
            - Companion summary table for the numeric sidebar

        This endpoint reuses the existing NETA calculate SQL function for marker
        data and the calc engine services for curve generation, while evaluating
        measured pickup results in-process so the plot response stays aligned
        with the route-owned marker and summary contract.
    """

    _enforce_plug_within_sensor_rating(req.sensor_id, req.plug_rating, db)

    warnings: list[str] = []
    ltd_delay_setting, ltd_test_multiple, ltd_curve_setting = _resolve_plot_delay_inputs(
        db=db,
        sensor_id=req.sensor_id,
        element_key="ltd",
        legacy_setting=req.ltd_setting,
        delay_setting=req.ltd_delay_setting,
        test_multiple=req.ltd_test_multiple,
        default_test_multiple=3.0,
    )
    std_delay_setting, std_test_multiple, std_curve_setting = _resolve_plot_delay_inputs(
        db=db,
        sensor_id=req.sensor_id,
        element_key="std",
        legacy_setting=req.std_setting,
        delay_setting=req.std_delay_setting,
        test_multiple=req.std_test_multiple,
        default_test_multiple=1.5,
    )
    gfd_delay_setting, gfd_test_multiple, gfd_curve_setting = _resolve_plot_delay_inputs(
        db=db,
        sensor_id=req.sensor_id,
        element_key="gfd",
        legacy_setting=req.gfd_setting,
        delay_setting=req.gfd_delay_setting,
        test_multiple=req.gfd_test_multiple,
        default_test_multiple=1.5,
    )

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
            "p_ltd_setting": ltd_test_multiple,
            "p_stpu_setting": req.stpu_setting,
            "p_std_setting": std_test_multiple,
            "p_inst_setting": req.inst_setting,
            "p_gfpu_setting": req.gfpu_setting,
            "p_gfd_setting": gfd_test_multiple,
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
        eval_data = _build_python_pickup_eval_data(calc_data, meas_map)
        overall_pass = eval_data.get("overall_pass")
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
        delay_setting = {
            "ltd": ltd_delay_setting,
            "std": std_delay_setting,
            "gfd": gfd_delay_setting,
        }[key]
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
            setting=delay_setting,
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
            ltd_setting=ltd_curve_setting,
            stpu_setting=req.stpu_setting,
            std_setting=std_curve_setting,
            inst_setting=req.inst_setting,
            gfpu_setting=req.gfpu_setting,
            gfd_setting=gfd_curve_setting,
            multiplier_value=req.multiplier_value,
            c_factor=req.c_factor,
        )
        warnings.extend(curve_warnings)

        for marker in expected_markers:
            if marker.kind != "delay" or marker.expected_time is not None:
                continue
            delay_setting = {
                "LTD": ltd_delay_setting,
                "STD": std_delay_setting,
                "GFD": gfd_delay_setting,
            }.get(marker.element)
            delay_test_multiple = {
                "LTD": ltd_test_multiple,
                "STD": std_test_multiple,
                "GFD": gfd_test_multiple,
            }.get(marker.element)
            expected_time, time_low, time_high, _timing_source = _authoritative_delay_surface(
                db=db,
                sensor_id=req.sensor_id,
                element_key=marker.element.lower(),
                setting=delay_setting,
                test_multiple=delay_test_multiple,
                curves=curves,
                expected_current=marker.expected_current,
                maint_mode=maint_mode,
                maint_profile=maint_profile,
                use_ltd_reference_window=True,
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
                        tr.deviation_pct = _round_deviation_pct(measurement.measured_time, tr.expected_time)
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
