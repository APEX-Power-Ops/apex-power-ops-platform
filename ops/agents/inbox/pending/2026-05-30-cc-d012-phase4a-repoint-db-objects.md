---
dispatch_id: 2026-05-30-cc-d012-phase4a-repoint-db-objects
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-d012-phase4-characterization
closeout: ops/agents/handoffs/2026-05-30-d012-phase4a-repoint-db-objects-closeout.md
---

# Decision-012 Phase 4a — repoint the 3 remaining DB object bodies → `tcc.*` (REVERSIBLE)

**Lane:** Decision-012, Phase 4a. **Operator-deferred-to-Desktop; Desktop (technical authority) authored + accepted the one behavior change below.** This repoints the last DB objects that still reference old names, so Phase 4b can drop the back-compat views. **This is `CREATE OR REPLACE` only — NO drops, NO table changes.** It is **reversible** (the DOWN restores the captured original definitions verbatim) and parity-gated. Follow the inbox lifecycle (claim-push BEFORE running).

## The 3 repoint targets (from the Phase-4 characterization)
1. **`public.fn_calculate_test_currents(...)`** — change the single body ref `public.tcc_etu_stpu_overrides` → `tcc.etu_stpu_overrides`. No other logic change.
2. **`public.fn_sensor_available_settings(p_sensor_id integer)`** — change ALL old ETU availability refs → `tcc.*`: `tcc_etu_gfpu_pickups`, `tcc_etu_inst_pickups`, `tcc_etu_ltd_bands`, `tcc_etu_ltpu_multipliers`, `tcc_etu_ltpu_pickups`, `tcc_etu_plugs` (incl. the one unqualified `tcc_etu_plugs` token), `tcc_etu_sensors`, `tcc_etu_stpu_pickups` → the matching `tcc.<name>`. No other logic change.
3. **`public.vw_trip_unit_cascade`** — **ACCEPTED BEHAVIOR FIX (Desktop technical-authority).** Remove the stale `_pre_rebuild` bridge in the `trip_type` CTE and join `tcc.trip_types` directly by **canonical `manufacturer_id`** AND `name = ts.type` (keep everything else identical — manufacturer columns already come from canonical `tcc.manufacturers`). This restores 396 trip-type associations currently NULLed by the canonical-id-through-_pre_rebuild-name mismatch. It is **purely additive** (396 NULL→value; the characterization confirmed 0 rows change an existing value). Preserve all current output columns + names + ordering exactly.

## Method (reversible)
1. **Claim** (`git mv` pending→claimed, push) BEFORE running.
2. **Capture the 3 CURRENT definitions verbatim** (`pg_get_functiondef` for the 2 functions, `pg_get_viewdef('public.vw_trip_unit_cascade', true)` for the view). These become the **DOWN** migration (exact restore — no edits).
3. **Author the migration pair:**
   - `infra/database/migrations/tcc/002_phase4a_repoint_db_objects.sql` (UP): `CREATE OR REPLACE FUNCTION`/`VIEW` for the 3 objects with the repoints above, wrapped in one transaction with guards.
   - `infra/database/migrations/tcc/002_phase4a_repoint_db_objects_down.sql` (DOWN): the 3 captured originals verbatim.
   - **Include the final `vw_trip_unit_cascade` UP definition in the closeout** for the record.
4. **Dry-run:** `BEGIN` → apply UP → run the gate checks (below) inside the txn where possible → `ROLLBACK`. Confirm clean + the 396-restore shows up.
5. **Apply:** commit the 2 migration files, then apply UP with `COMMIT` to prod.
6. **Post-apply parity-gate:**
   - `scripts/probe_live_etu_sql_parity.py` → **PASS 3/0** (covers `fn_calculate_test_currents`).
   - `GET /api/v1/neta/settings/{sensor_id}` for a real sensor (pick one from `etu/search`) → 200 with sane available settings (covers `fn_sensor_available_settings`).
   - **`vw_trip_unit_cascade` consumers:** hit the breaker routes that use it — `GET /api/v1/neta/context/{id}` and the `etu/breaker-cascade` path (router.py lines 1647/2849/2926/2943/2964/2988/3008/3039/3084/3105) → 200.
   - **396-restore spot-check:** confirm sensor **29442** (Chint) now resolves trip type **`531 / NA`** (was NULL), and the view's total NULL-`trip_type_id` count dropped by ~396 vs the captured pre-apply baseline. (Read-only SELECT on the view, or via a consumer route.)
   - breaker `catalog/status` → 200 `{63,17831}`; relay parity 6/6 + `relay/sections` 200 (UNAFFECTED).
   - **Any FAIL → apply the DOWN (restores originals), report.** No drops were done, so this is a clean restore.

## Guardrails
- **4a ONLY — `CREATE OR REPLACE` of the 3 objects.** NO `DROP` of anything (views/tables = Phase 4b). NO change to MUST-KEEP `_pre_rebuild` tables. NO app code changes (app already on `tcc.*`).
- DSN out-of-band; no `.env*` contents. Scoped `git add` (the 2 migration files + closeout).

## Closeout
Record: captured-originals confirmation (so DOWN is exact), the final `vw_trip_unit_cascade` UP definition, dry-run result (incl. the 396-restore observed), apply result, the full post-apply gate table (ETU 3/0, settings route, the cascade/context consumer routes, the 29442 spot-check + NULL-count delta, breaker + relay unaffected), and whether DOWN was needed. Then `git mv` claimed→done, commit, push, return to Desktop. **Next = Phase 4b** (the irreversible drop: 60 views + 10 SAFE-TO-DROP `_pre_rebuild` + `tcc_etu_sensor_maint_v2`), which Desktop will author with a final pre-drop verification and surface a go/no-go before it runs.
