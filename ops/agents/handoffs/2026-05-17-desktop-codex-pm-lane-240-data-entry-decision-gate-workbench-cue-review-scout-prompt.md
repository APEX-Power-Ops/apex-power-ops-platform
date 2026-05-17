# Desktop Codex PM Lane 240 Data Entry Decision Gate Workbench Cue Review Scout Prompt

Date: 2026-05-17

## Mission

Review the PM Lane 240 display-only workbench cue for clarity and authority-boundary risk.

## Read-Only Inputs

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
3. `docs/operations/APEX-PM-LANE-240-PROJECT-MINER-TEMP-POWER-DATA-ENTRY-DECISION-GATE-WORKBENCH-CUE-NO-LIVE-PACKET-2026-05-17.md`
4. `ops/agents/packets/draft/2026-05-17-pm-lane-240-project-miner-temp-power-data-entry-decision-gate-workbench-cue-no-live-packet.json`

## Questions To Answer

1. Does the cue reduce PM review burden without adding noise?
2. Are all four no-live labels visible and copyable?
3. Is any wording likely to be misread as approval/import authority?
4. Does the test coverage protect the intended cue?

## Guardrails

1. Do not edit files.
2. Do not stage, commit, or push.
3. Do not read source workbook or PDF contents.
4. Do not run macros.
5. Do not access Supabase, Render, Vercel, Olares, or hosted services.
6. Do not decide the PM response.
7. Do not admit live writes.
8. Do not mutate business state.

## Expected Return

Return a short closeout with clarity verdict, relay-burden verdict, authority-boundary risk if any, and recommended next PM lane only if no authority widening is required.
