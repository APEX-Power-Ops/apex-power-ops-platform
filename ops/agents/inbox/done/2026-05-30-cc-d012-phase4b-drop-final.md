---
dispatch_id: 2026-05-30-cc-d012-phase4b-drop-final
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-d012-phase4b-prep-resequence
closeout: ops/agents/handoffs/2026-05-30-d012-phase4b-drop-final-closeout.md
---

# Decision-012 Phase 4b — TERMINAL DROP (IRREVERSIBLE — closes D-012)

**Lane:** Decision-012, Phase 4b terminal drop. **Desktop (technical authority) go = GO.** The prep dispatch (`b38e13ea`) cleared the only sequence coupling and **already proved this exact drop dry-run passes clean under `RESTRICT`** (60 views + 11 tables drop, must-keep guard holds). This dispatch commits the terminal drop. **Table data is destroyed — there is no data DOWN.** Safety = re-run the final pre-drop verification + a fresh transactional dry-run + `RESTRICT` before the real `COMMIT`. Follow the inbox lifecycle (claim-push BEFORE running).

## Drop-set (unchanged from the characterization; the prep cleared its blockers)
- **60 back-compat VIEWS** — 39 `public.tcc_*` + 21 `work.tcc_relay_*` (full list in `2026-05-30-d012-phase4-characterization-closeout.md` §1).
- **10 SAFE-TO-DROP `_pre_rebuild` TABLES** — `tcc_etu_gfd_equations_pre_rebuild`, `tcc_etu_inst_curves_pre_rebuild`, `tcc_etu_ltd_params_pre_rebuild`, `tcc_etu_ltpu_multipliers_pre_rebuild`, `tcc_etu_plugs_pre_rebuild`, `tcc_etu_sensor_maint_pre_rebuild`, `tcc_etu_sensor_params_pre_rebuild`, `tcc_etu_settings_pre_rebuild`, `tcc_etu_std_equations_pre_rebuild`, `tcc_etu_stpu_overrides_pre_rebuild`.
- **1 `_v2` TABLE** — `public.tcc_etu_sensor_maint_v2`.

## MUST NOT DROP (verify present after)
10 MUST-KEEP `_pre_rebuild` (the `tcc_test_plans` FK chain), `public.sops_v2`, all `tcc.*` base tables, `tcc_test_plans`/`tcc_test_results`, and `tcc.etu_sensor_maint_id_seq` (now tcc-homed by the prep).

## Execute (gated)

1. **Claim** (`git mv` pending→claimed, push) BEFORE running.

2. **Final pre-drop verification (read-only — STOP if anything regressed since prep):**
   - DB-object scan: zero functions/views/matviews/triggers/rules reference any of the 60 views or 11 tables (literal `position()` match, not `LIKE`).
   - App scan: zero `apps/`+`scripts/` runtime references to the 10 safe `_pre_rebuild` names, `tcc_etu_sensor_maint_v2`, or any `public.tcc_*`/`work.tcc_relay_*` old view name.
   - Sequence coupling cleared: confirm `tcc.etu_sensor_maint_id_seq` is owned by `tcc.etu_sensor_maint.id` (the prep landed) and no SAFE-TO-DROP table owns a sequence with a kept dependent.
   - **Any reference/coupling found → STOP, report, do not drop.**

3. **Author** `infra/database/migrations/tcc/004_phase4b_drop_backcompat.sql` (UP, terminal — header comment: no data DOWN; views trivially re-creatable from `tcc.*`, orphaned table data intentionally retired). ONE transaction:
   - Pre-drop guard block (re-assert nothing depends on the drop-set; `RAISE` if so).
   - `DROP VIEW <schema>.<name> RESTRICT;` × 60.
   - `DROP TABLE public.<name> RESTRICT;` × 11.
   - Final guard: the 10 MUST-KEEP `_pre_rebuild` + `sops_v2` + a sample of `tcc.*` base tables + `tcc.etu_sensor_maint_id_seq` still exist; the drop-set is gone.
   - **`RESTRICT` only — never `CASCADE`.**

4. **Dry-run:** `BEGIN` → apply UP → run the post-drop gate → `ROLLBACK`. Must be zero errors, gate green, must-keep intact. (The prep already proved this; this is the final confirmation on the committed artifact.) **Any error → STOP, report.**

5. **Apply** (only if dry-run clean): commit the migration file, apply UP with `COMMIT`.

6. **Post-drop gate (behavior IDENTICAL):**
   - `scripts/probe_live_etu_sql_parity.py` → PASS 3/0.
   - `scripts/probe_live_relay_sql_parity.py` → PASS 6/6.
   - breaker `catalog/status` 200 `{63,17831}`; `etu/search` + `tmt/facets` + `emt/facets` 200.
   - `settings/29442` + `context/29442` + `etu/breaker-cascade?sensor_id=29442` 200; 29442 still `531 / NA`.
   - relay `sections` 200.
   - **Catalog confirmation:** 60 views gone; 11 tables gone; 10 MUST-KEEP `_pre_rebuild` + `sops_v2` + 60 `tcc.*` base tables present.
   - **Any post-COMMIT FAIL → escalate immediately** (recovery via migration history/backup; should be impossible given dry-run + RESTRICT + pre-scan).

## Guardrails
- **Drop EXACTLY the listed set. `RESTRICT` only.** Touch no MUST-KEEP table, no `tcc.*` base table, no `sops_v2`, no app code.
- DSN out-of-band; no `.env*` contents. Scoped `git add` (the `004` migration + closeout).

## Closeout
Record: final pre-drop verification (DB + app + sequence = clean), dry-run result, apply result, the full post-drop gate table, and the catalog confirmation (dropped gone + must-keep present). Then `git mv` claimed→done, commit, push, return to Desktop. **On PASS, Decision-012 is COMPLETE — `tcc.*` stands alone as the unified TCC catalog; the legacy `public.tcc_*` / `work.tcc_relay_*` back-compat views + orphaned `_pre_rebuild` + `_v2` surfaces are retired.**
