# PM Lane 282 - Project Miner Temp Power Production Tracking Baseline Live Admission

## Decision

Jason's 2026-05-18 standing PM blocker authority is accepted as stakeholder authority for the next predetermined post-durable-field-record blocker: production tracking baseline admission.

PM Lane 282 clears that blocker by adding a dedicated insert-only production tracking record seam and persisting one deterministic zero-actual Temp Power baseline record. It does not admit nonzero production quantities, labor entries, apparatus progress updates, customer reporting, or finance outputs.

## Preconditions

- PM Lane 277 approval row reads back as `approved_for_import_packet`.
- PM Lane 278 import reads back as `classification=imported`, `current_candidate_match=true`, and `counts_match=true`.
- PM Lane 279 field authorization/assignment reads back as 184 assignments for 184 unique imported apparatus rows.
- PM Lane 280 schedule/status readiness reads back as 15 tasks `ready`, 184 apparatus `ready`, 7 workpackages `not_started`, 184 assignments, and 0 issues.
- PM Lane 281 durable field record reads back as `durable_field_recorded`, `record_count=1`, and `production_quantity_count=0`.
- No production tracking baseline route or table existed before PM Lane 282.

## Schema And Routes

Schema:

- migration: `apps/mutation-seam/migrations/005_pm_lane_282_production_tracking_records.sql`
- table: `seam.production_tracking_records`
- insert-only update/delete rejection triggers
- RLS enabled
- guarded revoke for `anon`/`authenticated` roles when present

Routes:

- `POST /api/v1/mutations/production-tracking`
- `GET /api/v1/reads/production-tracking-status`
- `GET /api/v1/reads/production-tracking-records`

The route requires:

- actor role: `lead`
- source: `online`
- mutation class: `B`
- project scope containing `pm-import-project-miner-temp-power`

## Result

Hosted write:

- first POST status: `accepted`
- replay POST status: `idempotent_hit`
- mutation: `mut-fcbdadd0-aa51-4fd3-9f36-ce55721189cf`
- audit: `audit-ce7cdcb5-a032-49b3-9059-d3f4975a25a4`
- record count after replay: `1`

Hosted readback from both direct mutation-seam and operations-web:

- classification: `production_tracking_baseline_recorded`
- production tracking record id: `pm-lane-282-production-tracking-temp-power-2026-05-18`
- project id: `pm-import-project-miner-temp-power`
- source import candidate: `pm-import-candidate-miner-temp-power`
- source import fingerprint: `e111fdbe934bf9de07ed24c1`
- field authorization record: `pm-lane-279-field-auth-temp-power-2026-05-18`
- schedule status record: `pm-lane-280-status-readiness-temp-power-2026-05-18`
- durable field record: `pm-lane-281-durable-field-record-temp-power-2026-05-18`
- production tracking authority: `admitted_by_pm_lane_282_zero_actual_baseline`
- customer reporting authority: `not_admitted`
- finance authority: `not_admitted`
- production quantity count: `0`
- labor entry count: `0`
- actual labor hours: `0.00`
- apparatus progress count: `0`
- progress update count: `0`

## Schema Recovery Note

Hosted preflight initially returned `UndefinedTable` for `seam.production_tracking_records`. The local `.env` targets local `apex_pm_stage`, the bounded Supabase migration tool was disabled by server env, and the Olares governed live DSN loader returned stale session-pooler password material.

Commit `5c5e9b37` added a narrow runtime schema-ensure fallback that applies the exact committed migration 005 through the existing app database connection only if this Lane 282 table is missing. After deploy, hosted pre-write status returned `no_production_tracking_record`, `storage_available=true`, `record_count=0`, and durable field record count `1`.

No secret value was printed, stored, or committed.

## Validation

Hosted:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com
```

Results:

- deployed mutation-seam smoke: `RESULT PASS`
- hosted PM intake smoke: `PM_INTAKE_HOSTED_SUMMARY failed=0`
- hosted routes smoke: `SMOKE_SUMMARY failed=0 passed=12`

Local:

- focused persistence tests: `24 passed`
- `py_compile`: passed
- packet JSON parsed successfully
- scoped `git diff --check`: passed

## Boundary

PM Lane 282 created only the zero-actual production tracking baseline record plus the schema, route, readback, tests, and smoke coverage required for that record.

Still blocked:

- nonzero production quantity writes
- labor entry or actual labor hour writes
- apparatus progress or progress update writes
- field evidence attachment storage
- customer report, completion evidence, or customer commitment
- billing, payroll, invoice, accounting, or external finance output
- source workbook/PDF writeback
- workbook macros
- new service, DNS, auth, ingress, or secret changes

## Next Blocker

`STOPPED_AWAITING_CUSTOMER_REPORTING_COMPLETION_EVIDENCE_ADMISSION_PACKET_AFTER_PRODUCTION_TRACKING`
