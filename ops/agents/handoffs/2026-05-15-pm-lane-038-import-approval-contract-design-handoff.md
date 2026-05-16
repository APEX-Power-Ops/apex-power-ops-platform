# PM Lane 038 Handoff - Import Approval Contract Design

Date: 2026-05-15
Status: Locally executed, read-only
Scope: Project Miner import approval contract design before approval persistence or import mutation

## Executive Summary

PM Lane 038 adds the next PM workflow building block after the import-admission plan: a read-only approval contract for `pm-import-candidate-miner-temp-power`.

The goal is to make the future PM approval packet explicit before any approval record can be stored or any import rows can be written.

## What Changed

Backend:

1. `apps/mutation-seam/app/project_import_approval_contract.py`
2. `apps/mutation-seam/app/routers/reads.py`
3. `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
4. `apps/mutation-seam/tests/test_project_import_approval_contract.py`

Docs and governance:

1. `PROJECT_STATUS.md`
2. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
3. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
4. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
5. `ops/agents/packets/draft/2026-05-15-pm-lane-038-import-approval-contract-design.json`

## New Read Endpoint

```text
GET /api/v1/reads/project-import-approval-contract
```

The endpoint returns a read-only contract derived from the current import-admission plan. It includes:

1. approval contract id and version,
2. candidate id and version,
3. mutation authority and persistence authority,
4. required approval fields,
5. permitted decisions,
6. expected source fingerprint, shape fingerprint, idempotency key, and warning codes,
7. human-acceptance no-go acknowledgement policy,
8. non-overridable blocked checks,
9. decision payload template,
10. validation matrix,
11. future mutation contract placeholder,
12. explicit `not_allowed_now`.

## Hosted Smoke Update

The existing deployed-seam smoke flag now checks the approval contract too:

```powershell
.venv/Scripts/python.exe apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
```

Under `--include-pm-intake`, it now expects OpenAPI and read payload proof for:

1. `/api/v1/reads/project-import-candidate`,
2. `/api/v1/reads/project-import-admission-plan`,
3. `/api/v1/reads/project-import-approval-contract`.

## Validator Behavior

`validate_project_import_approval_payload()` is pure and local. It does not call the mutation pipeline, store adapters, Supabase, Render, Vercel, Excel, or workbook macros.

It rejects:

1. missing required fields,
2. unsupported decisions,
3. stale candidate id/version/source fingerprint/shape fingerprint/idempotency key,
4. changed warning-code acceptance set,
5. missing or extra human-acceptance no-go acknowledgements,
6. attempted acknowledgement of non-overridable checks,
7. empty PM review notes,
8. missing PM actor id,
9. missing approval timestamp.

## Sidecar Result

The sidecar scout completed read-only and did not edit, stage, commit, deploy, hit live services, or run tests.

Its key recommendation was accepted:

1. keep this lane out of `mutation_pipeline.py`,
2. keep this lane out of store adapters,
3. add a pure local contract and validator,
4. expose a GET-only read if useful,
5. defer persistence until a later storage packet.

## Validation

Commands run from:

```text
C:/APEX Platform/apex-power-ops-platform
```

Focused backend tests:

```powershell
$env:SEAM_STORE_BACKEND='memory'
.venv/Scripts/python.exe -m pytest apps/mutation-seam/tests/test_project_import_candidate.py apps/mutation-seam/tests/test_project_import_admission_plan.py apps/mutation-seam/tests/test_project_import_approval_contract.py -q
```

Result:

```text
8 passed
```

Additional validation:

1. `py_compile` passed for `project_import_approval_contract.py` and `smoke_deployed_mutation_seam.py`.
2. Packet JSON parsed successfully.
3. Scoped `git diff --check` passed for the Lane 038 file set.

## Guardrails Preserved

This tranche does not authorize:

1. approval persistence,
2. import mutation,
3. `mutation_pipeline.py` action admission,
4. store adapter write path,
5. SQL or schema migration,
6. live database write,
7. workbook macro execution,
8. workbook writeback,
9. Render deployment,
10. Vercel promotion,
11. service admission,
12. auth or ingress widening,
13. assignment mutation,
14. schedule mutation,
15. status mutation,
16. autonomous AI business-state mutation.

## Next Recommended Move

Keep PM Lane 037 active for Render-hosted backend parity. In parallel, the next PM product slice should decide the smallest governed storage surface for an import approval record, still without importing project/workpackage/task/apparatus rows.
