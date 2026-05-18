# PM Lane 267 - Live Admission Hosted Candidate Mismatch Hold Handoff

Date: 2026-05-17

## Packet

`docs/operations/APEX-PM-LANE-267-PROJECT-MINER-TEMP-POWER-LIVE-ADMISSION-HOSTED-CANDIDATE-MISMATCH-HOLD-2026-05-17.md`

## Trigger

Jason supplied the exact PM Lane 142 live-admission phrase as a current instruction.

## Objective

Perform read-only hosted readiness proof before any write, and stop if hosted mutation-seam is not serving the current Project Miner Temp Power candidate.

## Required Work

1. Confirm the exact live-admission phrase is present.
2. Run read-only hosted route and PM intake smokes.
3. Read hosted candidate, approval contract, and approval status.
4. Compare hosted candidate identity and shape against the current Temp Power candidate.
5. Stop without POST if the hosted candidate is not `pm-import-candidate-miner-temp-power`.
6. Record the next safe packet as hosted candidate source hydration/freshness repair.

## Out Of Scope

Do not send an approval POST, create an approval row, import project rows, update Render env vars, deploy Render or Vercel, run SQL, mutate Supabase, upload source files, commit source workbooks or source PDFs, read source workbook/PDF contents, run macros, assign resources, mutate schedule/status, create customer commitments, or grant Desktop Codex PM decision authority.

## Validation

Run focused validation:

1. hosted read-only candidate/contract/status preflight,
2. hosted operations-web smoke,
3. paired PM intake hosted smoke,
4. deployed mutation-seam smoke with PM intake,
5. packet JSON parse,
6. text search for PM Lane 267 and stop condition,
7. guardrail keyword scan,
8. corrupted-token scan,
9. `git diff --check`.
