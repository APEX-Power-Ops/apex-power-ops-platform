"""
Validated trip-unit setting catalog — cited vendor-doc override layer.
=====================================================================

Background (settings-correctness lane, 2026-06-02)
--------------------------------------------------
EasyPower's device library stores discrete dial positions for ~77% of ETU
sensors — one row per tap in the ``DatSection*`` tables (loaded into
``tcc.etu_*_pickups`` / ``tcc.etu_*_bands``). For the remaining ~23% — newer
digital trip units such as the Eaton Power Defense PXR2 — EasyPower stores only
the *envelope* (min/max endpoints) plus an internal calc step size.

For those "envelope-only" sensors the ``/settings`` endpoint was synthesising
dense, uniform option lists (e.g. LTPU 80, 81, ..., 225 A) that include settings
the breaker cannot physically be set to (e.g. 153 A), while the long-time delay
(LTD) collapsed to just its two endpoints (0.5 s, 24 s).

The real settable dial positions for those trip units come from the
manufacturer's documentation, **not** EasyPower. This module holds those
validated discrete positions, cited to the vendor document, keyed by
``(trip_style_id, rating)``. Per the field-trust discipline (G4) these taps are
authoritative because they are vendor-doc-validated; nothing is fabricated.

Adding a family
---------------
Add a :class:`CatalogEntry` to :data:`CATALOG`, cite the source document, and
provide the dial taps. ``ltpu`` units follow the sensor's ``ltpu_calc`` method
(amps when ``ltpu_calc == 7``; a multiple of In/Ir otherwise). For amps-based
long-time pickup the tap set is rating-specific, so key the entry by the exact
rating; multiplier/second-based elements (STPU/INST/LTD) are rating-independent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CatalogEntry:
    """Validated discrete dial positions for one trip-unit style at one rating.

    Any element left as ``None`` falls through to the existing EasyPower-derived
    behaviour (discrete rows when present, otherwise the range fallback).
    """

    style_name: str
    manufacturer: str
    source: str
    ltpu: Optional[list[float]] = None   # long-time pickup taps (unit per ltpu_calc)
    stpu: Optional[list[float]] = None   # short-time pickup taps (x Ir)
    inst: Optional[list[float]] = None   # instantaneous taps (x In)
    ltd: Optional[list[float]] = None    # long-time delay taps (seconds)
    notes: str = ""


# Keyed by (trip_style_id, rating). A rating of ``None`` applies style-wide.
CATALOG: dict[tuple[int, Optional[float]], CatalogEntry] = {
    # Eaton Power Defense — PXR2 20D/25 LSI, 225 A frame (trip_style_id 2204).
    # ltpu_calc == 7 (AMPS) → Ir taps are in amperes and rating-specific.
    (2204, 225.0): CatalogEntry(
        style_name="PXR2 20D/25 LSI",
        manufacturer="Eaton (Power Defense)",
        source="Eaton Power Defense Frame 2 TCC — TD012064EN (PXR 20/25 dial faces)",
        ltpu=[80, 90, 100, 110, 125, 150, 160, 175, 200, 225],   # Ir (A) @ In=225
        stpu=[1.5, 2, 3, 4, 5, 6, 8, 10, 12],                    # Isd (x Ir); OFF = edge
        inst=[2, 3, 4, 5, 6, 7, 8, 9],                           # Ii (x In); MAX = edge
        ltd=[0.5, 2, 4, 7, 10, 12, 15, 20, 24],                  # tr (s) @ 6x Ir
        notes=(
            "OFF (Isd short-time pickup) and MAX (Ii instantaneous) are real dial "
            "positions handled as edges, not yet wired. tsd/STD retains the EasyPower "
            "discrete rows for now. Ir taps are the 225 A frame; the 60/100/150 A "
            "ratings need their own dial sheets before being added."
        ),
    ),
}


def lookup(trip_style_id, rating) -> Optional[CatalogEntry]:
    """Return the validated catalog entry for a sensor, or ``None``.

    Tries an exact ``(trip_style_id, rating)`` match first, then a style-wide
    entry keyed with ``rating == None``.
    """
    if trip_style_id is None:
        return None
    try:
        sid = int(trip_style_id)
    except (TypeError, ValueError):
        return None

    r: Optional[float]
    try:
        r = float(rating) if rating is not None else None
    except (TypeError, ValueError):
        r = None

    entry = CATALOG.get((sid, r))
    if entry is not None:
        return entry
    return CATALOG.get((sid, None))


def pickup_unit(calc_code) -> str:
    """Display unit for a pickup option list, derived from its calc method.

    Mirrors ``ETUCalcMethod`` in the calc engine:
      7  AMPS            → "A"   (setting is already amperes)
      4  LTPU cascade    → "x Ir" (multiple of the long-time pickup)
      10 STPU cascade    → "x Isd" (multiple of the short-time pickup)
      0/1/2/3/5/6/8      → "x In" (frame- or plug-referenced)
    """
    try:
        c = int(calc_code)
    except (TypeError, ValueError):
        return "x In"
    if c == 7:
        return "A"
    if c == 4:
        return "x Ir"
    if c == 10:
        return "x Isd"
    return "x In"
