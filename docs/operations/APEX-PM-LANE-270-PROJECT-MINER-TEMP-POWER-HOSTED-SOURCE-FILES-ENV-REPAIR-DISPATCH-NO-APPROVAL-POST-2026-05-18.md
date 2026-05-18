# PM Lane 270 - Project Miner Temp Power Hosted Source Files Env Repair Dispatch

Date: 2026-05-18

Authority: VS Code Codex technical authority for the PM lane

Admitted return label:

`APPROVE_HOSTED_SOURCE_FILES_ENV_REPAIR_NO_APPROVAL_POST`

Decision label:

`PROJECT_MINER_TEMP_POWER_HOSTED_SOURCE_FILES_ENV_REPAIR_DISPATCH_NO_APPROVAL_POST`

Selected outcome:

`HOSTED_SOURCE_FILES_ENV_REPAIR_DISPATCHED_AWAITING_RENDER_AUTH_EXECUTOR_NO_APPROVAL_POST`

## Purpose

PM Lane 270 records Jason's exact PM Lane 268 source strategy return and converts it into a bounded hosted-source repair executor packet.

The approval is intentionally narrow. It admits the hosted source-files/env repair path for the existing Render mutation-seam service, but it does not admit an approval POST, approval-row creation, project import, Supabase write, source workbook/PDF edit, macro run, new service, public storage surface, or autonomous PM business-state mutation.

## Source Strategy Admission

The controlling current return is:

`APPROVE_HOSTED_SOURCE_FILES_ENV_REPAIR_NO_APPROVAL_POST`

That label selects the PM Lane 268 recommended strategy:

1. place governed Project Miner Temp Power source files in a hosted runtime-accessible location for the existing mutation-seam service,
2. point existing source reader env vars at the hosted paths,
3. restart or redeploy the existing Render service,
4. rerun hosted read-only candidate/smoke proof,
5. stop before any approval POST or approval-row creation.

## Local Capability Classification

VS Code Codex confirmed the local workstation has the current planning-folder source files, but it does not currently expose an authenticated Render CLI/API control surface.

Local source folder checked:

`C:/Users/jjswe/Desktop/Project Miner PM Planning`

Current files present there:

1. `15_ELECTRICAL_COMBINED.pdf`
2. `Building B IFC.pdf`
3. `Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm`
4. `EQUIPMENT INVENTORY - 2026.xlsx`
5. `Estimator R3 - Project Miner Temp Power Testing.xlsm`
6. `Garney- Central Mesa Reuse Tracker #677562.xlsm`
7. `Miner Temp SLD-AP-BCARRASCO.pdf`
8. `Phx Tech Testing Capability Matrix 032726.xlsx`
9. `RESA Power - Project Data Entry MASTER.xlsm`

No file contents were read in this lane. Only names, sizes, and timestamps were inspected.

Local hosted-control evidence:

1. no `render` CLI command was available in the shell,
2. no local env names matching Render API credentials or service IDs were exposed,
3. no repo-local `.env` source exposed Render API credentials or hosted source path values,
4. no Render dashboard/API mutation was performed from this shell.

## Render Platform Posture

Current Render documentation confirms the important repair boundary:

1. Render service filesystems are ephemeral unless a persistent disk is attached.
2. A persistent disk must be mounted under an explicit service path, such as `/var/data`.
3. File transfer to a disk-backed service can be performed through authenticated service access such as SSH/SCP or dashboard shell tooling.
4. Manual deploys and service restarts are Render-controlled operations through dashboard, CLI, deploy hook, or API.

Therefore, this lane dispatches an authenticated Render executor instead of committing large/source files to Git or inventing a repo-local hosted storage surface.

## Existing Service Target

Target service:

`apex-platform-mutation-seam`

Existing root directory:

`apps/mutation-seam`

Existing public base URL:

`https://mutation-seam.apexpowerops.com`

The executor must use the existing service only. Do not create a new Render service, public bucket, external file server, or second hosted authority.

## Minimum Source Set Required For Current Temp Power Candidate

The current code-required source set for candidate hydration is:

1. `Estimator R3 - Project Miner Temp Power Testing.xlsm`
2. `Miner Temp SLD-AP-BCARRASCO.pdf`
3. `RESA Power - Project Data Entry MASTER.xlsm`
4. `Garney- Central Mesa Reuse Tracker #677562.xlsm`
5. `EQUIPMENT INVENTORY - 2026.xlsx`
6. `Phx Tech Testing Capability Matrix 032726.xlsx`

The larger current planning-folder files should remain available as governed project context where hosted storage policy allows, but they are not required to unblock the current Temp Power candidate reader.

## Runtime Env Mapping

The authenticated hosted executor should use a governed hosted runtime path, for example:

`/var/data/project-miner-pm-planning`

If a different existing governed Render path is used, the closeout must name the non-secret path.

Set or confirm these env vars on the existing service, using hosted paths rather than Jason's Windows path:

1. `APEX_PROJECT_MINER_PLANNING_ROOT`
2. `APEX_PROJECT_ESTIMATOR_WORKBOOK`
3. `APEX_PROJECT_SLD_PDF`
4. `APEX_PROJECT_DATA_ENTRY_WORKBOOK`
5. `APEX_REFERENCE_TRACKER_WORKBOOK`
6. `APEX_FIELD_SEED_EQUIPMENT_WORKBOOK`
7. `APEX_FIELD_SEED_CAPABILITY_WORKBOOK`

Do not print or change `SEAM_DATABASE_URL`, `JWT_SECRET`, or other secrets.

## Required Hosted Readback Before Any Later Live Retry

After authenticated source placement, env update, and service restart/redeploy, the next proof must show:

1. deployed mutation-seam smoke with PM intake returns `RESULT PASS`,
2. paired operations-web PM-intake hosted smoke returns `failed=0`,
3. hosted candidate id is `pm-import-candidate-miner-temp-power`,
4. hosted candidate has `15` tasks,
5. hosted candidate has `184` apparatus candidates,
6. hosted candidate has `0` blockers,
7. hosted candidate preserves accepted warning `PROJECT_DATA_ENTRY_FORMULA_ERRORS`,
8. hosted approval-status readback is for the Temp Power candidate,
9. no approval row exists yet unless a later live approval packet creates it.

## Next Blocker Review Point

PM Lane 270 stops at:

`STOPPED_AWAITING_RENDER_AUTHENTICATED_SOURCE_FILES_REPAIR_NO_APPROVAL_POST`

The next expected closeout must come from an authenticated Render/source-placement executor and must report one of:

1. `HOSTED_SOURCE_FILES_ENV_REPAIR_PASS_NO_APPROVAL_POST`
2. `BLOCKED_RENDER_AUTH_UNAVAILABLE_NO_APPROVAL_POST`
3. `BLOCKED_NO_GOVERNED_HOSTED_SOURCE_STORAGE_NO_APPROVAL_POST`
4. `BLOCKED_HOSTED_CANDIDATE_STILL_NOT_TEMP_POWER_NO_APPROVAL_POST`

## Guardrails

PM Lane 270 adds no product code, UI section, writable control, button, link, route, handler, backend seam, payload version, localStorage schema, sessionStorage schema, live approval POST, approval row, project import, note, task, action item, owner/due-date assignment, field authorization, lead selection, crew assignment, schedule/status write, procurement or rental commitment, customer commitment, field instruction, durable field record, production tracking row, customer report, billing/payroll/invoice/accounting output, external finance-system output, Supabase write, Render env var update from this shell, Render deploy from this shell, Vercel deploy, Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook content read/write, workbook macro/writeback, durable source fingerprint promotion, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.

## Validation

Validation result: PASS

Proof:

1. local source-file presence metadata check,
2. local Render capability check,
3. current Render docs review,
4. PM Lane 270 text search,
5. packet JSON parse,
6. guardrail keyword scan,
7. corrupted-token scan,
8. `git diff --check`.
