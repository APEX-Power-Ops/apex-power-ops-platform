"""
TMT Curve Generator
===================
Generates smooth Time-Current Characteristic curves for
Thermal-Magnetic Trip (TMT) breakers via Catmull-Rom spline
interpolation in log-log space.

Algorithm:
  1. Load raw control points from tcc_tmt_curves, ordered by time DESC
     (traces the curve from high-time asymptote to low-time end).
  2. If < 4 points: return them directly (no interpolation possible).
  3. If >= 4 points: apply Catmull-Rom spline in log-log space.

Tables:
  tcc_tmt_curves  — raw (current, time) control points per frame/class
  tcc_tmt_frames  — frame size metadata
  tcc_tmt_amps    — available amp ratings per frame
  tcc_tmt_settings — trip settings with tolerance ranges

Usage:
    from config import SessionLocal
    from apex_calc_engine.services.calc_engine.tmt_curves import TMTCurveGenerator

    with SessionLocal() as session:
        gen = TMTCurveGenerator(session, frame_id=1)
        curve = gen.generate_curve(trip_class=0)
        # curve → [TMTCurvePoint(amps=1.09, seconds=9779.63), ...]
"""

import math
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from apex_calc_engine.models.tmt import TMTFrame, TMTCurve, TMTAmp, TMTSetting, TMTThermalAdj


@dataclass
class TMTCurvePoint:
    """One (current, time) point on a TMT TCC curve."""
    amps: float
    seconds: float


class TMTCurveGenerator:
    """
    Generates interpolated TCC curves for TMT (Thermal-Magnetic Trip)
    breakers using Catmull-Rom spline interpolation in log-log space.
    """

    POINTS_PER_SEGMENT = 20

    def __init__(self, session: Session, frame_id: int):
        self.session = session
        self.frame: TMTFrame = (
            session.query(TMTFrame)
            .filter(TMTFrame.id == frame_id)
            .one()
        )

    def generate_curve(
        self,
        trip_class: int,
        num_output_points: Optional[int] = None,
    ) -> list[TMTCurvePoint]:
        """
        Generate interpolated TMT curve for a given trip class.

        Args:
            trip_class: Curve class (maps to TMTCurve.class_ column).
            num_output_points: Desired output density. Default is
                               POINTS_PER_SEGMENT × number of segments.

        Returns:
            List of TMTCurvePoint ordered from high-time to low-time
            (top to bottom on a TCC chart).
        """
        raw = self._load_raw_points(trip_class)

        if len(raw) < 4:
            return [TMTCurvePoint(amps=p[0], seconds=p[1]) for p in raw]

        n_out = num_output_points or (len(raw) - 1) * self.POINTS_PER_SEGMENT
        interpolated = _catmull_rom_log(raw, n_out)

        return [
            TMTCurvePoint(amps=round(p[0], 4), seconds=round(p[1], 6))
            for p in interpolated
        ]

    # ------------------------------------------------------------------
    # Convenience queries
    # ------------------------------------------------------------------

    def get_raw_points(self, trip_class: int) -> list[TMTCurvePoint]:
        """Return the un-interpolated control points."""
        raw = self._load_raw_points(trip_class)
        return [TMTCurvePoint(amps=p[0], seconds=p[1]) for p in raw]

    def get_available_classes(self) -> list[int]:
        """Return distinct trip classes for this frame."""
        from sqlalchemy import distinct

        rows = (
            self.session.query(distinct(TMTCurve.class_))
            .filter_by(frame_id=self.frame.id)
            .order_by(TMTCurve.class_)
            .all()
        )
        return [r[0] for r in rows]

    def get_settings(self) -> list[dict]:
        """Get trip settings (with tolerance ranges) for this frame."""
        rows = (
            self.session.query(TMTSetting)
            .filter_by(frame_id=self.frame.id)
            .order_by(TMTSetting.value)
            .all()
        )
        return [
            {
                'value': float(r.value) if r.value is not None else None,
                'label': r.label,
                'tol_lo': float(r.tol_lo) if r.tol_lo is not None else None,
                'tol_hi': float(r.tol_hi) if r.tol_hi is not None else None,
            }
            for r in rows
        ]

    def get_amps(self) -> list[dict]:
        """Get available amp ratings for this frame."""
        rows = (
            self.session.query(TMTAmp)
            .filter_by(frame_id=self.frame.id)
            .order_by(TMTAmp.rating)
            .all()
        )
        return [
            {
                'rating': float(r.rating),
                'max_override': float(r.max_override) if r.max_override is not None else None,
            }
            for r in rows
        ]

    def get_thermal_adjustments(self) -> list[float]:
        """Thermal adjustment factors for this frame."""
        rows = (
            self.session.query(TMTThermalAdj)
            .filter_by(frame_id=self.frame.id)
            .all()
        )
        return [float(r.adjustment) for r in rows if r.adjustment is not None]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_raw_points(self, trip_class: int) -> list[tuple[float, float]]:
        """Load raw control points ordered by time DESC (curve path order)."""
        rows = (
            self.session.query(TMTCurve)
            .filter_by(frame_id=self.frame.id, class_=trip_class)
            .order_by(TMTCurve.time_sec.desc())
            .all()
        )
        return [(float(r.current_amp), float(r.time_sec)) for r in rows]


# ======================================================================
# Catmull-Rom spline (pure Python, no numpy)
# ======================================================================

def _catmull_rom_log(
    points: list[tuple[float, float]],
    num_output: int,
) -> list[tuple[float, float]]:
    """
    Catmull-Rom spline interpolation in log-log space.

    Converts (current, time) to (log10(current), log10(time)),
    runs the spline, then converts back.  Log-log is the natural
    coordinate system for TCC curves spanning many decades.
    """
    # Filter to positive values (required for log)
    valid = [(x, y) for x, y in points if x > 0 and y > 0]
    if len(valid) < 4:
        return valid

    log_pts = [(math.log10(x), math.log10(y)) for x, y in valid]
    interpolated = _catmull_rom_spline(log_pts, num_output)

    return [(10 ** lx, 10 ** ly) for lx, ly in interpolated]


def _catmull_rom_spline(
    points: list[tuple[float, float]],
    num_output: int,
) -> list[tuple[float, float]]:
    """
    Uniform Catmull-Rom spline through control points.

    Uses phantom-point padding at the start and end, and the standard
    basis-matrix formulation:

        q(t) = 0.5 × ( (2·P1)
                      + (-P0 + P2) · t
                      + (2·P0 - 5·P1 + 4·P2 - P3) · t²
                      + (-P0 + 3·P1 - 3·P2 + P3) · t³ )

    Both x and y are interpolated parametrically (the curve need not be
    monotonic in either dimension).
    """
    n = len(points)
    if n < 4:
        return list(points)

    # Phantom-point padding (reflection across first/last point)
    p_start = (2 * points[0][0] - points[1][0],
               2 * points[0][1] - points[1][1])
    p_end = (2 * points[-1][0] - points[-2][0],
             2 * points[-1][1] - points[-2][1])
    padded = [p_start] + list(points) + [p_end]

    segments = len(padded) - 3          # == n original points - 1
    pts_per_seg = max(2, num_output // segments)

    result: list[tuple[float, float]] = []

    for i in range(segments):
        p0 = padded[i]
        p1 = padded[i + 1]
        p2 = padded[i + 2]
        p3 = padded[i + 3]

        for j in range(pts_per_seg):
            # Skip first point of each segment after the first to
            # avoid duplicating the junction between segments.
            if i > 0 and j == 0:
                continue

            t = j / (pts_per_seg - 1) if pts_per_seg > 1 else 0.0
            t2 = t * t
            t3 = t2 * t

            x = 0.5 * (
                (2 * p1[0])
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                (2 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )

            result.append((x, y))

    return result


# ======================================================================
# Fillet utility (used by etu_merge.py at curve transitions)
# ======================================================================

def fillet(
    p_before: tuple[float, float],
    p_corner: tuple[float, float],
    p_after: tuple[float, float],
    radius: float = 0.09,
    num_points: int = 25,
) -> list[tuple[float, float]]:
    """
    Create a fillet (rounded corner) at *p_corner* in log-log space.

    Computes tangent points at *radius* distance (in log-decades) along
    each incoming/outgoing direction, then sweeps a quadratic Bézier
    from one tangent through the corner region to the other tangent.

    Args:
        p_before: (amps, seconds) — last point on incoming segment.
        p_corner: (amps, seconds) — the corner to round.
        p_after:  (amps, seconds) — first point on outgoing segment.
        radius:   Fillet size in log-decades (0.09 is the standard).
        num_points: Number of interpolation points on the arc.

    Returns:
        List of (amps, seconds) tracing the fillet arc.
    """
    # Work in log-log space
    lb = (_safe_log10(p_before[0]), _safe_log10(p_before[1]))
    lc = (_safe_log10(p_corner[0]), _safe_log10(p_corner[1]))
    la = (_safe_log10(p_after[0]), _safe_log10(p_after[1]))

    # Vectors from corner to before / after
    vb = (lb[0] - lc[0], lb[1] - lc[1])
    va = (la[0] - lc[0], la[1] - lc[1])

    len_b = math.hypot(vb[0], vb[1])
    len_a = math.hypot(va[0], va[1])

    if len_b < 1e-12 or len_a < 1e-12:
        return [p_corner]

    # Unit vectors
    ub = (vb[0] / len_b, vb[1] / len_b)
    ua = (va[0] / len_a, va[1] / len_a)

    # Clamp radius so tangent points don't overshoot halfway
    r = min(radius, len_b * 0.5, len_a * 0.5)

    # Tangent points
    tb = (lc[0] + ub[0] * r, lc[1] + ub[1] * r)
    ta = (lc[0] + ua[0] * r, lc[1] + ua[1] * r)

    # Quadratic Bézier: B(t) = (1-t)²·P0 + 2(1-t)t·P1 + t²·P2
    result: list[tuple[float, float]] = []
    for i in range(num_points):
        t = i / (num_points - 1) if num_points > 1 else 0.0
        omt = 1.0 - t
        lx = omt * omt * tb[0] + 2 * omt * t * lc[0] + t * t * ta[0]
        ly = omt * omt * tb[1] + 2 * omt * t * lc[1] + t * t * ta[1]
        result.append((10 ** lx, 10 ** ly))

    return result


def _safe_log10(v: float) -> float:
    """log10 with floor clamp to avoid domain errors."""
    return math.log10(max(v, 1e-30))
