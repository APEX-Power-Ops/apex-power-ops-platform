---
dispatch_id: 2026-05-30-cc-d012-phase2-expand-rerun
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: 2026-05-30-cc-d012-relay-guard-view-aware
closeout: ops/agents/handoffs/2026-05-30-d012-phase2-expand-rerun-closeout.md
---

# Decision-012 Phase 2 (EXPAND) — RE-RUN now that the relay guard is view-aware

**Lane:** Decision-012, Phase 2 EXPAND, third run. **Operator-authorized per-phase.** Two prior runs each cleared a blocker via the validate ladder (never a persisted half-state): dry-run #1 caught a `UNIQUE(manufacturer_id,name)` collision → fixed with a two-phase remap; the retry's UP committed clean but the post-commit gate caught a relay 503 from a view-blind route guard → DOWN restored prod. **That guard is now view-aware** (`_relay_work_schema_tables_available` unions `get_view_names`, commit `8fdc7fd7`, deployed + non-regression-verified). With it live, EXPAND's back-compat views satisfy the relay guard, so the post-commit relay checks should now pass. Follow the inbox lifecycle (claim-push BEFORE executing).

## What changed since the retry
- The migration SQL is **unchanged and already committed** (`infra/database/migrations/tcc/001_tcc_schema_expand.sql` UP + `..._down.sql` DOWN — the two-phase remap fix from §77). Do NOT re-edit it.
- The ONLY new thing is the deployed view-aware relay guard. So the dry-run should behave exactly as the retry's did (full pass-through), and the post-commit gate should now additionally pass relay.

## Execute (gated) — same validate-first flow

1. **Claim** (`git mv` pending→claimed, commit, push) BEFORE running.

2. **Dry-run first** against prod (direct DSN, out-of-band): run the UP body in a transaction ending in `ROLLBACK` (`psql -v ON_ERROR_STOP=1 -X`). Confirm it again runs cleanly through the two-phase remap → `CREATE SCHEMA tcc` → 60 moves → back-compat views → final guards, persisting nothing. (Expected remap counts: iccb 29 / mccb 599 / pcb 157 / emt 174 / trip_types 559.) Any error → STOP + report.

3. **Deploy-sanity (pre-commit):** immediately before the real commit, confirm the view-aware guard build is live by checking the hosted relay route is currently 200:
   - `GET https://control.apexpowerops.com/api/v1/neta/relay/sections` → 200.
   This is a base-table-state check (it passes with old or new guard), but it confirms the service is healthy right before you commit. (Positive proof of the view path comes from the post-commit relay gate below.)

4. **Real run (only if dry-run clean):** apply UP with `COMMIT` against prod.

5. **Post-commit parity-gate — relay MUST now pass (this is the integration proof of the view-aware guard over back-compat views):**
   - `scripts/probe_live_etu_sql_parity.py` → PASS 3/0.
   - `scripts/probe_live_relay_sql_parity.py` → **PASS 6/6** (previously 503 — must be green now).
   - breaker `catalog/status` → 200, `{63, 17831}`.
   - relay `sections` → **200**, real rows (previously 503).
   - **If relay still 503:** the most likely cause is that Render had not yet deployed `8fdc7fd7` at commit time (not a logic error — the unit tests prove the union logic). Re-poll `relay/sections` ONCE after ~90s. If it flips to 200, re-run the two relay gate checks. If still 503 after the re-poll, run the **DOWN** migration (`..._down.sql`), report "relay 503 persisted — suspected guard build not live", and STOP (we'll confirm the deploy and re-dispatch).
   - **Any OTHER failure** → run DOWN, report, do not leave a half-state.

6. **On full gate PASS:** EXPAND is LIVE. Record the post-commit verification table.

## Guardrails
- **Phase 2 ONLY** — no route/probe/test SQL repoint (Phase 3); no `_pre_rebuild`/`_v2`/view drops (Phase 4).
- DSN out-of-band; no `.env*` contents. Scoped `git add` (closeout only; the SQL + guard are already committed).

## Closeout
Record: dry-run result + remap NOTICE counts, deploy-sanity result, committing-run result, the 4 post-commit checks (esp. whether relay is now PASS), whether the 90s re-poll or DOWN was needed, and any new surprise. Then `git mv` claimed→done, commit, push, return to Desktop. **On PASS, `tcc.*` is live behind back-compat views — Phase 3 (route SQL repoint, parity-gated) is the next lane.**
