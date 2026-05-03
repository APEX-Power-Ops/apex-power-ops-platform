# TCC EasyPower Calc Engine Specification Execution Handoff

Date: 2026-04-26
Packet: `2026-04-26-tcc-task-g-easypower-calc-engine-spec`
Status: **Ready for Claude Code execution**
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-EASYPOWER-CALC-ENGINE-SPEC-2026-04-26.md`
Project: EasyPower calc-engine characterization and specification lane

## Objective

This handoff delegates the next bounded documentation-and-authority slice after TASK-A and TASK-B established the current characterization baseline on 2026-04-26.

Claude Code should execute only the calc-engine specification lane:

1. consolidate the accepted EasyPower dispatch evidence into one coherent engine contract,
2. write the authoritative specification at `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`,
3. preserve a strict distinction between evidence-backed rules and still-open questions,
4. return a bounded statement describing what downstream implementation or validation work is now authorized against that spec.

This handoff does not authorize platform implementation in `tcc_v5_backend`, broad new reverse-engineering, or workbook-driven behavior invention.

## Confirmed Entry Gate

The packet is authorized because the prerequisite characterization work is already landed:

1. TASK-A PASS — the companion brief and findings doc now reflect the DB-anchored Series B truth, including Full SE identity as `3000A + 4000A` and the resolved TASK-D wording.
2. TASK-B PASS after PM cleanup — the dispatch-enum sweep deliverable now records the three-way STD path split, removes the rejected Series B `(10,10,2)` escalation, and preserves the known open questions honestly.
3. Characterize-first policy remains in force — define the engine contract before delegating platform validation or parity implementation work against it.
4. Source authority remains stable — `D:\EasyPower\11.0\Stdlib.mdb` plus accepted reverse-engineering artifacts remain the governing evidence base for this slice.

If any one of those statements fails when execution begins, stop and return a blocker report instead of drafting the spec from stale or contradictory inputs.

## Mandatory Read Set

Open these files before the first substantive edit:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-EASYPOWER-CALC-ENGINE-SPEC-2026-04-26.md`
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-CC-SERIES-B-CALCULATOR-FULL-ROUTING-2026-04-26.findings.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-B-DVL-DISPATCH-ENUMERATION-2026-04-26.md`
4. `source-domains/neta-ett-study-material/Development/Architecture/TCC-LTPU-ELEMENT-INTERPRETATION.md`
5. `source-domains/neta-ett-study-material/Development/Architecture/TCC-STPU-ELEMENT-INTERPRETATION.md`
6. `source-domains/neta-ett-study-material/Development/Architecture/TCC-STD-ELEMENT-INTERPRETATION.md`
7. `source-domains/neta-ett-study-material/Development/Architecture/TCC-GF-ELEMENT-INTERPRETATION.md`
8. `source-domains/neta-ett-study-material/Development/Architecture/TCC-INST-ELEMENT-INTERPRETATION.md`
9. `source-domains/neta-ett-study-material/Development/Architecture/TCC-LTD-ELEMENT-INTERPRETATION.md`
10. Any already-landed reverse-engineering or authority docs directly cited by those files when needed for exact wording.

## First-Doc Anchors

Start from the accepted characterization artifacts and neighboring interpretation docs rather than reopening broad repo exploration.

### Spec-authority anchors

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-EASYPOWER-CALC-ENGINE-SPEC-2026-04-26.md`
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-CC-SERIES-B-CALCULATOR-FULL-ROUTING-2026-04-26.findings.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-B-DVL-DISPATCH-ENUMERATION-2026-04-26.md`

Local hypothesis for the first slice:

- The accepted TASK-A and TASK-B evidence is already sufficient to draft the calc-engine spec truthfully without a new broad reverse-engineering pass, provided each acceptance criterion is mapped to a cited evidence source before prose expands.

Cheapest falsifying check:

- Before drafting deep content, map each TASK-G acceptance criterion to at least one concrete source artifact. If any required statement lacks a cited evidence anchor, stop and classify it as an open question or blocker instead of smoothing over the gap.

### Interpretation anchors

1. `source-domains/neta-ett-study-material/Development/Architecture/TCC-LTPU-ELEMENT-INTERPRETATION.md`
2. `source-domains/neta-ett-study-material/Development/Architecture/TCC-STPU-ELEMENT-INTERPRETATION.md`
3. `source-domains/neta-ett-study-material/Development/Architecture/TCC-STD-ELEMENT-INTERPRETATION.md`
4. `source-domains/neta-ett-study-material/Development/Architecture/TCC-GF-ELEMENT-INTERPRETATION.md`
5. `source-domains/neta-ett-study-material/Development/Architecture/TCC-INST-ELEMENT-INTERPRETATION.md`
6. `source-domains/neta-ett-study-material/Development/Architecture/TCC-LTD-ELEMENT-INTERPRETATION.md`

Local hypothesis for the interpretation slice:

- Most of the missing work is synthesis, not discovery: the family-specific interpretation docs already explain substantial portions of LTD, STPU, STD, GF, and INST behavior, but they are not yet assembled into one engine-level contract with explicit boundaries between proven behavior and deferred RE.

Cheapest falsifying check:

- Compare the interpretation docs against TASK-B's dispatch inventory and verify whether each major section can be written without inventing enum semantics that the evidence does not yet prove.

### Output anchor

1. `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`

The first substantive edit should be the spec skeleton itself once the evidence map is credible.

## Execution Order

### 1. Consolidate the evidence map

Required outcomes:

1. Every acceptance criterion in the TASK-G packet is tied to one or more source artifacts.
2. The spec's authoritative claims are separated from still-open questions before prose hardens.
3. Series B is preserved as a direct `DatSection3STD` family and not re-opened as an inverse-equation ambiguity.

Execution rules:

1. Start from the packet's acceptance criteria rather than from a blank architecture narrative.
2. Preserve the table context of every tuple or enum reference.
3. If evidence conflicts, stop and flag the contradiction rather than reconciling it by assumption.

### 2. Draft the spec skeleton first

Required outcomes:

1. `Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md` exists with its core section structure before deep explanatory prose expands.
2. The skeleton makes room for table contracts, dispatch paths, section absence, family deviations, and unresolved questions.

Execution rules:

1. Keep the first draft structural and evidence-oriented.
2. Do not hide unresolved dispatch families inside generic wording.
3. Use explicit section boundaries for STD direct, STD inverse-equation, GF direct, GF inverse-equation, LTD, STPU, and INST behavior where supported.

### 3. Fill evidence-backed behavior only

Required outcomes:

1. The spec captures the three-way STD path split.
2. The spec states that `*ICalc`, not `*Eq`, is the operative inverse-equation dispatch byte family.
3. The spec records the proven path selector `DS3_SEC3_I2T = 2` for STD inverse-equation families.
4. The spec carries explicit treatment of the known open questions: `DS3_I2T_TYPE = 10`, `I2X = 255`, `DS2_DLY_PTY`, `DS1GF_PICKUP_CALC = 6`, and the `Sec4Inst*` curve-calc family.

Execution rules:

1. Write only to the level justified by `Stdlib.mdb`, landed findings, or accepted reverse-engineering evidence.
2. Mark uncertainty explicitly.
3. Do not convert unresolved dispatch bytes into fake completed semantics.

### 4. Close the packet with downstream guidance

Required outcomes:

1. The spec states what downstream tasks may now validate or implement against it.
2. The spec states which areas remain deferred pending further reverse-engineering.
3. Any minimal wording alignment needed in the companion findings doc is applied truthfully and narrowly.

## Hard Limits

1. `D:\EasyPower\11.0\Stdlib.mdb` remains the primary behavioral authority for this slice.
2. Do not implement runtime or schema changes in `tcc_v5_backend` from this handoff.
3. Do not use workbook formulas or labels as silent runtime authority.
4. Do not reopen the rejected TASK-B Series B reconciliation issue.
5. Do not broaden this packet into TASK-D workbook reconciliation or later implementation work.

## Stop-And-Flag Conditions

Stop and return control to Copilot if any of the following becomes true:

1. A required spec statement cannot be backed by `Stdlib.mdb`, landed findings, or accepted reverse-engineering evidence.
2. The only way to finish a section is to choose among multiple unresolved interpretations without a governing source.
3. The work widens into code implementation, fixture authoring, or parity-test design.
4. Existing authority docs disagree in a way that requires a new governance decision rather than a synthesis pass.
5. The spec would need to blur direct-band tuples and inverse-equation tuples to look coherent.

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. Exact files changed.
2. Whether `Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md` was created and which sections were completed.
3. Which acceptance criteria were satisfied directly by cited evidence.
4. Which open questions remain unresolved and how they were recorded.
5. Any companion-doc wording changes made to preserve terminology alignment.
6. One explicit downstream authorization statement for later validation or implementation work.

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| TASK-G packet entry gate still holds | PASS | Pending |
| `Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md` created | PASS | Pending |
| Spec distinguishes STD direct / STD inverse-equation / no-STD paths | PASS | Pending |
| Spec states `*ICalc` dispatch and `DS3_SEC3_I2T = 2` path selection truthfully | PASS | Pending |
| Series B recorded as direct `DatSection3STD` family with zero `DatSection3InvEq` rows | PASS | Pending |
| Five open questions preserved explicitly rather than invented away | PASS | Pending |
| Downstream validation or implementation boundary stated explicitly | PASS | Pending |

## Auditor Note

Copilot remains the project manager and auditor for this lane. Claude Code is executing a bounded authority-synthesis slice, not redefining the source of truth. If the evidence is insufficient for a required spec statement, preserve the gap, state it plainly, and hand the decision back instead of drafting over it.