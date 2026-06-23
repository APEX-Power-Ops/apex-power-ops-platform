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
- `.managed-secrets` -- NAMES of secrets now sourced from Infisical. Arming a name
  here makes `infra/secret-audit.sh` (Check 1c) FAIL if a stale copy still lingers
  in a local cache (rotation runbook step 6: "no value outside Infisical").
- `.env`, `.env.agent` -- gitignored 0600 caches (server config; machine-identity creds).

## Migrating a consumer (cutover checklist)
1. Replace the consumer's `infra/.env` source with `inject.sh <env> -- <cmd>`
   (or `dev-psql.sh` for dev-DB access).
2. Verify it works through Infisical.
3. Remove the secret's copy from the local cache(s).
4. Add the secret NAME to `.managed-secrets` so the audit enforces no-copy.
5. `infra/secret-audit.sh` -> clean.

Project id `985aac34-9665-423b-b472-78ddbd707ca7`; env slugs `dev`/`staging`/`prod`.
Topology + rotation: the private `SECRET_REGISTRY.md` (NOT in this repo).
