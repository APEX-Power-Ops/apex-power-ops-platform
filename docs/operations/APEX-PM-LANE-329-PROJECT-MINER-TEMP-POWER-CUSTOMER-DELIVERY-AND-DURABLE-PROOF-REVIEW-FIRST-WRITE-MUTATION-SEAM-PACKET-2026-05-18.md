# APEX PM Lane 329 - Project Miner Temp Power Customer Delivery And Durable Proof Review First Write Mutation Seam Packet

Date: 2026-05-18

Status: Local admitted first-write implementation for the delivery/proof review route only

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_DELIVERY_DURABLE_PROOF_REVIEW_FIRST_WRITE_MUTATION_SEAM_PACKET`

## Purpose

PM Lane 329 converts the separately admitted delivery/proof first-write branch into one bounded mutation-seam implementation slice for the delivery/proof review route only.

The exact admission phrase was present as current instruction before this lane began:

`ADMIT_TEMP_POWER_CUSTOMER_DELIVERY_DURABLE_PROOF_REVIEW_FIRST_WRITE_PACKET_ONLY`

This lane implements and locally validates only the delivery/proof review route described in Lanes 319 through 322 and preflighted in Lanes 323 through 328. It does not open hosted promotion, hosted or live request execution, finance behavior, source writeback, or customer billing delivery.

## Selected Outcome

Selected outcome:

`CUSTOMER_DELIVERY_DURABLE_PROOF_REVIEW_FIRST_WRITE_IMPLEMENTED_AND_VALIDATED_LOCALLY`

Meaning:

1. `POST /api/v1/mutations/temp-power-customer-delivery-proof-reviews` now exists in `apps/mutation-seam`.
2. `GET /api/v1/reads/temp-power-customer-delivery-proof-status` now exists in `apps/mutation-seam`.
3. The route enforces current Temp Power project/candidate/source identity, PM-only authority, preview-review lineage checks, deterministic idempotency, and blocked downstream boundaries.
4. Hosted promotion, hosted/live request execution, finance behavior, source writeback, and customer billing delivery remain future separately packeted work.

## Chosen Route

The single admitted route for this lane is:

1. `POST /api/v1/mutations/temp-power-customer-delivery-proof-reviews`
2. `action_type: persist_temp_power_customer_delivery_proof_review`

Paired readback:

1. `GET /api/v1/reads/temp-power-customer-delivery-proof-status`

## Implemented Mutation-Seam Surfaces

This lane adds or updates the following runtime surfaces:

1. delivery/proof review persistence module with deterministic review-id generation, PM-only auth checks, scope checks, preview-review lineage validation, payload validation, strict replay matching, audit append, and blocked finance/source-writeback/customer-billing-delivery authorities
2. delivery/proof review mutation router registration in the FastAPI app
3. paired delivery/proof readback classification for no-record, current-match, stale-source, lineage-mismatch, pending-followup, and storage-unavailable states
4. insert-only migration `010_pm_lane_329_customer_delivery_proof_reviews.sql` with RLS, update/delete rejection triggers, and JSON-object guardrails for stored payload shape
5. focused mutation-seam tests for accepted write, same-payload replay, stale/lineage mismatch classification, blocked-field and auth rejection, storage-unavailable classification, and migration guardrails
6. reset-safe in-memory and Supabase store support for the new canonical delivery/proof review collection and preview-review lookup

## Focused Local Validation

The local validation for this lane must show all of the following:

1. one accepted write for `POST /api/v1/mutations/temp-power-customer-delivery-proof-reviews`
2. same-payload replay returns `idempotent_hit`
3. replay preserves the original `mutation_id` and `audit_event_id`
4. paired status readback returns `customer_delivery_proof_review_recorded_current_match`
5. stale-source classification is explicit
6. preview-review lineage mismatch classification is explicit
7. PM follow-up classification is explicit
8. `finance_authority=not_admitted`
9. `source_writeback_authority=not_admitted`
10. `customer_billing_delivery_authority=not_admitted`

## Explicitly Still Blocked

This lane still does not admit:

1. hosted promotion of the delivery/proof review slice
2. hosted or live request execution against delivery/proof review records
3. any finance/export/accounting behavior
4. any source workbook writeback or macro behavior
5. any customer billing delivery behavior
6. any unrelated mutation or autonomous AI business-state mutation

## Validation Checks

Required validation for this lane:

1. focused pytest for `apps/mutation-seam/tests/test_temp_power_customer_delivery_proof_review_persistence.py`
2. packet JSON parse
3. decision label and selected outcome search across touched Lane 329 files
4. route/readback/migration markers search across touched Lane 329 files
5. blocked hosted/live/finance/writeback/customer-billing-delivery boundary search across touched Lane 329 files
6. scoped `git diff --check`

## Next Safe Step

No hosted promotion or live request send is admitted by this lane.

Separate later packet only:

`Project Miner Temp Power Customer Delivery And Durable Proof Review Publication Or Hosted Proof Packet`