# TCC Phase 4 Validation And Acceptance Execution Handoff

Date: 2026-04-26
Packet: `2026-04-26-tcc-phase-4-validation-and-acceptance`
Status: **CLOSED 2026-04-26** — all 8 merge gates PASS; Phase 5/6 authorized
Authority: `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE4-VALIDATION-AND-ACCEPTANCE-2026-04-25.md`
Evidence: `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE4-ACCEPTANCE-EVIDENCE-2026-04-26.md`
Project: rebuilt TCC runtime lane against Supabase `fxoyniqnrlkxfligbxmg`

## Objective

This handoff delegates the next authorized macro-phase after Runtime 016 closed cleanly on 2026-04-26.

Claude Code should execute only the bounded Phase 4 validation and acceptance lane:

1. run the checklist framework against the canonical post-swap ETU runtime,
2. reproduce the required route, staging, and live validation evidence,
3. reconcile the authority surfaces so they describe the frozen validated baseline truthfully,
4. record residual risks, deferred work, and the exact downstream authorization boundary for normalization and optimization work.

This handoff does not authorize reopening Phase 3 implementation except for a bounded blocker that falsifies the already-closed Runtime 016 evidence.

## Confirmed Entry Gate

The active packet is authorized because the required Phase 3 freeze prerequisites are already closed and evidenced:

1. TASK-009 PASS — `DatPlugs` remains sensor-rooted on the rebuilt corpus with preserved cardinality and clean parity evidence.
2. TASK-010 PASS — rebuilt-state authority docs were updated to remove stale pre-rebuild parity claims.
3. TASK-011 PASS — delay-routing semantics are implemented and documented as routing codes rather than generic booleans.
4. TASK-012 PASS across both parts — Python override branch closed first, then SQL RPC parity closed post-swap and locked in by committed live test coverage on sensor `16671`.
5. TASK-013 PASS across the authorized scope — linked selection and degraded-plug diagnostic behavior closed, and the Runtime 016 split-anchor policy (`4604` / `4174`) replaced stale `6258` proof dependency.
6. Maint-A bridge PASS — canonical MAINT runtime contracts survived the truthful swap.
7. Atomic swap PASS — canonical ETU names now point at the rebuilt source-faithful corpus.
8. Focused post-swap regression PASS — `67 passed, 2 skipped, 0 failed` across the five-file runtime-contract surface.

If any one of those statements fails during Phase 4 evidence reproduction, stop and return a blocker report instead of broadening scope or silently “fixing” the contradiction.

## Mandatory Read Set

Open these files before the first substantive validation action:

1. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE4-VALIDATION-AND-ACCEPTANCE-2026-04-25.md`
2. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-CHECKLIST-FRAMEWORK-SPEC-2026-04-25.md`
3. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-ACCESS-WORKFLOW-FIDELITY-COMPLETION-PATH-2026-04-25.md`
4. `source-domains/neta-ett-study-material/Development/TASK-VSCODE-TCC-FIDELITY-PHASE3-ATOMIC-SWAP-PREP-2026-04-26.md`
5. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE3-TASK-012-PART-2-SQL-RPC-OVERRIDE-EVIDENCE-2026-04-26.md`
6. `source-domains/neta-ett-study-material/Development/Platform/TCC/TCC-FIDELITY-PHASE3-TASK-013-PART-2-FIXTURE-REKEY-EVIDENCE-2026-04-26.md`
7. `source-domains/tcc_v5_backend/plan/architecture-tcc-access-workflow-fidelity-1.md`
8. `apex-power-ops-platform/ops/agents/handoffs/2026-04-26-tcc-runtime-016-atomic-swap-prep-execution-handoff.md`

## First Validation Anchors

Start from the already-proven post-swap runtime surfaces rather than broad repo exploration.

### Runtime validation anchors

1. `source-domains/tcc_v5_backend/tests/test_neta_plot_tcc.py`
2. `source-domains/tcc_v5_backend/tests/test_sensor_context_route.py`
3. `source-domains/tcc_v5_backend/tests/test_etu_delay_routing.py`
4. `source-domains/tcc_v5_backend/tests/test_stpu_override_enforcement.py`
5. `source-domains/tcc_v5_backend/tests/test_sql_rpc_pickup_methods_live.py`
6. `source-domains/tcc_v5_backend/migrations/maint/vw_sensor_calc_context.sql`
7. `source-domains/tcc_v5_backend/migrations/maint/fn_calculate_test_currents.sql`

Local hypothesis for the first slice:

- The canonical post-swap ETU runtime reproduces the already-accepted Runtime 016 evidence cleanly, and the remaining Phase 4 work is primarily checklist classification, documentation reconciliation, and closeout boundary definition rather than new runtime repair.

Cheapest falsifying check:

- Re-run the five-file regression surface and verify that the known proof anchors (`4604` cascade and `16671` override parity) still fire on the current canonical runtime before widening into broader evidence collection.

### Authority-reconciliation anchors

1. `source-domains/tcc_v5_backend/DLL_END_TO_END_MAPPING.md`
2. `source-domains/tcc_v5_backend/ACCESS_TO_SUPABASE_GAP_ANALYSIS.md`
3. `source-domains/tcc_v5_backend/DLL_SEMANTIC_FINDINGS.md`
4. `source-domains/tcc_v5_backend/IMPLEMENTATION_STATUS.md`
5. `source-domains/tcc_v5_backend/NETA_TCC_OVERLAY_SPEC.md`
6. `source-domains/tcc_v5_backend/migrations/phase3_supabase_rebuild/README.md`

Local hypothesis for the doc slice:

- The remaining risk is no longer hidden runtime drift; it is stale wording, methodology ambiguity, or deferred-work leakage across mapping, gap-analysis, and status docs.

Cheapest falsifying check:

- Read the current authority docs against the checklist framework and identify any statement that still overclaims pre-rebuild parity, obscures staging-to-live lineage, or prematurely authorizes normalization and cleanup work.

### Methodology-note anchor

1. `source-domains/tcc_v5_backend/plan/architecture-tcc-access-workflow-fidelity-1.md`
2. `source-domains/tcc_v5_backend/migrations/phase3_supabase_rebuild/README.md`

Phase 4 must close the plug-fingerprint methodology wording so the final record carries one canonical explanation for the already-proven divergence counts rather than multiple drifting phrasings.

## Execution Order

### 1. Reproduce the closed Runtime 016 baseline

Required outcomes:

1. The five-file post-swap regression reproduces on the current canonical runtime.
2. The `4604` cascade proof and `16671` override parity proof remain live and passing.
3. Any failure is classified immediately as either a real contradiction or an environment-specific blocker.

Execution rules:

1. Start from the narrowest executable checks first.
2. Do not widen into broad doc editing until the runtime baseline is reproduced or falsified.
3. If the first executable validation fails, repair scope is not automatically authorized; first determine whether the failure contradicts the closed Runtime 016 evidence.

### 2. Execute the checklist framework on the active ETU slice

Required outcomes:

1. Routing, linkage, selection, execution, degradation, evidence, and authority-hygiene each receive an explicit outcome under the framework.
2. Every non-`PASS` item carries a remediation or deferred-owner statement.
3. The outcome set is tied to durable evidence, not broad narrative.

Execution rules:

1. Use the checklist framework literally.
2. Cite exact files, tests, queries, and evidence records for every conclusion.
3. Preserve the distinction between Access authority, validated staging, and live Supabase.

### 3. Reconcile authority surfaces

Required outcomes:

1. Mapping, gap-analysis, runtime-status, and overlay docs agree on the post-swap baseline.
2. The plug-fingerprint methodology note is stated once, canonically.
3. No doc implies that bounded demo coherence equals full Access-fidelity parity unless the evidence actually proves it.

Execution rules:

1. Make the smallest truthful wording updates needed.
2. Do not invent new evidence to smooth contradictions.
3. Do not authorize Phase 5 or Phase 6 cleanup implementation inside these documents.

### 4. Close the acceptance packet

Required outcomes:

1. The frozen validated baseline is stated explicitly.
2. Residual risks and deferred work are captured cleanly.
3. The downstream normalization and optimization boundary is authorized or blocked with one exact statement.

## Hard Limits

1. `D:\TCC_NEW.accdb` remains the sole behavioral authority.
2. Do not reopen Phase 3 implementation unless Phase 4 evidence proves a closed Runtime 016 claim is no longer true.
3. Do not start Phase 5 or Phase 6 cleanup implementation in this packet.
4. Do not let doc cleanup blur the distinction between rebuilt source-faithful base, canonical post-swap runtime, and future product-facing normalization.
5. Do not turn environmental skips or data-availability parametric edges into unsupported parity claims.

## Stop-And-Flag Conditions

Stop and return control to Copilot if any of the following becomes true:

1. The five-file regression surface no longer reproduces the accepted `67 passed, 2 skipped, 0 failed` baseline.
2. The `4604` cascade proof or `16671` override parity proof stops firing on the canonical runtime.
3. A required Phase 4 conclusion depends on speculative Access exports, hidden local files, or unverified memory instead of cited evidence.
4. The required change widens into Phase 3 reimplementation or Phase 5 or 6 cleanup work.
5. Authority docs disagree in a way that cannot be reconciled honestly without a new governance decision.

## Expected Deliverables Back To Copilot

Return a completion or blocker note that includes all of the following:

1. Exact files changed.
2. Exact validations run and their outcomes.
3. Checklist outcomes for the active ETU slice, with any `CONDITIONAL PASS`, `FAIL`, or `BLOCKED` item enumerated explicitly.
4. Exact authority-doc contradictions found and how they were resolved.
5. Explicit frozen-baseline statement.
6. Explicit downstream authorization statement for post-validation normalization and optimization work.

## Merge Gate Target

| Gate | Target result | Actual outcome |
|---|---|---|
| Five-file post-swap regression reproduces | PASS (`67 passed, 2 skipped, 0 failed`) | **PASS 2026-04-26** — reproduced exactly: 67 passed / 2 skipped / 0 failed in 8.02s against the current canonical runtime |
| `4604` cascade proof remains live | PASS | **PASS 2026-04-26** — `test_sql_rpc_matches_python_for_stpu_ltpu_cascade_sensor_4604` PASS end-to-end |
| `16671` SQL=Python override parity remains live | PASS | **PASS 2026-04-26** — `test_sql_rpc_matches_python_for_stpu_override_sensor_16671` PASS end-to-end |
| Checklist framework executed across all 7 sections | PASS | **PASS 2026-04-26** — `TCC-FIDELITY-PHASE4-ACCEPTANCE-EVIDENCE-2026-04-26.md` §3 records 29 PASS / 2 CONDITIONAL PASS / 0 FAIL / 0 BLOCKED across routing, linkage, selection, execution, degradation, evidence, authority hygiene |
| Authority docs reconciled to the canonical post-swap baseline | PASS | **PASS 2026-04-26** — rebuilt-state banners flipped on 5 authority docs; `migrations/phase3_supabase_rebuild/README.md` "Out Of Scope" wording flipped to closed; architecture plan Phase 5 rows TASK-014/015/016 closed with evidence pointers; status badge advanced to "Phase 4 closed; Phase 5/6 authorized" |
| Plug-fingerprint methodology note closed canonically | PASS | **PASS 2026-04-26** — canonical disposition recorded in Phase 4 evidence §5.3 and annotated into `TCC-FIDELITY-PHASE2-STAGING-PARITY-EVIDENCE-2026-04-25.md` §4.4: divergent-style count `290 / 1,801 / 2,091 = 86.13%` is the load-bearing L1 metric; `12,071 vs 720` distinct-sensor-fingerprint discrepancy is a tokenization-artifact note, not L1 evidence |
| Frozen validated baseline stated explicitly | PASS | **PASS 2026-04-26** — Phase 4 evidence §6.1 records the frozen baseline statement covering canonical `tcc_etu_*` tables, pre-rebuild preservation at `*_pre_rebuild`, view rebinds, ORM aliasing pattern, regression result, and live anchor parity |
| Downstream normalization/optimization boundary stated explicitly | PASS | **GO** — Phase 4 evidence §6.2 explicitly authorizes Phase 5 Tier A (storage column renames), Phase 5 Tier B (derived aliases), and Phase 6 (cross-family FK retarget, non-runtime ORM realignment, dropped-UI-view rebuild); hard-limits enumerated; reopening Phase 3 implementation remains out of scope |

## Auditor Note

Copilot remains the project manager and auditor for this lane. Claude Code is executing a bounded validation and closeout slice, not redefining acceptance criteria or reopening closed work casually. If the evidence contradicts the closed Runtime 016 baseline, preserve the contradiction, stop at the boundary, and hand the decision back instead of smoothing the discrepancy over in code or docs.