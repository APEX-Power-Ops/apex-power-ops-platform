# Infisical consumer pattern (self-hosted, mesh-only)

Self-hosted Infisical (`http://100.64.0.1:8222`, mesh-only) is the platform's
secret-distribution layer. Host processes get secrets at runtime via the
**apex-host machine identity** -- no copied `.env` values.

## Files
- `inject.sh <dev|staging|prod> -- <cmd...>` -- authenticate (universal auth,
  creds in gitignored `.env.agent`) and run `<cmd>` with that env-slug's secrets
  injected. The canonical consumer entrypoint.
- `dev-psql.sh [psql args...]` -- example load-bearing consumer: a dev-cluster
  psql session with `DEV_PG_PASSWORD` injected from Infisical (default DB `ops_dev`).
- `apex-jobs.sh <verb> [args...]` -- runs the apex-jobs orchestration CLI with
  `APEX_JOBS_PGPASSWORD` injected from Infisical (dev env), against `orchestration_dev`;
  exports `APEX_JOBS_REPO` to this checkout.
- `.managed-secrets` -- NAMES of secrets now sourced from Infisical. Arming a name
  here makes `infra/secret-audit.sh` (Check 1c) FAIL if a stale copy still lingers
  in a local cache (rotation runbook step 6: "no value outside Infisical").
- `.env`, `.env.agent` -- gitignored 0600 caches (server config; machine-identity creds).
- `DEV_PG_PASSWORD` is intentionally retained in `infra/.env` (and is the sole
  `secret-audit.sh` `ENV_ALLOWED_KEYS` entry): it is the dev-cluster `postgres`
  superuser that `compose.dev-lanes.yml` uses to initialize the container. It is
  NOT a cutover target -- the orchestration-role password is `APEX_JOBS_PGPASSWORD`.

## Migrating a consumer (cutover checklist)
1. Replace the consumer's `infra/.env` source with `inject.sh <env> -- <cmd>`
   (or `dev-psql.sh` for dev-DB access).
2. Verify it works through Infisical.
3. Remove the secret's copy from the local cache(s).
4. Add the secret NAME to `.managed-secrets` so the audit enforces no-copy.
   (Do this ONLY after step 3 -- arming a name whose value still sits in a
   cache will correctly FAIL Check 1c; also drop it from `ENV_ALLOWED_KEYS`.)
5. `infra/secret-audit.sh` -> clean.

Project id `985aac34-9665-423b-b472-78ddbd707ca7`; env slugs `dev`/`staging`/`prod`.
Topology + rotation: the private `SECRET_REGISTRY.md` (NOT in this repo).
