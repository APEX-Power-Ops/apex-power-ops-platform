# APEX PM Lane 293 - Project Miner Temp Power Actuals And Customer Capture Review Surface Design No-Live Packet

Date: 2026-05-18

Status: Local no-live PM-facing review-surface design for actuals capture and customer preview

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_REVIEW_SURFACE_DESIGN_NO_LIVE_NO_OUTPUT_WRITE`

## Purpose

PM Lane 293 converts the Lane 292 contract design into a future PM-facing read-only review surface definition.

This lane still does not admit a route, UI control, data fetch, or any execution path. It defines what the future inspection-only surface must display, what it must never permit, which preview artifacts are safe to show, and how blocked boundaries must remain visible to the reviewer.

This lane is not live admission. It creates no product code, UI control, route, backend seam, payload version, hosted call, hosted smoke, browser live route access, live mutation POST, schema migration, Supabase/Render/Vercel/Olares action, service/auth/ingress/secret change, source workbook/PDF writeback, workbook macro, production quantity, labor entry, actual labor hour, apparatus progress, progress update, customer report, completion evidence, customer delivery, billing export, payroll export, invoice, payroll record, accounting record, labor reconciliation, external finance sync, customer billing delivery, or autonomous AI business-state mutation.

## Selected Outcome

Selected outcome:

`ACTUALS_CUSTOMER_CAPTURE_REVIEW_SURFACE_DESIGN_READY_NO_LIVE`

Meaning:

1. The Lane 292 contract is translated into one PM-facing read-only review-surface design.
2. The future surface is inspection-only and may not create or send anything.
3. Actuals capture remains preview-only and customer delivery remains explicitly not performed.
4. Finance outputs, source writeback, and all live/runtime behavior remain blocked.

## Surface Scope

| Field | Value |
| --- | --- |
| Current project | `pm-import-project-miner-temp-power` |
| Current candidate | `pm-import-candidate-miner-temp-power` |
| Prior lane | PM Lane 292 |
| Prior outcome | `ACTUALS_CUSTOMER_CAPTURE_CONTRACT_DESIGN_READY_NO_LIVE` |
| Surface type | PM-facing review surface |
| Surface behavior | inspection-only |
| Future route placeholder | `not_admitted_read_only_surface_placeholder` |
| Downstream output authority | `not_admitted` |

## Required Surface Sections

Any later review surface built from this lane must include the following sections:

1. Identity header: project, candidate, source fingerprint, and current lane lineage.
2. Actuals capture summary: `task_id`, `apparatus_id` or fallback reason, `work_date`, `recorder_role`, and `actual_labor_hours_preview`.
3. Evidence readiness panel: `primary_evidence_type`, `primary_evidence_ref`, supporting evidence count, and a clear nonzero-actuals readiness state.
4. Correction panel: `correction_mode`, `supersedes_capture_id`, and `replacement_reason` when applicable.
5. PM review panel: `pm_billable_payroll_review_status` and `pm_billable_payroll_review_note`.
6. Customer preview panel: `customer_preview_id`, named recipient, recipient role, delivery channel, preview artifact references, and proof placeholders.
7. Boundary panel: explicit `durable_delivery_event=false`, blocked finance/writeback/output boundaries, and not-admitted delivery state.
8. Payload preview panel: read-only rendering of the actuals capture preview template and customer preview template.

## Display Rules

The future surface must follow these display rules:

1. Show project/candidate/source identity before any editable-looking field preview.
2. Visually mark nonzero actuals as blocked until evidence requirements are present.
3. Render replacement linkage only when `correction_mode=VOID_AND_REPLACEMENT`.
4. Always show `durable_delivery_event=false` as a locked boundary, not an editable toggle.
5. Show blocked finance, payroll, invoice, accounting, external finance sync, and source writeback boundaries in the same view.
6. Do not show send, submit, save, approve, post, export-to-source, or customer-deliver actions.

## Export-Safe Review Artifacts

The following later review artifacts would be safe only as local no-live exports:

1. contract summary JSON
2. actuals capture preview JSON
3. customer preview JSON
4. combined review checkpoint JSON summarizing boundary status and completeness

None of these artifacts may claim that actuals were persisted or that customer delivery occurred.

## Guardrails

The future surface must preserve all of the following guardrails:

1. no persistence route or backend write path
2. no customer delivery trigger or durable delivery event
3. no finance, payroll, invoice, accounting, or external finance controls
4. no workbook writeback or macro execution path
5. no hidden bypass around evidence readiness or PM review requirements
6. no autonomous AI execution path

## Review Outcome States

The surface may only present no-live review states such as:

1. `REVIEW_ONLY_INCOMPLETE_EVIDENCE`
2. `REVIEW_ONLY_READY_FOR_PM_REVIEW`
3. `REVIEW_ONLY_CUSTOMER_PREVIEW_DRAFT`
4. `REVIEW_ONLY_BLOCKED_BY_DELIVERY_ADMISSION`

These states are display-only and do not authorize any mutation or delivery.

## Explicitly Blocked In This Lane

The following remain blocked after Lane 293:

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
2. Decision label is present in all touched Lane 293 files.
3. Selected outcome is present.
4. Required surface sections are present.
5. Display rules are present.
6. `durable_delivery_event=false` remains explicit.
7. Blocked-output boundaries remain explicit.
8. `git diff --check` passes.

## Next Safe Packet

Next safe packet:

`PM Lane 294 - Project Miner Temp Power Actuals And Customer Capture Storage Plan Design No-Live Packet`