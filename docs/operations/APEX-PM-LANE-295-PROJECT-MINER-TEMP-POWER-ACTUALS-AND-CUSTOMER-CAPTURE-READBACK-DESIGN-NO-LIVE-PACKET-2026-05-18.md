# APEX PM Lane 295 - Project Miner Temp Power Actuals And Customer Capture Readback Design No-Live Packet

Date: 2026-05-18

Status: Local no-live readback-design surface for actuals capture review and customer preview review

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_READBACK_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 295 converts the Lane 294 storage plan into future readback contracts only.

This lane still does not admit runtime reads, routes, or any implementation path. It defines what the future actuals-review and customer-preview status reads must return, which classifications are allowed, how current-candidate and source-fingerprint matching must work, and how preview-state readback must prove that no customer delivery occurred.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report, completion evidence, customer delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`ACTUALS_CUSTOMER_CAPTURE_READBACK_DESIGN_READY_NO_LIVE`

Meaning:

1. The storage plan now has explicit future readback contracts.
2. Readback remains design-only and does not admit runtime routes.
3. Customer preview readback must prove preview state without implying delivery.
4. Finance outputs, source writeback, and all live/runtime behavior remain blocked.

## Future Readback Routes

The future readback routes remain design-only placeholders:

1. `/api/v1/reads/temp-power-actuals-capture-review-status`
2. `/api/v1/reads/temp-power-customer-preview-status`

## Actuals Capture Review Status Contract

The actuals-capture readback must include:

1. identity fields: `project_id`, `candidate_id`, `source_fingerprint`
2. match fields: `current_candidate_match`, `current_source_fingerprint_match`
3. canonical status fields: `status`, `record_count`, `latest_review_id`, `latest_reviewed_at`
4. scope fields: `task_id`, `apparatus_id`, `task_day_fallback_reason`, `work_date`
5. review fields: `pm_review_status`, `pm_actor`, `recorder_role`, `actual_labor_hours_preview`
6. evidence fields: `primary_evidence_type`, `primary_evidence_ref`, `supporting_evidence_count`
7. correction fields: `correction_mode`, `replacement_chain_present`, `supersedes_review_id`
8. route/source fields: `storage_route_registered`, `storage_source`, `entity_type`

Allowed actuals-capture status values:

1. `no_actuals_capture_review_record`
2. `actuals_capture_review_recorded_current_match`
3. `actuals_capture_review_recorded_stale_source`
4. `actuals_capture_review_replacement_chain_present`
5. `actuals_capture_review_pending_pm_followup`

## Customer Preview Status Contract

The customer-preview readback must include:

1. identity fields: `project_id`, `candidate_id`, `source_fingerprint`
2. match fields: `current_candidate_match`, `current_source_fingerprint_match`
3. canonical status fields: `status`, `record_count`, `latest_customer_preview_review_id`, `latest_reviewed_at`
4. preview fields: `customer_preview_id`, `preview_summary`, `preview_artifact_count`
5. recipient fields: `named_recipient_name`, `named_recipient_role`, `delivery_channel`
6. PM review fields: `pm_review_status`, `pm_actor`, `approver_role`
7. delivery-boundary fields: `durable_delivery_event`, `delivery_block_reason`, `delivery_proof_recorded`
8. route/source fields: `storage_route_registered`, `storage_source`, `entity_type`

Allowed customer-preview status values:

1. `no_customer_preview_review_record`
2. `customer_preview_review_recorded_current_match`
3. `customer_preview_review_recorded_stale_source`
4. `customer_preview_delivery_blocked`
5. `customer_preview_pending_pm_followup`

## Readback Rules

The future readbacks must follow these rules:

1. `current_candidate_match` and `current_source_fingerprint_match` must be explicit booleans.
2. `record_count` must reflect canonical rows, not audit-log-only approximations.
3. Actuals replacement lineage must be visible through `replacement_chain_present` and `supersedes_review_id`.
4. Customer preview readback must always return `durable_delivery_event=false` in this design slice.
5. Customer preview readback must never claim delivery occurred; `delivery_proof_recorded` must stay `false` unless a later separately admitted delivery lane exists.
6. Readback must expose whether the dedicated storage route is registered without implying route admission in the current lane.

## Readback Proof Expectations

Any later admitted implementation should be able to prove:

1. same-payload replay leaves canonical ids stable
2. stale source fingerprints are classified explicitly
3. current candidate/source matches are visible without reading workbook contents
4. customer preview storage remains distinct from customer delivery
5. downstream finance, writeback, and live-output counts remain outside these readbacks

## Explicitly Blocked In This Lane

The following remain blocked after Lane 295:

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
2. Decision label is present in all touched Lane 295 files.
3. Selected outcome is present.
4. Future readback routes are present.
5. Allowed status values are present.
6. `durable_delivery_event=false` and no-delivery readback rules are explicit.
7. Blocked-output boundaries remain explicit.
8. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 296 - Project Miner Temp Power Actuals And Customer Capture Route And Payload Design No-Live Packet`