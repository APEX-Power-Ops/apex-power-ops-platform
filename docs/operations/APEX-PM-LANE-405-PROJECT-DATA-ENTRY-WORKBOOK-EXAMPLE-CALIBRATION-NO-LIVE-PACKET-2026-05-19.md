# PM Lane 405 - Project Data Entry Workbook Example Calibration No-Live Packet

Date: 2026-05-19
Status: Local executed, no-live
Scope: Calibrate the Project Data Entry formula-error explanation against the real Garney reference tracker workbook and surface that comparison in the PM warning detail.

## Trigger

The current repo already classified the Project Data Entry issue as an `All_Tasks` cache/build break, but the user directed the lane to refer to the real workbook example at `C:/Users/jjswe/Desktop/Project Miner PM Planning/Garney- Central Mesa Reuse Tracker #677562.xlsm`.

That created one narrow question: does the real Garney workbook reinforce the existing classifier or require a different interpretation?

## Direct Workbook Inspection

Focused read-only inspection returned:

- `Garney- Central Mesa Reuse Tracker #677562.xlsm`
- `Task_Entry` rows: `6`
- `All_Tasks` rows: `143`
- formula-error rows: `0`
- formula-error cells: `0`
- status counts: `COMPLETED=99`, `NOT STARTED=34`

- `RESA Power - Project Data Entry MASTER.xlsm`
- `Task_Entry` rows: `14`
- `All_Tasks` rows: `2857`
- formula-error rows: `234`
- formula-error cells: `3510`
- failing columns: `Drawing`, `Date Due`, `Notes`, `Assessment`, `DATASHEET`, `DATE COMPLETED`, `NOTES2`, `% COMPLETION`, `TASK DELAYS`, `Apparatus Hours`, `Remaining Hours`, `ACTUAL HOURS`, `STATUS`, `AVAILABILITY`, `PRIORITY`

## Outcome

Selected outcome:

`PM_PROJECT_DATA_ENTRY_WORKBOOK_EXAMPLE_CALIBRATION_LOCAL_CURRENT`

The Garney workbook is a clean counterexample, not another broken workbook. That strengthens the existing `all_tasks_formula_cache_break` interpretation instead of contradicting it.

## Change Surface

1. `apps/mutation-seam/app/project_import_candidate.py`
   - Keeps the existing cache-break warning code and message.
   - Appends a clean reference-workbook comparison to `formula_error_pattern_detail` when the Project Data Entry workbook is broken and the reference tracker workbook loads without formula errors.
2. `apps/mutation-seam/tests/test_project_import_candidate.py`
   - Adds a clean reference-tracker fixture.
   - Proves the Project Data Entry warning now carries the comparison detail and that the clean reference tracker does not emit its own formula-error warning.
3. `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
   - Updates the fixture detail and asserts the Garney comparison text appears in Exception Review and the exception-register export.
4. `apps/operations-web/tests/browser-shell.pm-import-candidate.smoke.spec.ts`
   - Updates the fixture detail and asserts the Garney comparison text appears in Warning Review.

## Validation

Commands run:

```text
C:\APEX Platform\apex-power-ops-platform\.venv\Scripts\python.exe -m pytest apps/mutation-seam/tests/test_project_import_candidate.py -q
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts tests/browser-shell.pm-import-candidate.smoke.spec.ts
```

Validation result:

- mutation-seam focused warning tests: pass
- operations-web focused browser smokes: `2 passed`

## Boundary

This lane does not:

1. modify either workbook,
2. execute workbook macros,
3. change the underlying cache-break classifier,
4. add new warning codes,
5. change route authority,
6. admit approval, import, assignment, schedule/status, field, production, customer, or finance writes,
7. deploy hosted services,
8. apply schema changes,
9. widen browser mutation behavior,
10. admit autonomous AI business-state mutation.

## Next Safe Move

If more workbook-specific refinement is needed, the next bounded move is to inspect additional real planning workbooks and decide whether they still fit the same cache-break family or justify a second named formula-error pattern. This lane does not justify changing the current classifier on its own.
