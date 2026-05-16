# PM Lane 135 - Current PM Next Actions and Guardrails Body Controls Handoff

## Purpose

PM Lane 135 reduces the `/pm-review/import-intake` scan burden by wrapping only the existing `Current PM Next Actions and Guardrails` body content in a labeled body-controls container under its already-existing browser-native, default-open disclosure.

This is local browser-only final guardrail scanning and AI-orchestration ergonomics only. It does not authorize approval persistence, accept, approve, persist, deploy, import, assign, schedule, change status, create issues, create tasks, create durable field records, write production tracking rows, claim hosted parity, or mutate production state.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `ad3b4137757e0df820b220ead5dc357f1bc87bf1`
- Prior lane: PM Lane 134, Approval Persistence Readiness Body Controls
- Hosted floor: PM Lane 041C accepted closed; hosted mutation-seam and paired PM intake smokes are green
- Sidecar scout: read-only PM Lane 136 recommendation completed with no edits

## Implemented Scope

- Added only a labeled `Current PM guardrails body controls` container under the existing `Current PM next actions and guardrails` disclosure summary.
- Preserved the existing `#guardrails` anchor, disclosure aria label, heading, placement inside Authority Boundary Detail, and default-open behavior.
- Preserved the two guardrail cards, action list, not-allowed list, blocked authority wording, route and quick-jump links, and no persisted collapse-state behavior.
- Added focused smoke coverage for default-open state, visible body controls, collapse/reopen behavior, hidden/visible guardrails controls, two guardrail cards, no `collapse|disclosure|guardrails` localStorage key, and unchanged authority guard posture.
- Updated the PM lane workflow docs, Temp Power orchestration plan, stakeholder acceleration lane, `PROJECT_STATUS.md`, and this packet/handoff.

## Files Changed

- `PROJECT_STATUS.md`
- `apps/operations-web/app/pm-review/import-intake/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-16-pm-lane-135-current-pm-next-actions-guardrails-body-controls.json`
- `ops/agents/handoffs/2026-05-16-pm-lane-135-current-pm-next-actions-guardrails-body-controls-handoff.md`

## Not Allowed

- No backend endpoint change.
- No new route or route target change.
- No quick-jump, route-link, output action, output status, project packet, source freshness, intake snapshot, operating queue, import exception register, workflow gates, exception review detail, admission and approval contract, local review checklist, local approval decision draft, local executor closeout intake, field-prep, approval-readiness, command-center, meeting-readout, constraint radar, daily-review-script, start-here, output-selector, handoff-guide, workflow-map, or open-items behavior change.
- No guardrail card heading, action-list item, not-allowed item, blocked-state wording, route link, quick-jump link, or export text behavior change.
- No helper panel relocation or detail group relocation.
- No new localStorage key and no persisted collapse state.
- No new export action, export artifact, export contract widening, read seam, mutation seam, hosted parity claim, SQL, schema migration, Supabase write, approval persistence, import mutation, live service call, Render redeploy, Vercel promotion, service creation, DNS/auth/ingress/secret change, fixture replay, workbook macro execution, workbook writeback, work authorization, field release, issue creation, task creation, live work order creation, durable field record, production tracking write, assignment mutation, schedule mutation, status mutation, or autonomous AI business-state mutation.

## Validation Commands

Run from `C:/APEX Platform/apex-power-ops-platform`:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
corepack pnpm --filter @apex/operations-web build
rg -n "selected recipient|handoff created|assigned|scheduled|ready for execution|ready for field|field ready|field log of record|hosted parity proven|approval ready|packet admitted|daily report|tracking system|percent complete|released|cleared|approved|accepted|authorized|go/no-go passed|dispatch|dispatched|customer confirmed|JHA complete|LOTO approved|material released|issue created|task created|work order|production-ready" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-135-current-pm-next-actions-guardrails-body-controls.json', encoding='utf-8')); print('packet-json-ok')"
git diff --check
git diff --cached --check
```

## Validation Results

- `corepack pnpm --filter @apex/operations-web typecheck` passed.
- `corepack pnpm --filter @apex/operations-web build` passed and kept `/pm-review/import-intake` in the static route output.
- Authority wording scan over the touched app and smoke test files returned no matches.
- Focused PM import-intake Playwright smoke passed with 1 test using `OPERATIONS_WEB_BROWSER_SMOKE_PORT=3055`.
- Four-route PM intake Playwright suite passed with 4 tests using `OPERATIONS_WEB_BROWSER_SMOKE_PORT=3056`.
- Packet JSON parse returned `packet-json-ok`.
- `git diff --check` passed with line-ending warnings only.

## Sidecar Result

The read-only sidecar scout recommended `PM Lane 136 - Import Candidate Approval Persistence Schema And Adapter Implementation` as the next bounded product lane after the guardrails body-control slice. The scout made no edits, staged nothing, committed nothing, pushed nothing, ran no browser or live services, and touched no external systems.

## Next Recommended Lane

`PM Lane 136 - Import Candidate Approval Persistence Schema And Adapter Implementation`

That next lane should implement only the Lane 049 approval persistence contract: a dedicated approval table, explicit insert-only approval adapter, and a narrow PM-only approval mutation seam. It must keep project import, workpackage, task, apparatus, assignment, schedule, status, production tracking writes, workbook macros/writeback, generic mutation shortcuts, fixture replay into live data, and deployment work blocked unless a separate packet explicitly admits them.
