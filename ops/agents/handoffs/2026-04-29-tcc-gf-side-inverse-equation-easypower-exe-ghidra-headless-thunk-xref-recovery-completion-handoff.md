# TCC GF-Side Inverse-Equation EasyPower.exe Ghidra-Headless Thunk/Xref Recovery — Completion Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-gf-side-inverse-equation-easypower-exe-ghidra-headless-thunk-xref-recovery`
Status: **Closed PASS — 2026-04-29.** §O **BLOCKER CLOSED.** Direct profile-to-setter binding recovered. Per-call-site populator, slot-to-setter binding matrix, `*ICalc → byICalc` translation, and Therm-vs-Ansi selector are all RECOVERED with direct native disassembly evidence. Profile-by-profile binding **BOUND × 3**. TASK-E remains gated only by spec §O's surrounding contractual wording (separate scoping question).

Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md`
Authority anchor: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-POPULATOR-CONSUMER-RECOVERY-2026-04-29.md`
Evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md`
Parent handoff (closed): `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-easypower-exe-ghidra-headless-thunk-xref-recovery-handoff.md`
Prior completion handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-populator-consumer-recovery-completion-handoff.md`

---

## Required Deliverables

### 1. Exact Ghidra-headless command / script surface used

```
analyzeHeadless.bat C:/Users/jjswe/Tools/ghidra-projects-loader-re TccGfPopulator_20260429
  -import C:/Users/jjswe/Tools/ghidra-projects-loader-re/isolated-easypower/EasyPower.exe
  -scriptPath C:/Users/jjswe/Tools/ghidra-scripts
  -postScript ResolveGfImportThunksAndXrefs.java
  -overwrite
```

Followed by:
```
analyzeHeadless.bat C:/Users/jjswe/Tools/ghidra-projects-loader-re TccGfPopulator_20260429
  -process EasyPower.exe -noanalysis
  -scriptPath C:/Users/jjswe/Tools/ghidra-scripts
  -postScript DumpGfPopulatorAndTranslator.java
```

Custom scripts authored under this packet:
- `C:\Users\jjswe\Tools\ghidra-scripts\ResolveGfImportThunksAndXrefs.java` (target resolution + xref enumeration + immediate-operand context dump)
- `C:\Users\jjswe\Tools\ghidra-scripts\DumpGfPopulatorAndTranslator.java` (full-disassembly dump of recovered targets)

Reference scripts (modeled after, not used directly):
- `C:\Users\jjswe\Tools\ghidra-scripts\BruteScanGfCallers.java`
- `C:\Users\jjswe\Tools\ghidra-scripts\FindGfLoaderEvidence.java`

Workaround: first import attempt failed with `IllegalDataException: 0xe is not a legal XML character` during PE library auto-resolution. Worked around by copying `EasyPower.exe` to a directory containing only that file, removing adjacent-DLL discovery. Result is unaffected because the recovery target is entirely inside `EasyPower.exe`'s own native section.

Ghidra project saved at: `C:\Users\jjswe\Tools\ghidra-projects-loader-re\TccGfPopulator_20260429:/EasyPower.exe`. Total Ghidra analysis time: 2074 seconds. Total functions discovered: 48,868.

### 2. Exact thunk list analyzed

| # | Symbol | Library | Ord | External addr | IAT pointer |
|---|--------|---------|-----|---------------|-------------|
| 1 | `dvlSSTGetInvEqDelays` | DVLENG.DLL | 0x322 | EXTERNAL:000027a1 | `PTR_dvlSSTGetInvEqDelays_012dd808` |
| 2 | `CSSTSensor::GetInvEqDelays` | DVLENG.DLL | 0x194 | EXTERNAL:00002710 | `PTR_GetInvEqDelays_012dd5c4` |
| 3 | `SetAnsi_FlatDelayClear` | TCCBASE.DLL | 0x13F | EXTERNAL:000008de | `PTR_SetAnsi_FlatDelayClear_012df60c` |
| 4 | `SetAnsi_FlatDelayOpen` | TCCBASE.DLL | 0x140 | EXTERNAL:000008df | `PTR_SetAnsi_FlatDelayOpen_012df610` |
| 5 | `SetAnsi_InverseDelayClear` | TCCBASE.DLL | 0x141 | EXTERNAL:000008dc | `PTR_SetAnsi_InverseDelayClear_012df604` |
| 6 | `SetAnsi_InverseDelayOpen` | TCCBASE.DLL | 0x142 | EXTERNAL:000008dd | `PTR_SetAnsi_InverseDelayOpen_012df608` |
| 7 | `SetTherm_FlatDelayClear` | TCCBASE.DLL | 0x18B | EXTERNAL:00000910 | `PTR_SetTherm_FlatDelayClear_012df6d4` |
| 8 | `SetTherm_FlatDelayOpen` | TCCBASE.DLL | 0x18C | EXTERNAL:00000911 | `PTR_SetTherm_FlatDelayOpen_012df6d8` |
| 9 | `SetTherm_InverseDelayClear` | TCCBASE.DLL | 0x18D | EXTERNAL:0000090e | `PTR_SetTherm_InverseDelayClear_012df6cc` |
| 10 | `SetTherm_InverseDelayOpen` | TCCBASE.DLL | 0x18E | EXTERNAL:0000090f | `PTR_SetTherm_InverseDelayOpen_012df6d0` |

All 10 resolved cleanly with stable xref counts.

### 3. Exact caller-chain summary from row-reader thunk(s) to setter thunk(s)

**Direct caller intersection at function-entry-point granularity: 0** (the populator does not directly call the row-reader thunk; it goes through a wrapper).

**Transitive caller chain — RECOVERED**:

```
FUN_01207bf0 @ 01207bf0   (1464B native body — the GF populator)
   │
   │  CALL 0x011e2710 at 01207ca2
   ▼
FUN_011e2710 @ 011e2710   (37B wrapper — pushes nSection=5 literal)
   │
   │  CALL [PTR_GetInvEqDelays_012dd5c4] at 011e271f
   ▼
DvlEng.dll!CSSTSensor::GetInvEqDelays(this, 5, &delays)
   │
   │  (DvlEng-internal — pass-3 confirmed at DvlEng.cs:105690+)
   ▼
DvlEng.dll!dvlSSTGetInvEqDelays(deviceLibrary, ?, 5, &delays)
   │
   │  fills TdbPtrArray<dvlDatInveqDelay> with GF (nSection=5) inverse rows
   ▼
returns to FUN_01207bf0, which iterates the row array and dispatches to all 8 setters
```

Setter call sites inside `FUN_01207bf0`:
- `01207dbb` → `[PTR_SetTherm_InverseDelayOpen_012df6d0]`
- `01207e2e` → `[PTR_SetTherm_InverseDelayClear_012df6cc]`
- `01207eda` → `[PTR_SetAnsi_InverseDelayOpen_012df608]`
- `01207f5e` → `[PTR_SetAnsi_InverseDelayClear_012df604]`
- `01207ffa` → `[PTR_SetTherm_FlatDelayOpen_012df6d8]`
- `0120805b` → `[PTR_SetTherm_FlatDelayClear_012df6d4]`
- `012080ef` → `[PTR_SetAnsi_FlatDelayOpen_012df610]`
- `0120815e` → `[PTR_SetAnsi_FlatDelayClear_012df60c]`

A second setter caller `FUN_011cff40 @ 011cff40` (904B) calls only the four Therm setters; its Ansi paths are STUBBED (write rTmin to consumer offsets and return without setter dispatch). It is a Therm-only refresh / single-row path, not the canonical populator. It is recorded for completeness but not load-bearing for §O closure.

The two unwrapped `dvlSSTGetInvEqDelays` callers (`FUN_01049990`, `FUN_01055680`) are description-list UI paths (`CDvlDatSection3::ResetPage` lambdas; one calls `PUSH 0x3` STPU, the other `PUSH 0x5` GF) for combo-box population, not kernel populators.

### 4. Exact `*ICalc` translation evidence recovered

**RECOVERED.** `FUN_01208640 @ 01208640` (32 bytes total) is a deterministic pure function called from every setter call site in `FUN_01207bf0` (8 sites) and `FUN_011cff40` (4 Therm sites). Full body:

```
01208640: PUSH EBP
01208641: MOV  EBP, ESP
01208643: MOVZX EAX, byte ptr [EBP + 0x8]    ; arg = sub-block's *ICalc
01208647: SUB  EAX, 0x0
0120864a: JZ   0x0120865c                     ; in==0 → return 2
0120864c: SUB  EAX, 0x1
0120864f: JZ   0x01208658                     ; in==1 → return 1
01208651: SUB  EAX, 0x7                       ; (dead arithmetic)
01208654: XOR  AL, AL                         ; else → return 0
01208656: POP  EBP
01208657: RET
01208658: MOV  AL, 0x1
0120865a: POP  EBP
0120865b: RET
0120865c: MOV  AL, 0x2
0120865e: POP  EBP
0120865f: RET
```

Translation: `byICalc = (in == 0) ? 2 : (in == 1) ? 1 : 0`.

On the spec's `*ICalc ∈ {1, 4, 8, 10}` set:
- `1` → `byICalc=1`
- `4` → `byICalc=0`
- `8` → `byICalc=0`
- `10` → `byICalc=0`

The spec's "5 dispatch profiles" reduces in native code to two distinct GF kernel byICalc outputs (1 and 0) for inputs in `{1,4,8,10}`. The third byICalc value (2) is reachable only when a sub-block stores `*ICalc=0` — whether that occurs in the actual database is a separate database-fact question outside this packet's scope.

### 5. Slot-to-setter binding matrix

**RECOVERED. BOUND × 3 (all three TASK-B §3.9 dispatch profiles bound).**

| Sub-block | Row offset | *Eq byte | *ICalc byte | Therm setter (when *Eq=0) | Ansi setter (when *Eq≠0) |
|-----------|------------|----------|-------------|----------------------------|----------------------------|
| FdOp | 0x08–0x3B | row 0x08 | row 0x09 | `SetTherm_FlatDelayOpen` (TccBase ord 0x18C) | `SetAnsi_FlatDelayOpen` (TccBase ord 0x140) |
| FdCl | 0x3C–0x6F | row 0x3C | row 0x3D | `SetTherm_FlatDelayClear` (TccBase ord 0x18B) | `SetAnsi_FlatDelayClear` (TccBase ord 0x13F) |
| IdOp | 0x70–0xA3 | row 0x70 | row 0x71 | `SetTherm_InverseDelayOpen` (TccBase ord 0x18E) | `SetAnsi_InverseDelayOpen` (TccBase ord 0x142) |
| IdCl | 0xA4–0xD7 | row 0xA4 | row 0xA5 | `SetTherm_InverseDelayClear` (TccBase ord 0x18D) | `SetAnsi_InverseDelayClear` (TccBase ord 0x141) |

Each setter receives `byICalc = FUN_01208640(sub-block.*ICalc)`. Therm vs Ansi selection for the entire row uses **only IdOp's `*Eq` byte at row offset 0x70** (not per-sub-block). Sub-block internal layout:
- byte 0: `*Eq` (0=Therm, !=0=Ansi)
- byte 1: `*ICalc` (input to translator)
- bytes 4–23: 5 Therm floats (rTmin, rX, rTref, rIref, rM)
- bytes 24–47: 6 Ansi floats (rTmin at byte 24; rA, rB, rC, rD, rE at bytes 28–47)

Direct binding evidence: the same basic block in `FUN_01207bf0` issues the `MOVSS [ESI+offset]` reads from the matching sub-block bytes immediately followed by the matching `CALL [import]` (no intervening branches). Hard Limit 3 ("do not treat structural agreement as binding") is honored — the binding is from in-function direct reads + call, not from name correspondence.

### 6. Exact blocker-posture ruling

**§O BLOCKER: NOT CLOSED → CLOSED.**

The blocker named at `EASYPOWER-CALC-ENGINE-SPEC.md` line 766 is closed by direct native evidence on the following five independently sufficient grounds:

1. The per-call-site GF populator is recovered (`FUN_01207bf0`).
2. The transitive row-reader chain is recovered (`FUN_01207bf0` → `FUN_011e2710` → DvlEng `CSSTSensor::GetInvEqDelays(this, 5, &delays)` → `dvlSSTGetInvEqDelays`).
3. The sub-block-to-setter binding is recovered for all 4 sub-blocks × Therm/Ansi (Item 5 above).
4. The `*ICalc → byICalc` translation function is recovered (Item 4 above).
5. The Therm-vs-Ansi selector is recovered (IdOp `*Eq` byte at row offset 0x70).

TASK-E remains gated only by spec §O's surrounding contractual wording ("Authorized in narrow scope only after the matching open question closes"), which no longer reflects the §O blocker state. A separately authored TASK-E scoping packet may now reference the §12 binding matrix and §8 translation function in the evidence document as direct contract anchors. This packet does not author or pre-authorize that scoping.

---

## Hard Limits Respected — 5 of 5

1. **HONORED** — §O closure backed by direct profile-to-setter binding (Items 4 + 5 above).
2. **HONORED** — no widening into TASK-E implementation, fixtures, runtime code, or schema work.
3. **HONORED** — binding evidence is `MOVSS [ESI+constant-offset]` followed by `CALL [import]` in the same basic block; not import-presence or structural-correspondence promotion.
4. **HONORED** — master-plan edit is justified because posture truly changes (NOT CLOSED → CLOSED). A new DEC entry is added; prior DEC entries are preserved as audit trail.
5. **HONORED** — only static Ghidra-headless analysis was used; no dynamic instrumentation; no debugger.

## Stop-And-Flag Compliance — All Five Triggers Negative

1. Headless thunk resolution failed reproducibly: **NEGATIVE** — all 10 thunks resolved.
2. Xref set too broad: **NEGATIVE** — 5–10 refs per thunk; 2 distinct setter callers.
3. Only debugger-backed move possible: **NEGATIVE** — static analysis closed it.
4. Caller chain narrowed only by speculative struct reinterpretation: **NEGATIVE** — direct in-function reads + matching calls.
5. Posture appears to change but no direct binding recovered: **NEGATIVE** — direct binding **is** recovered.

---

## Authority Surfaces Updated

1. Evidence document: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md` — created.
2. Completion handoff: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-easypower-exe-ghidra-headless-thunk-xref-recovery-completion-handoff.md` — this file.
3. Parent handoff Status banner: `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-easypower-exe-ghidra-headless-thunk-xref-recovery-handoff.md` — updated to "Closed PASS — 2026-04-29; §O BLOCKER CLOSED".
4. Authority task doc: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md` — Status banner updated; Completion Record populated.
5. Master plan `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md` — new DEC entry added recording §O closure (smallest necessary authority-surface update).
6. Project memory `C:\Users\jjswe\.claude\projects\C--Users-jjswe\memory\project_tcc_gf_loader_recovery_pass2.md` — extended with pass-5 record + §O closure.

Authority surfaces explicitly **NOT** updated by this packet:
- Spec text at `EASYPOWER-CALC-ENGINE-SPEC.md` line 766 — left unchanged per spec's own "Reopening this spec" rules. A separately authored spec-rewrite packet (TASK-G-equivalent) is the appropriate forum.
- Per-element docs / runtime / schema / fixtures / tests / pytest — Hard Limit 2.

---

## Next Honest Move

The single next move authorized by this packet is the master-plan DEC entry recording §O closure (already performed as part of authority-surface updates above).

A separately authored TASK-E scoping packet may now reference the §12 binding matrix and §8 translation function in the evidence document as direct contract anchors. This packet does not author or pre-authorize that scoping.

A separately authored spec-rewrite packet (TASK-G-equivalent) may update spec line 766 wording to reflect the closure. That is also outside this packet's scope.
