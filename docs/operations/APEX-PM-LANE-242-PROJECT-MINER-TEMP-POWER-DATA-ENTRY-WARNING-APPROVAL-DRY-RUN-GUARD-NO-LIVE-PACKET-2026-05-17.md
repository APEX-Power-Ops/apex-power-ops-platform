# PM Lane 242 - Project Miner Temp Power Data Entry Warning Approval Dry-Run Guard No-Live Packet

Date: 2026-05-17

Authority: VS Code Codex technical authority for the PM lane

Decision label:

`PROJECT_MINER_TEMP_POWER_DATA_ENTRY_WARNING_APPROVAL_DRY_RUN_GUARD_NO_LIVE`

## Purpose

PM Lane 242 closes a no-live review ambiguity in the local approval dry-run path.

Before this packet, a locally checked exception-review box could cause the dry-run envelope to list `PROJECT_DATA_ENTRY_FORMULA_ERRORS` under `accepted_warning_codes`. That was too permissive because the Project Data Entry warning still needs one exact PM label from the Lane 238 decision set.

This packet keeps local review evidence useful while making the distinction explicit:

1. reviewed is not accepted,
2. the Data Entry warning remains unresolved,
3. approval dry-run readiness reflects the unresolved warning disposition,
4. live-gate preflight includes a warning-disposition gate,
5. no live authority is opened.

## Selected Outcome

`DATA_ENTRY_WARNING_REVIEWED_NOT_ACCEPTED_IN_APPROVAL_DRY_RUN_NO_LIVE`

## What Changed

1. Added a Project Data Entry warning-disposition gate helper.
2. Removed `PROJECT_DATA_ENTRY_FORMULA_ERRORS` from local dry-run `accepted_warning_codes` while no exact PM label is present.
3. Added `unresolved_warning_codes` and `warning_disposition_gate` to the dry-run envelope.
4. Changed dry-run readiness from `4 ready, 1 needs review, 1 blocked` to `3 ready, 2 needs review, 1 blocked`.
5. Added a `warning-disposition-gate` item to live-gate preflight, changing preflight summary to `3 ready, 2 needs review, 2 blocked`.
6. Added focused smoke coverage for the guarded warning acceptance behavior.

## Guardrails

PM Lane 242 does not add an approval button, import button, submit button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, live approval POST, approval row, project import, note, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS
