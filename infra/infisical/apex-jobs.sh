#!/usr/bin/env bash
# apex-jobs.sh - run apex-jobs with dev secrets injected from Infisical, NOT the
# standalone infra/.env cache. Mirrors infra/infisical/dev-psql.sh.
# Usage: infra/infisical/apex-jobs.sh <verb> [args...]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG="$HERE/../../packages/apex-jobs"
# Repo-aware verbs (review-run, promotions, prune) resolve APEX_JOBS_REPO; default it
# to THIS checkout so the front door never acts on the stale legacy default repo.
export APEX_JOBS_REPO="${APEX_JOBS_REPO:-$(cd "$HERE/../.." && pwd)}"
# shellcheck disable=SC2016  # $1 and $@ intentionally expand inside the inner bash -c, not here
exec "$HERE/inject.sh" dev -- bash -c 'cd "$1" && shift && exec uv run apex-jobs "$@"' _ "$PKG" "$@"
