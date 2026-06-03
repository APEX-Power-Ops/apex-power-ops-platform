"""Route-1 (I2X / Iˣt) kernel parity — G4 §3b·I2X / STATE §113 / punch-list L4.

Validates the production ``etu_ixt`` power-law evaluator against DB-anchored
fixtures (``fixtures/i2x_ixt_db_anchored.json``) whose expected times are
hand-derived from the decompiled native ``CIxt`` closed form
(``t = T_anchor·(I_anchor/M)^X``, TccBase.dll 24248-24297) at binary-exact
multiples — an independent spec, not a restatement of the evaluator.

This is the I2X-3 parity foundation: it proves the managed Iˣt math + the
flat/ramp/composite shape dispatch + the field-trust gating (composite withheld)
BEFORE any live promotion. The native-CIxt oracle pass and the I2X=2 combine-rule
pinning remain the capstones (see fixture provenance).
"""
import json
import os

import pytest

from apex_calc_engine.services.calc_engine.etu_ixt import (
    EP_SENTINEL,
    SHAPE_COMPOSITE,
    SHAPE_FLAT,
    SHAPE_RAMP,
    SHAPE_UNKNOWN,
    i2x_delay_surface,
    i2x_shape,
    ixt_time,
)

_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "i2x_ixt_db_anchored.json")
_TOL = 1e-9


def _load():
    with open(_FIXTURE) as fh:
        return json.load(fh)


def _scenarios():
    return _load()["scenarios"]


def _by_label():
    return {s["label"]: s for s in _scenarios()}


def test_fixture_provenance_is_cixt_power_law():
    prov = _load()["provenance"]
    assert "CIxt" in prov["kernel"]
    assert "T_anchor" in prov["kernel"]
    assert "DatSection3STD" in prov["anchor_source"]


# ── the core power-law parity: evaluator vs hand-derived native-CIxt literals ──

@pytest.mark.parametrize("scn", [s for s in _scenarios() if s["shape"] == "ramp"],
                         ids=lambda s: s["label"])
def test_ixt_ramp_matches_native_cixt_literals(scn):
    x = scn["exp_x"]
    checked = 0
    for chk in scn["checks"]:
        m = chk["m"]
        got_open = ixt_time(m, scn["i_open"], scn["t_open"], x)
        got_clear = ixt_time(m, scn["i_clear"], scn["t_clear"], x)
        assert got_open is not None and got_clear is not None, (scn["label"], m)
        assert abs(got_open - chk["expected_open"]) < _TOL, (scn["label"], m, got_open, chk["expected_open"])
        assert abs(got_clear - chk["expected_clear"]) < _TOL, (scn["label"], m, got_clear, chk["expected_clear"])
        checked += 1
    assert checked >= 2  # every ramp scenario carries an anchor + at least one off-anchor point


@pytest.mark.parametrize("scn", [s for s in _scenarios() if s["shape"] == "ramp"],
                         ids=lambda s: s["label"])
def test_ixt_anchor_self_consistency(scn):
    """At M == I_anchor the power law must return exactly T_anchor."""
    assert ixt_time(scn["i_open"], scn["i_open"], scn["t_open"], scn["exp_x"]) == pytest.approx(scn["t_open"])
    assert ixt_time(scn["i_clear"], scn["i_clear"], scn["t_clear"], scn["exp_x"]) == pytest.approx(scn["t_clear"])


@pytest.mark.parametrize("scn", [s for s in _scenarios() if s["shape"] == "ramp"],
                         ids=lambda s: s["label"])
def test_ixt_monotonic_decreasing_in_current(scn):
    """Trip time strictly decreases as the test multiple rises (physics invariant)."""
    x, ia, ta = scn["exp_x"], scn["i_open"], scn["t_open"]
    prev = None
    for m in (1.0, 1.5, 2.0, 4.0, 8.0, 16.0):
        t = ixt_time(m, ia, ta, x)
        assert t is not None and t > 0.0
        if prev is not None:
            assert t < prev, (scn["label"], m, t, prev)
        prev = t


def test_x2_halving_current_quarters_time():
    """For X=2 (I²t), doubling current quarters the time — the defining property."""
    base = ixt_time(3.0, 6.0, 0.4, 2.0)
    dbl = ixt_time(6.0, 6.0, 0.4, 2.0)
    assert base / dbl == pytest.approx(4.0)


# ── shape dispatch + field-trust gating ──

def test_i2x_shape_mapping():
    assert i2x_shape(0) == SHAPE_FLAT
    assert i2x_shape(None) == SHAPE_FLAT
    assert i2x_shape(1) == SHAPE_RAMP
    assert i2x_shape(2) == SHAPE_COMPOSITE
    assert i2x_shape(2.0) == SHAPE_COMPOSITE
    assert i2x_shape(255) == SHAPE_UNKNOWN


def test_surface_ramp_supported_matches_evaluator():
    scn = _by_label()["s46-i2x1-x2-ramp"]
    surf = i2x_delay_surface(
        test_multiple=1.5, i2x_flag=1, exp_x=scn["exp_x"],
        i_open=scn["i_open"], t_open=scn["t_open"],
        i_clear=scn["i_clear"], t_clear=scn["t_clear"],
    )
    assert surf.supported and surf.shape == SHAPE_RAMP
    assert surf.expected_time == pytest.approx(6.400000095367432)
    # open < clear -> low = open, high = clear
    assert surf.time_low == pytest.approx(6.400000095367432)
    assert surf.time_high == pytest.approx(10.399999618530273)


def test_surface_composite_is_withheld():
    """I2X=2 composite combine rule is unconfirmed -> must be UNSUPPORTED (withheld)."""
    scn = _by_label()["s17-i2x2-x2-composite"]
    surf = i2x_delay_surface(
        test_multiple=1.5, i2x_flag=2, exp_x=scn["exp_x"],
        i_open=scn["i_open"], t_open=scn["t_open"],
        i_clear=scn["i_clear"], t_clear=scn["t_clear"],
        std_open=scn["std_open"], std_clear=scn["std_clear"],
    )
    assert surf.supported is False
    assert surf.shape == SHAPE_COMPOSITE
    assert "composite" in surf.reason.lower()


def test_surface_flat_is_current_independent():
    """I2X=0 flat band = the db-proven definite-time direct band; ignores the multiple."""
    a = i2x_delay_surface(test_multiple=1.5, i2x_flag=0, std_open=0.21, std_clear=0.31)
    b = i2x_delay_surface(test_multiple=8.0, i2x_flag=0, std_open=0.21, std_clear=0.31)
    assert a.supported and a.shape == SHAPE_FLAT
    assert a.expected_time == pytest.approx(0.21)
    assert a.time_low == pytest.approx(0.21) and a.time_high == pytest.approx(0.31)
    assert a.expected_time == b.expected_time  # current-independent


# ── native-CIxt degenerate guards (ComputeT 0.0 cases) -> None so callers withhold ──

@pytest.mark.parametrize("bad", [None, EP_SENTINEL])
def test_ixt_sentinel_and_none_guard(bad):
    assert ixt_time(bad, 6.0, 0.4, 2.0) is None
    assert ixt_time(1.5, bad, 0.4, 2.0) is None
    assert ixt_time(1.5, 6.0, bad, 2.0) is None
    assert ixt_time(1.5, 6.0, 0.4, bad) is None


def test_ixt_zero_guards():
    assert ixt_time(0.0, 6.0, 0.4, 2.0) is None   # M=0
    assert ixt_time(1.5, 0.0, 0.4, 2.0) is None   # I_anchor=0
    assert ixt_time(1.5, 6.0, 0.4, 0.0) is None   # X=0


def test_ixt_abs_exponent_matches_native_ctor():
    """CIxt ctor stores |dx|; a negative exponent must behave like its magnitude."""
    assert ixt_time(3.0, 6.0, 0.4, -2.0) == pytest.approx(ixt_time(3.0, 6.0, 0.4, 2.0))
