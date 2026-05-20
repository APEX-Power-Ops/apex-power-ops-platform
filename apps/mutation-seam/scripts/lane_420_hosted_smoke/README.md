# PM Lane 420 Hosted Dual-Route Smoke Runner

This folder contains the reusable hosted smoke runner for PM Lane 420.

## Purpose

The runner checks the hosted Lane 412 route pair without widening authority:

1. polls hosted OpenAPI for route registration
2. proves unauthenticated reachability behavior on both routes
3. when the hosted routes are present, exercises the role and response-shape scenarios from the Lane 420 packet
4. optionally captures read-only before and after row counts for the four financial tables if a production DSN is supplied explicitly
5. records a redacted structured JSON artifact under `output/`

The runner reads tokens from environment variables and never logs token values.

## Required Environment

Required:

1. `LANE_420_PM_TOKEN`
2. `LANE_420_OPERATIONS_TOKEN`
3. `LANE_420_TASK_LEAD_TOKEN`

Optional:

1. `LANE_420_FIELD_TECH_TOKEN`
2. `LANE_420_BASE_URL` - defaults to `https://mutation-seam.apexpowerops.com`
3. `LANE_420_DRY_RUN_FLAG_OBSERVATION` - one of `unset`, `set`, or `unknown`
4. `LANE_420_DB_DSN` - production Postgres DSN used only for read-only row counts

## PowerShell Token Helper

The hosted mutation-seam auth layer accepts base64-encoded JSON bearer payloads, so the lane can set tokens locally without any signing secret.

```powershell
$env:LANE_420_PM_TOKEN = 'Bearer ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('{"actor_id":"pm-001","actor_role":"pm","project_scope":["proj-001"]}'))
$env:LANE_420_OPERATIONS_TOKEN = 'Bearer ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('{"actor_id":"operations-001","actor_role":"operations","project_scope":["proj-001"]}'))
$env:LANE_420_TASK_LEAD_TOKEN = 'Bearer ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('{"actor_id":"task-lead-001","actor_role":"task_lead","project_scope":["proj-001"]}'))
$env:LANE_420_FIELD_TECH_TOKEN = 'Bearer ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('{"actor_id":"field-tech-002","actor_role":"field_tech","project_scope":["proj-001"]}'))
```

## Run

```powershell
python apps/mutation-seam/scripts/lane_420_hosted_smoke/run_lane_420_hosted_smoke.py
```

Optional flags:

```powershell
python apps/mutation-seam/scripts/lane_420_hosted_smoke/run_lane_420_hosted_smoke.py --poll-attempts 6 --poll-interval-seconds 5 --timeout-seconds 20 --dry-run-flag-observation unknown
```

## Current Recorded Blocker

The first recorded run is `output/smoke_run_20260520T210513Z.json`.

That run returned `overall_status = blocked` because:

1. hosted OpenAPI did not advertise `/api/v1/mutations/project-import-contract-support`
2. hosted OpenAPI did not advertise `/api/v1/reads/project-import-contract-support-status`
3. direct no-auth POST returned `404`
4. direct no-auth GET returned `404`
5. production dry-run flag inspection was unavailable from this workspace
6. production DB row-count verification was unavailable because no explicit production DSN was supplied

The runner is therefore ready for re-use as soon as the hosted route pair is actually deployed and the operator has the required Render and production-DB evidence path.