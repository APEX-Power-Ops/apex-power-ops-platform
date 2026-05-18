# PM Lane 308 - Project Miner Temp Power Actuals Capture Review Render-Authenticated Redeploy Gate Handoff

## Summary

PM Lane 308 packages the next hosted action for a Render-authenticated executor.

Local implementation, local first-write proof, hosted-smoke readiness tooling, and hosted blocker classification are complete. The remaining action is authenticated redeploy of the existing mutation-seam service and a rerun of the bounded Temp Power actuals hosted smoke.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_RENDER_AUTHENTICATED_REDEPLOY_GATE`

Selected outcome:

`RENDER_AUTHENTICATED_ACTUALS_ROUTE_REDEPLOY_PACKET_READY`

## Key Evidence

- local environment returned `RENDER_CLI_ABSENT`
- local environment exposed no `RENDER_*` variables
- hosted smoke against both live seam hosts failed identically
- both live hosts omit the Temp Power actuals routes from OpenAPI
- both live hosts return framework `404 Not Found` for the actuals readback route

## Executor Goal

1. inspect existing service `apex-platform-mutation-seam`
2. redeploy it from current `clean-main`
3. rerun `smoke_deployed_mutation_seam.py --include-temp-power-actuals-review`
4. close green if the routes appear and bounded smoke passes, or classify the remaining hosted blocker truthfully

## Boundaries

- no hosted write POST
- no customer-preview route execution
- no SQL/schema work
- no auth/ingress/secret widening
- no new service creation

## Required Closeout

- deployed branch/commit/working-directory verdict
- redeploy evidence or truthful auth blockage
- bounded hosted smoke result
- final blocker classification if still failing

## Executor Prompt

Use this copy/paste executor prompt:

`ops/agents/handoffs/2026-05-18-pm-lane-308-render-authenticated-actuals-route-redeploy-executor-copy-paste-prompt.md`

That prompt packages the exact bounded commands, closeout path, outcome labels, and stop conditions for the Render-authenticated executor.

Use this hosted closeout template for the executor closeout:

`ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md`