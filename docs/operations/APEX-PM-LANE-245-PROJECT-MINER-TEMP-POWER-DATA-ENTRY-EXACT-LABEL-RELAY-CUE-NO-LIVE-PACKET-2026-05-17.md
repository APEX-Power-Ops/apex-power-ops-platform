# PM Lane 245 - Project Miner Temp Power Data Entry Exact Label Relay Cue No-Live Packet

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_DATA_ENTRY_EXACT_LABEL_RELAY_CUE_NO_LIVE`

## Purpose

PM Lane 245 reduces PM relay burden by making the next required Data Entry warning input explicit and copy-safe.

The current unresolved warning is `PROJECT_DATA_ENTRY_FORMULA_ERRORS`. This lane does not choose a warning disposition. It only states that the next PM input must be exactly one PM Lane 238 label.

## Selected Outcome

`DATA_ENTRY_WARNING_GATE_EXPOSES_EXACT_ONE_LABEL_RESPONSE_FORMAT_NO_LIVE`

## What Changed

1. Added `next_input_needed` to the Project Data Entry warning-disposition gate.
2. Added a visible "Next exact input needed" card to the PM decision context.
3. Kept all four PM Lane 238 labels visible with short meanings.
4. Repeated that paraphrases and the already-applied Ground Resistance source-correction label do not close the Data Entry warning gate.
5. Added focused smoke coverage for the UI, dry-run envelope, and approval preview.

## Current Required Input

Return exactly one of these labels:

1. `ACCEPT_DATA_ENTRY_WARNING_NON_BLOCKING_NO_LIVE`
2. `REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE`
3. `HOLD_DATA_ENTRY_WARNING_NO_LIVE`
4. `PROVIDE_EXACT_LIVE_ADMISSION_LATER`

## Guardrails

PM Lane 245 does not add an approval button, import button, submit button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, live approval POST, approval row, project import, note, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS
