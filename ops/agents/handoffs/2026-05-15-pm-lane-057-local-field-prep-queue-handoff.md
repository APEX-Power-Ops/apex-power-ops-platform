# PM Lane 057 Handoff - Local Field Prep Queue

Date: 2026-05-15
Status: Local-current implemented
Scope: Browser-local derived field-prep guidance in the Project Miner intake workbench

## Executive Summary

PM Lane 057 adds a `Local Field Prep Queue` to `/pm-review/import-intake`.

The queue derives complete, next, and blocked prep moves from the browser-local field readiness checklist and field questions draft. It does not store additional state. It shows whether the current candidate has local field questions, local readiness evidence, enough context for a Field Kickoff Brief, field-authority boundary acknowledgement, and the still-blocked production execution tracking path.

The point is practical: reduce the PM burden of interpreting field-prep notes before Temp Power kickoff discussions. The queue is browser-local prep guidance only and grants no authority to create issues, create tasks, authorize work, release work, assign resources, schedule work, change status, approve, persist, import, claim hosted parity, or mutate production state.

## What Changed

The workbench now includes five derived queue items:

1. `Capture field questions draft`
2. `Mark field readiness prep evidence`
3. `Export field kickoff prep brief`
4. `Confirm field authority boundary`
5. `Production execution tracking`

The queue is derived from already-local state:

```text
pm-import-intake-field-readiness:<candidate_id>
pm-import-intake-field-questions:<candidate_id>
```

It adds no new localStorage key.

## Queue Logic

`Capture field questions draft` is complete when any field question text exists.

`Mark field readiness prep evidence` is complete when any field readiness checkbox is checked, next when questions exist, and blocked before questions exist.

`Export field kickoff prep brief` is next only when both field questions and readiness evidence exist.

`Confirm field authority boundary` is complete only when the field-authority boundary checkbox is checked, next when the kickoff brief has prep context, and blocked otherwise.

`Production execution tracking` is always blocked because no issue, task, assignment, schedule, status, import, approval, or production tracking write is admitted by this local workbench.

## Export Surfaces

The field prep queue now appears in two browser-local exports:

1. `Export PM Brief`
2. `Export Field Kickoff Brief`

Both exports include the queue count and all queue item statuses.

## Boundary

The queue consumes only local workbench state:

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
derived local PM operating queue
derived local field prep queue
```

It does not add a backend endpoint, mutation route, durable queue row, or new browser storage key.

The future approval route remains future only:

```text
/api/v1/mutations/project-import-approvals
```

## Sidecar Result

A read-only sidecar reviewed the field-prep queue scope and current patch direction. It confirmed:

1. this is a good bounded next slice if the queue stays derived from existing browser-local state,
2. the safest status logic is exactly the five-item shape used here,
3. queue wording must repeat browser-local prep guidance and no-authority language because `queue`, `complete`, and `Field Kickoff Brief` can otherwise sound operational,
4. smoke should prove initial and prepared queue counts, queue sections in both exports, reset behavior, exact read seams, and zero mutation calls.

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

Field-release wording scan:

```powershell
rg -n "ready for field|ready for execution|released|cleared|approved|accepted|authorized|go/no-go passed|dispatch|customer confirmed|JHA complete|LOTO approved|material released|issue created|task created|work order|production-ready" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-057-local-field-prep-queue.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. prohibited field-release wording scan passed with no matches.
4. focused import-intake Playwright smoke passed with `1 passed`.
5. focused PM intake Playwright smoke suite passed with `4 passed`.
6. packet JSON parse passed with `packet-json-ok`.
7. `git diff --check` passed with line-ending normalization warnings only.
8. scoped `git diff --cached --check` passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. durable queue rows,
3. work authorization,
4. field release,
5. issue creation,
6. task creation,
7. live work order creation,
8. live task creation,
9. hosted parity claims,
10. SQL file creation,
11. SQL execution,
12. schema migration,
13. Supabase writes,
14. adapter implementation,
15. approval persistence,
16. import mutation,
17. live service calls,
18. Render redeploy,
19. Vercel promotion,
20. service creation,
21. DNS, auth, ingress, or secret changes,
22. fixture replay,
23. workbook macro execution,
24. workbook writeback,
25. assignment mutation,
26. schedule mutation,
27. status mutation,
28. autonomous AI business-state mutation.

## Next Recommended Move

Use this queue to decide whether the local Field Kickoff Brief is ready enough for conversation prep. The next product slice should stay local and reduce Jason's field-prep burden unless a later packet explicitly admits hosted parity closeout, approval persistence, import mutation, or production execution tracking writes.
