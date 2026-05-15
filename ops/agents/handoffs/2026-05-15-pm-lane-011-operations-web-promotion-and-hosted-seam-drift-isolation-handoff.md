# PM Lane 011 Handoff - Operations-Web Promotion And Hosted Seam Drift Isolation

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-011`
Scope: PM hosted read-only deployment proof and blocker isolation

## Summary

This tranche promoted the current PM lane operations-web stack to production and reran the hosted read-only PM proof path.

The operations-web side is now current. The remaining blocker is the hosted mutation-seam runtime.

No product code, endpoint, package script, SQL, schema, auth, ingress, assignment, schedule, Operations Visibility, or autonomous AI mutation authority was added.

## Operations-Web Result

Local Vercel credentials are available:

```text
vercel whoami -> jasonlswenson-sys
```

The newest clean-main preview was promoted:

```powershell
npx -y vercel promote https://apex-operations-jucojx7de-jasonlswenson-sys-projects.vercel.app --scope jasonlswenson-sys-projects --yes
```

Production now resolves to:

```text
https://operations.apexpowerops.com
deployment: dpl_CP53VXXgr98ArXJ34QSvUyh4E6N3
status: Ready
created: 2026-05-15 09:22:59 America/Phoenix
```

Production route probes now return:

1. `/` -> `200`,
2. `/pm-review/workfront` -> `200`,
3. `/pm-review/approval` -> `200`,
4. `/api/v1/reads/decision-history?entity_id=__pm_workfront_smoke_noop__&limit=25` -> `200`.

Hosted route smoke passed:

```text
SMOKE_SUMMARY failed=0 passed=8 base_url=https://operations.apexpowerops.com/
```

The app-local Vercel env includes `MUTATION_SEAM_BASE_URL` for Production, Preview, and Development.

## Hosted Seam Result

The full PM live-data smoke still fails read-only:

```text
PM_LIVE_DATA_STEP mutation-seam https://mutation-seam.apexpowerops.com/
PM_LIVE_DATA_FATAL mutation seam schedule projects returned HTTP 500
```

Direct public probes show the failure is on the hosted mutation-seam runtime:

1. `https://mutation-seam.apexpowerops.com/health` -> `200`,
2. `https://mutation-seam.apexpowerops.com/openapi.json` -> `200`, but it does not advertise `/api/v1/reads/pm-workfront`,
3. `https://mutation-seam.apexpowerops.com/api/v1/reads/pm-workfront` -> `404`,
4. `https://mutation-seam.apexpowerops.com/api/v1/schedule/projects` -> `500`,
5. `https://mutation-seam.apexpowerops.com/api/v1/schedule/drivers` -> `500`,
6. `https://mutation-seam.apexpowerops.com/api/v1/reads/decision-history?entity_id=__pm_workfront_smoke_noop__&limit=25` -> `200`.

The Render default host `https://apex-platform-mutation-seam.onrender.com` showed the same OpenAPI omission, PM workfront `404`, and schedule `500` behavior.

## Delegation And Orchestration Notes

Two read-only scouts reviewed the hosted proof lane:

1. Operations-web promotion scout `019e2c70-7315-7c43-b363-c1d456997600` confirmed local Vercel credentials, current clean-main, app-local Vercel project context, and the fact that operations-web promotion is executable while full PM live-data remains blocked by mutation-seam.
2. Mutation-seam drift scout `019e2c70-5579-7883-8760-cd4d3a1c5f2e` confirmed current repo code mounts `/api/v1/reads/pm-workfront`, but hosted OpenAPI does not include it, making the PM workfront `404` a stale or wrong Render deployment symptom.

## Files Changed

Deployment/status surfaces only:

1. `apps/operations-web/DEPLOYMENT_VALIDATION.md`
2. `apps/mutation-seam/DEPLOYMENT_VALIDATION.md`
3. `PROJECT_STATUS.md`
4. `ops/agents/packets/draft/2026-05-15-pm-lane-011-operations-web-promotion-and-hosted-seam-drift-isolation.json`
5. `ops/agents/handoffs/2026-05-15-pm-lane-011-operations-web-promotion-and-hosted-seam-drift-isolation-handoff.md`

## Validation

Commands and outcomes:

```powershell
git rev-parse HEAD
git ls-remote origin clean-main
npx -y vercel whoami --scope jasonlswenson-sys-projects
npx -y vercel inspect https://operations.apexpowerops.com --scope jasonlswenson-sys-projects
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-hosted-routes.mjs --base-url https://operations.apexpowerops.com --timeout-ms 20000
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-live-data.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
$env:SEAM_STORE_BACKEND='memory'
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_schedule_bridge.py" -q
```

Results:

1. Local and remote `clean-main` both resolved to `3e8bba2d063a7a7227eeae22967d1430349f0546`.
2. Vercel credential check passed as `jasonlswenson-sys`.
3. Operations-web production inspect passed and showed `dpl_CP53VXXgr98ArXJ34QSvUyh4E6N3`.
4. Hosted operations-web route smoke passed `failed=0 passed=8`.
5. PM live-data smoke failed read-only on mutation-seam schedule `500`; no mutation was run and no live proof is claimed.
6. Local backend focused proof passed `17 passed`.

## Guardrails Preserved

1. No SQL or schema migration.
2. No live database write.
3. No new endpoint.
4. No new package script.
5. No new service admission.
6. No auth or ingress widening.
7. No assignment mutation.
8. No schedule mutation.
9. No Operations Visibility reopening.
10. No autonomous AI business-state mutation.
11. No new mutation endpoint.

## Next Bounded Move

Recommended next move: use a Render-authenticated surface to inspect service `apex-platform-mutation-seam`, confirm it deploys `clean-main` at `3e8bba2d063a7a7227eeae22967d1430349f0546` or later from `apps/mutation-seam`, redeploy the current head, and inspect Render logs if schedule reads still return `500`.

After the hosted seam advertises `/api/v1/reads/pm-workfront` and schedule reads stop returning `500`, rerun:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-live-data.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```
