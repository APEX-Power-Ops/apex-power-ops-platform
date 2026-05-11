# Active App Runtime And Validation Map

Date: 2026-04-21
Status: Active operator map
Scope: `C:/APEX Platform/apex-power-ops-platform`

Closeout interpretation note:

This map remains the current operator-facing runtime and validation baseline for the active app lanes after standalone cutover. It no longer depends on an open packet-era normalization queue to be useful.

Current routing:

1. use `APEX-PM-LANE-OPERATING-COCKPIT-2026-05-06.md` and `../../PROJECT_STATUS.md` for current whole-program frontier and lane selection,
2. use `../OPERATOR-BOOTSTRAP-RUNBOOK.md` for repo-root and host-root operator workflow rules,
3. use this map for the active app-lane run paths, focused validation defaults, and deployment-proof entrypoints.

## Purpose

This document defines the current operator entrypoints for the active app lanes.

It is intentionally bounded to app surfaces that are already active in the workspace:

1. `apps/control-plane-api`
2. `apps/operations-web`
3. `apps/mutation-seam`

Seed lanes, merge-target lanes, and deferred placeholders are excluded until they become real governed deployables.

## Operator Rules

1. prefer platform-root entrypoints when a workspace task or root command already exists
2. treat `.env.example` files as the tracked env contract boundary for each app
3. prefer the narrowest validation path that proves the touched runtime slice
4. use deployed smoke checks as deployment proof; local code state alone is not deployment proof

## App Map

| App lane | Runtime role | Primary local run path | Primary validation path | Env contract source | Deployment proof |
| --- | --- | --- | --- | --- | --- |
| `apps/control-plane-api` | governed backend control-plane runtime | workspace task `Run platform API local` or `Restart platform API local` | workspace task `Platform API focused tests` plus local apparatus smoke and deployed smoke when promoting | `apps/control-plane-api/.env.example` | `apps/control-plane-api/DEPLOYMENT_VALIDATION.md` |
| `apps/operations-web` | governed browser operator shell | `pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web dev` | `pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web typecheck` plus `build` for deployment proof | `apps/operations-web/.env.example` | `apps/operations-web/DEPLOYMENT_VALIDATION.md` |
| `apps/mutation-seam` | governed PM/work mutation boundary | workspace task `Run mutation seam local` | workspace task `Mutation seam tests` | `apps/mutation-seam/.env.example` | `apps/mutation-seam/DEPLOYMENT.md` |

## App Details

### `apps/control-plane-api`

Runtime posture:
- primary backend control-plane lane
- platform-root-first operation is already documented in the app README

Preferred local run path:
- workspace task: `Run platform API local`
- workspace task: `Restart platform API local` when `.env` or auth/runtime behavior changes and the existing `8010` host must be refreshed
- equivalent root command:

```powershell
.\apps\control-plane-api\scripts\run_platform_api_local.ps1
.\apps\control-plane-api\scripts\run_platform_api_local.ps1 -Restart
.venv\Scripts\python.exe -m uvicorn main:app --app-dir apps/control-plane-api --host 0.0.0.0 --port 8010
```

Focused validation path:
- workspace task: `Platform API focused tests`
- workspace task: `Control-plane local host readiness`
- workspace task: `Control-plane local apparatus-route smoke`
- bounded deployed smoke path:
- workspace task: `Control-plane public apparatus-route gate`
- workspace task: `Control-plane public apparatus-route dispatch dry-run`
- workspace task: `Control-plane public apparatus-route dispatch`

```powershell
.venv\Scripts\python.exe apps/control-plane-api/scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com
.venv\Scripts\python.exe apps/control-plane-api/scripts/dispatch_deployed_control_plane_smoke.py --initial-wait-seconds 90 --require-apparatus-study-route --dry-run
.venv\Scripts\python.exe apps/control-plane-api/scripts/dispatch_deployed_control_plane_smoke.py --initial-wait-seconds 90 --require-apparatus-study-route
```

- latest public-host rerun: health `200`, readiness `200`, OAuth discovery `200`, MCP `200`, unauthenticated task-packets `401 Bearer`, but apparatus route still omitted from deployed OpenAPI and returns framework `404 Not Found`
- dispatch note: the dry-run path requires no token and prints the exact `repository_dispatch` payload; the live dispatch path requires `GITHUB_REPOSITORY_DISPATCH_TOKEN` or `--token`

Env contract boundary:
- required local runtime contract is tracked in `apps/control-plane-api/.env.example`
- the current workstation now has a materialized `apps/control-plane-api/.env`, a workstation-local `DATABASE_URL` for `tcc_v5`, and a passing readiness probe; unresolved Supabase placeholder values still suppress public OAuth and MCP discovery surfaces locally, but they now degrade cleanly instead of crashing host-level validation
- key local/runtime fields currently include:
  - `DATABASE_URL`
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `SUPABASE_JWKS_URL`
  - `APP_ENV`
  - `LOG_LEVEL`

Promotion proof:
- use `apps/control-plane-api/DEPLOYMENT_VALIDATION.md`
- treat public-host smoke as the deploy gate, not repo-local code state

### `apps/operations-web`

Runtime posture:
- primary browser operator shell
- current package is a real Next.js app boundary, not a placeholder lane

Preferred local run path:

```powershell
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web dev
```

Focused validation path:

```powershell
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web typecheck
pnpm --dir C:/APEX Platform/apex-power-ops-platform --filter @apex/operations-web build
```

Env contract boundary:
- tracked in `apps/operations-web/.env.example`
- current public browser contract is limited to:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `NEXT_PUBLIC_CONTROL_PLANE_BASE_URL`

Deployment posture:
- use `apps/operations-web/DEPLOYMENT_VALIDATION.md`
- root task `Operations web promoted-host smoke` defaults the control-plane host to `https://control.apexpowerops.com` and only requires `OPERATIONS_WEB_BASE_URL` for the deployed browser host
- current deployment proof is bounded to local Next.js build success plus explicit backend seam verification

### `apps/mutation-seam`

Runtime posture:
- governed mutation boundary for the PM/work domain
- FastAPI service with Postgres-backed seam store by default and memory fallback for offline development

Preferred local run path:

```powershell
Set-Location C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam
python -m uvicorn app.main:app --reload --port 8000
```

Focused validation path:

- workspace task: `Mutation seam tests`
- task note: the workspace validation task forces `SEAM_STORE_BACKEND=memory` so the narrow local test path does not require a live Postgres seam store

```powershell
Set-Location C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam
$env:SEAM_STORE_BACKEND='memory'
pytest tests/ -v
```

Env contract boundary:
- tracked in `apps/mutation-seam/.env.example`
- current contract fields include:
  - `PORT`
  - `LOG_LEVEL`
  - `JWT_SECRET`
  - `SEAM_STORE_BACKEND` when forcing memory mode
  - `SEAM_DATABASE_URL` when running the persisted seam store

Deployment proof:
- use `apps/mutation-seam/DEPLOYMENT.md` for current local and future deployment posture
- note that this lane still documents future Docker and Kubernetes deployment as planned rather than fully operationalized

## Current Gaps

1. the current browser deployment proof now includes promoted-host route smoke, local Playwright browser smoke, and a promoted-host browser-plus-seam smoke wrapper for deployed targets; the remaining adjacent gap is authenticated browser proof breadth rather than public control-plane route exposure

## Immediate Next Use

Use this map as the current operator-facing runtime baseline:

1. extend the current promoted-host browser-plus-seam smoke path for `apps/operations-web` once the governed shell gains a legitimate authenticated browser proof surface
2. use the existing promoted-host smoke path as the runtime baseline for any future hosted regression rerun, rather than treating public control-plane route exposure as an open blocker
3. keep seed, merge-target, and deferred placeholder lanes out of this map until they become real deployables