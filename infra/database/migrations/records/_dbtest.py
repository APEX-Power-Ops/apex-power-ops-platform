# infra/database/migrations/records/_dbtest.py
"""Shared env-contract helper for the records migration tests and generators.

Single source for every default-resolution chain (PSQL_EXE, NETA paths) and for
the records_dev refusal guard. NO hardcoded credential fallbacks: RECORDS_DEV_DSN
must come from the environment (the validation runner sets it to a disposable
records_val_* database; standalone per-file runs skip loudly when it is absent).
Never inherits ambient PGHOST/PGUSER - they point at Supabase prod in some shells.
"""
import os
import re
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))

# Every external NETA extract filename the source-backed tests (023-038) read.
# The validation preflight asserts these EXACT filenames, never counts.
REQUIRED_NETA_FILES = (
    "NETA-Master-Equipment-Table-Enhanced.json",
    "NETA-ATS-2025-equipment-tests-v2.json",
    "NETA-ATS-2025-tables-extracted.json",
    "NETA-MTS-2023-tables-extracted.json",
)

_WIN_PSQL = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
_HOST_NETA = os.path.expanduser("~/neta-source/NETA-Data")
_WIN_NETA = (
    r"C:\Users\jjswe\OneDrive\Documents\GitHub\neta-ett-study-material"
    r"\Development\NETA-Data"
)


class RecordsEnvError(RuntimeError):
    """A records env-contract violation (missing or forbidden value)."""


def psql_exe():
    return os.environ.get("PSQL_EXE") or shutil.which("psql") or _WIN_PSQL


def neta_data_dir():
    d = os.environ.get("NETA_DATA_DIR") or (
        _HOST_NETA if os.path.isdir(_HOST_NETA) else _WIN_NETA
    )
    if not os.path.isdir(d):
        raise RecordsEnvError(
            f"NETA_DATA_DIR is not a directory: {d} (set NETA_DATA_DIR to the NETA extracts)"
        )
    missing = [f for f in REQUIRED_NETA_FILES if not os.path.isfile(os.path.join(d, f))]
    if missing:
        raise RecordsEnvError(
            f"NETA_DATA_DIR={d} is missing required extract file(s): {', '.join(missing)}"
        )
    return d


def neta_json():
    p = os.environ.get("NETA_JSON") or os.path.join(
        neta_data_dir(), "NETA-Master-Equipment-Table-Enhanced.json"
    )
    if not os.path.isfile(p):
        raise RecordsEnvError(f"NETA_JSON is not a file: {p} (set NETA_JSON)")
    return p


def dsn_params(dsn):
    return dict(re.findall(r"(\w+)=([^\s]+)", dsn))


def guard_target(dsn):
    if dsn_params(dsn).get("dbname") == "records_dev" and (
        os.environ.get("RECORDS_ALLOW_SHARED_DB") != "1"
    ):
        raise RecordsEnvError(
            "refusing to target shared records_dev (set RECORDS_ALLOW_SHARED_DB=1 "
            "only for an explicit legacy per-chip run)"
        )
    return dsn


def require_dsn():
    v = os.environ.get("RECORDS_DEV_DSN")
    if not v:
        raise RecordsEnvError(
            "RECORDS_DEV_DSN is not set (no fallback exists; see MANIFEST 'Validation')"
        )
    return guard_target(v)


def dsn():
    """Test-module variant: skip the whole module loudly when the DSN is absent."""
    v = os.environ.get("RECORDS_DEV_DSN")
    if not v:
        import pytest

        pytest.skip(
            "RECORDS_DEV_DSN is not set - records DB tests skipped",
            allow_module_level=True,
        )
    return guard_target(v)


def run_psql(fname, dsn_value):
    """Apply a .sql file (relative to this directory) to the DSN's database via psql.

    Connection params come from the DSN - never hardcoded - so the validation
    runner can point the applies at its disposable database.
    """
    p = dsn_params(guard_target(dsn_value))
    env = {**os.environ, "PGSSLMODE": "disable"}
    # Never let ambient PGPASSWORD leak through (it may belong to another
    # cluster): clear it, then set only the contract-provided value.
    env.pop("PGPASSWORD", None)
    pw = os.environ.get("RECORDS_DEV_PGPASSWORD") or p.get("password")
    if pw:
        env["PGPASSWORD"] = pw
    r = subprocess.run(
        [
            psql_exe(),
            "-h", p.get("host", "127.0.0.1"),
            "-p", p.get("port", "5432"),
            "-U", p.get("user", "postgres"),
            "-d", p["dbname"],
            "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(HERE, fname),
        ],
        env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"psql {fname} failed (rc={r.returncode}):\n{r.stderr}\n{r.stdout}"
        )
