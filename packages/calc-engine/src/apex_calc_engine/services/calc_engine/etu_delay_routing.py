"""
SSTDelayCalc routing dispatch for STD and GFD curves.

Promoted into packages/calc-engine from
source-domains/tcc_v5_backend/services/calc_engine/etu_delay_routing.py
per matrix #30 PROMOTE recommendation (operator-approved 2026-05-26).
Provenance baseline: tcc_v5_backend commit c2976a3. The tcc copy remains
unchanged per matrix #28 SOURCE-DOMAIN/PROVENANCE posture.

The integer columns previously surfaced as boolean-shaped `i2t_enabled` /
`i2t_type` metadata actually encode the SSTDelayCalc enum from the Access DLL:

    STD  (tcc.etu_sensors.stpu_delay_calc_code)   0=NONE, 1=I2X, 2=INVEQ, 3=TUSTD
    GFD  (tcc.etu_sensors.ground_delay_calc_code) 0=NONE, 1=I2X, 2=INVEQ, 4=TUG

Phase 5 Tier A (2026-04-26) renamed the storage columns from the legacy
`stpu_i2t` / `gfpu_i2t` identifiers; per-row values, type, and lineage to
`DatSensor.DS3_SEC3_I2T` / `DS1GF_SEC3_I2T` are unchanged.

Packet 009 backfilled the columns on 11,442 / 11,442 sensors; packet 010
restores routing semantics so callers can dispatch to the correct solver
path or surface an explicit unsupported marker rather than silently
ignoring the stored code.

INVEQ routes through the IEEE inverse-time solver (IEEEInverseTimeSolver
in etu_curves.py). I2X routes through a bounded band-anchor solver that
builds nominal STD/GFD curves directly from the selected band row's
anchor columns (`i_open` / `i_clear`, `t_open` / `t_clear`, and
`exp_x` / `i2x`). TUSTD / TUG still have no solver in this codebase.
Those paths are reported through DelayDispatch with `solver_path == None`
and a populated `unsupported_reason`, never silently coerced to the IEEE
path.

TASK-E execution (2026-04-29) — bounded inverse-equation contract anchors
========================================================================
The 2026-04-29 TASK-E execution packet wired the inverse-equation dispatch
surface to the corrected `EASYPOWER-CALC-ENGINE-SPEC.md` contract anchored
by the 2026-04-29 pass-5 Ghidra-headless recovery against EasyPower.exe.
This module exposes (and only exposes) the dispatch-layer artifacts the
scoping ruling (`Development/Platform/TCC/TCC-CALC-ENGINE-TASK-E-INVERSE-EQUATION-SCOPING-2026-04-29.md`)
authorized:

  - STD-side `DS3_SEC3_I2T = 2` integrity expectation (§G Path 2):
    `(FdOpICalc, FdClICalc, IdOpICalc, IdClICalc) = (10, 10, 4, 4)` across
    all 22,620 STD-side InvEq rows (TASK-B §3.7); `std_inveq_icalc_integrity_ok`
    surfaces the spec's family-integrity contract as an explicit check.

  - GF-side `DS1GF_SEC3_I2T = 2` dispatch metadata (§J Path 2 recovered
    native contract subsection):
      * `GFInvEqFamily` enum + `gf_inveq_family(id_open_eq)` — row-level
        Therm vs. Ansi selector keyed off the IdOp `*Eq` byte at native
        row offset 0x70 (single-byte basic-block compare in the populator
        FUN_01207bf0).
      * `gf_inveq_byicalc(in_value)` — the deterministic native translator
        FUN_01208640 with body `byICalc = (in == 0) ? 2 : (in == 1) ? 1 : 0`.
      * `GF_INVEQ_SLOT_BINDINGS` — the slot-to-setter binding matrix
        (BOUND × 3): four sub-blocks (FdOp/FdCl/IdOp/IdCl) at row offsets
        0x08/0x3C/0x70/0xA4, each binding to a Therm setter (when row's
        IdOp `*Eq` = 0) or an Ansi setter (when row's IdOp `*Eq` ≠ 0).
      * `gf_inveq_block_kind(in_out, gfp_enabled)` — the populator's
        consumer-flag plus `InOut` gating that selects the flat block
        (FdOp + FdCl) or inverse block (IdOp + IdCl) per the row.
      * `GFInvEqRowDispatch` + `dispatch_gf_inveq_row(...)` — single
        decision record packaging family, byICalc per sub-block, block
        kind, and integrity facts so callers downstream of the IEEE
        inverse-time solver can trace any output back to the recovered
        contract anchors without reopening §O blocker closure.

  - WEG OCR Type A diagnostic exclusion (scoping ruling §3.4 + §4.4 N.4):
    `dispatch_gfd_delay(..., gf_pickup_calc_code=6)` and the corresponding
    `route_delay_curve` `gf_pickup_calc_code` argument both surface a
    clean unresolved-pickup diagnostic rather than computing GF curves
    for the 7-sensor WEG OCR Type A cohort. This excludes those sensors
    from any GF InvEq output even when their delay-calc code is INVEQ.

Authority (must-cite for downstream consumers):

  1. `EASYPOWER-CALC-ENGINE-SPEC.md` §G Path 2, §J Path 2 (incl. recovered
     native contract surface subsection), §C InvEq row schemas, §O.
  2. `Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md`
     §12 (binding matrix), §8 (translator).
  3. `architecture-tcc-master-orchestration-1.md` DEC-021 (§O closure).
  4. `TCC-STD-ELEMENT-INTERPRETATION.md`, `TCC-GF-ELEMENT-INTERPRETATION.md`
     for kernel formula contents (the math inside `CalcThermEq`,
     `CalcAnsiEqGF`, `SetSTDB_*`, `CalcThermEq3`). This module DOES NOT
     redefine kernel math; the existing IEEEInverseTimeSolver remains the
     numerical engine for INVEQ curves on both STD and GF paths.

STD/GF evidence-pedigree asymmetry (transparency note): the GF-side
populator FUN_01207bf0 was bound at native depth in pass-5; the STD-side
per-call-site populator was not. Spec §G Path 2 has been at contract
authority since 2026-04-26 — the §O gate was always GF-only. Both paths
stand at contract authority for execution.
"""

import math
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Mapping, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # avoid circular import at runtime
    from .etu_curves import IEEEInverseTimeSolver


class DelayCalcPath(str):
    STD = "std"
    GFD = "gfd"


class SSTDelayCalc(IntEnum):
    NONE = 0
    I2X = 1
    INVEQ = 2
    TUSTD = 3
    TUG = 4


_NAME_BY_CODE = {
    SSTDelayCalc.NONE: "NONE",
    SSTDelayCalc.I2X: "I2X",
    SSTDelayCalc.INVEQ: "INVEQ",
    SSTDelayCalc.TUSTD: "TUSTD",
    SSTDelayCalc.TUG: "TUG",
}


# Codes that the STD and GFD paths are each allowed to carry per the DLL enum.
# Anything outside these is "unknown" and routed to the unsupported branch.
_VALID_STD_CODES = frozenset({0, 1, 2, 3})
_VALID_GFD_CODES = frozenset({0, 1, 2, 4})


@dataclass(frozen=True)
class DelayDispatch:
    """Resolved delay-routing decision for one path on one sensor.

    Fields:
        path: 'std' or 'gfd'
        code: raw SSTDelayCalc integer from tcc.etu_sensors (None if column null)
        name: canonical name ('NONE', 'I2X', 'INVEQ', 'TUSTD', 'TUG', or 'UNKNOWN')
        supported: True only when this code resolves to a solver in this codebase
        solver_path: 'flat' for NONE, 'i2x_band' for I2X,
            'ieee_inverse_time' for INVEQ, else None
        unsupported_reason: explicit reason string when supported=False (else None)
    """

    path: str
    code: Optional[int]
    name: str
    supported: bool
    solver_path: Optional[str]
    unsupported_reason: Optional[str] = None


def delay_calc_name(code: Optional[int]) -> str:
    """Return canonical SSTDelayCalc name or 'UNKNOWN' for unmapped values.

    Returns 'UNKNOWN' (not None) when the code is null or outside the enum so
    callers always have a concrete label for the unsupported branch.
    """
    if code is None:
        return "UNKNOWN"
    try:
        return _NAME_BY_CODE[SSTDelayCalc(code)]
    except ValueError:
        return "UNKNOWN"


# ──────────────────────────────────────────────────────────────────────
# TASK-E execution (2026-04-29) — STD-side `*ICalc` integrity expectation
# Spec §G Path 2 + TASK-B §3.7: across all 22,620 STD-side InvEq rows,
# the four `*ICalc` byte columns are uniformly (10, 10, 4, 4). This is a
# family-integrity expectation, NOT a behavior-switching dispatch byte
# on the STD side; rows that deviate may be rejected as a data error.
# ──────────────────────────────────────────────────────────────────────

#: Expected (FdOpICalc, FdClICalc, IdOpICalc, IdClICalc) on STD-side InvEq rows.
STD_INVEQ_ICALC_EXPECTED: tuple[int, int, int, int] = (10, 10, 4, 4)


def std_inveq_icalc_integrity_ok(
    fd_open_i_calc: Optional[int],
    fd_clear_i_calc: Optional[int],
    id_open_i_calc: Optional[int],
    id_clear_i_calc: Optional[int],
) -> bool:
    """True when the four STD-side InvEq `*ICalc` bytes match (10, 10, 4, 4).

    NULL is treated as a violation: spec §G Path 2 records the value as
    uniformly populated across all 22,620 rows, so a missing value is a
    data-load anomaly worth surfacing. Callers may either drop the row
    or surface an explicit integrity warning; this module deliberately
    does not auto-coerce.
    """
    return (
        fd_open_i_calc,
        fd_clear_i_calc,
        id_open_i_calc,
        id_clear_i_calc,
    ) == STD_INVEQ_ICALC_EXPECTED


# ──────────────────────────────────────────────────────────────────────
# TASK-E execution (2026-04-29) — GF-side recovered native dispatch surface
# Spec §J Path 2 "Recovered native contract surface (pass-5 RE, 2026-04-29)"
# pins the per-row Therm/Ansi family selector, sub-block layout, slot-to-
# setter binding matrix, *ICalc → byICalc translator, and consumer-flag
# plus InOut gating. The constants below mirror that contract 1:1.
# ──────────────────────────────────────────────────────────────────────


class GFInvEqFamily(IntEnum):
    """Therm vs. Ansi runtime kernel family for a GF-side InvEq row.

    The native populator (FUN_01207bf0 inside EasyPower.exe) selects this
    family for the entire row by reading IdOp's `*Eq` byte at native row
    offset 0x70: zero ⇒ Therm; nonzero ⇒ Ansi. All four sub-blocks within
    one row use the same family; per-sub-block `*Eq` bytes do not split
    families per sub-block within one row.
    """

    THERM = 0
    ANSI = 1


def gf_inveq_family(id_open_eq: Optional[int]) -> GFInvEqFamily:
    """Resolve the row's Therm/Ansi family from the IdOp `*Eq` byte.

    Mirrors the populator's single-byte basic-block compare at native row
    offset 0x70. Treats NULL as Therm (the default-zero observation across
    most of the GF InvEq table; the 100-row Federal Pioneer block carries
    `IdOpEq = 1` and selects Ansi).
    """
    return GFInvEqFamily.ANSI if id_open_eq else GFInvEqFamily.THERM


def gf_inveq_byicalc(in_value: Optional[int]) -> int:
    """Native FUN_01208640 translator: `byICalc = (in == 0) ? 2 : (in == 1) ? 1 : 0`.

    On the data-side `*ICalc ∈ {1, 4, 8, 10}` set documented at spec §C
    `DatSection1GfInvEq`, this collapses to `1 → 1` and `{4, 8, 10} → 0`.
    NULL is treated as the default-else branch (returns 0); the native
    code path applies the same fall-through.
    """
    if in_value == 0:
        return 2
    if in_value == 1:
        return 1
    return 0


@dataclass(frozen=True)
class GFInvEqSlotBinding:
    """One sub-block's contract anchors.

    Maps the SQL column-prefix for a `dvlDatInveqDelay` quadrant onto:
      - the native byte offsets recovered by pass-5,
      - the two `TccBase` setter names + ordinals the populator dispatches
        through depending on the row's Therm/Ansi family.
    """

    column_prefix: str  # 'fd_open' | 'fd_clear' | 'id_open' | 'id_clear'
    row_offset_start: int  # native row offset where the sub-block begins
    row_offset_end: int  # inclusive end offset
    eq_byte_offset: int  # native row offset of the `*Eq` byte
    icalc_byte_offset: int  # native row offset of the `*ICalc` byte
    therm_setter_name: str  # called when row's IdOp `*Eq` == 0
    therm_setter_ord: int  # TccBase ordinal of the Therm setter
    ansi_setter_name: str  # called when row's IdOp `*Eq` != 0
    ansi_setter_ord: int  # TccBase ordinal of the Ansi setter


#: Pass-5 recovered slot-to-setter binding matrix (BOUND × 3).
#: Spec §J Path 2 "Recovered native contract surface (pass-5 RE, 2026-04-29)".
GF_INVEQ_SLOT_BINDINGS: Mapping[str, GFInvEqSlotBinding] = {
    "fd_open": GFInvEqSlotBinding(
        column_prefix="fd_open",
        row_offset_start=0x08,
        row_offset_end=0x3B,
        eq_byte_offset=0x08,
        icalc_byte_offset=0x09,
        therm_setter_name="SetTherm_FlatDelayOpen",
        therm_setter_ord=0x18C,
        ansi_setter_name="SetAnsi_FlatDelayOpen",
        ansi_setter_ord=0x140,
    ),
    "fd_clear": GFInvEqSlotBinding(
        column_prefix="fd_clear",
        row_offset_start=0x3C,
        row_offset_end=0x6F,
        eq_byte_offset=0x3C,
        icalc_byte_offset=0x3D,
        therm_setter_name="SetTherm_FlatDelayClear",
        therm_setter_ord=0x18B,
        ansi_setter_name="SetAnsi_FlatDelayClear",
        ansi_setter_ord=0x13F,
    ),
    "id_open": GFInvEqSlotBinding(
        column_prefix="id_open",
        row_offset_start=0x70,
        row_offset_end=0xA3,
        eq_byte_offset=0x70,
        icalc_byte_offset=0x71,
        therm_setter_name="SetTherm_InverseDelayOpen",
        therm_setter_ord=0x18E,
        ansi_setter_name="SetAnsi_InverseDelayOpen",
        ansi_setter_ord=0x142,
    ),
    "id_clear": GFInvEqSlotBinding(
        column_prefix="id_clear",
        row_offset_start=0xA4,
        row_offset_end=0xD7,
        eq_byte_offset=0xA4,
        icalc_byte_offset=0xA5,
        therm_setter_name="SetTherm_InverseDelayClear",
        therm_setter_ord=0x18D,
        ansi_setter_name="SetAnsi_InverseDelayClear",
        ansi_setter_ord=0x141,
    ),
}


def gf_inveq_setter_for(prefix: str, family: GFInvEqFamily) -> tuple[str, int]:
    """Return (setter_name, TccBase_ordinal) for one sub-block + row family.

    The four `dvlDatInveqDelay` sub-blocks each bind to two TccBase setters
    — one Therm, one Ansi — selected by the row's IdOp `*Eq` byte; this
    helper realizes the BOUND × 3 binding matrix for callers that need to
    cite the recovered native contract anchor.
    """
    binding = GF_INVEQ_SLOT_BINDINGS[prefix]
    if family == GFInvEqFamily.THERM:
        return (binding.therm_setter_name, binding.therm_setter_ord)
    return (binding.ansi_setter_name, binding.ansi_setter_ord)


def gf_inveq_block_kind(in_out: Optional[int], gfp_enabled: bool) -> str:
    """Native populator gating for flat-vs-inverse block selection.

    Mirrors `FUN_01207bf0`'s consumer-flag plus row-`InOut` gating
    (pass-5 evidence §7.4):
      - `gfp_enabled != 0 AND row.InOut ∈ {1, 2}` ⇒ inverse block (IdOp + IdCl)
      - `gfp_enabled == 0 AND row.InOut ∈ {0, 2}` ⇒ flat block (FdOp + FdCl)
      - otherwise ⇒ neither block runs (`'skip'`)

    Returns one of `'inverse'`, `'flat'`, `'skip'`.
    """
    if gfp_enabled and in_out in (1, 2):
        return "inverse"
    if not gfp_enabled and in_out in (0, 2):
        return "flat"
    return "skip"


@dataclass(frozen=True)
class GFInvEqRowDispatch:
    """Per-row GF-side InvEq dispatch decision packaging the recovered contract.

    Builds in one place the four pieces the populator's native body weaves
    together so downstream consumers (e.g. trace logs, parity checks, UI
    layers) can cite the recovered contract anchors without re-deriving
    them per call site. This dataclass is metadata only — it does NOT call
    the IEEE solver or the native kernels itself.

    Fields:
        family: Therm or Ansi, from row's IdOp `*Eq`.
        block_kind: 'inverse' (IdOp + IdCl), 'flat' (FdOp + FdCl), or 'skip'.
        byicalc_per_subblock: dict keyed by sub-block prefix
            (`fd_open`/`fd_clear`/`id_open`/`id_clear`) of the native
            `byICalc` value the populator passes to each setter.
        active_setters: ordered list of (sub_block_prefix, setter_name,
            setter_ord) tuples for the sub-blocks selected by `block_kind`.
            Empty when `block_kind == 'skip'`.
    """

    family: GFInvEqFamily
    block_kind: str
    byicalc_per_subblock: Mapping[str, int]
    active_setters: tuple[tuple[str, str, int], ...]


_BLOCK_PREFIXES: Mapping[str, tuple[str, ...]] = {
    "flat": ("fd_open", "fd_clear"),
    "inverse": ("id_open", "id_clear"),
    "skip": (),
}


def dispatch_gf_inveq_row(
    *,
    in_out: Optional[int],
    id_open_eq: Optional[int],
    fd_open_i_calc: Optional[int],
    fd_clear_i_calc: Optional[int],
    id_open_i_calc: Optional[int],
    id_clear_i_calc: Optional[int],
    gfp_enabled: bool,
) -> GFInvEqRowDispatch:
    """Resolve the per-row GF-side InvEq dispatch decision.

    Packages the native populator's row-level decisions into a single
    metadata record:
      - Therm/Ansi family from IdOp `*Eq`,
      - flat-vs-inverse block kind from consumer-flag + `InOut`,
      - per-sub-block `byICalc` translator outputs,
      - the ordered list of active TccBase setters keyed off family + block.

    Numerical evaluation continues through `IEEEInverseTimeSolver` (kernel
    formulas governed by `TCC-GF-ELEMENT-INTERPRETATION.md` per scoping
    ruling §4.6); this function is dispatch metadata only.
    """
    family = gf_inveq_family(id_open_eq)
    block_kind = gf_inveq_block_kind(in_out=in_out, gfp_enabled=gfp_enabled)

    byicalc_per_subblock = {
        "fd_open": gf_inveq_byicalc(fd_open_i_calc),
        "fd_clear": gf_inveq_byicalc(fd_clear_i_calc),
        "id_open": gf_inveq_byicalc(id_open_i_calc),
        "id_clear": gf_inveq_byicalc(id_clear_i_calc),
    }

    active_setters: tuple[tuple[str, str, int], ...] = tuple(
        (prefix, *gf_inveq_setter_for(prefix, family))
        for prefix in _BLOCK_PREFIXES[block_kind]
    )

    return GFInvEqRowDispatch(
        family=family,
        block_kind=block_kind,
        byicalc_per_subblock=byicalc_per_subblock,
        active_setters=active_setters,
    )


# ──────────────────────────────────────────────────────────────────────
# TASK-E execution (2026-04-29) — WEG OCR Type A diagnostic exclusion
# Scoping ruling §3.4 + §4.4 N.4: when `DS1GF_PICKUP_CALC = 6`, surface
# a clean unresolved-pickup diagnostic instead of computing a GF curve.
# Applies regardless of the sensor's GFD delay-calc code.
# ──────────────────────────────────────────────────────────────────────


#: `DS1GF_PICKUP_CALC` value used by the 7-sensor WEG OCR Type A cohort
#: per spec §I + spec §N.4. The pickup formula is unresolved; spec policy
#: is to either RE the pickup or declare it out of scope.
WEG_OCR_TYPE_A_PICKUP_CALC: int = 6


def _dispatch(path: str, code: Optional[int], valid_codes: frozenset) -> DelayDispatch:
    if code is None or code not in valid_codes:
        return DelayDispatch(
            path=path,
            code=code,
            name=delay_calc_name(code),
            supported=False,
            solver_path=None,
            unsupported_reason=(
                f"{path.upper()} delay-routing code {code!r} is not a recognized "
                f"SSTDelayCalc value for this path"
            ),
        )

    if code == SSTDelayCalc.NONE:
        return DelayDispatch(
            path=path, code=code, name="NONE",
            supported=True, solver_path="flat",
        )

    if code == SSTDelayCalc.INVEQ:
        return DelayDispatch(
            path=path, code=code, name="INVEQ",
            supported=True, solver_path="ieee_inverse_time",
        )

    if code == SSTDelayCalc.I2X:
        return DelayDispatch(
            path=path, code=code, name="I2X",
            supported=True, solver_path="i2x_band",
        )

    if code == SSTDelayCalc.TUSTD:
        return DelayDispatch(
            path=path, code=code, name="TUSTD",
            supported=False, solver_path=None,
            unsupported_reason="TUSTD (GE thermal-utility STD) solver is not implemented",
        )

    if code == SSTDelayCalc.TUG:
        return DelayDispatch(
            path=path, code=code, name="TUG",
            supported=False, solver_path=None,
            unsupported_reason="TUG (GE thermal-utility ground) solver is not implemented",
        )

    return DelayDispatch(
        path=path, code=code,
        name=delay_calc_name(code),
        supported=False, solver_path=None,
        unsupported_reason=f"Unhandled SSTDelayCalc code {code}",
    )


def dispatch_std_delay(stpu_delay_calc_code: Optional[int]) -> DelayDispatch:
    """Resolve STD delay routing from tcc.etu_sensors.stpu_delay_calc_code.

    The argument keeps an SSTDelayCalc integer; the parameter name was
    previously `stpu_i2t` to match the legacy storage column. Phase 5 Tier A
    (2026-04-26) renamed the storage column to stpu_delay_calc_code; the
    function continues to accept the integer regardless of source column name.
    """
    return _dispatch("std", stpu_delay_calc_code, _VALID_STD_CODES)


def dispatch_gfd_delay(
    ground_delay_calc_code: Optional[int],
    gf_pickup_calc_code: Optional[int] = None,
) -> DelayDispatch:
    """Resolve GFD delay routing from tcc.etu_sensors.ground_delay_calc_code.

    The argument keeps an SSTDelayCalc integer; the parameter name was
    previously `gfpu_i2t` to match the legacy storage column. Phase 5 Tier A
    (2026-04-26) renamed the storage column to ground_delay_calc_code; the
    function continues to accept the integer regardless of source column name.

    TASK-E execution (2026-04-29): when ``gf_pickup_calc_code == 6`` (WEG OCR
    Type A, spec §N.4), return an unresolved-pickup diagnostic regardless of
    the sensor's delay-calc code. The 7-sensor WEG OCR Type A cohort has an
    unknown pickup formula, so the GF curve cannot be honestly computed even
    when the delay-calc code is INVEQ. Scoping ruling §3.4 + §4.4 N.4.
    """
    if gf_pickup_calc_code == WEG_OCR_TYPE_A_PICKUP_CALC:
        return DelayDispatch(
            path="gfd",
            code=ground_delay_calc_code,
            name=delay_calc_name(ground_delay_calc_code),
            supported=False,
            solver_path=None,
            unsupported_reason=(
                "WEG OCR Type A pickup unresolved (DS1GF_PICKUP_CALC = 6); "
                "see EASYPOWER-CALC-ENGINE-SPEC.md §N.4. GF curve withheld "
                "until a separately authored RE pass closes the pickup formula."
            ),
        )
    return _dispatch("gfd", ground_delay_calc_code, _VALID_GFD_CODES)


@dataclass
class RoutedDelayCurve:
    """Result of routing a delay-curve request through the dispatcher.

    Attributes:
        dispatch: the resolved DelayDispatch for the sensor's routing code
        points: curve points produced by the dispatched solver, or [] when
            the routing code maps to NONE / an unsupported path
        warnings: explicit messages for unsupported codes; never silently coerced
    """
    dispatch: DelayDispatch
    points: list = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DelayCurvePoint:
    amps: float
    seconds: float


def _coerce_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_i2x_exponent(band_row: Mapping[str, Any]) -> Optional[float]:
    for key in ("exp_x", "i2x"):
        exponent = _coerce_float(band_row.get(key))
        if exponent is not None and exponent > 0:
            return exponent
    return None


def _resolve_i2x_anchor_time(band_row: Mapping[str, Any], variant: str) -> Optional[float]:
    if variant.endswith("open"):
        return _coerce_float(band_row.get("t_open") or band_row.get("open_time"))
    return _coerce_float(band_row.get("t_clear") or band_row.get("clear_time"))


def _resolve_i2x_anchor_amps(
    band_row: Mapping[str, Any],
    variant: str,
    pickup_current: float,
) -> Optional[float]:
    raw_value = _coerce_float(
        band_row.get("i_open") if variant.endswith("open") else band_row.get("i_clear")
    )
    if raw_value is None or raw_value <= 0:
        return None
    if pickup_current > 0 and raw_value <= 100.0:
        return raw_value * pickup_current
    return raw_value


def _generate_i2x_band_curve(
    *,
    band_rows: list[Mapping[str, Any]],
    variant: str,
    pickup_current: float,
    max_amps: float,
    min_time: float = 0.001,
) -> list[DelayCurvePoint]:
    if not band_rows:
        raise ValueError("I2X routing selected but no band row was supplied")

    band_row = band_rows[0]
    exponent = _resolve_i2x_exponent(band_row)
    if exponent is None:
        raise ValueError("I2X routing selected but exp_x / i2x is missing from the band row")

    anchor_amps = _resolve_i2x_anchor_amps(band_row, variant, pickup_current)
    if anchor_amps is None:
        raise ValueError(f"I2X routing selected but {variant} anchor current is missing")

    anchor_time = _resolve_i2x_anchor_time(band_row, variant)
    if anchor_time is None or anchor_time <= 0:
        raise ValueError(f"I2X routing selected but {variant} anchor time is missing")

    start_amps = max(pickup_current * 1.01 if pickup_current > 0 else 0.0, min(anchor_amps, max_amps))
    if start_amps <= 0:
        raise ValueError("I2X routing selected but pickup current is not positive")
    if max_amps <= start_amps:
        max_amps = max(anchor_amps * 1.5, start_amps * 1.05)

    constant = anchor_time * math.pow(anchor_amps, exponent)
    log_start = math.log10(start_amps)
    log_end = math.log10(max_amps)
    steps = max(10, int(50 * max(log_end - log_start, 0.2)))

    points: list[DelayCurvePoint] = []
    for index in range(steps + 1):
        amps = math.pow(10, log_start + ((log_end - log_start) * index / steps))
        seconds = constant / math.pow(amps, exponent)
        if seconds < min_time:
            points.append(DelayCurvePoint(amps=round(amps, 2), seconds=round(min_time, 6)))
            if amps < max_amps:
                points.append(DelayCurvePoint(amps=round(max_amps, 2), seconds=round(min_time, 6)))
            break
        points.append(DelayCurvePoint(amps=round(amps, 2), seconds=round(seconds, 6)))
    return points


def route_delay_curve(
    solver: "IEEEInverseTimeSolver",
    delay_calc_code: Optional[int],
    path: str,
    sensor_id: int,
    ordinal: int,
    variant: str,
    pickup_current: float,
    max_amps: float = 100000.0,
    time_dial: float = 1.0,
    tolerance_pct: float = 0.0,
    gf_pickup_calc_code: Optional[int] = None,
    band_rows: Optional[list[Mapping[str, Any]]] = None,
) -> RoutedDelayCurve:
    """Generate a delay curve by dispatching on the stored SSTDelayCalc code.

    INVEQ (code 2) -> IEEE inverse-time solver via solver.generate_curve(...)
    I2X   (code 1) -> bounded band-anchor I^x*t curve built from the
        selected STD/GFD band row
    NONE  (code 0) -> empty point list (the runtime treats this as no curve)
    TUSTD / TUG -> empty point list + an explicit unsupported warning

    Args:
        solver: an IEEEInverseTimeSolver instance bound to a session
        delay_calc_code: integer from tcc.etu_sensors.stpu_delay_calc_code or
            .ground_delay_calc_code (renamed from legacy stpu_i2t/gfpu_i2t at
            Phase 5 Tier A 2026-04-26)
        path: 'std' or 'gfd' — selects equation_type and validates the code set
        gf_pickup_calc_code: optional integer from tcc.etu_sensors gfpu pickup
            calc column; when ``path == 'gfd'`` and value == 6 (WEG OCR Type
            A per spec §N.4), the function surfaces an unresolved-pickup
            diagnostic and returns no curve. Ignored on the STD path.

    The function never coerces an unsupported code into the IEEE path; if a
    caller needs IEEE evaluation regardless of the stored code, they must call
    solver.generate_curve(...) directly.
    """
    if path == "std":
        dispatch = dispatch_std_delay(delay_calc_code)
        equation_type = "std"
    elif path == "gfd":
        dispatch = dispatch_gfd_delay(delay_calc_code, gf_pickup_calc_code=gf_pickup_calc_code)
        equation_type = "gfd"
    else:
        raise ValueError(f"path must be 'std' or 'gfd', got {path!r}")

    result = RoutedDelayCurve(dispatch=dispatch)

    if dispatch.supported and dispatch.solver_path == "ieee_inverse_time":
        result.points = solver.generate_curve(
            sensor_id=sensor_id,
            ordinal=ordinal,
            variant=variant,
            pickup_current=pickup_current,
            max_amps=max_amps,
            time_dial=time_dial,
            tolerance_pct=tolerance_pct,
            equation_type=equation_type,
        )
        return result

    if dispatch.supported and dispatch.solver_path == "i2x_band":
        try:
            result.points = _generate_i2x_band_curve(
                band_rows=list(band_rows or []),
                variant=variant,
                pickup_current=pickup_current,
                max_amps=max_amps,
            )
        except ValueError as exc:
            result.warnings.append(
                f"{path.upper()} delay routing code {delay_calc_code!r} ({dispatch.name}) "
                f"is stored on sensor {sensor_id} but the selected band row cannot "
                f"be converted into a nominal curve; reason: {exc}"
            )
        return result

    if dispatch.supported and dispatch.solver_path == "flat":
        # NONE: the SST element is present but does not draw a delay curve.
        # Caller renders this as the pickup band alone; no curve points.
        return result

    # Unsupported branch: I2X / TUSTD / TUG, or unknown / null code.
    result.warnings.append(
        f"{path.upper()} delay routing code {delay_calc_code!r} ({dispatch.name}) "
        f"is stored on sensor {sensor_id} but has no solver path in this build; "
        f"reason: {dispatch.unsupported_reason}"
    )
    return result
