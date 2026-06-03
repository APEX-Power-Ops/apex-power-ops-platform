"""Tests for the relay Note-field OEM-tolerance parser (Chip 3 tier-0).

Synthetic examples mirroring the real `Relays.Note` formats (the raw notes are kept out of
the repo). Covers each tolerance shape + the precision-gate / false-positive rejections.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from services.neta.relay_note_tolerance import (
    NoteTolerance,
    has_tolerance_signal,
    parse_note_tolerances,
)


def _one(note):
    tols = parse_note_tolerances(note)
    assert len(tols) == 1, tols
    return tols[0]


# ── precision gate ──

@pytest.mark.parametrize("note", [None, "", "Just a model note, no accuracy data.",
                                  "Operate Time: < 15 ms at 4 x pickup", "90-110% of heater current rating"])
def test_no_tolerance_vocab_yields_nothing(note):
    assert parse_note_tolerances(note) == []


def test_has_tolerance_signal():
    assert has_tolerance_signal("TOC pickup tolerance ~ +/- 5%")
    assert has_tolerance_signal("Trip Time Accuracy : +0%, -15%")
    assert has_tolerance_signal("All Variations are +/- 5%")
    assert not has_tolerance_signal("Operate Time < 15 ms at 4x pickup")


# ── false positives a tolerance-vocab note must still reject (range / operate-time lines) ──

def test_rejects_setting_range_and_operate_time_lines():
    note = ("Pickup tolerance ~ +/- 5%\n"
            "Current Setting: 85 to 115% of heater current rating\n"   # range → skip
            "Operate Time: < 15 ms at 4 x pickup")                      # nominal time → skip
    tols = parse_note_tolerances(note)
    assert len(tols) == 1 and tols[0].low == -5.0 and tols[0].high == 5.0


# ── symmetric percent ──

def test_symmetric_pct_with_element_and_facet():
    t = _one("TOC pickup tolerance ~ +/- 5%")
    assert (t.element, t.facet, t.low, t.high, t.unit, t.confidence) == ("toc", "pickup", -5.0, 5.0, "pct", "high")


def test_instantaneous_pickup_pct():
    t = _one("Instantaneous pickup tolerance ~ +/- 10%")
    assert (t.element, t.facet, t.low, t.high) == ("inst", "pickup", -10.0, 10.0)


# ── bare / tilde percent (no sign) on a tolerance-vocab line ──

def test_bare_percent_tolerance():
    t = _one("Delay clearing time assumed at 12% tolerance.")
    assert (t.facet, t.low, t.high, t.unit) == ("time", -12.0, 12.0, "pct")


def test_tilde_percent_pickup_unit_suffix():
    # "TOCPU"/"InstPU" — PU suffix should resolve facet=pickup, element from the unit name
    t = _one("TOCPU tolerance ~15%")
    assert (t.element, t.facet, t.low, t.high) == ("toc", "pickup", -15.0, 15.0)


# ── asymmetric percent + positive range ──

def test_asymmetric_percent():
    t = _one("Trip Time Accuracy : +0%, -15%")
    assert (t.facet, t.low, t.high) == ("time", -15.0, 0.0)


def test_positive_range_percent():
    t = _one("Instantaneous Tolerance +0% to +10%")
    assert (t.element, t.low, t.high) == ("inst", 0.0, 10.0)


# ── absolute time tolerances ──

def test_symmetric_abs_seconds():
    t = _one("Time Delay tolerance ~ +/- 0.1 second")
    assert (t.facet, t.unit, t.low, t.high) == ("time", "s", -0.1, 0.1)


def test_symmetric_abs_ms_converts_to_seconds():
    t = _one("Accuracy : +/- 50 ms for nominal tripping time")
    assert t.unit == "s" and t.low == pytest.approx(-0.05) and t.high == pytest.approx(0.05)


def test_asymmetric_abs_ms():
    t = _one("Tolerance is +0/ -80 ms of setting")
    assert t.unit == "s" and t.low == pytest.approx(-0.08) and t.high == 0.0


# ── labelled tolerance line → two facets ──

def test_labelled_time_and_pickup():
    tols = parse_note_tolerances("Tolerance: Time - 10% Pickup - 10%")
    facets = {(t.facet, t.low, t.high) for t in tols}
    assert ("time", -10.0, 10.0) in facets
    assert ("pickup", -10.0, 10.0) in facets


# ── blanket "All Variations" ──

def test_blanket_variation_general():
    t = _one("All Variations are +/- 5%")
    assert (t.element, t.facet, t.low, t.high, t.confidence) == ("general", "general", -5.0, 5.0, "low")


# ── per-element pickup table (Fed Pioneer Digital 600 shape) ──

def test_per_element_table_long_short():
    note = ("Pickup Element  Tolerance\n"
            "Long Time   +/- 5%\n"
            "Short Time  +/- 5%\n"
            "Instantaneous  +/- 10%")
    tols = parse_note_tolerances(note)
    elems = {t.element for t in tols}
    assert {"long_time", "short_time", "inst"} <= elems
