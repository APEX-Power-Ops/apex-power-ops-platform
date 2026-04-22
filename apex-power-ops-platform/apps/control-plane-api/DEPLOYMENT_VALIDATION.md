# Control-Plane Deployment Validation

This runbook defines the bounded deployment-promotion checks for the governed control-plane surface.

## Core Principle

Promotion proof must come from executable checks against the target host. Repo code alone is not deployment proof.

## Local Host Readiness

Before attempting workstation-level host validation, run the explicit readiness probe:

```powershell
.venv\Scripts\python.exe apps/control-plane-api/scripts/check_local_host_readiness.py
```

For script-backed local host control on the default workstation port:

```powershell
.\apps\control-plane-api\scripts\run_platform_api_local.ps1
.\apps\control-plane-api\scripts\run_platform_api_local.ps1 -Restart
```

Workspace task note:

1. the root workspace task `Control-plane local host readiness` runs this exact readiness probe
2. it currently reports `host-ready` on this workstation; it reports `host-readiness-blocked` only when `apps/control-plane-api/.env` is absent, core runtime values are still unresolved, recommended local auth/runtime values are incomplete, or the backend still cannot import locally

Bootstrap note:

1. the root workspace task `Bootstrap control-plane local env` copies `apps/control-plane-api/.env.example` to `apps/control-plane-api/.env`
2. copied template placeholders do not count as readiness; rerun the readiness task only after replacing placeholder values with canonical local runtime settings

## Local Apparatus Seam Smoke

Once the local host is running, validate the workstation-local apparatus seam with:

```powershell
.venv\Scripts\python.exe apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url http://127.0.0.1:8010 --local-runtime --skip-authenticated-checks --require-apparatus-study-route
```

Workspace task note:

1. the root workspace task `Control-plane local apparatus-route smoke` runs this exact local-runtime seam check against the default local host on port `8010`
2. start the root workspace task `Run platform API local` first so the backend is listening before you run the smoke
3. if `8010` is already occupied by an older control-plane process, use the root workspace task `Restart platform API local` so the host picks up current `.env` and auth/runtime behavior before rerunning the smoke
4. `Run platform API local` now fails fast with a direct restart instruction instead of surfacing a generic uvicorn port-bind error

This local-runtime mode proves the bounded workstation seam only:

1. `GET /health`
2. `GET /health/ready`
3. `GET /openapi.json`
4. the governed apparatus study-resource route is advertised and probeable without returning framework `404 Not Found`

It does not treat public-host-only surfaces as local blockers:

1. OAuth discovery at `/.well-known/oauth-authorization-server`
2. MCP metadata at `/mcp`
3. control-plane auth route behavior on `/api/v1/control-plane/task-packets`

Acceptable local apparatus-route outcomes:

1. `200`
2. `404` with an application-level detail such as `Apparatus ... not found`
3. `503` when the local database or migration state is intentionally gated but the governed route is present

## Minimum Public-Host Smoke

From `C:/APEX Platform/apex-power-ops-platform`:

```powershell
.venv\Scripts\python.exe apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com
```

This validates the baseline public control-plane surface:

1. `GET /health`
2. `GET /health/ready`
3. `GET /.well-known/oauth-authorization-server`
4. `GET /mcp`
5. unauthenticated `401 Bearer` behavior on `/api/v1/control-plane/task-packets`
6. authenticated read-only control-plane list and detail routes when bearer-token or disposable-user auth is available

## Apparatus Study-Route Promotion Gate

When promotion depends on the governed apparatus study-resource seam, run the explicit route gate:

```powershell
.venv\Scripts\python.exe apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com --skip-authenticated-checks --require-apparatus-study-route
```

Workspace task note:

1. the root workspace task `Control-plane public apparatus-route gate` runs this exact public-host gate against `https://control.apexpowerops.com`
2. the task is expected to fail with `deployment-route-missing` until the deployed host actually exposes the governed apparatus study-resource route

Pass conditions:

1. deployed OpenAPI advertises `/api/v1/neta/apparatus/{apparatus_id}/resources`
2. probing that route does not return framework `404 Not Found`

Acceptable route-level outcomes once the route is actually deployed:

1. `200`
2. `404` with an application-level detail such as `Apparatus ... not found`
3. `503` when the host is intentionally migration-gated

Fail conditions:

1. deployed OpenAPI omits the route
2. the route probe returns framework `404 Not Found`
3. the route returns an unexpected status outside the governed set above

## Repository Dispatch

Prerequisite:

1. provide a GitHub token with permission to send `repository_dispatch` events either through `--token` or the default `GITHUB_REPOSITORY_DISPATCH_TOKEN` environment variable

To trigger the smoke workflow through GitHub repository dispatch:

```powershell
.venv\Scripts\python.exe apps/control-plane-api/scripts/dispatch_deployed_control_plane_smoke.py --initial-wait-seconds 90 --deploy-id render-control-plane-20260421 --require-apparatus-study-route
```

Workspace task note:

1. the root workspace task `Control-plane public apparatus-route dispatch dry-run` prints the resolved dispatch request without requiring a token
2. the root workspace task `Control-plane public apparatus-route dispatch` sends the real `repository_dispatch` event and requires `GITHUB_REPOSITORY_DISPATCH_TOKEN` or `--token`

Use this when deployment rollout timing should be absorbed by automation rather than manual reruns.

If the token is absent, the helper fails before dispatch and no workflow run is created.

Checklist note:

1. use `apps/control-plane-api/PUBLIC-APPARATUS-ROUTE-PROMOTION-CHECKLIST-2026-04-21.md` when the remaining work is external host promotion rather than repo-local runtime repair

## Truthful Outcomes

Use these dispositions consistently:

1. `host-validated` only when the target host actually passes the required smoke checks
2. `deployment-route-missing` when the host is reachable but the new route is not deployed
3. `host-ready` when the workstation readiness probe passes and local host proof can start from trusted runtime values
4. `host-readiness-blocked` when local runtime proof cannot start or cannot be trusted yet because required env is absent, unresolved, or otherwise incomplete

Do not collapse these into one generic failure bucket.