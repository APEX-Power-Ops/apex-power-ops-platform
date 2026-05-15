# PM Lane 022 Handoff - Workfront Task Review Drillthrough

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-022`
Scope: PM workfront task-review drillthrough ergonomics

## Summary

PM Lane 022 adds a focused product ergonomics path from the PM workfront into the existing PM approval task-review detail route. Rows with `task_id` and PM review posture now expose `Review task`, routing to `/pm-review/approval?screen=task-review&detailId=<task id>` with return context back to `/pm-review/workfront`.

The link is gated on `row.task_id` plus either `readiness === 'pm_review'` or `status === 'awaiting_review'`. Blocked, unassigned, and non-review rows do not receive the task approval drillthrough affordance.

PM Lane 012 remains the separate Render-authenticated hosted parity gate. This lane is local frontend-only and does not claim hosted PM live-data proof.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/pm-review/workfront/page.tsx`
2. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`
3. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
4. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-022-workfront-task-review-drillthrough.json`
5. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-022-workfront-task-review-drillthrough-handoff.md`

The implementation adds:

1. `workfrontTaskReviewLink(row)` using the existing route-navigation helper
2. `Review task` link rendering for rows in PM review with a task id
3. approval task-read mocks inside the focused workfront smoke
4. exact href proof for `screen=task-review`, `detailId`, `returnTo`, and `returnLabel`
5. click-through proof into active approval task review
6. return-to-workfront proof from the approval route
7. zero-mutation assertion before the explicit PM disposition path

## Orchestration Notes

Read-only product scout `019e2cbe-0084-7083-8f3a-87dfbccb79ec` confirmed the implementation should preserve the existing `buildPmRoute` convention, use `detailId` rather than `taskId` for approval detail routing, and gate the link to rows with `task_id` and PM review posture.

Read-only governance scout `019e2cbe-00d2-7411-b5a1-65a81ee72d78` confirmed PM Lane 022 should stay a local frontend-only PM runtime lane, with no backend, SQL, hosted, Render, auth, ingress, or AI helper scope.

The coordinator executed the focused product/test update locally while scouts ran in parallel, preserving disjoint orchestration roles: scouts for read-only product and governance review, coordinator for patch, validation, publication, and closeout.

## Validation

Passed:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build

$env:CI='1'
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.pm-workfront.smoke.spec.ts

$env:CI='1'
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.approval-context.smoke.spec.ts

corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck

git diff --check
```

Result:

```text
PM workfront: 1 passed
Approval context: 4 passed
```

## Publication And Host Parity

Publication and host parity are coordinator closeout duties for the commit containing this handoff:

1. push `clean-main`
2. fast-forward `/home/olares/code/apex/apex-power-ops-platform`
3. verify host head matches the published commit
4. verify host worktree status
5. verify `bash tools/ai/run-minimal-mcp-trio.sh status` returns `{"status":"not-running"}`

## Guardrails Preserved

1. No backend endpoint change.
2. No approval mutation behavior change.
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
13. No AI helper mutation.
14. No AI service admission widening.
15. No autonomous AI business-state mutation.

## Next Bounded Move

PM Lane 012 should still execute on a Render-authenticated surface to restore hosted mutation-seam parity and rerun hosted PM live-data proof.

The next local PM product slice can keep tightening workfront-to-approval ergonomics or broaden read-only PM operator context, but it should remain separate from the hosted Render parity gate.
