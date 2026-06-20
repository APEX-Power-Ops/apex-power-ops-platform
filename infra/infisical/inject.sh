#!/usr/bin/env bash
# Inject apex-platform/<env> secrets from self-hosted Infisical into a command.
# Usage: infra/infisical/inject.sh <dev|staging|prod> -- <command...>
# Auth = the apex-host machine identity (universal auth); creds in 0600 .env.agent (gitignored).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
set -a; . "$HERE/.env.agent"; set +a
DOMAIN="${INFISICAL_API_URL%/}/api"
PROJECT_ID="985aac34-9665-423b-b472-78ddbd707ca7"
ENV_SLUG="${1:?env slug required: dev|staging|prod}"; shift
[ "${1:-}" = "--" ] && shift
export INFISICAL_TOKEN
INFISICAL_TOKEN="$(infisical login --method=universal-auth --client-id="$INFISICAL_CLIENT_ID" --client-secret="$INFISICAL_CLIENT_SECRET" --domain="$DOMAIN" --plain --silent)"
exec infisical run --projectId="$PROJECT_ID" --env="$ENV_SLUG" --domain="$DOMAIN" -- "$@"
