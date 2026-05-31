---
dispatch_id: 2026-05-30-cc-d012-phase4b-drop-backcompat
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-d012-phase4a-repoint-db-objects
closeout: ops/agents/handoffs/2026-05-30-d012-phase4b-drop-backcompat-closeout.md
---

# Decision-012 Phase 4b — DROP the back-compat views + orphaned legacy tables (IRREVERSIBLE — closes D-012)

**Lane:** Decision-012, Phase 4b — the **terminal, irreversible** step. **Desktop (technical authority) go = GO**, gated on the final pre-drop verification below passing. This drops the 60 back-compat views + 10 orphaned `_pre_rebuild` tables + 1 `_v2` table — all confirmed to have zero consumers (app on `tcc.*` since Phase 3; DB objects repointed in Phase 4a, old-ref scan = 0). **Table data is destroyed — there is no data DOWN.** Safety = a final reference scan + `RESTRICT` drops + a transactional dry-run (any dependency → ROLLBACK, nothing dropped). Follow the inbox lifecycle (claim-push BEFORE running).

## Drop-set (exactly these; from the Phase-4 characterization)
**60 back-compat VIEWS** — all 39 `public.tcc_*` + all 21 `work.tcc_relay_*` old-name views (full list in `ops/agents/handoffs/2026-05-30-d012-phase4-characterization-closeout.md` §1).

**10 SAFE-TO-DROP `_pre_rebuild` TABLES** (orphaned — no inbound FK, no DB/app ref):
`public.tcc_etu_gfd_equations_pre_rebuild`, `public.tcc_etu_inst_curves_pre_rebuild`, `public.tcc_etu_ltd_params_pre_rebuild`, `public.tcc_etu_ltpu_multipliers_pre_rebuild`, `public.tcc_etu_plugs_pre_rebuild`, `public.tcc_etu_sensor_maint_pre_rebuild`, `public.tcc_etu_sensor_params_pre_rebuild`, `public.tcc_etu_settings_pre_rebuild`, `public.tcc_etu_std_equations_pre_rebuild`, `public.tcc_etu_stpu_overrides_pre_rebuild`.

**1 `_v2` TABLE:** `public.tcc_etu_sensor_maint_v2`.

## DO NOT DROP (must-keep — verify still present after)
- The **10 MUST-KEEP `_pre_rebuild`** tables (pinned by the `tcc_test_plans` FK chain per D1): `tcc_etu_gfd_bands_pre_rebuild`, `tcc_etu_gfpu_pickups_pre_rebuild`, `tcc_etu_inst_pickups_pre_rebuild`, `tcc_etu_ltd_bands_pre_rebuild`, `tcc_etu_ltpu_pickups_pre_rebuild`, `tcc_etu_sensors_pre_rebuild`, `tcc_etu_std_bands_pre_rebuild`, `tcc_etu_stpu_pickups_pre_rebuild`, `tcc_trip_styles_pre_rebuild`, `tcc_manufacturers_pre_rebuild`.
- `public.sops_v2` (non-TCC, out of scope). The `tcc.*` base tables. The `tcc_test_plans`/`tcc_test_results` tables.

## Execute (gated)

1. **Claim** (`git mv` pending→claimed, push) BEFORE running.

2. **FINAL pre-drop verification (read-only — STOP if anything fails):**
   - **DB-object scan:** confirm ZERO functions/views/matviews/triggers/rules reference any of the 60 views or the 11 drop tables (`pg_depend` + body text scan; escape `_` literally — the 4a guard lesson). Expect 0.
   - **App scan:** grep `apps/` + `scripts/` for the 10 safe `_pre_rebuild` names + `tcc_etu_sensor_maint_v2` + any `public.tcc_*`/`work.tcc_relay_*` old-view name. Expect 0 (relay/breaker already on `tcc.*`).
   - **If ANY reference is found → STOP, do not drop, report it.** (This would mean something was missed in Phase 3/4a.)

3. **Author** `infra/database/migrations/tcc/003_phase4b_drop_backcompat.sql` (UP). ONE transaction:
   - A guard block that re-asserts (via `pg_depend`/catalog) that nothing depends on the drop-set → `RAISE EXCEPTION` if so.
   - `DROP VIEW public.<name> RESTRICT;` × 39 + `DROP VIEW work.<name> RESTRICT;` × 21.
   - `DROP TABLE public.<name> RESTRICT;` × the 10 safe `_pre_rebuild` + `tcc_etu_sensor_maint_v2`.
   - A final guard asserting the 10 MUST-KEEP `_pre_rebuild` + `sops_v2` + a sample of `tcc.*` base tables still exist.
   - **Use `RESTRICT` (never `CASCADE`)** — if any unexpected dependency exists, the drop errors and the whole transaction rolls back. No `_down.sql` (terminal); state that explicitly in a header comment (views are trivially re-creatable from `tcc.*` if ever needed; the orphaned table data is intentionally retired).

4. **Dry-run:** `BEGIN` → apply UP → run the post-drop gate (below) → `ROLLBACK`. Confirm zero errors, all drops succeed under RESTRICT, gate green, must-keep intact. **If the dry-run errors (RESTRICT or guard) → STOP, report — do not force.**

5. **Apply** (only if dry-run clean): commit the migration file, apply UP with `COMMIT`.

6. **Post-drop gate (behavior must be IDENTICAL — nothing referenced the dropped objects):**
   - `scripts/probe_live_etu_sql_parity.py` → PASS 3/0.
   - `scripts/probe_live_relay_sql_parity.py` → PASS 6/6.
   - breaker `catalog/status` → 200 `{63,17831}`; `etu/search` + `tmt/facets` + `emt/facets` → 200.
   - `settings/29442` + `context/29442` + `etu/breaker-cascade?sensor_id=29442` → 200 (the 4a-fixed `vw_trip_unit_cascade` path); 29442 still resolves `531 / NA`.
   - relay `sections` → 200.
   - **Catalog confirmation:** the 60 views are gone; the 11 tables are gone; the 10 MUST-KEEP `_pre_rebuild` + `sops_v2` + `tcc.*` (60 base tables) remain.
   - **Any post-COMMIT gate FAIL → escalate immediately** (this should be impossible given the dry-run + RESTRICT + pre-scan; if it happens, report exact failure — recovery is via migration history / backup, not a code DOWN).

## Guardrails
- **Drop EXACTLY the listed set.** RESTRICT only. Touch no MUST-KEEP table, no `tcc.*` base table, no `sops_v2`, no app code.
- DSN out-of-band; no `.env*` contents. Scoped `git add` (the migration file + closeout).

## Closeout
Record: the final pre-drop verification results (DB + app scans = 0), the dry-run result, the apply result, the full post-drop gate table, and the catalog confirmation (dropped-set gone + must-keep present). Then `git mv` claimed→done, commit, push, return to Desktop. **On PASS, Decision-012 is COMPLETE — `tcc.*` stands alone as the single unified TCC catalog; the legacy `public.tcc_*` / `work.tcc_relay_*` / orphaned `_pre_rebuild` / `_v2` surfaces are retired.**
