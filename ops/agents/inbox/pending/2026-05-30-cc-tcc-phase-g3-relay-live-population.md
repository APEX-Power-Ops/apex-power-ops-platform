---
dispatch_id: 2026-05-30-cc-tcc-phase-g3-relay-live-population
target: CC
priority: 1
from: Desktop
created_at: 2026-05-30
authority: gated
predecessor: null
closeout: ops/agents/handoffs/2026-05-30-tcc-phase-g3-relay-live-population-closeout.md
---

# TCC Phase G-3 — populate relay work-schema in the governed live Supabase

**Lane:** TCC Runtime 017 (matrix #83), Phase G-3 (relay-hosted-live). **Operator authorization: GRANTED 2026-05-30.** This is the campaign's **first governed-live-DB WRITE** — additive only, isolated to `work.tcc_relay_*`. Follow the inbox lifecycle (claim-push BEFORE executing).

## Goal
The deployed relay routes return 503 because `work.tcc_relay_*` is absent from the governed Supabase. The schema + the full 1.57M-row population already exist as replayable migrations; this dispatch applies them to prod so `/relay/*` flips 503→200.

## Source of truth (Desktop-verified)
- Migrations in `infra/database/migrations/work/`: `010_tcc_relay_tables.sql` (schema + enums), `011_tcc_relay_indexes.sql`, `012_tcc_relay_staged_population.sql` (a psql `\copy` replay from the tracked snapshot CSVs at `infra/database/source-lineage/tcc-relay/stdlib-relay-snapshot-001/data/`).
- Desktop confirmed the identical slice in local staging `apex_pm_stage`: **21 relay tables; relays 1442, devices 6850, ranges 34213, tcp_points 1,570,700.** Prod must match these.

## Connection (out-of-band — CRITICAL)
- Target = the **governed live Supabase that `control.apexpowerops.com` connects to** (the SAME project Render uses — confirm; applying to a different project will "succeed" but leave the prod 503 in place).
- **Use the DIRECT write DSN, from the dedicated host key `ai-direct-dsn.env`:** `source /home/olares/apex-secrets/olares/ai-direct-dsn.env` → exposes `$APEX_OLARES_DIRECT_DSN` (direct, port 5432, write-capable).
- **Do NOT use the pooler key** (`ai-live-dsn.env` / `APEX_OLARES_LIVE_DSN`, port 6543) — `012`'s `\copy` needs a real session the pooler can't hold. If `ai-direct-dsn.env` is missing or stale after the recent rotation, STOP and request it (operator stages it out-of-band; never print or commit the value).

## Steps (psql, from the repo's `infra/database/migrations/work/` directory)
0. **Set up:** `source /home/olares/apex-secrets/olares/ai-direct-dsn.env` (→ `$APEX_OLARES_DIRECT_DSN`), then `cd` into `infra/database/migrations/work/`. Every psql call below connects via `psql "$APEX_OLARES_DIRECT_DSN" …`.
1. **Pre-flight (read-only):**
   - `SELECT count(*) FROM information_schema.schemata WHERE schema_name='work';` → want **1**.
     - If **0** → STOP, surface to Desktop (the `work` schema / PM base isn't on prod; needs `CREATE SCHEMA work;` first).
   - `SELECT count(*) FROM information_schema.tables WHERE table_schema='work' AND table_name LIKE 'tcc_relay%';` → want **0**.
     - If **>0** → STOP, surface (already partially populated).
2. **Apply (the write), in order:**
   - `psql "$APEX_OLARES_DIRECT_DSN" -v ON_ERROR_STOP=1 -f 010_tcc_relay_tables.sql`
   - `psql "$APEX_OLARES_DIRECT_DSN" -v ON_ERROR_STOP=1 -f 011_tcc_relay_indexes.sql`
   - `psql "$APEX_OLARES_DIRECT_DSN" -v ON_ERROR_STOP=1 -f 012_tcc_relay_staged_population.sql`  (~1.57M rows; a few minutes)
3. **Verify (read-only):** relay_tables = 21; relays 1442, devices 6850, ranges 34213, tcp_points 1,570,700 (match local).

## Guardrails
- `010`/`011` are **first-apply-only** (plain `CREATE TYPE/TABLE/INDEX`) — if they error "already exists," STOP (partial prior apply). `012` **is re-runnable** (it truncates only `work.tcc_relay_*`, then reloads).
- **Additive + isolated**: touches only `work.tcc_relay_*` + `work.relay_*` enums. No PM/breaker/ETU data, no other schema, no app/code/route change, no migration to any other table.
- Scoped, out-of-band DSN; read nothing else into the write.

## Post-apply verification (the payoff)
- `GET https://control.apexpowerops.com/api/v1/neta/relay/sections?q=SEL` → **HTTP 200** with relay data (was 503). Runtime table-presence check — no redeploy needed; it flips the moment the tables exist.
- Relay live-integration now **runs** instead of skipping: `pytest apps/control-plane-api/tests/test_neta_relay_live_integration.py -q -rs` (DSN set) → passes, not skipped.

## Closeout
Record pre-flight numbers, the apply result, the verify counts, and the prod 503→200 confirmation. Then `git mv claimed/ → done/`, commit, push. Return to Desktop — that closes G-3 and the entire TCC campaign.
