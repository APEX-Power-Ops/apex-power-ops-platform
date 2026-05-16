# Operations Web Deployment Validation

This runbook defines the current bounded deployment-proof surface for `apps/operations-web`.

## Core Principle

Promotion proof for the browser shell must come from executable app validation plus explicit confirmation of the backend seam it depends on.

Repo code and local typecheck alone are not deployment proof.

## Current App Boundary

`apps/operations-web` is currently a governed Next.js browser shell with these active constraints:

1. it uses only public browser env values
2. it routes its first live read through the governed control-plane API
3. it does not yet widen authority into direct browser-side admin or service-role access

## Minimum Local Proof

From `C:/APEX Platform/apex-power-ops-platform` run:

```powershell
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web typecheck
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web build
```

Pass conditions:

1. typecheck succeeds without TypeScript errors
2. Next production build succeeds for `@apex/operations-web`

Fail conditions:

1. missing or invalid browser env usage breaks the build
2. imports or runtime assumptions widen the browser boundary beyond the governed shell contract

## Local Runtime Proof

Start the app locally from the platform root:

```powershell
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web dev
```

Required local browser env contract comes from `apps/operations-web/.env.example`:

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
NEXT_PUBLIC_CONTROL_PLANE_BASE_URL
```

Minimum runtime checks:

1. the app boots successfully in the browser shell
2. the homepage renders the governed shell status cards
3. `Public API base` resolves to the intended control-plane base URL
4. the first live read remains backend-routed rather than direct browser database admission

## Backend Seam Proof

`apps/operations-web` currently depends on the governed control-plane routes consumed by the apparatus study-resource explorer and the relay read-only browser slice.

The re-homed PM surfaces additionally depend on the hosted mutation seam being reachable through the same-origin Next rewrite contract.

Before claiming browser-surface readiness against any target host, verify the backing seam first.

Local seam validation path:

```powershell
.venv\Scripts\python.exe apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com --skip-authenticated-checks --require-apparatus-study-route
```

Use the local control-plane host instead of the public host when validating a purely local stack.

Pass conditions:

1. the governed apparatus study-resource route is present on the target control-plane host
2. the route does not fail with framework `404 Not Found`

Fail conditions:

1. the browser app is buildable but the required backend seam is absent
2. the target host exposes stale frontend code against an older backend without the required route

## PM Seam Ingress Proof

`apps/operations-web` now owns the public ingress layer for PM-facing `/api/v1/{reads,schedule,mutations}` routes.

Required server-side environment variable:

```text
MUTATION_SEAM_BASE_URL=https://mutation-seam.apexpowerops.com
```

From `C:/APEX Platform/apex-power-ops-platform` run:

```powershell
python apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web build
```

Pass conditions:

1. the mutation seam public host passes the deployed seam smoke
2. the operations-web build succeeds with the rewrite contract present
3. hosted PM pages can keep calling same-origin `/api/v1/*` without public-host framework `404`

Fail conditions:

1. the PM pages are deployed but `/api/v1/reads/*` and `/api/v1/schedule/*` still 404 on the public host
2. the seam host exists, but `MUTATION_SEAM_BASE_URL` is unset or points at the wrong target

## Hosted Route Smoke

Use the dedicated hosted smoke script after the backend seam has already been proven for the same target environment.

From `C:/APEX Platform/apex-power-ops-platform` run:

```powershell
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web smoke:hosted -- --base-url https://your-host.example
```

Pass conditions:

1. the hosted root shell responds with HTML and still contains the governed shell markers
2. `/integration-dashboard/index.html`, `/lead-ops/index.html`, and `/pm-review/index.html` all respond with HTML and contain their expected host markers
3. the smoke output ends with `SMOKE_SUMMARY failed=0`

Fail conditions:

1. a hosted route returns non-HTML or a non-200 response
2. a route responds, but the expected marker string for the promoted artifact is missing
3. the deployed shell omits one of the re-homed prototype surfaces that the active lane claims to host

## Local Browser Smoke

Use the Playwright smoke to prove that the governed shell and the re-homed static hosts behave correctly in a real browser before widening into promoted-host browser automation.

From `C:/APEX Platform/apex-power-ops-platform` run:

```powershell
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web smoke:browser
```

Pass conditions:

1. the root shell renders in a real browser and the apparatus explorer blocks invalid UUID input before any backend fetch
2. the browser can navigate to `/integration-dashboard/index.html`, `/lead-ops/index.html`, `/pm-review/index.html`, and `/pm-review/approval-surface.html`
3. the smoke output ends with all Playwright checks passing

Fail conditions:

1. the root shell fails to render or its client-side validation path regresses
2. a re-homed static host fails to open in a real browser even though simple HTTP smoke still passes
3. local browser proof drifts away from the route contract claimed by the active lane

## Promoted-Host Browser-Plus-Seam Smoke

Use the promoted-host smoke wrapper when you need one executable proof path that checks the governed backend seam first, then verifies hosted routes, then exercises the real deployed browser shell.

From `C:/APEX Platform/apex-power-ops-platform` run:

```powershell
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web smoke:promoted-host -- --operations-web-base-url https://your-operations-web-host.example --control-plane-base-url https://your-control-plane-host.example --skip-authenticated-checks
```

The wrapper can also read `OPERATIONS_WEB_BASE_URL` and `OPERATIONS_WEB_CONTROL_PLANE_BASE_URL` from the environment.

When validating a workstation-local stack through the same wrapper, add `--local-control-plane-runtime` so the backend seam is checked in local-runtime mode instead of public-host mode.

Workspace task note:

1. the root workspace task `Operations web promoted-host smoke` now defaults `OPERATIONS_WEB_CONTROL_PLANE_BASE_URL` to `https://control.apexpowerops.com`
2. you only need to provide `OPERATIONS_WEB_BASE_URL` when using that task against a deployed operations-web host

Vercel deployment note:

1. `apex-operations-web` is rooted from the parent workspace path `C:/APEX Platform`, so CLI deploys must run from that parent root when the Vercel project `rootDirectory` is `apex-power-ops-platform/apps/operations-web`
2. if the project setting is reduced to `apps/operations-web`, Git-linked deployments fail before build because the actual git root is the parent workspace root, not `apex-power-ops-platform`
3. the Vercel project `rootDirectory` must remain `apex-power-ops-platform/apps/operations-web` for this workspace layout
4. preview hosts can still return `401` to unauthenticated route smoke when Vercel preview protection is enabled, so the governed public proof gate remains the production alias unless preview protection is deliberately disabled
5. the 2026-05-03 hosted recovery also required commit `2b572b3` (`fix(operations-web): align Vercel trace root`), which moved `outputFileTracingRoot` and `turbopack.root` to the true repo root `C:/APEX Platform` so Vercel could package Next runtime files correctly after the rootDirectory fix

Current public-host status:

1. the repo-owned promoted-host path is operational
2. the latest public seam rerun against `https://control.apexpowerops.com` passes health, readiness, discovery, MCP, OpenAPI, and the governed apparatus route requirement, with readiness reporting `database: connected` and the overall script ending in `RESULT PASS`
3. the 2026-05-15 PM Lane 011 production promotion now points `https://operations.apexpowerops.com` at deployment `dpl_CP53VXXgr98ArXJ34QSvUyh4E6N3`, sourced from the clean-main PM lane stack through commit `3e8bba2d063a7a7227eeae22967d1430349f0546`
4. hosted route smoke against `https://operations.apexpowerops.com` passes with `SMOKE_SUMMARY failed=0 passed=8`
5. PM live-data proof is still blocked by the hosted mutation-seam runtime, not by operations-web routing: `https://mutation-seam.apexpowerops.com/openapi.json` does not advertise `/api/v1/reads/pm-workfront`, `/api/v1/reads/pm-workfront` returns `404`, and schedule reads return `500`
6. PM Lane 012 is the bounded Render-authenticated mutation-seam redeploy/log-inspection gate before further hosted PM product proof is claimed
7. PM Lane 041 read-only hosted proof after the Lane 040 UI route shows `/pm-review/import-candidate` and `/pm-review/import-admission-plan` still pass on `https://operations.apexpowerops.com`, but `/pm-review/import-approval-readiness` returns `404`
8. PM Lane 041 local capability check found no Vercel CLI binary and no `VERCEL_*` environment names; `pnpm dlx vercel whoami` timed out waiting for authentication and was stopped
9. The next operations-web hosted action is existing-project promotion of current `origin/clean-main` by a Vercel-authenticated executor, followed by `smoke:hosted` and `smoke:pm-intake-hosted`

Pass conditions:

1. the control-plane host passes `smoke_deployed_control_plane.py` with the governed apparatus study-resource route required
2. the hosted app shell and re-homed static routes pass the HTML route smoke
3. the existing Playwright browser smoke passes against the deployed operations-web base URL without starting a local Next server
4. the output ends with `PROMOTED_HOST_SUMMARY failed=0`

Fail conditions:

1. the browser host is reachable, but the required backend seam is missing or stale for the same target environment
2. hosted routes still respond to simple fetch smoke, but the deployed browser shell fails in a real browser
3. promoted-host validation silently drifts away from the same Playwright assertions used in local browser smoke

## Truthful Deployment Outcomes

Use these outcomes consistently:

1. `browser-shell-validated` when the app typechecks, builds, and points at a host with the required governed backend seam
2. `promoted-host-validated` when the backend seam, hosted route smoke, and real-browser promoted-host smoke all pass against the same deployed host
3. `backend-seam-missing` when the app is locally valid but the required control-plane route is not present on the target host
4. `browser-env-blocked` when the browser shell cannot be validated because the public env contract is unset or invalid

## Current Limitation

This runbook is a bounded first deployment-proof surface, not the final browser promotion framework.

It does not yet add:

1. deployment orchestration for `apps/operations-web` itself beyond hosted, local, and promoted-host smoke validation
2. authenticated promoted-host browser proof once the governed shell adds a browser path that legitimately depends on authenticated backend reads

Those are follow-on steps once `operations-web` moves beyond the current shell-and-seam posture.
