# PM Lane 024 Handoff - Workfront Decision-History Drillthrough

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-024`
Scope: PM workfront decision-history drillthrough ergonomics

## Summary

PM Lane 024 adds a focused read-only product ergonomics path from the PM workfront into the existing PM approval Decision History route. Rows with decision entity context now expose `Review history`, routing to `/pm-review/approval?screen=history&historySearch=<entity id>` with return context back to `/pm-review/workfront`.

The link uses decision entity IDs already available in the workfront row context: `primary_blocking_issue_id`, `returnable_issue_id`, `last_pm_decision.entity_id`, and `blocking_issues[].id`. Rows without decision entity context do not receive the history drillthrough affordance.

PM Lane 012 remains the separate Render-authenticated hosted parity gate. This lane is local frontend-only and does not claim hosted PM live-data proof.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/pm-review/workfront/page.tsx`
2. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/pm-review/approval/page.tsx`
3. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`
4. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
5. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-024-workfront-decision-history-drillthrough.json`
6. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-024-workfront-decision-history-drillthrough-handoff.md`

The implementation adds:

1. `workfrontDecisionHistoryLink(row)` using the existing route-navigation helper
2. `Review history` link rendering for workfront rows with decision entity context
3. `historySearch` URL support for the approval Decision History screen
4. a stable `Decision history search` textbox label for browser proof
5. exact href proof for `screen=history`, `historySearch`, `returnTo`, and `returnLabel`
6. click-through proof into approval Decision History with prefilled search
7. proof that the explicit history screen still performs a full decision-history read
8. return-to-workfront proof from the approval route
9. zero-mutation assertion before the explicit PM disposition path

## Orchestration Notes

Read-only product scout `019e2ccb-1840-7210-ba9a-8efef68972c8` confirmed `historySearch` is the correct frontend-only route convention, approval history can initialize the existing search input from the URL, and the explicit history screen should keep its full-history read rather than becoming a scoped detail read.

Read-only governance scout `019e2ccb-188f-7c61-b0de-96cae456b33a` confirmed PM Lane 024 should stay a local frontend-only PM runtime lane, with no backend, SQL, hosted, Render, auth, ingress, or AI helper scope.

The coordinator executed the focused product/test update locally while scouts ran in parallel, preserving disjoint orchestration roles: scouts for read-only product and governance review, coordinator for patch, validation, publication, and closeout.

## Validation

Passed:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build

$env:CI='1'
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.pm-workfront.smoke.spec.ts

$env:CI='1'
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.static-surfaces.smoke.spec.ts

$env:CI='1'
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.approval-context.smoke.spec.ts

corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck

git diff --check
```

Result:

```text
PM workfront: 1 passed
Static surfaces: 1 passed
Approval context: 4 passed
```

One parallel Playwright attempt collided on port `3030`; the static-surfaces proof passed in that attempt, and the approval-context proof passed when rerun sequentially.

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

The next local PM product slice can continue improving read-only PM review context or tighten browser proof around already-promoted PM navigation, but it should remain separate from the hosted Render parity gate.
