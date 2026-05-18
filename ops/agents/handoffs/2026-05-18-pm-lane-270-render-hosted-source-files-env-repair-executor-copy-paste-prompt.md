# PM Lane 270 - Render Hosted Source Files Env Repair Executor Prompt

You are the authenticated hosted-source executor for PM Lane 270.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Packet: `ops/agents/packets/draft/2026-05-18-pm-lane-270-project-miner-temp-power-hosted-source-files-env-repair-dispatch-no-approval-post.json`
- Prior blocker: `STOPPED_AWAITING_HOSTED_SOURCE_STRATEGY_DECISION_NO_LIVE`
- Admitted return label: `APPROVE_HOSTED_SOURCE_FILES_ENV_REPAIR_NO_APPROVAL_POST`

Start with:

```powershell
cd "C:/APEX Platform/apex-power-ops-platform"
git pull --ff-only
git status --short --branch
git rev-parse HEAD
```

## Objective

Repair hosted mutation-seam source-file hydration for the current Project Miner Temp Power import candidate, using the existing Render service only.

Target service:

`apex-platform-mutation-seam`

Target hosted base URL:

`https://mutation-seam.apexpowerops.com`

The goal is for hosted read-only candidate routes to return the current Temp Power candidate before any later approval POST is considered.

## Local Source Folder

Use the local governed source folder supplied by Jason:

`C:/Users/jjswe/Desktop/Project Miner PM Planning`

Minimum code-required source files:

1. `Estimator R3 - Project Miner Temp Power Testing.xlsm`
2. `Miner Temp SLD-AP-BCARRASCO.pdf`
3. `RESA Power - Project Data Entry MASTER.xlsm`
4. `Garney- Central Mesa Reuse Tracker #677562.xlsm`
5. `EQUIPMENT INVENTORY - 2026.xlsx`
6. `Phx Tech Testing Capability Matrix 032726.xlsx`

Other planning-folder project context files may remain parked unless the authenticated source-storage path can include them without widening scope or blocking the current Temp Power candidate repair:

1. `15_ELECTRICAL_COMBINED.pdf`
2. `Building B IFC.pdf`
3. `Cupertino - Miner Estimator PHX Bldg A & B MV Rev9.xlsm`

Do not read workbook/PDF contents manually. Do not run macros. Do not edit these files.

## Hosted Placement Requirements

Use a governed hosted runtime-accessible path for the existing Render service. Prefer an existing attached persistent disk if one is already present.

If a new persistent disk, new paid storage resource, public bucket, second service, or external file authority would be required, stop and close out with:

`BLOCKED_NO_GOVERNED_HOSTED_SOURCE_STORAGE_NO_APPROVAL_POST`

Do not copy source files into Git. Do not commit binaries. Do not use Jason's Windows path as a hosted env value.

Recommended hosted path if a governed persistent runtime path is available:

`/var/data/project-miner-pm-planning`

If a different hosted path is used, record that non-secret path in the closeout.

## Render Env Vars

Set or confirm these env vars on the existing Render service, using hosted paths:

```text
APEX_PROJECT_MINER_PLANNING_ROOT=/var/data/project-miner-pm-planning
APEX_PROJECT_ESTIMATOR_WORKBOOK=/var/data/project-miner-pm-planning/Estimator R3 - Project Miner Temp Power Testing.xlsm
APEX_PROJECT_SLD_PDF=/var/data/project-miner-pm-planning/Miner Temp SLD-AP-BCARRASCO.pdf
APEX_PROJECT_DATA_ENTRY_WORKBOOK=/var/data/project-miner-pm-planning/RESA Power - Project Data Entry MASTER.xlsm
APEX_REFERENCE_TRACKER_WORKBOOK=/var/data/project-miner-pm-planning/Garney- Central Mesa Reuse Tracker #677562.xlsm
APEX_FIELD_SEED_EQUIPMENT_WORKBOOK=/var/data/project-miner-pm-planning/EQUIPMENT INVENTORY - 2026.xlsx
APEX_FIELD_SEED_CAPABILITY_WORKBOOK=/var/data/project-miner-pm-planning/Phx Tech Testing Capability Matrix 032726.xlsx
```

Adjust the prefix if the hosted path differs.

Confirm existing secret-bearing env vars remain present without printing values:

1. `SEAM_DATABASE_URL`
2. `JWT_SECRET`

Do not print, paste, store, rotate, or modify secret values.

## Deploy/Restart

After source placement and env confirmation, restart or redeploy the existing Render service so the running process has the updated runtime env.

Do not create a new Render service. Do not change DNS, custom domains, CORS, auth, ingress, or service topology.

## Read-Only Validation

Run from `C:/APEX Platform/apex-power-ops-platform` after the existing service is live:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
```

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

Also read these hosted routes without sending a mutation:

1. `https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-candidate`
2. `https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-admission-plan`
3. `https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-approval-contract`
4. `https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-approval-storage-plan`
5. `https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-approval-status`

Required readback:

1. candidate id `pm-import-candidate-miner-temp-power`,
2. task count `15`,
3. apparatus candidate count `184`,
4. blocker count `0`,
5. accepted warning code `PROJECT_DATA_ENTRY_FORMULA_ERRORS`,
6. approval status is for the Temp Power candidate,
7. no approval row exists yet unless a later packet creates it.

## Closeout File

Create exactly one closeout:

`ops/agents/handoffs/2026-05-18-pm-lane-270-render-hosted-source-files-env-repair-executor-closeout.md`

The closeout must include:

1. source commit tested,
2. existing Render service name,
3. authenticated surface used, without exposing secrets,
4. hosted source path used,
5. which minimum source files were placed or confirmed,
6. source env var key presence and non-secret path summary,
7. whether a persistent disk or already-governed runtime path was used,
8. restart/redeploy evidence,
9. exact validation command outputs,
10. hosted candidate readback summary,
11. final outcome label,
12. guardrail confirmation.

Final outcome must be exactly one of:

1. `HOSTED_SOURCE_FILES_ENV_REPAIR_PASS_NO_APPROVAL_POST`
2. `BLOCKED_RENDER_AUTH_UNAVAILABLE_NO_APPROVAL_POST`
3. `BLOCKED_NO_GOVERNED_HOSTED_SOURCE_STORAGE_NO_APPROVAL_POST`
4. `BLOCKED_HOSTED_CANDIDATE_STILL_NOT_TEMP_POWER_NO_APPROVAL_POST`

## Not Allowed

- Do not send `POST /api/v1/mutations/project-import-approvals`.
- Do not create an approval row.
- Do not import project rows.
- Do not run SQL writes or schema migrations.
- Do not create a new Render service.
- Do not create public file storage.
- Do not commit source workbooks, source PDFs, derived snapshots, or fixtures.
- Do not print or modify `SEAM_DATABASE_URL`, `JWT_SECRET`, or any secret.
- Do not run macros.
- Do not write back to source workbooks.
- Do not edit source PDFs.
- Do not mutate tasks, owners, due dates, resources, schedules, field records, customer records, production records, finance records, or other PM business state.

Commit and push only the closeout file if a closeout is created. Then fast-forward Olares and confirm `bash tools/ai/run-minimal-mcp-trio.sh status` returns `{"status":"not-running"}`.
