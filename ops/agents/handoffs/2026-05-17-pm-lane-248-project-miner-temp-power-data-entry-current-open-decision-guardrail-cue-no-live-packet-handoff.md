# PM Lane 248 - Data Entry Current Open Decision Guardrail Cue No-Live Handoff

Date: 2026-05-17

Decision label:

`PROJECT_MINER_TEMP_POWER_DATA_ENTRY_CURRENT_OPEN_DECISION_GUARDRAIL_CUE_NO_LIVE`

Selected outcome:

`DATA_ENTRY_OPEN_DECISION_VISIBLE_IN_CURRENT_GUARDRAILS_NO_LIVE`

## Instruction

Keep the Project Data Entry warning no-live and surface the current open decision in the main guardrail panel.

The current unresolved warning is `PROJECT_DATA_ENTRY_FORMULA_ERRORS`. The gate remains open until Jason returns exactly one PM Lane 238 label.

## Scope

1. Add a display-only current-open-decision cue under Current PM Next Actions and Guardrails.
2. Point the reviewer back to the Project Data Entry exact reply options card.
3. State that explanation text, paraphrases, and `REQUEST_SOURCE_CORRECTION_NO_LIVE` do not belong in the reply.
4. Preserve all live approval/import blockers.

## Guardrails

No approval button, import button, submit button, copy button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, browser live route authority, live approval POST, approval row, project import, note, task, owner/due-date assignment, field authorization, lead/crew assignment, schedule/status write, customer commitment, field instruction, durable field record, production tracking, customer reporting, billing, payroll, invoice, accounting, external finance-system output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation is admitted.

## Validation

Result: PASS.
