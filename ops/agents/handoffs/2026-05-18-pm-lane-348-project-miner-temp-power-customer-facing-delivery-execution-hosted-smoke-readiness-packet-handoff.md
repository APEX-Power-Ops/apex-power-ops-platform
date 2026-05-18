# PM Lane 348 - Project Miner Temp Power Customer-Facing Delivery Execution Hosted Smoke Readiness Packet Handoff

## Summary

PM Lane 348 extends the hosted validation surfaces with one no-live readiness flag for the Temp Power customer-facing delivery execution seam route and one hosted route marker for the promoted PM browser host.

The new seam flag verifies OpenAPI registration and readback shape for the separately admitted customer-facing delivery execution route without sending a hosted POST request. The hosted route smoke now also checks that `/pm-review/customer-delivery-execution` is present on a promoted operations-web host.

## Selected Outcome

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_FACING_DELIVERY_EXECUTION_HOSTED_SMOKE_READINESS_PACKET`

Selected outcome:

`HOSTED_CUSTOMER_FACING_DELIVERY_EXECUTION_ROUTE_SMOKE_READINESS_IMPLEMENTED`

## What The New Surfaces Check

- OpenAPI contains `/api/v1/mutations/temp-power-customer-delivery-events`
- OpenAPI contains `/api/v1/reads/temp-power-customer-delivery-event-status`
- OpenAPI exposes `POST` for the mutation route
- OpenAPI exposes `GET` for the readback route
- hosted readback returns the expected customer-facing delivery execution status fields
- hosted readback preserves `finance_authority=not_admitted`
- hosted readback preserves `source_writeback_authority=not_admitted`
- hosted readback preserves `customer_billing_delivery_authority=not_admitted`
- hosted operations-web route smoke checks `/pm-review/customer-delivery-execution`
- hosted operations-web route smoke checks the admitted route heading marker

## First-Class Invocation Surfaces

- CLI: `python apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url <host> --include-temp-power-customer-delivery-execution`
- VS Code task: `Mutation-seam hosted customer-delivery-execution smoke`
- GitHub Actions manual dispatch input: `include_temp_power_customer_delivery_execution=true`
- Operations-web CLI: `pnpm --filter @apex/operations-web smoke:hosted -- --base-url <host>`
- Operations-web CLI: `pnpm --filter @apex/operations-web smoke:promoted-host -- --operations-web-base-url <host> --control-plane-base-url <host>`

## Still Blocked

- hosted customer-facing delivery execution write execution
- hosted idempotent replay proof
- hosted persistence proof
- hosted promotion of the new customer-facing delivery execution slice
- any finance behavior, source writeback, or customer billing delivery admission

## Validation

- `python -m py_compile apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py`
- `node apps/operations-web/scripts/smoke-hosted-routes.mjs --help`
- diagnostics clean on touched readiness files

## Next Safe Step

Separate later admission only:

1. run hosted seam smoke with `--include-temp-power-customer-delivery-execution`
2. run hosted operations-web route smoke against the promoted PM host
3. decide whether hosted publication or hosted first-write proof is separately admitted