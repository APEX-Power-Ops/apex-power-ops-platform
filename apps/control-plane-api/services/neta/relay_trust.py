"""GR Relay Field-Trust Matrix — per-relay-section curve-trust classification.

Single in-API encoding of ``reference/tcc/GR-RELAY-REFERENCE.md`` §6 (the relay
field-trust matrix), applied to relay protective elements. The relay parallel to
``delay_trust.py`` (which gates breaker delay elements). It exists so a NETA *relay*
field sheet never badges an uncertified relay curve as field-authoritative.

Three trust tiers (GR §6 / mirrors G4 §0) plus one routing outcome:

  - ``"db"``          PROVEN (stored data). The relay's discrete settings (tap / pickup /
                      time-dial values) and the **raw Time/Current point grid** (Model 1
                      TCP) read **verbatim** — no solver, just stored data (GR §6 rows 1-2).
                      Field-authoritative, exactly as breaker pickups are in G4.
  - ``"verify"``      BOUNDED — the family solver is implemented and **formula-parity-
                      validated** against the published standard equation + live data (the
                      §69 non-circular parity harness, 6/6 families; IEC matched IEC-60255
                      to 4 sig figs), but **NOT yet proven bit-exact against the native
                      EasyPower renderer** (``CTccRelayCurveBase`` is a size-only shell,
                      GR §7). Covers the analytical families {IEC, MEQ, BSL, SWZ, PCD} and
                      TCP **interpolation** between stored points (GR §6 rows 3-4). Show the
                      curve, flagged; promotion to ``db`` is the captured-EasyPower-fixture
                      close (punch-list L10). (This refines GR §6 row 4's original
                      "withhold" to the breaker "verify" semantics — show-flagged, not
                      withheld — justified by the §69 parity.)
  - ``"unsupported"`` NOT IMPLEMENTED / hard-excluded. Bassler-0 (Model 0, legacy inline,
                      unregistered in the calc engine), RXD (7), LRM (8), EGC (9 — empty
                      both surfaces) have no validated evaluator — withhold (GR §6 rows 5-6).
  - ``"defer_g4"``    NOT a relay-trust tier. The SST-2 bridge relays
                      (``RelayDevices.Use_SST=1``; 39 live) delegate their trip behavior to
                      a borrowed breaker ETU sensor — gate the **curve** by the breaker G4
                      field-trust matrix (``delay_trust.py``) for that sensor, not here
                      (GR §6 row 7).

The relay model byte is ``RelayTDSection.Model`` (0-9). The supported/excluded partition
below mirrors ``apex_calc_engine.services.calc_engine.relay_types`` (SUPPORTED_FAMILIES /
UNSUPPORTED_FAMILIES); it is kept **local** so this trust module stays pure logic with no
calc-engine import (same design as ``delay_trust.py``). ``test_relay_trust.py`` asserts the
two stay in sync (drift guard).

NOTE (GR §0 / §6 row 1): the relay's **stored settings** (tap, pickup, time-dial) are
always ``db`` — they are read data, not solver output — exactly as breaker pickups are
always field-correct in G4. Only the **curve** (the time-current relationship) is gated.
"""
from __future__ import annotations

from typing import Optional

# Trust tiers, ordered most→least trustworthy, + the SST-2 routing outcome.
TRUST_DB = "db"
TRUST_VERIFY = "verify"
TRUST_UNSUPPORTED = "unsupported"
TRUST_DEFER_G4 = "defer_g4"

# Curve tiers that must NOT be rendered as a field-authoritative curve. "db" renders plain;
# "verify" renders flagged; "unsupported" withholds; "defer_g4" is gated by G4 elsewhere.
CURVE_WITHHELD = {TRUST_UNSUPPORTED}

# Element facets whose VALUE is stored data (always db — settings/points, not solver output).
_STORED_DATA_ELEMENTS = {"settings", "pickup", "tap", "time_dial", "tcp_points"}

# RelayTDSection.Model byte → family trust partition. Mirrors the calc engine's
# SUPPORTED_FAMILIES {TCP,IEC,MEQ,BSL,SWZ,PCD}=1..6 and UNSUPPORTED_FAMILIES {RXD,LRM,EGC}=7..9.
# Model 0 (UNKNOWN / Bassler-0) is unregistered in the calc engine → excluded here too.
_SUPPORTED_MODELS = frozenset({1, 2, 3, 4, 5, 6})
_EXCLUDED_MODELS = frozenset({0, 7, 8, 9})

_FAMILY_LABEL = {
    0: "Bassler-0 (legacy inline formula)",
    1: "TCP (Time/Current Points)",
    2: "IEC analytical",
    3: "MEQ (Multilin) analytical",
    4: "BSL (Basler / IEEE C37.112) analytical",
    5: "SWZ (Schweitzer/SEL) analytical",
    6: "PCD (ABB PCD2000) analytical",
    7: "RXD (RXIDG)",
    8: "LRM (Westinghouse IQ-1000)",
    9: "EGC (empty both surfaces)",
}


def _coerce_model(model_code: Optional[int]) -> Optional[int]:
    """Safe ``RelayTDSection.Model`` → int (``None`` if not an integer-like value)."""
    if model_code is None:
        return None
    try:
        return int(model_code)
    except (TypeError, ValueError):
        return None


def classify_relay_trust(
    element_key: str,
    *,
    model_code: Optional[int] = None,
    use_sst: bool = False,
) -> str:
    """Return the GR field-trust tier for one relay protective element.

    ``element_key`` — ``"settings"`` / ``"pickup"`` / ``"tap"`` / ``"time_dial"`` /
    ``"tcp_points"`` (all stored data → ``db``) or ``"curve"`` (the time-current curve,
    gated by ``model_code`` / ``use_sst``). Case-insensitive; any other key → unsupported.
    ``model_code`` — the ``RelayTDSection.Model`` byte (0-9).
    ``use_sst`` — the relay carries the SST-2 bridge (``RelayDevices.Use_SST=1``); its
    curve is delegated to a breaker ETU sensor → ``defer_g4``.
    """
    key = (element_key or "").lower()
    if key in _STORED_DATA_ELEMENTS:
        # Stored discrete settings + the raw TCP grid are read data, not solver output
        # (GR §6 rows 1-2). Always field-authoritative — independent of model/SST.
        return TRUST_DB
    if key != "curve":
        return TRUST_UNSUPPORTED
    # --- the time-current curve ---
    if use_sst:
        # SST-2 relay: trip behavior is the borrowed ETU sensor's; gate via G4 there.
        return TRUST_DEFER_G4
    model = _coerce_model(model_code)
    if model in _SUPPORTED_MODELS:
        # {TCP, IEC, MEQ, BSL, SWZ, PCD}: solver implemented + formula-parity-validated
        # (§69, 6/6), native render not proven (GR §7) → show flagged, not authoritative.
        return TRUST_VERIFY
    # Model 0 / 7 / 8 / 9 / unknown: no validated evaluator → withhold.
    return TRUST_UNSUPPORTED


def relay_curve_withheld(trust: str) -> bool:
    """True if a relay curve at this tier must NOT be rendered (withheld)."""
    return trust in CURVE_WITHHELD


def relay_family_label(model_code: Optional[int]) -> str:
    """Field-tech-facing relay family name for a ``RelayTDSection.Model`` byte."""
    model = _coerce_model(model_code)
    if model is None:
        return "unknown relay model"
    return _FAMILY_LABEL.get(model, f"relay model {model}")


def relay_trust_reason(
    element_key: str,
    trust: str,
    *,
    model_code: Optional[int] = None,
    use_sst: bool = False,
) -> str:
    """Short, field-tech-facing explanation of the relay trust tier for tooltips/notes."""
    key = (element_key or "").lower()
    if trust == TRUST_DB:
        if key == "tcp_points":
            return (
                "Stored Time/Current point grid (Model 1 TCP) read verbatim — stored data, "
                "no solver (GR §6 row 2). Field-authoritative."
            )
        return (
            "Stored relay setting (tap / pickup / time-dial) — read data, not solver "
            "output (GR §6 row 1). Field-authoritative."
        )
    if trust == TRUST_DEFER_G4:
        return (
            "SST-2 bridge relay (Use_SST=1) — trip behavior is delegated to a breaker ETU "
            "sensor; gate the curve by the breaker G4 field-trust matrix, not the relay "
            "solver (GR §6 row 7)."
        )
    if trust == TRUST_VERIFY:
        return (
            f"{relay_family_label(model_code)} curve — solver implemented and "
            "formula-parity-validated vs the published equation + live data (§69, 6/6 "
            "families), but NOT yet proven bit-exact against the native EasyPower renderer "
            "(CTccRelayCurveBase unrecovered, GR §7). Show flagged; the captured-fixture "
            "close (punch-list L10) is the verify->db gate."
        )
    # unsupported
    return (
        f"{relay_family_label(model_code)} — no validated relay evaluator (Bassler-0 "
        "legacy / RXD / LRM / EGC); curve withheld (GR §6 rows 5-6)."
    )
