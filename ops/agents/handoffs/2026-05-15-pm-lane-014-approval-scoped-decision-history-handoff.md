# PM Lane 014 Handoff - Approval Scoped Decision History

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-014`
Scope: PM approval frontend read narrowing for decision history

## Summary

PM Lane 014 narrows `/pm-review/approval` decision-history reads for route-scoped approval detail screens. The approval shell now uses the existing mutation-seam query support:

```text
/api/v1/reads/decision-history?entity_id=<detailId>&limit=25
```

for these detail contexts:

1. `task-review`
2. `wp-review`
3. `snapshot-review`
4. `escalations`

The queue and unresolved-detail screens skip decision-history reads because they do not render the history table. The explicit `history` screen preserves the existing full-history read.

This is a frontend-only product slice. It does not depend on the hosted mutation-seam being repaired, and it does not claim hosted PM live-data proof. PM Lane 012 remains the separate Render-authenticated hosted parity gate.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/pm-review/approval/page.tsx`
2. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.approval-context.smoke.spec.ts`
3. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
4. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-014-approval-scoped-decision-history.json`
5. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-014-approval-scoped-decision-history-handoff.md`

The approval route now builds a decision-history endpoint from the active approval `screen` and `detailId`. When a scoped detail screen is active, it fetches only the relevant entity history with `limit=25`; when no history is rendered, it avoids the read.

The approval-context browser smoke now captures `/api/v1/reads/decision-history**` requests and proves:

1. `screen=escalations&detailId=issue-001` reads `entity_id=issue-001&limit=25`.
2. `screen=snapshot-review&detailId=snap-001` reads `entity_id=snap-001&limit=25`.
3. Those deep-link screens do not make an unscoped decision-history request.
4. Existing tracer and schedule handoff behavior still works.

## Orchestration Notes

Read-only scout `019e2c88-c9e7-7813-82a9-48e124ca3819` confirmed the current eager full-history read and the existing backend support for `entity_id` plus `limit`.

The coordinator executed the implementation locally and kept PM Lane 014 separate from PM Lane 012 so hosted deployment repair and local product work remain auditable as separate lanes.

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

Initial focused Playwright attempts before rebuilding operations-web exercised stale built output and correctly failed the new scoped-history assertions. After the production build, the focused proof passed.

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

The next local PM product slice can continue improving approval-context navigation while preserving read-only proof discipline, for example adding detail-level approval history affordances beside the existing task, snapshot, and escalation action panels.
