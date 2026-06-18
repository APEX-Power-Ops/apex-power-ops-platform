# jobs Domain SQL Migration Manifest
## Lane: APEX platform orchestration (Chip 3 / D-ARCH-3) — the apex-jobs task bus
## Target: `orchestration_dev` (host PG17 dev-pg, 127.0.0.1:5432), role `orchestration`

The `jobs` schema is the DB-backed upgrade of the file-based `ops/agents/inbox`
dispatch queue: a durable queue (`jobs.job`) + run/promotion ledger (`jobs.run`)
+ human-approval gates (`jobs.gate`), consumed by the `packages/apex-jobs`
engine / CLI / worker.

## Execution order (psql -f, in order)

| # | File | Contents |
|---|------|----------|
| 1 | `001_jobs_enums.sql` | `jobs` schema + 6 enums (executor / authority / env / job_status / run_status / gate_state) |
| 2 | `002_jobs_tables.sql` | `job` (queue item) / `run` (ledger) / `gate` (approvals) + constraints (unique dispatch_id, self-FK predecessor, run.env CHECK in (sandbox,host), unique(job_id,attempt)) |
| 3 | `003_jobs_indexes.sql` | status / priority(+dispatch_id) / predecessor / run.job / gate.job + partial open-gate index |
| 4 | `004_jobs_views.sql` | `v_eligible` — claimable jobs (pending, predecessor succeeded-or-null, no open gate) in (priority, dispatch_id) order |

Each file has a matching `_down.sql` applied in reverse order. `001_jobs_enums_down.sql`
drops the schema CASCADE (removing enums + tables in one shot).

## Tests
- `test_001_jobs_schema.py` — schema + 6 enums + 3 tables + unique/self-FK + down reverses (3 tests)
- `test_004_jobs_eligibility.py` — `v_eligible` status/predecessor/open-gate exclusions + ordering (4 tests)
- Engine / CLI / worker tests: `packages/apex-jobs/tests/` (11 more; run against `orchestration_test`).

Run (host) per the records convention:
```
uv run --with "psycopg[binary]" --with pytest pytest test_001_jobs_schema.py
```
The harness pins `orchestration_test` explicitly and uses the host `/usr/bin/psql`
for apply (client 16.x is fine vs the PG17 server for `-f`; only `\l`/`\du`-style
describe meta-commands hit the renamed-catalog skew). No Windows-path assumptions.

## Apply to a database
```
for f in 001_jobs_enums 002_jobs_tables 003_jobs_indexes 004_jobs_views; do
  PGPASSWORD=$DEV_PG_PASSWORD psql -h 127.0.0.1 -p 5432 -U orchestration \
    -d orchestration_dev -v ON_ERROR_STOP=1 -f $f.sql
done
```
