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
        return {0, 1, 2, 3, 4}
    try:
        wanted = {int(x) for x in only.split(",") if x.strip()}
    except ValueError:
        raise HarnessError(f"--only takes a comma list of tiers 0-4, got {only!r}")
    unknown = wanted - {0, 1, 2, 3, 4}
    if not wanted or unknown:
        raise HarnessError(f"unknown tier(s) in --only: {sorted(unknown)} (valid: 0-4)")
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

    db_wanted = wanted & {3, 4}
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
                if wanted != {0, 1, 2, 3, 4}:
                    raise HarnessError("--only with DB tiers requires --db-dsn (records_val_* only)")
                if not admin:
                    detail = "RECORDS_PG_ADMIN_DSN is not set"
                    status = "FAIL" if args.require_db else "SKIP"
                    for n in sorted(db_wanted):
                        tiers.append(Tier(f"{n}-db", status, detail))
                    db_wanted = set()
                else:
                    check_admin_dsn(admin)
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
            finally:
                if created:
                    if args.keep_db:
                        print(f"[keep-db] retained database: {val_name} (drop it manually)")
                    else:
                        assert_val_name(val_name)
                        with _connect(admin) as c:
                            c.execute(f'drop database if exists "{val_name}" with (force)')
                        print(f"[drop] {val_name}")
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
