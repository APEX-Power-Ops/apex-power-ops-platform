# PM Lane 371 - Project Tracker Cache Lineage And UI Warning Alignment Closeout Handoff

## Outcome

Executed PM Lane 371 as a bounded PM-surface alignment slice and completed the hosted/public verification follow-through.

Selected outcome: `PM_PROJECT_TRACKER_CACHE_LINEAGE_AND_UI_WARNING_ALIGNMENT_HOSTED_VERIFIED_CURRENT`

The PM warning UI and exports now explain the Project Tracker issue as a macro-built `All_Tasks` cache/build break, the repo carries a packet that maps the failing columns back to the workbook lineage, and the hosted/public PM routes now render that richer explanation on the live domain.

## Scope

- Added cache-break warning fields to the local PM review route types.
- Updated `/pm-review/import-intake` to show pattern detail, workbook lineage modules, row/cell detail, and affected columns in Exception Review.
- Updated the intake exports so warning bundles carry the same workbook-cache explanation outside the browser card.
- Updated `/pm-review/import-candidate` to show the same pattern detail and workbook-lineage modules in Warning Review.
- Refreshed the focused Playwright fixtures to use the `all_tasks_formula_cache_break` wording.
- Authored the PM Lane 371 no-live packet documenting the failing `All_Tasks` columns, the `BuildAll` / `PopulateAllTasks_FromSheets` flow, the `Notes` anomaly, and the expected rebuild sequence.
- Verified the hosted operations-web proxy now returns the full warning payload and that the hydrated public DOM on both PM routes renders `Pattern detail`, `Workbook lineage modules`, and the macro-remediation text.

## Files Changed

- `apps/operations-web/app/pm-review/import-intake/page.tsx`
- `apps/operations-web/app/pm-review/import-candidate/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `apps/operations-web/tests/browser-shell.pm-import-candidate.smoke.spec.ts`
- `docs/operations/APEX-PM-LANE-371-PROJECT-TRACKER-ALL-TASKS-CACHE-LINEAGE-AND-UI-WARNING-ALIGNMENT-NO-LIVE-PACKET-2026-05-19.md`
- `PROJECT_STATUS.md`

## Validation

Focused validation passed:

```text
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts tests/browser-shell.pm-import-candidate.smoke.spec.ts
2 passed

corepack pnpm --dir apps/operations-web typecheck
pass

Invoke-RestMethod https://operations.apexpowerops.com/api/v1/reads/project-import-candidate
returned formula_error_pattern=all_tasks_formula_cache_break,
formula_error_pattern_detail, and formula_error_vba_lineage_modules=BuildAll,PopulateAllTasks_FromSheets

Playwright browser verification against https://operations.apexpowerops.com/pm-review/import-candidate
and https://operations.apexpowerops.com/pm-review/import-intake
confirmed the hydrated DOM renders Pattern detail, Workbook lineage modules,
BuildAll, and PopulateAllTasks_FromSheets on both hosted routes
```

## Guardrails Preserved

- No workbook macro execution.
- No workbook writeback.
- No approval/import/assignment/schedule/status mutation.
- No field, customer, finance, or production write authority widening.
- No autonomous AI business-state mutation.

## Notes

The new packet captures one important workbook-lineage nuance: `PopulateAllTasks.bas` currently writes `All_Tasks.Notes` as blank, so a uniform `#REF!` in that column is evidence of stale workbook formula residue or workbook-version drift, which further supports the cache/build-break classification instead of a missing-source interpretation.

## Next Bounded Move

Lane 371 no longer needs a publication/parity follow-up. Any next move should be a new downstream PM governance slice, not more warning-publication verification.