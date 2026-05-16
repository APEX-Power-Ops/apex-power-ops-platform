# PM Lane 125 - Local Review Checklist Body Controls Handoff

## Purpose

PM Lane 125 reduces the `/pm-review/import-intake` scan burden by wrapping only the existing `Local Review Checklist` body content in a labeled body-controls container under its already-existing browser-native, default-open disclosure.

This is local review-prep scanning and AI-orchestration ergonomics only. It does not accept, approve, persist, deploy, import, assign, schedule, change status, create issues, create tasks, create durable field records, write production tracking rows, claim hosted parity, or mutate production state.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Source floor: `37359fa9aab4bae4e8262667bd86c77fca428a39`
- Prior lane: PM Lane 124, Local Admission And Approval Contract Body Controls
- Hosted floor: PM Lane 041C accepted closed; hosted mutation-seam and paired PM intake smokes are green
- Sidecar scout: read-only PM Lane 126 recommendation completed with no edits

## Implemented Scope

- Added only a labeled `Local review checklist controls` body container under the existing `Local review checklist` disclosure summary.
- Preserved the existing disclosure, aria label, heading, and placement inside `Approval Prep Detail` after Admission and Approval Contract.
- Preserved the checklist count, seven checklist items, checkbox behavior, clear button, candidate-scoped browser storage, export behavior, and no persisted collapse-state behavior.
- Added focused smoke coverage for default-open state, visible body controls, collapse/reopen behavior, hidden/visible checklist controls, seven checklist labels, no `collapse|disclosure|local-review-checklist` localStorage key, preserved `0 of 7` to `2 of 7` local count behavior, preserved clear button enablement, and unchanged authority guard posture.
- Updated the PM lane workflow docs, Temp Power orchestration plan, stakeholder acceleration lane, `PROJECT_STATUS.md`, and this packet/handoff.

## Files Changed

- `PROJECT_STATUS.md`
- `apps/operations-web/app/pm-review/import-intake/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-16-pm-lane-125-local-review-checklist-body-controls.json`
- `ops/agents/handoffs/2026-05-16-pm-lane-125-local-review-checklist-body-controls-handoff.md`

## Not Allowed

- No backend endpoint change.
- No new route or route target change.
- No quick-jump, route-link, output action, output status, project packet, source freshness, intake snapshot, operating queue, import exception register, workflow gates, exception review detail, admission and approval contract, local approval decision draft, local executor closeout intake, local field readiness checklist, local field questions draft, field prep queue, field prep coverage snapshot, field prep conversation agenda, field observation scratchpad, approval-readiness, guardrails, command-center, meeting-readout, constraint radar, daily-review-script, start-here, output-selector, handoff-guide, workflow-map, or open-items behavior change.
- No checklist label, checklist detail, checkbox behavior, checklist count behavior, clear button behavior, candidate-scoped storage key, dynamic text, or export behavior change.
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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-125-local-review-checklist-body-controls.json', encoding='utf-8')); print('packet-json-ok')"
git diff --check
git diff --cached --check
```

## Validation Results

- `corepack pnpm --filter @apex/operations-web typecheck` passed.
- `corepack pnpm --filter @apex/operations-web build` passed and included `/pm-review/import-intake` in the static route output.
- Authority wording scan returned no matches for affirmative execution/admission/field-readiness/production-ready wording.
- `corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts` passed with 1 test using `OPERATIONS_WEB_BROWSER_SMOKE_PORT=3035`.
- `corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts` passed with 4 tests using `OPERATIONS_WEB_BROWSER_SMOKE_PORT=3036`.
- Packet JSON parse returned `packet-json-ok`.
- `git diff --check` passed with line-ending warnings only.

## Sidecar Result

The read-only sidecar scout recommended `PM Lane 126 - Local Approval Decision Draft Body Controls` as the next adjacent local ergonomics slice. The scout made no edits, staged nothing, committed nothing, ran no browser or live service calls, and did not touch Supabase, Render, Vercel, Olares, or workbook files.

## Next Recommended Lane

`PM Lane 126 - Local Approval Decision Draft Body Controls`

That next lane should wrap only the existing `Local approval decision draft` body content under its already-existing default-open disclosure, preserving the decision select, notes textarea, local attestation checkbox, clear button, existing candidate-scoped storage key, no persisted collapse state, no authority widening, and the same focused smoke pattern.
