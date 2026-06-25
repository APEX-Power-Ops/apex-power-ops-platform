#!/usr/bin/env bash
set -euo pipefail
# Usage: make_viewer.sh <BASELINE_DB> <VIEWER_DB>
BASELINE_DB="${1:?baseline}"; VIEWER_DB="${2:?viewer}"
SU() { docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres "$@"; }
# TEMPLATE requires zero sessions on BASELINE_DB (it is frozen / connection-free by design)
SU -d postgres -c "drop database if exists \"$VIEWER_DB\";"
SU -d postgres -c "create database \"$VIEWER_DB\" template \"$BASELINE_DB\";"
SU -d "$VIEWER_DB" -c "revoke connect on database \"$VIEWER_DB\" from public;"
# clone-local: disable RLS on every RLS-enabled tcc table
SU -d "$VIEWER_DB" <<'SQL'
do $$ declare r record; begin
  for r in select format('%I.%I', n.nspname, c.relname) as t
           from pg_class c join pg_namespace n on n.oid=c.relnamespace
           where n.nspname='tcc' and c.relkind='r' and c.relrowsecurity loop
    execute 'alter table '||r.t||' disable row level security';
  end loop;
end $$;
SQL
# read-only grants for tcc_breaker_ro
SU -d "$VIEWER_DB" -c "grant connect on database \"$VIEWER_DB\" to tcc_breaker_ro;"
SU -d "$VIEWER_DB" -c "grant usage on schema tcc to tcc_breaker_ro;"
SU -d "$VIEWER_DB" -c "grant select on all tables in schema tcc to tcc_breaker_ro;"
echo "make_viewer OK: $VIEWER_DB"
