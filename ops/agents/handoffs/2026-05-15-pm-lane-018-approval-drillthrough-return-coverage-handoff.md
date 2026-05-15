# PM Lane 018 Handoff - Approval Drillthrough Return Coverage

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-018`
Scope: PM approval drillthrough return-link proof for task and workpackage review

## Summary

PM Lane 018 closes the remaining local proof gap from PM Lanes 016 and 017: task-review and workpackage-review already expose Schedule, Drivers, and Variance drillthrough, and this lane proves those promoted routes preserve the correct approval return links.

This is a test-only lane. Product code already had the expected route behavior, so no product code was changed.

PM Lane 012 remains the separate Render-authenticated hosted parity gate.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.approval-context.smoke.spec.ts`
2. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
3. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-018-approval-drillthrough-return-coverage.json`
4. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-018-approval-drillthrough-return-coverage-handoff.md`

The focused approval-context smoke now has:

1. shared task-review fixture setup
2. shared workpackage-review fixture setup
3. a route-return assertion helper for approval drillthrough
4. task-review return-link proof for Open Schedule, Open Drivers, and Open Variance
5. workpackage-review return-link proof for Open Schedule, Open Drivers, and Open Variance

The existing tracer assertions remain unchanged because tracer intentionally includes `focusTaskId` and `taskLabel` in its return route. Schedule, Drivers, and Variance return to the approval detail route without those focus params.

## Orchestration Notes

Read-only scout `019e2ca1-7322-7513-ad89-4dcc1ff12d22` confirmed this could stay test-only and recommended a small route-return helper with regex-based URL assertions to avoid query-order brittleness.

The coordinator executed the focused smoke update locally while the scout ran in parallel, preserving disjoint orchestration roles: scout for read-only proof design, coordinator for patch, validation, publication, and closeout.

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

1. No product code change.
2. No backend endpoint change.
3. No package script change.
4. No SQL or schema migration.
5. No live database write.
6. No service admission.
7. No auth or ingress widening.
8. No assignment mutation.
9. No schedule mutation.
10. No Operations Visibility reopening.
11. No Vercel promotion.
12. No Render deployment action.
13. No autonomous AI business-state mutation.

## Next Bounded Move

PM Lane 012 should still execute on a Render-authenticated surface to restore hosted mutation-seam parity and rerun hosted PM live-data proof.

The next local PM product slice can return to workfront/approval ergonomics, or add broader route-return proof around snapshot and escalation contexts if that coverage becomes useful.
