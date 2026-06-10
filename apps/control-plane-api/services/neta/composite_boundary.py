"""
Native-faithful composite TCC boundary assembly (G4 §3g).

The native engine (``CPointsMergeSST.MergeSST`` / ``CPointsMergeGF.MergeGF``,
recovered 2026-06-09) draws the breaker characteristic as ONE ordered polyline
per boundary, not as independent per-element traces:

  1. vertical pickup asymptote at the leftmost block's start current
     (``AddLongTimePickup``: two points at the same x, top → curve)
  2. each element block clipped to a current window (``TrimCurveX``) ending
     at the LT→ST handoff — the log-log intersection where the adjacent
     element curves cross (``MergeLines``/``CLogLogIntersection``), else the
     next block's start current
  3. the INST horizontal floor extended to the right edge
  4. open (min-trip) and clear (total-clear) assembled as two separate
     boundaries; the frontend closes them into the classic shaded band
  5. ground fault is a fully separate band with its own GFPU vertical

Serving deviations from native (ratified §209 tiers):
  - right edge = ``RIGHT_EDGE_AMPS`` (the serving sweep default), not the
    study's available short-circuit current (no SC input yet);
  - corner fillets (``AutoAdjustFillet``) skipped — sharp corners;
  - an element with no clear curve (route-1 branches serve open-only)
    reuses its open block for the clear boundary — zero band width there,
    surfaced honestly in ``open_only_elements``.

Pure module: consumes the per-element ``PlotCurve`` list the generator
already serves; no DB access.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

# Native AddLongTimePickup writes the phase pickup vertical from t=1e6;
# the GF vertical uses a 1000 s top anchor (CTccLVBreakerCurveGF).
PHASE_TOP_SECONDS = 1_000_000.0
GF_TOP_SECONDS = 1_000.0

# Right-edge cap. Native clips at the study's available SC amps
# (ClipCurve(GetScAmps)); without a study SC input the band runs to the
# serving sweep default so the INST shelf reaches the plot's right edge.
RIGHT_EDGE_AMPS = 100_000.0

# Element assembly order within the phase band (left to right in current).
_PHASE_ELEMENTS = ("LTD", "STD", "INST")
_GF_ELEMENTS = ("GFD",)

_FLAT_REL_TOL = 1e-9


@dataclass
class CompositeBand:
    """One assembled boundary band (phase or ground-fault family)."""

    id: str
    family: str  # "phase" | "gf"
    open_points: list[tuple[float, float]]
    clear_points: list[tuple[float, float]]
    open_only_elements: list[str] = field(default_factory=list)
    right_edge_amps: float = RIGHT_EDGE_AMPS


def _loglog_time_at(points: list[tuple[float, float]], amps: float) -> Optional[float]:
    """Log-log interpolate the time at ``amps`` on a polyline; None outside."""
    if amps <= 0 or not points:
        return None
    if amps < points[0][0] or amps > points[-1][0]:
        return None
    for (a1, s1), (a2, s2) in zip(points, points[1:]):
        if a1 <= amps <= a2:
            if min(a1, a2, s1, s2) <= 0:
                return None
            la1, la2 = math.log(a1), math.log(a2)
            # Distinct doubles can still have log-equal values at large amps —
            # guard the denominator, not just exact float equality.
            if la1 == la2:
                return s1
            f = (math.log(amps) - la1) / (la2 - la1)
            return math.exp(math.log(s1) + f * (math.log(s2) - math.log(s1)))
    return None


def _clip_to_window(
    points: list[tuple[float, float]], x_start: float, x_end: float
) -> list[tuple[float, float]]:
    """TrimCurveX equivalent: clip a polyline to the current window
    [x_start, x_end], log-log interpolating the boundary points."""
    if x_end <= x_start or not points:
        return []
    mid = [(a, s) for a, s in points if x_start <= a <= x_end]
    out: list[tuple[float, float]] = []
    # Boundary interpolation only when the window edge falls strictly inside a
    # segment — if a data point already sits AT the edge (e.g. a vertical step
    # at the handoff current), appending the interpolated value would retrace
    # the step and zigzag the boundary.
    if points[0][0] < x_start and not (mid and mid[0][0] == x_start):
        t0 = _loglog_time_at(points, x_start)
        if t0 is not None:
            out.append((x_start, t0))
    out.extend(mid)
    if points[-1][0] > x_end and not (mid and mid[-1][0] == x_end):
        t1 = _loglog_time_at(points, x_end)
        if t1 is not None:
            out.append((x_end, t1))
    return out


def _loglog_crossing(
    upper: list[tuple[float, float]],
    lower: list[tuple[float, float]],
    lo: float,
    hi: float,
) -> Optional[float]:
    """First current in [lo, hi] where the two polylines cross in log-log
    space (MergeLines / CLogLogIntersection.SolveWithinConstraints).

    Both polylines are piecewise-linear in log-log space, so the time
    difference is piecewise-linear over the merged breakpoints — a sign
    change brackets an exact linear root."""
    if hi <= lo:
        return None
    xs = sorted(
        {lo, hi}
        | {a for a, _ in upper if lo <= a <= hi}
        | {a for a, _ in lower if lo <= a <= hi}
    )
    prev_x: Optional[float] = None
    prev_d: Optional[float] = None
    for x in xs:
        tu = _loglog_time_at(upper, x)
        tl = _loglog_time_at(lower, x)
        if tu is None or tl is None or tu <= 0 or tl <= 0:
            prev_x, prev_d = None, None
            continue
        d = math.log(tu) - math.log(tl)
        if abs(d) < 1e-12:
            return x
        if prev_d is not None and prev_x is not None and (d > 0) != (prev_d > 0):
            f = prev_d / (prev_d - d)
            lx = math.log(prev_x) + f * (math.log(x) - math.log(prev_x))
            return math.exp(lx)
        prev_x, prev_d = x, d
    return None


def _is_flat_tail(points: list[tuple[float, float]]) -> bool:
    if len(points) < 2:
        return False
    s1, s2 = points[-2][1], points[-1][1]
    if s2 <= 0:
        return False
    return abs(s1 - s2) <= _FLAT_REL_TOL * abs(s2)


def _dedup(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for p in points:
        if not out or out[-1] != p:
            out.append(p)
    return out


def _handoff(
    cur: list[tuple[float, float]], nxt: list[tuple[float, float]]
) -> float:
    """Handoff current between two adjacent element blocks (native MergeSST
    semantics): when the next element already governs at its own pickup —
    its start time is at or below the current curve there, or the current
    curve doesn't reach it — the handoff is the next block's start current
    (the classic vertical drop at the pickup). Only when the next block
    starts ABOVE the current curve does the current element keep governing
    until the curves cross (MergeLines / CLogLogIntersection delay
    priority)."""
    x0 = nxt[0][0]
    t_cur = _loglog_time_at(cur, x0)
    if t_cur is None or nxt[0][1] <= t_cur:
        return x0
    x = _loglog_crossing(cur, nxt, x0, min(cur[-1][0], nxt[-1][0]))
    return x if x is not None else x0


def _assemble_boundary(
    blocks: list[tuple[str, list[tuple[float, float]]]],
    top_seconds: float,
    right_edge: float,
) -> list[tuple[float, float]]:
    """Assemble one ordered boundary polyline from the element blocks.

    ``blocks`` is the ordered (element, points) list, points sorted by amps.
    Each block governs a current region [start_i, end_i): start_0 = the first
    block's data start, start_i = the handoff from the previous block, and
    end_i = the smallest of ALL later region starts — so a downstream element
    whose pickup lands left of an intermediate block (e.g. INST dialed below
    STPU) caps every earlier block at its pickup and empties the bypassed
    block, exactly as the native floor placement at INST amps does.
    """
    blocks = [(e, pts) for e, pts in blocks if pts]
    if not blocks:
        return []

    starts: list[float] = [blocks[0][1][0][0]]
    for (_, cur), (_, nxt) in zip(blocks, blocks[1:]):
        starts.append(_handoff(cur, nxt))

    # Region end = suffix-min of the later region starts (right edge last).
    ends: list[float] = [0.0] * len(blocks)
    suffix_min = right_edge
    for i in range(len(blocks) - 1, -1, -1):
        ends[i] = suffix_min
        suffix_min = min(suffix_min, starts[i])

    out: list[tuple[float, float]] = []
    last_emitted: Optional[tuple[str, list[tuple[float, float]]]] = None
    for i, (element, pts) in enumerate(blocks):
        is_last = i == len(blocks) - 1
        window_start = max(starts[i], pts[0][0])
        window_end = ends[i]
        # A middle block whose data ends short of its window: carry a flat
        # definite-time tail forward to the handoff so the staircase connects.
        if not is_last and pts[-1][0] < window_end and _is_flat_tail(pts):
            pts = pts + [(window_end, pts[-1][1])]
        clipped = _clip_to_window(pts, window_start, window_end)
        if clipped:
            out.extend(clipped)
            last_emitted = (element, clipped)

    if not out:
        return []
    # INST floor (and any flat definite-time tail) runs to the right edge;
    # a ramp tail must not fabricate a shelf.
    if last_emitted is not None:
        element, clipped = last_emitted
        if (element == "INST" or _is_flat_tail(clipped)) and out[-1][0] < right_edge:
            out.append((right_edge, out[-1][1]))
    # Vertical pickup asymptote at the leftmost block's start current.
    out = [(out[0][0], top_seconds)] + out
    return _dedup(out)


def _sorted_points(curve) -> list[tuple[float, float]]:
    return sorted(
        ((p.amps, p.seconds) for p in curve.points if p.amps > 0 and p.seconds > 0),
        key=lambda t: t[0],
    )


def _family_band(
    curves,
    band_id: str,
    family: str,
    elements: tuple[str, ...],
    top_seconds: float,
) -> Optional[CompositeBand]:
    open_blocks: list[tuple[str, list[tuple[float, float]]]] = []
    clear_blocks: list[tuple[str, list[tuple[float, float]]]] = []
    open_only: list[str] = []
    for element in elements:
        open_curve = next(
            (c for c in curves if c.element == element and c.phase == "open"), None
        )
        clear_curve = next(
            (c for c in curves if c.element == element and c.phase == "clear"), None
        )
        if open_curve is None and clear_curve is None:
            continue
        open_pts = _sorted_points(open_curve) if open_curve else []
        clear_pts = _sorted_points(clear_curve) if clear_curve else []
        if open_pts:
            open_blocks.append((element, open_pts))
        if clear_pts:
            clear_blocks.append((element, clear_pts))
        elif open_pts:
            # Route-1 branches serve open-only: reuse the open block so the
            # boundary stays continuous (zero band width — surfaced below).
            clear_blocks.append((element, open_pts))
            open_only.append(element)

    open_boundary = _assemble_boundary(open_blocks, top_seconds, RIGHT_EDGE_AMPS)
    clear_boundary = _assemble_boundary(clear_blocks, top_seconds, RIGHT_EDGE_AMPS)
    if not open_boundary and not clear_boundary:
        return None
    return CompositeBand(
        id=band_id,
        family=family,
        open_points=open_boundary,
        clear_points=clear_boundary,
        open_only_elements=open_only,
        right_edge_amps=RIGHT_EDGE_AMPS,
    )


def assemble_composite_bands(curves) -> list[CompositeBand]:
    """Assemble the composite boundary bands from the served per-element
    curves: a phase band (LTD→STD→INST) and a separate GF band (GFD)."""
    bands: list[CompositeBand] = []
    phase = _family_band(curves, "phase_band", "phase", _PHASE_ELEMENTS, PHASE_TOP_SECONDS)
    if phase is not None:
        bands.append(phase)
    gf = _family_band(curves, "gf_band", "gf", _GF_ELEMENTS, GF_TOP_SECONDS)
    if gf is not None:
        bands.append(gf)
    return bands
