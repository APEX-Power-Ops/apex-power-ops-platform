# PM Lane 093 - Local PM Intake Snapshot Disclosure Controls Handoff

## Purpose

PM Lane 093 reduces the `/pm-review/import-intake` scan burden by wrapping only the existing `Local PM Intake Snapshot` panel in a browser-native, default-open disclosure control.

This is local PM/AI-orchestration ergonomics only. It does not approve, persist, import, assign, schedule, change status, create issues, create tasks, create durable field records, write production tracking rows, claim hosted parity, or mutate production state.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `68da699e69176b0741e23d9a78c9c37e39fe6de1`
- Prior lane: PM Lane 092, Local PM Intake Open Items Lens Disclosure Controls

## Implemented Scope

- Converted only `#pm-intake-snapshot` / `Local PM Intake Snapshot` from a plain card section to a default-open native `<details>` disclosure.
- Preserved the `pm-intake-snapshot` id, `Local PM intake snapshot` aria label, and placement inside `Review Snapshot Detail`.
- Preserved the six derived snapshot entries, count summary, labels, detail text, evidence text, status pills, dynamic behavior, export behavior, no-storage behavior, read seams, and no-authority wording.
- Added focused smoke coverage for default-open state, collapse/reopen behavior, hidden/visible snapshot items, unchanged item count, and no `collapse|disclosure|snapshot` localStorage key.
- Updated the PM lane workflow docs, Temp Power orchestration plan, stakeholder acceleration lane, `PROJECT_STATUS.md`, and this packet/handoff.

## Files Changed

- `PROJECT_STATUS.md`
- `apps/operations-web/app/pm-review/import-intake/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-16-pm-lane-093-local-pm-intake-snapshot-disclosure-controls.json`
- `ops/agents/handoffs/2026-05-16-pm-lane-093-local-pm-intake-snapshot-disclosure-controls-handoff.md`

## Not Allowed

- No backend endpoint change.
- No new route or route target change.
- No quick-jump, route-link, output action, output status, output selector, workflow-map, open-items, or operating-queue behavior change.
- No snapshot entry label, detail text, evidence text, status pill, item count, dynamic behavior, export behavior, export filename, or export content change.
- No helper panel relocation or detail group relocation.
- No new localStorage key and no persisted collapse state.
- No new export action, export artifact, export contract widening, read seam, mutation seam, hosted parity claim, SQL, schema migration, Supabase write, approval persistence, import mutation, live service call, Render redeploy, Vercel promotion, service creation, DNS/auth/ingress/secret change, fixture replay, workbook macro execution, workbook writeback, work authorization, field release, issue creation, task creation, live work order creation, durable field record, production tracking write, assignment mutation, schedule mutation, status mutation, or autonomous AI business-state mutation.

## Sidecar Result

A read-only sidecar scout ran in parallel and made no edits, staged nothing, committed nothing, and did not touch Supabase, Render, Vercel, or Olares.

Recommended next lane:

`Project Miner Local PM Operating Queue Disclosure Controls`

The recommended PM Lane 094 scope is to wrap only `#pm-operating-queue` / `Local PM Operating Queue` in the same default-open disclosure pattern while preserving id, aria label, placement after the snapshot, six queue items, item order, status pills, dynamic count text, no-storage behavior, export references, and no-authority wording.

## Validation Commands

Run from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
corepack pnpm --filter @apex/operations-web build
rg -n "selected recipient|handoff created|assigned|scheduled|ready for execution|ready for field|field ready|field log of record|hosted parity proven|approval ready|packet admitted|daily report|tracking system|percent complete|released|cleared|approved|accepted|authorized|go/no-go passed|dispatch|dispatched|customer confirmed|JHA complete|LOTO approved|material released|issue created|task created|work order|production-ready" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-093-local-pm-intake-snapshot-disclosure-controls.json', encoding='utf-8')); print('packet-json-ok')"
git diff --check
git diff --cached --check
```

## Validation Results

- `corepack pnpm --filter @apex/operations-web typecheck` passed.
- `corepack pnpm --filter @apex/operations-web build` passed with `/pm-review/import-intake` in the route output.
- Authority wording scan returned no matches.
- Packet JSON parse returned `packet-json-ok`.
- `git diff --check` passed with line-ending warnings only.
- Focused import-intake Playwright smoke passed with `1 passed` after tightening the parent `Review Snapshot Detail` summary selector for nested disclosure markup.
- Focused PM intake Playwright smoke suite passed with `4 passed`.
- `git diff --cached --check` passed.

## Closeout Requirements

- Stage only the Lane 093 files listed above.
- Commit with message `Add PM intake snapshot disclosure controls`.
- Push `clean-main`.
- Restore Olares host parity with `git pull --ff-only`.
- Verify local and host heads match and `bash tools/ai/run-minimal-mcp-trio.sh status` returns `{"status":"not-running"}`.
