# TCC Runtime 017 ETU Live SQL Parity And Local Host Refresh - Closeout Handoff

Date: 2026-05-28
Status: Closed PASS for runtime repair; durability and parity backlog backfilled
Purpose: Record the ETU runtime repair closeout after live SQL helper repair, route-contract lock, parity proof, refreshed local host validation, and the later durability/provenance reconciliation review

---

## 1. Outcome

This lane is closed PASS. The control-plane ETU runtime now preserves one deliberate contract boundary and one deliberate maintenance boundary:

- The active API contract remains route-owned in `apps/control-plane-api/services/neta/router.py`.
- The live Supabase helper functions remain repaired and available as parity and maintenance surfaces.

The ETU routes intentionally continue to load settings from direct ETU tables and evaluate measured pickup data in-process rather than recoupling `GET /api/v1/neta/settings/{sensor_id}`, `POST /api/v1/neta/evaluate`, or `POST /api/v1/neta/plot-tcc` back to `fn_sensor_available_settings()` or `fn_evaluate_test_results()`.

A parity drift was found and repaired in the route-owned pickup deviation percentage rounding. The runtime now uses Decimal half-up rounding so the API matches Postgres `ROUND(..., 2)` for the shared ETU contract, including the sensor `25` GFPU case `310 vs 320 -> -3.13`.

The repo-owned local host on `http://127.0.0.1:8010` was then refreshed with `apps/control-plane-api/scripts/run_platform_api_local.ps1 -Restart`, and the refreshed host passed both the ETU SQL parity probe and the full local NETA family smoke.

---

## 2. Governing Surfaces

Code and tests:

- `apps/control-plane-api/services/neta/router.py`
- `apps/control-plane-api/tests/test_settings_route.py`
- `apps/control-plane-api/tests/test_neta_plot_tcc.py`
- `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py`
- `apps/control-plane-api/scripts/smoke_local_neta_family_routes.py`
- `apps/control-plane-api/scripts/run_platform_api_local.ps1`

Live SQL repair surfaces:

- `apps/control-plane-api/supabase/migrations/20260528_000010_align_etu_runtime_contract.sql`
- `apps/control-plane-api/supabase/migrations/20260528_000011_reapply_etu_evaluate_function.sql`

Artifacts:

- `output/dev/control-plane-live-etu-sql-parity.json`
- `output/dev/control-plane-local-neta-family-smoke.json`

---

## 3. Validation

Focused validation passed:

1. `pytest apps/control-plane-api/tests/test_settings_route.py apps/control-plane-api/tests/test_neta_plot_tcc.py`
   - Result: `41 passed`
2. `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py --base-url http://127.0.0.1:8010`
   - Result: PASS
   - Artifact: `output/dev/control-plane-live-etu-sql-parity.json`
3. `apps/control-plane-api/scripts/smoke_local_neta_family_routes.py --base-url http://127.0.0.1:8010`
   - Result: PASS
   - Artifact: `output/dev/control-plane-local-neta-family-smoke.json`

The ETU smoke remained truthful after host refresh:

- zero ETU warnings for the known scenario
- GFPU and LTPU pass
- STPU remains the truthful failing element for sensor `25`

---

## 4. Regression Provenance Verdict

The earlier closeout narrative was too clean on the demo-lineage question. The tighter verdict is:

- `git log --follow -- apps/control-plane-api/demo/neta_tcc.html` shows one committed platform-repo history point for the active demo file: `902a75a4` (`Add control-plane core publication tranche`, 2026-04-22).
- This platform repo does not contain a committed `working demo -> later broken demo` sequence for `apps/control-plane-api/demo/neta_tcc.html`.
- The correct narrower claim is therefore not `there was no regression anywhere`, but `the platform repo does not show a committed regression sequence for this file; the main committed gap here is a lagging or partial port relative to the lineage reference`.
- If the operator remembers a more functional ETU demo state, the current evidence says that state is more likely to live in the lineage reference `C:/APEX Platform/source-domains/tcc_v5_backend/demo/neta_tcc.html` or in local uncommitted work, not in committed platform-repo history for the active demo file.

---

## 5. Intended Scope Versus Actual Working-Tree Scope

The strict ETU runtime-repair core was smaller than the final working tree.

Strictly necessary to recover ETU runtime truthfulness:

- route-owned ETU settings and evaluate or plot repair in `apps/control-plane-api/services/neta/router.py`
- focused ETU regression coverage in `apps/control-plane-api/tests/test_settings_route.py` and `apps/control-plane-api/tests/test_neta_plot_tcc.py`
- shared ETU rounding and pickup support in `packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_ltd.py`, `packages/calc-engine/src/apex_calc_engine/services/calc_engine/etu_pickup.py`, and paired calc-engine tests
- live-helper durability through `apps/control-plane-api/supabase/migrations/20260528_000010_align_etu_runtime_contract.sql` and `apps/control-plane-api/supabase/migrations/20260528_000011_reapply_etu_evaluate_function.sql`
- proof surfaces `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py` and `apps/control-plane-api/scripts/smoke_local_neta_family_routes.py`

Operationally justified but adjacent hardening:

- `apps/control-plane-api/config.py` plus `apps/control-plane-api/tests/test_config_database_url_resolution.py` because the backend-local `.env` `DATABASE_URL` still points at local `tcc_v5` and can shadow the intended live DSN unless precedence is explicit

Widened scope beyond the strict ETU repair packet:

- demo parity work in `apps/control-plane-api/demo/neta_tcc.html` and `apps/control-plane-api/tests/test_demo_route.py`
- ETU browse and breaker-half parity work in `apps/control-plane-api/services/neta/router.py`, `apps/control-plane-api/services/neta/schemas.py`, `apps/control-plane-api/models/reference.py`, `apps/control-plane-api/tests/test_cascade_route.py`, `apps/control-plane-api/tests/test_etu_breaker_cascade_route.py`, and `apps/control-plane-api/tests/test_etu_search_route.py`
- TMT or EMT adjacent verification touches in `apps/control-plane-api/tests/test_neta_tmt_live_integration.py` and `apps/control-plane-api/tests/test_neta_emt_live_integration.py`
- documentation or workspace residue in `PROJECT_STATUS.md`, `apps/control-plane-api/README.md`, and `.vscode/tasks.json`

The most important durability note is that `apps/control-plane-api/services/neta/router.py` now co-mingles strict ETU runtime repair with broader ETU parity expansion, so the current worktree is not commit-ready as one undifferentiated tranche.

---

## 6. Git Durability And Push Risk

Current repo state at the time of this backfill:

- branch: `main`
- HEAD: `d7e4e016de24`
- tracked modifications: `18`
- untracked paths: `10`

The highest git-durability risks are:

- the two ETU repair migrations are already applied live but remain untracked in the repo
- the parity probe and family smoke scripts remain untracked even though they are part of the proof story
- this closeout handoff itself remains untracked in the current worktree
- `output/dev/control-plane-live-etu-sql-parity.json` and `output/dev/control-plane-local-neta-family-smoke.json` are raw local artifacts, are not ignored by repo policy today, and would become accidental commit substrate if staged casually
- `.vscode/tasks.json` is editor-local residue and should not be bundled into an application repair commit without explicit intent

Recommended commit segmentation if this lane is later made durable:

1. Core ETU runtime repair plus live SQL parity durability
2. Config and env precedence hardening
3. Demo and ETU parity expansion
4. Documentation closeout
5. Leave `.vscode/tasks.json` out unless explicitly meant to be shared

Artifact recommendation:

- keep `output/dev/*.json` as local evidence, not as default shared commit substrate
- preserve the durable proof in repo-owned handoffs and status notes
- decide any future `output/` ignore policy in a separate workspace-hygiene packet rather than silently bundling it into this runtime closeout

Push risk remains open and operator-gated:

- no push should occur without explicit operator authorization
- a direct push from the current `main` worktree would mix ETU runtime repair, parity expansion, config hardening, docs, and local residue in one batch
- app-code push risk is real because SQL migrations are already live while repo app code is still sitting as uncommitted local state

---

## 7. Active Versus Reference Demo Parity Backlog

The active control-plane demo is not an empty shell. It already contains family tabs, auth and local test auth controls, saved plans, ETU step-indicator UI, breaker-half selectors, plug lens wiring, ETU browse or search, ETU breaker-cascade wiring, and bounded TMT and EMT panels. The remaining gap versus `C:/APEX Platform/source-domains/tcc_v5_backend/demo/neta_tcc.html` is a bounded backlog, not a blank-slate rebuild.

Reference-only or reference-richer surfaces identified in this review:

- Breaker-context provenance tagging and classification (`.provenance-tag`, `classifyEtuBreakerContextSource`) are missing from the active demo. Backend dependency is already satisfied because the active stack already carries `breaker_context_source`. Verdict: `ready-to-port`.
- The richer ETU plug-compatibility workflow (`syncPlugCompatibilityControl`, `runPlugCompatibilityCheck`, `renderPlugCompatibilityResult`, and the more informative browse-refresh explanation path) is missing from the active demo. Backend dependency appears satisfied by existing `/api/v1/neta/cascade` and `/api/v1/neta/etu/search`. Verdict: `ready-to-port`.
- Control-path tagging and pickup-control helpers (`getActiveSettingControlId`, `getControlPathMode`, `renderControlPathTags`, `syncContinuousSettingInput`, `syncEtuPickupControlModes`, `applySettingValueIfApplicable`) are reference-only. They appear to sit on current settings payloads, but this backfill did not run focused browser proof for them. Verdict: `needs-evidence`.
- TMT facet-driven filter loading (`populateFacetSelect`, `gatherTmtFilters`, `refreshTmtFacets`, `ensureTmtFacetsLoaded`, `resetTmtFilters`) depends on `/api/v1/neta/tmt/facets`, which is not present in the active router. Verdict: `needs-backend-first`.
- EMT facet-driven filter loading (`gatherEmtFilters`, `refreshEmtFacets`, `ensureEmtFacetsLoaded`, `resetEmtFilters`) depends on `/api/v1/neta/emt/facets`, which is not present in the active router. Verdict: `needs-backend-first`.

This parity map should be treated as backlog only. No parity-port claim is made by this handoff.

---

## 8. Boundaries Preserved

This closeout did not:

- admit any new write path
- widen schema beyond the two ETU repair migrations already applied live
- recouple the ETU routes back to SQL helper execution
- claim hosted deployment or hosted production parity
- change TMT or EMT route authority beyond the existing local smoke proof
- make the current worktree git-durable or push-safe
- authorize any push from `main`

---

## 9. Closeout Summary

The ETU runtime repair still stands as a local PASS, but the durable record is now more honest about what remains unresolved around it.

What is durably true after this backfill:

- live SQL helpers repaired and directly revalidated
- route-owned API contract locked with regression coverage
- refreshed local `8010` host proven current via parity probe and full family smoke
- the active demo file is not proven to have regressed in committed platform-repo history; it is instead lagging a larger lineage reference while also carrying uncommitted forward-port work
- the current `main` worktree is not yet a safe single-tranche commit or push

The remaining work after this packet is not ETU runtime repair. It is git durability cleanup, commit segmentation, and a separately bounded demo parity backlog. Any follow-on should be opened as a new lane rather than smuggled in as more runtime-closeout work.
