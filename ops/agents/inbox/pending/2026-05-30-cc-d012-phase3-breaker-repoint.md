---
dispatch_id: 2026-05-30-cc-d012-phase3-breaker-repoint
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-d012-phase2-expand-rerun
closeout: ops/agents/handoffs/2026-05-30-d012-phase3-breaker-repoint-closeout.md
---

# Decision-012 Phase 3 (BREAKER) — repoint breaker route SQL `public.tcc_*` → `tcc.*`

**Lane:** Decision-012, Phase 3, **breaker half only** (relay is a separate follow-on dispatch). **Operator-authorized.** Phase 2 EXPAND is LIVE: the real tables are in `tcc.*` and old names (`public.tcc_*`) still resolve as **back-compat views**. This phase repoints the application's breaker SQL from the old names to `tcc.*`. **This is a CODE-ONLY change — no DB DDL.** Because both names currently resolve to the same data, it is **fully reversible by reverting the commit** (DB untouched) and **parity-gated**. Follow the inbox lifecycle (claim-push BEFORE editing).

## Scope — EXACTLY the 39 breaker carry tables, NOTHING else
Repoint each old breaker table reference `tcc_<suffix>` → `tcc.<suffix>` (the table moved to schema `tcc` AND dropped its `tcc_` prefix in Phase 2). The breaker set is these name families (all 39 EXPAND carry tables that are NOT relay):
- `tcc_brk_iccb`, `tcc_brk_iccb_styles`, `tcc_brk_mccb`, `tcc_brk_mccb_styles`, `tcc_brk_pcb`, `tcc_brk_pcb_styles`
- `tcc_emt`, `tcc_emt_band_names`, `tcc_emt_curves`, `tcc_emt_frame_amps`, `tcc_emt_frames`, `tcc_emt_pickups`, `tcc_emt_sections`
- `tcc_etu_*` (gfd_bands, gfd_equations, gfpu_pickups, inst_curves, inst_pickups, ltd_bands, ltd_params, ltpu_multipliers, ltpu_pickups, plugs, sensor_maint, sensor_params, sensors, settings, std_bands, std_equations, stpu_overrides, stpu_pickups)
- `tcc_manufacturers`
- `tcc_tmt_amps`, `tcc_tmt_curves`, `tcc_tmt_frames`, `tcc_tmt_settings`, `tcc_tmt_thermal_adj`
- `tcc_trip_styles`, `tcc_trip_types`

Mapping examples: `tcc_brk_iccb` → `tcc.brk_iccb`; `tcc_etu_sensors` → `tcc.etu_sensors`; `tcc_manufacturers` → `tcc.manufacturers`; `tcc_tmt_frames` → `tcc.tmt_frames`.

### DO NOT touch (critical — a blind `tcc_`→`tcc.` sed would corrupt these)
- **Relay tables** — `tcc_relays`, `tcc_relay_*`, and any `work.tcc_relay_*`. **Left entirely for the relay Phase-3 dispatch.**
- **Non-table tokens** — `tcc_number`, `tcc_no`, and any other `tcc_*` identifier that is NOT one of the 39 tables above (column names, Python variables, response-field keys, comments). Repoint **only inside SQL query text** where the token is an actual table reference (FROM/JOIN/INTO/UPDATE/etc.), never a column or a Python identifier.

## Execute (gated)

1. **Claim** (`git mv` pending→claimed, commit, push) BEFORE editing.

2. **Enumerate first (report in closeout):** for each of the 39 breaker tables, grep its occurrences across the control-plane app SQL — primary `apps/control-plane-api/services/neta/router.py`, plus any breaker-touching `scripts/probe_*`/helpers and `tests/`. Report a per-file count and confirm zero ambiguous hits (e.g. distinguish the table `tcc_manufacturers` from any column/field named similarly). If anything is ambiguous, note it and proceed conservatively (table references only).

3. **Repoint** the 39 breaker tables → `tcc.*` across router.py (route SQL) and the breaker probes/tests you enumerated. Keep relay refs untouched. Minimal, mechanical, table-reference-only edits.

4. **Build/test local:** run the control-plane breaker test subset + the ETU pickup tests; report pass counts. Push to `main` → Render autoDeploys.

5. **Post-deploy parity-gate (the breaker SQL now hits `tcc.*` directly; behavior must be IDENTICAL):** wait for the deploy to land (poll readiness), then against `https://control.apexpowerops.com`:
   - `scripts/probe_live_etu_sql_parity.py` → PASS 3/0 (this also exercises `fn_calculate_test_currents`/`fn_evaluate_test_results` via `/calculate` + `/evaluate`).
   - `GET /api/v1/neta/catalog/status` → 200 `{63, 17831}`.
   - `GET /api/v1/neta/etu/search?q=&limit=3` → 200.
   - `GET /api/v1/neta/tmt/facets` → 200; `GET /api/v1/neta/emt/facets` → 200.
   - relay sanity (must be UNAFFECTED): `scripts/probe_live_relay_sql_parity.py` → PASS 6/6; `GET /api/v1/neta/relay/sections` → 200.
   - **Any FAIL → `git revert` the repoint commit, push (redeploy restores old-name SQL over the still-present views), report.** No DB action needed — this is code-only.

6. **Surface for Phase 4 (do NOT fix here):** while you have DSN read access, report which **DB functions/views** still reference old breaker names in their bodies (e.g. `fn_calculate_test_currents`, `fn_evaluate_test_results`, `fn_sensor_available_settings`, `vw_sensor_calc_context`, `vw_trip_unit_cascade`) — query `pg_get_functiondef` / `pg_views`. These resolve through the back-compat views today; Phase 4 must repoint them (DB migration) before the views can be dropped. List them; that's the Phase-4 prerequisite set for the breaker side.

## Guardrails
- **Breaker app SQL ONLY.** No relay repoint. No DB DDL, no view/function-body edits, no view drops (Phase 4). No migration SQL changes.
- Scoped `git add` (the repointed app files + closeout). DSN out-of-band; no `.env*` contents.

## Closeout
Record: per-table/per-file enumeration counts, the diff summary (files + occurrences repointed), local test result, commit hash, Render deploy confirmation, the full post-deploy parity-gate table (incl. relay-unaffected sanity), whether a revert was needed, and the Phase-4 DB-object list from step 6. Then `git mv` claimed→done, commit, push, return to Desktop. **Next:** the relay Phase-3 dispatch (repoint `work.tcc_relay_*` + bare relay refs → `tcc.*`, plus repoint the relay guard from the `work` schema to `tcc`).
