# APEX PM Lane 320 - Project Miner Temp Power Customer Delivery And Durable Proof Readback Design No-Live Packet

Date: 2026-05-18

Status: Local no-live readback-design surface for customer delivery and durable proof review

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_DELIVERY_DURABLE_PROOF_READBACK_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 320 converts the Lane 319 storage plan into a future readback contract only.

This lane still does not admit runtime reads, routes, or any implementation path. It defines what the future delivery/proof status read must return, which classifications are allowed, how preview-review lineage and source-fingerprint matching must work, and how readback must prove that delivery/proof review state is not finance export, source writeback, or customer billing delivery.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report creation, completion evidence artifact storage, customer delivery event persistence, delivery proof persistence, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation output, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`CUSTOMER_DELIVERY_DURABLE_PROOF_READBACK_DESIGN_READY_NO_LIVE`

Meaning:

1. The storage plan now has an explicit future readback contract.
2. Readback remains design-only and does not admit runtime routes.
3. Delivery/proof readback must prove review state without implying finance export, source writeback, or customer billing delivery.
4. Finance outputs, source writeback, and all live/runtime behavior remain blocked.

## Future Readback Route

The future readback route remains a design-only placeholder:

1. `/api/v1/reads/temp-power-customer-delivery-proof-status`

## Customer Delivery And Durable Proof Status Contract

The delivery/proof readback must include:

1. identity fields: `project_id`, `candidate_id`, `source_fingerprint`, `customer_preview_review_id`
2. match fields: `current_candidate_match`, `current_source_fingerprint_match`, `preview_review_lineage_match`
3. canonical status fields: `status`, `record_count`, `latest_customer_delivery_proof_review_id`, `latest_reviewed_at`
4. delivery fields: `customer_delivery_event_id`, `delivery_channel`, `delivery_artifact_count`, `delivered_at_utc`
5. recipient fields: `named_recipient_name`, `named_recipient_role`
6. proof fields: `delivery_proof_type`, `delivery_proof_ref`, `delivery_proof_recorded`, `proof_recorded_at_utc`
7. PM review fields: `pm_delivery_approval_status`, `pm_actor`, `pm_reviewed_at`
8. route/source fields: `storage_route_registered`, `storage_source`, `entity_type`
9. boundary fields: `finance_export_recorded`, `source_writeback_recorded`, `customer_billing_delivery_recorded`

Allowed delivery/proof status values:

1. `no_customer_delivery_proof_review_record`
2. `customer_delivery_proof_review_recorded_current_match`
3. `customer_delivery_proof_review_recorded_stale_source`
4. `customer_delivery_proof_review_lineage_mismatch`
5. `customer_delivery_proof_pending_pm_followup`

## Readback Rules

The future readback must follow these rules:

1. `current_candidate_match`, `current_source_fingerprint_match`, and `preview_review_lineage_match` must be explicit booleans.
2. `record_count` must reflect canonical rows, not audit-log-only approximations.
3. `delivery_proof_recorded` may be true only when proof type and proof reference are present in the canonical record.
4. `finance_export_recorded`, `source_writeback_recorded`, and `customer_billing_delivery_recorded` must remain explicit booleans that prove those downstream actions are not part of this readback contract.
5. Readback must expose whether the dedicated storage route is registered without implying route admission in the current lane.
6. Readback must never claim that finance output, source writeback, or customer billing delivery occurred merely because delivery/proof review state exists.

## Readback Proof Expectations

Any later admitted implementation should be able to prove:

1. same-payload replay leaves canonical ids stable
2. stale source fingerprints are classified explicitly
3. preview-review lineage mismatches are surfaced without reading workbook contents
4. delivery/proof review storage remains distinct from finance export, source writeback, and customer billing delivery
5. downstream finance, writeback, and live-output counts remain outside this readback

## Explicitly Blocked In This Lane

The following remain blocked after Lane 320:

1. product code, UI controls, routes, backend seams, payload versions, hosted calls, hosted smokes, and browser live route access
2. live mutation POSTs, schema migrations, Supabase/Render/Vercel/Olares actions, service/auth/ingress changes, and secret changes
3. source workbook/PDF writeback and workbook macros
4. persistence execution, runtime reads, registered routes, and hosted delivery/proof admission
5. finance, billing, payroll, invoice, accounting, labor reconciliation, external finance sync, and customer billing delivery behavior
6. autonomous AI business-state mutation

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 320 files.
3. Selected outcome is present.
4. Future readback route is present.
5. Allowed status values are present.
6. Finance/source-writeback separation rules are explicit.
7. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 321 - Project Miner Temp Power Customer Delivery And Durable Proof Route And Payload Design No-Live Packet`