# PM Lane 038 Sidecar Handoff - Import Approval Persistence Design Scout

Date: 2026-05-15
Status: Read-only sidecar recommendation
Scope: next product lane after hosted PM intake Render parity

## Summary

The sidecar scout recommends that the next local PM product lane after hosted PM intake reads are truly current should be approval-persistence design only, not import execution.

The goal is to persist the PM decision for `pm-import-candidate-miner-temp-power` while keeping project, workpackage, task, and apparatus import rows blocked.

## Proposed Objective

Define and locally validate a governed PM approval record for the import candidate that captures:

1. PM decision,
2. candidate id and version,
3. source stat fingerprint,
4. candidate shape fingerprint,
5. warning-code acceptance,
6. no-go override notes,
7. reviewer notes,
8. actor and timestamp metadata.

This lane should not import rows.

## Write Scope Candidates

Likely backend scope:

1. `apps/mutation-seam/app/project_import_approval.py` or similar explicit approval entity module,
2. `apps/mutation-seam/app/services/mutation_pipeline.py` only if the existing governed Class C pipeline can admit a new import-candidate approval action cleanly,
3. `apps/mutation-seam/app/db/memory_store.py` and `apps/mutation-seam/app/db/supabase_store.py` only if a minimal explicit approval record store is admitted,
4. `apps/mutation-seam/app/routers/reads.py` for approval status/history readback,
5. focused backend tests for PM-only approval, idempotency, stale fingerprint rejection, and decision-history visibility.

Optional frontend scope after backend shape is proven:

1. `apps/operations-web/app/pm-review/import-candidate/page.tsx`,
2. `apps/operations-web/app/pm-review/import-admission-plan/page.tsx`,
3. focused Playwright smokes for approval status display and zero import mutation.

## Existing Patterns To Reuse

Use these as the design anchors:

1. `apps/mutation-seam/app/project_import_admission_plan.py` for the approval record contract, required fields, permitted decisions, minimum expected values, diff checks, and no-go posture.
2. `apps/mutation-seam/app/project_import_candidate.py` for candidate versioning, `mutation_authority: not_admitted`, source freshness, and candidate shape inputs.
3. `apps/mutation-seam/app/services/mutation_pipeline.py` for governed mutation structure: idempotency, Class C validation, role validation, entity load, payload validation, audit, and idempotency save.
4. `apps/mutation-seam/tests/test_pipeline_integration.py` for PM-only Class C action proof, audit exactly once, idempotent replay, and decision-history visibility.
5. `apps/mutation-seam/app/db/supabase_store.py` for current narrow JSON persistence adapter patterns.

## Recommended Validation

Backend local slice:

```powershell
$env:SEAM_STORE_BACKEND = "memory"
.venv/Scripts/python.exe -m pytest apps/mutation-seam/tests/test_project_import_candidate.py apps/mutation-seam/tests/test_project_import_admission_plan.py
.venv/Scripts/python.exe -m pytest apps/mutation-seam/tests/test_pipeline_integration.py apps/mutation-seam/tests/test_pm_issue_disposition.py
```

Frontend slice only if UI is touched:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
cd apps/operations-web
corepack pnpm exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts
```

## Guardrails

Keep this lane explicitly limited to approval persistence:

1. no project rows,
2. no workpackage rows,
3. no task rows,
4. no apparatus rows,
5. no workbook writeback,
6. no macro execution,
7. no schedule, status, or assignment mutation,
8. no autonomous AI business-state action,
9. no direct Supabase writes outside the governed seam/store path,
10. reject stale approvals when candidate id, version, source fingerprint, shape fingerprint, or warning-code set differs from the current candidate.

## Risks

The main risk is storage ownership. If approval persistence must survive hosted Render/Supabase, the lane needs a small governed storage decision before implementation.

The second risk is overloading existing production PM entity mutations. The scout recommends a small explicit import-candidate approval entity rather than smuggling candidate approval into issue/task/workpackage mutations or relying on audit log alone.

## Sidecar Boundary

The sidecar did not edit, stage, commit, deploy, or access live services. The recommendation is captured here so the coordinator can use it after PM Lane 037 closes or precisely classifies the Render blocker.
