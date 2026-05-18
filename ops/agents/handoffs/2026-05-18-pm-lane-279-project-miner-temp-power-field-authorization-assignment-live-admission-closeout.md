# PM Lane 279 - Project Miner Temp Power Field Authorization Assignment Live Admission Closeout

## Outcome

PM Lane 279 is complete.

The post-import field authorization and assignment blocker is cleared for the Project Miner Temp Power pilot. The hosted assignment seam now contains one assignment row for each imported apparatus row, and the hosted PM workfront read model shows all 184 imported apparatus as ready rather than unassigned.

Final outcome:

`FIELD_AUTHORIZATION_ASSIGNMENT_LIVE_ADMISSION_PASS_DOWNSTREAM_BLOCKED`

## Authority

Jason's 2026-05-18 standing blocker authority as repo technical authority and project stakeholder was applied to this bounded direct successor packet.

The authority extension now records PM Lane 279 as admitted only for existing assignment mutation seam writes against imported Temp Power apparatus rows and assignment-readback support code.

## Hosted Write

Route:

`POST https://operations.apexpowerops.com/api/v1/mutations/assignments`

Write contract:

- actor role: `lead`
- source: `online`
- mutation class: `B`
- action type: `assign`
- entity creation: route-owned `entity_id=null`
- idempotency key: `pm-lane-279-field-assignment-v2:<apparatus_id>`
- field authorization record: `pm-lane-279-field-auth-temp-power-2026-05-18`
- assignment policy: `deterministic_lowest_planned_hours_then_assignment_count_then_tech_id`

The first pass with deterministic new `entity_id` values was rejected with `ENTITY_NOT_FOUND`; no assignment rows were created. The successful pass used the existing route creation contract and returned:

- attempted: 184
- accepted: 184
- idempotent_hit: 0
- failures: 0

First accepted assignment:

- mutation: `mut-30ec549a-6141-4fec-bdba-1bfc48018272`
- assignment id: `assignment-2c4e178b-ab0d-419a-b5fe-69fcd1f6f623`
- apparatus: `pm-import-project-miner-temp-power-app-0001`
- assigned_to: `tech-001`
- audit: `audit-298a0933-4aac-434a-80f2-17eda5c57c89`

Last accepted assignment:

- mutation: `mut-5038f0d3-80e3-4d16-b557-a91ea467331a`
- assignment id: `assignment-7e5c1733-f2ce-4c30-995d-6270a307e743`
- apparatus: `pm-import-project-miner-temp-power-app-0184`
- assigned_to: `tech-002`
- audit: `audit-0060c826-6cf9-48c0-88bd-161faeb4b1af`

## Hosted Readback

Final hosted readback:

- import classification: `imported`
- current_candidate_match: `true`
- counts_match: `true`
- imported rows: 1 project, 7 workpackages, 15 tasks, 184 apparatus, 199 source trace rows, 1 warning review row
- assignments: 184
- unique apparatus: 184
- unique external ids: 184
- field authorization record: `pm-lane-279-field-auth-temp-power-2026-05-18`
- downstream schedule/status authority: `not_admitted`
- durable field record authority: `not_admitted`
- production tracking authority: `not_admitted`

Distribution:

| Tech | Assignment count | Planned hours |
| --- | ---: | ---: |
| `tech-001` | 66 | 194.5 |
| `tech-002` | 59 | 217.5 |
| `tech-003` | 59 | 194.75 |

Replay:

- replay attempted: 184
- `idempotent_hit`: 184
- accepted on replay: 0
- failures: 0
- assignment_count_after: 184

## Readback Fix And Deploy

PM workfront initially reported 184 unassigned because readiness only checked `apparatus.assigned_to`; assignment owners were resolved later but not passed into readiness.

Changed files in commit `be0891a1`:

- `apps/mutation-seam/app/pm_workfront_read_model.py`
- `apps/mutation-seam/tests/test_pm_workfront_read_model.py`
- `docs/authority/APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-18-pm-lane-279-project-miner-temp-power-field-authorization-assignment-live-admission.json`
- `ops/agents/handoffs/2026-05-18-pm-lane-279-project-miner-temp-power-field-authorization-assignment-live-admission-handoff.md`

Render auto-deployed the pushed commit. Hosted `/api/v1/reads/pm-workfront` then returned:

- total_count: 184
- blocked_count: 0
- unassigned_count: 0
- ready_count: 184
- in_progress_count: 0
- pm_review_count: 0
- complete_count: 0

## Validation

Local validation:

- `& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_pm_workfront_read_model.py -q` -> 3 passed
- `& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_project_import_persistence.py -q` -> 4 passed
- scoped `git diff --check` -> passed

Hosted validation:

- deployed mutation-seam smoke with PM intake -> `RESULT PASS`
- hosted PM intake smoke -> `PM_INTAKE_HOSTED_SUMMARY failed=0`
- hosted operations routes smoke -> `SMOKE_SUMMARY failed=0 passed=12`

## Boundary

This lane created assignment rows and patched assignment-readback projection only.

No task, workpackage, or apparatus status mutation, schedule/date mutation, durable field record, production tracking row, customer output, finance output, direct SQL, schema migration, workbook/PDF writeback, macro/writeback, new service, auth/ingress/DNS change, secret change, or autonomous AI business-state mutation was performed.

## Next Stop

`STOPPED_AWAITING_SCHEDULE_STATUS_MUTATION_ADMISSION_PACKET_AFTER_FIELD_AUTH_ASSIGNMENT`
