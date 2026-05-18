# PM Lane 313 - Project Miner Temp Power Actuals Route Post-Redeploy Code Build Defect Gate Handoff

## Summary

PM Lane 313 is a conditional fallback lane.

It is not the current blocker. It activates only if PM Lane 308 returns a hosted closeout proving the existing mutation-seam service is already on current `clean-main` and the Temp Power actuals routes are still absent after redeploy.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_ROUTE_POST_REDEPLOY_CODE_BUILD_DEFECT_GATE`

Selected outcome:

`ACTUALS_ROUTE_POST_REDEPLOY_CODE_BUILD_DEFECT_GATE_READY`

## Activation Rule

Open this lane only when all of the following are true:

1. Lane 308 closeout final outcome is `BLOCKED_HOSTED_ACTUALS_ROUTE_STILL_ABSENT_AFTER_REDEPLOY`
2. the closeout proves service `apex-platform-mutation-seam` is on repo `jasonlswenson-sys/apex-power-ops`, branch `clean-main`, working directory `apps/mutation-seam`
3. the closeout proves the deployed commit matches current repo head under the same bounded branch
4. the admitted Temp Power actuals route files are already published in `clean-main` rather than still local-only modified or untracked worktree state
5. the actuals routes still remain absent after redeploy

If the actuals slice is still unpublished local worktree state, use PM Lane 314 instead of Lane 313.

If any other activation condition is missing, Lane 308 remains the controlling blocker instead of Lane 313.

## Scope

This lane is bounded to repo-local code/build investigation and, if necessary, the smallest route-registration or build-surface repair for the Temp Power actuals route slice.

## Allowed Work

1. inspect the actuals route wiring in `apps/mutation-seam`
2. inspect FastAPI OpenAPI registration for the actuals mutation and readback paths
3. inspect `render.yaml` and app wiring only far enough to classify a build or runtime packaging defect
4. run focused local validation for the actuals slice
5. apply the smallest bounded fix if a local defect is confirmed

## Not Allowed

1. no repeated hosted redeploy loop without new evidence
2. no hosted actuals POST
3. no customer-preview route work
4. no SQL or schema work
5. no auth, ingress, DNS, or secret changes
6. no finance, delivery, or source-writeback widening

## Executor Prompt

Use this copy/paste prompt:

`ops/agents/handoffs/2026-05-18-pm-lane-313-actuals-route-post-redeploy-code-build-defect-investigation-prompt.md`

## Current Truth

- Lane 308 remains the current external blocker until an authenticated closeout exists
- the fallback outcome already exists in the Lane 308 prompt and shared hosted closeout template
- this lane removes the next coordination gap if that fallback is the truthful result