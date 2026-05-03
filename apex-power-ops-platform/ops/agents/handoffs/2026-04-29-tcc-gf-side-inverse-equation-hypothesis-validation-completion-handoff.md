# TCC GF-Side Inverse-Equation Hypothesis Validation — Completion Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-gf-side-inverse-equation-hypothesis-validation`
Status: **Closed PASS** — all four hypotheses validated; blocker posture NOT CHANGED (still NOT CLOSED, materially narrowed further)
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-HYPOTHESIS-VALIDATION-2026-04-29.md`
Authority anchor: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28-PASS2.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Active engine contract: `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
Evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-HYPOTHESIS-VALIDATION-2026-04-29.md`
Companion handoff (preserved): `ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-hypothesis-validation-handoff.md`
Prior pass-2 completion handoff (preserved): `ops/agents/handoffs/2026-04-28-tcc-gf-side-inverse-equation-loader-recovery-completion-handoff-pass2.md`

## Summary

The bounded hypothesis-validation packet executed end to end against the four already-on-disk artifacts named in the parent handoff Mandatory Read Set. All four working hypotheses recorded during the 2026-04-28 loader-recovery pass-2 review are **VALIDATED** by direct file-backed evidence:

1. `sdvlSSTSec2Curve` is confined to sec2/LTD curve-loading and UI-rendering paths; `dvlDatInveqDelay` is confined to later inverse-delay loader, reader, and writer paths. The two object models are spatially and structurally disjoint within DvlEng.dll.
2. The DvlEng switch values `((int*)SSTInfo)[32]` (case `2`) and `((int*)SSTInfo)[101]` (== `2`) are `SSTDelayCalc.INVEQ` enum values, confirmed by `SSTSensorRecord.cs:27,33` declaring `StpuDelayCalc` and `GroundDelayCalc` as `SSTDelayCalc`-typed fields plus `EasyPower.Types.cs:2689–2701` defining the enum with `INVEQ=2, TUSTD=3`. Section identity is the explicit `nSection` argument to `dvlSSTGetInvEqDelays`, not these switch values.
3. `nSection = 3` selects `DatSection3InvEq` (STPU inverse); `nSection = 5` selects `DatSection1GfInvEq` (GF inverse). This is **decisive, not structural**: `DvlEng.cs:105701` directly selects the table-name string literal via the ternary `(nSection != 3) ? "DatSection1GfInvEq" : "DatSection3InvEq"` (the literals appear in the IL as Visual C++ mangled UTF-16LE wide-string constants whose decoded text is exactly those table names).
4. The managed `ReadStpuDelay` / `ReadGroundDelay` surfaces, plus the `DevLibTripSensor` UI dropdown query, populate description-only UI list controls. No managed code path in any locally available managed binary calls any of the eight GF setters or reads any GF math-row coefficient column.

Despite full validation of all four hypotheses, **the §O blocker remains NOT CLOSED**, exactly as the parent handoff predicted in its Expected Result Shape. Profile-by-profile binding remains **NOT BOUND × 3**. Database `*ICalc` to kernel `byICalc` translation remains **UNRESOLVED**. TASK-E remains BLOCKED.

The most consequential finding from this pass is on Hypothesis 3: `dvlSSTGetInvEqDelays` is **directly the per-row reader of the GF math-row table**. The function body at `DvlEng.cs:105789–105888` issues `CRecordReader.GetByteValue` and `CRecordReader.GetFloatValue` calls naming every single one of the eight GF math-row dispatch columns (`FdOpEq`, `FdOpICalc`, `FdClEq`, `FdClICalc`, `IdOpEq`, `IdOpICalc`, `IdClEq`, `IdClICalc`) plus the math coefficient columns (`FdOp1..6`, `FdCl1..6`, `IdOp1..6`, `IdCl1..6`) and the per-row metadata (`Desc`, `InOut`). The pulled values are stored into a 216-byte `dvlDatInveqDelay` struct with a four-sub-block layout (FdOp at 8, FdCl at 60, IdOp at 112, IdCl at 164) where each sub-block is 52 bytes consisting of (`*Eq` byte, `*ICalc` byte, plus 5 or 6 floats depending on `*Eq` discriminator). The discriminator semantic in DvlEng (`*Eq=0` selects 5-float layout, `*Eq=1` selects 6-float layout, `*Eq=2` selects 1-float layout) is consistent with the pass-2 kernel-side recovery of `0=Therm (5 doubles)`, `1=Ansi (6 doubles)`, `2=FDly` — supporting agreement at the DVL/database boundary without binding any TASK-B §3.9 profile to a specific setter call.

The §O blocker is therefore **further narrowed** without being closed:

1. The row-reader half of the loader chain is recovered with named columns: it lives in DvlEng.dll's `dvlSSTGetInvEqDelays`.
2. The populator/consumer (the code that iterates the populated `TdbPtrArray<dvlDatInveqDelay>` and calls one of the eight `Set{Therm,Ansi}_{Flat,Inverse}Delay{Open,Clear}` setters per slot) and the `*ICalc → byICalc` translation it applies remain absent from all five binaries searched so far (TccBase.dll, EasyPower.DeviceLibrary.dll, EasyPower.DataLayer.dll, EasyPower.DatabaseBrowser.dll, plus DvlEng.dll covered by this pass).

The remaining-gap location is consequently sharpened to "the populator/consumer step in a binary not yet covered." The most plausible candidates remain `EasyPower.exe` native section, `dbBase.dll` / `UtlBase.dll` or another EasyPower DLL not currently on local disk, or bounded dynamic instrumentation against a live `EasyPower.exe` — none authorized by this packet.

## Expected Deliverables Back To Copilot

### 1. Exact files reviewed

The following files were read but not modified by this pass:

| Path | Why read |
|---|---|
| `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28-PASS2.md` | Entry-gate verification + restated hypotheses |
| `apex-power-ops-platform/ops/agents/handoffs/2026-04-28-tcc-gf-side-inverse-equation-loader-recovery-completion-handoff-pass2.md` | Entry-gate verification + restated hypotheses |
| `source-domains/neta-ett-study-material/Development/temp/ilspy-dvleng/DvlEng.decompiled.cs` | Hypothesis 1 + 3 evidence — sec2 vs inverse-delay isolation; `dvlSSTGetInvEqDelays` body |
| `source-domains/neta-ett-study-material/Development/temp/ilspy-easypower/EasyPower.DeviceLibrary/EasyPower.DeviceLibrary/DeviceLibrary.cs` | Hypothesis 2 + 4 evidence — `ReadStpuDelay` / `ReadGroundDelay` bodies and SSTDelayCalc dispatch |
| `source-domains/neta-ett-study-material/Development/temp/ilspy-easypower/EasyPower.DeviceLibrary/EasyPower.DeviceLibrary/SSTSensorRecord.cs` | Hypothesis 2 evidence — `StpuDelayCalc` and `GroundDelayCalc` field declarations |
| `source-domains/neta-ett-study-material/Development/temp/ilspy-easypower/EasyPower.DeviceLibrary/EasyPower.DeviceLibrary/DevLibTripSensor.cs` | Hypothesis 4 evidence — UI dropdown query (description-only) |
| `source-domains/neta-ett-study-material/Development/temp/ilspy-easypower-types/EasyPower.Types.decompiled.cs` | Hypothesis 2 evidence — `SSTDelayCalc` byte enum values |
| `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md` | Anchor blocker text in §O |

### 2. Exact files changed

The following files were written or edited by this pass; no other authority surface was touched.

| Path | Change |
|---|---|
| `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-HYPOTHESIS-VALIDATION-2026-04-29.md` | New evidence document (this pass) |
| `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-hypothesis-validation-completion-handoff.md` | This completion handoff |
| `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-HYPOTHESIS-VALIDATION-2026-04-29.md` | Completion Record populated only |

The active calc-engine spec, per-element interpretation docs, the findings ledger, the master orchestration plan, prior pass-2 evidence and completion handoffs, runtime / schema / migration / fixture / test surfaces, and other handoff packets are **not** edited (Hard Limit 5: "Do not edit the master plan unless blocker posture truly changes" — blocker posture is unchanged).

### 3. Hypothesis matrix covering all four core hypotheses

| # | Hypothesis | Result | One evidence line | One consequence line |
|---|---|---|---|---|
| 1 | `sdvlSSTSec2Curve` confined to sec2/LTD; `dvlDatInveqDelay` confined to later inverse-delay | **validated** | `DvlEng.cs` sec2 hits at 102001–102546 + 104569–104598 (UI combo); inverse-delay hits at 102702–102786 (STPU) + 103509–103593 (GF); zero overlap | sec2 vs inverse-delay split graduates to file-backed structural fact |
| 2 | DvlEng switch values at `[32]` and `[101]` are `SSTDelayCalc` enum values, not section IDs | **validated** | `SSTSensorRecord.cs:27,33` + `EasyPower.Types.cs:2689–2701` (`INVEQ=2, TUSTD=3`) + DvlEng `case 2` / `==2` at 102700, 103507 | switches are mode-discriminator branches; section identity is the explicit `nSection` argument |
| 3 | `nSection = 3` is STPU inverse (`DatSection3InvEq`); `nSection = 5` is GF inverse (`DatSection1GfInvEq`) | **validated, decisively** | `DvlEng.cs:105701` ternary `(nSection != 3) ? "DatSection1GfInvEq" : "DatSection3InvEq"` from mangled UTF-16LE wide-string literals; per-row reader at 105789–105888 names every GF math-row column directly | row-reader half of the GF loader chain recovered with named columns; populator/consumer step still missing |
| 4 | Managed `ReadStpuDelay` / `ReadGroundDelay` are description-only UI readers | **validated** | `DeviceLibrary.cs:1215–1303` only `SELECT [Desc]` / `SELECT *_DESC`; `DevLibTripSensor.cs:311` only `SELECT DISTINCT *.Desc`; zero managed setter callers | managed surfaces excluded from next-packet search target |

All four hypotheses **VALIDATED**. Zero hypotheses **disproved**. Zero hypotheses **still undetermined**.

### 4. Exact contradiction statement for any disproved hypothesis

**No contradiction was found.** Zero hypotheses were disproved. One pass-2 narrowing is **strengthened** (Hypothesis 3 graduated from structural inference to direct table-name string-literal selection), which is a sharpening of pass-2, not a contradiction of it.

### 5. Exact blocker-posture ruling

**NOT CHANGED.** The §O blocker remains **NOT CLOSED**. The blocker is materially narrowed beyond pass-2 by the direct row-reader recovery (Hypothesis 3 evidence) but is not closed because:

1. Profile-by-profile binding remains **NOT BOUND × 3** — the row-reader populates a `dvlDatInveqDelay` array but does not bind any TASK-B §3.9 profile to any of the eight `Set{Therm,Ansi}_{Flat,Inverse}Delay{Open,Clear}` setters.
2. Database `*ICalc ∈ {1, 4, 8, 10}` to kernel `byICalc ∈ {0, 1, 2}` translation remains **UNRESOLVED** — `dvlSSTGetInvEqDelays` stores the database byte verbatim at offsets 9, 61, 113, 165 of `dvlDatInveqDelay` with default 4; no translation is applied at the row-reader layer.
3. The populator/consumer that iterates the populated `TdbPtrArray<dvlDatInveqDelay>` and calls one of the eight setters per slot remains absent from all five binaries searched (TccBase, DeviceLibrary, DataLayer, DatabaseBrowser, plus DvlEng covered by this pass).

TASK-E remains **BLOCKED**. No TASK-E execution, scoping, or splitting packet is authorized or implied. No GF-side parity claim is implied. No follow-on packet is authored.

## Hard Limits Respected — 5 of 5

1. **PASS** — No claim that the §O blocker is closed.
2. **PASS** — No widening into EasyPower.exe native-side RE, debugger instrumentation, or missing-binary hunting; remaining candidates are named only as next-packet targets.
3. **PASS** — No TASK-E implementation, no fixture generation, no runtime code modification.
4. **PASS** — No structural hypothesis converted into a semantic conclusion without a file-backed bridge: the `*Eq` byte semantic is recorded as "consistent with the kernel discriminator" rather than as a binding.
5. **PASS** — Master plan is not edited; blocker posture truly does not change.

## Merge-Gate Mapping — 4 of 4 PASS

The parent handoff lists six required outcomes rather than explicit merge gates; treating those as the gate:

| Gate | Target | Outcome |
|---|---|---|
| Reconfirm blocker boundary; explicit hypothesis-only posture | PASS | **PASS** |
| Validate or disprove DvlEng object-model split | PASS | **PASS** (validated) |
| Validate or disprove named-field bridge | PASS | **PASS** (validated) |
| Validate or disprove section-parameter hypothesis | PASS | **PASS** (validated, decisively) |
| Validate or disprove managed-layer non-loader hypothesis | PASS | **PASS** (validated) |
| Publish compact hypothesis matrix | PASS | **PASS** |

## Auditor Note

Copilot remains the project manager and auditor for this lane. This hypothesis-validation closure preserves TASK-E's BLOCKED state and does not imply parity, scope split, or reopening of any earlier-closed gate. Per the parent task's Hard Limit 4, no structural hypothesis is converted into a semantic conclusion without a file-backed bridge: the `*Eq` byte semantic agreement between DvlEng's discriminator and the kernel's `0=Therm/1=Ansi/2=FDly` discriminator is recorded as structural agreement, not as a binding. Per the parent task's Hard Limit 5, the master plan is not edited; blocker posture truly does not change. The exact remaining gap is preserved verbatim in evidence §10 and §11 with three unsearched candidate locations named (none authorized by this packet): EasyPower.exe native-side Ghidra; the additional EasyPower DLLs not currently on local disk; bounded dynamic instrumentation against a live-running EasyPower.exe. The next-packet search target is now precisely "the populator/consumer that iterates `TdbPtrArray<dvlDatInveqDelay>` and dispatches per-row to the eight `Set{Therm,Ansi}_{Flat,Inverse}Delay{Open,Clear}` setters, plus the database-to-kernel `*ICalc` translation that the populator applies."
