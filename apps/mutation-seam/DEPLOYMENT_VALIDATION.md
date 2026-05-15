# Mutation Seam Deployment Validation

This runbook defines the bounded public-host and ingress contract for `apps/mutation-seam`.

## Core Principle

Public PM runtime proof requires both of these conditions to be true for the same target environment:

1. the mutation seam itself is reachable on its public host
2. `apps/operations-web` proxies the PM-facing `/api/v1/{reads,schedule,mutations}` routes to that host

Static PM pages calling same-origin `/api/v1/*` are not sufficient proof unless the rewrite contract and the seam host are both executable.

## Public Host Contract

The repo-owned target public host for this service is:

```text
https://mutation-seam.apexpowerops.com
```

The repository now includes a Render blueprint at `render.yaml` for this host shape.

Default Render service shape:

1. type: Python web service
2. build command: `pip install -r requirements.txt`
3. start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. health check path: `/health`
5. PM/browser origins admitted through `CORS_ORIGINS`

Recommended deployment sequence:

1. create a new Render Web Service from this repository or import the blueprint
2. confirm the service uses `apps/mutation-seam` as the working directory
3. set the required runtime environment variables from `.env.example` plus hosted values below
4. set `SEAM_STORE_BACKEND=postgres` for the hosted path
5. deploy the service and confirm `GET /health` returns `200`
6. attach the custom domain `mutation-seam.apexpowerops.com`
7. add the DNS record in GoDaddy using the Render-provided target
8. run the deployed seam smoke against the public host

Required hosted variables:

1. `APP_ENV=production`
2. `LOG_LEVEL=INFO`
3. `JWT_SECRET`
4. `SEAM_DATABASE_URL`
5. `CORS_ORIGINS=https://operations.apexpowerops.com,https://mutation-seam.apexpowerops.com`

## Local Proof

From `C:/APEX Platform/apex-power-ops-platform/apps/mutation-seam` run:

```powershell
python -m pytest tests/test_schedule_bridge.py
python validate.py --base-url http://localhost:8000
```

Pass conditions:

1. schedule bridge tests pass
2. the local mutation/read harness completes without route-level failures

## Public Host Proof

From `C:/APEX Platform/apex-power-ops-platform` run:

```powershell
python apps/mutation-seam/scripts/smoke_deployed_mutation_seam.py --base-url https://mutation-seam.apexpowerops.com
```

Pass conditions:

1. `/health` returns `200`
2. `/api/v1/reads/approval-queue` returns `200`
3. `/api/v1/schedule/projects` does not framework-404; `200` and `503` both count as route-present
4. `/api/v1/schedule/drivers`, `/api/v1/schedule/tracer`, and `/api/v1/schedule/variance` do not framework-404
5. the script ends with `RESULT PASS`

Fail conditions:

1. the public host is missing entirely
2. the PM read/schedule routes return framework `404 Not Found`
3. the service boots but only exposes `/health` without the PM seam routes

Current public-host status on 2026-05-15:

1. `https://mutation-seam.apexpowerops.com/health` returns `200`.
2. `https://mutation-seam.apexpowerops.com/openapi.json` does not advertise `/api/v1/reads/pm-workfront`, even though the current repo code mounts that route.
3. `https://mutation-seam.apexpowerops.com/api/v1/reads/pm-workfront` returns framework `404`.
4. deployed schedule reads return `500` for `projects`, `drivers`, `tracer`, and `variance`.
5. the smallest remediation path is deployment-first: inspect the Render service `apex-platform-mutation-seam`, confirm it deploys `clean-main` at `3e8bba2d063a7a7227eeae22967d1430349f0546` or later from `apps/mutation-seam`, redeploy the current head, then use Render logs to distinguish any remaining schedule DSN/schema/permission failure.
6. without Render credentials, this workspace can run read-only public probes and GitHub smoke workflows, but it cannot inspect Render deploy commit, trigger a Render redeploy, view Render logs, or confirm hosted environment variables.

## Operations Web Ingress Contract

`apps/operations-web` now owns the same-origin ingress layer for PM surfaces through Next rewrites.

Required server-side environment variable on the Vercel host:

```text
MUTATION_SEAM_BASE_URL=https://mutation-seam.apexpowerops.com
```

This value is server-side only. Do not expose it as a `NEXT_PUBLIC_*` browser variable.

The rewrite contract covers:

1. `/api/v1/reads/:path*`
2. `/api/v1/schedule/:path*`
3. `/api/v1/mutations/:path*`

Pass conditions:

1. the public seam host passes the deployed seam smoke
2. `operations-web` is rebuilt with `MUTATION_SEAM_BASE_URL` set to the public seam host
3. PM static pages on `https://operations.apexpowerops.com` stop returning `404` for those same-origin paths

## Automated Hosted Smoke

The repository includes `.github/workflows/deployed-mutation-seam-smoke.yml` for:

1. manual validation after deploy
2. repository-dispatch validation after hosted deployment automation lands
3. scheduled regression checks against the public seam host
