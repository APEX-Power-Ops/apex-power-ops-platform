# PM Lane 208 Copy/Paste Prompt - Approval First-Row Executor Prompt Refresh

You are executing a bounded future gate for Apex Power Ops PM Lane 208.

This prompt refreshes the PM Lane 142 first approval-row executor instructions. It does not, by itself, admit the live write.

The closed PM Lane 142 executor prompt remains historical provenance. Use this Lane 208 prompt for future first-row execution unless VS Code Codex coordinator provides a newer prompt.

## Repository

```text
C:\APEX Platform\apex-power-ops-platform
```

## Minimum Source Floor

Use the current `origin/clean-main` head unless a coordinator closeout says otherwise.

From the repository root:

```powershell
git fetch origin
git checkout clean-main
git pull --ff-only origin clean-main
git status --short
```

Stop if the repo is not clean except coordinator-approved unrelated residue.

## Required Admission Before Live Write

You may not send a live approval POST or create the first hosted approval row unless Jason or VS Code Codex coordinator provides this exact phrase as a current instruction outside this guardrail section:

```text
I explicitly admit PM Lane 142 live approval POST and first approval-row creation for the current Project Miner Temp Power import candidate.
```

The phrase appearing in this prompt as quoted guardrail text does not count as admission.

If the exact phrase is absent as a current instruction, stop with:

```text
STOPPED_NO_LIVE_ADMISSION
```

When stopped for no live admission:

1. do not deploy,
2. do not call hosted services,
3. do not send a live approval POST,
4. do not create an approval row,
5. do not import a project,
6. do not mutate Supabase, Render, Vercel, Olares, workbook files, or business state,
7. create only a secret-free closeout explaining that the live gate was not admitted.

## Read First

Read these repo files before any implementation or validation decision:

```text
C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-16-pm-lane-141-browser-approval-submission-packet-design.json
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-16-pm-lane-141-browser-approval-submission-packet-design-handoff.md
C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-16-pm-lane-142-browser-approval-submission-first-row-execution-gate-dispatch.json
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-16-pm-lane-142-browser-approval-submission-first-row-execution-gate-dispatch-handoff.md
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-16-pm-lane-142-browser-approval-submission-first-row-executor-copy-paste-prompt.md
C:\APEX Platform\apex-power-ops-platform\docs\operations\APEX-PM-LANE-207-APPROVAL-FIRST-ROW-WRITE-PREP-ADMISSION-READINESS-2026-05-17.md
C:\APEX Platform\apex-power-ops-platform\docs\operations\APEX-PM-LANE-208-APPROVAL-FIRST-ROW-EXECUTOR-PROMPT-REFRESH-2026-05-17.md
C:\APEX Platform\apex-power-ops-platform\docs\operations\PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md
```

## Objective

Prepare for or execute the first browser approval submission for the current Project Miner Temp Power import candidate, depending only on whether the exact current live-write admission phrase is present.

The only admitted live mutation, if the gate phrase is explicitly present as current instruction, is:

```text
POST /api/v1/mutations/project-import-approvals
```

Target table:

```text
seam.pm_import_candidate_approvals
```

This is approval-record persistence only. It is not project import.

## If The Phrase Is Absent

Do only repo-local/read-only validation needed to produce a closeout.

Allowed:

1. inspect the repo files listed above,
2. confirm the exact phrase is absent as current instruction,
3. optionally parse packet JSON files,
4. optionally run `git diff --check`,
5. create one closeout handoff under `ops/agents/handoffs/`.

Not allowed:

1. no hosted smoke,
2. no browser live route access,
3. no Vercel promotion,
4. no Render restart or deploy,
5. no Supabase write or query that requires secrets,
6. no approval POST,
7. no approval-row creation,
8. no project import,
9. no product-code changes unless separately authorized by VS Code Codex.

Closeout status must be:

```text
STOPPED_NO_LIVE_ADMISSION
```

## If The Phrase Is Present

Proceed only if the exact phrase is provided as current instruction.

### Local Preflight

Run from `C:\APEX Platform\apex-power-ops-platform`:

```powershell
Get-Content -Path "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-141-browser-approval-submission-packet-design.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
Get-Content -Path "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-142-browser-approval-submission-first-row-execution-gate-dispatch.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
```

Confirm current candidate proof:

1. candidate identity,
2. source fingerprint,
3. shape fingerprint,
4. warning-code acceptance,
5. human no-go acknowledgement coverage,
6. explicit PM decision value,
7. nonempty PM review notes,
8. approval-status readback context,
9. live-gate preflight context.

### Local Browser Proof

Use the existing operations-web proof if no code change is needed. If product code must be changed, stay within coordinator-authorized files only.

Required local proof before any live write:

1. local mocked browser validation is green,
2. unmocked `/api/v1/mutations/**` calls fail the local smoke,
3. the approval envelope matches the PM Lane 141 contract,
4. project import controls remain absent.

Expected validation commands if UI code changed:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
git diff --check
```

### Hosted Proof

Hosted proof is allowed only if the exact phrase is present and local proof is green.

Use only existing services:

```text
https://operations.apexpowerops.com
https://mutation-seam.apexpowerops.com
```

Do not create new hosted services. Do not widen DNS, auth, ingress, or secrets.

Run current hosted smoke coverage:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web smoke:hosted -- --base-url https://operations.apexpowerops.com
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

### Live First Approval Row

Before live POST:

1. confirm the exact phrase is present as current instruction,
2. confirm hosted smokes are green,
3. confirm approval-status GET is available,
4. confirm pre-submit approval record count for the current candidate is `0`,
5. confirm no project import controls are present,
6. confirm secrets are not printed, copied into repo files, or included in closeout.

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

1. treat this prompt's quoted gate phrase as admission,
2. send a live approval POST without the exact explicit current admission phrase,
3. create more than one approval row,
4. import project rows,
5. create workpackages, tasks, apparatus, issues, assignments, schedules, statuses, field records, work orders, or production tracking rows,
6. run direct Supabase SQL for the approval row,
7. print, store, rotate, or commit secrets,
8. create new hosted services,
9. widen DNS, auth, ingress, or service boundaries,
10. run workbook macros or write workbooks,
11. admit autonomous AI business-state mutation.

## Closeout Required

Create one closeout handoff under:

```text
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\
```

Include:

1. source commit,
2. changed files,
3. whether explicit live-write admission was present as current instruction,
4. if stopped, the exact `STOPPED_NO_LIVE_ADMISSION` status,
5. local validation commands/results,
6. hosted deployment evidence if any,
7. hosted validation commands/results if any,
8. pre-submit approval record count if live write was admitted,
9. live POST response summary if live write was admitted,
10. idempotent replay summary if live write was admitted,
11. approval-status readback if live write was admitted,
12. unchanged downstream count proof if live write was admitted,
13. explicit guardrail confirmation,
14. blocker classification if anything failed,
15. confirmation that no secrets were printed or written to repo files.

Do not stage, commit, push, or alter unrelated files unless explicitly instructed by VS Code Codex coordinator.
