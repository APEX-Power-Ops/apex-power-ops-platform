# PM Lane 237 - Project Miner Temp Power Project Data Entry Warning Triage No-Live Packet

Date: 2026-05-17
Status: Local executed, no-live
Scope: Project Miner Temp Power corrected candidate warning triage and review-burden reduction

## Trigger

PM Lane 236 corrected source row 28 / `miner-line-015` and cleared `MISSING_DESIGNATIONS`. The corrected Temp Power candidate still reports one warning:

`PROJECT_DATA_ENTRY_FORMULA_ERRORS`

This packet makes that warning reviewable without opening live approval/import authority.

## Lane 237 Classification

Selected outcome:

`PROJECT_DATA_ENTRY_FORMULA_WARNING_CLASSIFIED_LINEAGE_ONLY_NO_LIVE`

The Project Data Entry workbook remains a planning/import-shaping lineage source, not the current Temp Power estimator source. The warning is therefore not a candidate-shape blocker for the corrected Temp Power source package, but it is still a review item before anyone relies on that workbook as an import/export authority surface.

## Local Evidence

Read-only local preview after Lane 237 reports:

| Evidence | Value |
| --- | --- |
| Candidate | `pm-import-candidate-miner-temp-power` |
| Tasks | 15 |
| Apparatus candidates | 184 |
| Warning count | 1 |
| Blocker count | 0 |
| Remaining warning | `PROJECT_DATA_ENTRY_FORMULA_ERRORS` |
| Formula error rows | 234 |
| Formula error cells | 3510 |
| Sample row count surfaced | 5 |

The first sampled row is Project Data Entry `All_Tasks` source row 2, task ID `1.1.1`, task `MV13A-1`, apparatus `Protective Relay (Feeder Protection)`.

Top formula-error columns in the local preview:

1. `Drawing`: 234
2. `Date Due`: 234
3. `Notes`: 234
4. `Assessment`: 234
5. `DATASHEET`: 234
6. `DATE COMPLETED`: 234

## Implementation

Changed local read/review surfaces only:

1. `apps/mutation-seam/app/project_tracker_sources.py`
   - Adds formula-error column counts.
   - Adds bounded formula-error sample rows.
2. `apps/mutation-seam/app/project_import_candidate.py`
   - Adds row count, cell count, column counts, and sample rows to the warning payload.
3. `apps/operations-web/app/pm-review/import-intake/page.tsx`
   - Shows review action, formula detail, top affected columns, sample rows, and source path in the existing Exception Review card.
4. `apps/mutation-seam/tests/test_project_tracker_sources.py`
   - Covers column-count and sample-row payload shape.

## Guardrails

This packet does not:

1. write the Project Data Entry workbook,
2. run workbook macros,
3. edit source PDFs,
4. create hosted approval records,
5. POST approval decisions,
6. import project/workpackage/task/apparatus rows,
7. assign leads, crews, owners, or due dates,
8. write schedule/status/field/customer/production/finance records,
9. call Supabase, Render, Vercel, or Olares mutations,
10. promote Project Data Entry workbook rows to production truth,
11. admit Desktop Codex PM decision authority,
12. perform autonomous AI business-state mutation.

## Validation

Commands run:

```powershell
.\.venv\Scripts\python.exe -m pytest apps/mutation-seam/tests/test_project_tracker_sources.py apps/mutation-seam/tests/test_project_import_candidate.py
corepack pnpm --dir apps/operations-web typecheck
```

Local read-only preview also confirmed:

```text
candidate_id=pm-import-candidate-miner-temp-power
task_count=15
apparatus_candidate_count=184
warning_count=1
blocker_count=0
warning_code=PROJECT_DATA_ENTRY_FORMULA_ERRORS
formula_error_row_count=234
formula_error_cell_count=3510
sample_row_count=5
```

Validation result: PASS

## Next Safe Packet

PM Lane 238 should produce a compact no-live decision card for the remaining Project Data Entry lineage warning:

1. accept as non-blocking for Temp Power candidate review,
2. request Project Data Entry workbook correction before live admission,
3. hold no-live,
4. provide exact later live admission phrase.
