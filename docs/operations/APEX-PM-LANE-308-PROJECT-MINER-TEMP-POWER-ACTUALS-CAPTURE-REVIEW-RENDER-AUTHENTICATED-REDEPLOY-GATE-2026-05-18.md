# APEX PM Lane 308 - Project Miner Temp Power Actuals Capture Review Render-Authenticated Redeploy Gate

Date: 2026-05-18

Status: Ready for external authenticated execution

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_RENDER_AUTHENTICATED_REDEPLOY_GATE`

## Purpose

PM Lane 308 packages the next truthful hosted action after Lane 307.

The repo and smoke entrypoints are ready, but this local shell does not have Render CLI access or `RENDER_*` environment support. That makes the next step an external authenticated execution lane, not another local code lane.

## Selected Outcome

Selected outcome:

`RENDER_AUTHENTICATED_ACTUALS_ROUTE_REDEPLOY_PACKET_READY`

## Required Executor Capability

The next executor must have all of the following:

1. authenticated access to the existing Render service `apex-platform-mutation-seam`
2. ability to inspect current deployed branch/commit and deployment metadata
3. ability to trigger a redeploy of the existing service from current `clean-main`
4. ability to inspect non-secret runtime configuration posture without disclosing secret values

## Allowed Actions

1. inspect the existing service only
2. confirm the service is pointed at repository `jasonlswenson-sys/apex-power-ops`, branch `clean-main`, working directory `apps/mutation-seam`
3. trigger redeploy of the existing service from current `clean-main`
4. rerun `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com --include-temp-power-actuals-review`
5. optionally rerun the same bounded smoke against `https://apex-platform-mutation-seam.onrender.com`
6. classify any remaining blocker without secret disclosure

## Not Allowed

1. no hosted write POST for the actuals route
2. no customer-preview route execution
3. no customer delivery, finance, or source-writeback admission
4. no new service creation
5. no DNS, auth, ingress, or secret-widening work
6. no SQL write or schema migration

## Current Evidence Passed To Executor

1. local route implementation and local first-write proof are complete
2. hosted smoke readiness is implemented in repo-owned tooling
3. both live hosted seam hosts return `200` for existing baseline reads
4. both live hosted seam hosts omit the new Temp Power actuals routes from OpenAPI
5. both live hosted seam hosts return framework `404 Not Found` for the actuals readback route
6. local environment shows `RENDER_CLI_ABSENT`
7. local environment shows no `RENDER_*` variables

## Expected Closeout Evidence

1. deployed branch/commit/working-directory verdict
2. redeploy evidence or truthful Render-auth blockage
3. bounded hosted smoke result for `--include-temp-power-actuals-review`
4. final classification: green hosted readiness or remaining hosted blocker

## Next Safe Step

Execute the packet JSON and handoff in this lane using a Render-authenticated executor.

Executor prompt:

`ops/agents/handoffs/2026-05-18-pm-lane-308-render-authenticated-actuals-route-redeploy-executor-copy-paste-prompt.md`