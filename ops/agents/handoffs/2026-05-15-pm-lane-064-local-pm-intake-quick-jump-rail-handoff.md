# PM Lane 064 Handoff - Local PM Intake Quick Jump Rail

Date: 2026-05-15
Status: Local-current implemented
Scope: Browser-local quick-jump navigation rail for the Project Miner intake workbench

## Executive Summary

PM Lane 064 adds a `PM Intake Quick Jump Rail` to `/pm-review/import-intake`.

The rail links to the existing local PM snapshot, operating queue, import exception register, project/source packet, workflow gates, approval readiness, field-prep, executor closeout, and guardrails sections.

The point is practical: the workbench now has enough useful local panels that Jason needs faster movement through the page. This lane reduces first-screen orientation and scroll burden without creating another artifact, state store, backend path, or authority surface.

This is browser-local navigation only. It grants no authority to create issues, create tasks, authorize work, release work, assign resources, schedule work, change status, approve, persist, import, claim hosted parity, create durable field records, write production tracking rows, call live services, or mutate production state.

## What Changed

The workbench now includes:

1. `PM Intake Quick Jump Rail`
2. stable anchors for the local PM snapshot,
3. stable anchors for the local PM operating queue,
4. stable anchors for the local import exception register,
5. stable anchors for project packet and source freshness,
6. stable anchors for workflow gates,
7. stable anchors for approval persistence readiness,
8. stable anchors for local field prep,
9. stable anchors for local executor closeout,
10. stable anchors for current PM next actions and guardrails,
11. focused smoke coverage for rail rendering, anchor targets, no new localStorage key, exact four read seams, zero mutation calls, and no approve/persist/submit/import controls.

The rail is static and derived from the existing page layout. It adds no new storage key and no export contract.

## Quick Jump Targets

Current rail links:

1. `Snapshot` -> `#pm-intake-snapshot`
2. `Operating Queue` -> `#pm-operating-queue`
3. `Exception Register` -> `#import-exception-register`
4. `Project Packet` -> `#project-packet`
5. `Workflow Gates` -> `#workflow-gates`
6. `Approval Readiness` -> `#approval-readiness`
7. `Field Prep` -> `#field-prep`
8. `Executor Closeout` -> `#executor-closeout`
9. `Guardrails` -> `#guardrails`

## Boundary

The rail consumes no additional data.

It only sits on top of the existing local-current workbench, which still consumes:

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
derived local import exception decision register
derived local field prep coverage snapshot
derived local field prep conversation agenda
derived local PM intake snapshot
```

It does not add a backend endpoint, mutation route, localStorage key, durable field table, production tracking row, export contract, or service call.

The future approval route remains future only:

```text
/api/v1/mutations/project-import-approvals
```

## Sidecar Result

A read-only sidecar reviewed the planned scope and confirmed a browser-local hash-navigation quick jump rail is the right bounded PM lane after Lane 063, as long as it stays navigation-only.

The sidecar confirmed these major section anchors are sufficient:

1. `#pm-intake-snapshot`
2. `#pm-operating-queue`
3. `#import-exception-register`
4. `#project-packet`
5. `#workflow-gates`
6. `#approval-readiness`
7. `#field-prep`
8. `#executor-closeout`
9. `#guardrails`

The sidecar recommended avoiding language that implies action, approval, acceptance, field readiness, hosted proof, go/no-go passage, issue creation, task creation, work authorization, schedule or status changes, approval persistence, import admission, or hosted parity.

The sidecar made no edits, staged no files, committed nothing, pushed nothing, deployed nothing, ran no macros, and did not access Supabase, Render, Vercel, or Olares.

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

PM quick-jump wording scan:

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-064-local-pm-intake-quick-jump-rail.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. PM quick-jump wording scan passed with no matches.
4. focused import-intake Playwright smoke initially caught a non-unique top navigation `Approval readiness` assertion after the quick jump rail added a second same-topic link; the assertion was narrowed to the exact route link and the rerun passed with `1 passed`.
5. focused PM intake Playwright smoke suite passed with `4 passed`.
6. packet JSON parse passed with `packet-json-ok`.
7. `git diff --check` passed with line-ending normalization warnings only.
8. `git diff --cached --check` passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. new localStorage keys,
3. new export contracts,
4. Approval Preview JSON widening,
5. field-prep export contract widening,
6. durable field records,
7. production tracking writes,
8. work authorization,
9. field release,
10. issue creation,
11. task creation,
12. live work order creation,
13. live task creation,
14. hosted parity claims,
15. SQL file creation,
16. SQL execution,
17. schema migration,
18. Supabase writes,
19. adapter implementation,
20. approval persistence,
21. import mutation,
22. live service calls,
23. Render redeploy,
24. Vercel promotion,
25. service creation,
26. DNS, auth, ingress, or secret changes,
27. fixture replay,
28. workbook macro execution,
29. workbook writeback,
30. assignment mutation,
31. schedule mutation,
32. status mutation,
33. autonomous AI business-state mutation.

## Next Recommended Move

After the quick jump rail is validated, keep the next PM lane focused on reducing Jason's day-to-day operating load on the same local workbench, or return to hosted parity executor closeout if hosted proof becomes the controlling blocker. Durable field records, approval persistence, import mutation, and production tracking remain blocked until later admitted packets exist and are accepted.
