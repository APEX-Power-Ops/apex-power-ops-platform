# APEX PM Lane 292 - Project Miner Temp Power Actuals And Customer Capture Contract Design No-Live Packet

Date: 2026-05-18

Status: Local no-live contract-design surface for actuals capture and customer preview

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_CONTRACT_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 292 converts the accepted Lane 291 actuals/labor and customer report/delivery defaults into a no-live contract-design surface.

This lane does not admit persistence, delivery, or any runtime path. It defines the future packet shape, validator rules, review checklist, and payload-template boundaries that any later actuals/customer review surface or execution admission would have to satisfy.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report, completion evidence, customer delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`ACTUALS_CUSTOMER_CAPTURE_CONTRACT_DESIGN_READY_NO_LIVE`

Meaning:

1. The accepted Lane 291 defaults are translated into explicit contract fields and validators.
2. Actuals capture remains a no-live contract and review surface only.
3. Customer report remains a preview artifact design only with no durable delivery event.
4. Finance outputs, source writeback, and any live mutation path remain out of scope and blocked.

## Source Authority

| Field | Value |
| --- | --- |
| Current project | `pm-import-project-miner-temp-power` |
| Current candidate | `pm-import-candidate-miner-temp-power` |
| Prior lane | PM Lane 291 |
| Prior outcome | `ACTUALS_CUSTOMER_RULES_ONLY_NO_LIVE_CAPTURE_DESIGN_READY` |
| Allowed design scope | actuals capture contract and customer preview contract only |
| Finance design scope | blocked |
| Source writeback scope | blocked |
| Downstream output authority | `not_admitted` |

## Actuals Capture Contract

The actuals capture contract is review-only and future-facing.

Required contract fields:

1. `project_id` = `pm-import-project-miner-temp-power`
2. `candidate_id` = `pm-import-candidate-miner-temp-power`
3. `source_fingerprint`
4. `task_id`
5. `apparatus_id` when apparatus-specific; otherwise `task_day_fallback_reason`
6. `work_date`
7. `recorder_role` constrained to `PM` or `FIELD_LEAD`
8. `actual_labor_hours_preview` as a nonnegative decimal review field
9. `work_summary_note`
10. `evidence_bundle` containing `primary_evidence_type`, `primary_evidence_ref`, and optional `supporting_evidence_refs`
11. `correction_mode` constrained to `NEW_ENTRY` or `VOID_AND_REPLACEMENT`
12. `supersedes_capture_id` and `replacement_reason` when `correction_mode=VOID_AND_REPLACEMENT`
13. `pm_billable_payroll_review_status` and `pm_billable_payroll_review_note`

Validator rules:

1. `task_id` is always required.
2. `apparatus_id` is required when the capture is apparatus-specific; otherwise `task_day_fallback_reason` is required.
3. `recorder_role` must be `PM` or `FIELD_LEAD`.
4. `actual_labor_hours_preview` must be greater than or equal to `0.00`.
5. Any nonzero `actual_labor_hours_preview` requires a populated `evidence_bundle`.
6. `VOID_AND_REPLACEMENT` requires both `supersedes_capture_id` and `replacement_reason`.
7. No later billable or payroll relevance may be considered ready without PM review fields present.

## Customer Preview Contract

The customer preview contract remains preview-only and future-facing.

Required contract fields:

1. `project_id` = `pm-import-project-miner-temp-power`
2. `customer_preview_id`
3. `coverage_scope_task_ids`
4. `coverage_scope_apparatus_ids` when apparatus-specific coverage is present
5. `preview_summary`
6. `approver_role` constrained to `PM`
7. `named_recipient_name`
8. `named_recipient_role`
9. `delivery_channel` constrained to `CONTROLLED_EMAIL` or `LATER_APPROVED_PORTAL`
10. `preview_artifact_refs`
11. `future_delivery_proof_requirements`
12. `durable_delivery_event` fixed to `false`
13. `delivery_block_reason`

Validator rules:

1. `approver_role` must be `PM`.
2. `named_recipient_name` and `named_recipient_role` are required.
3. `delivery_channel` must be `CONTROLLED_EMAIL` or `LATER_APPROVED_PORTAL`.
4. `preview_artifact_refs` must point only to preview artifacts, not sent artifacts.
5. `durable_delivery_event` must remain `false`.
6. `future_delivery_proof_requirements` may record later evidence expectations but may not claim delivery occurred.

## Review Checklist

Any later PM review surface built from this contract must show:

1. project, candidate, and source identity
2. task and apparatus-or-fallback context
3. recorder-role restriction and PM review fields
4. evidence completeness before nonzero actuals
5. correction linkage when replacement is requested
6. named customer recipient and allowed delivery channel
7. explicit `durable_delivery_event=false`
8. blocked finance, writeback, and live-output boundaries

## Future Payload Templates

The contract defines future no-live payload templates only.

Actuals capture preview template:

```json
{
  "project_id": "pm-import-project-miner-temp-power",
  "candidate_id": "pm-import-candidate-miner-temp-power",
  "source_fingerprint": "<current-source-fingerprint>",
  "task_id": "<task-id>",
  "apparatus_id": "<apparatus-id-or-null>",
  "task_day_fallback_reason": "<required-when-apparatus-id-null>",
  "work_date": "YYYY-MM-DD",
  "recorder_role": "PM",
  "actual_labor_hours_preview": 0.0,
  "work_summary_note": "<review-note>",
  "evidence_bundle": {
    "primary_evidence_type": "SIGNED_FIELD_TICKET",
    "primary_evidence_ref": "<artifact-ref>",
    "supporting_evidence_refs": []
  },
  "correction_mode": "NEW_ENTRY",
  "supersedes_capture_id": null,
  "replacement_reason": null,
  "pm_billable_payroll_review_status": "PENDING_PM_REVIEW",
  "pm_billable_payroll_review_note": "<pm-note>"
}
```

Customer preview template:

```json
{
  "project_id": "pm-import-project-miner-temp-power",
  "customer_preview_id": "<preview-id>",
  "coverage_scope_task_ids": ["<task-id>"],
  "coverage_scope_apparatus_ids": [],
  "preview_summary": "<preview-summary>",
  "approver_role": "PM",
  "named_recipient_name": "<recipient-name>",
  "named_recipient_role": "<recipient-role>",
  "delivery_channel": "CONTROLLED_EMAIL",
  "preview_artifact_refs": ["<preview-artifact-ref>"],
  "future_delivery_proof_requirements": ["EMAIL_RECEIPT", "SIGNED_TRANSMITTAL"],
  "durable_delivery_event": false,
  "delivery_block_reason": "DELIVERY_REQUIRES_SEPARATE_ADMISSION"
}
```

## Explicitly Blocked In This Lane

The following remain blocked after Lane 292:

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
2. Decision label is present in all touched Lane 292 files.
3. Selected outcome is present.
4. Actuals capture contract fields are present.
5. Customer preview contract fields are present.
6. `durable_delivery_event` remains fixed to `false`.
7. Blocked-output boundaries remain explicit.
8. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 293 - Project Miner Temp Power Actuals And Customer Capture Review Surface Design No-Live Packet`