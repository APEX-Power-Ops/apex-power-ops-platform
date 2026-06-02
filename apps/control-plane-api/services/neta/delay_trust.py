"""G4 Field-Trust Matrix — per-sensor delay-route → field-trust classification.

Single in-API encoding of `reference/tcc/G4-CALC-GUIDE.md` §4 (the Field-Trust
Matrix) and §6 (the per-sensor gating algorithm), applied to *delay* (time)
elements (LTD / STD / GFD). It exists so the LV field sheet never badges an
uncertified delay TIME as field-authoritative.

Three trust tiers (G4 §0 / §4):

  - ``"db"``          PROVEN. Direct-band solvers (STD route 0 ``DatSection3STD`` /
                      GFD route 0 ``DatSection1GfGFD``), the LTD window (methods 1-5,
                      implementation complete), and **STD INVEQ (route 2) Therm** —
                      validated BIT-EXACT against the native EasyPower ``TccBase.dll``
                      ``CalcThermEq``/``CalcThermEq3`` kernel over the complete STD
                      Therm 4-dial corpus (G4 §5; captured-fixture parity closed
                      2026-06-01). Numerically validated — field-safe. (G4 rows 3/4/5/6.)
  - ``"verify"``      DISPATCH-WIRED, parity not yet closed. **GFD INVEQ (route 2)
                      Therm** only: the native ``CalcThermEq`` formula is recovered +
                      patched, but the GF runtime path uses ``byICalc=1``
                      (``num3=field13`` ≠ pickup) which the managed solver's
                      ``num3=num6`` form does not reproduce, and ``rIRef<rM`` GF rows
                      return None outright (G4 §5, row 7-Therm). Show the engine's best
                      estimate, flagged; promotion pending ``field13`` provenance.
  - ``"unsupported"`` NOT IMPLEMENTED / hard-excluded. I2X (route 1, I²t solver not
                      built), GE trip-unit STD/Gnd (routes 3/4, fall-through
                      diagnostic only), and the GF-INVEQ ANSI family
                      (``id_op_eq != 0`` on a GFD route-2 row — 23 sensors). The
                      solver is not built, so the band/curve number is a meaningless
                      fall-through — withhold it (G4 §6 step 6; rows 7-Ansi/9/10/11).

``SSTDelayCalc`` routing byte (G4 §3a): 0 NONE/direct-band · 1 I2X · 2 INVEQ ·
3 TUSTD · 4 TUG. STD path = ``etu_sensors.stpu_delay_calc_code`` (``DS3_SEC3_I2T``);
GFD path = ``etu_sensors.ground_delay_calc_code`` (``DS1GF_SEC3_I2T``).

NOTE on the test POINT vs the expected TIME (G4 §4 note): this module governs only
the trust of the expected trip *time*. The NETA test multiple and the inject current
(= multiple × the element's *proven* pickup current) are always field-correct and are
NOT gated here.
"""
from __future__ import annotations

from typing import Optional

# Trust tiers, ordered most→least trustworthy.
TRUST_DB = "db"
TRUST_VERIFY = "verify"
TRUST_UNSUPPORTED = "unsupported"

# Whether a tier's expected-TIME value is field-authoritative enough to render on
# the field sheet. Only "db" is; "verify" is shown flagged; "unsupported" is withheld.
TIME_WITHHELD = {TRUST_UNSUPPORTED}

_ROUTE_NAME = {
    0: "direct-band",
    1: "I²t/Iˣt (I2X)",
    2: "inverse-equation",
    3: "GE trip-unit short-time",
    4: "GE trip-unit ground",
}


def classify_delay_trust(
    element_key: str,
    *,
    std_route: Optional[int] = None,
    gfd_route: Optional[int] = None,
    gfd_is_ansi: bool = False,
) -> str:
    """Return the G4 field-trust tier for one delay element.

    ``element_key`` is one of ``"ltd"`` / ``"std"`` / ``"gfd"`` (case-insensitive).
    ``std_route`` / ``gfd_route`` are the persisted ``SSTDelayCalc`` route bytes.
    ``gfd_is_ansi`` marks a GFD route-2 sensor whose GF-INVEQ family is ANSI
    (``id_op_eq != 0``) — hard-excluded per G4 §3e.
    """
    key = (element_key or "").lower()
    if key == "ltd":
        # LTD is NOT routed by SSTDelayCalc; its window (methods 1-5) is
        # implementation-complete and window-proven (G4 §3c / row 5). The
        # DS2_DLY_PTY parity edge is flagged separately and does not demote the
        # window itself.
        return TRUST_DB
    if key == "std":
        return _classify_std(std_route)
    if key == "gfd":
        return _classify_gfd(gfd_route, gfd_is_ansi)
    return TRUST_UNSUPPORTED


def _classify_std(route: Optional[int]) -> str:
    if route == 0:
        return TRUST_DB
    if route == 2:
        # STD INVEQ is 100% Therm corpus-wide (G4 §3e) and runs byICalc=0
        # (IdOpICalc=4 → num3=field16=pickup). The managed solver reproduces the
        # native CalcThermEq kernel BIT-EXACT over the entire STD Therm corpus
        # (only 4 dial curves; G4 §5, captured-fixture parity closed 2026-06-01).
        return TRUST_DB
    return TRUST_UNSUPPORTED  # 1 I2X / 3 TUSTD / None / other


def _classify_gfd(route: Optional[int], is_ansi: bool) -> str:
    if route == 0:
        return TRUST_DB
    if route == 2:
        # GFD INVEQ: ANSI family hard-excluded (G4 §3e). GF Therm stays "verify"
        # (NOT promoted with STD): the GF runtime path is byICalc=1
        # (num3=field13 ≠ pickup), which the managed num3=num6 form does not
        # reproduce, and rIRef<rM GF rows yield None (G4 §5). Promotion to "db"
        # is gated on field13 provenance + native-oracle re-validation.
        return TRUST_UNSUPPORTED if is_ansi else TRUST_VERIFY
    return TRUST_UNSUPPORTED  # 1 I2X / 4 TUG / None / other


def delay_route_for(
    element_key: str,
    *,
    std_route: Optional[int] = None,
    gfd_route: Optional[int] = None,
) -> Optional[int]:
    """Return the raw SSTDelayCalc route byte that governs this delay element
    (``None`` for LTD, which is not SSTDelayCalc-routed)."""
    key = (element_key or "").lower()
    if key == "std":
        return std_route
    if key == "gfd":
        return gfd_route
    return None


def delay_trust_reason(
    element_key: str,
    trust: str,
    *,
    route: Optional[int] = None,
    gfd_is_ansi: bool = False,
) -> str:
    """Short, field-tech-facing explanation of the trust tier for tooltips/notes."""
    key = (element_key or "").lower()
    if key == "ltd":
        return "LTD long-time window (methods 1-5) is implementation-complete and proven (G4 row 5)."
    route_name = _ROUTE_NAME.get(route, "unknown") if route is not None else "n/a"
    if trust == TRUST_DB:
        if route == 2:
            return (
                "Inverse-equation (Therm) delay — validated BIT-EXACT against the native "
                "EasyPower CalcThermEq kernel over the complete STD Therm corpus (G4 §5)."
            )
        return f"Direct-band delay ({route_name}) — numerically validated row-for-row (G4)."
    if trust == TRUST_VERIFY:
        return (
            f"Inverse-equation delay ({route_name}) — dispatch-wired, native CalcThermEq "
            "recovered + patched; GF byICalc=1 (num3=field13) not yet reproduced by the "
            "managed solver, captured-fixture promotion pending (G4 §5)."
        )
    if gfd_is_ansi:
        return (
            "GF inverse-equation ANSI family (id_op_eq ≠ 0) — hard-excluded pending a "
            "family-aware ANSI solver with captured fixtures (G4 §3e)."
        )
    return (
        f"Delay solver not implemented ({route_name}) — time withheld; "
        "the band fall-through value is not a certified curve (G4 §6)."
    )
