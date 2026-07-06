#!/usr/bin/env python3
"""supabase_probe.py - reusable applier-privilege probe for the records lane on managed
(non-superuser) Supabase Postgres. Phase-4 prod precondition.

Given a target connection (value-silent, never printed), it exercises every privilege class
that records migrations 045-049 require - on RUN-SUFFIXED scratch roles/objects that are fully
torn down (zero residue) - then compares the observed outcomes against the Phase-0 baseline
(see PHASE0-FINDINGS.md) and emits a machine-readable pass/fail matrix. It exits nonzero on ANY
mismatch (an envelope drift). It also probes the Gate-A ESCALATION path (can `postgres` self-grant
SET/INHERIT via its admin option, then SET ROLE) and evaluates it against `--gate-a-policy`
(default `trusted-applier`): under `trusted-applier` the (expected) self-escalation is ACCEPTED and
reported, not fatal; under `preprovisioned` any self-escalation is a hard failure.

Collision-safety: every scratch role/object name carries a per-run suffix (uuid, or override via
SUPABASE_PROBE_RUN). The probe NEVER drops a name it did not create this run (no blind pre-drops).

This probe performs SCRATCH WRITES. It needs its OWN scratch-write GO, prior to the migration GO.

Connection (value-silent; pick ONE):
  SUPABASE_PROBE_DSN   - libpq conninfo or postgresql:// URI (parsed into PG* env, never echoed)
  or discrete:         SUPABASE_PROBE_HOST / SUPABASE_PROBE_PORT / SUPABASE_PROBE_USER /
                       SUPABASE_PROBE_DB + SUPABASE_PROBE_PW

Usage:
  SUPABASE_PROBE_DSN='...'  python3 supabase_probe.py [--json] [--gate-a-policy=trusted-applier|preprovisioned]
Gate-A policy (Task-2.0 decision; default `trusted-applier`): under `trusted-applier` the managed
`postgres` applier is custody-controlled and EXEMPT from invariant 8, so the self-escalation the
`gate_a_escalation` probe demonstrates is EXPECTED and does NOT fail the gate (it is reported, not
fatal). Under `preprovisioned` any self-escalation is a HARD failure (the records roles must be
minted out-of-band so `postgres` is never their creator).
Requires psql on PATH. Value-silent: prints only probe names, ok/sqlstate tokens, and match
booleans - never the DSN or password. Exit 0 = envelope OK for the selected policy; nonzero = drift.
"""
import os
import sys
import json
import uuid
import subprocess
import urllib.parse


def build_env():
    """Resolve connection into PG* env vars (value-silent: nothing printed)."""
    env = dict(os.environ)
    dsn = os.environ.get("SUPABASE_PROBE_DSN")
    if dsn:
        if "://" in dsn:
            u = urllib.parse.urlparse(dsn)
            if u.hostname:
                env["PGHOST"] = u.hostname
            if u.port:
                env["PGPORT"] = str(u.port)
            if u.username:
                env["PGUSER"] = urllib.parse.unquote(u.username)
            if u.password:
                env["PGPASSWORD"] = urllib.parse.unquote(u.password)
            env["PGDATABASE"] = (u.path or "/postgres").lstrip("/") or "postgres"
        else:  # keyword/value conninfo
            mp = {"host": "PGHOST", "port": "PGPORT", "user": "PGUSER",
                  "password": "PGPASSWORD", "dbname": "PGDATABASE"}
            for tok in dsn.split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    pg = mp.get(k.strip().lower())
                    if pg:
                        env[pg] = v.strip().strip("'")
    else:
        for var, pg in [("SUPABASE_PROBE_HOST", "PGHOST"),
                        ("SUPABASE_PROBE_PORT", "PGPORT"),
                        ("SUPABASE_PROBE_USER", "PGUSER"),
                        ("SUPABASE_PROBE_DB", "PGDATABASE"),
                        ("SUPABASE_PROBE_PW", "PGPASSWORD")]:
            if os.environ.get(var):
                env[pg] = os.environ[var]
    env.setdefault("PGPORT", "5432")
    env.setdefault("PGDATABASE", "postgres")
    env.setdefault("PGCONNECT_TIMEOUT", "25")
    if not env.get("PGHOST"):
        sys.stderr.write("ERROR: no connection (set SUPABASE_PROBE_DSN or SUPABASE_PROBE_HOST/...)\n")
        sys.exit(3)
    return env


def run_sql(env, sql):
    """Run a multi-statement probe via psql; return {k: v} from the trailing 'select k,v'."""
    p = subprocess.run(["psql", "-tAqX", "-F", "|", "-v", "ON_ERROR_STOP=0", "-c", sql],
                       env=env, capture_output=True, text=True)
    if p.returncode != 0:
        tail = (p.stderr.strip().splitlines() or ["psql failed"])[-1]
        return {"_error": tail[:200]}
    out = {}
    for line in p.stdout.splitlines():
        line = line.strip()
        if "|" in line:
            k, v = line.split("|", 1)
            out[k] = v
    return out


# Each probe: (name, sql_template_with___S___suffix, [(result_key, expected_substring), ...]).
# All scratch names carry the __S__ run-suffix; teardown drops ONLY those suffixed names.
PROBES = [
    ("role_attr_A2", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare s text:=''; begin
  begin execute 'create role sp_attr__S__ nologin'; s:=s||'create=ok;'; exception when others then s:=s||'create=FAIL:'||sqlstate||';'; end;
  begin execute 'alter role sp_attr__S__ nosuperuser'; s:=s||'nosuperuser=ok;'; exception when others then s:=s||'nosuperuser=FAIL:'||sqlstate||';'; end;
  begin execute 'alter role sp_attr__S__ nobypassrls'; s:=s||'nobypassrls=ok;'; exception when others then s:=s||'nobypassrls=FAIL:'||sqlstate||';'; end;
  begin execute 'alter role sp_attr__S__ nocreaterole'; s:=s||'nocreaterole=ok;'; exception when others then s:=s||'nocreaterole=FAIL:'||sqlstate||';'; end;
  begin execute 'alter role sp_attr__S__ login'; s:=s||'login=ok;'; exception when others then s:=s||'login=FAIL:'||sqlstate||';'; end;
  begin execute 'alter role sp_attr__S__ superuser'; s:=s||'superuser=ok;'; exception when others then s:=s||'superuser=FAIL:'||sqlstate||';'; end;
  insert into _pr values('steps', s);
  begin execute 'drop role if exists sp_attr__S__'; insert into _pr values('teardown','ok'); exception when others then insert into _pr values('teardown','FAIL:'||sqlstate); end;
end $$;
select k,v from _pr order by k;""",
     [("steps", "nosuperuser=FAIL:42501"), ("steps", "nobypassrls=ok"),
      ("steps", "login=ok"), ("steps", "superuser=FAIL:42501"), ("teardown", "ok")]),

    ("gate_a_creator_edge", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare edge text; canset text; after text; begin
  execute 'create role sp_ga__S__ nologin';
  select coalesce(string_agg('set='||set_option||'/inh='||inherit_option,';'),'NONE') into edge from pg_auth_members where roleid='sp_ga__S__'::regrole and member='postgres'::regrole;
  begin execute 'set role sp_ga__S__'; canset:='ok'; execute 'reset role'; exception when others then canset:='FAIL:'||sqlstate; begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'revoke sp_ga__S__ from postgres'; exception when others then null; end;
  select coalesce(string_agg(grantor::regrole::text,';'),'NONE') into after from pg_auth_members where roleid='sp_ga__S__'::regrole and member='postgres'::regrole;
  insert into _pr values('edge', edge); insert into _pr values('postgres_can_set_role', canset); insert into _pr values('after_revoke', after);
  begin execute 'drop role if exists sp_ga__S__'; insert into _pr values('teardown','ok'); exception when others then insert into _pr values('teardown','FAIL:'||sqlstate); end;
end $$;
select k,v from _pr order by k;""",
     [("edge", "set=false/inh=false"), ("postgres_can_set_role", "FAIL:42501"),
      ("after_revoke", "supabase_admin"), ("teardown", "ok")]),

    # SCARY-PATH probe: with ADMIN option on the auto-edge, can postgres self-grant SET/INHERIT
    # and thereby SET ROLE into the created role? Hard-fail if escalation succeeds.
    ("gate_a_escalation", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare g_set text; g_inh text; edge1 text; canset text; begin
  execute 'create role sp_esc__S__ nologin';
  begin execute 'grant sp_esc__S__ to postgres with set true'; g_set:='ACCEPTED'; exception when others then g_set:='REJECTED:'||sqlstate; end;
  begin execute 'grant sp_esc__S__ to postgres with inherit true'; g_inh:='ACCEPTED'; exception when others then g_inh:='REJECTED:'||sqlstate; end;
  select coalesce(string_agg(grantor::regrole::text||':set='||set_option||'/inh='||inherit_option,';'),'NONE') into edge1 from pg_auth_members where roleid='sp_esc__S__'::regrole and member='postgres'::regrole;
  begin execute 'set role sp_esc__S__'; canset:='SUCCESS_ESCALATED'; execute 'reset role'; exception when others then canset:='FAIL:'||sqlstate; begin execute 'reset role'; exception when others then null; end; end;
  insert into _pr values('self_grant_set', g_set);
  insert into _pr values('self_grant_inherit', g_inh);
  insert into _pr values('edge_after_selfgrant', edge1);
  insert into _pr values('set_role_after_selfgrant', canset);
  begin execute 'revoke sp_esc__S__ from postgres'; exception when others then null; end;
  begin execute 'drop role if exists sp_esc__S__'; insert into _pr values('teardown','ok'); exception when others then insert into _pr values('teardown','FAIL:'||sqlstate); end;
end $$;
select k,v from _pr order by k;""",
     [("set_role_after_selfgrant", "FAIL"), ("teardown", "ok")]),

    ("gate_b_policy_binding", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare s text:=''; begin
  execute 'create role sp_pol__S__ nologin';
  execute 'create schema sp_pols__S__';
  execute 'create table sp_pols__S__.t(id int)';
  execute 'alter table sp_pols__S__.t enable row level security';
  begin execute 'create policy p on sp_pols__S__.t for select to sp_pol__S__ using (true)'; s:=s||'create_policy_to_custom=ok;'; exception when others then s:=s||'create_policy_to_custom=FAIL:'||sqlstate||';'; end;
  insert into _pr values('steps', s);
  begin execute 'drop schema if exists sp_pols__S__ cascade'; exception when others then null; end;
  begin execute 'drop role if exists sp_pol__S__'; insert into _pr values('teardown','ok'); exception when others then insert into _pr values('teardown','FAIL:'||sqlstate); end;
end $$;
select k,v from _pr order by k;""",
     [("steps", "create_policy_to_custom=ok"), ("teardown", "ok")]),

    # Full-object-type ownership choreography: table/view/seq/function/schema transfer,
    # forward (as postgres) + owner-only under set-role + cross-role A->B + reverse B->A +
    # grant-postgres-to-custom (down reclaim, expect blocked).
    ("ownership_choreography", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare s text:=''; gpc text; begin
  execute 'create role sp_a__S__ nologin'; execute 'create role sp_b__S__ nologin';
  execute 'grant sp_a__S__ to postgres with set true, inherit false, admin false';
  execute 'grant sp_b__S__ to postgres with set true, inherit false, admin false';
  execute 'create schema sp_s__S__';
  execute 'create table sp_s__S__.t(id int)';
  execute 'create view sp_s__S__.v as select 1 x';
  execute 'create sequence sp_s__S__.sq';
  execute 'create function sp_s__S__.f() returns int language sql as $q$ select 1 $q$';
  begin execute 'set role sp_a__S__'; begin execute 'alter table sp_s__S__.t owner to sp_a__S__'; s:=s||'RED=ok(UNEXPECTED);'; exception when others then s:=s||'RED=FAIL:'||sqlstate||';'; end; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; end;
  -- grant receiver CREATE/USAGE to BOTH roles while postgres still owns the schema (a non-owner
  -- GRANT only WARNs and no-ops, so the receiver must be granted before the schema transfers away)
  execute 'grant create on schema sp_s__S__ to sp_a__S__'; execute 'grant usage on schema sp_s__S__ to sp_a__S__';
  execute 'grant create on schema sp_s__S__ to sp_b__S__'; execute 'grant usage on schema sp_s__S__ to sp_b__S__';
  begin execute 'alter table sp_s__S__.t owner to sp_a__S__'; s:=s||'fwd_table=ok;'; exception when others then s:=s||'fwd_table=FAIL:'||sqlstate||';'; end;
  begin execute 'alter view sp_s__S__.v owner to sp_a__S__'; s:=s||'fwd_view=ok;'; exception when others then s:=s||'fwd_view=FAIL:'||sqlstate||';'; end;
  begin execute 'alter sequence sp_s__S__.sq owner to sp_a__S__'; s:=s||'fwd_seq=ok;'; exception when others then s:=s||'fwd_seq=FAIL:'||sqlstate||';'; end;
  begin execute 'alter function sp_s__S__.f() owner to sp_a__S__'; s:=s||'fwd_func=ok;'; exception when others then s:=s||'fwd_func=FAIL:'||sqlstate||';'; end;
  begin execute 'alter schema sp_s__S__ owner to sp_a__S__'; s:=s||'fwd_schema=ok;'; exception when others then s:=s||'fwd_schema=FAIL:'||sqlstate||';'; end;
  begin execute 'set role sp_a__S__'; begin execute 'alter table sp_s__S__.t force row level security'; s:=s||'owner_only=ok;'; exception when others then s:=s||'owner_only=FAIL:'||sqlstate||';'; end; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'grant sp_b__S__ to sp_a__S__ with set true'; exception when others then s:=s||'grant_b_to_a=FAIL:'||sqlstate||';'; end;
  begin execute 'set role sp_a__S__'; begin execute 'alter table sp_s__S__.t owner to sp_b__S__'; s:=s||'cross=ok;'; exception when others then s:=s||'cross=FAIL:'||sqlstate||';'; end; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'revoke sp_b__S__ from sp_a__S__'; exception when others then null; end;
  begin execute 'grant sp_a__S__ to sp_b__S__ with set true'; exception when others then s:=s||'grant_a_to_b=FAIL:'||sqlstate||';'; end;
  begin execute 'set role sp_b__S__'; begin execute 'alter table sp_s__S__.t owner to sp_a__S__'; s:=s||'reverse=ok;'; exception when others then s:=s||'reverse=FAIL:'||sqlstate||';'; end; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'revoke sp_a__S__ from sp_b__S__'; exception when others then null; end;
  begin execute 'grant postgres to sp_a__S__ with set true'; gpc:='ACCEPTED'; begin execute 'revoke postgres from sp_a__S__'; exception when others then null; end; exception when others then gpc:='REJECTED:'||sqlstate; end;
  s:=s||'grant_postgres_to_custom='||gpc||';';
  insert into _pr values('steps', s);
  begin execute 'reset role'; exception when others then null; end;
  begin execute 'set role sp_a__S__'; execute 'drop schema if exists sp_s__S__ cascade'; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; begin execute 'drop schema if exists sp_s__S__ cascade'; exception when others then null; end; end;
  begin execute 'revoke sp_a__S__ from postgres'; exception when others then null; end;
  begin execute 'revoke sp_b__S__ from postgres'; exception when others then null; end;
  begin execute 'drop role if exists sp_a__S__'; exception when others then null; end;
  begin execute 'drop role if exists sp_b__S__'; exception when others then null; end;
  insert into _pr values('residue', coalesce((select 'schema:'||count(*) from pg_namespace where nspname='sp_s__S__'),'?')||';roles='||coalesce((select string_agg(rolname,',') from pg_roles where rolname in ('sp_a__S__','sp_b__S__')),'none'));
end $$;
select k,v from _pr order by k;""",
     [("steps", "RED=FAIL:42501"), ("steps", "fwd_table=ok"), ("steps", "fwd_view=ok"),
      ("steps", "fwd_seq=ok"), ("steps", "fwd_func=ok"), ("steps", "fwd_schema=ok"),
      ("steps", "owner_only=ok"), ("steps", "cross=ok"), ("steps", "reverse=ok"),
      ("steps", "grant_postgres_to_custom=REJECTED"), ("residue", "schema:0;roles=none")]),

    # DDL envelope exercised UNDER OWNER context (the real Phase-2 execution), incl. the
    # down-path positive PUBLIC re-grant on the owner's routine.
    ("ddl_envelope", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare s text:=''; begin
  execute 'create role sp_env__S__ nologin';
  execute 'grant sp_env__S__ to postgres with set true, inherit false, admin false';
  execute 'create schema sp_env__S__';
  execute 'grant create on schema sp_env__S__ to sp_env__S__'; execute 'grant usage on schema sp_env__S__ to sp_env__S__';
  execute 'alter schema sp_env__S__ owner to sp_env__S__';
  begin execute 'revoke create on schema public from public'; s:=s||'revoke_public_create=ok;'; begin execute 'grant create on schema public to public'; exception when others then null; end; exception when others then s:=s||'revoke_public_create=FAIL:'||sqlstate||';'; end;
  begin execute 'set role sp_env__S__';
    begin execute 'create table sp_env__S__.t(id int)'; s:=s||'create_table=ok;'; exception when others then s:=s||'create_table=FAIL:'||sqlstate||';'; end;
    begin execute 'alter table sp_env__S__.t enable row level security'; s:=s||'enable_rls=ok;'; exception when others then s:=s||'enable_rls=FAIL:'||sqlstate||';'; end;
    begin execute 'alter table sp_env__S__.t force row level security'; s:=s||'force_rls=ok;'; exception when others then s:=s||'force_rls=FAIL:'||sqlstate||';'; end;
    begin execute 'create policy p on sp_env__S__.t for select using (true)'; s:=s||'create_policy=ok;'; exception when others then s:=s||'create_policy=FAIL:'||sqlstate||';'; end;
    begin execute 'drop policy p on sp_env__S__.t'; s:=s||'drop_policy=ok;'; exception when others then s:=s||'drop_policy=FAIL:'||sqlstate||';'; end;
    begin execute 'create index sp_env_idx__S__ on sp_env__S__.t(id)'; s:=s||'create_index=ok;'; exception when others then s:=s||'create_index=FAIL:'||sqlstate||';'; end;
    begin execute 'create view sp_env__S__.v as select 1 x'; s:=s||'create_view=ok;'; exception when others then s:=s||'create_view=FAIL:'||sqlstate||';'; end;
    begin execute 'alter view sp_env__S__.v set (security_invoker=true)'; s:=s||'security_invoker=ok;'; exception when others then s:=s||'security_invoker=FAIL:'||sqlstate||';'; end;
    begin execute 'alter view sp_env__S__.v reset (security_invoker)'; s:=s||'reset_security_invoker=ok;'; exception when others then s:=s||'reset_security_invoker=FAIL:'||sqlstate||';'; end;
    begin execute 'create function sp_env__S__.fn() returns int language sql security definer as $q$ select 1 $q$'; s:=s||'secdef_fn=ok;'; exception when others then s:=s||'secdef_fn=FAIL:'||sqlstate||';'; end;
    begin execute 'revoke execute on function sp_env__S__.fn() from public'; s:=s||'revoke_exec_public=ok;'; exception when others then s:=s||'revoke_exec_public=FAIL:'||sqlstate||';'; end;
    begin execute 'grant execute on function sp_env__S__.fn() to public'; s:=s||'grant_exec_public=ok;'; exception when others then s:=s||'grant_exec_public=FAIL:'||sqlstate||';'; end;
    begin execute 'create function sp_env__S__.trg() returns trigger language plpgsql as $q$ begin return new; end $q$'; exception when others then s:=s||'trg_fn=FAIL:'||sqlstate||';'; end;
    begin execute 'create trigger tg after insert on sp_env__S__.t for each row execute function sp_env__S__.trg()'; s:=s||'create_trigger=ok;'; exception when others then s:=s||'create_trigger=FAIL:'||sqlstate||';'; end;
    execute 'reset role';
  exception when others then s:=s||'owner_block=ERR:'||sqlstate||';'; begin execute 'reset role'; exception when others then null; end; end;
  insert into _pr values('steps', s);
  begin execute 'reset role'; exception when others then null; end;
  begin execute 'set role sp_env__S__'; execute 'drop schema if exists sp_env__S__ cascade'; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; begin execute 'drop schema if exists sp_env__S__ cascade'; exception when others then null; end; end;
  begin execute 'revoke sp_env__S__ from postgres'; exception when others then null; end;
  begin execute 'drop role if exists sp_env__S__'; insert into _pr values('teardown','ok'); exception when others then insert into _pr values('teardown','FAIL:'||sqlstate); end;
end $$;
select k,v from _pr order by k;""",
     [("steps", "revoke_public_create=ok"), ("steps", "force_rls=ok"),
      ("steps", "security_invoker=ok"), ("steps", "reset_security_invoker=ok"),
      ("steps", "create_index=ok"), ("steps", "secdef_fn=ok"),
      ("steps", "revoke_exec_public=ok"), ("steps", "grant_exec_public=ok"),
      ("steps", "create_trigger=ok"), ("teardown", "ok")]),

    ("trigger_set_role", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare s text:=''; begin
  execute 'create role sp_to__S__ nologin';
  execute 'grant sp_to__S__ to postgres with set true, inherit false, admin false';
  execute 'create schema sp_ts__S__';
  execute 'grant create on schema sp_ts__S__ to sp_to__S__'; execute 'grant usage on schema sp_ts__S__ to sp_to__S__';
  execute 'alter schema sp_ts__S__ owner to sp_to__S__';
  begin execute 'set role sp_to__S__'; execute 'create table sp_ts__S__.tb(id int)'; execute 'create function sp_ts__S__.f() returns trigger language plpgsql as $q$ begin return new; end $q$'; execute 'reset role'; s:=s||'setup=ok;'; exception when others then s:=s||'setup=FAIL:'||sqlstate||';'; begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'create trigger tg after insert on sp_ts__S__.tb for each row execute function sp_ts__S__.f()'; s:=s||'trigger_as_postgres=ok(UNEXPECTED);'; exception when others then s:=s||'trigger_as_postgres=FAIL:'||sqlstate||';'; end;
  begin execute 'set role sp_to__S__'; execute 'create trigger tg2 after insert on sp_ts__S__.tb for each row execute function sp_ts__S__.f()'; execute 'reset role'; s:=s||'trigger_as_owner=ok;'; exception when others then s:=s||'trigger_as_owner=FAIL:'||sqlstate||';'; begin execute 'reset role'; exception when others then null; end; end;
  insert into _pr values('steps', s);
  begin execute 'reset role'; exception when others then null; end;
  begin execute 'set role sp_to__S__'; execute 'drop schema if exists sp_ts__S__ cascade'; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; begin execute 'drop schema if exists sp_ts__S__ cascade'; exception when others then null; end; end;
  begin execute 'revoke sp_to__S__ from postgres'; exception when others then null; end;
  begin execute 'drop role if exists sp_to__S__'; insert into _pr values('teardown','ok'); exception when others then insert into _pr values('teardown','FAIL:'||sqlstate); end;
end $$;
select k,v from _pr order by k;""",
     [("steps", "trigger_as_postgres=FAIL:42501"), ("steps", "trigger_as_owner=ok"),
      ("teardown", "ok")]),

    ("rls_enforcement", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare c int; begin
  execute 'create role sp_ro__S__ nologin nobypassrls';
  execute 'grant sp_ro__S__ to postgres with set true, inherit false, admin false';
  execute 'create schema sp_rs__S__';
  execute 'grant create on schema sp_rs__S__ to sp_ro__S__'; execute 'grant usage on schema sp_rs__S__ to sp_ro__S__';
  execute 'alter schema sp_rs__S__ owner to sp_ro__S__';
  begin execute 'set role sp_ro__S__';
    execute 'create table sp_rs__S__.t(id int)'; execute 'insert into sp_rs__S__.t values (1),(2),(3)';
    execute 'alter table sp_rs__S__.t enable row level security'; execute 'alter table sp_rs__S__.t force row level security';
    execute 'reset role';
  exception when others then insert into _pr values('setup','FAIL:'||sqlstate); begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'select count(*) from sp_rs__S__.t' into c; insert into _pr values('rows_as_postgres_bypassrls', c::text); exception when others then insert into _pr values('rows_as_postgres_bypassrls','ERR:'||sqlstate); end;
  begin execute 'set role sp_ro__S__'; execute 'select count(*) from sp_rs__S__.t' into c; execute 'reset role'; insert into _pr values('rows_as_owner_forcerls', c::text); exception when others then insert into _pr values('rows_as_owner_forcerls','ERR:'||sqlstate); begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'reset role'; exception when others then null; end;
  begin execute 'set role sp_ro__S__'; execute 'drop schema if exists sp_rs__S__ cascade'; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; begin execute 'drop schema if exists sp_rs__S__ cascade'; exception when others then null; end; end;
  begin execute 'revoke sp_ro__S__ from postgres'; exception when others then null; end;
  begin execute 'drop role if exists sp_ro__S__'; exception when others then null; end;
  insert into _pr values('residue', coalesce((select 'schema:'||count(*) from pg_namespace where nspname='sp_rs__S__'),'?'));
end $$;
select k,v from _pr order by k;""",
     [("rows_as_postgres_bypassrls", "3"), ("rows_as_owner_forcerls", "0"),
      ("residue", "schema:0")]),
]


def parse_policy():
    for a in sys.argv[1:]:
        if a.startswith("--gate-a-policy="):
            v = a.split("=", 1)[1].strip()
            if v in ("trusted-applier", "preprovisioned"):
                return v
            sys.stderr.write("ERROR: --gate-a-policy must be trusted-applier or preprovisioned\n")
            sys.exit(3)
    return "trusted-applier"  # Task-2.0 chosen model: postgres/applier exempt from invariant 8


def check_gate_a(obs, policy):
    """Policy-aware evaluation of the escalation probe. Returns (ok, mismatches, note)."""
    if "_error" in obs:
        return False, ["psql_error:" + obs["_error"]], ""
    canset = obs.get("set_role_after_selfgrant", "<missing>")
    escalatable = "SUCCESS_ESCALATED" in canset
    if policy == "trusted-applier":
        if escalatable:
            return True, [], ("escalation POSSIBLE - ACCEPTED under trusted-applier "
                              "(postgres exempt from invariant 8; non-admin roles unaffected)")
        return False, ["gate_a_escalation: expected self-escalation under managed Supabase, "
                       "got '%s' (platform behavior changed - re-review the trust model)" % canset], ""
    # preprovisioned: escalation must NOT be possible
    if "FAIL" in canset:
        return True, [], "escalation blocked - consistent with preprovisioned policy"
    return False, ["gate_a_escalation: escalation POSSIBLE (set_role=%s) - NOT allowed under "
                   "preprovisioned policy (roles must be minted out-of-band so postgres is not "
                   "their creator)" % canset], ""


def main():
    as_json = "--json" in sys.argv
    policy = parse_policy()
    env = build_env()
    token = os.environ.get("SUPABASE_PROBE_RUN") or ("r" + uuid.uuid4().hex[:10])
    results = []
    hard_fail = False
    for name, sql, checks in PROBES:
        obs = run_sql(env, sql.replace("__S__", token))
        note = ""
        if name == "gate_a_escalation":
            ok, mism, note = check_gate_a(obs, policy)
        else:
            mism = []
            if "_error" in obs:
                mism.append("psql_error:" + obs["_error"])
            else:
                for key, expect in checks:
                    got = obs.get(key, "<missing>")
                    if expect not in got:
                        mism.append("%s: expected ~'%s' got '%s'" % (key, expect, got))
            ok = not mism
        if not ok:
            hard_fail = True
        results.append({"probe": name, "match": ok, "observed": obs, "mismatches": mism, "note": note})

    matrix = {"passed": not hard_fail, "run_suffix": token, "gate_a_policy": policy,
              "probes": [{"probe": r["probe"], "match": r["match"], "mismatches": r["mismatches"],
                          "note": r["note"]} for r in results]}
    if as_json:
        print(json.dumps({"matrix": matrix, "detail": results}, indent=2))
    else:
        print("gate-a-policy: %s" % policy)
        for r in results:
            flag = "PASS" if r["match"] else "FAIL"
            print("[%s] %s" % (flag, r["probe"]))
            if r["note"]:
                print("       ~ " + r["note"])
            for m in r["mismatches"]:
                print("       - " + m)
        print("OVERALL: %s (run %s, gate-a-policy %s)" % ("PASS" if not hard_fail else "FAIL",
                                                          token, policy))
    sys.exit(0 if not hard_fail else 1)


if __name__ == "__main__":
    main()
