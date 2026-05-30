# TCC Phase G-3 Relay Live Population Closeout

Dispatch: `2026-05-30-cc-tcc-phase-g3-relay-live-population`
Executor: Codex
Date: 2026-05-30
Status: STOPPED by governed preflight; no live write performed.

## Claim

- Claim commit pushed: `3ab9f74a` (`claim: 2026-05-30-cc-tcc-phase-g3-relay-live-population by codex`)
- `psql` prerequisite was absent on this host and was installed as a host package only:
  - `postgresql-client` / `psql (PostgreSQL) 16.14`
  - No repo dependency files were changed for this prerequisite.

## DSN Guard

The direct write DSN was sourced from:

- `/home/olares/apex-secrets/olares/ai-direct-dsn.env`
- variable: `APEX_OLARES_DIRECT_DSN`

The pooler/read DSN was compared only by parsed metadata from:

- `/home/olares/apex-secrets/olares/ai-live-dsn.env`
- variable: `APEX_OLARES_LIVE_DSN`

No DSN value or password was printed. Parsed metadata showed both DSNs target the same Supabase project ref, `fxoyniqnrlkxfligbxmg`, with password material present. The direct DSN resolves to the direct project host on port 5432; the pooler DSN resolves to the Supabase pooler host for the same project.

## Preflight

Read-only preflight was run against the direct DSN from `infra/database/migrations/work/`.

Required guard results:

| Check | Expected | Actual | Result |
| --- | ---: | ---: | --- |
| `information_schema.schemata` where `schema_name='work'` | 1 | 0 | STOP |
| existing `work.tcc_relay%` tables | 0 | 0 | OK |

Additional read-only sanity check:

| Probe | Result |
| --- | --- |
| `current_database()` | `postgres` |
| `current_user` | `postgres` |
| `current_schema()` | `public` |
| `pg_namespace` contains `work` | `false` |

The missing `work` namespace confirms this was not only an `information_schema` visibility issue. The dispatch explicitly required STOP when the work schema count is 0.

## Apply Result

No migration was applied.

Skipped, by guard:

- `010_tcc_relay_tables.sql`
- `011_tcc_relay_indexes.sql`
- `012_tcc_relay_staged_population.sql`

No governed live DB writes were performed. No `work.tcc_relay_*`, relay enum, PM, breaker, ETU, app-code, or route changes were made.

## Post-Stop Public Check

The public relay route remains unavailable, matching the missing-table condition:

- `GET https://control.apexpowerops.com/api/v1/neta/relay/sections?q=SEL`
- HTTP status: `503`
- Response detail: `relay catalog unavailable: work-schema tables not present`

Relay live integration was not run after the STOP because the preflight prevented population and the route still reports the expected unavailable state.

## Required Follow-Up

Create or restore the governed live `work` schema / PM base for the same Supabase project, then rerun the G-3 relay population packet from the preflight step.
