# PM Lane 278 - Approved Import Mutation Admission Closeout

Date: 2026-05-18

Decision label:

`PROJECT_MINER_TEMP_POWER_APPROVED_IMPORT_MUTATION_ADMISSION`

Selected outcome:

`ROUTE_ADMITTED_LOCAL_PASS_HOSTED_DEPLOY_REQUIRED_NO_LIVE_IMPORT`

## Result

PM Lane 278 is complete as a repo implementation and deployment-dispatch tranche.

The Project Miner Temp Power import mutation route is now implemented, tested, committed, and pushed to `clean-main`.

Implementation commit:

`4d5af24f`

Commit message:

`Admit PM Lane 278 import route`

The route is:

`POST /api/v1/mutations/project-imports`

The status readback is:

`GET /api/v1/reads/project-import-status`

The route admits only the approved Temp Power candidate after the PM Lane 277 approval row. It writes deterministic project, workpackage, task, and apparatus rows through the existing application store, embeds source trace evidence on imported task/apparatus rows, embeds warning-review evidence on the imported project row, records an audit event, and caches idempotency.

## Local Validation

Focused validation passed:

```text
15 passed, 16 warnings
```

Command:

```powershell
..\..\.venv\Scripts\python.exe -m pytest tests/test_project_import_persistence.py tests/test_project_import_approval_persistence.py tests/test_project_import_admission_plan.py
```

The warnings were existing Pydantic class-config deprecation warnings and openpyxl data-validation warnings.

Validation covered:

1. no-approval import rejection,
2. accepted approval-backed import,
3. deterministic project/workpackage/task/apparatus row counts,
4. source trace and warning-review count proof,
5. same-payload replay returning `idempotent_hit`,
6. mismatched replay rejection,
7. non-PM, offline, and wrong-class rejection,
8. import-status readback returning `imported`,
9. assignment, snapshot, issue, and hour counts unchanged.

## Hosted Check

After `4d5af24f` was pushed, hosted preflight still showed the PM Lane 277 approval row is current:

| Field | Value |
| --- | --- |
| classification | `approved_for_import_packet` |
| approval record count | `1` |
| current candidate match | `true` |
| approval record id | `pm-import-approval-03a1aea39afde71b44516f44` |
| import authority | `not_admitted` |

Hosted route availability check still returned `404` after the push and a short wait:

| Hosted route | Result |
| --- | --- |
| `POST /api/v1/mutations/project-imports` | `404 {"detail":"Not Found"}` |
| `GET /api/v1/reads/project-import-status` | `404 {"detail":"Not Found"}` |

This shell has no `render` CLI and no Render environment surface exposed. Therefore no hosted live import was attempted from this shell.

## Files Changed

Created:

1. `apps/mutation-seam/app/project_import_persistence.py`
2. `apps/mutation-seam/app/routers/project_imports.py`
3. `apps/mutation-seam/tests/test_project_import_persistence.py`
4. `docs/operations/APEX-PM-LANE-278-PROJECT-MINER-TEMP-POWER-APPROVED-IMPORT-MUTATION-ADMISSION-2026-05-18.md`
5. `ops/agents/packets/draft/2026-05-18-pm-lane-278-project-miner-temp-power-approved-import-mutation-admission.json`
6. `ops/agents/handoffs/2026-05-18-pm-lane-278-project-miner-temp-power-approved-import-mutation-admission-handoff.md`
7. `ops/agents/handoffs/2026-05-18-pm-lane-278-project-miner-temp-power-approved-import-mutation-admission-closeout.md`
8. `ops/agents/handoffs/2026-05-18-pm-lane-278-render-project-import-route-deploy-and-live-import-executor-copy-paste-prompt.md`

Updated:

1. `apps/mutation-seam/app/main.py`
2. `apps/mutation-seam/app/routers/reads.py`
3. `docs/authority/APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.md`
4. `PROJECT_STATUS.md`
5. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
6. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
7. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
8. `ops/agents/handoffs/2026-05-17-desktop-codex-parallel-lane-orchestration-queue.md`

## Executor Dispatch

Because hosted still serves the pre-route build, PM Lane 278 now has an authenticated Render executor prompt:

`ops/agents/handoffs/2026-05-18-pm-lane-278-render-project-import-route-deploy-and-live-import-executor-copy-paste-prompt.md`

The executor prompt requires deploying the existing Render service to `4d5af24f`, proving candidate and approval-status preflight, executing one live import POST only if the deployed route and preflight match, replaying the exact payload, and recording downstream count proof.

## Next

Next blocker:

`STOPPED_AWAITING_RENDER_DEPLOY_OF_PROJECT_IMPORT_ROUTE`

Once the existing Render service is deployed to `4d5af24f`, the admitted next action is the PM Lane 278 hosted import executor path. It should not require another stakeholder approval if the preflight identity still matches and the executor stays inside the packet.

## Guardrails Preserved

No hosted live import, assignment, field authorization, lead/crew selection, schedule/status mutation, durable field record, production tracking, customer report, completion evidence, billing, payroll, invoice, accounting, external finance-system output, source workbook/PDF edit or writeback, workbook macro, direct SQL, schema migration, Render deploy from this shell, Vercel deploy, Olares action, DNS/auth/ingress change, new service, secret exposure, Desktop Codex PM decision authority, or autonomous AI business-state mutation was performed.
