"""The slice's central discipline: the projection session cannot write."""
import psycopg
import pytest

from learning_projections.db import connect


def test_session_is_read_only():
    with connect() as conn:
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute("create table _ro_probe (i int)")
