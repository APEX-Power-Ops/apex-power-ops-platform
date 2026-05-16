# PM Lane 066 Handoff - Local PM Intake Workflow Map

Date: 2026-05-15
Status: Local-current implemented
Scope: Browser-local derived workflow map for the Project Miner intake workbench

## Executive Summary

PM Lane 066 adds a `Local PM Intake Workflow Map` panel to `/pm-review/import-intake`.

The map derives the current PM intake path from existing workbench state:

1. source intake,
2. exception review,
3. decision draft,
4. field prep,
5. executor closeout,
6. approval-persistence boundary,
7. project-import boundary.

The point is practical: Jason should be able to see the whole local PM path without translating between every panel.

This is browser-local derived synthesis only. It grants no authority to create issues, create tasks, authorize work, release work, assign resources, schedule work, change status, approve, persist, import, claim hosted parity, create durable field records, write production tracking rows, call live services, or mutate production state.

## What Changed

The workbench now includes:

1. `Local PM Intake Workflow Map`,
2. `buildPmIntakeWorkflowMap(...)`,
3. `Workflow Map` in the existing `PM Intake Quick Jump Rail`,
4. focused smoke coverage for the map, links, default and updated derived states,
5. focused smoke coverage proving no `pm-import-intake-workflow-map:*` localStorage key,
6. focused smoke coverage preserving exact four read seams and zero mutation calls.

The map is derived from already-loaded reads and existing browser-local state. It adds no new storage key and no export contract.

## Workflow Inputs

The map consumes only these existing local values:

```text
candidate source freshness
derived local import exception decision register
browser-local approval-decision draft
derived local field prep queue
browser-local executor closeout checklist
approval-persistence readiness gates
read-only admission plan
```

It does not call additional read seams.

It does not add a backend endpoint, mutation route, localStorage key, durable field table, production tracking row, export contract, or service call.

The future approval route remains future only:

```text
/api/v1/mutations/project-import-approvals
```

## Sidecar Result

A read-only sidecar reviewed the planned scope and confirmed a browser-local workflow map is the right bounded PM lane after Lane 065.

The sidecar confirmed the data inputs:

1. source intake from candidate source freshness,
2. exception review from import exception register counts,
3. decision draft from local decision value, notes, and local-only attestation,
4. field prep from the first next or blocked field-prep queue item,
5. executor closeout from local closeout checks,
6. approval-persistence boundary from readiness gate blockers,
7. project-import boundary from admission-plan mutation authority.

The sidecar warned to avoid language that implies durable workflow authority, approval, acceptance, field readiness, release, persistence, import readiness, closeout completion, or a workflow engine. The implementation uses browser-local map, review synthesis, evidence, boundary, and not-admitted wording.

The sidecar also recommended using `context` instead of `source` for covered non-source stages; the status vocabulary was tightened accordingly.

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

PM workflow-map wording scan:

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-066-local-pm-intake-workflow-map.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. PM workflow-map wording scan passed with no matches.
4. focused import-intake Playwright smoke passed with `1 passed`.
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

After the workflow map is validated, keep the next PM lane focused on reducing Jason's day-to-day operating load on the same local workbench, or return to hosted parity executor closeout if hosted proof becomes the controlling blocker. Durable field records, approval persistence, import mutation, and production tracking remain blocked until later admitted packets exist and are accepted.
