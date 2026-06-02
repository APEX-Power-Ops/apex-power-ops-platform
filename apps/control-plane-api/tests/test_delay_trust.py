"""Tests for the G4 per-sensor delay-route field-trust classifier.

Encodes the G4-CALC-GUIDE §4 Field-Trust Matrix + §6 gating algorithm for delay
(time) elements. Pure unit tests — no DB, no app.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from services.neta.delay_trust import (
    TRUST_DB,
    TRUST_UNSUPPORTED,
    TRUST_VERIFY,
    classify_delay_trust,
    delay_route_for,
    delay_trust_reason,
)


# ── LTD: always DB (not SSTDelayCalc-routed; window methods 1-5 proven, G4 row 5) ──

@pytest.mark.parametrize("std_route", [0, 1, 2, 3, None])
@pytest.mark.parametrize("gfd_route", [0, 1, 2, 4, None])
def test_ltd_is_always_db(std_route, gfd_route):
    assert classify_delay_trust("ltd", std_route=std_route, gfd_route=gfd_route) == TRUST_DB


# ── STD path (stpu_delay_calc_code / DS3_SEC3_I2T) ──

@pytest.mark.parametrize(
    "route,expected",
    [
        (0, TRUST_DB),           # direct-band DatSection3STD — PROVEN (row 3)
        (2, TRUST_DB),           # INVEQ Therm — BIT-EXACT native parity, PROMOTED (row 6, G4 §5)
        (1, TRUST_UNSUPPORTED),  # I2X — solver not built (row 11)
        (3, TRUST_UNSUPPORTED),  # GE-TU STD — fall-through diagnostic (row 9)
        (None, TRUST_UNSUPPORTED),
        (99, TRUST_UNSUPPORTED),
    ],
)
def test_std_route_classification(route, expected):
    assert classify_delay_trust("std", std_route=route) == expected


# ── GFD path (ground_delay_calc_code / DS1GF_SEC3_I2T) ──

@pytest.mark.parametrize(
    "route,is_ansi,expected",
    [
        (0, False, TRUST_DB),            # direct-band DatSection1GfGFD — PROVEN (row 4)
        (2, False, TRUST_VERIFY),        # INVEQ Therm — fixtures pending (row 7-Therm)
        (2, True, TRUST_UNSUPPORTED),    # INVEQ ANSI family — hard-excluded (row 7-Ansi, G4 §3e)
        (1, False, TRUST_UNSUPPORTED),   # I2X — solver not built (row 11)
        (4, False, TRUST_UNSUPPORTED),   # GE-TU ground — fall-through (row 10)
        (None, False, TRUST_UNSUPPORTED),
    ],
)
def test_gfd_route_classification(route, is_ansi, expected):
    assert classify_delay_trust("gfd", gfd_route=route, gfd_is_ansi=is_ansi) == expected


def test_gfd_ansi_only_matters_on_route_2():
    # ANSI flag must not accidentally promote/demote a direct-band (route 0) GFD.
    assert classify_delay_trust("gfd", gfd_route=0, gfd_is_ansi=True) == TRUST_DB


def test_unknown_element_is_unsupported():
    assert classify_delay_trust("inst", std_route=0) == TRUST_UNSUPPORTED
    assert classify_delay_trust("", std_route=0) == TRUST_UNSUPPORTED


def test_case_insensitive_element_key():
    assert classify_delay_trust("STD", std_route=0) == TRUST_DB
    assert classify_delay_trust("Gfd", gfd_route=2) == TRUST_VERIFY


# ── delay_route_for: raw route byte the element is governed by ──

def test_delay_route_for():
    assert delay_route_for("std", std_route=2, gfd_route=0) == 2
    assert delay_route_for("gfd", std_route=2, gfd_route=4) == 4
    assert delay_route_for("ltd", std_route=2, gfd_route=4) is None


# ── reasons are non-empty and tier-appropriate ──

def test_reasons_present_and_distinct():
    db = delay_trust_reason("std", TRUST_DB, route=0)
    db_inveq = delay_trust_reason("std", TRUST_DB, route=2)
    verify = delay_trust_reason("gfd", TRUST_VERIFY, route=2)
    unsup = delay_trust_reason("std", TRUST_UNSUPPORTED, route=1)
    ansi = delay_trust_reason("gfd", TRUST_UNSUPPORTED, route=2, gfd_is_ansi=True)
    for r in (db, db_inveq, verify, unsup, ansi):
        assert isinstance(r, str) and r.strip()
    assert len({db, db_inveq, verify, unsup, ansi}) == 5
    assert "ANSI" in ansi
    # STD route-2 db reason must cite the native-kernel parity, not "direct-band"
    assert "BIT-EXACT" in db_inveq and "direct-band" not in db_inveq.lower()
    assert delay_trust_reason("ltd", TRUST_DB).startswith("LTD")
