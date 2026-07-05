"""Unit tests for the apex-jobs subprocess env policy (_env.sanitized_env).

Value-silence: assertions are on precomputed booleans / sorted NAME-lists / the
marker string only -- never env, set(env), env[...], or env.get(...) inside an
assert (pytest would render real values on failure). Battery values are fixed
placeholders, never asserted on.
"""
import os

from apex_jobs import _env

_SECRET_BATTERY = [
    "APEX_JOBS_PGPASSWORD", "DEV_PG_PASSWORD", "OPS_API_DSN",
    "OPS_INTAKE_WRITER_DSN", "SUPABASE_PROD_DSN", "PGPASSWORD",
    "TCC_BREAKER_RO_PW", "TCC_BREAKER_CODEX_PW", "GITHUB_TOKEN",
    "AWS_SECRET_ACCESS_KEY", "INFISICAL_CLIENT_SECRET",
]


def test_sanitized_env_strips_secret_names(monkeypatch):
    for k in _SECRET_BATTERY:
        monkeypatch.setenv(k, "PLACEHOLDER-TEST-VALUE")
    env = _env.sanitized_env("host")
    leaked = sorted(set(_SECRET_BATTERY) & set(env))
    assert leaked == []


def test_sanitized_env_keeps_basics_and_marker(monkeypatch):
    monkeypatch.setenv("HOME", "/home/olares")
    env = _env.sanitized_env("staging")
    home_present = "HOME" in env
    path_present = "PATH" in env
    marker = env.get("APEX_JOB_ENV")
    assert home_present is True
    assert path_present is True
    assert marker == "staging"


def test_sanitized_env_keeps_locale_and_xdg_by_prefix(monkeypatch):
    monkeypatch.setenv("LC_TIME", "en_US.UTF-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/home/olares/.config")
    env = _env.sanitized_env("host")
    lc_present = "LC_TIME" in env
    xdg_present = "XDG_CONFIG_HOME" in env
    assert lc_present is True
    assert xdg_present is True


def test_sanitized_env_command_path_no_prepend(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin")
    env = _env.sanitized_env("host")
    path_unchanged = env.get("PATH") == os.environ.get("PATH")
    assert path_unchanged is True


def test_sanitized_env_extra_path_prepends(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin")
    env = _env.sanitized_env("host", extra_path="/opt/agent/bin")
    prepended = env.get("PATH", "").startswith("/opt/agent/bin" + os.pathsep)
    assert prepended is True
