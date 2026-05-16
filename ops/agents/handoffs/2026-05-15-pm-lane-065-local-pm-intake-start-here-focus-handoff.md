# PM Lane 065 Handoff - Local PM Intake Start Here Focus

Date: 2026-05-15
Status: Local-current implemented
Scope: Browser-local derived start-here focus panel for the Project Miner intake workbench

## Executive Summary

PM Lane 065 adds a `Local PM Intake Start Here` panel to `/pm-review/import-intake`.

The panel derives one top-level focus list from existing workbench state:

1. first local move,
2. exception attention,
3. field-prep focus,
4. useful local export,
5. blocked future authority.

The point is practical: Jason should be able to open the workbench and immediately see where to begin without re-reading every local panel.

This is browser-local derived synthesis only. It grants no authority to create issues, create tasks, authorize work, release work, assign resources, schedule work, change status, approve, persist, import, claim hosted parity, create durable field records, write production tracking rows, call live services, or mutate production state.

## What Changed

The workbench now includes:

1. `Local PM Intake Start Here`,
2. `buildPmIntakeStartHere(...)`,
3. `Start Here` in the existing `PM Intake Quick Jump Rail`,
4. focused smoke coverage for default and updated focus states,
5. focused smoke coverage proving no `pm-import-intake-start-here:*` localStorage key,
6. focused smoke coverage preserving exact four read seams and zero mutation calls.

The panel is derived from already-loaded reads and existing browser-local state. It adds no new storage key and no export contract.

## Focus Inputs

The panel consumes only these existing local values:

```text
derived local PM operating queue
derived local import exception decision register
derived local field prep queue
derived local PM intake snapshot
approval-persistence readiness gates
```

It does not call additional read seams.

It does not add a backend endpoint, mutation route, localStorage key, durable field table, production tracking row, export contract, or service call.

The future approval route remains future only:

```text
/api/v1/mutations/project-import-approvals
```

## Sidecar Result

A read-only sidecar reviewed the planned scope and confirmed a browser-local start-here focus panel is the right bounded PM lane after Lane 064.

The sidecar confirmed the data inputs:

1. first next local move from the PM operating queue,
2. exception attention from import exception register counts,
3. field-prep next move from the field prep queue,
4. useful export guidance that points only to existing exports,
5. blocked future authority from approval-persistence readiness gates and snapshot posture.

The sidecar warned that the panel copy should explicitly say it creates no localStorage key or export artifact because the useful-export card could otherwise sound like a new export surface. That wording was added.

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

PM start-here wording scan:

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-065-local-pm-intake-start-here-focus.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. PM start-here wording scan passed with no matches.
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

After the start-here focus panel is validated, keep the next PM lane focused on reducing Jason's day-to-day operating load on the same local workbench, or return to hosted parity executor closeout if hosted proof becomes the controlling blocker. Durable field records, approval persistence, import mutation, and production tracking remain blocked until later admitted packets exist and are accepted.
