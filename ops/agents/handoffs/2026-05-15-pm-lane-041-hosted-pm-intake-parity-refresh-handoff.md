# PM Lane 041 Handoff - Hosted PM Intake Parity Refresh And Blocker Classification

Date: 2026-05-15
Status: Authored, read-only local proof complete, ready for authenticated hosted executors
Scope: Hosted operations-web and mutation-seam parity after PM Lane 040

## Executive Summary

PM Lane 041 refreshes the hosted parity gate after Lane 040.

The local product stack now includes:

```text
/pm-review/import-candidate
/pm-review/import-admission-plan
/pm-review/import-approval-readiness
GET /api/v1/reads/project-import-candidate
GET /api/v1/reads/project-import-admission-plan
GET /api/v1/reads/project-import-approval-contract
GET /api/v1/reads/project-import-approval-storage-plan
```

Hosted proof is currently split:

1. `https://operations.apexpowerops.com/pm-review/import-candidate` passes.
2. `https://operations.apexpowerops.com/pm-review/import-admission-plan` passes.
3. `https://operations.apexpowerops.com/pm-review/import-approval-readiness` returns `404`.
4. `https://mutation-seam.apexpowerops.com/health` returns `200`.
5. Hosted mutation-seam OpenAPI is missing all four current PM intake reads.
6. Hosted mutation-seam returns `404` for all four current PM intake reads.
7. Hosted mutation-seam schedule reads still return `500`.

This lane does not admit approval persistence or import. It creates the executor-ready hosted parity plan.

## Local Capability Verdict

This workspace can run read-only public probes and publish repo-visible packet/handoff evidence.

It cannot currently perform the hosted repairs directly:

1. no `render` CLI was found,
2. no `RENDER_*` environment names were present,
3. no `vercel` CLI binary was found,
4. no `VERCEL_*` environment names were present,
5. `pnpm dlx vercel whoami` timed out waiting for authentication and was stopped.

## Read-Only Hosted Evidence

Hosted PM intake smoke:

```powershell
corepack pnpm --dir apps/operations-web smoke:pm-intake-hosted
```

Result:

```text
PM_INTAKE_HOSTED_OK operations-web import candidate
PM_INTAKE_HOSTED_OK operations-web import admission plan
PM_INTAKE_HOSTED_FAIL operations-web import approval readiness operations-web import approval readiness returned HTTP 404
PM_INTAKE_HOSTED_OK mutation seam health
PM_INTAKE_HOSTED_FAIL mutation seam OpenAPI intake read paths mutation seam OpenAPI is missing /api/v1/reads/project-import-candidate
PM_INTAKE_HOSTED_FAIL mutation seam import candidate read mutation seam import candidate read returned HTTP 404
PM_INTAKE_HOSTED_FAIL mutation seam import admission plan read mutation seam import admission plan read returned HTTP 404
PM_INTAKE_HOSTED_FAIL mutation seam import approval contract read mutation seam import approval contract read returned HTTP 404
PM_INTAKE_HOSTED_FAIL mutation seam import approval storage plan read mutation seam import approval storage plan read returned HTTP 404
PM_INTAKE_HOSTED_SUMMARY failed=6
```

Deployed mutation-seam smoke:

```powershell
.venv/Scripts/python.exe apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
```

Result:

```text
health status=200
root status=200
reads_approval_queue status=200
schedule_projects status=500
schedule_drivers status=500
schedule_tracer status=500
schedule_variance status=500
openapi status=200
project_import_candidate status=404
project_import_admission_plan status=404
project_import_approval_contract status=404
project_import_approval_storage_plan status=404
RESULT FAIL
```

## Dual Executor Plan

Use two bounded hosted lanes only if both authenticated surfaces are available.

Split executor artifacts are now available:

1. `ops/agents/packets/draft/2026-05-15-pm-lane-041a-vercel-operations-web-promotion.json`
2. `ops/agents/handoffs/2026-05-15-pm-lane-041a-vercel-operations-web-promotion-handoff.md`
3. `ops/agents/packets/draft/2026-05-15-pm-lane-041b-render-mutation-seam-redeploy-classification.json`
4. `ops/agents/handoffs/2026-05-15-pm-lane-041b-render-mutation-seam-redeploy-classification-handoff.md`
5. `ops/agents/handoffs/2026-05-15-pm-lane-041-dual-executor-dispatch-board.md`

### Lane 041A - Vercel Operations-Web Promotion

Target:

```text
https://operations.apexpowerops.com
```

Goal:

Promote current `origin/clean-main` so the hosted operations-web project includes:

```text
/pm-review/import-approval-readiness
```

Allowed:

1. inspect the existing Vercel project serving `https://operations.apexpowerops.com`,
2. deploy or promote current `origin/clean-main` for the existing operations-web project only,
3. confirm the build includes `/pm-review/import-approval-readiness`,
4. run hosted route smoke and PM intake hosted smoke.

Not allowed:

1. no new Vercel project,
2. no DNS change,
3. no auth or preview-protection widening,
4. no backend code change,
5. no mutation, schema, or live data write.

Validation:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web smoke:hosted -- --base-url https://operations.apexpowerops.com
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

Expected intermediate result:

The operations-web route failures should clear. Mutation-seam failures may remain until Lane 041B completes.

### Lane 041B - Render Mutation-Seam Redeploy And Classification

Target existing Render service:

```text
apex-platform-mutation-seam
```

Target public host:

```text
https://mutation-seam.apexpowerops.com
```

Goal:

Redeploy current `origin/clean-main` or classify why hosted PM intake reads remain stale or missing.

Allowed:

1. inspect existing Render service `apex-platform-mutation-seam`,
2. confirm repo, branch, working directory, deploy commit, build command, start command, health path, autoDeploy, and non-secret env key presence,
3. trigger a redeploy of the existing service from current clean-main if stale or metadata repair is needed,
4. inspect logs only far enough to classify remaining PM intake `404`s or schedule `500`s,
5. run deployed mutation-seam smoke with `--include-pm-intake` and hosted PM intake smoke.

Not allowed:

1. no new Render service,
2. no DNS change,
3. no auth or ingress widening,
4. no secret rotation,
5. no SQL write,
6. no schema migration,
7. no fixture replay,
8. no approval persistence,
9. no import mutation,
10. no live business-state mutation.

Validation:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake

corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

Expected result:

Either all current PM intake read paths appear and return governed read-only payloads, or the blocker is precisely classified as stale deploy, Render auth unavailable, DSN, schema, permission, runtime import, or product-code issue.

## Copy/Paste Coordinator Prompt

```text
You are executing PM Lane 041 for Apex Power Ops as a hosted parity executor/coordinator.

Repository:
C:\APEX Platform\apex-power-ops-platform

Authoritative packet:
C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-15-pm-lane-041-hosted-pm-intake-parity-refresh.json

Handoff:
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-041-hosted-pm-intake-parity-refresh-handoff.md

Read first:
1. C:\APEX Platform\apex-power-ops-platform\docs\authority\APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.md
2. C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-040-import-approval-readiness-ui-handoff.md
3. C:\APEX Platform\apex-power-ops-platform\apps\operations-web\DEPLOYMENT_VALIDATION.md
4. C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\DEPLOYMENT_VALIDATION.md
5. C:\APEX Platform\apex-power-ops-platform\apps\operations-web\scripts\smoke-pm-intake-hosted.mjs
6. C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\scripts\smoke_deployed_mutation_seam.py

Current source:
origin/clean-main at or after ee214d9559ed5d0ebc2fa4311def407a3711c390.

Tasks:
1. If you have Vercel access, execute Lane 041A against the existing operations-web project and alias only.
2. If you have Render access, execute Lane 041B against the existing Render service apex-platform-mutation-seam only.
3. Do not create new services, change DNS, widen auth/ingress, rotate secrets, run SQL, migrate schema, replay fixtures, persist approval, import rows, or mutate business state.
4. Run the validation commands from this handoff.
5. Update only the packet/handoff/deployment-validation/status closeout surfaces with exact evidence and blocker classification.
6. Commit and push only scoped closeout changes.
7. Preserve unrelated local residue.

Success:
Green hosted PM intake parity, or a precise blocker classification with no widened authority.
```

## Next Recommended Move

Execute Lane 041A and 041B on authenticated hosted surfaces. Do not start approval persistence schema/adapter admission until hosted PM intake reads are current or the blocker is tightly classified.
