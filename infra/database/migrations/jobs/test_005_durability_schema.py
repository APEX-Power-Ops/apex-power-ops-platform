"""TDD — jobs 005 durability + agent columns. RED until 005 exists."""
from _dbtest import psql_file, connect

APPLY = ["001_jobs_enums.sql", "002_jobs_tables.sql", "003_jobs_indexes.sql",
         "004_jobs_views.sql", "005_durability_and_agents.sql"]
DOWN = ["005_durability_and_agents_down.sql", "004_jobs_views_down.sql",
        "003_jobs_indexes_down.sql", "002_jobs_tables_down.sql", "001_jobs_enums_down.sql"]


def _reset_up():
    for f in DOWN:
        try:
            psql_file(f)
        except Exception:
            pass
    for f in APPLY:
        psql_file(f)


def _cols(c, table):
    return {r[0] for r in c.execute(
        "select column_name from information_schema.columns "
        "where table_schema='jobs' and table_name=%s", (table,)).fetchall()}


def test_new_columns_present_and_additive():
    _reset_up()
    with connect() as c:
        job = _cols(c, "job")
        assert {"kind", "max_attempts", "base_ref"} <= job, job
        # additive: the 002 columns survive
        assert {"dispatch_id", "payload", "status", "predecessor_id"} <= job, job
        run = _cols(c, "run")
        assert {"lease_expires_at", "heartbeat_at", "worktree_path",
                "branch", "diff_stat"} <= run, run
        assert {"attempt", "claimed_by", "env", "exit_code"} <= run, run


def test_job_kind_enum_and_awaiting_promotion():
    _reset_up()
    with connect() as c:
        kinds = {r[0] for r in c.execute(
            "select e.enumlabel from pg_enum e join pg_type t on t.oid=e.enumtypid "
            "join pg_namespace n on n.oid=t.typnamespace "
            "where n.nspname='jobs' and t.typname='job_kind_enum'").fetchall()}
        assert kinds == {"command", "agent"}, kinds
        statuses = {r[0] for r in c.execute(
            "select e.enumlabel from pg_enum e join pg_type t on t.oid=e.enumtypid "
            "join pg_namespace n on n.oid=t.typnamespace "
            "where n.nspname='jobs' and t.typname='job_status_enum'").fetchall()}
        assert "awaiting_promotion" in statuses, statuses


def test_down_drops_new_columns():
    _reset_up()
    for f in DOWN:
        psql_file(f)
    # full down (001_down drops the schema CASCADE)
    with connect() as c:
        ns = c.execute("select 1 from information_schema.schemata "
                       "where schema_name='jobs'").fetchone()
        assert ns is None, "down should drop the jobs schema"
