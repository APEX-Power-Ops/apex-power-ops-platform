# TCC Phase 5 Tier B Slice 1 `vw_etu_calc_context` Execution Handoff

Date: 2026-04-27
Packet: `2026-04-27-tcc-phase-5-tier-b-vw-etu-calc-context`
Status: **Completed 2026-04-27. PASS — Tier B Slice 2 may open cleanly when separately authorized.**
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-TIERB-VW-ETU-CALC-CONTEXT-2026-04-27.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Project: rebuilt TCC runtime lane against Supabase `fxoyniqnrlkxfligbxmg`

## Execution Result

Tier B Slice 1 closed PASS on 2026-04-27.

Exact files changed:

1. `source-domains/tcc_v5_backend/migrations/maint/vw_etu_calc_context.sql`
2. `source-domains/tcc_v5_backend/tests/test_vw_etu_calc_context.py`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5-TIER-B-SLICE1-EVIDENCE-2026-04-27.md`
4. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-TIERB-VW-ETU-CALC-CONTEXT-2026-04-27.md`

Exact live DB additions:

1. Supabase migration `phase5_tier_b_slice1_create_vw_etu_calc_context` applied to project `fxoyniqnrlkxfligbxmg`.
2. `CREATE OR REPLACE VIEW vw_etu_calc_context`.
3. `COMMENT ON VIEW vw_etu_calc_context`.
4. No schema mutations.
5. No edits to `vw_sensor_calc_context`, `fn_calculate_test_currents`, or `fn_evaluate_test_results`.

Exact lineage proofs returned PASS:

1. row-count parity: `vw_etu_calc_context = 17,831 = tcc_etu_sensors = vw_sensor_calc_context` and `count(*) = count(distinct sensor_id)`.
2. aggregate parity: `SUM(ltd_params_count) = 3,919`, sensors with curves `= 1,127`, `MAX(ltd_params_count) = 8`.
3. element-wise spot check on sensor 23767: `view EXCEPT base = 0` and `base EXCEPT view = 0` across all 14 non-timestamp columns; jsonb ordinal sequence matches base `ORDER BY ordinal`.
4. column shape: legacy 101 columns preserved at the same ordinal positions; additions are exactly `ltd_params_count` and `ltd_params` at positions 102 and 103.
5. empty aggregate behavior: sensors without curves expose `ltd_params_count = 0` and `ltd_params = '[]'::jsonb`.

Exact simplification proof:

1. probe sensor 23767 (warm): legacy 2-call assembly `0.336 ms + 0.124 ms = 0.460 ms` across 2 round trips.
2. Tier B Slice 1 single-call `1.365 ms` across 1 round trip.
3. Equivalent buffer footprint; one fewer round trip per context-plus-curves call.

Exact validations run:

1. `pytest tests/test_vw_etu_calc_context.py -v` → `5 passed in 2.08s`.
2. Adjacent regression: `pytest tests/test_sensor_context_route.py tests/test_series_b_safe_parity.py -v` → `12 passed`.
3. Pre-existing `tests/test_settings_route.py` REST-fallback failures (5) recorded as out-of-scope and unrelated.

Adoption disposition:

1. `vw_sensor_calc_context` remains the runtime contract surface.
2. `vw_etu_calc_context` is published side-by-side as a derived read-model.
3. Adoption is intentionally deferred to a separately governed slice.

Downstream disposition:

1. Tier B Slice 1 is closed.
2. Tier B Slice 2 (`vw_etu_browse`) may open cleanly when a separate execution packet is authorized.
3. Tier B Slice 3 remains gated on a measured browse-latency target.
4. Tier C and the No-Go list remain out of scope.

## Objective

This handoff delegates the first approved Tier B implementation slice: author
and validate `vw_etu_calc_context` as a bounded derived ETU read-model.

Claude Code should execute only this slice:

1. define `vw_etu_calc_context` on the live canonical ETU surface,
2. land the matching repo SQL mirror or maintenance asset,
3. make the smallest necessary runtime, schema, or test changes needed to prove
   the view is truthful and useful,
4. return explicit lineage proof and explicit simplification evidence,
5. state whether Tier B slice 2 remains gated cleanly or whether this slice
   found a blocker.

This handoff does **not** authorize `vw_etu_browse`, materialized facets, Tier
C normalization probes, or Phase 6 work.

## Confirmed Entry Gate

The packet is authorized because the required upstream state is already
recorded on disk:

1. Phase 4 acceptance remains closed and preserves the frozen validated ETU
   baseline.
2. Phase 5 Tier A remains closed with rename evidence.
3. The Tier A review/alignment audit is closed PASS and states that Tier B may
   open cleanly.
4. TASK-C is closed PASS for the spec section O safe direct-band surface.
5. The master register marks Tier B slice 1 `vw_etu_calc_context` as the next
   operational implementation move.

If any one of those statements fails when execution begins, stop and return a
blocker report instead of widening or redrafting the Tier B lane.

## Mandatory Read Set

Open these files before the first substantive action:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-TIERB-VW-ETU-CALC-CONTEXT-2026-04-27.md`
2. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-POST-VALIDATION-NORMALIZATION-AND-OPTIMIZATION-2026-04-26.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE4-ACCEPTANCE-EVIDENCE-2026-04-26.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5-TIER-A-CANONICAL-RENAME-EVIDENCE-2026-04-26.md`
5. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5A-CANDIDATE-REGISTER-AND-NO-GO-LIST-2026-04-26.md`
6. `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
7. `source-domains/tcc_v5_backend/migrations/maint/vw_sensor_calc_context.sql`
8. `source-domains/tcc_v5_backend/migrations/maint/fn_calculate_test_currents.sql`
9. `source-domains/tcc_v5_backend/services/neta/router.py`
10. `source-domains/tcc_v5_backend/services/neta/schemas.py`
11. `source-domains/tcc_v5_backend/tests/test_sensor_context_route.py`
12. `apex-power-ops-platform/ops/agents/handoffs/2026-04-27-tcc-phase-5-tier-a-review-and-alignment-audit-handoff.md`

## First-Code And First-Validation Anchors

Start from the existing sensor-context SQL surface and the nearest runtime
consumer instead of mapping the whole repo.

### SQL anchors

1. `source-domains/tcc_v5_backend/migrations/maint/vw_sensor_calc_context.sql`
2. the live `public.vw_sensor_calc_context` surface
3. the new `public.vw_etu_calc_context` implementation surface

Local hypothesis for the first slice:

- the new Tier B view can stay bounded if it is derived from the accepted ETU
  context graph rather than introducing a broader browse or normalization
  structure.

Cheapest falsifying check:

- sketch the intended `vw_etu_calc_context` shape directly against
  `vw_sensor_calc_context` and the minimum extra ETU context fields needed for
  one-row sensor context; if that shape fans out or needs speculative joins,
  stop before coding deeper.

### Runtime anchors

1. `source-domains/tcc_v5_backend/services/neta/router.py`
2. `source-domains/tcc_v5_backend/services/neta/schemas.py`
3. `source-domains/tcc_v5_backend/tests/test_sensor_context_route.py`

Local hypothesis for the runtime slice:

- if the new view is truthful, the smallest adoption surface is the sensor
  context route or an adjacent proof path, not a broad route-family rewrite.

Cheapest falsifying check:

- after the first substantive SQL change, run the narrowest sensor-context
  validation slice before touching any wider runtime surface.

## Execution Order

### 1. Reconfirm the boundary

Required outcomes:

1. The entry gate still holds.
2. `vw_etu_calc_context` remains the only authorized Tier B slice in this
   packet.
3. No later doc has widened Tier B into `vw_etu_browse`, facet work, or Phase 6.

### 2. Implement the bounded view slice

Required outcomes:

1. `vw_etu_calc_context` is defined as a derived ETU read-model.
2. The repo mirror or maintenance SQL artifact matches the intended live shape.
3. The implementation stays one-row-per-sensor and lineage-safe.

Execution rules:

1. Prefer the smallest honest SQL package.
2. Do not silently repurpose `vw_sensor_calc_context` into the new view.
3. Keep any compatibility or side-by-side surface explicit.

### 3. Validate behavior and value

Required outcomes:

1. The touched route, schema, or test slice still passes focused validation.
2. One explicit note states the simplification gained by the new view.
3. One explicit note states how the view maps back to the frozen validated ETU
   base.

Execution rules:

1. Run the narrowest executable check first.
2. If the first validation fails, repair the same slice before widening.
3. If value cannot be demonstrated honestly, stop instead of forcing adoption.

### 4. Reconcile authority surfaces

Required outcomes:

1. The new view is described truthfully in the touched docs.
2. Tier B slice 2 remains explicitly gated.
3. The packet ends with an exact next-step statement.

## Hard Limits

1. No `vw_etu_browse` work in this packet.
2. No facet table work in this packet.
3. No physical base-table normalization in this packet.
4. No reopening of Tier A, Phase 4, or calc-engine section N questions unless a
   closed claim is actually falsified.
5. No hidden transforms that weaken deterministic lineage.

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. exact files changed,
2. exact SQL objects created or updated,
3. exact validations run and their outcomes,
4. exact lineage proof for the view shape,
5. exact simplification evidence,
6. exact next-step statement.

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| Phase 4 / Tier A / audit / TASK-C entry gate still holds | PASS | PASS |
| `vw_etu_calc_context` stays bounded to Tier B slice 1 | PASS | PASS |
| One-row-per-sensor lineage-safe view shape is achieved | PASS | PASS |
| Focused runtime or API validation passes | PASS | PASS |
| Simplification value is stated explicitly | PASS | PASS |
| Tier B slice 2 remains gated explicitly | PASS | PASS |

## Auditor Note

Copilot remains the project manager and auditor for this lane. Claude Code is
executing one bounded Tier B read-model slice, not opening the broader Phase 5
or Phase 6 cleanup program. If `vw_etu_calc_context` cannot be proven truthful,
bounded, and useful without widening scope, preserve the contradiction and stop.