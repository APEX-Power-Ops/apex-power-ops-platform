# APEX PM Lane 349 - Project Miner Temp Power Customer-Facing Delivery Execution Hosted Publication And Current-Match Proof Packet

Date: 2026-05-18

Status: Hosted publication green and public-host current-match proof recorded for the admitted customer-facing delivery execution slice while downstream finance, source writeback, and customer billing delivery remain blocked

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_FACING_DELIVERY_EXECUTION_HOSTED_PUBLICATION_AND_CURRENT_MATCH_PROOF_PACKET`

## Purpose

PM Lane 349 closes the next truthful hosted blocker after PM Lane 348 by proving two things about the separately admitted customer-facing delivery execution slice:

1. the promoted operations-web route `/pm-review/customer-delivery-execution` is publicly published
2. the canonical hosted customer delivery event row is already present and current across the public operations-web alias and both public mutation-seam hosts

This lane records current hosted truth only. It does not claim that this session's clean replay created the first hosted customer delivery event row, and it does not admit finance output, source writeback, or customer billing delivery.

## Selected Outcome

Selected outcome:

`HOSTED_CUSTOMER_FACING_DELIVERY_EXECUTION_PUBLISHED_AND_CURRENT_MATCH_PROVEN`

## Hosted Publication Proof

The current public operations-web smoke now passes end to end on `https://operations.apexpowerops.com`:

1. `corepack pnpm --filter @apex/operations-web smoke:hosted -- --base-url https://operations.apexpowerops.com`
2. `SMOKE_SUMMARY failed=0 passed=13 base_url=https://operations.apexpowerops.com/`
3. `/pm-review/customer-delivery-execution` returns `200`
4. the hosted route body includes `PM customer delivery execution now has an admitted orchestration route.`

Hosted publication is no longer the controlling blocker for this slice.

## Canonical Hosted Lineage

The canonical hosted lineage for the current customer-facing delivery execution slice is:

1. customer preview review id: `temp-power-customer-preview-review-1085e8e5fad27553463479f7`
2. customer delivery/proof review id: `temp-power-customer-delivery-proof-review-2ec74d71b109cfb3f8b1fb60`
3. canonical customer delivery event id: `pm-lane-337-temp-power-delivery-event-2026-05-18`

The hosted proof-status read continues to return:

1. `status=customer_delivery_proof_review_recorded_current_match`
2. canonical preview review continuity
3. canonical delivery event identity reuse through the reviewed proof row

## Hosted Proof Window

Observed hosted sequence for the current proof window:

1. a read-only prewrite probe showed the proof row was current and identified canonical delivery event id `pm-lane-337-temp-power-delivery-event-2026-05-18`
2. an initial hosted delivery-event POST with mismatched envelope and payload idempotency keys was rejected, proving the live seam still enforces packet-shape parity
3. a later clean same-payload hosted replay against `POST /api/v1/mutations/temp-power-customer-delivery-events` returned `idempotent_hit`
4. that clean replay resolved to entity id `pm-lane-337-temp-power-delivery-event-2026-05-18`
5. the replay preserved mutation id `mut-b2ea9ced-aae1-49ed-9180-72426fff1564`
6. the replay preserved audit event id `audit-755d4643-4320-4098-84d4-be7cb9939e32`

This packet therefore proves replay-safe hosted current state, not that the clean replay itself created the first hosted row.

## Current-Match Readback Proof

Public readback is now aligned across all current public surfaces.

Operations-web alias readback from `https://operations.apexpowerops.com/api/v1/reads/temp-power-customer-delivery-event-status` returned:

1. `status=customer_delivery_event_recorded_current_match`
2. `record_count=1`
3. `latest_customer_delivery_event_id=pm-lane-337-temp-power-delivery-event-2026-05-18`

Mutation-seam readback from `https://mutation-seam.apexpowerops.com/api/v1/reads/temp-power-customer-delivery-event-status` returned:

1. `status=customer_delivery_event_recorded_current_match`
2. `record_count=1`
3. `latest_customer_delivery_event_id=pm-lane-337-temp-power-delivery-event-2026-05-18`
4. `preview_review_lineage_match=true`
5. `delivery_proof_review_lineage_match=true`

Render-hosted mutation-seam readback from `https://apex-platform-mutation-seam.onrender.com/api/v1/reads/temp-power-customer-delivery-event-status` returned:

1. `status=customer_delivery_event_recorded_current_match`
2. `record_count=1`
3. `latest_customer_delivery_event_id=pm-lane-337-temp-power-delivery-event-2026-05-18`

## Hosted Smoke Proof

The deployed mutation-seam smoke now passes on both public seam hosts with the customer delivery proof and execution flags enabled:

1. `python apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com --include-temp-power-customer-delivery-proof-review --include-temp-power-customer-delivery-execution`
2. `python apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://apex-platform-mutation-seam.onrender.com --include-temp-power-customer-delivery-proof-review --include-temp-power-customer-delivery-execution`
3. both runs returned `RESULT PASS`

The repo-owned smoke checker now matches the canonical hosted field names for the delivery-proof and delivery-event readbacks.

## Boundary

This lane records hosted publication and hosted current-match proof only.

It does not admit or claim:

1. that the clean replay in this closeout window created the first hosted delivery-event row
2. finance, billing, payroll, invoice, accounting, or external finance output
3. source workbook or PDF writeback
4. customer billing delivery

## Next Truth

The hosted publication blocker and the hosted customer-facing delivery execution current-match blocker are both closed.

Any next lane must be separately packeted for downstream authority expansion only, not for re-proving this hosted publication/current-match slice.
