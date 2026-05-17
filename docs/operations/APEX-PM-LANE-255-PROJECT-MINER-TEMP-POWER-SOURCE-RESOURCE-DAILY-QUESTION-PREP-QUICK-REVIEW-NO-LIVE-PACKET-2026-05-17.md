# PM Lane 255 - Project Miner Temp Power Source Resource Daily Question Prep Quick Review No-Live Packet

Date: 2026-05-17

Decision label:

`PROJECT_MINER_TEMP_POWER_SOURCE_RESOURCE_DAILY_QUESTION_PREP_QUICK_REVIEW_NO_LIVE`

Selected outcome:

`SOURCE_RESOURCE_DAILY_QUESTION_PREP_CUE_VISIBLE_NO_LIVE`

## Purpose

PM Lane 255 executes the next safe no-live continuation move from PM Lane 254: bring the source/resource question-prep cue into the morning Daily Action Panels field-start path.

The active warning remains `PROJECT_DATA_ENTRY_FORMULA_ERRORS`. This lane does not choose a PM Lane 238 label, accept the warning, run workbook correction, approve the candidate, import project rows, assign resources, change schedule/status, or open live authority.

## Product Scope

1. Add a display-only `Local Field-Start Source/Resource Question Prep Cue` section inside the existing Daily Action Panels stack.
2. Place the cue after `Local Field Start Operator Script` and before `Local Field Start Stop-Line Quick Review`.
3. Reuse existing source/resource question-prep cues and source/resource counts.
4. Add smoke coverage for visibility, text, no links, no buttons, and no cue-related storage key.
5. Preserve the PM Lane 254 field-question cue and the PM Lane 238 Data Entry decision gate.

## Cue Rules

Allowed no-live question preparation:

1. source lineage questions,
2. crew, tooling, lift, rental, equipment, and logistics questions,
3. technician capability coverage questions,
4. material, staging, and customer/site constraint questions.

Blocked until later admission:

1. resource assignment,
2. schedule or status changes,
3. procurement or rental commitments,
4. customer commitments,
5. warning acceptance,
6. approval rows,
7. project import.

## Guardrails

No approval button, import button, submit button, copy button, link, writable control, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, browser live route authority, live approval POST, approval row, project import, note, task, owner/due-date assignment, field authorization, lead/crew assignment, schedule/status write, procurement or rental commitment, customer commitment, field instruction, durable field record, production tracking, customer reporting, billing, payroll, invoice, accounting, external finance-system output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, workbook/PDF content read by Desktop Codex, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation is admitted.

## Validation Plan

1. Operations-web typecheck.
2. Operations-web build.
3. Focused PM import-intake Playwright smoke.
4. Packet JSON parse.
5. Daily source/resource cue text search.
6. Unresolved-marker scan.
7. Corrupted-token scan.
8. `git diff --check`.
