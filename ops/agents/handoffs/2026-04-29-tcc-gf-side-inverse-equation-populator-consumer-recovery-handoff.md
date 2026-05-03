# TCC GF-Side Inverse-Equation Populator / Consumer Recovery Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-gf-side-inverse-equation-populator-consumer-recovery`
Status: **Closed PASS — 2026-04-29.** Executed by Claude Code; consumer binary recovered (`EasyPower.exe`) by direct PE import-table evidence; per-call-site recovery still pending; blocker posture NOT CHANGED (still NOT CLOSED, materially narrowed further). Evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-POPULATOR-CONSUMER-RECOVERY-2026-04-29.md`. Completion handoff: `ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-populator-consumer-recovery-completion-handoff.md`.

Original status (preserved): Ready for execution — bounded native-side recovery only; blocker posture unchanged unless direct slot-to-setter binding evidence is recovered
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-POPULATOR-CONSUMER-RECOVERY-2026-04-29.md`
Authority anchor: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-HYPOTHESIS-VALIDATION-2026-04-29.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Active engine contract: `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
Prior completion handoff: `ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-hypothesis-validation-completion-handoff.md`

## Objective

This handoff delegates the next bounded recovery lane after pass-3 closed PASS.
The row-reader is no longer the unknown. The managed layer is no longer the
unknown. The exact remaining gap is now:

1. the native populator / consumer that receives populated GF-side
   `dvlDatInveqDelay` rows,
2. the translation from database `*ICalc ∈ {1, 4, 8, 10}` to kernel
   `byICalc ∈ {0, 1, 2}`,
3. the direct slot-to-setter binding between the four row sub-blocks and the
   eight `Set{Therm,Ansi}_{Flat,Inverse}Delay{Open,Clear}` setter surfaces.

This handoff does **not** authorize TASK-E implementation, parity claims,
master-plan edits, or broad binary hunting beyond the bounded populator path.

## Entry Gate

Execute this handoff only if all of the following remain true:

1. Pass-3 evidence still records the row-reader as recovered in
   `dvlSSTGetInvEqDelays` and the populator / consumer as still missing.
2. Profile-by-profile binding remains **NOT BOUND × 3**.
3. TASK-E remains BLOCKED.
4. No newer accepted evidence on disk already binds the four row sub-blocks to
   the eight setters strongly enough to make this handoff redundant.

If any one of those statements fails, stop and return a contradiction note
instead of extending the recovery lane.

## Mandatory Read Set

Open these files before the first substantive action:

1. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-HYPOTHESIS-VALIDATION-2026-04-29.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-hypothesis-validation-completion-handoff.md`
3. `source-domains/neta-ett-study-material/Development/temp/ilspy-dvleng/DvlEng.decompiled.cs`
4. `source-domains/neta-ett-study-material/Development/temp/ilspy-easypower/TccBase/-Module-.cs`
5. `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
6. `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`

## First Anchors

Start from these anchors, in order:

1. `DvlEng.cs:105690+` — `dvlSSTGetInvEqDelays` as the recovered row-reader.
2. `DvlEng.cs` GF call site for `dvlSSTGetInvEqDelays(..., 5, ...)`.
3. `TccBase/-Module-.cs` — the eight GF setter bodies as the known sink.
4. The installed `EasyPower.exe` native image as the highest-probability
   consumer location unless a stronger already-on-disk DLL candidate appears.

Cheapest discriminating checks:

1. import / xref / symbol search for the eight setter surfaces in local native
   binaries,
2. native search for `dvlDatInveqDelay` consumers or row-iteration shapes,
3. native search for branches or lookup tables over `1, 4, 8, 10` nearest the
   setter path,
4. only if those fail, stop and flag the need for a new packet authorizing
   debugger-backed runtime instrumentation.

## Expected Deliverables

Return one bounded completion note or evidence update that includes:

1. exact binaries searched,
2. exact consumer evidence recovered,
3. exact `*ICalc` translation evidence recovered or an exact unresolved ruling,
4. one slot-to-setter binding matrix if direct binding is found,
5. one exact blocker-posture ruling.

If blocker posture does **not** change, say so explicitly.

## Hard Limits

1. Do not claim the §O blocker is closed unless direct slot-to-setter binding
   evidence is actually recovered.
2. Do not widen into TASK-E implementation, fixtures, or runtime code changes.
3. Do not treat structural agreement as binding.
4. Do not edit the master plan unless blocker posture truly changes.
5. Do not improvise debugger or live-instrumentation work under this handoff;
   stop and flag it instead if static work exhausts.

## Expected Result Shape

The best honest outcomes are:

1. `consumer recovered` — the missing native populator path is located,
2. `translation recovered` — the `*ICalc` mapping is directly evidenced,
3. `binding recovered` — one or more row sub-blocks are directly tied to one or
   more setter surfaces,
4. `still blocked` — the search materially narrows but does not close the
   binding gap.

If the consumer remains absent after bounded static work, the blocker still
remains **NOT CLOSED** and the next honest move becomes a separately authored
instrumentation or missing-binary packet.