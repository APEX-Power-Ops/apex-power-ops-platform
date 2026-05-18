# APEX PM Lane 311 - Project Miner Temp Power Intake Workflow Runbook Refresh

Date: 2026-05-18

Status: Documentation-only coordination lane for the current Temp Power workflow runbook

Decision label:

`PROJECT_MINER_TEMP_POWER_INTAKE_WORKFLOW_RUNBOOK_REFRESH`

## Purpose

PM Lane 311 does not add code, does not execute hosted work, and does not widen admission.

It refreshes the day-to-day Project Miner intake workflow runbook so the current Temp Power actuals branch is visible from the operator workflow surface that the canonical plan already links to.

## Selected Outcome

Selected outcome:

`TEMP_POWER_WORKFLOW_RUNBOOK_REFRESHED_TO_CURRENT_BRANCH`

## What Was Refreshed

The runbook at `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md` now states:

1. the controlling actuals-branch admission phrase,
2. the active Lane 304 through Lane 310 sequence,
3. that PM intake hosted parity is no longer the active blocker,
4. that the remaining blocker is the external Render-authenticated Lane 308 redeploy path,
5. the controlling executor prompt and shared closeout template.

## Current Truth After Refresh

1. PM intake hosted parity remains accepted historical background
2. local actuals-capture review implementation and proof are complete
3. hosted smoke readiness and blocker classification are complete
4. the remaining blocker is still external Render-authenticated execution for Lane 308

## Guardrails Preserved

This lane does not authorize:

1. hosted redeploy from this shell
2. hosted actuals POST execution
3. customer-preview route expansion
4. finance or source-writeback admission
5. SQL, schema, auth, ingress, or secret changes

## Next Safe Step

Continue with Lane 308 through the Lane 309 dispatch binder and the shared hosted closeout template. Do not reopen PM intake parity as if it were still the controlling branch blocker.