import psycopg

from learning_projections.db import dsn


def _scalar(sql):
    with psycopg.connect(dsn(), autocommit=True) as c:
        return c.execute(sql).fetchone()[0]


def test_fixture_rows_seeded():
    assert _scalar("select count(*) from user_profiles") == 5
    assert _scalar("select count(*) from ksas where certification_level='II'") == 4
    assert _scalar("select count(*) from learning_events") == 12
    assert _scalar("select count(*) from learning_events where study_content_id is null") == 1
    assert _scalar("select count(*) from edition_ksa_map where is_active=false") == 1


def test_fixture_refuses_non_test_db(monkeypatch):
    monkeypatch.setenv("LEARNING_DEV_DSN", "host=127.0.0.1 dbname=learning_dev user=postgres")
    from tests.conftest import _target
    import pytest
    with pytest.raises(RuntimeError):
        _target()
