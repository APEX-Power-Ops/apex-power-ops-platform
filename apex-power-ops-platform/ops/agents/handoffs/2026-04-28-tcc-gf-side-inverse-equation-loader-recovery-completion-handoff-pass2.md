# TCC GF-Side Inverse-Equation Loader Recovery — Pass 2 Completion Handoff

Date: 2026-04-28
Packet: `2026-04-28-tcc-gf-side-inverse-equation-loader-recovery` (reopened, pass 2)
Status: **Closed PASS** — blocker NOT CLOSED, materially narrowed beyond TASK-019B and the prior 2026-04-28 pass
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Active engine contract: `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
Evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28-PASS2.md`
Prior pass evidence (preserved): `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28.md`
Prior completion handoff (preserved): `ops/agents/handoffs/2026-04-28-tcc-gf-side-inverse-equation-loader-recovery-completion-handoff.md`

## Summary

The reopened bounded GF-side inverse-equation loader-recovery packet executed end to end against four local binaries: `TccBase.dll`, `EasyPower.DeviceLibrary.dll`, plus `EasyPower.DataLayer.dll` and `EasyPower.DatabaseBrowser.dll` (the latter two surfaced on local disk by operator hint mid-execution; the packet's bounded scope was honored by treating each new binary the same way as the original two). The §O blocker remains **NOT CLOSED** but is materially narrowed beyond TASK-019B and the prior 2026-04-28 pass: the loader is now binary-confirmed absent from all four local binaries via Ghidra-headless analysis plus per-binary instruction-operand / vtable-slot / setter-symbol / column-name byte-pattern scans in both ASCII and UTF-16LE encodings, plus PE-imports inventory confirming none of the candidate binaries statically link to TccBase.dll's GF setter exports. TASK-E remains BLOCKED. No TASK-E execution, scoping, or splitting packet is authorized. All four merge gates passed and all five hard limits were respected.

Follow-up review after pass-2 closure adds one useful DVL-layer narrowing without changing the blocker ruling: `DvlEng.dll` uses `sdvlSSTSec2Curve` as a dedicated sec2/LTD curve model, while both later inverse-delay call sites flow through the generic `dvlDatInveqDelay` loader `dvlSSTGetInvEqDelays(..., nSection, ...)` with `nSection = 3` and `nSection = 5`. That supports a shared or section-parameterized STD/GF inverse-delay abstraction at the DVL layer, but it still does not expose any GF setter call site or any `*ICalc`-to-`byICalc` translation.

Follow-up review also resolves one naming ambiguity in that DVL branch structure: the controlling switch values are not section IDs, they are `SSTDelayCalc` enum values carried on the sensor record. Managed `EasyPower.DeviceLibrary` shows `StpuDelayCalc` and `GroundDelayCalc` both use `SSTDelayCalc`, where `INVEQ = 2` and `TUSTD = 3`. That matches the two DvlEng switches exactly: the section-3 branch switches on the STPU delay-calc field and only then calls `dvlSSTGetInvEqDelays(..., 3, ...)`, while the later GF branch switches on the ground-delay field and only then calls `dvlSSTGetInvEqDelays(..., 5, ...)`. So `2` and `3` in the switch are mode values, while `3` and `5` passed into `dvlSSTGetInvEqDelays` are the actual section parameters.

## Expected Deliverables Back To Copilot

### 1. Exact files changed

The following files were written or edited by this pass; no other authority surface was touched.

| Path | Change |
|---|---|
| `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28-PASS2.md` | New evidence document (this pass) |
| `apex-power-ops-platform/ops/agents/handoffs/2026-04-28-tcc-gf-side-inverse-equation-loader-recovery-completion-handoff-pass2.md` | This completion handoff |
| `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28.md` | Status banner / Reopen Record extension recording pass-2 closure (no scope or limit changes) |
| `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md` | Current Program Posture extended; Stakeholder Approval Posture row advanced to "Approved and closed (pass 2)"; new DEC-020 row; TASK-019C row marked closed in Phase 6 implementation table |

The active calc-engine spec (`EASYPOWER-CALC-ENGINE-SPEC.md`), per-element interpretation docs, the findings ledger, the prior pass's evidence and completion handoff, runtime / schema / migration / fixture / test surfaces, and other handoff packets are **not** edited.

### 2. Exact new evidence reviewed or produced

Evidence newly produced:

| Artifact | Bytes | Purpose |
|---|---|---|
| `C:\Users\jjswe\Tools\ghidra-projects-loader-re\TccGfLoader_20260428.gpr` (+ `.rep` directory) | — | Fresh Ghidra project containing both DLLs with full default auto-analysis |
| `C:\Users\jjswe\Tools\ghidra-scripts\FindGfLoaderEvidence.java` | ~7 KB | Author-script: 8-setter symbol/xref scan + string scan + function-name scan + raw ASCII byte-pattern scan + UTF-16LE byte-pattern scan |
| `C:\Users\jjswe\Tools\ghidra-scripts\BruteScanGfCallers.java` | ~4 KB | Author-script: per-instruction operand scan against 16 GF setter addresses + 8 GF vtable slots |
| `C:\Users\jjswe\Tools\ghidra-projects-loader-re\evidence_TccBase.dll.txt` | 28,237 B | Setter / string / function / import / pattern dump for TccBase.dll |
| `C:\Users\jjswe\Tools\ghidra-projects-loader-re\evidence_EasyPower.DeviceLibrary.dll.txt` | 4,658 B | Same dump for DeviceLibrary.dll |
| `C:\Users\jjswe\Tools\ghidra-projects-loader-re\evidence_EasyPower.DataLayer.dll.txt` | 12,590 B | Same dump for DataLayer.dll (operator-surfaced mid-execution) |
| `C:\Users\jjswe\Tools\ghidra-projects-loader-re\evidence_EasyPower.DatabaseBrowser.dll.txt` | 3,340 B | Same dump for DatabaseBrowser.dll (operator-surfaced mid-execution; auto-analysis bounded at 180 s) |
| `C:\Users\jjswe\Tools\ghidra-projects-loader-re\brute_scan_gf.txt` | ~2 KB | Per-target hit summary: 8 setter-target hits (all are PE export-table entries), 0 vtable-slot hits |
| `C:\Users\jjswe\Tools\ghidra-projects-loader-re\headless_run.log` | 441,669 B | Full headless analyzer log (auto-analysis warnings + script execution trace) |
| `C:\Users\jjswe\Tools\ghidra-projects-loader-re\script_run.log` | 4,554 B | Script-rerun log |
| `C:\Users\jjswe\Tools\ghidra-projects-loader-re\brute_scan_gf_run.log` | small | Brute-scan run log |
| `C:\Users\jjswe\Tools\ghidra-projects-loader-re\datalayer_run.log` | 2,222,472 B | DataLayer + (attempted) DatabaseBrowser auto-analysis log |
| `C:\Users\jjswe\Tools\ghidra-projects-loader-re\dbbrowser_run2.log` | small | DatabaseBrowser bounded re-run log (180 s auto-analysis cap) |

Evidence reviewed but not modified (entry-gate verification, restated kernel-side knowledge, cross-checks of setter signatures and SQL surfaces): the 8 mandatory-read-set documents named in the parent handoff §Mandatory Read Set; the prior pass's evidence and completion handoff; the existing TccBase Ghidra project's `field_writers.log`, `vtable_dispatcher.log`, `brute_scan.log`, `force_disasm.log`, `byte_pattern.log`, `sst_callers*.log`; ILSpy decompile drops at `temp/ilspy-easypower/TccBase/-Module-.cs` (lines 18930–19024 for setter signatures, lines 7642–7666 / 7659–7666 / 7715 / 7736 for prior kernel-side findings) and `temp/ilspy-easypower/EasyPower.DeviceLibrary/EasyPower.DeviceLibrary/DeviceLibrary.cs` (line 1281 for the description-only `ReadGroundDelay` SQL).

Additional follow-up review for further investigation: `temp/ilspy-dvleng/DvlEng.decompiled.cs` around the SST loader blocks and the generic inverse-delay loader `dvlSSTGetInvEqDelays(...)`, specifically the sec2/LTD `sdvlSSTSec2Curve` branch and the two later inverse-delay call sites using `nSection = 3` and `nSection = 5`.

Additional naming bridge reviewed in the managed layer: `temp/ilspy-easypower/EasyPower.DeviceLibrary/EasyPower.DeviceLibrary/SSTSensorRecord.cs`, `temp/ilspy-easypower/EasyPower.DeviceLibrary/EasyPower.DeviceLibrary/DeviceLibrary.cs`, and `temp/ilspy-easypower-types/EasyPower.Types.decompiled.cs` for `StpuDelayCalc`, `GroundDelayCalc`, `ReadStpuDelay`, `ReadGroundDelay`, and the `SSTDelayCalc` enum values.

### 3. Exact loader-recovery result

**Loader is binary-confirmed absent from all four local candidate binaries. NOT RECOVERED.** Detail:

1. **TccBase.dll** — no instruction in the executable code references any of the 16 GF setter addresses (8 native impls at `1001bc24`, `1001bc7c`, `1001bcd4`, `1001bd2c`, `1001bd84`, `1001bde4`, `1001be44`, `1001bea4` + 8 managed-export wrappers at `1001bc68`, `1001bcc0`, `1001bd18`, `1001bd70`, `1001bdd2`, `1001be32`, `1001be92`, `1001bef2`); the only references are the 8 PE export-table `ImageBaseOffset32` entries themselves. Zero instructions load from the 8 GF vtable slot addresses (`100cdfa4..100cdfb0`, `100ce0d4..100ce0e0`); the GF curve type's vtable is dead within the DLL — used only by external callers. Zero ASCII or UTF-16LE byte-pattern hits for `DatSection1GfInvEq`, `DatSection3InvEq`, `FdOpICalc`, `IdOpICalc`, `FdOpEq`, `IdOpEq`. PE imports show no database client library.
2. **EasyPower.DeviceLibrary.dll** — zero symbols matching any of the 8 GF setter names (exact or partial), zero byte-pattern hits for any GF math-row column name in any encoding, only `MSCOREE.DLL _CorDllMain` as native PE import. Its only `DatSection1GfInvEq` reference is the description-only SQL string already enumerated by TASK-019B §3.1.
3. **EasyPower.DataLayer.dll** (operator-surfaced mid-execution) — zero symbols matching any of the 8 GF setter names across 11,050 identified functions; zero ASCII or UTF-16LE byte-pattern hits for any GF math-row column name; no PE import from `TccBase.dll` or any database driver library. Its 38 keyword-matched function hits are oneline-diagram property accessors (`COnelineRecordBase`, `CdbOliRecGEN`, `CdbOliRecMOT`) and CLI marshalling templates — a different domain from trip-curve loading.
4. **EasyPower.DatabaseBrowser.dll** (operator-surfaced mid-execution) — zero symbols matching any of the 8 GF setter names across 3,191 identified functions; zero ASCII or UTF-16LE byte-pattern hits for any GF math-row column name; only `MSCOREE.DLL _CorDllMain` as native PE import. Its 12 keyword-matched function hits are UI/database-browser property accessors and ANSI/IEEE C57.109 / C57.12.59 column-value getters. Auto-analysis was bounded at 180 s after an unbounded run accumulated 70+ minutes in the decompiler analyzer; the early analyzers (PE loader, disassembly, function manager, symbol analyzer, string analyzer) completed within the cap and the results above do not depend on the decompiler analyzer.
5. **DvlEng.dll cross-check (follow-up review)** — the DVL-layer SST loader uses `sdvlSSTSec2Curve` as a dedicated sec2/LTD model, but uses the generic `dvlDatInveqDelay` container for two later inverse-delay paths by calling `dvlSSTGetInvEqDelays(..., 3, ...)` and `dvlSSTGetInvEqDelays(..., 5, ...)`. This supports a section-parameterized inverse-delay abstraction shared across the STD and GF later-section branches at the DVL layer. It narrows the likely native-loader shape, but it still yields zero GF setter call sites and zero `*ICalc`-to-`byICalc` translation evidence.
6. **Managed naming bridge for the DvlEng switches (follow-up review)** — `EasyPower.DeviceLibrary.SSTSensorRecord` exposes `StpuDelayCalc` and `GroundDelayCalc`, both typed as `SSTDelayCalc`; `EasyPower.Types.SSTDelayCalc` confirms `INVEQ = 2` and `TUSTD = 3`; and `ReadStpuDelay` / `ReadGroundDelay` show the exact table mapping (`DatSection3InvEq` vs `DatSection3STD`, and `DatSection1GfInvEq` vs `DatSection1GfGFD`). This lets us reinterpret the DvlEng switches correctly: the switch value is delay-calc mode, not section identity. Section identity is the separate `3` or `5` argument passed into `dvlSSTGetInvEqDelays`. This materially sharpens the DVL interpretation, but still does not surface any GF setter call site or any `*ICalc`-to-`byICalc` translation.
5. The brute scan of TccBase.dll covered 13,044 disassembled instructions plus 13,186 defined data items — the full auto-analyzer-disassembled subset. The prior packet's `force_disasm.log` (271,000+ force-disasm starts on `.text`) reported zero SST-setter hits even after aggressive disassembly, indicating that further force-disasm on TccBase.dll is unlikely to surface a GF caller absent from the auto-analyzed surface.

### 4. Exact profile-by-profile binding result

**NOT BOUND × 3.** No profile from TASK-B §3.9 is bound to a specific setter call.

| Profile (`InOut`, `*ICalc`, `*Eq`) | n | Style attribution | Binding |
|---|---|---|---|
| `(0, (8,8,4,4), (0,0,0,0))` | 1,690 | unattributed | NOT BOUND (kernel-side recovered per TASK-019B §6.1; loader-side absent from both local binaries) |
| `(1, (4,4,8,8), (0,0,1,1))` | 100 | Federal Pioneer LSIG / LSIG (2) / LVPCB | NOT BOUND (kernel-side recovered per TASK-019B §6.2; "*Eq selects setter family" hypothesis recorded but explicitly NOT adopted) |
| `(2, (8,8,1,1), (0,0,0,0))` | 6,760 | most Square D Micrologic 6.x and MTZ frames | NOT BOUND (kernel-side recovered per TASK-019B §6.3; loader-side absent from both local binaries) |

### 5. Exact `*ICalc` translation result

**UNRESOLVED.** Same posture as TASK-019B §7. Kernel-internal `byICalc ∈ {0, 1, 2}` enum is fully closed against accepted binary-backed evidence (`{0 → ((double*)P_0)[16], 1 → ((double*)P_0)[13], 2 → ((double*)P_0)[12]}`, with any other value yielding zero curve points). Database `*ICalc ∈ {1, 4, 8, 10}` to kernel `byICalc` translation is unrecoverable without the loader; no caller of the setters is present in either local binary.

### 6. Exact blocker-status ruling

**NOT CLOSED.** The GF-side inverse-equation dispatch blocker named in `EASYPOWER-CALC-ENGINE-SPEC.md` §O is **not** resolved by anything on disk today. Materially narrowed beyond the prior pass: the loader is binary-confirmed absent from **all four local candidate binaries** (TccBase.dll, EasyPower.DeviceLibrary.dll, EasyPower.DataLayer.dll, EasyPower.DatabaseBrowser.dll) via per-binary instruction-operand / vtable-slot / setter-symbol / column-name byte-pattern scans in both ASCII and UTF-16LE encodings, plus PE-imports inventory confirming none of the candidate binaries statically link to TccBase.dll's GF setter exports. The exact remaining gap is the loader code in a binary OTHER THAN those four local binaries, plus any database-to-kernel `*ICalc` translation. Likely-unsearched candidates (none authorized by this packet) are: `EasyPower.exe` native section via Ghidra (the 30 MB exe is on local disk but a Ghidra native-side pass has not been performed); `dbBase.dll` / `UtlBase.dll` or any other proprietary EasyPower loader DLL not currently on local disk; bounded dynamic instrumentation against a live-running `EasyPower.exe`.

### 7. Exact downstream authorization ruling

**Continued block. TASK-E remains BLOCKED.** No TASK-E execution, scoping, or splitting packet is authorized or implied by this ruling. No TASK-F fixture-generation packet is authorized; deferred independently. No spec reopen, master-plan re-sequencing, or policy change is implied. Spec §O retains its current authorization wording; master-plan TASK-019 retains its current wording.

## Hard Limits Respected — 5 of 5

1. **PASS** — No TASK-E implementation in this packet.
2. **PASS** — No GF-side parity claim (blocker explicitly NOT CLOSED).
3. **PASS** — No fixture, test, or runtime code change.
4. **PASS** — No Tier B reopening or Phase 6 widening.
5. **PASS** — No invented semantics for unresolved loader behavior, `*ICalc`, `*Eq`, or `InOut`.

## Merge-Gate Mapping — 4 of 4 PASS

| Gate | Target | Outcome |
|---|---|---|
| Entry-gate loader-recovery posture reconfirmed | PASS | **PASS** |
| Loader path recovery result stated exactly | PASS | **PASS** (NOT RECOVERED, with binary-backed evidence against all four local binaries in evidence §6) |
| GF-side profile-by-profile binding result stated exactly | PASS | **PASS** (NOT BOUND × 3 in evidence §7) |
| One explicit blocker-status and downstream ruling published | PASS | **PASS** (NOT CLOSED in evidence §9; TASK-E BLOCKED in evidence §10; no follow-on packet authorized in evidence §11) |

## Auditor Note

Copilot remains the project manager and auditor for this lane. This pass-2 closure preserves TASK-E's BLOCKED state and does not imply parity, scope split, or reopening of any earlier-closed gate. Per the parent task's Stop-And-Flag rule 2, the "*Eq selects setter family" hypothesis is recorded but explicitly not adopted; per the parent task's Hard Limit 5, no semantics are invented for unresolved loader behavior. The exact remaining gap is preserved verbatim in evidence §11 with three unsearched candidate locations named (none authorized by this packet): EasyPower.exe native-side Ghidra; the additional EasyPower DLLs not currently on local disk; bounded dynamic instrumentation against a live-running EasyPower.exe.
