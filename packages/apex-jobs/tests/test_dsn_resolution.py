"""Contract lock for apex_jobs.db.resolve_dsn(): the apex-jobs worker password
comes from APEX_JOBS_PGPASSWORD (preferred) or DEV_PG_PASSWORD (fallback), and
builds the dev-tier DSN. Value-silent: assertions use non-secret SENTINELs and
precomputed booleans, never an env dump. Run standalone with --noconftest (no DB).
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


def test_injected_var_used_when_dev_pg_unset():
    dsn = _resolve_with({"APEX_JOBS_PGPASSWORD": "SENTINEL_A"})
    targets_dev = "dbname=orchestration_dev" in dsn
    right_user = "user=orchestration" in dsn
    uses_injected = "password=SENTINEL_A" in dsn
    assert targets_dev and right_user and uses_injected


def test_apex_jobs_pw_preferred_over_dev_pg():
    dsn = _resolve_with({"APEX_JOBS_PGPASSWORD": "SENTINEL_A", "DEV_PG_PASSWORD": "SENTINEL_B"})
    uses_apex = "password=SENTINEL_A" in dsn
    ignores_dev = "SENTINEL_B" not in dsn
    assert uses_apex and ignores_dev


def test_missing_both_raises():
    saved = {k: os.environ.get(k) for k in _KEYS}
    try:
        for k in _KEYS:
            os.environ.pop(k, None)
        raised = False
        try:
            db.resolve_dsn()
        except RuntimeError:
            raised = True
        assert raised
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
