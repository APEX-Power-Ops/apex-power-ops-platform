"""
FastAPI router for NETA Demo Plan & Result Persistence.

Endpoints:
  POST /api/v1/neta/plans              — Save a named demo plan
  GET  /api/v1/neta/plans              — List saved demo plans
  GET  /api/v1/neta/plans/{plan_id}    — Load a saved demo plan
  POST /api/v1/neta/plans/{plan_id}/results — Save a result artifact

Contract notes:
  The demo stores plans as structured settings snapshots rather than
  FK references to individual pickup/band rows.  This is intentional:
  the demo works with setting *values* (e.g., ltpu_setting=0.8) while
  the production-path schema uses FK IDs to specific pickup rows.

  The persistence layer uses dedicated JSONB columns on tcc_test_plans:
    - settings_snapshot: structured dial settings
    - display_snapshot: cascade display names + measurements
  This is a narrow, documented addition to the existing table —
  not an opaque blob.  The structure is:

    {
      "plug_rating": 800,
      "ltpu_setting": 0.8,
      "ltd_setting": 6,
      "stpu_setting": 4.0,
      "std_setting": 1.0,
      "inst_setting": 10.0,
      "gfpu_setting": 0.4,
      "gfd_setting": 1.0,
      "maint_mode": false
    }

  Future slices can resolve setting values to FK IDs for the
  production path once the full calc engine is backend-driven.

  Note on IDs:
    The live Supabase schema uses UUID primary keys on tcc_test_plans
    and tcc_test_results.  All id fields in the API contract are strings
    to accommodate this.  The INSERT relies on Supabase's default
    gen_random_uuid() for id generation.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from config import get_db
from services.auth import AuthenticatedUser, get_current_user
from services.neta.schemas import ResolvedEquipmentSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/neta/plans", tags=["neta-plans"])


# ── Pydantic Contracts ──


class PlanSettings(BaseModel):
    """The dial settings that define a demo scenario."""
    plug_rating: float
    ltpu_setting: Optional[float] = None
    ltd_setting: Optional[float] = None
    stpu_setting: Optional[float] = None
    std_setting: Optional[float] = None
    inst_setting: Optional[float] = None
    gfpu_setting: Optional[float] = None
    gfd_setting: Optional[float] = None
    maint_mode: bool = False


class PlanMeasurements(BaseModel):
    """Optional measured values to save with the plan."""
    ltpu: Optional[float] = None
    ltd: Optional[float] = None
    stpu: Optional[float] = None
    std: Optional[float] = None
    inst: Optional[float] = None
    gfpu: Optional[float] = None
    gfd: Optional[float] = None


class PlanCascadeState(BaseModel):
    """The saved family-aware cascade path required for honest restore behavior."""
    family: str = "etu"
    manufacturer_id: Optional[int] = None
    trip_type_id: Optional[int] = None
    trip_style_id: Optional[int] = None
    sensor_id: Optional[int] = None
    resolved_id: Optional[str] = None


class SavePlanRequest(BaseModel):
    """Request body for saving a named demo plan."""
    family: Literal["etu"] = "etu"
    name: str = Field(..., min_length=1, max_length=200)
    sensor_id: int
    manufacturer_id: Optional[int] = None
    manufacturer_name: Optional[str] = None
    trip_type_id: Optional[int] = None
    trip_type_name: Optional[str] = None
    trip_style_id: Optional[int] = None
    trip_style_name: Optional[str] = None
    breaker_context_label: Optional[str] = None
    breaker_context_source: Optional[str] = None
    sensor_desc: Optional[str] = None
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None
    settings: PlanSettings
    measurements: Optional[PlanMeasurements] = None


class PlanSummary(BaseModel):
    """Compact plan metadata for list views."""
    id: str
    family: str = "etu"
    name: str
    sensor_id: int
    cascade_state: Optional[PlanCascadeState] = None
    breaker_context_label: Optional[str] = None
    sensor_desc: Optional[str] = None
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None
    maint_mode: bool = False
    created_at: str
    updated_at: Optional[str] = None


class PlanDetail(BaseModel):
    """Full plan detail for loading back into the demo."""
    id: str
    family: str = "etu"
    name: str
    sensor_id: int
    cascade_state: Optional[PlanCascadeState] = None
    manufacturer_id: Optional[int] = None
    manufacturer_name: Optional[str] = None
    trip_type_id: Optional[int] = None
    trip_type_name: Optional[str] = None
    trip_style_id: Optional[int] = None
    trip_style_name: Optional[str] = None
    breaker_context_label: Optional[str] = None
    breaker_context_source: Optional[str] = None
    sensor_desc: Optional[str] = None
    resolved_equipment: Optional[ResolvedEquipmentSummary] = None
    settings: PlanSettings
    measurements: Optional[PlanMeasurements] = None
    result_count: int = 0
    created_at: str
    updated_at: Optional[str] = None


class ElementResultSummary(BaseModel):
    """Per-element result summary for persistence."""
    element: str
    test_current: Optional[float] = None
    measured_current: Optional[float] = None
    limit_low: Optional[float] = None
    limit_high: Optional[float] = None
    passed: Optional[bool] = None
    deviation_pct: Optional[float] = None


class SaveResultRequest(BaseModel):
    """Request body for saving a result artifact from a demo run."""
    overall_pass: Optional[bool] = None
    tested_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    maint_mode: bool = False
    elements: List[ElementResultSummary] = []
    warnings: List[str] = []
    notes: Optional[str] = None


class SavedResult(BaseModel):
    """Confirmation of a saved result."""
    id: str
    plan_id: str
    overall_pass: Optional[bool] = None
    tested_count: int = 0
    created_at: str


def _build_fallback_etu_resolved_equipment(req: SavePlanRequest) -> ResolvedEquipmentSummary:
    trip_unit_label = " · ".join(
        [part for part in [req.manufacturer_name, req.trip_type_name, req.trip_style_name] if part]
    ) or None
    rating_label = f"Sensor {req.sensor_desc}" if req.sensor_desc else None
    return ResolvedEquipmentSummary(
        family=req.family,
        family_label=req.family.upper(),
        resolved_id=f"sensor:{req.sensor_id}",
        primary_label=trip_unit_label or rating_label,
        secondary_label=req.breaker_context_label or rating_label,
        breaker_context={
            "label": req.breaker_context_label,
            "source": req.breaker_context_source,
            "manufacturer_name": req.manufacturer_name,
            "breaker_style_name": req.trip_style_name,
        },
        trip_unit={
            "manufacturer_name": req.manufacturer_name,
            "trip_type_name": req.trip_type_name,
            "trip_style_name": req.trip_style_name,
            "label": trip_unit_label,
        },
        rating_context={
            "label": rating_label,
            "sensor_id": req.sensor_id,
            "sensor_desc": req.sensor_desc,
        },
    )


def _parse_resolved_equipment(display: dict[str, Any], sensor_id: int, family: str) -> Optional[ResolvedEquipmentSummary]:
    resolved = display.get("resolved_equipment") if isinstance(display, dict) else None
    if isinstance(resolved, dict):
        return ResolvedEquipmentSummary(**resolved)
    if family != "etu":
        return None
    req_like = SavePlanRequest(
        family=family,
        name="fallback",
        sensor_id=sensor_id,
        manufacturer_id=display.get("manufacturer_id"),
        manufacturer_name=display.get("manufacturer_name"),
        trip_type_id=display.get("trip_type_id"),
        trip_type_name=display.get("trip_type_name"),
        trip_style_id=display.get("trip_style_id"),
        trip_style_name=display.get("trip_style_name"),
        breaker_context_label=display.get("breaker_context_label"),
        breaker_context_source=display.get("breaker_context_source"),
        sensor_desc=display.get("sensor_desc"),
        settings=PlanSettings(plug_rating=0),
        measurements=None,
    )
    return _build_fallback_etu_resolved_equipment(req_like)


def _build_cascade_state(display: dict[str, Any], sensor_id: int, family: str) -> PlanCascadeState:
    cascade = display.get("cascade_state") if isinstance(display, dict) else None
    if isinstance(cascade, dict):
        cascade_payload = dict(cascade)
        cascade_payload.setdefault("family", family)
        cascade_payload.setdefault("sensor_id", sensor_id)
        if not cascade_payload.get("resolved_id"):
            resolved = _parse_resolved_equipment(display, sensor_id, family)
            cascade_payload["resolved_id"] = resolved.resolved_id if resolved else None
        return PlanCascadeState(**cascade_payload)

    resolved = _parse_resolved_equipment(display, sensor_id, family)
    return PlanCascadeState(
        family=family,
        manufacturer_id=display.get("manufacturer_id") if isinstance(display, dict) else None,
        trip_type_id=display.get("trip_type_id") if isinstance(display, dict) else None,
        trip_style_id=display.get("trip_style_id") if isinstance(display, dict) else None,
        sensor_id=sensor_id,
        resolved_id=resolved.resolved_id if resolved else None,
    )


# ── Routes ──


@router.post("", response_model=PlanDetail, status_code=201)
def save_plan(
    req: SavePlanRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a named demo plan.

    Stores the plan name, sensor reference, and a structured settings
    snapshot.  The snapshot preserves the exact dial values the operator
    selected so the plan can be reloaded without re-deriving from FKs.
    """
    settings_json = req.settings.model_dump()
    measurements_json = req.measurements.model_dump() if req.measurements else None
    resolved_equipment = req.resolved_equipment or _build_fallback_etu_resolved_equipment(req)
    cascade_state = PlanCascadeState(
        family=req.family,
        manufacturer_id=req.manufacturer_id,
        trip_type_id=req.trip_type_id,
        trip_style_id=req.trip_style_id,
        sensor_id=req.sensor_id,
        resolved_id=resolved_equipment.resolved_id,
    )
    display_json = {
        "family": req.family,
        "cascade_state": cascade_state.model_dump(mode="json"),
        "manufacturer_id": req.manufacturer_id,
        "manufacturer_name": req.manufacturer_name,
        "trip_type_id": req.trip_type_id,
        "trip_type_name": req.trip_type_name,
        "trip_style_id": req.trip_style_id,
        "trip_style_name": req.trip_style_name,
        "breaker_context_label": req.breaker_context_label,
        "breaker_context_source": req.breaker_context_source,
        "sensor_desc": req.sensor_desc,
        "resolved_equipment": resolved_equipment.model_dump(mode="json"),
    }

    try:
        row = db.execute(
            text("""
                INSERT INTO tcc_test_plans
                    (user_id, name, sensor_id, project, settings_snapshot, display_snapshot)
                VALUES
                    (CAST(:user_id AS uuid), :name, :sensor_id, :project,
                     CAST(:settings_snapshot AS jsonb), CAST(:display_snapshot AS jsonb))
                RETURNING id, created_at, updated_at
            """),
            {
                "user_id": str(current_user.user_id),
                "name": req.name,
                "sensor_id": req.sensor_id,
                "project": "neta-demo",
                "settings_snapshot": json.dumps(settings_json),
                "display_snapshot": json.dumps({
                    "display": display_json,
                    "measurements": measurements_json,
                }),
            },
        ).fetchone()
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Failed to save plan: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"Plan save failed — database may be unreachable: {exc}",
        )

    return PlanDetail(
        id=str(row[0]),
        family=req.family,
        name=req.name,
        sensor_id=req.sensor_id,
        cascade_state=cascade_state,
        manufacturer_id=req.manufacturer_id,
        manufacturer_name=req.manufacturer_name,
        trip_type_id=req.trip_type_id,
        trip_type_name=req.trip_type_name,
        trip_style_id=req.trip_style_id,
        trip_style_name=req.trip_style_name,
        breaker_context_label=req.breaker_context_label,
        breaker_context_source=req.breaker_context_source,
        sensor_desc=req.sensor_desc,
        resolved_equipment=resolved_equipment,
        settings=req.settings,
        measurements=req.measurements,
        result_count=0,
        created_at=str(row[1]),
        updated_at=str(row[2]) if row[2] else None,
    )


@router.get("", response_model=List[PlanSummary])
def list_plans(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List saved demo plans, newest first."""
    try:
        rows = db.execute(
            text("""
                SELECT id, name, sensor_id, settings_snapshot,
                       display_snapshot, created_at, updated_at
                FROM tcc_test_plans
                WHERE project = 'neta-demo'
                  AND user_id = CAST(:user_id AS uuid)
                ORDER BY created_at DESC
            """),
            {"user_id": str(current_user.user_id)},
        ).fetchall()
    except Exception as exc:
        logger.warning("Failed to list plans: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"Plan list failed — database may be unreachable: {exc}",
        )

    result = []
    for r in rows:
        settings = _parse_jsonb(r[3])
        display = _parse_jsonb(r[4])
        disp_meta = display.get("display", {}) if isinstance(display, dict) else {}
        family = disp_meta.get("family", "etu")
        result.append(PlanSummary(
            id=str(r[0]),
            family=family,
            name=r[1],
            sensor_id=r[2],
            cascade_state=_build_cascade_state(disp_meta, r[2], family),
            breaker_context_label=disp_meta.get("breaker_context_label"),
            sensor_desc=disp_meta.get("sensor_desc"),
            resolved_equipment=_parse_resolved_equipment(disp_meta, r[2], family),
            maint_mode=settings.get("maint_mode", False),
            created_at=str(r[5]),
            updated_at=str(r[6]) if r[6] else None,
        ))
    return result


@router.get("/{plan_id}", response_model=PlanDetail)
def load_plan(
    plan_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Load a saved demo plan by ID (UUID string)."""
    try:
        row = db.execute(
            text("""
                SELECT id, name, sensor_id, settings_snapshot,
                       display_snapshot, created_at, updated_at
                FROM tcc_test_plans
                WHERE id = CAST(:pid AS uuid)
                  AND project = 'neta-demo'
                  AND user_id = CAST(:user_id AS uuid)
            """),
            {"pid": plan_id, "user_id": str(current_user.user_id)},
        ).fetchone()
    except Exception as exc:
        logger.warning("Failed to load plan %s: %s", plan_id, exc)
        raise HTTPException(
            status_code=503,
            detail=f"Plan load failed — database may be unreachable: {exc}",
        )

    if not row:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

    settings = _parse_jsonb(row[3])
    extra = _parse_jsonb(row[4])
    display = extra.get("display", {}) if isinstance(extra, dict) else {}
    measurements = extra.get("measurements") if isinstance(extra, dict) else None
    family = display.get("family", "etu")

    # Count results for this plan
    try:
        count_row = db.execute(
                        text("""
                                SELECT COUNT(*)
                                FROM tcc_test_results r
                                WHERE r.plan_id = CAST(:pid AS uuid)
                                    AND EXISTS (
                                            SELECT 1
                                            FROM tcc_test_plans p
                                            WHERE p.id = r.plan_id
                                                AND p.user_id = CAST(:user_id AS uuid)
                                    )
                        """),
                        {"pid": plan_id, "user_id": str(current_user.user_id)},
        ).fetchone()
        result_count = count_row[0] if count_row else 0
    except Exception:
        result_count = 0

    return PlanDetail(
        id=str(row[0]),
        family=family,
        name=row[1],
        sensor_id=row[2],
        cascade_state=_build_cascade_state(display, row[2], family),
        manufacturer_id=display.get("manufacturer_id"),
        manufacturer_name=display.get("manufacturer_name"),
        trip_type_id=display.get("trip_type_id"),
        trip_type_name=display.get("trip_type_name"),
        trip_style_id=display.get("trip_style_id"),
        trip_style_name=display.get("trip_style_name"),
        breaker_context_label=display.get("breaker_context_label"),
        breaker_context_source=display.get("breaker_context_source"),
        sensor_desc=display.get("sensor_desc"),
        resolved_equipment=_parse_resolved_equipment(display, row[2], family),
        settings=PlanSettings(**settings),
        measurements=PlanMeasurements(**measurements) if measurements else None,
        result_count=result_count,
        created_at=str(row[5]),
        updated_at=str(row[6]) if row[6] else None,
    )


@router.post("/{plan_id}/results", response_model=SavedResult, status_code=201)
def save_result(
    plan_id: str,
    req: SaveResultRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a result artifact from a demo run.

    Each element in the evaluate response becomes a row in tcc_test_results.
    The overall summary (pass/fail, warnings) is stored in the first row's
    notes field as structured JSON for auditability.
    """
    # Verify the plan exists
    try:
        plan_row = db.execute(
            text("""
                SELECT id
                FROM tcc_test_plans
                WHERE id = CAST(:pid AS uuid)
                  AND project = 'neta-demo'
                  AND user_id = CAST(:user_id AS uuid)
            """),
            {"pid": plan_id, "user_id": str(current_user.user_id)},
        ).fetchone()
    except Exception as exc:
        logger.warning("Failed to verify plan %s: %s", plan_id, exc)
        raise HTTPException(
            status_code=503,
            detail=f"Result save failed — database may be unreachable: {exc}",
        )

    if not plan_row:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")

    summary_json = json.dumps({
        "overall_pass": req.overall_pass,
        "tested_count": req.tested_count,
        "passed_count": req.passed_count,
        "failed_count": req.failed_count,
        "maint_mode": req.maint_mode,
        "warnings": req.warnings,
    })

    first_result_id = None
    try:
        for i, elem in enumerate(req.elements):
            row = db.execute(
                text("""
                    INSERT INTO tcc_test_results
                        (plan_id, test_type, element, expected, actual,
                         min_accept, max_accept, passed, notes)
                    VALUES
                        (CAST(:plan_id AS uuid), :test_type, :element, :expected, :actual,
                         :min_accept, :max_accept, :passed, :notes)
                    RETURNING id, tested_at
                """),
                {
                    "plan_id": plan_id,
                    "test_type": elem.element,
                    "element": "pickup",
                    "expected": elem.test_current,
                    "actual": elem.measured_current,
                    "min_accept": elem.limit_low,
                    "max_accept": elem.limit_high,
                    "passed": elem.passed,
                    "notes": summary_json if i == 0 else req.notes,
                },
            ).fetchone()
            if i == 0:
                first_result_id = str(row[0])
                result_created = str(row[1])

        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Failed to save results for plan %s: %s", plan_id, exc)
        raise HTTPException(
            status_code=503,
            detail=f"Result save failed — database may be unreachable: {exc}",
        )

    if first_result_id is None:
        raise HTTPException(
            status_code=400,
            detail="No elements provided — cannot create empty result",
        )

    return SavedResult(
        id=first_result_id,
        plan_id=str(plan_id),
        overall_pass=req.overall_pass,
        tested_count=req.tested_count,
        created_at=result_created,
    )


# ── Helpers ──


def _parse_jsonb(raw) -> dict:
    """Parse a JSONB column value.

    SQLAlchemy may return the value as a dict (psycopg2 auto-deserializes
    JSONB) or as a string (if the driver doesn't auto-deserialize).
    Handle both cases.
    """
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
