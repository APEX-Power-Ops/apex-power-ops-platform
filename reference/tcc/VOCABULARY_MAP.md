# TCC Vocabulary Map (SEED) - source term -> our term, with trust tier

> **Status: SEED (2026-06-27).** TCC-first, structured to generalize to records/NETA/ops at the 2nd domain.
> Consolidates and productizes G1 sec 3 (the DVL-flag dictionary + engine-constant reconciliation), adding a
> `canonical_term` column (our verbiage) and a `trust_tier`. Doc-first; promote to a `*.vocab` table at the
> first serving consumer that needs to JOIN canonical labels (build-at-2nd-consumer).

## Architecture - normalization is an ADDITIVE MAP, not a rename

The base stays **source-faithful and immutable** (EasyPower names kept verbatim in `access_raw.*` and the
re-carried `tcc.*` columns - provenance, debuggability, re-derivation). The canonical vocabulary is a
**separate map** the serving views / field_schema / renderers read. Because the map is additive over an
unchanged base, baking source-faithful columns in now can never conflict with normalization later. This is the
same two-layer pattern already in the platform (`access_raw` vs `tcc.*`; the D1 "carry source-faithful names,
resolve at query time" rule; public-concept vs seam-impl).

**Authority split:** the operator owns the `canonical_term` column (our verbiage). CC supplies `source_term`,
`definition`, `unit/enum`, `provenance`, and proposes `canonical_term` drafts drawn from the existing
records/NETA datasheet vocabulary (align, do not invent a third dialect). `canonical_term` cells below are left
**BLANK** for operator ratification.

## Trust tiers

| tier | meaning | re-carry posture |
|---|---|---|
| `source_faithful` | value AND meaning fully known from source (DVL-DB legend or managed engine code) | safe to carry verbatim; `served` flags the subset the managed cascade reads |
| `native_bounded` | raw value readable, but semantics/application live in symbol-stripped native code (`DvlEng`/`TccBase`) - input layout recoverable, NOT enum legends or curve math | carry as raw data tagged `native_bounded`, do NOT claim behavior or wire to serving |
| `deferred` | full-fidelity curve/rating BEHAVIOR not consumed by serving | not actioned; bounded like the relay kernel (needs live-behavior / vendor docs) |

## Seed rows (TCC / EasyPower; D4 + D5; canonical_term for operator)

| domain | source_term | canonical_term | definition | unit / enum | served | trust_tier | provenance |
|---|---|---|---|---|---|---|---|
| tcc | `TMT_Use_SST` |  | gate: 1 = borrow solid-state ETU cascade, 0 = thermal-magnetic frame path | enum 0/1 | yes | source_faithful | `[DLL DevLibBreakerStyle]` (carried, D1) |
| tcc | `TMT_Thermal` (ICCB) / `TMT_ThermalMagnetic` (MCCB) |  | inst-gate: 0 = with adjustable instantaneous, 1 = without; gates whether the TMT frame exposes an inst-settings list. Per-class column-name split, same model property | enum 0/1 | yes | source_faithful | `[DVL-DB]` `[DLL G1 sec 3.1 split]` |
| tcc | `TMT_BreakerType` |  | 0 = Thermal Magnetic, 1 = Motor Circuit Protector | enum 0/1 | no | source_faithful | `[DVL-DB G1 sec 3.1]` |
| tcc | `TMT_TripPlug` |  | 0 = Trip, 1 = Plug (~99% are 0) | enum 0/1 | no | source_faithful | `[DVL-DB G1 sec 3.1]` |
| tcc | `TMT_TCCNumber` |  | free-text vendor-doc reference (curve-set citation, e.g. `GES-6164`); NOT an FK | text | no | source_faithful | `[VERIFIED-LIVE 2026-06-27]` |
| tcc | `TMT_Notes` |  | human note / curve-provenance prose | memo (text) | no | source_faithful | `[VERIFIED-LIVE]` (memo) |
| tcc | `InstOvr*` (16 cols) |  | instantaneous-override block: amps, min/max tolerance, clr/opn delay+radius, notetext, clearing+opening curve sets (curve/char/curvecalc/enteredat) | mixed Single/Byte | no | native_bounded | `[DLL DvlEng/-Module-.cs:11961,12155]` `[NATIVE-BOUNDED]` |
| tcc | `NInstOvr*` (15 cols) |  | the **Non-Instantaneous** variant of `InstOvr*` (breaker with instantaneous defeated / short-time-only); defaults to `InstOvr*` when N columns absent | mixed Single/Byte | no | native_bounded | `[DLL DvlEng/-Module-.cs:12164,12172]` |
| tcc | `BrkTimes*50/60` |  | mechanism timing (MechOpening, STDelayBand) at 50/60 Hz | Single (s) | no | native_bounded | `[VERIFIED-LIVE]` `[08 sec 3.4]` |
| tcc | `r_int_inst_*` / `r_int_series_*` / `r_int_ninst_*` |  | ANSI interrupting ratings at 240/480/600 V: instantaneous / series-rated / **non-instantaneous** (`ninst` = PCB-only) | Single (kA) | no | native_bounded | `[DLL TccBase GetIntKaNonInst]` `[VERIFIED-LIVE]` |
| tcc | `r_iec_inst_*` / `r_iec_ninst_*` |  | IEC interrupting ratings at 220-1000 V: instantaneous / non-instantaneous (`ninst` = PCB-only) | Single (kA) | no | native_bounded | `[VERIFIED-LIVE 2026-06-27]` |
| tcc | `Breaker_OvrCurves` (table) |  | inst-override curve points by `StyleID` (four classes 0-3 via `ReadBreakerOvrCurve`; empty in current Access) | curve points | no | native_bounded | `[DLL DvlEng/-Module-.cs:12278,15426]` |
| tcc | InstOvr/NInstOvr `Curve`/`Char`/`CurveCalc` byte-enum legends |  | curve-shape selector meanings (byte enums) - UNDECODED | enum (undecoded) | no | deferred | `[NATIVE-BOUNDED]` - needs live-behavior / vendor docs |
| tcc | override curve-application math |  | how the native engine recalculates the override trip band | n/a | no | deferred | `[TccBase native, symbol-stripped]` |

## Lane-2 data-carry plan (operator-gated migrations; authored next, applied on explicit go)

Both ride the existing `source_id` (= Access `Breaker*Styles.ID`, NOT NULL + UNIQUE per mig 007), source-faithful,
name-faithful (D1 precedent: no FK coercion). Apply via governed `apply_migration` after a harness dry-run, same
gate discipline as 027/028.

**Naming rule (HARD):** target columns are **`lower_snake_case`** - NEVER quoted mixed-case Postgres identifiers
(matches the D1 precedent `tmt_use_sst` / `tmt_sst_mfr`). Preserve the verbatim Access source name + the decode in
`COMMENT ON COLUMN`. The canonical UI/serving label comes from `canonical_term` (this map), not the physical column
name - so the physical name stays conventional while the Access provenance + the our-verbiage label both live in
metadata, not in a quoted identifier.

- **D4 re-carry (`source_faithful`):** `ALTER tcc.brk_iccb_styles / brk_mccb_styles ADD` the six helper columns as
  `lower_snake_case`: `tmt_tcc_number` (text), `tmt_notes` (text), `tmt_trip_plug` (smallint), `tmt_breaker_type`
  (smallint), `tmt_thermal_magnetic` (smallint), `tmt_thermal` (smallint) - each `COMMENT`-ed with its verbatim
  Access name + decode; read row-level from Access via the harness. Memo (`tmt_notes`) -> `text` (row-level read,
  never CSV). This is the "easy one" - decoded, low-risk, unblocks TMT-breaker characterization metadata.
- **D5 raw-carry (`native_bounded`):** add a side table (e.g. `tcc.brk_style_native_overrides`) or raw columns for
  `InstOvr*` / `NInstOvr*` / `BrkTimes*` / `r_int_*` / `r_iec_*` + the `Breaker_OvrCurves` points, tagged
  `native_bounded`, keyed on **`(breaker_class, source_id)`** - a shared side table MUST include `breaker_class`
  because `source_id` collides across classes (G1 sec 2B per-class id overlap); or use per-class side tables.
  Preserves fidelity (the raw floats/bytes) WITHOUT wiring to serving and WITHOUT claiming the native behavior. The
  curve/char byte-enum legends + the application math stay `deferred`.
- **028 diagnostic-view transition (031, AFTER the data carry):** once D4/D5 are POPULATED, the live 028 views
  (`vw_lvbreakertcc_tmt_frame_contract`) still emit `d4_tmt_helper_columns_absent_from_projection` /
  `d5_inst_override_columns_absent_from_projection` - now stale. A `031` `CREATE OR REPLACE VIEW` must transition the
  hazard state: **drop** the D4 absent flag (D4 carried + populated), and **change** D5 to
  `d5_inst_override_carried_reference_only` (native_bounded reference, NOT wired to serving). Sequence: 029 DDL ->
  029 data (harness) -> 030 DDL -> 030 data (harness) -> **031 view-transition** (guarded to RAISE if the D4 data is
  not yet populated, so the flags never flip prematurely). Authored at carry time against the actual populated state.
  This keeps the 028 hazard surface honest after apply (the operator's "not okay after apply unless a follow-up view
  patch changes the hazard language" requirement).

## Cross-refs
- G1 sec 3.1 / sec 3.4 / sec 5 (D4/D5) - the authoritative decoded register this map productizes.
- The Access Fidelity Harness - the read path for the row-level source values.
