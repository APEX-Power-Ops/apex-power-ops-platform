# APEX PM Lane 294 - Project Miner Temp Power Actuals And Customer Capture Storage Plan Design No-Live Packet

Date: 2026-05-18

Status: Local no-live storage-plan design for actuals capture review and customer preview review

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_STORAGE_PLAN_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 294 converts the Lane 292 contract design and Lane 293 review-surface design into a future storage decision only.

This lane still does not admit schema, persistence, runtime routes, or any execution path. It documents where later reviewed actuals-capture packets and customer-preview packets should live, what adapters and readbacks they would require, what fields must remain append-only, and which unsafe storage shortcuts stay rejected.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report, completion evidence, customer delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`ACTUALS_CUSTOMER_CAPTURE_STORAGE_PLAN_DESIGN_READY_NO_LIVE`

Meaning:

1. The accepted actuals/customer contracts now have a future storage-plan decision.
2. The plan remains design-only and does not admit schema or persistence.
3. Customer preview remains non-delivery storage only.
4. Finance outputs, source writeback, and all live/runtime behavior remain blocked.

## Storage Scope

| Field | Value |
| --- | --- |
| Current project | `pm-import-project-miner-temp-power` |
| Current candidate | `pm-import-candidate-miner-temp-power` |
| Prior lane | PM Lane 293 |
| Prior outcome | `ACTUALS_CUSTOMER_CAPTURE_REVIEW_SURFACE_DESIGN_READY_NO_LIVE` |
| Storage owner | mutation seam only |
| Finance storage scope | blocked |
| Source writeback scope | blocked |
| Delivery-event storage scope | blocked |

## Recommended Storage Decision

The later admitted storage path should use dedicated insert-only tables owned by the mutation seam:

1. `seam.pm_actuals_capture_reviews`
2. `seam.pm_customer_preview_reviews`

Recommended future entity types:

1. `pm_actuals_capture_review`
2. `pm_customer_preview_review`

Recommended future mutation routes:

1. `/api/v1/mutations/temp-power-actuals-capture-reviews`
2. `/api/v1/mutations/temp-power-customer-preview-reviews`

Recommended future readback routes:

1. `/api/v1/reads/temp-power-actuals-capture-review-status`
2. `/api/v1/reads/temp-power-customer-preview-status`

## Recommended Columns And Constraints

Recommended columns for `seam.pm_actuals_capture_reviews`:

1. canonical ids: `review_id`, `project_id`, `candidate_id`, `source_fingerprint`
2. capture identity: `task_id`, `apparatus_id`, `task_day_fallback_reason`, `work_date`
3. reviewer metadata: `recorder_role`, `pm_review_status`, `pm_review_note`, `pm_actor`, `pm_reviewed_at`
4. actuals preview values: `actual_labor_hours_preview`, `work_summary_note`
5. evidence metadata: `primary_evidence_type`, `primary_evidence_ref`, `supporting_evidence_refs_json`
6. correction linkage: `correction_mode`, `supersedes_review_id`, `replacement_reason`
7. idempotency and audit: `idempotency_key`, `mutation_class`, `created_at`, `source_route`

Recommended columns for `seam.pm_customer_preview_reviews`:

1. canonical ids: `customer_preview_review_id`, `project_id`, `candidate_id`, `source_fingerprint`
2. preview identity: `customer_preview_id`, `coverage_scope_task_ids_json`, `coverage_scope_apparatus_ids_json`
3. preview content: `preview_summary`, `preview_artifact_refs_json`, `future_delivery_proof_requirements_json`
4. recipient metadata: `named_recipient_name`, `named_recipient_role`, `delivery_channel`
5. PM review metadata: `approver_role`, `pm_review_status`, `pm_review_note`, `pm_actor`, `pm_reviewed_at`
6. delivery boundary metadata: `durable_delivery_event`, `delivery_block_reason`
7. idempotency and audit: `idempotency_key`, `mutation_class`, `created_at`, `source_route`

Required storage constraints:

1. insert-only storage; later corrections use append-only replacement rows
2. unique `idempotency_key` per route and canonical record
3. `durable_delivery_event` must remain `false` for all customer preview rows in this design lane
4. no finance/accounting/payroll/export columns in either table
5. no source workbook path or macro command columns in either table

## Adapter And Readback Requirements

Any later admitted implementation must include:

1. dedicated adapters rather than generic PgDict upsert
2. readback classification for current status, candidate/source match, record counts, and last-review metadata
3. same-payload idempotent replay behavior returning the original canonical record ids
4. append-only correction lineage readback for actuals review replacements
5. explicit proof in readback that customer preview storage is not customer delivery

## Rejected Unsafe Storage Options

The following remain explicitly rejected:

1. audit-log-only storage as canonical review state
2. reusing `projects`, `tasks`, `apparatus`, or delivery rows for review-state persistence
3. browser-local storage as canonical PM review storage
4. generic PgDict upsert without a dedicated adapter and readback contract
5. direct Supabase writes from Excel, UI, or ad hoc scripts
6. any storage path that implies customer delivery or finance export occurred

## Admission Sequence For Later Packets

Any future live implementation must be sequenced after separate packets for:

1. storage-plan review acceptance
2. readback contract design
3. route and payload admission
4. dedicated schema admission
5. bounded execution gate with idempotent replay proof

## Explicitly Blocked In This Lane

The following remain blocked after Lane 294:

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
2. Decision label is present in all touched Lane 294 files.
3. Selected outcome is present.
4. Recommended tables and routes are present.
5. Rejected unsafe storage options are present.
6. `durable_delivery_event` remains constrained to `false`.
7. Blocked-output boundaries remain explicit.
8. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 295 - Project Miner Temp Power Actuals And Customer Capture Readback Design No-Live Packet`