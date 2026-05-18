# PM Lane 281 - Project Miner Temp Power Durable Field Record Live Admission

## Decision

Jason's 2026-05-18 standing PM blocker authority is accepted as stakeholder authority for the next predetermined post-schedule/status blocker: durable field record admission.

PM Lane 281 clears that blocker by adding a dedicated insert-only durable field record seam and persisting one deterministic Temp Power field-start readiness record. It does not admit production quantity capture, field evidence attachment storage, customer reporting, or finance outputs.

## Preconditions

- PM Lane 277 approval row reads back as `approved_for_import_packet`.
- PM Lane 278 import reads back as `classification=imported`, `current_candidate_match=true`, and `counts_match=true`.
- PM Lane 279 field authorization/assignment reads back as 184 assignments for 184 unique imported apparatus rows.
- PM Lane 280 schedule/status readiness reads back as 15 tasks `ready`, 184 apparatus `ready`, 7 workpackages `not_started`, 184 assignments, and 0 issues.
- No durable field record route or table existed before PM Lane 281.

## Schema And Routes

Schema:

- migration: `apps/mutation-seam/migrations/004_pm_lane_281_durable_field_records.sql`
- table: `seam.durable_field_records`
- insert-only update/delete rejection triggers
- RLS enabled
- guarded revoke for `anon`/`authenticated` roles when present

Routes:

- `POST /api/v1/mutations/durable-field-records`
- `GET /api/v1/reads/durable-field-record-status`
- `GET /api/v1/reads/durable-field-records`

The route requires:

- actor role: `lead`
- source: `online`
- mutation class: `B`
- action type: `create_daily_field_record`
- project scope containing `pm-import-project-miner-temp-power`

## Result

Hosted write:

- first POST status: `accepted`
- replay POST status: `idempotent_hit`
- mutation: `mut-76b3aeba-446f-4399-b452-21d98ab66d27`
- audit: `audit-70d8cc1f-151f-4730-b8db-4b3fc1b5765c`
- record count after replay: `1`

Hosted readback from both direct mutation-seam and operations-web:

- classification: `durable_field_recorded`
- field record id: `pm-lane-281-durable-field-record-temp-power-2026-05-18`
- project id: `pm-import-project-miner-temp-power`
- source import candidate: `pm-import-candidate-miner-temp-power`
- source import fingerprint: `e111fdbe934bf9de07ed24c1`
- field authorization record: `pm-lane-279-field-auth-temp-power-2026-05-18`
- schedule status record: `pm-lane-280-status-readiness-temp-power-2026-05-18`
- production tracking authority: `not_admitted`
- customer reporting authority: `not_admitted`
- finance authority: `not_admitted`
- field evidence authority: `not_admitted_attachment_write`
- production quantity count: `0`

Record payload/count evidence:

- workpackages: 7
- ready tasks: 15
- ready apparatus: 184
- assignments: 184
- unique assignment apparatus: 184
- issues: 0
- field evidence attachments: 0
- production quantity count: 0

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

- focused persistence tests: `18 passed`
- `py_compile`: passed
- migration applied against runtime DSN without printing secrets
- runtime DSN verification: table exists, insert-only triggers exist, RLS enabled, initial record count `0`
- scoped `git diff --check`: passed

## Correction Note

The first hosted live POST returned HTTP 500 before the generic PgDict JSONB adapter patch. Pre-retry status readback showed `record_count=0`. Commit `f801cf38` fixed typed JSON/JSONB serialization in the Supabase-backed adapter, after which the admitted write and replay passed.

## Boundary

PM Lane 281 created only the durable readiness record plus the schema, route, readback, tests, and smoke coverage required for that record.

Still blocked:

- production quantity writes
- field evidence attachment storage
- schedule/date writes
- workpackage status writes
- production tracking rows
- customer report, completion evidence, or customer commitment
- billing, payroll, invoice, accounting, or external finance output
- direct SQL business-record insertion
- source workbook/PDF writeback
- workbook macros
- new service, DNS, auth, ingress, or secret changes

## Next Blocker

`STOPPED_AWAITING_PRODUCTION_TRACKING_ADMISSION_PACKET_AFTER_DURABLE_FIELD_RECORD`
