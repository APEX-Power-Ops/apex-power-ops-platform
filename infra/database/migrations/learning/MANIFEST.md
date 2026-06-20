# learning migrations -- manifest

Learning / enablement lane. Dev DB: `learning_dev` (host PG17 `apex-dev-pg`). The baseline content
was loaded from a frozen prod dump (NOT migrations); this lane holds the **additive** Slice 2+ changes.
**Nothing here is applied to prod.** Objects live in the `public` schema (lane isolation = the database,
per separate-DB-per-lane D-ARCH-1). **`learning_dev` apply is an operator-gated `schema` step**
(see the Slice 2a plan); validation runs on the throwaway `learning_test`.

| # | Up | Down | What | Slice | Status |
|---|---|---|---|---|---|
| 001 | `001_person_bridge.sql` | `001_person_bridge_down.sql` | `public.user_profiles.employee_id` cross-DB contract-FK to prod `public.employees.id` (app-enforced, no DB FK; partial-unique). Mirrors `additive_person_spine_prod`. | 2a | validated on `learning_test` |
| 002 | `002_learning_events.sql` | `002_learning_events_down.sql` | append-only `public.learning_events` capture ledger (event_type CHECK vocab; FKs user CASCADE / study_content SET NULL; `neta_section` work-context; payload jsonb; UPDATE/DELETE-blocking trigger). | 2a | validated on `learning_test` |

## Test harness
`test_prereq.sql` creates minimal stub `user_profiles` + `study_content` (+ seed rows) so the throwaway
`learning_test` carries the tables the FKs reference. `conftest.py` applies it once per session.
Create the DB first: `psql -U postgres -c "CREATE DATABASE learning_test;"`. Run a migration test:
`LEARNING_TEST_PGPASSWORD=<pw> uv run --with "psycopg[binary]" --with pytest pytest test_001_person_bridge.py -q`.

## Conventions
- Each migration ships a reversible `_down`. Validation gate = down -> up -> invariant tests -> down clean on `learning_test`.
- Applying to `learning_dev` is a SEPARATE operator-approved `schema` gate (additive/idempotent).

## Deferred (later sub-slices)
2b: derive `user_study_progress` / `user_test_attempts` projections + management dashboards - 2c: ROI
correlation (learning_events -> records/ops field output via `employee_id` + NETA section).
