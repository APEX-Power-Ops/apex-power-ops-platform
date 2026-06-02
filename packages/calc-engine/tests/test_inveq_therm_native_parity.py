"""G4 §5 InvEq-Therm captured-fixture parity (the field-trust promotion gate).

These tests close the long-standing InvEq numeric-parity gap by validating the
production ``IEEEInverseTimeSolver`` native-Therm branch against curve points
**captured from the actual EasyPower native kernel** — ``CalcThermEq`` /
``CalcThermEq3`` in ``TccBase.dll`` — executed in-process by the oracle harness
under ``output/inveq-parity/oracle/``. The captured points live in
``fixtures/inveq_therm_native_parity.json`` so this regression runs without the
(x86, Windows-only) DLL.

Findings encoded here (see G4 §3e/§4/§5/§6):
  * STD route-2 Therm is the COMPLETE 4-dial curve space and is reproduced
    BIT-EXACT by production  → promoted "verify"→"db" in delay_trust.py.
  * GF route-2 Therm runs the byICalc=1 path (num3=field13 != pickup); production
    assumes num3=num6 and for rIRef<rM returns None outright → kept WITHHELD.
"""
import json
import os

import pytest

from apex_calc_engine.services.calc_engine.etu_curves import (
    Coefficients,
    IEEEInverseTimeSolver,
)

_FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "inveq_therm_native_parity.json"
)

_EVAL = IEEEInverseTimeSolver._evaluate_native_therm


def _load():
    with open(_FIXTURE) as fh:
        return json.load(fh)


def _by_label():
    return {s["label"]: s for s in _load()["scenarios"]}


def _smooth_points(scn):
    """Yield (I_norm, native_t) for the smooth curve region only.

    Skips point[0] (the asymptote anchor at I == rM, where production correctly
    returns None) and the rTmin floor knee (native uses a linear-log extension
    there; production clamps — both floor at rTmin)."""
    rM = scn["coeff"]["c5"]
    floor = scn["floor"]
    for amps, t in scn["points"]:
        if amps <= rM + 1e-9:
            continue
        if t <= floor * 1.0001:
            continue
        yield amps, t  # pickup == 1.0 -> amps == I_norm


def test_fixture_provenance_is_native_kernel():
    prov = _load()["provenance"]
    assert "TccBase.dll" in prov["oracle"]
    assert "CalcThermEq" in prov["functions"]


@pytest.mark.parametrize("dial", ["0.08", "0.14", "0.23", "0.35"])
def test_std_therm_bit_exact_vs_native_gf_fn(dial):
    """Entire STD Therm corpus (4 dial curves) reproduced bit-exact."""
    scn = _by_label()[f"STD-gf-d{dial}"]
    coeff = Coefficients(**scn["coeff"])
    checked = 0
    for i_norm, native_t in _smooth_points(scn):
        prod = _EVAL(coeff, i_norm)
        assert prod is not None, (dial, i_norm, native_t)
        assert abs(prod - native_t) < 1e-9, (dial, i_norm, prod, native_t)
        checked += 1
    assert checked >= 70  # ~83 smooth points per curve


@pytest.mark.parametrize("dial", ["0.08", "0.14", "0.23", "0.35"])
def test_std_gf_and_sst_native_functions_agree(dial):
    """GF CalcThermEq (byICalc=0) and SST CalcThermEq3 (byICalc=11) emit the
    identical native curve — confirms STD and GF share one Therm evaluator."""
    by = _by_label()
    g = by[f"STD-gf-d{dial}"]["points"]
    s = by[f"STD-sst-d{dial}"]["points"]
    assert len(g) == len(s) and len(g) > 0
    for (ag, tg), (as_, ts) in zip(g, s):
        assert abs(ag - as_) < 1e-9
        assert abs(tg - ts) < 1e-9


def test_std_sst_fn_also_bit_exact_vs_production():
    for dial in ["0.08", "0.14", "0.23", "0.35"]:
        scn = _by_label()[f"STD-sst-d{dial}"]
        coeff = Coefficients(**scn["coeff"])
        for i_norm, native_t in _smooth_points(scn):
            assert abs(_EVAL(coeff, i_norm) - native_t) < 1e-9


def test_gf_byicalc1_diverges_from_production():
    """WHY GF route-2 Therm stays withheld: the real GF path is byICalc=1
    (num3=field13 != pickup); production assumes num3=num6, so its GF curve is
    not native-faithful."""
    scn = _by_label()["GFbic1-f13eq2-d0.14"]
    coeff = Coefficients(**scn["coeff"])
    diverged = False
    compared = 0
    for i_norm, native_t in _smooth_points(scn):
        compared += 1
        prod = _EVAL(coeff, i_norm)
        if prod is None or abs(prod - native_t) > 1e-3:
            diverged = True
    # also count the I<=rM anchor where production None vs native real curve
    assert diverged or compared == 0
    if compared == 0:
        # all native points at/below floor or anchor; still a divergence because
        # production can't represent the byICalc=1 vertical scale — assert anchor
        anchor_amps = scn["points"][0][0]
        assert _EVAL(coeff, anchor_amps) is None


def test_gf_riref_lt_rm_unrepresentable_by_production():
    """GF rIRef<rM: native produces a real curve via field13; production returns
    None for every input (rIRef <= rM) -> must stay withheld, never a number."""
    scn = _by_label()["GF048-f13eq2-d0.14"]
    coeff = Coefficients(**scn["coeff"])
    floor = scn["floor"]
    assert any(t > floor * 1.0001 for _, t in scn["points"])  # native has a curve
    for amps, _t in scn["points"]:
        assert _EVAL(coeff, amps) is None  # production cannot represent it
