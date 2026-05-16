# PM Lane 041B Handoff - Render Mutation-Seam PM Intake Redeploy And Blocker Classification

Date: 2026-05-15
Status: Ready for Render-authenticated executor
Scope: Existing mutation-seam Render service redeploy/classification for current PM intake reads

## Executive Summary

PM Lane 041B is the Render-only half of the hosted parity refresh.

Its goal is to make the existing mutation-seam host serve the current PM intake reads, or classify the blocker precisely.

Target existing Render service:

```text
apex-platform-mutation-seam
```

Target public host:

```text
https://mutation-seam.apexpowerops.com
```

This does not create services, change DNS, rotate secrets, run SQL, migrate schema, persist approval, import rows, or mutate business state.

## Current Evidence

PM Lane 041 read-only hosted proof shows:

1. `https://mutation-seam.apexpowerops.com/health` returns `200`,
2. hosted OpenAPI is missing all four current PM intake read paths,
3. all four current PM intake reads return framework `404`,
4. hosted schedule projects, drivers, tracer, and variance reads return `500`,
5. the coordinator workspace lacks Render auth: no `render` CLI and no `RENDER_*` environment names.

Current PM intake reads expected on hosted mutation-seam:

```text
/api/v1/reads/project-import-candidate
/api/v1/reads/project-import-admission-plan
/api/v1/reads/project-import-approval-contract
/api/v1/reads/project-import-approval-storage-plan
```

## Allowed

1. Inspect existing Render service `apex-platform-mutation-seam`.
2. Confirm repository `jasonlswenson-sys/apex-power-ops`, branch `clean-main`, working directory `apps/mutation-seam`, and deployed commit at or after `ee214d9559ed5d0ebc2fa4311def407a3711c390`.
3. Confirm build command, start command, health path, and autoDeploy posture match `apps/mutation-seam/render.yaml`.
4. Confirm non-secret env key presence only: `SEAM_STORE_BACKEND`, `SEAM_DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `APP_ENV`, `LOG_LEVEL`, and `PYTHON_VERSION`.
5. Repair only existing-service metadata needed to match `apps/mutation-seam/render.yaml`.
6. Trigger existing-service redeploy from current clean-main if stale or metadata repair is needed.
7. Inspect logs only far enough to classify remaining PM intake `404`s or schedule `500`s.
8. Run deployed mutation-seam smoke with `--include-pm-intake` and the paired hosted PM intake smoke.

## Not Allowed

1. No new Render service.
2. No DNS change.
3. No auth widening.
4. No ingress widening.
5. No secret value disclosure.
6. No secret rotation.
7. No SQL write.
8. No schema migration.
9. No fixture replay.
10. No product code change unless the coordinator opens a new packet.
11. No approval persistence.
12. No import mutation.
13. No schedule mutation.
14. No assignment, status, issue, task, workpackage, project, or autonomous AI business-state mutation.

## Validation

Run from:

```text
C:/APEX Platform/apex-power-ops-platform
```

```powershell
git rev-parse HEAD
git ls-remote origin clean-main
```

Confirm Render deployment source is at or after:

```text
ee214d9559ed5d0ebc2fa4311def407a3711c390
```

Then run:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
```

And:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

## Blocker Classification

If proof is still red, classify the blocker as one of:

1. Render auth unavailable,
2. stale deploy,
3. service metadata mismatch,
4. DSN issue,
5. schema issue,
6. permission issue,
7. runtime import/startup issue,
8. product-code issue,
9. other deployment failure.

Stop before SQL writes, schema migration, fixture replay, secret rotation, or live mutation.

## Copy/Paste Executor Prompt

```text
You are executing PM Lane 041B for Apex Power Ops as a Render-authenticated mutation-seam hosted runtime executor.

Repository:
C:\APEX Platform\apex-power-ops-platform

Authoritative packet:
C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-15-pm-lane-041b-render-mutation-seam-redeploy-classification.json

Handoff:
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-041b-render-mutation-seam-redeploy-classification-handoff.md

Read first:
1. C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-041-hosted-pm-intake-parity-refresh-handoff.md
2. C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\DEPLOYMENT_VALIDATION.md
3. C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\render.yaml
4. C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\scripts\smoke_deployed_mutation_seam.py
5. C:\APEX Platform\apex-power-ops-platform\apps\operations-web\scripts\smoke-pm-intake-hosted.mjs

Task:
Inspect existing Render service apex-platform-mutation-seam. If stale or metadata-mismatched, repair only existing-service metadata needed to match render.yaml and redeploy current origin/clean-main. Then run deployed mutation-seam and hosted PM intake smoke. If still red, classify the blocker precisely from logs without printing secrets.

Constraints:
No new service, DNS change, auth widening, ingress widening, secret value disclosure, secret rotation, SQL write, schema migration, fixture replay, product-code change, approval persistence, import mutation, schedule mutation, or business-state mutation.

Closeout:
Use ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md to create:
ops/agents/handoffs/2026-05-15-pm-lane-041b-render-mutation-seam-redeploy-classification-closeout-handoff.md

Update only scoped closeout/status surfaces, commit, and push. Preserve unrelated residue.
```

## Success

Success is either:

1. hosted mutation-seam exposes all four current PM intake reads and returns governed read-only payloads, or
2. the remaining blocker is precisely classified with log-backed evidence and no widened authority.
