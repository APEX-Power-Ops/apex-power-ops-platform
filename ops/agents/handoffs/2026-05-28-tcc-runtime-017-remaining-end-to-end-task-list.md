# TCC Runtime 017 Remaining End-To-End Task List

Date: 2026-05-28
Status: Planning backlog
Purpose: Record the remaining bounded work needed to move the NETA TCC lane from the current ETU runtime-repair closeout to an end-to-end durable, validated, and decision-ready posture

---

## 1. Current Starting Point

What is already true:

- ETU runtime repair is locally closed PASS.
- Live SQL helper parity has been repaired and revalidated.
- The active demo is proven to lag the lineage reference rather than showing a committed in-repo regression sequence.
- The worktree is still mixed and not yet durable as one safe commit or push unit.

What is not yet true:

- the current lane is not git-durable
- the active demo is not yet reconciled to a clearly chosen reference target
- ETU parity backlog items have not been split into execution slices
- TMT and EMT facet-driven parity remains backend-incomplete
- no hosted parity or deployment decision has been taken for this tranche

---

## 2. Governing Decision First

Before additional implementation, resolve the target stance for the active demo:

1. Confirm whether the active control-plane demo is intended to reach full lineage parity with `C:/APEX Platform/source-domains/tcc_v5_backend/demo/neta_tcc.html`.
2. If not full parity, define the deliberately scoped subset that is considered the promoted runtime target.
3. Freeze that decision in repo-owned documentation before more parity work lands, so later slices are measured against an explicit target rather than memory.

This decision is the gate between a bounded parity program and open-ended forward-port drift.

---

## 3. Remaining Task List

### Phase A - Git Durability And Lane Separation

1. Split the mixed worktree into commit-safe slices:
   - core ETU runtime repair plus live SQL parity durability
   - config and env precedence hardening
   - ETU demo and parity expansion
   - documentation closeout
2. Use the current path mapping below so no modified files are orphaned during the local commit split:
    - core ETU runtime repair plus live SQL parity durability:
       `apps/control-plane-api/services/neta/router.py`
       `apps/control-plane-api/tests/test_settings_route.py`
       `apps/control-plane-api/tests/test_neta_plot_tcc.py`
       `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py`
       `apps/control-plane-api/scripts/smoke_local_neta_family_routes.py`
       `apps/control-plane-api/supabase/migrations/20260528_000010_align_etu_runtime_contract.sql`
       `apps/control-plane-api/supabase/migrations/20260528_000011_reapply_etu_evaluate_function.sql`
       `packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_ltd.py`
       `packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_pickup.py`
       `packages/calc-engine/tests/test_source_faithful_adapters.py`
       `packages/calc-engine/tests/test_stpu_override.py`
    - config and env precedence hardening:
       `apps/control-plane-api/config.py`
       `apps/control-plane-api/tests/test_config_database_url_resolution.py`
       `apps/control-plane-api/tests/test_neta_tmt_live_integration.py`
       `apps/control-plane-api/tests/test_neta_emt_live_integration.py`
    - ETU demo and parity expansion:
       `apps/control-plane-api/demo/neta_tcc.html`
       `apps/control-plane-api/services/neta/schemas.py`
       `apps/control-plane-api/models/reference.py`
       `apps/control-plane-api/tests/test_cascade_route.py`
       `apps/control-plane-api/tests/test_demo_route.py`
       `apps/control-plane-api/tests/test_etu_breaker_cascade_route.py`
       `apps/control-plane-api/tests/test_etu_search_route.py`
    - documentation closeout:
       `PROJECT_STATUS.md`
       `apps/control-plane-api/README.md`
       `ops/agents/handoffs/2026-05-28-tcc-runtime-017-etu-live-sql-parity-and-local-host-refresh-closeout-handoff.md`
       `ops/agents/handoffs/2026-05-28-tcc-runtime-017-remaining-end-to-end-task-list.md`
3. The TMT and EMT live-integration tests belong with config and env precedence hardening, not the ETU runtime-repair commit: their current diffs change swallowed connection failures into explicit `SQLAlchemyError` test failures, which is database-truthfulness hardening rather than family-smoke feature expansion.
4. Keep `output/dev/*.json` as local evidence unless a separate workspace-hygiene decision explicitly promotes them into tracked substrate.
5. Keep `.vscode/tasks.json` out of the lane unless explicitly intended for shared repo use.
6. Create the local commits in that order before any push decision.
7. Treat push as a separate operator-gated deployment decision because the migrations are already live.

### Phase B - Reference Target And Backlog Freezing

1. Convert the current parity findings into an explicit backlog board with three labels:
   - `ready-to-port`
   - `needs-evidence`
   - `needs-backend-first`
2. Record the source-domain demo as the current behavioral reference-of-record unless or until the operator selects a smaller target.
3. Freeze the forward-port boundary so future work can say whether it is:
   - parity recovery
   - runtime hardening
   - deliberate divergence

### Phase C - ETU Frontend-Ready Parity Recovery

1. Port breaker-context provenance tagging into the active demo:
   - `classifyEtuBreakerContextSource`
   - provenance tag render path
   - ETU summary disclosure styling
2. Port the richer ETU plug-compatibility workflow into the active demo:
   - compatibility control sync
   - explicit compatibility check action
   - result rendering and advisory copy
   - browse-refresh explanation improvements
3. Add focused browser and route proof for these ETU parity items so they are validated as workflow logic rather than assumed UI polish.

### Phase D - ETU Evidence-Gated Parity Recovery

1. Run focused browser proof on control-path and pickup-control helpers against the current active runtime.
2. Decide whether the following should be promoted as part of the active contract:
   - `getActiveSettingControlId`
   - `getControlPathMode`
   - `renderControlPathTags`
   - `syncContinuousSettingInput`
   - `syncEtuPickupControlModes`
   - `applySettingValueIfApplicable`
3. If the proof is clean, port them as the next ETU slice.
4. If the proof exposes contract gaps, split those gaps into backend or settings-shape follow-ons rather than burying them in demo code.

### Phase E - TMT And EMT Backend-First Completion

1. Define the missing facet contracts for `/api/v1/neta/tmt/facets` and `/api/v1/neta/emt/facets`.
2. Implement those routes in `apps/control-plane-api/services/neta/router.py` with explicit schema support.
3. Add focused route tests for both facet endpoints.
4. Port the reference facet-driven demo behavior only after the backend contracts exist.
5. Re-run TMT and EMT local route smoke after each family slice rather than waiting for a final bundle.

### Phase F - End-To-End Validation Surface

1. Keep the existing ETU proof surfaces green:
   - ETU focused pytest slice
   - live SQL parity probe
   - local family smoke
2. Add browser-level proof for the active demo against the selected parity target.
3. Add family-scoped validation for any new TMT or EMT facet work.
4. Re-run the full family smoke on the refreshed local host after each bounded tranche.
5. Do not claim hosted parity until local route, local browser, and local smoke proof all agree.

### Phase G - Hosted Decision And Deployment Gate

1. After local durability and parity slices are committed, decide whether the tranche should be deployed.
2. If deployment is admitted, separate that packet from the local commit packet.
3. Revalidate hosted behavior explicitly rather than assuming local parity implies hosted parity.
4. Record the hosted verdict in a new bounded handoff, not by extending the local repair closeout.

### Phase H - Documentation And Lane Closeout

1. Update `PROJECT_STATUS.md` only after the durability split and parity target are stable.
2. Keep the runtime-repair closeout as historical truth and record follow-on parity work in new bounded notes.
3. When the lane is truly end-to-end complete, close it with one final summary that states:
   - committed durability achieved
   - selected parity target achieved
   - local proof achieved
   - hosted proof achieved or intentionally deferred

---

## 4. Recommended Immediate Sequence

The next practical order is:

1. make the current ETU runtime-repair slice git-durable locally
2. freeze the reference-target decision for the active demo
3. execute the ETU `ready-to-port` parity slice
4. run focused browser proof for the ETU `needs-evidence` slice
5. open backend-first TMT and EMT facet work as separate bounded slices

This keeps the highest current risk first: local loss and repo-versus-live drift.

---

## 5. Explicit Boundaries

This task list does not itself:

- authorize a push
- claim hosted parity
- collapse ETU, TMT, and EMT into one unbounded implementation packet
- promote raw `output/dev` artifacts into tracked substrate
- treat the source-domain reference as auto-port authority without the explicit target decision above