"""
ETU Pickup Calculator
=====================
Computes pickup currents (amps) for all 4 protection elements
based on the sensor's configured calc method enum.

Calc Methods (ETUCalcMethod):
  -1  NONE           Element not present → 0.0
   0  SENSORFRAME    setting × sensor.rating
   1  PLUGTAP        setting × plug.value
   2  SENSORFRAME_MULT  setting × sensor.rating × multiplier
   3  PLUGTAP_MULT   setting × plug.value × multiplier
   4  LTPU           CASCADE: setting × ltpu_current
   5  SENSORFRAME_C  setting × sensor.rating × c_factor
   6  PLUGTAP_C      setting × plug.value × c_factor
   7  AMPS           setting is already in amperes
   8  GFPU           CASCADE: from GFPU result (reserved)
   9  MULTWTH        Reserved
  10  STPU           CASCADE: from STPU result (reserved)

Usage:
    from config import SessionLocal
    from apex_calc_engine.services.calc_engine.etu_pickup import ETUPickupCalculator

    with SessionLocal() as session:
        calc = ETUPickupCalculator(session, sensor_id=6258)
        result = calc.calculate(
            plug_id=7389,
            ltpu_setting=0.8,
            stpu_setting=4.0,
            inst_setting=10.0,
        )
        # result.ltpu  → PickupResult(current=480.0, min_limit=..., max_limit=...)
"""

from enum import IntEnum
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from apex_calc_engine.models.etu_core import ETUSensor, ETUPlug
from apex_calc_engine.models.etu_curves import ETUSensorMaint, ETUSTPUOverride
from apex_calc_engine.models.etu_pickups import (
    ETULTPUPickup, ETULTPUMultiplier,
    ETUSTPUPickup, ETUInstPickup, ETUGFPUPickup,
)


class ETUCalcMethod(IntEnum):
    """Calculation method enum — mirrors tcc_etu_sensors.*_calc columns."""
    NONE = -1
    SENSORFRAME = 0
    PLUGTAP = 1
    SENSORFRAME_MULT = 2
    PLUGTAP_MULT = 3
    LTPU = 4
    SENSORFRAME_C = 5
    PLUGTAP_C = 6
    AMPS = 7
    GFPU = 8
    MULTWTH = 9
    STPU = 10


@dataclass
class PickupResult:
    """Result for a single protection element."""
    current: float          # Pickup current in amps
    min_limit: float        # Low tolerance bound (amps)
    max_limit: float        # High tolerance bound (amps)
    method: int             # Calc method used
    method_name: str        # Human-readable method name
    maint_mode: bool = False
    reduction: Optional[float] = None
    delay_opening: Optional[float] = None
    delay_clearing: Optional[float] = None
    override_applied: bool = False
    override_open_time: Optional[float] = None
    override_clear_time: Optional[float] = None


@dataclass
class AllPickupResults:
    """Results for all 4 protection elements."""
    sensor_id: int
    rating: int
    maint_mode: bool
    maint_capable: bool
    maint_support_level: str
    warnings: list[str]
    ltpu: Optional[PickupResult]
    stpu: Optional[PickupResult]
    inst: Optional[PickupResult]
    gfpu: Optional[PickupResult]
    maint_profile: dict[str, Any]


class ETUPickupCalculator:
    """
    Computes pickup currents for a given sensor.

    Fetches the sensor, plug, and multiplier data from the database,
    then applies the appropriate calc method for each element.
    """

    def __init__(self, session: Session, sensor_id: int):
        self.session = session
        self.sensor: ETUSensor = (
            session.query(ETUSensor)
            .filter(ETUSensor.id == sensor_id)
            .one()
        )
        self.maint_record: Optional[ETUSensorMaint] = (
            session.query(ETUSensorMaint)
            .filter(ETUSensorMaint.sensor_id == sensor_id)
            .order_by(ETUSensorMaint.id.desc())
            .first()
        )
        self.stpu_override: dict = self._load_stpu_override(sensor_id)

    def calculate(
        self,
        plug_id: Optional[int] = None,
        ltpu_setting: Optional[float] = None,
        stpu_setting: Optional[float] = None,
        inst_setting: Optional[float] = None,
        gfpu_setting: Optional[float] = None,
        multiplier_value: Optional[float] = None,
        c_factor: Optional[float] = None,
        maint_mode: bool = False,
    ) -> AllPickupResults:
        """
        Calculate pickup currents for all protection elements.

        Args:
            plug_id: ID of the selected rating plug (for PLUGTAP methods)
            ltpu_setting: LTPU dial setting (multiplier)
            stpu_setting: STPU dial setting (multiplier)
            inst_setting: INST dial setting (multiplier)
            gfpu_setting: GFPU dial setting (multiplier)
            multiplier_value: C/multiplier value (for *_MULT methods)
            c_factor: C factor (for *_C methods)

        Returns:
            AllPickupResults with current + tolerance for each element.
        """
        sensor = self.sensor
        plug_value = self._get_plug_value(plug_id)
        maint_profile = self._resolve_maint_profile()
        effective_maint = maint_mode and maint_profile["capable"]
        warnings: list[str] = []

        if maint_mode and not maint_profile["capable"]:
            warnings.append(
                "Sensor does not have maintenance mode data — using normal calculations"
            )
        elif effective_maint:
            if maint_profile["ltpu_reduction"] is None and maint_profile["stpu_reduction"] is None:
                warnings.append(
                    "LTPU/STPU reduction factors not available — defaulting to 1.0 (partial MAINT support: INST/GFPU only)"
                )
            if maint_profile["inst_calc"] in (None, -1):
                warnings.append("INST maint calc inactive (-1) — using normal INST")
            if maint_profile["gfpu_calc"] in (None, -1):
                warnings.append("GFPU maint calc inactive (-1) — using normal GFPU")

        # Compute in dependency order: LTPU → STPU → INST → GFPU
        ltpu_result = self._calc_element(
            calc_method=sensor.ltpu_calc,
            setting=ltpu_setting,
            plug_value=plug_value,
            multiplier=multiplier_value,
            c_factor=c_factor,
            tol_lo=sensor.ltpu_tol_lo,
            tol_hi=sensor.ltpu_tol_hi,
            cascade_current=None,
            element_name=sensor.ltpu_name,
            current_factor=(
                maint_profile["ltpu_reduction"] if effective_maint and maint_profile["ltpu_reduction"] is not None else 1.0
            ),
            maint_mode=effective_maint,
            reduction=(
                maint_profile["ltpu_reduction"] if effective_maint else None
            ),
        )

        # STPU may cascade from LTPU (method=4)
        ltpu_current = ltpu_result.current if ltpu_result else 0.0
        if self.stpu_override.get("applied"):
            stpu_result = self._build_override_stpu_result(
                maint_mode=effective_maint and maint_profile["stpu_reduction"] is not None,
            )
            if effective_maint and maint_profile["stpu_reduction"] is not None:
                warnings.append(
                    "STPU override active - MAINT reduction factor not applied to override amps"
                )
        else:
            stpu_result = self._calc_element(
                calc_method=sensor.stpu_calc,
                setting=stpu_setting,
                plug_value=plug_value,
                multiplier=multiplier_value,
                c_factor=c_factor,
                tol_lo=sensor.stpu_tol_lo,
                tol_hi=sensor.stpu_tol_hi,
                cascade_current=ltpu_current,
                element_name=sensor.stpu_name,
                current_factor=(
                    maint_profile["stpu_reduction"] if effective_maint and maint_profile["stpu_reduction"] is not None else 1.0
                ),
                maint_mode=effective_maint,
                reduction=(
                    maint_profile["stpu_reduction"] if effective_maint else None
                ),
            )

        # INST can cascade from LTPU (method=4) or STPU (method=10)
        stpu_current = stpu_result.current if stpu_result else 0.0
        inst_cascade = ltpu_current  # default cascade source
        if sensor.inst_calc is not None and sensor.inst_calc == ETUCalcMethod.STPU:
            inst_cascade = stpu_current
        inst_method = (
            maint_profile["inst_calc"]
            if effective_maint and maint_profile["inst_calc"] not in (None, -1)
            else sensor.inst_calc
        )
        inst_result = self._calc_element(
            calc_method=inst_method,
            setting=inst_setting,
            plug_value=plug_value,
            multiplier=multiplier_value,
            c_factor=c_factor,
            tol_lo=(
                maint_profile["inst_tol_lo"]
                if effective_maint and maint_profile["inst_tol_lo"] is not None
                else sensor.inst_tol_lo
            ),
            tol_hi=(
                maint_profile["inst_tol_hi"]
                if effective_maint and maint_profile["inst_tol_hi"] is not None
                else sensor.inst_tol_hi
            ),
            cascade_current=inst_cascade,
            element_name=sensor.inst_name,
            maint_mode=effective_maint and maint_profile["inst_calc"] not in (None, -1),
            delay_opening=maint_profile["inst_delay_opening"] if effective_maint else None,
            delay_clearing=maint_profile["inst_delay_clearing"] if effective_maint else None,
        )

        # GFPU — method -1 is very common (3,071 sensors)
        gfpu_method = (
            maint_profile["gfpu_calc"]
            if effective_maint and maint_profile["gfpu_calc"] not in (None, -1)
            else sensor.gfpu_calc
        )
        gfpu_result = self._calc_element(
            calc_method=gfpu_method,
            setting=gfpu_setting,
            plug_value=plug_value,
            multiplier=multiplier_value,
            c_factor=c_factor,
            tol_lo=(
                maint_profile["gfpu_tol_lo"]
                if effective_maint and maint_profile["gfpu_tol_lo"] is not None
                else sensor.gfpu_tol_lo
            ),
            tol_hi=(
                maint_profile["gfpu_tol_hi"]
                if effective_maint and maint_profile["gfpu_tol_hi"] is not None
                else sensor.gfpu_tol_hi
            ),
            cascade_current=None,
            element_name=sensor.gfpu_name,
            maint_mode=effective_maint and maint_profile["gfpu_calc"] not in (None, -1),
        )

        return AllPickupResults(
            sensor_id=sensor.id,
            rating=sensor.rating,
            maint_mode=effective_maint,
            maint_capable=maint_profile["capable"],
            maint_support_level=maint_profile["support_level"],
            warnings=warnings,
            ltpu=ltpu_result,
            stpu=stpu_result,
            inst=inst_result,
            gfpu=gfpu_result,
            maint_profile=maint_profile,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_stpu_override(self, sensor_id: int) -> dict:
        """Read the flat tcc_etu_stpu_overrides row for a sensor.

        Promoted from tcc_v5_backend per matrix #30(c). A present row with
        non-null override amps bypasses the normal STPU formula and carries
        override-specific tolerances/open/clear times into PickupResult.
        """
        try:
            row = self.session.execute(
                text(
                    """
                    SELECT ovr_amps,
                           ovr_toler_low_pct,
                           ovr_toler_high_pct,
                           ovr_open_sec,
                           ovr_clear_sec
                    FROM tcc_etu_stpu_overrides
                    WHERE sensor_id = :sensor_id
                    LIMIT 1
                    """
                ),
                {'sensor_id': sensor_id},
            ).fetchone()
            mapping = row._mapping if hasattr(row, '_mapping') else row
            if row is not None and mapping.get("ovr_amps") is not None:
                return {
                    "applied": True,
                    "amps": float(mapping.get("ovr_amps")),
                    "tolerance_low": (
                        float(mapping.get("ovr_toler_low_pct"))
                        if mapping.get("ovr_toler_low_pct") is not None else None
                    ),
                    "tolerance_high": (
                        float(mapping.get("ovr_toler_high_pct"))
                        if mapping.get("ovr_toler_high_pct") is not None else None
                    ),
                    "open_time": (
                        float(mapping.get("ovr_open_sec"))
                        if mapping.get("ovr_open_sec") is not None else None
                    ),
                    "clear_time": (
                        float(mapping.get("ovr_clear_sec"))
                        if mapping.get("ovr_clear_sec") is not None else None
                    ),
                }
        except Exception:
            if hasattr(self.session, 'rollback'):
                self.session.rollback()

        rows = (
            self.session.query(ETUSTPUOverride)
            .filter(ETUSTPUOverride.sensor_id == sensor_id)
            .all()
        )
        values = {getattr(row, "type_", None): getattr(row, "value", None) for row in rows}
        amps = values.get("amps")
        if amps is None:
            return {
                "applied": False,
                "amps": None,
                "tolerance_low": None,
                "tolerance_high": None,
                "open_time": None,
                "clear_time": None,
            }
        return {
            "applied": True,
            "amps": float(amps),
            "tolerance_low": float(values["tolerance_low"]) if values.get("tolerance_low") is not None else None,
            "tolerance_high": float(values["tolerance_high"]) if values.get("tolerance_high") is not None else None,
            "open_time": float(values["open_time"]) if values.get("open_time") is not None else None,
            "clear_time": float(values["clear_time"]) if values.get("clear_time") is not None else None,
        }

    def _build_override_stpu_result(self, maint_mode: bool) -> PickupResult:
        """Build an STPU PickupResult directly from override amps/tolerances."""
        amps = float(self.stpu_override["amps"] or 0.0)
        tol_lo = self.stpu_override.get("tolerance_low")
        tol_hi = self.stpu_override.get("tolerance_high")
        lo_pct = float(tol_lo) if tol_lo is not None else 0.0
        hi_pct = float(tol_hi) if tol_hi is not None else 0.0
        min_limit = amps * (1.0 + lo_pct / 100.0)
        max_limit = amps * (1.0 + hi_pct / 100.0)
        return PickupResult(
            current=round(amps, 2),
            min_limit=round(min_limit, 2),
            max_limit=round(max_limit, 2),
            method=int(ETUCalcMethod.AMPS),
            method_name="OVERRIDE",
            maint_mode=maint_mode,
            reduction=None,
            override_applied=True,
            override_open_time=self.stpu_override.get("open_time"),
            override_clear_time=self.stpu_override.get("clear_time"),
        )

    def _get_plug_value(self, plug_id: Optional[int]) -> Optional[int]:
        """Fetch plug rating value by ID."""
        if plug_id is None:
            return None
        plug = (
            self.session.query(ETUPlug)
            .filter(ETUPlug.id == plug_id)
            .one_or_none()
        )
        return plug.value if plug else None

    def _calc_element(
        self,
        calc_method: Optional[int],
        setting: Optional[float],
        plug_value: Optional[int],
        multiplier: Optional[float],
        c_factor: Optional[float],
        tol_lo: Optional[Decimal],
        tol_hi: Optional[Decimal],
        cascade_current: Optional[float],
        element_name: Optional[str],
        current_factor: float = 1.0,
        maint_mode: bool = False,
        reduction: Optional[float] = None,
        delay_opening: Optional[float] = None,
        delay_clearing: Optional[float] = None,
    ) -> Optional[PickupResult]:
        """
        Calculate pickup current for one protection element.

        Returns None if element is not present (name is None or method is NONE).
        """
        # Element not present on this sensor
        if element_name is None:
            return None
        if calc_method is None or calc_method == ETUCalcMethod.NONE:
            return None

        method = ETUCalcMethod(calc_method)
        rating = self.sensor.rating
        current = 0.0

        if setting is None:
            setting = 0.0

        if method == ETUCalcMethod.SENSORFRAME:
            # setting × sensor rating
            current = setting * rating

        elif method == ETUCalcMethod.PLUGTAP:
            # setting × plug value
            if plug_value is None:
                return None
            current = setting * plug_value

        elif method == ETUCalcMethod.SENSORFRAME_MULT:
            # setting × sensor rating × multiplier
            mult = float(multiplier) if multiplier else 1.0
            current = setting * rating * mult

        elif method == ETUCalcMethod.PLUGTAP_MULT:
            # setting × plug value × multiplier
            if plug_value is None:
                return None
            mult = float(multiplier) if multiplier else 1.0
            current = setting * plug_value * mult

        elif method == ETUCalcMethod.LTPU:
            # CASCADE: setting × ltpu_current
            if cascade_current is None or cascade_current == 0.0:
                return None
            current = setting * cascade_current

        elif method == ETUCalcMethod.SENSORFRAME_C:
            # setting × sensor rating × c_factor
            cf = float(c_factor) if c_factor else 1.0
            current = setting * rating * cf

        elif method == ETUCalcMethod.PLUGTAP_C:
            # setting × plug value × c_factor
            if plug_value is None:
                return None
            cf = float(c_factor) if c_factor else 1.0
            current = setting * plug_value * cf

        elif method == ETUCalcMethod.AMPS:
            # setting is already in amperes
            current = setting

        elif method == ETUCalcMethod.GFPU:
            # CASCADE from GFPU (reserved — not commonly used)
            if cascade_current is not None:
                current = setting * cascade_current
            else:
                current = setting * rating

        elif method == ETUCalcMethod.STPU:
            # CASCADE from STPU
            if cascade_current is not None:
                current = setting * cascade_current
            else:
                current = setting * rating

        elif method == ETUCalcMethod.MULTWTH:
            # Reserved — not seen in data
            current = setting * rating

        current *= current_factor

        # Tolerance limits
        min_limit, max_limit = self._calc_tolerance(current, tol_lo, tol_hi)

        return PickupResult(
            current=round(current, 2),
            min_limit=round(min_limit, 2),
            max_limit=round(max_limit, 2),
            method=int(method),
            method_name=method.name,
            maint_mode=maint_mode,
            reduction=round(reduction, 4) if reduction is not None else None,
            delay_opening=delay_opening,
            delay_clearing=delay_clearing,
        )

    def _resolve_maint_profile(self) -> dict[str, Any]:
        """Build the effective MAINT profile from the maint record and params_json."""
        if self.maint_record is None:
            return {
                "capable": False,
                "support_level": "none",
                "ltpu_reduction": None,
                "stpu_reduction": None,
                "inst_calc": None,
                "inst_tol_lo": None,
                "inst_tol_hi": None,
                "inst_delay_opening": None,
                "inst_delay_clearing": None,
                "gfpu_calc": None,
                "gfpu_tol_lo": None,
                "gfpu_tol_hi": None,
                "gf_delay_opening": None,
                "gf_delay_clearing": None,
                "gf_frame_opening": None,
                "gf_frame_clearing": None,
            }

        params = self.maint_record.params_json or {}
        inst = params.get("instantaneous") or {}
        gf = params.get("ground_fault") or {}

        inst_calc = self._to_int(inst.get("pickup_calc"))
        gfpu_calc = self._to_int(gf.get("pickup_calc"))
        ltpu_reduction = self._to_float(self.maint_record.maint_ltpu_reduction)
        stpu_reduction = self._to_float(self.maint_record.maint_stpu_reduction)
        capable = bool(self.maint_record.maint_available) or any(
            value not in (None, -1) for value in (inst_calc, gfpu_calc)
        )

        if not capable:
            support_level = "none"
        elif ltpu_reduction is not None and stpu_reduction is not None:
            support_level = "full"
        else:
            support_level = "partial_inst_gfpu"

        return {
            "capable": capable,
            "support_level": support_level,
            "ltpu_reduction": ltpu_reduction,
            "stpu_reduction": stpu_reduction,
            "inst_calc": inst_calc,
            "inst_tol_lo": self._to_decimal(inst.get("tolerance_low")),
            "inst_tol_hi": self._to_decimal(inst.get("tolerance_high")),
            "inst_delay_opening": self._to_float(inst.get("delay_opening")),
            "inst_delay_clearing": self._to_float(inst.get("delay_clearing")),
            "gfpu_calc": gfpu_calc,
            "gfpu_tol_lo": self._to_decimal(gf.get("tolerance_low")),
            "gfpu_tol_hi": self._to_decimal(gf.get("tolerance_high")),
            "gf_delay_opening": self._to_float(gf.get("delay_opening")),
            "gf_delay_clearing": self._to_float(gf.get("delay_clearing")),
            "gf_frame_opening": self._to_float(gf.get("fr_opening")),
            "gf_frame_clearing": self._to_float(gf.get("fr_closing")),
        }

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        return int(value)

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        return float(value)

    @staticmethod
    def _to_decimal(value: Any) -> Optional[Decimal]:
        if value is None or value == "":
            return None
        return Decimal(str(value))

    @staticmethod
    def _calc_tolerance(
        current: float,
        tol_lo: Optional[Decimal],
        tol_hi: Optional[Decimal],
    ) -> tuple[float, float]:
        """
        Compute tolerance band around a pickup current.

        Formula (verified against golden data):
            min = current × (1 + tol_lo / 100)
            max = current × (1 + tol_hi / 100)

        The sign of tol_lo determines direction:
        - tol_lo = -10.0 → min = current × 0.90  (10% below nominal)
        - tol_lo =   5.0 → min = current × 1.05  (5% above nominal — asymmetric)

        Golden: sensor 6258 LTPU tol_lo=5.00, tol_hi=20.00, current=480A
            → min = 480 × 1.05 = 504A, max = 480 × 1.20 = 576A  ✓

        Golden: sensor 6258 STPU tol_lo=-10.00, tol_hi=10.00, current=1920A
            → min = 1920 × 0.90 = 1728A, max = 1920 × 1.10 = 2112A  ✓
        """
        lo_pct = float(tol_lo) if tol_lo is not None else 0.0
        hi_pct = float(tol_hi) if tol_hi is not None else 0.0

        min_limit = current * (1.0 + lo_pct / 100.0)
        max_limit = current * (1.0 + hi_pct / 100.0)

        return min_limit, max_limit

    # ------------------------------------------------------------------
    # Convenience queries
    # ------------------------------------------------------------------

    def get_available_pickups(self, element: str) -> list[dict]:
        """
        Get all available pickup settings for a given element.

        Args:
            element: One of 'ltpu', 'stpu', 'inst', 'gfpu'

        Returns:
            List of dicts with 'id', 'value', 'label', 'is_default', 'sort_order'
        """
        model_map = {
            'ltpu': ETULTPUPickup,
            'stpu': ETUSTPUPickup,
            'inst': ETUInstPickup,
            'gfpu': ETUGFPUPickup,
        }
        model = model_map.get(element)
        if model is None:
            return []

        rows = (
            self.session.query(model)
            .filter(model.sensor_id == self.sensor.id)
            .order_by(model.sort_order)
            .all()
        )

        results = []
        for row in rows:
            entry = {
                'id': row.id,
                'value': float(row.value) if row.value is not None else None,
                'is_default': row.is_default,
                'sort_order': row.sort_order,
            }
            if hasattr(row, 'label'):
                entry['label'] = row.label
            results.append(entry)
        return results

    def get_available_multipliers(self) -> list[dict]:
        """Get available LTPU multiplier/C values for this sensor."""
        rows = (
            self.session.query(ETULTPUMultiplier)
            .filter(ETULTPUMultiplier.sensor_id == self.sensor.id)
            .order_by(ETULTPUMultiplier.sort_order)
            .all()
        )
        return [
            {
                'id': r.id,
                'c_value': float(r.c_value) if r.c_value is not None else None,
                'is_default': r.is_default,
                'sort_order': r.sort_order,
            }
            for r in rows
        ]

    def get_plugs_for_style(self) -> list[dict]:
        """Get available rating plugs for this sensor's trip style."""
        rows = (
            self.session.query(ETUPlug)
            .filter(ETUPlug.trip_style_id == self.sensor.trip_style_id)
            .order_by(ETUPlug.value)
            .all()
        )
        return [{'id': r.id, 'value': r.value} for r in rows]
