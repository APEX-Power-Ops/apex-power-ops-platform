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
  select 'tbl:' || c.relkind || ':' || n.nspname || '.' || c.relname as x
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
    expected = list(range(nums[0], nums[-1] + 1))
    if nums != expected:
        missing = sorted(set(expected) - set(nums))
        raise HarnessError(f"migration sequence gap: missing {missing}")
    orphans = sorted(set(tests) - set(nums))
    if orphans:
        raise HarnessError(f"orphan test file(s) with no matching migration: {orphans}")
    return migs, tests


def derive_child_dsn(admin_dsn, dbname):
    if "dbname=" not in admin_dsn:
        raise HarnessError("admin DSN has no dbname= component")
    return re.sub(r"dbname=[^\s]+", f"dbname={dbname}", admin_dsn)


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


def main(argv=None):  # wired fully in the next task
    raise SystemExit("run_validation: tiers are wired in Task 6")


if __name__ == "__main__":
    main()
