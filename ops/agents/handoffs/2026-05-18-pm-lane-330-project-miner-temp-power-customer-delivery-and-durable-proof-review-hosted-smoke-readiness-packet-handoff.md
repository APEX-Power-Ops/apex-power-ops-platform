# PM Lane 330 - Project Miner Temp Power Customer Delivery And Durable Proof Review Hosted Smoke Readiness Packet Handoff

## Summary

PM Lane 330 extends the deployed mutation-seam smoke tool and its first-class invocation surfaces with one no-live readiness flag for the Temp Power customer-delivery/durable-proof review route.

The new `--include-temp-power-customer-delivery-proof-review` option verifies OpenAPI registration and readback shape for the separately admitted delivery/proof route without sending a hosted POST request.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_DELIVERY_DURABLE_PROOF_REVIEW_HOSTED_SMOKE_READINESS_PACKET`

Selected outcome:

`HOSTED_CUSTOMER_DELIVERY_DURABLE_PROOF_REVIEW_ROUTE_SMOKE_READINESS_IMPLEMENTED`

## What The New Flag Checks

- OpenAPI contains `/api/v1/mutations/temp-power-customer-delivery-proof-reviews`
- OpenAPI contains `/api/v1/reads/temp-power-customer-delivery-proof-status`
- OpenAPI exposes `POST` for the mutation route
- OpenAPI exposes `GET` for the readback route
- hosted readback returns the expected delivery/proof status fields
- hosted readback preserves `finance_authority=not_admitted`
- hosted readback preserves `source_writeback_authority=not_admitted`
- hosted readback preserves `customer_billing_delivery_authority=not_admitted`

## First-Class Invocation Surfaces

- CLI: `python apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url <host> --include-temp-power-customer-delivery-proof-review`
- VS Code task: `Mutation-seam hosted customer-delivery-proof smoke`
- GitHub Actions manual dispatch input: `include_temp_power_customer_delivery_proof_review=true`

## Still Blocked

- hosted delivery/proof review write execution
- hosted idempotent replay proof
- hosted persistence proof
- hosted promotion of the new delivery/proof route slice
- any finance behavior, source writeback, or customer billing delivery admission

## Validation

- `python -m py_compile apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
- workflow/task/doc surfaces updated to reference the new flag

## Next Safe Step

Separate later admission only:

1. run hosted smoke with `--include-temp-power-customer-delivery-proof-review`
2. decide whether hosted publication or hosted first-write proof is separately admitted