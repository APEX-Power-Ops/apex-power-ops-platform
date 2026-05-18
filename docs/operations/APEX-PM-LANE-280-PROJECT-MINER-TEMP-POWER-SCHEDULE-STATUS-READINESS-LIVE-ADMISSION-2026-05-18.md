# PM Lane 280 - Project Miner Temp Power Schedule Status Readiness Live Admission

## Decision

Jason's 2026-05-18 standing PM blocker authority is accepted as stakeholder authority for the next predetermined post-assignment blocker: schedule/status readiness admission.

PM Lane 280 clears that blocker only by setting imported Temp Power task and apparatus status to `ready` through existing governed mutation seams. It does not admit schedule/date writes or workpackage status writes.

## Preconditions

- PM Lane 277 approval row reads back as `approved_for_import_packet`.
- PM Lane 278 import reads back as `classification=imported`, `current_candidate_match=true`, and `counts_match=true`.
- PM Lane 279 reads back as 184 assignments for 184 unique imported apparatus rows.
- Hosted preflight showed 15 imported tasks, 184 imported apparatus, 7 imported workpackages, 184 assignments, and 0 issues.
- Hosted schedule routes are read-only context: 1 project, 4 tasks-with-scope, and 3 relationships.
- Existing governed seams admit `task.start` and `apparatus.update_status`; no existing governed workpackage start route or schedule/date write route exists.

## Execution

The lane used:

- task route: `POST https://operations.apexpowerops.com/api/v1/mutations/tasks`
- apparatus route: `POST https://operations.apexpowerops.com/api/v1/mutations/apparatus`
- actor role: `lead`
- source: `online`
- mutation class: `B`
- task action: `start`
- apparatus action: `update_status`
- target status: `ready`
- task idempotency key pattern: `pm-lane-280-task-ready:<task_id>`
- apparatus idempotency key pattern: `pm-lane-280-apparatus-ready:<apparatus_id>`
- status readiness record: `pm-lane-280-status-readiness-temp-power-2026-05-18`

Each task/apparatus payload preserved downstream boundaries:

- `schedule_date_authority: not_admitted`
- `workpackage_status_authority: not_admitted_no_existing_start_route`
- `durable_field_record_authority: not_admitted`
- `production_tracking_authority: not_admitted`
- `customer_reporting_authority: not_admitted`
- `finance_authority: not_admitted`

## Result

Hosted write:

- admitted at: `2026-05-18T02:51:37.9231947Z`
- tasks attempted: 15
- tasks accepted: 15
- apparatus attempted: 184
- apparatus accepted: 184
- failures: 0

Hosted readback:

- tasks: 15 `ready`
- apparatus: 184 `ready`
- workpackages: 7 `not_started`
- assignments: 184
- unique assignment apparatus: 184
- issues: 0
- PM workfront ready count: 184
- PM workfront unassigned count: 0
- import status: `imported`, `current_candidate_match=true`, `counts_match=true`
- downstream authority bad counts: 0

Replay proof:

- task replay attempted: 15
- task `idempotent_hit`: 15
- apparatus replay attempted: 184
- apparatus `idempotent_hit`: 184
- other replay statuses: 0

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

- packet JSON parsed successfully
- `git diff --check` passed

## Boundary

PM Lane 280 created only task and apparatus readiness status writes plus boundary metadata.

Still blocked:

- schedule/date writes
- workpackage status writes
- durable field record writes
- production tracking writes
- customer report, completion evidence, or customer commitment
- billing, payroll, invoice, accounting, or external finance output
- direct SQL
- schema migration
- source workbook/PDF writeback
- workbook macros
- new service, DNS, auth, ingress, or secret changes

## Next Blocker

`STOPPED_AWAITING_DURABLE_FIELD_RECORD_ADMISSION_PACKET_AFTER_SCHEDULE_STATUS_READINESS`
