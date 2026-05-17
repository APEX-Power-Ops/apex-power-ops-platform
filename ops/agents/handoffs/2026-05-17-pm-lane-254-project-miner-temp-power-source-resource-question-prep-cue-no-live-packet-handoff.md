# PM Lane 254 - Source Resource Question Prep Cue No-Live Handoff

Date: 2026-05-17

Decision label:

`PROJECT_MINER_TEMP_POWER_SOURCE_RESOURCE_QUESTION_PREP_CUE_NO_LIVE`

Selected outcome:

`SOURCE_RESOURCE_QUESTION_PREP_VISIBLE_NO_LIVE`

## Instruction

Add a no-live source/resource question preparation cue for Project Miner Temp Power while the Project Data Entry warning gate remains parked.

The active unresolved warning remains `PROJECT_DATA_ENTRY_FORMULA_ERRORS`. This lane must not choose a PM Lane 238 label, accept the warning, run workbook correction, assign resources, change schedule/status, or open any live approval/import path.

## Scope

1. Add a static `article` cue inside `Local Field Questions Draft`.
2. Preserve the existing six field-question draft inputs and their browser-local storage behavior.
3. Add matching cue text to local exports that already carry field-question context.
4. Keep Desktop Codex review-only for clarity, relay-burden, and boundary-risk scouting.
5. Preserve all live approval/import/field/customer/production/finance blockers.

## Sidecar Recommendation Adopted

Read-only sidecar review recommended placing the cue under the existing Source and Site Questions group as an `article`, not a new input. It also recommended asserting that no new state key is created and that the six existing labels remain six.

## Guardrails

No approval button, import button, submit button, copy button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, browser live route authority, live approval POST, approval row, project import, note, task, owner/due-date assignment, field authorization, lead/crew assignment, schedule/status write, customer commitment, field instruction, durable field record, production tracking, customer reporting, billing, payroll, invoice, accounting, external finance-system output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation is admitted.
