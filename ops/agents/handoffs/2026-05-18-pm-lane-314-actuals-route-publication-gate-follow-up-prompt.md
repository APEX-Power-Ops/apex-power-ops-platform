# PM Lane 314 - Actuals Route Publication Gate Follow-Up Prompt

You are the repo-local publication executor for PM Lane 314.

Authenticated Render execution is already complete. The existing mutation-seam service redeployed successfully and is live on current committed `clean-main`, but the Temp Power actuals routes still remain absent because the admitted route slice is still local-only worktree state.

## Objective

Publish only the admitted Temp Power actuals route slice to `clean-main`, then rerun the bounded hosted smoke for the same existing mutation-seam service.

## Publish Only These Admitted Files

1. `apps/mutation-seam/app/db/memory_store_original.py`
2. `apps/mutation-seam/app/main.py`
3. `apps/mutation-seam/app/routers/reads.py`
4. `apps/mutation-seam/app/routers/temp_power_actuals_capture_reviews.py`
5. `apps/mutation-seam/app/temp_power_actuals_capture_review_persistence.py`
6. `apps/mutation-seam/migrations/008_pm_lane_304_actuals_capture_reviews.sql`
7. `apps/mutation-seam/scripts/run_temp_power_actuals_capture_review_local_proof.py`
8. `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
9. `apps/mutation-seam/tests/test_temp_power_actuals_capture_review_persistence.py`
10. `apps/mutation-seam/DEPLOYMENT_VALIDATION.md`
11. repo-owned packet and handoff/status updates required to keep blocker routing truthful

## Not Allowed

- do not widen into customer-preview route implementation
- do not widen into finance, delivery, or source-writeback work
- do not add unrelated workspace residue
- do not add auth, ingress, DNS, or secret changes
- do not send hosted mutation POSTs

## Required Validation

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_temp_power_actuals_capture_review_persistence.py"
```

After publication and push, verify the hosted route by rerunning:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-temp-power-actuals-review
```

Optionally rerun against the Render hostname for drift confirmation:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://apex-platform-mutation-seam.onrender.com --include-temp-power-actuals-review
```

## Expected Truth After Publication

If the hosted smoke turns green after publication, the old blocker was publication, not Render auth.

If the hosted smoke still fails after publication, only then reopen the bounded code/build investigation path.