# PM Lane 254 - Source Resource Question Prep Cue No-Live Closeout

Date: 2026-05-17

Decision label:

`PROJECT_MINER_TEMP_POWER_SOURCE_RESOURCE_QUESTION_PREP_CUE_NO_LIVE`

Selected outcome:

`SOURCE_RESOURCE_QUESTION_PREP_VISIBLE_NO_LIVE`

## Result

PM Lane 254 is complete as a no-live source/resource question preparation cue packet.

The `Local Field Questions Draft` panel now includes a display-only `No-live source and resource question preparation cue`. It preserves the six existing field-question inputs, creates no new storage key, and gives PM/lead review a bounded way to shape source lineage, crew/tooling/lift/rental/equipment logistics, technician capability coverage, material/staging, and customer/site constraint questions while the `PROJECT_DATA_ENTRY_FORMULA_ERRORS` warning gate waits for exactly one PM Lane 238 Data Entry label.

The PM intake brief, field kickoff brief, field prep packet, and local import exception register exports now carry matching source/resource question-prep context.

## Sidecar Review

Read-only sidecar review recommended placing the cue as a static `article`, not a new input, inside the existing Local Field Questions Draft panel. That recommendation was adopted, including smoke assertions that the existing field-question input count remains six and no cue-related storage key is created.

## Validation

Result: PASS.

Proof:

1. `corepack pnpm --filter @apex/operations-web typecheck`
2. `corepack pnpm --filter @apex/operations-web build`
3. `corepack pnpm exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts`
4. Packet JSON parse
5. Source/resource cue text search
6. Pending-marker scan
7. Corrupted-token scan
8. `git diff --check`

## Next

The active Project Data Entry warning still needs exactly one PM Lane 238 label:

1. `ACCEPT_DATA_ENTRY_WARNING_NON_BLOCKING_NO_LIVE`
2. `REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE`
3. `HOLD_DATA_ENTRY_WARNING_NO_LIVE`
4. `PROVIDE_EXACT_LIVE_ADMISSION_LATER`

Safe no-live PM development can continue on candidate/readiness review, packet drafting, Desktop Codex read-only scout review, and source/resource question preparation while that gate remains open.

## Guardrails Preserved

No approval button, import button, submit button, copy button, persistence route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, hosted smoke, browser live route authority, live approval POST, approval row, project import, note, task, owner/due-date assignment, field authorization, lead/crew assignment, schedule/status write, customer commitment, field instruction, durable field record, production tracking, customer reporting, billing, payroll, invoice, accounting, external finance-system output, Supabase/Render/Vercel/Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook macro/writeback, workbook/PDF content read by Desktop Codex, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation was added.
