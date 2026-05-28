"""Tests for control-plane database URL resolution."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost/test")

import config


def test_resolve_database_url_prefers_governed_live_dsn_names():
    env = {
        "APEX_OLARES_LIVE_DSN": "postgresql://live/apex",
        "SEAM_DATABASE_URL": "postgresql://seam/apex",
        "APEX_DB_CONNECTION_STRING": "postgresql://compat/apex",
        "DATABASE_URL": "postgresql://fallback/apex",
    }

    assert config.resolve_database_url(env.get) == "postgresql://live/apex"


def test_resolve_database_url_falls_back_through_supported_names():
    env = {
        "APEX_OLARES_LIVE_DSN": "",
        "SEAM_DATABASE_URL": None,
        "APEX_DB_CONNECTION_STRING": "postgresql://compat/apex",
        "DATABASE_URL": "postgresql://fallback/apex",
    }

    assert config.resolve_database_url(env.get) == "postgresql://compat/apex"


def test_resolve_database_url_requires_supported_name():
    with pytest.raises(RuntimeError, match="Expected one of"):
        config.resolve_database_url({}.get)


def test_build_connect_args_omits_statement_timeout_for_supabase_transaction_pooler():
    connect_args = config.build_connect_args(
        "postgresql://postgres:secret@db.fxoyniqnrlkxfligbxmg.supabase.co:6543/postgres"
    )

    assert connect_args == {}


def test_build_connect_args_keeps_statement_timeout_for_direct_postgres_connections():
    connect_args = config.build_connect_args(
        "postgresql://postgres:secret@db.fxoyniqnrlkxfligbxmg.supabase.co:5432/postgres"
    )

    assert connect_args == {"options": "-c statement_timeout=30000"}


def test_runtime_env_files_prefers_repo_root_env_local_before_backend_env():
    config_path = Path("C:/repo/apps/control-plane-api/config.py")

    env_files = config.runtime_env_files(config_path)

    assert env_files == (
        Path("C:/repo/.env.local"),
        Path("C:/repo/apps/control-plane-api/.env"),
    )


def test_load_runtime_env_loads_existing_files_in_precedence_order(tmp_path):
    config_path = tmp_path / "apps" / "control-plane-api" / "config.py"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("# config", encoding="utf-8")

    root_env = tmp_path / ".env.local"
    backend_env = config_path.with_name(".env")
    root_env.write_text("SEAM_DATABASE_URL=postgresql://live/apex\n", encoding="utf-8")
    backend_env.write_text("DATABASE_URL=postgresql://fallback/apex\n", encoding="utf-8")

    loaded = []

    def fake_loader(path):
        loaded.append(Path(path))

    env_files = config.load_runtime_env(config_path=config_path, loader=fake_loader)

    assert env_files == (root_env, backend_env)
    assert loaded == [root_env, backend_env]