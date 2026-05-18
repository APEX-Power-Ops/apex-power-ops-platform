# PM Lane 335 - Project Miner Temp Power Customer Preview Review Hosted First Row Live Admission

## Decision

Jason's standing PM blocker authority plus explicit authority to provide the next exact phrase as applicable is applied to the missing hosted preview-review first row.

Exact phrase used for this bounded packet:

`ADMIT_TEMP_POWER_CUSTOMER_PREVIEW_REVIEW_HOSTED_FIRST_ROW_PACKET_ONLY`

This lane admits one hosted customer-preview review row only. It does not admit customer-facing delivery execution, customer delivery events, finance output, source writeback, or customer billing delivery.

## Prewrite Blocker

The first hosted prewrite probe after PM Lane 334 exposed a real storage blocker rather than a governance blocker.

Both public hosts returned:

- preview status: `customer_preview_review_storage_unavailable`
- delivery/proof status: `customer_delivery_proof_review_storage_unavailable`
- error type: `UndefinedTable`
- missing tables: `seam.pm_customer_preview_reviews` and `seam.pm_customer_delivery_proof_reviews`

This was not a general database outage. A previously admitted lane such as `GET /api/v1/reads/customer-completion-status` still returned `classification=customer_completion_baseline_recorded` with `storage_available=true`.

## Repair Path

The branch repaired the hosted blocker in two bounded steps:

1. commit `1da2aff564e39c849c118681a50b241ea3056e52` added runtime schema-ensure fallback for the Temp Power preview-review and delivery/proof tables so the public service can apply committed migrations only when those tables are missing
2. the first hosted preview POST then exposed a narrow insert-shape defect, so commit `9f8e66c4adf0bceaf6ebc7445c72407079516fd4` removed non-schema field `review_storage_status` from persisted preview rows while keeping it in the response envelope

## Hosted Packet

Hosted prewrite status after the repair path:

- status: `no_customer_preview_review_record`
- storage available: `true`
- record count: `0`

Hosted request envelope:

- route: `POST /api/v1/mutations/temp-power-customer-preview-reviews`
- action type: `persist_temp_power_customer_preview_review`
- mutation class: `C`
- source: `online`
- project id: `pm-import-project-miner-temp-power`
- candidate id: `pm-import-candidate-miner-temp-power`
- source fingerprint: `e111fdbe934bf9de07ed24c1`
- preview artifact refs: `preview://temp-power/2026-05-18/review-bundle-0001`

Hosted result:

- first POST status: `accepted`
- replay POST status: `idempotent_hit`
- preview review id: `temp-power-customer-preview-review-1085e8e5fad27553463479f7`
- mutation id: `mut-0b90c799-7b57-48da-bfd5-7016c22fc3cd`
- audit event id: `audit-e9057a6e-fd7c-479a-87f8-6b561ac4a310`

Hosted readback from both `https://mutation-seam.apexpowerops.com` and `https://apex-platform-mutation-seam.onrender.com`:

- status: `customer_preview_delivery_blocked`
- record count: `1`
- latest customer preview review id: `temp-power-customer-preview-review-1085e8e5fad27553463479f7`
- storage available: `true`
- current candidate match: `true`
- current source fingerprint match: `true`

## Boundary

This lane creates only the canonical hosted preview-review row.

Still blocked:

- customer-facing delivery execution
- finance, billing, payroll, invoice, accounting, and external finance output
- source workbook or PDF writeback
- customer billing delivery

## Outcome

Final outcome:

`CUSTOMER_PREVIEW_REVIEW_HOSTED_FIRST_ROW_PASS_DELIVERY_BLOCKED`

## Next Blocker

The canonical hosted preview-review row now exists, so the next bounded packet is the already-gated delivery/proof hosted first-row sequence.