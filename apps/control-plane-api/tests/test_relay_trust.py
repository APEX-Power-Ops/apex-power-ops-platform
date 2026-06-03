"""Tests for the GR relay field-trust classifier.

Encodes GR-RELAY-REFERENCE §6 (the relay field-trust matrix). Pure unit tests — no DB,
no app. The relay parallel to ``test_delay_trust.py``.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from services.neta.relay_trust import (
    TRUST_DB,
    TRUST_DEFER_G4,
    TRUST_UNSUPPORTED,
    TRUST_VERIFY,
    classify_relay_trust,
    relay_curve_withheld,
    relay_family_label,
    relay_trust_reason,
)


# ── Stored data: always db (settings + raw TCP grid; GR §6 rows 1-2) ──

@pytest.mark.parametrize("element", ["settings", "pickup", "tap", "time_dial", "tcp_points", "SETTINGS"])
@pytest.mark.parametrize("model_code", [0, 1, 2, 5, 8, 9, None])
@pytest.mark.parametrize("use_sst", [False, True])
def test_stored_data_always_db(element, model_code, use_sst):
    # Stored values are read data, not solver output — db regardless of model or SST-2.
    assert classify_relay_trust(element, model_code=model_code, use_sst=use_sst) == TRUST_DB


# ── Curve: supported families (TCP/IEC/MEQ/BSL/SWZ/PCD) → verify (GR §6 rows 3-4) ──

@pytest.mark.parametrize("model_code", [1, 2, 3, 4, 5, 6])
def test_supported_curve_is_verify(model_code):
    assert classify_relay_trust("curve", model_code=model_code) == TRUST_VERIFY


# ── Curve: excluded families (Bassler-0 / RXD / LRM / EGC) → unsupported (GR §6 rows 5-6) ──

@pytest.mark.parametrize("model_code", [0, 7, 8, 9])
def test_excluded_curve_is_unsupported(model_code):
    assert classify_relay_trust("curve", model_code=model_code) == TRUST_UNSUPPORTED


def test_curve_unknown_or_missing_model_is_unsupported():
    assert classify_relay_trust("curve", model_code=42) == TRUST_UNSUPPORTED
    assert classify_relay_trust("curve", model_code=None) == TRUST_UNSUPPORTED
    assert classify_relay_trust("curve", model_code="1") == TRUST_VERIFY  # numeric-string coerces


# ── SST-2 curve → defer_g4 (GR §6 row 7), overriding the model family ──

@pytest.mark.parametrize("model_code", [1, 2, 5, 0, 8, None])
def test_sst2_curve_defers_to_g4(model_code):
    assert classify_relay_trust("curve", model_code=model_code, use_sst=True) == TRUST_DEFER_G4


def test_sst2_does_not_change_stored_settings():
    # An SST-2 relay's stored tap/pickup/grid are still db; only the CURVE defers.
    assert classify_relay_trust("settings", use_sst=True) == TRUST_DB
    assert classify_relay_trust("tcp_points", use_sst=True) == TRUST_DB


# ── Unknown element key → unsupported ──

def test_unknown_element_is_unsupported():
    assert classify_relay_trust("inst", model_code=1) == TRUST_UNSUPPORTED
    assert classify_relay_trust("", model_code=1) == TRUST_UNSUPPORTED


def test_case_insensitive_element():
    assert classify_relay_trust("CURVE", model_code=2) == TRUST_VERIFY
    assert classify_relay_trust("Settings") == TRUST_DB


# ── withheld helper ──

def test_curve_withheld_only_for_unsupported():
    assert relay_curve_withheld(TRUST_UNSUPPORTED) is True
    assert relay_curve_withheld(TRUST_VERIFY) is False
    assert relay_curve_withheld(TRUST_DB) is False
    assert relay_curve_withheld(TRUST_DEFER_G4) is False


# ── family labels ──

def test_family_label():
    assert "TCP" in relay_family_label(1)
    assert "SEL" in relay_family_label(5)
    assert relay_family_label(None) == "unknown relay model"


# ── reasons present, distinct, tier-appropriate ──

def test_reasons_present_and_distinct():
    db_set = relay_trust_reason("settings", TRUST_DB)
    db_pts = relay_trust_reason("tcp_points", TRUST_DB)
    verify = relay_trust_reason("curve", TRUST_VERIFY, model_code=5)
    unsup = relay_trust_reason("curve", TRUST_UNSUPPORTED, model_code=8)
    g4 = relay_trust_reason("curve", TRUST_DEFER_G4, use_sst=True)
    for r in (db_set, db_pts, verify, unsup, g4):
        assert isinstance(r, str) and r.strip()
    assert len({db_set, db_pts, verify, unsup, g4}) == 5
    assert "69" in verify  # cites the §69 parity basis
    assert "G4" in g4 and "SST-2" in g4


# ── drift guard: local model partition must match the calc-engine family sets ──

def test_local_model_partition_matches_calc_engine():
    try:
        from apex_calc_engine.services.calc_engine.relay_types import (
            SUPPORTED_FAMILIES,
            UNSUPPORTED_FAMILIES,
        )
    except Exception:  # pragma: no cover - environment without calc-engine on path
        pytest.skip("calc-engine not importable in this environment")
    from services.neta.relay_trust import _EXCLUDED_MODELS, _SUPPORTED_MODELS

    assert {int(f) for f in SUPPORTED_FAMILIES} == set(_SUPPORTED_MODELS)
    # calc-engine UNSUPPORTED = {7,8,9}; relay_trust also folds in Model 0 (Bassler-0,
    # unregistered in the calc engine) → calc UNSUPPORTED ⊆ relay_trust excluded.
    assert {int(f) for f in UNSUPPORTED_FAMILIES}.issubset(_EXCLUDED_MODELS)
    # The two local sets partition the full 0-9 model space with no overlap.
    assert _SUPPORTED_MODELS.isdisjoint(_EXCLUDED_MODELS)
    assert _SUPPORTED_MODELS | _EXCLUDED_MODELS == set(range(10))
