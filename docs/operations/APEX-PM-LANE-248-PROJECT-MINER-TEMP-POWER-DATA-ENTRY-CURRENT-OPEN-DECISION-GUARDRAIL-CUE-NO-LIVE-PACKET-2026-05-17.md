# PM Lane 248 - Project Miner Temp Power Data Entry Current Open Decision Guardrail Cue No-Live Packet

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_DATA_ENTRY_CURRENT_OPEN_DECISION_GUARDRAIL_CUE_NO_LIVE`

## Purpose

PM Lane 248 reduces PM scan burden by surfacing the open Project Data Entry decision in the main Current PM Next Actions and Guardrails panel.

PM Lane 247 made the exact reply options copy-safe inside PM Decision Context. This lane adds a compact current-open-decision cue near the daily guardrails so the unresolved `PROJECT_DATA_ENTRY_FORMULA_ERRORS` decision is visible before a reviewer drills into the detailed exception panel.

## Selected Outcome

`DATA_ENTRY_OPEN_DECISION_VISIBLE_IN_CURRENT_GUARDRAILS_NO_LIVE`

## What Changed

1. Added a display-only "Current Open PM Decision" card under Current Review Actions.
2. Pointed the reviewer back to the Project Data Entry exact reply options card.
3. Repeated that explanation text, paraphrases, and `REQUEST_SOURCE_CORRECTION_NO_LIVE` do not belong in the reply.
4. Repeated the no-live boundary for warning acceptance, approval, import, source writeback, and hosted mutation.
5. Added focused smoke coverage for the guardrail cue.

## Current Required Input

Copy exactly one PM Lane 238 label from the Project Data Entry exact reply options card:

1. `ACCEPT_DATA_ENTRY_WARNING_NON_BLOCKING_NO_LIVE`
2. `REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE`
3. `HOLD_DATA_ENTRY_WARNING_NO_LIVE`
4. `PROVIDE_EXACT_LIVE_ADMISSION_LATER`

## Guardrails

PM Lane 248 does not add an approval button, import button, submit button, copy button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, live approval POST, approval row, project import, note, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS
