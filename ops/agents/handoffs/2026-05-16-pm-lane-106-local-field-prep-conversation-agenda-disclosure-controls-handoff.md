# PM Lane 106 - Local Field Prep Conversation Agenda Disclosure Controls Handoff

## Purpose

PM Lane 106 reduces the `/pm-review/import-intake` scan burden by wrapping only the existing `Local field prep conversation agenda` panel in a browser-native, default-open disclosure control.

This is local PM/AI-orchestration ergonomics only. It does not accept, approve, persist, deploy, import, assign, schedule, change status, create issues, create tasks, create durable field records, write production tracking rows, claim hosted parity, or mutate production state.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `3745c134730fc145b3508c8d7c6eac092f3758c3`
- Prior lane: PM Lane 105, Local Field Prep Coverage Snapshot Disclosure Controls

## Implemented Scope

- Converted only `Local field prep conversation agenda` from a plain panel to a default-open native `<details>` disclosure.
- Preserved the `Local field prep conversation agenda` aria label, heading, derived pill, and placement inside `Field Prep Detail`.
- Preserved the seven agenda items, item order, summary text, status pills, dynamic derived behavior, export inclusion, no-storage behavior, read seams, and no-authority wording.
- Added focused smoke coverage for default-open state, collapse/reopen behavior, hidden/visible agenda controls, seven agenda-control cards, no `collapse|disclosure|field-prep-agenda` localStorage key before agenda export use, and unchanged initial/later agenda counts.
- Updated the PM lane workflow docs, Temp Power orchestration plan, stakeholder acceleration lane, `PROJECT_STATUS.md`, and this packet/handoff.

## Files Changed

- `PROJECT_STATUS.md`
- `apps/operations-web/app/pm-review/import-intake/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-16-pm-lane-106-local-field-prep-conversation-agenda-disclosure-controls.json`
- `ops/agents/handoffs/2026-05-16-pm-lane-106-local-field-prep-conversation-agenda-disclosure-controls-handoff.md`

## Not Allowed

- No backend endpoint change.
- No new route or route target change.
- No quick-jump, route-link, output action, output status, output selector, project packet, source freshness, import exception register, workflow gates, exception review detail, admission and approval contract, local review checklist, local approval decision draft, local executor closeout intake, local field readiness checklist, local field questions draft, field prep queue, field prep coverage snapshot, field observation scratchpad, snapshot, operating queue, workflow-map, or open-items behavior change.
- No field prep agenda item label, detail, count, status pill, dynamic derived-state behavior, or export inclusion change.
- No helper panel relocation or detail group relocation.
- No new localStorage key and no persisted collapse state.
- No new export action, export artifact, export contract widening, read seam, mutation seam, hosted parity claim, SQL, schema migration, Supabase write, approval persistence, import mutation, live service call, Render redeploy, Vercel promotion, service creation, DNS/auth/ingress/secret change, fixture replay, workbook macro execution, workbook writeback, work authorization, field release, issue creation, task creation, live work order creation, durable field record, production tracking write, assignment mutation, schedule mutation, status mutation, or autonomous AI business-state mutation.

## Sidecar Result

A read-only PM Lane 107 sidecar scout ran in parallel and made no edits, staged nothing, committed nothing, ran no validation, and did not touch Supabase, Render, Vercel, Olares, live services, macros, source-domain files, project source files, or workbook files.

Recommended next lane:

`Project Miner Local Field Observation Scratchpad Disclosure Controls`

The recommended PM Lane 107 scope is to wrap only the existing `Local field observation scratchpad` panel in the same default-open disclosure pattern while preserving aria label, heading, browser-local pill, placement after the Lane 106 agenda, six textarea fields, placeholders, candidate-scoped storage key, clear button behavior, derived field-observations behavior, export inclusion, no persisted collapse state, and read seams.

## Validation Commands

Run from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
corepack pnpm --filter @apex/operations-web build
rg -n "selected recipient|handoff created|assigned|scheduled|ready for execution|ready for field|field ready|field log of record|hosted parity proven|approval ready|packet admitted|daily report|tracking system|percent complete|released|cleared|approved|accepted|authorized|go/no-go passed|dispatch|dispatched|customer confirmed|JHA complete|LOTO approved|material released|issue created|task created|work order|production-ready" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-106-local-field-prep-conversation-agenda-disclosure-controls.json', encoding='utf-8')); print('packet-json-ok')"
git diff --check
git diff --cached --check
```

## Validation Results

- `corepack pnpm --filter @apex/operations-web typecheck` passed.
- `corepack pnpm --filter @apex/operations-web build` passed with `/pm-review/import-intake` in the route output.
- Authority wording scan returned no matches.
- Packet JSON parse returned `packet-json-ok`.
- `git diff --check` passed with line-ending warnings only.
- Focused import-intake Playwright smoke passed with `1 passed`.
- Focused PM intake Playwright smoke suite passed with `4 passed`.
- `git diff --cached --check` passed.

## Closeout Requirements

- Stage only the Lane 106 files listed above.
- Commit with message `Add PM field prep agenda disclosure controls`.
- Push `clean-main`.
- Restore Olares host parity with `git pull --ff-only`.
- Verify local and host heads match and `bash tools/ai/run-minimal-mcp-trio.sh status` returns `{"status":"not-running"}`.
