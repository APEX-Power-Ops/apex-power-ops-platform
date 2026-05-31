---
dispatch_id: 2026-05-30-cc-d012-phase2-expand-retry
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-d012-phase2-expand
closeout: ops/agents/handoffs/2026-05-30-d012-phase2-expand-retry-closeout.md
---

# Decision-012 Phase 2 (EXPAND) — RETRY after dry-run fix (two-phase manufacturer remap)

**Lane:** Decision-012 — Phase 2 EXPAND, retry. **Operator-authorized per-phase.** The prior dry-run (`2026-05-30-cc-d012-phase2-expand`) did its job: it **caught a real bug and rolled back cleanly** (prod untouched — `tcc` absent, original FKs intact). Follow the inbox lifecycle (claim-push BEFORE executing).

## What the prior dry-run caught + the fix
- **Failure:** `ERROR: duplicate key value violates unique constraint "tcc_brk_mccb_manufacturer_id_name_key"` during the D2 manufacturer remap (before `CREATE SCHEMA`/moves). These breaker tables carry a `UNIQUE(manufacturer_id, name)` key (not in the Phase-0 FK map). The remap is a monotonic +2/+4 id shift, so an in-place single UPDATE collides with a not-yet-shifted row mid-statement, even though the FINAL state is collision-free.
- **Verified safe final state:** both manufacturer tables have 450 distinct names (0 internal dups) and the id→canonical map is injective → the remapped `(manufacturer_id, name)` is provably unique. Only the *intermediate* state collided.
- **Fix (already committed):** `infra/database/migrations/tcc/001_tcc_schema_expand.sql` now does a **two-phase remap** — Phase A maps every row to a disjoint temp id-space (`+100000`, disjoint from real ids ≤454), Phase B brings it back to canonical — so no intermediate collision. A leak-guard asserts phase-A count == phase-B count. The DOWN migration got the symmetric fix.

## Execute (gated) — same validate-first flow
1. **Claim** (git mv pending→claimed, push) BEFORE running.
2. **Dry-run first** against prod (direct DSN, out-of-band): run the UP body in a transaction ending in `ROLLBACK` (`psql -v ON_ERROR_STOP=1 -X`). Confirm it now runs PAST the remap, through `CREATE SCHEMA tcc` + the 60 moves + back-compat views + all final guards, with NO error and sane `NOTICE` remap counts — persisting nothing.
3. **If the dry-run surfaces a NEW downstream surprise** (another unknown constraint, a view/function blocking a `SET SCHEMA`, a guard RAISE): **STOP and report to Desktop** with the exact message — do not edit the migration to force it through. (This is the loop working; we iterate.)
4. **Real run (only if dry-run clean):** apply UP with `COMMIT` against prod.
5. **Post-commit parity-gate (behavior must be UNCHANGED — routes hit back-compat views):**
   - `scripts/probe_live_etu_sql_parity.py` → PASS 3/0.
   - `scripts/probe_live_relay_sql_parity.py` → PASS 6/6.
   - breaker `catalog/status` (63/17,831) + a relay `sections` query → 200, real rows.
   - Any FAIL → run the DOWN migration, report, do not leave a half-state.

## Guardrails
- **Phase 2 ONLY** — no route/probe/test SQL repoint (Phase 3); no `_pre_rebuild`/`_v2`/view drops (Phase 4).
- DSN out-of-band; no `.env*` contents. Scoped `git add` (closeout only; the SQL is already committed).

## Closeout
Record: dry-run result (now full pass-through?), the remap NOTICE counts, committing-run result, the 4 post-commit checks, whether DOWN was needed, and any NEW surprise. Then `git mv claimed/ → done/`, commit, push, return to Desktop.
