# PM Lane 282 - Project Miner Temp Power Production Tracking Baseline Live Admission Handoff

## Summary

PM Lane 282 admits the first production tracking baseline seam for the Project Miner Temp Power pilot.

Jason's 2026-05-18 standing PM blocker authority is the stakeholder authority for this bounded packet. The lane creates the dedicated production tracking schema, route, readback, tests, smoke coverage, and one deterministic zero-actual baseline record. It does not open nonzero quantities, labor entries, apparatus progress updates, customer reporting, billing, payroll, invoice, accounting, or external finance outputs.

## Preconditions

- PM Lane 277 approval row exists and reads back as `approved_for_import_packet`.
- PM Lane 278 import reads back as `classification=imported`, `current_candidate_match=true`, and `counts_match=true`.
- PM Lane 279 reads back as 184 assignments for 184 unique imported apparatus rows.
- PM Lane 280 reads back as 15 tasks `ready`, 184 apparatus `ready`, 7 workpackages `not_started`, 184 assignments, and 0 issues.
- PM Lane 281 reads back as `durable_field_recorded` with one durable field record and `production_quantity_count=0`.
- No production tracking baseline route or table existed before this lane.

## Admitted Schema And Routes

Schema:

`apps/mutation-seam/migrations/005_pm_lane_282_production_tracking_records.sql`

Table:

`seam.production_tracking_records`

Routes:

- `POST /api/v1/mutations/production-tracking`
- `GET /api/v1/reads/production-tracking-status`
- `GET /api/v1/reads/production-tracking-records`

The table is insert-only through update/delete rejection triggers, has RLS enabled, and revokes `anon`/`authenticated` access only when those roles exist in the target database.

## Live Record Contract

The admitted live write uses:

- actor role: `lead`
- source: `online`
- mutation class: `B`
- action type: `create_daily_production_baseline`
- production tracking record id: `pm-lane-282-production-tracking-temp-power-2026-05-18`
- idempotency key: `pm-lane-282-production-tracking:pm-import-project-miner-temp-power:2026-05-18`
- record date: `2026-05-18`
- tracking kind: `field_start_zero_actual_baseline`
- record scope: `production_tracking_baseline_no_customer_or_finance`
- source fingerprint: `e111fdbe934bf9de07ed24c1`
- durable field record: `pm-lane-281-durable-field-record-temp-power-2026-05-18`

Required readback counts:

- workpackages: 7
- ready tasks: 15
- ready apparatus: 184
- assignments: 184
- unique assignment apparatus: 184
- issues: 0
- durable field records: 1
- production quantities: 0
- labor entries: 0
- actual labor hours: 0.0
- apparatus progress entries: 0
- progress updates: 0

Required downstream boundary fields:

- `production_tracking_authority: admitted_by_pm_lane_282_zero_actual_baseline`
- `customer_reporting_authority: not_admitted`
- `finance_authority: not_admitted`

## Boundary

This lane admits only the dedicated zero-actual production tracking baseline record.

Still blocked:

- nonzero production quantity writes
- labor entry or actual labor hour writes
- apparatus progress or progress update writes
- field evidence attachment storage
- customer reporting or completion evidence
- billing, payroll, invoice, accounting, or external finance output
- source workbook/PDF writeback
- workbook macros
- new service, DNS, auth, ingress, or secret changes

## Validation Before Live Closeout

Run before publication:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_production_tracking_persistence.py apps/mutation-seam/tests/test_durable_field_record_persistence.py apps/mutation-seam/tests/test_project_import_persistence.py apps/mutation-seam/tests/test_project_import_approval_persistence.py -q
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m py_compile apps/mutation-seam/app/production_tracking_persistence.py apps/mutation-seam/app/routers/production_tracking.py apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py
```

Run after deploy:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com
```

## Next Blocker

After live production tracking baseline closeout, the next blocker is customer reporting and completion evidence admission after production tracking proof.
