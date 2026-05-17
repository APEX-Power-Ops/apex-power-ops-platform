# PM Lane 247 - Project Miner Temp Power Data Entry Exact Reply Options Workbench Cue No-Live Packet

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_DATA_ENTRY_EXACT_REPLY_OPTIONS_WORKBENCH_CUE_NO_LIVE`

## Purpose

PM Lane 247 reduces PM relay burden by making the open Project Data Entry warning response copy-safe in the workbench.

The current unresolved warning is `PROJECT_DATA_ENTRY_FORMULA_ERRORS`. PM Lane 245 made the next required response format explicit, and PM Lane 246 carried it into exports. This lane adds a display-only exact reply options card so the workbench itself shows that the next answer should be exactly one line, not a paraphrase or the already-applied source-correction label.

## Selected Outcome

`DATA_ENTRY_WORKBENCH_SHOWS_COPY_SAFE_ONE_LINE_REPLY_OPTIONS_NO_LIVE`

## What Changed

1. Added a display-only "Exact reply options" card under PM Decision Context.
2. Listed the four PM Lane 238 labels as one-line reply options.
3. Added a local warning not to include explanation text, a paraphrase, or `REQUEST_SOURCE_CORRECTION_NO_LIVE`.
4. Added focused smoke coverage for the workbench cue.
5. Preserved warning acceptance, approval, import, and hosted mutation blockers.

## Current Required Input

Copy exactly one of these lines:

1. `ACCEPT_DATA_ENTRY_WARNING_NON_BLOCKING_NO_LIVE`
2. `REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE`
3. `HOLD_DATA_ENTRY_WARNING_NO_LIVE`
4. `PROVIDE_EXACT_LIVE_ADMISSION_LATER`

## Guardrails

PM Lane 247 does not add an approval button, import button, submit button, copy button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, live approval POST, approval row, project import, note, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS
