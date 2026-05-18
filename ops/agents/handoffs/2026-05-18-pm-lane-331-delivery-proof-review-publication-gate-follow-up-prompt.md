# PM Lane 331 - Delivery/Proof Review Publication Gate Follow-Up Prompt

You are the repo-local publication executor for PM Lane 331.

Bounded hosted smoke has already proved both public mutation-seam hosts still omit the delivery/proof review routes. The reason is publication: the separately admitted delivery/proof review slice is still local-only worktree state.

## Objective

Publish only the separately admitted Temp Power customer-delivery/durable-proof review slice to `clean-main`, then rerun the bounded hosted smoke for the same existing mutation-seam service on both public hosts.

## Publish Only These Admitted Files

1. `.github/workflows/deployed-mutation-seam-smoke.yml`
2. `.vscode/tasks.json`
3. `apps/mutation-seam/DEPLOYMENT_VALIDATION.md`
4. `apps/mutation-seam/app/db/memory_store_original.py`
5. `apps/mutation-seam/app/db/supabase_store.py`
6. `apps/mutation-seam/app/main.py`
7. `apps/mutation-seam/app/routers/reads.py`
8. `apps/mutation-seam/app/routers/temp_power_customer_delivery_proof_reviews.py`
9. `apps/mutation-seam/app/temp_power_customer_delivery_proof_review_persistence.py`
10. `apps/mutation-seam/migrations/010_pm_lane_329_customer_delivery_proof_reviews.sql`
11. `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
12. `apps/mutation-seam/tests/test_temp_power_customer_delivery_proof_review_persistence.py`
13. repo-owned packet and handoff/status updates required to keep blocker routing truthful

## Not Allowed

- do not widen into hosted delivery/proof POST execution
- do not widen into finance behavior, source writeback, or customer billing delivery work
- do not add unrelated workspace residue
- do not add auth, ingress, DNS, or secret changes
- do not send hosted mutation POSTs

## Required Validation

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_temp_power_customer_delivery_proof_review_persistence.py"
```

After publication and push, verify both public hosts by rerunning:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-temp-power-customer-delivery-proof-review
```

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://apex-platform-mutation-seam.onrender.com --include-temp-power-customer-delivery-proof-review
```

## Expected Truth After Publication

If both hosted smokes turn green after publication, the old blocker was publication, not hosted infrastructure.

If hosted smoke still fails after publication, only then reopen the bounded hosted deploy or code/build investigation path.