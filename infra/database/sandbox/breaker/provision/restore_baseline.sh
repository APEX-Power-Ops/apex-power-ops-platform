#!/usr/bin/env bash
set -euo pipefail
# Usage: restore_baseline.sh <BASELINE_DB> <DUMP_FILE(host path)>
BASELINE_DB="${1:?baseline db}"; DUMP_FILE="${2:?dump file}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SU() { docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres "$@"; }
RESTORE_OK=0
# Fail-closed cleanup on ANY exit: always remove the in-container dump copy; and if the restore did
# NOT complete (RESTORE_OK!=1), DROP the partial baseline. A half-restored baseline must never be
# left behind — it would otherwise linger with restored data reachable and break template cloning.
cleanup() {
  docker exec apex-dev-pg rm -f /tmp/restore.dump >/dev/null 2>&1 || true
  if [ "$RESTORE_OK" -ne 1 ]; then
    docker exec -i apex-dev-pg psql -U postgres -d postgres \
      -c "drop database if exists \"$BASELINE_DB\";" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

SU -d postgres -c "drop database if exists \"$BASELINE_DB\";"
SU -d postgres -c "create database \"$BASELINE_DB\";"
# Freeze IMMEDIATELY (before restore) so the baseline is never PUBLIC-connectable, even transiently
# mid-restore. The superuser (postgres) still connects to run the stubs + pg_restore (superusers
# bypass the CONNECT privilege check). On failure the cleanup trap drops the DB entirely.
SU -d "$BASELINE_DB" -c "revoke connect on database \"$BASELINE_DB\" from public;"
# preflight: auth stubs BEFORE restore (policies reference auth.uid())
SU -d "$BASELINE_DB" < "$HERE/sql/10_auth_stubs.sql"
# copy dump into the container and restore with the in-container (PG17) pg_restore, fail-closed
docker cp "$DUMP_FILE" "apex-dev-pg:/tmp/restore.dump"
docker exec apex-dev-pg pg_restore --no-owner --no-privileges --exit-on-error \
  -U postgres -d "$BASELINE_DB" /tmp/restore.dump
RESTORE_OK=1
echo "restore_baseline OK: $BASELINE_DB"
