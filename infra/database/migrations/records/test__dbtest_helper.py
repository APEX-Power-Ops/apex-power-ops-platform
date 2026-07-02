# infra/database/migrations/records/test__dbtest_helper.py
"""Unit tests for the _dbtest env-contract helper. No database required.

Named WITHOUT a 3-digit numeric prefix on purpose: the runner's migration walk
only collects test_NNN_*.py, so this file never enters the walk.
"""
import os

import pytest

import _dbtest


def test_guard_refuses_records_dev(monkeypatch):
    monkeypatch.delenv("RECORDS_ALLOW_SHARED_DB", raising=False)
    with pytest.raises(_dbtest.RecordsEnvError, match="records_dev"):
        _dbtest.guard_target("host=127.0.0.1 port=5432 dbname=records_dev user=postgres")


def test_guard_allows_records_dev_with_optin(monkeypatch):
    monkeypatch.setenv("RECORDS_ALLOW_SHARED_DB", "1")
    d = "host=127.0.0.1 port=5432 dbname=records_dev user=postgres"
    assert _dbtest.guard_target(d) == d


def test_guard_passes_other_dbnames(monkeypatch):
    monkeypatch.delenv("RECORDS_ALLOW_SHARED_DB", raising=False)
    d = "host=x port=5432 dbname=records_val_20260702T000000_1 user=postgres"
    assert _dbtest.guard_target(d) == d


def test_require_dsn_raises_when_unset(monkeypatch):
    monkeypatch.delenv("RECORDS_DEV_DSN", raising=False)
    with pytest.raises(_dbtest.RecordsEnvError, match="RECORDS_DEV_DSN"):
        _dbtest.require_dsn()


def test_require_dsn_returns_and_guards(monkeypatch):
    monkeypatch.setenv("RECORDS_DEV_DSN", "host=h port=1 dbname=records_val_x user=u")
    assert _dbtest.require_dsn() == "host=h port=1 dbname=records_val_x user=u"


def test_dsn_params_parses_kv():
    p = _dbtest.dsn_params("host=127.0.0.1 port=5432 dbname=db1 user=u password=p sslmode=disable")
    assert p["host"] == "127.0.0.1" and p["port"] == "5432"
    assert p["dbname"] == "db1" and p["user"] == "u" and p["password"] == "p"


def test_neta_data_dir_missing_dir_names_variable(monkeypatch, tmp_path):
    monkeypatch.setenv("NETA_DATA_DIR", str(tmp_path / "nope"))
    with pytest.raises(_dbtest.RecordsEnvError, match="NETA_DATA_DIR"):
        _dbtest.neta_data_dir()


def test_neta_data_dir_missing_required_file_names_it(monkeypatch, tmp_path):
    monkeypatch.setenv("NETA_DATA_DIR", str(tmp_path))
    for name in _dbtest.REQUIRED_NETA_FILES[:-1]:
        (tmp_path / name).write_text("{}", encoding="utf-8")
    with pytest.raises(_dbtest.RecordsEnvError, match=_dbtest.REQUIRED_NETA_FILES[-1]):
        _dbtest.neta_data_dir()


def test_neta_data_dir_ok_and_neta_json_default(monkeypatch, tmp_path):
    monkeypatch.setenv("NETA_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("NETA_JSON", raising=False)
    for name in _dbtest.REQUIRED_NETA_FILES:
        (tmp_path / name).write_text("{}", encoding="utf-8")
    assert _dbtest.neta_data_dir() == str(tmp_path)
    assert _dbtest.neta_json() == os.path.join(
        str(tmp_path), "NETA-Master-Equipment-Table-Enhanced.json"
    )


def test_required_neta_files_exact_set():
    assert _dbtest.REQUIRED_NETA_FILES == (
        "NETA-Master-Equipment-Table-Enhanced.json",
        "NETA-ATS-2025-tables-extracted.json",
        "NETA-MTS-2023-tables-extracted.json",
    )
