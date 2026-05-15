# PM Lane 013 Handoff - Workfront Schedule Drillthrough

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-013`
Scope: PM workfront frontend drillthrough to promoted schedule surfaces

## Summary

PM Lane 013 adds row-level schedule drillthrough from `/pm-review/workfront` into the existing promoted PM routes:

1. `/pm-review`
2. `/pm-review/schedule`
3. `/pm-review/tracer`
4. `/pm-review/variance`

This is a frontend-only product slice. It does not depend on the hosted mutation-seam being repaired, and it does not claim hosted PM live-data proof. PM Lane 012 remains the separate Render-authenticated hosted parity gate.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/pm-review/workfront/page.tsx`
2. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`
3. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
4. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-013-workfront-schedule-drillthrough.json`
5. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-013-workfront-schedule-drillthrough-handoff.md`

Workfront rows now accept optional `task_id` context and build drillthrough links with the existing route helper:

```text
C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/pm-review/route-navigation.ts
```

For a row with `task_id=task-002` and `task_name=Switchgear Sweep`, the generated links are:

```text
/pm-review?focusTaskId=task-002&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM+workfront
/pm-review/schedule?focusTaskId=task-002&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM+workfront
/pm-review/tracer?taskId=task-002&taskLabel=Switchgear+Sweep&maxDepth=10&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM+workfront
/pm-review/variance?projectId=stack-dc&focusTaskId=task-002&returnTo=%2Fpm-review%2Fworkfront&returnLabel=PM+workfront
```

## Orchestration Notes

Read-only scout `019e2c83-d777-7941-bcde-6b443e6a003d` independently checked the workfront row shape, route helper conventions, UI insertion point, and focused test assertions.

The coordinator executed the implementation locally and kept PM Lane 013 separate from PM Lane 012 so hosted deployment repair and local product work remain auditable as separate lanes.

## Validation

Passed:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck

corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build

$env:CI='1'
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.pm-workfront.smoke.spec.ts
```

Result:

```text
1 passed
```

The first Playwright attempt failed against a stale reused `next start` production server on port `3030`. After rebuilding operations-web and forcing a fresh server path with `CI=1`, the focused proof passed.

## Guardrails Preserved

1. No backend endpoint change.
2. No package script change.
3. No SQL or schema migration.
4. No live database write.
5. No service admission.
6. No auth or ingress widening.
7. No assignment mutation.
8. No schedule mutation.
9. No Operations Visibility reopening.
10. No Vercel promotion.
11. No Render deployment action.
12. No autonomous AI business-state mutation.

## Next Bounded Move

PM Lane 012 should still execute on a Render-authenticated surface to restore hosted mutation-seam parity and rerun hosted PM live-data proof.

After that gate closes or produces a precise log-backed blocker, the next local product slice is PM Lane 014: approval escalation scoped history in `apps/operations-web/app/pm-review/approval/page.tsx` with focused approval-context Playwright proof.
