# APEX PM Lane 306 - Project Miner Temp Power Actuals Capture Review Hosted Smoke Readiness Packet

Date: 2026-05-18

Status: No-live readiness extension for future hosted proof of the admitted actuals-capture review route

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_HOSTED_SMOKE_READINESS_PACKET`

## Purpose

PM Lane 306 prepares the existing deployed mutation-seam smoke tool for a later separately admitted hosted proof of the Temp Power actuals-capture review route.

This lane does not run against a hosted base URL. It only extends the existing smoke script so a later hosted operator can verify route registration and readback shape for the admitted actuals route without sending a hosted POST request.

## Selected Outcome

Selected outcome:

`HOSTED_ACTUALS_ROUTE_SMOKE_READINESS_IMPLEMENTED`

## What Changed

Updated:

1. `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`

New hosted-readiness flag:

1. `--include-temp-power-actuals-review`

When enabled, the smoke script now validates all of the following on a deployed host:

1. `GET /openapi.json` contains `/api/v1/mutations/temp-power-actuals-capture-reviews`
2. `GET /openapi.json` contains `/api/v1/reads/temp-power-actuals-capture-review-status`
3. OpenAPI exposes `POST` for the mutation route
4. OpenAPI exposes `GET` for the readback route
5. `GET /api/v1/reads/temp-power-actuals-capture-review-status` returns the expected readback fields
6. hosted readback still reports `customer_delivery_authority=not_admitted`
7. hosted readback still reports `finance_authority=not_admitted`
8. hosted readback still reports `source_writeback_authority=not_admitted`
9. hosted readback still reports `durable_delivery_event=false`

## Validation Performed

This lane was validated narrowly and locally only:

1. diagnostics on `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
2. `python -m py_compile apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`

No hosted target execution was performed in this lane.

## Explicitly Not Claimed

This lane does not claim:

1. hosted acceptance of a Temp Power actuals-capture review write
2. hosted idempotent replay proof
3. hosted row persistence proof
4. customer-preview route admission or execution
5. any customer delivery, finance, or source-writeback admission

## Next Safe Step

Separate later admission only:

1. execute the deployed smoke script against a hosted base URL with `--include-temp-power-actuals-review`
2. if hosted route registration and readback pass, decide whether hosted first-write proof is separately admitted