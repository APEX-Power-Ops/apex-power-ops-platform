# APEX PM Lane 347 - Project Miner Temp Power Customer-Facing Delivery Execution First Packet

Date: 2026-05-18

Status: Local admitted first-packet implementation for customer-facing delivery execution orchestration plus canonical seam event recording

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_FACING_DELIVERY_EXECUTION_FIRST_PACKET`

## Purpose

PM Lane 347 converts the separately admitted customer-facing delivery execution branch into one bounded local implementation packet covering the admitted operations-web orchestration surface plus the admitted mutation-seam delivery-event persistence/readback slice.

The exact admission phrase was present as current instruction before this lane began:

`ADMIT_TEMP_POWER_CUSTOMER_FACING_DELIVERY_EXECUTION_FIRST_PACKET_ONLY`

This lane implements and locally validates only the first packet described by Lanes 338 through 346. It does not admit hosted promotion, hosted/live request execution against deployed services, finance output, source writeback, or customer billing delivery.

## Selected Outcome

Selected outcome:

`CUSTOMER_FACING_DELIVERY_EXECUTION_FIRST_PACKET_IMPLEMENTED_AND_VALIDATED_LOCALLY`

Meaning:

1. `/pm-review/customer-delivery-execution` now exists in `apps/operations-web`.
2. `POST /api/v1/mutations/temp-power-customer-delivery-events` now exists in `apps/mutation-seam`.
3. `GET /api/v1/reads/temp-power-customer-delivery-event-status` now exists in `apps/mutation-seam`.
4. The packet enforces current Temp Power project/candidate/source identity, preview-review continuity, delivery/proof review continuity, canonical `customer_delivery_event_id` reuse, deterministic idempotent replay, and blocked downstream boundaries.
5. Hosted promotion, hosted/live request execution, finance behavior, source writeback, and customer billing delivery remain future separately packeted work.

## Chosen Surfaces

The admitted surfaces for this lane are:

1. operations-web orchestration route: `/pm-review/customer-delivery-execution`
2. seam mutation route: `POST /api/v1/mutations/temp-power-customer-delivery-events`
3. seam status readback: `GET /api/v1/reads/temp-power-customer-delivery-event-status`

## Implemented Operations-Web Surface

This lane adds or updates the following browser-shell surfaces:

1. a PM-only orchestration route that renders the admitted request contract and blocked-boundary posture
2. one bounded submit control that sends the admitted seam request with the current PM token
3. one readback refresh control that fetches the paired seam status route
4. result panels that show mutation acceptance or rejection plus latest readback without claiming hosted/live execution
5. navigation link exposure from the PM landing route so the orchestration surface is discoverable inside the governed PM shell

## Implemented Mutation-Seam Surfaces

This lane adds or updates the following runtime seam surfaces:

1. customer delivery event persistence module using canonical `customer_delivery_event_id` as the entity id
2. PM-only auth and scope checks for the current Temp Power project
3. preview-review and delivery/proof review lineage validation before event acceptance
4. delivery-channel and execution-method compatibility checks plus constrained `customer_delivery_status`
5. deterministic idempotent replay using exact payload matching
6. insert-only migration `011_pm_lane_347_customer_delivery_events.sql` with RLS and update/delete rejection triggers
7. readback classification for no-record, current-match, stale-source, preview-review lineage mismatch, delivery/proof review lineage mismatch, and storage-unavailable states
8. reset-safe in-memory and Supabase store bindings for canonical delivery-event storage

## Focused Local Validation

The local validation for this lane must show all of the following:

1. one accepted write for `POST /api/v1/mutations/temp-power-customer-delivery-events`
2. same-payload replay returns `idempotent_hit`
3. replay preserves the original `mutation_id` and `audit_event_id`
4. paired status readback returns `customer_delivery_event_recorded_current_match`
5. stale-source classification is explicit
6. preview-review lineage mismatch classification is explicit
7. delivery/proof review lineage mismatch classification is explicit
8. `finance_authority=not_admitted`
9. `source_writeback_authority=not_admitted`
10. `customer_billing_delivery_authority=not_admitted`
11. operations-web typecheck passes
12. focused Playwright smoke for the admitted orchestration route passes

## Explicitly Still Blocked

This lane still does not admit:

1. hosted promotion of the customer-facing delivery execution slice
2. hosted or live request execution against deployed operations-web or mutation-seam services
3. any finance/export/accounting behavior
4. any source workbook writeback or macro behavior
5. any customer billing delivery behavior
6. any unrelated mutation or autonomous AI business-state mutation

## Validation Checks

Required validation for this lane:

1. focused pytest for `apps/mutation-seam/tests/test_temp_power_customer_delivery_event_persistence.py`
2. `corepack pnpm typecheck` in `apps/operations-web`
3. `corepack pnpm build` plus focused Playwright for `tests/browser-shell.pm-customer-delivery-execution.smoke.spec.ts`
4. packet JSON parse
5. decision label and selected outcome search across touched Lane 347 files
6. route/readback/migration markers search across touched Lane 347 files
7. blocked hosted/live/finance/writeback/customer-billing-delivery boundary search across touched Lane 347 files
8. scoped `git diff --check`

## Next Safe Step

The current local first packet is closed.

Separate later packet only:

`Project Miner Temp Power Customer-Facing Delivery Execution Publication Or Hosted Packet`