# Records Validation Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One trustworthy records gate: a tiered runner that validates converters, records-import, and the full 001-044 migration stack against a disposable database it creates and drops, with an explicit env contract (zero hardcoded credential fallbacks), NETA source-data provisioning as a first-class gate, and a CI workflow that proves it all on ephemeral infrastructure.

**Architecture:** A shared `_dbtest.py` helper owns every env-resolution chain and guard; 38 migration tests + 5 generators are mechanically rewritten onto it by an exact-match-asserted script; `run_validation.py` runs 5 tiers (syntax+origin, converters, records-import pure, forward-incremental migration walk with completeness preflight + restoration assert, records-import DB tests) against `records_val_*` databases only; `records-ci.yml` reproduces the whole flow with a postgres:17 service and a SHA-pinned checkout of the private NETA source repo.

**Tech Stack:** Python 3.11+, psycopg3, pytest, psql CLI, GitHub Actions, uv (host) / pip (CI).

**Spec:** `docs/superpowers/specs/2026-07-02-records-validation-harness-design.md` rev 3 (`22f74e5b`). Decisions D1-D9 are RATIFIED - do not relitigate them.

## Global Constraints

- **Execution environment:** all commands run ON THE HOST in the lane worktree `W=/home/olares/code/apex/apex-records-validation` (branch `records/validation-harness`). From the controller, wrap each command as `ssh olares-mesh '...'`. `uv` needs `export PATH=$HOME/.local/bin:$PATH` first.
- **Test/run convention (host):** `RUN='uv run --with psycopg[binary] --with pytest --with-editable /home/olares/code/apex/apex-records-validation/packages/power-test-converters --with-editable /home/olares/code/apex/apex-records-validation/packages/records-import'` then `$RUN python -m pytest ...`. Quote `psycopg[binary]` if the shell globs it.
- **ASCII only** on every added line (no em-dashes, no arrows, no section signs). Audit with the Python one-liner in Task 9 before every commit.
- **NEVER echo secrets:** no DSN values, no passwords, in code, logs, commit messages, or PR text. Compose DSNs from env at runtime. The literal `TCC_v5_2025` may appear ONLY in grep commands verifying its removal.
- **NEVER target `records_dev`:** no test, script, or runner invocation in this plan may point at `records_dev`. The shared dev DB is out of the loop entirely. Never run destructive migration tests against it.
- **Single-role model (D7):** the disposable DB DSN is the admin DSN with dbname swapped. Admin DSN dbname must be exactly `postgres`.
- **Disposable DB names:** `records_val_<UTCSTAMP>_<PID>` only; CREATE/DROP assert this exact run-generated name (allowlist).
- **Stop on first failure** inside Tier 3; exit codes unmasked (never pipe a test command into anything before checking its exit code).
- **CI:** python `3.11`, `ubuntu-latest`, pinned action SHAs: `actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4.3.1`, `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0`.
- **Commits:** small, per-task, message ends with `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- **No schema changes, no app-code feature work, no RLS.** Docs-and-harness only.
- Merges are operator-gated: open the PR at the end; do not merge.

## File Map

| File | Action | Responsibility |
| --- | --- | --- |
| `infra/database/migrations/records/_dbtest.py` | Create | Env contract, guards, psql runner, NETA validation (single source) |
| `infra/database/migrations/records/test__dbtest_helper.py` | Create | Unit tests for `_dbtest` (no DB; numeric-prefix regex excludes it from the walk) |
| `infra/database/migrations/records/conftest.py` | Rewrite | Thin shim delegating defaults to `_dbtest` |
| `infra/database/migrations/records/test_0NN_*.py` (38 files) | Scripted rewrite | Route creds/psql/NETA through `_dbtest` |
| `infra/database/migrations/records/gen_020/021/022/039/040_*.py` (5 files) | Scripted rewrite | `require_dsn()`, no fallback |
| `packages/records-import/tests/conftest.py` | Create | `require_records_dsn()` skip + records_dev guard |
| `packages/records-import/tests/test_db_write.py`, `test_ingest_end_to_end.py`, `test_ingest_dtax_end_to_end.py` | Modify | Use `require_records_dsn()`; drop fallback + sys.path hack |
| `packages/power-test-converters/src/power_test_converters/testing.py` | Create | Promoted sample builders (public API) |
| `packages/power-test-converters/tests/test_ptm_to_dtax.py` | Modify | Import builders from the package |
| `packages/records-import/pyproject.toml` | Modify | dependency-groups + uv.sources declaration (D8) |
| `infra/database/migrations/records/run_validation.py` | Create | The tiered runner |
| `infra/database/migrations/records/test_run_validation_unit.py` | Create | Unit tests for runner pure functions |
| `.github/workflows/records-ci.yml` | Create | CI on the calc-engine pattern + private source checkout |
| `infra/database/migrations/records/MANIFEST.md` | Modify | New "Validation" section |
| `reference/records/CURRENT-STATE.md`, `.env.dev.template`, `docs/lanes/README.md` | Modify | Docs |
| `docs/operations/RECORDS-VALIDATION-HARNESS-EVIDENCE-2026-07.md` | Create | AC transcripts + red proofs |

---

### Task 1: `_dbtest.py` shared helper (TDD)

**Files:**
- Create: `infra/database/migrations/records/_dbtest.py`
- Test: `infra/database/migrations/records/test__dbtest_helper.py`

**Interfaces:**
- Consumes: nothing (foundation).
- Produces (later tasks rely on these EXACT names):
  `REQUIRED_NETA_FILES: tuple[str, ...]`, `RecordsEnvError(RuntimeError)`,
  `psql_exe() -> str`, `neta_data_dir() -> str`, `neta_json() -> str`,
  `guard_target(dsn: str) -> str`, `dsn() -> str` (pytest module-level skip when unset),
  `require_dsn() -> str` (raises when unset), `dsn_params(dsn: str) -> dict`,
  `run_psql(fname: str, dsn_value: str) -> None`.

- [ ] **Step 1: Write the failing unit tests**

```python
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
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /home/olares/code/apex/apex-records-validation/infra/database/migrations/records
export PATH=$HOME/.local/bin:$PATH
uv run --with 'psycopg[binary]' --with pytest python -m pytest test__dbtest_helper.py -q
```
Expected: FAIL/ERROR with `ModuleNotFoundError: No module named '_dbtest'`.

- [ ] **Step 3: Write `_dbtest.py`**

```python
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
```

- [ ] **Step 4: Run unit tests to verify pass**

Same command as Step 2. Expected: `11 passed`.

- [ ] **Step 5: Commit**

```bash
cd /home/olares/code/apex/apex-records-validation
git add infra/database/migrations/records/_dbtest.py infra/database/migrations/records/test__dbtest_helper.py
git commit -m "feat(records): _dbtest env-contract helper (no-fallback DSN, records_dev guard, NETA validation)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: conftest shim + mechanical rewrite of 38 tests and 5 generators

**Files:**
- Modify: `infra/database/migrations/records/conftest.py` (full rewrite, small)
- Modify (scripted): all `infra/database/migrations/records/test_0NN_*.py` (38) and `gen_020_xfmr_capture_mode.py`, `gen_021_xfmr_pf_readings.py`, `gen_022_it_pf_readings.py`, `gen_039_xfmr_neta_standards.py`, `gen_040_neta_standards_scaleout.py`

**Interfaces:**
- Consumes: `_dbtest.dsn()`, `_dbtest.require_dsn()`, `_dbtest.run_psql(fname, dsn_value)`, `_dbtest.neta_json()`, `_dbtest.neta_data_dir()`, `_dbtest.psql_exe()` (Task 1).
- Produces: every migration test reads `DSN` from `_dbtest.dsn()` and applies SQL via `_dbtest.run_psql` - the runner can redirect them wholesale via `RECORDS_DEV_DSN`.

Verified ground truth this task relies on (2026-07-02): the `PGPW`/`DSN` lines are byte-identical in all 43 files; the `def _psql(fname):` body is byte-identical in all 38 test files; the `PSQL = ...` line is identical in all 38; 15 files have the identical 4-line `JSON = ...` block; test_038 has the 3-line `DATA = ...` block; only test_005 carries a 2-line comment between the PSQL and PGPW lines. The rewrite script asserts every one of these matches per file and exits nonzero on ANY drift (fail-closed).

- [ ] **Step 1: Rewrite conftest.py**

```python
# infra/database/migrations/records/conftest.py
"""Thin pytest shim: env defaults now live in _dbtest.py (the single source).

Kept so standalone per-file pytest runs stay portable on host and laptop; the
validation runner exports fully-resolved values into child environments and
never relies on these setdefaults.
"""
import os

import _dbtest

os.environ.setdefault("PSQL_EXE", _dbtest.psql_exe())
```

Note: NETA defaults are NOT setdefault-ed here anymore - tests call
`_dbtest.neta_json()` / `_dbtest.neta_data_dir()` directly, which validate on
every resolution (a stale env default can no longer bypass validation).

- [ ] **Step 2: Write the rewrite script**

Save on the host as `/tmp/records_rewrite.py` (throwaway; not committed):

```python
"""Mechanical rewrite: route 38 records migration tests + 5 generators through
_dbtest. Exact-match asserted; ANY drift = exit 1 with the offending file."""
import glob
import os
import sys

D = "/home/olares/code/apex/apex-records-validation/infra/database/migrations/records"

PSQL_LINE = 'PSQL = os.environ.get("PSQL_EXE", r"C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe")\n'
T005_COMMENT = (
    # \u2014 renders the em-dash present in the EXISTING file (being deleted here).
    "# Pin the LOCAL password \u2014 do NOT fall through to ambient PGPASSWORD (it points at\n"
    "# Supabase prod in this shell's profile).\n"
)
PGPW_DSN_BLOCK = (
    'PGPW = os.environ.get("RECORDS_DEV_PGPASSWORD") or "TCC_v5_2025"\n'
    'DSN = os.environ.get("RECORDS_DEV_DSN") or (\n'
    '    f"host=127.0.0.1 port=5432 dbname=records_dev user=postgres password={PGPW} sslmode=disable"\n'
    ")\n"
)
OLD_PSQL_FN = (
    "def _psql(fname):\n"
    '    env = {**os.environ, "PGPASSWORD": PGPW, "PGSSLMODE": "disable"}\n'
    "    r = subprocess.run(\n"
    '        [PSQL, "-h", "127.0.0.1", "-p", "5432", "-U", "postgres", "-d", "records_dev",\n'
    '         "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(HERE, fname)],\n'
    "        env=env, capture_output=True, text=True,\n"
    "    )\n"
    "    if r.returncode != 0:\n"
    '        raise RuntimeError(f"psql {fname} failed (rc={r.returncode}):\\n{r.stderr}\\n{r.stdout}")\n'
)
NEW_PSQL_FN = "def _psql(fname):\n    _dbtest.run_psql(fname, DSN)\n"
OLD_JSON_BLOCK = (
    'JSON = os.environ.get("NETA_JSON") or (\n'
    '    r"C:\\Users\\jjswe\\OneDrive\\Documents\\GitHub\\neta-ett-study-material"\n'
    '    r"\\Development\\NETA-Data\\NETA-Master-Equipment-Table-Enhanced.json"\n'
    ")\n"
)
OLD_DATA_BLOCK = (
    'DATA = os.environ.get("NETA_DATA_DIR") or (\n'
    '    r"C:\\Users\\jjswe\\OneDrive\\Documents\\GitHub\\neta-ett-study-material\\Development\\NETA-Data"\n'
    ")\n"
)


def sub1(s, old, new, path, label):
    n = s.count(old)
    if n != 1:
        print(f"FAIL {path} [{label}]: found {n} matches, expected 1")
        sys.exit(1)
    return s.replace(old, new, 1)


def rewrite_test(path):
    s = open(path, encoding="utf-8").read()
    if T005_COMMENT in s:
        s = s.replace(T005_COMMENT, "", 1)
    s = sub1(s, "import pytest\n", "import pytest\n\nimport _dbtest\n", path, "import")
    s = sub1(s, PSQL_LINE, "", path, "psql-line")
    s = sub1(s, PGPW_DSN_BLOCK, "DSN = _dbtest.dsn()\n", path, "pgpw-dsn")
    s = sub1(s, OLD_PSQL_FN, NEW_PSQL_FN, path, "_psql-fn")
    if OLD_JSON_BLOCK in s:
        s = sub1(s, OLD_JSON_BLOCK, "JSON = _dbtest.neta_json()\n", path, "neta-json")
    if OLD_DATA_BLOCK in s:
        s = sub1(s, OLD_DATA_BLOCK, "DATA = _dbtest.neta_data_dir()\n", path, "neta-data")
    open(path, "w", encoding="utf-8", newline="").write(s)


def rewrite_gen(path):
    s = open(path, encoding="utf-8").read()
    s = sub1(s, "import psycopg\n", "import psycopg\n\nimport _dbtest\n", path, "import")
    s = sub1(s, PGPW_DSN_BLOCK, "DSN = _dbtest.require_dsn()\n", path, "pgpw-dsn")
    open(path, "w", encoding="utf-8", newline="").write(s)


tests = sorted(glob.glob(os.path.join(D, "test_0*.py")))
gens = [os.path.join(D, f"gen_{n}") for n in (
    "020_xfmr_capture_mode.py", "021_xfmr_pf_readings.py", "022_it_pf_readings.py",
    "039_xfmr_neta_standards.py", "040_neta_standards_scaleout.py")]
assert len(tests) == 38, f"expected 38 test files, found {len(tests)}"
for t in tests:
    rewrite_test(t)
for g in gens:
    rewrite_gen(g)
json_count = sum("JSON = _dbtest.neta_json()" in open(t, encoding="utf-8").read() for t in tests)
data_count = sum("DATA = _dbtest.neta_data_dir()" in open(t, encoding="utf-8").read() for t in tests)
print(f"rewrote {len(tests)} tests ({json_count} neta_json, {data_count} neta_data_dir) + {len(gens)} generators")
```

Caveats encoded above: (a) `T005_COMMENT` contains the one non-ASCII em-dash
that exists in the CURRENT file - it is being DELETED, so the ASCII-added-lines
rule holds; (b) gen files import psycopg (verified), so the import anchor
differs from tests; (c) if any gen lacks `import psycopg` the script fails
loudly - extend `rewrite_gen`'s anchor for that file, do not weaken the assert.

- [ ] **Step 3: Run the script**

```bash
export PATH=$HOME/.local/bin:$PATH
python3 /tmp/records_rewrite.py
```
Expected: `rewrote 38 tests (15 neta_json, 1 neta_data_dir) + 5 generators`.

- [ ] **Step 4: Verify - compile, greps, and skip behavior**

```bash
cd /home/olares/code/apex/apex-records-validation
python3 -m compileall -q infra/database/migrations/records && echo COMPILE_OK
grep -rn "TCC_v5_2025" infra/database/migrations/records/ ; echo "grep rc=$? (1 = clean)"
grep -c "_dbtest.dsn()" infra/database/migrations/records/test_0*.py | grep -c ":1$"
# skip behavior: unset DSN => whole module skips loudly, never touches a DB
cd infra/database/migrations/records
env -u RECORDS_DEV_DSN uv run --with 'psycopg[binary]' --with pytest \
  python -m pytest test_010_lv_cb_template.py -q 2>&1 | tail -2
```
Expected: COMPILE_OK; the fallback grep prints nothing with rc=1; 38 files with
exactly one `_dbtest.dsn()`; the pytest run reports `1 skipped` (or `skipped`
in the summary line) mentioning `RECORDS_DEV_DSN is not set`.

- [ ] **Step 5: Verify the guard end-to-end (no opt-in => refuse)**

```bash
cd /home/olares/code/apex/apex-records-validation/infra/database/migrations/records
env RECORDS_DEV_DSN="host=127.0.0.1 port=5432 dbname=records_dev user=postgres" \
  uv run --with 'psycopg[binary]' --with pytest python -m pytest test_010_lv_cb_template.py -q 2>&1 | tail -3
```
Expected: collection ERROR containing `refusing to target shared records_dev`.
No connection is attempted (no password was provided - refusal happens first).

- [ ] **Step 6: Commit**

```bash
cd /home/olares/code/apex/apex-records-validation
git add -A infra/database/migrations/records
git commit -m "refactor(records): route 38 migration tests + 5 generators through _dbtest

Mechanical exact-match-asserted rewrite: no credential fallback, DSN-derived
psql invocation (redirectable), validated NETA resolution, records_dev guard.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: records-import DB-test guard

**Files:**
- Create: `packages/records-import/tests/conftest.py`
- Modify: `packages/records-import/tests/test_db_write.py`, `packages/records-import/tests/test_ingest_end_to_end.py`, `packages/records-import/tests/test_ingest_dtax_end_to_end.py`

**Interfaces:**
- Consumes: nothing cross-package (deliberate ~15-line local duplication of the guard semantics - no import across the packages/infra boundary).
- Produces: `require_records_dsn() -> str` in the tests' conftest; the 3 DB test modules define `DSN = require_records_dsn()` at module level.

- [ ] **Step 1: Write conftest.py**

```python
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
```

- [ ] **Step 2: Rewire the 3 DB test modules**

In EACH of the 3 files, replace the module-level block (byte-identical in all 3):

```python
PGPW = os.environ.get("RECORDS_DEV_PGPASSWORD") or "TCC_v5_2025"
DSN = os.environ.get("RECORDS_DEV_DSN") or (
    f"host=127.0.0.1 port=5432 dbname=records_dev user=postgres password={PGPW} sslmode=disable"
)
```

with:

```python
from conftest import require_records_dsn

DSN = require_records_dsn()
```

(`import conftest` resolves because pytest prepends the tests directory to
`sys.path` - the same mechanism the old sibling hack relied on, now used only
within the package's own tests directory.)

- [ ] **Step 3: Verify skip + guard + fallback-grep**

```bash
cd /home/olares/code/apex/apex-records-validation
export PATH=$HOME/.local/bin:$PATH
RUN="uv run --with psycopg[binary] --with pytest --with-editable packages/power-test-converters --with-editable packages/records-import"
env -u RECORDS_DEV_DSN $RUN python -m pytest packages/records-import/tests/test_db_write.py -q 2>&1 | tail -2
env RECORDS_DEV_DSN="host=127.0.0.1 port=5432 dbname=records_dev user=postgres" \
  $RUN python -m pytest packages/records-import/tests/test_db_write.py -q 2>&1 | tail -3
grep -rn "TCC_v5_2025" packages/records-import/ ; echo "grep rc=$? (1 = clean)"
```
Expected: first run `skipped` naming RECORDS_DEV_DSN; second run FAILS/ERRORS
with `refusing to target shared records_dev`; grep clean (rc=1).

- [ ] **Step 4: Verify the pure tests still pass**

```bash
$RUN python -m pytest packages/records-import/tests/test_review_proposal.py \
  packages/records-import/tests/test_ptm_transformer_mapping.py \
  packages/records-import/tests/test_smoke.py -q
```
Expected: `9 passed` (the pure slice count from the 2026-07-02 audit).

- [ ] **Step 5: Commit**

```bash
git add packages/records-import/tests
git commit -m "feat(records-import): DB-test env guard (skip when unset, refuse records_dev)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: promote sample builders + declare the converter dependency (D8)

**Files:**
- Create: `packages/power-test-converters/src/power_test_converters/testing.py`
- Modify: `packages/power-test-converters/tests/test_ptm_to_dtax.py`
- Modify: `packages/records-import/tests/test_ingest_dtax_end_to_end.py`
- Modify: `packages/records-import/pyproject.toml`

**Interfaces:**
- Consumes: the existing private builders in `test_ptm_to_dtax.py`:
  `_write_sample_ptm(tmp_path: Path) -> Path` (line ~313),
  `_write_sample_template(tmp_path: Path) -> Path` (~line 408), and the private
  XML helpers they call: `_transformer_xml`, `_bushing_xml`, `_test_set_info_xml`,
  `_tan_delta_xml`, `_turns_ratio_xml`, `_winding_resistance_xml`,
  `_exciting_current_xml`, `_demagnetization_xml`.
- Produces: `power_test_converters.testing.write_sample_ptm(tmp_path: Path) -> Path`
  and `power_test_converters.testing.write_sample_template(tmp_path: Path) -> Path`.

- [ ] **Step 1: Move the builders into the package**

Create `packages/power-test-converters/src/power_test_converters/testing.py` with
this module docstring, then MOVE (cut, do not copy) the two builder functions and
the eight private XML helper functions from `tests/test_ptm_to_dtax.py` into it,
renaming ONLY the two public entry points (`_write_sample_ptm` ->
`write_sample_ptm`, `_write_sample_template` -> `write_sample_template`; the
private `_xml` helpers keep their names). Bring the imports the moved code needs
(`zipfile`, `pathlib.Path`):

```python
# packages/power-test-converters/src/power_test_converters/testing.py  (header)
"""Sample-fixture builders for tests of this package AND downstream consumers
(records-import). Promoted from tests/test_ptm_to_dtax.py so no consumer needs
a sys.path reach into another package's tests directory."""
import zipfile
from pathlib import Path

# ... moved functions follow, verbatim except the two public renames ...
```

- [ ] **Step 2: Rewire the converter tests**

In `packages/power-test-converters/tests/test_ptm_to_dtax.py`: delete the moved
function bodies; add to the imports:

```python
from power_test_converters.testing import write_sample_ptm, write_sample_template
```

and replace every call-site of `_write_sample_ptm(` with `write_sample_ptm(` and
`_write_sample_template(` with `write_sample_template(` in that file.

- [ ] **Step 3: Rewire records-import's e2e test**

In `packages/records-import/tests/test_ingest_dtax_end_to_end.py`: delete the
sys.path block (the comment line starting `# Reuse the proven sample .ptm
builder`, the `import sys` line, the `_PTC_TESTS` assignment, the
`sys.path.insert(0, str(_PTC_TESTS))` line, and the
`from test_ptm_to_dtax import _write_sample_ptm  # noqa: E402` line). Add to the
normal import block:

```python
from power_test_converters.testing import write_sample_ptm
```

and replace every `_write_sample_ptm(` call with `write_sample_ptm(`.

- [ ] **Step 4: Declare the dependency (D8 - NOT in the pip-visible extra)**

In `packages/records-import/pyproject.toml`, replace the stale comment block above
`dependencies` and append the two new tables:

```toml
# power-test-converters is a sibling monorepo package (unpublished on PyPI - do
# NOT add it to [project.optional-dependencies]: a bare name there would resolve
# against PyPI, a dependency-confusion vector on this public repo). uv resolves
# it via [tool.uv.sources]; pip users install it explicitly first:
#   pip install -e packages/power-test-converters && pip install -e "packages/records-import[test]"
dependencies = ["psycopg[binary]>=3.1"]
```

```toml
[dependency-groups]
dev = ["power-test-converters"]

[tool.uv.sources]
power-test-converters = { path = "../power-test-converters", editable = true }
```

- [ ] **Step 5: Verify both suites + the hack is gone**

```bash
cd /home/olares/code/apex/apex-records-validation
export PATH=$HOME/.local/bin:$PATH
RUN="uv run --with psycopg[binary] --with pytest --with-editable packages/power-test-converters --with-editable packages/records-import"
$RUN python -m pytest packages/power-test-converters/tests -q
grep -n "sys.path" packages/records-import/tests/*.py ; echo "grep rc=$? (1 = clean)"
env -u RECORDS_DEV_DSN $RUN python -m pytest packages/records-import/tests -q 2>&1 | tail -2
```
Expected: converters `11 passed`; sys.path grep clean; records-import run shows
`9 passed` + skips for the DB modules (no errors).

- [ ] **Step 6: Commit**

```bash
git add packages/power-test-converters packages/records-import
git commit -m "feat(converters): promote sample builders to power_test_converters.testing; declare records-import dep (D8)

Kills the cross-package sys.path hack; dependency-groups + uv.sources, never a
bare name in the pip-visible extra (dependency-confusion on a public repo).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: runner pure core (TDD)

**Files:**
- Create: `infra/database/migrations/records/run_validation.py` (pure functions + CLI skeleton this task; DB tiers wired in Task 6)
- Test: `infra/database/migrations/records/test_run_validation_unit.py`

**Interfaces:**
- Consumes: `_dbtest.dsn_params`, `_dbtest.RecordsEnvError`, `_dbtest.REQUIRED_NETA_FILES` (Task 1).
- Produces (Task 6 relies on these EXACT names):
  `enumerate_stack(d: str) -> tuple[list[tuple[int, str]], dict[int, str]]`
  (sorted `(num, sql_filename)` list excluding `_down`, and `num -> test filename` map;
  raises `HarnessError` on numeric gaps or orphan tests),
  `derive_child_dsn(admin_dsn: str, dbname: str) -> str`,
  `check_admin_dsn(admin_dsn: str) -> None` (dbname must equal `postgres`),
  `make_val_name() -> str` (`records_val_<UTCSTAMP>_<PID>`),
  `parse_tiers(only: str) -> set[int]` (REFUSES unknown tiers),
  `assert_val_name(name: str) -> None`,
  `FINGERPRINT_SQL: str`, `HarnessError(RuntimeError)`,
  `class Tier` / `summary(tiers) -> str` (name, status in {PASS, FAIL, SKIP}, detail).

- [ ] **Step 1: Write the failing unit tests**

```python
# infra/database/migrations/records/test_run_validation_unit.py
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
```

- [ ] **Step 2: Run to verify failure**

```bash
cd /home/olares/code/apex/apex-records-validation/infra/database/migrations/records
export PATH=$HOME/.local/bin:$PATH
uv run --with 'psycopg[binary]' --with pytest python -m pytest test_run_validation_unit.py -q
```
Expected: `ModuleNotFoundError: No module named 'run_validation'`.

- [ ] **Step 3: Write the pure core**

```python
# infra/database/migrations/records/run_validation.py
"""The records validation gate. One command, five tiers, honest exit code.

Tiers: 0 syntax+origin, 1 converter tests, 2 records-import pure tests,
3 forward-incremental migration walk on a disposable records_val_* database,
4 records-import DB tests against that migrated database.

DB safety: only ever CREATEs/DROPs the exact records_val_* name generated this
run; the admin DSN must point at the postgres maintenance DB; child processes
receive an explicit environment (no ambient DSN is ever consulted by a tier).

See docs/superpowers/specs/2026-07-02-records-validation-harness-design.md.
"""
import argparse
import collections
import datetime
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)

import _dbtest  # noqa: E402


class HarnessError(RuntimeError):
    """A harness-contract violation (preflight, naming, sequencing)."""


Tier = collections.namedtuple("Tier", "name status detail")

MIG_RE = re.compile(r"^(\d{3})_.+\.sql$")
TEST_RE = re.compile(r"^test_(\d{3})_.+\.py$")
VAL_RE = re.compile(r"^records_val_\d{8}T\d{6}_\d+$")

# Schema-only catalog fingerprint of the records schema: tables, columns,
# constraints, indexes, functions, triggers, enums. Data-only changes (the 006/
# 009 seeds that tests 005/008 apply beyond their own number) do NOT move it.
FINGERPRINT_SQL = """
select md5(coalesce(string_agg(x, '|' order by x), 'empty')) from (
  select 'tbl:' || c.relkind || ':' || n.nspname || '.' || c.relname as x
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'records'
  union all
  select 'col:' || table_name || '.' || column_name || ':' || data_type || ':'
         || coalesce(column_default, '') || ':' || is_nullable
    from information_schema.columns where table_schema = 'records'
  union all
  select 'con:' || conrelid::regclass::text || ':' || conname || ':' || pg_get_constraintdef(oid)
    from pg_constraint
   where connamespace = (select oid from pg_namespace where nspname = 'records')
  union all
  select 'idx:' || schemaname || '.' || indexname || ':' || indexdef
    from pg_indexes where schemaname = 'records'
  union all
  select 'fn:' || p.proname || ':' || md5(pg_get_functiondef(p.oid))
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
   where n.nspname = 'records'
  union all
  select 'trg:' || t.tgrelid::regclass::text || ':' || t.tgname || ':' || pg_get_triggerdef(t.oid)
    from pg_trigger t
   where not t.tgisinternal
     and t.tgrelid in (select c.oid from pg_class c join pg_namespace n
                        on n.oid = c.relnamespace where n.nspname = 'records')
  union all
  select 'enum:' || ty.typname || ':' || e.enumlabel || ':' || e.enumsortorder
    from pg_type ty join pg_enum e on e.enumtypid = ty.oid
    join pg_namespace n on n.oid = ty.typnamespace
   where n.nspname = 'records'
) s
"""


def enumerate_stack(d):
    """Completeness preflight: sorted migrations + num->test map, fail-closed.

    FAILs on any gap in the numeric sequence (a withheld/deleted migration) and
    on any orphan test (a test_NNN with no NNN migration - rename drift would
    otherwise silently stop that test from ever running)."""
    migs, tests = [], {}
    for f in sorted(os.listdir(d)):
        if f.endswith("_down.sql"):
            continue
        m = MIG_RE.match(f)
        if m:
            migs.append((int(m.group(1)), f))
        t = TEST_RE.match(f)
        if t:
            tests[int(t.group(1))] = f
    if not migs:
        raise HarnessError(f"no migrations found in {d}")
    nums = [n for n, _ in migs]
    dupes = [n for n, c in collections.Counter(nums).items() if c > 1]
    if dupes:
        raise HarnessError(f"duplicate migration numbers: {dupes}")
    expected = list(range(nums[0], nums[-1] + 1))
    if nums != expected:
        missing = sorted(set(expected) - set(nums))
        raise HarnessError(f"migration sequence gap: missing {missing}")
    orphans = sorted(set(tests) - set(nums))
    if orphans:
        raise HarnessError(f"orphan test file(s) with no matching migration: {orphans}")
    return migs, tests


def derive_child_dsn(admin_dsn, dbname):
    if "dbname=" not in admin_dsn:
        raise HarnessError("admin DSN has no dbname= component")
    return re.sub(r"dbname=[^\s]+", f"dbname={dbname}", admin_dsn)


def check_admin_dsn(admin_dsn):
    db = _dbtest.dsn_params(admin_dsn).get("dbname")
    if db != "postgres":
        raise HarnessError(
            f"RECORDS_PG_ADMIN_DSN must point at the postgres maintenance DB, got dbname={db!r}"
        )


def make_val_name():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"records_val_{stamp}_{os.getpid()}"


def assert_val_name(name):
    if not VAL_RE.fullmatch(name):
        raise HarnessError(f"refusing CREATE/DROP: {name!r} is not a run-generated records_val_* name")


def parse_tiers(only):
    """Validate --only. Unknown tiers must REFUSE - a typo like --only 9
    running zero tiers and exiting 0 would be a false-green gate."""
    if not only:
        return {0, 1, 2, 3, 4}
    try:
        wanted = {int(x) for x in only.split(",") if x.strip()}
    except ValueError:
        raise HarnessError(f"--only takes a comma list of tiers 0-4, got {only!r}")
    unknown = wanted - {0, 1, 2, 3, 4}
    if not wanted or unknown:
        raise HarnessError(f"unknown tier(s) in --only: {sorted(unknown)} (valid: 0-4)")
    return wanted


def summary(tiers):
    lines = ["", "=== records validation summary ==="]
    for t in tiers:
        lines.append(f"  {t.name:<16} {t.status:<5} {t.detail}")
    return "\n".join(lines)


def main(argv=None):  # wired fully in the next task
    raise SystemExit("run_validation: tiers are wired in Task 6")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run unit tests to verify pass**

Same command as Step 2. Expected: `9 passed`.

- [ ] **Step 5: Commit**

```bash
cd /home/olares/code/apex/apex-records-validation
git add infra/database/migrations/records/run_validation.py infra/database/migrations/records/test_run_validation_unit.py
git commit -m "feat(records): run_validation pure core (completeness preflight, DSN derivation, val-name allowlist, fingerprint SQL)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: runner tiers + first full green run (AC1)

**Files:**
- Modify: `infra/database/migrations/records/run_validation.py` (replace the `main` stub; add tier functions)

**Interfaces:**
- Consumes: everything Task 5 produced; `_dbtest.run_psql`, `_dbtest.neta_data_dir`, `_dbtest.neta_json`, `_dbtest.psql_exe`, `_dbtest.dsn_params` (Task 1); the rewritten tests (Task 2); the guarded records-import DB tests (Task 3); `power_test_converters` importability (Task 4).
- Produces: the runner CLI: `python run_validation.py [--require-db] [--only TIERS] [--db-dsn DSN] [--keep-db]`. Exit 0 = all run tiers PASS (SKIPs allowed only without `--require-db`); nonzero otherwise.

- [ ] **Step 1: Replace the `main` stub with the tier engine**

Replace `def main(argv=None): ...` (and keep everything above it) with:

```python
def _run(cmd, env=None, cwd=None):
    """Run a child, stream nothing, return (rc, tail). Exit code is checked
    directly by callers - never piped through anything that could mask it."""
    r = subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True)
    tail = "\n".join((r.stdout + "\n" + r.stderr).strip().splitlines()[-12:])
    return r.returncode, tail


def _pytest(paths, env, label):
    rc, tail = _run([sys.executable, "-m", "pytest", "-q", *paths], env=env, cwd=REPO_ROOT)
    print(f"--- {label} (rc={rc}) ---\n{tail}")
    return rc


def _connect(dsn_value):
    import psycopg

    print(f"[connect] dbname={_dbtest.dsn_params(dsn_value).get('dbname')}")
    return psycopg.connect(dsn_value, autocommit=True)


def _fingerprint(dsn_value):
    with _connect(dsn_value) as c:
        return c.execute(FINGERPRINT_SQL).fetchone()[0]


def tier0_syntax_origin():
    rc, tail = _run([sys.executable, "-m", "compileall", "-q",
                     os.path.join(REPO_ROOT, "packages", "power-test-converters"),
                     os.path.join(REPO_ROOT, "packages", "records-import"), HERE])
    if rc != 0:
        return Tier("0-syntax", "FAIL", tail)
    for name in ("power_test_converters", "records_import"):
        code = (f"import os,{name};p=os.path.abspath({name}.__file__);"
                f"raise SystemExit(0 if p.startswith({REPO_ROOT!r}) else 'ORIGIN:'+p)")
        rc, tail = _run([sys.executable, "-c", code])
        if rc != 0:
            return Tier("0-syntax", "FAIL",
                        f"{name} does not resolve inside this repo (dependency-confusion tripwire): {tail}")
    return Tier("0-syntax", "PASS", "compileall + origin asserts")


def tier1_converters(env):
    rc = _pytest([os.path.join("packages", "power-test-converters", "tests")], env, "tier1")
    return Tier("1-converters", "PASS" if rc == 0 else "FAIL", f"pytest rc={rc}")


PURE_IMPORT_TESTS = ["test_review_proposal.py", "test_ptm_transformer_mapping.py", "test_smoke.py"]
DB_IMPORT_TESTS = ["test_db_write.py", "test_ingest_end_to_end.py", "test_ingest_dtax_end_to_end.py"]


def tier2_import_pure(env):
    paths = [os.path.join("packages", "records-import", "tests", f) for f in PURE_IMPORT_TESTS]
    rc = _pytest(paths, env, "tier2")
    return Tier("2-import-pure", "PASS" if rc == 0 else "FAIL", f"pytest rc={rc}")


def _child_env(child_dsn):
    env = dict(os.environ)
    env["RECORDS_DEV_DSN"] = child_dsn
    pw = _dbtest.dsn_params(child_dsn).get("password")
    if pw:
        env["RECORDS_DEV_PGPASSWORD"] = pw
    env["NETA_DATA_DIR"] = _dbtest.neta_data_dir()
    env["NETA_JSON"] = _dbtest.neta_json()
    env["PSQL_EXE"] = _dbtest.psql_exe()
    env.pop("RECORDS_ALLOW_SHARED_DB", None)
    return env


def tier3_walk(child_dsn, executed, migs, tests):
    env = _child_env(child_dsn)
    for num, sql in migs:
        _dbtest.run_psql(sql, child_dsn)
        tf = tests.get(num)
        if not tf:
            continue
        pre = _fingerprint(child_dsn)
        rc = _pytest([os.path.join("infra", "database", "migrations", "records", tf)], env, tf)
        if rc != 0:
            return Tier("3-migrations", "FAIL", f"{tf} failed (rc={rc}); walk stopped")
        post = _fingerprint(child_dsn)
        if pre != post:
            return Tier("3-migrations", "FAIL",
                        f"{tf} PASSED but did not restore its migration (schema fingerprint moved)")
        executed.append(tf)
    return Tier("3-migrations", "PASS", f"{len(migs)} applied, {len(executed)} tests executed, 0 skipped")


def tier4_import_db(child_dsn, executed):
    env = _child_env(child_dsn)
    paths = [os.path.join("packages", "records-import", "tests", f) for f in DB_IMPORT_TESTS]
    rc = _pytest(paths, env, "tier4")
    if rc == 0:
        executed.extend(DB_IMPORT_TESTS)
    return Tier("4-import-db", "PASS" if rc == 0 else "FAIL",
                f"{len(DB_IMPORT_TESTS)} DB test files, pytest rc={rc}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="records validation gate")
    ap.add_argument("--require-db", action="store_true",
                    help="CI mode: any absence/skip on DB or source inputs is a failure")
    ap.add_argument("--only", default="", help="comma list of tiers to run, e.g. 3,4")
    ap.add_argument("--db-dsn", default="", help="explicit records_val_* DSN (required with --only 3/4)")
    ap.add_argument("--keep-db", action="store_true", help="skip the drop; print the retained name")
    args = ap.parse_args(argv)

    try:
        wanted = parse_tiers(args.only)
    except HarnessError as e:
        print(f"error: {e}")
        return 2
    tiers, executed = [], []
    admin = os.environ.get("RECORDS_PG_ADMIN_DSN", "")
    child_dsn, val_name, created = "", "", False

    if args.db_dsn:
        name = _dbtest.dsn_params(args.db_dsn).get("dbname", "")
        assert_val_name(name)
        child_dsn = args.db_dsn

    if 0 in wanted:
        tiers.append(tier0_syntax_origin())
    if 1 in wanted:
        tiers.append(tier1_converters(dict(os.environ)))
    if 2 in wanted:
        tiers.append(tier2_import_pure(dict(os.environ)))

    db_wanted = wanted & {3, 4}
    if db_wanted and not any(t.status == "FAIL" for t in tiers):
        try:
            # Source + completeness preflights run BEFORE any skip decision
            # and BEFORE any CREATE (spec sec 3; red proof 1 depends on it).
            migs, tests = None, None
            if 3 in wanted:
                _dbtest.neta_data_dir()
                _dbtest.neta_json()
                migs, tests = enumerate_stack(HERE)
            if not child_dsn:
                if wanted != {0, 1, 2, 3, 4}:
                    raise HarnessError("--only with DB tiers requires --db-dsn (records_val_* only)")
                if not admin:
                    detail = "RECORDS_PG_ADMIN_DSN is not set"
                    status = "FAIL" if args.require_db else "SKIP"
                    for n in sorted(db_wanted):
                        tiers.append(Tier(f"{n}-db", status, detail))
                    db_wanted = set()
                else:
                    check_admin_dsn(admin)
                    val_name = make_val_name()
                    assert_val_name(val_name)
                    with _connect(admin) as c:
                        exists = c.execute(
                            "select 1 from pg_database where datname = %s", (val_name,)
                        ).fetchone()
                        if exists:
                            raise HarnessError(f"disposable name already exists: {val_name}")
                        c.execute(f'create database "{val_name}"')
                    created = True
                    child_dsn = derive_child_dsn(admin, val_name)
            try:
                if 3 in db_wanted:
                    tiers.append(tier3_walk(child_dsn, executed, migs, tests))
                if 4 in db_wanted and not any(
                    t.name == "3-migrations" and t.status == "FAIL" for t in tiers
                ):
                    if 3 in db_wanted or args.db_dsn:
                        tiers.append(tier4_import_db(child_dsn, executed))
                    else:
                        tiers.append(Tier("4-import-db", "SKIP", "no migrated target (run tier 3 or pass --db-dsn)"))
                elif 4 in db_wanted:
                    tiers.append(Tier("4-import-db", "SKIP", "tier 3 failed"))
            finally:
                if created:
                    if args.keep_db:
                        print(f"[keep-db] retained database: {val_name} (drop it manually)")
                    else:
                        assert_val_name(val_name)
                        with _connect(admin) as c:
                            c.execute(f'drop database if exists "{val_name}" with (force)')
                        print(f"[drop] {val_name}")
        except (HarnessError, _dbtest.RecordsEnvError) as e:
            tiers.append(Tier("3-migrations" if 3 in wanted else "4-import-db", "FAIL", str(e)))
    elif db_wanted:
        for n in sorted(db_wanted):
            tiers.append(Tier(f"{n}-db", "SKIP", "earlier tier failed"))

    print(summary(tiers))
    print(f"executed test files: {len(executed)}")
    failed = any(t.status == "FAIL" for t in tiers)
    skipped = any(t.status == "SKIP" for t in tiers)
    if failed or (args.require_db and skipped):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Re-run the unit tests (still pass)**

```bash
cd /home/olares/code/apex/apex-records-validation/infra/database/migrations/records
export PATH=$HOME/.local/bin:$PATH
uv run --with 'psycopg[binary]' --with pytest python -m pytest test_run_validation_unit.py test__dbtest_helper.py -q
```
Expected: `20 passed`.

- [ ] **Step 3: Compose the admin DSN (values stay in the shell, never in output)**

```bash
cd /home/olares/code/apex/apex-records-validation
set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a
export RECORDS_PG_ADMIN_DSN="host=127.0.0.1 port=5432 dbname=postgres user=postgres password=${DEV_PG_PASSWORD} sslmode=disable"
```
(`DEV_PG_PASSWORD` is the apex-dev-pg maintenance credential already provisioned
in the canonical worktree's `infra/.env`. NEVER echo it.)

- [ ] **Step 4: Full run - first AC1 attempt**

```bash
export PATH=$HOME/.local/bin:$PATH
uv run --with 'psycopg[binary]' --with pytest \
  --with-editable packages/power-test-converters --with-editable packages/records-import \
  python infra/database/migrations/records/run_validation.py ; echo "runner rc=$?"
```
Expected: summary shows tiers 0-4 all `PASS`; `[connect]` lines show ONLY
`dbname=postgres` and `dbname=records_val_...`; final line `runner rc=0`.
Tier 3 detail reads `44 applied, 38 tests executed, 0 skipped`.

If any migration test fails here, STOP and diagnose (systematic debugging - the
tests all passed per-chip historically; a failure is most likely an env-contract
regression from Task 2, not a records bug). Do not weaken any assert to get to
green.

- [ ] **Step 5: Capture the transcript for evidence**

```bash
mkdir -p /tmp/rvh-evidence
uv run --with 'psycopg[binary]' --with pytest \
  --with-editable packages/power-test-converters --with-editable packages/records-import \
  python infra/database/migrations/records/run_validation.py > /tmp/rvh-evidence/ac1-full-run.txt 2>&1
echo "runner rc=$?" >> /tmp/rvh-evidence/ac1-full-run.txt
grep -c "dbname=records_dev" /tmp/rvh-evidence/ac1-full-run.txt ; echo "(expect 0)"
```
(The redirect here captures a SECOND run for the record; the rc is appended from
the shell variable, not piped - the gate itself was checked unmasked in Step 4.)

- [ ] **Step 6: Commit**

```bash
git add infra/database/migrations/records/run_validation.py
git commit -m "feat(records): run_validation tier engine - forward-incremental disposable-DB walk, restoration assert, AC1 green

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: red proofs (AC3) + evidence document

**Files:**
- Create: `docs/operations/RECORDS-VALIDATION-HARNESS-EVIDENCE-2026-07.md`

**Interfaces:**
- Consumes: the working runner (Task 6).
- Produces: the evidence doc later tasks append to.

- [ ] **Step 1: Red proof 1 - withheld migration (scratch copy, repo untouched)**

```bash
cp -a /home/olares/code/apex/apex-records-validation /tmp/rvh-redproof
rm /tmp/rvh-redproof/infra/database/migrations/records/031_cap_bank_template.sql
cd /tmp/rvh-redproof
export PATH=$HOME/.local/bin:$PATH
set -a; . /home/olares/code/apex/apex-power-ops-platform/infra/.env; set +a
export RECORDS_PG_ADMIN_DSN="host=127.0.0.1 port=5432 dbname=postgres user=postgres password=${DEV_PG_PASSWORD} sslmode=disable"
uv run --with 'psycopg[binary]' --with pytest \
  --with-editable packages/power-test-converters --with-editable packages/records-import \
  python infra/database/migrations/records/run_validation.py > /tmp/rvh-evidence/redproof1.txt 2>&1
echo "rc=$?" >> /tmp/rvh-evidence/redproof1.txt
grep -E "gap|missing \[31\]|rc=" /tmp/rvh-evidence/redproof1.txt
```
Expected: Tier 3 FAIL naming `migration sequence gap: missing [31]`; `rc=1`; no
`records_val_` database was created (the preflight fires before CREATE - verify
with `docker exec apex-dev-pg psql -U postgres -lqt | grep records_val` on the
canonical host: empty).

- [ ] **Step 2: Red proof 2 - missing source data under --require-db**

```bash
cd /home/olares/code/apex/apex-records-validation
env NETA_DATA_DIR=/nonexistent-neta uv run --with 'psycopg[binary]' --with pytest \
  --with-editable packages/power-test-converters --with-editable packages/records-import \
  python infra/database/migrations/records/run_validation.py --require-db > /tmp/rvh-evidence/redproof2.txt 2>&1
echo "rc=$?" >> /tmp/rvh-evidence/redproof2.txt
grep -E "NETA_DATA_DIR|rc=" /tmp/rvh-evidence/redproof2.txt
```
Expected: Tier 3 FAIL naming `NETA_DATA_DIR is not a directory: /nonexistent-neta`;
`rc=1`.

- [ ] **Step 3: Clean up the scratch copy**

```bash
rm -rf /tmp/rvh-redproof
```

- [ ] **Step 4: Write the evidence doc**

Create `docs/operations/RECORDS-VALIDATION-HARNESS-EVIDENCE-2026-07.md` with this
skeleton, pasting the three captured transcripts verbatim into the fenced blocks
(they contain no secrets - verify with `grep -i password` first: zero hits):

```markdown
# Records Validation Harness - Evidence Record (2026-07)

Lane: records/validation-harness. Spec: docs/superpowers/specs/2026-07-02-records-validation-harness-design.md (rev 3).

## AC1 - full host run (disposable DB only)

<paste /tmp/rvh-evidence/ac1-full-run.txt; note the [connect] dbname lines show
only postgres + records_val_*>

## AC3 red proof 1 - withheld migration fails the completeness preflight

<paste /tmp/rvh-evidence/redproof1.txt>

## AC3 red proof 2 - missing NETA_DATA_DIR fails loudly under --require-db

<paste /tmp/rvh-evidence/redproof2.txt>

## AC2 - CI run

<appended in the CI task: link to the green Actions run + the executed-counts lines>

## AC4 - fallback removal grep

<appended in the docs task>
```

- [ ] **Step 5: Commit**

```bash
git add docs/operations/RECORDS-VALIDATION-HARNESS-EVIDENCE-2026-07.md
git commit -m "docs(records): harness evidence record - AC1 transcript + both red proofs (AC3)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: records-ci.yml + operator secret checkpoint + CI green (AC2)

**Files:**
- Create: `.github/workflows/records-ci.yml`
- Modify: `docs/operations/RECORDS-VALIDATION-HARNESS-EVIDENCE-2026-07.md` (AC2 section)

**Interfaces:**
- Consumes: the runner CLI (Task 6); the dependency install contract (Task 4).
- Produces: the CI gate.

- [ ] **Step 1: Resolve the source-repo pin**

```bash
export PATH=/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH
gh api repos/APEX-Power-Ops/neta-ett-study-material/commits/HEAD -q .sha
```
Use the printed 40-char SHA as `<NETA_PIN_SHA>` in Step 2.

- [ ] **Step 2: Write the workflow**

```yaml
# .github/workflows/records-ci.yml
name: Records CI

on:
  push:
    paths:
      - packages/power-test-converters/**
      - packages/records-import/**
      - infra/database/migrations/records/**
      - .github/workflows/records-ci.yml
  pull_request:
    paths:
      - packages/power-test-converters/**
      - packages/records-import/**
      - infra/database/migrations/records/**
      - .github/workflows/records-ci.yml

jobs:
  validate:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env:
          # Throwaway literal: job-scoped container, unreachable from outside
          # the runner, holds only disposable validation data.
          POSTGRES_PASSWORD: records_ci_throwaway
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10
    env:
      RECORDS_PG_ADMIN_DSN: host=127.0.0.1 port=5432 dbname=postgres user=postgres password=records_ci_throwaway sslmode=disable
      NETA_DATA_DIR: ${{ github.workspace }}/neta-source/Development/NETA-Data
    steps:
      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4.3.1
      - name: Checkout NETA source extracts (private repo, read-only token)
        uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4.3.1
        with:
          repository: APEX-Power-Ops/neta-ett-study-material
          ref: <NETA_PIN_SHA>
          token: ${{ secrets.NETA_SOURCE_REPO_TOKEN }}
          path: neta-source
      - name: Verify required extract files by name (never content)
        run: |
          for f in NETA-Master-Equipment-Table-Enhanced.json NETA-ATS-2025-tables-extracted.json NETA-MTS-2023-tables-extracted.json; do
            test -f "$NETA_DATA_DIR/$f" && echo "present: $f" || { echo "MISSING: $f"; exit 1; }
          done
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0
        with:
          python-version: '3.11'
      - name: Install packages (ordered - see records-import pyproject comment)
        run: |
          python -m pip install --upgrade pip
          pip install -e packages/power-test-converters
          pip install -e "packages/records-import[test]"
      - name: Run the records validation gate
        run: python infra/database/migrations/records/run_validation.py --require-db
```

- [ ] **Step 3: OPERATOR CHECKPOINT (blocking)**

The workflow needs the repo secret `NETA_SOURCE_REPO_TOKEN` on
`APEX-Power-Ops/apex-power-ops-platform`: a fine-grained PAT, resource owner
`APEX-Power-Ops`, repository access ONLY `neta-ett-study-material`, permission
Contents: Read-only, expiry per operator policy (no-expiry or calendared). The
operator creates and installs it out-of-band; report BLOCKED and wait if it is
not in place. Verify presence WITHOUT reading it:

```bash
gh api repos/APEX-Power-Ops/apex-power-ops-platform/actions/secrets -q '.secrets[].name'
```
Expected: list contains `NETA_SOURCE_REPO_TOKEN`.

- [ ] **Step 4: Push and verify CI green**

```bash
cd /home/olares/code/apex/apex-records-validation
git add .github/workflows/records-ci.yml
git commit -m "ci(records): records validation gate - postgres:17 service + SHA-pinned private NETA source checkout

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git push -u origin records/validation-harness
gh run watch $(gh run list --workflow records-ci.yml --branch records/validation-harness -L 1 --json databaseId -q '.[0].databaseId') --exit-status
```
Expected: run concludes `success`. Pull the executed-count lines for evidence:

```bash
gh run view --log $(gh run list --workflow records-ci.yml --branch records/validation-harness -L 1 --json databaseId -q '.[0].databaseId') | grep -E "applied, .* tests executed|executed test files|present: NETA" > /tmp/rvh-evidence/ac2-ci.txt
cat /tmp/rvh-evidence/ac2-ci.txt
```
Expected lines include `44 applied, 38 tests executed, 0 skipped`,
`executed test files: 41`, and the three `present:` lines.

- [ ] **Step 5: Append AC2 to the evidence doc and commit**

Paste `/tmp/rvh-evidence/ac2-ci.txt` plus the Actions run URL into the evidence
doc's AC2 section.

```bash
git add docs/operations/RECORDS-VALIDATION-HARNESS-EVIDENCE-2026-07.md
git commit -m "docs(records): AC2 CI evidence - source-backed tests executed on ephemeral infra

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git push
```

---

### Task 9: docs, final sweeps, PR

**Files:**
- Modify: `infra/database/migrations/records/MANIFEST.md`, `reference/records/CURRENT-STATE.md`, `.env.dev.template`, `docs/lanes/README.md`, evidence doc (AC4)

- [ ] **Step 1: MANIFEST "Validation" section**

Insert directly ABOVE the existing per-chip warning block (`> **Run the records
tests per-chip...`):

```markdown
## Validation

The records gate is `run_validation.py` in this directory - the PRIMARY way to
validate this stack. It builds a disposable `records_val_*` database (never
shared `records_dev`), applies 001-044 forward-incrementally, runs each
migration test at the exact stack state it was developed for, verifies each
test restored its migration (schema fingerprint), then runs the records-import
DB tests against the migrated result. Env contract: `RECORDS_PG_ADMIN_DSN`
(maintenance DB `postgres`), NETA extracts resolved and validated via
`_dbtest.py` (`REQUIRED_NETA_FILES`). See `.env.dev.template` and
`docs/superpowers/specs/2026-07-02-records-validation-harness-design.md`.
CI: `.github/workflows/records-ci.yml`.

The per-chip guidance below remains for LEGACY manual runs only; targeting
`records_dev` now requires the explicit `RECORDS_ALLOW_SHARED_DB=1` opt-in.
```

- [ ] **Step 2: `.env.dev.template` additions**

Append:

```bash
# --- records validation harness (Gate 2) ---
# Maintenance DSN the validation runner uses to CREATE/DROP disposable
# records_val_* databases. dbname MUST be postgres. No fallback exists.
RECORDS_PG_ADMIN_DSN=host=127.0.0.1 port=5432 dbname=postgres user=postgres password=<from-vault> sslmode=disable
# DSN of the records database under test for STANDALONE per-file pytest runs
# (the runner sets this itself; targeting records_dev additionally requires
# RECORDS_ALLOW_SHARED_DB=1).
RECORDS_DEV_DSN=
RECORDS_DEV_PGPASSWORD=
# NETA extracts directory (validated against REQUIRED_NETA_FILES in _dbtest.py).
NETA_DATA_DIR=
```

- [ ] **Step 3: CURRENT-STATE.md + lanes README status lines**

In `reference/records/CURRENT-STATE.md` "## Next Gates": change line
`2. Validation Harness - ...` to append ` **DONE 2026-07 (this lane): runner +
CI live; see infra/database/migrations/records/run_validation.py and the
evidence record in docs/operations/.**` and check off minimum-resume-checklist
items 3 and 4 (append `(DONE 2026-07)` to each). In `docs/lanes/README.md`
records section, update the Status line to append: `Validation harness (Gate 2)
landed 2026-07: run_validation.py + records-ci.yml; next = security/RLS (Gate 3).`

- [ ] **Step 4: AC4/AC5 final sweeps + ASCII audit**

```bash
cd /home/olares/code/apex/apex-records-validation
grep -rn "TCC_v5_2025" infra/database/migrations/records/ packages/records-import/ ; echo "AC4 rc=$? (1 = clean)"
grep -rn "sys.path" packages/records-import/tests/ ; echo "AC5 rc=$? (1 = clean)"
git diff origin/main...HEAD --unified=0 | grep "^+" | python3 -c "
import sys
bad = [l for l in sys.stdin if any(ord(c) > 127 for c in l)]
print('ASCII:', 'CLEAN' if not bad else bad[:5])"
git diff --check origin/main...HEAD && echo WHITESPACE_OK
```
Append the AC4 grep transcript to the evidence doc.

- [ ] **Step 5: Commit + open the PR (operator-gated merge)**

```bash
git add -A
git commit -m "docs(records): validation section in MANIFEST, env template, gate-2 status; AC4 evidence

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
git push
cat > /tmp/pr-body.md <<'EOF'
Gate 2 of the records lane (operator-ratified 2026-07-02). Spec:
docs/superpowers/specs/2026-07-02-records-validation-harness-design.md (rev 3).

- run_validation.py: 5 tiers, forward-incremental disposable-DB migration walk
  (completeness preflight, restoration assert, stop-on-first-failure,
  records_val_* CREATE/DROP allowlist)
- _dbtest.py env contract: zero hardcoded credential fallbacks (47 refs removed),
  records_dev refusal guard on BOTH test families, validated NETA resolution
  (REQUIRED_NETA_FILES by name)
- power_test_converters.testing promotion + D8 dependency declaration
  (dependency-groups + uv.sources; nothing pip-resolvable from PyPI)
- records-ci.yml: postgres:17 service + SHA-pinned private neta-ett-study-material
  checkout - source-backed tests EXECUTE in CI (never skip)
- Evidence: docs/operations/RECORDS-VALIDATION-HARNESS-EVIDENCE-2026-07.md
  (AC1 transcript, both red proofs, AC2 CI counts, AC4 greps)

Post-merge closeout (operator-only, out-of-band): rotate the burned
Windows-local PG18 password (AC7).

Do not merge without operator ratification.
EOF
# Footer emoji emitted at runtime so this plan file stays ASCII-only:
printf '\n\U0001F916 Generated with [Claude Code](https://claude.com/claude-code)\n' >> /tmp/pr-body.md
gh pr create --title "records: validation harness (Gate 2) - tiered runner, env contract, disposable-DB migration walk, CI" --body-file /tmp/pr-body.md
```

- [ ] **Step 6: Report** - final whole-branch review + the lane's mandatory
cross-engine IRP run before the operator merge decision (controller-level, not
a subagent task).

---

## Plan Self-Review (done at authoring)

- Spec coverage: sec 3 -> Tasks 1/2/3/6; 4.1 -> Task 1/2; 4.2 -> Task 3; 4.3 ->
  Tasks 5/6; 4.4 -> Task 4; 4.5 -> Task 4; 4.6 -> Task 8; 4.7 -> Tasks 2/3 +
  AC4 sweep; 4.8 -> Task 9; sec 5 -> Task 7; AC1-AC6 -> Tasks 6-9. AC7
  (rotation) is deliberately NOT a plan task: operator-only, post-merge.
- The `031_cap_bank_template.sql` file named in red proof 1 exists (verified in
  the 2026-07-02 stack survey); any other non-seed migration works identically.
- Type consistency: `_dbtest` API names match across Tasks 1/2/5/6; `Tier`,
  `enumerate_stack`, `derive_child_dsn`, `make_val_name`, `assert_val_name`
  match between Tasks 5 and 6; `write_sample_ptm` matches Tasks 4's producer
  and consumer edits.
- Executed-count expectations: Tier 3 = 38 test files; Tier 4 = 3; total 41
  (`executed test files: 41`).
