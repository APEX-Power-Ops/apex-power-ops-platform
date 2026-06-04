"""Validated canonical Micrologic 6.0 A/E curve model — cited vendor-doc spec.
================================================================================

The Square D / Schneider Micrologic 6.0 A/E trip unit (Masterpact NW/NT,
Compact NS) is a full **LSIG** electronic trip unit. Its time-current
characteristic is, per element (Schneider doc ``micrologic_20_70a_eng`` —
"Long-time, short-time and instantaneous protection (Micrologic 5.0/6.0/7.0)" +
"Ground-fault protection (Micrologic 6.0 A/E)"):

  * **L (long-time):** I²t inverse — ``t(I) = tr·(6·Ir/I)²`` where ``Ir`` (long-time
    pickup) = 0.4…1·In and ``tr`` (the long-time delay band) is the trip time at
    6·Ir. Rendered by ``_synthesize_longtime_i2t`` (STATE §135; the §111 reference
    window, native-CIxt bit-exact I2X-4).
  * **S (short-time):** a route-1 (I2X) **composite** — an Iˣt-ON ramp clamped to an
    I²t-OFF definite floor (``max(ramp, floor)``). Isd = 1.5…10·Ir; the ramp
    references **Ir** (``M = I/Ir``); the ramp meets the floor at ``i_open = 10·Ir``.
  * **G (ground-fault):** the same I2X composite, but the ramp references **In**
    (``M = I/In``); the ramp meets the floor at ``i_open = 1·In``. Ig = A…J·In,
    1200 A max. (Micrologic **7.0** replaces ground-fault with earth-leakage Vigi
    IΔn — a residual-current/RCD function with no phase-overcurrent TCC; STATE §134.)
  * **I (instantaneous):** Ii = 2…15·In, definite at the breaker clearing time.

This module holds the **rating-independent** S/G band spec (the delay seconds + the
Iˣt anchors are the same on every 6.0A frame). It is validated two ways:

  1. **DB:** the governed ``tcc`` trip-style **246** "MICROLOGIC 6.0A" record carries
     exactly these bands (``etu_std_bands`` / ``etu_gfd_bands``: ``i2x=2``,
     ``i_open`` 10/1, the floor + ramp anchors below; ``stpu_i2t_val`` /
     ``gfpu_i2t_val`` = X = 2). The values here are copied verbatim from that record.
  2. **Datasheet:** the composite ramp meets the floor exactly at the ``i_open``
     anchor (10·Ir for S, 1·In for G), where the published curves flatten (STATE §136).

It is used as the **render/serving fallback for the band-LESS 6.0A style records**
(``tcc`` styles 238 / 1919 — the same device, but the STD/GFD band tables were not
loaded; ~158 sensors). The durable fix is reloading those styles from the source
library; until then this cited spec serves the validated bands (the Eaton-PXR2
"serve the validated characteristic where EasyPower's record is incomplete" pattern).
"""

from __future__ import annotations

from typing import Optional

SOURCE = (
    "Schneider Micrologic 2.0A-7.0A user manual (micrologic_20_70a_eng) + governed "
    "tcc trip_style 246 'MICROLOGIC 6.0A' band records (etu_std_bands/etu_gfd_bands)"
)

# Per-sensor Iˣt exponent for the 6.0A short-time + ground (DS3_I2T_VAL / DS1GF_I2T_VAL).
CANONICAL_I2X_EXPONENT = 2.0

# Short-time (S) bands — i2x=2 composite, ramp references Ir (i_open = 10·Ir).
# Keys mirror the etu_std_bands columns _load_i2x_curve_band returns.
CANONICAL_STD_BANDS: list[dict] = [
    {"i2x": 2, "i_open": 10, "t_open": 0.08, "i_clear": 10, "t_clear": 0.10, "floor_open": 0.08, "floor_clear": 0.14, "ordinal": 0, "desc": "0.1"},
    {"i2x": 2, "i_open": 10, "t_open": 0.16, "i_clear": 10, "t_clear": 0.20, "floor_open": 0.14, "floor_clear": 0.20, "ordinal": 1, "desc": "0.2"},
    {"i2x": 2, "i_open": 10, "t_open": 0.24, "i_clear": 10, "t_clear": 0.30, "floor_open": 0.23, "floor_clear": 0.32, "ordinal": 2, "desc": "0.3"},
    {"i2x": 2, "i_open": 10, "t_open": 0.32, "i_clear": 10, "t_clear": 0.40, "floor_open": 0.35, "floor_clear": 0.50, "ordinal": 3, "desc": "0.4"},
]

# Ground-fault (G) bands — i2x=2 composite (ramp references In, i_open = 1·In);
# ordinal 1 "Off" is the I²t-OFF flat (definite-time) minimum.
CANONICAL_GFD_BANDS: list[dict] = [
    {"i2x": None, "i_open": None, "t_open": None, "i_clear": None, "t_clear": None, "floor_open": 0.02, "floor_clear": 0.08, "ordinal": 1, "desc": "Off"},
    {"i2x": 2, "i_open": 1, "t_open": 0.08, "i_clear": 1, "t_clear": 0.10, "floor_open": 0.08, "floor_clear": 0.14, "ordinal": 2, "desc": "0.1"},
    {"i2x": 2, "i_open": 1, "t_open": 0.16, "i_clear": 1, "t_clear": 0.20, "floor_open": 0.14, "floor_clear": 0.20, "ordinal": 3, "desc": "0.2"},
    {"i2x": 2, "i_open": 1, "t_open": 0.24, "i_clear": 1, "t_clear": 0.30, "floor_open": 0.23, "floor_clear": 0.32, "ordinal": 4, "desc": "0.3"},
    {"i2x": 2, "i_open": 1, "t_open": 0.32, "i_clear": 1, "t_clear": 0.40, "floor_open": 0.35, "floor_clear": 0.50, "ordinal": 5, "desc": "0.4"},
]


def is_micrologic_6_0(style_name: Optional[str]) -> bool:
    """True for a Square D Micrologic 6.0 (A/E/P/H) trip-unit style label.

    The 6.0 designation is the LSIG variant whose S/G delays follow this canonical
    I2X composite spec. 5.0 (LSI, no ground) and 7.0 (earth-leakage) are excluded.
    """
    if not style_name:
        return False
    s = str(style_name).lower()
    return "micrologic" in s and "6.0" in s


def canonical_i2x_bands(element: str) -> Optional[list[dict]]:
    """The canonical 6.0A S/G band spec for ``element`` (``"std"`` / ``"gfd"``)."""
    key = (element or "").lower()
    if key == "std":
        return [dict(b) for b in CANONICAL_STD_BANDS]
    if key == "gfd":
        return [dict(b) for b in CANONICAL_GFD_BANDS]
    return None


def delay_bands_as_settings(element: str) -> Optional[list[dict]]:
    """The canonical S/G bands in the Screen-2 ``/settings`` delay-band shape
    (``band``/``label``/``open_time``/``clear_time``/``is_default``), so a band-less
    6.0A sensor's settings screen serves the validated delays (and the plot's
    availability gate stays consistent with it)."""
    bands = canonical_i2x_bands(element)
    if not bands:
        return None
    return [
        {
            "band": b["desc"],
            "label": b["desc"],
            "open_time": b["floor_open"],
            "clear_time": b["floor_clear"],
            "is_default": idx == 0,
        }
        for idx, b in enumerate(bands)
    ]
