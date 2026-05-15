# PM Lane 012 Handoff - Render-Authenticated Mutation-Seam Redeploy And Live-Data Proof Gate

Date: 2026-05-15
Status: Ready for Render-authenticated executor
Packet: `2026-05-15-pm-lane-012`
Scope: existing Render mutation-seam deployment parity and read-only hosted PM proof

## Summary

PM Lane 011 proved that operations-web production is current and that the remaining hosted PM blocker lives in the mutation-seam Render runtime.

PM Lane 012 is the bounded executor packet for the next move: use an authenticated Render surface for existing service `apex-platform-mutation-seam`, confirm or repair only deployment metadata, redeploy current `clean-main`, and rerun read-only hosted PM proof.

No product code, SQL, schema migration, live database write, auth widening, ingress widening, new service admission, Vercel promotion, schedule mutation, assignment mutation, Operations Visibility reopening, or autonomous AI business-state mutation is authorized.

## Coordinator Preflight

Current local repo head:

```text
18b16fe0e2fd4a7dbaa57652c177d4327b51b1b5
```

Existing untracked residue remains unrelated and should stay untouched:

```text
.playwright-mcp/
output/
```

Render credentials are not available in the local shell:

```text
RENDER_API_KEY=false
RENDER_TOKEN=false
RENDER_SERVICE_ID=false
RENDER_OWNER_ID=false
RENDER_WORKSPACE_ID=false
```

The authoritative Render blueprint is app-local:

```text
C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\render.yaml
```

There is no root-level `C:\APEX Platform\apex-power-ops-platform\render.yaml`.

## Current Hosted Failure

The coordinator re-probed both hosted seam hosts on 2026-05-15:

1. `https://mutation-seam.apexpowerops.com/health` -> `200`
2. `https://apex-platform-mutation-seam.onrender.com/health` -> `200`
3. both OpenAPI documents still omit `/api/v1/reads/pm-workfront`
4. both `/api/v1/reads/pm-workfront` probes return `404`
5. both schedule project and driver reads return `500`
6. both narrowed no-op decision-history reads return `200 []`

The repo-owned deployed seam smoke also fails read-only:

```text
health status=200 detail=ok
root status=200 detail=ok
reads_approval_queue status=200 detail=ok
schedule_projects status=500 detail=Internal Server Error
schedule_drivers status=500 detail=Internal Server Error
schedule_tracer status=500 detail=Internal Server Error
schedule_variance status=500 detail=Internal Server Error
RESULT FAIL
```

## Orchestration Inputs

Two read-only scouts informed this packet:

1. Render deployability scout `019e2c7b-6d25-7023-94d8-dfd06a2ea9ac` confirmed the root Render blueprint is absent, `apps/mutation-seam/render.yaml` is the actual service blueprint, and no repo-owned Render CLI/API redeploy or log-inspection command exists.
2. PM backlog scout `019e2c7b-9398-7782-b73a-c65492d612c5` confirmed hosted mutation-seam parity is the blocker before additional hosted PM product proof, and queued PM product follow-ons behind this gate.

## Executor Prompt

Copy/paste the following prompt into a Render-authenticated Codex or Claude Code executor:

```text
You are executing PM Lane 012 for Apex Power Ops as a bounded Render-authenticated hosted-runtime executor.

Repository:
C:\APEX Platform\apex-power-ops-platform

Authoritative packet:
C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-15-pm-lane-012-render-authenticated-mutation-seam-redeploy-and-live-data-proof-gate.json

Handoff:
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-012-render-authenticated-mutation-seam-redeploy-and-live-data-proof-gate-handoff.md

Read first:
1. C:\APEX Platform\apex-power-ops-platform\docs\authority\APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.md
2. C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-011-operations-web-promotion-and-hosted-seam-drift-isolation-handoff.md
3. C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\DEPLOYMENT_VALIDATION.md
4. C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\render.yaml
5. C:\APEX Platform\apex-power-ops-platform\apps\operations-web\DEPLOYMENT_VALIDATION.md

Target existing Render service:
apex-platform-mutation-seam

Target public host:
https://mutation-seam.apexpowerops.com

Required current repo head:
18b16fe0e2fd4a7dbaa57652c177d4327b51b1b5 or later on clean-main

Your task:
1. Inspect existing Render service apex-platform-mutation-seam.
2. Confirm the service uses repository jasonlswenson-sys/apex-power-ops, branch clean-main, working directory apps/mutation-seam, and deployed commit 18b16fe0e2fd4a7dbaa57652c177d4327b51b1b5 or later.
3. Confirm deployment metadata matches apps/mutation-seam/render.yaml: build command pip install -r requirements.txt, start command uvicorn app.main:app --host 0.0.0.0 --port $PORT, health path /health, and autoDeploy true.
4. Confirm non-secret env posture only: SEAM_STORE_BACKEND=postgres and key presence for SEAM_DATABASE_URL, JWT_SECRET, CORS_ORIGINS, APP_ENV, LOG_LEVEL, and PYTHON_VERSION. Do not print secret values.
5. If the service is stale or metadata does not match the app-local blueprint, repair only existing deployment metadata needed to match this packet and trigger a redeploy from clean-main.
6. After redeploy, run the read-only validation commands below.
7. If schedule reads still return 500, inspect Render logs only far enough to classify the blocker as DSN, schema, permission, runtime import, or other deployment failure. Stop before SQL writes, schema migrations, secret rotation, fixture replay, or live business-state mutation.
8. Update only the allowed closeout surfaces with the exact evidence and verdict.

Allowed write scope:
C:\APEX Platform\apex-power-ops-platform\PROJECT_STATUS.md
C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\DEPLOYMENT_VALIDATION.md
C:\APEX Platform\apex-power-ops-platform\apps\operations-web\DEPLOYMENT_VALIDATION.md
C:\APEX Platform\apex-power-ops-platform\ops\agents\packets\draft\2026-05-15-pm-lane-012-render-authenticated-mutation-seam-redeploy-and-live-data-proof-gate.json
C:\APEX Platform\apex-power-ops-platform\ops\agents\handoffs\2026-05-15-pm-lane-012-render-authenticated-mutation-seam-redeploy-and-live-data-proof-gate-handoff.md

Validation commands:
git rev-parse HEAD
git ls-remote origin clean-main

& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py" --base-url https://mutation-seam.apexpowerops.com

corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web exec node scripts/smoke-pm-live-data.mjs --operations-web-base-url https://operations.apexpowerops.com --mutation-seam-base-url https://mutation-seam.apexpowerops.com --timeout-ms 20000

$env:SEAM_STORE_BACKEND='memory'
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -m pytest "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_pm_workfront_read_model.py" "C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam/tests/test_schedule_bridge.py" -q

Stop conditions:
1. Render auth is unavailable.
2. The repair would require a new Render service, DNS change, auth change, ingress widening, secret rotation, SQL write, schema migration, fixture replay, or live mutation.
3. Logs point to a product-code bug rather than stale deployment metadata.
4. Hosted proof requires a live mutation test.

Do not stage unrelated residue such as .playwright-mcp/ or output/.
```

## Product Queue After Hosted Parity

Once PM Lane 012 closes with hosted PM live-data proof green or with a precisely classified deployment blocker, the next product slices are:

1. PM Lane 013 - workfront schedule drillthrough in `apps/operations-web/app/pm-review/workfront/page.tsx` plus focused Playwright proof.
2. PM Lane 014 - approval escalation scoped history in `apps/operations-web/app/pm-review/approval/page.tsx` plus approval-context Playwright proof.
3. PM Lane 015 - workfront readiness enrichment in `apps/mutation-seam/app/pm_workfront_read_model.py` plus focused backend proof.

Keep those product slices separate from the Render-authenticated deployment packet.
