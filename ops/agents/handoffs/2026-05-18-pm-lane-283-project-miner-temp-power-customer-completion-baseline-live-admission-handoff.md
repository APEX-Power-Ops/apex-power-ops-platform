# PM Lane 283 - Project Miner Temp Power Customer Completion Baseline Live Admission Handoff

## Summary

PM Lane 283 admits the first customer completion baseline seam for the Project Miner Temp Power pilot.

Jason's 2026-05-18 standing PM blocker authority is the stakeholder authority for this bounded packet. The lane creates the dedicated customer completion schema, route, readback, tests, smoke coverage, and one deterministic zero-report and zero-evidence baseline record. It does not open customer-facing delivery, customer commitments, billing, payroll, invoice, accounting, or external finance outputs.

## Preconditions

- PM Lane 277 approval row exists and reads back as `approved_for_import_packet`.
- PM Lane 278 import reads back as `classification=imported`, `current_candidate_match=true`, and `counts_match=true`.
- PM Lane 279 reads back as 184 assignments for 184 unique imported apparatus rows.
- PM Lane 280 reads back as 15 tasks `ready`, 184 apparatus `ready`, 7 workpackages `not_started`, 184 assignments, and 0 issues.
- PM Lane 281 reads back as `durable_field_recorded` with one durable field record and `production_quantity_count=0`.
- PM Lane 282 reads back as `production_tracking_baseline_recorded` with one production tracking record and zero quantities, labor, actual hours, apparatus progress, and progress updates.
- No customer completion baseline route or table existed before this lane.

## Admitted Schema And Routes

Schema:

`apps/mutation-seam/migrations/006_pm_lane_283_customer_completion_records.sql`

Table:

`seam.customer_completion_records`

Routes:

- `POST /api/v1/mutations/customer-completion`
- `GET /api/v1/reads/customer-completion-status`
- `GET /api/v1/reads/customer-completion-records`

The table is insert-only through update/delete rejection triggers, has RLS enabled, and revokes `anon`/`authenticated` access only when those roles exist in the target database.

## Live Record Contract

The admitted live write uses:

- actor role: `pm`
- source: `online`
- mutation class: `C`
- action type: `create_customer_completion_baseline`
- customer completion record id: `pm-lane-283-customer-completion-temp-power-2026-05-18`
- idempotency key: `pm-lane-283-customer-completion:pm-import-project-miner-temp-power:2026-05-18`
- record date: `2026-05-18`
- record kind: `customer_completion_zero_evidence_baseline`
- record scope: `customer_completion_baseline_no_external_delivery_or_finance`
- source fingerprint: `e111fdbe934bf9de07ed24c1`
- durable field record: `pm-lane-281-durable-field-record-temp-power-2026-05-18`
- production tracking record: `pm-lane-282-production-tracking-temp-power-2026-05-18`

Required readback counts:

- workpackages: 7
- ready tasks: 15
- ready apparatus: 184
- assignments: 184
- unique assignment apparatus: 184
- issues: 0
- durable field records: 1
- production tracking records: 1
- production quantities: 0
- labor entries: 0
- actual labor hours: 0.0
- apparatus progress entries: 0
- progress updates: 0
- customer report artifacts: 0
- completion evidence artifacts: 0

Required authority fields:

- `production_tracking_authority: admitted_by_pm_lane_282_zero_actual_baseline`
- `customer_reporting_authority: admitted_by_pm_lane_283_customer_completion_baseline`
- `completion_evidence_authority: admitted_by_pm_lane_283_zero_evidence_baseline`
- `customer_delivery_authority: not_admitted_external_delivery`
- `finance_authority: not_admitted`
- `billing_authority: not_admitted`
- `payroll_authority: not_admitted`
- `invoice_authority: not_admitted`
- `accounting_authority: not_admitted`

## Boundary

This lane admits only the dedicated zero-report and zero-evidence customer completion baseline record.

Still blocked:

- customer-facing report delivery
- completion evidence artifact storage
- customer commitments or delivery events
- nonzero production quantities
- labor entries or actual labor hours
- apparatus progress or progress updates
- billing, payroll, invoice, accounting, or external finance output
- source workbook/PDF writeback
- workbook macros
- new service, DNS, auth, ingress, or secret changes

## Validation Before Live Closeout

Run before publication:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_customer_completion_persistence.py apps/mutation-seam/tests/test_production_tracking_persistence.py apps/mutation-seam/tests/test_durable_field_record_persistence.py apps/mutation-seam/tests/test_project_import_persistence.py apps/mutation-seam/tests/test_project_import_approval_persistence.py -q
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m py_compile apps/mutation-seam/app/customer_completion_persistence.py apps/mutation-seam/app/routers/customer_completion.py apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py
```

Run after deploy:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com
```

## Live Closeout

Hosted execution is complete.

Results:

- pre-write direct mutation-seam status: `no_customer_completion_record`, `storage_available=true`, `record_count=0`, `production_tracking_record_count=1`
- pre-write operations-web status: `no_customer_completion_record`, `storage_available=true`, `record_count=0`, `production_tracking_record_count=1`
- first POST after fix deployment: `accepted`
- replay POST: `idempotent_hit`
- mutation: `mut-6c633d45-a288-4ac9-8d69-d6bdeff5e811`
- audit: `audit-5607d1dd-aa46-4454-91d6-00737a1ac3c9`
- final direct mutation-seam status: `customer_completion_baseline_recorded`, `record_count=1`
- final operations-web status: `customer_completion_baseline_recorded`, `record_count=1`
- customer report count: `0`
- completion evidence count: `0`
- production quantity count: `0`
- labor entry count: `0`
- actual labor hours: `0.00`
- apparatus progress count: `0`
- progress update count: `0`
- customer delivery authority: `not_admitted_external_delivery`
- finance/billing/payroll/invoice/accounting authorities: `not_admitted`

The first hosted POST attempts hit the pre-fix deployment and returned HTTP 500. Immediate readback confirmed no partial customer completion record. Commit `91a7f9a6` made the nested precondition evidence JSON-safe for hosted PostgreSQL values; after Render deployed that fix, the same admitted payload returned `accepted` and replay returned `idempotent_hit`.

Hosted validation passed:

- deployed mutation-seam smoke: `RESULT PASS`
- hosted PM intake smoke: `PM_INTAKE_HOSTED_SUMMARY failed=0`
- hosted operations routes smoke: `SMOKE_SUMMARY failed=0 passed=12`

## Next Blocker

After PM Lane 283 closes, the next expected blocker is:

`STOPPED_AWAITING_FINANCIAL_HANDOFF_ADMISSION_PACKET_AFTER_CUSTOMER_COMPLETION_EVIDENCE`
