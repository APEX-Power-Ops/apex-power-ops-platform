"""
ETU Curve Merge Engine
======================
Merges individual protection-element curves (LTD, STD, INST, Override)
into a single composite TCC curve.

Dispatch variants (Section 6.1 of CALC_ENGINE_SPEC):
  LT only         — LTD curve alone
  LT + INST       — LTD → INST with fillet at transition
  LT + OVR        — LTD → Override
  LT + ST         — LTD → STD (with delay-priority sub-variants)
  LT + ST + INST  — LTD → STD → INST (most common case)
  ST + OVR        — STD → Override

Core algorithm:
  MergeLines finds the log-log intersection of two curve segments,
  truncates the first curve at that point, and splices the second.

Usage:
    from apex_calc_engine.services.calc_engine.etu_merge import merge_sst_curves

    merged = merge_sst_curves(
        ltpu=480.0, stpu=1920.0, inst=6000.0, ovrd=0,
        ltd_curve=[(480, 100), (600, 50), ...],
        std_curve=[(1920, 10), (2400, 5), ...],
        inst_curve=[(6000, 0.05), (100000, 0.05)],
        ovrd_curve=[],
    )
"""

import math
from typing import Optional

from apex_calc_engine.services.calc_engine.tmt_curves import fillet as _fillet

# Sentinel value used in C# source to indicate "not present"
SENTINEL = 3.12345e38

# Standard fillet parameters
FILLET_INST = 0.09
FILLET_POINTS = 25

# Type alias for curve data
Curve = list[tuple[float, float]]  # [(amps, seconds), ...]


# ======================================================================
# Public API
# ======================================================================

def merge_sst_curves(
    ltpu: float,
    stpu: float,
    inst: float,
    ovrd: float,
    ltd_curve: Curve,
    std_curve: Curve,
    inst_curve: Curve,
    ovrd_curve: Curve,
    fillet_inst: float = FILLET_INST,
    is_clearing: bool = False,
    max_amps: float = 100000.0,
    delay_priority: Optional[str] = None,
) -> Curve:
    """
    Merge protection-element curves into a single TCC curve.

    Args:
        ltpu, stpu, inst, ovrd:
            Pickup currents.  0, SENTINEL, or None means "element absent".
        ltd_curve, std_curve, inst_curve, ovrd_curve:
            Individual element curves — each is [(amps, seconds)] sorted
            by ascending current.
        fillet_inst:  Fillet radius (log-decades) for the INST transition.
        is_clearing:  True → clearing curve (reverses output order).
        max_amps:     Maximum current for the composite curve.
        delay_priority:
            For LT+ST / LT+ST+INST merges: None | 'LT' | 'ST' | 'Min'.

    Returns:
        Composite [(amps, seconds)] curve.
    """
    has_stpu = _element_present(stpu)
    has_inst = _element_present(inst)
    has_ovrd = _element_present(ovrd)

    if not has_stpu:
        if not has_inst:
            if has_ovrd:
                result = _merge_lt_ovr(ltd_curve, ovrd_curve, max_amps)
            else:
                result = _merge_lt_only(ltd_curve)
        else:
            result = _merge_lt_inst(
                ltd_curve, inst_curve, max_amps, fillet_inst,
            )
    elif not has_inst:
        result = _merge_lt_st(
            ltd_curve, std_curve, max_amps, delay_priority,
        )
    else:
        result = _merge_lt_st_inst(
            ltd_curve, std_curve, inst_curve,
            max_amps, fillet_inst, delay_priority,
        )

    if is_clearing:
        result = list(reversed(result))

    return result


# ======================================================================
# Merge variants
# ======================================================================

def _merge_lt_only(ltd_curve: Curve) -> Curve:
    """LTD curve alone — nothing to merge."""
    return list(ltd_curve)


def _merge_lt_inst(
    ltd_curve: Curve,
    inst_curve: Curve,
    max_amps: float,
    fillet_radius: float,
) -> Curve:
    """LTD → INST.  Splice at intersection, fillet at the transition."""
    if not ltd_curve:
        return list(inst_curve)
    if not inst_curve:
        return list(ltd_curve)

    splice = _merge_lines(ltd_curve, inst_curve, max_amps)
    if splice is None:
        # No intersection — use dominant curve logic
        return _no_intersect_merge(ltd_curve, inst_curve)

    merged, splice_idx = splice
    tail = inst_curve[splice_idx:]

    if fillet_radius > 0 and len(merged) >= 1 and len(tail) >= 1:
        f = _fillet(
            merged[-2] if len(merged) >= 2 else merged[-1],
            merged[-1],
            tail[0],
            radius=fillet_radius,
            num_points=FILLET_POINTS,
        )
        return merged[:-1] + f + tail
    else:
        return merged + tail


def _merge_lt_ovr(
    ltd_curve: Curve,
    ovrd_curve: Curve,
    max_amps: float,
) -> Curve:
    """LTD → Override.  Direct splice at intersection."""
    if not ltd_curve:
        return list(ovrd_curve)
    if not ovrd_curve:
        return list(ltd_curve)

    splice = _merge_lines(ltd_curve, ovrd_curve, max_amps)
    if splice is None:
        return _no_intersect_merge(ltd_curve, ovrd_curve)
    merged, idx = splice
    return merged + ovrd_curve[idx:]


def _merge_lt_st(
    ltd_curve: Curve,
    std_curve: Curve,
    max_amps: float,
    delay_priority: Optional[str],
) -> Curve:
    """LTD → STD with delay-priority handling."""
    if not ltd_curve:
        return list(std_curve)
    if not std_curve:
        return list(ltd_curve)

    if delay_priority == 'LT':
        return _merge_priority_lt(ltd_curve, std_curve, max_amps)
    elif delay_priority == 'ST':
        return _merge_priority_st(ltd_curve, std_curve, max_amps)
    elif delay_priority == 'Min':
        return _merge_priority_min(ltd_curve, std_curve, max_amps)
    else:
        # default: fastest trip wins (lower time)
        return _merge_priority_none(ltd_curve, std_curve, max_amps)


def _merge_lt_st_inst(
    ltd_curve: Curve,
    std_curve: Curve,
    inst_curve: Curve,
    max_amps: float,
    fillet_radius: float,
    delay_priority: Optional[str],
) -> Curve:
    """LTD → STD → INST.  Most common case for ETU breakers."""
    # First merge LTD + STD
    lt_st = _merge_lt_st(ltd_curve, std_curve, max_amps, delay_priority)

    # Then merge the result with INST
    return _merge_lt_inst(lt_st, inst_curve, max_amps, fillet_radius)


# ======================================================================
# Delay-priority sub-variants
# ======================================================================

def _merge_priority_none(
    curve1: Curve, curve2: Curve, max_amps: float,
) -> Curve:
    """Default: use whichever gives the faster (lower) trip time."""
    splice = _merge_lines(curve1, curve2, max_amps)
    if splice is None:
        # No intersection — determine which is faster in the overlap region
        # and return the dominant curve, appending the other only if it
        # extends beyond
        return _no_intersect_merge(curve1, curve2)
    merged, idx = splice
    return merged + curve2[idx:]


def _merge_priority_lt(
    ltd_curve: Curve, std_curve: Curve, max_amps: float,
) -> Curve:
    """LTD takes priority — use LTD in the overlap region."""
    splice = _merge_lines(ltd_curve, std_curve, max_amps)
    if splice is None:
        return _no_intersect_merge(ltd_curve, std_curve)
    merged, idx = splice
    # Extend LTD through overlap, then switch to STD
    return merged + std_curve[idx:]


def _merge_priority_st(
    ltd_curve: Curve, std_curve: Curve, max_amps: float,
) -> Curve:
    """STD takes priority — switch to STD at first overlap."""
    splice = _merge_lines(std_curve, ltd_curve, max_amps)
    if splice is not None:
        merged, idx = splice
        return ltd_curve[:idx] + merged
    return _no_intersect_merge(ltd_curve, std_curve)


def _merge_priority_min(
    curve1: Curve, curve2: Curve, max_amps: float,
) -> Curve:
    """Use minimum trip time at each current point."""
    if not curve1:
        return list(curve2)
    if not curve2:
        return list(curve1)

    # Build a combined set of current values
    all_amps = sorted(set(a for a, _ in curve1) | set(a for a, _ in curve2))

    result: Curve = []
    for amps in all_amps:
        if amps > max_amps:
            break
        t1 = _interpolate_time(curve1, amps)
        t2 = _interpolate_time(curve2, amps)

        if t1 is not None and t2 is not None:
            result.append((amps, min(t1, t2)))
        elif t1 is not None:
            result.append((amps, t1))
        elif t2 is not None:
            result.append((amps, t2))

    return result


def _no_intersect_merge(curve1: Curve, curve2: Curve) -> Curve:
    """
    When two curves don't intersect, keep curve1 up to where curve2
    starts, then use whichever is faster (lower time) point-by-point,
    and append any tail from whichever curve extends further.
    """
    if not curve2:
        return list(curve1)
    if not curve1:
        return list(curve2)

    c2_start = curve2[0][0]
    c2_end = curve2[-1][0]
    c1_end = curve1[-1][0]

    # Determine overlap region
    overlap_lo = max(curve1[0][0], c2_start)
    overlap_hi = min(c1_end, c2_end)

    if overlap_lo > overlap_hi:
        # No overlap in current range — sequential concatenation
        if c2_start >= c1_end:
            return list(curve1) + list(curve2)
        else:
            return list(curve2) + list(curve1)

    # Check which is faster in the overlap
    mid = (overlap_lo * overlap_hi) ** 0.5 if overlap_lo < overlap_hi else overlap_lo
    t1 = _interpolate_time(curve1, mid)
    t2 = _interpolate_time(curve2, mid)

    if t1 is not None and t2 is not None and t1 <= t2:
        # curve1 is faster — keep curve1, then append curve2 points
        # beyond curve1's range
        result = list(curve1)
        for a, t in curve2:
            if a > c1_end:
                result.append((a, t))
        return result
    elif t1 is not None and t2 is not None:
        # curve2 is faster in overlap — keep curve1 points before overlap,
        # then curve2
        result = [(a, t) for a, t in curve1 if a < c2_start]
        result.extend(curve2)
        return result
    else:
        # Can't determine — curve1 then curve2 if sequential
        if c2_start >= c1_end:
            return list(curve1) + list(curve2)
        return list(curve1)


# ======================================================================
# Core merge algorithm
# ======================================================================

def _merge_lines(
    curve1: Curve,
    curve2: Curve,
    max_amps: float,
) -> Optional[tuple[Curve, int]]:
    """
    Find where curve1 and curve2 intersect in log-log space, then splice.

    Returns:
        (truncated_curve1_with_intersection, splice_index_in_curve2)
        or None if no intersection found.
    """
    if len(curve1) < 2 or len(curve2) < 2:
        return None

    for i in range(1, len(curve1)):
        seg1 = (curve1[i - 1], curve1[i])

        for j in range(1, len(curve2)):
            seg2 = (curve2[j - 1], curve2[j])

            ix = log_log_intersect(seg1, seg2)
            if ix is None:
                continue

            if _point_in_bounds(ix, seg1, seg2, tolerance=0.01):
                # Truncate curve1 at intersection, return splice index
                truncated = list(curve1[:i]) + [ix]
                return (truncated, j)

    return None


# ======================================================================
# Geometry helpers (log-log space)
# ======================================================================

def log_log_intersect(
    seg1: tuple[tuple[float, float], tuple[float, float]],
    seg2: tuple[tuple[float, float], tuple[float, float]],
) -> Optional[tuple[float, float]]:
    """
    Find intersection of two line segments in log-log space.

    Each segment is ((x1, y1), (x2, y2)) in linear (amps, seconds).
    Returns (amps, seconds) in linear space, or None.
    """
    if any(v <= 0 for pt in (seg1[0], seg1[1], seg2[0], seg2[1]) for v in pt):
        return None

    lx1, ly1 = math.log10(seg1[0][0]), math.log10(seg1[0][1])
    lx2, ly2 = math.log10(seg1[1][0]), math.log10(seg1[1][1])
    lx3, ly3 = math.log10(seg2[0][0]), math.log10(seg2[0][1])
    lx4, ly4 = math.log10(seg2[1][0]), math.log10(seg2[1][1])

    denom = (lx1 - lx2) * (ly3 - ly4) - (ly1 - ly2) * (lx3 - lx4)
    if abs(denom) < 1e-12:
        return None  # Parallel / collinear

    t = ((lx1 - lx3) * (ly3 - ly4) - (ly1 - ly3) * (lx3 - lx4)) / denom
    lx = lx1 + t * (lx2 - lx1)
    ly = ly1 + t * (ly2 - ly1)

    # Guard against overflow when segments are near-parallel
    if abs(lx) > 300 or abs(ly) > 300:
        return None

    return (10 ** lx, 10 ** ly)


def _point_in_bounds(
    pt: tuple[float, float],
    seg1: tuple[tuple[float, float], tuple[float, float]],
    seg2: tuple[tuple[float, float], tuple[float, float]],
    tolerance: float = 0.01,
) -> bool:
    """Check that intersection point lies within both segments (with tolerance)."""
    x, y = pt
    for seg in (seg1, seg2):
        x_lo = min(seg[0][0], seg[1][0])
        x_hi = max(seg[0][0], seg[1][0])
        y_lo = min(seg[0][1], seg[1][1])
        y_hi = max(seg[0][1], seg[1][1])

        # Allow tolerance in log-space
        x_range = max(x_hi - x_lo, 1e-12)
        y_range = max(y_hi - y_lo, 1e-12)

        if (x < x_lo - tolerance * x_range
                or x > x_hi + tolerance * x_range):
            return False
        if (y < y_lo - tolerance * y_range
                or y > y_hi + tolerance * y_range):
            return False

    return True


def _interpolate_time(curve: Curve, amps: float) -> Optional[float]:
    """Linear interpolation in log-log space to find time at given amps."""
    if not curve:
        return None

    # Exact or boundary match
    if amps <= curve[0][0]:
        return curve[0][1]
    if amps >= curve[-1][0]:
        return curve[-1][1]

    for i in range(1, len(curve)):
        if curve[i][0] >= amps:
            a0, t0 = curve[i - 1]
            a1, t1 = curve[i]

            if a0 <= 0 or a1 <= 0 or t0 <= 0 or t1 <= 0:
                return t0  # Fallback linear

            if abs(a1 - a0) < 1e-12:
                return t0

            # Log-log interpolation
            la0, lt0 = math.log10(a0), math.log10(t0)
            la1, lt1 = math.log10(a1), math.log10(t1)
            la = math.log10(amps)

            frac = (la - la0) / (la1 - la0)
            lt = lt0 + frac * (lt1 - lt0)
            return 10 ** lt

    return None


def _element_present(value: Optional[float]) -> bool:
    """Check whether a pickup value indicates an active element."""
    if value is None:
        return False
    if value == 0:
        return False
    if abs(value - SENTINEL) < 1.0:
        return False
    return True
