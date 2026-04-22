"""
ETU LTD Curve Calculator
========================
Implements 5 Long-Time Delay calculation methods dispatched by
ETULTDParam.method:

  0  — No curve (return empty)
  1  — Thermal (CalcThermEq2)
  2  — IEEE (delegates to IEEEInverseTimeSolver in etu_curves.py)
  3  — GE-SMR (CalcGESMREq2)
  4  — Thermal-TU (CalcThermTU2)
  5  — Thermal-TUF (CalcThermTUF2)

Tables:
  tcc_etu_ltd_params   — Method dispatch + tolerances
  tcc_etu_ltd_bands    — Delay band settings (band_mult from open_time)
  tcc_etu_sensor_params — Equation coefficients (section=2, idx 0-15)
  tcc_etu_std_bands    — Min time floors (for GetMinOpenSTDB/GetMinClearSTDB)

Usage:
    from config import SessionLocal
    from apex_calc_engine.services.calc_engine.etu_ltd import ETULTDCalculator

    with SessionLocal() as session:
        calc = ETULTDCalculator(session, sensor_id=7102)
        points = calc.generate_curve(
            ltd_param_ordinal=1,
            ltd_band_ordinal=1,
            pickup_current=896.0,
            is_clear=False,
        )
"""

import math
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from apex_calc_engine.models.etu_core import ETUSensor
from apex_calc_engine.models.etu_curves import ETUSensorParam, ETULTDParam
from apex_calc_engine.models.etu_bands import ETULTDBand, ETUSTDBand
from apex_calc_engine.services.calc_engine.etu_curves import IEEEInverseTimeSolver, CurvePoint


@dataclass
class LTDCurvePoint:
    """One (current, time) point on an LTD TCC curve."""
    amps: float
    seconds: float


class ETULTDCalculator:
    """
    Generates Long-Time Delay curves using the method specified in
    tcc_etu_ltd_params for the given sensor.
    """

    POINTS_PER_DECADE = 50
    MIN_TIME = 0.001

    # Method 1 (Thermal) sensor_params layout (section=2)
    _T1_OPEN = {'ipu': 0, 'k': 1, 'n': 2, 'ithresh': 3, 'min_t': 4}
    _T1_CLEAR = {'ipu': 5, 'k': 6, 'n': 7, 'ithresh': 8, 'min_t': 9}

    # Methods 4/5 (Thermal-TU / Thermal-TUF) sensor_params layout
    _TU_OPEN = {'ipu': 0, 'alpha': 1, 'k': 2, 'n': 3, 'min_t': 4, 'ithresh': 5}
    _TU_CLEAR = {'ipu': 6, 'alpha': 7, 'k': 8, 'n': 9, 'min_t': 10, 'ithresh': 11}

    # Method 5 TUF has a shifted layout (no Ipu at idx 0)
    _TUF_OPEN = {'alpha': 0, 'k': 1, 'n': 2, 'min_t': 3}
    _TUF_CLEAR = {'alpha': 6, 'k': 7, 'n': 8, 'min_t': 9}

    def __init__(self, session: Session, sensor_id: int):
        self.session = session
        self.sensor: ETUSensor = (
            session.query(ETUSensor)
            .filter(ETUSensor.id == sensor_id)
            .one()
        )
        self._params: dict[int, float] = {}
        self._params_by_curve: dict[int, dict[int, float]] = {}
        self._load_sensor_params()

    def _load_sensor_params(self):
        """Load section=2 sensor params, grouped by curve_id."""
        rows = (
            self.session.query(ETUSensorParam)
            .filter_by(sensor_id=self.sensor.id, section=2)
            .all()
        )
        for row in rows:
            if row.value is None:
                continue
            val = float(row.value)
            # Global fallback (first value per idx)
            if row.idx not in self._params:
                self._params[row.idx] = val
            # Per-curve_id grouping
            cid = row.curve_id if row.curve_id is not None else 0
            bucket = self._params_by_curve.setdefault(cid, {})
            if row.idx not in bucket:
                bucket[row.idx] = val

    def _p(self, idx: int, default: float = 0.0) -> float:
        """Get sensor param value by index (global/fallback)."""
        return self._params.get(idx, default)

    def _pc(self, curve_id: int, idx: int, default: float = 0.0) -> float:
        """Get sensor param value by curve_id and index."""
        bucket = self._params_by_curve.get(curve_id)
        if bucket is not None and idx in bucket:
            return bucket[idx]
        return self._params.get(idx, default)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_curve(
        self,
        ltd_param_ordinal: int,
        ltd_band_ordinal: int,
        pickup_current: float,
        is_clear: bool = False,
        max_amps: float = 100000.0,
        tolerance_pct: float = 0.0,
    ) -> list[LTDCurvePoint]:
        """
        Generate LTD curve points for a given param ordinal and band.

        Args:
            ltd_param_ordinal: Which LTD curve type (ordinal in tcc_etu_ltd_params)
            ltd_band_ordinal: Which delay band (ordinal in tcc_etu_ltd_bands)
            pickup_current: LTPU pickup current in amps
            is_clear: True for clearing curve, False for opening
            max_amps: Maximum current in amps
            tolerance_pct: Tolerance percentage (e.g. 10.0 = +10%)

        Returns:
            List of LTDCurvePoint sorted by ascending current.
        """
        if pickup_current <= 0:
            return []

        ltd_param = self._get_ltd_param(ltd_param_ordinal)
        if ltd_param is None:
            return []

        method = ltd_param.method if ltd_param.method is not None else 0

        band = self._get_ltd_band(ltd_band_ordinal)
        band_mult = 1.0
        if band is not None:
            if is_clear and band.clear_time is not None:
                band_mult = float(band.clear_time)
            elif band.open_time is not None:
                band_mult = float(band.open_time)

        rating = self.sensor.rating

        # Resolve curve_id from band (needed for per-curve param lookup)
        curve_id = band.curve_id if band is not None and band.curve_id is not None else 0

        match method:
            case 1:
                return self._calc_thermal(
                    rating, pickup_current, is_clear, max_amps,
                    band_mult, tolerance_pct, curve_id,
                )
            case 2:
                return self._calc_ieee(
                    pickup_current, is_clear, max_amps,
                    band_mult, tolerance_pct, ltd_band_ordinal,
                )
            case 3:
                return self._calc_ge_smr(
                    rating, pickup_current, is_clear, max_amps,
                    tolerance_pct,
                )
            case 4:
                return self._calc_thermal_tu(
                    rating, pickup_current, is_clear, max_amps,
                    band_mult, tolerance_pct, curve_id,
                )
            case 5:
                return self._calc_thermal_tuf(
                    rating, pickup_current, is_clear, max_amps,
                    band_mult, tolerance_pct, curve_id,
                )
            case _:
                return []

    def get_ltd_info(self) -> list[dict]:
        """Get available LTD curve configurations for this sensor."""
        rows = (
            self.session.query(ETULTDParam)
            .filter_by(sensor_id=self.sensor.id)
            .order_by(ETULTDParam.ordinal)
            .all()
        )
        return [
            {
                'ordinal': r.ordinal,
                'method': r.method,
                'curve_name': r.curve_name,
                'tol_hi': float(r.tol_hi) if r.tol_hi is not None else None,
                'tol_lo': float(r.tol_lo) if r.tol_lo is not None else None,
                'delay_priority': r.delay_priority,
            }
            for r in rows
        ]

    def get_band_info(self, curve_id: Optional[int] = None) -> list[dict]:
        """Get available LTD delay bands for this sensor."""
        q = (
            self.session.query(ETULTDBand)
            .filter_by(sensor_id=self.sensor.id)
        )
        if curve_id is not None:
            q = q.filter(ETULTDBand.curve_id == curve_id)
        rows = q.order_by(ETULTDBand.ordinal).all()
        return [
            {
                'ordinal': r.ordinal,
                'band': r.band,
                'band_label': r.band_label,
                'open_time': float(r.open_time) if r.open_time is not None else None,
                'clear_time': float(r.clear_time) if r.clear_time is not None else None,
                'curve_id': r.curve_id,
                'is_default': r.is_default,
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Method 1: Thermal (CalcThermEq2)
    # ------------------------------------------------------------------

    def _calc_thermal(
        self,
        rating: int,
        pickup: float,
        is_clear: bool,
        max_amps: float,
        band_mult: float,
        tol_pct: float,
        curve_id: int = 0,
    ) -> list[LTDCurvePoint]:
        """
        Thermal curve: time = K * band_mult * ln(1/(1-arg)) / ref_ratio

        Where arg = (rating * Ipu / amps)^n
        """
        idx = self._T1_CLEAR if is_clear else self._T1_OPEN
        Ipu = self._pc(curve_id, idx['ipu'])
        K = self._pc(curve_id, idx['k'])
        n = self._pc(curve_id, idx['n'])
        Ithresh = self._pc(curve_id, idx['ithresh'])
        min_time = self._pc(curve_id, idx['min_t'], self.MIN_TIME)

        if Ipu == 0 or K == 0 or n == 0 or Ithresh == 0:
            return []

        # Reference ratio: the denominator normalizes the curve
        ref_base = rating * Ipu / (pickup * Ithresh)
        ref_arg = ref_base ** n
        if ref_arg >= 1.0:
            return []
        ref_ratio = math.log(1.0 / (1.0 - ref_arg))
        if ref_ratio <= 0:
            return []

        # Apply min time from STD bands if available and no explicit min
        if min_time <= 0:
            min_time = self._get_min_stdb_time(is_clear) or self.MIN_TIME

        # Asymptote: current at which arg=1 → time=infinity
        asymptote_amps = rating * Ipu

        return self._sweep_thermal(
            rating, pickup, Ipu, K, n, band_mult, ref_ratio,
            asymptote_amps, min_time, max_amps, tol_pct,
        )

    def _sweep_thermal(
        self,
        rating: int,
        pickup: float,
        Ipu: float,
        K: float,
        n: float,
        band_mult: float,
        ref_ratio: float,
        asymptote_amps: float,
        min_time: float,
        max_amps: float,
        tol_pct: float,
    ) -> list[LTDCurvePoint]:
        """Log-spaced current sweep for thermal equation."""
        start_amps = asymptote_amps * 1.001
        if start_amps >= max_amps:
            return []

        points: list[LTDCurvePoint] = []
        num_points = max(
            10,
            int(self.POINTS_PER_DECADE * math.log10(max_amps / start_amps)),
        )
        log_start = math.log10(start_amps)
        log_end = math.log10(max_amps)
        step = (log_end - log_start) / num_points

        tol_mult = 1.0 + tol_pct / 100.0

        for i in range(num_points + 1):
            amps = 10 ** (log_start + i * step)
            arg = (rating * Ipu / amps) ** n

            if arg >= 1.0:
                continue
            if arg <= 0:
                continue

            t = K * band_mult * math.log(1.0 / (1.0 - arg)) / ref_ratio
            t *= tol_mult

            if t <= 0:
                continue

            if t < min_time:
                points.append(LTDCurvePoint(
                    amps=round(amps, 2), seconds=round(min_time, 6),
                ))
                if amps < max_amps:
                    points.append(LTDCurvePoint(
                        amps=round(max_amps, 2), seconds=round(min_time, 6),
                    ))
                break

            points.append(LTDCurvePoint(
                amps=round(amps, 2), seconds=round(t, 6),
            ))

        return points

    # ------------------------------------------------------------------
    # Method 2: IEEE (delegates to IEEEInverseTimeSolver)
    # ------------------------------------------------------------------

    def _calc_ieee(
        self,
        pickup: float,
        is_clear: bool,
        max_amps: float,
        band_mult: float,
        tol_pct: float,
        ordinal: int,
    ) -> list[LTDCurvePoint]:
        """Delegate to the existing IEEE solver in etu_curves.py."""
        solver = IEEEInverseTimeSolver(self.session)
        variant = 'fd_clear' if is_clear else 'fd_open'

        curve_points = solver.generate_curve(
            sensor_id=self.sensor.id,
            ordinal=ordinal,
            variant=variant,
            pickup_current=pickup,
            max_amps=max_amps,
            time_dial=band_mult,
            tolerance_pct=tol_pct,
            equation_type='std',
        )
        return [
            LTDCurvePoint(amps=p.amps, seconds=p.seconds)
            for p in curve_points
        ]

    # ------------------------------------------------------------------
    # Method 3: GE-SMR (CalcGESMREq2)
    # ------------------------------------------------------------------

    def _calc_ge_smr(
        self,
        rating: int,
        pickup: float,
        is_clear: bool,
        max_amps: float,
        tol_pct: float,
    ) -> list[LTDCurvePoint]:
        """
        GE-SMR: time = -102.4 * ln(1 - (I_rated² - 1) / I_eff²)

        Where I_rated = rating * 1.12 (112% of rated)
        No band_mult applied.
        """
        I_rated = rating * 1.12

        # Starting current offset from sensor_params
        if is_clear:
            offset = self._p(self._T1_CLEAR.get('ipu', 5))
        else:
            offset = self._p(self._T1_OPEN.get('ipu', 0))

        start_amps = (offset + 1) * rating
        if start_amps <= 0:
            start_amps = rating * 1.01
        if start_amps >= max_amps:
            return []

        points: list[LTDCurvePoint] = []
        num_points = max(
            10,
            int(self.POINTS_PER_DECADE * math.log10(max_amps / start_amps)),
        )
        log_start = math.log10(start_amps)
        log_end = math.log10(max_amps)
        step = (log_end - log_start) / num_points

        tol_mult = 1.0 + tol_pct / 100.0

        for i in range(num_points + 1):
            amps = 10 ** (log_start + i * step)

            # Effective current varies by open/clear
            if is_clear:
                denominator = max_amps * 15.6 - I_rated / 0.9
                if abs(denominator) < 1e-12:
                    continue
                scale = 1.0 - ((amps - I_rated / 0.9) * 0.1 / denominator + 0.1)
                I_eff = scale * amps
            else:
                I_eff = amps * 1.2

            if I_eff <= 0:
                continue

            inner = 1.0 - (I_rated ** 2 - 1.0) / (I_eff ** 2)
            if inner <= 0:
                continue

            t = -102.4 * math.log(inner)
            t *= tol_mult

            if t <= 0:
                continue

            points.append(LTDCurvePoint(
                amps=round(amps, 2), seconds=round(t, 6),
            ))

        return points

    # ------------------------------------------------------------------
    # Method 4: Thermal-TU (CalcThermTU2)
    # ------------------------------------------------------------------

    def _calc_thermal_tu(
        self,
        rating: int,
        pickup: float,
        is_clear: bool,
        max_amps: float,
        band_mult: float,
        tol_pct: float,
        curve_id: int = 0,
    ) -> list[LTDCurvePoint]:
        """
        Thermal-TU: like Thermal but with (1-alpha) denominator + TU_offset.

        time = -K * band_mult * ln(1 - (rating*Ipu)^n / (amps*(1-alpha))^n) + TU_offset
        """
        idx = self._TU_CLEAR if is_clear else self._TU_OPEN
        Ipu = self._pc(curve_id, idx['ipu'])
        alpha = self._pc(curve_id, idx['alpha'])
        K = self._pc(curve_id, idx['k'])
        n = self._pc(curve_id, idx['n'])
        min_time = self._pc(curve_id, idx['min_t'], self.MIN_TIME)
        Ithresh = self._pc(curve_id, idx['ithresh'])

        if Ipu == 0 or K == 0 or n == 0:
            return []

        # TU_offset: only applied for clearing curves
        TU_offset = 0.0
        if is_clear:
            # Check for a stored TU offset (idx 12 or similar)
            tu_val = self._pc(curve_id, 12, 0.0)
            if tu_val != 0.0 and abs(tu_val) < 1e30:
                TU_offset = tu_val

        # Nominal current where arg=1 (asymptote)
        denom_factor = 1.0 - alpha
        if abs(denom_factor) < 1e-12:
            return []
        asymptote_amps = rating * Ipu / denom_factor

        start_amps = asymptote_amps * 1.001
        if start_amps >= max_amps:
            return []

        if min_time <= 0:
            min_time = self._get_min_stdb_time(is_clear) or self.MIN_TIME

        points: list[LTDCurvePoint] = []
        num_points = max(
            10,
            int(self.POINTS_PER_DECADE * math.log10(max_amps / start_amps)),
        )
        log_start = math.log10(start_amps)
        log_end = math.log10(max_amps)
        step = (log_end - log_start) / num_points

        tol_mult = 1.0 + tol_pct / 100.0
        numerator_base = (rating * Ipu) ** n

        for i in range(num_points + 1):
            amps = 10 ** (log_start + i * step)
            denom_val = (amps * denom_factor) ** n

            if denom_val <= 0:
                continue
            inner = 1.0 - numerator_base / denom_val
            if inner <= 0:
                continue

            t = (-K) * band_mult * math.log(inner) + TU_offset
            t *= tol_mult

            if t <= 0:
                continue

            if t < min_time:
                points.append(LTDCurvePoint(
                    amps=round(amps, 2), seconds=round(min_time, 6),
                ))
                if amps < max_amps:
                    points.append(LTDCurvePoint(
                        amps=round(max_amps, 2), seconds=round(min_time, 6),
                    ))
                break

            points.append(LTDCurvePoint(
                amps=round(amps, 2), seconds=round(t, 6),
            ))

        return points

    # ------------------------------------------------------------------
    # Method 5: Thermal-TUF (CalcThermTUF2)
    # ------------------------------------------------------------------

    def _calc_thermal_tuf(
        self,
        rating: int,
        pickup: float,
        is_clear: bool,
        max_amps: float,
        band_mult: float,
        tol_pct: float,
        curve_id: int = 0,
    ) -> list[LTDCurvePoint]:
        """
        Thermal-TUF (simplified): time = (rating/(amps*(1-alpha)))^n * K * band_mult + TU_offset
        """
        idx = self._TUF_CLEAR if is_clear else self._TUF_OPEN
        alpha = self._pc(curve_id, idx['alpha'])
        K = self._pc(curve_id, idx['k'])
        n = self._pc(curve_id, idx['n'])
        min_time = self._pc(curve_id, idx['min_t'], self.MIN_TIME)

        if K == 0 or n == 0:
            return []

        denom_factor = 1.0 - alpha
        if abs(denom_factor) < 1e-12:
            return []

        # TU_offset for clearing curves
        TU_offset = 0.0
        if is_clear:
            tu_val = self._pc(curve_id, 12, 0.0)
            if tu_val != 0.0 and abs(tu_val) < 1e30:
                TU_offset = tu_val

        # Starting current: TUF has no Ipu, start just above pickup
        start_amps = pickup * 1.001
        if start_amps <= 0:
            start_amps = rating * 1.01
        if start_amps >= max_amps:
            return []

        if min_time <= 0:
            min_time = self._get_min_stdb_time(is_clear) or self.MIN_TIME

        points: list[LTDCurvePoint] = []
        num_points = max(
            10,
            int(self.POINTS_PER_DECADE * math.log10(max_amps / start_amps)),
        )
        log_start = math.log10(start_amps)
        log_end = math.log10(max_amps)
        step = (log_end - log_start) / num_points

        tol_mult = 1.0 + tol_pct / 100.0

        for i in range(num_points + 1):
            amps = 10 ** (log_start + i * step)
            base = rating / (amps * denom_factor)
            t = (base ** n) * K * band_mult + TU_offset
            t *= tol_mult

            if t <= 0:
                continue

            if t < min_time:
                points.append(LTDCurvePoint(
                    amps=round(amps, 2), seconds=round(min_time, 6),
                ))
                if amps < max_amps:
                    points.append(LTDCurvePoint(
                        amps=round(max_amps, 2), seconds=round(min_time, 6),
                    ))
                break

            points.append(LTDCurvePoint(
                amps=round(amps, 2), seconds=round(t, 6),
            ))

        return points

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_ltd_param(self, ordinal: int) -> Optional[ETULTDParam]:
        """Load LTD param row by ordinal."""
        return (
            self.session.query(ETULTDParam)
            .filter_by(sensor_id=self.sensor.id, ordinal=ordinal)
            .one_or_none()
        )

    def _get_ltd_band(self, ordinal: int) -> Optional[ETULTDBand]:
        """Load LTD band row by ordinal."""
        return (
            self.session.query(ETULTDBand)
            .filter_by(sensor_id=self.sensor.id, ordinal=ordinal)
            .one_or_none()
        )

    def _get_min_stdb_time(self, is_clear: bool) -> Optional[float]:
        """Get minimum time from STD band data (open or clear)."""
        from sqlalchemy import func as sqlfunc

        col = ETUSTDBand.clear_time if is_clear else ETUSTDBand.open_time
        result = (
            self.session.query(sqlfunc.min(col))
            .filter(ETUSTDBand.sensor_id == self.sensor.id)
            .scalar()
        )
        return float(result) if result is not None else None
