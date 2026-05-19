# PM Lane 364 - Project Miner Temp Power Project-Overview Durable Task-Plan Baseline Closeout Handoff

## Outcome

Executed and locally validated PM Lane 364 as a bounded project-overview visibility slice.

Selected outcome: `PM_PROJECT_OVERVIEW_TASK_PLAN_BASELINE_SURFACED_LOCAL_CURRENT`

`/pm-review/project-overview` now reflects the planning-only durable task-plan baseline already admitted in PM Lanes 361 and 362.

## Scope

- Added `taskPlanStatus` to the project-overview packet read path.
- Wired `GET /api/v1/reads/project-import-task-plan-status` into the overview route.
- Added a `Task plan baseline` summary card to the overview posture grid.
- Added an attention item when the durable planning baseline is missing or stale.
- Updated the stage flow so the approval gate now carries current planning-only task-plan-baseline truth and points back to import-candidate review when PM needs to refresh it.
- Added a focused Playwright smoke for `/pm-review/project-overview` that mocks the new read seam and asserts the route stays read-only.

## Files Changed

- `apps/operations-web/app/pm-review/project-overview/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-project-overview.smoke.spec.ts`
- `PROJECT_STATUS.md`

## Validation

Focused validation passed:

```text
runTests apps/operations-web/tests/browser-shell.pm-project-overview.smoke.spec.ts
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

The first local file validation missed a syntax defect in the updated overview stage-card object. A targeted read exposed the missing comma, it was repaired immediately in the same slice, and the route-scoped smoke then passed cleanly.

This tranche keeps the project-overview route aligned with the import-candidate and import-intake surfaces without changing the admitted authority boundary: task-plan persistence remains planning-only context, and approval/import still require separate admitted packets.

## Next Bounded Move

If the current overview change should be visible on the non-local host, the next adjacent tranche is hosted publication of the updated project-overview route after commit/push and Vercel preview readiness are confirmed.