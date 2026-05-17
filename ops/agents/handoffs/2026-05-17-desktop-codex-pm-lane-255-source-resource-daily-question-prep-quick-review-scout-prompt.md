# Desktop Codex PM Lane 255 Source Resource Daily Question Prep Quick Review Scout Prompt

Date: 2026-05-17

## Mission

Perform a read-only review of PM Lane 255 after VS Code Codex publishes the no-live Daily Action Panels source/resource question-prep quick review cue.

## Review Target

Primary product surface:

`apps/operations-web/app/pm-review/import-intake/page.tsx`

Primary smoke surface:

`apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`

Expected cue:

`section#pm-field-start-source-resource-question-prep-cue`

Expected aria label:

`Local field-start source and resource question prep cue`

## Questions To Answer

1. Does the cue reduce PM/lead review burden by surfacing source/resource question prep before stop-line review?
2. Does the cue avoid implied authority for resource assignment, schedule/status changes, procurement/rental commitments, customer commitments, warning acceptance, approval rows, or project import?
3. Do the tests assert visibility, count context, no links, no buttons, and no cue-related localStorage?
4. Does the cue preserve the open `PROJECT_DATA_ENTRY_FORMULA_ERRORS` decision gate?
5. Should the next PM lane continue no-live, or should VS Code Codex wait for exactly one PM Lane 238 Data Entry label?

## Guardrails

Read only. Do not edit product code, tests, docs, packet files, or handoffs. Do not open hosted services. Do not read source workbook contents. Do not read source PDF contents. Do not run workbook macros. Do not stage, commit, or push. Do not choose or infer a PM Lane 238 Data Entry label. Do not assign resources, change schedule/status, make procurement/rental commitments, create customer commitments, approve rows, import project rows, or mutate business state.
