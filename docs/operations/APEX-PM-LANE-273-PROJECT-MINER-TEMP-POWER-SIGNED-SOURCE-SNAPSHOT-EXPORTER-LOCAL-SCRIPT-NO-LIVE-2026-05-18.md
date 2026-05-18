# PM Lane 273 - Project Miner Temp Power Signed Source Snapshot Exporter Local Script

Date: 2026-05-18

Authority: VS Code Codex technical authority for the PM lane with Jason-delegated incremental no-live blocker approval

Decision label:

`PROJECT_MINER_TEMP_POWER_SIGNED_SOURCE_SNAPSHOT_EXPORTER_LOCAL_SCRIPT_NO_LIVE`

Selected outcome:

`LOCAL_EXPORTER_SCRIPT_ADDED_SYNTHETIC_TESTED_NO_SOURCE_ARTIFACT_CREATED_NO_LIVE`

## Purpose

PM Lane 273 implements the local exporter script designed in PM Lane 272 without running it against the real Project Miner source files and without creating a durable source snapshot artifact.

The script gives VS Code Codex a governed no-live fallback tool if the PM Lane 270 authenticated Render/source-placement path remains blocked, while preserving the current live approval boundary.

## Files Added

1. `apps/mutation-seam/scripts/export_pm_import_candidate_snapshot.py`
2. `apps/mutation-seam/tests/test_project_import_candidate_snapshot_exporter.py`

## Exporter Behavior

The exporter:

1. reuses the existing read-only candidate and admission-plan builders,
2. requires an explicit `--output-dir`,
3. blocks output inside the repo unless `--allow-repo-output` is explicitly passed,
4. writes `candidate.json`, `admission-plan.json`, `manifest.json`, and `SHA256SUMS.txt`,
5. records SHA-256 hashes for payload integrity,
6. redacts source file paths from `manifest.json`,
7. labels the snapshot authority as `derived_source_snapshot_no_live`,
8. preserves `mutation_authority: not_admitted`.

The exporter does not add hosted loader behavior, does not set `APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH`, and does not change any read or write endpoint.

## Test Boundary

The new focused tests use synthetic candidate data only. They prove:

1. manifest source entries redact personal/absolute paths,
2. payload SHA-256 values match file contents,
3. candidate and admission payloads preserve `mutation_authority: not_admitted`,
4. warning-code and count fields land in the manifest,
5. repo output is rejected by default.

The focused test command also reran the existing import candidate and admission-plan tests so the exporter remains aligned with the current PM intake model.

## Validation

Validation result: PASS

Commands:

1. `python -m pytest ...` with ambient Python failed because that interpreter has no `pytest`.
2. `.venv/Scripts/python.exe -m pytest tests/test_project_import_candidate_snapshot_exporter.py tests/test_project_import_candidate.py tests/test_project_import_admission_plan.py`

Result:

`8 passed, 7 warnings`

The warnings were the existing Pydantic class-based config deprecation warnings and openpyxl data-validation warning already present in this test slice.

## Guardrails

PM Lane 273 adds no UI section, writable control, button, link, route, handler, backend seam, payload version, localStorage schema, sessionStorage schema, live approval POST, approval row, project import, note, task, action item, owner/due-date assignment, field authorization, lead selection, crew assignment, schedule/status write, procurement or rental commitment, customer commitment, field instruction, durable field record, production tracking row, customer report, billing/payroll/invoice/accounting output, external finance-system output, Supabase write, hosted source upload, Render env var update, Render deploy, Vercel deploy, Olares action, SQL/schema migration, committed signed snapshot artifact, snapshot runtime fallback, source workbook writeback, source PDF content edit, real source workbook/PDF content read/write, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Next Technical Move

The next blocker is still PM Lane 270's hosted source-placement capability:

`STOPPED_AWAITING_RENDER_AUTHENTICATED_SOURCE_FILES_REPAIR_NO_APPROVAL_POST`

If that path remains unavailable, the next no-live packet may admit running the exporter against the current local Project Miner Temp Power source set and producing a runtime-only snapshot artifact outside tracked repo paths. That later packet must explicitly admit local real-source read plus transient artifact creation before the exporter is run against the real source files.
