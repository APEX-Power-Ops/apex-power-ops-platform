# Access Fidelity Harness - Governed Materialization + Per-Table Checksum Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the harness produce a durable, provenance-stamped `access_raw` mirror of the breaker/TMT slice (incl. the 3 style parents with all D4/D5 columns) in a dedicated governed DB, with a recorded, access-vs-staging-validated per-table checksum, so the next slice can generate the 029/030 population SQL FROM governed `access_raw` with a complete provenance header.

**Architecture:** Three additive changes to the existing harness (no schema migration - all target columns/tables already exist in `sql/001_schemas.sql`): (1) a `--governed` CLI route that derives + fences a dedicated `tcc_fidelity_governed` DB; (2) a `validate.reconcile_checksums()` step wired into the load pipeline that computes + records per-table checksums and the access-vs-staging reconciliation; (3) `key_quality` coverage for the 3 style parents. The loader itself is unchanged (it already carries the style parents full-width).

**Tech Stack:** Python 3 (uv project), psycopg v3, pyodbc + pywin32 (Windows-only Access path), pytest. Built + run on THIS Windows machine (`C:\dev\apex-access-harness`); the `.accdb` and local PG18 are here.

## Global Constraints

- ASCII-only in ALL user-facing copy and code comments (no smart quotes, no em-dashes - use `--`).
- Merge to main is OPERATOR-GATED; no prod writes; no promotion without an explicit go.
- The `--governed` path MUST fail closed: assert `current_database() = 'tcc_fidelity_governed'` before ANY destructive schema/table action.
- Tests MUST prove `--governed` refuses `postgres`, `tcc_fidelity_test`, and arbitrary DB names.
- The normal test suite NEVER touches `tcc_fidelity_governed`; only explicit operator-run `--governed` / `provision-governed` commands do. TDD targets `tcc_fidelity_test` (the `pg` fixture).
- Governed DB name is exactly `tcc_fidelity_governed`.
- Access is read ONLY (read-only pyodbc against the frozen copy). Never echo secrets / DSNs / passwords.
- No new third-party dependencies.
- Every new validation value is STRUCTURAL (a sha256 hash, a boolean `matches`, counts, a key-uniqueness boolean) - HR1: no interpretation, no verdict columns.
- Commit identity `jasonlswenson-sys <jasonlswenson@gmail.com>`; every commit ends with the trailer `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- Single writer = the Windows worktree `C:\dev\apex-access-harness`; push to origin from here only.
- Run tests with `uv run pytest` from `infra/database/access-harness/`.

## Operator audit conditions (binding acceptance criteria)

Folded from the operator spec-review; carry into every task brief AND the per-task reviews:

- **AC-1 (Task 1): the `ensure_database` create/drop test is cluster-mutating -- gate it.** It must be opt-in (skipped unless `ACCESS_HARNESS_ALLOW_DB_CREATE=1`) so a default `uv run pytest` never mutates the cluster, and must NEVER target `tcc_fidelity_governed`.
- **AC-2 (Task 1): prove wrong-DB refusal for EVERY governed command path.** `load`, `inventory`, AND `run-all` must fence BOTH the autocommit/admin connection AND the transaction connection BEFORE any write (`record_extraction_run`, `load_table`, inventory). A parametrized integration test proves each command raises the fence error (never reaching load/record) when `--governed` resolves to a non-governed DB. Most important safety invariant.
- **AC-3 (Task 2): checksum type round-trip via real Postgres readback.** Beyond pure-checksum tests, a test loads diverse-typed rows into a real `access_raw` table (integer, double precision, numeric/decimal, date, timestamp, boolean, bytea, text, NULLs), reconciles, and proves access-side == staging-side canonicalization (`matches=True`). AND a style-parent checksum mismatch FAILS CLOSED (raises), not quietly recorded: the pipeline RECORDS the reconciliation (HR1 evidence) then runs a hard gate.
- **AC-4 (Task 1, minor): `provision-governed` cannot fence before the DB exists.** It creates/no-ops from the admin/base connection, THEN connects to `tcc_fidelity_governed` and runs the fence as a POST-check before applying DDL. Reviewers must NOT flag the absent pre-create fence as a defect.
- **AC-5 (merge): fold into PR #42.** All slice commits land on `tcc/access-fidelity-harness` (= PR #42); no second "make it durable" PR. The cross-engine IRP pass runs on the full branch before the operator merge gate.

## File Structure

- `access_harness/config.py` (modify) - add `GOVERNED_DB`, `governed_pg_dsn()`, `assert_current_database()`, `ensure_database()`.
- `access_harness/cli.py` (modify) - add `--governed` flag, `_pg_dsn_for(args)`, `_fence_governed(conn, args)`, a `provision-governed` subcommand; route + fence `load`/`inventory`/`run-all`; wire `reconcile_checksums` + style `key_quality` into the pipeline; `_load_slice` returns `col_types_by_table`.
- `access_harness/validate.py` (modify) - add `reconcile_checksums()` (+ a private `_read_all_rows` helper); add a `_STYLE_TABLES` constant + `reconcile_style_key_quality()` helper.
- `tests/test_config.py` (create) - `governed_pg_dsn`, `assert_current_database`, `ensure_database` tests.
- `tests/test_cli.py` (modify) - `--governed` routing + fence refusal tests.
- `tests/test_validate.py` (modify) - `reconcile_checksums` match/mismatch/skip tests; style `key_quality` test.
- `tests/test_acceptance_f79_03.py` (modify) - assert style-parent checksum + key_quality coverage after `run_all`.

---

### Task 1: Governed DSN + provision + `--governed` fence/routing

**Files:**
- Modify: `access_harness/config.py`
- Modify: `access_harness/cli.py`
- Create: `tests/test_config.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `config.pg_dsn()`, `config._with_db(dsn, dbname)`, `config.test_pg_dsn()`, `config.apply_sql(conn, path)` (all existing); `cli._pg_dsn_from_env()`, `cli._connect_pg(dsn, *, autocommit)` (existing).
- Produces:
  - `config.GOVERNED_DB = "tcc_fidelity_governed"` (str constant).
  - `config.governed_pg_dsn() -> str` (base DSN with db path swapped to `tcc_fidelity_governed`).
  - `config.assert_current_database(conn, expected: str) -> None` (raises `RuntimeError` if `current_database() != expected`).
  - `config.ensure_database(admin_conn, dbname: str) -> bool` (returns True if it created the DB, False if it already existed; admin_conn must be autocommit and connected to a DB other than `dbname`).
  - `cli._pg_dsn_for(args) -> str` (governed DSN when `args.governed`, else base).
  - `cli._fence_governed(conn, args) -> None` (asserts the governed DB when `args.governed`; no-op otherwise).
  - CLI global flag `--governed`; subcommand `provision-governed`.

- [ ] **Step 1: Write failing tests for `governed_pg_dsn` + `assert_current_database`**

Create `tests/test_config.py`:

```python
"""Tests for access_harness.config governed-target helpers.

The governed DSN derivation is pure-string (no DB).  assert_current_database is
proven with BOTH a real fixture connection AND a stub connection parametrized
over the DB names the --governed fence must refuse (postgres / tcc_fidelity_test
/ arbitrary) -- so the refusal logic is proven for every name without the suite
ever touching tcc_fidelity_governed.
"""
import os
from contextlib import contextmanager

import pytest

from access_harness import config


def _base_dsn() -> str:
    if not os.environ.get("ACCESS_HARNESS_SUPERUSER_DSN"):
        pytest.skip("ACCESS_HARNESS_SUPERUSER_DSN unset")
    return config.pg_dsn()


def test_governed_pg_dsn_swaps_db_only(monkeypatch):
    """governed_pg_dsn() swaps ONLY the db path to tcc_fidelity_governed; the
    netloc (user/host/port) is byte-identical to the base DSN."""
    base = "postgresql://u:pw@127.0.0.1:5432/postgres"
    monkeypatch.setenv("ACCESS_HARNESS_SUPERUSER_DSN", base)
    gov = config.governed_pg_dsn()
    assert gov == "postgresql://u:pw@127.0.0.1:5432/tcc_fidelity_governed"
    # netloc identical to test_pg_dsn (which targets tcc_fidelity_test)
    assert config.test_pg_dsn().rsplit("/", 1)[0] == gov.rsplit("/", 1)[0]
    assert config.GOVERNED_DB == "tcc_fidelity_governed"


class _StubConn:
    """Minimal psycopg-conn stand-in: cursor() -> ctx mgr; execute/fetchone
    return a fixed current_database() value."""
    def __init__(self, db):
        self._db = db
    @contextmanager
    def cursor(self):
        outer = self
        class _Cur:
            def execute(self, *_a, **_k):
                pass
            def fetchone(self):
                return (outer._db,)
        yield _Cur()


@pytest.mark.parametrize("wrong_db", ["postgres", "tcc_fidelity_test", "whatever_db"])
def test_assert_current_database_refuses_wrong_db(wrong_db):
    """assert_current_database raises for any DB that is not the expected one."""
    with pytest.raises(RuntimeError):
        config.assert_current_database(_StubConn(wrong_db), "tcc_fidelity_governed")


def test_assert_current_database_passes_on_match():
    """assert_current_database is a no-op when the connected DB matches."""
    config.assert_current_database(_StubConn("tcc_fidelity_governed"),
                                   "tcc_fidelity_governed")  # must not raise


def test_assert_current_database_real_conn(pg):
    """With the real fixture conn (tcc_fidelity_test): passes for its own name,
    raises for the governed name."""
    config.assert_current_database(pg, "tcc_fidelity_test")  # no raise
    with pytest.raises(RuntimeError):
        config.assert_current_database(pg, "tcc_fidelity_governed")
```

- [ ] **Step 2: Run the new tests; verify they FAIL**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL with `AttributeError: module 'access_harness.config' has no attribute 'governed_pg_dsn'` (and `GOVERNED_DB` / `assert_current_database`).

- [ ] **Step 3: Implement `GOVERNED_DB`, `governed_pg_dsn`, `assert_current_database` in `config.py`**

Append to `access_harness/config.py`:

```python
GOVERNED_DB = "tcc_fidelity_governed"


def governed_pg_dsn() -> str:
    """Return a DSN pointing at tcc_fidelity_governed (derived from pg_dsn()).

    Mirrors test_pg_dsn(): only the database path is swapped; the netloc
    (user / host / port) stays byte-identical to the base DSN.
    """
    return _with_db(pg_dsn(), GOVERNED_DB)


def assert_current_database(conn, expected: str) -> None:
    """Raise RuntimeError unless conn.current_database() == expected.

    The fail-closed fence for governed runs: a governed command must refuse to
    do any work unless it is actually connected to `expected`.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        (current,) = cur.fetchone()
    if current != expected:
        raise RuntimeError(
            f"DATABASE FENCE VIOLATION: connected to '{current}' but this "
            f"operation requires '{expected}'. Refusing to proceed."
        )
```

- [ ] **Step 4: Run the tests; verify they PASS**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS (4 tests: swap, refuses-parametrized x3, passes-on-match, real-conn).

- [ ] **Step 5: Write failing test for `ensure_database` (idempotent create)**

Append to `tests/test_config.py`:

```python
import psycopg


def test_ensure_database_idempotent(pg):
    """ensure_database creates a missing DB (True), is a no-op if present (False),
    and never raises on an existing DB.  Uses a uniquely-named throwaway probe DB
    -- NEVER tcc_fidelity_governed -- and drops it afterward.

    OPT-IN (AC-1): cluster-mutating (creates/drops a probe db), so it is SKIPPED
    unless ACCESS_HARNESS_ALLOW_DB_CREATE=1 -- a default suite run never mutates
    the cluster."""
    if os.environ.get("ACCESS_HARNESS_ALLOW_DB_CREATE") != "1":
        pytest.skip("opt-in only: set ACCESS_HARNESS_ALLOW_DB_CREATE=1 (AC-1)")
    base = _base_dsn()  # connect to the base DB (postgres); ensure a DIFFERENT db
    probe = "tcc_fidelity_ensure_probe_t1"
    admin = psycopg.connect(base, autocommit=True)
    try:
        # Clean slate: drop the probe if a prior run left it.
        with admin.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {probe}")

        created = config.ensure_database(admin, probe)
        assert created is True, "first ensure must CREATE the probe db"

        # It now exists.
        with admin.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (probe,))
            assert cur.fetchone() is not None

        again = config.ensure_database(admin, probe)
        assert again is False, "second ensure must be a no-op (already exists)"
    finally:
        with admin.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {probe}")
        admin.close()
```

- [ ] **Step 6: Run the test; verify it FAILS**

Run: `uv run pytest tests/test_config.py::test_ensure_database_idempotent -v`
Expected: FAIL with `AttributeError: ... 'ensure_database'`.

- [ ] **Step 7: Implement `ensure_database` in `config.py`**

Append to `access_harness/config.py` (add `from psycopg import sql` to the imports at the top of the file):

```python
def ensure_database(admin_conn, dbname: str) -> bool:
    """CREATE DATABASE dbname if it does not exist. Idempotent; never drops.

    admin_conn must be an AUTOCOMMIT psycopg connection to a DIFFERENT database
    (CREATE DATABASE cannot run inside a transaction block). Returns True if it
    created the database, False if it already existed. The dbname is embedded via
    psycopg.sql.Identifier (never an f-string) so it is safely quoted.
    """
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        if cur.fetchone() is not None:
            return False
        cur.execute(
            sql.SQL("CREATE DATABASE {db}").format(db=sql.Identifier(dbname))
        )
    return True
```

(Top-of-file import line becomes: `from psycopg import sql` alongside the existing `import os`, `import re`, etc. `psycopg` itself is already a dependency.)

- [ ] **Step 8: Run the test; verify it PASSES**

Run: `uv run pytest tests/test_config.py::test_ensure_database_idempotent -v`
Expected: PASS.

- [ ] **Step 9: Write failing tests for CLI `--governed` routing + fence**

Append to `tests/test_cli.py`:

```python
from access_harness import config as _config


def test_cli_parser_accepts_governed_flag():
    """The parser exposes a --governed boolean defaulting to False."""
    parser = cli.build_parser()
    args = parser.parse_args(["--governed", "run-all"])
    assert args.governed is True
    args2 = parser.parse_args(["run-all"])
    assert args2.governed is False


def test_pg_dsn_for_routes_governed(monkeypatch):
    """_pg_dsn_for returns the governed DSN when args.governed, else the base."""
    base = "postgresql://u:pw@127.0.0.1:5432/postgres"
    monkeypatch.setenv("ACCESS_HARNESS_SUPERUSER_DSN", base)

    class _A:
        governed = True
    class _B:
        governed = False

    assert cli._pg_dsn_for(_A()).endswith("/tcc_fidelity_governed")
    assert cli._pg_dsn_for(_B()).endswith("/postgres")


def test_fence_governed_refuses_wrong_db():
    """_fence_governed raises when --governed but connected to the wrong DB, and
    is a no-op when --governed is not set (even on a non-governed DB)."""
    from tests.test_config import _StubConn  # reuse the stub

    class _Gov:
        governed = True
    class _Plain:
        governed = False

    # --governed on the wrong db -> refuse.
    with pytest.raises(RuntimeError):
        cli._fence_governed(_StubConn("tcc_fidelity_test"), _Gov())
    # --governed on the right db -> ok.
    cli._fence_governed(_StubConn("tcc_fidelity_governed"), _Gov())
    # not --governed -> no fence, even on a non-governed db.
    cli._fence_governed(_StubConn("postgres"), _Plain())
```

(Note: `tests/test_config.py` must be importable as `tests.test_config`; the test package already has `tests/__init__.py`.)

- [ ] **Step 10: Run the tests; verify they FAIL**

Run: `uv run pytest tests/test_cli.py -k "governed or pg_dsn_for or fence" -v`
Expected: FAIL (`AttributeError` on `cli._pg_dsn_for` / `cli._fence_governed`; parser has no `--governed`).

- [ ] **Step 11: Implement `--governed`, `_pg_dsn_for`, `_fence_governed` in `cli.py`**

In `access_harness/cli.py`:

(a) Add the flag in `build_parser()`, right after the existing `--with-curves` argument:

```python
    p.add_argument(
        "--governed",
        action="store_true",
        help="target the durable governed DB (tcc_fidelity_governed) and FENCE "
             "every connection to it (fail closed); off = the base DSN's db",
    )
```

(b) Add the two helpers near `_pg_dsn_from_env`:

```python
def _pg_dsn_for(args) -> str:
    """Return the governed DSN when --governed is set, else the base DSN.

    Both go through config so the SQLAlchemy-style +driver prefix is stripped
    identically to the tests' connection path.
    """
    if getattr(args, "governed", False):
        return config.governed_pg_dsn()
    return config.pg_dsn()


def _fence_governed(conn, args) -> None:
    """Fail closed: when --governed is set, assert conn is on tcc_fidelity_governed.

    Called immediately after each connection is opened and BEFORE any load /
    schema action, so a governed command can never write into postgres / _test /
    any other DB. No-op when --governed is not set.
    """
    if getattr(args, "governed", False):
        config.assert_current_database(conn, config.GOVERNED_DB)
```

- [ ] **Step 12: Run the tests; verify they PASS**

Run: `uv run pytest tests/test_cli.py -k "governed or pg_dsn_for or fence" -v`
Expected: PASS.

- [ ] **Step 13: Route + fence `load`/`inventory`/`run-all`; add `provision-governed`**

In `access_harness/cli.py`, replace each subcommand's `dsn = _pg_dsn_from_env()` with `dsn = _pg_dsn_for(args)`, and add a `_fence_governed(conn, args)` call immediately after EACH `_connect_pg(...)` in `cmd_load`, `cmd_inventory`, and `cmd_run_all`, BEFORE `_load_slice` / `record_extraction_run` writes. Concretely, in `cmd_run_all`:

```python
def cmd_run_all(args) -> int:
    accdb = _accdb_path(args)
    dest = Path(args.frozen_dir) if args.frozen_dir else frozen_dir()
    dsn = _pg_dsn_for(args)
    pg_auto = _connect_pg(dsn, autocommit=True)
    pg_tx = _connect_pg(dsn, autocommit=False)
    try:
        _fence_governed(pg_auto, args)   # fail closed before ANY work
        _fence_governed(pg_tx, args)
        result = run_all(
            pg_auto, pg_tx, accdb, dest, with_curves=args.with_curves
        )
    finally:
        pg_tx.close()
        pg_auto.close()
    print(f"run_id:     {result['run_id']}")
    print(f"snapshot_id:{result['snapshot_id']}")
    print(f"loaded:     {len(result['loaded'])} tables")
    print(f"inventoried:{len(result['all_tables'])} tables")
    return 0
```

Apply the identical change (swap to `_pg_dsn_for(args)` + `_fence_governed(...)` right after each connect, before any write) to `cmd_load` and `cmd_inventory`.

Add the `provision-governed` subcommand:

```python
def cmd_provision_governed(args) -> int:
    """Create tcc_fidelity_governed if absent and apply the harness DDL to it.

    Operator-run only (never the test suite). Connects to the BASE db to create
    the governed db, then connects to the governed db, FENCES, and applies the
    idempotent schema DDL (CREATE SCHEMA/TABLE IF NOT EXISTS).
    """
    base_dsn = config.pg_dsn()
    admin = _connect_pg(base_dsn, autocommit=True)
    try:
        created = config.ensure_database(admin, config.GOVERNED_DB)
    finally:
        admin.close()
    print(f"governed db {config.GOVERNED_DB}: "
          f"{'created' if created else 'already present'}")

    gov = _connect_pg(config.governed_pg_dsn(), autocommit=True)
    try:
        config.assert_current_database(gov, config.GOVERNED_DB)  # fail closed
        schema_sql = Path(__file__).parent.parent / "sql" / "001_schemas.sql"
        config.apply_sql(gov, schema_sql)
    finally:
        gov.close()
    print(f"applied 001_schemas.sql to {config.GOVERNED_DB}")
    return 0
```

Register it in `build_parser()`:

```python
    sub.add_parser(
        "provision-governed",
        help="create tcc_fidelity_governed (if absent) + apply harness DDL",
    ).set_defaults(func=cmd_provision_governed)
```

Then add the AC-2 per-command fence integration test to `tests/test_cli.py` (proves EVERY governed command path fences before any write):

```python
def test_governed_command_paths_fence_before_write(monkeypatch):
    """AC-2: load / inventory / run-all with --governed resolving to a NON-governed
    DB must raise the fence error BEFORE any write (record_extraction_run and
    _load_slice never run). Access-dependent steps are monkeypatched to no-ops so
    the test is fast + independent of the Windows Access path; the fence is the
    thing under test."""
    from access_harness import cli, config, extract, freeze as freeze_mod

    base = _base_dsn()
    monkeypatch.setenv("ACCESS_HARNESS_SUPERUSER_DSN", base)
    # --governed resolves to tcc_fidelity_test (a NON-governed db) -> fence fires.
    monkeypatch.setattr(config, "governed_pg_dsn", config.test_pg_dsn)

    class _FS:
        frozen_path = "X:/frozen.accdb"
        source_sha256 = "00" * 32
    monkeypatch.setattr(freeze_mod, "freeze", lambda *a, **k: _FS())
    monkeypatch.setattr(cli, "driver_preflight", lambda *a, **k: ("drv", "ver", 1))
    monkeypatch.setattr(extract, "connect_data", lambda *a, **k: object())
    monkeypatch.setattr(extract, "connect_ace", lambda *a, **k: object())

    def _boom_record(*a, **k):
        raise AssertionError("record_extraction_run ran BEFORE the fence")
    def _boom_load(*a, **k):
        raise AssertionError("_load_slice ran BEFORE the fence")
    monkeypatch.setattr(freeze_mod, "record_extraction_run", _boom_record)
    monkeypatch.setattr(cli, "_load_slice", _boom_load)

    class _Args:
        governed = True
        with_curves = False
        accdb = None
        frozen_dir = None

    for cmd in (cli.cmd_load, cli.cmd_inventory, cli.cmd_run_all):
        with pytest.raises(RuntimeError, match="FENCE VIOLATION"):
            cmd(_Args())
```

Run: `uv run pytest tests/test_cli.py::test_governed_command_paths_fence_before_write -v`
Expected: PASS -- each command raises the fence (the boom sentinels prove no write was reached). If a `_boom_*` AssertionError surfaces instead, a command writes before fencing -> a real AC-2 defect; fix the connect/fence ordering.

- [ ] **Step 14: Run the full fast suite; verify nothing regressed**

Run: `uv run pytest -q --deselect tests/test_acceptance_f79_03.py`
Expected: PASS (prior 124 + the new config/cli tests). `provision-governed` is NOT exercised by the suite (operator-run only).

- [ ] **Step 15: Commit Task 1**

```bash
cd /c/dev/apex-access-harness
git add infra/database/access-harness/access_harness/config.py \
        infra/database/access-harness/access_harness/cli.py \
        infra/database/access-harness/tests/test_config.py \
        infra/database/access-harness/tests/test_cli.py
git -c user.name='jasonlswenson-sys' -c user.email='jasonlswenson@gmail.com' \
    commit -m "feat(access-harness): governed-target DSN + provision + --governed fail-closed fence

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Checksum + checksum_reconciliation wiring

**Files:**
- Modify: `access_harness/validate.py`
- Modify: `access_harness/cli.py`
- Modify: `tests/test_validate.py`

**Interfaces:**
- Consumes: `checksum.table_checksum(rows, col_types)` (existing, returns sha256 hex over sorted canonical rows); `typemap.ColumnType` (existing dataclass with `.name`, `.pg_type`, etc.); `access_meta.tables` + `access_validation.checksum_reconciliation` (existing schema); `cli._load_slice` (existing).
- Produces:
  - `validate.reconcile_checksums(pg_conn, run_id, loaded_tables, col_types_by_table, access_rows_for) -> None`.
    - `loaded_tables`: iterable of table names (data-loaded into access_raw; callers exclude count-only curves).
    - `col_types_by_table`: dict `{table_name: list[ColumnType]}` (the column metadata used to load the table; column order == access_raw create order).
    - `access_rows_for`: callable `table_name -> Iterable[tuple]` yielding the ACCESS-side rows (production passes `lambda t: extract.read_rows(data_conn, t)`; tests pass a dict-backed reader).
    - For each table: computes staging checksum (from `access_raw.<table>`, columns read in `col_types` order) and access checksum (from `access_rows_for`), both via `table_checksum` with the SAME `col_types`; writes `access_meta.tables.checksum = <staging checksum>` + `load_state='checksummed'`; upserts `access_validation.checksum_reconciliation (run_id, table_name, access_checksum, staging_checksum, matches)`.
  - `cli._load_slice(...)` now returns `(loaded_set, col_types_by_table)`.

- [ ] **Step 1: Write failing test for `reconcile_checksums` MATCH**

Append to `tests/test_validate.py`:

```python
from access_harness.typemap import ColumnType


def _ct(name, pg_type="integer"):
    """A minimal ColumnType for checksum canonicalization in tests."""
    return ColumnType(
        access_type="", pg_type=pg_type, nullable=True, size=None,
        precision=None, round_trippable=True, name=name,
    )


def _seed_loaded_table(pg_conn, run_id, table, staging_count):
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO access_meta.tables
                (run_id, table_name, object_type, load_state,
                 access_row_count, staging_row_count, tcc_build_kind)
            VALUES (%s, %s, 'TABLE', 'loaded', %s, %s, '1:1_load')
            ON CONFLICT (run_id, table_name) DO UPDATE SET load_state='loaded'
            """,
            (run_id, table, staging_count, staging_count),
        )


def test_reconcile_checksums_match(pg):
    """Identical access + staging rows -> matches=True, checksum recorded,
    load_state='checksummed', access_checksum == staging_checksum."""
    from access_harness.validate import reconcile_checksums

    run_id = _seed_run(pg, "run-cksum-match")
    with pg.cursor() as cur:
        cur.execute('CREATE TABLE access_raw."T1" (a integer, b integer)')
        cur.executemany(
            'INSERT INTO access_raw."T1" (a, b) VALUES (%s, %s)',
            [(1, 10), (2, 20), (3, 30)],
        )
    _seed_loaded_table(pg, run_id, "T1", 3)

    col_types = {"T1": [_ct("a"), _ct("b")]}
    access_rows = {"T1": [(1, 10), (2, 20), (3, 30)]}  # identical -> match

    reconcile_checksums(pg, run_id, ["T1"], col_types,
                        access_rows_for=lambda t: access_rows[t])

    with pg.cursor() as cur:
        cur.execute(
            "SELECT access_checksum, staging_checksum, matches "
            "FROM access_validation.checksum_reconciliation "
            "WHERE run_id=%s AND table_name=%s", (run_id, "T1"))
        access_ck, staging_ck, matches = cur.fetchone()
        cur.execute(
            "SELECT checksum, load_state FROM access_meta.tables "
            "WHERE run_id=%s AND table_name=%s", (run_id, "T1"))
        meta_ck, state = cur.fetchone()

    assert matches is True
    assert access_ck == staging_ck
    assert meta_ck == staging_ck and meta_ck is not None
    assert state == "checksummed"
```

- [ ] **Step 2: Run; verify FAIL**

Run: `uv run pytest tests/test_validate.py::test_reconcile_checksums_match -v`
Expected: FAIL with `ImportError: cannot import name 'reconcile_checksums'`.

- [ ] **Step 3: Implement `reconcile_checksums` + `_read_all_rows` in `validate.py`**

Add `from access_harness.checksum import canonical_row, multiset_diff, table_checksum` (extend the existing import) and append:

```python
def _read_all_rows(pg_conn, schema: str, table: str, col_names: list) -> list:
    """SELECT col_names (in order) from schema.table; return list of tuples.

    Reading by the SAME column order used to build col_types guarantees the row
    tuples align positionally with col_types for canonical_row / table_checksum.
    """
    col_ids = sql.SQL(", ").join(sql.Identifier(c) for c in col_names)
    stmt = sql.SQL("SELECT {cols} FROM {schema}.{table}").format(
        cols=col_ids, schema=sql.Identifier(schema), table=sql.Identifier(table),
    )
    with pg_conn.cursor() as cur:
        cur.execute(stmt)
        return [tuple(r) for r in cur.fetchall()]


def reconcile_checksums(
    pg_conn,
    run_id: str,
    loaded_tables,
    col_types_by_table: dict,
    access_rows_for,
) -> None:
    """Record a per-table checksum + the access-vs-staging reconciliation.

    For each table in loaded_tables, compute:
      * staging checksum = table_checksum(access_raw.<table> rows, col_types)
      * access  checksum = table_checksum(access_rows_for(table), col_types)
    using the SAME col_types (the Task-2 symmetric-canonicalization contract).
    Write access_meta.tables.checksum = staging checksum + load_state='checksummed',
    and upsert access_validation.checksum_reconciliation (access/staging/matches).

    Purely structural (a hash + a boolean). HR1: records WHAT differs (matches),
    never opines on whether a mismatch is acceptable. Does NOT raise on mismatch.
    """
    for table in loaded_tables:
        col_types = col_types_by_table[table]
        col_names = [ct.name for ct in col_types]
        staging_rows = _read_all_rows(pg_conn, "access_raw", table, col_names)
        staging_ck = table_checksum(staging_rows, col_types)
        access_ck = table_checksum(access_rows_for(table), col_types)
        matches = access_ck == staging_ck

        with pg_conn.cursor() as cur:
            cur.execute(
                """
                UPDATE access_meta.tables
                   SET checksum = %s, load_state = 'checksummed'
                 WHERE run_id = %s AND table_name = %s
                """,
                (staging_ck, run_id, table),
            )
            cur.execute(
                """
                INSERT INTO access_validation.checksum_reconciliation
                    (run_id, table_name, access_checksum, staging_checksum, matches)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (run_id, table_name) DO UPDATE SET
                    access_checksum = EXCLUDED.access_checksum,
                    staging_checksum = EXCLUDED.staging_checksum,
                    matches = EXCLUDED.matches
                """,
                (run_id, table, access_ck, staging_ck, matches),
            )
```

Also add the AC-3 fail-closed gate + its error to `validate.py`. `reconcile_checksums` RECORDS the reconciliation (HR1 structural evidence -- it never raises); this GATE, run after recording, refuses to certify a non-faithful style mirror:

```python
class ChecksumFidelityError(RuntimeError):
    """A governed/certified table's access_raw mirror did not round-trip
    (checksum_reconciliation.matches != True). A mirror that is not byte-faithful
    must not be certified for population -- fail closed."""


def assert_style_parents_faithful(pg_conn, run_id: str) -> None:
    """Fail closed (AC-3) if any present style parent did not round-trip.

    The 3 BreakerXXXStyles tables are the D4/D5 carriers feeding the 029/030
    population, so matches=False (or no recorded checksum) there means the mirror
    is not byte-faithful and must not be certified. The reconciliation evidence is
    already persisted by reconcile_checksums; this only READS it and raises
    ChecksumFidelityError naming the offender(s). Style tables not present this run
    are skipped (not every run loads them).
    """
    offenders = []
    for table in sorted(_ACCESS_STYLE_TABLES.values()):
        with pg_conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='access_raw' AND table_name=%s", (table,))
            if cur.fetchone() is None:
                continue
            cur.execute(
                "SELECT matches FROM access_validation.checksum_reconciliation "
                "WHERE run_id=%s AND table_name=%s", (run_id, table))
            row = cur.fetchone()
        if row is None:
            offenders.append(f"{table} (no checksum recorded)")
        elif row[0] is not True:
            offenders.append(f"{table} (matches={row[0]!r})")
    if offenders:
        raise ChecksumFidelityError(
            "style-parent access_raw mirror is NOT byte-faithful; refusing to "
            "certify for population. Offending: " + ", ".join(offenders)
        )
```

- [ ] **Step 4: Run; verify PASS**

Run: `uv run pytest tests/test_validate.py::test_reconcile_checksums_match -v`
Expected: PASS.

- [ ] **Step 5: Write failing tests for MISMATCH + SKIP-non-loaded**

Append to `tests/test_validate.py`:

```python
def test_reconcile_checksums_mismatch_records_not_raises(pg):
    """Differing access vs staging -> matches=False, both checksums recorded and
    distinct, no exception (HR1: records the discrepancy, never opines)."""
    from access_harness.validate import reconcile_checksums

    run_id = _seed_run(pg, "run-cksum-mismatch")
    with pg.cursor() as cur:
        cur.execute('CREATE TABLE access_raw."T2" (a integer)')
        cur.executemany('INSERT INTO access_raw."T2" (a) VALUES (%s)',
                        [(1,), (2,), (3,)])
    _seed_loaded_table(pg, run_id, "T2", 3)

    col_types = {"T2": [_ct("a")]}
    access_rows = {"T2": [(1,), (2,), (999,)]}  # one differing row

    reconcile_checksums(pg, run_id, ["T2"], col_types,
                        access_rows_for=lambda t: access_rows[t])

    with pg.cursor() as cur:
        cur.execute(
            "SELECT access_checksum, staging_checksum, matches "
            "FROM access_validation.checksum_reconciliation "
            "WHERE run_id=%s AND table_name=%s", (run_id, "T2"))
        access_ck, staging_ck, matches = cur.fetchone()
    assert matches is False
    assert access_ck != staging_ck
    assert access_ck and staging_ck


def test_reconcile_checksums_only_processes_listed_tables(pg):
    """Tables NOT in loaded_tables get no checksum row (count-only/unloaded are
    excluded by the caller)."""
    from access_harness.validate import reconcile_checksums

    run_id = _seed_run(pg, "run-cksum-skip")
    with pg.cursor() as cur:
        cur.execute('CREATE TABLE access_raw."Kept" (a integer)')
        cur.execute('INSERT INTO access_raw."Kept" (a) VALUES (1)')
    _seed_loaded_table(pg, run_id, "Kept", 1)

    reconcile_checksums(pg, run_id, ["Kept"], {"Kept": [_ct("a")]},
                        access_rows_for=lambda t: [(1,)])

    with pg.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM access_validation.checksum_reconciliation "
            "WHERE run_id=%s", (run_id,))
        (n,) = cur.fetchone()
    assert n == 1, "only the one listed table should be checksummed"


def test_reconcile_checksums_type_roundtrip(pg):
    """AC-3: diverse column types round-trip through a REAL access_raw readback so
    the access-side and staging-side canonicalize identically (matches=True)."""
    from datetime import date, datetime
    from decimal import Decimal
    from access_harness.validate import reconcile_checksums

    run_id = _seed_run(pg, "run-cksum-types")
    with pg.cursor() as cur:
        cur.execute(
            'CREATE TABLE access_raw."Typed" ('
            '"i" integer, "f" double precision, "n" numeric, "d" date, '
            '"ts" timestamp, "b" boolean, "by" bytea, "t" text)'
        )
        rows = [
            (1, 1.5, Decimal("2.50"), date(2026, 6, 27),
             datetime(2026, 6, 27, 12, 0, 0), True, b"\x01\x02\xff", "memo text"),
            (None, None, None, None, None, None, None, None),
        ]
        cur.executemany(
            'INSERT INTO access_raw."Typed" '
            '("i","f","n","d","ts","b","by","t") VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
            rows,
        )
    _seed_loaded_table(pg, run_id, "Typed", len(rows))
    col_types = {"Typed": [
        _ct("i", "integer"), _ct("f", "double precision"), _ct("n", "numeric"),
        _ct("d", "date"), _ct("ts", "timestamp"), _ct("b", "boolean"),
        _ct("by", "bytea"), _ct("t", "text"),
    ]}
    # access-side rows == the SAME logical values; a faithful round-trip -> match.
    reconcile_checksums(pg, run_id, ["Typed"], col_types,
                        access_rows_for=lambda t: list(rows))

    with pg.cursor() as cur:
        cur.execute(
            "SELECT matches FROM access_validation.checksum_reconciliation "
            "WHERE run_id=%s AND table_name=%s", (run_id, "Typed"))
        (matches,) = cur.fetchone()
    assert matches is True, (
        "diverse-typed access vs staging readback must canonicalize identically")


def test_assert_style_parents_faithful_gate(pg):
    """AC-3: the gate raises when a present style parent has matches=False (or no
    recorded checksum), and is a no-op when all present style parents match."""
    from access_harness.validate import (
        ChecksumFidelityError, assert_style_parents_faithful, reconcile_checksums,
    )

    run_id = _seed_run(pg, "run-style-gate")
    with pg.cursor() as cur:
        cur.execute('CREATE TABLE access_raw."BreakerICCBStyles" ("ID" integer)')
        cur.executemany(
            'INSERT INTO access_raw."BreakerICCBStyles" ("ID") VALUES (%s)',
            [(1,), (2,)],
        )
    _seed_loaded_table(pg, run_id, "BreakerICCBStyles", 2)

    # Faithful -> gate passes.
    reconcile_checksums(pg, run_id, ["BreakerICCBStyles"],
                        {"BreakerICCBStyles": [_ct("ID")]},
                        access_rows_for=lambda t: [(1,), (2,)])
    assert_style_parents_faithful(pg, run_id)  # must not raise

    # Force a mismatch -> gate raises, naming the offending table.
    reconcile_checksums(pg, run_id, ["BreakerICCBStyles"],
                        {"BreakerICCBStyles": [_ct("ID")]},
                        access_rows_for=lambda t: [(1,), (999,)])
    with pytest.raises(ChecksumFidelityError, match="BreakerICCBStyles"):
        assert_style_parents_faithful(pg, run_id)
```

- [ ] **Step 6: Run; verify PASS**

Run: `uv run pytest tests/test_validate.py -k "reconcile_checksums or type_roundtrip or style_parents_faithful" -v`
Expected: PASS (5 tests: match, mismatch, skip, type-roundtrip, gate). The gate `assert_style_parents_faithful` is implemented in Step 3.

- [ ] **Step 7: Wire `reconcile_checksums` into the pipeline; `_load_slice` returns col_types**

In `access_harness/cli.py`:

(a) Make `_load_slice` capture + return col_types per table:

```python
def _load_slice(pg_conn, data_conn, run_id: str, *, with_curves: bool) -> tuple:
    """Data-load the breaker/TMT slice into access_raw.

    Returns (loaded_table_set, col_types_by_table) so the caller can checksum the
    loaded tables with the SAME col_types used to load them.
    """
    loaded = set()
    col_types_by_table = {}
    for table in SLICE_TABLES:
        if table == CURVES_TABLE and not with_curves:
            continue
        col_types = extract.column_meta(data_conn, table)
        rows = extract.read_rows(data_conn, table)
        count = load.load_table(pg_conn, table, col_types, rows, run_id)
        loaded.add(table)
        col_types_by_table[table] = col_types
        print(f"loaded access_raw.{table}: {count} rows")
    return loaded, col_types_by_table
```

(b) Update every caller of `_load_slice` to unpack the tuple, and run `reconcile_checksums` while `data_conn` is still open. In `run_all`:

```python
    data_conn = extract.connect_data(fs.frozen_path)
    ace_conn = extract.connect_ace(fs.frozen_path)
    try:
        loaded, col_types_by_table = _load_slice(
            pg_tx, data_conn, run_id, with_curves=with_curves
        )
        all_tables = extract.list_user_tables(ace_conn)
        count_only = set() if with_curves else {CURVES_TABLE}
        inventory.populate_meta(
            pg_auto, data_conn, ace_conn, run_id, all_tables, loaded,
            count_only_tables=count_only,
        )
        # Per-table checksum + access-vs-staging reconciliation (after inventory,
        # which re-inserts load_state='loaded'; this upgrades it to 'checksummed').
        validate.reconcile_checksums(
            pg_auto, run_id, sorted(loaded), col_types_by_table,
            access_rows_for=lambda t: extract.read_rows(data_conn, t),
        )
    finally:
        try:
            ace_conn.Close()
        except Exception:
            pass
        data_conn.close()
```

In `cmd_load`, unpack and add a checksum step on an autocommit connection while `data_conn` is open (reorder so `data_conn` is not closed first):

```python
def cmd_load(args) -> int:
    fs = _frozen_for(args)
    driver_name, dbms_version, _ = driver_preflight(fs.frozen_path)
    dsn = _pg_dsn_for(args)

    pg_auto = _connect_pg(dsn, autocommit=True)
    try:
        _fence_governed(pg_auto, args)
        run_id = freeze_mod.record_extraction_run(
            pg_auto, fs, driver_name, dbms_version
        )
        data_conn = extract.connect_data(fs.frozen_path)
        pg_tx = _connect_pg(dsn, autocommit=False)
        try:
            _fence_governed(pg_tx, args)
            loaded, col_types_by_table = _load_slice(
                pg_tx, data_conn, run_id, with_curves=args.with_curves
            )
            validate.reconcile_checksums(
                pg_auto, run_id, sorted(loaded), col_types_by_table,
                access_rows_for=lambda t: extract.read_rows(data_conn, t),
            )
        finally:
            pg_tx.close()
            data_conn.close()
    finally:
        pg_auto.close()
    print(f"run_id: {run_id}; loaded {len(loaded)} slice tables")
    return 0
```

In `cmd_inventory`, unpack `_load_slice` and add the same `reconcile_checksums(pg_auto, ...)` call after `inventory.populate_meta`, while `data_conn` is open (before the `data_conn.close()` in its finally).

Ensure `validate` is imported in `cli.py` (it already is: `from access_harness import ... validate`).

Then wire the AC-3 fail-closed gate so a non-faithful style mirror aborts the run (evidence is recorded first, THEN the gate raises):
- In `run_all`: add `validate.assert_style_parents_faithful(pg_auto, run_id)` immediately AFTER the existing `_run_validation(pg_auto, run_id, snapshot_id)` call and before `return {...}` (so all evidence -- counts, checksums, key_quality -- is persisted before the gate fires).
- In `cmd_load` and `cmd_inventory`: add `validate.assert_style_parents_faithful(pg_auto, run_id)` immediately AFTER the `reconcile_checksums(...)` call.

The gate runs in every mode (governed and not), so the live acceptance (non-governed, `tcc_fidelity_test`) also exercises it: a faithful run returns normally; a non-faithful style mirror raises `ChecksumFidelityError` and the command exits nonzero.

- [ ] **Step 8: Run the full fast suite**

Run: `uv run pytest -q --deselect tests/test_acceptance_f79_03.py`
Expected: PASS (all prior + new). If `test_snapshot_tcc`/integration tests call `_load_slice` directly, fix their unpacking too (grep `_load_slice(` first: `uv run python -c "import subprocess"` not needed -- use ripgrep).

Run before implementing wiring: `git grep -n "_load_slice(" -- infra/database/access-harness` to find every caller.

- [ ] **Step 9: Commit Task 2**

```bash
cd /c/dev/apex-access-harness
git add infra/database/access-harness/access_harness/validate.py \
        infra/database/access-harness/access_harness/cli.py \
        infra/database/access-harness/tests/test_validate.py
git -c user.name='jasonlswenson-sys' -c user.email='jasonlswenson@gmail.com' \
    commit -m "feat(access-harness): wire per-table checksum + access-vs-staging reconciliation

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Style-parent validation coverage

**Files:**
- Modify: `access_harness/validate.py`
- Modify: `access_harness/cli.py`
- Modify: `tests/test_validate.py`
- Modify: `tests/test_acceptance_f79_03.py`

**Interfaces:**
- Consumes: `validate.key_quality(pg_conn, schema, table, key_cols, *, run_id, write)` (existing); `reconcile_checksums` (Task 2); `cli._run_validation` (existing).
- Produces:
  - `validate.reconcile_style_key_quality(pg_conn, run_id) -> None` (writes an `access_validation.key_quality` row keyed on `ID` for each of the 3 `BreakerXXXStyles` tables present in `access_raw`).

- [ ] **Step 1: Write failing test for style key_quality coverage**

Append to `tests/test_validate.py`:

```python
def test_style_key_quality_coverage(pg):
    """reconcile_style_key_quality writes a key_quality row (is_unique on ID) for
    each BreakerXXXStyles table present in access_raw."""
    from access_harness.validate import reconcile_style_key_quality

    run_id = _seed_run(pg, "run-style-kq")
    with pg.cursor() as cur:
        for tbl in ("BreakerICCBStyles", "BreakerMCCBStyles", "BreakerPCBStyles"):
            cur.execute(f'CREATE TABLE access_raw."{tbl}" ("ID" integer)')
            cur.executemany(
                f'INSERT INTO access_raw."{tbl}" ("ID") VALUES (%s)',
                [(1,), (2,), (3,)],
            )

    reconcile_style_key_quality(pg, run_id)

    with pg.cursor() as cur:
        cur.execute(
            "SELECT table_name, is_unique, distinct_count, total_count "
            "FROM access_validation.key_quality "
            "WHERE run_id=%s ORDER BY table_name", (run_id,))
        rows = cur.fetchall()
    names = [r[0] for r in rows]
    assert names == ["BreakerICCBStyles", "BreakerMCCBStyles", "BreakerPCBStyles"]
    for _name, is_unique, distinct_ct, total_ct in rows:
        assert is_unique is True
        assert distinct_ct == 3 and total_ct == 3
```

- [ ] **Step 2: Run; verify FAIL**

Run: `uv run pytest tests/test_validate.py::test_style_key_quality_coverage -v`
Expected: FAIL with `ImportError: cannot import name 'reconcile_style_key_quality'`.

- [ ] **Step 3: Implement `reconcile_style_key_quality` in `validate.py`**

`_ACCESS_STYLE_TABLES` already exists in `validate.py` (the `{class: table}` map). Append:

```python
def reconcile_style_key_quality(pg_conn, run_id: str) -> None:
    """Write a key_quality row (keyed on the integer surrogate ID) for each
    BreakerXXXStyles table present in access_raw.

    The style parents are the D4/D5 carriers; their ID is the keyable surrogate
    (style_provenance_antijoin already maps ID -> tcc source_id). Recording
    key_quality completes the style parents' Phase-1 structural coverage. Skips a
    table that is not present (not loaded this run).
    """
    for table in sorted(_ACCESS_STYLE_TABLES.values()):
        with pg_conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='access_raw' AND table_name=%s",
                (table,),
            )
            if cur.fetchone() is None:
                continue
        key_quality(pg_conn, "access_raw", table, ["ID"],
                    run_id=run_id, write=True)
```

- [ ] **Step 4: Run; verify PASS**

Run: `uv run pytest tests/test_validate.py::test_style_key_quality_coverage -v`
Expected: PASS.

- [ ] **Step 5: Wire `reconcile_style_key_quality` into `_run_validation`**

In `access_harness/cli.py`, in `_run_validation`, after the existing `style_provenance_antijoin` loop, add:

```python
    # (4'') style-parent key-quality coverage (ID uniqueness on each style table).
    validate.reconcile_style_key_quality(pg_conn, run_id)
```

- [ ] **Step 6: Extend the live acceptance test to assert style-parent coverage**

In `tests/test_acceptance_f79_03.py`, after the existing `run_all` assertions, add a block that asserts the 3 style parents carry checksum + key_quality coverage. (Read the file first to match its run_id/connection variable names; the run targets `tcc_fidelity_test`.) Add:

```python
def _assert_style_parent_coverage(pg_conn, run_id):
    """The 3 style parents must carry a recorded checksum (load_state checksummed),
    a checksum_reconciliation row, and a key_quality row after run_all."""
    styles = ("BreakerICCBStyles", "BreakerMCCBStyles", "BreakerPCBStyles")
    for tbl in styles:
        with pg_conn.cursor() as cur:
            cur.execute(
                "SELECT checksum, load_state FROM access_meta.tables "
                "WHERE run_id=%s AND table_name=%s", (run_id, tbl))
            ck, state = cur.fetchone()
            assert ck is not None, f"{tbl}: no recorded checksum"
            assert state == "checksummed", f"{tbl}: load_state={state!r}"
            cur.execute(
                "SELECT matches FROM access_validation.checksum_reconciliation "
                "WHERE run_id=%s AND table_name=%s", (run_id, tbl))
            recon = cur.fetchone()
            assert recon is not None, f"{tbl}: no checksum_reconciliation row"
            # Fidelity expectation: the style parents round-trip faithfully
            # (int/text/float/smallint columns). A False here is a GENUINE
            # fidelity finding to surface, not to suppress.
            assert recon[0] is True, (
                f"{tbl}: access-vs-staging checksum MISMATCH (matches=False) -- "
                "investigate the round-trip before generating population SQL")
            cur.execute(
                "SELECT is_unique FROM access_validation.key_quality "
                "WHERE run_id=%s AND table_name=%s", (run_id, tbl))
            kq = cur.fetchone()
            assert kq is not None, f"{tbl}: no key_quality row"
```

Call `_assert_style_parent_coverage(<pg_conn>, <run_id>)` inside the existing acceptance test after `run_all` returns, using that test's own connection + `result['run_id']`.

- [ ] **Step 7: Run the FULL suite incl. live acceptance**

Run: `uv run pytest -q`
Expected: PASS (all fast + 2 live acceptance). The acceptance now also proves the 3 style parents carry checksum + reconciliation (matches True) + key_quality against REAL Access data in `tcc_fidelity_test`.

If `matches` is False for a style table, the AC-3 gate makes `run_all` raise `ChecksumFidelityError` (the command fails closed) -- the acceptance surfaces it as an error at the `run_all` call. STOP and apply systematic-debugging: determine whether it is a real round-trip fidelity gap (a column the typemap maps lossily) or a canonicalization nuance; surface to the operator. Do NOT relax the gate or the assertion to make it pass.

- [ ] **Step 8: Commit Task 3**

```bash
cd /c/dev/apex-access-harness
git add infra/database/access-harness/access_harness/validate.py \
        infra/database/access-harness/access_harness/cli.py \
        infra/database/access-harness/tests/test_validate.py \
        infra/database/access-harness/tests/test_acceptance_f79_03.py
git -c user.name='jasonlswenson-sys' -c user.email='jasonlswenson@gmail.com' \
    commit -m "feat(access-harness): style-parent validation coverage (checksum + key_quality)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Post-build: cross-engine IRP pass (before merge)

After all 3 tasks are green, run the mandatory cross-engine pass on the branch delta (Codex via `apex-jobs review-run --review-head tcc/access-fidelity-harness --base-ref main` + an opus adversarial review), convergence-bounded. Fold genuine findings, hard-stop on convergence. Then bring the branch to the operator at the MERGE GATE. Do NOT merge without an explicit go.

Known risk for the cross-engine lens to scrutinize: the access-vs-staging checksum equality semantics -- whether the Python types read back from `access_raw` (post type-map) canonicalize identically to the Access-side types for every style column, so `matches` is a true fidelity signal and not a spurious mismatch (or a spurious match).

## Self-Review

**1. Spec coverage:**
- Piece 1 (governed affordance: `governed_pg_dsn`, `--governed` route, fail-closed fence, idempotent ensure-db/provision) -> Task 1. Covered.
- Piece 2 (checksum + checksum_reconciliation wired into load/inventory/run-all) -> Task 2. Covered.
- Piece 3 (style-parent coverage: checksum [Task 2, they are loaded] + key_quality) -> Task 3. Covered.
- Operator caution (fence fail-closed before destructive action; refuses postgres/_test/arbitrary; suite never touches governed) -> Task 1 Steps 1/9/11/13 + the parametrized refusal test + provision-governed being operator-only. Covered.
- "no schema migration" -> confirmed: checksum/checksum_reconciliation/'checksummed'/key_quality all pre-exist in 001_schemas.sql. Covered.

**2. Placeholder scan:** No TBD/TODO; every code step shows real code; test code is concrete; commands are exact. The acceptance-test wiring (Task 3 Step 6) instructs reading the file first to match variable names -- that is a real integration constraint, not a placeholder (the helper code is fully given).

**3. Type consistency:** `governed_pg_dsn`/`GOVERNED_DB`/`assert_current_database`/`ensure_database` (config) used consistently in cli (`_pg_dsn_for`, `_fence_governed`, `cmd_provision_governed`). `reconcile_checksums(pg_conn, run_id, loaded_tables, col_types_by_table, access_rows_for)` signature identical in validate def, tests, and all 3 cli call sites. `_load_slice` returns `(loaded, col_types_by_table)` -- every caller (run_all, cmd_load, cmd_inventory) updated to unpack. `reconcile_style_key_quality(pg_conn, run_id)` consistent in validate, test, and `_run_validation`. `ColumnType(...)` fields match the real dataclass used in `validate._neutral_col_types`.
