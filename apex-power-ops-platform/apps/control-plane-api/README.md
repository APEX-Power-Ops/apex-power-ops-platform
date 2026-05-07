# Control Plane API

This app is the first controlled import of the historical `tcc_v5_backend` runtime lineage into the Apex Power Ops platform bootstrap.

Current posture:
- runtime compatibility import, not final architecture
- historical source lineage traces back to `tcc_v5_backend`, but current operator work should treat this platform root as the live implementation surface
- schema alignment and functional remapping are intentionally deferred until the broader platform work-package model is ratified

This app currently hosts:
- FastAPI runtime and routing surfaces
- auth, MCP, and control-plane endpoints
- demo pages and operational scripts
- transitional local ORM compatibility and runtime surfaces needed to preserve continuity while shared packages are hardened

## Authority Note

This repository owns runtime implementation, not final TCC architecture authority.

For any work that touches platform data ownership, TCC schema meaning, family selection, routing semantics, or backend contract validity, start with the platform authority stack and then the older TCC authority documents when needed:

1. `C:/APEX Platform/Platform-Authority/`
2. `docs/authority/CONTROL-PLANE-CALC-BOUNDARY-MAP-2026-04-12.md`
3. `docs/authority/CONTROL-PLANE-CALC-SCHEMA-MAPPING-2026-04-12.md`
4. `Development/Architecture/TCC-MASTER-SCHEMA-AUTHORITY.md`
5. `Development/Architecture/TCC-DLL-ARCHITECTURE-AUTHORITY.md`

This backend should be treated as a consumer and implementation surface for that governed architecture, not as a competing source of truth.

## Import Status

The platform bootstrap now carries this app under `apps/control-plane-api` and a parallel calc-domain extraction under `packages/calc-engine`.

The extracted calc package is now the intended implementation source. The local `services/calc_engine` modules remain only as compatibility shims for legacy import paths while the remaining app-local dependencies are retired.

## Project Structure

```
apps/control-plane-api/
├── models/          # SQLAlchemy ORM models
├── services/        # Business logic, auth, MCP, and app-local calc routing over shared calc shims
├── api/             # FastAPI endpoints
├── tests/           # Unit and integration tests
├── utils/           # Utility functions
├── config.py        # Database configuration
└── .env             # Environment variables (not in git)
```

## Setup

1. Preferred: activate the platform-root virtual environment from the Olares-hosted platform root:
   ```
   cd /home/olares/code/apex/apex-power-ops-platform
   source .venv/bin/activate
   ```

   Windows client fallback:
   ```
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

   Legacy fallback: activate another compatible environment and ensure it has this app's requirements plus the editable calc package installed.

2. If the root `.venv` does not exist yet, bootstrap it from the platform root.

   Olares-hosted example:
   ```
   cd /home/olares/code/apex/apex-power-ops-platform
   python -m venv .venv
   .venv/bin/python -m pip install --upgrade pip setuptools wheel
   cd apps/control-plane-api
   ../../.venv/bin/python -m pip install -r requirements-dev.txt
   ```

   Windows client fallback:
   ```
   python -m venv .venv
   .venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
   cd apps\control-plane-api
   ..\..\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
   ```

3. Install runtime dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Install dev and test dependencies for local work:
   ```
   pip install -r requirements-dev.txt

   For monorepo work, install the extracted calc package separately when you want to exercise or evolve the shared package boundary:

   ```
   pip install -e ../../packages/calc-engine[test]
   ```
   ```

5. Create a local `.env` from `.env.example` and set the canonical environment values for your target mode.

   Local runtime:
   ```
   DATABASE_URL
   SUPABASE_URL
   SUPABASE_ANON_KEY
   SUPABASE_SERVICE_ROLE_KEY
   SUPABASE_JWKS_URL
   APP_ENV
   LOG_LEVEL
   ```

   Local migration or admin utilities:
   ```
   DATABASE_URL_LOCAL
   SOURCE_DATABASE_URL
   DATABASE_URL_DIRECT
   ```
   `DATABASE_URL_DIRECT` should stay reserved for admin-only operations that cannot run safely through the pooler.

   Hosted deployment:
   ```
   DATABASE_URL
   SUPABASE_URL
   SUPABASE_ANON_KEY
   SUPABASE_SERVICE_ROLE_KEY
   SUPABASE_JWKS_URL
   APP_ENV
   LOG_LEVEL
   ```
   Do not enable local test auth outside local development.

6. Optional but recommended for Magic Link auth in the demo page:
   ```
   SUPABASE_EMAIL_REDIRECT_URL
   ```
   If omitted, the backend defaults the redirect target to `/demo/neta-tcc` on the current host.

7. Optional public Desktop activation settings for the governed remote control-plane surface:
   ```
   PUBLIC_MCP_BASE_URL
   PUBLIC_OAUTH_AUTHORIZATION_URL
   PUBLIC_OAUTH_TOKEN_URL
   PUBLIC_OAUTH_JWKS_URL
   PUBLIC_OAUTH_CLIENT_ID
   PUBLIC_OAUTH_REDIRECT_URIS
   PUBLIC_OAUTH_SCOPES
   ```
   These stay unset until a real public host exists. When configured, the backend exposes a metadata-only MCP root at `/mcp`, a standard OAuth discovery document at `/.well-known/oauth-authorization-server`, and a machine-readable operator surface at `/api/v1/auth/public-desktop-config`.
   For the current platform settings, ChatGPT connector requirements, Supabase mapping, and Auth0 target settings, use `MCP_OAUTH_PLATFORM_SETTINGS.md` as the primary runbook.

   Optional dedicated Supabase MCP surface:
   ```
   SUPABASE_MCP_PUBLIC_BASE_URL
   SUPABASE_MCP_OAUTH_AUTHORIZATION_URL
   SUPABASE_MCP_OAUTH_TOKEN_URL
   SUPABASE_MCP_OAUTH_JWKS_URL
   SUPABASE_MCP_OAUTH_CLIENT_ID
   SUPABASE_MCP_OAUTH_REDIRECT_URIS
   SUPABASE_MCP_OAUTH_SCOPES
   SUPABASE_ALLOWED_PROJECTS_JSON
   SUPABASE_MANAGEMENT_API_URL
   SUPABASE_MANAGEMENT_TOKEN
   SUPABASE_ALLOWED_MIGRATION_ROOTS
   SUPABASE_ALLOWED_FUNCTION_ROOTS
   SUPABASE_ENABLE_MIGRATION_APPLY
   SUPABASE_ENABLE_EDGE_FUNCTION_DEPLOY
   SUPABASE_CLI_PROJECT_DIR
   SUPABASE_CLI_PATH
   SUPABASE_CLI_TIMEOUT_SECONDS
   SUPABASE_ACCESS_TOKEN
   ```
   When configured, the backend exposes a second MCP transport at `/supabase-mcp` with its own OAuth discovery surface under `/supabase-mcp/.well-known/`.
   The management token is required for advisory notices, service logs, database branch listing and creation, and publishable key inspection.
   The two confirmed-write execution tools are additionally env-gated on purpose:
   `apply_repo_migration` requires `SUPABASE_ENABLE_MIGRATION_APPLY=true`, and `deploy_edge_function_from_repo` requires `SUPABASE_ENABLE_EDGE_FUNCTION_DEPLOY=true` plus a working Supabase CLI host configuration.
   Edge Function deployment also requires `SUPABASE_ACCESS_TOKEN` and a valid CLI project layout rooted at `SUPABASE_CLI_PROJECT_DIR`, with functions present under `supabase/functions/<function_name>`.

   Optional dedicated GitHub MCP surface:
   ```
   GITHUB_MCP_PUBLIC_BASE_URL
   GITHUB_MCP_OAUTH_AUTHORIZATION_URL
   GITHUB_MCP_OAUTH_TOKEN_URL
   GITHUB_MCP_OAUTH_JWKS_URL
   GITHUB_MCP_OAUTH_CLIENT_ID
   GITHUB_MCP_OAUTH_REDIRECT_URIS
   GITHUB_MCP_OAUTH_SCOPES
   GITHUB_ALLOWED_REPOS_JSON
   GITHUB_APP_ID
   GITHUB_APP_PRIVATE_KEY
   GITHUB_APP_INSTALLATION_IDS_JSON
   GITHUB_ALLOWED_WORKFLOW_DISPATCHES_JSON
   GITHUB_COPILOT_REVIEWERS_JSON
   ```
   When configured, the backend exposes a third MCP transport at `/github-mcp` with its own OAuth discovery surface under `/github-mcp/.well-known/`.

8. Optional but recommended for unattended AI/browser testing in local development:
   ```
   ENABLE_LOCAL_TEST_AUTH
   LOCAL_TEST_AUTH_SECRET
   LOCAL_TEST_AUTH_USERS_JSON
   ```
   When enabled outside production, the backend exposes a localhost-only test-session bootstrap for deterministic test users so browser automation can authenticate without Email Magic Link mailbox access.

9. Test database connection:
   ```
   python config.py
   ```

10. For Email Magic Link auth in the demo page, configure Supabase Dashboard to allow the redirect URL used above and set the Magic Link email template to send users back to that route.
   Recommended template target: `{{ .RedirectTo }}?token_hash={{ .TokenHash }}&type=email`

11. Keep `.env` local-only. The backend repo ignores `.env` and `.env.local`, and the tracked contract lives in `.env.example`.

## Platform-First Operation

When working inside the bootstrap root, prefer these commands from `/home/olares/code/apex/apex-power-ops-platform`:

```
./apps/control-plane-api/scripts/run_platform_api_local.ps1
./apps/control-plane-api/scripts/run_platform_api_local.ps1 -Restart
.venv/bin/python -m uvicorn main:app --app-dir apps/control-plane-api --host 0.0.0.0 --port 8010
.venv/bin/python -m pytest apps/control-plane-api/tests/test_control_plane.py -q
.venv/bin/python apps/control-plane-api/scripts/smoke_remote_control_plane_authoring_queue.py --task-id <task> --target-path <path> --content <text> --dry-run
```

Windows client fallback:

```
.\apps\control-plane-api\scripts\run_platform_api_local.ps1
.\apps\control-plane-api\scripts\run_platform_api_local.ps1 -Restart
.venv\Scripts\python.exe -m uvicorn main:app --app-dir apps/control-plane-api --host 0.0.0.0 --port 8010
.venv\Scripts\python.exe -m pytest apps/control-plane-api/tests/test_control_plane.py -q
.venv\Scripts\python.exe apps/control-plane-api/scripts/smoke_remote_control_plane_authoring_queue.py --task-id <task> --target-path <path> --content <text> --dry-run
```

The VS Code workspace tasks are now aligned to that same root-first workflow and prefer the root `.venv` automatically.

When attached through VS Code Remote-SSH or `ssh olares-mesh`, prefer originating this workflow from the Olares-hosted parent-root mirror rather than the Windows client surface.

## Schema Drift Check

Use the local drift check before or after forward schema changes:

```
python scripts/check_schema_drift.py
```

What it checks:

1. model tables missing from the live schema
2. unexpected extra live `tcc_` tables outside the accepted Phase 3 allowlist
3. whether `tcc_test_plans.user_id` is still non-nullable in live schema
4. whether row-level security remains enabled on `tcc_test_plans` and `tcc_test_results`

Use `scripts/inspect_live_schema.py` when you need the fuller inspection narrative. Use `scripts/check_schema_drift.py` for the bounded pass or fail signal during migration work.

For the bounded Phase 3 LV breaker family validation packet, also run:

```
python scripts/validate_lv_breaker_phase3_families.py
```

That script is read-only. It validates current live ETU, MAINT, TMT, and EMT family surfaces against the active LV breaker completion scope and reports a documentary-only rollback-boundary policy rather than automating rollback or legacy backfill behavior.

## Deployed Control-Plane Smoke Validation

For the public Render-hosted control-plane surface, use:

```
python scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com
python scripts/smoke_deployed_control_plane.py --base-url https://control.apexpowerops.com --skip-authenticated-checks --require-apparatus-study-route
```

Workspace task shortcut:

1. use the root workspace task `Control-plane public apparatus-route gate` to run the public apparatus-route promotion gate against `https://control.apexpowerops.com`
2. that task is expected to fail until the deployed public host actually carries the governed apparatus study-resource route

Local readiness shortcut:

1. use the root workspace task `Control-plane local host readiness` before attempting workstation-level host validation
2. that readiness probe closes as `host-ready` on the current workstation; it falls back to `host-readiness-blocked` only when `.env` is absent, core runtime values still match template placeholders, recommended local auth/runtime values are incomplete, or the backend still fails import locally
3. use the root workspace task `Bootstrap control-plane local env` only to materialize the tracked template locally; copied placeholders do not count as configured runtime values
4. once `Run platform API local` is active, use the root workspace task `Control-plane local apparatus-route smoke` to validate the bounded local apparatus seam against `http://127.0.0.1:8010`
5. that local-runtime smoke intentionally validates only health, readiness, OpenAPI, and the governed apparatus route; it does not require public OAuth discovery, public MCP metadata, or local control-plane auth-surface behavior to pass
6. when the existing local `8010` host must pick up `.env` or auth/runtime changes, use the root workspace task `Restart platform API local` instead of assuming rerunning the original task replaced the old process
7. `Run platform API local` now fails fast with a clear instruction when `8010` is already occupied; the task-backed helper is `apps/control-plane-api/scripts/run_platform_api_local.ps1`

The script validates:

1. `GET /health`
2. `GET /health/ready`
3. OAuth discovery at `/.well-known/oauth-authorization-server`
4. public MCP metadata at `/mcp`
5. unauthenticated `401 Bearer` behavior on `/api/v1/control-plane/task-packets`
6. authenticated read-only control-plane list and detail routes using either:
   a. a provided bearer token
   b. a disposable confirmed Supabase user minted and deleted for the run
7. optional apparatus study-resource route presence and deployed OpenAPI advertisement when `--require-apparatus-study-route` is set

For a workstation-local host instead of the public-host contract, use:

```
python scripts/smoke_deployed_control_plane.py --base-url http://127.0.0.1:8010 --local-runtime --skip-authenticated-checks --require-apparatus-study-route
```

In local-runtime mode, `503` remains an acceptable apparatus-route result when the governed route is present but the local database is still intentionally migration-gated.

The no-auth apparatus-route mode is intended for release promotion checks where the new backend route must be present on the public host before end-to-end browser seam proof can proceed, even if authenticated smoke credentials are not available in the current workstation session.

For the full operational procedure and expected pass conditions, see `DEPLOYMENT_VALIDATION.md`.

Automation:

1. `.github/workflows/deployed-control-plane-smoke.yml`
2. supports manual runs through `workflow_dispatch`
3. supports reuse from another workflow through `workflow_call`
4. runs nightly on a schedule for ongoing production drift detection
5. supports external `repository_dispatch` calls for deploy-coupled validation without binding directly to `push`
6. accepts an optional initial wait window before the first validation attempt
7. intentionally does not run on `push`, because Render auto-deploy timing can race a GitHub-side smoke check
8. retries automatically before failing to absorb transient rollout timing
9. uploads the smoke output as a workflow artifact for diagnosis
10. uses `PUBLIC_CONTROL_PLANE_BEARER_TOKEN` when present, otherwise falls back to disposable-user auth with:
   `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY`
11. can send optional Slack-compatible failure alerts through `CONTROL_PLANE_SMOKE_ALERT_WEBHOOK_URL` for scheduled or deploy-dispatch runs
12. external `repository_dispatch` callers must provide a GitHub token with permission to send dispatch events, typically through `GITHUB_REPOSITORY_DISPATCH_TOKEN`

Dispatch helper:

1. `scripts/dispatch_deployed_control_plane_smoke.py`
2. sends the `repository_dispatch` event expected by the workflow
3. accepts `--base-url`, `--initial-wait-seconds`, optional deploy metadata, and `--require-apparatus-study-route` when promotion depends on the governed apparatus study-resource seam
4. requires either `--token` or a configured `GITHUB_REPOSITORY_DISPATCH_TOKEN` environment variable for real dispatches; `--dry-run` does not require credentials

Dedicated connector readiness helper:

1. `scripts/check_dedicated_mcp_surfaces.py`
2. validates the local env contract for `/supabase-mcp` and `/github-mcp`
3. can optionally probe deployed discovery and protected-resource endpoints for each dedicated surface
4. supports `--require-ready` and `--require-write-ready` so operator validation can distinguish OAuth readiness from confirmed-write readiness
5. GitHub Actions workflow: `.github/workflows/dedicated-mcp-surface-readiness.yml`
6. repository-dispatch helper: `scripts/dispatch_dedicated_mcp_surface_check.py`

Example PowerShell usage:

```
python scripts/check_dedicated_mcp_surfaces.py --require-ready
python scripts/check_dedicated_mcp_surfaces.py --require-ready --require-write-ready --supabase-base-url https://supabase-mcp.apexpowerops.com --github-base-url https://github-mcp.apexpowerops.com
python scripts/dispatch_dedicated_mcp_surface_check.py --initial-wait-seconds 90 --require-write-ready --deploy-id render-dedicated-mcp-latest
```

## Local Test Auth For AI-Operated Browser Testing

The demo now supports a local-only test auth mode for unattended browser automation.

Behavior:

1. disabled in production
2. enabled only when `ENABLE_LOCAL_TEST_AUTH=true`
3. available only to localhost callers via `POST /api/v1/auth/test-session`
4. signs in deterministic test users without mailbox access
5. issues local `HS256` test tokens that the backend accepts only while local test auth is enabled

Default local test users:

1. `neta-test-a@example.com`
2. `neta-test-b@example.com`

Browser workflow:

1. open `/demo/neta-tcc`
2. choose a user from the `Use Test User` selector in the Authentication panel
3. click `Use Test User`
4. the page stores a local test session and sends the returned bearer token on plan/result API requests

This mode is intended for AI-operated Playwright or integrated-browser testing and should not be exposed outside local development.

## Remote Control-Plane Queue Smoke Client

For the desktop-authoring queue seam, a thin HTTP smoke client now exists at:

1. `scripts/smoke_remote_control_plane_authoring_queue.py`

Purpose:

1. read the governed remote tool schema from the study-material repo
2. obtain a localhost-only bearer token through `POST /api/v1/auth/test-session`
3. build a schema-compliant `queue_local_action` request for `write_staging_authoring_candidate`
4. send that request to `/api/v1/control-plane/local-actions`

Usage example:

```powershell
python scripts/smoke_remote_control_plane_authoring_queue.py \
   --task-id 2026-03-29-example-authoring-001 \
   --target-path Development/staging/example-guide/SG-CT-EXAMPLE-GUIDE.md \
   --content-file .\temp\candidate.md \
   --overwrite \
   --dry-run
```

Live run prerequisites:

1. the FastAPI app must already be running locally
2. `ENABLE_LOCAL_TEST_AUTH=true` must be active
3. the packet must already be at `approved_for_local_action`
4. the target path must exactly match the packet authoring allowlist

## Public Desktop Discovery Surface

The backend now includes the first implementation slice for a public Desktop activation boundary.

Endpoints:

1. `GET /api/v1/auth/public-desktop-config`
2. `GET /.well-known/oauth-authorization-server`
3. `GET /mcp`

Current behavior:

1. these routes stay effectively inactive until the public OAuth environment variables are configured
2. `/mcp` is metadata-only and does not yet claim a full MCP transport
3. redirect URIs are normalized and rejected if they are not absolute URLs
4. outside local development, public URLs must use `https`
5. the existing localhost-only test auth remains a separate development-only seam and is not treated as public Desktop activation

The backend now also includes an initial dedicated Supabase MCP slice at `/supabase-mcp`.

Current Supabase MCP behavior:

1. it uses a separate OAuth environment contract from the governed control-plane surface
2. it exposes database-backed `get_project_context`, `list_tables`, `describe_table`, and guarded `run_readonly_sql`
3. when `SUPABASE_MANAGEMENT_TOKEN` is configured, it returns live advisory notices, service logs, database branch listings, confirmed branch creation results, and publishable key inspection
4. it exposes allowlisted repository inspection for Edge Function sources and migration targets
5. confirmed database branch creation is durably audit-logged in the application database through `public.mcp_external_action_audits`

The backend now also includes an initial dedicated GitHub MCP slice at `/github-mcp`.

Current GitHub MCP behavior:

1. it uses a separate OAuth environment contract from both the governed control-plane surface and the Supabase connector
2. it uses a GitHub App plus installation tokens for upstream repository access instead of a broad PAT
3. it exposes allowlisted repository, issue, pull request, status-check, workflow, and workflow-run inspection tools
4. confirmed write actions are bounded to issue comments, branch creation, pull request creation, configured review requests, and allowlisted workflow dispatches
5. confirmed write actions are durably audit-logged in the application database through `public.mcp_external_action_audits`
6. `request_copilot_review` is implemented as a configured reviewer-request alias because GitHub does not expose a distinct public Copilot-review REST surface for this backend to target directly

Validation utility:

1. `python scripts/check_public_desktop_surface.py`
2. `python scripts/check_public_desktop_surface.py --require-ready`
3. `python scripts/check_public_desktop_surface.py --base-url https://your-public-host.example.com --require-ready`

Use the first form to validate the local environment contract. Use the third form only after deployment, when you want the backend to verify the live public endpoints over HTTP.

Public proof helper:

1. `python scripts/smoke_public_control_plane_access.py --base-url https://your-public-host.example.com --token-env PUBLIC_CONTROL_PLANE_BEARER_TOKEN`
2. `python scripts/smoke_public_control_plane_access.py --base-url https://your-public-host.example.com --task-id 2026-03-29-example-packet-001`

This helper is for the non-local proof step. It checks the public discovery endpoints and then verifies authenticated access to the bounded control-plane using a real bearer token.

## Render Deployment

The repository now includes a Render blueprint at `render.yaml` for the public backend host.

Default Render service shape:

1. type: Python web service
2. build command: `pip install -r requirements.txt`
3. start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. health check path: `/health`
5. local test auth disabled in hosted mode

Recommended deployment sequence:

1. create a new Render Web Service from this repository or import the blueprint
2. confirm the service uses the root of this repo as the working directory
3. set the required runtime environment variables from `.env.example`
4. leave `ENABLE_LOCAL_TEST_AUTH=false`
5. deploy the service and confirm `GET /health` returns `200`
6. attach the custom domain `control.apexpowerops.com`
7. add the DNS record in GoDaddy using the Render-provided target
8. run `python scripts/check_public_desktop_surface.py --base-url https://control.apexpowerops.com --require-ready`

Required hosted variables:

1. `DATABASE_URL`
2. `SUPABASE_URL`
3. `SUPABASE_ANON_KEY`
4. `SUPABASE_SERVICE_ROLE_KEY`
5. `SUPABASE_JWKS_URL`
6. `APP_ENV=production`
7. `LOG_LEVEL=INFO`

Required public Desktop activation variables once the public host and OAuth client are real:

1. `PUBLIC_MCP_BASE_URL=https://control.apexpowerops.com`
2. `PUBLIC_OAUTH_AUTHORIZATION_URL=https://<oauth-provider>/authorize`
3. `PUBLIC_OAUTH_TOKEN_URL=https://<oauth-provider>/oauth/token`
4. `PUBLIC_OAUTH_JWKS_URL=https://<oauth-provider>/.well-known/jwks.json`
5. `PUBLIC_OAUTH_ISSUER=<real token issuer>` when it cannot be derived cleanly from the auth endpoints
6. `PUBLIC_OAUTH_AUDIENCE=https://control.apexpowerops.com` when the provider issues audience-bound access tokens
7. `PUBLIC_OAUTH_CLIENT_ID=<production client id>`
8. `PUBLIC_OAUTH_REDIRECT_URIS=https://chat.openai.com/aip/callback,https://chatgpt.com/aip/callback`
9. `PUBLIC_OAUTH_SCOPES=openid profile email`

These values support both the legacy Supabase-backed surface and an Auth0-backed cutover. Before changing the authorization platform or connector mode, update the operator guidance in `MCP_OAUTH_PLATFORM_SETTINGS.md` and then bring `.env.example`, Render env vars, and deployment validation back into sync.

Do not treat the Render deploy as complete public activation until the public-surface validator and authenticated smoke proof both pass against the deployed host.

## Authenticated Plan Persistence

The demo page can calculate anonymously, but plan and result persistence now requires a valid Supabase bearer token.

Backend enforcement details:

1. FastAPI verifies Supabase JWTs against `SUPABASE_JWKS_URL`
2. `/api/v1/neta/plans` routes are identity-scoped to the authenticated user
3. new plan writes persist `tcc_test_plans.user_id = <jwt sub>`
4. result writes are allowed only for plans owned by the authenticated user

This retires the old anonymous steady-state write path even though legacy demo rows may still exist during transition cleanup.

## Database

- **Name:** tcc_v5
- **Tables:** 33
- **Rows:** 2,475,137
- **Status:** Schema populated and usable for active implementation, but backend maturity is mixed and must be classified against the governed authority stack rather than this README.

## Next Steps

1. Keep backend implementation aligned with the paired schema and DLL authority documents before promoting any TCC behavior claim.
2. Continue family-by-family contract lift using bounded status classification rather than global readiness claims.
3. Treat ETU bounded delay or evaluate parity and TMT bounded contract coverage as implemented slices, not as proof of full backend completion.
4. Use the current queue from the governed study-material docs for remaining family work such as EMT, fuse, relay, BreakerHV, and support families.
