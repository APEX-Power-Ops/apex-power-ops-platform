"""
Unit tests for the native-faithful composite TCC boundary assembly (G4 §3g).

The module under test is pure (no DB): it consumes the per-element PlotCurve
list the generator already serves and assembles the classic composite
staircase boundaries the native engine builds (CPointsMergeSST / CPointsMergeGF):

  - vertical pickup asymptote at the leftmost block's start current
  - each element block clipped to a current window ending at the next
    element's handoff (log-log intersection where the curves cross, else
    the next block's start current)
  - INST floor extended to the right edge
  - open and clear boundaries assembled separately; an element with no
    clear curve reuses its open block (zero band width, surfaced in
    open_only_elements)
  - ground fault = a fully separate band with its own GFPU vertical
"""

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neta.composite_boundary import (  # noqa: E402
    GF_TOP_SECONDS,
    PHASE_TOP_SECONDS,
    RIGHT_EDGE_AMPS,
    assemble_composite_bands,
)
from services.neta.schemas import PlotCurve, PlotCurvePoint  # noqa: E402


def _curve(cid, element, phase, pts, line_style="solid"):
    return PlotCurve(
        id=cid,
        element=element,
        phase=phase,
        line_style=line_style,
        points=[PlotCurvePoint(amps=a, seconds=s) for a, s in pts],
    )


def _xy(points):
    # The assembly module returns plain (amps, seconds) tuples.
    return list(points)


# Self-clipped staircase fixture (the Micrologic-style route-1 shape):
# LT ends at STPU, ST runs STPU→INST, INST runs pickup→5×pickup.
LT_OPEN = [(2475.0, 1000.0), (4500.0, 38.0), (8000.0, 5.5)]
ST_OPEN = [(8000.0, 0.42), (11000.0, 0.34), (12800.0, 0.30)]
INST_OPEN = [(12800.0, 0.05), (64000.0, 0.05)]
INST_CLEAR = [(12800.0, 0.08), (64000.0, 0.08)]
GF_OPEN = [(480.0, 6.0), (720.0, 2.8), (1440.0, 0.4), (3000.0, 0.4)]


def _staircase_curves():
    return [
        _curve("ltd_open", "LTD", "open", LT_OPEN),
        _curve("std_open", "STD", "open", ST_OPEN),
        _curve("inst_open", "INST", "open", INST_OPEN),
        _curve("inst_clear", "INST", "clear", INST_CLEAR),
    ]


def _band(bands, band_id):
    matches = [b for b in bands if b.id == band_id]
    assert matches, f"band {band_id!r} not assembled (got {[b.id for b in bands]})"
    return matches[0]


class TestPhaseBandOpen:
    def test_full_staircase_shape(self):
        bands = assemble_composite_bands(_staircase_curves())
        phase = _band(bands, "phase_band")
        pts = _xy(phase.open_points)

        # Vertical asymptote anchor at the LT block's start current.
        assert pts[0] == (2475.0, PHASE_TOP_SECONDS)
        assert pts[1][0] == 2475.0 and pts[1][1] == 1000.0

        # Strictly non-decreasing in current (one ordered polyline).
        amps = [a for a, _ in pts]
        assert amps == sorted(amps)

        # INST floor extended to the right edge.
        assert pts[-1] == (RIGHT_EDGE_AMPS, 0.05)

        # Vertical drop AT the INST pickup: two consecutive points share
        # amps=12800 (ST shelf end → INST floor).
        drops = [
            (pts[i], pts[i + 1])
            for i in range(len(pts) - 1)
            if pts[i][0] == pts[i + 1][0] == 12800.0
        ]
        assert drops, f"no vertical drop at INST pickup in {pts}"
        hi, lo = drops[0]
        assert hi[1] > lo[1]

    def test_overlapping_lt_clipped_at_st_start(self):
        # InvEq-style LT sweeps far past STPU; with the ST shelf entirely
        # below it, the handoff falls back to the ST block's start current.
        lt = [(1000.0, 500.0), (8000.0, 30.0), (100000.0, 2.0)]
        st = [(8000.0, 0.42), (100000.0, 0.30)]
        bands = assemble_composite_bands([
            _curve("ltd_open", "LTD", "open", lt),
            _curve("std_open", "STD", "open", st),
        ])
        phase = _band(bands, "phase_band")
        pts = _xy(phase.open_points)
        # No LT point beyond the ST start except the interpolated boundary point.
        lt_region = [(a, s) for a, s in pts if s > 0.42]
        assert all(a <= 8000.0 + 1e-6 for a, _ in lt_region), lt_region
        amps = [a for a, _ in pts]
        assert amps == sorted(amps)

    def test_handoff_at_loglog_crossing_when_st_starts_above(self):
        # ST starting ABOVE the LT curve (slower near its pickup) with a
        # steeper descent: the current element keeps governing until the
        # curves cross — the handoff is the log-log crossing, not the ST
        # start (native MergeLines delay priority).
        # LT: t = 1e6 / I (slope −1); ST: I⁴t ramp from (2000, 2000) onto a
        # 125 s shelf — crosses LT at I³ = 2000⁵/1e6 → I ≈ 3174.8 A.
        lt = [(1000.0, 1000.0), (100000.0, 10.0)]
        st = [(2000.0, 2000.0), (4000.0, 125.0), (100000.0, 125.0)]
        bands = assemble_composite_bands([
            _curve("ltd_open", "LTD", "open", lt),
            _curve("std_open", "STD", "open", st),
        ])
        phase = _band(bands, "phase_band")
        pts = _xy(phase.open_points)
        expected_x = (2000.0 ** 5 / 1e6) ** (1.0 / 3.0)
        assert any(
            a == pytest.approx(expected_x, rel=1e-6)
            and s == pytest.approx(1e6 / expected_x, rel=1e-6)
            for a, s in pts
        ), pts
        # 2000 A (the fallback handoff) must not appear — LT governs past it.
        assert all(a != 2000.0 for a, _ in pts), pts

    def test_handoff_at_st_start_when_shelf_below_lt(self):
        # THE production configuration: a DB-route LT curve descending all
        # the way to its min-time floor passes THROUGH the ST shelf — but the
        # shelf already governs at the ST pickup (0.42 s << LT's 30 s), so
        # the handoff is the ST start with the classic vertical drop AT STPU,
        # never the deep crossing (~22 kA) inside the overlap.
        lt = [(1000.0, 500.0), (8000.0, 30.0), (30000.0, 0.15), (100000.0, 0.001)]
        st = [(8000.0, 0.42), (11000.0, 0.34), (12800.0, 0.30), (100000.0, 0.30)]
        bands = assemble_composite_bands([
            _curve("ltd_open", "LTD", "open", lt),
            _curve("std_open", "STD", "open", st),
        ])
        phase = _band(bands, "phase_band")
        pts = _xy(phase.open_points)
        # Vertical drop at STPU: 8000 A appears at the LT time then the shelf.
        at_stpu = [s for a, s in pts if a == 8000.0]
        assert 30.0 in at_stpu and 0.42 in at_stpu, pts
        # No LT segment survives past STPU (everything right of 8 kA is shelf).
        assert all(s <= 0.42 for a, s in pts if a > 8000.0), pts

    def test_inst_below_stpu_floor_starts_at_inst_pickup(self):
        # INST dialed BELOW the short-time pickup: the floor starts at the
        # INST amps (native AddInstantaneous), the bypassed ST block drops
        # out, and the LT block is capped at the INST pickup — not at STPU.
        lt = [(1000.0, 500.0), (8000.0, 30.0)]
        st = [(8000.0, 0.42), (12800.0, 0.30)]
        inst = [(6000.0, 0.05), (30000.0, 0.05)]
        bands = assemble_composite_bands([
            _curve("ltd_open", "LTD", "open", lt),
            _curve("std_open", "STD", "open", st),
            _curve("inst_open", "INST", "open", inst),
        ])
        phase = _band(bands, "phase_band")
        pts = _xy(phase.open_points)
        # Floor corner at the INST pickup, extended to the right edge.
        assert any(a == 6000.0 and s == 0.05 for a, s in pts), pts
        assert pts[-1] == (RIGHT_EDGE_AMPS, 0.05)
        # Nothing slower than the floor survives right of the INST pickup.
        assert all(s <= 0.05 for a, s in pts if a > 6000.0 + 1e-9), pts
        # The bypassed ST shelf contributes nothing.
        assert all(s not in (0.42, 0.30) for _, s in pts), pts

    def test_inst_only_band(self):
        bands = assemble_composite_bands([
            _curve("inst_open", "INST", "open", INST_OPEN),
            _curve("inst_clear", "INST", "clear", INST_CLEAR),
        ])
        phase = _band(bands, "phase_band")
        pts = _xy(phase.open_points)
        assert pts[0] == (12800.0, PHASE_TOP_SECONDS)
        assert pts[-1] == (RIGHT_EDGE_AMPS, 0.05)

    def test_lt_only_ramp_tail_not_extended(self):
        bands = assemble_composite_bands([
            _curve("ltd_open", "LTD", "open", LT_OPEN),
        ])
        phase = _band(bands, "phase_band")
        pts = _xy(phase.open_points)
        # Ramp tail (5.5 s at 8 kA) is NOT flat — must not fabricate a shelf.
        assert pts[-1] == (8000.0, 5.5)

    def test_lt_only_flat_tail_extended(self):
        lt = LT_OPEN + [(20000.0, 5.5)]
        bands = assemble_composite_bands([
            _curve("ltd_open", "LTD", "open", lt),
        ])
        phase = _band(bands, "phase_band")
        pts = _xy(phase.open_points)
        assert pts[-1] == (RIGHT_EDGE_AMPS, 5.5)

    def test_no_curves_no_bands(self):
        assert assemble_composite_bands([]) == []


class TestClearBoundary:
    def test_clear_assembled_from_clear_curves(self):
        lt_clear = [(2475.0, 1400.0), (4500.0, 55.0), (8000.0, 8.0)]
        curves = _staircase_curves() + [
            _curve("ltd_clear", "LTD", "clear", lt_clear, "dashed"),
        ]
        bands = assemble_composite_bands(curves)
        phase = _band(bands, "phase_band")
        cpts = _xy(phase.clear_points)
        assert cpts[0] == (2475.0, PHASE_TOP_SECONDS)
        # Clear LT data is used (1400 s, not the open 1000 s).
        assert any(s == 1400.0 for _, s in cpts)
        # INST clear floor at 0.08 extended to the edge.
        assert cpts[-1] == (RIGHT_EDGE_AMPS, 0.08)

    def test_open_only_elements_fall_back_to_open(self):
        bands = assemble_composite_bands(_staircase_curves())
        phase = _band(bands, "phase_band")
        # LTD + STD served open-only → their clear blocks reuse the open data.
        assert set(phase.open_only_elements) == {"LTD", "STD"}
        cpts = _xy(phase.clear_points)
        assert any(s == 1000.0 for _, s in cpts)  # the open LT data
        assert cpts[-1] == (RIGHT_EDGE_AMPS, 0.08)  # the real INST clear

    def test_all_elements_with_clear_have_empty_open_only(self):
        curves = [
            _curve("inst_open", "INST", "open", INST_OPEN),
            _curve("inst_clear", "INST", "clear", INST_CLEAR),
        ]
        bands = assemble_composite_bands(curves)
        phase = _band(bands, "phase_band")
        assert phase.open_only_elements == []


class TestGfBand:
    def test_gf_band_separate_with_own_vertical(self):
        curves = _staircase_curves() + [
            _curve("gfd_open", "GFD", "open", GF_OPEN),
        ]
        bands = assemble_composite_bands(curves)
        gf = _band(bands, "gf_band")
        assert gf.family == "gf"
        pts = _xy(gf.open_points)
        # Own vertical at the GF start current, native 1000 s top anchor.
        assert pts[0] == (480.0, GF_TOP_SECONDS)
        assert pts[1] == (480.0, 6.0)
        # Flat tail (0.4 s definite floor) extended to the right edge.
        assert pts[-1] == (RIGHT_EDGE_AMPS, 0.4)
        # GFD open-only → clear reuses open.
        assert gf.open_only_elements == ["GFD"]

    def test_phase_band_excludes_gfd(self):
        curves = _staircase_curves() + [
            _curve("gfd_open", "GFD", "open", GF_OPEN),
        ]
        bands = assemble_composite_bands(curves)
        phase = _band(bands, "phase_band")
        assert all(s > 0.04 for _, s in _xy(phase.open_points))
        # No phase point at the GF pickup current.
        assert all(a >= 2475.0 for a, _ in _xy(phase.open_points))

    def test_gfd_only_yields_gf_band_only(self):
        bands = assemble_composite_bands([
            _curve("gfd_open", "GFD", "open", GF_OPEN),
        ])
        assert [b.id for b in bands] == ["gf_band"]


class TestGeometry:
    def test_clip_interpolates_in_loglog_space(self):
        # LT: t = 1e6 / I. Clipped at the ST start 10000 A the boundary point
        # must be log-log interpolated: t(10000) = 100 s exactly.
        lt = [(1000.0, 1000.0), (100000.0, 10.0)]
        st = [(10000.0, 0.5), (100000.0, 0.5)]
        bands = assemble_composite_bands([
            _curve("ltd_open", "LTD", "open", lt),
            _curve("std_open", "STD", "open", st),
        ])
        phase = _band(bands, "phase_band")
        pts = _xy(phase.open_points)
        boundary = [s for a, s in pts if abs(a - 10000.0) < 1e-6 and s > 0.5]
        assert boundary and boundary[0] == pytest.approx(100.0, rel=1e-9)

    def test_right_edge_metadata(self):
        bands = assemble_composite_bands(_staircase_curves())
        phase = _band(bands, "phase_band")
        assert phase.right_edge_amps == RIGHT_EDGE_AMPS

    def test_clip_at_vertical_step_does_not_zigzag(self):
        # The LT data carries a pre-baked vertical step exactly at the
        # handoff current (8 kA): the clip must not retrace the step with an
        # interpolated point — time at 8 kA must be strictly decreasing.
        lt = [(1000.0, 100.0), (8000.0, 50.0), (8000.0, 30.0), (12000.0, 20.0)]
        st = [(8000.0, 0.4), (20000.0, 0.3)]
        bands = assemble_composite_bands([
            _curve("ltd_open", "LTD", "open", lt),
            _curve("std_open", "STD", "open", st),
        ])
        phase = _band(bands, "phase_band")
        at_handoff = [s for a, s in _xy(phase.open_points) if a == 8000.0]
        assert at_handoff == sorted(at_handoff, reverse=True), at_handoff

    def test_log_equal_distinct_doubles_do_not_crash(self):
        # Two DISTINCT doubles can have identical math.log values at large
        # amps — the interpolation denominator must be guarded.
        big = 1e9
        nudge = math.nextafter(big, math.inf)
        lt = [(1000.0, 100.0), (big, 50.0), (nudge, 40.0), (2e9, 30.0)]
        st = [(5e8, 10.0), (1.5e9, 8.0)]
        bands = assemble_composite_bands([
            _curve("ltd_open", "LTD", "open", lt),
            _curve("std_open", "STD", "open", st),
        ])
        assert bands and bands[0].open_points
