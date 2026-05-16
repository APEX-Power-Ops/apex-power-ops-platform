# PM Lane 097 - Exception Review and PM Decision Detail Disclosure Controls Handoff

## Purpose

PM Lane 097 reduces the `/pm-review/import-intake` scan burden by wrapping only the existing `Exception review and PM decision detail` panel in a browser-native, default-open disclosure control.

This is local PM/AI-orchestration ergonomics only. It does not approve, persist, import, assign, schedule, change status, create issues, create tasks, create durable field records, write production tracking rows, claim hosted parity, or mutate production state.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `dc4711223b118eb2185bdf867ca0e8a8250d71c7`
- Prior lane: PM Lane 096, Workflow Gates Disclosure Controls

## Implemented Scope

- Converted only `Exception review and PM decision detail` from a plain panel to a default-open native `<details>` disclosure.
- Preserved the `Exception review and PM decision detail` aria label and placement inside `Source and Exception Detail` after Workflow Gates.
- Preserved the warning card, PM decision card, warning severity/code pills, decision prompt/recommended action text, fallback empty states, export behavior, no-storage behavior, read seams, and no-authority wording.
- Added focused smoke coverage for default-open state, collapse/reopen behavior, hidden/visible exception and decision child cards, fixture warning/decision content while open, and no `collapse|disclosure|exception-review|pm-decision` localStorage key.
- Updated the PM lane workflow docs, Temp Power orchestration plan, stakeholder acceleration lane, `PROJECT_STATUS.md`, and this packet/handoff.

## Files Changed

- `PROJECT_STATUS.md`
- `apps/operations-web/app/pm-review/import-intake/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-16-pm-lane-097-exception-review-pm-decision-detail-disclosure-controls.json`
- `ops/agents/handoffs/2026-05-16-pm-lane-097-exception-review-pm-decision-detail-disclosure-controls-handoff.md`

## Not Allowed

- No backend endpoint change.
- No new route or route target change.
- No quick-jump, route-link, output action, output status, output selector, project packet, source freshness, import exception register, workflow gates, approval prep, snapshot, operating queue, workflow-map, or open-items behavior change.
- No warning item label, order, severity/code pill, decision item label, decision order, decision prompt, decision recommended action, fallback empty-state, export behavior, export filename, or export content change.
- No helper panel relocation or detail group relocation.
- No new localStorage key and no persisted collapse state.
- No new export action, export artifact, export contract widening, read seam, mutation seam, hosted parity claim, SQL, schema migration, Supabase write, approval persistence, import mutation, live service call, Render redeploy, Vercel promotion, service creation, DNS/auth/ingress/secret change, fixture replay, workbook macro execution, workbook writeback, work authorization, field release, issue creation, task creation, live work order creation, durable field record, production tracking write, assignment mutation, schedule mutation, status mutation, or autonomous AI business-state mutation.

## Sidecar Result

A read-only sidecar scout ran in parallel and made no edits, staged nothing, committed nothing, and did not touch Supabase, Render, Vercel, or Olares.

Recommended next lane:

`Project Miner Admission And Approval Contract Disclosure Controls`

The recommended PM Lane 098 scope is to wrap only `section aria-label="Admission and approval contract"` in the same default-open disclosure pattern while preserving its placement inside `Approval Prep Detail` before `Local Review Checklist`, the `Admission Shape` and `Approval Contract` child cards, existing labels, values, order, fallback text, exports, route links, quick-jump links, read seams, no-storage behavior, and no-authority wording.

## Validation Commands

Run from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
corepack pnpm --filter @apex/operations-web build
rg -n "selected recipient|handoff created|assigned|scheduled|ready for execution|ready for field|field ready|field log of record|hosted parity proven|approval ready|packet admitted|daily report|tracking system|percent complete|released|cleared|approved|accepted|authorized|go/no-go passed|dispatch|dispatched|customer confirmed|JHA complete|LOTO approved|material released|issue created|task created|work order|production-ready" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-097-exception-review-pm-decision-detail-disclosure-controls.json', encoding='utf-8')); print('packet-json-ok')"
git diff --check
git diff --cached --check
```

## Validation Results

- `corepack pnpm --filter @apex/operations-web typecheck` passed.
- `corepack pnpm --filter @apex/operations-web build` passed with `/pm-review/import-intake` in the route output.
- Authority wording scan returned no matches.
- Packet JSON parse returned `packet-json-ok`.
- `git diff --check` passed with line-ending warnings only.
- Focused import-intake Playwright smoke passed with `1 passed` after rebuilding the final source.
- Focused PM intake Playwright smoke suite passed with `4 passed`.
- `git diff --cached --check` passed.

## Closeout Requirements

- Stage only the Lane 097 files listed above.
- Commit with message `Add PM exception decision disclosure controls`.
- Push `clean-main`.
- Restore Olares host parity with `git pull --ff-only`.
- Verify local and host heads match and `bash tools/ai/run-minimal-mcp-trio.sh status` returns `{"status":"not-running"}`.
