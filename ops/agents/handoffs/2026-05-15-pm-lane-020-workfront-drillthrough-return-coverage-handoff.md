# PM Lane 020 Handoff - Workfront Drillthrough Return Coverage

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-020`
Scope: PM workfront drillthrough return-link proof

## Summary

PM Lane 020 extends the local route-return proof from the approval lane back to the PM workfront. The workfront smoke already asserted generated hrefs; this lane clicks those links into the promoted Drivers, Schedule, Trace, and Variance routes and proves each destination returns to `/pm-review/workfront`.

The lane also covers the taskless unassigned-row edge so optional `task_id` rows do not leak `undefined`, do not include `focusTaskId` or `taskId` where no task exists, and still preserve the PM workfront return link.

This is a test-only lane. Product code already had the expected route behavior, so no product code was changed.

PM Lane 012 remains the separate Render-authenticated hosted parity gate.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`
2. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
3. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-020-workfront-drillthrough-return-coverage.json`
4. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-020-workfront-drillthrough-return-coverage-handoff.md`

The focused PM workfront smoke now has:

1. a shared workfront drillthrough return helper
2. local schedule API fixtures for promoted route destinations
3. Cable Assembly A click-through proof for Drivers, Schedule, Trace, and Variance with focused task context
4. Main Switchgear taskless href proof for Drivers, Schedule, Trace, and Variance
5. Main Switchgear click-through proof that taskless destination routes return to PM workfront
6. preserved read-only advisory, scoped decision-history, lens-filter, mutation sentinel, and PM-clicked return-to-lead proof

## Orchestration Notes

Read-only scout `019e2cae-0f5d-7300-a589-af62d26b4183` identified the taskless workfront-row edge as the highest-value refinement for PM Lane 020.

Read-only scout `019e2cae-282f-7490-96f8-6950946c7021` confirmed the governance shape should remain a PM-runtime packet with only the focused workfront smoke plus status, packet, and handoff surfaces in scope.

The coordinator executed the focused smoke update locally while scouts ran in parallel, preserving disjoint orchestration roles: scouts for read-only product and governance design, coordinator for patch, validation, publication, and closeout.

## Validation

Passed:

```powershell
$env:CI='1'
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec playwright test tests/browser-shell.pm-workfront.smoke.spec.ts

corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck

corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build

git diff --check
```

Result:

```text
1 passed
```

## Publication And Host Parity

Publication and host parity are coordinator closeout duties for the commit containing this handoff:

1. push `clean-main`
2. fast-forward `/home/olares/code/apex/apex-power-ops-platform`
3. verify host head matches the published commit
4. verify host worktree status
5. verify `bash tools/ai/run-minimal-mcp-trio.sh status` returns `{"status":"not-running"}`

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
13. No AI helper mutation.
14. No AI service admission widening.
15. No autonomous AI business-state mutation.

## Next Bounded Move

PM Lane 012 should still execute on a Render-authenticated surface to restore hosted mutation-seam parity and rerun hosted PM live-data proof.

The next local PM product slice can move from proof coverage back into a small PM workfront or approval ergonomics improvement, but it should remain separate from the hosted Render parity gate.
