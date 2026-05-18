# PM Lane 270 - Hosted Source Files Env Repair Dispatch Handoff

Date: 2026-05-18

Admitted return label:

`APPROVE_HOSTED_SOURCE_FILES_ENV_REPAIR_NO_APPROVAL_POST`

Decision label:

`PROJECT_MINER_TEMP_POWER_HOSTED_SOURCE_FILES_ENV_REPAIR_DISPATCH_NO_APPROVAL_POST`

Selected outcome:

`HOSTED_SOURCE_FILES_ENV_REPAIR_DISPATCHED_AWAITING_RENDER_AUTH_EXECUTOR_NO_APPROVAL_POST`

## Objective

Dispatch the authenticated hosted-source repair path selected by Jason without opening the live approval POST.

## Result

The exact source strategy label is accepted. PM Lane 270 creates the authenticated Render/source-placement executor prompt and stops at:

`STOPPED_AWAITING_RENDER_AUTHENTICATED_SOURCE_FILES_REPAIR_NO_APPROVAL_POST`

## Why This Stops Here

The local VS Code Codex shell can verify the source files and repo contract, but it does not expose the Render CLI, Render API credentials, Render deploy hook, or an authenticated dashboard/session control surface.

Render's current platform docs also matter here: the running service filesystem is ephemeral unless a persistent disk is attached, so a durable hosted source repair must use a governed runtime-accessible storage path for the existing service instead of a one-off shell copy into ephemeral storage.

## Minimum Hosted Repair Scope

Existing service only:

`apex-platform-mutation-seam`

Minimum code-required source files:

1. `Estimator R3 - Project Miner Temp Power Testing.xlsm`
2. `Miner Temp SLD-AP-BCARRASCO.pdf`
3. `RESA Power - Project Data Entry MASTER.xlsm`
4. `Garney- Central Mesa Reuse Tracker #677562.xlsm`
5. `EQUIPMENT INVENTORY - 2026.xlsx`
6. `Phx Tech Testing Capability Matrix 032726.xlsx`

Source env vars to set or confirm:

1. `APEX_PROJECT_MINER_PLANNING_ROOT`
2. `APEX_PROJECT_ESTIMATOR_WORKBOOK`
3. `APEX_PROJECT_SLD_PDF`
4. `APEX_PROJECT_DATA_ENTRY_WORKBOOK`
5. `APEX_REFERENCE_TRACKER_WORKBOOK`
6. `APEX_FIELD_SEED_EQUIPMENT_WORKBOOK`
7. `APEX_FIELD_SEED_CAPABILITY_WORKBOOK`

## Executor Prompt

Use:

`ops/agents/handoffs/2026-05-18-pm-lane-270-render-hosted-source-files-env-repair-executor-copy-paste-prompt.md`

## Closeout Expected From Executor

Expected executor outcome labels:

1. `HOSTED_SOURCE_FILES_ENV_REPAIR_PASS_NO_APPROVAL_POST`
2. `BLOCKED_RENDER_AUTH_UNAVAILABLE_NO_APPROVAL_POST`
3. `BLOCKED_NO_GOVERNED_HOSTED_SOURCE_STORAGE_NO_APPROVAL_POST`
4. `BLOCKED_HOSTED_CANDIDATE_STILL_NOT_TEMP_POWER_NO_APPROVAL_POST`

## Guardrails

Do not send an approval POST. Do not create an approval row. Do not import project rows. Do not create a new Render service or public file authority. Do not commit source workbooks or PDFs to Git. Do not print or change secrets. Do not run SQL. Do not run macros. Do not read workbook/PDF contents beyond the existing app's read-only source parsing during hosted validation. Do not mutate schedule, resource, field, customer, production, finance, or other PM business state.
