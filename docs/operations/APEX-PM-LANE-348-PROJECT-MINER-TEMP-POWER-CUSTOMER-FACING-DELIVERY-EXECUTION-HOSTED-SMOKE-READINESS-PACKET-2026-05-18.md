# APEX PM Lane 348 - Project Miner Temp Power Customer-Facing Delivery Execution Hosted Smoke Readiness Packet

Date: 2026-05-18

Status: No-live readiness extension for future hosted proof of the separately admitted customer-facing delivery execution slice

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_FACING_DELIVERY_EXECUTION_HOSTED_SMOKE_READINESS_PACKET`

## Purpose

PM Lane 348 prepares the existing hosted validation surfaces for a later separately admitted hosted proof of the Temp Power customer-facing delivery execution slice.

This lane does not run against a hosted base URL. It only extends the existing smoke script, workflow, local task, and hosted route marker surfaces so a later hosted operator can verify route registration and readback shape for the customer-facing delivery execution slice without sending a hosted POST request.

## Selected Outcome

Selected outcome:

`HOSTED_CUSTOMER_FACING_DELIVERY_EXECUTION_ROUTE_SMOKE_READINESS_IMPLEMENTED`

## What Changed

Updated:

1. `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
2. `.github/workflows/deployed-mutation-seam-smoke.yml`
3. `.vscode/tasks.json`
4. `apps/mutation-seam/DEPLOYMENT_VALIDATION.md`
5. `apps/operations-web/scripts/smoke-hosted-routes.mjs`

New hosted-readiness flag:

1. `--include-temp-power-customer-delivery-execution`

When enabled, the seam smoke path now validates all of the following on a deployed host:

1. `GET /openapi.json` contains `/api/v1/mutations/temp-power-customer-delivery-events`
2. `GET /openapi.json` contains `/api/v1/reads/temp-power-customer-delivery-event-status`
3. OpenAPI exposes `POST` for the mutation route
4. OpenAPI exposes `GET` for the readback route
5. `GET /api/v1/reads/temp-power-customer-delivery-event-status` returns the expected readback fields
6. hosted readback still reports `finance_authority=not_admitted`
7. hosted readback still reports `source_writeback_authority=not_admitted`
8. hosted readback still reports `customer_billing_delivery_authority=not_admitted`

The hosted operations-web route smoke path now validates all of the following on a deployed browser host:

1. `/pm-review/customer-delivery-execution` returns HTML
2. the hosted route body includes `PM customer delivery execution now has an admitted orchestration route.`

## First-Class Invocation Surfaces

Seam hosted-readiness invocation surfaces:

1. CLI: `python apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url <host> --include-temp-power-customer-delivery-execution`
2. VS Code task: `Mutation-seam hosted customer-delivery-execution smoke`
3. GitHub Actions manual dispatch input: `include_temp_power_customer_delivery_execution=true`

Operations-web hosted-readiness invocation surfaces:

1. CLI: `pnpm --filter @apex/operations-web smoke:hosted -- --base-url <host>`
2. CLI: `pnpm --filter @apex/operations-web smoke:promoted-host -- --operations-web-base-url <host> --control-plane-base-url <host>`
3. route marker included in `apps/operations-web/scripts/smoke-hosted-routes.mjs`

## Validation Performed

This lane was validated narrowly and locally only:

1. `python -m py_compile apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
2. `node apps/operations-web/scripts/smoke-hosted-routes.mjs --help`
3. diagnostics check across touched readiness files

No hosted target execution was performed in this lane.

## Explicitly Not Claimed

This lane does not claim:

1. hosted acceptance of a customer-facing delivery execution write
2. hosted idempotent replay proof
3. hosted row persistence proof
4. hosted promotion of the new customer-facing delivery execution slice
5. any finance behavior, source writeback, or customer billing delivery admission

## Next Safe Step

Separate later packet only:

1. execute the deployed smoke path against a hosted base URL with `--include-temp-power-customer-delivery-execution`
2. execute the hosted operations-web route smoke against the promoted PM host
3. decide whether hosted publication or hosted first-row proof is separately admitted