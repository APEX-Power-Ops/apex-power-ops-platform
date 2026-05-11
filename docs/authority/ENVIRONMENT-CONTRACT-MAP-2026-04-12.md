# Environment Contract Map

This document records the first environment-contract scaffold for the imported control-plane runtime.

Closeout interpretation note:

This document remains the repo-owned environment-contract interpretation surface for the imported control-plane runtime, but it now operates as a retained post-cutover baseline rather than a platform-bootstrap interpretation layer.

Current routing:

1. use `OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md` and `../architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md` for current workspace and operator-boundary decisions,
2. use `../architecture/ACTIVE-APP-RUNTIME-VALIDATION-MAP-2026-04-21.md` for current app-lane runtime and validation entrypoints,
3. use `../architecture/OLARES-AI-ORCHESTRATION-DECISION-SURFACE-2026-05-07.md` and `../architecture/control-plane-lineage/apex-resa/AI_ORCHESTRATION_PROTOCOL.md` for the current AI and MCP orchestration boundary,
4. use this document when the control-plane environment contract groups, ownership split, or historical imported-runtime boundaries need to be interpreted.

Scope in this phase:
- define the env surface carried forward from the legacy TCC backend
- separate runtime-critical values from admin, connector, and local-test values
- establish what belongs to `apps/control-plane-api` versus what remains future platform-wide governance

## Ownership

- `apps/control-plane-api/.env.example` is the tracked app-level contract source for the imported runtime surface
- this document is the repo-owned interpretation layer for that contract
- future platform-wide normalization should happen only after schema and work-package alignment planning

## Control Plane API Environment Groups

### Runtime Required

- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWKS_URL`
- `APP_ENV`
- `LOG_LEVEL`

These are the minimum values for the primary FastAPI runtime.

### Runtime Optional

- `SUPABASE_EMAIL_REDIRECT_URL`

This remains app-scoped because it controls the demo and auth redirect behavior exposed by the imported runtime.

### Migration And Admin

- `DATABASE_URL_LOCAL`
- `SOURCE_DATABASE_URL`
- `DATABASE_URL_DIRECT`

These should remain restricted to admin-only workflows and should not be treated as standard runtime configuration.

### Public Desktop OAuth And MCP Surface

- `PUBLIC_MCP_BASE_URL`
- `PUBLIC_OAUTH_AUTHORIZATION_URL`
- `PUBLIC_OAUTH_TOKEN_URL`
- `PUBLIC_OAUTH_JWKS_URL`
- `PUBLIC_OAUTH_REGISTRATION_URL`
- `PUBLIC_OAUTH_ISSUER`
- `PUBLIC_OAUTH_AUDIENCE`
- `PUBLIC_OAUTH_CLIENT_ID`
- `PUBLIC_OAUTH_REDIRECT_URIS`
- `PUBLIC_OAUTH_SCOPES`

These are connector-surface values for the public control-plane host and should remain env-gated.

### Dedicated Supabase MCP Surface

- `SUPABASE_MCP_PUBLIC_BASE_URL`
- `SUPABASE_MCP_OAUTH_AUTHORIZATION_URL`
- `SUPABASE_MCP_OAUTH_TOKEN_URL`
- `SUPABASE_MCP_OAUTH_JWKS_URL`
- `SUPABASE_MCP_OAUTH_REGISTRATION_URL`
- `SUPABASE_MCP_OAUTH_ISSUER`
- `SUPABASE_MCP_OAUTH_AUDIENCE`
- `SUPABASE_MCP_OAUTH_CLIENT_ID`
- `SUPABASE_MCP_OAUTH_REDIRECT_URIS`
- `SUPABASE_MCP_OAUTH_SCOPES`
- `SUPABASE_MCP_OAUTH_USERINFO_URL`
- `SUPABASE_ALLOWED_PROJECTS_JSON`
- `SUPABASE_MANAGEMENT_API_URL`
- `SUPABASE_MANAGEMENT_TOKEN`
- `SUPABASE_MANAGEMENT_TIMEOUT_SECONDS`
- `SUPABASE_ALLOWED_MIGRATION_ROOTS`
- `SUPABASE_ALLOWED_FUNCTION_ROOTS`
- `SUPABASE_ENABLE_MIGRATION_APPLY`
- `SUPABASE_ENABLE_EDGE_FUNCTION_DEPLOY`
- `SUPABASE_CLI_PROJECT_DIR`
- `SUPABASE_CLI_PATH`
- `SUPABASE_CLI_TIMEOUT_SECONDS`
- `SUPABASE_ACCESS_TOKEN`

These values represent an operator connector boundary, not the final database governance model.

### Dedicated GitHub MCP Surface

- `GITHUB_MCP_PUBLIC_BASE_URL`
- `GITHUB_MCP_OAUTH_AUTHORIZATION_URL`
- `GITHUB_MCP_OAUTH_TOKEN_URL`
- `GITHUB_MCP_OAUTH_JWKS_URL`
- `GITHUB_MCP_OAUTH_REGISTRATION_URL`
- `GITHUB_MCP_OAUTH_ISSUER`
- `GITHUB_MCP_OAUTH_AUDIENCE`
- `GITHUB_MCP_OAUTH_CLIENT_ID`
- `GITHUB_MCP_OAUTH_REDIRECT_URIS`
- `GITHUB_MCP_OAUTH_SCOPES`
- `GITHUB_MCP_OAUTH_USERINFO_URL`
- `GITHUB_ALLOWED_REPOS_JSON`
- `GITHUB_APP_ID`
- `GITHUB_APP_PRIVATE_KEY`
- `GITHUB_APP_INSTALLATION_IDS_JSON`
- `GITHUB_ALLOWED_WORKFLOW_DISPATCHES_JSON`
- `GITHUB_COPILOT_REVIEWERS_JSON`

These values stay app-scoped until the future platform integration boundary is redesigned.

### Local Test And Operator Bootstrap

- `ENABLE_LOCAL_TEST_AUTH`
- `LOCAL_TEST_AUTH_SECRET`
- `LOCAL_TEST_AUTH_USERS_JSON`
- `OPERATOR_BOOTSTRAP_TOKEN`
- `OPERATOR_TOKEN_SIGNING_SECRET`
- `OPERATOR_TOKEN_EMAIL`
- `OPERATOR_TOKEN_LABEL`
- `OPERATOR_TOKEN_USER_ID`
- `OPERATOR_TOKEN_TTL_MINUTES`

These values are operationally sensitive and should be isolated from standard developer runtime templates.

## Package Boundary Note

`packages/calc-engine` does not own an environment contract in this phase.

The calc package currently consumes SQLAlchemy sessions supplied by a host application. That keeps the first extraction small and avoids forcing premature decisions about platform-wide database/session orchestration.

## Operations Web Browser Shell Environment Group

Packet `2026-04-13-apex-unification-001o` introduced the first governed browser-side shell under `apps/operations-web`.

Ownership:

- `apps/operations-web/.env.example` is the tracked browser-shell contract source for that app
- this browser contract is intentionally limited to public browser-safe values only

Current browser-shell values:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_CONTROL_PLANE_BASE_URL`

Restriction:

- service-role keys, admin tokens, and server-only connector credentials must not be placed in the browser-shell contract
- packet `001o` created the shell and env contract, but packet `001p` kept the legacy Supabase client deferred pending client-shape redesign or split admission
