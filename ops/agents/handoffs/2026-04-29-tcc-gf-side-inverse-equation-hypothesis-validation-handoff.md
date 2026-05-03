# TCC GF-Side Inverse-Equation Hypothesis Validation Handoff

Date: 2026-04-29
Packet: `2026-04-29-tcc-gf-side-inverse-equation-hypothesis-validation`
Status: **Closed PASS — 2026-04-29.** Executed by Claude Code; all four hypotheses validated; blocker posture NOT CHANGED (still NOT CLOSED, materially narrowed further). Evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-HYPOTHESIS-VALIDATION-2026-04-29.md`. Completion handoff: `ops/agents/handoffs/2026-04-29-tcc-gf-side-inverse-equation-hypothesis-validation-completion-handoff.md`.

Original status (preserved): Ready for execution — bounded validation/disproof handoff only; blocker posture unchanged unless direct contradictory evidence is recovered
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-HYPOTHESIS-VALIDATION-2026-04-29.md`
Authority anchor: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28-PASS2.md`
Primary completion handoff anchor: `apex-power-ops-platform/ops/agents/handoffs/2026-04-28-tcc-gf-side-inverse-equation-loader-recovery-completion-handoff-pass2.md`
Parent packet authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Active engine contract: `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`

## Objective

This handoff delegates a bounded follow-on review whose only purpose is to
validate or disprove the hypotheses recorded during the loader-recovery pass-2
review, without widening into TASK-E implementation, parity claims, or a fresh
blocker-closure claim by narrative drift.

The working hypotheses to test are:

1. `sdvlSSTSec2Curve` is a dedicated section-2/LTD model, while later inverse
   paths reuse the generic `dvlDatInveqDelay` container.
2. The DvlEng switch values `((int*)SSTInfo)[32]` and `((int*)SSTInfo)[101]`
   are `SSTDelayCalc` mode values, not section IDs.
3. `dvlSSTGetInvEqDelays(..., 3, ...)` is the STPU inverse sibling of
   `DatSection3InvEq`, while `dvlSSTGetInvEqDelays(..., 5, ...)` is the later
   GF inverse sibling of `DatSection1GfInvEq` or the equivalent GF inverse row
   family.
4. Managed `EasyPower.DeviceLibrary.ReadStpuDelay` and `ReadGroundDelay` are
   description-only UI readers, not the missing GF math-row loader.
5. If any of the above is false, the contradiction can be stated precisely from
   file-backed evidence already on disk or from a bounded new read-only RE
   slice.

This handoff does **not** authorize TASK-E implementation, blocker closure,
fixture generation, runtime code changes, or master-plan resequencing.

## Entry Gate

Execute this handoff only if all of the following remain true:

1. The pass-2 evidence still records the §O blocker as **NOT CLOSED**.
2. TASK-E remains BLOCKED with no execution, scoping, or splitting packet
   authorized.
3. The pass-2 evidence already records the DVL abstraction and named-field
   hypotheses as hypotheses or narrowing clues rather than as closed facts.
4. No newer accepted evidence on disk already validates or disproves these
   hypotheses strongly enough to make this handoff redundant.

If any one of those statements fails, stop and return a contradiction note
instead of extending the hypothesis record.

## Mandatory Read Set

Open these files before the first substantive action:

1. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CALC-ENGINE-GF-SIDE-INVERSE-EQUATION-LOADER-RECOVERY-2026-04-28-PASS2.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-28-tcc-gf-side-inverse-equation-loader-recovery-completion-handoff-pass2.md`
3. `source-domains/neta-ett-study-material/Development/temp/ilspy-dvleng/DvlEng.decompiled.cs`
4. `source-domains/neta-ett-study-material/Development/temp/ilspy-easypower/EasyPower.DeviceLibrary/EasyPower.DeviceLibrary/DeviceLibrary.cs`
5. `source-domains/neta-ett-study-material/Development/temp/ilspy-easypower/EasyPower.DeviceLibrary/EasyPower.DeviceLibrary/SSTSensorRecord.cs`
6. `source-domains/neta-ett-study-material/Development/temp/ilspy-easypower-types/EasyPower.Types.decompiled.cs`
7. `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
8. `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`

## First Anchors

Start from the four concrete claims already recorded in pass-2 evidence, not
from a new broad repo scan.

### Hypothesis 1 anchor

- `sdvlSSTSec2Curve` appears only in the sec2/LTD loader blocks.
- `dvlDatInveqDelay` appears in the later inverse-delay blocks via
  `dvlSSTGetInvEqDelays`.

Cheapest falsifying check:

- find any sec2/LTD path that uses `dvlDatInveqDelay`, or any later inverse
  branch that directly uses `sdvlSSTSec2Curve` rather than the generic inverse
  container.

### Hypothesis 2 anchor

- `SSTSensorRecord` exposes `StpuDelayCalc` and `GroundDelayCalc` as
  `SSTDelayCalc` fields.
- `SSTDelayCalc` shows `INVEQ = 2` and `TUSTD = 3`.

Cheapest falsifying check:

- find evidence that `((int*)SSTInfo)[32]` or `((int*)SSTInfo)[101]` is loaded
  from a field other than the delay-calc columns, or that the DvlEng switch
  cases do not align with the managed enum values.

### Hypothesis 3 anchor

- DvlEng calls `dvlSSTGetInvEqDelays(..., 3, ...)` in the STPU-side inverse
  branch.
- DvlEng calls `dvlSSTGetInvEqDelays(..., 5, ...)` in the later GF-side
  inverse branch.

Cheapest falsifying check:

- read `dvlSSTGetInvEqDelays` closely enough to determine whether `nSection = 5`
  actually maps to GF inverse rows, or whether it maps to some different later
  section family.

### Hypothesis 4 anchor

- Managed `ReadStpuDelay` and `ReadGroundDelay` currently surface only
  description strings and mode selection.

Cheapest falsifying check:

- find any managed path in `EasyPower.DeviceLibrary`, `EasyPower.DataLayer`, or
  `EasyPower.DatabaseBrowser` that reads GF inverse coefficient columns,
  `*ICalc`, `*Eq`, or calls any GF setter.

## Suggested Execution Order

1. Reconfirm the blocker boundary.
   Required outcome: state explicitly that this handoff is hypothesis-only and
   does not itself reopen TASK-E or close the blocker.
2. Validate or disprove the DvlEng object-model split.
   Required outcome: one explicit statement on whether sec2/LTD is isolated to
   `sdvlSSTSec2Curve` and later inverse branches are isolated to
   `dvlDatInveqDelay`.
3. Validate or disprove the named-field bridge.
   Required outcome: one explicit statement on whether `((int*)SSTInfo)[32]`
   and `((int*)SSTInfo)[101]` are best interpreted as `StpuDelayCalc` and
   `GroundDelayCalc`.
4. Validate or disprove the section-parameter hypothesis.
   Required outcome: one explicit statement on whether `nSection = 3` and
   `nSection = 5` map to the STPU inverse and GF inverse sibling paths.
5. Validate or disprove the managed-layer non-loader hypothesis.
   Required outcome: one explicit statement on whether the managed reads remain
   description-only and non-populating.
6. Publish one compact hypothesis matrix.
   Required outcome: each hypothesis marked `validated`, `disproved`, or
   `still undetermined`, with one evidence line and one consequence line.

## Required Deliverables

Return one completion note or evidence update that includes all of the
following:

1. exact files reviewed,
2. exact new evidence produced, if any,
3. one hypothesis matrix covering all four core hypotheses,
4. one exact statement of any contradiction found,
5. one exact statement of whether blocker posture changes.

If blocker posture does **not** change, say so explicitly.

## Hard Limits

1. Do not claim the §O blocker is closed unless direct loader evidence or a
   direct contradiction to pass-2 evidence is actually recovered.
2. Do not widen into EasyPower.exe native-side RE, debugger instrumentation, or
   missing-binary hunting unless a new separately authored packet explicitly
   authorizes that move.
3. Do not implement TASK-E, generate fixtures, or modify runtime code.
4. Do not convert a structural hypothesis into a semantic conclusion without a
   file-backed bridge.
5. Do not edit the master plan unless blocker posture truly changes.

## Expected Result Shape

The best possible honest outcomes are:

1. `validated` — the current hypothesis survives a targeted falsification pass,
2. `disproved` — a file-backed contradiction shows the current hypothesis is
   wrong,
3. `still undetermined` — the current evidence narrows but does not settle the
   question.

If every hypothesis validates while the direct GF setter caller remains absent,
the blocker still remains **NOT CLOSED**; the result merely sharpens where the
next authorized native-side search should land.

## Auditor Note

Copilot remains the project manager and auditor for this lane. This handoff is
intentionally narrower than the original loader-recovery packet: it exists to
prevent the DVL/managed follow-up reasoning from drifting into assumed fact
without a targeted validation pass. Its success condition is a cleaner,
explicitly falsifiable record of what survived review and what did not, not a
premature blocker-closure claim.