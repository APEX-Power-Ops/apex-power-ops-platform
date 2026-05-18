# PM Lane 275 - Project Miner Temp Power Snapshot Loader Fallback

Date: 2026-05-18

Authority: VS Code Codex technical authority for the PM lane with Jason-delegated incremental no-live blocker approval

Decision label:

`PROJECT_MINER_TEMP_POWER_SNAPSHOT_LOADER_FALLBACK_NO_LIVE`

Selected outcome:

`SNAPSHOT_LOADER_IMPLEMENTED_AND_REAL_RUNTIME_SNAPSHOT_VERIFIED_NO_LIVE`

## Purpose

PM Lane 275 implements the no-live fallback needed to unblock hosted candidate readback if authenticated Render source-file placement remains unavailable.

The mutation-seam read layer can now load the Project Miner import candidate and admission plan from a runtime snapshot folder or file path supplied by:

`APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH`

This is read-only support only. It does not create approval authority, import authority, hosted upload automation, Render deployment automation, or business-state mutation.

## Files Added

1. `apps/mutation-seam/app/project_import_snapshot.py`
2. `apps/mutation-seam/tests/test_project_import_snapshot_loader.py`

## Files Updated

1. `apps/mutation-seam/app/project_import_candidate.py`
2. `apps/mutation-seam/app/project_import_admission_plan.py`

## Loader Behavior

When `APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH` is unset, existing source-file reader behavior remains unchanged.

When the env var is set and no explicit source paths are passed, the loader:

1. resolves the snapshot root from a folder path or a file path,
2. requires `candidate.json`, `admission-plan.json`, `manifest.json`, and `SHA256SUMS.txt`,
3. verifies SHA-256 checksums before returning payloads,
4. requires manifest schema `pm_import_candidate_snapshot_manifest_v1`,
5. requires authority `derived_source_snapshot_no_live`,
6. requires `mutation_authority: not_admitted` on manifest, candidate, and admission plan,
7. requires candidate ids to match across manifest, candidate, and admission plan,
8. returns the snapshot candidate from `/api/v1/reads/project-import-candidate`,
9. returns the snapshot admission plan from `/api/v1/reads/project-import-admission-plan`.

Explicit source-path arguments still bypass the snapshot env var for testability and source-reader preservation.

## Validation

Validation result: PASS

Focused test command:

`C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe -m pytest tests/test_project_import_snapshot_loader.py tests/test_project_import_candidate_snapshot_exporter.py tests/test_project_import_candidate.py tests/test_project_import_admission_plan.py`

Result:

`11 passed, 8 warnings`

The warnings are the existing Pydantic class-based config deprecations and openpyxl data-validation warning already present in this test slice.

The loader was also exercised against the actual PM Lane 274 runtime snapshot:

1. candidate id: `pm-import-candidate-miner-temp-power`
2. workpackages/tasks/apparatus: `7 / 15 / 184`
3. source stat fingerprint: `e111fdbe934bf9de07ed24c1`
4. candidate shape fingerprint: `ddc49565eb586af913ad48b2`
5. mutation authority: `not_admitted`

## Render Unblock Path

The Render item is now narrowed to an authenticated hosted environment step:

1. place the four PM Lane 274 runtime snapshot files on a governed hosted runtime or persistent path for the existing `apex-platform-mutation-seam` service,
2. set `APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH` to that hosted snapshot folder or `candidate.json` path,
3. redeploy or restart the existing Render service,
4. rerun hosted readback for `/api/v1/reads/project-import-candidate` and `/api/v1/reads/project-import-admission-plan`,
5. confirm hosted readback returns `pm-import-candidate-miner-temp-power`, 7 workpackages, 15 tasks, 184 apparatus candidates, source fingerprint `e111fdbe934bf9de07ed24c1`, and shape fingerprint `ddc49565eb586af913ad48b2`,
6. only after that proof, rerun approval-status readback and revisit the live approval-row gate.

No approval POST or approval-row creation is admitted by this lane.

## Guardrails

PM Lane 275 adds no UI section, writable control, button, link, approval route, import route, mutation handler, payload write version, localStorage schema, sessionStorage schema, live approval POST, approval row, project import, note, task, action item, owner/due-date assignment, field authorization, lead selection, crew assignment, schedule/status write, procurement or rental commitment, customer commitment, field instruction, durable field record, production tracking row, customer report, billing/payroll/invoice/accounting output, external finance-system output, Supabase write, hosted source upload, Render env var update, Render deploy, Vercel deploy, Olares action, SQL/schema migration, committed snapshot payload, source workbook writeback, source PDF content edit, workbook macro/writeback, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Next Technical Move

The active blocker is now:

`STOPPED_AWAITING_RENDER_AUTHENTICATED_SOURCE_PLACEMENT_OR_SNAPSHOT_ENV_DEPLOY_NO_APPROVAL_POST`

VS Code Codex can continue no-live repo work, but hosted Temp Power readback cannot be repaired from this shell until an authenticated Render operator either completes PM Lane 270 source placement or applies the PM Lane 275 snapshot env deployment path.
