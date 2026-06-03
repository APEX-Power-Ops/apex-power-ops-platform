"""Relay `Note`-field OEM-tolerance parser (Chip 3, tier-0 in-DB seed).

EasyPower carries no *structured* relay tolerance (GR §7), but records the OEM's stated
pickup/time accuracy as **free text in `Relays.Note`** for a small legacy/GF-heavy subset.
This module extracts those into structured `NoteTolerance` records so the relay NETA sheet
can seed its per-manufacturer tolerance tier from data already in the library.

**Precision over recall, by design.** The free text is heterogeneous and full of look-alikes
that are NOT tolerances — nominal operate-times ("Operate Time < 15 ms at 4x pickup"), setting
ranges ("90-110% of heater current rating"), voltage-restraint percentages, etc. So extraction
is gated on an explicit tolerance vocabulary (``tolerance`` / ``accuracy`` / ``variation``);
notes without it return ``[]``. A flagged value with the wrong element is worse than a miss on
a field sheet, so ambiguous matches are dropped or marked low-confidence rather than guessed.

Coverage is intentionally small (≈ dozens of relays) — this is a *seed*, not the whole story;
the NETA generic floor + an external accuracy catalog (e.g. Enoserv RTS) carry the rest.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# The precision gate: a note must contain one of these to be considered tolerance-bearing.
_TOLERANCE_GATE = re.compile(r"toleranc|accuracy|variation", re.IGNORECASE)

# Element keywords (longest/most-specific first) → canonical element.
_ELEMENT_PATTERNS = [
    (re.compile(r"long\s*time|\bLTPU\b|\bLT\b", re.IGNORECASE), "long_time"),
    (re.compile(r"short\s*time|\bSTPU\b|\bST\b", re.IGNORECASE), "short_time"),
    (re.compile(r"instantaneous|\binst\b|\bInstPU\b|\bIOC\b", re.IGNORECASE), "inst"),
    (re.compile(r"ground|\bGF\b|earth|\bGnd\b|residual", re.IGNORECASE), "ground"),
    (re.compile(r"\bTOC\b|\bTOCPU\b|time[\s-]*overcurrent|\b51\b", re.IGNORECASE), "toc"),
]
# Facet keywords → 'pickup' | 'time'.
_PICKUP_RE = re.compile(r"pickup|pick-?up|PU\b|\btap\b", re.IGNORECASE)  # PU\b also catches TOCPU/InstPU
_TIME_RE = re.compile(r"\btime\b|timing|trip\s*time|clearing|delay|operat", re.IGNORECASE)

# Value patterns.
_SYM_PCT = re.compile(r"~?\s*(?:±|\+/-|\+\s*-)\s*(\d+(?:\.\d+)?)\s*%")
_ASYM_PCT = re.compile(r"\+\s*(\d+(?:\.\d+)?)\s*%?\s*[,/]\s*-\s*(\d+(?:\.\d+)?)\s*%")
_ASYM_POS_PCT = re.compile(r"\+\s*(\d+(?:\.\d+)?)\s*%\s*to\s*\+\s*(\d+(?:\.\d+)?)\s*%")  # "+0% to +10%"
_BARE_PCT = re.compile(r"(\d+(?:\.\d+)?)\s*%")  # bare/tilde percent, used only on a tolerance-vocab line
_SYM_ABS = re.compile(r"~?\s*(?:±|\+/-|\+\s*-)\s*(\d+(?:\.\d+)?)\s*(ms|msec|millisecond[s]?|sec|second[s]?|cycle[s]?|s)\b", re.IGNORECASE)
_ASYM_ABS = re.compile(r"\+\s*(\d+(?:\.\d+)?)\s*/\s*-\s*(\d+(?:\.\d+)?)\s*(ms|msec|sec|second[s]?|cycle[s]?|s)\b", re.IGNORECASE)
# "Tolerance: Time - 10%" / "Pick-Up + - 10%" — facet word then a percent, under a tolerance line.
_LABELLED_PCT = re.compile(r"(pickup|pick-?up|\btime\b|\bPU\b)\s*[-:]?\s*~?\s*(?:±|\+/-|\+\s*-)?\s*(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)

# Lines that look like a tolerance value but are actually a setting range / nominal time → skip.
_RANGE_OR_OPERATE = re.compile(
    r"%\s*of\s+(?:rating|heater|coil|FLA|FLC|CT|rated|trip\s*value|pickup\s*setting)"
    r"|operat(?:e|ing)\s*time|of\s*(?:FLA|FLC)|current\s*rating",
    re.IGNORECASE,
)

_ABS_UNIT_SECONDS = {"ms": 1e-3, "msec": 1e-3, "millisecond": 1e-3, "milliseconds": 1e-3,
                     "s": 1.0, "sec": 1.0, "second": 1.0, "seconds": 1.0}


@dataclass(frozen=True)
class NoteTolerance:
    """One parsed tolerance band from a relay Note."""
    element: str          # 'toc'|'inst'|'long_time'|'short_time'|'ground'|'general'
    facet: str            # 'pickup'|'time'
    low: float            # signed lower bound (e.g. -5.0)
    high: float           # signed upper bound (e.g. +5.0)
    unit: str             # 'pct' | 's' | 'cycle'
    confidence: str       # 'high'|'medium'|'low'
    raw: str              # the source line (provenance)


def has_tolerance_signal(note: Optional[str]) -> bool:
    """True if the note contains explicit tolerance/accuracy vocabulary (the precision gate)."""
    return bool(note) and bool(_TOLERANCE_GATE.search(note))


def _facet_for(line: str) -> Optional[str]:
    has_pu = bool(_PICKUP_RE.search(line))
    has_time = bool(_TIME_RE.search(line))
    if has_pu and not has_time:
        return "pickup"
    if has_time and not has_pu:
        return "time"
    # neither, or an ambiguous line mentioning both → let the caller apply its default
    return None


def _element_for(line: str) -> str:
    for pat, name in _ELEMENT_PATTERNS:
        if pat.search(line):
            return name
    return "general"


def _abs_seconds(value: float, unit: str) -> tuple[float, str]:
    u = unit.lower().rstrip("s")
    if u in ("cycle",):
        return value, "cycle"
    factor = _ABS_UNIT_SECONDS.get(unit.lower(), _ABS_UNIT_SECONDS.get(u + "s", 1.0))
    return value * factor, "s"


def parse_note_tolerances(note: Optional[str]) -> list[NoteTolerance]:
    """Extract structured tolerance bands from a relay Note. ``[]`` if the note has no
    tolerance vocabulary (the precision gate) or nothing parseable."""
    if not has_tolerance_signal(note):
        return []
    out: list[NoteTolerance] = []
    for raw_line in note.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line or _RANGE_OR_OPERATE.search(line):
            continue  # blank, or a setting range / nominal operate time (not a tolerance)
        facet = _facet_for(line)
        element = _element_for(line)
        has_vocab = bool(re.search(r"toleranc|accuracy|variation", line, re.IGNORECASE))
        before = len(out)

        # asymmetric percent: "+0%, -15%"
        m = _ASYM_PCT.search(line)
        if m:
            out.append(NoteTolerance(element, facet or "time", -float(m.group(2)), float(m.group(1)),
                                     "pct", "high" if facet else "medium", line))
            continue
        # positive range: "+0% to +10%"
        m = _ASYM_POS_PCT.search(line)
        if m:
            out.append(NoteTolerance(element, facet or "time", float(m.group(1)), float(m.group(2)),
                                     "pct", "high" if facet else "medium", line))
            continue
        # asymmetric absolute: "+0/ -80 ms"
        m = _ASYM_ABS.search(line)
        if m:
            hi_v, _ = _abs_seconds(float(m.group(1)), m.group(3))
            lo_v, unit = _abs_seconds(float(m.group(2)), m.group(3))
            out.append(NoteTolerance(element, facet or "time", -lo_v, hi_v, unit,
                                     "high" if facet else "medium", line))
            continue
        # symmetric percent: "± 5%" / "+/- 10%"
        m = _SYM_PCT.search(line)
        if m:
            v = float(m.group(1))
            conf = "high" if (facet and has_vocab) else ("medium" if facet else "low")
            out.append(NoteTolerance(element, facet or "general", -v, v, "pct", conf, line))
            continue
        # symmetric absolute: "± 0.1 second" / "± 50 ms"
        m = _SYM_ABS.search(line)
        if m:
            v, unit = _abs_seconds(float(m.group(1)), m.group(2))
            conf = "high" if (facet and has_vocab) else "medium"
            out.append(NoteTolerance(element, facet or "time", -v, v, unit, conf, line))
            continue
        # labelled percent on a tolerance line: "Tolerance: Time - 10%, Pickup - 10%"
        if has_vocab:
            for lm in _LABELLED_PCT.finditer(line):
                label, val = lm.group(1).lower(), float(lm.group(2))
                lf = "pickup" if re.search(r"pickup|pick-?up|pu", label) else "time"
                out.append(NoteTolerance(element, lf, -val, val, "pct", "high", line))
            # bare/tilde percent fallback: a tolerance-vocab line with a plain "X%" and nothing matched
            if len(out) == before:
                bm = _BARE_PCT.search(line)
                if bm:
                    v = float(bm.group(1))
                    out.append(NoteTolerance(element, facet or "general", -v, v, "pct", "medium", line))
    return out
