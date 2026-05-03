# TCC GF-Side Inverse-Equation Populator / Consumer Recovery — Completion Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-gf-side-inverse-equation-populator-consumer-recovery`
Status: **Closed PASS** — consumer binary recovered (`EasyPower.exe`); per-call-site recovery still pending; blocker posture NOT CHANGED (still NOT CLOSED, materially narrowed further)
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-POPULATOR-CONSUMER-RECOVERY-2026-04-29.md`
Authority anchor: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-HYPOTHESIS-VALIDATION-2026-04-29.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Active engine contract: `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
Evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-POPULATOR-CONSUMER-RECOVERY-2026-04-29.md`
Companion handoff (preserved): `ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-populator-consumer-recovery-handoff.md`
Prior pass-3 completion handoff (preserved): `ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-hypothesis-validation-completion-handoff.md`
Prior pass-2 completion handoff (preserved): `ops/agents/handoffs/2026-04-28-tcc-gf-side-inverse-equation-loader-recovery-completion-handoff-pass2.md`

## Summary

The bounded populator/consumer-recovery packet executed end to end against the full PE import-table surface of every native and managed binary at `D:\EasyPower\` (eleven PE files: one .exe + ten .dll) plus all locally available ILSpy decompile drops. The single decisive finding: **`EasyPower.exe` is the unique on-disk binary that imports both ends of the GF loader chain** — it imports `?dvlSSTGetInvEqDelays@@YA_NPAVCDeviceLibrary@@JHAAV?$TdbPtrArray@UdvlDatInveqDelay@@@@@Z` (and the wrapper `?GetInvEqDelays@CSSTSensor@@QAE_NHAAV?$TdbPtrArray@UdvlDatInveqDelay@@@@@Z`) from `DvlEng.dll`, AND all eight `?Set{Therm,Ansi}_{Flat,Inverse}Delay{Open,Clear}@CTccLVBreakerCurveGF@@QAE_NE...@Z` setters from `TccBase.dll`. No other binary on disk imports any of the eight GF setter symbols.

The DEC-018 candidate set named in pass-3 (the off-disk EasyPower DLLs) is now refined: `dbBase.dll`, `UtlBase.dll`, `OliBase.dll`, and `DbBase.Common.dll` are now on local disk and have been searched. None imports any of the eight setters. They are eliminated from the populator-binary candidate set.

The IL section of `EasyPower.exe` (both the 207 MB `EasyPower.il` raw IL dump and the 77 MB `EasyPower.decompiled.cs` ILSpy C# view) contains zero plain-text references to `dvlSSTGetInvEqDelays`, `GetInvEqDelays`, `dvlDatInveqDelay`, or any of the eight GF setter friendly names. Yet the binary's PE import-address table contains all eleven of these symbols. The only consistent explanation is that the call sites that consume these imports live in the **native x86 code section** of the same binary (mixed-mode C++/CLI), invisible to ILSpy.

This is decisive consumer-recovery evidence at binary granularity. Per-call-site recovery within `EasyPower.exe` requires Ghidra-headless static disassembly targeting the eight setter import-thunks and the `dvlSSTGetInvEqDelays` / `GetInvEqDelays` import-thunks, with cross-reference analysis. That step is not authorized by this packet.

DvlEng.dll's GF branch at `DvlEng.cs:103509–103593` was re-read end-to-end and confirmed UI-only: it iterates the populated `TdbPtrArray<dvlDatInveqDelay>` and copies ONLY `Desc` (offset 0) and `InOut` (offset 4) into per-row `sdvlSSTDelay` instances for combo-box display. The 216-byte rows are then cleared. Math-row coefficients and `*ICalc` bytes are never propagated forward by DvlEng. The populator that consumes the math data must therefore be a separate caller of `dvlSSTGetInvEqDelays(..., 5, ...)` — and per import-table evidence above, that caller is in `EasyPower.exe`'s native section.

**The §O blocker remains NOT CLOSED.** Profile-by-profile binding remains **NOT BOUND × 3**. Database `*ICalc ∈ {1, 4, 8, 10}` to kernel `byICalc ∈ {0, 1, 2}` translation remains **UNRESOLVED**. TASK-E remains BLOCKED. The blocker is **further narrowed**: the candidate set of binaries that could host the populator collapses from "any local DLL plus DEC-018 off-disk candidates" to "the native code section of EasyPower.exe." The structural correspondence between DvlEng's `(Fd|Id) × (Op|Cl)` sub-block names and TccBase's `(Flat|Inverse)Delay × (Open|Clear)` setter names is recorded as structural agreement only, not as binding (Hard Limit 3 respected).

## Expected Deliverables Back To Copilot

### 1. Exact binaries searched

| Path | Searched For | Result |
|---|---|---|
| `D:\EasyPower\TccBase.dll` | exports inventory of the 8 GF setters | All 8 exported (ordinals 13F, 140, 141, 142, 18B, 18C, 18D, 18E) |
| `D:\EasyPower\EasyPower.exe` | imports of the 8 setters + `dvlSSTGetInvEqDelays` + `GetInvEqDelays` | **Imports all 11** — sole on-disk binary doing so |
| `D:\EasyPower\DvlEng.dll` | imports of the 8 setters | 0 / 8 |
| `D:\EasyPower\dbBase.dll` | imports of the 8 setters | 0 / 8 |
| `D:\EasyPower\UtlBase.dll` | imports of the 8 setters | 0 / 8 |
| `D:\EasyPower\OliBase.dll` | imports of the 8 setters | 0 / 8 |
| `D:\EasyPower\EasyPower.Database.dll` | imports of the 8 setters | 0 / 8 |
| `D:\EasyPower\EasyPower.DeviceLibrary.dll` | imports of the 8 setters | 0 / 8 |
| `D:\EasyPower\EasyPower.DataLayer.dll` | imports of the 8 setters | 0 / 8 |
| `D:\EasyPower\EasyPower.DatabaseBrowser.dll` | imports of the 8 setters | 0 / 8 |
| `D:\EasyPower\DbBase.Common.dll` | imports of the 8 setters | 0 / 8 |
| Full sweep `D:\EasyPower\*.dll *.exe` | imports of the 8 setters | Only `EasyPower.exe` matches; all other DLLs (incl. Telerik, BCG, System.*, Microsoft.*) return 0 |
| `temp/ilspy-easypower-exe/EasyPower.decompiled.cs` (77 MB) | plain-text matches for setter friendly names + row-reader names + `dvlDatInveqDelay` | Zero direct matches for setter or row-reader; 22 matches for `CTccLVBreakerCurveGF` (all `ComputeAmps`/`ComputeTime` evaluator calls); 13 matches for `sdvlSSTDelay` (all `blvPopulate*` UI calls) |
| `temp/ilspy-easypower-exe-il/EasyPower.il` (207 MB) | same patterns | Zero direct matches for setter or row-reader; 27 matches for `CTccLVBreakerCurveGF` (all evaluator) |
| `temp/ilspy-dvleng/DvlEng.decompiled.cs` | callers of `dvlSSTGetInvEqDelays`; structure of GF branch | 4 callers (definition + wrapper at 38987 + STPU branch at 102720 + GF branch at 103527); GF branch confirmed UI-only |
| `temp/ilspy-easypower-database/EasyPower.Database.decompiled.cs` | any of the patterns | Zero matches |
| `temp/dbBase/dbBase/` (per-function ILSpy drop) | any of the patterns | Zero matches |
| `temp/ilspy-easypower/TccBase/-Module-.cs` (focus 18930–19024) | 8 setter body shapes | All 8 confirmed: Therm = 5 doubles, Ansi = 6 doubles; first byte ∈ {0,1} = Therm/Ansi flag; second byte = byICalc; struct anchors at offsets 272/376/480/584 |

### 2. Exact files changed

| Path | Change |
|---|---|
| `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-POPULATOR-CONSUMER-RECOVERY-2026-04-29.md` | New evidence document (this pass) — 20 sections covering entry-gate verification, RE authority surface, setter inventory, setter-import sweep, row-reader import sweep, IL-surface confirmation, DvlEng GF-branch cross-check, structural correspondence, `*ICalc` translation status, hypothesis matrix, blocker-posture ruling, next-step ruling, authority-surface reconciliation, acceptance criteria mapping, hard-limits compliance, stop-and-flag compliance, decision-boundary answers |
| `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-populator-consumer-recovery-completion-handoff.md` | This completion handoff |
| `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-POPULATOR-CONSUMER-RECOVERY-2026-04-29.md` | Status banner advanced to "Closed PASS — 2026-04-29"; Completion Record populated only |
| `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-populator-consumer-recovery-handoff.md` | Status banner advanced to "Closed PASS — 2026-04-29" |

The active calc-engine spec, per-element interpretation docs, the findings ledger, the master orchestration plan, prior pass-2 / pass-3 evidence and completion handoffs, runtime / schema / migration / fixture / test surfaces, and other handoff packets are **not** edited (Hard Limit 4: "Do not edit the master plan unless blocker posture truly changes" — blocker posture is unchanged).

### 3. Exact consumer evidence recovered

**Binary granularity: RECOVERED.** `EasyPower.exe` is the unique on-disk binary that imports both:

1. The DvlEng row-reader and its wrapper:
   - `?dvlSSTGetInvEqDelays@@YA_NPAVCDeviceLibrary@@JHAAV?$TdbPtrArray@UdvlDatInveqDelay@@@@@Z` (DvlEng.dll ordinal 322)
   - `?GetInvEqDelays@CSSTSensor@@QAE_NHAAV?$TdbPtrArray@UdvlDatInveqDelay@@@@@Z` (DvlEng.dll ordinal 194)
2. All eight TccBase.dll GF setters:
   - `?SetAnsi_FlatDelayClear@CTccLVBreakerCurveGF@@QAE_NENNNNNN@Z` (ordinal 13F)
   - `?SetAnsi_FlatDelayOpen@CTccLVBreakerCurveGF@@QAE_NENNNNNN@Z` (ordinal 140)
   - `?SetAnsi_InverseDelayClear@CTccLVBreakerCurveGF@@QAE_NENNNNNN@Z` (ordinal 141)
   - `?SetAnsi_InverseDelayOpen@CTccLVBreakerCurveGF@@QAE_NENNNNNN@Z` (ordinal 142)
   - `?SetTherm_FlatDelayClear@CTccLVBreakerCurveGF@@QAE_NENNNNN@Z` (ordinal 18B)
   - `?SetTherm_FlatDelayOpen@CTccLVBreakerCurveGF@@QAE_NENNNNN@Z` (ordinal 18C)
   - `?SetTherm_InverseDelayClear@CTccLVBreakerCurveGF@@QAE_NENNNNN@Z` (ordinal 18D)
   - `?SetTherm_InverseDelayOpen@CTccLVBreakerCurveGF@@QAE_NENNNNN@Z` (ordinal 18E)

**Per-call-site granularity: NOT YET RECOVERED.** The IL section of `EasyPower.exe` contains zero plain-text references to any of the imports above. The call sites must therefore live in the native x86 code section of `EasyPower.exe`, requiring Ghidra-headless static disassembly to recover. This is the next-packet target, not authorized by this packet.

### 4. Exact `*ICalc` translation evidence recovered or unresolved ruling

**UNRESOLVED.** The translation from database `*ICalc ∈ {1, 4, 8, 10}` to kernel `byICalc ∈ {0, 1, 2}` is not directly recovered by this packet. Direct evidence narrows its location:

1. `dvlSSTGetInvEqDelays` (DvlEng row-reader, recovered in pass-3) stores the database `*ICalc` byte verbatim into `dvlDatInveqDelay` offsets 9, 61, 113, 165 with default 4. No translation at the row-reader layer.
2. DvlEng.dll's GF branch at `DvlEng.cs:103509–103593` (re-read in this pass) reads only `InOut` (offset 4) and `Desc` (offset 0) from each populated row. It never reads `*ICalc` bytes. No translation in DvlEng's consumer.
3. The eight kernel setters take `byte byICalc` directly (per `temp/ilspy-easypower/TccBase/-Module-.cs:18930–19024`). The translation must therefore be applied at the populator that calls these setters — i.e., inside `EasyPower.exe`'s native x86 section, which is the only on-disk location that imports both the row-reader and the setters.

The translation is therefore narrowed to "the same native function (or functions) inside `EasyPower.exe` that contains the per-call-site populator." Direct recovery requires Ghidra-headless static disassembly.

### 5. Slot-to-setter binding matrix — NOT BOUND × 3

No direct binding is claimed. Structural correspondence is recorded as agreement only, per Hard Limit 3 ("Do not treat structural agreement as binding"):

| `dvlDatInveqDelay` sub-block | Sub-block first-byte (`*Eq`) | Setter family |
|---|---|---|
| FdOp at offset 8 | `FdOpEq ∈ {0, 1, 2}` | `Set{Therm,Ansi}_FlatDelayOpen` (kernel anchor at offset 272) |
| FdCl at offset 60 | `FdClEq ∈ {0, 1, 2}` | `Set{Therm,Ansi}_FlatDelayClear` (kernel anchor at offset 376) |
| IdOp at offset 112 | `IdOpEq ∈ {0, 1, 2}` | `Set{Therm,Ansi}_InverseDelayOpen` (kernel anchor at offset 480) |
| IdCl at offset 164 | `IdClEq ∈ {0, 1, 2}` | `Set{Therm,Ansi}_InverseDelayClear` (kernel anchor at offset 584) |

The slot-name correspondence (`Fd→FlatDelay`, `Id→InverseDelay`, `Op→Open`, `Cl→Clear`) and the first-byte semantic (`0→Therm 5-float`, `1→Ansi 6-float`, `2→FDly 1-float`) match the kernel-side recovery. **This is not direct binding.** Profile-by-profile binding remains **NOT BOUND × 3**. Direct binding requires per-call-site native-side recovery that observes which sub-block dispatches to which setter at runtime — not produced by this packet.

### 6. Exact blocker-posture ruling

**NOT CHANGED.** The §O blocker remains **NOT CLOSED**. The blocker is materially narrowed beyond pass-3 by the import-table-decisive consumer-binary recovery (§3 above) but is not closed because:

1. Profile-by-profile binding remains **NOT BOUND × 3** — no TASK-B §3.9 profile is directly bound to any setter path. Structural correspondence is recorded as agreement only.
2. Database `*ICalc ∈ {1, 4, 8, 10}` to kernel `byICalc ∈ {0, 1, 2}` translation remains **UNRESOLVED** — narrowed to "inside EasyPower.exe's native section" but not directly recovered.
3. The per-call-site populator inside `EasyPower.exe` is **not yet recovered** — its existence is established by import-table evidence, but the per-function name and the dispatch shape live in the native x86 section beyond ILSpy's reach.

TASK-E remains **BLOCKED**. No TASK-E execution, scoping, or splitting packet is authorized or implied. No GF-side parity claim is implied. No follow-on packet is authored.

## Hard Limits Respected — 5 of 5

1. **PASS** — No claim that the §O blocker is closed.
2. **PASS** — No widening into TASK-E implementation, fixtures, or runtime code changes.
3. **PASS** — No structural agreement is treated as binding: the slot-to-setter correspondence and first-byte semantic are recorded as agreement only.
4. **PASS** — Master plan is not edited; blocker posture truly does not change.
5. **PASS** — No debugger or live-instrumentation work was improvised. Static work has not exhausted (Ghidra-headless on EasyPower.exe remains an authorized next-packet option); this packet is bounded by the cheapest static check (PE import-table evidence) and stops before requiring Ghidra or dynamic instrumentation.

## Stop-And-Flag Compliance — All Five Triggers Negative

| Trigger | Status |
|---|---|
| Remaining evidence depends on speculative struct reinterpretation rather than direct native-side evidence | **NEGATIVE** — all evidence is direct PE import-table and ILSpy plain-text grep |
| Claimed binding relies only on `*Eq` discriminator and not on actual setter dispatch | **NEGATIVE** — no binding claim made; structural correspondence recorded as non-binding |
| Dynamic instrumentation becomes the only honest next move | **NEGATIVE** — Ghidra-headless static disassembly of EasyPower.exe remains an authorized static option not yet attempted in this lane |
| The next binary required is not on local disk | **NEGATIVE** — EasyPower.exe is on local disk |
| Blocker posture appears to change but the recovered evidence still does not bind profiles to setter paths directly | **NEGATIVE** — blocker posture explicitly preserved; structural correspondence not promoted to binding |

## Auditor Note

Copilot remains the project manager and auditor for this lane. This populator/consumer-recovery closure preserves TASK-E's BLOCKED state and does not imply parity, scope split, or reopening of any earlier-closed gate. Per the parent task's Hard Limit 3, no structural correspondence is converted into binding; the four-sub-block name correspondence and the first-byte 0/1/2 semantic are recorded as structural agreement only. Per the parent task's Hard Limit 4, the master plan is not edited; blocker posture truly does not change. The exact remaining gap is preserved verbatim in evidence §13 and §14: the per-call-site populator inside `EasyPower.exe`'s native x86 section that bridges `dvlSSTGetInvEqDelays(..., 5, ...)` to the eight setters, plus the `*ICalc → byICalc` translation that the same populator applies. The next-packet method is named: Ghidra-headless static disassembly of `EasyPower.exe` targeting the import-thunks of the eight setters (TccBase.dll ordinals 13F/140/141/142/18B/18C/18D/18E) and the import-thunks of `dvlSSTGetInvEqDelays` / `GetInvEqDelays` (DvlEng.dll ordinals 322/194), with cross-reference analysis modeled on the existing `BruteScanGfCallers.java` and `FindGfLoaderEvidence.java` Ghidra scripts at `C:\Users\jjswe\Tools\ghidra-scripts\`. That work is not authorized by this packet.

The DEC-018 candidate list is updated by direct evidence: `dbBase.dll`, `UtlBase.dll`, `OliBase.dll`, and `DbBase.Common.dll` are now on local disk and **eliminated** from the populator-binary candidate set — they import zero of the eight GF setters. The DEC-018 line of inquiry concerning off-disk EasyPower DLLs is therefore closed for the GF-side populator question (subject to the residual possibility that some binary loaded dynamically via `LoadLibrary` could host the populator without appearing in any static import table; that residual possibility is not justified by current evidence and would require dynamic instrumentation to disprove).
