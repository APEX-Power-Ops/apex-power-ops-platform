# APEX PM Lane 330 - Project Miner Temp Power Customer Delivery And Durable Proof Review Hosted Smoke Readiness Packet

Date: 2026-05-18

Status: No-live readiness extension for future hosted proof of the separately admitted delivery/proof review route

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_DELIVERY_DURABLE_PROOF_REVIEW_HOSTED_SMOKE_READINESS_PACKET`

## Purpose

PM Lane 330 prepares the existing deployed mutation-seam smoke tool for a later separately admitted hosted proof of the Temp Power customer-delivery/durable-proof review route.

This lane does not run against a hosted base URL. It only extends the existing smoke script, workflow, and local task surfaces so a later hosted operator can verify route registration and readback shape for the delivery/proof review route without sending a hosted POST request.

## Selected Outcome

Selected outcome:

`HOSTED_CUSTOMER_DELIVERY_DURABLE_PROOF_REVIEW_ROUTE_SMOKE_READINESS_IMPLEMENTED`

## What Changed

Updated:

1. `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
2. `.github/workflows/deployed-mutation-seam-smoke.yml`
3. `.vscode/tasks.json`
4. `apps/mutation-seam/DEPLOYMENT_VALIDATION.md`

New hosted-readiness flag:

1. `--include-temp-power-customer-delivery-proof-review`

When enabled, the smoke path now validates all of the following on a deployed host:

1. `GET /openapi.json` contains `/api/v1/mutations/temp-power-customer-delivery-proof-reviews`
2. `GET /openapi.json` contains `/api/v1/reads/temp-power-customer-delivery-proof-status`
3. OpenAPI exposes `POST` for the mutation route
4. OpenAPI exposes `GET` for the readback route
5. `GET /api/v1/reads/temp-power-customer-delivery-proof-status` returns the expected readback fields
6. hosted readback still reports `finance_authority=not_admitted`
7. hosted readback still reports `source_writeback_authority=not_admitted`
8. hosted readback still reports `customer_billing_delivery_authority=not_admitted`

## Validation Performed

This lane was validated narrowly and locally only:

1. `python -m py_compile apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
2. packet JSON parse
3. `git diff --check`

No hosted target execution was performed in this lane.

## Explicitly Not Claimed

This lane does not claim:

1. hosted acceptance of a delivery/proof review write
2. hosted idempotent replay proof
3. hosted row persistence proof
4. hosted promotion of the new delivery/proof route slice
5. any finance behavior, source writeback, or customer billing delivery admission

## Next Safe Step

Separate later admission only:

1. execute the deployed smoke path against a hosted base URL with `--include-temp-power-customer-delivery-proof-review`
2. decide whether hosted publication or hosted first-write proof is separately admitted