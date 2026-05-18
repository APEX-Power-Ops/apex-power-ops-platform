# APEX PM Lane 317 - Project Miner Temp Power Customer Delivery And Durable Proof Contract Design No-Live Packet

Date: 2026-05-18

Status: Local no-live contract-design surface for customer delivery and durable proof

Decision label:

`PROJECT_MINER_TEMP_POWER_CUSTOMER_DELIVERY_DURABLE_PROOF_CONTRACT_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 317 converts Lane 316's next-admission gate into a design-first contract packet.

This lane does not admit delivery execution, proof recording, or any runtime path. It defines the future customer-delivery packet shape, validator rules, review checklist, and payload-template boundaries that any later delivery/proof review surface or execution admission would have to satisfy.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report creation, completion evidence artifact storage, customer delivery event, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation output, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`CUSTOMER_DELIVERY_DURABLE_PROOF_CONTRACT_DESIGN_READY_NO_LIVE`

## Source Authority

| Field | Value |
| --- | --- |
| Current project | `pm-import-project-miner-temp-power` |
| Current candidate | `pm-import-candidate-miner-temp-power` |
| Prior lane | PM Lane 316 |
| Prior outcome | `CUSTOMER_DELIVERY_AND_DURABLE_PROOF_NEXT_ADMISSION_GATE_DEFINED` |
| Current review baseline | PM Lane 315 hosted-green customer-preview review |
| Finance design scope | blocked |
| Source writeback scope | blocked |
| Downstream output authority | `not_admitted` |

## Customer Delivery And Durable Proof Contract

The customer-delivery contract is future-facing and post-review only.

Required contract fields:

1. `project_id` = `pm-import-project-miner-temp-power`
2. `candidate_id` = `pm-import-candidate-miner-temp-power`
3. `source_fingerprint`
4. `customer_preview_review_id` referencing the approved customer-preview review record
5. `customer_delivery_event_id`
6. `named_recipient_name`
7. `named_recipient_role`
8. `delivery_channel` constrained to `CONTROLLED_EMAIL` or `LATER_APPROVED_PORTAL`
9. `delivery_artifact_refs` pointing only to the delivered customer-facing artifact set
10. `delivered_at_utc`
11. `delivery_proof_type` constrained to `EMAIL_RECEIPT`, `SIGNED_TRANSMITTAL`, or `PORTAL_TIMESTAMP`
12. `delivery_proof_ref`
13. `pm_delivery_approval_status`
14. `pm_delivery_approval_note`
15. `delivery_note`
16. `durable_delivery_event` constrained to `true` only inside a later separately admitted delivery lane
17. `delivery_proof_recorded` constrained to `true` only when proof is present in that same later lane

Validator rules:

1. `customer_preview_review_id` is always required and must point to the current hosted-green customer-preview review slice.
2. `named_recipient_name` and `named_recipient_role` are required and must match the intended customer recipient of the delivery event.
3. `delivery_channel` must be `CONTROLLED_EMAIL` or `LATER_APPROVED_PORTAL`.
4. `delivery_artifact_refs` must contain at least one delivered customer-facing artifact reference and may not reuse preview-only refs without explicit promotion traceability.
5. `delivered_at_utc` is required for any later durable delivery claim.
6. `delivery_proof_type` and `delivery_proof_ref` are both required together.
7. `pm_delivery_approval_status` and `pm_delivery_approval_note` are required before any later durable delivery event may be considered valid.
8. No finance, billing, payroll, invoice, accounting, external finance sync, or source-writeback fields may appear in the delivery contract.

## Review Checklist

Any later PM review surface built from this contract must show:

1. project, candidate, and source identity
2. linked customer-preview review id and preview-to-delivery lineage
3. named recipient and allowed delivery channel
4. delivered artifact set and proof type/reference completeness
5. PM delivery approval status and note
6. explicit separation from finance, billing, payroll, accounting, and source-writeback behavior

## Future Payload Template

The contract defines a future no-live payload template only.

```json
{
  "project_id": "pm-import-project-miner-temp-power",
  "candidate_id": "pm-import-candidate-miner-temp-power",
  "source_fingerprint": "<current-source-fingerprint>",
  "customer_preview_review_id": "<hosted-green-customer-preview-review-id>",
  "customer_delivery_event_id": "<delivery-event-id>",
  "named_recipient_name": "<recipient-name>",
  "named_recipient_role": "<recipient-role>",
  "delivery_channel": "CONTROLLED_EMAIL",
  "delivery_artifact_refs": ["<delivered-artifact-ref>"],
  "delivered_at_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "delivery_proof_type": "EMAIL_RECEIPT",
  "delivery_proof_ref": "<proof-ref>",
  "pm_delivery_approval_status": "APPROVED_FOR_DELIVERY_RECORDING",
  "pm_delivery_approval_note": "<pm-note>",
  "delivery_note": "<delivery-summary>",
  "durable_delivery_event": true,
  "delivery_proof_recorded": true
}
```

## Explicitly Blocked In This Lane

The following remain blocked after Lane 317:

1. product code, UI controls, routes, backend seams, payload versions, hosted calls, hosted smokes, and browser live route access
2. live mutation POSTs, schema migrations, Supabase/Render/Vercel/Olares actions, service/auth/ingress changes, and secret changes
3. source workbook/PDF writeback and workbook macros
4. production quantity writes, labor entry writes, actual labor hour writes, apparatus progress writes, and progress update writes
5. finance, billing, payroll, invoice, accounting, labor reconciliation, external finance sync, and customer billing delivery behavior
6. autonomous AI business-state mutation

## Validation Checks

Required validation for this lane:

1. Packet JSON parses.
2. Decision label is present in all touched Lane 317 files.
3. Selected outcome is present.
4. Customer delivery contract fields are present.
5. Validator rules for PM approval, delivery channel, and delivery proof are present.
6. Finance and source-writeback boundaries remain explicit.
7. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 318 - Project Miner Temp Power Customer Delivery And Durable Proof Review Surface Design No-Live Packet`