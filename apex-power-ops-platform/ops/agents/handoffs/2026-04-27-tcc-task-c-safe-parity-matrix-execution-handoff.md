# TCC TASK-C Safe Parity Matrix Execution Handoff

Date: 2026-04-27
Packet: `2026-04-27-tcc-task-c-safe-parity-matrix`
Status: **Completed 2026-04-27**
Authority: `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md` §O
Companion authority: `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-CC-SERIES-B-CALCULATOR-FULL-ROUTING-2026-04-26.findings.md`
Project: EasyPower calc-engine characterization and bounded parity-validation lane

## Execution Result

TASK-C closed PASS on 2026-04-27 against canonical Supabase.

Exact file changed:

1. `source-domains/tcc_v5_backend/tests/test_series_b_safe_parity.py` — new 8-test bounded pytest surface.

Exact assertions covered:

1. SE Series B STD tuple parity row-for-row across 8 rows for sensors `30338` and `30245`.
2. MX STD tuple parity row-for-row across 16 rows for sensors `1863`, `1864`, `26973`, and `1865`.
3. PX-6B per-band mixed STD parity for sensor `1701`, including asymmetric ordinal 0.
4. Full SE GFD literal `2000A` anchor across the 8 GFD rows of `30338` and `30245`.
5. STPU dispatch truth: all 7 Series B sensors carry `DS3_PICKUP_CALC = 1`.
6. GFPU dispatch split truth: SE=`7`, MX / PX-6B=`0`.
7. Section-absent handling for the LI-only style cohort with zero STD-band rows.
8. Override-branch routing through `tcc_etu_stpu_overrides` for sensors `16671`, `16672`, and `16673` at the spec §K constants.

Validation command and result:

1. `./.venv/Scripts/pytest.exe tests/test_series_b_safe_parity.py -v`
2. Result: `8 passed in 3.33s` against canonical Supabase (`db.fxoyniqnrlkxfligbxmg.supabase.co`).

Execution note:

1. The initial LI-only section-absent matcher overreached by pattern-matching `%MCCB-LI%` and catching `MCCB-LIG`, which legitimately carries STD bands outside the §L LI-only cohort. The test was tightened to exact style equality against `MCCB-LI`, `MICROLOGIC 3.0`, `MICROLOGIC 3.0A`, and `MICROLOGIC 3.0P`. This was a test-surface correction, not a contract weakening.

Downstream disposition:

1. The spec §O safe TASK-C surface is now closed.
2. No spec reopen is authorized from this packet.
3. §N.1, §N.2, §N.3, §N.4, and §N.5 remain open questions outside this packet.
4. TASK-E remains narrow-scope and blocked until the matching open question closes.
5. TASK-F remains deferred.

## Objective

This handoff delegates the next unblocked validation slice after TASK-H closed the interpretation-doc truth gap on 2026-04-27.

Claude Code should execute only the open-question-independent TASK-C pytest surface already authorized in spec §O:

1. implement or update a bounded pytest matrix for the Series B direct-band parity cases explicitly enumerated in spec §O items 1-8,
2. prove those tests against repo-owned fixtures or repo-owned query surfaces without reopening reverse-engineering,
3. preserve the current engine-contract boundaries around unresolved §N questions,
4. return one bounded statement saying whether the safe parity surface is now covered and what remains intentionally deferred.

This handoff does not authorize broad calc-engine implementation beyond the already-governed direct-band Series B surface, does not authorize inverse-equation parity claims, and does not authorize any implementation that depends on unresolved §N.1, §N.3, or §N.5 semantics.

## Confirmed Entry Gate

The packet is authorized because the prerequisite contract work is already landed:

1. TASK-G PASS — `Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md` is published and active.
2. TASK-H PASS — the STD, GF, and STPU interpretation docs now align to the Series B contract and no longer carry the stale provisional wording that previously blocked truthful parity work.
3. Spec §O explicitly authorizes TASK-C against the open-question-independent Series B validation surface.
4. The remaining blockers are now limited to the open questions already preserved in spec §N; no new doc-truth blocker remains after TASK-H.

If any one of those statements fails when execution begins, stop and return a blocker report instead of writing parity tests from stale or contradictory inputs.

## Mandatory Read Set

Open these files before the first substantive edit:

1. `source-domains/neta-ett-study-material/Development/Architecture/EASYPOWER-CALC-ENGINE-SPEC.md`
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-CC-SERIES-B-CALCULATOR-FULL-ROUTING-2026-04-26.findings.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TASK-D-WORKBOOK-DB-RECONCILIATION-2026-04-26.md`
4. `source-domains/neta-ett-study-material/Development/Architecture/TCC-STD-ELEMENT-INTERPRETATION.md`
5. `source-domains/neta-ett-study-material/Development/Architecture/TCC-GF-ELEMENT-INTERPRETATION.md`
6. `source-domains/neta-ett-study-material/Development/Architecture/TCC-STPU-ELEMENT-INTERPRETATION.md`
7. The current repo-owned pytest surface in `source-domains/tcc_v5_backend` that is nearest to the calc-engine runtime or query path under test

## First-Test Anchors

Start from the spec-authorized assertions and the smallest existing test surface that can host them rather than broad repo exploration.

### Primary parity anchors

1. SE Series B: `SensorID 30338`, `30245`
2. MX: `SensorID 1863`, `1864`, `26973`, `1865`
3. PX-6B: `SensorID 1701`
4. Full SE GFD literal anchor: `DatSection1GfGFD.I_OPEN = 2000`
5. STPU and GFPU dispatch bytes for the 7-sensor set: `DS3_PICKUP_CALC` and `DS1GF_PICKUP_CALC`
6. Section-absent references called out in spec §O item 7
7. Override branch references for `DatSection3STOvr` and `CBreakerOverride`

Local hypothesis for the first slice:

- the safe parity matrix can be expressed entirely from the already-published direct-band Series B contract without touching unresolved inverse-equation, LTD delay-parity, or INST curve-calc semantics.

Cheapest falsifying check:

- identify one existing pytest file or calc-engine test seam that can assert a representative SE/MX/PX-6B direct-band case plus the dispatch-byte checks without requiring any N.1 / N.3 / N.5-dependent behavior.

## Execution Order

### 1. Reconfirm the governing contract

Required outcomes:

1. The test matrix is scoped only to the spec §O TASK-C surface.
2. The Series B direct-band contract remains the authority for these tests.
3. Unresolved §N questions remain explicitly out of scope.

Execution rules:

1. Start from spec §O and the interpretation docs, not from ad hoc assumptions in existing tests.
2. If the runtime or repository test seam cannot express an authorized assertion without crossing into an unresolved §N surface, stop and classify that as the boundary.
3. Do not turn this packet into a broader calc-engine feature-implementation lane.

### 2. Add the safe parity assertions

Required outcomes:

1. SE Series B assertions prove `(I_OPEN, I_CLEAR, I2X) = (10, 10, 2)` row-for-row across the 8 STD rows.
2. MX assertions prove `(6, 6, 1)` across the 16 STD rows.
3. PX-6B assertions prove per-band mixed `[(4,10,2), (10,10,2), (6,6,2), (6,6,2)]` and preserve the asymmetric ordinal-0 behavior.
4. Full SE GFD assertions prove the literal-amps `2000` anchor across the 4 GFD ordinals.
5. Dispatch assertions prove all 7 Series B calculator-target sensors carry `DS3_PICKUP_CALC = 1` while GFPU still splits SE=`7` and MX/PX-6B=`0`.
6. Section-absent handling and override-branch handling are covered only to the extent already authorized in spec §O items 7 and 8.

Execution rules:

1. Prefer the smallest repo-owned fixture or query seam that can falsify the current contract.
2. Preserve exact sensor IDs and exact per-band tuples; do not collapse family-level assertions into lossy aggregates.
3. Keep the tests explicit about STD versus GF versus pickup-dispatch surfaces.

### 3. Validate the bounded pytest surface

Required outcomes:

1. The narrowest relevant pytest slice is run after the first substantive test edit.
2. Failures are resolved only if they belong to the bounded TASK-C surface.
3. The packet closes with a clear statement of what remains deferred.

Execution rules:

1. Run the smallest executable validation that covers the touched tests.
2. If a failing test exposes a contradiction with spec §O or the interpretation docs, stop and flag it instead of silently weakening assertions.
3. Do not widen into all-up test repair unrelated to this parity matrix.

## Hard Limits

1. Do not implement or claim parity for inverse-equation paths that depend on unresolved GF-side `*ICalc` interpretation.
2. Do not implement or claim parity for LTD behavior that depends on unresolved `DS2_DLY_PTY` semantics.
3. Do not implement or claim parity for INST timing surfaces that depend on unresolved `Sec4Inst*` semantics.
4. Do not treat `DS3_PICKUP_CALC = 0` and `= 4` as the same branch.
5. Do not treat workbook labels or formulas as runtime authority.
6. Do not reopen TASK-E, TASK-F, or TASK-G from this packet.

## Stop-And-Flag Conditions

Stop and return control to Copilot if any of the following becomes true:

1. The safe parity matrix cannot be expressed without crossing into spec §N.1, §N.3, or §N.5 behavior.
2. The available repo-owned test seam cannot represent the authorized assertions without requiring new broad runtime implementation.
3. A parity-test failure appears to contradict the published Series B contract rather than a local implementation defect.
4. The packet widens into inverse-equation characterization, fixture-generation infrastructure, or broad test-suite repair.

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. Exact files changed.
2. Exact pytest files or test cases added or updated.
3. Exact assertions covered for SE, MX, PX-6B, GFD, STPU dispatch, GFPU dispatch, section-absent handling, and override routing.
4. Exact validation command run and result.
5. One explicit downstream statement saying whether the safe TASK-C parity surface is now closed and what remains deferred to TASK-E / TASK-F or the spec §N open questions.

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| TASK-C entry gate still holds | PASS | PASS |
| SE Series B STD tuple parity covered row-for-row | PASS | PASS |
| MX STD tuple parity covered row-for-row | PASS | PASS |
| PX-6B mixed per-band parity preserved explicitly | PASS | PASS |
| Full SE GFD `2000` literal anchor covered | PASS | PASS |
| STPU and GFPU dispatch split covered truthfully | PASS | PASS |
| Section-absent and override cases handled only within spec-authorized bounds | PASS | PASS |
| No unresolved §N behavior was smuggled into the packet | PASS | PASS |

## Auditor Note

Copilot remains the project manager and auditor for this lane. Claude Code is executing a bounded parity-validation slice against an already-published engine contract, not using tests to redefine unresolved runtime semantics. If the safe TASK-C surface cannot be closed without reopening spec §N questions, preserve that boundary explicitly and hand it back rather than broadening the packet.