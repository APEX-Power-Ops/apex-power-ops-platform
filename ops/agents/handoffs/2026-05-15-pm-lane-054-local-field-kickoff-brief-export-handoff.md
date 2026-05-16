# PM Lane 054 Handoff - Local Field Kickoff Prep Brief Export

Date: 2026-05-15
Status: Local-current implemented
Scope: Browser-local PM-to-field relay reduction in the Project Miner intake workbench

## Executive Summary

PM Lane 054 adds an `Export Field Kickoff Brief` action to `/pm-review/import-intake`.

The downloaded Markdown brief packages the current candidate identity, project location, source freshness, proposed workpackage/task/apparatus shape, workpackage preview, field-prep questions, warnings, human decisions, local review evidence, executor closeout evidence, local PM operating queue, workflow gates, future-not-admitted surfaces, and not-allowed guardrails.

The point is practical: give PM, lead, and field review conversations a portable prep artifact without creating release-to-field authority. The brief is context only and grants no authority to approve, persist, import, create tasks, authorize work, assign work, schedule work, change status, claim hosted parity, or mutate production state.

## What Changed

The workbench now has four local exports:

1. `Export PM Brief`
2. `Export Approval Preview JSON`
3. `Export Executor Handoff`
4. `Export Field Kickoff Brief`

The new field-prep filename is candidate-scoped:

```text
pm-import-candidate-miner-temp-power-field-kickoff-brief.md
```

## Brief Sections

The generated Markdown includes:

1. title and no-authority preamble,
2. field-prep boundary,
3. project snapshot,
4. proposed field shape,
5. workpackage preview,
6. field prep questions,
7. exceptions and PM decisions,
8. local review evidence,
9. local PM operating queue,
10. workflow gates,
11. future surfaces are not admitted,
12. not allowed,
13. minimum field-prep use.

## Boundary

The field-prep brief consumes only the already-loaded local workbench state:

```text
GET /api/v1/reads/project-import-candidate
GET /api/v1/reads/project-import-admission-plan
GET /api/v1/reads/project-import-approval-contract
GET /api/v1/reads/project-import-approval-storage-plan
browser-local review checklist
browser-local approval-decision draft
browser-local executor closeout checklist
derived local PM operating queue
derived workflow gates
```

It does not add a backend endpoint, localStorage key, or mutation route.

The future approval route remains future only:

```text
/api/v1/mutations/project-import-approvals
```

## Sidecar Result

A read-only sidecar reviewed the proposed next slice and confirmed:

1. a field kickoff prep brief is a good bounded next slice if framed as local context only,
2. avoid wording such as released to field, authorized work, dispatch, assigned, scheduled, or ready for execution,
3. include project identity, candidate shape, exceptions, PM decisions, safe field review questions, not-authorized uses, approval/import blockers, and not-allowed guardrails,
4. keep smoke coverage light and focused on the download, no-authority wording, exact read seams, and zero mutation calls.

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

Release-to-field wording scan:

```powershell
rg -n "kickoff approved|released to field|ready for execution|authorized work|dispatch|production-ready|assigned|scheduled" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-054-local-field-kickoff-brief-export.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. prohibited release-to-field wording scan passed with no matches.
4. focused import-intake Playwright smoke passed with `1 passed`.
5. focused PM intake Playwright smoke suite passed with `4 passed` on serialized rerun after build.
6. packet JSON parse passed with `packet-json-ok`.
7. `git diff --check` passed with line-ending normalization warnings only.
8. scoped `git diff --cached --check` passed.

Note: an earlier suite attempt was run concurrently with `next build`, causing the web server to see `.next` mid-rebuild and return connection-refused errors. The serialized rerun after the build passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. work authorization,
3. live task creation,
4. hosted parity claims,
5. SQL file creation,
6. SQL execution,
7. schema migration,
8. Supabase writes,
9. adapter implementation,
10. approval persistence,
11. import mutation,
12. live service calls,
13. Render redeploy,
14. Vercel promotion,
15. service creation,
16. DNS, auth, ingress, or secret changes,
17. fixture replay,
18. workbook macro execution,
19. workbook writeback,
20. assignment mutation,
21. schedule mutation,
22. status mutation,
23. autonomous AI business-state mutation.

## Next Recommended Move

Use this export when PM, lead, or field context needs to be shared before production execution tracking exists. The next product slice should either add another local review reducer that shortens Jason's day-to-day process, or explicitly admit a later persistence/write lane only after hosted parity, schema authority, and approval persistence authority are packet-approved.
