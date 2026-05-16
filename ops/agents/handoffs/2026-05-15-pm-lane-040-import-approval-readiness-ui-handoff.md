# PM Lane 040 Handoff - Import Approval Readiness PM UI Review

Date: 2026-05-15
Status: Locally executed, read-only
Scope: Project Miner import approval contract and storage-plan UI before approval persistence or import mutation

## Executive Summary

PM Lane 040 adds a read-only PM-facing route for approval readiness:

```text
/pm-review/import-approval-readiness
```

The route combines the current approval-persistence contract and approval storage decision in one inspection surface. It does not approve, persist, import, submit, assign, schedule, change status, or mutate production state.

## What Changed

Operations-web:

1. `apps/operations-web/app/pm-review/import-approval-readiness/page.tsx`
2. `apps/operations-web/tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts`
3. `apps/operations-web/app/pm-review/import-candidate/page.tsx`
4. `apps/operations-web/app/pm-review/import-admission-plan/page.tsx`
5. `apps/operations-web/app/page.tsx`
6. `apps/operations-web/scripts/smoke-hosted-routes.mjs`
7. `apps/operations-web/scripts/smoke-pm-intake-hosted.mjs`

Docs and governance:

1. `PROJECT_STATUS.md`
2. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
3. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
4. `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
5. `ops/agents/packets/draft/2026-05-15-pm-lane-040-import-approval-readiness-ui.json`

## New UI Route

```text
/pm-review/import-approval-readiness
```

The page reads only:

```text
GET /api/v1/reads/project-import-approval-contract
GET /api/v1/reads/project-import-approval-storage-plan
```

It shows:

1. approval contract and candidate identity,
2. required fields and permitted decisions,
3. expected values and decision payload template,
4. human-acceptance policy and non-overridable blocked checks,
5. validation matrix,
6. future mutation contract,
7. selected table `seam.pm_import_candidate_approvals`,
8. future route `/api/v1/mutations/project-import-approvals`,
9. record lifecycle and adapter requirements,
10. recommended columns and constraints,
11. rejected storage shortcuts,
12. future admission sequence and guardrails.

## Sidecar Result

The read-only sidecar completed without edits, staging, commit, deployment, live-service access, or tests.

Its key recommendation was accepted: create a separate route named `/pm-review/import-approval-readiness` instead of touching `/pm-review/approval`, because `/pm-review/approval` already owns current PM approval mutation workflows. The new route stays inspection-only and has no forms, local drafts, approval controls, persistence controls, import controls, or production write authority.

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
passed; route output included /pm-review/import-approval-readiness
```

Focused PM intake Playwright smokes:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts
```

Result:

```text
3 passed
```

The new smoke proves:

1. the approval-readiness page calls both read seams exactly once,
2. no mutation route is called,
3. no `Approve`, `Persist`, `Import`, or `Submit` button is present,
4. the future table, route, authorities, storage shortcuts, and guardrail text render.

Note: an earlier Playwright run failed because it was run in parallel with `next build`, causing `next start` to race before `.next` existed. The sequential rerun after the successful build passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. approval persistence,
3. import mutation,
4. schema migration,
5. SQL write,
6. live database write,
7. localStorage or browser-draft approval capture,
8. approval, persist, import, submit, or production write controls,
9. workbook macro execution,
10. workbook writeback,
11. Render deployment,
12. Vercel promotion,
13. service admission,
14. auth or ingress widening,
15. assignment mutation,
16. schedule mutation,
17. status mutation,
18. autonomous AI business-state mutation.

## Next Recommended Move

Keep PM Lane 037 active for hosted Render parity and promote operations-web only when a hosted UI tranche is explicitly opened. The next product slice should be a dedicated approval persistence schema and adapter admission packet only after hosted reads are current or the Render blocker is precisely classified.
