# TCC Phase 5/6 Post-Validation Normalization And Optimization Execution Handoff

Date: 2026-04-26
Packet: `2026-04-26-tcc-phase-5-post-validation-normalization-and-optimization`
Status: **CLOSED 2026-04-26 (Phase 5 Tier A landed).** Tier A storage rename + COMMENT ON COLUMN docs + 5-file post-rename regression 67/2/0 + both anchor proofs (4604 cascade, 16671 override) PASS recorded in `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5-TIER-A-CANONICAL-RENAME-EVIDENCE-2026-04-26.md`. Tier B remains authorized in principle and requires its own execution packet. Post-closure review/alignment audit at `2026-04-27-tcc-phase-5-tier-a-review-and-alignment-audit-handoff.md`.
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-POST-VALIDATION-NORMALIZATION-AND-OPTIMIZATION-2026-04-26.md`
Phase 4 Authorization: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE4-ACCEPTANCE-EVIDENCE-2026-04-26.md` §6.2
Project: rebuilt TCC runtime lane against Supabase `fxoyniqnrlkxfligbxmg`

## Objective

This handoff delegates the first authorized post-validation implementation slice after Phase 4 established the frozen validated baseline on 2026-04-26.

Claude Code should execute only the bounded **Phase 5 Tier A** lane inside the broader Phase 5/6 authorization envelope:

1. rename `tcc_etu_sensors.stpu_i2t` to `stpu_delay_calc_code`,
2. rename `tcc_etu_sensors.gfpu_i2t` to `ground_delay_calc_code`,
3. add `COMMENT ON COLUMN` documentation for the proven delay-calc and pickup-calc enum fields already carried by the authority docs,
4. update the smallest necessary runtime, test, migration, and authority surfaces so the new canonical names are the preferred path forward,
5. return explicit evidence that the Tier A changes preserve deterministic lineage back to the frozen validated base,
6. state whether Tier B may open next or remains blocked.

This handoff does **not** authorize opening Tier B read-models, Tier C normalization probes, or the separately authorized Phase 6 items during the first implementation slice. Those remain downstream boundaries pending Tier A closure.

## Confirmed Entry Gate

The packet is authorized because the required Phase 4 closure conditions are already recorded on disk:

1. Phase 4 acceptance is CLOSED 2026-04-26 and explicitly establishes the frozen validated baseline.
2. Phase 4 evidence §6.2 explicitly authorizes Phase 5 Tier A, Phase 5 Tier B, and Phase 6 categories to begin against that frozen base.
3. The governing Phase 5 packet explicitly narrows the **first implementation slice** to Tier A only unless Phase 4 evidence forces resequencing.
4. The completed Phase 5A audit already published the candidate inventory, naming-and-deprecation draft, ranked candidate register, and no-go list needed to bound execution.
5. The two Tier A rename targets carry independent DLL and architecture-plan evidence and were already semantically pre-authorized by TASK-011.

If any one of those statements fails when execution begins, stop and return a blocker report instead of widening scope or drafting an alternate Phase 5 starting slice.

## Mandatory Read Set

Open these files before the first substantive edit:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-POST-VALIDATION-NORMALIZATION-AND-OPTIMIZATION-2026-04-26.md`
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE4-ACCEPTANCE-EVIDENCE-2026-04-26.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5A-EARLY-NORMALIZATION-AND-OPTIMIZATION-AUDIT-SPIKE-2026-04-26.md`
4. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5A-CANDIDATE-INVENTORY-2026-04-26.md`
5. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5A-CANONICAL-NAMING-DEPRECATION-MAP-DRAFT-2026-04-26.md`
6. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE5A-CANDIDATE-REGISTER-AND-NO-GO-LIST-2026-04-26.md`
7. `source-domains/tcc_v5_backend/plan/architecture-tcc-access-workflow-fidelity-1.md`
8. `source-domains/tcc_v5_backend/DLL_END_TO_END_MAPPING.md`
9. `source-domains/tcc_v5_backend/DLL_SEMANTIC_FINDINGS.md`
10. `source-domains/tcc_v5_backend/ACCESS_TO_SUPABASE_GAP_ANALYSIS.md`
11. `source-domains/tcc_v5_backend/NETA_TCC_OVERLAY_SPEC.md`
12. `source-domains/tcc_v5_backend/IMPLEMENTATION_STATUS.md`
13. `source-domains/tcc_v5_backend/migrations/maint/vw_sensor_calc_context.sql`
14. `source-domains/tcc_v5_backend/migrations/maint/fn_calculate_test_currents.sql`
15. `source-domains/tcc_v5_backend/services/neta/router.py`
16. `source-domains/tcc_v5_backend/services/calc_engine/etu_delay_routing.py`
17. `source-domains/tcc_v5_backend/services/calc_engine/etu_pickup.py`
18. `source-domains/tcc_v5_backend/services/neta/schemas.py`
19. `source-domains/tcc_v5_backend/tests/test_etu_delay_routing.py`
20. `source-domains/tcc_v5_backend/tests/test_sensor_context_route.py`
21. `source-domains/tcc_v5_backend/tests/test_neta_plot_tcc.py`
22. `source-domains/tcc_v5_backend/tests/test_sql_rpc_pickup_methods_live.py`

## First-Code And First-Validation Anchors

Start from the canonical rename targets and the nearest runtime consumers rather than broad repo exploration.

### Schema anchors

1. `source-domains/tcc_v5_backend/models/etu_core.py`
2. `source-domains/tcc_v5_backend/migrations/maint/vw_sensor_calc_context.sql`
3. `source-domains/tcc_v5_backend/migrations/maint/fn_calculate_test_currents.sql`
4. Any migration surface that renames the two canonical columns and applies `COMMENT ON COLUMN` documentation

Local hypothesis for the first slice:

- The two Tier A rename targets are pure semantic corrections with bounded blast radius because runtime surfaces already treat them as delay-routing codes rather than booleans, so the primary risk is consumer drift rather than behavioral change.

Cheapest falsifying check:

- Identify every live consumer of `stpu_i2t` and `gfpu_i2t`, make the smallest rename-compatible change set, then run the focused delay-routing and sensor-context validation slice before widening into additional docs.

### Runtime anchors

1. `source-domains/tcc_v5_backend/services/calc_engine/etu_delay_routing.py`
2. `source-domains/tcc_v5_backend/services/neta/router.py`
3. `source-domains/tcc_v5_backend/services/neta/schemas.py`
4. `source-domains/tcc_v5_backend/tests/test_etu_delay_routing.py`
5. `source-domains/tcc_v5_backend/tests/test_sensor_context_route.py`
6. `source-domains/tcc_v5_backend/tests/test_neta_plot_tcc.py`
7. `source-domains/tcc_v5_backend/tests/test_sql_rpc_pickup_methods_live.py`

Local hypothesis for the runtime slice:

- If the rename is handled truthfully at the schema and ORM edges, the existing delay-routing behavior and the 4604 / 16671 anchors should continue to pass without semantic changes.

Cheapest falsifying check:

- Re-run the narrowest touched tests first (`test_etu_delay_routing.py` and `test_sensor_context_route.py`), then the live anchor tests if the touched slice still holds.

### Authority-doc anchors

1. `source-domains/tcc_v5_backend/DLL_END_TO_END_MAPPING.md`
2. `source-domains/tcc_v5_backend/DLL_SEMANTIC_FINDINGS.md`
3. `source-domains/tcc_v5_backend/ACCESS_TO_SUPABASE_GAP_ANALYSIS.md`
4. `source-domains/tcc_v5_backend/NETA_TCC_OVERLAY_SPEC.md`
5. `source-domains/tcc_v5_backend/IMPLEMENTATION_STATUS.md`
6. `source-domains/tcc_v5_backend/plan/architecture-tcc-access-workflow-fidelity-1.md`
7. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE5-POST-VALIDATION-NORMALIZATION-AND-OPTIMIZATION-2026-04-26.md`

Local hypothesis for the doc slice:

- The smallest truthful doc package is a canonical-name and compatibility-language sweep for the two Tier A columns plus explicit preservation of the no-go and deferred Tier B / Tier C boundaries.

Cheapest falsifying check:

- Confirm that no touched doc quietly opens Tier B, Phase 6, or no-go surfaces while updating the preferred terminology.

## Execution Order

### 1. Reconfirm the authorization boundary

Required outcomes:

1. Phase 4 evidence still clearly authorizes Phase 5/6 against the frozen base.
2. The active Phase 5 packet still requires Tier A only as the first implementation slice.
3. The Tier A rename targets still rank first in the Phase 5A register.

Execution rules:

1. Do not start coding until the boundary is re-checked on disk.
2. If the packet, evidence, and register disagree, stop and return the contradiction.
3. Do not widen from “Phase 5/6 authorized” to “everything in Phase 5/6 is in scope now.”

### 2. Implement the Tier A schema and consumer slice

Required outcomes:

1. The two canonical column renames are applied on the active canonical ETU sensor surface.
2. The required runtime, ORM, route, schema, and SQL surfaces are updated to the new canonical names.
3. `COMMENT ON COLUMN` documentation is added for the proven delay-calc and relevant `*_calc` / `*_func` enum fields without inventing semantics.
4. Any compatibility shim introduced is explicitly justified by a proven consumer need.

Execution rules:

1. Prefer the smallest honest migration package.
2. Do not carry deprecated aliases as physical duplicate columns unless a validated consumer requires it.
3. If compatibility is needed, prefer a clearly named compatibility view over silent dual-write or ambiguous duplicate schema.

### 3. Validate behavior and lineage

Required outcomes:

1. The touched runtime slice still passes focused validation.
2. Delay-routing semantics remain unchanged after the rename.
3. The 4604 cascade anchor and 16671 override anchor still pass if the touched slice reaches those surfaces.
4. One explicit evidence record proves that the renamed columns still map directly to `DatSensor.DS3_SEC3_I2T` and `DatSensor.DS1GF_SEC3_I2T` on the frozen validated base.

Execution rules:

1. Run the narrowest executable checks first.
2. If the first focused validation fails, repair the same slice before widening.
3. Record lineage as evidence, not as hand-wavy narrative.

### 4. Reconcile authority and completion surfaces

Required outcomes:

1. Preferred terminology flips to `stpu_delay_calc_code` and `ground_delay_calc_code` on the touched authority docs.
2. Deprecated names are explicitly marked compatibility-only or lineage-only where retained.
3. The Phase 5 packet completion record is updated truthfully.
4. One exact statement says whether Tier B may open next or remains blocked.

Execution rules:

1. Apply the smallest truthful wording changes needed.
2. Preserve the no-go list and Tier C deferrals explicitly.
3. Do not start implementing `vw_etu_calc_context`, `vw_etu_browse`, materialized facets, cross-family FK retargets, or Phase 6 rebuild items in this packet.

## Hard Limits

1. `D:\TCC_NEW.accdb` remains the lineage authority.
2. The frozen validated post-swap ETU base remains the implementation baseline.
3. Execute **Tier A only** in the first slice, even though broader Phase 5/6 categories are authorized program-wide.
4. Do not open Tier B read-models, Tier C normalization probes, or any no-go surface in this handoff.
5. Do not erase or weaken reproducibility from the frozen validated base.
6. Do not reopen Phase 3 or Phase 4 unless current evidence falsifies a closed claim.
7. Do not invent enum semantics beyond what `DLL_END_TO_END_MAPPING.md`, `DLL_SEMANTIC_FINDINGS.md`, and the existing accepted evidence actually prove.

## Stop-And-Flag Conditions

Stop and return control to Copilot if any of the following becomes true:

1. The Phase 4 frozen-baseline authorization is missing, contradictory, or weaker than the Phase 5 packet assumes.
2. The Tier A rename requires opening Tier B, Tier C, or a no-go surface to keep the runtime functional.
3. The only way to preserve consumers is to keep duplicate physical columns without a clear governed reason.
4. A proposed compatibility layer breaks deterministic lineage or hides the canonical rename.
5. Focused validation shows a real behavior change rather than a naming-only migration.
6. Cross-family FK retarget, dropped UI-view rebuild, or non-runtime helper ORM realignment becomes necessary to finish this packet.

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. Exact files changed.
2. Exact schema objects renamed and exact column comments added.
3. Exact validations run and their outcomes.
4. Exact lineage evidence tying the renamed columns back to the frozen validated base.
5. Exact compatibility surfaces introduced, if any, and why they were necessary.
6. Exact authority-doc updates made.
7. One explicit Tier B authorization statement: open next, or blocked with reason.

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| Phase 4 authorization for post-validation work still holds | PASS | PASS (closed 2026-04-26) |
| Tier A remains the first required implementation slice | PASS | PASS (closed 2026-04-26) |
| `stpu_i2t` renamed to `stpu_delay_calc_code` on the canonical ETU sensor surface | PASS | PASS (closed 2026-04-26) |
| `gfpu_i2t` renamed to `ground_delay_calc_code` on the canonical ETU sensor surface | PASS | PASS (closed 2026-04-26) |
| Enum-column documentation added truthfully | PASS | PASS (closed 2026-04-26) |
| Focused delay-routing and sensor-context validations pass | PASS | PASS (closed 2026-04-26) |
| 4604 cascade anchor remains live | PASS | PASS (closed 2026-04-26) |
| 16671 override parity anchor remains live | PASS | PASS (closed 2026-04-26) |
| Authority docs prefer canonical names and mark deprecated names correctly | PASS | PASS (closed 2026-04-26) |
| Tier B boundary stated explicitly | PASS | PASS (closed 2026-04-26 — Tier B authorized in principle, separate packet required) |

## Auditor Note

Copilot remains the project manager and auditor for this lane. Claude Code is executing a bounded first implementation slice inside the broader Phase 5/6 authorization envelope, not opening the full cleanup program in one pass. If the smallest honest Tier A slice does not hold, preserve the contradiction, stop at the boundary, and hand the decision back instead of widening into Tier B or Phase 6 work to make the migration “come out clean.”
