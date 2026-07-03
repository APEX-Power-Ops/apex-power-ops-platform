"""The records validation gate. One command, five tiers, honest exit code.

Tiers: 0 syntax+origin, 1 converter tests, 2 records-import pure tests,
3 forward-incremental migration walk on a disposable records_val_* database,
4 records-import DB tests against that migrated database.

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
        return {0, 1, 2, 3, 4, 5}
    try:
        wanted = {int(x) for x in only.split(",") if x.strip()}
    except ValueError:
        raise HarnessError(f"--only takes a comma list of tiers 0-5, got {only!r}")
    unknown = wanted - {0, 1, 2, 3, 4, 5}
    if not wanted or unknown:
        raise HarnessError(f"unknown tier(s) in --only: {sorted(unknown)} (valid: 0-5)")
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

    db_wanted = wanted & {3, 4, 5}
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
                if wanted != {0, 1, 2, 3, 4, 5}:
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
