"""Contract lock for apex_jobs.db.resolve_dsn(): the apex-jobs worker password
comes from APEX_JOBS_PGPASSWORD (Infisical, injected). DEV_PG_PASSWORD is NOT a
fallback -- it is the postgres superuser password and does not authenticate as
the orchestration role. Value-silent: assertions use non-secret SENTINELs and
precomputed booleans, never an env dump. Lives in tests_unit/ (outside the DB
conftest's scope) so it always runs with no DB fixture or credentials.
"""
import os

import apex_jobs.db as db

_KEYS = (
    "APEX_JOBS_DSN", "APEX_JOBS_PGPASSWORD", "DEV_PG_PASSWORD",
    "APEX_JOBS_DB", "APEX_JOBS_HOST", "APEX_JOBS_PORT", "APEX_JOBS_USER",
)


def _resolve_with(overrides):
    saved = {k: os.environ.get(k) for k in _KEYS}
    try:
        for k in _KEYS:
            os.environ.pop(k, None)
        os.environ.update(overrides)
        return db.resolve_dsn()
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_apex_jobs_pw_resolves():
    dsn = _resolve_with({"APEX_JOBS_PGPASSWORD": "SENTINEL_A"})
    targets_dev = "dbname=orchestration_dev" in dsn
    right_user = "user=orchestration" in dsn
    uses_injected = "password=SENTINEL_A" in dsn
    assert targets_dev and right_user and uses_injected


def test_dev_pg_password_alone_does_not_resolve():
    # Load-bearing contract: DEV_PG_PASSWORD is the postgres superuser password,
    # not an orchestration fallback. With only it set, resolution must fail closed
    # and must not leak the value into the DSN or the error message.
    raised = False
    leaked = True
    try:
        out = _resolve_with({"DEV_PG_PASSWORD": "SENTINEL_B"})
        leaked = "SENTINEL_B" in out
    except RuntimeError as e:
        raised = True
        leaked = "SENTINEL_B" in str(e)
    assert raised and not leaked


def test_missing_apex_jobs_pw_raises():
    raised = False
    try:
        _resolve_with({})
    except RuntimeError:
        raised = True
    assert raised


def test_apex_jobs_dsn_override_wins():
    dsn = _resolve_with({"APEX_JOBS_DSN": "SENTINEL_DSN"})
    assert dsn == "SENTINEL_DSN"
