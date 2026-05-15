# PM Lane 035 Handoff - Import Admission Plan

Date: 2026-05-15
Status: Complete
Scope: Project Miner Temp Power read-only import-admission plan

## Executive Summary

PM Lane 035 adds the first read-only design surface for the future Project Miner Temp Power import gate.

New read seam:

`GET /api/v1/reads/project-import-admission-plan`

New PM route:

`/pm-review/import-admission-plan`

This tranche defines what a future import packet must prove before it can write. It does not persist approval, import project rows, write Supabase, run workbook macros, write workbook cells, assign work, change status, mutate schedules, or admit autonomous AI business-state action.

## What Changed

Backend:

1. `apps/mutation-seam/app/project_import_admission_plan.py` builds a read-only admission plan from the current import candidate.
2. `apps/mutation-seam/app/routers/reads.py` exposes `GET /api/v1/reads/project-import-admission-plan`.
3. `apps/mutation-seam/tests/test_project_import_admission_plan.py` proves the plan contract and route.

Frontend:

1. `apps/operations-web/app/pm-review/import-admission-plan/page.tsx` renders the admission plan.
2. `apps/operations-web/app/pm-review/import-candidate/page.tsx` links to the admission plan.
3. `apps/operations-web/app/page.tsx` links the route from the governed shell.
4. `apps/operations-web/tests/browser-shell.pm-import-admission-plan.smoke.spec.ts` proves the UI route is read-only.

## Admission Plan Contents

The plan includes:

1. approval record contract,
2. deterministic idempotency plan,
3. candidate shape fingerprint,
4. source stat fingerprint,
5. target row plan,
6. preview-to-import diff checks,
7. no-go checks,
8. future import sequence,
9. not-allowed-now guardrails.

## Orchestration Notes

The coordinator used an internal read-only sidecar scout for PM Lane 035. The scout independently confirmed the GET-only route shape as the safest next lane and called out the same expected components:

1. approval record contract,
2. idempotency key,
3. preview-to-import diff checks,
4. no-go checks,
5. target row plan,
6. read-only UI route,
7. backend and Playwright tests.

The coordinator retained final write ownership, integrated the recommendation, and closed the tranche through validation, packet authoring, and publication.

## Validation

Commands run from `C:/APEX Platform/apex-power-ops-platform` unless noted:

```powershell
.venv/Scripts/python.exe -m pytest apps/mutation-seam/tests/test_project_import_candidate.py apps/mutation-seam/tests/test_project_import_admission_plan.py
```

Result:

`4 passed`

```powershell
corepack pnpm --filter @apex/operations-web typecheck
```

Result:

passed

```powershell
corepack pnpm --filter @apex/operations-web build
```

Result:

passed and listed `/pm-review/import-admission-plan`

```powershell
corepack pnpm exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts
```

Run from:

`C:/APEX Platform/apex-power-ops-platform/apps/operations-web`

Result:

`2 passed`

The first browser-smoke attempts found duplicate text assertions for expected repeated labels. Assertions were tightened and rerun successfully.

## Guardrails Preserved

This packet does not authorize:

1. SQL or schema migration,
2. live database write,
3. production import,
4. approval persistence,
5. workbook writeback,
6. workbook macro execution,
7. Render deployment,
8. Vercel promotion,
9. service admission,
10. auth or ingress widening,
11. package dependency addition,
12. server-side PM note persistence,
13. candidate edit persistence,
14. import mutation,
15. assignment mutation,
16. schedule mutation,
17. status mutation,
18. autonomous AI business-state mutation.

## Recommended Next Packet

PM Lane 036 should prepare the first approval-persistence design or hosted parity gate, depending on operational urgency:

1. If hosted Render parity is still stale, run the hosted parity packet before claiming user-facing proof.
2. If local rehearsal remains acceptable, define approval persistence as a separate read/write boundary without importing rows.
3. Only after approval persistence is admitted should a later packet implement the narrow idempotent import mutation.
