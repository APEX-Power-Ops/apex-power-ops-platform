# APEX PM Lane 298 - Project Miner Temp Power Actuals And Customer Capture Local Mocked Request Dry Run No-Live Packet

Date: 2026-05-18

Status: Local no-live mocked-request dry run for actuals capture review and customer preview review

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_LOCAL_MOCKED_REQUEST_DRY_RUN_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 298 converts the Lane 296 request contract and Lane 297 execution gate into a mock-only local request preview.

This lane still does not admit any runtime route, browser control, or request send. It defines a dry-run builder that can assemble the exact future request envelope and payload for one chosen route, keep the preview on-screen or in local packet context only, and prove that no network request or record creation occurred.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report, completion evidence, customer delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`ACTUALS_CUSTOMER_CAPTURE_LOCAL_MOCKED_REQUEST_DRY_RUN_READY_NO_LIVE`

Meaning:

1. The future request can now be previewed locally in mock-only form.
2. The dry run remains no-live and sends no request.
3. Customer preview retains explicit no-delivery posture in the mock payload.
4. Finance outputs, source writeback, and all live/runtime behavior remain blocked.

## Dry Run Scope

The dry run may build exactly one of the following future requests at a time:

1. `POST /api/v1/mutations/temp-power-actuals-capture-reviews`
2. `POST /api/v1/mutations/temp-power-customer-preview-reviews`

The dry run must always include:

1. exact current `project_id`, `candidate_id`, and `source_fingerprint`
2. exact matching envelope and payload `idempotency_key`
3. `mutation_class: C`
4. `pm_actor`, `pm_actor_role=PM`, and `pm_timestamp`
5. full payload for the chosen route

## Mocked Request Builder Rules

The dry-run builder must satisfy all of the following:

1. choose exactly one route at a time
2. build the full future envelope and payload shape
3. set `network_request_sent=false`
4. set `record_created=false`
5. keep the result local-only for review or later packet context
6. reject stale project/candidate/source identity before any preview is considered valid

## Actuals Capture Mock Payload

For actuals-capture review, the dry run must preview:

1. `action_type: persist_temp_power_actuals_capture_review`
2. task/apparatus-or-fallback scope
3. review-only `actual_labor_hours_preview`
4. evidence bundle fields
5. correction linkage fields when applicable
6. PM review status and note fields

## Customer Preview Mock Payload

For customer-preview review, the dry run must preview:

1. `action_type: persist_temp_power_customer_preview_review`
2. named recipient and recipient-role review
3. delivery-channel review
4. preview artifact references
5. future delivery-proof placeholders
6. `durable_delivery_event=false`
7. `delivery_proof_recorded=false`
8. `delivery_block_reason`

## Required Local Dry Run Proof

Any local dry-run artifact or closeout must be able to show:

1. chosen route
2. exact envelope preview
3. exact payload preview
4. `network_request_sent=false`
5. `record_created=false`
6. unchanged downstream delivery/finance/writeback posture

## Explicitly Not Admitted By This Lane

This lane does not admit:

1. browser controls that submit a request
2. any runtime route call or network request
3. any record creation or replay proof
4. customer delivery or delivery-proof recording
5. any finance/export/accounting/source-writeback behavior

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 298 files.
3. Selected outcome is present.
4. Dry-run builder rules are present.
5. Chosen routes and action types are present.
6. `network_request_sent=false`, `record_created=false`, `durable_delivery_event=false`, and `delivery_proof_recorded=false` are explicit.
7. Blocked-output boundaries remain explicit.
8. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 299 - Project Miner Temp Power Actuals And Customer Capture Dry Run Envelope Export No-Live Packet`