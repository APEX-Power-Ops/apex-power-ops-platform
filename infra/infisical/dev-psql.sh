#!/usr/bin/env bash
# First load-bearing Infisical consumer: a psql session to the dev cluster whose
# postgres password is injected from self-hosted Infisical (dev env, apex-host
# machine identity) -- NOT read from the standalone infra/.env cache.
#
# Usage:   infra/infisical/dev-psql.sh [psql args...]        # default DB: ops_dev
# Examples:
#   infra/infisical/dev-psql.sh -c 'select current_database()'
#   PGDATABASE=ops_test infra/infisical/dev-psql.sh -c '\dn'
#
# The password reaches psql via PGPASSWORD inside the injected subprocess only
# (never on argv, never logged). Host/port/user/db use libpq env defaults below,
# each overridable from the caller's environment.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
export PGHOST="${PGHOST:-127.0.0.1}"
export PGPORT="${PGPORT:-5432}"
export PGUSER="${PGUSER:-postgres}"
export PGDATABASE="${PGDATABASE:-ops_dev}"
exec "$HERE/inject.sh" dev -- bash -c 'PGPASSWORD="$DEV_PG_PASSWORD" exec psql "$@"' _ "$@"
