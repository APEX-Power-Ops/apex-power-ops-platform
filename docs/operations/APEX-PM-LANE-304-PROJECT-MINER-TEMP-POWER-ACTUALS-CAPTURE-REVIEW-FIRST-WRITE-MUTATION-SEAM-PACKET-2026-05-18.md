# APEX PM Lane 304 - Project Miner Temp Power Actuals Capture Review First Write Mutation Seam Packet

Date: 2026-05-18

Status: Local admitted first-write implementation for the actuals-capture review route only

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CAPTURE_REVIEW_FIRST_WRITE_MUTATION_SEAM_PACKET`

## Purpose

PM Lane 304 converts the separately admitted first-write branch into one bounded mutation-seam implementation slice for the actuals-capture review route only.

The exact admission phrase was present as current instruction before this lane began:

`ADMIT_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_REVIEW_FIRST_WRITE_PACKET_ONLY`

This lane implements and locally validates only the actuals route described in Lanes 295 through 303. It does not open the customer-preview route, customer delivery, finance behavior, or source writeback.

## Selected Outcome

Selected outcome:

`ACTUALS_CAPTURE_REVIEW_FIRST_WRITE_IMPLEMENTED_AND_VALIDATED_LOCALLY`

Meaning:

1. `POST /api/v1/mutations/temp-power-actuals-capture-reviews` now exists in `apps/mutation-seam`.
2. `GET /api/v1/reads/temp-power-actuals-capture-review-status` now exists in `apps/mutation-seam`.
3. The route enforces current Temp Power project/candidate/source identity, PM-only authority, deterministic idempotency, and blocked downstream boundaries.
4. Customer preview remains a future separately packeted route.

## Chosen Route

The single admitted route for this lane is:

1. `POST /api/v1/mutations/temp-power-actuals-capture-reviews`
2. `action_type: persist_temp_power_actuals_capture_review`

Paired readback:

1. `GET /api/v1/reads/temp-power-actuals-capture-review-status`

The customer-preview route is intentionally not implemented in this lane.

## Implemented Mutation-Seam Surfaces

This lane adds or updates the following runtime surfaces:

1. actuals-capture review persistence module with deterministic review-id generation, PM-only auth checks, scope checks, payload validation, strict replay matching, audit append, and blocked delivery/finance/writeback authorities
2. actuals-capture review mutation router registration in the FastAPI app
3. paired actuals-capture readback classification for no-record, current-match, stale-source, replacement-chain, pending-followup, and storage-unavailable states
4. insert-only migration `008_pm_lane_304_actuals_capture_reviews.sql` with RLS and update/delete rejection triggers
5. focused mutation-seam tests for accepted write, same-payload replay, stale/replacement classification, blocked-field and auth rejection, storage-unavailable classification, and migration guardrails
6. in-memory store reset support for the new canonical review collection so focused tests remain truthful between runs

## Local First-Write Proof

The local first-write proof for this lane must show all of the following:

1. one accepted local write to `/api/v1/mutations/temp-power-actuals-capture-reviews`
2. same-payload replay returns `idempotent_hit`
3. replay preserves the original `mutation_id` and `audit_event_id`
4. paired status readback returns `actuals_capture_review_recorded_current_match`
5. stale-source classification is explicit
6. replacement-chain classification is explicit
7. downstream project, workpackage, task, apparatus, assignment, hour, and issue counts remain unchanged
8. `customer_delivery_authority=not_admitted`
9. `finance_authority=not_admitted`
10. `source_writeback_authority=not_admitted`
11. `durable_delivery_event=false`

## Explicitly Still Blocked

This lane still does not admit:

1. `POST /api/v1/mutations/temp-power-customer-preview-reviews`
2. any customer preview review persistence
3. any customer delivery event or delivery-proof recording
4. any finance/export/accounting behavior
5. any source workbook writeback or macro behavior
6. any hosted promotion or hosted live-row proof

## Validation Checks

Required validation for this lane:

1. focused pytest for `apps/mutation-seam/tests/test_temp_power_actuals_capture_review_persistence.py`
2. diagnostics check on touched mutation-seam files
3. packet JSON parse
4. decision label and selected outcome search across touched Lane 304 files
5. route/readback/migration markers search across touched Lane 304 files
6. blocked customer preview/delivery/finance/writeback boundary search across touched Lane 304 files
7. scoped `git diff --check`

## Next Safe Step

No second route is admitted by this lane.

Separate later admission only:

`Project Miner Temp Power Customer Preview Review First Write Packet`

only if later separately admitted as a new bounded packet.