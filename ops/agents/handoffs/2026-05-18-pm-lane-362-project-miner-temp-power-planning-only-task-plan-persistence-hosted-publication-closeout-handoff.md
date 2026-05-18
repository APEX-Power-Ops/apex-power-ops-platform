# PM Lane 362 Hosted Closeout

Packet: PM Lane 362 / Project Miner Temp Power planning-only task-plan persistence hosted publication

Executor: GitHub Copilot

Date: 2026-05-18

Status: PASS

Source repository: `jasonlswenson-sys/apex-power-ops`

Source branch: `clean-main`

Published commit: `974a2b84`

Hosted surfaces:

1. operations web production alias `https://operations.apexpowerops.com`
2. mutation seam custom domain `https://mutation-seam.apexpowerops.com`
3. mutation seam onrender host `https://apex-platform-mutation-seam.onrender.com`

## Scope Executed

Completed the hosted follow-through after the repo-local PM Lane 361 admission:

1. published the bounded PM Lane 360 and PM Lane 361 snapshot to `clean-main`
2. confirmed Render served the new task-plan status route on both hosted mutation-seam origins
3. confirmed Vercel built ready preview deployment `dpl_9XgCmYssXwQ9pDbFTKUR8z4c2S7V`
4. promoted that preview into production deployment `dpl_57kPKq8kSeeYHCX65Y6qPdKWeh1d`
5. verified production HTML for `/pm-review/import-candidate` includes the new task-plan UI and updated authority-boundary copy
6. verified production `/pm-review/import-approval-readiness` includes the staged review-context surfaces
7. ran the repo-owned hosted PM intake smoke against production
8. recorded hosted closeout evidence in the repo status ledger and this handoff

## Changed Files

1. `PROJECT_STATUS.md`
2. `ops/agents/handoffs/2026-05-18-pm-lane-362-project-miner-temp-power-planning-only-task-plan-persistence-hosted-publication-closeout-handoff.md`

## Hosted Action Evidence

Git publication:

1. bounded publish commit: `974a2b84`
2. push target: `origin clean-main`

Vercel:

1. ready preview deployment: `dpl_9XgCmYssXwQ9pDbFTKUR8z4c2S7V`
2. preview URL: `https://apex-operations-jpuyfwldf-jasonlswenson-sys-projects.vercel.app`
3. promoted production deployment: `dpl_57kPKq8kSeeYHCX65Y6qPdKWeh1d`
4. production alias: `https://operations.apexpowerops.com`

Render:

1. hosted task-plan status route responds on `https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-task-plan-status`
2. hosted task-plan status route responds on `https://apex-platform-mutation-seam.onrender.com/api/v1/reads/project-import-task-plan-status`
3. hosted OpenAPI includes both `project-import-task-plans` and `project-import-task-plan-status`

## Validation Commands And Results

Repo-local validation before publication:

```powershell
Set-Location "C:/APEX Platform/apex-power-ops-platform"
corepack pnpm --dir . --filter @apex/operations-web build
.\.venv\Scripts\python.exe -m pytest apps/mutation-seam/tests/test_project_import_task_plan_persistence.py apps/mutation-seam/tests/test_pm_workfront_read_model.py -q
```

Result:

```text
operations-web build passed
7 passed
```

Focused browser-route validation before publication:

```text
runTests -> apps/operations-web/tests/browser-shell.pm-import-candidate.smoke.spec.ts
runTests -> apps/operations-web/tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts
```

Result:

```text
2 passed
```

Vercel deployment inspection and promotion:

```powershell
Set-Location "C:/APEX Platform/apex-power-ops-platform"
corepack pnpm dlx vercel ls apex-operations-web --scope jasonlswenson-sys-projects
corepack pnpm dlx vercel inspect https://apex-operations-jpuyfwldf-jasonlswenson-sys-projects.vercel.app --scope jasonlswenson-sys-projects
corepack pnpm dlx vercel promote https://apex-operations-jpuyfwldf-jasonlswenson-sys-projects.vercel.app --scope jasonlswenson-sys-projects --yes --non-interactive
corepack pnpm dlx vercel inspect https://apex-operations-nolav8msk-jasonlswenson-sys-projects.vercel.app --scope jasonlswenson-sys-projects
```

Result:

```text
preview dpl_9XgCmYssXwQ9pDbFTKUR8z4c2S7V was ready and production dpl_57kPKq8kSeeYHCX65Y6qPdKWeh1d reached ready with alias https://operations.apexpowerops.com
```

Hosted PM smoke:

```powershell
Set-Location "C:/APEX Platform/apex-power-ops-platform/apps/operations-web"
corepack pnpm run smoke:pm-intake-hosted
```

Result:

```text
PM_INTAKE_HOSTED_SUMMARY failed=0 operations_web_base_url=https://operations.apexpowerops.com/ mutation_seam_base_url=https://mutation-seam.apexpowerops.com/
```

Hosted route proof:

```powershell
curl https://operations.apexpowerops.com/pm-review/import-candidate
curl https://mutation-seam.apexpowerops.com/openapi.json
curl -H "Authorization: Bearer <pm token>" https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-task-plan-status
```

Result:

```text
operations-web production HTML includes `explicitly persist a durable task plan`, `Durable Task Plan`, and `Persist durable task plan`
hosted OpenAPI includes `project-import-task-plans` and `project-import-task-plan-status`
hosted task-plan status readback returns classification `no_task_plan_record`
```

## Final Verdict

```text
PASS
```

## Guardrails Confirmed

1. hosted availability now includes only the already admitted planning-only task-plan slice: confirmed
2. no approval persistence write admission: confirmed
3. no full project import admission: confirmed
4. no assignment admission: confirmed
5. no schedule or status mutation admission: confirmed
6. no finance or customer-billing-delivery widening: confirmed
7. no source workbook or PDF writeback: confirmed
8. no SQL schema migration in this hosted tranche: confirmed
9. no autonomous AI business-state mutation: confirmed

## Coordinator Recommendation

```text
ACCEPT_AND_CLOSE
```