"""Unit tests for run_validation pure functions. No database required.
No 3-digit prefix => excluded from the migration walk by construction."""
import os
import re

import pytest

import run_validation as rv


def _mk(tmp_path, names):
    for n in names:
        (tmp_path / n).write_text("-- x", encoding="utf-8")
    return str(tmp_path)


def test_enumerate_stack_happy(tmp_path):
    d = _mk(tmp_path, [
        "001_a.sql", "001_a_down.sql", "002_b.sql", "003_c.sql",
        "test_001_a.py", "test_003_c.py", "test__helper.py", "conftest.py",
    ])
    migs, tests = rv.enumerate_stack(d)
    assert migs == [(1, "001_a.sql"), (2, "002_b.sql"), (3, "003_c.sql")]
    assert tests == {1: "test_001_a.py", 3: "test_003_c.py"}


def test_enumerate_stack_gap_fails(tmp_path):
    d = _mk(tmp_path, ["001_a.sql", "003_c.sql"])
    with pytest.raises(rv.HarnessError, match="gap"):
        rv.enumerate_stack(d)


def test_enumerate_stack_orphan_test_fails(tmp_path):
    d = _mk(tmp_path, ["001_a.sql", "test_002_ghost.py"])
    with pytest.raises(rv.HarnessError, match="orphan"):
        rv.enumerate_stack(d)


def test_derive_child_dsn_swaps_only_dbname():
    child = rv.derive_child_dsn(
        "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=x sslmode=disable",
        "records_val_x",
    )
    assert "dbname=records_val_x" in child
    assert "host=127.0.0.1" in child and "user=postgres" in child
    assert "password=x" in child and "dbname=postgres" not in child


def test_check_admin_dsn_requires_postgres_db():
    rv.check_admin_dsn("host=h port=1 dbname=postgres user=u")
    with pytest.raises(rv.HarnessError, match="maintenance"):
        rv.check_admin_dsn("host=h port=1 dbname=records_dev user=u")
    with pytest.raises(rv.HarnessError, match="maintenance"):
        rv.check_admin_dsn("host=h port=1 dbname=ops_dev user=u")


def test_val_name_shape_and_assert():
    n = rv.make_val_name()
    assert re.fullmatch(r"records_val_\d{8}T\d{6}_\d+", n)
    rv.assert_val_name(n)
    for bad in ("records_dev", "postgres", "records_val", "x_records_val_1"):
        with pytest.raises(rv.HarnessError):
            rv.assert_val_name(bad)


def test_parse_tiers_default_and_valid():
    assert rv.parse_tiers("") == {0, 1, 2, 3, 4}
    assert rv.parse_tiers("3,4") == {3, 4}


def test_parse_tiers_rejects_unknown():
    with pytest.raises(rv.HarnessError, match="unknown tier"):
        rv.parse_tiers("9")
    with pytest.raises(rv.HarnessError, match="tiers 0-4"):
        rv.parse_tiers("x")


def test_summary_formats_all_statuses():
    tiers = [rv.Tier("0-syntax", "PASS", ""), rv.Tier("3-migrations", "FAIL", "boom"),
             rv.Tier("4-import-db", "SKIP", "tier 3 failed")]
    out = rv.summary(tiers)
    assert "0-syntax" in out and "PASS" in out and "FAIL" in out and "SKIP" in out
