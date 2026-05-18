# APEX PM Lane 312 - Project Miner Temp Power Companion Doc Refresh

Date: 2026-05-18

Status: Documentation-only coordination lane for Temp Power companion docs

Decision label:

`PROJECT_MINER_TEMP_POWER_COMPANION_DOC_REFRESH`

## Purpose

PM Lane 312 does not add code, does not execute hosted work, and does not widen admission.

It refreshes the Temp Power companion guidance docs so the visual map and stakeholder-acceleration surface point at the same current actuals branch as the canonical plan and workflow runbook.

## Selected Outcome

Selected outcome:

`TEMP_POWER_COMPANION_DOCS_REFRESHED_TO_CURRENT_BRANCH`

## What Was Refreshed

The following companion docs now point at the current Temp Power branch:

1. `docs/operations/APEX-OPS-VISUAL-SYSTEM-MAP-2026-05-15.md`
2. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`

The refresh records:

1. that earlier intake/parity tranches are background, not the current blocker,
2. that the controlling actuals branch is Lane 304 through Lane 311,
3. that the remaining blocker is the external Render-authenticated Lane 308 redeploy path,
4. that bounded hosted validation must use `--include-temp-power-actuals-review`.

## Current Truth After Refresh

1. canonical plan, workflow runbook, visual map, and acceleration lane now agree on the current Temp Power branch
2. local actuals implementation and proof are complete
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

Continue with the existing Lane 308 external executor path and the Lane 309 dispatch binder. Do not reopen older intake/parity tranches as if they were the controlling blocker.