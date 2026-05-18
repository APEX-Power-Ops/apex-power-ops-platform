# PM Lane 311 - Project Miner Temp Power Intake Workflow Runbook Refresh Handoff

## Summary

PM Lane 311 is a documentation-only coordination lane.

It refreshes the Project Miner intake workflow runbook so the current Temp Power actuals branch is visible from the operator-facing workflow surface.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_INTAKE_WORKFLOW_RUNBOOK_REFRESH`

Selected outcome:

`TEMP_POWER_WORKFLOW_RUNBOOK_REFRESHED_TO_CURRENT_BRANCH`

## Refreshed Surface

- workflow runbook: `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- controlling executor prompt: `ops/agents/handoffs/2026-05-18-pm-lane-308-render-authenticated-actuals-route-redeploy-executor-copy-paste-prompt.md`
- dispatch binder: `ops/agents/handoffs/2026-05-18-pm-lane-309-project-miner-temp-power-actuals-capture-review-executor-dispatch-binder-handoff.md`
- shared closeout template: `ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md`

## Current Truth

- PM intake hosted parity is accepted historical background, not the controlling blocker
- the controlling Temp Power branch is Lane 304 through Lane 310
- the remaining blocker is external Render-authenticated execution for Lane 308
- this lane adds no execution authority beyond clearer operator routing

## Next Safe Step

Continue with the existing Lane 308 external executor path. Reopen this runbook only if the controlling branch changes again.