# TCC Phase G-3 Relay Live Population Closeout

Dispatch: `2026-05-30-cc-tcc-phase-g3-relay-live-population`
Executor: Codex
Date: 2026-05-30
Status: Initially STOPPED by governed preflight; completed after operator-approved live DDL follow-up.

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

## Operator-Approved Continuation

After the initial STOP closeout was pushed, the operator explicitly authorized the missing live DDL prerequisites in chat:

- `CREATE SCHEMA work`
- `CREATE TYPE work.provenance_source_enum`
- `CREATE TYPE work.provenance_status_enum`
- all enum blockers required by the relay schema

Applied live DDL/results:

| Step | Result |
| --- | --- |
| `CREATE SCHEMA work` | succeeded; `work_schema_count=1`, `pg_namespace` contains `work` |
| `work.provenance_source_enum` | created with labels `manual,p6_import,api,automation,migration,bulk_upload` |
| `work.provenance_status_enum` | created with labels `curated,imported,provisional,validated,rejected` |
| relay-local enum blockers | already present from the partial `010` attempt: `relay_range_parent_kind_enum`, `relay_voltage_restraint_kind_enum` |

The first replay attempt of `010_tcc_relay_tables.sql` had created the two relay-local enums, then stopped because the PM/work provenance enum dependency was absent. After the operator-approved enum DDL, the live relay table state was still clean: 21 relay tables absent / 0 relay rows loaded. To avoid dropping the already-created relay enum objects, the remaining table body of `010_tcc_relay_tables.sql` was applied from the canonical file after its enum block, then `011_tcc_relay_indexes.sql` was applied normally.

`012_tcc_relay_staged_population.sql` initially stopped during `\copy` on `Relays.csv` with `invalid byte sequence for encoding "UTF8": 0x96`. The tracked CSV snapshot is extended-ASCII/Windows-1252 for that file, so the migration was rerun unchanged with `PGCLIENTENCODING=WIN1252`. `012` is designed to truncate/reload only `work.tcc_relay_*`; the rerun completed successfully.

Final live relay counts:

| Metric | Count |
| --- | ---: |
| relay tables | 21 |
| relays | 1,442 |
| devices | 6,850 |
| ranges | 34,213 |
| TCP points | 1,570,700 |

Hosted runtime verification:

- `GET https://control.apexpowerops.com/api/v1/neta/relay/sections?q=SEL` returned HTTP `200` with relay data.
- Hosted discovery/settings/preview probe returned HTTP `200` end to end using TD-section `5075`; preview meta status was `supported` and one curve was returned.

Live integration test result:

- Command: `PYTHONPATH=../../packages/calc-engine/src:. .venv/bin/python -m pytest tests/test_neta_relay_live_integration.py -q -rs`
- Result: `1 skipped, 1 warning`
- Skip reason: the test selects first supported section `82782`, which has no stored preview options. This is no longer the previous table-absence skip. A manual sample showed subsequent supported sections do expose preview options, including `5075`, `30154`, `30148`, `5078`, `30156`, `30706`, `5084`, `5085`, and `5171`.

Final live DB write boundary:

- touched `work` schema creation, the two required PM/work provenance enums, relay-local enums, and `work.tcc_relay_*` relay tables/indexes/data
- did not change PM/breaker/ETU data, app code, routes, or tracked source snapshot files
