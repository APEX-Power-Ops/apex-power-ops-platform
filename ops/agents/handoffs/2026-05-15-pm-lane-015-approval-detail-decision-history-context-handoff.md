# PM Lane 015 Handoff - Approval Detail Decision History Context

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-015`
Scope: PM approval detail read-only decision-history context

## Summary

PM Lane 015 makes the PM Lane 014 scoped decision-history read visible in the approval workflows where PM decisions are made.

The approval route now renders a compact read-only `Decision History` context card on:

1. workpackage review
2. task review
3. snapshot review
4. active escalation detail

The card is display-only and consumes `data.history` from the existing route-derived read. It does not create another fetch, mutation, endpoint, schema change, or runtime dependency.

PM Lane 012 remains the separate Render-authenticated hosted parity gate.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/pm-review/approval/page.tsx`
2. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.approval-context.smoke.spec.ts`
3. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
4. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-015-approval-detail-decision-history-context.json`
5. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-015-approval-detail-decision-history-context-handoff.md`

The new compact renderer shows up to three scoped history rows with:

1. action
2. timestamp
3. state transition
4. actor
5. reason

Stable browser selectors were added:

```text
data-testid="approval-decision-history-context"
data-testid="approval-decision-history-row"
```

The focused approval-context browser smoke now injects decision-history fixture rows and proves the card renders for:

1. `screen=escalations&detailId=issue-001`
2. `screen=snapshot-review&detailId=snap-001`

The same smoke keeps the PM Lane 014 scoped-read assertions and the existing tracer/schedule handoff proof.

## Orchestration Notes

Read-only scout `019e2c92-20ed-7260-b16d-809f2d39ffde` confirmed the smallest implementation shape: one display-only renderer, inserted immediately before mutable decision/disposition controls, using `data.history` from PM Lane 014.

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
2 passed
```

Initial focused Playwright execution before rebuilding operations-web exercised stale built output and failed the new compact-history assertions. After the production build, the focused proof passed.

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

The next local PM product slice can add a task-review focused browser assertion for the same compact history context, or continue approval detail ergonomics with read-only return-path improvements, while preserving the no-new-fetch and no-mutation guardrails.
