# PM Lane 025 Handoff - Workfront Snapshot-Review Drillthrough

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-025`
Scope: PM workfront snapshot-review drillthrough ergonomics

## Summary

PM Lane 025 adds a focused read-only product ergonomics path from the PM workfront into the existing PM approval `snapshot-review` route. PM-review rows with a submitted progress snapshot for the same `workpackage_id` now expose `Review snapshot`, routing to `/pm-review/approval?screen=snapshot-review&detailId=<snapshot id>` with return context back to `/pm-review/workfront`.

The lane reuses the existing `/api/v1/reads/snapshots` seam and existing approval snapshot-review screen. It adds no backend endpoint and does not change approval mutation behavior.

PM Lane 012 remains the separate Render-authenticated hosted parity gate. This lane is local frontend-only and does not claim hosted PM live-data proof.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/pm-review/workfront/page.tsx`
2. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`
3. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
4. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-025-workfront-snapshot-review-drillthrough.json`
5. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-025-workfront-snapshot-review-drillthrough-handoff.md`

The implementation adds:

1. read-only submitted snapshot loading from `/api/v1/reads/snapshots`
2. shared `rowNeedsPmReview(row)` gating for task, package, and snapshot review affordances
3. submitted snapshot matching by `workpackage_id`
4. `Review snapshot` link rendering only when a PM-review row has a submitted snapshot for the same workpackage
5. route generation for `screen=snapshot-review`, `detailId=<snapshot id>`, `returnTo=/pm-review/workfront`, and `returnLabel=PM workfront`
6. focused PM workfront proof for exact href, click-through, `Progress Snapshot` rendering, scoped snapshot history read, return-to-workfront, and zero mutation calls

## Orchestration Notes

Read-only product scout `019e2cd2-e992-7a01-b17e-e57c381159e9` confirmed `Workfront Snapshot-Review Drillthrough` as the right bounded PM Lane 025 candidate. The scout confirmed approval already supports `snapshot-review`, scoped history, related task actions, and return links, so no approval route or backend change was needed.

Read-only governance scout `019e2cd2-e9cf-7e53-967c-0006a731a9ed` supplied the packet, handoff, validation, and host parity closeout scaffold. The coordinator narrowed the suggested review-action grouping concept to the concrete snapshot-review drillthrough scope to preserve a smaller product increment.

The coordinator executed the focused product/test update locally while scouts ran in parallel, preserving disjoint orchestration roles: scouts for read-only product and governance review, coordinator for patch, validation, publication, and closeout.

## Validation

Passed:

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck

corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build

$env:CI='1'
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.pm-workfront.smoke.spec.ts

$env:CI='1'
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.approval-context.smoke.spec.ts

$env:CI='1'
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.static-surfaces.smoke.spec.ts

git diff --check
```

Result:

```text
PM workfront: 1 passed
Approval context: 4 passed
Static surfaces: 1 passed
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

The next local PM product slice can tighten the visual grouping and scan ergonomics for row-level review actions, but it should remain separate from the hosted Render parity gate.
