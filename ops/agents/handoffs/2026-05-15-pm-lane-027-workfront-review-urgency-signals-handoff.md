# PM Lane 027 Handoff - Workfront Review-Urgency Signals

Date: 2026-05-15
Status: Completed
Packet: `2026-05-15-pm-lane-027`
Scope: PM workfront scan-context ergonomics

## Summary

PM Lane 027 adds compact, always-visible PM signal badges to `/pm-review/workfront`. The signal strip uses existing read-only workfront and submitted snapshot context so PM can scan urgency before choosing a drillthrough or disposition action.

Signals include `Needs PM disposition`, `Stale blocker`, `Returned to lead`, `Ready for PM review`, `Submitted snapshot`, `Owner unassigned`, and open issue count where applicable. They render as non-interactive row context under owner/workpackage/checklist metadata and above schedule drillthrough links.

PM Lane 012 remains the separate Render-authenticated hosted parity gate. This lane is local frontend-only and does not claim hosted PM live-data proof.

## Implementation

Changed files:

1. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/app/pm-review/workfront/page.tsx`
2. `C:/APEX Platform/apex-power-ops-platform/apps/operations-web/tests/browser-shell.pm-workfront.smoke.spec.ts`
3. `C:/APEX Platform/apex-power-ops-platform/PROJECT_STATUS.md`
4. `C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-027-workfront-review-urgency-signals.json`
5. `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-15-pm-lane-027-workfront-review-urgency-signals-handoff.md`

The implementation adds:

1. typed `ReviewSignal` rows derived from existing PM workfront fields
2. signal derivation from `lens_tags`, `returnable_issue_id`, `latest_pm_followup_note`, `owner_name`, open issue counts, PM-review posture, and submitted snapshot context
3. signal tone styling for attention, warning, ok, and neutral context
4. a row-level `PM signals for <row>` region containing only non-interactive badge text
5. proof for blocked, PM-review, and unassigned row signal rendering
6. proof that signal regions contain no links or buttons
7. proof that the initial PM workfront render does not fetch decision history
8. proof that the existing return-to-lead path updates signals from `Stale blocker` to `Returned to lead`

## Orchestration Notes

Read-only product scout `019e2ce1-68b4-7533-bd45-1e403fbf72e1` confirmed the strongest Lane 027 slice was an always-visible, read-only PM signal strip using existing row and snapshot fields. The scout explicitly kept the mutation-adjacent disposition-history panel separate.

Read-only governance scout `019e2ce1-68f0-7043-9e5b-e3d0a09ea8b9` supplied the local frontend-only scan-context packet and closeout shape, preserving PM Lane 012 as the hosted Render parity gate.

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
2. No read API shape change.
3. No approval route change.
4. No approval mutation behavior change.
5. No package script change.
6. No SQL or schema migration.
7. No live database write.
8. No seed or fixture replay.
9. No service admission.
10. No auth or ingress widening.
11. No assignment mutation.
12. No schedule mutation.
13. No Operations Visibility reopening.
14. No Vercel promotion.
15. No Render deployment action.
16. No AI helper mutation.
17. No AI service admission widening.
18. No autonomous AI business-state mutation.

## Next Bounded Move

PM Lane 012 should still execute on a Render-authenticated surface to restore hosted mutation-seam parity and rerun hosted PM live-data proof.

The next local PM product slice can improve PM workfront context density or extract some repeated presentation helpers, but it should remain separate from the hosted Render parity gate.
