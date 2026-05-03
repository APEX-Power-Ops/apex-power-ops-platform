# TCC Phase 5 Tier B Slice 2 `vw_etu_browse` Execution Handoff

Date: 2026-04-27
Packet: `2026-04-27-tcc-phase-5-tier-b-vw-etu-browse`
Status: **Completed 2026-04-27. PASS — no further Tier B slice is open; Slice 3 remains gated pending a measured target.**
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-TIERB-VW-ETU-BROWSE-2026-04-27.md`
Program authority: `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
Project: rebuilt TCC runtime lane against Supabase `fxoyniqnrlkxfligbxmg`

## Execution Result

Tier B Slice 2 closed PASS on 2026-04-27.

Exact files changed:

1. `source-domains/tcc_v5_backend/migrations/maint/vw_etu_browse.sql`
2. `source-domains/tcc_v5_backend/tests/test_vw_etu_browse.py`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5-TIER-B-SLICE2-EVIDENCE-2026-04-27.md`
4. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-TIERB-VW-ETU-BROWSE-2026-04-27.md`

Exact live DB additions:

1. Supabase migration `phase5_tier_b_slice2_create_vw_etu_browse` applied to project `fxoyniqnrlkxfligbxmg`.
2. `CREATE OR REPLACE VIEW vw_etu_browse`.
3. `COMMENT ON VIEW vw_etu_browse`.
4. No schema mutations.
5. No edits to `vw_trip_unit_cascade`, `vw_sensor_calc_context`, `vw_etu_calc_context`, `fn_calculate_test_currents`, or `fn_evaluate_test_results`.

Exact lineage proofs returned PASS:

1. row-count parity: `vw_etu_browse = 17,831 = tcc_etu_sensors = vw_trip_unit_cascade` and `count(*) = count(distinct sensor_id)`.
2. routing-flag parity with legacy: `has_ltpu = 17,791`, `has_stpu = 15,259`, `has_inst = 17,178`, `has_gfpu = 11,407`.
3. child-relation flag parity: `has_ltd_curves = 1,127`, `has_std_bands = 10,425`, `has_gfd_bands = 8,615`, `has_inst_curves = 7,903`, `maint_available = 0`.
4. cohort cardinality parity: `63` manufacturers, `2,091` styles, `494` trip-type names.
5. Tier A canonical-field consistency: zero mismatches across all `17,831` rows for `stpu_delay_calc_code` and `ground_delay_calc_code`.

Exact simplification proof:

1. parity-projection `EXPLAIN` probe (`manufacturer_id = 1`, warm): legacy `2.838 ms / 472 hits / 4-way + CTE`; new `2.503 ms / 464 hits / 3-way`.
2. consumer full-row probe (sensor `23767`, warm): legacy `5` round trips / `~0.97 ms`; new `1` round trip / `0.470 ms`.
3. Net browse simplification: `-4` round trips at comparable warm execution.

Exact validations run:

1. `pytest tests/test_vw_etu_browse.py -v` → `5 passed in 2.20s`.
2. Adjacent regression: `pytest tests/test_vw_etu_calc_context.py tests/test_sensor_context_route.py tests/test_series_b_safe_parity.py -v` → `14 passed in 4.95s`.
3. Cascade-route REST-fallback failures (4) recorded as pre-existing environmental config (`NETA_PREFER_DATA_API_READS=true`) and out of scope.

Adoption disposition:

1. `vw_etu_browse` is published side-by-side as a derived read-model.
2. `vw_trip_unit_cascade` remains the runtime contract surface.
3. Adoption is intentionally deferred to a separately governed slice.

Downstream disposition:

1. Tier B Slice 2 is closed.
2. Tier B Slice 3 remains gated on a measured browse-latency or operator-simplicity target.
3. No such target has been recorded, so no further Tier B slice opens from this packet.
4. Tier C and the No-Go list remain out of scope; no calc-engine section N reopen is authorized.

## Objective

This handoff delegates the second approved Tier B implementation slice: author
and validate `vw_etu_browse` as a bounded derived ETU browse and cascade
read-model.

Claude Code should execute only this slice:

1. define `vw_etu_browse` on the live canonical ETU surface,
2. land the matching repo SQL mirror or maintenance asset,
3. make the smallest necessary runtime, schema, or test changes needed to prove
   the view is truthful and useful for the browse or cascade path,
4. return explicit lineage proof and explicit browse-simplification evidence,
5. state whether Tier B Slice 3 remains gated cleanly or whether this slice
   found a blocker.

This handoff does **not** authorize materialized facets, Tier C normalization
probes, or Phase 6 work.

## Confirmed Entry Gate

The packet is authorized because the required upstream state is already
recorded on disk:

1. Phase 4 acceptance remains closed and preserves the frozen validated ETU
   baseline.
2. Phase 5 Tier A remains closed with rename evidence.
3. The Tier A review/alignment audit is closed PASS and states that Tier B may
   open cleanly.
4. TASK-C is closed PASS for the spec section O safe direct-band surface.
5. Tier B Slice 1 `vw_etu_calc_context` is closed PASS.
6. The master register marks Tier B Slice 2 `vw_etu_browse` as the next
   operational implementation move.

If any one of those statements fails when execution begins, stop and return a
blocker report instead of widening or redrafting the Slice 2 lane.

## Mandatory Read Set

Open these files before the first substantive action:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-TIERB-VW-ETU-BROWSE-2026-04-27.md`
2. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-POST-VALIDATION-NORMALIZATION-AND-OPTIMIZATION-2026-04-26.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE4-ACCEPTANCE-EVIDENCE-2026-04-26.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5-TIER-A-CANONICAL-RENAME-EVIDENCE-2026-04-26.md`
5. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5-TIER-B-SLICE1-EVIDENCE-2026-04-27.md`
6. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5A-CANDIDATE-REGISTER-AND-NO-GO-LIST-2026-04-26.md`
7. `source-domains/tcc_v5_backend/plan/architecture-tcc-master-orchestration-1.md`
8. `source-domains/tcc_v5_backend/services/neta/router.py`
9. `source-domains/tcc_v5_backend/services/neta/schemas.py`
10. `apex-power-ops-platform/ops/agents/handoffs/2026-04-27-tcc-phase-5-tier-b-vw-etu-calc-context-execution-handoff.md`

## First-Code And First-Validation Anchors

Start from the existing ETU cascade path and the nearest browse consumer rather
than mapping the whole repo.

### Browse anchors

1. `source-domains/tcc_v5_backend/services/neta/router.py` `/cascade` path
2. the live browse or cascade SQL surface currently backing that route
3. the new `public.vw_etu_browse` implementation surface

Local hypothesis for the first slice:

- the new Tier B view can stay bounded if it is derived from the accepted ETU
  browse graph rather than introducing facets, cached counts, or broader
  normalization.

Cheapest falsifying check:

- sketch the intended `vw_etu_browse` shape directly against the current
  `/cascade` data contract; if the shape requires facet tables, speculative
  denormalization, or unbounded consumer rewrites, stop before coding deeper.

### Runtime anchors

1. `source-domains/tcc_v5_backend/services/neta/router.py`
2. `source-domains/tcc_v5_backend/services/neta/schemas.py`
3. the narrowest cascade or browse test slice available or newly added

Local hypothesis for the runtime slice:

- if the new view is truthful, the smallest adoption surface is the ETU browse
  or cascade route, not a broad route-family rewrite.

Cheapest falsifying check:

- after the first substantive SQL change, run the narrowest browse or cascade
  validation slice before touching any wider runtime surface.

## Execution Order

### 1. Reconfirm the boundary

Required outcomes:

1. The entry gate still holds.
2. `vw_etu_browse` remains the only authorized Slice 2 surface in this packet.
3. No later doc has widened Slice 2 into facets, Tier C, or Phase 6.

### 2. Implement the bounded browse slice

Required outcomes:

1. `vw_etu_browse` is defined as a derived ETU browse read-model.
2. The repo mirror or maintenance SQL artifact matches the intended live shape.
3. The implementation stays lineage-safe and bounded.

Execution rules:

1. Prefer the smallest honest SQL package.
2. Do not silently repurpose a broader browse lane into facet work.
3. Keep any compatibility or side-by-side surface explicit.

### 3. Validate behavior and value

Required outcomes:

1. The touched browse, cascade, schema, or test slice still passes focused validation.
2. One explicit note states the simplification gained by the new view.
3. One explicit note states how the view maps back to the frozen validated ETU base.

Execution rules:

1. Run the narrowest executable check first.
2. If the first validation fails, repair the same slice before widening.
3. If value cannot be demonstrated honestly, stop instead of forcing adoption.

### 4. Reconcile authority surfaces

Required outcomes:

1. The new view is described truthfully in the touched docs.
2. Tier B Slice 3 remains explicitly gated.
3. The packet ends with an exact next-step statement.

## Hard Limits

1. No materialized facet work in this packet.
2. No facet counts or filter caches in this packet.
3. No physical base-table normalization in this packet.
4. No reopening of Tier A, Phase 4, Slice 1, or calc-engine section N questions unless a closed claim is actually falsified.
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
| Phase 4 / Tier A / audit / TASK-C / Slice 1 entry gate still holds | PASS | PASS |
| `vw_etu_browse` stays bounded to Tier B Slice 2 | PASS | PASS |
| Browse view shape is lineage-safe and bounded | PASS | PASS |
| Focused browse or cascade validation passes | PASS | PASS |
| Browse simplification value is stated explicitly | PASS | PASS |
| Tier B Slice 3 remains gated explicitly | PASS | PASS |

## Auditor Note

Copilot remains the project manager and auditor for this lane. Claude Code is
executing one bounded Tier B browse read-model slice, not opening the broader
browse-facet or Phase 6 cleanup program. If `vw_etu_browse` cannot be proven
truthful, bounded, and useful without widening scope, preserve the contradiction
and stop.