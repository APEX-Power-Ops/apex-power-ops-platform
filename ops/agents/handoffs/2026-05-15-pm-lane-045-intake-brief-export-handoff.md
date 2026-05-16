# PM Lane 045 Handoff - Project Miner PM Intake Brief Export

Date: 2026-05-15
Status: Locally executed, read-only
Scope: Local Markdown PM intake brief export from `/pm-review/import-intake`

## Executive Summary

PM Lane 045 adds a local-only export action to the Project Miner intake workbench:

```text
Export PM Brief
```

The button downloads a Markdown brief generated from the already-loaded four read seams. It is designed to reduce Jason's handoff burden by creating a concise, portable review artifact for PM review or executor context without adding approval, persistence, import, backend routes, hosted deployment, or production writes.

## What Changed

Operations-web:

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`

Docs and governance:

1. `PROJECT_STATUS.md`
2. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
3. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
4. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
5. `ops/agents/packets/draft/2026-05-15-pm-lane-045-intake-brief-export.json`

## Export Behavior

The export is generated entirely in the browser from:

```text
GET /api/v1/reads/project-import-candidate
GET /api/v1/reads/project-import-admission-plan
GET /api/v1/reads/project-import-approval-contract
GET /api/v1/reads/project-import-approval-storage-plan
```

The downloaded filename is derived from the candidate id:

```text
pm-import-candidate-miner-temp-power-intake-brief.md
```

The brief includes:

1. candidate id, version, authority, project, location, drawings, and source fingerprint,
2. proposed workpackage, task, apparatus, warning, blocker, and decision counts,
3. warning summaries,
4. required PM decisions,
5. workflow gates,
6. admission and approval authority,
7. future approval table and route,
8. target rows,
9. not-allowed-now guardrails.

The brief explicitly states that it is not approval, persistence, import, assignment, schedule, status, or production state.

## Sidecar Result

A read-only sidecar confirmed the safest scope: client-only Markdown export, no hosted smoke expansion, no API export, no clipboard dependency, and no write path.

The sidecar recommended asserting downloaded content in the browser smoke, and that recommendation was accepted.

## Validation

Commands run from:

```text
C:/APEX Platform/apex-power-ops-platform
```

Operations-web typecheck:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
```

Result:

```text
passed
```

Operations-web production build:

```powershell
corepack pnpm --filter @apex/operations-web build
```

Result:

```text
passed; route output included /pm-review/import-intake
```

Focused import-intake smoke:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Result:

```text
1 passed
```

Focused PM intake smoke suite:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Result:

```text
4 passed
```

The strengthened import-intake smoke proves:

1. all four PM intake reads are called exactly once,
2. zero mutation routes are called,
3. no `Approve`, `Persist`, `Submit`, or `Import` button is present,
4. the Markdown brief downloads with the expected candidate-derived filename,
5. the downloaded brief includes source freshness, warning code, future approval route, and not-allowed-now guardrails,
6. the page reports that the brief was prepared without a server write.

Note: an initial Playwright attempt failed because it was run in parallel with `next build`, causing `next start` to race before the production build existed. The sequential reruns after build completed passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. hosted deployment,
3. Vercel promotion,
4. Render redeploy,
5. approval persistence,
6. import mutation,
7. schema migration,
8. SQL write,
9. live database write,
10. workbook macro execution,
11. workbook writeback,
12. service admission,
13. auth or ingress widening,
14. assignment mutation,
15. schedule mutation,
16. status mutation,
17. autonomous AI business-state mutation.

## Next Recommended Move

Keep PM Lane 041A/041B as the hosted parity lanes. Locally, the next product slice can either harden the brief into a reviewer checklist or prepare the approval-persistence schema/adapter packet only after hosted parity is green or precisely classified.
