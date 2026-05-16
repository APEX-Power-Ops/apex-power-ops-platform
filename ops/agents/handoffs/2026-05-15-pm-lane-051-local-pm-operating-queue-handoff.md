# PM Lane 051 Handoff - Local PM Operating Queue

Date: 2026-05-15
Status: Local-current implemented
Scope: Browser-local PM review guidance in the Project Miner intake workbench

## Executive Summary

PM Lane 051 adds a browser-local `Local PM Operating Queue` to `/pm-review/import-intake`.

The queue translates the current local checklist, local approval-decision draft, and approval-persistence readiness gates into complete, next, and blocked PM review moves. It is meant to reduce the daily interpretation burden: Jason can see what to do next without reading packet docs or asking another agent to summarize state.

This is local review guidance only. It creates no live task, approval record, schema, persistence, import mutation, assignment, schedule, status, hosted proof, or production state.

## What Changed

The queue appears high in the `Daily Intake Starting Point` workbench, immediately after the intake summary.

It currently derives six queue items:

1. `Review source and exceptions`
2. `Prepare local decision draft`
3. `Export review artifacts`
4. `Hosted parity executor closeout`
5. `Approval persistence implementation`
6. `Project import packet`

The first three are local review-prep moves. The last three remain blocked until later packets admit hosted parity, approval persistence implementation, and import mutation.

The Markdown PM brief now includes a `PM Operating Queue` section with complete, next, and blocked counts plus each queue item detail.

## Boundary

This lane does not change the four read seams:

```text
GET /api/v1/reads/project-import-candidate
GET /api/v1/reads/project-import-admission-plan
GET /api/v1/reads/project-import-approval-contract
GET /api/v1/reads/project-import-approval-storage-plan
```

It does not add any mutation route.

The future approval route remains future only:

```text
/api/v1/mutations/project-import-approvals
```

## Sidecar Result

A read-only sidecar reviewed the intended PM operating queue and recommended:

1. label it as local/browser-local so it does not sound like live task creation,
2. place it high in the workbench after the intake summary,
3. avoid authority wording such as approve, persist, submit, run import, create schema, write approval, ready to import, or production-ready,
4. prove initial and updated queue states in the smoke,
5. keep localStorage and zero-mutation assertions.

Those recommendations were accepted. The sidecar made no edits, staged no files, committed nothing, pushed nothing, deployed nothing, and did not call live services.

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-051-local-pm-operating-queue.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. focused import-intake Playwright smoke passed with `1 passed` after refreshing the production build.
4. focused PM intake Playwright smoke suite passed with `4 passed`.
5. packet JSON parse passed with `packet-json-ok`.
6. `git diff --check` passed with line-ending normalization warnings only.
7. scoped `git diff --cached --check` passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. live task creation,
3. SQL file creation,
4. SQL execution,
5. schema migration,
6. Supabase writes,
7. adapter implementation,
8. approval persistence,
9. import mutation,
10. live service calls,
11. Render redeploy,
12. Vercel promotion,
13. hosted parity claim,
14. service creation,
15. DNS, auth, ingress, or secret changes,
16. fixture replay,
17. workbook macro execution,
18. workbook writeback,
19. assignment mutation,
20. schedule mutation,
21. status mutation,
22. autonomous AI business-state mutation.

## Next Recommended Move

Keep PM Lane 041A/041B as the hosted parity lanes. In parallel, continue small local PM workbench slices only when they reduce Jason's daily review burden without opening schema, persistence, import, assignment, schedule, or status writes.
