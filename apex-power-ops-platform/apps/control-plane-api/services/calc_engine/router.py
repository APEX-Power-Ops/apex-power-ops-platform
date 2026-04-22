"""
FastAPI router for the platform calc surface.

Endpoints:
  POST /api/v1/calculate/etu-pickup
  POST /api/v1/calculate/etu-curve
  POST /api/v1/calculate/tmt-curve
"""

from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apex_calc_engine.services.calc_engine import ETUPickupCalculator
from apex_calc_engine.services.calc_engine import ETULTDCalculator
from apex_calc_engine.services.calc_engine import IEEEInverseTimeSolver
from apex_calc_engine.services.calc_engine import TMTCurveGenerator
from config import get_db

router = APIRouter(prefix="/api/v1/calculate", tags=["calculate"])


# ──────────────────────────────────────────────
# Request / Response Schemas
# ──────────────────────────────────────────────

class PickupRequest(BaseModel):
    sensor_id: int
    plug_id: Optional[int] = None
    ltpu_setting: Optional[float] = None
    stpu_setting: Optional[float] = None
    inst_setting: Optional[float] = None
    gfpu_setting: Optional[float] = None
    maint_mode: bool = Field(False, description="Enable maintenance-mode pickup overrides")

class PickupElementResponse(BaseModel):
    test_current: float
    min_limit: float
    max_limit: float
    method: int
    method_name: str
    maint_mode: bool = False
    reduction: Optional[float] = None
    delay_opening: Optional[float] = None
    delay_clearing: Optional[float] = None

class PickupResponse(BaseModel):
    sensor_id: int
    rating: int
    maint_mode: bool = False
    maint_capable: bool = False
    maint_support_level: str = "none"
    warnings: list[str] = Field(default_factory=list)
    elements: dict[str, Optional[PickupElementResponse]]

class CurveRequest(BaseModel):
    sensor_id: int
    plug_id: Optional[int] = None
    ltpu_setting: Optional[float] = None
    stpu_setting: Optional[float] = None
    std_ordinal: int = 1
    inst_setting: Optional[float] = None
    maint_mode: bool = Field(False, description="Enable maintenance-mode pickup overrides")
    max_amps: float = 100000.0

class CurveResponse(BaseModel):
    sensor_id: int
    maint_mode: bool = False
    maint_capable: bool = False
    maint_support_level: str = "none"
    warnings: list[str] = Field(default_factory=list)
    curves: dict[str, list[list[float]]]

class TMTRequest(BaseModel):
    frame_id: int
    trip_class: int = 0
    amp_rating: Optional[float] = None

class TMTResponse(BaseModel):
    frame_id: int
    trip_class: int
    curve: list[list[float]]


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@router.post("/etu-pickup", response_model=PickupResponse)
def calculate_etu_pickup(req: PickupRequest, db: Session = Depends(get_db)):
    """Calculate pickup currents for all 4 protection elements."""
    try:
        calc = ETUPickupCalculator(db, req.sensor_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Sensor {req.sensor_id} not found")

    result = calc.calculate(
        plug_id=req.plug_id,
        ltpu_setting=req.ltpu_setting,
        stpu_setting=req.stpu_setting,
        inst_setting=req.inst_setting,
        gfpu_setting=req.gfpu_setting,
        maint_mode=req.maint_mode,
    )

    def _elem(pr):
        if pr is None:
            return None
        return PickupElementResponse(
            test_current=pr.current,
            min_limit=pr.min_limit,
            max_limit=pr.max_limit,
            method=pr.method,
            method_name=pr.method_name,
            maint_mode=pr.maint_mode,
            reduction=pr.reduction,
            delay_opening=pr.delay_opening,
            delay_clearing=pr.delay_clearing,
        )

    return PickupResponse(
        sensor_id=result.sensor_id,
        rating=result.rating,
        maint_mode=result.maint_mode,
        maint_capable=result.maint_capable,
        maint_support_level=result.maint_support_level,
        warnings=result.warnings,
        elements={
            "LTPU": _elem(result.ltpu),
            "STPU": _elem(result.stpu),
            "INST": _elem(result.inst),
            "GFPU": _elem(result.gfpu),
        },
    )


@router.post("/etu-curve", response_model=CurveResponse)
def calculate_etu_curve(req: CurveRequest, db: Session = Depends(get_db)):
    """Generate LTD/STD open+clear curves for a sensor."""
    try:
        pickup_calc = ETUPickupCalculator(db, req.sensor_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Sensor {req.sensor_id} not found")

    # Compute pickup currents first
    pickups = pickup_calc.calculate(
        plug_id=req.plug_id,
        ltpu_setting=req.ltpu_setting,
        stpu_setting=req.stpu_setting,
        inst_setting=req.inst_setting,
        maint_mode=req.maint_mode,
    )

    ltpu_current = pickups.ltpu.current if pickups.ltpu else 0.0
    stpu_current = pickups.stpu.current if pickups.stpu else 0.0
    inst_current = pickups.inst.current if pickups.inst else 0.0

    curves: dict[str, list[list[float]]] = {}

    # LTD curves (from etu_ltd — multiple methods possible)
    ltd_calc = ETULTDCalculator(db, req.sensor_id)
    ltd_info = ltd_calc.get_ltd_info()

    if ltd_info:
        # Use first LTD param, first band
        bands = ltd_calc.get_band_info()
        band_ord = bands[0]['ordinal'] if bands else 1

        for is_clear, suffix in [(False, 'open'), (True, 'clear')]:
            pts = ltd_calc.generate_curve(
                ltd_param_ordinal=1,
                ltd_band_ordinal=band_ord,
                pickup_current=ltpu_current,
                is_clear=is_clear,
                max_amps=req.max_amps,
            )
            curves[f'ltd_{suffix}'] = [[p.amps, p.seconds] for p in pts]

    # STD curves (IEEE equations)
    ieee = IEEEInverseTimeSolver(db)
    for variant, key in [('fd_open', 'std_open'), ('fd_clear', 'std_clear')]:
        pts = ieee.generate_curve(
            sensor_id=req.sensor_id,
            ordinal=req.std_ordinal,
            variant=variant,
            pickup_current=stpu_current if stpu_current > 0 else ltpu_current,
            max_amps=req.max_amps,
        )
        curves[key] = [[p.amps, p.seconds] for p in pts]

    # INST curves (flat line from inst_current to max_amps)
    if inst_current > 0:
        inst_time_open = 0.05   # typical INST timing
        inst_time_clear = 0.08
        curves['inst_open'] = [[inst_current, inst_time_open],
                               [req.max_amps, inst_time_open]]
        curves['inst_clear'] = [[inst_current, inst_time_clear],
                                [req.max_amps, inst_time_clear]]

    return CurveResponse(
        sensor_id=req.sensor_id,
        maint_mode=pickups.maint_mode,
        maint_capable=pickups.maint_capable,
        maint_support_level=pickups.maint_support_level,
        warnings=pickups.warnings,
        curves=curves,
    )


@router.post("/tmt-curve", response_model=TMTResponse)
def calculate_tmt_curve(req: TMTRequest, db: Session = Depends(get_db)):
    """Generate TMT breaker curve via Catmull-Rom spline."""
    tmt = TMTCurveGenerator(db, req.frame_id)

    classes = tmt.get_available_classes()
    if req.trip_class not in classes:
        raise HTTPException(
            status_code=400,
            detail=f"Trip class {req.trip_class} not available. "
                   f"Available: {classes}",
        )

    pts = tmt.generate_curve(req.trip_class)

    return TMTResponse(
        frame_id=req.frame_id,
        trip_class=req.trip_class,
        curve=[[p.amps, p.seconds] for p in pts],
    )
