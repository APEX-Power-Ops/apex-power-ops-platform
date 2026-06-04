"""Tests for the relay tolerance serving layer (Chip 3).

The serving layer resolves a relay (manufacturer + relay_type) to its per-element pickup/timing
acceptance tolerance, applying the tier order: Enoserv [VENDOR-DOC] catalog (PRIMARY) ->
`Relays.Note` OEM seed -> (NETA floor, not yet sourced -> withheld). Asserts against real catalog
entries (stable) plus synthetic notes.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from services.neta.relay_tolerance import (
    canonical_relay_type,
    lookup_relay_tolerance,
    normalize_relay_type,
    serve_relay_tolerance,
)


# ── normalization ──

def test_normalize_strips_to_alnum_upper():
    assert normalize_relay_type("SEL-751") == "SEL751"
    assert normalize_relay_type("BE1-50/51B") == "BE15051B"
    assert normalize_relay_type("  co-11  ") == "CO11"


def test_canonical_strips_parenthetical_and_trailing_year():
    assert canonical_relay_type("CO-11(92)") == "CO11"
    assert canonical_relay_type("SEL-751 - 2017") == "SEL751"
    # a leading qualifier is preserved (conservative — no false bridge to a different family)
    assert canonical_relay_type("Hi Lo CO-9(99)") == "HILOCO9"


# ── exact catalog lookup ──

def test_lookup_exact_sel751():
    e = lookup_relay_tolerance("Schweitzer", "SEL-751")
    assert e is not None
    assert e.match_kind == "exact"
    assert e.pickup_pct == (-5.0, 5.0)
    assert e.time_pct == (-5.0, 5.0)


def test_lookup_exact_westinghouse_co11_timing_is_ten_percent():
    e = lookup_relay_tolerance("Westinghouse", "CO-11")
    assert e is not None and e.match_kind == "exact"
    assert e.pickup_pct == (-5.0, 5.0)
    assert e.time_pct == (-10.0, 10.0)


# ── canonical (safe) lookup — revision/year suffixes ──

def test_lookup_canonical_co11_revision_suffix():
    e = lookup_relay_tolerance("ABB", "CO-11(92)")
    assert e is not None
    assert e.match_kind == "canonical"
    assert e.pickup_pct == (-5.0, 5.0)


def test_lookup_canonical_sel751_year_suffix():
    e = lookup_relay_tolerance("Schweitzer", "SEL-751 - 2017")
    assert e is not None and e.match_kind == "canonical"
    assert e.pickup_pct == (-5.0, 5.0)


def test_lookup_miss_returns_none():
    assert lookup_relay_tolerance("GE", "Totally-Made-Up-999") is None
    assert lookup_relay_tolerance("Nonexistent Mfr", "SEL-751") is None


# ── serve: tier order + trust ──

def test_serve_vendor_doc_is_primary():
    r = serve_relay_tolerance("Schweitzer", "SEL-751")
    assert r.found
    assert r.provenance == "vendor-doc"
    assert r.trust == "validated"
    assert r.pickup.pct_low == -5.0 and r.pickup.pct_high == 5.0
    assert r.pickup.unit == "A"
    assert r.timing.unit == "s"
    assert "Enoserv" in r.source


def test_serve_falls_back_to_note_when_not_in_catalog():
    # Cutler-Hammer isn't an Enoserv-matched manufacturer -> catalog miss -> note tier
    note = "TOC pickup tolerance ~ +/- 10%"
    r = serve_relay_tolerance("Cutler-Hammer", "D64RPB100", note=note)
    assert r.found
    assert r.provenance == "note"
    assert r.pickup.pct_low == -10.0 and r.pickup.pct_high == 10.0


def test_serve_total_miss_is_withheld():
    r = serve_relay_tolerance("Toshiba", "ICO17D", note=None)
    assert not r.found
    assert r.provenance == "none"
    assert r.trust == "withheld"
    assert r.pickup is None and r.timing is None


def test_serve_catalog_wins_over_note():
    # even if a note is supplied, the structured Enoserv catalog takes precedence
    r = serve_relay_tolerance("Schweitzer", "SEL-751", note="pickup tolerance +/- 20%")
    assert r.provenance == "vendor-doc"
    assert r.pickup.pct_high == 5.0
