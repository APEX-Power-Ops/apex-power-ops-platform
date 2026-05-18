# PM Lane 279 - Project Miner Temp Power Field Authorization Assignment Live Admission

## Decision

Jason's 2026-05-18 standing PM blocker authority is accepted as stakeholder authority for the next predetermined post-import blocker: field authorization and assignment admission.

PM Lane 279 clears that blocker by creating assignment rows for the already-imported Project Miner Temp Power apparatus through the existing governed assignment mutation seam.

## Preconditions

- PM Lane 277 approval row reads back as `approved_for_import_packet`.
- PM Lane 278 import reads back as `classification=imported`, `current_candidate_match=true`, and `counts_match=true`.
- Imported row counts remain 1 project, 7 workpackages, 15 tasks, 184 apparatus, 199 source trace rows, and 1 warning review row.
- Hosted assignments read back as 0 before the PM Lane 279 write.
- Hosted crew reads provide `tech-001`, `tech-002`, and `tech-003`.

## Execution

The lane used:

- route: `POST https://operations.apexpowerops.com/api/v1/mutations/assignments`
- actor role: `lead`
- mutation class: `B`
- source: `online`
- action: `assign`
- idempotency key pattern: `pm-lane-279-field-assignment-v2:<apparatus_id>`
- field authorization record: `pm-lane-279-field-auth-temp-power-2026-05-18`
- assignment policy: `deterministic_lowest_planned_hours_then_assignment_count_then_tech_id`

The first attempt supplied deterministic new `entity_id` values and was rejected by the existing route with `ENTITY_NOT_FOUND`, proving the route treats supplied assignment ids as update targets. No assignment rows were created in that attempt. The successful pass used the route-owned creation contract with `entity_id=null` and deterministic external ids in `assignment_external_id`.

## Result

Hosted readback:

- assignments: 184
- unique apparatus assigned: 184
- unique assignment external ids: 184
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

Replay proof:

- replay attempted: 184
- `idempotent_hit`: 184
- accepted on replay: 0
- failures: 0
- assignment count after replay: 184

## Readback Repair

The hosted assignment rows were correct, but the PM workfront projection initially still reported 184 unassigned rows because readiness only checked `apparatus.assigned_to`. PM Lane 279 patches the read model so readiness uses the resolved owner from either apparatus or assignment rows.

After Render auto-deploy of commit `be0891a1`, hosted `/api/v1/reads/pm-workfront` returned:

- total_count: 184
- blocked_count: 0
- unassigned_count: 0
- ready_count: 184
- in_progress_count: 0
- pm_review_count: 0
- complete_count: 0

## Validation

Local:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_pm_workfront_read_model.py -q
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_project_import_persistence.py -q
```

Results:

- `test_pm_workfront_read_model.py`: 3 passed
- `test_project_import_persistence.py`: 4 passed

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

## Boundary

PM Lane 279 created only assignment rows and assignment-readback support.

Still blocked:

- task, workpackage, or apparatus status mutation
- schedule/date mutation
- durable field record write
- production tracking write
- customer report or customer commitment
- billing, payroll, invoice, accounting, or external finance output
- direct SQL
- schema migration
- source workbook/PDF writeback
- workbook macros
- new service, DNS, auth, ingress, or secret change

## Next Blocker

`STOPPED_AWAITING_SCHEDULE_STATUS_MUTATION_ADMISSION_PACKET_AFTER_FIELD_AUTH_ASSIGNMENT`
