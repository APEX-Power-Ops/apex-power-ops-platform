import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))  # make `fixtures` importable regardless of rootdir
from fixtures.build_fixture import build

_OPS_TRUNCATE = (
    "truncate ops.apparatus, ops.scope_quote_line, ops.scope_quote, "
    "ops.scopes, ops.standard_hours, ops.projects cascade;"
)


def _dsn() -> str:
    return os.environ.get("OPS_DEV_DSN") or (
        "host=127.0.0.1 port=5432 dbname=ops_dev user=postgres "
        f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD', '')} "
        "sslmode=disable"
    )


@pytest.fixture
def dsn() -> str:
    return _dsn()


@pytest.fixture
def clean_ops() -> str:
    """Truncate ops data tables (keep schema) and return the dsn."""
    import psycopg

    d = _dsn()
    with psycopg.connect(d, autocommit=True) as c:
        c.execute(_OPS_TRUNCATE)
    return d


@pytest.fixture(scope="session")
def mini_workbook(tmp_path_factory) -> pathlib.Path:
    return build(tmp_path_factory.mktemp("wb") / "mini_estimator.xlsx")


@pytest.fixture
def real_workbook() -> pathlib.Path:
    p = os.environ.get("MINER_WORKBOOK")
    if not p or not pathlib.Path(p).exists():
        pytest.skip("set MINER_WORKBOOK to the Rev10 .xlsm on the host")
    return pathlib.Path(p)
