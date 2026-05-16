# PM Lane 060 Handoff - Local Field Prep Conversation Agenda

Date: 2026-05-15
Status: Local-current implemented
Scope: Browser-local derived field-prep conversation agenda and export in the Project Miner intake workbench

## Executive Summary

PM Lane 060 adds a `Local Field Prep Conversation Agenda` and `Export Field Prep Conversation Agenda` action to `/pm-review/import-intake`.

The agenda derives context, ask, confirm, and blocked items from the existing local field prep coverage snapshot. It does not add another form or storage key. It turns the local prep material into a practical "what do I say next?" surface for PM, lead, customer, and field conversations.

The point is practical: reduce Jason's field-prep conversation burden before Temp Power work begins. The agenda is browser-local conversation prep only and grants no authority to create issues, create tasks, authorize work, release work, assign resources, schedule work, change status, approve, persist, import, claim hosted parity, create durable field records, write production tracking rows, or mutate production state.

## What Changed

The workbench now includes:

1. `Local Field Prep Conversation Agenda`
2. `Export Field Prep Conversation Agenda`
3. PM brief inclusion for the agenda
4. Field Kickoff Brief inclusion for the agenda
5. focused smoke coverage for default and updated agenda states, no new localStorage key, standalone export content, existing export content, reset behavior, exact four read seams, zero mutation calls, and no approve/persist/submit/import controls

The agenda is derived from the coverage snapshot and adds no new storage key.

## Agenda Logic

The agenda uses the existing field prep coverage snapshot:

1. `covered` coverage becomes agenda `context`.
2. `partial` coverage becomes agenda `confirm`.
3. `open` coverage becomes agenda `ask`.
4. `field-authority-boundary` becomes `context` only when covered, `confirm` once any prep context exists, and `blocked` when no prep context exists.
5. `production-tracking-boundary` is always `blocked`.

Agenda status values:

1. `context`
2. `ask`
3. `confirm`
4. `blocked`

## Export Surfaces

The conversation agenda now appears in three browser-local exports:

1. `Export PM Brief`
2. `Export Field Kickoff Brief`
3. `Export Field Prep Conversation Agenda`

`Export Field Prep Conversation Agenda` produces:

```text
<candidate_id>-field-prep-conversation-agenda.md
```

The export includes candidate identity, authority, source freshness, proposed shape counts, agenda summary, agenda items, coverage snapshot context, not-allowed guardrails, and minimum-use instructions.

## Boundary

The agenda consumes only local workbench state:

```text
GET /api/v1/reads/project-import-candidate
GET /api/v1/reads/project-import-admission-plan
GET /api/v1/reads/project-import-approval-contract
GET /api/v1/reads/project-import-approval-storage-plan
browser-local review checklist
browser-local approval-decision draft
browser-local executor closeout checklist
browser-local field readiness checklist
browser-local field questions draft
browser-local field observation scratchpad
derived local PM operating queue
derived local field prep queue
derived local field prep coverage snapshot
derived local field prep conversation agenda
```

It does not add a backend endpoint, mutation route, localStorage key, durable field table, production tracking row, or service call.

The future approval route remains future only:

```text
/api/v1/mutations/project-import-approvals
```

## Sidecar Result

A read-only sidecar reviewed PM Lanes 054-059 and recommended the local field prep conversation agenda as the correct next reducer. It confirmed:

1. this lane should be derived from the coverage snapshot,
2. the UI should sit directly after `Local Field Prep Coverage Snapshot`,
3. the agenda should use context, ask, confirm, and blocked language,
4. the export should include candidate context, agenda items, coverage context, not-allowed guardrails, and minimum-use wording,
5. tests should prove exact read seams, zero mutations, no new storage key, exported content, reset behavior, and no approve/persist/submit/import controls.

The sidecar made no edits, staged no files, committed nothing, pushed nothing, deployed nothing, and did not call live services.

## Validation

Commands are run from:

```text
C:/APEX Platform/apex-power-ops-platform
```

Operations-web typecheck:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
```

Operations-web build:

```powershell
corepack pnpm --filter @apex/operations-web build
```

Field-prep agenda wording scan:

```powershell
rg -n "ready for field|ready for execution|field ready|field log of record|daily report|tracking system|percent complete|released|cleared|approved|accepted|authorized|go/no-go passed|dispatch|dispatched|assigned|scheduled|customer confirmed|JHA complete|LOTO approved|material released|issue created|task created|work order|production-ready" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Focused import-intake smoke:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Focused PM intake smoke suite:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Packet JSON parse:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-060-local-field-prep-conversation-agenda.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. field-prep agenda wording scan passed with no matches.
4. focused import-intake Playwright smoke passed with `1 passed`; parallel server startup emitted an `EADDRINUSE` notice after the test completed because another smoke server occupied port `3030`.
5. focused PM intake Playwright smoke suite passed with `4 passed`.
6. packet JSON parse passed with `packet-json-ok`.
7. `git diff --check` passed with line-ending normalization warnings only.
8. scoped `git diff --cached --check` passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. new localStorage keys,
3. durable field records,
4. production tracking writes,
5. work authorization,
6. field release,
7. issue creation,
8. task creation,
9. live work order creation,
10. live task creation,
11. hosted parity claims,
12. SQL file creation,
13. SQL execution,
14. schema migration,
15. Supabase writes,
16. adapter implementation,
17. approval persistence,
18. import mutation,
19. live service calls,
20. Render redeploy,
21. Vercel promotion,
22. service creation,
23. DNS, auth, ingress, or secret changes,
24. fixture replay,
25. workbook macro execution,
26. workbook writeback,
27. assignment mutation,
28. schedule mutation,
29. status mutation,
30. autonomous AI business-state mutation.

## Next Recommended Move

Use the agenda as the last local field-prep reducer before either improving review ergonomics or preparing a later durable execution-tracking admission path behind an explicit packet boundary.
