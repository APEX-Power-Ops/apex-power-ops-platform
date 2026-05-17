# PM Lane 243 - Project Miner Temp Power Approval Preview Warning Disposition Guard No-Live Packet

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_APPROVAL_PREVIEW_WARNING_DISPOSITION_GUARD_NO_LIVE`

## Purpose

PM Lane 243 carries the PM Lane 242 warning-disposition guard into the older approval packet preview export.

The approval preview is still browser-local review context only. It now distinguishes reviewed warning evidence from accepted warning evidence before any later approval-persistence packet can consume the preview.

## Selected Outcome

`APPROVAL_PREVIEW_CARRIES_DATA_ENTRY_WARNING_DISPOSITION_NO_LIVE`

## What Changed

1. Added `warning_review` to the approval packet preview local review evidence.
2. Added reviewed warning codes, accepted warning codes, unresolved warning codes, and the Project Data Entry warning-disposition gate.
3. Kept `PROJECT_DATA_ENTRY_FORMULA_ERRORS` out of accepted warning evidence while no exact PM Lane 238 label is present.
4. Added focused smoke coverage for the approval preview warning-disposition fields.
5. Added a Desktop Codex review-burden prompt for preview-context review only.

## Current Warning Disposition

`PROJECT_DATA_ENTRY_FORMULA_ERRORS` is reviewed but unresolved. It remains excluded from accepted warning codes until one exact PM Lane 238 label is provided:

1. `ACCEPT_DATA_ENTRY_WARNING_NON_BLOCKING_NO_LIVE`
2. `REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE`
3. `HOLD_DATA_ENTRY_WARNING_NO_LIVE`
4. `PROVIDE_EXACT_LIVE_ADMISSION_LATER`

## Guardrails

PM Lane 243 does not add an approval button, import button, submit button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, live approval POST, approval row, project import, note, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS
