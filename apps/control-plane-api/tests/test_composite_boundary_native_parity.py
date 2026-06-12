"""
#72 — native composite-assembly primitive parity (G4 §3g spot-check gate).

Validates ``services/neta/composite_boundary``'s assembly primitives against
the NATIVE EasyPower TccBase.dll assembly primitives, captured as a DLL-free
fixture (``composite_primitives_native_parity.json``) by the host-local
reflection oracle (the §107 harness pattern; see the fixture's provenance
block). The scenario inputs are the EXACT primitive calls
``assemble_composite_bands`` performs on LIVE served curves (5 vendor-diverse
sensors × hi/lo dials) + replication-guarded offline vendor sweeps + synthetic
adversarial edges.

The characterized native contract this file asserts:

  1. ``_loglog_time_at``  == ``CLinearEquation.ComputeY``/``ComputeLogY``
     (double precision; observed max rel ~6e-15).
  2. ``_clip_to_window``  == ``CLinearEquation.TrimCurveX`` on the shared data
     domain (edge interpolation included). Beyond the data, native EXTENDS by
     log-log extrapolation of the boundary segment — EXCEPT when the
     extrapolated value would fall below the native 0.001 s plot floor (the
     ``AddLongTimePickup`` bottom anchor), where it holds the last value
     horizontally (characterized by the fill probes; 8/8 observations).
     For flat tails both regimes reduce to the horizontal shelf = our
     assembler's flat-tail/INST right-edge rule (= every real composite case:
     floors and INST shelves are flat by construction). Our assembler never
     requests a window left of a block's data start (window_start is clamped
     to the data start), and does not slope-extrapolate truncated ramp tails
     (honest under-draw; ratified deviation).
  3. ``_loglog_crossing`` == ``CLogLogIntersection`` — the native intersection
     solver computes in SINGLE precision (float32), so parity is asserted at
     1.2e-7 relative; ours is the same root at double precision. Dispatch
     mirrors MergeLines: horizontal seg2 → SolveWithinConstraints; sloped
     seg2 → Solve + 1%-padded bbox containment.
  4. ``_handoff`` vertical-drop == native MergeLines no-cross/disjoint
     outcomes (every real-corpus handoff). When a genuine crossing exists,
     native quantizes the join to the end of the crossing curve-1 segment
     (the IL_0473 snap); ours uses the exact crossing — asserted within the
     containing segment span.
  5. GF band assembly == ``CPointsMergeGF.MergeGF``: GFPU vertical (top
     1000 s) + the band start-clipped WITH log-log interpolation at GFPU
     (TrimCurveStartX mutates the start point in place — the same rule as
     ``_clip_to_window``) + clear-pass reversal. Real rows match the native
     output exactly up to our ratified right-edge extension.
"""

import json
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.neta import composite_boundary as cb  # noqa: E402

FIXTURE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "fixtures",
    "composite_primitives_native_parity.json",
)

# Interpolation primitives are double-precision on both sides.
REL_TOL_DOUBLE = 1e-9
# The native intersection solver computes in single precision.
REL_TOL_FLOAT32 = 1.2e-7


@pytest.fixture(scope="module")
def fx():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def _curves(fx):
    return {k: [tuple(p) for p in v] for k, v in fx["curves"].items()}


def _rel(a: float, b: float) -> float:
    if a == b:
        return 0.0
    m = max(abs(a), abs(b))
    return abs(a - b) / m if m else 0.0


def test_provenance_and_corpus_complete(fx):
    prov = fx["provenance"]
    assert "TccBase.dll" in prov["native_source"]
    assert "#72" in prov["task"]
    sc = fx["scenarios"]
    # The recorded corpus (live + vendor sweeps + synthetics) — a shrunk
    # fixture means the corpus was regenerated without the full sweep.
    assert len(sc["computey"]) >= 25
    assert len(sc["trimx"]) >= 60
    assert len(sc["mergelines"]) >= 24
    assert len(sc["mergegf"]) >= 20
    assert len(sc["cross"]) >= 7
    assert len(sc["seglogy"]) >= 5
    # vendor diversity: every corpus sensor contributes scenarios (sensor 809
    # enters via its vendor sweep contexts — its live INST placeholder curves
    # dedup against 3833's identical ones)
    ids = " ".join(s["id"] for s in sc["trimx"])
    for tag in ("s17", "809", "s1160", "s3833", "s4628", "syn"):
        assert tag in ids, f"corpus missing {tag} scenarios"


def test_loglog_time_at_matches_native_computey(fx):
    curves = _curves(fx)
    worst = 0.0
    for s in fx["scenarios"]["computey"]:
        ours = cb._loglog_time_at(curves[s["curve"]], s["x"])
        assert ours is not None, s["id"]
        r = _rel(ours, s["native"]["y"])
        worst = max(worst, r)
        assert r <= REL_TOL_DOUBLE, f"{s['id']}: ours={ours} native={s['native']['y']} rel={r}"
    assert worst <= REL_TOL_DOUBLE


def test_loglog_time_at_matches_native_segment_computelogy(fx):
    for s in fx["scenarios"]["seglogy"]:
        ours = cb._loglog_time_at([tuple(s["p1"]), tuple(s["p2"])], s["x"])
        assert ours is not None, s["id"]
        assert s["native"]["set_ok"] is True
        r = _rel(ours, s["native"]["y"])
        assert r <= REL_TOL_DOUBLE, f"{s['id']}: ours={ours} native={s['native']['y']} rel={r}"


def test_clip_to_window_matches_native_trimx_on_data_domain(fx):
    curves = _curves(fx)
    for s in fx["scenarios"]["trimx"]:
        src = curves[s["curve"]]
        npts = [tuple(p) for p in s["native"]["points"]]
        ours = [tuple(p) for p in cb._clip_to_window(src, s["min_x"], s["max_x"])]

        if s["max_x"] <= s["min_x"]:
            # degenerate/inverted window: we return nothing; native emits at
            # most a degenerate point — neither draws a segment.
            assert len(ours) == 0
            continue
        if not ours:
            # window entirely outside data — native may still emit edge fill;
            # no real assembly call hits this (windows derive from the data).
            continue

        # native output truncated to the shared data domain on BOTH sides:
        # native extrapolates past either data edge when the window asks for
        # it; our assembler never requests beyond-data windows (left edges are
        # clamped to the block's data start; right fills are the flat-tail
        # rule, asserted separately below).
        data_start = src[0][0]
        data_end = src[-1][0]
        n_core = [p for p in npts if data_start - 1e-12 <= p[0] <= data_end + 1e-12]
        assert n_core, f"{s['id']}: native emitted nothing inside the data domain"

        # endpoints on the shared domain
        assert _rel(ours[0][0], n_core[0][0]) <= REL_TOL_DOUBLE, (
            f"{s['id']}: start ours={ours[0]} native={n_core[0]}"
        )
        assert _rel(ours[-1][0], n_core[-1][0]) <= REL_TOL_DOUBLE, (
            f"{s['id']}: end ours={ours[-1]} native={n_core[-1]}"
        )

        # geometric equality at every breakpoint of both outputs
        xs = sorted({p[0] for p in ours} | {p[0] for p in n_core})
        for x in xs:
            yo = cb._loglog_time_at(ours, x)
            yn = cb._loglog_time_at(n_core, x)
            if yo is None or yn is None:
                continue
            assert _rel(yo, yn) <= REL_TOL_DOUBLE, (
                f"{s['id']}: y@{x} ours={yo} native={yn}"
            )


NATIVE_PLOT_FLOOR_SECONDS = 0.001  # the AddLongTimePickup bottom anchor


def _native_fill_expectation(p_prev, p_last, max_x):
    """The characterized native right-edge fill: log-log extrapolation of the
    final segment to max_x, falling back to the horizontal hold at the last
    value when the extrapolated time lands below the 0.001 s plot floor."""
    (x1, y1), (x2, y2) = p_prev, p_last
    if x1 <= 0 or x2 <= 0 or y1 <= 0 or y2 <= 0 or x1 == x2:
        return y2
    la1, la2 = math.log(x1), math.log(x2)
    if la1 == la2 or y1 == y2:
        return y2
    slope = (math.log(y2) - math.log(y1)) / (la2 - la1)
    extrap = math.exp(math.log(y2) + slope * (math.log(max_x) - la2))
    return extrap if extrap >= NATIVE_PLOT_FLOOR_SECONDS else y2


def _assert_fill_rule(sid, src, max_x, npts):
    data_end = src[-1][0]
    beyond = [p for p in npts if p[0] > data_end + 1e-9]
    if not beyond:
        return 0
    expected = _native_fill_expectation(src[-2], src[-1], max_x)
    assert _rel(beyond[-1][0], max_x) <= REL_TOL_DOUBLE, sid
    assert _rel(beyond[-1][1], expected) <= 1e-6, (
        f"{sid}: native fill {beyond[-1]} != characterized expectation "
        f"{expected} (extrap-with-0.001s-floor rule)"
    )
    return 1


def test_native_right_edge_fill_matches_characterized_rule(fx):
    """Beyond the data end, native TrimCurveX extends by log-log extrapolation
    of the final segment, holding the last value horizontally when the
    extrapolation would fall below the 0.001 s plot floor. For flat tails both
    regimes equal our assembler's flat-tail/INST right-edge extension."""
    curves = _curves(fx)
    checked = 0
    for s in fx["scenarios"]["trimx"]:
        src = curves[s["curve"]]
        if len(src) < 2 or s["max_x"] <= s["min_x"]:
            continue
        npts = [tuple(p) for p in s["native"]["points"]]
        checked += _assert_fill_rule(s["id"], src, s["max_x"], npts)
        # flat tails: the native fill == our assembler's flat extension value
        if (
            npts
            and npts[-1][0] > src[-1][0] + 1e-9
            and cb._is_flat_tail(src)
        ):
            assert _rel(npts[-1][1], src[-1][1]) <= REL_TOL_DOUBLE, (
                f"{s['id']}: flat-tail fill differs from our extension"
            )
    # dedicated probes pin the rule across both regimes
    pcurves = {k: [tuple(p) for p in v] for k, v in fx.get("fill_probe_curves", {}).items()}
    for s in fx["scenarios"].get("fill_probes", []):
        src = pcurves[s["curve"]]
        npts = [tuple(p) for p in s["native"]["points"]]
        checked += _assert_fill_rule(s["id"], src, s["max_x"], npts)
    assert checked >= 12  # the corpus + probes exercise the fill repeatedly


def _native_cross_dispatch(s):
    """Mirror MergeLines' intersection dispatch (decomp 1236-1295):
    horizontal seg2 (slope==0) -> SolveWithinConstraints; sloped seg2 ->
    Solve + 1%-padded bbox containment on both segments."""
    n = s["native"]
    q1, q2 = tuple(s["q1"]), tuple(s["q2"])
    p1, p2 = tuple(s["p1"]), tuple(s["p2"])
    if n["out2"] == 0.0:  # seg2 horizontal — the SolveWithinConstraints path
        return (n["swc_pt"][0] if n["swc"] else None)
    if not n["solve"]:
        return None
    x, y = n["solve_pt"]
    rect_ok = True
    for (a, b), v in (((p1[0], p2[0]), x), ((p1[1], p2[1]), y),
                      ((q1[0], q2[0]), x), ((q1[1], q2[1]), y)):
        lo, hi = min(a, b), max(a, b)
        if not (lo * 0.99 <= v <= hi * 1.01):
            rect_ok = False
    return x if rect_ok else None


def test_crossing_matches_native_within_single_precision(fx):
    for s in fx["scenarios"]["cross"]:
        seg1 = [tuple(s["p1"]), tuple(s["p2"])]
        seg2 = [tuple(s["q1"]), tuple(s["q2"])]
        lo = max(min(p[0] for p in seg1), min(p[0] for p in seg2))
        hi = min(max(p[0] for p in seg1), max(p[0] for p in seg2))
        ours = cb._loglog_crossing(seg1, seg2, lo, hi)
        native_x = _native_cross_dispatch(s)

        if s["id"] == "cross_horiz_coincident":
            # coincident horizontals: MergeLines' |dt|<1e-4 special case joins
            # the curves without solving; ours picks the first overlap point.
            # Both yield the same drawn boundary (the segments coincide).
            assert ours is not None and s["native"]["horizontal1"]
            continue
        if s["id"] == "cross_touch_endpoint":
            # segments touch at a shared endpoint: ours treats the tangency
            # point as a crossing (|d|<1e-12 at the breakpoint); the native
            # padded-bbox Solve path rejects it (no transversal crossing).
            # Geometrically identical handoff either way (join at the shared
            # endpoint = the next block's start).
            assert ours is None or _rel(ours, seg2[0][0]) <= REL_TOL_DOUBLE
            continue

        if native_x is None:
            assert ours is None, f"{s['id']}: ours={ours} native=none"
        else:
            assert ours is not None, f"{s['id']}: ours=none native={native_x}"
            r = _rel(ours, native_x)
            assert r <= REL_TOL_FLOAT32, (
                f"{s['id']}: ours={ours} native={native_x} rel={r} "
                "(native solver is single-precision)"
            )


def test_handoff_branches_match_native_mergelines(fx):
    curves = _curves(fx)
    real_rows = 0
    for s in fx["scenarios"]["mergelines"]:
        c1 = curves[s["curve1"]]
        c2 = curves[s["curve2"]]
        ours = cb._handoff(c1, c2)
        n0 = s["native_dp0"]
        x0 = c2[0][0]
        merged_with_truncation = n0["merged"] and n0["count1_out"] != n0["count1_in"]

        if not merged_with_truncation:
            # native found NO crossing (returns false), or curve1 ends before
            # curve2 starts (disjoint true): the caller clips at the next
            # element's pickup — our vertical-drop branch.
            assert _rel(ours, x0) <= REL_TOL_DOUBLE, (
                f"{s['id']}: native no-cross but ours={ours} != next start {x0}"
            )
            if not s["id"].startswith("mlines_0") or "syn_" not in s["id"]:
                real_rows += 1
            continue

        # native truncated curve1 at the join: a genuine crossing. Native
        # quantizes the join to the end of the crossing curve-1 segment
        # (IL_0473) — assert ours lies within that segment's span.
        njoin_x = n0["curve1_out"][n0["count1_out"] - 1][0]
        spans = [
            (a1, a2) for (a1, _), (a2, _) in zip(c1, c1[1:])
            if min(a1, a2) - 1e-9 <= njoin_x <= max(a1, a2) + 1e-9
        ]
        lo = min(a for a, _ in spans) if spans else njoin_x
        hi = max(b for _, b in spans) if spans else njoin_x
        # the vertical-first-segment synthetic: native joins ON the vertical
        # (x0); ours crosses within the first sloped span after it.
        lo = min(lo, x0)
        assert lo - 1e-9 <= ours <= hi + 1e-9, (
            f"{s['id']}: ours={ours} outside the native join segment "
            f"[{lo}, {hi}] (native join x={njoin_x})"
        )
    assert real_rows >= 20  # every real-corpus handoff is the vertical-drop branch


def test_gf_band_assembly_matches_native_mergegf(fx):
    curves = _curves(fx)
    real_checked = 0
    for s in fx["scenarios"]["mergegf"]:
        band = curves[s["band"]]
        npts = [tuple(p) for p in s["native"]["points"]]
        assert npts, s["id"]
        if s["clearing"]:
            npts = list(reversed(npts))  # native reverses the clear pass

        if abs(s["gfpu"] - band[0][0]) > 1e-9:
            # synthetic gfpu != band start: native writes the vertical at GFPU
            # and start-clips the band by interpolating AT GFPU in place
            # (TrimCurveStartX) — the same rule as our _clip_to_window edge
            # interpolation. Assert that equivalence on the inside case.
            if band[0][0] < s["gfpu"] < band[-1][0]:
                clipped = cb._clip_to_window(band, s["gfpu"], band[-1][0])
                assert _rel(npts[1][0], clipped[0][0]) <= REL_TOL_DOUBLE
                assert _rel(npts[1][1], clipped[0][1]) <= REL_TOL_DOUBLE, (
                    f"{s['id']}: native interpolated start {npts[1]} != "
                    f"our clip start {clipped[0]}"
                )
            continue

        # real serving rows (vertical at the band start): our assembled gf
        # boundary equals the native output exactly, up to our ratified
        # right-edge extension (native's SC clip happens in the outer
        # RecalcCurve; the serving band runs to RIGHT_EDGE_AMPS instead).
        ours = cb._assemble_boundary(
            [("GFD", band)], cb.GF_TOP_SECONDS, cb.RIGHT_EDGE_AMPS
        )
        core = ours
        if len(ours) == len(npts) + 1 and ours[-1][0] == cb.RIGHT_EDGE_AMPS:
            core = ours[:-1]  # drop our flat right-edge extension point
        assert len(core) == len(npts), (
            f"{s['id']}: ours={len(ours)}pts native={len(npts)}pts"
        )
        assert _rel(core[0][1], cb.GF_TOP_SECONDS) <= REL_TOL_DOUBLE  # 1000 s top
        for (oa, os_), (na, ns) in zip(core, npts):
            assert _rel(oa, na) <= REL_TOL_DOUBLE, f"{s['id']}: amps {oa} vs {na}"
            assert _rel(os_, ns) <= REL_TOL_DOUBLE, f"{s['id']}: secs {os_} vs {ns}"
        real_checked += 1
    assert real_checked >= 16  # all live + vendor-sweep GF rows


def test_full_assembly_consumes_fixture_curves(fx):
    """End-to-end smoke: the assembler still produces both boundaries from a
    fixture curve set (3833 GF + the synthetic staircase inputs are covered by
    the per-primitive tests; this guards the recorded corpus stays loadable)."""
    curves = _curves(fx)
    gf_rows = [s for s in fx["scenarios"]["mergegf"] if "s3833" in s["id"]]
    assert gf_rows
    band = curves[gf_rows[0]["band"]]
    out = cb._assemble_boundary([("GFD", band)], cb.GF_TOP_SECONDS, cb.RIGHT_EDGE_AMPS)
    assert out and out[0][1] == cb.GF_TOP_SECONDS
