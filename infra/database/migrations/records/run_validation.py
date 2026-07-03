"""The records validation gate. One command, seven tiers, honest exit code.

Tiers: 0 syntax+origin, 1 converter tests, 2 records-import pure tests,
3 forward-incremental migration walk on a disposable records_val_* database,
4 records-import DB tests against that migrated database, 5 role/RLS binding
proofs (Gate 3), 6 durable Gate-5 ownership + audit posture proofs.

DB safety: only ever CREATEs/DROPs the exact records_val_* name generated this
run; the admin DSN must point at the postgres maintenance DB; child processes
receive an explicit environment (no ambient DSN is ever consulted by a tier).

See docs/superpowers/specs/2026-07-02-records-validation-harness-design.md.
"""
import argparse
import collections
import datetime
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)

import _dbtest  # noqa: E402


class HarnessError(RuntimeError):
    """A harness-contract violation (preflight, naming, sequencing)."""


Tier = collections.namedtuple("Tier", "name status detail")

MIG_RE = re.compile(r"^(\d{3})_.+\.sql$")
TEST_RE = re.compile(r"^test_(\d{3})_.+\.py$")
VAL_RE = re.compile(r"^records_val_\d{8}T\d{6}_\d+$")

# Schema-only catalog fingerprint of the records schema: tables, columns,
# constraints, indexes, functions, triggers, enums. Data-only changes (the 006/
# 009 seeds that tests 005/008 apply beyond their own number) do NOT move it.
FINGERPRINT_SQL = """
select md5(coalesce(string_agg(x, '|' order by x), 'empty')) from (
  select 'tbl:' || c.relkind::text || ':' || n.nspname || '.' || c.relname as x
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'records'
  union all
  select 'col:' || table_name || '.' || column_name || ':' || data_type || ':'
         || coalesce(column_default, '') || ':' || is_nullable
    from information_schema.columns where table_schema = 'records'
  union all
  select 'con:' || conrelid::regclass::text || ':' || conname || ':' || pg_get_constraintdef(oid)
    from pg_constraint
   where connamespace = (select oid from pg_namespace where nspname = 'records')
  union all
  select 'idx:' || schemaname || '.' || indexname || ':' || indexdef
    from pg_indexes where schemaname = 'records'
  union all
  select 'fn:' || p.proname || ':' || md5(pg_get_functiondef(p.oid))
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'records'
  union all
  select 'trg:' || t.tgrelid::regclass::text || ':' || t.tgname || ':' || pg_get_triggerdef(t.oid)
    from pg_trigger t
   where not t.tgisinternal
     and t.tgrelid in (select c.oid from pg_class c join pg_namespace n
                        on n.oid = c.relnamespace where n.nspname = 'records')
  union all
  select 'enum:' || ty.typname || ':' || e.enumlabel || ':' || e.enumsortorder
    from pg_type ty join pg_enum e on e.enumtypid = ty.oid
    join pg_namespace n on n.oid = ty.typnamespace
   where n.nspname = 'records'
) s
"""


def enumerate_stack(d):
    """Completeness preflight: sorted migrations + num->test map, fail-closed.

    FAILs on any gap in the numeric sequence (a withheld/deleted migration) and
    on any orphan test (a test_NNN with no NNN migration - rename drift would
    otherwise silently stop that test from ever running)."""
    migs, tests = [], {}
    for f in sorted(os.listdir(d)):
        if f.endswith("_down.sql"):
            continue
        m = MIG_RE.match(f)
        if m:
            migs.append((int(m.group(1)), f))
        t = TEST_RE.match(f)
        if t:
            tests[int(t.group(1))] = f
    if not migs:
        raise HarnessError(f"no migrations found in {d}")
    nums = [n for n, _ in migs]
    dupes = [n for n, c in collections.Counter(nums).items() if c > 1]
    if dupes:
        raise HarnessError(f"duplicate migration numbers: {dupes}")
    if nums[0] != 1:
        raise HarnessError(
            f"migration sequence must start at 001 (schema foundation); found {nums[0]:03d} first"
        )
    expected = list(range(nums[0], nums[-1] + 1))
    if nums != expected:
        missing = sorted(set(expected) - set(nums))
        raise HarnessError(f"migration sequence gap: missing {missing}")
    orphans = sorted(set(tests) - set(nums))
    if orphans:
        raise HarnessError(f"orphan test file(s) with no matching migration: {orphans}")
    return migs, tests


def derive_child_dsn(admin_dsn, dbname):
    toks = admin_dsn.split()
    hits = [i for i, t in enumerate(toks) if t.startswith("dbname=")]
    if len(hits) != 1:
        raise HarnessError("admin DSN must contain exactly one dbname= component")
    toks[hits[0]] = f"dbname={dbname}"
    return " ".join(toks)


def check_admin_dsn(admin_dsn):
    db = _dbtest.dsn_params(admin_dsn).get("dbname")
    if db != "postgres":
        raise HarnessError(
            f"RECORDS_PG_ADMIN_DSN must point at the postgres maintenance DB, got dbname={db!r}"
        )


def make_val_name():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"records_val_{stamp}_{os.getpid()}"


def assert_val_name(name):
    if not VAL_RE.fullmatch(name):
        raise HarnessError(f"refusing CREATE/DROP: {name!r} is not a run-generated records_val_* name")


def parse_tiers(only):
    """Validate --only. Unknown tiers must REFUSE - a typo like --only 9
    running zero tiers and exiting 0 would be a false-green gate."""
    if not only:
        return {0, 1, 2, 3, 4, 5, 6}
    try:
        wanted = {int(x) for x in only.split(",") if x.strip()}
    except ValueError:
        raise HarnessError(f"--only takes a comma list of tiers 0-6, got {only!r}")
    unknown = wanted - {0, 1, 2, 3, 4, 5, 6}
    if not wanted or unknown:
        raise HarnessError(f"unknown tier(s) in --only: {sorted(unknown)} (valid: 0-6)")
    return wanted


def summary(tiers):
    lines = ["", "=== records validation summary ==="]
    for t in tiers:
        lines.append(f"  {t.name:<16} {t.status:<5} {t.detail}")
    return "\n".join(lines)


def _run(cmd, env=None, cwd=None):
    """Run a child, stream nothing, return (rc, tail). Exit code is checked
    directly by callers - never piped through anything that could mask it."""
    r = subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True)
    tail = "\n".join((r.stdout + "\n" + r.stderr).strip().splitlines()[-12:])
    return r.returncode, tail


def _pytest(paths, env, label):
    rc, tail = _run([sys.executable, "-m", "pytest", "-q", *paths], env=env, cwd=REPO_ROOT)
    print(f"--- {label} (rc={rc}) ---\n{tail}")
    return rc


def _connect(dsn_value):
    import psycopg

    print(f"[connect] dbname={_dbtest.dsn_params(dsn_value).get('dbname')}")
    return psycopg.connect(dsn_value, autocommit=True)


def _fingerprint(dsn_value):
    with _connect(dsn_value) as c:
        return c.execute(FINGERPRINT_SQL).fetchone()[0]


def tier0_syntax_origin():
    rc, tail = _run([sys.executable, "-m", "compileall", "-q",
                     os.path.join(REPO_ROOT, "packages", "power-test-converters"),
                     os.path.join(REPO_ROOT, "packages", "records-import"), HERE])
    if rc != 0:
        return Tier("0-syntax", "FAIL", tail)
    for name in ("power_test_converters", "records_import"):
        code = (f"import os,{name};p=os.path.abspath({name}.__file__);"
                f"raise SystemExit(0 if p.startswith({REPO_ROOT!r}) else 'ORIGIN:'+p)")
        rc, tail = _run([sys.executable, "-c", code])
        if rc != 0:
            return Tier("0-syntax", "FAIL",
                        f"{name} does not resolve inside this repo (dependency-confusion tripwire): {tail}")
    return Tier("0-syntax", "PASS", "compileall + origin asserts")


def tier1_converters(env):
    rc = _pytest([os.path.join("packages", "power-test-converters", "tests")], env, "tier1")
    return Tier("1-converters", "PASS" if rc == 0 else "FAIL", f"pytest rc={rc}")


PURE_IMPORT_TESTS = ["test_review_proposal.py", "test_ptm_transformer_mapping.py", "test_smoke.py"]
DB_IMPORT_TESTS = ["test_db_write.py", "test_ingest_end_to_end.py", "test_ingest_dtax_end_to_end.py"]


def tier2_import_pure(env):
    paths = [os.path.join("packages", "records-import", "tests", f) for f in PURE_IMPORT_TESTS]
    rc = _pytest(paths, env, "tier2")
    return Tier("2-import-pure", "PASS" if rc == 0 else "FAIL", f"pytest rc={rc}")


def _child_env(child_dsn):
    env = dict(os.environ)
    env["RECORDS_DEV_DSN"] = child_dsn
    pw = _dbtest.dsn_params(child_dsn).get("password")
    if pw:
        env["RECORDS_DEV_PGPASSWORD"] = pw
    env["NETA_DATA_DIR"] = _dbtest.neta_data_dir()
    env["NETA_JSON"] = _dbtest.neta_json()
    env["PSQL_EXE"] = _dbtest.psql_exe()
    env.pop("RECORDS_ALLOW_SHARED_DB", None)
    return env


def tier3_walk(child_dsn, executed, migs, tests):
    env = _child_env(child_dsn)
    for num, sql in migs:
        _dbtest.run_psql(sql, child_dsn)
        tf = tests.get(num)
        if not tf:
            continue
        pre = _fingerprint(child_dsn)
        rc = _pytest([os.path.join("infra", "database", "migrations", "records", tf)], env, tf)
        if rc != 0:
            return Tier("3-migrations", "FAIL", f"{tf} failed (rc={rc}); walk stopped")
        post = _fingerprint(child_dsn)
        if pre != post:
            return Tier("3-migrations", "FAIL",
                        f"{tf} PASSED but did not restore its migration (schema fingerprint moved)")
        executed.append(tf)
    return Tier("3-migrations", "PASS", f"{len(migs)} applied, {len(executed)} tests executed, 0 skipped")


def tier4_import_db(child_dsn, executed):
    env = _child_env(child_dsn)
    paths = [os.path.join("packages", "records-import", "tests", f) for f in DB_IMPORT_TESTS]
    rc = _pytest(paths, env, "tier4")
    if rc == 0:
        executed.extend(DB_IMPORT_TESTS)
    return Tier("4-import-db", "PASS" if rc == 0 else "FAIL",
                f"{len(DB_IMPORT_TESTS)} DB test files, pytest rc={rc}")


def snapshot_roles(admin, names=("records_api", "records_intake_writer")):
    with _connect(admin) as c:
        existing = {r[0] for r in c.execute(
            "select rolname from pg_roles where rolname = any(%s)", (list(names),)).fetchall()}
    return [n for n in names if n not in existing]   # roles 045 will create THIS run


WRITE_PATH = ["assets", "form_submissions", "form_field_values", "pm_schedules", "pm_events", "persons"]
VIEWS = {
    "v_asset_test_history": ["assets", "form_submissions", "form_templates"],
    "v_pm_due": ["pm_schedules", "assets", "pm_programs"],
}


def tier5_roles(child_dsn, val_name):
    """The complete binding proof set: PP1-2, DP1-9, DP-ESC. Every expected-raise is
    savepoint-bracketed (aborted-txn discipline). All dynamic proofs run in ONE rolled-back
    transaction so the disposable DB is left pristine; introspection asserts run read-only."""
    import psycopg
    rogue = f"records_val_rogue_{val_name.split('records_val_', 1)[1]}"
    if not re.fullmatch(r"records_val_rogue_\d{8}T\d{6}_\d+", rogue):
        return Tier("5-roles", "FAIL", f"bad rogue name {rogue!r}")
    fails = []

    def expect_raise(cur, sql, label, params=None):
        cur.execute("savepoint p")
        try:
            cur.execute(sql, params)
            cur.execute("rollback to savepoint p")
            fails.append(f"{label}: DID NOT RAISE")
        except psycopg.errors.Error:
            cur.execute("rollback to savepoint p")

    # --- introspection (read-only autocommit): DP6, DP7, DP8, polroles ---
    ro = psycopg.connect(child_dsn, autocommit=True)
    try:
        if ro.execute("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace "
                      "where n.nspname='records' and c.relkind='r' and not c.relrowsecurity").fetchone()[0]:
            fails.append("DP7: a records table has RLS disabled")
        for v in VIEWS:
            opts = ro.execute("select reloptions from pg_class c join pg_namespace n on n.oid=c.relnamespace "
                              "where n.nspname='records' and c.relname=%s", (v,)).fetchone()[0]
            if not (opts and any(o.startswith("security_invoker=") and o.split("=")[1] in ("true", "on", "1") for o in opts)):
                fails.append(f"DP8: {v} not security_invoker")
        if ro.execute("select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace, "
                      "lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a "
                      "where ns.nspname='records' and a.grantee=0 and a.privilege_type='EXECUTE'").fetchone()[0]:
            fails.append("DP6: PUBLIC holds EXECUTE on a records routine")
        if ro.execute("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace, "
                      "lateral aclexplode(coalesce(c.relacl, acldefault('r', c.relowner))) a "
                      "where n.nspname='records' and c.relkind in ('r','v') and a.grantee=0").fetchone()[0]:
            fails.append("DP6: PUBLIC holds a grant on a records table/view")
        if ro.execute("select count(*) from pg_policies where schemaname='records' "
                      "and (roles is null or 'public' = any(roles))").fetchone()[0]:
            fails.append("polroles: a records policy is TO PUBLIC")
    finally:
        ro.close()

    # --- dynamic proofs, ONE rolled-back transaction ---
    conn = psycopg.connect(child_dsn)  # autocommit=False
    try:
        cur = conn.cursor()
        cur.execute(f'create role "{rogue}" nosuperuser nologin nobypassrls')
        # seed a JOIN-satisfying set (as the maintenance role) for PP1/DP9 positive controls
        cur.execute("insert into records.asset_classes(class_code,name) values('t5','Tier5') returning asset_class_id")
        acid = cur.fetchone()[0]
        cur.execute("insert into records.assets(asset_tag,name,asset_class_id) values('T5','t5',%s) returning asset_id", (acid,))
        aid = cur.fetchone()[0]
        cur.execute("insert into records.form_templates(template_code,title,asset_class_id) values('t5','t5',%s) returning template_id", (acid,))
        tid = cur.fetchone()[0]
        cur.execute("insert into records.form_submissions(template_id,asset_id) values(%s,%s) returning form_submission_id", (tid, aid))
        sid = cur.fetchone()[0]
        cur.execute("insert into records.pm_programs(program_code,name,interval_value) values('t5','t5',1) returning pm_program_id")
        ppid = cur.fetchone()[0]
        cur.execute("insert into records.pm_schedules(pm_program_id,asset_id) values(%s,%s)", (ppid, aid))

        # PP1 + DP1 + DP-ESC(a) reader->writer, as records_api
        cur.execute("set session authorization records_api")
        cur.execute("select count(*) from records.form_submissions")            # PP1 read ok
        cur.execute("select count(*) from records.v_asset_test_history")        # PP1 view ok
        for t in WRITE_PATH:
            expect_raise(cur, f"insert into records.{t} default values", f"DP1 reader INSERT {t}")
            expect_raise(cur, f"update records.{t} set updated_at=now()", f"DP1 reader UPDATE {t}")
            expect_raise(cur, f"delete from records.{t}", f"DP1 reader DELETE {t}")
        expect_raise(cur, "set role records_intake_writer", "DP-ESC reader->writer")
        cur.execute("reset session authorization")

        # PP2 + DP2 + DP3 + DP4 + DP-ESC(a) writer->reader, as records_intake_writer
        cur.execute("set session authorization records_intake_writer")
        cur.execute("savepoint w")
        cur.execute("insert into records.form_submissions(template_id,asset_id) values(%s,%s) returning status", (tid, aid))
        if cur.fetchone()[0] != "draft":
            fails.append("PP2: writer INSERT did not default status to draft")
        cur.execute("rollback to savepoint w")
        expect_raise(cur, "update records.form_submissions set status='approved' where form_submission_id=%s", "DP2 form_submissions.status", (sid,))
        expect_raise(cur, "update records.form_submissions set reviewed_by='x' where form_submission_id=%s", "DP2 form_submissions.reviewed_by", (sid,))
        expect_raise(cur, "update records.pm_events set status='completed' where false", "DP2/D9 pm_events.status")
        expect_raise(cur, "update records.form_field_values set assessment='pass' where false", "DP2/D9 form_field_values.assessment")
        expect_raise(cur, "update records.persons set worker_class='1099' where false", "DP2/D9 persons.worker_class")
        expect_raise(cur, "update records.persons set employee_ref=gen_random_uuid() where false", "DP3 persons.employee_ref")
        expect_raise(cur, "update records.persons set match_adjudicated_by=gen_random_uuid() where false", "DP3 persons.match_adjudicated_by")
        expect_raise(cur, "drop table records.form_submissions", "DP4 writer DROP")
        expect_raise(cur, "alter table records.assets add column x int", "DP4 writer ALTER")
        expect_raise(cur, "set role records_api", "DP-ESC writer->reader")
        cur.execute("reset session authorization")

        # DP-ESC(b): a rogue role can assume NEITHER app role
        cur.execute(f'set session authorization "{rogue}"')
        expect_raise(cur, "set role records_api", "DP-ESC rogue->records_api")
        expect_raise(cur, "set role records_intake_writer", "DP-ESC rogue->records_intake_writer")
        cur.execute("reset session authorization")

        # DP5 accidental-grant: rogue with USAGE+SELECT on a write-path table -> default-deny + no write
        cur.execute(f'grant usage on schema records to "{rogue}"')
        cur.execute(f'grant select on records.form_submissions to "{rogue}"')
        cur.execute(f'set session authorization "{rogue}"')
        cur.execute("select count(*) from records.form_submissions")
        if cur.fetchone()[0] != 0:
            fails.append("DP5: rogue with SELECT saw rows (RLS default-deny failed)")
        expect_raise(cur, "insert into records.form_submissions default values", "DP5 rogue write")
        cur.execute("reset session authorization")

        # DP9 for EACH view: positive control (records_api sees rows) then rogue sees 0
        for view, bases in VIEWS.items():
            cur.execute("set session authorization records_api")
            cur.execute(f"select count(*) from records.{view}")
            if cur.fetchone()[0] < 1:
                fails.append(f"DP9 {view}: positive control 0 rows (join empty - seed problem)")
            cur.execute("reset session authorization")
            cur.execute(f'grant usage on schema records to "{rogue}"')  # idempotent
            cur.execute(f'grant select on records.{view} to "{rogue}"')
            for b in bases:
                cur.execute(f'grant select on records.{b} to "{rogue}"')
            cur.execute(f'set session authorization "{rogue}"')
            cur.execute(f"select count(*) from records.{view}")
            if cur.fetchone()[0] != 0:
                fails.append(f"DP9 {view}: rogue saw rows through the security_invoker view (RLS leak)")
            cur.execute("reset session authorization")
    finally:
        conn.rollback()   # undoes rogue role + grants + seeds
        conn.close()

    return Tier("5-roles", "FAIL" if fails else "PASS",
                "; ".join(fails) if fails else "PP1-2/DP1-9/DP-ESC/polroles green")


# ---- Tier 6 (Gate-5 ownership + audit posture, durable every-CI-run) --------
AUDIT_ROLES = ("records_owner", "records_fn_owner", "records_auditor")

# Ownership across ALL THREE catalogs (pg_class relkind r/v/m/S + pg_proc +
# pg_namespace) - the identical union 046/test_046 use - counting records objects
# whose OWNER is a rolsuper OR rolbypassrls role. Zero is the durable invariant.
OWNED_BY_SUPER_OR_BYPASS = """
select
  (select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace
     join pg_roles r on r.oid=c.relowner
    where ns.nspname='records' and c.relkind in ('r','v','m','S')
      and (r.rolsuper or r.rolbypassrls))
+ (select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
     join pg_roles r on r.oid=p.proowner
    where ns.nspname='records' and (r.rolsuper or r.rolbypassrls))
+ (select case when exists (select 1 from pg_namespace ns join pg_roles r on r.oid=ns.nspowner
                             where ns.nspname='records' and (r.rolsuper or r.rolbypassrls))
          then 1 else 0 end)
"""

# fn_audit_capture durable re-check: owner, SECURITY DEFINER, search_path pinned,
# no PUBLIC EXECUTE (materialized ACL, NULL-acl-safe). Mirrors 048's own asserts.
FN_CAPTURE_META = (
    "select pg_get_userbyid(proowner), prosecdef, "
    "  exists (select 1 from unnest(coalesce(proconfig,'{}'::text[])) x "
    "          where x like 'search_path=%'), "
    "  (select count(*) from pg_proc p2, "
    "     lateral aclexplode(coalesce(p2.proacl, acldefault('f', p2.proowner))) a "
    "   where p2.oid='records.fn_audit_capture()'::regprocedure "
    "     and a.grantee=0 and a.privilege_type='EXECUTE') "
    "from pg_proc where oid='records.fn_audit_capture()'::regprocedure"
)

# records_fn_owner EXACT ALLOWLIST - copied VERBATIM from 048_records_audit_log.sql
# (the '048:' error prefix retained so a Tier-6 failure names the same invariant),
# resolving the schema oid in THIS database. USAGE-present / CREATE-deny / PUBLIC-
# deny / owner / existence + the single pg_shdepend deptype='a' exclusivity edge.
FN_OWNER_ALLOWLIST = """
do $$
declare
  gcnt int;
  v_schema  text := 'records';
  v_owner   text := 'records_owner';
  v_fnowner text := 'records_fn_owner';
  v_schema_oid oid;
begin
  select oid into v_schema_oid from pg_namespace where nspname = v_schema;
  if v_schema_oid is null then
    raise exception '048: schema % does not exist (run after 045/048 GRANT)', v_schema; end if;
  if (select nspowner from pg_namespace where oid = v_schema_oid) <> (select oid from pg_roles where rolname = v_owner)
    then raise exception '048: schema % owner drifted (expected %); ownership confers implicit USAGE+CREATE', v_schema, v_owner; end if;
  if not has_schema_privilege(v_fnowner, v_schema, 'USAGE')
    then raise exception '048: % lacks USAGE on schema % (definer cannot reach audit_log)', v_fnowner, v_schema; end if;
  if not exists (select 1 from pg_namespace ns, lateral aclexplode(ns.nspacl) a join pg_roles g on g.oid = a.grantee
                 where ns.oid = v_schema_oid and g.rolname = v_fnowner and a.privilege_type = 'USAGE')
    then raise exception '048: % lacks an EXPLICIT USAGE ACL grant on schema % (effective USAGE may leak via PUBLIC/membership)', v_fnowner, v_schema; end if;
  if has_schema_privilege(v_fnowner, v_schema, 'CREATE')
    then raise exception '048: % must NOT hold CREATE on schema %', v_fnowner, v_schema; end if;
  if has_schema_privilege('public', v_schema, 'USAGE') or has_schema_privilege('public', v_schema, 'CREATE')
    then raise exception '048: PUBLIC holds USAGE/CREATE on schema % (migration 045 REVOKE reverted)', v_schema; end if;
  select count(*) into gcnt from pg_shdepend s join pg_roles r on r.oid = s.refobjid
   where r.rolname = v_fnowner and s.deptype = 'a'
     and not (s.classid = 'pg_namespace'::regclass
              and s.dbid  = (select oid from pg_database where datname = current_database())
              and s.objid = v_schema_oid);
  if gcnt > 0 then raise exception '048: % holds % ACL grant edge(s) beyond USAGE on schema % (cross-schema/column/type/default-priv/database/shared-object escalation)', v_fnowner, gcnt, v_schema; end if;
end $$;
"""

# zero pg_auth_members edges (either direction) touching ANY of the three Gate-5
# roles - the identical query 047 asserts, generalized to all three. DURABLE: a
# login role granted membership AFTER the migrations would escape a point-in-time
# SET ROLE sample, but this count catches it on every CI run.
MEMBERSHIP_EDGES = (
    "select count(*) from pg_auth_members am "
    "where am.roleid in (select oid from pg_roles where rolname = any(%s)) "
    "   or am.member in (select oid from pg_roles where rolname = any(%s))"
)

# trg_audit set == writer-grant set (records_intake_writer INSERT/UPDATE), same
# two counts 049/test_049 use.
TRG_WANT = (
    "select count(distinct table_name) from information_schema.role_column_grants "
    "where grantee='records_intake_writer' and table_schema='records' "
    "  and privilege_type in ('INSERT','UPDATE')"
)
TRG_GOT = (
    "select count(*) from pg_trigger tg join pg_class c on c.oid=tg.tgrelid "
    "  join pg_namespace ns on ns.oid=c.relnamespace "
    "where ns.nspname='records' and tg.tgname='trg_audit' and not tg.tgisinternal"
)


def tier6_posture(child_dsn):
    """Durable Gate-5 in-DB posture proof on the fully-migrated (001-049) DB.

    Every clause is a standing invariant the per-migration tests assert only
    point-in-time; Tier 6 re-proves them on the final migrated state on EVERY CI
    run so post-migration drift (a membership grant, an ownership move, a dropped
    grant) is caught. Mutating-identity checks use SET SESSION AUTHORIZATION
    (session_user switch); the FORCE-RLS red proof runs inside a rolled-back
    savepoint so the disposable DB is left pristine."""
    import psycopg
    fails = []
    rogue = None
    m = re.search(r"records_val_(\d{8}T\d{6}_\d+)$", _dbtest.dsn_params(child_dsn).get("dbname", ""))
    if m:
        rogue = f"records_val_t6rogue_{m.group(1)}"
        if not re.fullmatch(r"records_val_t6rogue_\d{8}T\d{6}_\d+", rogue):
            return Tier("6-posture", "FAIL", f"bad rogue name {rogue!r}")

    def expect_raise(cur, sql, label, params=None):
        cur.execute("savepoint p")
        try:
            cur.execute(sql, params)
            cur.execute("rollback to savepoint p")
            fails.append(f"{label}: DID NOT RAISE")
        except psycopg.errors.Error:
            cur.execute("rollback to savepoint p")

    # --- (a)(b)(c)(d-count)(e) static introspection (read-only autocommit) ----
    ro = psycopg.connect(child_dsn, autocommit=True)
    try:
        # (a) no records object owned by a super/bypassrls role (all 3 catalogs).
        if ro.execute(OWNED_BY_SUPER_OR_BYPASS).fetchone()[0]:
            fails.append("6a: a records object is owned by a super/bypassrls role")
        # (b) the three Gate-5 roles: flags + login posture.
        want_login = {"records_owner": False, "records_fn_owner": False, "records_auditor": True}
        seen = set()
        for name, su, brls, canlogin, cdb, crole, crepl in ro.execute(
            "select rolname, rolsuper, rolbypassrls, rolcanlogin, rolcreatedb, "
            "rolcreaterole, rolreplication from pg_roles where rolname = any(%s)",
            (list(AUDIT_ROLES),)).fetchall():
            seen.add(name)
            if su or brls:
                fails.append(f"6b: {name} is super/bypassrls")
            if canlogin != want_login[name]:
                fails.append(f"6b: {name} login flag {canlogin} != expected {want_login[name]}")
            if cdb or crole or crepl:
                fails.append(f"6b: {name} has createdb/createrole/replication")
        missing = set(AUDIT_ROLES) - seen
        if missing:
            fails.append(f"6b: Gate-5 role(s) absent: {sorted(missing)}")
        # (c) fn_audit_capture durable meta + the 048 exact allowlist.
        owner, secdef, sp_pinned, pub_exec = ro.execute(FN_CAPTURE_META).fetchone()
        if owner != "records_fn_owner":
            fails.append(f"6c: fn_audit_capture owner {owner} != records_fn_owner")
        if not secdef:
            fails.append("6c: fn_audit_capture is not SECURITY DEFINER")
        if not sp_pinned:
            fails.append("6c: fn_audit_capture search_path not pinned")
        if pub_exec:
            fails.append("6c: fn_audit_capture still has PUBLIC EXECUTE")
        try:
            ro.execute(FN_OWNER_ALLOWLIST)   # RAISEs on any allowlist violation
        except psycopg.errors.RaiseException as e:
            fails.append(f"6c allowlist: {str(e).strip().splitlines()[0]}")
        # (d) zero membership edges touching any Gate-5 role (durable no-drift).
        if ro.execute(MEMBERSHIP_EDGES, (list(AUDIT_ROLES), list(AUDIT_ROLES))).fetchone()[0]:
            fails.append("6d: a pg_auth_members edge touches a Gate-5 role (membership drift)")
        # (e) trg_audit set == writer-grant set.
        want = ro.execute(TRG_WANT).fetchone()[0]
        got = ro.execute(TRG_GOT).fetchone()[0]
        if got != want:
            fails.append(f"6e: trg_audit count {got} != writer-grant table count {want}")
        # (g) records_auditor holds NO table/column grant and NO policy outside
        # audit_log (source_links + every operational/reference table).
        if ro.execute(
            "select count(*) from information_schema.role_table_grants "
            "where grantee='records_auditor' and table_schema='records' "
            "  and table_name <> 'audit_log'").fetchone()[0]:
            fails.append("6g: records_auditor holds a table grant outside audit_log")
        if ro.execute(
            "select count(*) from information_schema.role_column_grants "
            "where grantee='records_auditor' and table_schema='records' "
            "  and table_name <> 'audit_log'").fetchone()[0]:
            fails.append("6g: records_auditor holds a column grant outside audit_log")
        if ro.execute(
            "select count(*) from pg_policies where schemaname='records' "
            "  and tablename <> 'audit_log' and 'records_auditor' = any(roles)").fetchone()[0]:
            fails.append("6g: records_auditor is named in a policy outside audit_log")
    finally:
        ro.close()

    # --- (d-SET ROLE)(f) identity-switch proofs (autocommit; no residue) -------
    # (d) SET ROLE records_owner/records_fn_owner denied from records_api + rogue.
    with psycopg.connect(child_dsn, autocommit=True) as c:
        for src in ("records_api",):
            c.execute(f"set session authorization {src}")
            for tgt in ("records_owner", "records_fn_owner"):
                try:
                    c.execute(f"set role {tgt}")
                    c.execute("reset role")
                    fails.append(f"6d: {src} could SET ROLE {tgt} (must be denied)")
                except psycopg.errors.Error:
                    pass
            c.execute("reset session authorization")
    # (f) audit isolation: records_auditor reads audit_log; api/writer cannot.
    with psycopg.connect(child_dsn, autocommit=True) as c:
        c.execute("set role records_auditor")
        try:
            c.execute("select count(*) from records.audit_log").fetchone()
        except psycopg.errors.Error as e:
            fails.append(f"6f: records_auditor cannot read audit_log: {e}")
        c.execute("reset role")
        for role in ("records_api", "records_intake_writer"):
            c.execute(f"set session authorization {role}")
            try:
                c.execute("select count(*) from records.audit_log").fetchone()
                fails.append(f"6f: {role} could read audit_log (must be denied)")
            except psycopg.errors.Error:
                pass
            c.execute("reset session authorization")

    # --- (d-rogue)(h) dynamic proofs, ONE rolled-back transaction --------------
    conn = psycopg.connect(child_dsn)  # autocommit=False
    try:
        cur = conn.cursor()
        # (d) a freshly-created rogue login role can assume NEITHER owner role.
        if rogue:
            cur.execute(f'create role "{rogue}" nosuperuser login nobypassrls')
            cur.execute(f'set session authorization "{rogue}"')
            expect_raise(cur, "set role records_owner", "6d rogue->records_owner")
            expect_raise(cur, "set role records_fn_owner", "6d rogue->records_fn_owner")
            cur.execute("reset session authorization")
        # (h) FORCE-RLS negative control: drop the INSERT policy inside a savepoint,
        # fire the definer path via a REAL writer insert (persons carries trg_audit,
        # and display_name is FK-independent), assert the capture RAISES the RLS
        # violation, then rollback to the savepoint (which un-drops the policy). If
        # the policy were a no-op (FORCE missing / owner bypass) the insert SUCCEEDS.
        cur.execute("savepoint h")
        cur.execute("drop policy p_audit_log_ins on records.audit_log")
        cur.execute("set session authorization records_intake_writer")
        raised = False
        try:
            cur.execute("insert into records.persons (display_name) values ('t6-forcerls-probe')")
        except psycopg.errors.InsufficientPrivilege as e:
            raised = True
            if e.sqlstate != "42501" or "row-level security policy" not in str(e):
                fails.append(f"6h: capture raised but not the expected RLS violation: {e}")
        except psycopg.errors.Error as e:
            raised = True
            fails.append(f"6h: capture raised an unexpected error (not 42501 RLS): {e}")
        if not raised:
            fails.append("6h: writer insert SUCCEEDED with p_audit_log_ins dropped "
                         "(FORCE-RLS no-op / owner bypass - audit_log admission is not policy-gated)")
        cur.execute("rollback to savepoint h")   # aborts the txn + un-drops the policy
        # the policy is back after the savepoint rollback.
        cur.execute("reset session authorization")
        if cur.execute(
            "select count(*) from pg_policies where schemaname='records' "
            "and tablename='audit_log' and policyname='p_audit_log_ins'").fetchone()[0] != 1:
            fails.append("6h: p_audit_log_ins not restored by savepoint rollback")
    finally:
        conn.rollback()   # undoes the rogue role + everything above
        conn.close()

    return Tier("6-posture", "FAIL" if fails else "PASS",
                "; ".join(fails) if fails
                else "ownership/roles/definer-allowlist/no-membership/trigger-set/isolation/FORCE-RLS green")


def main(argv=None):
    ap = argparse.ArgumentParser(description="records validation gate")
    ap.add_argument("--require-db", action="store_true",
                    help="CI mode: any absence/skip on DB or source inputs is a failure")
    ap.add_argument("--only", default="", help="comma list of tiers to run, e.g. 3,4")
    ap.add_argument("--db-dsn", default="", help="explicit records_val_* DSN (required with --only 3/4)")
    ap.add_argument("--keep-db", action="store_true", help="skip the drop; print the retained name")
    args = ap.parse_args(argv)

    try:
        wanted = parse_tiers(args.only)
    except HarnessError as e:
        print(f"error: {e}")
        return 2
    tiers, executed = [], []
    admin = os.environ.get("RECORDS_PG_ADMIN_DSN", "")
    child_dsn, val_name, created = "", "", False
    created_roles = []

    if args.db_dsn:
        name = _dbtest.dsn_params(args.db_dsn).get("dbname", "")
        assert_val_name(name)
        child_dsn = args.db_dsn

    if 0 in wanted:
        tiers.append(tier0_syntax_origin())
    if 1 in wanted:
        tiers.append(tier1_converters(dict(os.environ)))
    if 2 in wanted:
        tiers.append(tier2_import_pure(dict(os.environ)))

    db_wanted = wanted & {3, 4, 5, 6}
    if db_wanted and not any(t.status == "FAIL" for t in tiers):
        try:
            # Source + completeness preflights run BEFORE any skip decision
            # and BEFORE any CREATE (spec sec 3; red proof 1 depends on it).
            migs, tests = None, None
            if 3 in wanted:
                _dbtest.neta_data_dir()
                _dbtest.neta_json()
                migs, tests = enumerate_stack(HERE)
            if not child_dsn:
                if wanted != {0, 1, 2, 3, 4, 5, 6}:
                    raise HarnessError("--only with DB tiers requires --db-dsn (records_val_* only)")
                if not admin:
                    detail = "RECORDS_PG_ADMIN_DSN is not set"
                    status = "FAIL" if args.require_db else "SKIP"
                    for n in sorted(db_wanted):
                        tiers.append(Tier(f"{n}-db", status, detail))
                    db_wanted = set()
                else:
                    check_admin_dsn(admin)
                    created_roles = snapshot_roles(admin)
                    val_name = make_val_name()
                    assert_val_name(val_name)
                    with _connect(admin) as c:
                        exists = c.execute(
                            "select 1 from pg_database where datname = %s", (val_name,)
                        ).fetchone()
                        if exists:
                            raise HarnessError(f"disposable name already exists: {val_name}")
                        c.execute(f'create database "{val_name}"')
                    created = True
                    child_dsn = derive_child_dsn(admin, val_name)
            try:
                if 3 in db_wanted:
                    tiers.append(tier3_walk(child_dsn, executed, migs, tests))
                if 4 in db_wanted and not any(
                    t.name == "3-migrations" and t.status == "FAIL" for t in tiers
                ):
                    if 3 in db_wanted or args.db_dsn:
                        tiers.append(tier4_import_db(child_dsn, executed))
                    else:
                        tiers.append(Tier("4-import-db", "SKIP", "no migrated target (run tier 3 or pass --db-dsn)"))
                elif 4 in db_wanted:
                    tiers.append(Tier("4-import-db", "SKIP", "tier 3 failed"))
                if 5 in db_wanted and not any(t.name=="3-migrations" and t.status=="FAIL" for t in tiers):
                    if 3 in db_wanted or args.db_dsn:
                        tiers.append(tier5_roles(child_dsn, val_name or _dbtest.dsn_params(child_dsn).get("dbname")))
                    else:
                        tiers.append(Tier("5-roles","SKIP","no migrated target"))
                elif 5 in db_wanted:
                    tiers.append(Tier("5-roles","SKIP","tier 3 failed"))
                if 6 in db_wanted and not any(t.name=="3-migrations" and t.status=="FAIL" for t in tiers):
                    if 3 in db_wanted or args.db_dsn:
                        tiers.append(tier6_posture(child_dsn))
                    else:
                        tiers.append(Tier("6-posture","SKIP","no migrated target"))
                elif 6 in db_wanted:
                    tiers.append(Tier("6-posture","SKIP","tier 3 failed"))
            finally:
                if created:
                    if args.keep_db:
                        print(f"[keep-db] retained database: {val_name} (drop it manually)")
                    else:
                        assert_val_name(val_name)
                        with _connect(admin) as c:
                            c.execute(f'drop database if exists "{val_name}" with (force)')
                        print(f"[drop] {val_name}")
                for role in created_roles:   # from snapshot_roles(), only roles this run created
                    try:
                        with _connect(admin) as c:
                            has_pw = c.execute("select rolpassword is not null from pg_authid where rolname=%s", (role,)).fetchone()
                            if has_pw and has_pw[0]:
                                print(f"[keep-role] {role} carries a password; left in place"); continue
                            c.execute(f'drop role if exists "{role}"')
                            print(f"[drop-role] {role}")
                    except Exception as e:
                        print(f"[keep-role] {role}: {e}")
        except (HarnessError, _dbtest.RecordsEnvError) as e:
            tiers.append(Tier("3-migrations" if 3 in wanted else "4-import-db", "FAIL", str(e)))
    elif db_wanted:
        for n in sorted(db_wanted):
            tiers.append(Tier(f"{n}-db", "SKIP", "earlier tier failed"))

    print(summary(tiers))
    print(f"executed test files: {len(executed)}")
    failed = any(t.status == "FAIL" for t in tiers)
    skipped = any(t.status == "SKIP" for t in tiers)
    if failed or (args.require_db and skipped):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
