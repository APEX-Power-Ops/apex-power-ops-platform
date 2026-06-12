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
                      2026-06-01), and **GFD INVEQ (route 2) Therm** — the GF runtime
                      path (``byICalc=1``) anchors on ``field[13]`` = the PLUG rating;
                      the managed plug-basis form (``rIRef' = rIRef × plug/pickup``)
                      reproduces the native kernel BIT-EXACT over the complete GF
                      Therm corpus (L1 close 2026-06-09; fixtures
                      ``gf_inveq_field13_native_parity.json``). **I2X route 1**
                      (shape-gated): ``flat`` = the stored definite time;
                      ``ramp`` = native-bit-exact ``CIxt.ComputeT`` (I2X-4); and
                      ``composite`` (``max(ramp, floor)``) — ramp bit-exact +
                      floor stored + the RENDER ASSEMBLY validated against the
                      native ``TccBase.dll`` assembly primitives
                      (TrimCurveX / ComputeY / CLogLogIntersection / MergeLines /
                      MergeGF; #72 close 2026-06-11, fixtures
                      ``composite_primitives_native_parity.json``) → db by
                      composition. Numerically validated — field-safe.
                      (G4 rows 3/4/5/6/7-Therm/11-flat-ramp-composite.)
  - ``"verify"``      DISPATCH-WIRED, parity not yet closed. No delay element
                      currently classifies here (the last occupant — the I2X
                      composite shape — was promoted by the #72 spot-check);
                      retained as the framework's flagged middle tier.
  - ``"unsupported"`` NOT IMPLEMENTED / hard-excluded. I2X route-1 bands whose
                      shape is unknown/withheld at the evaluator, and GE
                      trip-unit STD/Gnd (routes 3/4, fall-through diagnostic
                      only). The solver is not built / not certified, so the
                      band/curve number is a meaningless fall-through —
                      withhold it (G4 §6 step 6; rows 9/10/11-unknown).

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
    i2x_shape: Optional[str] = None,
) -> str:
    """Return the G4 field-trust tier for one delay element.

    ``element_key`` is one of ``"ltd"`` / ``"std"`` / ``"gfd"`` (case-insensitive).
    ``std_route`` / ``gfd_route`` are the persisted ``SSTDelayCalc`` route bytes.
    ``gfd_is_ansi`` marks a GFD route-2 sensor whose GF-INVEQ family is ANSI
    (``id_op_eq != 0``) — hard-excluded per G4 §3e.
    ``i2x_shape`` is the per-band I2X shape (``"flat"``/``"ramp"``/``"composite"``/
    ``"unknown"``) for a route-1 element — set once ``etu_ixt`` is wired (I2X-6); it
    governs the route-1 tier (see ``_classify_i2x``).
    """
    key = (element_key or "").lower()
    if key == "ltd":
        # LTD is NOT routed by SSTDelayCalc; its window (methods 1-5) is
        # implementation-complete and window-proven (G4 §3c / row 5). The
        # DS2_DLY_PTY parity edge is flagged separately and does not demote the
        # window itself.
        return TRUST_DB
    if key == "std":
        return _classify_std(std_route, i2x_shape)
    if key == "gfd":
        return _classify_gfd(gfd_route, gfd_is_ansi, i2x_shape)
    return TRUST_UNSUPPORTED


def _classify_i2x(shape: Optional[str]) -> str:
    """Route-1 (I2X / Iˣt) per-band field-trust tier (G4 §3b·I2X · STATE §120/§214).

    - ``flat`` (definite-time band, current-independent) → ``db`` — identical to the
      db-proven route-0 direct band.
    - ``ramp`` (pure Iˣt) → ``db`` — ``etu_ixt.ixt_time`` is native-bit-exact to the
      EasyPower ``CIxt.ComputeT`` kernel (I2X-4, max 0 ULP).
    - ``composite`` (max(ramp, floor)) → ``db`` — PROMOTED by the #72 spot-check
      (2026-06-11): the ramp is bit-exact (I2X-4), the floor is the stored band
      value, the max-combine is decompile-cited, and the RENDER ASSEMBLY is
      validated against the native TccBase assembly primitives over live served
      curves + vendor sweeps (fixtures ``composite_primitives_native_parity.json``)
      → db by composition.
    - anything else (``unknown`` / variable-X-unsupported / NULL anchors / None) →
      ``unsupported``: the evaluator withheld it, so the time is not certified.
    """
    s = (shape or "").lower()
    if s in ("flat", "ramp", "composite"):
        return TRUST_DB
    return TRUST_UNSUPPORTED


def _classify_std(route: Optional[int], i2x_shape: Optional[str] = None) -> str:
    if route == 0:
        return TRUST_DB
    if route == 1:
        # I2X / Iˣt route — shape-gated once etu_ixt is wired (I2X-6). Until a shape
        # is supplied this stays unsupported (the legacy withhold).
        return _classify_i2x(i2x_shape)
    if route == 2:
        # STD INVEQ is 100% Therm corpus-wide (G4 §3e) and runs byICalc=0
        # (IdOpICalc=4 → num3=field16=pickup). The managed solver reproduces the
        # native CalcThermEq kernel BIT-EXACT over the entire STD Therm corpus
        # (only 4 dial curves; G4 §5, captured-fixture parity closed 2026-06-01).
        return TRUST_DB
    return TRUST_UNSUPPORTED  # 3 TUSTD / None / other


def _classify_gfd(route: Optional[int], is_ansi: bool, i2x_shape: Optional[str] = None) -> str:
    if route == 0:
        return TRUST_DB
    if route == 1:
        return _classify_i2x(i2x_shape)
    if route == 2:
        # GFD INVEQ — BOTH native families now validated BIT-EXACT and "db":
        #   * Therm (L1 close, 2026-06-09): field[13] = PLUG rating; managed
        #     plug-basis form rIRef' = rIRef × plug/pickup matches CalcThermEq
        #     byICalc=1 (fixtures gf_inveq_field13_native_parity.json).
        #   * ANSI (#120, 2026-06-10): CalcAnsiEqGF C37.112 inverse reproduced
        #     over the complete corpus (18 tuples / 108 rows / 25 sensors;
        #     fixtures gf_inveq_ansi_native_parity.json). All ANSI rows carry
        #     id_op_i_calc=8 → byICalc=0 (pickup basis) — standalone, no
        #     field[13] dependency (the §206 over-read is corrected).
        # Rows whose basis is unavailable are withheld at the solver, never
        # silently computed.
        return TRUST_DB
    return TRUST_UNSUPPORTED  # 4 TUG / None / other


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
        if route == 2 and gfd_is_ansi:
            return (
                "Inverse-equation (ANSI/C37.112) delay — validated BIT-EXACT against the "
                "native EasyPower CalcAnsiEqGF kernel over the complete GF ANSI corpus "
                "(#120; fixtures gf_inveq_ansi_native_parity)."
            )
        if route == 2:
            return (
                "Inverse-equation (Therm) delay — validated BIT-EXACT against the native "
                "EasyPower CalcThermEq kernel over the complete Therm corpus (STD G4 §5; "
                "GF plug-basis L1 close, fixtures gf_inveq_field13_native_parity)."
            )
        if route == 1:
            return (
                "I²t/Iˣt (I2X) band delay — the ramp is native-bit-exact (CIxt, I2X-4), "
                "the floor is the stored band value, and the composite render assembly is "
                "validated against the native TccBase assembly primitives (#72; fixtures "
                "composite_primitives_native_parity)."
            )
        return f"Direct-band delay ({route_name}) — numerically validated row-for-row (G4)."
    if trust == TRUST_VERIFY:
        return (
            f"Delay ({route_name}) — dispatch-wired and partially native-validated; "
            "final confirmation pending (shown flagged, G4 §4)."
        )
    return (
        f"Delay solver not implemented ({route_name}) — time withheld; "
        "the band fall-through value is not a certified curve (G4 §6)."
    )
