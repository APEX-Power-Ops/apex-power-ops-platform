import psycopg

from learning_resolver.db import connect, dsn


def test_dsn_targets_learning_dev():
    assert "dbname=learning_dev" in dsn()


def test_connect_reads_baseline(dsn):
    with connect() as c:
        n = c.execute("select count(*) from study_content").fetchone()[0]
    assert n > 0  # the frozen baseline is populated (967 rows)
