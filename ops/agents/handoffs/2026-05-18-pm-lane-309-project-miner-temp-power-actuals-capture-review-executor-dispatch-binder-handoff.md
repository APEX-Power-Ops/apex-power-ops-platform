# PM Lane 309 - Project Miner Temp Power Actuals Capture Review Executor Dispatch Binder Handoff

## Summary

PM Lane 309 is a dispatch-only coordination lane.

It packages the active external executor lane for Temp Power actuals-route hosted follow-through into one canonical PM handoff surface.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_EXECUTOR_DISPATCH_BINDER`

Selected outcome:

`ACTUALS_ROUTE_EXECUTOR_DISPATCH_BINDER_READY`

## Active Executor Surfaces

- packet: `ops/agents/packets/draft/2026-05-18-pm-lane-308-project-miner-temp-power-actuals-capture-review-render-authenticated-redeploy-gate.json`
- handoff: `ops/agents/handoffs/2026-05-18-pm-lane-308-project-miner-temp-power-actuals-capture-review-render-authenticated-redeploy-gate-handoff.md`
- prompt: `ops/agents/handoffs/2026-05-18-pm-lane-308-render-authenticated-actuals-route-redeploy-executor-copy-paste-prompt.md`
- closeout template: `ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md`

## Current Hosted Truth

- local actuals route implementation is complete
- local first-write proof is complete
- hosted smoke readiness is implemented
- both live hosted seam hosts still omit the Temp Power actuals routes from OpenAPI
- both live hosted seam hosts still return framework `404 Not Found` for the actuals readback route
- this shell cannot perform Render-authenticated redeploy

## Dispatch Rule

1. if Render-authenticated access exists, run Lane 308 exactly as written
2. if Render-authenticated access does not exist, return a credential-unavailable hosted closeout instead of reopening repo-side discovery

## Next Safe Step

Hand the Lane 308 prompt to a Render-authenticated executor and require a closeout using the shared hosted closeout template.