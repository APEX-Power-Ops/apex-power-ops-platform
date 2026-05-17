# PM Lane 246 - Project Miner Temp Power Data Entry Exact Label Export Relay Context No-Live Packet

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_DATA_ENTRY_EXACT_LABEL_EXPORT_RELAY_CONTEXT_NO_LIVE`

## Purpose

PM Lane 246 reduces PM relay burden by carrying the exact-label response cue into copied review artifacts.

PM Lane 245 made the workbench UI explicit: the current unresolved `PROJECT_DATA_ENTRY_FORMULA_ERRORS` warning needs exactly one PM Lane 238 label. This lane extends that same cue into the PM intake brief and local import exception register export so copied handoffs do not lose the required response format.

## Selected Outcome

`DATA_ENTRY_EXPORTS_CARRY_EXACT_ONE_LABEL_RESPONSE_FORMAT_NO_LIVE`

## What Changed

1. Added "Next input needed" text to the exported Project Data Entry decision gate.
2. Added `return_exactly_one_pm_lane_238_label` as the response format in the PM intake brief and exception register exports.
3. Repeated that paraphrases and prior source-correction labels do not close the Data Entry warning gate.
4. Added focused smoke coverage for both export surfaces.
5. Preserved warning acceptance, approval, import, and hosted mutation blockers.

## Current Required Input

Return exactly one of these labels:

1. `ACCEPT_DATA_ENTRY_WARNING_NON_BLOCKING_NO_LIVE`
2. `REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE`
3. `HOLD_DATA_ENTRY_WARNING_NO_LIVE`
4. `PROVIDE_EXACT_LIVE_ADMISSION_LATER`

## Guardrails

PM Lane 246 does not add an approval button, import button, submit button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, live approval POST, approval row, project import, note, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS
