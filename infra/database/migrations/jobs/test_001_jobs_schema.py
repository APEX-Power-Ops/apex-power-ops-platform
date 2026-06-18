"""TDD - jobs domain schema (001 enums + 002 tables). RED until the .sql exist."""
from _dbtest import connect, psql_file

APPLY = ["001_jobs_enums.sql", "002_jobs_tables.sql"]
DOWN = ["002_jobs_tables_down.sql", "001_jobs_enums_down.sql"]


def _reset_up():
    for f in DOWN:
        try:
            psql_file(f)
        except Exception:
            pass
    for f in APPLY:
        psql_file(f)


def test_schema_tables_enums_exist():
    _reset_up()
    with connect() as c:
        ns = c.execute(
            "select 1 from information_schema.schemata where schema_name='jobs'"
        ).fetchone()
        assert ns, "jobs schema missing"
        tables = {r[0] for r in c.execute(
            "select table_name from information_schema.tables where table_schema='jobs'"
        ).fetchall()}
        assert {"job", "run", "gate"} <= tables, tables
        enums = {r[0] for r in c.execute(
            "select typname from pg_type t join pg_namespace n on n.oid=t.typnamespace "
            "where n.nspname='jobs' and t.typtype='e'"
        ).fetchall()}
        assert {"job_status_enum", "run_status_enum", "env_enum", "executor_enum",
                "authority_enum", "gate_state_enum"} <= enums, enums


def test_job_unique_dispatch_id_and_self_fk():
    _reset_up()
    with connect() as c:
        cons = {r[0] for r in c.execute(
            "select conname from pg_constraint con join pg_class rel on rel.oid=con.conrelid "
            "join pg_namespace n on n.oid=rel.relnamespace "
            "where n.nspname='jobs' and rel.relname='job'"
        ).fetchall()}
        assert any("dispatch_id" in x for x in cons), cons
        col = c.execute(
            "select 1 from information_schema.columns where table_schema='jobs' "
            "and table_name='job' and column_name='predecessor_id'"
        ).fetchone()
        assert col


def test_down_reverses():
    _reset_up()
    for f in DOWN:
        psql_file(f)
    with connect() as c:
        ns = c.execute(
            "select 1 from information_schema.schemata where schema_name='jobs'"
        ).fetchone()
        assert ns is None, "down should drop the jobs schema"
