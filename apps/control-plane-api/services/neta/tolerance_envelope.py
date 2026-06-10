"""
Field-acceptance tolerance envelope (#124, operator-ratified 2026-06-10).

The #122/#123 composite band is the manufacturer's PUBLISHED curve pair
(min-trip / total-clear). The envelope is a different surface: the
field-acceptance corridor — where a measured (current, time) may legitimately
land under the per-sensor manufacturer tolerances that Screen 2 / the plot
whiskers already grade against (G4 §2: authoritative per-sensor DATA).

Ratified semantics:
  - PU tolerance shifts the AMPS axis for every participating element.
    Every served curve shape is multiplicative in current (power-law ramps,
    flat floors, pickup verticals), so scaling the polyline's amps by
    (1 + tol/100) IS the pickup-shifted curve exactly.
  - Time tolerance widens the SECONDS axis only in acceptance-window mode
    (LTD: the §111 reference-window law ``nominal·(1+tol/100)`` around the
    OPEN curve — both envelope edges derive from OPEN; the published clear
    never leaks in, keeping the envelope identical to the grading surface).
  - Published-band mode (STD / INST / GFD): the published open/clear window
    IS the manufacturer's time acceptance — amps shift only. A missing clear
    curve degrades honestly (max edge reuses open, surfaced in
    ``open_only_elements``).
  - No basis / withheld element → NO envelope segment, surfaced in
    ``no_envelope_elements`` (fabricating a zero-tolerance corridor would
    read as a tighter acceptance than certified).

Pure module: transforms the served per-element ``PlotCurve`` objects and
reassembles boundaries through the #122 composite assembler (DURABLE 33:
serving choices become band geometry — this is the serving layer).
"""

from dataclasses import dataclass, field
from typing import Optional

from .composite_boundary import (
    RIGHT_EDGE_AMPS,
    _clip_to_window,
    assemble_composite_bands,
)

# time_source values that mean "acceptance window around the OPEN curve"
# (a real or flagged time tolerance applies multiplicatively to seconds).
ACCEPTANCE_WINDOW_SOURCES = ("ltd_curve_tol", "ltd_generic_estimate")
# time_source value meaning "the published open/clear pair is the window".
PUBLISHED_BAND_SOURCE = "published_band"

_PHASE_ELEMENTS = ("LTD", "STD", "INST")
_GF_ELEMENTS = ("GFD",)


@dataclass
class ElementEnvelopeBasis:
    """Per-element tolerance basis, derived from the SAME served acceptance
    surfaces the whiskers use (marker pickup limits / delay table rows) so the
    envelope and the whiskers cannot drift apart."""

    element: str  # "LTD" | "STD" | "INST" | "GFD"
    pu_tol_lo_pct: Optional[float] = None  # signed %, e.g. -10.0
    pu_tol_hi_pct: Optional[float] = None
    time_tol_lo_pct: Optional[float] = None
    time_tol_hi_pct: Optional[float] = None
    pu_source: Optional[str] = None  # "db_sensor_tolerance"
    time_source: Optional[str] = None  # ACCEPTANCE_WINDOW_SOURCES | "published_band"
    estimated: bool = False  # True only for the flagged generic fallback


@dataclass
class EnvelopeBand:
    """One assembled acceptance-envelope band (phase or gf family)."""

    id: str  # "phase_envelope" | "gf_envelope"
    family: str  # "phase" | "gf"
    min_points: list[tuple[float, float]]
    max_points: list[tuple[float, float]]
    element_basis: list[ElementEnvelopeBasis] = field(default_factory=list)
    open_only_elements: list[str] = field(default_factory=list)
    no_envelope_elements: list[str] = field(default_factory=list)
    right_edge_amps: float = RIGHT_EDGE_AMPS


@dataclass
class _Pt:
    amps: float
    seconds: float


@dataclass
class _Curve:
    """Lightweight PlotCurve stand-in accepted by the composite assembler."""

    id: str
    element: str
    phase: str
    points: list


def _scale(points, amps_factor: float, secs_factor: float = 1.0) -> list[_Pt]:
    return [_Pt(p.amps * amps_factor, p.seconds * secs_factor) for p in points]


def _factor(pct: Optional[float]) -> Optional[float]:
    if pct is None:
        return None
    f = 1.0 + float(pct) / 100.0
    return f if f > 0 else None


def _family_envelope(
    curves,
    family: str,
    elements: tuple[str, ...],
    basis_by_element,
) -> Optional[EnvelopeBand]:
    # (basis, published start amps, min curve, max curve) per included element.
    blocks: list[tuple[ElementEnvelopeBasis, float, _Curve, _Curve]] = []
    open_only: list[str] = []
    no_envelope: list[str] = []
    # Published region-start currents of served-but-uncertified elements —
    # feeds the truncation law below.
    excluded_starts: list[float] = []

    for element in elements:
        open_curve = next(
            (c for c in curves if c.element == element and c.phase == "open"), None
        )
        if open_curve is None or not open_curve.points:
            continue
        clear_curve = next(
            (c for c in curves if c.element == element and c.phase == "clear"), None
        )
        start_amps = min(p.amps for p in open_curve.points)

        basis = basis_by_element.get(element)
        pu_lo = _factor(basis.pu_tol_lo_pct) if basis else None
        pu_hi = _factor(basis.pu_tol_hi_pct) if basis else None
        if basis is None or pu_lo is None or pu_hi is None:
            no_envelope.append(element)
            excluded_starts.append(start_amps)
            continue

        if basis.time_source in ACCEPTANCE_WINDOW_SOURCES:
            # Acceptance window around the OPEN curve (the grading law):
            # both edges derive from open; published clear never leaks in.
            t_lo = _factor(basis.time_tol_lo_pct)
            t_hi = _factor(basis.time_tol_hi_pct)
            if t_lo is None or t_hi is None:
                no_envelope.append(element)
                excluded_starts.append(start_amps)
                continue
            min_pts = _scale(open_curve.points, pu_lo, t_lo)
            max_pts = _scale(open_curve.points, pu_hi, t_hi)
        elif basis.time_source == PUBLISHED_BAND_SOURCE:
            # The published open/clear pair IS the mfr time window: amps
            # shift only. Missing clear → max reuses open (honest, flagged).
            min_pts = _scale(open_curve.points, pu_lo)
            if clear_curve is not None and clear_curve.points:
                max_src = clear_curve.points
            else:
                max_src = open_curve.points
                open_only.append(element)
            max_pts = _scale(max_src, pu_hi)
        else:
            no_envelope.append(element)
            excluded_starts.append(start_amps)
            continue

        key = element.lower()
        blocks.append((
            basis,
            start_amps,
            _Curve(f"{key}_env_min", element, "open", min_pts),
            _Curve(f"{key}_env_max", element, "clear", max_pts),
        ))

    if not blocks:
        return None

    # Truncation law (#124 review): the corridor must never SPAN the region
    # of a served-but-uncertified element — the assembler's region laws
    # (suffix-min ends, flat-tail/right-edge extension) would otherwise
    # chord or extend fabricated geometry across it. A LEADING withhold
    # degrades naturally (the corridor starts at the next certified block);
    # a middle/last withhold cuts the corridor at that element's published
    # region start. Certified blocks lying entirely at/beyond the cut are
    # not drawn and are surfaced as withheld-from-the-corridor too.
    first_included = min(s for _, s, _, _ in blocks)
    later_excluded = [s for s in excluded_starts if s > first_included]
    cut: Optional[float] = min(later_excluded) if later_excluded else None
    if cut is not None:
        no_envelope.extend(b.element for b, s, _, _ in blocks if s >= cut)
        blocks = [t for t in blocks if t[1] < cut]
        open_only = [e for e in open_only if any(b.element == e for b, _, _, _ in blocks)]

    assembled = assemble_composite_bands(
        [mn for _, _, mn, _ in blocks] + [mx for _, _, _, mx in blocks]
    )
    band = next((b for b in assembled if b.family == family), None)
    if band is None or (not band.open_points and not band.clear_points):
        return None

    min_points = band.open_points
    max_points = band.clear_points
    right_edge = band.right_edge_amps
    if cut is not None:
        min_points = _clip_to_window(
            min_points, min(p[0] for p in min_points), cut
        ) if min_points else []
        max_points = _clip_to_window(
            max_points, min(p[0] for p in max_points), cut
        ) if max_points else []
        right_edge = cut

    return EnvelopeBand(
        id=f"{family}_envelope",
        family=family,
        min_points=min_points,
        max_points=max_points,
        element_basis=[b for b, _, _, _ in blocks],
        open_only_elements=open_only,
        no_envelope_elements=no_envelope,
        right_edge_amps=right_edge,
    )


def assemble_envelope_bands(curves, basis_by_element) -> list[EnvelopeBand]:
    """Assemble the acceptance-envelope bands from the served per-element
    curves and the per-element tolerance bases: a phase envelope
    (LTD→STD→INST) and a separate GF envelope (GFD), mirroring the #122
    composite families. ``basis_by_element`` maps element name → basis (or
    None); elements with served curves but no usable basis are surfaced in
    ``no_envelope_elements``."""
    bands: list[EnvelopeBand] = []
    phase = _family_envelope(curves, "phase", _PHASE_ELEMENTS, basis_by_element)
    if phase is not None:
        bands.append(phase)
    gf = _family_envelope(curves, "gf", _GF_ELEMENTS, basis_by_element)
    if gf is not None:
        bands.append(gf)
    return bands
