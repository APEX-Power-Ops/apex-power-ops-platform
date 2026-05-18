# PM Lane 363 - Project Miner Temp Power Import-Intake Durable Task-Plan Status Closeout Handoff

## Outcome

Executed and locally validated PM Lane 363 as a bounded import-intake visibility slice.

Selected outcome: `PM_INTAKE_TASK_PLAN_STATUS_SURFACED_LOCAL_CURRENT`

`/pm-review/import-intake` now reflects the planning-only durable task-plan baseline already admitted in PM Lanes 361 and 362.

## Scope

- Added `taskPlanStatus` to the import-intake workbench packet read path.
- Wired `GET /api/v1/reads/project-import-task-plan-status` into the main page render scope.
- Added a `Durable Task Plan Status` card under the existing `Approval Status Context` section.
- Added durable task-plan status readback lines to the browser-local PM Brief export.
- Updated the focused Playwright smoke to mock the new read seam and assert the added status card.
- Reconciled the smoke with the current Shell route-link count and current `Project overview` route target.

## Files Changed

- `apps/operations-web/app/pm-review/import-intake/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `PROJECT_STATUS.md`

## Validation

Focused validation passed:

```text
runTests apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
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

The first focused validation exposed a local render bug: the new task-plan status card referenced `taskPlanStatus` before the main page component bound `packet?.taskPlanStatus`. That was repaired immediately, then the same smoke was rerun until green.

The same smoke also surfaced existing route-link expectation drift after the new task-plan slice was fixed. The test was aligned to the current Shell route set so the focused intake proof now matches current product truth.

## Next Bounded Move

If the PM lane wants the same planning-only baseline surfaced one level higher, the next adjacent read-only slice is to reflect durable task-plan status in `/pm-review/project-overview` without widening any write authority.
