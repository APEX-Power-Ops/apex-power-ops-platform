#!/usr/bin/env python3
"""supabase_probe.py - reusable applier-privilege probe for the records lane on managed
(non-superuser) Supabase Postgres.

Given a target connection (value-silent, never printed), it exercises every privilege class
that records migrations 045-049 require - on uniquely-named scratch roles/objects that are
fully torn down (zero residue) - then compares the observed outcomes against the Phase-0
baseline (see PHASE0-FINDINGS.md) and emits a machine-readable pass/fail matrix. It exits
nonzero on ANY mismatch (an envelope drift), so it can gate a managed apply as the Phase-4
prod precondition.

This probe performs SCRATCH WRITES (creates + drops roles/objects transactionally). It
therefore needs its OWN scratch-write GO, distinct from and prior to the migration write GO.

Connection (value-silent; pick ONE):
  SUPABASE_PROBE_DSN   - a libpq conninfo or postgresql:// URI (parsed into PG* env, never echoed)
  or discrete:         SUPABASE_PROBE_HOST / SUPABASE_PROBE_PORT / SUPABASE_PROBE_USER /
                       SUPABASE_PROBE_DB + SUPABASE_PROBE_PW

Usage:
  SUPABASE_PROBE_DSN='...'  python3 supabase_probe.py [--json]
Requires psql on PATH. Value-silent: prints only probe names, ok/sqlstate tokens, and match
booleans - never the DSN or password. Exit 0 = envelope matches baseline; nonzero = drift.
"""
import os
import sys
import json
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


# Each probe: (name, sql, [(result_key, expected_substring), ...]). All scratch is torn down
# inside the DO block; a final 'select k,v from _pr' returns the outcome rows.
PROBES = [
    ("role_attr_A2", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare s text:=''; begin
  begin execute 'drop role if exists sp_attr'; exception when others then null; end;
  begin execute 'create role sp_attr nologin'; s:=s||'create=ok;'; exception when others then s:=s||'create=FAIL:'||sqlstate||';'; end;
  begin execute 'alter role sp_attr nosuperuser'; s:=s||'nosuperuser=ok;'; exception when others then s:=s||'nosuperuser=FAIL:'||sqlstate||';'; end;
  begin execute 'alter role sp_attr nobypassrls'; s:=s||'nobypassrls=ok;'; exception when others then s:=s||'nobypassrls=FAIL:'||sqlstate||';'; end;
  begin execute 'alter role sp_attr nocreaterole'; s:=s||'nocreaterole=ok;'; exception when others then s:=s||'nocreaterole=FAIL:'||sqlstate||';'; end;
  begin execute 'alter role sp_attr login'; s:=s||'login=ok;'; exception when others then s:=s||'login=FAIL:'||sqlstate||';'; end;
  begin execute 'alter role sp_attr superuser'; s:=s||'superuser=ok;'; exception when others then s:=s||'superuser=FAIL:'||sqlstate||';'; end;
  insert into _pr values('steps', s);
  begin execute 'drop role if exists sp_attr'; insert into _pr values('teardown','ok'); exception when others then insert into _pr values('teardown','FAIL:'||sqlstate); end;
end $$;
select k,v from _pr order by k;""",
     [("steps", "nosuperuser=FAIL:42501"), ("steps", "nobypassrls=ok"),
      ("steps", "login=ok"), ("steps", "superuser=FAIL:42501"), ("teardown", "ok")]),

    ("gate_a_creator_edge", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare edge text; canset text; after text; begin
  begin execute 'drop role if exists sp_ga'; exception when others then null; end;
  execute 'create role sp_ga nologin';
  select coalesce(string_agg('set='||set_option||'/inh='||inherit_option,';'),'NONE') into edge from pg_auth_members where roleid='sp_ga'::regrole and member='postgres'::regrole;
  begin execute 'set role sp_ga'; canset:='ok'; execute 'reset role'; exception when others then canset:='FAIL:'||sqlstate; begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'revoke sp_ga from postgres'; exception when others then null; end;
  select coalesce(string_agg(grantor::regrole::text,';'),'NONE') into after from pg_auth_members where roleid='sp_ga'::regrole and member='postgres'::regrole;
  insert into _pr values('edge', edge);
  insert into _pr values('postgres_can_set_role', canset);
  insert into _pr values('after_revoke', after);
  begin execute 'drop role if exists sp_ga'; insert into _pr values('teardown','ok'); exception when others then insert into _pr values('teardown','FAIL:'||sqlstate); end;
end $$;
select k,v from _pr order by k;""",
     [("edge", "set=false/inh=false"), ("postgres_can_set_role", "FAIL:42501"),
      ("after_revoke", "supabase_admin"), ("teardown", "ok")]),

    ("gate_b_policy_binding", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare s text:=''; begin
  begin execute 'drop schema if exists sp_pol cascade'; exception when others then null; end;
  begin execute 'drop role if exists sp_pol_owner'; exception when others then null; end;
  execute 'create role sp_pol_owner nologin';
  execute 'create schema sp_pol';
  execute 'create table sp_pol.t(id int)';
  execute 'alter table sp_pol.t enable row level security';
  begin execute 'create policy p on sp_pol.t for select to sp_pol_owner using (true)'; s:=s||'create_policy_to_custom=ok;'; exception when others then s:=s||'create_policy_to_custom=FAIL:'||sqlstate||';'; end;
  insert into _pr values('steps', s);
  begin execute 'drop schema if exists sp_pol cascade'; exception when others then null; end;
  begin execute 'drop role if exists sp_pol_owner'; insert into _pr values('teardown','ok'); exception when others then insert into _pr values('teardown','FAIL:'||sqlstate); end;
end $$;
select k,v from _pr order by k;""",
     [("steps", "create_policy_to_custom=ok"), ("teardown", "ok")]),

    ("choreography", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare s text:=''; gpc text; begin
  begin execute 'drop schema if exists sp_s cascade'; exception when others then null; end;
  begin execute 'drop role if exists sp_a'; exception when others then null; end;
  begin execute 'drop role if exists sp_b'; exception when others then null; end;
  execute 'create role sp_a nologin'; execute 'create role sp_b nologin';
  execute 'create schema sp_s'; execute 'create table sp_s.t(id int)';
  execute 'grant sp_a to postgres with set true, inherit false, admin false';
  execute 'grant sp_b to postgres with set true, inherit false, admin false';
  begin execute 'set role sp_a'; begin execute 'alter table sp_s.t owner to sp_a'; s:=s||'RED=ok(UNEXPECTED);'; exception when others then s:=s||'RED=FAIL:'||sqlstate||';'; end; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; end;
  execute 'grant create on schema sp_s to sp_a';
  execute 'grant usage on schema sp_s to sp_a';
  begin execute 'alter table sp_s.t owner to sp_a'; s:=s||'fwd=ok;'; exception when others then s:=s||'fwd=FAIL:'||sqlstate||';'; end;
  begin execute 'set role sp_a'; begin execute 'alter table sp_s.t force row level security'; s:=s||'owner_only=ok;'; exception when others then s:=s||'owner_only=FAIL:'||sqlstate||';'; end; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; end;
  execute 'grant create on schema sp_s to sp_b'; execute 'grant usage on schema sp_s to sp_b';
  begin execute 'grant sp_b to sp_a with set true'; exception when others then s:=s||'grant_b_to_a=FAIL:'||sqlstate||';'; end;
  begin execute 'set role sp_a'; begin execute 'alter table sp_s.t owner to sp_b'; s:=s||'cross=ok;'; exception when others then s:=s||'cross=FAIL:'||sqlstate||';'; end; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'revoke sp_b from sp_a'; exception when others then null; end;
  begin execute 'grant sp_a to sp_b with set true'; exception when others then s:=s||'grant_a_to_b=FAIL:'||sqlstate||';'; end;
  begin execute 'set role sp_b'; begin execute 'alter table sp_s.t owner to sp_a'; s:=s||'reverse=ok;'; exception when others then s:=s||'reverse=FAIL:'||sqlstate||';'; end; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'revoke sp_a from sp_b'; exception when others then null; end;
  begin execute 'grant postgres to sp_a with set true'; gpc:='ok'; begin execute 'revoke postgres from sp_a'; exception when others then null; end; exception when others then gpc:='FAIL:'||sqlstate; end;
  s:=s||'grant_postgres_to_custom='||gpc||';';
  insert into _pr values('steps', s);
  begin execute 'reset role'; exception when others then null; end;
  begin execute 'set role sp_a'; execute 'drop schema if exists sp_s cascade'; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; begin execute 'drop schema if exists sp_s cascade'; exception when others then null; end; end;
  begin execute 'revoke sp_a from postgres'; exception when others then null; end;
  begin execute 'revoke sp_b from postgres'; exception when others then null; end;
  begin execute 'drop role if exists sp_a'; exception when others then null; end;
  begin execute 'drop role if exists sp_b'; exception when others then null; end;
  insert into _pr values('residue', coalesce((select 'schema:'||count(*) from pg_namespace where nspname='sp_s'),'?')||';roles='||coalesce((select string_agg(rolname,',') from pg_roles where rolname in ('sp_a','sp_b')),'none'));
end $$;
select k,v from _pr order by k;""",
     [("steps", "RED=FAIL:42501"), ("steps", "fwd=ok"), ("steps", "owner_only=ok"),
      ("steps", "cross=ok"), ("steps", "reverse=ok"),
      ("steps", "grant_postgres_to_custom=FAIL:42501"), ("residue", "schema:0;roles=none")]),

    ("trigger_set_role", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare s text:=''; begin
  begin execute 'drop schema if exists sp_t cascade'; exception when others then null; end;
  begin execute 'drop role if exists sp_t_owner'; exception when others then null; end;
  execute 'create role sp_t_owner nologin';
  execute 'grant sp_t_owner to postgres with set true, inherit false, admin false';
  execute 'create schema sp_t';
  execute 'grant create on schema sp_t to sp_t_owner'; execute 'grant usage on schema sp_t to sp_t_owner';
  execute 'alter schema sp_t owner to sp_t_owner';
  begin execute 'set role sp_t_owner'; execute 'create table sp_t.tb(id int)'; execute 'create function sp_t.f() returns trigger language plpgsql as $q$ begin return new; end $q$'; execute 'reset role'; s:=s||'setup=ok;'; exception when others then s:=s||'setup=FAIL:'||sqlstate||';'; begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'create trigger tg after insert on sp_t.tb for each row execute function sp_t.f()'; s:=s||'trigger_as_postgres=ok(UNEXPECTED);'; exception when others then s:=s||'trigger_as_postgres=FAIL:'||sqlstate||';'; end;
  begin execute 'set role sp_t_owner'; execute 'create trigger tg2 after insert on sp_t.tb for each row execute function sp_t.f()'; execute 'reset role'; s:=s||'trigger_as_owner=ok;'; exception when others then s:=s||'trigger_as_owner=FAIL:'||sqlstate||';'; begin execute 'reset role'; exception when others then null; end; end;
  insert into _pr values('steps', s);
  begin execute 'reset role'; exception when others then null; end;
  begin execute 'set role sp_t_owner'; execute 'drop schema if exists sp_t cascade'; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; begin execute 'drop schema if exists sp_t cascade'; exception when others then null; end; end;
  begin execute 'revoke sp_t_owner from postgres'; exception when others then null; end;
  begin execute 'drop role if exists sp_t_owner'; insert into _pr values('teardown','ok'); exception when others then insert into _pr values('teardown','FAIL:'||sqlstate); end;
end $$;
select k,v from _pr order by k;""",
     [("steps", "trigger_as_postgres=FAIL:42501"), ("steps", "trigger_as_owner=ok"),
      ("teardown", "ok")]),

    ("rls_enforcement", r"""
drop table if exists _pr; create temp table _pr(k text,v text);
do $$ declare c int; begin
  begin execute 'drop schema if exists sp_r cascade'; exception when others then null; end;
  begin execute 'drop role if exists sp_r_owner'; exception when others then null; end;
  execute 'create role sp_r_owner nologin nobypassrls';
  execute 'grant sp_r_owner to postgres with set true, inherit false, admin false';
  execute 'create schema sp_r';
  execute 'grant create on schema sp_r to sp_r_owner'; execute 'grant usage on schema sp_r to sp_r_owner';
  execute 'alter schema sp_r owner to sp_r_owner';
  begin execute 'set role sp_r_owner';
    execute 'create table sp_r.t(id int)'; execute 'insert into sp_r.t values (1),(2),(3)';
    execute 'alter table sp_r.t enable row level security'; execute 'alter table sp_r.t force row level security';
    execute 'reset role';
  exception when others then insert into _pr values('setup','FAIL:'||sqlstate); begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'select count(*) from sp_r.t' into c; insert into _pr values('rows_as_postgres_bypassrls', c::text); exception when others then insert into _pr values('rows_as_postgres_bypassrls','ERR:'||sqlstate); end;
  begin execute 'set role sp_r_owner'; execute 'select count(*) from sp_r.t' into c; execute 'reset role'; insert into _pr values('rows_as_owner_forcerls', c::text); exception when others then insert into _pr values('rows_as_owner_forcerls','ERR:'||sqlstate); begin execute 'reset role'; exception when others then null; end; end;
  begin execute 'reset role'; exception when others then null; end;
  begin execute 'set role sp_r_owner'; execute 'drop schema if exists sp_r cascade'; execute 'reset role'; exception when others then begin execute 'reset role'; exception when others then null; end; begin execute 'drop schema if exists sp_r cascade'; exception when others then null; end; end;
  begin execute 'revoke sp_r_owner from postgres'; exception when others then null; end;
  begin execute 'drop role if exists sp_r_owner'; exception when others then null; end;
  insert into _pr values('residue', coalesce((select 'schema:'||count(*) from pg_namespace where nspname='sp_r'),'?'));
end $$;
select k,v from _pr order by k;""",
     [("rows_as_postgres_bypassrls", "3"), ("rows_as_owner_forcerls", "0"),
      ("residue", "schema:0")]),
]


def main():
    as_json = "--json" in sys.argv
    env = build_env()
    results = []
    hard_fail = False
    for name, sql, checks in PROBES:
        obs = run_sql(env, sql)
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
        results.append({"probe": name, "match": ok, "observed": obs, "mismatches": mism})

    matrix = {"passed": not hard_fail,
              "probes": [{"probe": r["probe"], "match": r["match"], "mismatches": r["mismatches"]} for r in results]}
    if as_json:
        print(json.dumps({"matrix": matrix, "detail": results}, indent=2))
    else:
        for r in results:
            flag = "PASS" if r["match"] else "FAIL"
            print("[%s] %s" % (flag, r["probe"]))
            for m in r["mismatches"]:
                print("       - " + m)
        print("OVERALL: %s" % ("PASS (envelope matches Phase-0 baseline)" if not hard_fail
                                else "FAIL (envelope drift vs baseline)"))
    sys.exit(0 if not hard_fail else 1)


if __name__ == "__main__":
    main()
