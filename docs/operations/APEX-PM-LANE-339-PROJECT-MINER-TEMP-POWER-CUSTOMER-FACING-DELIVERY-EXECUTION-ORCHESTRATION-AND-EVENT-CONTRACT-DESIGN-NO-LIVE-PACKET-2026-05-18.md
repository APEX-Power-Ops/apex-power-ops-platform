# APEX PM Lane 339 - Project Miner Temp Power Customer-Facing Delivery Execution Orchestration And Event Contract Design No-Live Packet

Date: 2026-05-18

Status: Local no-live contract design for customer-facing delivery execution orchestration and canonical event recording

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_FACING_DELIVERY_EXECUTION_ORCHESTRATION_AND_EVENT_CONTRACT_DESIGN_NO_LIVE`

## Purpose

PM Lane 339 converts PM Lane 338's architecture split into exact future request contracts.

This lane still does not admit implementation, hosted promotion, browser execution, external delivery send, or event persistence. It defines the future operations-web orchestration surface, the future mutation-seam delivery-event mutation and readback contracts, the shared lineage rules, and the exact fields that any later admitted implementation would have to satisfy.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, customer-facing report delivery, email send, portal upload, customer delivery event persistence, finance output, source writeback, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`CUSTOMER_FACING_DELIVERY_EXECUTION_ORCHESTRATION_AND_EVENT_CONTRACT_DESIGN_READY_NO_LIVE`

Meaning:

1. The future operations-web orchestration contract is now defined.
2. The future mutation-seam delivery-event mutation and status contracts are now defined.
3. Contract design remains no-live and does not admit implementation or execution.
4. Finance outputs, source writeback, customer billing delivery, and all unrelated runtime behavior remain blocked.

## Future Surface Boundaries

The future customer-facing delivery execution slice is split into these design-only placeholders:

1. operations-web orchestration route: `/pm-review/customer-delivery-execution`
2. seam mutation route: `POST /api/v1/mutations/temp-power-customer-delivery-events`
3. seam status route: `GET /api/v1/reads/temp-power-customer-delivery-event-status`

## Shared Preconditions

Any later admitted execution must prove all of the following before a request is allowed:

1. `project_id` is `pm-import-project-miner-temp-power`
2. `candidate_id` is `pm-import-candidate-miner-temp-power`
3. `source_fingerprint` matches the current candidate baseline
4. the canonical hosted preview-review row exists and remains current
5. the canonical hosted delivery/proof review row exists and remains current
6. the reviewed `customer_delivery_event_id` from the delivery/proof review row is reused as the canonical delivery-event identity
7. customer completion still remains a downstream summary surface rather than the primary event store

## Operations-Web Orchestration Contract

The future operations-web route remains orchestration-only.

It must collect and render, without direct persistence authority of its own:

1. `project_id`
2. `candidate_id`
3. `source_fingerprint`
4. `customer_preview_review_id`
5. `customer_delivery_proof_review_id`
6. `customer_delivery_event_id`
7. `named_recipient_name`
8. `named_recipient_role`
9. `delivery_channel`
10. `delivery_artifact_refs`
11. `delivered_at_utc`
12. `execution_method` constrained to `CONTROLLED_EMAIL_OPERATOR_SEND` or `LATER_APPROVED_PORTAL_OPERATOR_RELEASE`
13. `delivery_proof_type`
14. `delivery_proof_ref`
15. `execution_note`
16. explicit blocked-boundary indicators for finance, source writeback, and customer billing delivery

Operations-web contract rules:

1. it may orchestrate operator review and launch intent only
2. it may not hold long-lived delivery secrets or bypass the seam
3. it may not directly mutate the database or claim delivery succeeded without the seam response contract
4. it must display the linked preview-review and delivery/proof review lineage before launch is allowed
5. it must show blocked downstream boundaries in the same operator surface

## Common Seam Envelope Requirements

Any later admitted request to the seam mutation route must include a common envelope with:

1. `mutation_class: C`
2. exact matching `idempotency_key` in the envelope and payload
3. exact current `project_id`, `candidate_id`, and `source_fingerprint`
4. `pm_actor`
5. `pm_actor_role` constrained to `PM`
6. `pm_timestamp`
7. `action_type`
8. `payload`

Common validation rules:

1. stale candidate, source, preview-review, or delivery/proof review lineage must reject the request
2. envelope and payload idempotency keys must match exactly
3. `pm_actor_role` must be `PM`
4. payloads may not include finance, export, source-writeback, or customer-billing-delivery fields

## Future Seam Delivery-Event Mutation Contract

The future seam delivery-event request must use:

1. route: `POST /api/v1/mutations/temp-power-customer-delivery-events`
2. `action_type: persist_temp_power_customer_delivery_event`

Required payload fields:

1. `idempotency_key`
2. `project_id`
3. `candidate_id`
4. `source_fingerprint`
5. `customer_preview_review_id`
6. `customer_delivery_proof_review_id`
7. `customer_delivery_event_id`
8. `named_recipient_name`
9. `named_recipient_role`
10. `delivery_channel`
11. `delivery_artifact_refs`
12. `delivered_at_utc`
13. `execution_method`
14. `delivery_proof_type`
15. `delivery_proof_ref`
16. `customer_delivery_status`
17. `execution_note`
18. `proof_recorded_at_utc`

Mutation rules:

1. `customer_delivery_event_id` must match the reviewed event identity from the linked delivery/proof review row
2. `delivery_channel` must be `CONTROLLED_EMAIL` or `LATER_APPROVED_PORTAL`
3. `execution_method` must be compatible with the chosen `delivery_channel`
4. `customer_delivery_status` must be constrained to `DELIVERED_AND_PROOF_ATTACHED`
5. `proof_recorded_at_utc` is required when a durable delivery event is claimed
6. payload may describe delivery execution and proof, but may not claim finance export, source writeback, or customer billing delivery occurred

## Success, Replay, And Failure Expectations

Any later admitted implementation must follow these expectations:

1. first accepted request returns canonical record id plus `accepted_for_customer_delivery_event_storage`
2. same-payload replay returns `idempotent_hit` and the original canonical record id
3. mismatched candidate, source, preview-review, or delivery/proof review lineage returns a stale-lineage rejection class
4. missing operator lineage, missing proof linkage, or malformed payload returns validation rejection
5. successful write must be followed by matching status readback for the same canonical event id

## Future Status Readback Contract

The future status route must return, at minimum:

1. current candidate/source match status
2. preview-review lineage match status
3. delivery/proof review lineage match status
4. canonical delivery-event record count
5. latest `customer_delivery_event_id`
6. latest `delivered_at_utc`
7. latest proof type and proof ref summary
8. explicit separation from finance export, source writeback, and customer billing delivery

## Contractual Guardrails

Any later implementation built from this lane must preserve all of the following:

1. operations-web is orchestration-only and does not bypass the seam
2. mutation-seam records canonical state and paired readback, but does not hide ungoverned external-send behavior
3. the existing delivery/proof review route remains review-state only and is not widened into execution
4. customer completion remains a downstream summary surface and not the primary delivery-event store
5. no finance, billing, payroll, invoice, accounting, external finance sync, source writeback, or customer billing delivery fields may appear

## Exact Phrase Result

No exact live-execution phrase is applicable yet.

Why:

1. the contract is now designed, but the separate execution gate is still not defined
2. the next truthful step is a no-live execution-gate packet for this exact contract
3. a live phrase before that gate would skip the stop conditions and bounded executor sequence the PM lane requires

## Current Stop Boundary

The PM lane is truthfully stopped at:

`STOPPED_AWAITING_CUSTOMER_FACING_DELIVERY_EXECUTION_EXPLICIT_GATE_DESIGN_NO_LIVE`

## Next Safe Packet

The next safe packet is:

`PM Lane 340 - Project Miner Temp Power Customer-Facing Delivery Execution Explicit Gate Design No-Live Packet`

That packet should define:

1. the exact future admission phrase for one bounded execution packet
2. the forced stop conditions when the phrase is absent or lineage is stale
3. the allowed future executor sequence across operations-web orchestration proof, seam event mutation proof, replay proof, and readback proof
4. the unchanged downstream proof that must remain true after any later execution

## Explicitly Blocked In This Lane

The following remain blocked after Lane 339:

1. product code, UI controls, routes, backend seams, payload versions, hosted calls, hosted smokes, and browser live route access
2. live mutation POSTs, schema migrations, Supabase/Render/Vercel/Olares actions, service/auth/ingress changes, and secret changes
3. customer-facing report delivery, email send, portal upload, or any other external delivery execution
4. finance, billing, payroll, invoice, accounting, labor reconciliation, external finance sync, and customer billing delivery behavior
5. source workbook/PDF writeback and workbook macros
6. autonomous AI business-state mutation

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 339 files.
3. Selected outcome is present.
4. Operations-web orchestration contract is present.
5. Seam mutation and status contracts are present.
6. The absence of an applicable exact live-execution phrase is explicit.
7. The stop boundary is present.
8. The next safe packet is present.
9. `git diff --check` passes.