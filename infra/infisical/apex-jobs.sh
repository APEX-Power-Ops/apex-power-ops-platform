#!/usr/bin/env bash
# apex-jobs.sh - run apex-jobs with dev secrets injected from Infisical, NOT the
# standalone infra/.env cache. Mirrors infra/infisical/dev-psql.sh.
# Usage: infra/infisical/apex-jobs.sh <verb> [args...]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG="$HERE/../../packages/apex-jobs"
# shellcheck disable=SC2016  # $1 and $@ intentionally expand inside the inner bash -c, not here
exec "$HERE/inject.sh" dev -- bash -c 'cd "$1" && shift && exec uv run apex-jobs "$@"' _ "$PKG" "$@"
