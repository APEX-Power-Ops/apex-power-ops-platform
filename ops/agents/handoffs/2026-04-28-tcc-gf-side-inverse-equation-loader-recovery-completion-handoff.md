# TCC GF-Side Inverse-Equation Loader Recovery And Profile-Binding Completion Handoff

Date: 2026-04-28
Packet: `2026-04-28-tcc-gf-side-inverse-equation-loader-recovery`
Status: **Executed / closed PASS**
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Inbound handoff: `ops/agents/handoffs/2026-04-28-tcc-gf-side-inverse-equation-loader-recovery-handoff.md`
Project: rebuilt TCC runtime lane against Supabase `fxoyniqnrlkxfligbxmg`

## Headline Result

The bounded GF-side inverse-equation loader-recovery and profile-binding
packet executed end to end. The truthful result on disk is that the GF-side
inverse-equation dispatch blocker named in `EASYPOWER-CALC-ENGINE-SPEC.md` §O
is still **NOT CLOSED**, materially narrowed further than TASK-019B left it.
The loader path that reads `DatSection1GfInvEq` math-row columns and invokes
the eight `Set{Therm,Ansi}_{Flat,Inverse}Delay{Open,Clear}` setters is now
confirmed absent from every preserved managed-IL artifact on disk and not
recoverable from the preserved TccBase native-side Ghidra logs (which
targeted non-GF offsets). All four merge gates passed and all five hard
limits were respected.

## Exact Files Changed

1. `C:\APEX Platform\source-domains\neta-ett-study-material\Development\Platform\TCC\TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28.md`
   — **created**; 14-section evidence document.
2. `C:\APEX Platform\source-domains\neta-ett-study-material\Development\TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28.md`
   — Status banner advanced from "Authored 2026-04-28. Not yet executed." to
   "Closed PASS 2026-04-28" with structured NOT CLOSED ruling text;
   Completion Record advanced to a 5-item structured closure naming the
   loader-recovery, profile-binding, `*ICalc` translation, blocker-status,
   and downstream rulings exactly.
3. `C:\APEX Platform\source-domains\tcc_v5_backend\plan\architecture-tcc-master-orchestration-1.md`
   — Current Program Posture extended 15→16 items (item 13 advanced to
   record packet closure with NOT CLOSED ruling; new item 14 "no further
   calc-engine move automatically queued"; old items 14-15 renumbered to
   15-16). Stakeholder Approval Posture row "GF-side inverse-equation
   loader-recovery and profile-binding packet" advanced from "Approved and
   next" to "Approved and closed" with closure result. New DEC-018 added
   to Decision Ledger.
4. `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-04-28-tcc-gf-side-inverse-equation-loader-recovery-completion-handoff.md`
   — **this completion handoff**.

`EASYPOWER-CALC-ENGINE-SPEC.md` §O is **not** modified. The spec retains its
existing authorization wording.

## Exact New Evidence Reviewed Or Produced

Reviewed:

1. The full preserved decompile corpus across `C:\APEX Platform\source-domains\neta-ett-study-material\Development\temp\` (8 ilspy roots) and `C:\Users\jjswe\Box\TCC_Master\` (DLL + Decompile trees with 7 sub-projects).
2. The 28+ class files inside `Box\TCC_Master\Decompile\EasyPower.DeviceLibrary\EasyPower\DeviceLibrary\` including `DevLibTripSensor.cs`, `DeviceLibrary.cs`, `SSTSensorRecord.cs`, `AdoDatabase.cs`, `DataConvert.cs`, plus 23 other class files.
3. The 648 files in `Box\TCC_Master\Decompile\TCCBase\` including the `<Module>`-level setter definitions in `-Module-.cs`, the `CTccLVBreakerCurveGF.cs`, `GFInverseEqDelay.cs`, `GFInverseEqDelayData.cs`, `SSTInverseEqDelay.cs`, `SSTInverseEqDelayData.cs` definition files, and the C++/CLI mangled-name native artifact files.
4. The preserved Ghidra-headless log artifacts at `C:\Users\jjswe\Tools\ghidra-projects\`: `field_writers.log` (28,838 native instructions in TccBase range `10001000-10056dff` scanned, target offsets corresponded to `CTccTransformerCurveBase` not `CTccLVBreakerCurveGF`), `vtable_dispatcher.log` (8 vtable slots and 3 probe addresses all returned "no refs at all"), plus precedent `sst_callers.log`, `brute_scan.log`, `byte_pattern.log`, `force_disasm.log`.
5. `TccBase.csproj` revealing references to `dbBase.dll`, `EasyPower.DataLayer.dll`, `UtlBase.dll` whose binaries are not on local disk.

Produced:

1. The 14-section evidence document at `Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28.md`.
2. Structured authority-surface deltas in the parent task doc (Status + Completion Record) and master plan (Current Program Posture, Stakeholder Approval Posture row, DEC-018).

## Exact Loader-Recovery Result

**NOT RECOVERED.**

1. Setter-name caller search across all artifacts: 16 occurrences = 8 setter definitions × 2 mirror copies of TccBase `-Module-.cs`. **Zero callers** in any decompiled managed IL across the full corpus. Reproduces TASK-019B at maximum search scope.
2. Math-row column-name search (`FdOpEq`, `FdClEq`, `IdOpEq`, `IdClEq`, `FdOpICalc`, `FdClICalc`, `IdOpICalc`, `IdClICalc`, `FdOp[1-6]`, `FdCl[1-6]`, `IdOp[1-6]`, `IdCl[1-6]`): **zero matches** in any decompiled .cs or .il file anywhere on disk. Math columns are only referenced in DB schema/data files (Tables_Schema.csv, DatSection1GfInvEq.csv, migration .py).
3. `DatSection1GfInvEq` reference search: exactly **one** managed-IL consumer found anywhere — `EasyPower.DeviceLibrary.DeviceLibrary.ReadGroundDelay` line 1281 selecting `[Desc]` for the UI dropdown. This consumer does not read math-row columns and does not invoke any setter.
4. Slot-offset write search (`[272]`, `[273]`, `[376]`, `[377]`, `[480]`, `[481]`, `[584]`, `[585]`): hits in `EasyPower.decompiled.cs` and `DvlEng.decompiled.cs` are unrelated power-flow code (CDlgPfMcc, CDlgPfMot, CPFEngine, COnelineDatabase pointer arrays at incidental offsets), **not** GF discriminator writes.
5. Adjacent decompile dirs (`dbBase`, `EasyPowerTypes`, `EntityFramework`, `TCCCurve`): **zero** GF-side references.
6. Prior TccBase Ghidra logs: `field_writers.log` targeted `CTccTransformerCurveBase` at offsets `0x248`, `0x280`, `0x290` (not GF offsets `0x110/0x111`, `0x178/0x179`, `0x1e0/0x1e1`, `0x248/0x249` inside `GFInverseEqDelay`). `vtable_dispatcher.log` returned "no refs" across 8 slots + 3 probes. **No GF-targeted Ghidra run was executable in this packet** because TccBase.dll and EasyPower.DeviceLibrary.dll binaries are not on the local disk and D drive (where `D:\EasyPower\11.0\` lives) is currently not mounted.
7. **Curve-class hierarchy ILSpy stubs are empty-body native types — including `CTccLVBreakerCurveGF` itself** (per stakeholder pointer 2026-04-28 to apex-temp `GFInverseEqDelay.cs`): The canonical apex-temp ILSpy emission `Development\temp\ilspy-easypower\TccBase\` and the byte-identical Box mirror `Box\TCC_Master\Decompile\TCCBase\` show the entire curve-class family — `CTccCurveBase` (size 96), `CTccGenericCurveBase` (size 40), `CTccCableCurveBase` (size 96 + nested empty `Material` enum), `CTccFuseCurveBase`, `CTccGeneratorCurveBase`, `CTccMotorCurveBase`, `CTccMotorOverloadBase`, `CTccRelayCurveBase`, `CTccTransformerCurveBase`, **`CTccLVBreakerCurveGF` (size 1360)**, `CTccLVBreakerCurveMCP` (size 376), `CTccLVBreakerCurveNSST` (size 1128), `CTccLVBreakerCurveSST` (size 2592), `CTccLVBreakerCurveTMT` (size 512), `GFInverseEqDelay` (size 424), `GFInverseEqDelayData` (size 104, with nested `sTherm`/`sAnsi`/`sFDly` of sizes 40/48/8), `SSTInverseEqDelay` (size 232), `SSTInverseEqDelayData` (size 56, with nested `sTherm`/`sFDly` of sizes 40/8) — as 8-to-16-line `[NativeCppClass]` `[StructLayout]` size-only stubs with no method bodies. This **proves** the curve types are pure native C++ classes whose implementation ILSpy cannot lift.
8. **EasyPower.DeviceLibrary breaker layer is UI picker only; EasyPower.exe is read-only against the GF sub-curve** (per stakeholder pointer 2026-04-28 at the apex-temp `EasyPower.DeviceLibrary\EasyPower.DeviceLibrary\` directory). The breaker-named files (`DevLibBreakerManufacturer/Style/Type`, `DevLibTripSensor/Style/Type/Manufacturer`, `DevLibTMTFrameSize`, `HvBreakerStyleInfo`, `SSTSensorRecord`) issue description-and-setting `SELECT` queries against `BreakerPCB/ICCB/MCCB`, `DatSensor`, `DatPlugs`, `DatSection*` tables for UI dropdowns; they never read math-row coefficient columns. EasyPower.exe (`EasyPower.decompiled.cs`) has 674 references to `CTccLVBreakerCurveGF` but **zero setter calls and zero math-row column references**: it declares `CTccLVBreakerCurveGF.ComputeAmps` and `.ComputeTime` as `extern` managed-IL imports from TccBase.dll (lines 1330869 and 1335159) and uses the pattern `(CTccLVBreakerCurveGF*)((byte*)ptr_outer + 376)` (lines 361917, 451740, 657105, 660378-661523, 663369) to access an embedded GF sub-curve at offset +376 of an enclosing LV breaker curve, but only to *read* the populated curve. The entire managed-IL surface above TccBase.dll is read-only against the GF sub-curve. Population happens entirely inside TccBase.dll native C++ code. Recorded in evidence document §6.2.
9. **Correction to TASK-019B §6 attribution:** TASK-019B cited the 2,187-line file at `Box\TCC_Master\DLL\CTccLVBreakerCurveGF.cs` as the source of the in-class kernel dispatcher and 8 setter definitions. That file is **not** a direct ILSpy emission; it is a curated/synthesized view aggregating `<Module>`-level managed C++/CLI free functions textually under the class name. The canonical ILSpy emission of `CTccLVBreakerCurveGF` is a 9-line empty stub. The functional facts (slot offsets, kernel discriminator, `byICalc` enum) recovered in TASK-019B §6 remain correct because they appear in the canonical `<Module>`-level emission at `Development\temp\ilspy-easypower\TccBase\-Module-.cs` (54,707 lines): (a) the 8 setter definitions are at lines 18932-19027, with each setter family writing only to one of the 4 slot pairs (272/273, 376/377, 480/481, 584/585); (b) the 4-slot curve evaluator at lines 17583-17749 reads discriminator bytes at `[272]` (slot 1 = flat open), `[376]` (slot 2 = flat clear), `[480]` (slot 3 = inverse open), `[584]` (slot 4 = inverse clear) and dispatches to `CalcThermEq` or `CalcAnsiEqGF` per discriminator. **Slot identity is now firmly bound to curve-type × operation: slot 1 = flat open, slot 2 = flat clear, slot 3 = inverse open, slot 4 = inverse clear.** Slot-byte write count in `-Module-.cs` is exactly 16 = 2 × 8 setters; zero external writers. Loader path is provably in unmanaged native code in TccBase.dll (or a sibling DLL of similar mixed-mode emission), not in any managed-IL artifact anywhere on disk. Recorded in evidence document §6.1.

## Exact Profile-By-Profile Binding Result

**NOT BOUND × 3.**

| Profile | InOut | (FdOpICalc, FdClICalc, IdOpICalc, IdClICalc) | (FdOpEq/FdClEq, IdOpEq/IdClEq) | Row count | Style examples | Setter family attempted | byICalc binding attempted | Slot offset attempted | Binding result |
|---------|-------|------------------------------------------------|---------------------------------|-----------|----------------|-------------------------|---------------------------|------------------------|----------------|
| 1 | 0 | (8, 8, 4, 4) | (0, 0) | 1,690 | (general LV breaker baseline) | unknown | unknown | unknown | **NOT BOUND** |
| 2 | 1 | (4, 4, 8, 8) | (1, 1) | 100 | Federal Pioneer LSIG | unknown | unknown | unknown | **NOT BOUND** |
| 3 | 2 | (8, 8, 1, 1) | (0, 0) | 6,760 | Square D Micrologic 6.x / MTZ | unknown | unknown | unknown | **NOT BOUND** |

Inferring bindings from naming similarity (e.g., "*Eq selects setter family"
or "FdOp* → SetTherm_FlatDelayOpen") was rejected per Stop-And-Flag rule 2.

## Exact `*ICalc` Translation Result

**UNRESOLVED.**

| Database `*ICalc` | Frequency in TASK-B §3.9 | Hypothesized kernel `byICalc` | Evidence on disk |
|-------------------|--------------------------|--------------------------------|-------------------|
| 1 | dominant in profile 3 IdOp/IdCl (6,760 rows) | unknown | none |
| 4 | dominant in profile 1 IdOp/IdCl (1,690 rows) and profile 2 FdOp/FdCl (100 rows) | unknown | none |
| 8 | dominant in profile 1 FdOp/FdCl (1,690 rows), profile 3 FdOp/FdCl (6,760 rows), and profile 2 IdOp/IdCl (100 rows) | unknown | none |
| 10 | small style-specific row count in TASK-B §3.9 raw enumeration | unknown | none |

Direct pass-through (treat `*ICalc` as `byICalc`) is structurally implausible
(would yield "no curve" per the kernel `byICalc` enum `{0→ref[16], 1→ref[13],
2→ref[12], else→no curve}` for the dominant majority of rows) but
implausibility is not recovered evidence of any specific translation table.

## Exact Blocker-Status Ruling

**NOT CLOSED, materially narrowed further than TASK-019B left it.**

The GF-side inverse-equation dispatch blocker named in
`EASYPOWER-CALC-ENGINE-SPEC.md` §O is preserved. Material narrowing this
packet adds beyond TASK-019B:

1. EasyPower.exe high-level decompile + raw IL form — no GF-side loader; slot-offset hits are unrelated power-flow code.
2. DvlEng decompile — zero GF-side references.
3. EasyPower.DeviceLibrary full decompile tree — only `[Desc]`-only `ReadGroundDelay`; `DevLibTripSensor.cs` only touches `DatSection3InvEq.InOut` (SST-side STD inverse, not GF-side).
4. Adjacent decompile dirs (dbBase, EasyPowerTypes, EntityFramework, TCCCurve) — zero GF-side references.
5. Slot-offset writes search across the full corpus — only the 8 setter definitions themselves; no external writer.
6. TccBase.dll prior Ghidra logs — both prior runs targeted non-GF offsets and returned zero useful GF callers.

The exact remaining gap: the loader is in either (a) `TccBase.dll` native
side at GF-specific offsets the prior Ghidra runs did not target, or (b) one
of `EasyPower.DeviceLibrary.dll`, `dbBase.dll`, `UtlBase.dll`,
`EasyPower.DataLayer.dll` whose binaries are not on the local disk.

## Exact Downstream Authorization Ruling

**TASK-E remains BLOCKED.**

No TASK-E execution, scoping, or splitting packet is authorized or implied
by this ruling. No GF-side parity claim is implied. Any future
loader-recovery packet must be separately authored under its own authority
and is conditional on either:

1. D drive availability + GF-targeted Ghidra `FindFieldWriters` against
   `EasyPower.DeviceLibrary.dll` (highest-promise per stakeholder guidance
   2026-04-28), `dbBase.dll`, `UtlBase.dll`, `EasyPower.DataLayer.dll`, or
   a fresh GF-targeted run against `TccBase.dll` with target offsets
   `0x110, 0x111, 0x178, 0x179, 0x1e0, 0x1e1, 0x248, 0x249` (i.e.,
   272/273, 376/377, 480/481, 584/585 in decimal) plus per-slot
   coefficient offsets, or
2. a separately authored bounded dynamic instrumentation lane against a
   live `EasyPower.exe` with debugger-backed argument capture at the
   eight `<Module>`-level setter symbols.

`EASYPOWER-CALC-ENGINE-SPEC.md` §O retains its current "narrow scope only
after the matching open question closes" wording without modification.
DEC-005, DEC-014, DEC-015, DEC-016, DEC-017, and DEC-018 remain operative.

## Merge Gate Outcomes — 4 of 4 PASS

| Gate | Target result | Actual outcome |
|---|---|---|
| Entry-gate loader-recovery posture reconfirmed | PASS | **PASS** (6 of 6 entry-gate facts re-verified on disk) |
| Loader path recovery result stated exactly | PASS | **PASS** (NOT RECOVERED, with the exact methodology and search scope recorded) |
| GF-side profile-by-profile binding result stated exactly | PASS | **PASS** (NOT BOUND × 3 across the three accepted TASK-B §3.9 profiles) |
| One explicit blocker-status and downstream ruling published | PASS | **PASS** (NOT CLOSED with material narrowing recorded; TASK-E BLOCKED with conditional re-open trigger named) |

All five hard limits respected: no TASK-E implementation, no GF-side parity
claim, no fixture/test/runtime code change, no Tier B reopening or Phase 6
widening, no invented semantics.

## Auditor Note

Copilot remains the project manager and auditor for this lane. Control
returns to Copilot. No follow-on packet is authored or pre-authorized by
this ruling. Any future GF-side inverse-equation loader-recovery RE packet
must be authored separately under its own authority document and must not
reuse this packet's authorization to bypass the still-active blocker. The
operator hint that `EasyPower.DeviceLibrary.dll` is the highest-promise
next Ghidra target is recorded in §14 of the evidence document and in
DEC-018 as guidance for any future packet, not as a pre-authorization.
