# PM Lane 056 Handoff - Local Field Questions Draft

Date: 2026-05-15
Status: Local-current implemented
Scope: Browser-local field question drafting in the Project Miner intake workbench

## Executive Summary

PM Lane 056 adds a `Local Field Questions Draft` to `/pm-review/import-intake`.

The draft gives the PM one local place to capture drawing/source questions, site access and safety questions, crew/equipment questions, material/staging questions, customer constraint questions, and PM follow-up notes for the current Project Miner Temp Power candidate.

The point is practical: reduce PM-to-lead and PM-to-field relay burden before production execution tracking exists. The draft is browser-local prep context only and grants no authority to create issues, create tasks, authorize work, release work, assign resources, schedule work, change status, approve, persist, import, claim hosted parity, or mutate production state.

## What Changed

The workbench now includes six local draft fields:

1. `Drawing/source questions`
2. `Site access and safety questions`
3. `Crew and equipment questions`
4. `Material and staging questions`
5. `Customer constraint questions`
6. `PM follow-up notes`

Draft state is scoped to the active import candidate in browser localStorage:

```text
pm-import-intake-field-questions:<candidate_id>
```

For the current Temp Power candidate, the key is:

```text
pm-import-intake-field-questions:pm-import-candidate-miner-temp-power
```

## Export Surfaces

The field questions draft now appears in two browser-local exports:

1. `Export PM Brief`
2. `Export Field Kickoff Brief`

The PM brief records whether the draft is present and includes each local draft field.

The Field Kickoff Brief includes the same field questions draft section so PM, lead, and field review conversations can start from the same local notes.

## Boundary

The draft consumes only local workbench state:

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
derived readiness gates
derived local PM operating queue
```

It does not add a backend endpoint or mutation route.

The future approval route remains future only:

```text
/api/v1/mutations/project-import-approvals
```

## Sidecar Result

A read-only sidecar reviewed the field-question scope and current patch direction. It confirmed:

1. this is a good bounded next slice because it follows the existing browser-local pattern,
2. labels should use questions, draft, prep context, and local export context,
3. avoid wording such as ready for field, released, cleared, approved, accepted, authorized, dispatch, issue created, task created, work order, or production-ready,
4. include the draft in PM brief and Field Kickoff Brief,
5. keep smoke coverage focused on candidate-scoped localStorage, exported text, clear behavior, exact read seams, zero mutation calls, and no approve/persist/submit/import controls.

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-056-local-field-questions-draft.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. prohibited field-release wording scan passed with no matches after tightening one inherited read-only handoff phrase and one test variable name.
4. focused import-intake Playwright smoke passed with `1 passed` after aligning a visible text assertion.
5. focused PM intake Playwright smoke suite passed with `4 passed`.
6. packet JSON parse passed with `packet-json-ok`.
7. `git diff --check` passed with line-ending normalization warnings only.
8. scoped `git diff --cached --check` passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. work authorization,
3. field release,
4. issue creation,
5. task creation,
6. live work order creation,
7. live task creation,
8. hosted parity claims,
9. SQL file creation,
10. SQL execution,
11. schema migration,
12. Supabase writes,
13. adapter implementation,
14. approval persistence,
15. import mutation,
16. live service calls,
17. Render redeploy,
18. Vercel promotion,
19. service creation,
20. DNS, auth, ingress, or secret changes,
21. fixture replay,
22. workbook macro execution,
23. workbook writeback,
24. assignment mutation,
25. schedule mutation,
26. status mutation,
27. autonomous AI business-state mutation.

## Next Recommended Move

Use this draft to capture the exact open questions that would otherwise live in chat or memory. The next product slice should stay local and reduce Jason's field-prep burden unless a later packet explicitly admits hosted parity closeout, approval persistence, import mutation, or production execution tracking writes.
