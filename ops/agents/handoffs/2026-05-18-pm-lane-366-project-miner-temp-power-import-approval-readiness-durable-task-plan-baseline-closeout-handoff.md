# PM Lane 366 - Project Miner Temp Power Import-Approval-Readiness Durable Task-Plan Baseline Closeout Handoff

## Outcome

Executed and locally validated PM Lane 366 as a bounded approval-readiness visibility slice.

Selected outcome: `PM_IMPORT_APPROVAL_READINESS_TASK_PLAN_BASELINE_SURFACED_LOCAL_CURRENT`

`/pm-review/import-approval-readiness` now reflects the planning-only durable task-plan baseline already admitted in PM Lanes 361 and 362.

## Scope

- Added `taskPlanStatus` to the approval-readiness packet read path.
- Wired `GET /api/v1/reads/project-import-task-plan-status` into the approval-readiness route.
- Added a `Task Plan Baseline` summary card to the approval-readiness posture grid.
- Added a `Durable Task Plan Context` card inside Candidate Review Context so PM can inspect planning-only baseline classification, current-candidate match, authority posture, and persisted row counts before future approval persistence review.
- Extended the focused Playwright smoke for `/pm-review/import-approval-readiness` to mock the new read seam and assert the route remains read-only while rendering the durable planning baseline.

## Files Changed

- `apps/operations-web/app/pm-review/import-approval-readiness/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts`
- `PROJECT_STATUS.md`

## Validation

Focused validation passed:

```text
runTests apps/operations-web/tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts
<summary passed=1 failed=0 />
```

## Guardrails Preserved

- No new mutation route was added.
- No approval persistence authority was widened.
- No project import, assignment, schedule mutation, or status mutation was admitted.
- No finance or customer-billing-delivery authority was widened.
- No source writeback was added.
- No hosted publication or deployment was performed in this slice.
- No autonomous AI business-state mutation was introduced.

## Notes

The first focused smoke failed because the same baseline-summary sentence deliberately rendered in both the top-level posture card and the durable-context card, which triggered a Playwright strict-mode collision. The test was repaired by scoping those assertions to the intended surfaces, and the route-scoped smoke then passed cleanly.

This tranche keeps approval-readiness aligned with import-candidate, import-intake, and project-overview without changing the admitted authority boundary: task-plan persistence remains planning-only context, and approval persistence/import still require separate admitted packets.

## Next Bounded Move

If the updated approval-readiness route should be visible on the non-local host, the next adjacent tranche is hosted publication of the already-validated read-only route after commit/push and Vercel preview readiness are confirmed.