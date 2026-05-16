# PM Lane 094 - Local PM Operating Queue Disclosure Controls Handoff

## Purpose

PM Lane 094 reduces the `/pm-review/import-intake` scan burden by wrapping only the existing `Local PM Operating Queue` panel in a browser-native, default-open disclosure control.

This is local PM/AI-orchestration ergonomics only. It does not approve, persist, import, assign, schedule, change status, create issues, create tasks, create durable field records, write production tracking rows, claim hosted parity, or mutate production state.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `c09b0e6cdf278c832e09c51ff016ad6538029e50`
- Prior lane: PM Lane 093, Local PM Intake Snapshot Disclosure Controls

## Implemented Scope

- Converted only `#pm-operating-queue` / `Local PM Operating Queue` from a plain card section to a default-open native `<details>` disclosure.
- Preserved the `pm-operating-queue` id, `Local PM operating queue` aria label, and placement inside `Review Snapshot Detail` after the snapshot.
- Preserved the six derived queue items, item order, status pills, dynamic count text, export references, no-storage behavior, read seams, and no-authority wording.
- Added focused smoke coverage for default-open state, collapse/reopen behavior, hidden/visible queue items, unchanged item count, and no `collapse|disclosure|operating-queue` localStorage key.
- Updated the PM lane workflow docs, Temp Power orchestration plan, stakeholder acceleration lane, `PROJECT_STATUS.md`, and this packet/handoff.

## Files Changed

- `PROJECT_STATUS.md`
- `apps/operations-web/app/pm-review/import-intake/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-16-pm-lane-094-local-pm-operating-queue-disclosure-controls.json`
- `ops/agents/handoffs/2026-05-16-pm-lane-094-local-pm-operating-queue-disclosure-controls-handoff.md`

## Not Allowed

- No backend endpoint change.
- No new route or route target change.
- No quick-jump, route-link, output action, output status, output selector, workflow-map, open-items, snapshot, import exception register, project packet, or workflow gates behavior change.
- No operating queue item label, order, count, status pill, dynamic count behavior, export reference, export filename, or export content change.
- No helper panel relocation or detail group relocation.
- No new localStorage key and no persisted collapse state.
- No new export action, export artifact, export contract widening, read seam, mutation seam, hosted parity claim, SQL, schema migration, Supabase write, approval persistence, import mutation, live service call, Render redeploy, Vercel promotion, service creation, DNS/auth/ingress/secret change, fixture replay, workbook macro execution, workbook writeback, work authorization, field release, issue creation, task creation, live work order creation, durable field record, production tracking write, assignment mutation, schedule mutation, status mutation, or autonomous AI business-state mutation.

## Sidecar Result

A read-only sidecar scout ran in parallel and made no edits, staged nothing, committed nothing, and did not touch Supabase, Render, Vercel, or Olares.

Recommended next lane:

`Project Miner Local Import Exception Decision Register Disclosure Controls`

The recommended PM Lane 095 scope is to wrap only `#import-exception-register` / `Local Import Exception Decision Register` in the same default-open disclosure pattern while preserving id, aria label, placement, six register items, item order, status pills, summary counts, dynamic behavior, export behavior, no-storage behavior, and no-authority wording.

## Validation Commands

Run from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
corepack pnpm --filter @apex/operations-web build
rg -n "selected recipient|handoff created|assigned|scheduled|ready for execution|ready for field|field ready|field log of record|hosted parity proven|approval ready|packet admitted|daily report|tracking system|percent complete|released|cleared|approved|accepted|authorized|go/no-go passed|dispatch|dispatched|customer confirmed|JHA complete|LOTO approved|material released|issue created|task created|work order|production-ready" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-094-local-pm-operating-queue-disclosure-controls.json', encoding='utf-8')); print('packet-json-ok')"
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

- Stage only the Lane 094 files listed above.
- Commit with message `Add PM operating queue disclosure controls`.
- Push `clean-main`.
- Restore Olares host parity with `git pull --ff-only`.
- Verify local and host heads match and `bash tools/ai/run-minimal-mcp-trio.sh status` returns `{"status":"not-running"}`.
