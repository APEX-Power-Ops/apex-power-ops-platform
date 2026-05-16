# PM Lane 037 Handoff - Render-Authenticated PM Intake Mutation-Seam Redeploy Gate

Date: 2026-05-15
Status: Ready for Render-authenticated executor
Scope: existing Render mutation-seam deployment parity for Project Miner PM intake reads

## Executive Summary

PM Lane 037 is the current Render-authenticated backend parity packet for the Project Miner PM intake workflow.

PM Lane 036 proved the Vercel UI is live at:

1. `https://operations.apexpowerops.com/pm-review/import-candidate`
2. `https://operations.apexpowerops.com/pm-review/import-admission-plan`

The remaining hosted blocker is Render mutation-seam:

1. `https://mutation-seam.apexpowerops.com/health` returns `200`,
2. hosted OpenAPI omits both new PM intake read paths,
3. both PM intake read routes return `404`,
4. hosted schedule reads still return `500`.

This packet supersedes the older PM Lane 012 workfront-focused Render handoff for the current intake blocker. PM Lane 012 remains useful precedent; PM Lane 037 is the updated executor prompt.

## What Changed In This Repo

`apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py` now accepts:

```powershell
--include-pm-intake
```

That flag keeps the existing default smoke behavior unchanged, then adds backend-only validation for:

1. OpenAPI registration of `/api/v1/reads/project-import-candidate`,
2. OpenAPI registration of `/api/v1/reads/project-import-admission-plan`,
3. `GET /api/v1/reads/project-import-candidate`,
4. `GET /api/v1/reads/project-import-admission-plan`,
5. `mutation_authority: not_admitted` on both PM intake payloads.

## Coordinator Evidence

Workstation starting head for this packet:

```text
4eca3dcc6b8d93b687b187a31d58188179ca8f22
```

Render credentials remain unavailable in this Codex workspace:

```text
RENDER_API_KEY=false
RENDER_TOKEN=false
RENDER_SERVICE_ID=false
RENDER_OWNER_ID=false
RENDER_WORKSPACE_ID=false
render CLI=false
```

Authoritative Render blueprint:

```text
C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\render.yaml
```

Existing Render service:

```text
apex-platform-mutation-seam
```

Target public host:

```text
https://mutation-seam.apexpowerops.com
```

## Local Validation

Commands run from `C:/APEX Platform/apex-power-ops-platform`.

```powershell
.venv/Scripts/python.exe -m py_compile apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py
```

Result:

passed

```powershell
.venv/Scripts/python.exe apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --help
```

Result:

help output includes `--include-pm-intake`

```powershell
.venv/Scripts/python.exe apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com --include-pm-intake
```

Result:

```text
health status=200 detail=ok
root status=200 detail=ok
reads_approval_queue status=200 detail=ok
schedule_projects status=500 detail=Internal Server Error
schedule_drivers status=500 detail=Internal Server Error
schedule_tracer status=500 detail=Internal Server Error
schedule_variance status=500 detail=Internal Server Error
openapi status=200 detail=ok
project_import_candidate status=404 detail=Not Found
project_import_admission_plan status=404 detail=Not Found
RESULT FAIL
FAILURE schedule_projects returned unexpected status 500
FAILURE schedule_drivers returned unexpected status 500
FAILURE schedule_tracer returned unexpected status 500
FAILURE schedule_variance returned unexpected status 500
FAILURE openapi missing /api/v1/reads/project-import-admission-plan
FAILURE openapi missing /api/v1/reads/project-import-candidate
FAILURE project_import_candidate returned framework 404 Not Found
FAILURE project_import_admission_plan returned framework 404 Not Found
```

This is the expected current hosted failure and should turn green only after the Render service is current.

```powershell
$env:SEAM_STORE_BACKEND='memory'
.venv/Scripts/python.exe -m pytest apps/mutation-seam/tests/test_project_import_candidate.py apps/mutation-seam/tests/test_project_import_admission_plan.py -q
```

Result:

`4 passed`

```powershell
.venv/Scripts/python.exe -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-037-render-authenticated-pm-intake-seam-redeploy-gate.json', encoding='utf-8')); print('packet-json-ok')"
```

Result:

`packet-json-ok`

Scoped `git diff --check` passed for the Lane 037 authoring file set.

## Executor Prompt

Copy/paste the following prompt into a Render-authenticated Codex or Claude Code executor:

```text
You are executing PM Lane 037 for Apex Power Ops as a bounded Render-authenticated hosted-runtime executor.

Repository:
C:\APEX Platform\apex-power-ops-platform

Authoritative packet:
C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-15-pm-lane-037-render-authenticated-pm-intake-seam-redeploy-gate.json

Handoff:
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-037-render-authenticated-pm-intake-seam-redeploy-gate-handoff.md

Read first:
1. C:\APEX Platform\apex-power-ops-platform\docs\authority\APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.md
2. C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-036-hosted-pm-intake-parity-handoff.md
3. C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\render.yaml
4. C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\scripts\smoke_deployed_mutation_seam.py
5. C:\APEX Platform\apex-power-ops-platform\apps\operations-web\scripts\smoke-pm-intake-hosted.mjs

Target existing Render service:
apex-platform-mutation-seam

Target public host:
https://mutation-seam.apexpowerops.com

Required source:
current origin/clean-main. At minimum, deployment must be later than PM Lane 036 starting head 4eca3dcc6b8d93b687b187a31d58188179ca8f22 and must include the PM intake read routes plus this PM Lane 037 handoff.

Your task:
1. Inspect existing Render service apex-platform-mutation-seam.
2. Confirm the service uses repository jasonlswenson-sys/apex-power-ops, branch clean-main, working directory apps/mutation-seam, and current origin/clean-main.
3. Confirm deployment metadata matches apps/mutation-seam/render.yaml: build command pip install -r requirements.txt, start command uvicorn app.main:app --host 0.0.0.0 --port $PORT, health path /health, and autoDeploy true.
4. Confirm non-secret env posture only: SEAM_STORE_BACKEND=postgres and key presence for SEAM_DATABASE_URL, JWT_SECRET, CORS_ORIGINS, APP_ENV, LOG_LEVEL, and PYTHON_VERSION. Do not print secret values.
5. If the service is stale or metadata does not match the app-local blueprint, repair only existing deployment metadata needed to match this packet and trigger a redeploy from clean-main.
6. After redeploy, run the read-only validation commands below.
7. If PM intake reads still return 404 or schedule reads still return 500, inspect Render logs only far enough to classify the blocker as stale deployment, DSN, schema, permission, runtime import, or other deployment failure. Stop before SQL writes, schema migrations, secret rotation, fixture replay, or live business-state mutation.
8. Update only the allowed closeout surfaces with exact evidence and verdict.

Allowed write scope:
C:\APEX Platform\apex-power-ops-platform\PROJECT_STATUS.md
C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\DEPLOYMENT_VALIDATION.md
C:\APEX Platform\apex-power-ops-platform\apps\operations-web\DEPLOYMENT_VALIDATION.md
C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-15-pm-lane-037-render-authenticated-pm-intake-seam-redeploy-gate.json
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-037-render-authenticated-pm-intake-seam-redeploy-gate-handoff.md

Validation commands:
git rev-parse HEAD
git ls-remote origin clean-main

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com --include-pm-intake

corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-intake-hosted.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000

$env:SEAM_STORE_BACKEND='memory'
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_import_candidate.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_project_import_admission_plan.py" -q

Stop conditions:
1. Render auth is unavailable.
2. The repair would require a new Render service, DNS change, auth change, ingress widening, secret rotation, SQL write, schema migration, fixture replay, or live mutation.
3. Logs point to a product-code bug rather than stale deployment metadata.
4. Hosted proof requires a live mutation test.

Do not stage unrelated residue such as .playwright-mcp/ or output/.
```

## Guardrails Preserved

This packet does not authorize:

1. product code changes in the Render executor lane,
2. new Render service admission,
3. SQL or schema migration,
4. live database write,
5. production import,
6. approval persistence,
7. workbook writeback,
8. workbook macro execution,
9. auth or ingress widening,
10. Vercel promotion,
11. package dependency addition,
12. import mutation,
13. assignment mutation,
14. schedule mutation,
15. status mutation,
16. autonomous AI business-state mutation.

## Product Queue After Hosted Parity

Once PM Lane 037 closes with hosted PM intake live-data proof green or a precise log-backed blocker, the next PM product lane should be approval persistence design for the reviewed import candidate. That lane must remain separate from the Render deployment packet and must not import project rows.

The sidecar recommendation for that next product lane is captured at:

`ops/agents/handoffs/2026-05-15-pm-lane-038-sidecar-import-approval-persistence-design-scout-handoff.md`
