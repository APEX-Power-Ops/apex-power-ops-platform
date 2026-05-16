# PM Lane 043 Handoff - Project Miner Import Intake Workbench

Date: 2026-05-15
Status: Locally executed, read-only
Scope: Consolidated Project Miner PM intake workbench before approval persistence or import mutation

## Executive Summary

PM Lane 043 adds a read-only PM workbench route:

```text
/pm-review/import-intake
```

The route gives Jason one day-to-day starting point for Project Miner intake by combining the current import candidate, admission plan, approval contract, and approval storage plan. It does not approve, persist, import, submit, assign, schedule, change status, deploy, or mutate production state.

## What Changed

Operations-web:

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
3. `apps/operations-web/app/page.tsx`
4. `apps/operations-web/app/pm-review/page.tsx`
5. `apps/operations-web/app/pm-review/import-candidate/page.tsx`
6. `apps/operations-web/app/pm-review/import-admission-plan/page.tsx`
7. `apps/operations-web/app/pm-review/import-approval-readiness/page.tsx`

Docs and governance:

1. `PROJECT_STATUS.md`
2. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
3. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
4. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
5. `ops/agents/packets/draft/2026-05-15-pm-lane-043-project-miner-intake-workbench.json`

## New UI Route

```text
/pm-review/import-intake
```

The page reads only:

```text
GET /api/v1/reads/project-import-candidate
GET /api/v1/reads/project-import-admission-plan
GET /api/v1/reads/project-import-approval-contract
GET /api/v1/reads/project-import-approval-storage-plan
```

It shows:

1. candidate id, version, authority, project name, location, drawings, and source freshness,
2. proposed workpackage, task, apparatus, warning, blocker, and human-decision counts,
3. candidate warnings and required PM decisions,
4. workflow gates from source intake through future import,
5. admission plan target rows and no-go count,
6. approval contract authority and future mutation route,
7. approval storage table `seam.pm_import_candidate_approvals`,
8. hosted-parity status pointing back to PM Lane 041A/041B,
9. merged not-allowed-now guardrails.

## Sidecar Result

A read-only sidecar inspected the existing PM import routes and browser smokes. It made no edits, staging, commits, deployments, or live service calls.

The sidecar recommendation was accepted: use `/pm-review/import-intake` instead of a more bespoke route name, because it fits the existing `/pm-review/import-*` cluster while staying review-only.

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

Focused PM intake Playwright smokes:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Result:

```text
4 passed
```

The new smoke proves:

1. all four PM intake read seams are called exactly once,
2. zero mutation routes are called,
3. the future approval table and route render,
4. hosted parity and approval persistence remain future/not-admitted states,
5. no `Approve`, `Persist`, `Submit`, or `Import` button is present.

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

Keep PM Lane 041A/041B as the hosted parity lanes. Use `/pm-review/import-intake` locally as the consolidated PM intake starting point while hosted operations-web and Render parity are refreshed by authenticated executors.
