# PM Lane 138 - Approval Persistence Hosted Application Gate Executor Copy/Paste Prompt

You are executing a bounded hosted application gate for the APEX PM lane.

## Source And Workspace

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Use the latest pushed `origin/clean-main` after PM Lane 137 closeout.
- Do not work from sibling legacy repos.
- Preserve unrelated local residue.

## Objective

Apply only `apps/mutation-seam/migrations/003_pm_import_candidate_approvals.sql` to the existing hosted Supabase database, then redeploy only the existing Render service `apex-platform-mutation-seam` so the hosted mutation seam has the approval persistence table and the approval persistence routes from clean-main.

This is a hosted application gate. It is not UI activation and not project import.

## Allowed Actions

1. Fast-forward the local repo to latest `origin/clean-main`.
2. Load `SEAM_DATABASE_URL` only from the approved non-git secret boundary or existing Render environment; do not print it.
3. Apply only `apps/mutation-seam/migrations/003_pm_import_candidate_approvals.sql`.
4. Redeploy only the existing Render service `apex-platform-mutation-seam`.
5. Verify hosted health, OpenAPI route registration, schema/trigger presence, and hosted smokes.
6. Produce a closeout handoff with exact non-secret evidence.

## Prohibited Actions

- No operations-web approval POST wiring.
- No approval button.
- No operations-web deployment unless a separate packet explicitly admits it.
- No project import mutation.
- No generic mutation-pipeline registration for `pm_import_candidate_approval`.
- No new hosted service.
- No DNS, auth, ingress, or secret change unless the current DSN is broken and the coordinator explicitly approves repair.
- No secret values in repo files, handoffs, logs, or chat.
- No fixture replay into live data.
- No live POST smoke that creates an approval record.
- No workbook macro execution or workbook writeback.
- No direct Excel-to-Supabase write.
- No project, workpackage, task, apparatus, issue, assignment, schedule, status, durable field record, production tracking, work order, field release, or AI business-state mutation.

## Local Preflight

Run from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
git fetch origin
git checkout clean-main
git pull --ff-only origin clean-main
git status --short
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m py_compile apps/mutation-seam/app/project_import_approval_persistence.py apps/mutation-seam/app/db/supabase_store.py apps/mutation-seam/app/audit/logger.py apps/mutation-seam/app/services/mutation_pipeline.py
$env:SEAM_STORE_BACKEND='memory'; & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_project_import_approval_persistence.py apps/mutation-seam/tests/test_project_import_approval_contract.py apps/mutation-seam/tests/test_project_import_approval_storage_plan.py apps/mutation-seam/tests/test_project_import_admission_plan.py apps/mutation-seam/tests/test_project_import_candidate.py apps/mutation-seam/tests/test_pipeline_integration.py
```

Stop if the repo is not clean except known unrelated residue, or if focused tests fail.

## Apply Migration

Load the runtime DSN without echoing it. Then apply only migration 003:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import os,pathlib,psycopg2; sql=pathlib.Path('apps/mutation-seam/migrations/003_pm_import_candidate_approvals.sql').read_text(encoding='utf-8'); conn=psycopg2.connect(os.environ['SEAM_DATABASE_URL']); conn.autocommit=True; conn.cursor().execute(sql); print('migration-003-applied')"
```

## Schema Proof

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import os,psycopg2; conn=psycopg2.connect(os.environ['SEAM_DATABASE_URL']); cur=conn.cursor(); cur.execute(\"select to_regclass('seam.pm_import_candidate_approvals') is not null, exists(select 1 from pg_trigger where tgname='trg_pm_import_candidate_approvals_insert_only_update'), exists(select 1 from pg_trigger where tgname='trg_pm_import_candidate_approvals_insert_only_delete')\"); print(cur.fetchone())"
```

Expected tuple: `(True, True, True)`.

## Render Redeploy

Redeploy only the existing Render service:

- Service: `apex-platform-mutation-seam`
- Root directory must remain `apps/mutation-seam`
- Existing `SEAM_DATABASE_URL` env var must remain present and secret.
- Do not create a new Render service.

Record non-secret deploy evidence: service name, deploy id or timestamp, deployed commit, and final live state.

## Hosted Proof

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

The standard hosted smokes now verify:

1. OpenAPI registration for `GET /api/v1/reads/project-import-approval-status`,
2. hosted readback from `GET /api/v1/reads/project-import-approval-status`,
3. OpenAPI registration for `POST /api/v1/mutations/project-import-approvals`.

They must not send a live approval POST or create an approval row.

OpenAPI route proof:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json,urllib.request; p=json.load(urllib.request.urlopen('https://mutation-seam.apexpowerops.com/openapi.json', timeout=20)); assert '/api/v1/mutations/project-import-approvals' in p['paths']; assert 'post' in p['paths']['/api/v1/mutations/project-import-approvals']; assert '/api/v1/reads/project-import-approval-status' in p['paths']; assert 'get' in p['paths']['/api/v1/reads/project-import-approval-status']; print('approval-routes-hosted')"
```

## Closeout Required

Create one closeout handoff under:

`C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/`

Use the PM Lane 138 section of:

`C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md`

Include:

1. source commit,
2. exact migration command result without DSN,
3. schema proof tuple,
4. Render service/deploy evidence,
5. non-secret `SEAM_DATABASE_URL` presence confirmation,
6. hosted mutation-seam smoke result,
7. paired PM intake hosted smoke result,
8. OpenAPI approval POST and approval-status GET route proof,
9. explicit guardrail confirmation,
10. blocker classification if anything is red.

Do not stage, commit, push, or alter unrelated files unless explicitly instructed by the coordinator.
