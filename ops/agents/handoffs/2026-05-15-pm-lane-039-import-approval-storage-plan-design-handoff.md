# PM Lane 039 Handoff - Import Approval Storage-Plan Design

Date: 2026-05-15
Status: Locally executed, read-only
Scope: Project Miner import approval storage decision before schema, approval persistence, or import mutation

## Executive Summary

PM Lane 039 chooses the future storage shape for Project Miner import approval records without implementing that storage.

The selected future shape is:

1. table: `seam.pm_import_candidate_approvals`,
2. entity type: `pm_import_candidate_approval`,
3. future route: `/api/v1/mutations/project-import-approvals`,
4. write model: insert-once with strict idempotent replay.

This is a storage decision only. It does not create a table, persist approval, write Supabase rows, or import project rows.

## What Changed

Backend:

1. `apps/mutation-seam/app/project_import_approval_storage_plan.py`
2. `apps/mutation-seam/app/project_import_approval_contract.py`
3. `apps/mutation-seam/app/routers/reads.py`
4. `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
5. `apps/mutation-seam/tests/test_project_import_approval_storage_plan.py`

Docs and governance:

1. `PROJECT_STATUS.md`
2. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
3. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
4. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
5. `ops/agents/packets/draft/2026-05-15-pm-lane-039-import-approval-storage-plan-design.json`

## New Read Endpoint

```text
GET /api/v1/reads/project-import-approval-storage-plan
```

The endpoint returns a read-only storage decision plan derived from the PM Lane 038 approval contract. It includes:

1. selected future table, route, and entity type,
2. contract dependency and candidate identity,
3. record lifecycle,
4. recommended columns,
5. recommended constraints,
6. adapter requirements,
7. readback requirements,
8. rejected storage shortcuts,
9. future admission sequence,
10. explicit `not_allowed_now`.

## Storage Shortcuts Rejected

The plan rejects:

1. audit-log-only approval storage,
2. reusing issue, task, or workpackage rows for pre-import approval,
3. browser-local storage as canonical approval,
4. generic PgDict upsert without an explicit approval adapter,
5. direct Supabase writes from Excel or UI.

## Sidecar Result

The read-only sidecar completed without edits, staging, commit, deployment, live-service access, or tests.

Its key conclusion matched the implementation: keep Lane 039 design-only. Actual persistence is unsafe until a dedicated table and adapter are admitted because the default mutation-seam store is Supabase-backed, no approval collection exists, and the generic mutation pipeline does not own `pm_import_candidate_approval`.

## Validation

Commands run from:

```text
C:/APEX Platform/apex-power-ops-platform
```

Focused backend tests:

```powershell
$env:SEAM_STORE_BACKEND='memory'
.venv/Scripts/python.exe -m pytest apps/mutation-seam/tests/test_project_import_candidate.py apps/mutation-seam/tests/test_project_import_admission_plan.py apps/mutation-seam/tests/test_project_import_approval_contract.py apps/mutation-seam/tests/test_project_import_approval_storage_plan.py -q
```

Result:

```text
12 passed
```

Additional validation:

1. `py_compile` passed for the approval-contract module, storage-plan module, and deployed smoke script.
2. PM Lane 039 packet JSON and refreshed PM Lane 037 packet JSON parsed successfully.
3. Scoped `git diff --check` passed for the Lane 039 file set.

## Guardrails Preserved

This tranche does not authorize:

1. schema migration,
2. approval persistence,
3. import mutation,
4. mutation pipeline action admission,
5. store adapter write path,
6. SQL write,
7. live database write,
8. workbook macro execution,
9. workbook writeback,
10. Render deployment,
11. Vercel promotion,
12. service admission,
13. auth or ingress widening,
14. assignment mutation,
15. schedule mutation,
16. status mutation,
17. autonomous AI business-state mutation.

## Next Recommended Move

Keep PM Lane 037 active for hosted Render parity. The next PM product slice should be `Import Candidate Approval Persistence Schema And Adapter Admission`, only after hosted reads are current or the Render blocker is precisely classified.
