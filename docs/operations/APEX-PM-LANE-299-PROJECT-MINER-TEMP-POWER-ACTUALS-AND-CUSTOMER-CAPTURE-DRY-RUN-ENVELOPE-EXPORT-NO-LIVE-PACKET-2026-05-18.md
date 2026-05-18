# APEX PM Lane 299 - Project Miner Temp Power Actuals And Customer Capture Dry Run Envelope Export No-Live Packet

Date: 2026-05-18

Status: Local no-live dry-run envelope export for actuals capture review and customer preview review

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_DRY_RUN_ENVELOPE_EXPORT_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 299 converts the Lane 298 local mocked-request preview into one browser-local export artifact.

This lane still does not admit any runtime route, browser submit control, or request send. It defines how the exact mock-only request envelope can be exported as JSON for review or later packet context while refreshing the local preview and proving that no network request or record creation occurred.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report, completion evidence, customer delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`ACTUALS_CUSTOMER_CAPTURE_DRY_RUN_ENVELOPE_EXPORT_READY_NO_LIVE`

Meaning:

1. One chosen mock-only request envelope can now be exported as JSON.
2. The exported envelope remains review-only and no-live.
3. The local preview may refresh after export, but no request is sent.
4. Delivery, finance, and source-writeback boundaries remain blocked.

## Export Scope

The export may contain exactly one of the following route envelopes at a time:

1. `POST /api/v1/mutations/temp-power-actuals-capture-reviews`
2. `POST /api/v1/mutations/temp-power-customer-preview-reviews`

The exported JSON must preserve:

1. exact `project_id`, `candidate_id`, and `source_fingerprint`
2. exact matching envelope and payload `idempotency_key`
3. `mutation_class: C`
4. `pm_actor`, `pm_actor_role=PM`, and `pm_timestamp`
5. full mock payload for the chosen route
6. boundary flags proving no request, no record, and no delivery event

## Export Artifact Contract

The dry-run envelope export artifact must include:

1. `artifact_type: temp_power_actuals_customer_capture_dry_run_envelope`
2. `route_selected`
3. `export_timestamp`
4. `export_actor`
5. `mock_envelope`
6. `mock_payload`
7. `boundary_flags`
8. `blocked_domains`

## Boundary Flags

The exported artifact must explicitly include:

1. `network_request_sent=false`
2. `record_created=false`
3. `durable_delivery_event=false`
4. `delivery_proof_recorded=false`

## Export Behavior Rules

The dry-run envelope export must satisfy all of the following:

1. export only the current chosen route preview
2. refresh the local preview after export
3. keep the result browser-local or packet-local only
4. reject export if project/candidate/source identity is stale or incomplete
5. preserve unchanged downstream delivery/finance/writeback posture

## Customer Preview Export Rules

If the chosen route is customer-preview review, the exported JSON must also preserve:

1. named recipient and recipient-role review
2. delivery-channel review
3. preview artifact references
4. `delivery_block_reason`
5. future delivery-proof placeholders

## Required Local Export Proof

Any local export proof or closeout must be able to show:

1. chosen route
2. exported artifact type
3. exact envelope preview snapshot
4. exact payload preview snapshot
5. `network_request_sent=false`
6. `record_created=false`
7. unchanged downstream delivery/finance/writeback posture

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
2. Decision label is present in all touched Lane 299 files.
3. Selected outcome is present.
4. Export artifact contract is present.
5. Chosen routes and artifact type are present.
6. `network_request_sent=false`, `record_created=false`, `durable_delivery_event=false`, and `delivery_proof_recorded=false` are explicit.
7. Blocked-output boundaries remain explicit.
8. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 300 - Project Miner Temp Power Actuals And Customer Capture Dry Run Readiness Checkpoint No-Live Packet`