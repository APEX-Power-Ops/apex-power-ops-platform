# PM Lane 314 - Project Miner Temp Power Actuals Route Publication Gate After Authenticated Redeploy Handoff

## Summary

PM Lane 314 is the current truthful blocker lane after authenticated Render execution.

Render auth worked, the existing mutation-seam service redeployed successfully, and both hosted seam URLs still omitted the Temp Power actuals routes. The reason is no longer external access: the admitted actuals route slice remains unpublished local worktree state.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_ROUTE_PUBLICATION_GATE_AFTER_AUTHENTICATED_REDEPLOY`

Selected outcome:

`ACTUALS_ROUTE_PUBLICATION_GATE_READY`

## Hosted Proof Already Collected

- existing service `apex-platform-mutation-seam` was inspected through authenticated Render browser access
- repo `jasonlswenson-sys/apex-power-ops`, branch `clean-main`, and root directory `apps/mutation-seam` were confirmed
- manual redeploy reached live deployment `dep-d85ipjjeo5us73f02c6g`
- the live deployed commit is `2bd07725d97d8b806d1c0e35e98e6595c5b1d584`
- both `https://mutation-seam.apexpowerops.com` and `https://apex-platform-mutation-seam.onrender.com` still omit the actuals routes from OpenAPI and return framework `404 Not Found` for the actuals readback route

## Publication-Gap Proof

The admitted actuals slice is still only local worktree state:

- modified tracked files: `app/main.py`, `app/routers/reads.py`, `app/db/memory_store_original.py`, `scripts/smoke_deployed_mutation_seam.py`, `DEPLOYMENT_VALIDATION.md`
- untracked actuals files: `app/routers/temp_power_actuals_capture_reviews.py`, `app/temp_power_actuals_capture_review_persistence.py`, `migrations/008_pm_lane_304_actuals_capture_reviews.sql`, `scripts/run_temp_power_actuals_capture_review_local_proof.py`, `tests/test_temp_power_actuals_capture_review_persistence.py`

## Current Safe Step

Publish only the admitted Temp Power actuals slice to `clean-main`, then rerun the bounded hosted smoke path.

## Executor Prompt

Use this copy/paste prompt for the publication follow-through:

`ops/agents/handoffs/2026-05-18-pm-lane-314-actuals-route-publication-gate-follow-up-prompt.md`