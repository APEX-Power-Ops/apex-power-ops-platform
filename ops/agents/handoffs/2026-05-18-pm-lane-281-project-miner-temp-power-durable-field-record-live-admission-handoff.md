# PM Lane 281 - Project Miner Temp Power Durable Field Record Live Admission Handoff

## Summary

PM Lane 281 admits the first durable field record seam for the Project Miner Temp Power pilot.

Jason's 2026-05-18 standing PM blocker authority is the stakeholder authority for this bounded packet. The lane creates the dedicated durable field record schema, route, readback, tests, smoke coverage, and one deterministic field-start readiness record. It does not open production quantities, evidence attachment storage, customer reporting, or finance outputs.

## Preconditions

- PM Lane 277 approval row exists and reads back as `approved_for_import_packet`.
- PM Lane 278 import reads back as `classification=imported`, `current_candidate_match=true`, and `counts_match=true`.
- PM Lane 279 reads back as 184 assignments for 184 unique imported apparatus rows.
- PM Lane 280 reads back as 15 tasks `ready`, 184 apparatus `ready`, 7 workpackages `not_started`, 184 assignments, and 0 issues.
- No durable field record route or table existed before this lane.

## Admitted Schema And Routes

Schema:

`apps/mutation-seam/migrations/004_pm_lane_281_durable_field_records.sql`

Table:

`seam.durable_field_records`

Routes:

- `POST /api/v1/mutations/durable-field-records`
- `GET /api/v1/reads/durable-field-record-status`
- `GET /api/v1/reads/durable-field-records`

The table is insert-only through update/delete rejection triggers, has RLS enabled, and revokes `anon`/`authenticated` access only when those roles exist in the target database.

## Live Record Contract

The admitted live write uses:

- actor role: `lead`
- source: `online`
- mutation class: `B`
- action type: `create_daily_field_record`
- field record id: `pm-lane-281-durable-field-record-temp-power-2026-05-18`
- idempotency key: `pm-lane-281-durable-field-record:pm-import-project-miner-temp-power:2026-05-18`
- record date: `2026-05-18`
- record kind: `field_start_readiness`
- record scope: `daily_readiness_no_production_quantities`
- source fingerprint: `e111fdbe934bf9de07ed24c1`
- field authorization record: `pm-lane-279-field-auth-temp-power-2026-05-18`
- schedule status record: `pm-lane-280-status-readiness-temp-power-2026-05-18`

Required readback counts:

- workpackages: 7
- ready tasks: 15
- ready apparatus: 184
- assignments: 184
- unique assignment apparatus: 184
- issues: 0
- production quantity count: 0

Required downstream boundary fields:

- `field_evidence_authority: not_admitted_attachment_write`
- `production_tracking_authority: not_admitted`
- `customer_reporting_authority: not_admitted`
- `finance_authority: not_admitted`

## Boundary

This lane admits only the dedicated durable readiness record.

Still blocked:

- production quantity writes
- field evidence attachment storage
- schedule/date writes
- workpackage status writes
- production tracking
- customer reporting or completion evidence
- billing, payroll, invoice, accounting, or external finance output
- source workbook/PDF writeback
- workbook macros
- new service, DNS, auth, ingress, or secret changes

## Validation Before Live Closeout

Local validation already passed:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_durable_field_record_persistence.py apps/mutation-seam/tests/test_project_import_persistence.py apps/mutation-seam/tests/test_project_import_approval_persistence.py -q
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m py_compile apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py apps/mutation-seam/app/durable_field_record_persistence.py apps/mutation-seam/app/routers/durable_field_records.py
```

Results:

- focused tests: 18 passed
- `py_compile`: passed
- migration 004 runtime DSN apply: table exists, insert-only triggers exist, RLS enabled, record count 0

Run after deploy:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com
```

## Next Blocker

After live record closeout, the next blocker is production tracking admission after durable field record proof.
