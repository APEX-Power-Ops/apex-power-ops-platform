# PM Lane 251 - Project Miner Temp Power Data Entry Valid Return Checklist No-Live Packet

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_DATA_ENTRY_VALID_RETURN_CHECKLIST_NO_LIVE`

## Purpose

PM Lane 251 reduces relay ambiguity by making the accepted and rejected reply shapes explicit for the open Project Data Entry warning.

The active warning remains `PROJECT_DATA_ENTRY_FORMULA_ERRORS`. PM Lane 250 showed what each exact PM Lane 238 label would route to next. This lane does not choose a label. It only defines the intake checklist for screening a future returned reply before a later no-live decision packet records it.

## Selected Outcome

`DATA_ENTRY_VALID_RETURN_CHECKLIST_VISIBLE_NO_LIVE`

## What Changed

1. Added a display-only "Valid return checklist" card in PM Decision Context.
2. Added matching valid-return checklist lines to the PM intake brief and local import exception register exports.
3. Kept the exact reply options card as the copy-safe answer source.
4. Preserved the open warning gate until exactly one PM Lane 238 Data Entry label is returned.
5. Added focused smoke coverage for the checklist card and exported checklist lines.

## Valid Return Checklist

| Rule | Meaning |
| --- | --- |
| `accepted` | Exactly one PM Lane 238 Data Entry label. |
| `rejected` | Explanation text, paraphrase, `REQUEST_SOURCE_CORRECTION_NO_LIVE`, multiple labels, or live-admission language without a later admitting packet. |
| `after valid label` | Record the label in a no-live decision packet and keep live admission separate. |

## Guardrails

PM Lane 251 does not add an approval button, import button, submit button, copy button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, live approval POST, approval row, project import, note, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS
