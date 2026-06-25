#!/usr/bin/env bash
set -euo pipefail
# Build the synthetic fixture SOURCE db, then pg_dump it to a custom-format file that mirrors the
# prod dump shape (schema tcc only; auth schema EXCLUDED, so restore must re-stub auth).
# Usage: build_fixture_dump.sh <BUILD_DB> <DUMP_OUT>
BUILD_DB="${1:?build db name}"; DUMP_OUT="${2:?dump out path}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
install -d -m 700 "$(dirname "$DUMP_OUT")"   # _local/ is gitignored and not auto-created
SU() { docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres "$@"; }

SU -d postgres -c "drop database if exists \"$BUILD_DB\";"
SU -d postgres -c "create database \"$BUILD_DB\";"
# auth stub must exist BEFORE the policy is created
SU -d "$BUILD_DB" < "$HERE/sql/10_auth_stubs.sql"
SU -d "$BUILD_DB" < "$HERE/fixture/synthetic_tcc.sql"
# dump schema tcc only, custom format, in-container (paths are container-local)
docker exec apex-dev-pg pg_dump -U postgres --no-owner --no-privileges --schema=tcc -Fc \
  -d "$BUILD_DB" -f "/tmp/$(basename "$DUMP_OUT")"
docker cp "apex-dev-pg:/tmp/$(basename "$DUMP_OUT")" "$DUMP_OUT"
docker exec apex-dev-pg rm -f "/tmp/$(basename "$DUMP_OUT")"
echo "fixture dump written: $DUMP_OUT"
