# Public Apparatus Route Promotion Checklist

Use this checklist when deployment authority for `https://control.apexpowerops.com` lives outside the repo workspace and the remaining goal is to promote the governed apparatus study-resource route.

## Current Status

Hosted route promotion for the packet `001af` scope closed on 2026-04-22.

Current verified hosted proof:

1. `https://control.apexpowerops.com/openapi.json` advertises `/api/v1/neta/apparatus/{apparatus_id}/resources`
2. the public apparatus probe now returns handler-owned responses instead of framework `404 Not Found`
3. GitHub Actions run `24781243756` succeeded for the deployed control-plane smoke workflow
4. the repo-owned smoke script returned `RESULT PASS`

## Current Blocker

No active blocker remains for the completed hosted route-promotion lane.

Treat the rest of this checklist as the bounded rerun path if a future deploy ever regresses the hosted seam.

## Pre-Deploy Checks

1. confirm the target public host is still `https://control.apexpowerops.com`
2. confirm the repo route gate is still the required proof surface:

```powershell
.venv\Scripts\python.exe apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com --skip-authenticated-checks --require-apparatus-study-route
```

3. if deploy automation should trigger hosted validation, confirm the dispatch payload with:

```powershell
.venv\Scripts\python.exe apps/control-plane-api/scripts/dispatch_deployed_control_plane_smoke.py --initial-wait-seconds 90 --require-apparatus-study-route --dry-run
```

4. if the real dispatch path will be used, confirm `GITHUB_REPOSITORY_DISPATCH_TOKEN` is available or plan to pass `--token`

Current workspace note:

1. a 2026-04-21 check from the active repo workspace confirmed that `GITHUB_REPOSITORY_DISPATCH_TOKEN` is absent here, so the live dispatch path is not executable from this workspace unless a token is provided later

## Promotion Options

Choose one bounded promotion path if the hosted seam regresses and needs to be re-promoted:

1. manual host promotion followed by the root workspace task `Control-plane public apparatus-route gate`
2. automation-driven promotion followed by the root workspace task `Control-plane public apparatus-route dispatch`

On the current workstation, option 1 remains the direct executable fallback if the hosted seam ever needs to be re-promoted again.

## Success Criteria

The public route promotion is complete only when all of the following are true on the hosted control-plane:

1. `GET /openapi.json` advertises `/api/v1/neta/apparatus/{apparatus_id}/resources`
2. probing `/api/v1/neta/apparatus/00000000-0000-0000-0000-000000000000/resources` does not return framework `404 Not Found`
3. the root workspace task `Control-plane public apparatus-route gate` closes as pass

Acceptable route-level outcomes once the route is actually deployed:

1. `200`
2. `404` with an application-level detail such as `Apparatus ... not found`
3. `503` when the host is intentionally migration-gated

These success conditions are already satisfied for the 2026-04-22 closure.

## After The Route Gate Passes

1. rerun the root workspace task `Operations web promoted-host smoke` against the intended deployed browser host
2. only treat the promoted-host browser path as eligible for closure after the backend seam gate has already passed for the same environment

## Do Not Infer

1. do not treat a healthy OAuth or MCP surface as proof that the apparatus route is deployed
2. do not treat repository dispatch submission as proof that the hosted smoke workflow passed
3. do not reopen the workstation-local env lane as the active blocker on this machine; the local lane is already green