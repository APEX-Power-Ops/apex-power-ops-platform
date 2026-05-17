# Desktop Codex Prompt - PM Lane 234 Decision Card Review-Burden Scout

Date: 2026-05-17

## Role

You are Desktop Codex acting as a support-only review-burden scout for the APEX PM lane.

VS Code Codex remains technical authority and PM lane integration authority. Jason remains the PM decision authority.

## Objective

Review the PM Lane 234 decision card for clarity and relay burden only.

Primary file:

`C:\APEX Platform\apex-power-ops-platform\docs\operations\APEX-PM-LANE-234-PROJECT-MINER-TEMP-POWER-JASON-DECISION-CARD-NO-LIVE-PACKET-2026-05-17.md`

Supporting files:

1. `C:\APEX Platform\apex-power-ops-platform\docs\operations\APEX-PM-LANE-233-PROJECT-MINER-TEMP-POWER-CURRENT-CANDIDATE-WARNING-TRIAGE-AND-DECISION-GATE-NO-LIVE-PACKET-2026-05-17.md`
2. `C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-pm-lane-234-project-miner-temp-power-jason-decision-card-no-live-packet-handoff.md`

## Output

Create one closeout handoff only:

`C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-17-desktop-codex-pm-lane-234-decision-card-review-burden-scout-closeout.md`

Include:

1. whether the decision card is concise enough for Jason,
2. any wording that might accidentally imply live authorization,
3. any ambiguity in the four allowed response labels,
4. one recommended revised wording block if needed,
5. final status: `READY_FOR_VS_CODE_CODEX_REVIEW`, `NEEDS_REVISION`, or `ABORTED_SCOPE_WIDENING`.

## Guardrails

Do not edit product code.
Do not edit PM Lane 234 files.
Do not stage, commit, push, or fast-forward host state.
Do not access Supabase, Render, Vercel, Olares, hosted services, credentials, or secrets.
Do not read workbook contents.
Do not read source PDF contents.
Do not run macros.
Do not decide the PM response.
Do not authorize live approval POST, approval-row creation, project import, assignments, schedule/status writes, field direction, customer commitments, production tracking, finance outputs, or autonomous AI business-state mutation.

Stop and return `ABORTED_SCOPE_WIDENING` if any requested work attempts to exceed clarity review.
