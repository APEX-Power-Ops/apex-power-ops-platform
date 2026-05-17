# PM Lane 142 Copy/Paste Prompt - Browser Approval Submission First-Row Executor

You are executing a bounded future gate for Apex Power Ops PM Lane 142.

## Repository

```text
C:\APEX Platform\apex-power-ops-platform
```

## Minimum Source Floor

```text
clean-main 04cdba43e3d062fd8a9bbb37007d210f75f52f33
```

If `origin/clean-main` is newer, fast-forward and use the newer head unless a coordinator closeout says otherwise.

## Required Admission Before Live Write

You may not send a live approval POST or create the first hosted approval row unless the prompt from Jason or the coordinator includes this exact phrase:

```text
I explicitly admit PM Lane 142 live approval POST and first approval-row creation for the current Project Miner Temp Power import candidate.
```

If that exact phrase is absent, stop after local mocked validation. Do not deploy hosted UI, do not send a live POST, and do not create an approval row.

## Authoritative Inputs

Read first:

```text
C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-16-pm-lane-141-browser-approval-submission-packet-design.json
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-16-pm-lane-141-browser-approval-submission-packet-design-handoff.md
C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-16-pm-lane-142-browser-approval-submission-first-row-execution-gate-dispatch.json
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-16-pm-lane-142-browser-approval-submission-first-row-execution-gate-dispatch-handoff.md
```

## Objective

Prepare or execute the first browser approval submission for the current Project Miner Temp Power import candidate, depending on whether explicit live-write admission is present.

The approved live write, when admitted, is only:

```text
POST /api/v1/mutations/project-import-approvals
```

Target table:

```text
seam.pm_import_candidate_approvals
```

This is approval-record persistence only. It is not project import.

## Local Preflight

Run from `C:\APEX Platform\apex-power-ops-platform`:

```powershell
git fetch origin
git checkout clean-main
git pull --ff-only origin clean-main
git status --short
Get-Content -Path "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-141-browser-approval-submission-packet-design.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
Get-Content -Path "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-142-browser-approval-submission-first-row-execution-gate-dispatch.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
```

Stop if the repo is not clean except coordinator-approved unrelated residue.

## Local Implementation Scope If UI Is Missing

Allowed files:

```text
C:\APEX Platform\apex-power-ops-platform\apps\operations-web\app\pm-review\import-intake\page.tsx
C:\APEX Platform\apex-power-ops-platform\apps\operations-web\tests\browser-shell.pm-import-intake.smoke.spec.ts
```

Allowed behavior:

1. Add a browser approval submission control only for the current approval-persistence contract.
2. Require local decision draft, review notes, local-only attestation, checklist evidence, hosted schema gate, and hosted route gate before enabling the control.
3. Show confirmation copy that the approval record does not import projects, workpackages, tasks, apparatus, assignments, schedules, statuses, field records, work orders, or production tracking.
4. Build the envelope from PM Lane 141:
   - `mutation_class: C`
   - `action_type: persist_import_approval`
   - `source: online`
   - envelope `idempotency_key` equals payload `idempotency_key`
   - payload contains the required candidate identity, fingerprints, decision, warning acceptance, no-go acknowledgement, and review notes.
5. Keep project import controls absent.

Local validation must mock the mutation route. The local smoke must fail on unmocked `/api/v1/mutations/**` calls.

Run:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
git diff --check
```

## Hosted Promotion If UI Changed

Only if explicit live-write admission is present and local validation is green:

- Promote only the existing operations-web Vercel project.
- Use only `https://operations.apexpowerops.com`.
- Do not create a new Vercel project.
- Do not create or change Render services.
- Do not change DNS, auth, ingress, or secrets.

Required hosted validation:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web smoke:hosted -- --base-url https://operations.apexpowerops.com
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

## Live First Approval Row Only If Explicitly Admitted

Before live POST:

1. Confirm the exact admission phrase is present.
2. Confirm hosted smokes are green.
3. Confirm approval-status GET is available.
4. Confirm approval record count for the current candidate is `0`.
5. Confirm no project import controls are present.

Live write rules:

1. Use the browser approval submission path, not direct SQL.
2. Send exactly one live POST for the current candidate.
3. Verify response:
   - `status: accepted`
   - `entity_type: pm_import_candidate_approval`
   - `action_type: persist_import_approval`
   - `new_state.import_authority: not_admitted`
4. Submit the exact same payload once as an idempotent replay.
5. Verify replay does not create a second approval row.
6. Verify approval-status readback matches the submitted decision.
7. Verify project, workpackage, task, apparatus, assignment, schedule, status, durable field record, and production tracking counts are unchanged.

## Hard Prohibitions

Do not:

1. send a live approval POST without the exact explicit admission phrase,
2. create more than one approval row,
3. import project rows,
4. create workpackages, tasks, apparatus, issues, assignments, schedules, statuses, field records, work orders, or production tracking rows,
5. run direct Supabase SQL for the approval row,
6. print, store, rotate, or commit secrets,
7. create new hosted services,
8. widen DNS, auth, ingress, or service boundaries,
9. run workbook macros or write workbooks,
10. admit autonomous AI business-state mutation.

## Closeout Required

Create a closeout handoff under:

```text
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\
```

Include:

1. source commit,
2. changed files,
3. whether explicit live-write admission was present,
4. exact local validation commands/results,
5. hosted deployment evidence if any,
6. hosted validation commands/results if any,
7. pre-submit approval record count if live write was admitted,
8. live POST response summary if live write was admitted,
9. idempotent replay summary if live write was admitted,
10. approval-status readback if live write was admitted,
11. unchanged downstream count proof if live write was admitted,
12. explicit guardrail confirmation,
13. blocker classification if anything failed.

Do not stage, commit, push, or alter unrelated files unless explicitly instructed by the coordinator.
