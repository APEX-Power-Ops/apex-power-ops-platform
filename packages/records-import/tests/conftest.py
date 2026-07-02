# packages/records-import/tests/conftest.py
"""Env guard for the records-import DB-backed tests.

Same semantics as infra/database/migrations/records/_dbtest.py (skip loudly
when RECORDS_DEV_DSN is unset; refuse shared records_dev without explicit
opt-in). Duplicated locally on purpose: no import across the packages/infra
boundary. Keep the two in sync."""
import os
import re

import pytest


def require_records_dsn():
    dsn = os.environ.get("RECORDS_DEV_DSN")
    if not dsn:
        pytest.skip(
            "RECORDS_DEV_DSN is not set - records-import DB tests skipped",
            allow_module_level=True,
        )
    m = re.search(r"dbname=([^\s]+)", dsn)
    if m and m.group(1) == "records_dev" and os.environ.get("RECORDS_ALLOW_SHARED_DB") != "1":
        pytest.fail(
            "refusing to target shared records_dev (set RECORDS_ALLOW_SHARED_DB=1 "
            "only for an explicit legacy run)"
        )
    return dsn
