"""
Unit tests for services.neta.tolerance_envelope (#124, the tolerance-envelope lane).

The envelope is the field-acceptance corridor: the served per-element open/clear
curves transformed by the SAME tolerance bases the Screen-2/Screen-3 acceptance
surfaces use (PU tolerance on the amps axis for every element; time tolerance
only where a real basis exists — LTD's reference-window tolerance), then
assembled into min/max boundaries through the #122 composite assembler.

Laws under test (operator-ratified 2026-06-10):
  - PU-shift on the amps axis for ALL participating elements (PROVEN data).
  - Time-widening ONLY in acceptance-window mode (LTD); published-band elements
    (STD/INST/GFD) keep their published open/clear times.
  - No basis (or withheld) → NO envelope for that element, surfaced honestly.
  - Acceptance-window mode derives BOTH edges from the OPEN curve (the grading
    law: nominal·(1+tol) around the trip curve), never from the published clear.
"""

import os
import sys
from dataclasses import dataclass

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neta.tolerance_envelope import (
    ElementEnvelopeBasis,
    assemble_envelope_bands,
)


@dataclass
class _Pt:
    amps: float
    seconds: float


@dataclass
class _Curve:
    id: str
    element: str
    phase: str
    points: list


def _curve(cid, element, phase, pts):
    return _Curve(cid, element, phase, [_Pt(a, s) for a, s in pts])


def _ltpu_basis(time_source="ltd_curve_tol", t_lo=-26.83, t_hi=0.0,
                pu_lo=-10.0, pu_hi=10.0, estimated=False):
    return ElementEnvelopeBasis(
        element="LTD",
        pu_tol_lo_pct=pu_lo, pu_tol_hi_pct=pu_hi,
        time_tol_lo_pct=t_lo, time_tol_hi_pct=t_hi,
        pu_source="db_sensor_tolerance",
        time_source=time_source,
        estimated=estimated,
    )


def _published_basis(element, pu_lo=-10.0, pu_hi=10.0):
    return ElementEnvelopeBasis(
        element=element,
        pu_tol_lo_pct=pu_lo, pu_tol_hi_pct=pu_hi,
        pu_source="db_sensor_tolerance",
        time_source="published_band",
    )


# A simple LTD ramp: starts at the LTPU vertical region (1000 A), I²t-ish decay.
LTD_OPEN = [(1000.0, 100.0), (2000.0, 25.0), (6000.0, 2.78)]
# STD flat band with a clear edge above it; starts at STPU 4000 A.
STD_OPEN = [(4000.0, 0.2), (20000.0, 0.2)]
STD_CLEAR = [(4000.0, 0.3), (20000.0, 0.3)]
# INST vertical + floor pair at 18 kA.
INST_OPEN = [(18000.0, 0.02), (100000.0, 0.02)]
INST_CLEAR = [(18000.0, 0.05), (100000.0, 0.05)]
# GFD flat band at 480 A pickup.
GFD_OPEN = [(480.0, 0.14), (10000.0, 0.14)]
GFD_CLEAR = [(480.0, 0.2), (10000.0, 0.2)]


def _phase_curves():
    return [
        _curve("ltd_open", "LTD", "open", LTD_OPEN),
        _curve("std_open", "STD", "open", STD_OPEN),
        _curve("std_clear", "STD", "clear", STD_CLEAR),
        _curve("inst_open", "INST", "open", INST_OPEN),
        _curve("inst_clear", "INST", "clear", INST_CLEAR),
    ]


def _gf_curves():
    return [
        _curve("gfd_open", "GFD", "open", GFD_OPEN),
        _curve("gfd_clear", "GFD", "clear", GFD_CLEAR),
    ]


def _basis_map(**overrides):
    base = {
        "LTD": _ltpu_basis(),
        "STD": _published_basis("STD"),
        "INST": _published_basis("INST", pu_lo=-20.0, pu_hi=20.0),
        "GFD": _published_basis("GFD", pu_lo=-15.0, pu_hi=15.0),
    }
    base.update(overrides)
    return base


def _seg_seconds(points, amps, default=None):
    """Curve time at an exact amps breakpoint (no interpolation). A pickup
    vertical stacks the top asymptote at the same amps as the first data
    point — the curve value is the smallest seconds at that breakpoint."""
    matches = [p[1] for p in points if p[0] == pytest.approx(amps)]
    return min(matches) if matches else default


class TestEnvelopeTransform:
    def test_acceptance_window_mode_scales_open_curve_both_edges(self):
        bands = assemble_envelope_bands(
            [_curve("ltd_open", "LTD", "open", LTD_OPEN)],
            {"LTD": _ltpu_basis(t_lo=-30.0, t_hi=0.0, pu_lo=-10.0, pu_hi=10.0)},
        )
        assert len(bands) == 1
        env = bands[0]
        assert env.id == "phase_envelope"
        assert env.family == "phase"
        # Min edge: amps ×0.9, seconds ×0.7. The assembler prepends the pickup
        # asymptote at the (shifted) start current.
        assert env.min_points[0][0] == pytest.approx(1000.0 * 0.9)
        assert _seg_seconds(env.min_points, 2000.0 * 0.9) == pytest.approx(25.0 * 0.7)
        # Max edge: amps ×1.1, seconds ×1.0 (tol_hi = 0).
        assert env.max_points[0][0] == pytest.approx(1000.0 * 1.1)
        assert _seg_seconds(env.max_points, 2000.0 * 1.1) == pytest.approx(25.0)

    def test_acceptance_window_mode_ignores_published_clear(self):
        # Even when an LTD clear curve serves, the acceptance window derives
        # BOTH edges from the open curve (the grading law) — the published
        # clear must not leak into the envelope max.
        ltd_clear = [(1000.0, 140.0), (2000.0, 35.0), (6000.0, 3.9)]
        bands = assemble_envelope_bands(
            [
                _curve("ltd_open", "LTD", "open", LTD_OPEN),
                _curve("ltd_clear", "LTD", "clear", ltd_clear),
            ],
            {"LTD": _ltpu_basis(t_lo=-20.0, t_hi=10.0)},
        )
        env = bands[0]
        assert _seg_seconds(env.max_points, 2000.0 * 1.1) == pytest.approx(25.0 * 1.1)

    def test_published_band_mode_shifts_amps_only(self):
        bands = assemble_envelope_bands(
            [
                _curve("std_open", "STD", "open", STD_OPEN),
                _curve("std_clear", "STD", "clear", STD_CLEAR),
            ],
            {"STD": _published_basis("STD", pu_lo=-10.0, pu_hi=10.0)},
        )
        env = bands[0]
        # Min = open shifted left, times untouched.
        assert env.min_points[0][0] == pytest.approx(4000.0 * 0.9)
        assert _seg_seconds(env.min_points, 4000.0 * 0.9) == pytest.approx(0.2)
        # Max = clear shifted right, times untouched.
        assert env.max_points[0][0] == pytest.approx(4000.0 * 1.1)
        assert _seg_seconds(env.max_points, 4000.0 * 1.1) == pytest.approx(0.3)
        assert env.open_only_elements == []

    def test_published_band_mode_open_only_reuses_open_for_max(self):
        bands = assemble_envelope_bands(
            [_curve("std_open", "STD", "open", STD_OPEN)],
            {"STD": _published_basis("STD")},
        )
        env = bands[0]
        assert env.open_only_elements == ["STD"]
        # Max edge falls back to the open data (amps-shifted only).
        assert _seg_seconds(env.max_points, 4000.0 * 1.1) == pytest.approx(0.2)

    def test_element_without_basis_is_skipped_and_surfaced(self):
        bands = assemble_envelope_bands(
            _phase_curves(), _basis_map(STD=None),
        )
        env = bands[0]
        assert "STD" in env.no_envelope_elements
        assert all(b.element != "STD" for b in env.element_basis)
        # Truncation law (#124 review): the corridor must never span the
        # region of a served-but-uncertified element — it ENDS at STD's
        # published region start, so the trailing INST block is not drawn
        # (and is surfaced as withheld-from-the-corridor, not silently cut).
        assert {b.element for b in env.element_basis} == {"LTD"}
        assert set(env.no_envelope_elements) == {"STD", "INST"}

    def test_acceptance_window_without_time_pcts_is_withheld(self):
        # An acceptance-window element missing its time tolerance has no
        # certified corridor — no envelope, never a zero-width fabrication.
        basis = _ltpu_basis()
        basis.time_tol_lo_pct = None
        basis.time_tol_hi_pct = None
        bands = assemble_envelope_bands(
            [_curve("ltd_open", "LTD", "open", LTD_OPEN)], {"LTD": basis},
        )
        assert bands == []

    def test_element_without_pu_pcts_is_withheld(self):
        basis = _published_basis("STD")
        basis.pu_tol_lo_pct = None
        bands = assemble_envelope_bands(
            [_curve("std_open", "STD", "open", STD_OPEN)], {"STD": basis},
        )
        assert bands == []

    def test_no_curves_no_bands(self):
        assert assemble_envelope_bands([], _basis_map()) == []


class TestEnvelopeTruncation:
    """The corridor must never span a served-but-uncertified element's
    region (#124 review: the assembler's suffix-min/flat-tail laws would
    otherwise chord/extend across the gap — fabricated geometry)."""

    def test_middle_element_withhold_truncates_at_its_region_start(self):
        bands = assemble_envelope_bands(_phase_curves(), _basis_map(STD=None))
        env = bands[0]
        # Corridor ends AT STD's published region start (4000 A) — no chord
        # across the STD region, no INST tail beyond it.
        assert max(p[0] for p in env.min_points) == pytest.approx(4000.0)
        assert max(p[0] for p in env.max_points) == pytest.approx(4000.0)
        assert env.right_edge_amps == pytest.approx(4000.0)
        assert {b.element for b in env.element_basis} == {"LTD"}
        assert set(env.no_envelope_elements) == {"STD", "INST"}

    def test_leading_element_withhold_needs_no_truncation(self):
        bands = assemble_envelope_bands(_phase_curves(), _basis_map(LTD=None))
        env = bands[0]
        # A leading withhold degrades naturally: the corridor simply starts
        # at the next certified block; the INST tail stays intact.
        assert env.min_points[0][0] == pytest.approx(4000.0 * 0.9)
        assert max(p[0] for p in env.min_points) == pytest.approx(100_000.0)
        assert {b.element for b in env.element_basis} == {"STD", "INST"}
        assert env.no_envelope_elements == ["LTD"]

    def test_last_element_withhold_truncates_before_it(self):
        bands = assemble_envelope_bands(_phase_curves(), _basis_map(INST=None))
        env = bands[0]
        # No flat-tail extension to the right edge across INST's region.
        assert max(p[0] for p in env.min_points) == pytest.approx(18000.0)
        assert max(p[0] for p in env.max_points) == pytest.approx(18000.0)
        assert env.right_edge_amps == pytest.approx(18000.0)
        assert {b.element for b in env.element_basis} == {"LTD", "STD"}
        assert env.no_envelope_elements == ["INST"]


class TestEnvelopeAssembly:
    def test_phase_envelope_staircase_handoffs_use_shifted_pickups(self):
        bands = assemble_envelope_bands(_phase_curves(), _basis_map())
        env = next(b for b in bands if b.family == "phase")
        # The min boundary's STD region starts at the SHIFTED STPU
        # (4000 × 0.9 = 3600) — the handoff recomputes on transformed blocks.
        min_amps = [p[0] for p in env.min_points]
        assert any(a == pytest.approx(3600.0) for a in min_amps)
        # And the max boundary's STD region starts at 4000 × 1.1 = 4400.
        max_amps = [p[0] for p in env.max_points]
        assert any(a == pytest.approx(4400.0) for a in max_amps)

    def test_gf_envelope_is_a_separate_band(self):
        bands = assemble_envelope_bands(
            _phase_curves() + _gf_curves(), _basis_map(),
        )
        ids = {b.id for b in bands}
        assert ids == {"phase_envelope", "gf_envelope"}
        gf = next(b for b in bands if b.family == "gf")
        assert gf.min_points[0][0] == pytest.approx(480.0 * 0.85)
        assert gf.max_points[0][0] == pytest.approx(480.0 * 1.15)
        # Published-band mode: GF times untouched.
        assert _seg_seconds(gf.min_points, 480.0 * 0.85) == pytest.approx(0.14)
        assert _seg_seconds(gf.max_points, 480.0 * 1.15) == pytest.approx(0.2)

    def test_envelope_contains_published_band_pointwise(self):
        # The corridor must bound the published geometry it derives from:
        # min ≤ open and max ≥ clear at every shared breakpoint (sanity law
        # for negative-lo / positive-hi tolerances).
        bands = assemble_envelope_bands(_gf_curves(), _basis_map())
        env = next(b for b in bands if b.family == "gf")
        # Min starts left of the published pickup; max starts right of it.
        assert env.min_points[0][0] < 480.0
        assert env.max_points[0][0] > 480.0

    def test_basis_metadata_passthrough(self):
        bands = assemble_envelope_bands(
            [_curve("ltd_open", "LTD", "open", LTD_OPEN)],
            {"LTD": _ltpu_basis(time_source="ltd_generic_estimate", t_lo=-30.0,
                                t_hi=0.0, estimated=True)},
        )
        basis = bands[0].element_basis[0]
        assert basis.element == "LTD"
        assert basis.estimated is True
        assert basis.time_source == "ltd_generic_estimate"
        assert basis.pu_source == "db_sensor_tolerance"
