# PM Lane 138 - Approval Persistence Hosted Application Gate Closeout

## Header

Packet: PM Lane 138 - Approval Persistence Hosted Application Gate

Executor: VS Code Codex with native Supabase connector

Date: 2026-05-16 17:58:45 -07:00

Status: PASS

Source repository: `C:/APEX Platform/apex-power-ops-platform`

Source branch: `clean-main`

Source commit tested: `21df246de774f7cabdca53ae1c076a5c5b4f5f4c`

Hosted surface: Supabase project `resa-power-db` (`fxoyniqnrlkxfligbxmg`) plus existing Render mutation seam `https://mutation-seam.apexpowerops.com`

## Scope Executed

Applied exactly the approval persistence schema gate for Project Miner import-candidate approvals.

Executed scope:

1. verified local repo source floor at `21df246de774f7cabdca53ae1c076a5c5b4f5f4c`,
2. ran local PM Lane 138 preflight,
3. verified hosted approval table and triggers were absent before migration,
4. applied the exact SQL body from `apps/mutation-seam/migrations/003_pm_import_candidate_approvals.sql` through the native Supabase connector,
5. proved the hosted approval table and insert-only triggers exist,
6. proved no approval records were created by the gate,
7. ran hosted mutation-seam and paired PM-intake smokes,
8. proved OpenAPI registration for approval-status GET and approval POST.

No manual Render redeploy was triggered from this surface. After migration application, the existing hosted mutation seam already exposed the approval-status GET route and approval POST OpenAPI registration, and both hosted smokes passed. This means the existing Render service was already serving a current enough clean-main build for this gate.

## Changed Files

No repo files were changed by the hosted executor action before this closeout.

This closeout file and status/doc updates are coordinator publication artifacts after successful hosted proof.

## Hosted Action Evidence

Supabase:

1. project name: `resa-power-db`,
2. project id/ref: `fxoyniqnrlkxfligbxmg`,
3. migration tool result: `{"success": true}`,
4. migration name used by connector: `pm_lane_138_003_pm_import_candidate_approvals`,
5. migration SQL source: `apps/mutation-seam/migrations/003_pm_import_candidate_approvals.sql`.

Schema proof:

```text
approval_table_exists=true
update_trigger_exists=true
delete_trigger_exists=true
approval_record_count=0
```

Render:

1. existing service: `apex-platform-mutation-seam`,
2. public host: `https://mutation-seam.apexpowerops.com`,
3. manual redeploy from this surface: not performed,
4. deploy id: not observed from this surface,
5. hosted route proof: current approval-status GET and approval POST OpenAPI registration were live after migration.

Secret boundary:

1. no `SEAM_DATABASE_URL` value was accessed, printed, stored, or committed,
2. no Render env var was changed,
3. native Supabase connector handled the schema gate without exposing database credentials.

Tooling note:

The Apex-specific bounded Supabase MCP read-only query path returned a stale pooler authentication error. The native Supabase connector was authenticated and successfully executed the migration/proof path. This is a connector-credential maintenance gap, not a blocker for PM Lane 138.

## Validation Commands And Results

Local preflight:

```powershell
git fetch origin
git rev-parse HEAD
git rev-parse origin/clean-main
git status --short
```

Result:

```text
HEAD and origin/clean-main: 21df246de774f7cabdca53ae1c076a5c5b4f5f4c
Only pre-existing unrelated local residue was present.
```

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m py_compile apps/mutation-seam/app/project_import_approval_persistence.py apps/mutation-seam/app/db/supabase_store.py apps/mutation-seam/app/audit/logger.py apps/mutation-seam/app/services/mutation_pipeline.py
```

Result: passed.

```powershell
$env:SEAM_STORE_BACKEND='memory'; & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest apps/mutation-seam/tests/test_project_import_approval_persistence.py apps/mutation-seam/tests/test_project_import_approval_contract.py apps/mutation-seam/tests/test_project_import_approval_storage_plan.py apps/mutation-seam/tests/test_project_import_admission_plan.py apps/mutation-seam/tests/test_project_import_candidate.py apps/mutation-seam/tests/test_pipeline_integration.py
```

Result:

```text
33 passed, 22 warnings
```

Pre-migration schema check through native Supabase connector:

```sql
select to_regclass('seam.pm_import_candidate_approvals') is not null as approval_table_exists,
       exists(select 1 from pg_trigger where tgname='trg_pm_import_candidate_approvals_insert_only_update') as update_trigger_exists,
       exists(select 1 from pg_trigger where tgname='trg_pm_import_candidate_approvals_insert_only_delete') as delete_trigger_exists;
```

Result:

```text
approval_table_exists=false
update_trigger_exists=false
delete_trigger_exists=false
```

Migration application:

```text
native Supabase connector apply_migration
project_id=fxoyniqnrlkxfligbxmg
name=pm_lane_138_003_pm_import_candidate_approvals
query=<exact contents of apps/mutation-seam/migrations/003_pm_import_candidate_approvals.sql>
```

Result:

```json
{"success": true}
```

Post-migration schema proof:

```sql
select to_regclass('seam.pm_import_candidate_approvals') is not null as approval_table_exists,
       exists(select 1 from pg_trigger where tgname='trg_pm_import_candidate_approvals_insert_only_update') as update_trigger_exists,
       exists(select 1 from pg_trigger where tgname='trg_pm_import_candidate_approvals_insert_only_delete') as delete_trigger_exists,
       (select count(*) from seam.pm_import_candidate_approvals) as approval_record_count;
```

Result:

```text
approval_table_exists=true
update_trigger_exists=true
delete_trigger_exists=true
approval_record_count=0
```

Hosted mutation-seam smoke:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
```

Result:

```text
health status=200 detail=ok
root status=200 detail=ok
reads_approval_queue status=200 detail=ok
schedule_projects status=200 detail=ok
schedule_drivers status=200 detail=ok
schedule_tracer status=200 detail=ok
schedule_variance status=200 detail=ok
openapi status=200 detail=ok
project_import_candidate status=200 detail=ok
project_import_admission_plan status=200 detail=ok
project_import_approval_contract status=200 detail=ok
project_import_approval_storage_plan status=200 detail=ok
project_import_approval_status status=200 detail=ok
RESULT PASS
```

Paired PM-intake hosted smoke:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

Result:

```text
PM_INTAKE_HOSTED_SUMMARY failed=0 operations_web_base_url=https://operations.apexpowerops.com/ mutation_seam_base_url=https://mutation-seam.apexpowerops.com/
```

OpenAPI route proof:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json,urllib.request; paths=json.load(urllib.request.urlopen('https://mutation-seam.apexpowerops.com/openapi.json', timeout=20))['paths']; assert '/api/v1/mutations/project-import-approvals' in paths; assert 'post' in paths['/api/v1/mutations/project-import-approvals']; assert '/api/v1/reads/project-import-approval-status' in paths; assert 'get' in paths['/api/v1/reads/project-import-approval-status']; print('approval-routes-hosted')"
```

Result:

```text
approval-routes-hosted
```

## Final Verdict

```text
PASS
```

## Remaining Blocker Classification

None for PM Lane 138.

The Apex-specific bounded Supabase MCP credential should be refreshed separately so future read-only SQL proof can use the bounded connector again. The native Supabase connector is working.

## Guardrails Confirmed

1. no new hosted service,
2. no DNS change,
3. no auth widening,
4. no ingress widening,
5. no secret value printed or committed,
6. no secret rotation,
7. only migration 003 was applied,
8. no SQL other than migration 003 was executed,
9. no fixture replay,
10. approval persistence was admitted only as the dedicated table/schema gate,
11. no approval row was created,
12. no live approval POST smoke,
13. no operations-web approval POST wiring,
14. no approval button,
15. no import mutation,
16. no assignment, schedule, status, issue, task, workpackage, project, production tracking, workbook, direct Excel write, workbook macro, workbook writeback, field release, work order, or autonomous AI business-state mutation.

## Coordinator Recommendation

```text
ACCEPT_AND_CLOSE
```

Next recommended lane: keep frontend approval controls and project import blocked. The next safe PM lane should either repair the stale Apex bounded Supabase MCP credential as tooling maintenance or author the next no-write review/approval readiness step before any approval POST UI activation is admitted.
