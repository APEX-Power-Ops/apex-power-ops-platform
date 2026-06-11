"""GF-InvEq ANSI captured-fixture parity (#120 — punch-list L1 close).

Closes the GF ANSI half of the InvEq numeric-parity gap. The native kernel
``CTccLVBreakerCurveGF.CalcAnsiEqGF`` evaluates the standard ANSI/C37.112
inverse curve

    T(M) = rA + rB/(M - rC) + rD/(M - rC)^2 + rE/(M - rC)^3   floored at rTmin

where M = I / pickup (byICalc=0 — all 25 GF ANSI sensors carry
``id_op_i_calc = 8`` → pickup basis; G4 §3f). The six stored floats map
``c1=rTmin c2=rA c3=rB c4=rC c5=rD c6=rE``.

``fixtures/gf_inveq_ansi_native_parity.json`` is captured from the actual
TccBase.dll kernel (``ansi_oracle.exe`` under ``output/inveq-parity/oracle/``)
over the COMPLETE distinct GF ANSI coefficient corpus (18 tuples = 9 open +
9 clear; 108 rows / 25 sensors / 3 trip styles in prod). This regression runs
without the DLL.

Promotion gate: the managed ``_evaluate_native_ansi`` reproduces every native
smooth-region point BIT-EXACT → GF ANSI un-excluded + promoted verify→db.
"""
import json
import os

import pytest

from apex_calc_engine.services.calc_engine.etu_curves import (
    Coefficients,
    IEEEInverseTimeSolver,
)

_FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "gf_inveq_ansi_native_parity.json"
)
_EVAL = IEEEInverseTimeSolver._evaluate_native_ansi


def _load():
    with open(_FIXTURE) as fh:
        return json.load(fh)


def _smooth_points(scn):
    """(I_norm, native_t) for the smooth region only: skip the rTmin floor
    knee + the [1e10, floor] sentinel tail. byICalc=0, field16=1 → amps == M."""
    floor = scn["floor"]
    for amps, t in scn["points"]:
        if amps >= 1e9:
            continue
        if t <= floor * 1.0001:
            continue
        yield amps, t


def test_fixture_provenance_is_native_kernel():
    prov = _load()["provenance"]
    assert "TccBase.dll" in prov["oracle"]
    assert "CalcAnsiEqGF" in prov["oracle"]
    assert "c1=rTmin" in prov["column_map"]


def test_corpus_is_complete():
    """All 18 distinct corpus tuples are present (9 open + 9 clear)."""
    scns = _load()["scenarios"]
    assert len(scns) == 18
    assert sum(1 for s in scns if s["variant"] == "open") == 9
    assert sum(1 for s in scns if s["variant"] == "clear") == 9
    # both families exercised
    assert any(s["family"] == "flat" for s in scns)
    assert any(s["family"] == "inverse" for s in scns)


def test_gf_ansi_bit_exact_vs_native():
    """Every valid fixture scenario reproduced bit-exact on the smooth region."""
    checked_points = 0
    checked_scenarios = 0
    for scn in _load()["scenarios"]:
        coeff = Coefficients(**scn["coeff"])
        had = False
        for i_norm, native_t in _smooth_points(scn):
            prod = _EVAL(coeff, i_norm)
            assert prod is not None, (scn["label"], i_norm, native_t)
            assert abs(prod - native_t) < 1e-9, (scn["label"], i_norm, prod, native_t)
            checked_points += 1
            had = True
        if had:
            checked_scenarios += 1
    assert checked_scenarios == 18
    assert checked_points >= 2000  # dense sweep across the full corpus


def test_gf_ansi_flat_family_is_i2t():
    """The flat OPEN family is the standard GF I²t characteristic: T=1.05/M²
    floored at the labeled definite-time delay (corroborates the column map)."""
    flats = [s for s in _load()["scenarios"] if s["family"] == "flat"]
    assert flats, "expected the flat I²t open family in the corpus"
    for scn in flats:
        c = Coefficients(**scn["coeff"])
        # rA=rB=rC=rE=0, rD=1.05 → T = 1.05 / M²
        assert (c.c2, c.c3, c.c4, c.c6) == (0.0, 0.0, 0.0, 0.0)
        assert c.c5 == pytest.approx(1.05)
        # at M=2: 1.05/4 = 0.2625 (above every flat floor) — raw, not yet floored
        assert _EVAL(c, 2.0) == pytest.approx(max(1.05 / 4.0, c.c1))
        # deep on the floor: clamps to rTmin
        assert _EVAL(c, 100.0) == pytest.approx(c.c1)


def test_gf_ansi_floor_clamps_to_rtmin():
    """In the floor region the managed evaluator clamps to rTmin (== the native
    lin-log extension target)."""
    for scn in _load()["scenarios"]:
        c = Coefficients(**scn["coeff"])
        floor = scn["floor"]
        for amps, t in scn["points"]:
            if amps >= 1e9 or t > floor * 1.0001:
                continue
            prod = _EVAL(c, amps)
            if prod is not None:
                assert abs(prod - floor) < 1e-9 or abs(prod - t) < 1e-9, (
                    scn["label"], amps, prod, t,
                )


def test_ansi_coeff_routes_to_ansi_evaluator():
    """A coeff flagged is_ansi must NOT fall to the IEEE/Therm path — the
    inverse-family rows have c4<0 / c6!=0 which would silently mis-evaluate."""
    c = Coefficients(c1=0.001, c2=0.065048, c3=0.416414, c4=-0.6,
                     c5=-0.03903, c6=1.10257, is_ansi=True)
    assert not IEEEInverseTimeSolver._uses_native_therm_eq(c)
    # routed result equals the direct ANSI evaluation (not the IEEE fallback)
    direct = IEEEInverseTimeSolver._evaluate_native_ansi(c, 3.0)
    routed = IEEEInverseTimeSolver._evaluate(c, 3.0, 1.0, 0.0)
    assert routed == pytest.approx(direct)
