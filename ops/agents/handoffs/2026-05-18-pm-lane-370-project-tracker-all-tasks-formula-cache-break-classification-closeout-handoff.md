# PM Lane 370 - Project Tracker All_Tasks Formula Cache-Break Classification Closeout Handoff

## Outcome

Executed and locally validated PM Lane 370 as a bounded Project Tracker lineage-classification slice.

Selected outcome: `PM_PROJECT_TRACKER_ALL_TASKS_FORMULA_CACHE_BREAK_CLASSIFIED_LOCAL_CURRENT`

The mutation seam now distinguishes a macro-built `All_Tasks` cache-break pattern from a generic planning-workbook formula discrepancy.

## Scope

- Reviewed the historical VBA modules in `C:/APEX Platform/Reference_Files/Excel/Project Tracker VBA Modules` as static lineage evidence for the Project Tracker workbook flow.
- Confirmed `Build_All.bas` builds formula-heavy scope sheets and `PopulateAllTasks.bas` flattens scope data into `All_Tasks`.
- Confirmed the live planning preview shape: `Task_Entry` source rows are present while every `All_Tasks` row in the Project Data Entry workbook carries the same 15 `#REF!`-backed derived-column failures.
- Added mutation-seam pattern detection for a uniform `All_Tasks` formula cache break.
- Reworded the import-candidate warning so it points reviewers at `Task_Entry` as lineage source truth and the workbook's `BuildAll` / `PopulateAllTasks` macro output as the likely repair surface.
- Added focused tests for the new tracker classification and warning message.

## Files Changed

- `apps/mutation-seam/app/project_tracker_sources.py`
- `apps/mutation-seam/app/project_import_candidate.py`
- `apps/mutation-seam/tests/test_project_tracker_sources.py`
- `apps/mutation-seam/tests/test_project_import_candidate.py`
- `PROJECT_STATUS.md`

## Validation

Focused validation passed:

```text
Set-Location "c:/APEX Platform/apex-power-ops-platform/apps/mutation-seam"
python -m pytest tests/test_project_tracker_sources.py tests/test_project_import_candidate.py
7 passed, 5 warnings in 1.83s
```

Additional live evidence used during classification:

- `preview_pm_planning_sources.py --format json` showed `project_data_entry.task_entry_count=14`
- The same preview showed `project_data_entry.all_tasks_count=234`
- `formula_error_row_count=234` and `formula_error_column_counts` repeated the same 15 derived columns across every `All_Tasks` row

## Guardrails Preserved

- No workbook macro was executed.
- No workbook file was modified.
- No hosted deployment or runtime mutation was performed.
- No PM route authority was widened.
- No approval/import/assignment/schedule/status write path was admitted.
- No finance, customer-delivery, or source-writeback authority was widened.
- No autonomous AI business-state mutation was introduced.

## Notes

The prior warning treated any `#...` cached value inside `All_Tasks` as a generic workbook formula discrepancy. The live workbook shape and VBA lineage together show a more specific condition: the workbook still has usable `Task_Entry` source rows, while the macro-built `All_Tasks` cache is uniformly broken across derived workflow columns. That is a materially better explanation for reviewers because it narrows the likely repair surface to the workbook build/cache flow instead of implying broad source corruption.

This slice is intentionally classification-only. It does not repair the workbook itself, execute macros, or change hosted PM lane behavior.

## Next Bounded Move

If this formula issue needs deeper resolution, the next truthful move is a no-live workbook-lineage packet that maps the failing derived columns back to the exact scope-template formulas and any expected rebuild sequence in the Project Tracker macro flow.