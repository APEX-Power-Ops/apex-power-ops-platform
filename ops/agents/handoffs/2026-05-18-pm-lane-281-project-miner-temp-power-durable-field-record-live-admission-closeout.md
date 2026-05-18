# PM Lane 281 - Project Miner Temp Power Durable Field Record Live Admission Closeout

## Outcome

PM Lane 281 is complete.

The post-schedule/status durable field record blocker is cleared for the Project Miner Temp Power pilot. Hosted mutation-seam now has a dedicated insert-only durable field record seam and one deterministic field-start readiness record for the imported Temp Power work.

Final outcome:

`DURABLE_FIELD_RECORD_LIVE_ADMISSION_PASS_PRODUCTION_CUSTOMER_FINANCE_BLOCKED`

## Authority

Jason's 2026-05-18 standing blocker authority as repo technical authority and project stakeholder was applied to this bounded direct successor packet.

PM Lane 281 admitted only the durable readiness record for the imported Temp Power project. It did not admit production quantities, evidence attachment storage, customer reporting, billing, payroll, invoice, or external finance output.

## Published Changes

Commits used for the live admission:

- `269d6926` - durable field record schema, route, reads, packet, tests, smoke extension, and authority update
- `f801cf38` - generic Supabase/PgDict JSONB adapter fix for typed JSONB fields

Schema:

- `apps/mutation-seam/migrations/004_pm_lane_281_durable_field_records.sql`
- table: `seam.durable_field_records`
- insert-only update/delete rejection triggers
- RLS enabled
- guarded revoke for `anon` and `authenticated` roles when present

Routes:

- `POST https://operations.apexpowerops.com/api/v1/mutations/durable-field-records`
- `GET https://operations.apexpowerops.com/api/v1/reads/durable-field-record-status`
- `GET https://operations.apexpowerops.com/api/v1/reads/durable-field-records`

## Hosted Write

Live write contract:

- actor role: `lead`
- source: `online`
- mutation class: `B`
- action type: `create_daily_field_record`
- field record id: `pm-lane-281-durable-field-record-temp-power-2026-05-18`
- idempotency key: `pm-lane-281-durable-field-record:pm-import-project-miner-temp-power:2026-05-18`
- project id: `pm-import-project-miner-temp-power`
- source import candidate: `pm-import-candidate-miner-temp-power`
- source import fingerprint: `e111fdbe934bf9de07ed24c1`
- field authorization record: `pm-lane-279-field-auth-temp-power-2026-05-18`
- schedule status record: `pm-lane-280-status-readiness-temp-power-2026-05-18`

Pre-write readback on both direct mutation-seam and operations-web returned:

- classification: `no_durable_field_record`
- storage available: `true`
- record count: `0`
- production/customer/finance authorities: `not_admitted`

The successful pass returned:

- first POST status: `accepted`
- replay POST status: `idempotent_hit`
- mutation: `mut-76b3aeba-446f-4399-b452-21d98ab66d27`
- audit: `audit-70d8cc1f-151f-4730-b8db-4b3fc1b5765c`
- record count after replay: `1`

## Hosted Readback

Final hosted readback from both `https://mutation-seam.apexpowerops.com` and `https://operations.apexpowerops.com` returned:

- classification: `durable_field_recorded`
- record count: `1`
- field record id: `pm-lane-281-durable-field-record-temp-power-2026-05-18`
- mutation: `mut-76b3aeba-446f-4399-b452-21d98ab66d27`
- audit: `audit-70d8cc1f-151f-4730-b8db-4b3fc1b5765c`
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

## Correction Note

The first hosted live POST returned HTTP 500 before the JSONB adapter patch. Pre-retry status confirmed no durable record was inserted. Commit `f801cf38` fixed generic Supabase/PgDict serialization for typed JSON/JSONB columns, focused tests passed again, and the retry succeeded with replay proof.

## Validation

Local validation:

- focused mutation-seam persistence slice: `18 passed`
- `py_compile`: passed
- runtime DSN migration apply: table exists, insert-only triggers exist, RLS enabled, initial record count `0`
- scoped `git diff --check`: passed

Hosted validation:

- deployed mutation-seam smoke with PM intake -> `RESULT PASS`
- hosted PM intake smoke -> `PM_INTAKE_HOSTED_SUMMARY failed=0`
- hosted operations routes smoke -> `SMOKE_SUMMARY failed=0 passed=12`

## Boundary

This lane created only the dedicated durable field readiness record plus the schema/route/readback required to persist it.

No production quantity write, field evidence attachment storage, schedule/date write, workpackage status write, production tracking row, customer report, completion evidence, customer commitment, billing, payroll, invoice, accounting output, external finance output, direct SQL record insertion, source workbook/PDF writeback, workbook macro, new service, auth/ingress/DNS change, secret change, or autonomous AI business-state mutation was performed.

## Next Stop

`STOPPED_AWAITING_PRODUCTION_TRACKING_ADMISSION_PACKET_AFTER_DURABLE_FIELD_RECORD`
