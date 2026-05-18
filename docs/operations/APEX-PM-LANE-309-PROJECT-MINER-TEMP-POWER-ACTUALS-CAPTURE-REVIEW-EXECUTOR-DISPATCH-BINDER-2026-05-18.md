# APEX PM Lane 309 - Project Miner Temp Power Actuals Capture Review Executor Dispatch Binder

Date: 2026-05-18

Status: Dispatch-only coordination lane for the Render-authenticated actuals-route redeploy gate

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_EXECUTOR_DISPATCH_BINDER`

## Purpose

PM Lane 309 does not implement code, does not execute hosted work, and does not widen admission.

It creates the current dispatch wrapper for the active external executor lane so the next authenticated operator can start from one canonical PM coordination surface instead of reconstructing context from multiple artifact files.

## Selected Outcome

Selected outcome:

`ACTUALS_ROUTE_EXECUTOR_DISPATCH_BINDER_READY`

## Current Active Executor Lane

The active hosted execution lane is:

1. `PM Lane 308 - Project Miner Temp Power Actuals Capture Review Render-Authenticated Redeploy Gate`

Its required executor prompt is:

1. `ops/agents/handoffs/2026-05-18-pm-lane-308-render-authenticated-actuals-route-redeploy-executor-copy-paste-prompt.md`

Its closeout contract is:

1. `ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md`

## Current Hosted Truth

1. local actuals route implementation is complete
2. local first-write proof is complete
3. hosted smoke readiness is implemented with `--include-temp-power-actuals-review`
4. both live hosted mutation-seam hosts still omit the Temp Power actuals routes from OpenAPI
5. both live hosted mutation-seam hosts still return framework `404 Not Found` for the actuals readback route
6. local coordinator workspace has no direct Render execution path

## Dispatch Decision

If the next executor has Render-authenticated access, run PM Lane 308 exactly as written.

If the next executor does not have Render-authenticated access, return a credential-unavailable closeout instead of reopening local repo exploration.

## Guardrails Preserved

This lane does not authorize:

1. hosted actuals POST execution
2. customer-preview route execution
3. SQL or schema work
4. auth, ingress, or secret widening
5. new service creation
6. finance, delivery, or source-writeback admission

## Next Safe Step

Hand the Lane 308 copy/paste prompt to a Render-authenticated executor and require a hosted closeout using the shared template.