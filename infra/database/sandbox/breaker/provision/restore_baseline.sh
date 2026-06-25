#!/usr/bin/env bash
set -euo pipefail
# Usage: restore_baseline.sh <BASELINE_DB> <DUMP_FILE(host path)>
BASELINE_DB="${1:?baseline db}"; DUMP_FILE="${2:?dump file}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SU() { docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres "$@"; }
RESTORE_OK=0
# Fail-closed cleanup on ANY exit: always remove the in-container dump + TOC; and if the restore did
# NOT complete (RESTORE_OK!=1), DROP the partial baseline. A half-restored baseline must never linger.
cleanup() {
  docker exec apex-dev-pg rm -f /tmp/restore.dump /tmp/restore.toc >/dev/null 2>&1 || true
  if [ "$RESTORE_OK" -ne 1 ]; then
    docker exec -i apex-dev-pg psql -U postgres -d postgres \
      -c "drop database if exists \"$BASELINE_DB\";" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

SU -d postgres -c "drop database if exists \"$BASELINE_DB\";"
SU -d postgres -c "create database \"$BASELINE_DB\";"
# Freeze IMMEDIATELY (before restore) so the baseline is never PUBLIC-connectable, even transiently
# mid-restore. Superuser (postgres) still connects to run the stubs + pg_restore.
SU -d "$BASELINE_DB" -c "revoke connect on database \"$BASELINE_DB\" from public;"
# preflight stubs BEFORE restore: the --schema=tcc dump references external objects that must
# pre-exist — (1) auth.* functions (RLS policies reference auth.uid()); (2) work.* enum types
# (relay_* columns are typed work.provenance_*_enum / work.relay_*_kind_enum).
SU -d "$BASELINE_DB" < "$HERE/sql/10_auth_stubs.sql"
SU -d "$BASELINE_DB" < "$HERE/sql/11_work_enums.sql"
docker cp "$DUMP_FILE" "apex-dev-pg:/tmp/restore.dump"
# Restore via a TOC that EXCLUDES "FK CONSTRAINT" entries. Prod carries data-quality orphans (e.g. 484
# tmt_curves rows whose frame_id has no tmt_frames row) under FKs prod marks valid but does NOT
# enforce, so re-validating those FKs on restore fails. The sandbox is an analytical/audit copy — FK
# enforcement is not part of what Codex audits, and the orphan rows are PRESERVED as real prod data.
# Tables / PKs / unique / check / indexes / sequences / data all restore; only FOREIGN KEY constraints
# are omitted. --exit-on-error still guards everything else (fail-closed).
docker exec apex-dev-pg sh -c 'pg_restore -l /tmp/restore.dump | grep -v "FK CONSTRAINT" > /tmp/restore.toc'
docker exec apex-dev-pg pg_restore -L /tmp/restore.toc --no-owner --no-privileges --exit-on-error \
  -U postgres -d "$BASELINE_DB" /tmp/restore.dump
RESTORE_OK=1
echo "restore_baseline OK: $BASELINE_DB (FK constraints omitted by design — see manifest)"
