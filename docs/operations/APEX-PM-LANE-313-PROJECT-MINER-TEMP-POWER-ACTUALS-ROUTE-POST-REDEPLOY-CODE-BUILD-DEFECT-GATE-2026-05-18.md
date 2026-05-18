# APEX PM Lane 313 - Project Miner Temp Power Actuals Route Post-Redeploy Code Build Defect Gate

Date: 2026-05-18

Status: Conditional fallback lane that activates only if Lane 308 proves current `clean-main` is deployed and the actuals routes are still absent after redeploy

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_ROUTE_POST_REDEPLOY_CODE_BUILD_DEFECT_GATE`

## Purpose

PM Lane 313 does not replace the current blocker.

The current blocker remains external Render-authenticated execution for Lane 308.

This lane exists only to remove the next coordination gap if Lane 308 returns the specific fallback outcome `BLOCKED_HOSTED_ACTUALS_ROUTE_STILL_ABSENT_AFTER_REDEPLOY` while proving the hosted service is already on current `clean-main`.

## Selected Outcome

Selected outcome:

`ACTUALS_ROUTE_POST_REDEPLOY_CODE_BUILD_DEFECT_GATE_READY`

## Activation Rule

Open this lane only when all of the following are true:

1. Lane 308 closeout final outcome is `BLOCKED_HOSTED_ACTUALS_ROUTE_STILL_ABSENT_AFTER_REDEPLOY`
2. the closeout proves service `apex-platform-mutation-seam` is on repo `jasonlswenson-sys/apex-power-ops`, branch `clean-main`, working directory `apps/mutation-seam`
3. the closeout proves the deployed commit matches the current repo head for this bounded branch
4. the admitted Temp Power actuals route slice is already published in `clean-main` and is not still local-only modified or untracked worktree state
5. the actuals routes still remain absent after redeploy

If condition 4 is not met, use PM Lane 314 instead of PM Lane 313.

If the other conditions are not met, Lane 308 remains the truthful controlling blocker and Lane 313 should not be opened.

## Scope

This lane is bounded to repo-local route-registration and build-surface investigation for the Temp Power actuals slice.

Allowed work is limited to:

1. route wiring review in `apps/mutation-seam`
2. FastAPI OpenAPI registration review for the two actuals paths
3. render/build-surface inspection limited to `apps/mutation-seam/render.yaml`
4. focused local validation of the actuals test slice and local OpenAPI presence
5. the smallest bounded fix if a clear local defect is proven

## Guardrails Preserved

This lane does not authorize:

1. another blind hosted redeploy loop
2. hosted actuals POST execution
3. customer-preview route work
4. SQL or schema work
5. auth, ingress, DNS, or secret changes
6. finance, delivery, or source-writeback widening

## Executor Surface

Use this copy/paste prompt when the activation rule is satisfied:

`ops/agents/handoffs/2026-05-18-pm-lane-313-actuals-route-post-redeploy-code-build-defect-investigation-prompt.md`

## Why This Lane Exists

Lane 308 already names the truthful fallback outcome if redeploy succeeds but the routes remain absent.

Before Lane 313, that fallback had no packet behind it. The branch would have stalled on fresh coordination work instead of moving directly into a bounded repo-local defect investigation.

Lane 313 removes that upcoming blocker while preserving the current truthful blocker: Lane 308 external execution still comes first.