import pathlib
import psycopg
import pytest
from learning_capture.db import dsn

REPO = pathlib.Path(__file__).resolve().parents[3]
PROVISION = REPO / "scripts" / "learning" / "slice2d_provision_cohort.sql"
RETIRE = REPO / "scripts" / "learning" / "slice2d_retire_cohort.sql"
COHORT = "a0000000-2d00-4000-8000-000000000001"


def _run(sql_path):
    with psycopg.connect(dsn(), autocommit=True) as c:  # dsn() -> learning_test under conftest
        c.execute(sql_path.read_text(encoding="utf-8"))


def _row():
    with psycopg.connect(dsn(), autocommit=True) as c:
        return c.execute(
            "select target_certification_level::text, employee_id, is_active, "
            "study_preferences->>'data_fidelity' from user_profiles where id=%s", (COHORT,)).fetchone()


def test_provision_is_idempotent_and_shapes_the_cohort_row():
    _run(PROVISION)
    _run(PROVISION)  # second apply must not error or duplicate
    level, employee_id, is_active, fidelity = _row()
    assert level == "III"
    assert employee_id is None          # deferred per spec
    assert is_active is True
    assert fidelity == "rehearsal"


def test_retire_deactivates_without_deleting():
    _run(PROVISION)
    _run(RETIRE)
    level, employee_id, is_active, fidelity = _row()  # row STILL EXISTS
    assert is_active is False
