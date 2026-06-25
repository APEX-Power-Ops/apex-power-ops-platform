#!/usr/bin/env bash
set -euo pipefail
# Usage: restore_baseline.sh <BASELINE_DB> <DUMP_FILE(host path)>
BASELINE_DB="${1:?baseline db}"; DUMP_FILE="${2:?dump file}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SU() { docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres "$@"; }
# Clean the in-container dump copy on ANY exit (success OR failure) so proprietary catalog data is
# never left in container /tmp after a failed restore.
trap 'docker exec apex-dev-pg rm -f /tmp/restore.dump >/dev/null 2>&1 || true' EXIT

SU -d postgres -c "drop database if exists \"$BASELINE_DB\";"
SU -d postgres -c "create database \"$BASELINE_DB\";"
# preflight: auth stubs BEFORE restore (policies reference auth.uid())
SU -d "$BASELINE_DB" < "$HERE/sql/10_auth_stubs.sql"
# copy dump into the container and restore with the in-container (PG17) pg_restore, fail-closed
docker cp "$DUMP_FILE" "apex-dev-pg:/tmp/restore.dump"
docker exec apex-dev-pg pg_restore --no-owner --no-privileges --exit-on-error \
  -U postgres -d "$BASELINE_DB" /tmp/restore.dump
# (the EXIT trap removes /tmp/restore.dump; no explicit rm needed)
# freeze: no PUBLIC connect (clones are spawned by the superuser, which is unaffected)
SU -d "$BASELINE_DB" -c "revoke connect on database \"$BASELINE_DB\" from public;"
echo "restore_baseline OK: $BASELINE_DB"
