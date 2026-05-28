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
from types import SimpleNamespace
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from apex_calc_engine.models.etu_core import ETUSensor
from apex_calc_engine.models.etu_curves import ETULTDParam
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
        """Load section=2 sensor params, grouped by curve_id.

        The live Supabase surface no longer exposes a surrogate ``id`` column on
        ``tcc_etu_sensor_params``. Read the flat table directly so LTD curve
        generation remains aligned with the active schema instead of depending on
        the older ORM shape.
        """
        rows = self.session.execute(
            text(
                """
                SELECT sensor_id, section, curve_id, idx, value
                FROM tcc_etu_sensor_params
                WHERE sensor_id = :sensor_id
                  AND section = 2
                ORDER BY curve_id NULLS FIRST, idx
                """
            ),
            {"sensor_id": self.sensor.id},
        ).fetchall()
        for row in rows:
            mapping = row._mapping if hasattr(row, "_mapping") else row
            value = mapping.get("value")
            if value is None:
                continue
            idx = mapping.get("idx")
            if idx is None:
                continue
            val = float(value)
            # Global fallback (first value per idx)
            if idx not in self._params:
                self._params[idx] = val
            # Per-curve_id grouping
            curve_id = mapping.get("curve_id")
            cid = curve_id if curve_id is not None else 0
            bucket = self._params_by_curve.setdefault(cid, {})
            if idx not in bucket:
                bucket[idx] = val

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
        return [
            {
                'ordinal': row['ordinal'],
                'method': row['method'],
                'curve_name': row['curve_name'],
                'tol_hi': float(row['tol_hi']) if row['tol_hi'] is not None else None,
                'tol_lo': float(row['tol_lo']) if row['tol_lo'] is not None else None,
                'delay_priority': row['delay_priority'],
            }
            for row in self._load_ltd_param_rows()
        ]

    def get_band_info(self, curve_id: Optional[int] = None) -> list[dict]:
        """Get available LTD delay bands for this sensor."""
        params = {'sensor_id': self.sensor.id}
        curve_filter = ''
        if curve_id is not None:
            params['curve_id'] = curve_id
            curve_filter = ' AND curve_id = :curve_id'

        try:
            rows = self.session.execute(
                text(
                    f"""
                    SELECT ordinal,
                           band,
                           band_label,
                           open_time,
                           clear_time,
                           curve_id,
                           COALESCE(is_default, FALSE) AS is_default
                    FROM tcc_etu_ltd_bands
                    WHERE sensor_id = :sensor_id{curve_filter}
                    ORDER BY ordinal NULLS LAST,
                             sort_order NULLS LAST,
                             open_time NULLS LAST,
                             id
                    """
                ),
                params,
            ).fetchall()
            return self._normalize_ltd_band_rows(rows)
        except Exception:
            if hasattr(self.session, 'rollback'):
                self.session.rollback()

        try:
            rows = self.session.execute(
                text(
                    f"""
                    SELECT curve_id,
                           ltd_desc AS band_label,
                           ltd_setting AS open_time
                    FROM tcc_etu_ltd_bands
                    WHERE sensor_id = :sensor_id{curve_filter}
                    ORDER BY curve_id NULLS LAST,
                             ltd_setting NULLS LAST,
                             id
                    """
                ),
                params,
            ).fetchall()
            return self._normalize_ltd_band_rows(rows, legacy=True)
        except Exception:
            if hasattr(self.session, 'rollback'):
                self.session.rollback()

        q = self.session.query(ETULTDBand).filter_by(sensor_id=self.sensor.id)
        if curve_id is not None:
            q = q.filter(ETULTDBand.curve_id == curve_id)
        rows = q.order_by(ETULTDBand.ordinal).all()
        return self._normalize_ltd_band_rows(rows)

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

    def _load_ltd_param_rows(self) -> list[dict[str, object]]:
        """Load source-faithful LTD parameter rows, with package ORM fallback.

        Promoted from the tcc source-domain compatibility path per matrix
        #30(b). The SQL path accepts rebuilt/source-faithful column names and
        aliases them back into the package calculator contract.
        """
        params = {'sensor_id': self.sensor.id}

        try:
            rows = self.session.execute(
                text(
                    """
                    SELECT curve_name,
                           curve_id,
                           ordinal,
                           setting_method AS method,
                           sec2_ltf AS ltf,
                           ds2_tol_high AS tol_hi,
                           ds2_tol_low AS tol_lo,
                           setting_val AS value,
                           setting_type AS type,
                           slope,
                           ds2_step_size AS step,
                           ds2_dly_pty AS delay_priority,
                           ds2_force_i2x_out AS force_i2x_out
                    FROM tcc_etu_ltd_params
                    WHERE sensor_id = :sensor_id
                    ORDER BY ordinal NULLS LAST, curve_name
                    """
                ),
                params,
            ).fetchall()
            return self._normalize_ltd_param_rows(rows)
        except Exception:
            if hasattr(self.session, 'rollback'):
                self.session.rollback()

        rows = (
            self.session.query(ETULTDParam)
            .filter_by(sensor_id=self.sensor.id)
            .order_by(ETULTDParam.ordinal)
            .all()
        )
        return self._normalize_ltd_param_rows(rows)

    @staticmethod
    def _normalize_ltd_param_rows(rows) -> list[dict[str, object]]:
        normalized: list[dict[str, object]] = []

        def _read(row, key: str, default=None):
            if hasattr(row, '_mapping'):
                return row._mapping.get(key, default)
            if isinstance(row, dict):
                return row.get(key, default)
            return getattr(row, key, default)

        for index, row in enumerate(rows, start=1):
            ordinal = _read(row, 'ordinal', index)
            normalized.append({
                'curve_name': _read(row, 'curve_name'),
                'curve_id': _read(row, 'curve_id'),
                'ordinal': int(ordinal) if ordinal is not None else index,
                'method': _read(row, 'method'),
                'ltf': _read(row, 'ltf'),
                'tol_hi': _read(row, 'tol_hi'),
                'tol_lo': _read(row, 'tol_lo'),
                'value': _read(row, 'value'),
                'type': _read(row, 'type'),
                'slope': _read(row, 'slope'),
                'step': _read(row, 'step'),
                'delay_priority': _read(row, 'delay_priority'),
                'force_i2x_out': _read(row, 'force_i2x_out'),
            })
        return normalized

    @staticmethod
    def _normalize_ltd_band_rows(rows, legacy: bool = False) -> list[dict]:
        normalized: list[dict] = []

        def _read(row, key: str, default=None):
            if hasattr(row, '_mapping'):
                return row._mapping.get(key, default)
            if isinstance(row, dict):
                return row.get(key, default)
            return getattr(row, key, default)

        for index, row in enumerate(rows, start=1):
            open_time = _read(row, 'open_time')
            clear_time = _read(row, 'clear_time') if not legacy else open_time
            band_label = _read(row, 'band_label')
            ordinal = _read(row, 'ordinal', index)
            normalized.append({
                'ordinal': int(ordinal) if ordinal is not None else index,
                'band': _read(row, 'band') or band_label or f'Band {index}',
                'band_label': band_label,
                'open_time': float(open_time) if open_time is not None else None,
                'clear_time': float(clear_time) if clear_time is not None else None,
                'curve_id': _read(row, 'curve_id'),
                'is_default': bool(_read(row, 'is_default')) if not legacy else index == 1,
            })
        return normalized

    def _get_ltd_param(self, ordinal: int):
        """Load LTD param row by ordinal."""
        row = next(
            (param_row for param_row in self._load_ltd_param_rows() if int(param_row['ordinal']) == int(ordinal)),
            None,
        )
        return SimpleNamespace(**row) if row is not None else None

    def _get_ltd_band(self, ordinal: int):
        """Load LTD band row by ordinal."""
        band = next(
            (band_row for band_row in self.get_band_info() if int(band_row['ordinal']) == int(ordinal)),
            None,
        )
        return SimpleNamespace(**band) if band is not None else None

    def _get_min_stdb_time(self, is_clear: bool) -> Optional[float]:
        """Get minimum time from STD band data (open or clear)."""
        time_column = 'clear_time' if is_clear else 'open_time'
        legacy_time_column = 'std_clear' if is_clear else 'std_open'

        try:
            result = self.session.execute(
                text(
                    f"""
                    SELECT MIN({time_column}) AS min_time
                    FROM tcc_etu_std_bands
                    WHERE sensor_id = :sensor_id
                    """
                ),
                {'sensor_id': self.sensor.id},
            ).fetchone()
        except Exception:
            if hasattr(self.session, 'rollback'):
                self.session.rollback()
            result = self.session.execute(
                text(
                    f"""
                    SELECT MIN({legacy_time_column}) AS min_time
                    FROM tcc_etu_std_bands
                    WHERE sensor_id = :sensor_id
                    """
                ),
                {'sensor_id': self.sensor.id},
            ).fetchone()

        if result is None:
            return None
        mapping = result._mapping if hasattr(result, '_mapping') else result
        min_time = mapping.get('min_time')
        return float(min_time) if min_time is not None else None
