"""Destructive-target guard for the jobs migration tests (same class as the
packages/apex-jobs suite guard): the down files DROP the jobs schema
(001_jobs_enums_down.sql CASCADE), so the resolved target dbname
(ORCH_TEST_DSN wins, else ORCH_TEST_DB) must end in _test. Override only via
an explicit ORCH_TEST_DANGEROUSLY_ALLOW_DB=<that exact dbname>. Lives in
conftest so pytest aborts collection loudly (rc=4) before any test module
imports _dbtest."""
import os

import pytest
from psycopg import conninfo

_DBNAME = os.environ.get("ORCH_TEST_DB", "orchestration_test")
_DSN = os.environ.get("ORCH_TEST_DSN")
_TARGET = str(conninfo.conninfo_to_dict(_DSN).get("dbname", _DBNAME)) if _DSN else _DBNAME
if not _TARGET.endswith("_test") and \
        os.environ.get("ORCH_TEST_DANGEROUSLY_ALLOW_DB") != _TARGET:
    pytest.exit(
        f"refusing to run the jobs migration tests against '{_TARGET}': the "
        "down files DROP the jobs schema (001_jobs_enums_down.sql CASCADE). "
        "Use a disposable *_test DB (default orchestration_test), or set "
        f"ORCH_TEST_DANGEROUSLY_ALLOW_DB={_TARGET} to override explicitly.",
        returncode=4,
    )
