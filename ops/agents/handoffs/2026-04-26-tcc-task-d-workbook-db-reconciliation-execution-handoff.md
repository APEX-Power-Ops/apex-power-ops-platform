# TCC TASK-D Workbook vs DB Reconciliation Execution Handoff

Date: 2026-04-26
Packet: `2026-04-26-tcc-task-d-workbook-db-reconciliation`
Status: **Ready for Claude Code execution**
Authority: `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md` §O
Companion authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-CC-SERIES-B-CALCULATOR-FULL-ROUTING-2026-04-26.findings.md`
Project: EasyPower calc-engine characterization and workbook-reconciliation lane

## Objective

This handoff delegates the next bounded validation slice after TASK-G established the active EasyPower calc-engine contract on 2026-04-26.

Claude Code should execute only the workbook-versus-DB reconciliation lane:

1. compare the SQD Series B workbook's per-band values against the DB-authoritative `DatSection3STD` and `DatSection1GfGFD` surfaces for the resolved 7-sensor set,
2. record every match, divergence, and ambiguity explicitly,
3. preserve the contract rule that `Stdlib.mdb` wins whenever workbook content disagrees,
4. return one bounded statement describing whether the workbook is usable as a calibration artifact for this family and what exact fixes or caveats remain.

This handoff does not authorize platform implementation in `tcc_v5_backend`, broad new reverse-engineering, reinterpretation of DB authority to match workbook behavior, or opening TASK-C / TASK-F.

## Confirmed Entry Gate

The packet is authorized because the prerequisite contract work is already landed:

1. TASK-G PASS — `Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md` is published and active.
2. Spec §O explicitly authorizes TASK-D for immediate execution against the Series B 7-sensor set.
3. The findings doc and companion brief are aligned on Full SE identity as `3000A + 4000A`, with workbook `3600A` labeling explicitly treated as workbook-only divergence to be reconciled here.
4. The Series B contract is already bounded to the direct-band DB path (`DatSection3STD` / `DatSection1GfGFD`) and does not depend on unresolved inverse-equation behavior.

If any one of those statements fails when execution begins, stop and return a blocker report instead of reconciling against stale or contradictory inputs.

## Mandatory Read Set

Open these files before the first substantive action:

1. `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-CC-SERIES-B-CALCULATOR-FULL-ROUTING-2026-04-26.findings.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-CC-SERIES-B-CALCULATOR-FULL-ROUTING-2026-04-26.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-B-DVL-DISPATCH-ENUMERATION-2026-04-26.md`
5. `source-domains/neta-ett-study-material/Development/Architecture/TCC-STD-ELEMENT-INTERPRETATION.md`
6. `source-domains/neta-ett-study-material/Development/Architecture/TCC-GF-ELEMENT-INTERPRETATION.md`
7. `Reference_Files/Excel/SQD Microligic Series B Trip Curve Calculator.xlsx`

## First-Check Anchors

Start from the already-resolved 7-sensor set and the exact DB rows that define their contract rather than broad repo exploration.

### Sensor-set anchors

1. Full SE: `SensorID 30338` (3000A), `SensorID 30245` (4000A)
2. MX: `SensorID 1863` (250A), `1864` (400A), `26973` (600A), `1865` (800A)
3. PX-6B: `SensorID 1701` (1600A)

### DB-contract anchors

1. `DatSection3STD` rows for the 7-sensor set
2. `DatSection1GfGFD` rows for the 7-sensor set
3. `DatSection3STP` and `DatSection1GfGFP` pickup menus for the 7-sensor set
4. `DatPlugs` rows for the 7-sensor set
5. `DatStyle` and `DatSensor` identity rows for the 7-sensor set

### Workbook anchors

1. Full SE workbook tabs / inputs that correspond to the DB's 3000A and 4000A sensors
2. MX workbook tabs / inputs for 250A, 400A, 600A, 800A
3. PX-6B workbook tabs / inputs for the 1600A sensor and both plug options if the workbook exposes them

Local hypothesis for the first slice:

- The workbook should largely track DB timing for the resolved Series B set, but any mismatch must be classified as workbook divergence rather than as a reason to weaken the DB-backed spec.

Cheapest falsifying check:

- Compare the workbook's published per-band `T_OPEN` / `T_CLEAR` values for one representative sensor from each family (SE, MX, PX-6B) against the exact `DatSection3STD` rows before broadening into full family coverage.

## Execution Order

### 1. Reconfirm the governing contract

Required outcomes:

1. The 7-sensor set is still the active reconciliation scope.
2. The workbook is still explicitly classified as calibration-only, not runtime authority.
3. The DB-side contract values for STD and GFD are still the ones recorded in TASK-G and the findings doc.

Execution rules:

1. Start from the spec and findings doc, not from the workbook.
2. If the spec and findings doc disagree, stop and flag that contradiction before comparing workbook values.
3. Do not let workbook labels redefine sensor identity or path semantics.

### 2. Extract the workbook-side values

Required outcomes:

1. For each of the 7 sensors, identify the workbook surface being compared.
2. Capture the workbook's per-band `T_OPEN` / `T_CLEAR` values for STD and any directly exposed GFD values.
3. Record any workbook assumptions about frame amps, plug choice, or pickup units that are necessary to make the comparison intelligible.

Execution rules:

1. Preserve exact workbook wording and displayed values.
2. If the workbook does not expose a value the DB does, record that as an absence, not a mismatch.
3. If the workbook exposes a derived value without clear inputs, record the ambiguity explicitly.

### 3. Compare workbook versus DB

Required outcomes:

1. A row-for-row comparison exists for the STD bands of the 7-sensor set.
2. Full SE GFD literal `2000A` behavior is checked wherever the workbook exposes a comparable surface.
3. The workbook's `3600A` SE labeling is reconciled explicitly against the DB's `3000A` / `4000A` identity.
4. Any mismatch is classified as one of: workbook-label issue, workbook-formula issue, workbook-missing-surface issue, or unresolved ambiguity.

Execution rules:

1. Treat `Stdlib.mdb` as correct when values diverge.
2. Do not average, normalize, or reinterpret DB rows to make the workbook look right.
3. Preserve the PX-6B ordinal-0 asymmetry exactly if the workbook smooths it away.

### 4. Close the packet with a bounded disposition

Required outcomes:

1. One statement says whether the workbook is usable as a calibration artifact for Series B.
2. Every workbook defect or caveat is listed explicitly.
3. One statement says what downstream work is now authorized or still blocked.

Execution rules:

1. Keep the conclusion bounded to workbook-versus-DB reconciliation.
2. Do not widen this packet into test authoring, fixture generation, or platform code edits.
3. If the workbook is partially usable, say exactly for which family or surface.

## Hard Limits

1. `D:\EasyPower\11.0\Stdlib.mdb` remains the runtime authority.
2. Do not let workbook labels or formulas override DB identity, dispatch, or timing rows.
3. Do not touch `tcc_v5_backend` code, tests, or schema in this handoff.
4. Do not reopen TASK-G, TASK-B, or the rejected Series B `(10,10,2)` inverse-equation escalation.
5. Do not widen into TASK-H doc reconciliation, TASK-C validation matrix work, or TASK-F fixture generation.

## Stop-And-Flag Conditions

Stop and return control to Copilot if any of the following becomes true:

1. The workbook cannot be mapped to the resolved 7-sensor set without inventing identity correspondence.
2. A required DB-side comparison value cannot be reproduced from the accepted authority docs or direct DB evidence.
3. The only way to produce a “match” is to reinterpret DB semantics to fit workbook assumptions.
4. The workbook exposes additional hidden rules that appear to contradict the current spec rather than merely diverge from it.
5. The task widens into platform implementation, workbook repair, or broad new reverse-engineering.

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. Exact files changed, if any.
2. Exact workbook surfaces inspected.
3. Exact DB surfaces queried or cited.
4. A per-family comparison summary for SE, MX, and PX-6B.
5. Exact workbook-versus-DB mismatches and how each was classified.
6. Explicit resolution of the workbook `3600A` label against the DB's `3000A` / `4000A` identity.
7. One explicit downstream authorization statement: what may proceed next, and what remains blocked.

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| TASK-D entry gate still holds | PASS | Pending |
| 7-sensor reconciliation scope preserved | PASS | Pending |
| Full SE identity resolved as `3000A + 4000A` without workbook override | PASS | Pending |
| STD `T_OPEN` / `T_CLEAR` workbook-versus-DB comparison completed for the 7-sensor set | PASS | Pending |
| Full SE GFD `2000A` anchor checked wherever workbook exposes a comparable surface | PASS | Pending |
| PX-6B ordinal-0 asymmetry preserved explicitly | PASS | Pending |
| Workbook defects / caveats classified explicitly | PASS | Pending |
| Downstream authorization boundary stated explicitly | PASS | Pending |

## Auditor Note

Copilot remains the project manager and auditor for this lane. Claude Code is executing a bounded workbook-reconciliation slice against an already-published engine contract, not redefining the source of truth. If the workbook diverges, preserve the divergence, classify it honestly, and hand it back instead of sanding the DB-backed contract down to match the workbook.
