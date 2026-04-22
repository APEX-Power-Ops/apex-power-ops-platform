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

`apps/operations-web` currently depends on the governed control-plane route consumed by the apparatus study-resource explorer.

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

Workspace task note:

1. the root workspace task `Operations web promoted-host smoke` now defaults `OPERATIONS_WEB_CONTROL_PLANE_BASE_URL` to `https://control.apexpowerops.com`
2. you only need to provide `OPERATIONS_WEB_BASE_URL` when using that task against a deployed operations-web host

Current public-host status:

1. the repo-owned promoted-host path is operational
2. the latest public seam rerun against `https://control.apexpowerops.com` passes the governed apparatus-route gate, with deployed OpenAPI advertising `/api/v1/neta/apparatus/{apparatus_id}/resources` and the host returning handler-owned responses instead of framework `404 Not Found`
3. promoted-host proof against the public environment should now treat a route-level failure as a fresh regression, not as the previously known blocked state

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
2. `backend-seam-missing` when the app is locally valid but the required control-plane route is not present on the target host
3. `browser-env-blocked` when the browser shell cannot be validated because the public env contract is unset or invalid

## Current Limitation

This runbook is a bounded first deployment-proof surface, not the final browser promotion framework.

It does not yet add:

1. deployment orchestration for `apps/operations-web` itself beyond hosted, local, and promoted-host smoke validation
2. authenticated promoted-host browser proof once the governed shell adds a browser path that legitimately depends on authenticated backend reads

Those are follow-on steps once `operations-web` moves beyond the current shell-and-seam posture.