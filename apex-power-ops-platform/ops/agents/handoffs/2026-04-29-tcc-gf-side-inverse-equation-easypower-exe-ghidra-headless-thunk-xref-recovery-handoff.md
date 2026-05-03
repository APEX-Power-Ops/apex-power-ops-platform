# TCC GF-Side Inverse-Equation EasyPower.exe Ghidra Headless Thunk/Xref Recovery Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-gf-side-inverse-equation-easypower-exe-ghidra-headless-thunk-xref-recovery`
Status: **Closed PASS — 2026-04-29.** §O **BLOCKER CLOSED.** Direct profile-to-setter binding recovered: per-call-site populator `FUN_01207bf0` recovered; sub-block-to-setter binding matrix recovered (4 sub-blocks × Therm/Ansi → 8 setters); `*ICalc → byICalc` translation recovered (`FUN_01208640`: `(in==0)?2:(in==1)?1:0`); Therm/Ansi selector recovered (IdOp `*Eq` byte). Profile-by-profile binding **BOUND × 3**. Evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md`. Completion handoff: `ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-easypower-exe-ghidra-headless-thunk-xref-recovery-completion-handoff.md`.

Original status (preserved): Ready for execution — bounded Ghidra-headless static-native recovery only; blocker posture unchanged unless direct profile-to-setter binding evidence is recovered
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-EASYPOWER-EXE-GHIDRA-HEADLESS-THUNK-XREF-RECOVERY-2026-04-29.md`
Authority anchor: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-POPULATOR-CONSUMER-RECOVERY-2026-04-29.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Active engine contract: `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
Prior completion handoff: `ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-populator-consumer-recovery-completion-handoff.md`

## Objective

This handoff delegates the next bounded native recovery lane after pass-4
closed PASS. The consumer binary is no longer unknown. The remaining gap is now
entirely inside `EasyPower.exe`'s native x86 section:

1. the per-call-site populator that calls the DvlEng row-reader path,
2. the dispatch path from populated rows to the eight GF setter thunks,
3. the database `*ICalc ∈ {1, 4, 8, 10}` to kernel `byICalc ∈ {0, 1, 2}`
   translation,
4. any direct profile-to-setter binding evidence that would materially change
   blocker posture.

This handoff does **not** authorize TASK-E implementation, parity claims,
dynamic instrumentation, or master-plan edits.

## Entry Gate

Execute this handoff only if all of the following remain true:

1. Pass-4 evidence still records `EasyPower.exe` as the unique on-disk binary
   importing both the row-reader path and all eight GF setters.
2. Per-call-site recovery still remains pending.
3. Profile-by-profile binding remains **NOT BOUND × 3**.
4. Database `*ICalc` to kernel `byICalc` translation remains **UNRESOLVED**.
5. TASK-E remains BLOCKED.

If any one of those statements fails, stop and return a contradiction note
instead of extending the recovery lane.

## Mandatory Read Set

Open these files before the first substantive action:

1. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-POPULATOR-CONSUMER-RECOVERY-2026-04-29.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-populator-consumer-recovery-completion-handoff.md`
3. `source-domains/neta-ett-study-material/Development/temp/ilspy-dvleng/DvlEng.decompiled.cs`
4. `source-domains/neta-ett-study-material/Development/temp/ilspy-easypower/TccBase/-Module-.cs`
5. `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
6. `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
7. `C:\Users\jjswe\Tools\ghidra-scripts\BruteScanGfCallers.java`
8. `C:\Users\jjswe\Tools\ghidra-scripts\FindGfLoaderEvidence.java`

## First Anchors

Start from these anchors, in order:

1. `D:\EasyPower\EasyPower.exe` import-thunks for DvlEng.dll ordinals 322 and
   194.
2. `D:\EasyPower\EasyPower.exe` import-thunks for TccBase.dll ordinals 13F,
   140, 141, 142, 18B, 18C, 18D, 18E.
3. The existing script models at `C:\Users\jjswe\Tools\ghidra-scripts\`.

Cheapest discriminating checks:

1. resolve xrefs to the two row-reader thunks,
2. resolve xrefs to the eight setter thunks,
3. intersect or correlate caller clusters,
4. inspect only the strongest clustered callers for row iteration, slot
   dispatch, and `*ICalc` translation,
5. if static recovery stalls, stop and flag the need for a separately authored
   debugger-backed packet.

## Expected Deliverables

Return one bounded completion note or evidence update that includes:

1. exact Ghidra-headless command / script surface used,
2. exact thunk list analyzed,
3. exact caller-chain evidence recovered,
4. exact `*ICalc` translation evidence recovered or an exact unresolved ruling,
5. one binding matrix if direct binding is found,
6. one exact blocker-posture ruling.

If blocker posture does **not** change, say so explicitly.

## Hard Limits

1. Do not claim the §O blocker is closed unless direct profile-to-setter
   binding evidence is actually recovered.
2. Do not widen into TASK-E implementation, fixtures, runtime code changes, or
   schema work.
3. Do not treat import presence or structural agreement as binding.
4. Do not edit the master plan unless blocker posture truly changes.
5. Do not improvise dynamic instrumentation under this handoff; stop and flag
   it instead if static Ghidra work exhausts.

## Expected Result Shape

The best honest outcomes are:

1. `caller chain recovered` — one or more EasyPower.exe native callers are tied
   to both thunk families,
2. `translation recovered` — the `*ICalc` mapping is directly evidenced,
3. `binding recovered` — one or more row sub-blocks are directly tied to one or
   more setter paths,
4. `still blocked` — the search materially narrows but does not close the
   binding gap.

If the caller chain remains unrecovered after bounded static work, the blocker
still remains **NOT CLOSED** and the next honest move becomes a separately
authored debugger-backed or alternate-static packet.