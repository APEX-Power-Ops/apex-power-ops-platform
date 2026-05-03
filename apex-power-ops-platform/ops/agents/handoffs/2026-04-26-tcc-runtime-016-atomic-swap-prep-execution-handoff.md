# TCC Runtime 016 Atomic-Swap Prep Execution Handoff

Date: 2026-04-26
Packet: `2026-04-26-tcc-runtime-016`
Status: **Ready for Claude Code execution**
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE3-ATOMIC-SWAP-PREP-2026-04-26.md`
Project: rebuilt TCC runtime lane against Supabase `fxoyniqnrlkxfligbxmg`

## Objective

This handoff delegates the next authorized macro-phase after runtime-contract trio part 1 closed cleanly on 2026-04-26.

Claude Code should execute only the post-part-1 atomic-swap-prep lane:

1. TASK-012 part 2: close SQL RPC parity for the STPU override branch.
2. TASK-013 part 2: replace remaining `6258` rebuilt-state caveat bridges with truthful rebuilt-state split-anchor fixtures and golden values.
3. Execute the ETU atomic swap only if those two part-2 slices prove the rebuilt `*_v2` surface is the more truthful canonical runtime.
4. Run focused post-swap regression and update the authority surfaces that define the frozen baseline.

This handoff does not authorize Phase 4 execution or Phase 5 normalization.

## Sequencing Clarification

Runtime 016 no longer uses the original Step 1 -> Step 2 -> Step 3 order.

Policy clarification on 2026-04-26 established that a truthful live SQL proof for TASK-012 part 2 cannot close pre-swap because `vw_sensor_calc_context` is still bound to the pre-rebuild sensor universe while `tcc_etu_stpu_overrides_v2` is keyed to rebuilt sensor IDs.

Authorized order from this handoff forward:

1. TASK-013 part 2 first,
2. then atomic swap or the smallest truthful swap-equivalent runtime rebind,
3. then TASK-012 part 2 on the post-swap canonical runtime,
4. then focused post-swap regression and authority-doc reconciliation.

Do not implement TASK-012 part 2 against the pre-rebuild EAV override shape and do not use synthetic fixtures to fake rebuilt-state proof.

## Substitute Clarification

Runtime 016 also no longer uses `11442` as the presumed `6258` replacement.

Approved substitute policy:

1. `test_calc_engine.py` remains historical executable lineage rather than the active pytest proof lane; bounded split-anchor maintenance is acceptable if it stays explicitly historical and skip-guarded pre-swap.
2. Sensor **4604** is the approved rebuilt-state anchor for pickup/cascade proof surfaces.
3. Sensor **4174** is the approved rebuilt-state anchor for IEEE-depth proof surfaces.
4. Sensor **11442** is rejected as the general substitute.

Do not force a one-sensor drop-in replacement where the rebuilt corpus does not actually provide one.

## MAINT Clarification

Runtime 016 Step 3 also no longer treats `tcc_etu_sensor_maint_v2` as a pure rename candidate.

Approved MAINT swap policy:

1. Preserve `tcc_etu_sensor_maint_v2` as the raw source-faithful MAINT authority surface.
2. Materialize the existing canonical MAINT runtime contract from that raw v2 source data before or during the swap.
3. Keep `vw_sensor_calc_context`, the MAINT SQL functions, and Python MAINT consumers stable across the cutover.
4. Do not use a view-only remap or a full raw-column consumer refactor in this packet.

The blocker that triggered this clarification was direct: the active runtime depends on canonical `maint_*` columns plus `params_json`, and those fields do not exist on the raw source-faithful `tcc_etu_sensor_maint_v2` surface.

## Confirmed Entry Gate

The upstream packet and current runtime handoff already record the required entry conditions:

1. TASK-011 PASS.
2. TASK-012 part 1 PASS.
3. TASK-013 part 1 PASS.
4. Combined regression PASS across `test_neta_plot_tcc.py`, `test_sensor_context_route.py`, `test_etu_delay_routing.py`, and `test_stpu_override_enforcement.py`.
5. Atomic swap still explicitly blocked pending TASK-012 part 2 and TASK-013 part 2.

If any of those statements no longer holds when execution begins, stop and return a blocker report instead of editing code.

## Mandatory Read Set

Open these files before the first edit:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE3-ATOMIC-SWAP-PREP-2026-04-26.md`
2. `apex-power-ops-platform/ops/agents/handoffs/2026-04-26-tcc-runtime-015-runtime-contract-trio-kickoff-handoff.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE3-TASK-012-STPU-OVERRIDE-EVIDENCE-2026-04-26.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE3-TASK-013-LINKED-ETU-SELECTION-EVIDENCE-2026-04-26.md`
5. `source-domains/tcc_v5_backend/plan/architecture-tcc-access-workflow-fidelity-1.md`
6. `source-domains/tcc_v5_backend/migrations/phase3_supabase_rebuild/README.md`
7. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE3-RUNTIME-016-MAINT-SWAP-DECISION-2026-04-26.md`

## First-Code Anchors

Start from these local surfaces rather than re-exploring the repo broadly.

### TASK-012 part 2 anchors

1. `source-domains/tcc_v5_backend/migrations/maint/fn_calculate_test_currents.sql`
2. `source-domains/tcc_v5_backend/services/neta/router.py`
3. `source-domains/tcc_v5_backend/tests/test_stpu_override_enforcement.py`
4. `source-domains/tcc_v5_backend/tests/test_sql_rpc_pickup_methods_live.py`
5. `source-domains/tcc_v5_backend/migrations/phase3_supabase_rebuild/phase3_load.py`
6. `source-domains/tcc_v5_backend/migrations/phase3_supabase_rebuild/phase3_load_postgrest.py`
7. `source-domains/tcc_v5_backend/migrations/phase3_supabase_rebuild/20260425_001_phase3_v2_schema.sql`

Local hypothesis for the first slice:

- The Python contract already honors the STPU override branch, but `fn_calculate_test_currents` still computes `stpu_test_i` directly through `fn_calc_etu_pickup_current(...)` and never consults the override source.

Cheapest falsifying check:

- Add or adapt a focused SQL RPC regression that exercises a known rebuilt-v2 override sensor and proves whether SQL returns the override amps/tolerances/times instead of the calculated STPU branch.

### TASK-013 part 2 anchors

1. `source-domains/tcc_v5_backend/test_calc_engine.py`
2. `source-domains/tcc_v5_backend/services/calc_engine/CALC_ENGINE_SPEC.md`
3. `source-domains/tcc_v5_backend/services/calc_engine/etu_pickup.py`
4. `source-domains/tcc_v5_backend/services/calc_engine/etu_curves.py`
5. `source-domains/tcc_v5_backend/tests/test_sql_rpc_pickup_methods_live.py`
6. `source-domains/tcc_v5_backend/migrations/phase3_supabase_rebuild/README.md`

Local hypothesis for the fixture slice:

- Rebuilt-state proof is still blocked by `6258`-anchored tests, examples, and assertions that survived as caveat-banner bridges after part 1. Those surfaces must be re-keyed to source-backed rebuilt-state fixtures under the approved split-anchor policy.

Cheapest falsifying check:

- Confirm the selected rebuilt-state substitute exists in the rebuilt runtime surface, is source-backed from `D:\TCC_NEW.accdb`, and can support the specific golden assertions being moved off `6258`.

### Atomic-swap anchors

1. `source-domains/tcc_v5_backend/migrations/phase3_supabase_rebuild/README.md`
2. `source-domains/tcc_v5_backend/migrations/phase3_supabase_rebuild/20260425_002_phase3_v2_source_faithful.sql`
3. `source-domains/tcc_v5_backend/migrations/maint/vw_sensor_calc_context.sql`
4. `source-domains/tcc_v5_backend/migrations/maint/fn_calculate_test_currents.sql`
5. Any SQL or runtime surface that still points readers or callers at pre-swap canonical ETU tables instead of the validated rebuilt source-faithful layer.

Do not start the swap until both part-2 slices above are validated.

## Execution Order

### 1. TASK-013 part 2: rebuilt-state fixture re-keying

Required outcomes:

1. Canonical rebuilt-state proof no longer depends on `6258` caveat banners where the surface is meant to prove active runtime truth.
2. New fixture values are recomputed from the rebuilt source-faithful surface, not copied from pre-rebuild examples.
3. The linked-selection contract from part 1 remains intact unless rebuilt-state proof forces a narrower repair.

Execution rules:

1. Re-key the smallest proof-bearing surfaces first.
2. Separate historical illustration from active rebuilt-state proof explicitly if any `6258` example must remain for lineage.
3. Do not claim rebuilt-state parity from any fixture unless its values are re-derived against the rebuilt corpus.
4. Use the approved split-anchor policy: `4604` for pickup/cascade proof, `4174` for IEEE-depth proof, and historical-lineage treatment for `test_calc_engine.py`.

Required validation after each re-keying slice:

1. Narrow tests for the touched calc-engine or SQL surface.
2. Documentation consistency check for any changed golden values.

### 2. Atomic swap

Required outcomes:

1. Canonical MAINT runtime contracts survive the swap through a compatibility-materialized bridge sourced from raw v2 MAINT data.
1. Canonical ETU runtime names point at the rebuilt source-faithful surface.
2. The swap is documented as truthful, not merely completed.
3. The rebuilt sensor universe becomes addressable through the live runtime path for downstream TASK-012 closure.

Execution rules:

1. Perform the swap only after TASK-013 part 2 passes.
2. Do not pure-rename `tcc_etu_sensor_maint_v2`; preserve the canonical MAINT contract first.
3. If the swap would make canonical names less truthful than the current `*_v2` layer, stop and report no-go.
4. Keep Phase 4 blocked until post-swap validation is explicit.

### 3. TASK-012 part 2: SQL RPC parity

Required outcomes:

1. `fn_calculate_test_currents` honors the same STPU override contract already pinned in Python.
2. The implementation reads the truthful override shape for the post-swap canonical runtime baseline.
3. Loader and SQL surfaces are aligned so the same override contract survives after swap.

Execution rules:

1. Prefer the smallest edit that proves or falsifies the current SQL gap before widening into loader changes.
2. Keep the Python contract authoritative; do not change Python behavior to match SQL.
3. If the SQL function changes, keep the repo-owned canonical function file and the live database change path aligned truthfully.

Required validation after the first substantive edit:

1. Focused override-scoped SQL regression.
2. `tests/test_stpu_override_enforcement.py`
3. Any narrow route or SQL test touched by the change.

### 4. Post-swap regression and doc reconciliation

Minimum required checks before closing the packet:

1. Re-run the combined runtime-contract regression surface.
2. Re-run the focused SQL RPC override proof.
3. Re-run any rebuilt-state fixture tests changed in TASK-013 part 2.
4. Update the task packet, evidence docs, and handoff surfaces to match the actual final state.

## Hard Limits

1. `D:\TCC_NEW.accdb` remains the sole behavioral authority.
2. Do not reopen TASK-011 part 1 behavior except where the swap mechanically changes the source surface beneath it.
3. Do not pull Phase 4 validation into this packet.
4. Do not start Phase 5 renames or normalization, including the delayed storage rename to `*_delay_calc_code`.
5. Do not leave `6258`-keyed statements phrased as rebuilt-state proof.

## Stop-And-Flag Conditions

Stop and return control to Copilot if any of the following becomes true:

1. SQL RPC parity requires behavior that contradicts the already-proven Python override contract.
2. Rebuilt-state fixture replacement cannot be justified from Access authority plus rebuilt corpus evidence.
3. The atomic swap would make canonical names less truthful than the current `*_v2` runtime layer.
4. The required change widens into Phase 4 acceptance or Phase 5 normalization.
5. The live database state and repo SQL surface diverge in a way that cannot be reconciled within this packet.

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. Exact files changed.
2. Exact TASK-012 part 2 behavior closed.
3. Exact TASK-013 part 2 fixture surfaces re-keyed.
4. Whether atomic swap completed.
5. Exact validations run and their outcomes.
6. Whether Phase 4 is now authorized or still blocked, with one exact reason.

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| TASK-012 part 2 SQL RPC override parity | PASS | **PASS 2026-04-26** — `fn_calculate_test_currents` honors override branch on canonical flat surface; SQL=Python parity validated end-to-end via new `test_sql_rpc_matches_python_for_stpu_override_sensor_16671` |
| TASK-013 part 2 rebuilt-state fixture re-keying | PASS | **PASS 2026-04-26** (accepted prior) — split-anchor 4604/4174 fixtures fire end-to-end post-swap; 4604 cascade test flipped SKIPPED→PASSED |
| Atomic swap | PASS or explicit truthful NO-GO | **PASS 2026-04-26** — Maint-A bridge + 20 table renames + view rebinds executed atomically; canonical surface holds source-faithful corpus |
| Post-swap combined regression | PASS | **PASS** — 67 passed, 2 skipped, 0 failed across the 5-file regression surface (up 2 passes from pre-swap 66/2 baseline) |
| Authority docs reconciled | PASS | **PASS** — TASK-012 part 2 evidence doc published; this handoff updated; packet completion record closed; architecture plan TASK-012 row updated |
| Phase 4 entry decision | Explicit GO or NO-GO | **GO** — explicitly authorized; all 5 packet acceptance criteria satisfied |

## Auditor Note

Copilot remains the project manager and auditor for this lane. Claude Code is executing within a bounded slice, not redefining acceptance criteria. If execution uncovers a truth conflict, Claude should stop at the boundary, preserve evidence, and hand the decision back instead of smoothing the discrepancy over in code or docs.