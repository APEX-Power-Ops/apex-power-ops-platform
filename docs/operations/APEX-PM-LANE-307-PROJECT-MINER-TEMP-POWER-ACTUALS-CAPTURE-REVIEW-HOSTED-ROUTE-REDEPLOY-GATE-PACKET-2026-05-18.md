# APEX PM Lane 307 - Project Miner Temp Power Actuals Capture Review Hosted Route Redeploy Gate Packet

Date: 2026-05-18

Status: Hosted blocker classification and redeploy gate for the admitted Temp Power actuals-capture review route

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_HOSTED_ROUTE_REDEPLOY_GATE_PACKET`

## Purpose

PM Lane 307 converts the first hosted smoke execution for the admitted Temp Power actuals route into a precise blocker classification.

The goal of this lane is not to perform a hosted write. The goal is to prove whether the hosted mutation-seam service already serves the new route set added in Lane 304 and prepared in Lane 306.

## Selected Outcome

Selected outcome:

`HOSTED_ACTUALS_ROUTE_ABSENT_REDEPLOY_REQUIRED`

## Hosted Proof Performed

The repo-owned hosted smoke was run with the new bounded flag against both existing live hosts:

1. `https://mutation-seam.apexpowerops.com`
2. `https://apex-platform-mutation-seam.onrender.com`

Executed command shape:

1. `python apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url <host> --include-temp-power-actuals-review`

## Recorded Result

Both hosts returned the same outcome:

1. `/health` returned `200`
2. root returned `200`
3. approval queue returned `200`
4. all existing schedule reads returned `200`
5. `openapi.json` returned `200`
6. OpenAPI did not contain `/api/v1/mutations/temp-power-actuals-capture-reviews`
7. OpenAPI did not contain `/api/v1/reads/temp-power-actuals-capture-review-status`
8. `GET /api/v1/reads/temp-power-actuals-capture-review-status` returned framework `404 Not Found`

This proves the blocker is not custom-domain drift. It is service-wide hosted deploy lag: both the custom domain and the Render hostname are still serving a build that predates the new Temp Power actuals route registration.

## What Changed In This Lane

Updated repo-owned operator entrypoints:

1. `.github/workflows/deployed-mutation-seam-smoke.yml` now accepts `include_temp_power_actuals_review`
2. `.vscode/tasks.json` now includes `Mutation-seam hosted actuals-review smoke`
3. `apps/mutation-seam/DEPLOYMENT_VALIDATION.md` now documents the new hosted-readiness command path

These changes do not execute a hosted deploy. They only make the hosted verification path first-class once a redeploy occurs.

## Required Next Action

The next truthful action is a hosted redeploy of the existing mutation-seam service from current `clean-main`, then a rerun of the bounded hosted smoke with `--include-temp-power-actuals-review`.

Stop conditions:

1. do not claim hosted first-write proof before the new routes appear in OpenAPI and the readback route stops returning framework `404`
2. do not widen into customer-preview route execution
3. do not widen customer delivery, finance, or source-writeback authority
4. do not create a new service, change DNS, widen ingress, or change secrets as part of this lane

## Validation Performed

1. hosted smoke against `https://mutation-seam.apexpowerops.com`
2. hosted smoke against `https://apex-platform-mutation-seam.onrender.com`
3. diagnostics on `.github/workflows/deployed-mutation-seam-smoke.yml` and `.vscode/tasks.json`
4. JSON parse of `.vscode/tasks.json`
5. scoped `git diff --check`

## Next Safe Step

Separate later execution lane only:

1. redeploy existing hosted mutation-seam service
2. rerun hosted smoke with `--include-temp-power-actuals-review`
3. only if hosted smoke turns green, decide whether hosted first-write proof is separately admitted