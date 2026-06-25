#!/usr/bin/env bash
set -euo pipefail
# Usage: make_codex_clone.sh <BASELINE_DB> <CLONE_DB> <CODEX_ROLE>
BASELINE_DB="${1:?baseline}"; CLONE_DB="${2:?clone}"; CODEX_ROLE="${3:?role}"
SU() { docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres "$@"; }
SU -d postgres -c "drop database if exists \"$CLONE_DB\";"
SU -d postgres -c "create database \"$CLONE_DB\" template \"$BASELINE_DB\";"
SU -d "$CLONE_DB" -c "revoke connect on database \"$CLONE_DB\" from public;"
SU -d "$CLONE_DB" -c "grant connect on database \"$CLONE_DB\" to \"$CODEX_ROLE\";"
SU -d "$CLONE_DB" -c "grant usage on schema tcc to \"$CODEX_ROLE\";"
# clone-local ownership transfer: codex owns every object originally owned by postgres in this DB
# (owners are RLS-exempt on their own tables -> full read/write/DDL without any cluster bypass)
# REASSIGN OWNED BY postgres is blocked on PG17 (postgres owns system catalog objects);
# generate and execute per-object ALTER OWNER statements scoped to tcc schema — identical semantic.
SU -d "$CLONE_DB" -c "alter schema tcc owner to \"$CODEX_ROLE\";"
# $CODEX_ROLE is alphanumeric+underscores (verified by caller); safe to embed as identifier literal
SU -d "$CLONE_DB" -c "
do \$body\$
declare r record;
begin
  for r in
    select n.nspname as ns, c.relname, c.relkind
      from pg_class c join pg_namespace n on n.oid=c.relnamespace
     where n.nspname='tcc' and c.relkind in ('r','S','v')
       and pg_get_userbyid(c.relowner)='postgres'
  loop
    execute format('alter %s %I.%I owner to ${CODEX_ROLE}',
      case r.relkind when 'r' then 'table' when 'S' then 'sequence' when 'v' then 'view' end,
      r.ns, r.relname);
  end loop;
end \$body\$;
"
echo "make_codex_clone OK: $CLONE_DB owned by $CODEX_ROLE"
