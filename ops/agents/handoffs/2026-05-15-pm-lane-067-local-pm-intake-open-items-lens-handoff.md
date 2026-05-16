# PM Lane 067 Handoff - Local PM Intake Open Items Lens

Date: 2026-05-15
Status: Local-current implemented
Scope: Browser-local derived open-items lens for the Project Miner intake workbench

## Executive Summary

PM Lane 067 adds a `Local PM Intake Open Items Lens` panel to `/pm-review/import-intake`.

The lens derives current PM triage posture from existing workbench state:

1. exception review,
2. decision draft,
3. field prep,
4. executor closeout evidence,
5. approval-persistence boundary,
6. project-import boundary.

The point is practical: Jason should be able to separate local attention from future authority blockers without scanning the full page.

This is browser-local derived synthesis only. It grants no authority to create issues, create tasks, authorize work, release work, assign resources, schedule work, change status, approve, persist, import, claim hosted parity, create durable field records, write production tracking rows, call live services, or mutate production state.

## What Changed

The workbench now includes:

1. `Local PM Intake Open Items Lens`,
2. `buildPmIntakeOpenItemsLens(...)`,
3. `Open Items` in the existing `PM Intake Quick Jump Rail`,
4. focused smoke coverage for the lens, links, default and updated derived states,
5. focused smoke coverage proving no `pm-import-intake-open-items:*` localStorage key,
6. focused smoke coverage preserving exact four read seams and zero mutation calls.

The lens is derived from already-loaded reads and existing browser-local state. It adds no new storage key and no export contract.

## Lens Inputs

The lens consumes only these existing local values:

```text
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

A read-only sidecar reviewed the planned scope and confirmed the open-items lens is a good bounded PM Lane 067 slice after Lane 066.

The sidecar confirmed the data inputs:

1. exception register counts from candidate warnings, human decisions, no-go checks, checklist, and decision draft,
2. decision draft completion from decision value, review notes, and local-only attestation,
3. field prep from next and blocked queue counts,
4. executor closeout from local closeout checks,
5. approval persistence from blocked readiness gates,
6. project import from admission-plan mutation authority.

The sidecar warned to avoid language that implies durable authority or completion, including approved, persisted, admitted, import ready, executor closeout complete, or hosted parity proven. The implementation uses local attention, marked, boundary, blocked until later packet, browser-local context, and not-admitted wording.

The sidecar also recommended explicit Playwright coverage for the panel, quick-jump link, target id, initial derived text, live recompute, and no-storage checks. Those assertions were added to the focused import-intake smoke test.

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

PM open-items wording scan:

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-067-local-pm-intake-open-items-lens.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. PM open-items wording scan passed with no matches.
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

After the open-items lens is validated, keep the next PM lane focused on reducing Jason's daily review load on the same local workbench. Durable field records, approval persistence, import mutation, and production tracking remain blocked until later admitted packets exist and are explicitly accepted.
