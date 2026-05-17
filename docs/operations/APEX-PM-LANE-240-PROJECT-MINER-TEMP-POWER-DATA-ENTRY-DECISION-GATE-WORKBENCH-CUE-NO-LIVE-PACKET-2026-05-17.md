# PM Lane 240 - Project Miner Temp Power Data Entry Decision Gate Workbench Cue No-Live Packet

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_DATA_ENTRY_DECISION_GATE_WORKBENCH_CUE_NO_LIVE`

## Purpose

PM Lane 240 moves the PM Lane 238/239 Project Data Entry warning decision state into the `/pm-review/import-intake` workbench.

The cue is display-only. It appears inside the existing Exception Review and PM Decisions panel when `PROJECT_DATA_ENTRY_FORMULA_ERRORS` is present. It shows the four allowed no-live response labels and the later admission prerequisites so the PM review surface carries the same decision boundary as the packet handoffs.

## Selected Outcome

`DATA_ENTRY_DECISION_GATE_VISIBLE_IN_WORKBENCH_NO_LIVE`

## What Changed

1. Added a display-only Project Data Entry decision gate cue inside the existing PM Decisions card.
2. Kept the surrounding disclosure structure, route, storage posture, and mutation boundary unchanged.
3. Added focused smoke coverage for the cue, all four allowed labels, and admission-prerequisite summary.
4. Added a Desktop Codex review-burden prompt for clarity review only.

## Allowed Labels Shown

1. `ACCEPT_DATA_ENTRY_WARNING_NON_BLOCKING_NO_LIVE`
2. `REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE`
3. `HOLD_DATA_ENTRY_WARNING_NO_LIVE`
4. `PROVIDE_EXACT_LIVE_ADMISSION_LATER`

## Admission Prerequisites Shown

The workbench cue summarizes:

1. current candidate identity,
2. warning disposition,
3. exact live phrase,
4. hosted-read currency,
5. replay/idempotency requirements,
6. approval-row evidence,
7. Desktop Codex review-only boundary.

## Guardrails

PM Lane 240 does not add an approval button, import button, submit button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, live approval POST, approval row, project import, note, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS
