# PM Lane 280 - Project Miner Temp Power Schedule Status Readiness Live Admission Handoff

## Summary

PM Lane 280 admits the first post-assignment schedule/status readiness write for the Project Miner Temp Power pilot.

Jason's 2026-05-18 standing PM blocker authority is the stakeholder authority for this bounded packet. The lane uses existing hosted task and apparatus mutation seams and does not open schedule/date writes, workpackage status writes, durable field records, production tracking, customer reporting, or finance outputs.

## Preconditions

- PM Lane 277 approval row exists and reads back as `approved_for_import_packet`.
- PM Lane 278 import reads back as `classification=imported`, `current_candidate_match=true`, and `counts_match=true`.
- PM Lane 279 reads back as 184 assignments for 184 unique imported apparatus rows.
- Hosted preflight showed 15 imported tasks and 184 imported apparatus still at `not_started`, 7 imported workpackages still at `not_started`, and 0 issues.
- The existing mutation registry admits `task.start` and `apparatus.update_status` with lead actor role, online source, and mutation class `B`.
- The schedule router is read-only, and no existing governed workpackage start route exists.

## Readiness Contract

The admitted write uses:

- task route: `POST https://operations.apexpowerops.com/api/v1/mutations/tasks`
- apparatus route: `POST https://operations.apexpowerops.com/api/v1/mutations/apparatus`
- actor role: `lead`
- source: `online`
- mutation class: `B`
- task action: `start`
- apparatus action: `update_status`
- target status: `ready`
- task idempotency key: `pm-lane-280-task-ready:<task_id>`
- apparatus idempotency key: `pm-lane-280-apparatus-ready:<apparatus_id>`
- status readiness record: `pm-lane-280-status-readiness-temp-power-2026-05-18`

Each payload preserves these downstream boundaries:

- `schedule_date_authority: not_admitted`
- `workpackage_status_authority: not_admitted_no_existing_start_route`
- `durable_field_record_authority: not_admitted`
- `production_tracking_authority: not_admitted`
- `customer_reporting_authority: not_admitted`
- `finance_authority: not_admitted`

## Execution Result

The live hosted write used `2026-05-18T02:51:37.9231947Z` as the status readiness timestamp.

Result:

- task attempted: 15
- task accepted: 15
- apparatus attempted: 184
- apparatus accepted: 184
- failures: 0

First and last task mutations:

- `pm-import-project-miner-temp-power-task-0001`: `mut-54247a6b-44c1-40de-8054-47e2a644917b`, audit `audit-d2a90098-7f0a-462a-b1b7-d0761a5eb496`
- `pm-import-project-miner-temp-power-task-0015`: `mut-9e83736e-08dc-41fb-bb19-052fa88397f2`, audit `audit-146cf77b-7aa0-49dd-a7e2-c23132c327a2`

First and last apparatus mutations:

- `pm-import-project-miner-temp-power-app-0001`: `mut-5af95789-a4ec-41b9-9a10-474d590ce9fb`, audit `audit-1d8cbf9f-4550-4063-b501-bbd114209fcd`
- `pm-import-project-miner-temp-power-app-0184`: `mut-8ce22e8e-6fcd-4c63-89b1-bb8515c23477`, audit `audit-122c9faa-a9b0-431b-a077-4b512455f32b`

## Hosted Readback

Final hosted readback:

- tasks: 15 `ready`
- apparatus: 184 `ready`
- workpackages: 7 `not_started`
- assignments: 184
- unique assignment apparatus: 184
- issues: 0
- PM workfront: total 184, blocked 0, unassigned 0, ready 184, in progress 0, PM review 0, complete 0
- import status: `classification=imported`, `current_candidate_match=true`, `counts_match=true`
- schedule read-only context: 1 project, 4 tasks-with-scope, 3 relationships
- downstream authority bad counts: 0

Replay proof:

- task replay attempted: 15
- task `idempotent_hit`: 15
- apparatus replay attempted: 184
- apparatus `idempotent_hit`: 184
- other replay statuses: 0

## Boundary

This lane writes only task and apparatus readiness status plus Lane 280 boundary metadata.

Still blocked:

- schedule/date writes
- workpackage status writes
- durable field records
- production tracking
- customer reporting or completion evidence
- billing, payroll, invoice, accounting, or external finance output
- direct SQL
- schema migration
- source workbook/PDF writeback
- workbook macros
- new service, DNS, auth, ingress, or secret changes

## Validation

Run before closeout:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com
git diff --check
```

## Next Blocker

`STOPPED_AWAITING_DURABLE_FIELD_RECORD_ADMISSION_PACKET_AFTER_SCHEDULE_STATUS_READINESS`
