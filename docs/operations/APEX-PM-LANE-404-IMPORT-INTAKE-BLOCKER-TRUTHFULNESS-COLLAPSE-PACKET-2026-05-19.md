# APEX PM Lane 404 - Import-Intake Blocker Truthfulness Collapse Packet

Date: 2026-05-19

Status: Executed and accepted closed.

Decision label:

`PM_IMPORT_INTAKE_BLOCKER_TRUTHFULNESS_COLLAPSE`

## Purpose

PM Lane 404 closes the next bounded blocker-review slice after PM Lane 403 reconciled downstream post-approval prerequisites.

The remaining local inconsistency was in the top-level blocker model itself: once the current candidate already has an accepted approval record, the workbench should no longer present browser approval submission and approval-row creation as active blockers.

## Root Cause

The route had become truthful in downstream export and prerequisite copy, but the controlling blocker builders still counted legacy approval prerequisites as current blocked work.

That stale posture appeared in:

1. approval persistence readiness gates,
2. the PM operating queue,
3. the PM intake snapshot authority item,
4. blocker-count summaries reused by Start Here and Daily Script.

## Change Surface

Product files changed:

1. `apps/operations-web/app/pm-review/import-intake/page.tsx`

Repo governance files changed:

1. `PROJECT_STATUS.md`
2. `docs/operations/APEX-PM-LANE-404-IMPORT-INTAKE-BLOCKER-TRUTHFULNESS-COLLAPSE-PACKET-2026-05-19.md`
3. `ops/agents/handoffs/2026-05-19-pm-lane-404-import-intake-blocker-truthfulness-collapse-closeout-handoff.md`

## Implementation

`/pm-review/import-intake` now uses the accepted-approval-state helpers to collapse obsolete approval blockers out of the top-level blocker model.

Implemented behavior:

1. browser approval submit authority becomes `ready` when the readback already shows an accepted current-candidate approval record,
2. PM operating queue items for browser approval submission and approval-row creation become completed historical prerequisites in that accepted state,
3. the intake snapshot authority item stops reporting the approval-persistence boundary as blocked when the only real remaining boundary is import mutation authority,
4. blocker-count summaries used by Start Here and Daily Script now fall with that accepted post-approval state instead of overstating approval-side blockers.

## Validation

Focused validation passed:

```text
corepack pnpm --dir apps/operations-web typecheck
tsc --noEmit

corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
1 passed
```

## Boundary

This lane does not:

1. add or change backend routes,
2. wire browser approval POST,
3. create or mutate approval rows,
4. admit project import or any downstream write authority,
5. change schema, payload shape, or hosted services,
6. widen assignment, schedule/status, field, production, customer, or finance scope,
7. perform autonomous AI business-state mutation.

## Result

The import-intake workbench now collapses already-satisfied approval prerequisites out of its current blocker model. In the accepted post-approval state, the real next blocker shown to PM is project import mutation authority, not browser approval submission or first approval-row creation.