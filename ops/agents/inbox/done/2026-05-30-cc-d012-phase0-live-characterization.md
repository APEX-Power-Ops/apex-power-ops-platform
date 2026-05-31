---
dispatch_id: 2026-05-30-cc-d012-phase0-live-characterization
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: autonomous-safe
predecessor: 2026-05-30-cc-hosted-breaker-resource-explorer
closeout: ops/agents/handoffs/2026-05-30-d012-phase0-live-characterization-closeout.md
---

# Decision-012 Phase 0 — live characterization (READ-ONLY) for the `tcc.*` schema unification

**Lane:** Decision-012 TCC schema unification — **Phase 0 of 5** (characterize-before-execute). **READ-ONLY: no DDL, no writes, no schema/data/route changes.** This produces the verified-live ground truth the detailed migration DDL will be authored against (my plan is grounded in a 2026-05-22 snapshot + repo grep — Phase 0 confirms reality). Plan: `apex-ops-substrate/.claude/PLATFORM/DECISION_012_TCC_SCHEMA_UNIFICATION_PLAN_2026-05-30.md`. Follow the inbox lifecycle (claim-push BEFORE executing).

## Deliverable A — live schema inventory (read-only via the read-only DSN)
Against the governed live Supabase (read-only pooler DSN, e.g. `APEX_OLARES_LIVE_DSN` — **do not print the DSN**):
1. **`public.tcc_*` full inventory by generation** — list every `public` table matching `tcc_%`, classify each as **base** / `_pre_rebuild` / `_v2`, with row count. (Confirms the "3 generations / carry base only" model.)
2. **FK landmine check** — for the breaker frame tables (`tcc_brk_iccb/mccb/pcb`, `tcc_emt`), report the ACTUAL FK target of `manufacturer_id` (is it `tcc_manufacturers_pre_rebuild` or `tcc_manufacturers`?), and confirm which `tcc_manufacturers*` the routes JOIN. Enumerate all FKs among the base TCC tables (so the move preserves them).
3. **`work.tcc_relay_*` inventory** — list the relay tables + row counts (cross-check vs the G-3 counts: relays 1442 / devices 6850 / ranges 34213 / tcp_points 1,570,700).
4. **Confirm `tcc` schema does NOT exist yet** (target is clear).
5. **Apparatus anchor existence** — does live have: an `apparatus` table (which schema? PK?), `seam.equipment_models` (populated? row count?), and the function `get_apparatus_resources(...)`? This determines whether Decision-010 anchor is "full FK now" vs "documented-deferred" (plan Decision B).

## Deliverable B — exhaustive repo enumeration of SQL reference sites (the Phase-3 repoint surface)
Grep the repo for EVERY site that references a TCC/relay catalog table (so Phase-3 scope is exact, not just `router.py`):
- `apps/control-plane-api/services/neta/router.py` (count by table; note unqualified-breaker vs `work.`-relay), the curve-family config dict, `_RELAY_WORK_SCHEMA_TABLES`, the `_relay_work_schema_tables_available`/`_ensure_relay_catalog_available` guard.
- `apps/control-plane-api/scripts/probe_live_etu_sql_parity.py` + `probe_live_relay_sql_parity.py` (+ matrices).
- tests (`apps/control-plane-api/tests/*`, `packages/calc-engine/tests/*`).
- ANY other consumer (mutation-seam, other apps, other scripts). Report a table → {file:line} reference map + total site count per lane.

## Deliverable C — characterization summary
A structured writeup: confirmed table list to carry (base breaker + relay), the FK map (with landmine resolution target), the apparatus-anchor disposition (full-FK-feasible vs deferred-recommended, with evidence), and the exact repoint-site count/inventory. Flag any surprise vs the plan's repo-fact assumptions (e.g., a generation that's actually route-used, a hidden consumer, a missing expected table).

## Verify / Guardrails
- **READ-ONLY.** No `CREATE`/`ALTER`/`DROP`/`INSERT`/`UPDATE`/`COPY`. No route/schema/data/test changes. (A throwaway read-only characterization script is fine; do not commit data dumps with sensitive content.)
- Do NOT print DSN values; do NOT read `.env*`/credential files for contents.
- Scoped `git add` (only the closeout + any read-only helper script, if kept).

## Closeout
Record Deliverables A/B/C (inventory + FK map + apparatus-anchor disposition + repoint-site inventory + any surprises). Then `git mv claimed/ → done/`, commit, push, return to Desktop. **This unblocks Phase 1 (design finalize) — Desktop authors the exact `tcc.*` DDL against this ground truth; no live DDL runs until the plan's Decisions A/B are ratified and Phase 2 is per-phase authorized.**
