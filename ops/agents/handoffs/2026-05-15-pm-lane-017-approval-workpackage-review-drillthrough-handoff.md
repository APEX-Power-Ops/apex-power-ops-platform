# PM Lane 017 Handoff - Approval Workpackage Review Drillthrough

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-017`
Scope: PM approval workpackage-review drillthrough to promoted review routes

## Summary

PM Lane 017 adds focused-task drillthrough from `/pm-review/approval?screen=wp-review` into the existing promoted PM routes:

1. `/pm-review/tracer`
2. `/pm-review/schedule`
3. `/pm-review`
4. `/pm-review/variance`

The workpackage-review detail screen now matches the task, snapshot, and escalation operational-navigation shape. The workpackage decision-history context remains scoped to the workpackage id, not the focused task id.

This is a frontend-only product slice. It does not depend on the hosted mutation-seam being repaired, and it does not claim hosted PM live-data proof. PM Lane 012 remains the separate Render-authenticated hosted parity gate.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/pm-review/approval/page.tsx`
2. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.approval-context.smoke.spec.ts`
3. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
4. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-017-approval-workpackage-review-drillthrough.json`
5. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-017-approval-workpackage-review-drillthrough-handoff.md`

`WorkPackageReview` now receives and uses the existing approval-shell callbacks:

1. `onTraceTask`
2. `onViewSchedule`
3. `onViewDrivers`
4. `onViewVariance`

The workpackage detail panel renders a `Related Task Actions` card when `pickFocusedTask(workPackageTasks)` returns a task. That keeps empty workpackages guarded while using the existing focused-task rule: first non-complete task, then first task fallback.

The focused approval-context browser smoke now includes a workpackage-review deep link fixture for `wp-017` and proves:

1. scoped history read uses `entity_id=wp-017&limit=25`
2. no unscoped decision-history read occurs on the workpackage detail screen
3. complete task appears first in fixture data and the active task is still selected for drillthrough
4. compact decision-history context renders for the workpackage
5. all workpackage action controls are visible
6. tracer handoff carries `taskId=task-017`, `taskLabel=Focused WP Task`, `maxDepth=10`, and a return link to PM work package review

## Orchestration Notes

Read-only scout `019e2c9c-dd6b-7023-b474-3338413b5906` confirmed the smallest implementation shape: reuse the existing approval callbacks, keep decision history scoped to `wp-017`, prove focused-task selection with complete-first fixture data, and leave fuller schedule/drivers/variance URL assertions as a later coverage extension.

The coordinator executed the implementation locally while the scout ran in parallel, preserving disjoint orchestration roles: scout for read-only placement/test guidance, coordinator for patch, validation, publication, and closeout.

## Validation

Passed:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck

corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build

$env:CI='1'
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.approval-context.smoke.spec.ts

git diff --check
```

Result:

```text
4 passed
```

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

The next local PM product slice can extend approval-context route-return coverage for schedule, drivers, and variance, now that task and workpackage review both expose the same action set.
