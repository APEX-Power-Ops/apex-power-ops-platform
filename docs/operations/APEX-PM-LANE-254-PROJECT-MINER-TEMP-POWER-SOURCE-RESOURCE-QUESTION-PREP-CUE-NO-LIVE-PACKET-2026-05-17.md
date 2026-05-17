# PM Lane 254 - Project Miner Temp Power Source Resource Question Prep Cue No-Live Packet

Date: 2026-05-17

Decision label:

`PROJECT_MINER_TEMP_POWER_SOURCE_RESOURCE_QUESTION_PREP_CUE_NO_LIVE`

Selected outcome:

`SOURCE_RESOURCE_QUESTION_PREP_VISIBLE_NO_LIVE`

## Purpose

PM Lane 254 executes the next safe continuation move from PM Lane 253: source/resource question preparation while the Project Data Entry warning gate remains parked.

The active warning remains `PROJECT_DATA_ENTRY_FORMULA_ERRORS`. This lane does not choose a PM Lane 238 label, accept the warning, run workbook correction, approve the candidate, import project rows, or open live authority.

## Product Scope

1. Add a display-only source/resource question preparation cue inside the existing `Local Field Questions Draft` panel.
2. Keep the existing six field-question draft inputs unchanged.
3. Carry matching cue text into local PM review exports that already include field-question context.
4. Preserve the safe-continuation boundary from PM Lane 253.
5. Keep Desktop Codex limited to read-only clarity, relay-burden, and boundary-risk review.

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

No approval button, import button, submit button, copy button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, browser live route authority, live approval POST, approval row, project import, note, task, owner/due-date assignment, field authorization, lead/crew assignment, schedule/status write, customer commitment, field instruction, durable field record, production tracking, customer reporting, billing, payroll, invoice, accounting, external finance-system output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, workbook/PDF content read by Desktop Codex, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation is admitted.

## Validation Plan

1. Operations-web typecheck.
2. Operations-web build.
3. Focused PM import-intake Playwright smoke.
4. Packet JSON parse.
5. Source/resource cue text search.
6. Pending-marker scan.
7. Corrupted-token scan.
8. `git diff --check`.
