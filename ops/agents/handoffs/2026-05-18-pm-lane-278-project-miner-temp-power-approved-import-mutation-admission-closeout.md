# PM Lane 278 - Approved Import Mutation Admission Closeout

Date: 2026-05-18

Decision label:

`PROJECT_MINER_TEMP_POWER_APPROVED_IMPORT_MUTATION_ADMISSION`

Selected outcome:

`HOSTED_IMPORT_ACCEPTED_REPLAY_SAFE_DOWNSTREAM_BLOCKED`

## Result

PM Lane 278 is complete.

The Project Miner Temp Power import mutation route was implemented, tested, committed, pushed, deployed by the hosted service, and executed through the application path.

Implementation commit:

`4d5af24f`

Live route:

`https://operations.apexpowerops.com/api/v1/mutations/project-imports`

Status readback:

`https://operations.apexpowerops.com/api/v1/reads/project-import-status`

## Local Validation

Focused validation passed before publication:

```text
15 passed, 16 warnings
```

Command:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/test_project_import_persistence.py tests/test_project_import_approval_persistence.py tests/test_project_import_admission_plan.py
```

The warnings were existing Pydantic class-config deprecation warnings and openpyxl data-validation warnings.

## Hosted Preflight

Hosted candidate before import:

| Field | Value |
| --- | --- |
| candidate id | `pm-import-candidate-miner-temp-power` |
| candidate version | `pm_import_candidate_read_only_v1` |
| workpackages | `7` |
| tasks | `15` |
| apparatus candidates | `184` |
| blocker count | `0` |
| warning count | `1` |
| source fingerprint | `e111fdbe934bf9de07ed24c1` |
| mutation authority | `not_admitted` |

Hosted approval status before import:

| Field | Value |
| --- | --- |
| classification | `approved_for_import_packet` |
| approval record count | `1` |
| current candidate match | `true` |
| approval record id | `pm-import-approval-03a1aea39afde71b44516f44` |
| approval mutation id | `mut-bc747179-0232-40a4-9288-2ee93381fd3f` |
| approval audit event id | `audit-aca55758-2385-47f0-a026-7b012f9f5c1f` |
| import authority on approval status | `not_admitted` |

Import status before import:

| Field | Value |
| --- | --- |
| classification | `no_import_record` |
| expected projects | `1` |
| expected workpackages | `7` |
| expected tasks | `15` |
| expected apparatus | `184` |
| expected source trace rows | `199` |
| expected warning review rows | `1` |

## Live Import Evidence

First POST response summary:

| Field | Value |
| --- | --- |
| HTTP status | `200` |
| status | `accepted` |
| entity type | `pm_import` |
| action type | `persist_project_import` |
| entity id | `pm-import-project-miner-temp-power` |
| mutation id | `mut-1529e376-4f5c-4c03-960d-4d38462312d9` |
| audit event id | `audit-5035aeae-cd58-4290-b0a6-70a0eab97c1c` |
| import authority | `admitted_by_pm_lane_278` |
| source trace storage | `embedded_on_imported_task_and_apparatus_rows` |
| warning review storage | `embedded_on_imported_project_row` |

First POST row counts:

| Surface | Count |
| --- | ---: |
| projects | 1 |
| workpackages | 7 |
| tasks | 15 |
| apparatus | 184 |
| source trace rows | 199 |
| warning review rows | 1 |
| assignments | 0 |
| snapshots | 0 |
| issues | 0 |
| hours | 0 |

Same-payload replay response:

| Field | Value |
| --- | --- |
| HTTP status | `200` |
| status | `idempotent_hit` |
| entity id | `pm-import-project-miner-temp-power` |
| mutation id | `mut-1529e376-4f5c-4c03-960d-4d38462312d9` |
| audit event id | `audit-5035aeae-cd58-4290-b0a6-70a0eab97c1c` |

Import-status readback after replay:

| Field | Value |
| --- | --- |
| classification | `imported` |
| current candidate match | `true` |
| counts match | `true` |
| imported projects | `1` |
| imported workpackages | `7` |
| imported tasks | `15` |
| imported apparatus | `184` |
| imported source trace rows | `199` |
| imported warning review rows | `1` |

## Downstream Count Proof

Accessible counts before and after import:

| Surface | Before | After |
| --- | ---: | ---: |
| workpackages | 0 | 7 |
| tasks | 0 | 15 |
| apparatus | 0 | 184 |
| assignments | 0 | 0 |
| snapshots | 0 | 0 |
| issues | 0 | 0 |
| hours | 0 | 0 |
| approval queue total | 0 | 0 |
| schedule projects | 1 | 1 |
| schedule tasks with scope | 4 | 4 |
| schedule relationships | 3 | 3 |

The import created only the admitted project/workpackage/task/apparatus rows. It did not create assignments, field authorizations, schedule/status mutations, snapshots, issues, hours, approval-queue items, production rows, customer outputs, or finance outputs.

## Hosted Validation

Post-import hosted validation passed:

1. deployed mutation-seam smoke with PM intake: `RESULT PASS`,
2. operations-web hosted route smoke: `SMOKE_SUMMARY failed=0 passed=12`,
3. paired hosted PM intake smoke: `PM_INTAKE_HOSTED_SUMMARY failed=0`,
4. import-status readback: `classification=imported`, `current_candidate_match=true`, `counts_match=true`.

## Files Changed

Created:

1. `apps/mutation-seam/app/project_import_persistence.py`
2. `apps/mutation-seam/app/routers/project_imports.py`
3. `apps/mutation-seam/tests/test_project_import_persistence.py`
4. `docs/operations/APEX-PM-LANE-278-PROJECT-MINER-TEMP-POWER-APPROVED-IMPORT-MUTATION-ADMISSION-2026-05-18.md`
5. `ops/agents/packets/draft/2026-05-18-pm-lane-278-project-miner-temp-power-approved-import-mutation-admission.json`
6. `ops/agents/handoffs/2026-05-18-pm-lane-278-project-miner-temp-power-approved-import-mutation-admission-handoff.md`
7. `ops/agents/handoffs/2026-05-18-pm-lane-278-project-miner-temp-power-approved-import-mutation-admission-closeout.md`

Updated:

1. `apps/mutation-seam/app/main.py`
2. `apps/mutation-seam/app/routers/reads.py`
3. `docs/authority/APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.md`
4. `PROJECT_STATUS.md`
5. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
6. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
7. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
8. `ops/agents/handoffs/2026-05-17-desktop-codex-parallel-lane-orchestration-queue.md`
9. `ops/agents/handoffs/2026-05-18-pm-lane-278-render-project-import-route-deploy-and-live-import-executor-copy-paste-prompt.md`

## Next

Next blocker:

`STOPPED_AWAITING_FIELD_AUTHORIZATION_AND_LEAD_ASSIGNMENT_PACKET_AFTER_PROJECT_IMPORT`

The imported rows are now available for the next PM lane. Field authorization, lead/crew selection, assignment creation, schedule/status controls, durable field records, production tracking, customer reporting, and finance outputs remain separately packeted.

## Guardrails Preserved

No assignment, field authorization, lead/crew selection, schedule/status mutation, durable field record, production tracking, customer report, completion evidence, billing, payroll, invoice, accounting, external finance-system output, source workbook/PDF edit or writeback, workbook macro, direct SQL, schema migration, Vercel deploy, Olares action, DNS/auth/ingress change, new service, secret exposure, Desktop Codex PM decision authority, or autonomous AI business-state mutation was performed.
