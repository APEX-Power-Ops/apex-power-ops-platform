# PM Lane 276 - VS Code Copilot Render Completion Executor Prompt

You are the authenticated Render executor for PM Lane 276.

Use your Internal browser for Render dashboard access, logs, shell, env configuration, deploy/restart controls, and hosted route checks as needed.

## Source Floor

- Repo: `C:/APEX Platform/apex-power-ops-platform`
- Branch: `clean-main`
- Packet: `ops/agents/packets/draft/2026-05-18-pm-lane-276-project-miner-temp-power-vscode-copilot-render-completion-dispatch-no-approval-post.json`
- Target service: `apex-platform-mutation-seam`
- Target hosted base URL: `https://mutation-seam.apexpowerops.com`
- Current blocker: `STOPPED_AWAITING_RENDER_AUTHENTICATED_SOURCE_PLACEMENT_OR_SNAPSHOT_ENV_DEPLOY_NO_APPROVAL_POST`

Start with:

```powershell
cd "C:/APEX Platform/apex-power-ops-platform"
git pull --ff-only
git status --short --branch
git rev-parse HEAD
```

The Render service must be on a deployed `clean-main` commit that includes PM Lane 275 snapshot-loader support for:

`APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH`

At packet authoring, the local PM Lane 275 floor was:

`c0f99ff89391334d674b0ea75a79ae85a89b3086`

Deploy this commit or newer to the existing service if Render is not already serving it.

## Objective

Complete the hosted Render requirements so read-only mutation-seam routes return the current Project Miner Temp Power import candidate.

Preferred outcome:

`RENDER_SNAPSHOT_ENV_DEPLOY_PASS_NO_APPROVAL_POST`

Fallback outcome, only if snapshot env deploy is blocked and governed source-file storage already exists:

`RENDER_SOURCE_FILES_ENV_REPAIR_PASS_NO_APPROVAL_POST`

## Path A - Preferred Snapshot Env Deploy

Use the existing PM Lane 274 runtime snapshot.

Local source folder:

`C:/APEX Platform/runtime/pm-lane-274-project-miner-temp-power-snapshot-2026-05-18`

Files:

1. `candidate.json`
2. `admission-plan.json`
3. `manifest.json`
4. `SHA256SUMS.txt`

Expected hashes:

```text
b370e6999e9beddc5ae70feca8454052c001dec47dc42fcfc19269d853ce01cd  admission-plan.json
813013d12cab476ffa67cfbb42d0421bc107d5e189a229e2450f490fc9022445  candidate.json
80a05dcc70728099ee52ff0f80204feee5e6f4102334f919837016ef89b87f95  manifest.json
```

Verify locally before transfer:

```powershell
Get-FileHash "C:/APEX Platform/runtime/pm-lane-274-project-miner-temp-power-snapshot-2026-05-18/candidate.json" -Algorithm SHA256
Get-FileHash "C:/APEX Platform/runtime/pm-lane-274-project-miner-temp-power-snapshot-2026-05-18/admission-plan.json" -Algorithm SHA256
Get-FileHash "C:/APEX Platform/runtime/pm-lane-274-project-miner-temp-power-snapshot-2026-05-18/manifest.json" -Algorithm SHA256
```

Preferred hosted path:

`/var/data/project-import-snapshots/pm-lane-274-project-miner-temp-power-snapshot-2026-05-18`

Use a governed persistent or runtime-accessible path for the existing service. Render filesystems are ephemeral unless a persistent disk is attached, so do not rely on a one-off copy outside a preserved runtime path for durable proof.

If Render requires a new paid disk, new public bucket, new service, new database, or external file authority, stop unless Jason explicitly approves that resource in the authenticated flow. Close out with:

`BLOCKED_RENDER_STORAGE_REQUIRES_NEW_RESOURCE_NO_APPROVAL_POST`

Transfer the four files using the authenticated Render surface available to you:

1. dashboard shell plus transfer tooling,
2. Render SSH/SCP,
3. another Render-supported private service file-transfer method.

Do not print secrets. Do not upload source workbooks or PDFs for Path A.

Set this non-secret env var on the existing service:

```text
APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH=/var/data/project-import-snapshots/pm-lane-274-project-miner-temp-power-snapshot-2026-05-18
```

If you use a different hosted path, set the env var to that path and record it in closeout.

Confirm secret-bearing keys remain present without printing values:

1. `SEAM_DATABASE_URL`
2. `JWT_SECRET`

Restart or redeploy the existing service after file placement and env update.

## Path B - Fallback Source-Files Env Repair

Use only if Path A is blocked and the existing service already has a governed source-file storage path.

Follow PM Lane 270:

`ops/agents/handoffs/2026-05-18-pm-lane-270-render-hosted-source-files-env-repair-executor-copy-paste-prompt.md`

Minimum source env keys:

1. `APEX_PROJECT_MINER_PLANNING_ROOT`
2. `APEX_PROJECT_ESTIMATOR_WORKBOOK`
3. `APEX_PROJECT_SLD_PDF`
4. `APEX_PROJECT_DATA_ENTRY_WORKBOOK`
5. `APEX_REFERENCE_TRACKER_WORKBOOK`
6. `APEX_FIELD_SEED_EQUIPMENT_WORKBOOK`
7. `APEX_FIELD_SEED_CAPABILITY_WORKBOOK`

Use hosted paths only. Do not use Jason's Windows path as a Render env value. Do not commit source workbooks or PDFs to Git. Do not manually read workbook/PDF contents. Do not run macros.

## Read-Only Validation

Run after the existing Render service is live.

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
```

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000
```

Run exact Temp Power readback:

```powershell
@'
import base64
import json
import urllib.request

base = 'https://mutation-seam.apexpowerops.com'
token = base64.b64encode(json.dumps({
    'actor_id': 'pm-001',
    'actor_role': 'pm',
    'project_scope': ['proj-001'],
}).encode('utf-8')).decode('ascii')
headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {token}',
}

def get(path):
    request = urllib.request.Request(f'{base}{path}', headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)

candidate = get('/api/v1/reads/project-import-candidate')
plan = get('/api/v1/reads/project-import-admission-plan')
status = get('/api/v1/reads/project-import-approval-status')

workpackages = candidate.get('workpackages') or []
tasks = [task for workpackage in workpackages for task in workpackage.get('tasks', [])]
apparatus = [
    apparatus_candidate
    for task in tasks
    for apparatus_candidate in task.get('apparatus_candidates', [])
]
expected_warning = 'PROJECT_DATA_ENTRY_FORMULA_ERRORS'
accepted_warnings = (
    plan.get('approval_record_contract', {})
    .get('minimum_expected_values', {})
    .get('accepted_warning_codes', [])
)

assert candidate.get('candidate_id') == 'pm-import-candidate-miner-temp-power', candidate.get('candidate_id')
assert candidate.get('mutation_authority') == 'not_admitted', candidate.get('mutation_authority')
assert len(workpackages) == 7, len(workpackages)
assert len(tasks) == 15, len(tasks)
assert len(apparatus) == 184, len(apparatus)
assert candidate.get('source_freshness', {}).get('aggregate_fingerprint') == 'e111fdbe934bf9de07ed24c1'
assert plan.get('candidate_shape_fingerprint') == 'ddc49565eb586af913ad48b2'
assert expected_warning in accepted_warnings, accepted_warnings
assert plan.get('mutation_authority') == 'not_admitted', plan.get('mutation_authority')
assert status.get('import_authority') == 'not_admitted', status.get('import_authority')

print(json.dumps({
    'candidate_id': candidate.get('candidate_id'),
    'workpackages': len(workpackages),
    'tasks': len(tasks),
    'apparatus_candidates': len(apparatus),
    'source_stat_fingerprint': candidate.get('source_freshness', {}).get('aggregate_fingerprint'),
    'candidate_shape_fingerprint': plan.get('candidate_shape_fingerprint'),
    'warning_code': expected_warning,
    'mutation_authority': candidate.get('mutation_authority'),
    'approval_status_classification': status.get('classification'),
}, sort_keys=True))
'@ | & "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -
```

Also inspect these routes in the Internal browser or terminal without sending mutations:

1. `https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-candidate`
2. `https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-admission-plan`
3. `https://mutation-seam.apexpowerops.com/api/v1/reads/project-import-approval-status`

Do not browse to, script, or send:

`POST /api/v1/mutations/project-import-approvals`

## Closeout File

Create exactly one closeout:

`ops/agents/handoffs/2026-05-18-pm-lane-276-vscode-copilot-render-completion-executor-closeout.md`

The closeout must include:

1. source commit tested,
2. existing Render service name,
3. authenticated surface used, without exposing secrets,
4. selected path: snapshot env deploy or source-files env repair,
5. hosted runtime path used,
6. file placement evidence without payload contents,
7. env var key presence and non-secret path summary,
8. whether a persistent disk, existing runtime path, SSH/SCP, or dashboard shell was used,
9. restart/redeploy evidence,
10. exact validation command outputs,
11. hosted candidate readback summary,
12. final outcome label,
13. guardrail confirmation.

Final outcome must be exactly one of:

1. `RENDER_SNAPSHOT_ENV_DEPLOY_PASS_NO_APPROVAL_POST`
2. `RENDER_SOURCE_FILES_ENV_REPAIR_PASS_NO_APPROVAL_POST`
3. `BLOCKED_RENDER_AUTH_UNAVAILABLE_NO_APPROVAL_POST`
4. `BLOCKED_RENDER_STORAGE_REQUIRES_NEW_RESOURCE_NO_APPROVAL_POST`
5. `BLOCKED_RENDER_RUNTIME_FILE_TRANSFER_UNAVAILABLE_NO_APPROVAL_POST`
6. `BLOCKED_RENDER_DEPLOY_OR_RESTART_FAILED_NO_APPROVAL_POST`
7. `BLOCKED_HOSTED_SNAPSHOT_CHECKSUM_OR_AUTHORITY_MISMATCH_NO_APPROVAL_POST`
8. `BLOCKED_HOSTED_CANDIDATE_STILL_NOT_TEMP_POWER_NO_APPROVAL_POST`

## Not Allowed

- Do not send `POST /api/v1/mutations/project-import-approvals`.
- Do not create an approval row.
- Do not import project rows.
- Do not run SQL writes or schema migrations.
- Do not create a new Render service.
- Do not create public file storage.
- Do not change DNS, custom domains, CORS, auth, ingress, or service topology.
- Do not print, paste, store, rotate, or modify secrets.
- Do not commit source workbooks, source PDFs, runtime snapshots, or hosted payloads.
- Do not run macros.
- Do not write back to source workbooks or source PDFs.
- Do not mutate tasks, owners, due dates, resources, schedules, field records, customer records, production records, finance records, billing, payroll, invoice, accounting, or other PM business state.

Commit and push only the executor closeout file if a closeout is created. Then fast-forward Olares and confirm `bash tools/ai/run-minimal-mcp-trio.sh status` returns `{"status":"not-running"}`.
