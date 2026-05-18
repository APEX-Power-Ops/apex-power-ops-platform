# PM Lane 306 - Project Miner Temp Power Actuals Capture Review Hosted Smoke Readiness Packet Handoff

## Summary

PM Lane 306 extends the deployed mutation-seam smoke tool with one no-live readiness flag for the Temp Power actuals-capture review route.

The new `--include-temp-power-actuals-review` option verifies OpenAPI registration and readback shape for the admitted actuals route without sending a hosted POST request.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_HOSTED_SMOKE_READINESS_PACKET`

Selected outcome:

`HOSTED_ACTUALS_ROUTE_SMOKE_READINESS_IMPLEMENTED`

## What The New Flag Checks

- OpenAPI contains `/api/v1/mutations/temp-power-actuals-capture-reviews`
- OpenAPI contains `/api/v1/reads/temp-power-actuals-capture-review-status`
- OpenAPI exposes `POST` for the mutation route
- OpenAPI exposes `GET` for the readback route
- hosted readback returns the expected Temp Power status fields
- hosted readback preserves `customer_delivery_authority=not_admitted`
- hosted readback preserves `finance_authority=not_admitted`
- hosted readback preserves `source_writeback_authority=not_admitted`
- hosted readback preserves `durable_delivery_event=false`

## Still Blocked

- hosted actuals-capture review write execution
- hosted idempotent replay proof
- hosted persistence proof
- `POST /api/v1/mutations/temp-power-customer-preview-reviews`
- any customer delivery, finance, or source-writeback admission

## Validation

- diagnostics clean on `apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
- `python -m py_compile apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`

## Next Safe Step

Separate later admission only:

1. run hosted smoke with `--include-temp-power-actuals-review`
2. decide whether hosted first-write proof is separately admitted