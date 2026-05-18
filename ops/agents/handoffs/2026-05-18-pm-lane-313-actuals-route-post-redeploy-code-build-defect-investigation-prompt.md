# PM Lane 313 - Actuals Route Post-Redeploy Code Build Defect Investigation Prompt

You are the repo-local executor for PM Lane 313.

This lane is a conditional fallback only. Do not start it unless PM Lane 308 has already returned a hosted closeout proving the existing Render service is on current `clean-main` and the Temp Power actuals routes are still absent after redeploy.

## Activation Preconditions

All of these must already be true before you proceed:

1. Lane 308 closeout exists
2. Lane 308 final outcome is `BLOCKED_HOSTED_ACTUALS_ROUTE_STILL_ABSENT_AFTER_REDEPLOY`
3. the closeout proves service `apex-platform-mutation-seam` is using repo `jasonlswenson-sys/apex-power-ops`, branch `clean-main`, working directory `apps/mutation-seam`
4. the closeout proves the deployed commit matches current repo head for this bounded slice
5. the admitted Temp Power actuals route files are already published in `clean-main` and are not still local-only modified or untracked worktree state

If preconditions 1 through 4 are true but precondition 5 is false, stop and use PM Lane 314 instead.

If any other precondition is false or missing, stop and keep Lane 308 as the controlling blocker.

## Objective

Investigate whether a bounded repo-local code or build defect is keeping the Temp Power actuals routes out of hosted OpenAPI after redeploy, and if the defect is clear and local, implement the smallest fix plus focused validation.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Packet: `ops/agents/packets/draft/2026-05-18-pm-lane-313-project-miner-temp-power-actuals-route-post-redeploy-code-build-defect-gate.json`
- Handoff: `ops/agents/handoffs/2026-05-18-pm-lane-313-project-miner-temp-power-actuals-route-post-redeploy-code-build-defect-gate-handoff.md`
- Prior hosted lane: `ops/agents/handoffs/2026-05-18-pm-lane-308-project-miner-temp-power-actuals-capture-review-render-authenticated-redeploy-gate-handoff.md`

## Start With

```powershell
cd "C:/APEX Platform/apex-power-ops-platform"
git pull --ff-only
git status --short --branch
git rev-parse HEAD
rg -n "temp-power-actuals-capture-review|temp_power_actuals_capture_review" apps/mutation-seam/app apps/mutation-seam/tests apps/mutation-seam/render.yaml
```

## Allowed Actions

1. inspect `apps/mutation-seam/app/main.py`
2. inspect `apps/mutation-seam/app/routers/temp_power_actuals_capture_reviews.py`
3. inspect `apps/mutation-seam/app/routers/reads.py`
4. inspect `apps/mutation-seam/app/temp_power_actuals_capture_review_persistence.py`
5. inspect `apps/mutation-seam/render.yaml`
6. run focused actuals tests
7. run a local OpenAPI presence check for the two actuals paths
8. apply the smallest repo-local fix if a bounded defect is confirmed

## Not Allowed

- do not repeat hosted redeploys without new evidence
- do not execute hosted mutation POSTs
- do not widen into customer-preview, finance, delivery, or source-writeback work
- do not add SQL or schema work
- do not change auth, ingress, DNS, or secrets

## Required Local Validation

Run the focused actuals persistence slice:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_temp_power_actuals_capture_review_persistence.py"
```

Run a local OpenAPI presence check from the mutation-seam app root:

```powershell
Push-Location "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam"
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "from app.main import app; paths = app.openapi().get('paths', {}); print('POST_PRESENT=' + str('/api/v1/mutations/temp-power-actuals-capture-reviews' in paths)); print('READ_PRESENT=' + str('/api/v1/reads/temp-power-actuals-capture-review-status' in paths))"
Pop-Location
```

## Target Outcome Labels

If a local defect is fixed and validation passes, classify the result as:

`ACTUALS_ROUTE_CODE_BUILD_DEFECT_FIXED_LOCALLY_READY_FOR_HOSTED_RETRY`

If no bounded repo-local defect is found and the hosted closeout still proves current clean-main is deployed, classify the result as:

`ACTUALS_ROUTE_ABSENT_AFTER_REDEPLOY_REQUIRES_NEW_BUILD_OR_RUNTIME_PACKET`

## Stop Conditions

1. stop if Lane 308 did not actually prove current clean-main is deployed
2. stop if the likely repair would require SQL, schema, auth, ingress, DNS, secret, or service-topology work
3. stop if the issue no longer reproduces locally and only hosted build/runtime evidence remains, because that requires a new hosted runtime packet rather than speculative local edits