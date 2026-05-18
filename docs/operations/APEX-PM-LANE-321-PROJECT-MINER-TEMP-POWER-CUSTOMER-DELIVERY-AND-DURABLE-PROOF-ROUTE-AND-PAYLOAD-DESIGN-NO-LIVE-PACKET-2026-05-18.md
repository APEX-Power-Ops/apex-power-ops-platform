# APEX PM Lane 321 - Project Miner Temp Power Customer Delivery And Durable Proof Route And Payload Design No-Live Packet

Date: 2026-05-18

Status: Local no-live route-and-payload design for customer delivery and durable proof review

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_DELIVERY_DURABLE_PROOF_ROUTE_AND_PAYLOAD_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 321 converts the Lane 319 storage plan and Lane 320 readback design into exact future request contracts only.

This lane still does not admit route implementation, persistence, or any execution path. It defines the future mutation route, envelope shape, required payload fields, success/failure responses, idempotent replay expectations, and mandatory follow-up readback proof that any later admitted implementation would have to satisfy.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report creation, completion evidence artifact storage, customer delivery event persistence, delivery proof persistence, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation output, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`CUSTOMER_DELIVERY_DURABLE_PROOF_ROUTE_AND_PAYLOAD_DESIGN_READY_NO_LIVE`

Meaning:

1. The delivery/proof review slice now has an exact future request contract.
2. Request design remains no-live and does not admit implementation.
3. Delivery/proof requests must preserve separation from finance export, source writeback, and customer billing delivery.
4. Finance outputs, source writeback, and all live/runtime behavior remain blocked.

## Future Mutation Route

The future mutation route remains a design-only placeholder:

1. `POST /api/v1/mutations/temp-power-customer-delivery-proof-reviews`

## Common Envelope Requirements

Any later admitted request must include a common envelope with:

1. `mutation_class: C`
2. exact matching `idempotency_key` in the envelope and payload
3. exact current `project_id`, `candidate_id`, and `source_fingerprint`
4. `pm_actor`
5. `pm_actor_role` constrained to `PM`
6. `pm_timestamp`
7. `action_type`
8. `payload`

Common validation rules:

1. stale candidate or source fingerprints must reject the request
2. envelope and payload idempotency keys must match exactly
3. `pm_actor_role` must be `PM`
4. payloads may not include finance, export, source-writeback, or customer-billing-delivery fields

## Customer Delivery And Durable Proof Review Request

The future delivery/proof request must use:

1. route: `POST /api/v1/mutations/temp-power-customer-delivery-proof-reviews`
2. `action_type: persist_temp_power_customer_delivery_proof_review`

Required payload fields:

1. `idempotency_key`
2. `project_id`
3. `candidate_id`
4. `source_fingerprint`
5. `customer_preview_review_id`
6. `customer_delivery_event_id`
7. `preview_artifact_lineage`
8. `named_recipient_name`
9. `named_recipient_role`
10. `delivery_channel`
11. `delivery_artifact_refs`
12. `delivered_at_utc`
13. `delivery_proof_type`
14. `delivery_proof_ref`
15. `delivery_proof_recorded`
16. `pm_delivery_approval_status`
17. `pm_delivery_approval_note`
18. `delivery_note`

Delivery/proof request rules:

1. `delivery_channel` must be `CONTROLLED_EMAIL` or `LATER_APPROVED_PORTAL`.
2. `preview_artifact_lineage` must prove traceability from the hosted-green preview-review baseline.
3. `delivery_proof_recorded` may be `true` only when `delivery_proof_type` and `delivery_proof_ref` are present.
4. payload may describe delivery/proof review state but may not claim finance export, source writeback, or customer billing delivery occurred.

## Success, Replay, And Failure Expectations

Any later admitted implementation must follow these expectations:

1. first accepted request returns canonical record id plus `accepted_for_review_storage`
2. same-payload replay returns `idempotent_hit` and the original canonical record id
3. mismatched candidate or source returns a stale-source rejection class
4. missing PM actor/timestamp, missing proof linkage, or malformed payload returns validation rejection
5. successful write must be followed by matching status readback for the same canonical record

## Follow-Up Readback Proof

After any later admitted request, the paired status readback must prove:

1. current candidate/source match status
2. preview-review lineage match status
3. canonical record count
4. latest review id and timestamp
5. explicit separation from finance export, source writeback, and customer billing delivery

## Separate Execution Gate Requirement

First execution of the future route must remain owned by a separate explicit execution-gate packet.

This lane does not authorize route implementation, deployment, browser controls, local mocked request send, live request send, schema application, or any record creation.

## Explicitly Blocked In This Lane

The following remain blocked after Lane 321:

1. product code, UI controls, routes, backend seams, payload versions, hosted calls, hosted smokes, and browser live route access
2. live mutation POSTs, schema migrations, Supabase/Render/Vercel/Olares actions, service/auth/ingress changes, and secret changes
3. source workbook/PDF writeback and workbook macros
4. persistence execution, runtime route admission, and hosted delivery/proof admission
5. finance, billing, payroll, invoice, accounting, labor reconciliation, external finance sync, and customer billing delivery behavior
6. autonomous AI business-state mutation

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 321 files.
3. Selected outcome is present.
4. Future mutation route and action type are present.
5. Required payload fields are present.
6. Separate execution-gate requirement remains explicit.
7. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 322 - Project Miner Temp Power Customer Delivery And Durable Proof Execution Gate Design No-Live Packet`