# APEX PM Lane 296 - Project Miner Temp Power Actuals And Customer Capture Route And Payload Design No-Live Packet

Date: 2026-05-18

Status: Local no-live route-and-payload design for actuals capture review and customer preview review

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_ROUTE_AND_PAYLOAD_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 296 converts the Lane 294 storage plan and Lane 295 readback design into exact future request contracts only.

This lane still does not admit route implementation, persistence, or any execution path. It defines the future mutation routes, envelope shape, required payload fields, success/failure responses, idempotent replay expectations, and mandatory follow-up readback proof that any later admitted implementation would have to satisfy.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report, completion evidence, customer delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`ACTUALS_CUSTOMER_CAPTURE_ROUTE_AND_PAYLOAD_DESIGN_READY_NO_LIVE`

Meaning:

1. The actuals/customer review slice now has exact future request contracts.
2. Request design remains no-live and does not admit implementation.
3. Customer preview requests must preserve no-delivery posture.
4. Finance outputs, source writeback, and all live/runtime behavior remain blocked.

## Future Mutation Routes

The future mutation routes remain design-only placeholders:

1. `POST /api/v1/mutations/temp-power-actuals-capture-reviews`
2. `POST /api/v1/mutations/temp-power-customer-preview-reviews`

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
4. payloads may not include finance, export, delivery-complete, or source-writeback fields

## Actuals Capture Review Request

The future actuals-capture request must use:

1. route: `POST /api/v1/mutations/temp-power-actuals-capture-reviews`
2. `action_type: persist_temp_power_actuals_capture_review`

Required payload fields:

1. `idempotency_key`
2. `project_id`
3. `candidate_id`
4. `source_fingerprint`
5. `task_id`
6. `apparatus_id` or `task_day_fallback_reason`
7. `work_date`
8. `recorder_role`
9. `actual_labor_hours_preview`
10. `work_summary_note`
11. `primary_evidence_type`
12. `primary_evidence_ref`
13. `supporting_evidence_refs`
14. `correction_mode`
15. `supersedes_review_id` when replacing
16. `replacement_reason` when replacing
17. `pm_review_status`
18. `pm_review_note`

Actuals-capture request rules:

1. `apparatus_id` is required for apparatus-specific review; otherwise `task_day_fallback_reason` is required.
2. `actual_labor_hours_preview` must be nonnegative.
3. nonzero `actual_labor_hours_preview` requires primary evidence.
4. `VOID_AND_REPLACEMENT` requires `supersedes_review_id` and `replacement_reason`.

## Customer Preview Review Request

The future customer-preview request must use:

1. route: `POST /api/v1/mutations/temp-power-customer-preview-reviews`
2. `action_type: persist_temp_power_customer_preview_review`

Required payload fields:

1. `idempotency_key`
2. `project_id`
3. `candidate_id`
4. `source_fingerprint`
5. `customer_preview_id`
6. `coverage_scope_task_ids`
7. `coverage_scope_apparatus_ids`
8. `preview_summary`
9. `preview_artifact_refs`
10. `named_recipient_name`
11. `named_recipient_role`
12. `delivery_channel`
13. `future_delivery_proof_requirements`
14. `durable_delivery_event`
15. `delivery_proof_recorded`
16. `delivery_block_reason`
17. `pm_review_status`
18. `pm_review_note`

Customer-preview request rules:

1. `delivery_channel` must be `CONTROLLED_EMAIL` or `LATER_APPROVED_PORTAL`.
2. `durable_delivery_event` must remain `false`.
3. `delivery_proof_recorded` must remain `false` in this design slice.
4. payload may describe later proof expectations but may not claim customer delivery occurred.

## Success, Replay, And Failure Expectations

Any later admitted implementation must follow these expectations:

1. first accepted request returns canonical record id plus `accepted_for_review_storage`
2. same-payload replay returns `idempotent_hit` and the original canonical record id
3. mismatched candidate or source returns a stale-source rejection class
4. missing PM actor/timestamp or malformed payload returns validation rejection
5. successful write must be followed by matching status readback for the same canonical record

## Follow-Up Readback Proof

After any later admitted request, the paired status readback must prove:

1. current candidate/source match status
2. canonical record count
3. latest review id and timestamp
4. replacement lineage visibility for actuals reviews when applicable
5. `durable_delivery_event=false` and `delivery_proof_recorded=false` for customer preview reviews

## Separate Execution Gate Requirement

First execution of either future route must remain owned by a separate explicit execution-gate packet.

This lane does not authorize route implementation, deployment, browser controls, local mocked request send, live request send, schema application, or any record creation.

## Explicitly Blocked In This Lane

The following remain blocked after Lane 296:

1. product code, UI controls, routes, backend seams, payload versions, hosted calls, hosted smokes, and browser live route access
2. live mutation POSTs, schema migrations, Supabase/Render/Vercel/Olares actions, service/auth/ingress changes, and secret changes
3. source workbook/PDF writeback and workbook macros
4. production quantity writes, labor entry writes, actual labor hour writes, apparatus progress writes, and progress update writes
5. customer report creation, completion evidence artifact storage, customer delivery, customer commitment, and customer billing delivery
6. billing exports, payroll exports, invoices, payroll records, accounting records, labor reconciliation outputs, and external finance-system syncs
7. autonomous AI business-state mutation

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 296 files.
3. Selected outcome is present.
4. Future mutation routes and action types are present.
5. Required payload fields are present.
6. `durable_delivery_event=false` and `delivery_proof_recorded=false` remain explicit.
7. Separate execution-gate requirement remains explicit.
8. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 297 - Project Miner Temp Power Actuals And Customer Capture Execution Gate Design No-Live Packet`