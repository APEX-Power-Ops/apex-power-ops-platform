# APEX PM Lane 314 - Project Miner Temp Power Actuals Route Publication Gate After Authenticated Redeploy

Date: 2026-05-18

Status: Current truthful blocker lane after authenticated Render execution

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_ROUTE_PUBLICATION_GATE_AFTER_AUTHENTICATED_REDEPLOY`

## Purpose

PM Lane 314 replaces the earlier external-auth blocker classification.

Render-authenticated execution is no longer the blocker. The existing mutation-seam service was inspected and redeployed successfully, but the admitted Temp Power actuals route slice is still only present in local worktree changes and therefore is not yet eligible for hosted promotion.

## Selected Outcome

Selected outcome:

`ACTUALS_ROUTE_PUBLICATION_GATE_READY`

## Proven Facts

1. existing service `apex-platform-mutation-seam` is bound to repo `jasonlswenson-sys/apex-power-ops`, branch `clean-main`, root directory `apps/mutation-seam`
2. manual redeploy reached live deployment `dep-d85ipjjeo5us73f02c6g`
3. that deploy is running commit `2bd07725d97d8b806d1c0e35e98e6595c5b1d584`
4. both hosted seam URLs still omit the Temp Power actuals routes from OpenAPI and still return framework `404 Not Found` for the actuals readback route
5. the admitted actuals route slice remains modified or untracked in the local worktree, so committed `clean-main` still does not contain the lane 304 implementation

## Current Blocker

The current blocker is publication of the admitted Temp Power actuals route slice to `clean-main`.

After publication, rerun the bounded hosted smoke. Only if the hosted route is still absent after publication should the branch reopen a bounded code/build-defect investigation.