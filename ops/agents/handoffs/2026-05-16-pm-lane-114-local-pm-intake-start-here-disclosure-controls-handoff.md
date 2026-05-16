# PM Lane 114 - Local PM Intake Start Here Disclosure Controls Handoff

## Purpose

PM Lane 114 reduces the `/pm-review/import-intake` scan burden by wrapping only the existing `Local PM intake start here` panel in a browser-native, default-open disclosure control.

This is local PM orientation and AI-orchestration ergonomics only. It does not accept, approve, persist, deploy, import, assign, schedule, change status, create issues, create tasks, create durable field records, write production tracking rows, claim hosted parity, or mutate production state.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `8ce517e71f031504d2a66eac9a1de65a54d7ac8a`
- Prior lane: PM Lane 113, Local PM Intake Daily Review Script Disclosure Controls

## Implemented Scope

- Converted only `Local PM intake start here` from a plain panel to a default-open native `<details>` disclosure.
- Preserved the `#pm-start-here` anchor, aria label, heading, browser-local pill, and placement under `Daily Action Panels` after `#pm-daily-review-script`.
- Preserved the explanatory no-authority wording, five derived start-here cards, card order, hrefs, dynamic text, status pills, quick-jump target, read seams, and no-storage behavior.
- Added focused smoke coverage for default-open state, collapse/reopen behavior, hidden/visible start-here controls, five start-here cards, no `collapse|disclosure|start-here` localStorage key, unchanged hrefs, and unchanged before/after dynamic start-here assertions.
- Updated the PM lane workflow docs, Temp Power orchestration plan, stakeholder acceleration lane, `PROJECT_STATUS.md`, and this packet/handoff.

## Files Changed

- `PROJECT_STATUS.md`
- `apps/operations-web/app/pm-review/import-intake/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-16-pm-lane-114-local-pm-intake-start-here-disclosure-controls.json`
- `ops/agents/handoffs/2026-05-16-pm-lane-114-local-pm-intake-start-here-disclosure-controls-handoff.md`

## Not Allowed

- No backend endpoint change.
- No new route or route target change.
- No quick-jump, route-link, output action, output status, output selector, project packet, source freshness, import exception register, workflow gates, exception review detail, admission and approval contract, local review checklist, local approval decision draft, local executor closeout intake, local field readiness checklist, local field questions draft, field prep queue, field prep coverage snapshot, field prep conversation agenda, field observation scratchpad, approval-readiness, guardrails, command-center, meeting-readout, constraint radar, daily-review-script, snapshot, operating queue, workflow-map, or open-items behavior change.
- No start-here anchor, card label, card detail, card href, card count, status pill, dynamic text, or export inclusion change.
- No helper panel relocation or detail group relocation.
- No new localStorage key and no persisted collapse state.
- No new export action, export artifact, export contract widening, read seam, mutation seam, hosted parity claim, SQL, schema migration, Supabase write, approval persistence, import mutation, live service call, Render redeploy, Vercel promotion, service creation, DNS/auth/ingress/secret change, fixture replay, workbook macro execution, workbook writeback, work authorization, field release, issue creation, task creation, live work order creation, durable field record, production tracking write, assignment mutation, schedule mutation, status mutation, or autonomous AI business-state mutation.

## Sidecar Result

A read-only PM Lane 115 sidecar scout ran in parallel and made no edits, staged nothing, committed nothing, ran no macros, created no artifacts, and did not touch Supabase, Render, Vercel, Olares, live services, source-domain files, project source files, or workbook files.

Recommended next lane:

`Project Miner Local PM Intake Output Selector Disclosure Controls`

The recommended PM Lane 115 scope is to wrap only the existing `Local PM Intake Output Selector` panel in the same default-open disclosure pattern while preserving the `#pm-output-selector` anchor, aria label, placement after `#pm-start-here` and before `#pm-handoff-guide`, heading, browser-local pill, existing copy, five output-selector cards, hrefs, order, dynamic text, status pills, no persisted collapse state, and read seams.

## Validation Commands

Run from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
corepack pnpm --filter @apex/operations-web build
rg -n "selected recipient|handoff created|assigned|scheduled|ready for execution|ready for field|field ready|field log of record|hosted parity proven|approval ready|packet admitted|daily report|tracking system|percent complete|released|cleared|approved|accepted|authorized|go/no-go passed|dispatch|dispatched|customer confirmed|JHA complete|LOTO approved|material released|issue created|task created|work order|production-ready" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-114-local-pm-intake-start-here-disclosure-controls.json', encoding='utf-8')); print('packet-json-ok')"
git diff --check
git diff --cached --check
```

## Validation Results

- `corepack pnpm --filter @apex/operations-web typecheck` passed.
- `corepack pnpm --filter @apex/operations-web build` passed and included `/pm-review/import-intake` in the static route output.
- Authority wording scan returned no matches for affirmative execution/admission/field-readiness/production-ready wording.
- `corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts` passed with 1 test.
- `corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts` passed with 4 tests.
- Packet JSON parse returned `packet-json-ok`.
- `git diff --check` passed with line-ending warnings only.
- `git diff --cached --check` passed after staging only the Lane 114 files.

## Closeout Requirements

- Stage only the Lane 114 files listed above.
- Commit with message `Add PM start here disclosure controls`.
- Push `clean-main`.
- Restore Olares host parity with `git pull --ff-only`.
- Verify local and host heads match and `bash tools/ai/run-minimal-mcp-trio.sh status` returns `{"status":"not-running"}`.
