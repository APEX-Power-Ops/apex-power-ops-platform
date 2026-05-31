---
dispatch_id: 2026-05-30-cc-d012-phase4-characterization
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-d012-phase3-relay-repoint
closeout: ops/agents/handoffs/2026-05-30-d012-phase4-characterization-closeout.md
---

# Decision-012 Phase 4 — CHARACTERIZATION (read-only; produces the safe drop-set + repoint plan)

**Lane:** Decision-012, Phase 4 prep. **READ-ONLY — absolutely no DDL, no drops, no repoints.** Phase 3 is complete: the app reads `tcc.*` and the 60 back-compat views have zero app consumers. Phase 4 is the **irreversible** cleanup (repoint the remaining DB object bodies, then drop the back-compat views + `_pre_rebuild`/`_v2`). Before any drop, this dispatch produces the precise, evidence-backed plan. Use a read-only transaction (`BEGIN READ ONLY` / pure `SELECT` over `pg_catalog`/`information_schema`). Follow the inbox lifecycle (claim-push BEFORE running).

## Why read-only first
The drop is the point of no easy return (once `_pre_rebuild` is gone, the Phase-2 DOWN's name-based reverse-remap can't resolve). We do not guess the drop-set — we derive it from live dependency evidence, then Desktop authors the migration and we gate the irreversible step.

## Produce (report each as a section in the closeout)

1. **Back-compat view drop-set (the 60).** Enumerate all old-name views — 39 `public.tcc_*` + 21 `work.tcc_relay_*`. For EACH, list any remaining references from **other DB objects** (functions, views, matviews, triggers, rules, defaults, constraints) via `pg_depend`/`pg_get_functiondef`/`pg_views`. (App refs are already zero — Phase 3.) Goal: confirm each view is droppable once the step-2 bodies are repointed.

2. **DB object bodies still referencing OLD names (the 4a repoint targets).** Re-scan ALL functions/procedures/views/matviews/triggers/rules in `public` (and any schema) whose body references any old breaker/relay name (`tcc_<breaker>` unqualified, `public.tcc_*`, `work.tcc_relay_*`, bare `tcc_relay*`). Confirm the 3 known breaker objects (`fn_calculate_test_currents` → `tcc_etu_stpu_overrides`; `fn_sensor_available_settings` → 8 etu tables; `vw_trip_unit_cascade` → `tcc_manufacturers_pre_rebuild`) and **find any others**. For each: object name, the exact old name(s) it references, and the `tcc.*` target each should repoint to.

3. **`vw_trip_unit_cascade` deep-dive (the ⚠).** It references `tcc_manufacturers_pre_rebuild` (the OLD pre-rebuild manufacturers, which per the D2 finding carry different attributions than canonical). Determine: (a) is it referenced by any application route (grep `apps/`) or any other DB object? (b) does it expose manufacturer fields sourced from `_pre_rebuild`? (c) would repointing it to canonical `tcc.manufacturers` (join by name or id?) CHANGE its output — i.e. is it currently mis-attributing manufacturers? Give a concrete recommendation: **repoint-to-canonical** (and whether that's a behavior fix) **vs drop** (if unused). Include a small sample query showing current vs canonical-mapped manufacturer for a few rows if feasible.

4. **`_pre_rebuild` disposition (the careful one).** List ALL `*_pre_rebuild` tables. For EACH, enumerate inbound FKs + view/function references (`pg_depend` + body scan). Split into:
   - **MUST-KEEP** — still referenced by a surviving object. Per D1, `tcc_test_plans`/`tcc_test_results` stay in `public` and keep their `_pre_rebuild` **ETU** FKs → those specific `_pre_rebuild` ETU tables CANNOT be dropped. Plus `tcc_manufacturers_pre_rebuild` if `vw_trip_unit_cascade` (or anything) still needs it after step-3's decision.
   - **SAFE-TO-DROP** — orphaned (no inbound FK, no DB-object reference, no app reference).
   Report the exact two sets with the reason per table.

5. **`_v2` disposition.** List `*_v2` tables (Phase 0 said ~1, "partial abandoned rebuild, unused"). Confirm zero references (app grep + DB `pg_depend`/body scan). Recommend drop or keep with evidence.

6. **Proposed Phase-4 execution plan (recommendation for Desktop to author).** Lay out the safe ordering:
   - **4a** — repoint the step-2 DB object bodies → `tcc.*` (+ the step-3 `vw_trip_unit_cascade` decision). Reversible (restore old defs).
   - **4b** — drop the 60 views + the step-4 SAFE-TO-DROP `_pre_rebuild` set + the step-5 `_v2` set. Irreversible.
   Note any ordering constraints (e.g. drop views before/after which objects), any object that blocks a drop, and anything ambiguous that needs a Desktop/operator decision.

## Guardrails
- **READ-ONLY.** No `DROP`, `ALTER`, `CREATE`, `UPDATE` — pure inspection. If any step would require a write to verify, describe it instead of doing it.
- DSN out-of-band; no `.env*` contents. No app code changes. Scoped `git add` (closeout only).

## Closeout
The 6 sections above, each evidence-backed (counts, object names, FK lists, sample rows where noted), ending with the explicit **SAFE-TO-DROP set** + **MUST-KEEP set** + **4a repoint map** + any flagged decisions. Then `git mv` claimed→done, commit, push, return to Desktop. Desktop will author the 4a + 4b migrations from this; the irreversible 4b drop will be gated with a final pre-drop verification.
