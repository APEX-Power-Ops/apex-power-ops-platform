# APEX PM Lane 319 - Project Miner Temp Power Customer Delivery And Durable Proof Storage Plan Design No-Live Packet

Date: 2026-05-18

Status: Local no-live storage-plan design for customer delivery and durable proof review

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_DELIVERY_DURABLE_PROOF_STORAGE_PLAN_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 319 converts the Lane 317 contract design and Lane 318 review-surface design into a future storage decision only.

This lane still does not admit schema, persistence, runtime routes, or any execution path. It documents where later reviewed customer-delivery/proof packets should live, what adapters and readbacks they would require, what fields must remain append-only, and which unsafe storage shortcuts stay rejected.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report creation, completion evidence artifact storage, customer delivery event persistence, delivery proof persistence, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation output, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`CUSTOMER_DELIVERY_DURABLE_PROOF_STORAGE_PLAN_DESIGN_READY_NO_LIVE`

Meaning:

1. The accepted delivery/proof contract and review surface now have a future storage-plan decision.
2. The plan remains design-only and does not admit schema or persistence.
3. Customer delivery and proof remain future non-runtime storage objects only.
4. Finance outputs, source writeback, and all live/runtime behavior remain blocked.

## Storage Scope

| Field | Value |
| --- | --- |
| Current project | `pm-import-project-miner-temp-power` |
| Current candidate | `pm-import-candidate-miner-temp-power` |
| Prior lane | PM Lane 318 |
| Prior outcome | `CUSTOMER_DELIVERY_DURABLE_PROOF_REVIEW_SURFACE_DESIGN_READY_NO_LIVE` |
| Storage owner | mutation seam only |
| Finance storage scope | blocked |
| Source writeback scope | blocked |
| Runtime delivery scope | blocked |

## Recommended Storage Decision

The later admitted storage path should use one dedicated insert-only table owned by the mutation seam:

1. `seam.pm_customer_delivery_proof_reviews`

Recommended future entity type:

1. `pm_customer_delivery_proof_review`

Recommended future mutation route:

1. `/api/v1/mutations/temp-power-customer-delivery-proof-reviews`

Recommended future readback route:

1. `/api/v1/reads/temp-power-customer-delivery-proof-status`

## Recommended Columns And Constraints

Recommended columns for `seam.pm_customer_delivery_proof_reviews`:

1. canonical ids: `customer_delivery_proof_review_id`, `project_id`, `candidate_id`, `source_fingerprint`
2. lineage identity: `customer_preview_review_id`, `customer_delivery_event_id`, `preview_artifact_lineage_json`
3. recipient metadata: `named_recipient_name`, `named_recipient_role`, `delivery_channel`
4. delivery metadata: `delivery_artifact_refs_json`, `delivered_at_utc`, `delivery_note`
5. proof metadata: `delivery_proof_type`, `delivery_proof_ref`, `delivery_proof_recorded`, `proof_recorded_at_utc`
6. PM approval metadata: `pm_delivery_approval_status`, `pm_delivery_approval_note`, `pm_actor`, `pm_reviewed_at`
7. idempotency and audit: `idempotency_key`, `mutation_class`, `created_at`, `source_route`

Required storage constraints:

1. insert-only storage; later corrections use append-only replacement rows
2. unique `idempotency_key` per route and canonical record
3. `delivery_proof_recorded` may be true only when `delivery_proof_type` and `delivery_proof_ref` are both present
4. no finance/accounting/payroll/export columns in the table
5. no source workbook path, macro command, or customer billing delivery columns in the table

## Adapter And Readback Requirements

Any later admitted implementation must include:

1. a dedicated adapter rather than generic PgDict upsert
2. readback classification for preview-review linkage, current status, record counts, proof completeness, and last-review metadata
3. same-payload idempotent replay behavior returning the original canonical record ids
4. explicit proof in readback that delivery/proof storage is not finance export, source writeback, or customer billing delivery
5. append-only correction lineage readback if later replacement records are admitted

## Rejected Unsafe Storage Options

The following remain explicitly rejected:

1. audit-log-only storage as canonical delivery/proof review state
2. reusing customer preview review rows or generic delivery rows for delivery/proof review persistence
3. browser-local storage as canonical PM review storage
4. generic PgDict upsert without a dedicated adapter and readback contract
5. direct provider logs from email or portal systems as canonical storage without a seam-owned review row
6. direct Supabase writes from UI, scripts, or ad hoc tools
7. any storage path that implies finance export or source writeback occurred

## Admission Sequence For Later Packets

Any future live implementation must be sequenced after separate packets for:

1. storage-plan review acceptance
2. readback contract design
3. route and payload admission
4. dedicated schema admission
5. bounded execution gate with idempotent replay proof

## Explicitly Blocked In This Lane

The following remain blocked after Lane 319:

1. product code, UI controls, routes, backend seams, payload versions, hosted calls, hosted smokes, and browser live route access
2. live mutation POSTs, schema migrations, Supabase/Render/Vercel/Olares actions, service/auth/ingress changes, and secret changes
3. source workbook/PDF writeback and workbook macros
4. persistence execution, readback routes, and hosted delivery/proof admission
5. finance, billing, payroll, invoice, accounting, labor reconciliation, external finance sync, and customer billing delivery behavior
6. autonomous AI business-state mutation

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 319 files.
3. Selected outcome is present.
4. Recommended table and route are present.
5. Rejected unsafe storage options are present.
6. Runtime/finance boundaries remain explicit.
7. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 320 - Project Miner Temp Power Customer Delivery And Durable Proof Readback Design No-Live Packet`