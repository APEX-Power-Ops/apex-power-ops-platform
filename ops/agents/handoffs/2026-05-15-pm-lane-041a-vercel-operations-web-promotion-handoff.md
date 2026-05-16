# PM Lane 041A Handoff - Vercel Operations-Web PM Intake Route Promotion

Date: 2026-05-15
Status: Ready for Vercel-authenticated executor
Scope: Existing operations-web production promotion for `/pm-review/import-approval-readiness`

## Executive Summary

PM Lane 041A is the Vercel-only half of the hosted parity refresh.

Its only runtime goal is to promote current `origin/clean-main` to the existing operations-web production alias so this route is hosted:

```text
https://operations.apexpowerops.com/pm-review/import-approval-readiness
```

This does not touch Render, Supabase, schema, approval persistence, import mutation, auth, ingress, DNS, or business state.

## Current Evidence

1. PM Lane 040 added `/pm-review/import-approval-readiness` locally and pushed it to `origin/clean-main`.
2. PM Lane 041 read-only hosted smoke shows `/pm-review/import-candidate` passes.
3. PM Lane 041 read-only hosted smoke shows `/pm-review/import-admission-plan` passes.
4. PM Lane 041 read-only hosted smoke shows `/pm-review/import-approval-readiness` returns `404`.
5. The coordinator workspace lacks Vercel auth: no `vercel` CLI binary, no `VERCEL_*` environment names, and `pnpm dlx vercel whoami` timed out waiting for login.

## Target

Existing operations-web production host:

```text
https://operations.apexpowerops.com
```

Expected route after promotion:

```text
https://operations.apexpowerops.com/pm-review/import-approval-readiness
```

## Allowed

1. Inspect the existing Vercel project serving `https://operations.apexpowerops.com`.
2. Confirm the deployment source is `jasonlswenson-sys/apex-power-ops`, branch `clean-main`, at or after `ee214d9559ed5d0ebc2fa4311def407a3711c390`.
3. Confirm the operations-web root/build settings still match the existing deployment contract.
4. Deploy or promote current clean-main to the existing production alias.
5. Run hosted route smoke and PM intake hosted smoke.
6. Update only closeout/status surfaces with exact deployment evidence.

## Not Allowed

1. No new Vercel project.
2. No DNS change.
3. No auth or preview-protection widening.
4. No Render action.
5. No backend endpoint change.
6. No product code change unless the coordinator opens a new packet.
7. No SQL write.
8. No schema migration.
9. No approval persistence.
10. No import mutation.
11. No live business-state mutation.

## Validation

Run from:

```text
C:/APEX Platform/apex-power-ops-platform
```

```powershell
git rev-parse HEAD
git ls-remote origin clean-main
```

Confirm hosted deployment source is at or after:

```text
ee214d9559ed5d0ebc2fa4311def407a3711c390
```

Then run:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web smoke:hosted -- --base-url https://operations.apexpowerops.com
```

And:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

Expected intermediate result:

1. hosted route smoke includes and passes `/pm-review/import-approval-readiness`,
2. PM intake hosted smoke no longer reports an operations-web `404` for import approval readiness,
3. mutation-seam failures may remain until PM Lane 041B completes.

## Copy/Paste Executor Prompt

```text
You are executing PM Lane 041A for Apex Power Ops as a Vercel-authenticated operations-web promotion executor.

Repository:
C:\APEX Platform\apex-power-ops-platform

Authoritative packet:
C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-15-pm-lane-041a-vercel-operations-web-promotion.json

Handoff:
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-041a-vercel-operations-web-promotion-handoff.md

Read first:
1. C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-041-hosted-pm-intake-parity-refresh-handoff.md
2. C:\APEX Platform\apex-power-ops-platform\apps\operations-web\DEPLOYMENT_VALIDATION.md
3. C:\APEX Platform\apex-power-ops-platform\apps\operations-web\scripts\smoke-hosted-routes.mjs
4. C:\APEX Platform\apex-power-ops-platform\apps\operations-web\scripts\smoke-pm-intake-hosted.mjs

Task:
Promote current origin/clean-main to the existing operations-web production alias so https://operations.apexpowerops.com/pm-review/import-approval-readiness is live.

Constraints:
Use the existing Vercel project and alias only. Do not create a project, change DNS, widen auth, change preview protection, touch Render, change backend code, run SQL, migrate schema, persist approval, import rows, or mutate business state.

Validation:
Run the two hosted smoke commands from this handoff. Record exact deployment id, alias, route-smoke result, and any remaining mutation-seam-only failures.

Closeout:
Update only scoped closeout/status surfaces, commit, and push. Preserve unrelated residue.
```

## Success

Success is not full PM intake parity by itself. Success is operations-web parity:

1. `/pm-review/import-approval-readiness` is hosted,
2. the operations-web route smoke passes,
3. any remaining hosted PM intake failures are mutation-seam-only and are assigned to PM Lane 041B.
