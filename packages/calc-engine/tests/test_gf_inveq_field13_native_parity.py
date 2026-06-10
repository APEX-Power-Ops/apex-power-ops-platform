"""G4 §5 GF-InvEq field[13]-basis captured-fixture parity (the L1 promotion gate).

Closes the GF-side InvEq numeric-parity gap: the GF runtime path (``byICalc=1``)
anchors the Therm equation's reference current on object slot ``field[13]``,
which is the **plug rating (In)** — identified via the kernel's own pickup-basis
dispatcher (``CTccLVBreakerCurveGF.ComputeAmps``: native uCalc = DB ``*_calc``+1;
slot map [12]=sensor/frame, [13]=plug, [15]=C-factor, [16]=pickup). The managed
equivalence is the STD-proven normalized Therm form with the effective
``rIRef' = rIRef × (plug / pickup)`` correction (G4 §3f).

The captured points in ``fixtures/gf_inveq_field13_native_parity.json`` come
from the actual EasyPower native kernel (``CalcThermEq`` in ``TccBase.dll``,
``byICalc=1``, object field [13] set per scenario) executed in-process by the
oracle harness under ``output/inveq-parity/oracle/`` — 416 scenarios covering
the COMPLETE GF Therm coefficient corpus (4 open + 4 clear dials × all observed
rIRef values) × 8 plug/pickup ratios. This regression runs without the DLL.

Promotion encoded here:
  * GF route-2 Therm with the plug-basis correction is reproduced BIT-EXACT →
    promoted "verify"→"db" in delay_trust.py (together with the slot-map bank).
  * A byICalc=1 row with NO basis available must be WITHHELD (None/[]), never
    silently computed on the pickup basis (the pre-L1 unfaithful form).
"""
import json
import os

import pytest

from apex_calc_engine.services.calc_engine.etu_curves import (
    Coefficients,
    IEEEInverseTimeSolver,
    apply_gf_basis,
)

_FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "gf_inveq_field13_native_parity.json"
)

_EVAL = IEEEInverseTimeSolver._evaluate_native_therm


def _load():
    with open(_FIXTURE) as fh:
        return json.load(fh)


def _smooth_points(scn):
    """(I_norm, native_t) for the smooth region only (§107 contract):
    skip the asymptote anchor at I <= rM and the rTmin floor knee."""
    rM = scn["coeff"]["c5"]
    floor = scn["floor"]
    for amps, t in scn["points"]:
        if amps <= rM + 1e-9:
            continue
        if t <= floor * 1.0001:
            continue
        yield amps, t  # pickup == 1.0 -> amps == I_norm


# ---------------------------------------------------------------------------
# apply_gf_basis — the native byICalc basis gate (pure unit behavior)
# ---------------------------------------------------------------------------

_COEFF = Coefficients(c1=0.14, c2=2.0, c3=0.14, c4=0.48, c5=0.9, c6=0.0)


def test_basis_passthrough_for_pickup_based_rows():
    """i_calc 4/8/10 translate to byICalc=0 (pickup basis) — unchanged."""
    for i_calc in (4, 8, 10):
        out = apply_gf_basis(_COEFF, i_calc, None)
        assert out is not None
        assert out.c4 == _COEFF.c4
    # ratio supplied but row is pickup-based: still unchanged
    out = apply_gf_basis(_COEFF, 4, 3.0)
    assert out is not None and out.c4 == _COEFF.c4


def test_basis_scales_riref_for_field13_rows():
    """i_calc=1 -> byICalc=1 -> rIRef' = rIRef × (plug/pickup)."""
    out = apply_gf_basis(_COEFF, 1, 2.5)
    assert out is not None
    assert out.c4 == pytest.approx(0.48 * 2.5, abs=0.0)
    # remaining coefficients untouched
    assert (out.c1, out.c2, out.c3, out.c5, out.c6) == (
        _COEFF.c1, _COEFF.c2, _COEFF.c3, _COEFF.c5, _COEFF.c6,
    )


def test_basis_withholds_field13_row_without_ratio():
    """byICalc=1 with no basis available must be withheld — never computed
    on the pickup basis (the pre-L1 unfaithful form)."""
    assert apply_gf_basis(_COEFF, 1, None) is None
    assert apply_gf_basis(_COEFF, 1, 0.0) is None
    assert apply_gf_basis(_COEFF, 1, -1.0) is None


def test_basis_withholds_field12_rows():
    """i_calc=0 -> byICalc=2 -> field[12] (sensor/frame) basis — corpus-absent
    (G4 §3f *ICalc=0 residual closed at zero rows); withhold defensively."""
    assert apply_gf_basis(_COEFF, 0, 2.0) is None


# ---------------------------------------------------------------------------
# Native parity — the L1 promotion gate
# ---------------------------------------------------------------------------

def test_fixture_provenance_is_native_kernel():
    prov = _load()["provenance"]
    assert "TccBase.dll" in prov["oracle"]
    assert "byICalc=1" in prov["functions"]


def test_gf_field13_basis_bit_exact_vs_native():
    """Every valid fixture scenario reproduced bit-exact on the smooth region."""
    checked_points = 0
    checked_scenarios = 0
    for scn in _load()["scenarios"]:
        if not scn["valid"]:
            continue
        coeff = Coefficients(**scn["coeff"])
        scaled = apply_gf_basis(coeff, 1, scn["basis_ratio"])
        assert scaled is not None, scn["label"]
        had = False
        for i_norm, native_t in _smooth_points(scn):
            prod = _EVAL(scaled, i_norm)
            assert prod is not None, (scn["label"], i_norm, native_t)
            assert abs(prod - native_t) < 1e-9, (scn["label"], i_norm, prod, native_t)
            checked_points += 1
            had = True
        if had:
            checked_scenarios += 1
    assert checked_points >= 250  # dense sweep: 252 smooth points captured
    assert checked_scenarios >= 60


def test_gf_field13_floor_region_clamps_to_rtmin():
    """In the floor knee the native lin-log extension and the production clamp
    agree to within the §107 contract (clamp == rTmin or == native point)."""
    for scn in _load()["scenarios"]:
        if not scn["valid"]:
            continue
        coeff = Coefficients(**scn["coeff"])
        scaled = apply_gf_basis(coeff, 1, scn["basis_ratio"])
        floor = scn["floor"]
        for amps, t in scn["points"]:
            if amps <= scn["coeff"]["c5"] + 1e-9 or t > floor * 1.0001:
                continue
            prod = _EVAL(scaled, amps)
            if prod is not None:
                assert abs(prod - floor) < 1e-9 or abs(prod - t) < 1e-9, (
                    scn["label"], amps, prod, t,
                )


def test_gf_field13_invalid_configs_withheld():
    """All-sentinel native output <=> R×rIRef <= rM: production returns None
    across the sweep (no fabricated curve below the effective asymptote)."""
    seen = 0
    for scn in _load()["scenarios"]:
        if scn["valid"]:
            continue
        coeff = Coefficients(**scn["coeff"])
        eff = scn["basis_ratio"] * scn["coeff"]["c4"]
        assert eff <= scn["coeff"]["c5"] + 1e-6, scn["label"]
        scaled = apply_gf_basis(coeff, 1, scn["basis_ratio"])
        assert scaled is not None
        for i_norm in (1.0, 2.0, 5.0, 10.0, 39.0):
            assert _EVAL(scaled, i_norm) is None, (scn["label"], i_norm)
        seen += 1
    assert seen >= 100  # 152 invalid configs captured


# ---------------------------------------------------------------------------
# Loader integration — i_calc read + basis applied at coefficient load
# ---------------------------------------------------------------------------

class _FakeSolver(IEEEInverseTimeSolver):
    """Bypass the DB: serve one synthetic GFD payload row."""

    def __init__(self, row):
        self._row = row  # no session

    def _load_equation_rows(self, sensor_id, equation_type):
        return [self._row]


_GFD_ROW = {
    # Normalized row contract (see _normalize_equation_rows): variant-prefixed keys.
    "ordinal": 1,
    "label": "0.2",
    "in_out": 2,
    "id_open_1": 0.14, "id_open_2": 2.0, "id_open_3": 0.14,
    "id_open_4": 0.48, "id_open_5": 0.9, "id_open_6": None,
    "id_open_i_calc": 1,
    "fd_open_1": 0.14, "fd_open_2": 2.0, "fd_open_3": 0.0056,
    "fd_open_4": 1.0, "fd_open_5": 0.9, "fd_open_6": None,
    "fd_open_i_calc": 8,
}


def test_loader_applies_basis_to_field13_variant():
    solver = _FakeSolver(_GFD_ROW)
    coeff = solver._load_coefficients(
        1, 1, "id_open", "gfd", gf_basis_ratio=2.5,
    )
    assert coeff is not None
    assert coeff.c4 == pytest.approx(0.48 * 2.5, abs=0.0)


def test_loader_withholds_field13_variant_without_ratio():
    solver = _FakeSolver(_GFD_ROW)
    coeff = solver._load_coefficients(1, 1, "id_open", "gfd")
    assert coeff is None


def test_loader_leaves_pickup_based_variant_unscaled():
    solver = _FakeSolver(_GFD_ROW)
    coeff = solver._load_coefficients(
        1, 1, "fd_open", "gfd", gf_basis_ratio=2.5,
    )
    assert coeff is not None
    assert coeff.c4 == pytest.approx(1.0, abs=0.0)


def test_loader_std_rows_unaffected():
    """STD rows (i_calc≡4 -> byICalc=0) load identically with/without ratio."""
    row = dict(_GFD_ROW, id_open_i_calc=4)
    solver = _FakeSolver(row)
    a = solver._load_coefficients(1, 1, "id_open", "std")
    b = solver._load_coefficients(1, 1, "id_open", "std", gf_basis_ratio=9.9)
    assert a is not None and b is not None
    assert a.c4 == b.c4 == pytest.approx(0.48, abs=0.0)


def test_generate_curve_passes_basis_through():
    solver = _FakeSolver(_GFD_ROW)
    # R=5 -> rIRef' = 2.4 > rM: a real curve must come back
    pts = solver.generate_curve(
        sensor_id=1, ordinal=1, variant="id_open", pickup_current=240.0,
        max_amps=240.0 * 40, equation_type="gfd", gf_basis_ratio=5.0,
    )
    assert pts, "expected a curve for R*rIRef > rM"
    # R=1 -> rIRef' = 0.48 <= rM: withheld (no curve)
    pts = solver.generate_curve(
        sensor_id=1, ordinal=1, variant="id_open", pickup_current=240.0,
        max_amps=240.0 * 40, equation_type="gfd", gf_basis_ratio=1.0,
    )
    assert pts == []
    # no ratio on a byICalc=1 row: withheld
    pts = solver.generate_curve(
        sensor_id=1, ordinal=1, variant="id_open", pickup_current=240.0,
        max_amps=240.0 * 40, equation_type="gfd",
    )
    assert pts == []
