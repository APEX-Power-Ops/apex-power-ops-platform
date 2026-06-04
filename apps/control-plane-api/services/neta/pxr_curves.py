"""Eaton Power Defense (PDG2-6) + PXR 10/20/20D/25 — cited authoritative curve catalog.
================================================================================

The validated `[VENDOR-DOC]` model of the Eaton Power Defense molded-case breaker
family and its Power Xpert Release (PXR) electronic trip units, used to (a) serve the
correct time-current characteristic for the Power Defense frames and (b) drive the
SST-bridge correction (STATE §138/§139/§140) where EasyPower's library mis-maps or
imperfectly represents these (newer) frames.

Sources (operator-supplied, on host; values extracted, files NOT committed):
  * Eaton TCC documents: **TD012064EN** (PD2) · **TD012065EN** (PD3) · **TD012067EN** (PD5)
    · **TD012068EN** (PD6) — the per-frame setting ranges, slopes, and tolerances.
  * Eaton Power Xpert Protection Manager **PXR2025MCCB.xml** (the PXR25 setpoint model:
    Frame = Power Defense 2-6; Isd/tsd/Ir setting IDs + ranges).
  * Cross-ref: `reference/tcc/EATON-POWER-DEFENSE-PXR.md`, the §108 PXR2 setting catalog.

Key authoritative facts (TD012065EN/068EN):
  * The PXR trip is **selectable-slope** — long delay I2t *or* I4t; short delay
    **flat (definite)** *or* **I2t**. So a single fixed EasyPower `i2x` is an
    approximation; this module records the real (selectable) model.
  * Per-frame ratings differ; the per-unit curve model is shared by PXR variant.
"""

from __future__ import annotations

import re
from typing import Optional

SOURCE = (
    "Eaton Power Defense TCC docs TD012064/065/067/068EN + Power Xpert Protection "
    "Manager PXR2025MCCB.xml (PXR25 setpoint model)"
)

# --- Frame -> sensor ratings (A) -------------------------------------------------
# TD012064-068EN frame rating tables (standard global-UL PDG frames; H/PDC variants
# share the curve model). PD2 per the §108 PXR2 catalog.
POWER_DEFENSE_FRAMES: dict[str, list[int]] = {
    "PDG2": [60, 100, 125, 150, 160, 175, 200, 225, 250],
    "PDG3": [125, 250, 400, 600],
    "PDG4": [800, 1000, 1200],
    "PDG5": [800, 1200, 1600],
    "PDG6": [1600, 2000, 2500],
}

# --- Per-PXR-variant curve model (rating-independent) ----------------------------
# Ranges/slopes/tolerances verbatim from TD012065EN (PD3) — the curve model is the
# same across Power Defense frames; only the ratings differ. PXR 10 = the basic
# variant (reduced LD-time + SD ranges); PXR 20 / 20D / 25 share the full model.
_FULL_PXR = {
    "ld": {
        "pickup_pct_of_ir": 110,          # LDPU = 110% of Ir, +/-5%
        "ir_step_a": 1,                   # Ir set Min..Max in 1 A steps
        "time_min": 0.5, "time_max": 24.0, "time_step": 0.1,   # +0%/-30%
        "slopes": ("i2t", "i4t"),
    },
    "sd": {
        "isd_min": 1.5, "isd_max": 12.0, "isd_step": 0.1,      # +/-5%
        "tsd_min": 0.05, "tsd_max": 0.5, "tsd_step": 0.010,    # graded tol (see sd_time_tolerance)
        "slopes": ("flat", "i2t"),
    },
    "inst": {"pickup_min_xin": 2.0, "tol_pct": 10.0},          # +/-10%, + override (frame-specific)
    "gf": {"pickup_min_xin": 0.2, "pickup_max_xin": 1.0, "slopes": ("flat", "i2t")},
}

_BASIC_PXR10 = {
    "ld": {
        "pickup_pct_of_ir": 110, "ir_step_a": 1,
        "time_min": 0.5, "time_max": 7.0, "time_step": 0.1,    # PXR 10: LD time tops at 7 s
        "slopes": ("i2t", "i4t"),
    },
    "sd": {
        "isd_min": 1.5, "isd_max": 10.0, "isd_step": 0.5,      # PXR 10: 1.5-10x in 0.5x steps
        "tsd_min": 0.05, "tsd_max": 0.3, "tsd_step": 0.010,    # tsd 50-300 ms
        "slopes": ("flat", "i2t"),
    },
    "inst": {"pickup_min_xin": 2.0, "tol_pct": 10.0},
    "gf": {"pickup_min_xin": 0.2, "pickup_max_xin": 1.0, "slopes": ("flat", "i2t")},
}

PXR_VARIANTS: dict[str, dict] = {
    "PXR 10": _BASIC_PXR10,
    "PXR20": _FULL_PXR,
    "PXR20/25": _FULL_PXR,
    "PXR20D/PXR25": _FULL_PXR,
}

# Field-trust tolerances (the PE-value asset) — TD012065EN notes.
_TOLERANCES = {
    "ldpu": (-5.0, 5.0),
    "sdpu": (-5.0, 5.0),
    "inst": (-10.0, 10.0),
    "gfpu": (-10.0, 10.0),
    "ld_time": (-30.0, 0.0),
    # sd_time is graded -> use sd_time_tolerance()
}

# --- The SST-bridge correction map (STATE §139/§140) -----------------------------
# Each defective Power Defense frame -> the rating-correct (mfr, type, style) trip
# triple. PDG2 maps correctly already (no entry). Vendor-confirmed ratings:
# PD3 125-600 == PXR20 PDG3-LSI; PD5 800-1600 == PXR20 PDG5-LSI (shipped, migr 009);
# PD6 1600-2500 == PXR20 PDG6-LSIGM (PD6 also ships LSI -> LSIGM over-offers G; caveat).
_SST_CORRECTION: dict[str, tuple[str, str, str]] = {
    "PDG3": ("Eaton", "PXR20", "PDG3-LSI"),
    "PDG5": ("Eaton", "PXR20", "PDG5-LSI"),
    "PDG6": ("Eaton", "PXR20", "PDG6-LSIGM"),
}


def _frame_key(frame: Optional[str]) -> Optional[str]:
    """Normalize a frame label ("PDG3-F PXR 400A") to its family key ("PDG3")."""
    if not frame:
        return None
    m = re.match(r"\s*(PD[GFC]?\s*-?\s*([2-6]))", str(frame), re.IGNORECASE)
    if not m:
        return None
    return "PDG" + m.group(2)


def frame_ratings(frame: Optional[str]) -> list[int]:
    """Sensor ratings (A) for a Power Defense frame label; [] if unknown."""
    key = _frame_key(frame)
    return list(POWER_DEFENSE_FRAMES.get(key, [])) if key else []


def curve_model(pxr_variant: Optional[str]) -> Optional[dict]:
    """The rating-independent curve model for a PXR variant ('PXR 10' / 'PXR20' / ...)."""
    if not pxr_variant:
        return None
    return PXR_VARIANTS.get(str(pxr_variant).strip())


def tolerances(pxr_variant: Optional[str]) -> dict:
    """Field-trust tolerance windows (low%, high%) per element. Variant-independent
    for PD (the doc tolerances are common); arg kept for API symmetry / future deltas."""
    return dict(_TOLERANCES)


def sd_time_tolerance(tsd_seconds: float) -> tuple[float, float]:
    """Graded short-delay-time tolerance (low%, high%) for a tsd setting (TD012065EN):
    0.50-0.20 s -> +0/-20% · 0.19-0.16 s -> +0/-30% · 0.15-0.10 s -> +0/-40% ·
    0.09-0.05 s -> +0/-50%."""
    t = float(tsd_seconds)
    if t >= 0.20:
        return (-20.0, 0.0)
    if t >= 0.16:
        return (-30.0, 0.0)
    if t >= 0.10:
        return (-40.0, 0.0)
    return (-50.0, 0.0)


def correct_sst_target(frame: Optional[str]) -> Optional[tuple[str, str, str]]:
    """The rating-correct (mfr, type, style) SST triple for a defective Power Defense
    frame, or None if the frame maps correctly already (e.g. PDG2/PDG4)."""
    key = _frame_key(frame)
    return _SST_CORRECTION.get(key) if key else None
