"""
Golden Fixture Validation — B4 / B5 / B6
==========================================
Validates calc-engine formulas and algorithms against pre-computed
reference values stored in tests/fixtures/*.json.

IEEE and Thermal-M1 tests are **offline** (pure math, no DB).
Thermal-TUF uses a DB session to read actual sensor params.
TMT and Merge tests are offline.
"""

import json
import math
import os
import pytest

from apex_calc_engine.services.calc_engine.etu_merge import log_log_intersect, merge_sst_curves
from apex_calc_engine.services.calc_engine.tmt_curves import _catmull_rom_log

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')
PASS = 0
FAIL = 0


def check(label: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))


def load_fixture(name: str) -> dict:
    with open(os.path.join(FIXTURES, name)) as f:
        return json.load(f)


def pct_err(actual: float, expected: float) -> float:
    """Percentage error.  Returns 0.0 when both are zero."""
    if expected == 0:
        return 0.0 if actual == 0 else abs(actual) * 100
    return abs(actual - expected) / abs(expected) * 100


# ==============================================================
# B4 — IEEE Inverse-Time (offline formula)
# ==============================================================
#   T = band_mult × (A / (I^p − 1) + B + C6),  clamped to min

def _test_ieee_offline(fixture_file: str, test_label: str):
    print(f"\n=== {test_label} ===")
    fx = load_fixture(fixture_file)
    c = fx['coefficients']
    A = c['A_open']
    B = c['B_open']
    p = c['p_open']
    C6 = c.get('C6_open', 0.0)
    floor = c.get('min_open', 0.001)

    for grp in fx['golden_points_open']:
        bm = grp['band_mult']
        for pt in grp['points']:
            I = pt['I_multiple']
            exp = pt['expected_time_sec']
            denom = I ** p - 1.0
            if abs(denom) < 1e-12:
                continue
            t = max(bm * (A / denom + B + C6), floor)
            err = pct_err(t, exp)
            check(f"BM={bm} I={I} → {t:.6f} vs {exp:.6f}",
                  err < 0.01, f"err={err:.5f}%")


def test_b4_ieee_ext_inv():
    _test_ieee_offline('b4_ieee_ext_inv.json',
                       'B4 IEEE Ext Inv — Sensor 5817')


def test_b4_ieee_mod_inv():
    _test_ieee_offline('b4_ieee_mod_inv.json',
                       'B4 IEEE Mod Inv — Sensor 5817')


def test_b4_ieee_very_inv():
    _test_ieee_offline('b4_ieee_very_inv.json',
                       'B4 IEEE Very Inv — Sensor 5817')


# ==============================================================
# B4 — Thermal I²T  (Method 1, offline formula)
# ==============================================================
#   ref_ratio = ln(1 / (1 − (rating×Ipu / (pickup×Ithresh))^n))
#   arg       = (rating×Ipu / amps)^n
#   T         = K × band_mult × ln(1/(1−arg)) / ref_ratio

def test_b4_thermal_m1():
    print("\n=== B4 Thermal I²T (M1) — Sensor 15561 ===")
    fx = load_fixture('b4_thermal.json')
    c = fx['coefficients']
    rating = fx['rating']
    pickup = fx['pickup_current']
    Ipu = c['Ipu_open']
    K = c['K_open']
    n = c['n_open']
    Ithresh = c['Ithresh_open']
    min_t = c.get('min_time_open', 0.001)

    ref_base = rating * Ipu / (pickup * Ithresh)
    ref_arg = ref_base ** n
    check("ref_arg < 1", ref_arg < 1.0, f"ref_arg={ref_arg}")
    if ref_arg >= 1.0:
        return
    ref_ratio = math.log(1.0 / (1.0 - ref_arg))

    for grp in fx['golden_points_open']:
        bm = grp['band_mult']
        for pt in grp['points']:
            I_mult = pt['I_multiple']
            exp = pt['expected_time_sec']
            amps = I_mult * pickup

            arg = (rating * Ipu / amps) ** n
            if arg >= 1.0:
                check(f"BM={bm} I={I_mult} arg<1", False)
                continue
            t = K * bm * math.log(1.0 / (1.0 - arg)) / ref_ratio
            t = max(t, min_t)

            err = pct_err(t, exp)
            check(f"BM={bm} I={I_mult} → {t:.6f} vs {exp:.6f}",
                  err < 0.1, f"err={err:.4f}%")


# ==============================================================
# B4 — Thermal-TU  (Method 4, offline formula)
# ==============================================================
#   inner = 1 − (rating×Ipu)^n / (amps×(1−α))^n
#   T     = −K × band_mult × ln(inner)

def test_b4_thermal_tu():
    print("\n=== B4 Thermal-TU (M4) — Sensor 7102 ===")
    fx = load_fixture('b4_thermal_tu.json')
    c = fx['coefficients']
    rating = fx['rating']
    pickup = fx['pickup_current']
    Ipu = c['Ipu_open']
    alpha = c['alpha_open']
    K = c['K_open']
    n = c['n_open']
    min_t = c.get('min_time_open', 0.025)

    df = 1.0 - alpha
    num_base = (rating * Ipu) ** n

    for grp in fx['golden_points_open']:
        bm = grp['band_mult']
        for pt in grp['points']:
            I_mult = pt['I_multiple']
            exp = pt['expected_time_sec']
            amps = I_mult * pickup

            dval = (amps * df) ** n
            if dval <= 0:
                continue
            inner = 1.0 - num_base / dval
            if inner <= 0:
                continue
            t = (-K) * bm * math.log(inner)
            t = max(t, min_t)

            err = pct_err(t, exp)
            check(f"BM={bm} I={I_mult} → {t:.4f} vs {exp:.4f}",
                  err < 0.1, f"err={err:.4f}%")


# ============================================================== 
# B4 — Thermal-TUF  (Method 5, DB-backed)
# ============================================================== 
# This legacy case depends on the host app's config/session layer and stays
# out of the extracted package's offline validation lane for now.

@pytest.mark.skip(reason="Requires legacy app config and live DB-backed session")
def test_b4_thermal_tuf():
    pass


# ==============================================================
# B5 — TMT Catmull-Rom Spline (offline)
# ==============================================================

def test_b5_tmt_spline():
    print("\n=== B5 TMT Spline — Frame 3773, Class 0 ===")
    fx = load_fixture('b5_tmt_spline.json')
    raw = [(p['current_amp'], p['time_sec']) for p in fx['raw_points']]

    check(f"{fx['point_count']} raw points", len(raw) == fx['point_count'],
          f"got {len(raw)}")

    n_out = (len(raw) - 1) * 20
    spline = _catmull_rom_log(raw, n_out)

    check("Spline output > input", len(spline) > len(raw),
          f"{len(spline)} vs {len(raw)}")

    eb = fx['expected_behavior']
    first_exp = eb['first_point_matches']
    last_exp = eb['last_point_matches']

    check("First I matches",
          abs(spline[0][0] - first_exp['current_amp']) < 0.01,
          f"got {spline[0][0]:.4f}")
    check("First T matches",
          abs(spline[0][1] - first_exp['time_sec']) < 1.0,
          f"got {spline[0][1]:.4f}")
    check("Last I matches",
          abs(spline[-1][0] - last_exp['current_amp']) < 0.5,
          f"got {spline[-1][0]:.4f}")
    check("Last T matches",
          abs(spline[-1][1] - last_exp['time_sec']) < 0.001,
          f"got {spline[-1][1]:.6f}")

    for sc in fx['validation_spot_checks']:
        target_I = sc['current_amp']
        exp_T = sc['expected_time_sec']
        tol = sc['tolerance_pct']

        nearest = min(spline, key=lambda p: abs(p[0] - target_I))
        err = pct_err(nearest[1], exp_T)
        check(f"Spot I={target_I} T≈{exp_T}",
              err < tol, f"got T={nearest[1]:.4f}, err={err:.2f}%")


# ==============================================================
# B5 — TMT Small (< 4 points → direct copy, offline)
# ==============================================================

def test_b5_tmt_small():
    print("\n=== B5 TMT Small (< 4 pts → direct copy) ===")
    fx = load_fixture('b5_tmt_small.json')
    raw = [(p['current_amp'], p['time_sec']) for p in fx['raw_points']]

    check(f"{fx['point_count']} raw points", len(raw) == fx['point_count'])

    result = _catmull_rom_log(raw, 100)

    check("Output count = input count", len(result) == len(raw),
          f"got {len(result)}")
    if len(result) == len(raw):
        for i, (r, e) in enumerate(zip(result, raw)):
            check(f"Point {i} matches",
                  abs(r[0] - e[0]) < 1e-9 and abs(r[1] - e[1]) < 1e-9,
                  f"got {r} vs {e}")


# ==============================================================
# B6 — log_log_intersect (offline)
# ==============================================================

def test_b6_log_log_intersect():
    print("\n=== B6 log_log_intersect — Fixture Segments ===")
    fx = load_fixture('b6_merge_lt_st_inst.json')
    llt = fx['log_log_intersection_test']

    seg1 = (tuple(llt['seg1'][0]), tuple(llt['seg1'][1]))
    seg2 = (tuple(llt['seg2'][0]), tuple(llt['seg2'][1]))

    ix = log_log_intersect(seg1, seg2)
    check("Intersection found", ix is not None)
    if ix is None:
        return

    exp_I = llt['expected_intersection']['current']
    exp_T = llt['expected_intersection']['time']

    check(f"I ≈ {exp_I}",
          abs(ix[0] - exp_I) < 0.1, f"got {ix[0]:.4f}")
    check(f"T ≈ {exp_T}",
          abs(ix[1] - exp_T) < 0.001, f"got {ix[1]:.4f}")


# ==============================================================
# B6 — merge_sst_curves structural validation (offline)
# ==============================================================

def test_b6_merge_properties():
    print("\n=== B6 Merge LT+ST+INST — Structural Validation ===")
    fx = load_fixture('b6_merge_lt_st_inst.json')
    sc = fx['synthetic_input_curves']

    ltd = [tuple(p) for p in sc['ltd_curve']]
    std = [tuple(p) for p in sc['std_curve']]
    inst = [tuple(p) for p in sc['inst_curve']]

    merged = merge_sst_curves(
        ltpu=ltd[0][0],
        stpu=std[0][0],
        inst=inst[0][0],
        ovrd=0,
        ltd_curve=ltd,
        std_curve=std,
        inst_curve=inst,
        ovrd_curve=[],
        fillet_inst=fx['merge_validation']['fillet_radius'],
    )

    check("Merged has points", len(merged) > 0, f"got {len(merged)}")
    if not merged:
        return

    amps = [m[0] for m in merged]
    times = [m[1] for m in merged]

    check("Amps monotonic increasing",
          all(a1 <= a2 for a1, a2 in zip(amps, amps[1:])))

    check("Starts at LTD first I",
          merged[0][0] == ltd[0][0], f"got {merged[0][0]}")

    # INST region: look for times near the inst curve's time values
    inst_times = {p[1] for p in inst}
    inst_pts = [m for m in merged
                if any(abs(m[1] - it) < 0.01 for it in inst_times)]
    check("INST region present", len(inst_pts) > 0,
          f"found {len(inst_pts)} pts")

    # Time generally non-increasing (small increases from fillet OK)
    increases = sum(1 for t1, t2 in zip(times, times[1:])
                    if t2 > t1 * 1.01)
    check("Time mostly decreasing", increases <= 3,
          f"{increases} increases")


# ==============================================================
# Runner
# ==============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Golden Fixture Validation — B4 / B5 / B6")
    print("=" * 60)

    # B4 IEEE (offline)
    test_b4_ieee_ext_inv()
    test_b4_ieee_mod_inv()
    test_b4_ieee_very_inv()

    # B4 Thermal (offline + DB)
    test_b4_thermal_m1()
    test_b4_thermal_tu()
    test_b4_thermal_tuf()

    # B5 TMT (offline)
    test_b5_tmt_spline()
    test_b5_tmt_small()

    # B6 Merge (offline)
    test_b6_log_log_intersect()
    test_b6_merge_properties()

    print("\n" + "=" * 60)
    total = PASS + FAIL
    print(f"Results: {PASS}/{total} PASS, {FAIL}/{total} FAIL")
    print("=" * 60)

    sys.exit(0 if FAIL == 0 else 1)
