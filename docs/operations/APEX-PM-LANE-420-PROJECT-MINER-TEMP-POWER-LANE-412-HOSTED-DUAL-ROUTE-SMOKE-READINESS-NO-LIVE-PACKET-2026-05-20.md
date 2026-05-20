# APEX PM Lane 420 - Project Miner Temp Power Lane 412 Hosted Dual-Route Smoke Readiness No-Live Packet

Date: 2026-05-20

Status: Blocked and not promoted

Decision label:

`PROJECT_MINER_TEMP_POWER_LANE_412_HOSTED_DUAL_ROUTE_SMOKE_READINESS_NO_LIVE`

## Purpose

PM Lane 420 attempts the first hosted no-live proof for the Lane 412 route pair on the public Render mutation-seam:

1. route registration on hosted OpenAPI
2. hosted endpoint reachability
3. hosted role enforcement
4. hosted response-shape parity with the frozen Lane 415 exports
5. proof that no financial-table rows change during the smoke

This lane does not admit promotion when any hosted prerequisite is missing.

## Selected Outcome

Selected outcome:

`LANE_412_HOSTED_DUAL_ROUTE_SMOKE_BLOCKED_NOT_PROMOTED_NO_LIVE`

Meaning:

1. the reusable Lane 420 hosted smoke runner now exists locally
2. the runner executed successfully against the public mutation-seam host and produced a structured artifact
3. the hosted route pair is not currently deployed on the public host, so the lane cannot truthfully pass
4. production env-flag verification is not available from this workspace
5. production financial-table row-count verification is not available from this workspace
6. no promotion or Lane 421 admission can follow from this packet

## Phase 0 Discovery

### 1. Hosted route deployment state

Discovery result:

1. `https://mutation-seam.apexpowerops.com/health` returned `200`
2. hosted OpenAPI returned `200`
3. hosted OpenAPI did not advertise `/api/v1/mutations/project-import-contract-support`
4. hosted OpenAPI did not advertise `/api/v1/reads/project-import-contract-support-status`
5. direct public `POST /api/v1/mutations/project-import-contract-support` returned `404 {"detail":"Not Found"}`
6. direct public `GET /api/v1/reads/project-import-contract-support-status` returned `404 {"detail":"Not Found"}`

Conclusion:

The public Render host is not serving the Lane 412 route pair, so the hosted smoke cannot enter the PM, Operations, task_lead, or field_tech scenario matrix truthfully.

### 2. Hosted auth feasibility

Discovery result:

1. `apps/mutation-seam/app/auth/jwt.py` still accepts unsigned base64-encoded JSON bearer payloads
2. the focused Lane 419 test file already proves the exact token shape for `pm`, `operations`, `task_lead`, and `field_tech`
3. the existing deployed-smoke precedent already generates PM auth locally the same way

Conclusion:

Hosted auth is not the blocker for Lane 420.

### 3. Production dry-run flag visibility

Discovery result:

1. the Lane 412 dry-run gate still lives at `LANE_412_DRY_RUN_ENABLED`
2. the public health endpoint exposes only `status`, `version`, and `seam`
3. this workspace has no Render environment access and no hosted env-introspection route for that flag

Conclusion:

The lane cannot verify from this workspace that production `LANE_412_DRY_RUN_ENABLED` is unset.

### 4. Production financial-table row-count access

Discovery result:

1. the required tables are `seam.apparatus_financials`, `seam.project_contract_snapshots`, `seam.scope_labor_details`, and `seam.apparatus_revenue_events`
2. the repo has direct Postgres count-query precedent for store-backed reads
3. the current workspace shell exposed no Render or DB environment names for hosted verification
4. no explicit production DSN was available to the lane

Conclusion:

The lane cannot prove before and after row-count equality from this workspace today.

## Implemented Artifact Surface

### 1. Reusable hosted smoke runner

Implemented surface:

1. added `apps/mutation-seam/scripts/lane_420_hosted_smoke/run_lane_420_hosted_smoke.py`
2. the runner reads auth tokens from environment variables and never prints them
3. it polls hosted OpenAPI before route scenarios
4. it compares hosted response bodies to the exact frozen Lane 415 fixture text when the hosted routes are present
5. it optionally performs read-only before and after row counts when `LANE_420_DB_DSN` is supplied
6. it writes a structured redacted JSON artifact to `apps/mutation-seam/scripts/lane_420_hosted_smoke/output/`

### 2. Reusable operator README

Implemented surface:

1. added `apps/mutation-seam/scripts/lane_420_hosted_smoke/README.md`
2. documented required env vars, optional env vars, PowerShell token setup, run commands, and the current blocked state

### 3. Current smoke artifact

Recorded artifact:

`apps/mutation-seam/scripts/lane_420_hosted_smoke/output/smoke_run_20260520T210513Z.json`

Recorded facts:

1. `overall_status = blocked`
2. route-registration poll returned `200` twice but both hosted routes were missing each time
3. unauthenticated POST returned `404`
4. unauthenticated GET returned `404`
5. production dry-run flag verification recorded `unknown`
6. production DB row-count verification recorded unavailable because no explicit production DSN was supplied

## Validation

Focused executable validation passed for the new runner itself and truthfully produced a blocked hosted artifact:

```powershell
$env:LANE_420_BASE_URL='https://mutation-seam.apexpowerops.com'
$env:LANE_420_PM_TOKEN='Bearer ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('{"actor_id":"pm-001","actor_role":"pm","project_scope":["proj-001"]}'))
$env:LANE_420_OPERATIONS_TOKEN='Bearer ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('{"actor_id":"operations-001","actor_role":"operations","project_scope":["proj-001"]}'))
$env:LANE_420_TASK_LEAD_TOKEN='Bearer ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('{"actor_id":"task-lead-001","actor_role":"task_lead","project_scope":["proj-001"]}'))
$env:LANE_420_FIELD_TECH_TOKEN='Bearer ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('{"actor_id":"tech-001","actor_role":"field_tech","project_scope":["proj-001"]}'))
python apps/mutation-seam/scripts/lane_420_hosted_smoke/run_lane_420_hosted_smoke.py --poll-attempts 2 --poll-interval-seconds 1
```

Result:

`LANE_420_SMOKE_STATUS blocked`

## Boundary

This packet does not admit:

1. hosted promotion
2. Lane 421 advancement
3. any claim that production `LANE_412_DRY_RUN_ENABLED` is unset
4. any claim that the four financial tables were row-count-equal before and after smoke
5. any Render configuration mutation
6. any production DB write
7. any schema migration execution
8. any widening of auth, ingress, or runtime authority

## Next Truth

The next truthful follow-on is an authenticated Render-side deployment and environment-verification lane for the existing mutation-seam service, followed by a rerun of this exact Lane 420 smoke with explicit production env-flag proof and explicit read-only DB-count proof.