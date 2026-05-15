# PM Lane 021 Handoff - Workfront Escalation Approval Drillthrough

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-021`
Scope: PM workfront escalation-to-approval drillthrough ergonomics

## Summary

PM Lane 021 adds a focused product ergonomics path from the PM workfront into the existing PM approval escalation detail route. Rows with an active escalated issue now expose `Review escalation`, routing to `/pm-review/approval?screen=escalations&detailId=<issue id>` with return context back to `/pm-review/workfront`.

The link is gated on an active escalated issue from `returnableIssue(row)`. It does not use stale `primary_blocking_issue_id` fallback context, so the affordance disappears after PM returns the issue to lead review.

PM Lane 012 remains the separate Render-authenticated hosted parity gate.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/pm-review/workfront/page.tsx`
2. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`
3. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
4. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-021-workfront-escalation-approval-drillthrough.json`
5. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-021-workfront-escalation-approval-drillthrough-handoff.md`

The implementation adds:

1. `workfrontEscalationReviewLink(issueId)` using the existing route-navigation helper
2. `Review escalation` link rendering for rows with an active escalated issue
3. approval-read mocks inside the focused workfront smoke
4. click-through proof into active approval escalation detail
5. return-to-workfront proof from the approval route
6. zero-mutation assertion before the explicit PM disposition
7. stale-link absence proof after return-to-lead clears the active escalation

## Orchestration Notes

Read-only scout `019e2cb4-f52b-7770-bab0-2bc8ee56b374` confirmed PM Lane 021 should remain a PM-runtime frontend ergonomics packet, not an AI/helper lane and not a hosted parity lane.

Read-only scout `019e2cb4-daa4-7952-a761-412a978ebc39` confirmed the link should be gated on an actual active escalated/returnable issue, not generic primary blocking issue context.

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

One parallel Playwright attempt collided on port `3030`; the approval-context proof passed when rerun sequentially.

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

The next local PM product slice can add another small PM review ergonomics path or tighten read-only live-data proof surfaces, but it should remain separate from the hosted Render parity gate.
