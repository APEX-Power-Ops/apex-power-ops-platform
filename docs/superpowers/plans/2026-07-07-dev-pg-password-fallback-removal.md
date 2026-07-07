# DEV_PG_PASSWORD Dead-Fallback Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task (inline, single-writer over mesh). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the incoherent `DEV_PG_PASSWORD` fallback from every apex-jobs path that connects as the `orchestration` role, so that role's password is unambiguously `APEX_JOBS_PGPASSWORD` (Infisical `dev`, injected), fails closed when absent, and never leaks; keep `DEV_PG_PASSWORD` in `infra/.env` by design as the `postgres` superuser / `compose`-init credential.

**Architecture:** A three-file behavior change (`db.py` runtime resolver + two test helpers) gated by a value-silent no-DB contract test, then a stale-string cleanup and a doc/comment reclassification sweep. No schema, no new files except none; `DEV_PG_PASSWORD` stays in the cache and in the secret-audit allowlist.

**Tech Stack:** Python 3 (psycopg3), pytest, uv, bash, Infisical injection (`infra/infisical/inject.sh`, `apex-jobs.sh`), host PostgreSQL 17 dev container `apex-dev-pg`.

**Spec:** `docs/superpowers/specs/2026-07-07-dev-pg-password-fallback-removal-design.md`

## Global Constraints

- **Host-canonical single-writer over mesh.** Author locally, `scp` per file, commit host-side; ONE writer on the host worktree; never push a stale mirror.
- **Lane branch runs IN the MAIN worktree** `/home/olares/code/apex/apex-power-ops-platform` (branch `secrets/dev-pg-password-fallback-removal`), so the gitignored 0600 caches (`infra/.env`, `infra/infisical/.env.agent`) are present for injection / secret-audit / DB suites. Restore `main` after merge.
- **Value-silent:** assert on precomputed booleans / SENTINELs / name-lists; never echo a secret value or full DSN; classify psql stderr, never dump it.
- **ASCII-only added lines** in code, shell, and docs.
- **shellcheck rc=0** on any edited shell file (`infra/secret-audit.sh` is the only one here); editing it owns making the WHOLE file rc=0.
- **`DEV_PG_PASSWORD` STAYS in `infra/.env`.** The secret-audit `ENV_ALLOWED_KEYS` VALUE is UNCHANGED (comment-only edit); `.managed-secrets` is UNCHANGED; `apex-jobs.sh` already exists and is NOT re-created.
- **The rule:** `APEX_JOBS_PGPASSWORD` = orchestration role password; `APEX_JOBS_DSN` / `ORCH_TEST_DSN` = whole-DSN overrides; `DEV_PG_PASSWORD` = postgres superuser, never an orchestration fallback.
- **Merge governance:** author self-merges after green CI + Codex; squash; NO admin-bypass.

### Mesh command conventions (used throughout)

- `SSH` = `ssh olares-mesh`
- `REPO` = `/home/olares/code/apex/apex-power-ops-platform`
- `PATHX` = `export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH`
- **Edit convention (per file):** author the full new content (or apply exact hunks) to the scratchpad copy, then
  `scp -q "<local>" olares-mesh:REPO/<path>`, then verify + commit host-side with
  `SSH 'cd REPO && LC_ALL=C grep -qP "[^\x00-\x7F]" <path> && { echo NON_ASCII; exit 1; } || true; git add <paths> && git commit -m "..."'`.
- **Injected test run (strict proof):** `SSH 'cd REPO && PATHX && infra/infisical/inject.sh dev -- bash -c "unset DEV_PG_PASSWORD; <cmd>"'`.

---

## Task 1: resolve_dsn dead-fallback removal + contract lock

**Files:**
- Modify: `packages/apex-jobs/src/apex_jobs/db.py` (module docstring + `resolve_dsn`)
- Rewrite: `packages/apex-jobs/tests_unit/test_dsn_resolution.py`

**Interfaces:**
- Produces: `apex_jobs.db.resolve_dsn() -> str` requires `APEX_JOBS_PGPASSWORD` (or `APEX_JOBS_DSN` whole-DSN override); raises `RuntimeError` (value-silent) when neither is set. `DEV_PG_PASSWORD` is ignored entirely.
- Consumes: nothing from other tasks.

- [ ] **Step 1: Rewrite the contract test (RED author).** Write the full new content of `packages/apex-jobs/tests_unit/test_dsn_resolution.py`:

```python
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
```

- [ ] **Step 2: scp the test, run it against CURRENT db.py, verify RED.**

`scp -q "<scratch>/test_dsn_resolution.py" olares-mesh:REPO/packages/apex-jobs/tests_unit/test_dsn_resolution.py`
Run: `SSH 'cd REPO/packages/apex-jobs && PATHX && uv run --extra test pytest tests_unit/test_dsn_resolution.py -v'`
Expected: `test_dev_pg_password_alone_does_not_resolve` **FAILS** (current code returns a DSN with `password=SENTINEL_B`, so `raised=False`, `leaked=True`). The other three PASS.

- [ ] **Step 3: Rewrite `resolve_dsn` (GREEN).** Write the full new content of `packages/apex-jobs/src/apex_jobs/db.py`:

```python
"""DSN resolution + connection helper for apex-jobs.

Defaults to orchestration_dev on the host dev-pg (127.0.0.1:5432) as the
`orchestration` role. Override the database via APEX_JOBS_DB (tests use
orchestration_test) or the whole DSN via APEX_JOBS_DSN. The orchestration role
password is APEX_JOBS_PGPASSWORD, injected from Infisical (dev) -- e.g. via
infra/infisical/apex-jobs.sh; never committed to this PUBLIC repo.
"""
import os

import psycopg
from psycopg.rows import dict_row


def resolve_dsn() -> str:
    dsn = os.environ.get("APEX_JOBS_DSN")
    if dsn:
        return dsn
    db = os.environ.get("APEX_JOBS_DB", "orchestration_dev")
    pw = os.environ.get("APEX_JOBS_PGPASSWORD")
    if not pw:
        raise RuntimeError(
            "set APEX_JOBS_PGPASSWORD before running apex-jobs (or APEX_JOBS_DSN to "
            "override the whole DSN) -- inject it from Infisical, e.g. "
            "`infra/infisical/apex-jobs.sh <verb>`. DEV_PG_PASSWORD is the postgres "
            "superuser password and does NOT authenticate as the orchestration role."
        )
    host = os.environ.get("APEX_JOBS_HOST", "127.0.0.1")
    port = os.environ.get("APEX_JOBS_PORT", "5432")
    user = os.environ.get("APEX_JOBS_USER", "orchestration")
    return f"host={host} port={port} dbname={db} user={user} password={pw} sslmode=disable"


def connect():
    """A dict-row connection (autocommit off; callers manage the transaction)."""
    return psycopg.connect(resolve_dsn(), row_factory=dict_row)
```

- [ ] **Step 4: scp db.py, re-run the contract, verify GREEN.**

`scp -q "<scratch>/db.py" olares-mesh:REPO/packages/apex-jobs/src/apex_jobs/db.py`
Run: `SSH 'cd REPO/packages/apex-jobs && PATHX && uv run --extra test pytest tests_unit/test_dsn_resolution.py -v'`
Expected: **4 passed** (the load-bearing test now passes; the value never leaks).

- [ ] **Step 5: ASCII check + commit.**

Run: `SSH 'cd REPO && for f in packages/apex-jobs/src/apex_jobs/db.py packages/apex-jobs/tests_unit/test_dsn_resolution.py; do LC_ALL=C grep -qP "[^\x00-\x7F]" "$f" && { echo NON_ASCII:$f; exit 1; }; done; echo ASCII_CLEAN; git add packages/apex-jobs/src/apex_jobs/db.py packages/apex-jobs/tests_unit/test_dsn_resolution.py && git commit -q -m "feat(apex-jobs): resolve_dsn requires APEX_JOBS_PGPASSWORD (drop dead DEV_PG_PASSWORD fallback)

DEV_PG_PASSWORD is the postgres superuser password and cannot authenticate as
orchestration; the fallback was dead. resolve_dsn now requires APEX_JOBS_PGPASSWORD
(or APEX_JOBS_DSN) and fails closed. Load-bearing contract test: DEV_PG_PASSWORD
alone must raise and must not leak the sentinel.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'`

---

## Task 2: test-helper fallback removal + cleanup sweep

**Files:**
- Modify: `packages/apex-jobs/tests/conftest.py` (docstring, `PGPW`, `ENV_HINT`)
- Modify: `infra/database/migrations/jobs/_dbtest.py` (docstring, `_password`, `ENV_HINT`)
- Modify: `packages/apex-jobs/tests/test_review_worktree_lock.py` (line 96 synthetic string)

**Interfaces:**
- Consumes: the rule from Task 1 (orchestration password = `APEX_JOBS_PGPASSWORD`).
- Produces: both jobs test suites source the orchestration password from `APEX_JOBS_PGPASSWORD` (or `ORCH_TEST_PGPASSWORD` / `*_DSN` overrides); no `DEV_PG_PASSWORD` read.

- [ ] **Step 1: Rewrite `conftest.py`.** Write the full new content of `packages/apex-jobs/tests/conftest.py` (only the docstring line, `PGPW`, and `ENV_HINT` change vs current; everything else byte-identical):

```python
"""Pytest fixtures: apply the jobs migrations to orchestration_test once per
session; truncate the tables before each test. Host-native psql, no Windows paths.

Credentials come from env only -- no in-code fallback (records-lane convention):
APEX_JOBS_PGPASSWORD, injected from Infisical (dev) e.g. via
infra/infisical/apex-jobs.sh. DEV_PG_PASSWORD is the postgres superuser and does
NOT authenticate as orchestration. The whole suite skips with a clear hint when
the env is absent.

The engine's resolve_dsn() defaults to orchestration_dev, while these fixtures
prep DBNAME (default orchestration_test) -- so the runtime is PINNED below to
the exact fixture target (DB + host + port + user). Without the pin, a run
missing APEX_JOBS_DB writes test jobs into the live dev DB. APEX_JOBS_DSN and
DBNAME=orchestration_dev are refused outright: the fixtures down/up + truncate
their target, which must never be the dev DB or an unvetted foreign DSN."""
import os
import subprocess

import psycopg
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MIG = os.path.join(REPO, "infra", "database", "migrations", "jobs")
PSQL = os.environ.get("PSQL_EXE", "psql")
DBNAME = os.environ.get("APEX_JOBS_DB", "orchestration_test")

if DBNAME == "orchestration_dev":
    pytest.exit(
        "refusing to run the apex-jobs suite against orchestration_dev: the "
        "fixtures down/up the jobs schema and truncate its tables. Use "
        "APEX_JOBS_DB=orchestration_test (or another disposable *_test DB).",
        returncode=4,
    )
if os.environ.get("APEX_JOBS_DSN"):
    pytest.exit(
        "APEX_JOBS_DSN is set, but this suite pins the engine runtime to the "
        "fixture target (host 127.0.0.1:5432, user orchestration, db "
        f"{DBNAME}). Unset APEX_JOBS_DSN; use APEX_JOBS_DB to pick the test DB.",
        returncode=4,
    )

# Pin the engine runtime to the fixture target so app writes can never land in
# a different DB than the one the fixtures prep and truncate.
os.environ["APEX_JOBS_DB"] = DBNAME
os.environ["APEX_JOBS_HOST"] = "127.0.0.1"
os.environ["APEX_JOBS_PORT"] = "5432"
os.environ["APEX_JOBS_USER"] = "orchestration"

PGPW = os.environ.get("APEX_JOBS_PGPASSWORD")
DSN = (
    f"host=127.0.0.1 port=5432 dbname={DBNAME} user=orchestration "
    f"password={PGPW} sslmode=disable"
) if PGPW else None

ENV_HINT = (
    "DB env absent: set APEX_JOBS_PGPASSWORD (inject from Infisical dev, e.g. "
    "infra/infisical/apex-jobs.sh) -- no in-code fallback; DEV_PG_PASSWORD does "
    "not authenticate as orchestration"
)

APPLY = ["001_jobs_enums.sql", "002_jobs_tables.sql", "003_jobs_indexes.sql",
         "004_jobs_views.sql", "005_durability_and_agents.sql"]
DOWN = ["005_durability_and_agents_down.sql", "004_jobs_views_down.sql",
        "003_jobs_indexes_down.sql", "002_jobs_tables_down.sql", "001_jobs_enums_down.sql"]


def _psql(fname):
    env = {**os.environ, "PGPASSWORD": PGPW, "PGSSLMODE": "disable"}
    r = subprocess.run(
        [PSQL, "-h", "127.0.0.1", "-p", "5432", "-U", "orchestration", "-d", DBNAME,
         "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(MIG, fname)],
        env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"psql {fname}: {r.stderr}\n{r.stdout}")


@pytest.fixture(scope="session", autouse=True)
def _schema():
    if not PGPW:
        pytest.skip(ENV_HINT)
    for f in DOWN:
        try:
            _psql(f)
        except Exception:
            pass
    for f in APPLY:
        _psql(f)
    yield


@pytest.fixture
def conn_test():
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute("truncate jobs.gate, jobs.run, jobs.job cascade")
        yield c
```

- [ ] **Step 2: Rewrite `_dbtest.py`.** Write the full new content of `infra/database/migrations/jobs/_dbtest.py` (docstring line 6, `ENV_HINT`, and `_password` change; rest byte-identical):

```python
"""Host-native psycopg3 migration test helper for the jobs domain.
Applies .sql via the host psql over TCP; pins orchestration_test explicitly
because ambient PG env may point elsewhere. No Windows-path assumptions.

Credentials come from env only -- no in-code fallback (records-lane convention):
ORCH_TEST_PGPASSWORD or APEX_JOBS_PGPASSWORD, or ORCH_TEST_DSN as a full override
that drives BOTH the psycopg connection and the psql apply path (parsed via
psycopg.conninfo; a DSN without a password still needs one of the password
vars). The orchestration role password is APEX_JOBS_PGPASSWORD (injected from
Infisical dev); DEV_PG_PASSWORD is the postgres superuser and does NOT
authenticate as orchestration. DB-backed tests skip with a clear hint when the
env is absent. The destructive-target guard (resolved dbname must end in _test)
lives in this directory's conftest.py."""
import os
import subprocess

import psycopg
import pytest
from psycopg import conninfo

HERE = os.path.dirname(os.path.abspath(__file__))
PSQL = os.environ.get("PSQL_EXE", "psql")
DBNAME = os.environ.get("ORCH_TEST_DB", "orchestration_test")

ENV_HINT = (
    "DB env absent: set ORCH_TEST_PGPASSWORD or APEX_JOBS_PGPASSWORD "
    "(inject from Infisical dev) -- no in-code fallback"
)


def _password():
    pw = os.environ.get("ORCH_TEST_PGPASSWORD") or os.environ.get("APEX_JOBS_PGPASSWORD")
    if not pw:
        pytest.skip(ENV_HINT)
    return pw


def _params():
    """One connection target for both paths; ORCH_TEST_DSN wins whole."""
    dsn = os.environ.get("ORCH_TEST_DSN")
    if dsn:
        p = conninfo.conninfo_to_dict(dsn)
        p.setdefault("dbname", DBNAME)
    else:
        p = {"host": "127.0.0.1", "port": "5432", "dbname": DBNAME,
             "user": "orchestration", "sslmode": "disable"}
    if not p.get("password"):
        p["password"] = _password()
    return p


def psql_file(fname):
    p = _params()
    env = {**os.environ, "PGPASSWORD": str(p["password"]),
           "PGSSLMODE": str(p.get("sslmode", "disable"))}
    r = subprocess.run(
        [PSQL, "-h", str(p.get("host", "127.0.0.1")), "-p", str(p.get("port", "5432")),
         "-U", str(p.get("user", "orchestration")), "-d", str(p["dbname"]),
         "-v", "ON_ERROR_STOP=1", "-q", "-f", os.path.join(HERE, fname)],
        env=env, capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"psql {fname} failed (rc={r.returncode}):\n{r.stderr}\n{r.stdout}")


def connect():
    return psycopg.connect(conninfo.make_conninfo(**_params()), autocommit=True)
```

- [ ] **Step 3: Cleanup sweep -- `test_review_worktree_lock.py:96`.** Apply this exact one-line hunk (author full file or targeted edit):

Old:
```python
        raise RuntimeError("APEX_JOBS_PGPASSWORD or DEV_PG_PASSWORD required")
```
New:
```python
        raise RuntimeError("APEX_JOBS_PGPASSWORD required")
```

- [ ] **Step 4: scp the three files.**

```
scp -q "<scratch>/conftest.py" olares-mesh:REPO/packages/apex-jobs/tests/conftest.py
scp -q "<scratch>/_dbtest.py"  olares-mesh:REPO/infra/database/migrations/jobs/_dbtest.py
scp -q "<scratch>/test_review_worktree_lock.py" olares-mesh:REPO/packages/apex-jobs/tests/test_review_worktree_lock.py
```

- [ ] **Step 5: Strict injected proof -- package suite green with DEV_PG_PASSWORD unset in the child.**

Run: `SSH 'cd REPO && PATHX && infra/infisical/inject.sh dev -- bash -c "unset DEV_PG_PASSWORD; cd packages/apex-jobs && APEX_JOBS_DB=orchestration_test PSQL_EXE=psql uv run --extra test pytest -q"' 2>&1 | grep -v -i "release of infisical\|To update, run\|Injecting .* secrets"; echo SUITE_RC=${PIPESTATUS[0]}`
Expected: full package suite passes (0 failed); `SUITE_RC=0`. (Runs migration + engine + lock tests; `test_e6_...` still asserts value-silent wrapping with the updated synthetic string.)

- [ ] **Step 6: Strict injected proof -- jobs migration tests green with DEV_PG_PASSWORD unset in the child.**

Run: `SSH 'cd REPO && PATHX && infra/infisical/inject.sh dev -- bash -c "unset DEV_PG_PASSWORD; cd infra/database/migrations/jobs && uv run --with \"psycopg[binary]\" --with pytest pytest -q"' 2>&1 | grep -v -i "release of infisical\|To update, run\|Injecting .* secrets"; echo MIG_RC=${PIPESTATUS[0]}`
Expected: `test_001_jobs_schema.py` + `test_004_jobs_eligibility.py` + `test_005_durability_schema.py` pass; `MIG_RC=0`. (Proves `_dbtest.py` reaches orchestration_test via injected `APEX_JOBS_PGPASSWORD` with `DEV_PG_PASSWORD` genuinely absent.)

NOTE: run Steps 5 and 6 SEQUENTIALLY (both down/up the shared `orchestration_test` jobs schema).

- [ ] **Step 7: ASCII check + commit.**

Run: `SSH 'cd REPO && for f in packages/apex-jobs/tests/conftest.py infra/database/migrations/jobs/_dbtest.py packages/apex-jobs/tests/test_review_worktree_lock.py; do LC_ALL=C grep -qP "[^\x00-\x7F]" "$f" && { echo NON_ASCII:$f; exit 1; }; done; echo ASCII_CLEAN; git add packages/apex-jobs/tests/conftest.py infra/database/migrations/jobs/_dbtest.py packages/apex-jobs/tests/test_review_worktree_lock.py && git commit -q -m "test(apex-jobs): jobs test helpers require APEX_JOBS_PGPASSWORD (drop DEV_PG_PASSWORD)

conftest.py and _dbtest.py connect as orchestration; DEV_PG_PASSWORD (postgres
superuser) never authenticated there. Source the orchestration password from
APEX_JOBS_PGPASSWORD (with ORCH_TEST_PGPASSWORD/*_DSN overrides). Sweep the stale
synthetic string in test_review_worktree_lock.py to match resolve_dsn message.
Verified green via injection with DEV_PG_PASSWORD unset inside the child.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'`

---

## Task 3: docs / comment sweep + no-regression secret-audit

**Files:**
- Modify: `infra/database/migrations/jobs/MANIFEST.md`
- Modify: `.env.dev.template`
- Modify: `packages/apex-jobs/README.md`
- Modify: `infra/secret-audit.sh` (comment only)
- Modify: `infra/infisical/README.md`

**Interfaces:** none (text only). No behavior change; `secret-audit.sh` allowlist VALUE unchanged.

- [ ] **Step 1: `MANIFEST.md` -- three hunks.**

Hunk A (credential note):
Old:
```
no in-code fallback: source the governed infra/.env first (DEV_PG_PASSWORD),
or set ORCH_TEST_PGPASSWORD / ORCH_TEST_DSN; the tests skip with a hint
```
New:
```
no in-code fallback: set ORCH_TEST_PGPASSWORD or APEX_JOBS_PGPASSWORD (inject
from Infisical dev), or ORCH_TEST_DSN; the tests skip with a hint
```
Hunk B (Run example):
Old:
```
set -a; . ../../../.env; set +a
uv run --with "psycopg[binary]" --with pytest pytest test_001_jobs_schema.py
```
New:
```
../../../infisical/inject.sh dev -- bash -c 'unset DEV_PG_PASSWORD; uv run --with "psycopg[binary]" --with pytest pytest test_001_jobs_schema.py'
```
Hunk C (Apply block):
Old:
```
for f in 001_jobs_enums 002_jobs_tables 003_jobs_indexes 004_jobs_views 005_durability_and_agents; do
  PGPASSWORD=$DEV_PG_PASSWORD psql -h 127.0.0.1 -p 5432 -U orchestration \
    -d orchestration_dev -v ON_ERROR_STOP=1 -f $f.sql
done
```
New:
```
../../../infisical/inject.sh dev -- bash -c 'for f in 001_jobs_enums 002_jobs_tables 003_jobs_indexes 004_jobs_views 005_durability_and_agents; do
  PGPASSWORD=$APEX_JOBS_PGPASSWORD psql -h 127.0.0.1 -p 5432 -U orchestration \
    -d orchestration_dev -v ON_ERROR_STOP=1 -f $f.sql
done'
```

- [ ] **Step 2: `.env.dev.template` -- one hunk.**

Old:
```
# Jobs-lane test credentials come from env only (no in-code fallback).
# Canonical source is the governed, gitignored infra/.env (DEV_PG_PASSWORD);
# lane-scoped overrides documented here, commented on purpose:
```
New:
```
# Jobs-lane test credentials come from env only (no in-code fallback).
# The orchestration-role password is APEX_JOBS_PGPASSWORD, injected from Infisical
# (dev); DEV_PG_PASSWORD is the postgres superuser and does NOT authenticate as
# orchestration. Lane-scoped overrides documented here, commented on purpose:
```

- [ ] **Step 3: `packages/apex-jobs/README.md` -- one hunk (CLI section).**

Old:
```
Infisical-managed and no longer in `infra/.env`; `DEV_PG_PASSWORD` (still cached)
remains the fallback when you source `infra/.env` and run `apex-jobs` directly.
```
New:
```
Infisical-managed and no longer in `infra/.env`; there is no `DEV_PG_PASSWORD`
fallback (it is the postgres superuser password and does not authenticate as the
`orchestration` role).
```

- [ ] **Step 4: `infra/secret-audit.sh` -- comment above the allowlist (VALUE unchanged).**

Insert immediately above the `ENV_ALLOWED_KEYS="${APEX_ENV_ALLOWED_KEYS:-DEV_PG_PASSWORD}"` line:
```bash
# DEV_PG_PASSWORD is intentionally retained in infra/.env and is the sole allowed
# cache key: it is the dev-cluster postgres superuser password that
# compose.dev-lanes.yml uses to initialize the apex-dev-pg container. It is NOT an
# orchestration-role credential (that is APEX_JOBS_PGPASSWORD, injected from
# Infisical) and is NOT a cutover target in the current secret-hygiene lanes.
```
The `ENV_ALLOWED_KEYS=` line itself is byte-unchanged.

- [ ] **Step 5: `infra/infisical/README.md` -- add a note under the `## Files` list.**

Insert after the `- `.env`, `.env.agent` -- gitignored 0600 caches ...` bullet:
```
- `DEV_PG_PASSWORD` is intentionally retained in `infra/.env` (and is the sole
  `secret-audit.sh` `ENV_ALLOWED_KEYS` entry): it is the dev-cluster `postgres`
  superuser that `compose.dev-lanes.yml` uses to initialize the container. It is
  NOT a cutover target -- the orchestration-role password is `APEX_JOBS_PGPASSWORD`.
```

- [ ] **Step 6: scp the five files.**

```
scp -q "<scratch>/MANIFEST.md" olares-mesh:REPO/infra/database/migrations/jobs/MANIFEST.md
scp -q "<scratch>/.env.dev.template" olares-mesh:REPO/.env.dev.template
scp -q "<scratch>/README.md" olares-mesh:REPO/packages/apex-jobs/README.md
scp -q "<scratch>/secret-audit.sh" olares-mesh:REPO/infra/secret-audit.sh
scp -q "<scratch>/infisical-README.md" olares-mesh:REPO/infra/infisical/README.md
```

- [ ] **Step 7: shellcheck the edited shell file (whole-file rc=0).**

Run: `SSH 'cd REPO && shellcheck infra/secret-audit.sh; echo SHELLCHECK_RC=$?'`
Expected: `SHELLCHECK_RC=0` (comment-only change introduces no new findings; the whole file must be clean).

- [ ] **Step 8: No-regression secret-audit (value-silent) + ASCII check.**

Run: `SSH 'cd REPO && bash infra/secret-audit.sh; echo AUDIT_RC=$?' 2>&1 | grep -v -Ei "password|dsn=|=.*[A-Za-z0-9]{12}"`
Expected: identical FAIL set to the pre-lane baseline -- Check 1b flags ONLY the parked keys `SUPABASE_PROD_DSN`, `TCC_BREAKER_RO_PW`, `TCC_BREAKER_CODEX_PW`; `DEV_PG_PASSWORD` still allowed by name; `.managed-secrets` (OPS_API_DSN, OPS_INTAKE_WRITER_DSN, APEX_JOBS_PGPASSWORD) drift-clean. `AUDIT_RC=1` (parked keys keep it non-zero -- this is the unchanged baseline, NOT a regression). The audit prints key NAMES only.
Then: `SSH 'cd REPO && for f in infra/database/migrations/jobs/MANIFEST.md .env.dev.template packages/apex-jobs/README.md infra/secret-audit.sh infra/infisical/README.md; do LC_ALL=C grep -qP "[^\x00-\x7F]" "$f" && { echo NON_ASCII:$f; exit 1; }; done; echo ASCII_CLEAN'`

- [ ] **Step 9: Commit.**

Run: `SSH 'cd REPO && git add infra/database/migrations/jobs/MANIFEST.md .env.dev.template packages/apex-jobs/README.md infra/secret-audit.sh infra/infisical/README.md && git commit -q -m "docs(secrets): reclassify DEV_PG_PASSWORD as superuser/compose-init cache; fix jobs runbooks

Update jobs runbooks/templates so the orchestration-role password is
APEX_JOBS_PGPASSWORD (injected), not DEV_PG_PASSWORD. Document DEV_PG_PASSWORD as
the intentionally-retained postgres superuser / compose-init credential and the
sole secret-audit ENV_ALLOWED_KEYS entry (VALUE unchanged; .managed-secrets
unchanged). Comment-only change to secret-audit.sh (shellcheck rc=0).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"'`

---

## Task 4: focused Codex whole-branch review + finish

**Files:** none (review + merge).

- [ ] **Step 1: Whole-branch Codex review via the front door (through injection).**

Run: `SSH 'cd REPO && PATHX && infra/infisical/apex-jobs.sh review-run --review-head secrets/dev-pg-password-fallback-removal --base-ref main --json' 2>&1 | grep -v -i "release of infisical\|To update, run\|Injecting .* secrets"`
Expected: JSON envelope, `status: succeeded`. Read `.findings`; for any finding, adjudicate (confirm against source, value-silent), fix on the branch, re-run. Fold into the review record.

- [ ] **Step 2: Push the branch.**

Run: `SSH 'cd REPO && git push -u origin secrets/dev-pg-password-fallback-removal'`

- [ ] **Step 3: Open the PR (host `gh`).**

Run: `SSH 'cd REPO && gh pr create --base main --head secrets/dev-pg-password-fallback-removal --title "secrets: remove dead DEV_PG_PASSWORD orchestration fallback (dev)" --body "<summary: rule, verified ground truth, validation results, Codex record>"'`
Wait for CI green.

- [ ] **Step 4: Squash-merge (no admin bypass) after green CI + Codex clean.**

Run: `SSH 'cd REPO && gh pr merge --squash --delete-branch'`
Verify: `SSH 'cd REPO && git fetch -q origin && git log --oneline -1 origin/main'` shows the squash commit.

- [ ] **Step 5: Restore the main worktree to main.**

Run: `SSH 'cd REPO && git checkout main && git pull -q --ff-only && echo "HEAD=$(git rev-parse --short HEAD) BR=$(git branch --show-current) porcelain=$(git status --porcelain | wc -l)"'`
Expected: `BR=main`, `porcelain=0`, HEAD = the new squash commit.

- [ ] **Step 6: Doc reconcile.** Update `/home/olares/code/notes/platform-hygiene-status-and-next-steps.md`, `.remember/remember.md`, and any relevant memory to reflect the merge and the reclassification (DEV_PG_PASSWORD = intentional superuser cache; next hygiene target = TCC_BREAKER_* per the deferred order).

---

## Self-Review (done at authoring)

- **Spec coverage:** db.py drop-fallback (T1) / tests_unit contract incl. load-bearing RED (T1) / conftest + _dbtest -> APEX_JOBS_PGPASSWORD (T2) / cleanup sweep test_review_worktree_lock.py:96 (T2) / KEEP sanitizer battery (untouched, no task -- correct) / MANIFEST + .env.dev.template + README + secret-audit comment + infisical README (T3) / DEV_PG_PASSWORD stays + allowlist value unchanged + .managed-secrets unchanged (T3, Global) / two-tier live proof (T2 strict; launcher `queue` covered by the injected suites) / no-regression audit (T3) / Codex + finish + restore-main (T4). All mapped.
- **Placeholder scan:** none (`<scratch>` and `<summary>` are execution-time substitutions, not content gaps; every code block is complete).
- **Type consistency:** `APEX_JOBS_PGPASSWORD` / `DEV_PG_PASSWORD` / `ORCH_TEST_PGPASSWORD` / `APEX_JOBS_DSN` / `ORCH_TEST_DSN` used consistently; `resolve_dsn`, `_password`, `_params`, `_resolve_with`, `PGPW`, `ENV_HINT` names match across tasks and the current source.
