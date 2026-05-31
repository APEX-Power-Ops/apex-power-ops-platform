---
dispatch_id: 2026-05-30-cc-d012-phase2-expand
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-d012-phase0-live-characterization
closeout: ops/agents/handoffs/2026-05-30-d012-phase2-expand-closeout.md
---

# Decision-012 Phase 2 (EXPAND) — create `tcc.*`, move catalog, back-compat views (non-destructive)

**Lane:** Decision-012 TCC schema unification — **Phase 2 of 5 (EXPAND).** **Operator authorization required per-phase — this is the FIRST live-prod DDL of the migration.** Plan: `apex-ops-substrate/.claude/PLATFORM/DECISION_012_TCC_SCHEMA_UNIFICATION_PLAN_2026-05-30.md` (§4, §8). Follow the inbox lifecycle (claim-push BEFORE executing).

## Artifacts (authored by Desktop, in-repo)
- **UP:** `infra/database/migrations/tcc/001_tcc_schema_expand.sql` — single transaction: precondition guards → manufacturer name-based remap (D2, live-verified) → `CREATE SCHEMA tcc` → move+rename the 60 carry tables (39 base breaker from `public` + 21 relay from `work`; drop the `tcc_` prefix) → re-add manufacturer FKs to `tcc.manufacturers` → back-compat VIEWS at the old `public.tcc_*` / `work.tcc_relay_*` names → final guards.
- **DOWN:** `infra/database/migrations/tcc/001_tcc_schema_expand_down.sql` — full reverse (incl. reversing the remap), single transaction.

## What it does / why it's safe
- **Non-destructive + reversible:** nothing is dropped. `public.tcc_*` and `work.tcc_relay_*` survive as **views over `tcc.*`**, so routes (unqualified `public` + qualified `work.`), the views (`vw_sensor_calc_context`, `vw_trip_unit_cascade`) and functions (`fn_sensor_available_settings`, `fn_calculate_test_currents`, `fn_evaluate_test_results`) keep working **with no route change**. Route repoint is Phase 3; view + `_pre_rebuild`/`_v2` drop is Phase 4.
- **Atomic:** one transaction; any guard `RAISE` rolls the whole thing back (prod untouched). `SET SCHEMA`/`RENAME` are metadata-only → fast even on `tmt_curves` (1.1M) / `relay_curve_points_tcp` (1.57M).
- **D2 remap is the only data change** and is live-verified (189-mfr renumber, 0 orphan/0 ambiguous); a post-remap guard halts if any `manufacturer_id` fails to resolve in canonical.

## Execute (gated)
1. **Claim** (git mv pending→claimed, push) BEFORE running.
2. **Validate first — pick the safe isolation:**
   - **Preferred:** a Supabase **test branch** with data, if available → run UP, confirm clean + guards pass, run the parity probes against the branch (must stay green).
   - **Otherwise:** an **on-prod dry-run** — run the UP body inside a transaction that ends in `ROLLBACK` (execute against real data, confirm all guards pass + `NOTICE` remap counts look sane, persist NOTHING). Run during low catalog traffic (brief `ACCESS EXCLUSIVE` locks). Use the **direct DSN** (port 5432) out-of-band; do not print it.
3. **Real run (only if validation clean):** apply UP with `COMMIT` against prod (direct DSN).
4. **Post-commit gate — behavior must be UNCHANGED** (routes still hit the back-compat views):
   - `scripts/probe_live_etu_sql_parity.py` → still PASS 3/0.
   - `scripts/probe_live_relay_sql_parity.py` → still PASS 6/6.
   - breaker `catalog/status` (63/17,831) + a relay `sections` query → still 200 with real rows.
   - If any FAIL: run the DOWN migration and report — do not leave a half-state.

## Guardrails
- **Phase 2 ONLY** — do NOT repoint any route/probe/test SQL (that's Phase 3); do NOT drop `_pre_rebuild`/`_v2` or the back-compat views (Phase 4).
- Read-only against credentials; DSN out-of-band; no `.env*` contents. Scoped `git add` (closeout only — the SQL is already committed).
- If the UP guards `RAISE` on the dry-run (e.g. an unexpected FK/constraint name, a count mismatch, the carry-set check), **STOP and report to Desktop** with the exact message — do not edit the migration to force it through.

## Closeout
Record: isolation used (branch vs dry-run); dry-run guard/NOTICE output; committing-run result; the 4 post-commit checks (ETU parity / relay parity / breaker catalog / relay sections); whether DOWN was needed. Then `git mv claimed/ → done/`, commit, push, return to Desktop. **This lands the `tcc.*` schema with the app still green via back-compat views; Phase 3 (route repoint + parity-gate) is the next dispatch.**
