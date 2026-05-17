# PM Lane 244 - Project Miner Temp Power Data Entry Source-Correction Boundary Cue No-Live Packet

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_DATA_ENTRY_SOURCE_CORRECTION_BOUNDARY_CUE_NO_LIVE`

## Purpose

PM Lane 244 prevents an already-resolved source-correction label from being mistaken for the active Project Data Entry warning disposition.

The Ground Resistance source correction from PM Lane 236 remains applied as `Ground Resistance Test Lot`. The active unresolved warning is now `PROJECT_DATA_ENTRY_FORMULA_ERRORS`, which requires one PM Lane 238 Data Entry-specific label before warning acceptance or later live admission can be considered.

## Selected Outcome

`DATA_ENTRY_WARNING_GATE_NAMES_PRIOR_SOURCE_CORRECTION_AS_ALREADY_APPLIED`

## What Changed

1. Added a source-correction boundary object to the Project Data Entry warning-disposition gate.
2. Added PM-facing UI copy stating that `REQUEST_SOURCE_CORRECTION_NO_LIVE` is already applied to the Ground Resistance row.
3. Clarified that the active workbook-correction label is `REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE`.
4. Added focused smoke coverage for the boundary cue in the UI, dry-run envelope, and approval preview.
5. Added a Desktop Codex review-burden prompt limited to clarity and authority-boundary review.

## Current Warning Disposition

`REQUEST_SOURCE_CORRECTION_NO_LIVE` is not the active label for the current warning. It remains historical context for the resolved Ground Resistance source correction.

The active Data Entry warning remains reviewed but unresolved until one exact PM Lane 238 label is provided:

1. `ACCEPT_DATA_ENTRY_WARNING_NON_BLOCKING_NO_LIVE`
2. `REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE`
3. `HOLD_DATA_ENTRY_WARNING_NO_LIVE`
4. `PROVIDE_EXACT_LIVE_ADMISSION_LATER`

## Guardrails

PM Lane 244 does not add an approval button, import button, submit button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, live approval POST, approval row, project import, note, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS
