# PM Lane 250 - Project Miner Temp Power Data Entry Decision Outcome Route Preview No-Live Packet

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_DATA_ENTRY_DECISION_OUTCOME_ROUTE_PREVIEW_NO_LIVE`

## Purpose

PM Lane 250 reduces PM decision friction by showing what each exact PM Lane 238 Project Data Entry label would route to next.

PM Lane 249 kept the active `PROJECT_DATA_ENTRY_FORMULA_ERRORS` gate open because the returned `REQUEST_SOURCE_CORRECTION_NO_LIVE` label already belongs to the Ground Resistance correction. This lane does not choose a Data Entry label. It only adds a route preview so the next exact label can be selected with less back-and-forth.

## Selected Outcome

`DATA_ENTRY_EXACT_LABEL_OUTCOME_ROUTES_VISIBLE_NO_LIVE`

## What Changed

1. Added a display-only "What each reply does next" route-preview card in PM Decision Context.
2. Added the same outcome route lines to the local import exception register export.
3. Preserved the exact reply options card as the only copy-safe answer source.
4. Preserved the open warning gate until exactly one PM Lane 238 Data Entry label is returned.
5. Added focused smoke coverage for the route-preview card and export lines.

## Route Preview

| Exact label | Route preview |
| --- | --- |
| `ACCEPT_DATA_ENTRY_WARNING_NON_BLOCKING_NO_LIVE` | Record no-live warning acceptance context; keep live admission separate. |
| `REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE` | Open a no-live workbook-correction packet before warning acceptance or live admission. |
| `HOLD_DATA_ENTRY_WARNING_NO_LIVE` | Keep the warning unresolved and continue no-live readiness only. |
| `PROVIDE_EXACT_LIVE_ADMISSION_LATER` | Defer disposition until a later exact live-admission packet. |

## Guardrails

PM Lane 250 does not add an approval button, import button, submit button, copy button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, live approval POST, approval row, project import, note, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS
