# Desktop Codex PM Lane 244 Data Entry Source-Correction Boundary Review Scout Prompt

Date: 2026-05-17

## Assignment

Review the PM Lane 244 source-correction boundary cue for clarity and relay-burden reduction.

## Read Only Surfaces

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
3. `docs/operations/APEX-PM-LANE-244-PROJECT-MINER-TEMP-POWER-DATA-ENTRY-SOURCE-CORRECTION-BOUNDARY-CUE-NO-LIVE-PACKET-2026-05-17.md`
4. `ops/agents/packets/draft/2026-05-17-pm-lane-244-project-miner-temp-power-data-entry-source-correction-boundary-cue-no-live-packet.json`

## Questions

1. Does the cue clearly state that `REQUEST_SOURCE_CORRECTION_NO_LIVE` is already applied to `Ground Resistance Test Lot`?
2. Does the cue clearly separate that historical source correction from the active `PROJECT_DATA_ENTRY_FORMULA_ERRORS` warning?
3. Is `REQUEST_DATA_ENTRY_WORKBOOK_CORRECTION_NO_LIVE` clear as the current workbook-correction label?
4. Is there any wording that could imply warning acceptance, live approval, import authority, source writeback, hosted access, or Desktop Codex PM decision authority?

## Guardrails

Do not edit files. Do not stage, commit, or push. Do not read workbook contents. Do not read source PDF contents. Do not run macros. Do not access Supabase, Render, Vercel, Olares, or hosted services. Do not approve the warning. Do not create or mutate business state. Return only a concise review note and any recommended wording changes.
