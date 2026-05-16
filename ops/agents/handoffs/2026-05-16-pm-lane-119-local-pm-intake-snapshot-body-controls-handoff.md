# PM Lane 119 - Local PM Intake Snapshot Body Controls Handoff

## Purpose

PM Lane 119 reduces the `/pm-review/import-intake` scan burden by wrapping only the existing `Local PM intake snapshot` body content in a labeled body-controls container under its already-existing browser-native, default-open disclosure.

This is local PM snapshot scanning and AI-orchestration ergonomics only. It does not accept, approve, persist, deploy, import, assign, schedule, change status, create issues, create tasks, create durable field records, write production tracking rows, claim hosted parity, or mutate production state.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `25cb4896e81f83ca430cc868619e25bfa149087a`
- Prior lane: PM Lane 118, Local PM Intake Open Items Lens Body Controls

## Implemented Scope

- Added only a labeled `PM intake snapshot controls` body container under the existing `Local PM intake snapshot` disclosure summary.
- Preserved the `#pm-intake-snapshot` anchor, existing disclosure, aria label, heading, browser-local pill, and placement inside `Review Snapshot Detail` before `#pm-operating-queue`.
- Preserved the explanatory no-authority wording, snapshot summary count, six derived snapshot cards, card order, dynamic detail/evidence text, status pills, quick-jump target, read seams, export behavior, and no-storage behavior.
- Added focused smoke coverage for default-open state, visible body controls, collapse/reopen behavior, hidden/visible snapshot controls, six snapshot articles, no `collapse|disclosure|snapshot` localStorage key, unchanged summary text, and unchanged snapshot labels.
- Updated the PM lane workflow docs, Temp Power orchestration plan, stakeholder acceleration lane, `PROJECT_STATUS.md`, and this packet/handoff.

## Files Changed

- `PROJECT_STATUS.md`
- `apps/operations-web/app/pm-review/import-intake/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-16-pm-lane-119-local-pm-intake-snapshot-body-controls.json`
- `ops/agents/handoffs/2026-05-16-pm-lane-119-local-pm-intake-snapshot-body-controls-handoff.md`

## Not Allowed

- No backend endpoint change.
- No new route or route target change.
- No quick-jump, route-link, output action, output status, project packet, source freshness, import exception register, workflow gates, exception review detail, admission and approval contract, local review checklist, local approval decision draft, local executor closeout intake, local field readiness checklist, local field questions draft, field prep queue, field prep coverage snapshot, field prep conversation agenda, field observation scratchpad, approval-readiness, guardrails, command-center, meeting-readout, constraint radar, daily-review-script, start-here, output-selector, handoff-guide, workflow-map, open-items, or operating queue behavior change.
- No snapshot anchor, card label, card detail, card count, status pill, dynamic text, or export behavior change.
- No helper panel relocation or detail group relocation.
- No new localStorage key and no persisted collapse state.
- No new export action, export artifact, export contract widening, read seam, mutation seam, hosted parity claim, SQL, schema migration, Supabase write, approval persistence, import mutation, live service call, Render redeploy, Vercel promotion, service creation, DNS/auth/ingress/secret change, fixture replay, workbook macro execution, workbook writeback, work authorization, field release, issue creation, task creation, live work order creation, durable field record, production tracking write, assignment mutation, schedule mutation, status mutation, or autonomous AI business-state mutation.

## Sidecar Result

A read-only PM Lane 120 sidecar scout ran in parallel and made no edits, staged nothing, committed nothing, ran no macros, created no artifacts, and did not touch Supabase, Render, Vercel, Olares, live services, source-domain files, project source files, or workbook files.

Recommended next lane:

`Project Miner Local PM Operating Queue Body Controls`

The recommended PM Lane 120 scope is to add only a body wrapper under the existing `Local PM Operating Queue` disclosure summary, preserving the `#pm-operating-queue` anchor, aria label, heading, browser-local pill, existing copy, count summary, six queue items, order, status pills, no persisted collapse state, and read-only seams.

## Validation Commands

Run from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
corepack pnpm --filter @apex/operations-web build
rg -n "selected recipient|handoff created|assigned|scheduled|ready for execution|ready for field|field ready|field log of record|hosted parity proven|approval ready|packet admitted|daily report|tracking system|percent complete|released|cleared|approved|accepted|authorized|go/no-go passed|dispatch|dispatched|customer confirmed|JHA complete|LOTO approved|material released|issue created|task created|work order|production-ready" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-119-local-pm-intake-snapshot-body-controls.json', encoding='utf-8')); print('packet-json-ok')"
git diff --check
git diff --cached --check
```

## Validation Results

- `corepack pnpm --filter @apex/operations-web typecheck` passed.
- `corepack pnpm --filter @apex/operations-web build` passed and included `/pm-review/import-intake` in the static route output after a stale local Playwright test-server process was cleared; no code change was required for the retry.
- Authority wording scan returned no matches for affirmative execution/admission/field-readiness/production-ready wording.
- `corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts` passed with 1 test on rerun after one local timeout at an existing download-read assertion; no code change was required for the retry.
- `corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts` passed with 4 tests.
- Packet JSON parse returned `packet-json-ok`.
- `git diff --check` passed with line-ending warnings only.
- `git diff --cached --check` passed after staging only the Lane 119 files.

## Closeout Requirements

- Stage only the Lane 119 files listed above.
- Commit with message `Add PM snapshot body controls`.
- Push `clean-main`.
- Restore Olares host parity with `git pull --ff-only`.
- Verify local and host heads match and `bash tools/ai/run-minimal-mcp-trio.sh status` returns `{"status":"not-running"}`.
