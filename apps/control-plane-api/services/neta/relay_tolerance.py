"""
Relay tolerance serving layer (Chip 3) — cited [VENDOR-DOC] override + tier fallback.
====================================================================================

Background (relay-parity lane, 2026-06-03)
------------------------------------------
EasyPower does **not** compute or store a structured relay tolerance band (it plots relays as
nominal curves — see GR §7 / GR-RELAY-FIELD-DICTIONARY). The per-element field-test acceptance
tolerances come from outside EasyPower. This module serves them, in tier order:

  (0) **Enoserv [VENDOR-DOC] catalog** (PRIMARY) — ``data/relay_tolerance_catalog.json``, the
      manufacturer accuracy bands harvested from the operator's licensed Enoserv RTS install
      (values only; not Enoserv's test scripts). 155 of 1,442 governed relays match by name, on
      the workhorse legacy + modern US families (SEL, Westinghouse/ABB, GE, Basler, Beckwith, …).
  (1) **``Relays.Note`` OEM seed** — the free-text OEM tolerances EasyPower records for a small
      legacy/GF subset, parsed by :mod:`services.neta.relay_note_tolerance` (~24 relays).
  (2) **NETA generic floor** — not yet sourced; a miss is **withheld** (we never fabricate a band).

Matching is by ``(manufacturer, normalized relay_type)``: an exact normalized match first, then a
conservative *canonical* match that strips revision/order parentheticals (``CO-11(92)`` → CO-11)
and a trailing year/version (``SEL-751 - 2017`` → SEL-751). This is deliberately **not** fuzzy
matching (no prefix/family bridging) — it only removes suffixes that cannot change the relay model.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .relay_note_tolerance import parse_note_tolerances

_CATALOG_PATH = Path(__file__).parent / "data" / "relay_tolerance_catalog.json"

Band = Optional[tuple[float, float]]


# ── normalization ──

def normalize_relay_type(relay_type: Optional[str]) -> str:
    """Uppercase, strip every non-alphanumeric character."""
    return re.sub(r"[^A-Za-z0-9]", "", (relay_type or "")).upper()


def canonical_relay_type(relay_type: Optional[str]) -> str:
    """Conservative canonical form: drop revision parentheticals + a trailing year/version.

    ``CO-11(92)`` → ``CO11`` · ``SEL-751 - 2017`` → ``SEL751``. A leading qualifier is kept
    (``Hi Lo CO-9(99)`` → ``HILOCO9``) so we never bridge to a different family.
    """
    if not relay_type:
        return ""
    s = re.sub(r"\([^)]*\)", "", relay_type)        # revision/order parentheticals
    s = re.sub(r"\s*-\s*\d{4}\s*$", "", s)           # trailing " - 2017"
    s = re.sub(r"\s+\d{4}\s*$", "", s)               # trailing " 2017"
    return normalize_relay_type(s)


# ── catalog ──

@dataclass(frozen=True)
class RelayToleranceEntry:
    mfr: str
    relay_type: str
    ntype: str
    pickup_pct: Band
    pickup_abs: Band
    time_pct: Band
    time_abs: Band
    match_kind: str          # "exact" | "canonical"
    source: str


def _tup(v) -> Band:
    if not v:
        return None
    return (float(v[0]), float(v[1]))


def _load_catalog():
    raw = json.loads(_CATALOG_PATH.read_text())
    source = raw.get("_meta", {}).get("source", "Enoserv RTS")
    index: dict[tuple[str, str], dict] = {}
    for e in raw.get("entries", []):
        index[(e["mfr"], e["ntype"])] = e
    return index, source


_CATALOG_INDEX, _CATALOG_SOURCE = _load_catalog()


def lookup_relay_tolerance(mfr_name: str, relay_type: str) -> Optional[RelayToleranceEntry]:
    """Resolve a relay to its Enoserv [VENDOR-DOC] tolerance, or ``None``.

    Tries an exact normalized-type match first, then the conservative canonical match.
    """
    nt = normalize_relay_type(relay_type)
    e = _CATALOG_INDEX.get((mfr_name, nt))
    match_kind = "exact"
    if e is None:
        cnt = canonical_relay_type(relay_type)
        if cnt and cnt != nt:
            e = _CATALOG_INDEX.get((mfr_name, cnt))
            match_kind = "canonical"
    if e is None:
        return None
    return RelayToleranceEntry(
        mfr=e["mfr"], relay_type=e["type"], ntype=e["ntype"],
        pickup_pct=_tup(e.get("pickup_pct")), pickup_abs=_tup(e.get("pickup_abs")),
        time_pct=_tup(e.get("time_pct")), time_abs=_tup(e.get("time_abs")),
        match_kind=match_kind, source=_CATALOG_SOURCE,
    )


# ── serving result ──

@dataclass(frozen=True)
class FacetTolerance:
    pct_low: Optional[float]
    pct_high: Optional[float]
    abs_low: Optional[float]
    abs_high: Optional[float]
    unit: str                # "A" (pickup) | "s" (timing)


@dataclass(frozen=True)
class RelayToleranceResult:
    found: bool
    pickup: Optional[FacetTolerance]
    timing: Optional[FacetTolerance]
    provenance: str          # "vendor-doc" | "note" | "none"
    trust: str               # "validated" | "withheld"
    source: str
    match_kind: str          # "exact" | "canonical" | "note" | ""


def _facet(pct: Band, absb: Band, unit: str) -> Optional[FacetTolerance]:
    if not pct and not absb:
        return None
    return FacetTolerance(
        pct_low=pct[0] if pct else None, pct_high=pct[1] if pct else None,
        abs_low=absb[0] if absb else None, abs_high=absb[1] if absb else None,
        unit=unit,
    )


def _from_note(note: str) -> tuple[Optional[FacetTolerance], Optional[FacetTolerance]]:
    p_pct = p_abs = t_pct = t_abs = None
    for nt in parse_note_tolerances(note):
        rng = (float(nt.low), float(nt.high))
        facets = ("pickup", "time") if nt.facet == "general" else (nt.facet,)
        for f in facets:
            if f == "pickup":
                if nt.unit == "pct":
                    p_pct = p_pct or rng
                else:
                    p_abs = p_abs or rng
            elif f == "time":
                if nt.unit == "pct":
                    t_pct = t_pct or rng
                else:
                    t_abs = t_abs or rng
    return _facet(p_pct, p_abs, "A"), _facet(t_pct, t_abs, "s")


def serve_relay_tolerance(
    mfr_name: str, relay_type: str, note: Optional[str] = None
) -> RelayToleranceResult:
    """Serve a relay's per-element tolerance, applying the tier order (catalog > note > withheld)."""
    entry = lookup_relay_tolerance(mfr_name, relay_type)
    if entry is not None:
        return RelayToleranceResult(
            found=True,
            pickup=_facet(entry.pickup_pct, entry.pickup_abs, "A"),
            timing=_facet(entry.time_pct, entry.time_abs, "s"),
            provenance="vendor-doc", trust="validated",
            source=entry.source, match_kind=entry.match_kind,
        )
    if note:
        pickup, timing = _from_note(note)
        if pickup or timing:
            return RelayToleranceResult(
                found=True, pickup=pickup, timing=timing,
                provenance="note", trust="validated",
                source="EasyPower Relays.Note (OEM free text)", match_kind="note",
            )
    return RelayToleranceResult(
        found=False, pickup=None, timing=None,
        provenance="none", trust="withheld", source="", match_kind="",
    )
