"""Tests for access_harness.hr1_guard.

HR1 rule: access_validation must contain only structural columns.
The pg fixture (conftest.py) applies 001_schemas.sql to tcc_fidelity_test
and tears it down on exit (autocommit=True; schema drop is in teardown).

The injected-column test uses ALTER TABLE within the live session.  Because
the pg fixture uses autocommit=True, the ALTER TABLE is immediately committed.
The teardown DROP SCHEMA ... CASCADE in conftest.py removes it automatically,
so no cleanup is needed within this test module.
"""
import psycopg
import pytest

from access_harness.hr1_guard import assert_no_interpretive_columns


def test_clean_schema_has_no_interpretive_columns(pg):
    """The schema created by 001_schemas.sql must pass HR1 with zero violations."""
    assert assert_no_interpretive_columns(pg) == []


def test_injected_interpretive_column_is_detected(pg):
    """Adding is_gap to a validation table must be caught by the guard.

    The pg fixture uses autocommit=True, so this ALTER TABLE is committed
    immediately.  conftest.py teardown drops the entire schema CASCADE.
    """
    pg.execute(
        "ALTER TABLE access_validation.row_count_reconciliation "
        "ADD COLUMN is_gap boolean"
    )
    viol = assert_no_interpretive_columns(pg)
    assert ("row_count_reconciliation", "is_gap") in viol


def test_legit_structural_columns_not_flagged(pg):
    """Structural columns (delta, matches, is_unique, etc.) must not be flagged."""
    assert assert_no_interpretive_columns(pg) == []
