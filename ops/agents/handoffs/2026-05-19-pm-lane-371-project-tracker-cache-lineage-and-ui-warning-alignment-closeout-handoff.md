# PM Lane 371 - Project Tracker Cache Lineage And UI Warning Alignment Closeout Handoff

## Outcome

Executed and locally validated PM Lane 371 as a bounded PM-surface alignment slice.

Selected outcome: `PM_PROJECT_TRACKER_CACHE_LINEAGE_AND_UI_WARNING_ALIGNMENT_LOCAL_CURRENT`

The PM warning UI and exports now explain the Project Tracker issue as a macro-built `All_Tasks` cache/build break, and the repo now carries a packet that maps the failing columns back to the workbook lineage.

## Scope

- Added cache-break warning fields to the local PM review route types.
- Updated `/pm-review/import-intake` to show pattern detail, workbook lineage modules, row/cell detail, and affected columns in Exception Review.
- Updated the intake exports so warning bundles carry the same workbook-cache explanation outside the browser card.
- Updated `/pm-review/import-candidate` to show the same pattern detail and workbook-lineage modules in Warning Review.
- Refreshed the focused Playwright fixtures to use the `all_tasks_formula_cache_break` wording.
- Authored the PM Lane 371 no-live packet documenting the failing `All_Tasks` columns, the `BuildAll` / `PopulateAllTasks_FromSheets` flow, the `Notes` anomaly, and the expected rebuild sequence.

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
```

## Guardrails Preserved

- No workbook macro execution.
- No workbook writeback.
- No mutation-seam hosted deployment.
- No operations-web hosted promotion.
- No approval/import/assignment/schedule/status mutation.
- No field, customer, finance, or production write authority widening.
- No autonomous AI business-state mutation.

## Notes

The new packet captures one important workbook-lineage nuance: `PopulateAllTasks.bas` currently writes `All_Tasks.Notes` as blank, so a uniform `#REF!` in that column is evidence of stale workbook formula residue or workbook-version drift, which further supports the cache/build-break classification instead of a missing-source interpretation.

## Next Bounded Move

If hosted PM surfaces need this same explanation, the next truthful move is a publication lane that promotes the already-local operations-web wording and verifies hosted mutation-seam is serving the classified warning payload.