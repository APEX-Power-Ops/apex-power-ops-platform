# PM Lane 405 - Project Data Entry Workbook Example Calibration Closeout Handoff

## Outcome

Executed PM Lane 405 as the no-live workbook-example calibration tranche for Project Data Entry formula warnings.

Selected outcome: `PM_PROJECT_DATA_ENTRY_WORKBOOK_EXAMPLE_CALIBRATION_LOCAL_CURRENT`

The real Garney workbook is the clean comparison case for this warning family. It loads without formula errors, while the master Project Data Entry workbook still shows the uniform `All_Tasks` cache-break signature.

## Change Surface

Product files changed:

- `apps/mutation-seam/app/project_import_candidate.py`
- `apps/mutation-seam/tests/test_project_import_candidate.py`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `apps/operations-web/tests/browser-shell.pm-import-candidate.smoke.spec.ts`

Repo governance files changed:

- `PROJECT_STATUS.md`
- `docs/operations/APEX-PM-LANE-405-PROJECT-DATA-ENTRY-WORKBOOK-EXAMPLE-CALIBRATION-NO-LIVE-PACKET-2026-05-19.md`
- `ops/agents/handoffs/2026-05-19-pm-lane-405-project-data-entry-workbook-example-calibration-closeout-handoff.md`

## Validation

Focused validation passed:

```text
C:\APEX Platform\apex-power-ops-platform\.venv\Scripts\python.exe -m pytest apps/mutation-seam/tests/test_project_import_candidate.py -q
4 passed

corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts tests/browser-shell.pm-import-candidate.smoke.spec.ts
2 passed
```

## Boundary

- No workbook edits.
- No macro execution.
- No classifier replacement or new warning code.
- No route authority widening.
- No hosted deployment.
- No schema change.
- No approval/import/assignment/schedule-status/field/production/customer/finance write admission.
- No autonomous AI business-state mutation.

## Next Branch Set

The current classifier still stands: the broken Project Data Entry workbook looks like an `All_Tasks` cache/build break, and the Garney workbook now serves as the clean comparison example in the warning detail. The next bounded move, if needed, is to inspect more real workbooks for additional formula-error families rather than weakening the current cache-break interpretation.
