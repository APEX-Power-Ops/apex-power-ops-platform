# PM Lane 283 - Project Miner Temp Power Customer Completion Baseline Live Admission

## Decision

Jason's 2026-05-18 standing PM blocker authority is accepted as stakeholder authority for the next predetermined post-production-tracking blocker: customer reporting and completion evidence baseline admission.

PM Lane 283 clears that blocker by adding a dedicated insert-only customer completion record seam and persisting one deterministic Temp Power zero-report and zero-evidence baseline record. It does not admit customer-facing delivery, customer commitments, billing, payroll, invoice, accounting, or external finance outputs.

## Preconditions

- PM Lane 277 approval row reads back as `approved_for_import_packet`.
- PM Lane 278 import reads back as `classification=imported`, `current_candidate_match=true`, and `counts_match=true`.
- PM Lane 279 field authorization/assignment reads back as 184 assignments for 184 unique imported apparatus rows.
- PM Lane 280 schedule/status readiness reads back as 15 tasks `ready`, 184 apparatus `ready`, 7 workpackages `not_started`, 184 assignments, and 0 issues.
- PM Lane 281 durable field record reads back as `durable_field_recorded`, `record_count=1`, and `production_quantity_count=0`.
- PM Lane 282 production tracking reads back as `production_tracking_baseline_recorded`, `record_count=1`, and zero quantities, labor, actual hours, apparatus progress, and progress updates.
- No customer completion baseline route or table existed before PM Lane 283.

## Schema And Routes

Schema:

- migration: `apps/mutation-seam/migrations/006_pm_lane_283_customer_completion_records.sql`
- table: `seam.customer_completion_records`
- insert-only update/delete rejection triggers
- RLS enabled
- guarded revoke for `anon`/`authenticated` roles when present

Routes:

- `POST /api/v1/mutations/customer-completion`
- `GET /api/v1/reads/customer-completion-status`
- `GET /api/v1/reads/customer-completion-records`

The route requires:

- actor role: `pm`
- source: `online`
- mutation class: `C`
- project scope containing `pm-import-project-miner-temp-power`

## Result

Hosted write:

- first POST status: `accepted`
- replay POST status: `idempotent_hit`
- mutation: `mut-6c633d45-a288-4ac9-8d69-d6bdeff5e811`
- audit: `audit-5607d1dd-aa46-4454-91d6-00737a1ac3c9`
- record count after replay: `1`

Hosted readback from both direct mutation-seam and operations-web:

- classification: `customer_completion_baseline_recorded`
- customer completion record id: `pm-lane-283-customer-completion-temp-power-2026-05-18`
- source import candidate: `pm-import-candidate-miner-temp-power`
- source import fingerprint: `e111fdbe934bf9de07ed24c1`
- production tracking record: `pm-lane-282-production-tracking-temp-power-2026-05-18`
- customer reporting authority: `admitted_by_pm_lane_283_customer_completion_baseline`
- completion evidence authority: `admitted_by_pm_lane_283_zero_evidence_baseline`
- customer delivery authority: `not_admitted_external_delivery`
- finance, billing, payroll, invoice, and accounting authorities: `not_admitted`
- customer report count: `0`
- completion evidence count: `0`
- production quantity count: `0`
- labor entry count: `0`
- actual labor hours: `0.00`
- apparatus progress count: `0`
- progress update count: `0`

## Correction Note

The first hosted POST attempts hit the pre-fix deployment and returned HTTP 500. Immediate status readback from both hosts confirmed `no_customer_completion_record` and `record_count=0`.

Commit `91a7f9a6` made nested precondition evidence JSON-safe before the Supabase-backed adapter writes it to JSONB. After Render deployed that fix, the same admitted payload returned `accepted` and replay returned `idempotent_hit`.

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

- focused persistence tests: `30 passed`
- regression slice after hosted 500: `12 passed`
- `py_compile`: passed
- packet JSON parsed successfully
- scoped `git diff --check`: passed

## Boundary

PM Lane 283 created only the zero-report and zero-evidence customer completion baseline record plus the schema, route, readback, tests, and smoke coverage required for that record.

Still blocked:

- customer-facing report delivery
- completion evidence artifact storage
- customer commitments or delivery events
- nonzero production quantity writes
- labor entries or actual labor hours
- apparatus progress or progress updates
- billing, payroll, invoice, accounting, or external finance output
- source workbook/PDF writeback
- workbook macros
- new service, DNS, auth, ingress, or secret changes

## Next Blocker

`STOPPED_AWAITING_FINANCIAL_HANDOFF_ADMISSION_PACKET_AFTER_CUSTOMER_COMPLETION_EVIDENCE`
