---
dispatch_id: 2026-05-29-cc-tcc-phase-f-validation-surface
target: CC
priority: 1
from: Desktop
created_at: 2026-05-29
authority: gated
predecessor: 2026-05-29-cc-tcc-phase-e3-demo-facet-wiring
closeout: ops/agents/handoffs/2026-05-29-tcc-phase-f-validation-closeout.md
---

# TCC Runtime 017 Phase F — end-to-end validation surface

**Lane:** TCC Runtime 017 (matrix #83), Phase F per `ops/agents/handoffs/2026-05-28-tcc-runtime-017-remaining-end-to-end-task-list.md` §3.F. **Predecessor:** E3 (`2026-05-29-cc-tcc-phase-e3-demo-facet-wiring`) must be in `done/` first.

## DB posture — DECIDED (read this first)
The live-integration + family-smoke surfaces run against the **governed Supabase** via the `APEX_OLARES_LIVE_DSN` env var (the same read-only DSN used for the ETU parity probe / live cutover). **Do NOT stand up a local Postgres**, and do NOT rely on `localhost:5432`. Rationale: there is no faithful local mirror; Supabase IS the accurate DB; these tests are **strictly read-only** (GET + plot-compute, no writes), so pointing them at the governed DB is safe and is what "live integration" means. Set the DSN **out-of-band** in the test environment (never commit it; watch the stale-`.env`-shadow trap from matrix #83). If isolation from production is ever wanted later, the path is a Supabase **test branch**, not a local PG.

## Run the full validation surface
1. **Offline route tests** (no DB): ETU demo/search/cascade + the new TMT/EMT facet route tests — green from the repo-local `.venv`.
2. **Live-integration** (DSN set): `test_neta_tmt_live_integration.py` + `test_neta_emt_live_integration.py` (+ any ETU live-integration) against Supabase — confirm they **actually run** (not skip — the data is present) and pass the search → context → settings → plot surface.
3. **Family smoke:** `scripts/smoke_local_neta_family_routes.py --base-url http://127.0.0.1:8010` against the DSN-backed local host — all families.
4. **ETU live SQL parity probe:** `scripts/probe_live_etu_sql_parity.py --base-url http://127.0.0.1:8010` still **3 pass / 0 warn** (no regression from E1/E2/E3).
5. **E3 browser proof** green (from E3's closeout).

## Acceptance
All five agree (route + live-integration + smoke + parity + browser). Record each surface's result. **No hosted-parity claim** — that's Phase G (a separate operator-gated decision after F is green).

## Guardrails
- **Read-only against Supabase** — no writes/migrations from these tests.
- DSN out-of-band; never printed/committed.
- Local-commit + push at closeout (inbox protocol).

## Closeout
Write the closeout to the `closeout:` path; record each surface's result + confirm the DB posture (Supabase-via-DSN, no local PG). Then `git mv` this dispatch `claimed/` → `done/`, commit, push. Return to Desktop for the Phase G (hosted) decision.
