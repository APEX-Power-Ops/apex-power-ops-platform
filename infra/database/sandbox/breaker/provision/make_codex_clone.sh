#!/usr/bin/env bash
set -euo pipefail
# Usage: make_codex_clone.sh <BASELINE_DB> <CLONE_DB> <CODEX_ROLE>
BASELINE_DB="${1:?baseline}"; CLONE_DB="${2:?clone}"; CODEX_ROLE="${3:?role}"
# Harden the unquoted identifier interpolation below: the role name is embedded directly into
# dynamic SQL, so reject anything that is not a plain lower_snake identifier (fail-closed).
[[ "$CODEX_ROLE" =~ ^[a-z_][a-z0-9_]*$ ]] || { echo "make_codex_clone: invalid role name '$CODEX_ROLE'" >&2; exit 1; }
SU() { docker exec -i apex-dev-pg psql -v ON_ERROR_STOP=1 -U postgres "$@"; }
SU -d postgres -c "drop database if exists \"$CLONE_DB\";"
SU -d postgres -c "create database \"$CLONE_DB\" template \"$BASELINE_DB\";"
SU -d "$CLONE_DB" -c "revoke connect on database \"$CLONE_DB\" from public;"
SU -d "$CLONE_DB" -c "grant connect on database \"$CLONE_DB\" to \"$CODEX_ROLE\";"
SU -d "$CLONE_DB" -c "grant usage on schema tcc to \"$CODEX_ROLE\";"
# clone-local ownership transfer: codex owns every tcc object (owners are RLS-exempt on their own
# tables -> full read/write/DDL without any cluster bypass). NOTE: `reassign owned by postgres` is
# REJECTED on PG17 (postgres owns system catalogs); transfer tcc schema + its r/S/v via per-object
# ALTER OWNER. SKIP sequences LINKED to a table column (identity/serial) — Postgres rejects changing
# their owner directly; altering the owning table cascades ownership to them automatically.
SU -d "$CLONE_DB" -c "alter schema tcc owner to \"$CODEX_ROLE\";"
SU -d "$CLONE_DB" -c "
do \$body\$
declare r record;
begin
  for r in
    select n.nspname as ns, c.relname, c.relkind
      from pg_class c join pg_namespace n on n.oid=c.relnamespace
     where n.nspname='tcc' and c.relkind in ('r','S','v')
       and pg_get_userbyid(c.relowner)='postgres'
       and not (c.relkind='S' and exists (
         select 1 from pg_depend d
          where d.objid=c.oid and d.classid='pg_class'::regclass
            and d.refclassid='pg_class'::regclass and d.deptype in ('a','i')))
  loop
    execute format('alter %s %I.%I owner to ${CODEX_ROLE}',
      case r.relkind when 'r' then 'table' when 'S' then 'sequence' when 'v' then 'view' end,
      r.ns, r.relname);
  end loop;
end \$body\$;
"
echo "make_codex_clone OK: $CLONE_DB owned by $CODEX_ROLE"
