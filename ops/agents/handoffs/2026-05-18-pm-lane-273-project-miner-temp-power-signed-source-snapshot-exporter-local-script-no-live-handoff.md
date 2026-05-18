# PM Lane 273 - Signed Source Snapshot Exporter Local Script Handoff

Date: 2026-05-18

Decision label:

`PROJECT_MINER_TEMP_POWER_SIGNED_SOURCE_SNAPSHOT_EXPORTER_LOCAL_SCRIPT_NO_LIVE`

Selected outcome:

`LOCAL_EXPORTER_SCRIPT_ADDED_SYNTHETIC_TESTED_NO_SOURCE_ARTIFACT_CREATED_NO_LIVE`

## Result

PM Lane 273 adds the local exporter script and focused tests from the PM Lane 272 design.

Added:

1. `apps/mutation-seam/scripts/export_pm_import_candidate_snapshot.py`
2. `apps/mutation-seam/tests/test_project_import_candidate_snapshot_exporter.py`

## Validation

Ambient Python failed because `pytest` is not installed there.

The platform-local venv passed:

`C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe -m pytest tests/test_project_import_candidate_snapshot_exporter.py tests/test_project_import_candidate.py tests/test_project_import_admission_plan.py`

Result:

`8 passed, 7 warnings`

Warnings are existing Pydantic/openpyxl warnings for this test slice.

## Boundary

The exporter was not run against the real Project Miner source files. No source workbook/PDF content was read in this lane, no durable snapshot artifact was created, no hosted loader was added, no Render or Supabase action was taken, and no approval POST or approval row was created.

## Next

The current blocker remains:

`STOPPED_AWAITING_RENDER_AUTHENTICATED_SOURCE_FILES_REPAIR_NO_APPROVAL_POST`

If Render source placement remains unavailable, a later packet may admit:

`PM Lane 274 - Project Miner Temp Power Runtime Snapshot Export No-Live`

That packet must explicitly admit local real-source read and transient runtime artifact creation before this exporter is run against the current Project Miner source set.
