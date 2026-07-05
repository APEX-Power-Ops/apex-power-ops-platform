#!/usr/bin/env bash
# Infisical-backed local launch for control-plane-api (ops-router work).
# OPS_* are injected from Infisical dev at runtime -- never a cache. The main
# DATABASE_URL still resolves in config.py from the app .env cache (its migration
# is out of scope for this lane); DEV_PG_PASSWORD is also injected but feeds
# dev-DB tooling (dev-psql.sh), not config.py's DATABASE_URL.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"
exec infra/infisical/inject.sh dev -- \
  uvicorn main:app --app-dir apps/control-plane-api \
  --host "${HOST:-127.0.0.1}" --port "${PORT:-8010}"
