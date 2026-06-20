# Learning Slice 2a — Capture Path — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the end-to-end mechanism that lets a real tech record the first real learning event — an append-only `learning_events` ledger in `learning_dev`, a `learning-capture` package, write/read API routes, and a capture panel on the Slice 1 demo.

**Architecture:** A write vertical mirroring Slice 1's read vertical (`resolve → API → demo`). A new additive migration lane (`infra/database/migrations/learning/`) adds a person-spine bridge column to `user_profiles` and an append-only `learning_events` table. A `learning-capture` Python package (mirroring `learning-resolver`, but read-WRITE) exposes `record_event` / `list_events` / `list_users`. The existing `control-plane-api` learning router is extended with `POST/GET /events` + `GET /users`. The `operations-web /learning-demo` page gains a capture panel so the resolve→capture loop is one screen.

**Tech Stack:** PostgreSQL 17 (`learning_dev` / throwaway `learning_test` on host `127.0.0.1:5432`), Python 3.11 + `psycopg[binary]>=3.1`, FastAPI (control-plane-api), Next.js (operations-web). All work on the Olares host over mesh SSH (`ssh olares-mesh`).

## Global Constraints

- **All DB writes target `learning_dev` only** (or the throwaway `learning_test` for tests). NO prod writes. NO prod-governance gate.
- **Migration tests run against a THROWAWAY `learning_test`, never `learning_dev`.** `learning_events` FKs reference `public.user_profiles` + `public.study_content`, which a bare test DB lacks → an idempotent `test_prereq.sql` creates minimal stub tables + seed rows first.
- **After tests pass on `learning_test`, apply `001`+`002` to `learning_dev`** (additive/safe) so the API/demo can capture into it. Mirrors the ops pattern (validated on `ops_test`, applied to `ops_dev`).
- **The ledger is append-only:** a DB trigger raises on UPDATE/DELETE; the package issues INSERT/SELECT only.
- **Event-type vocab is exactly these 4 text values** (CHECK, not an enum): `resource_viewed`, `resource_completed`, `assessment_completed`, `self_assessment`.
- **The integration contract is the NETA section** — `neta_section` on an event is the same `records.neta_procedures.section` / `study_content.neta_section_primary` key Slice 1 resolves on.
- **The person-spine bridge column** `public.user_profiles.employee_id` is a cross-DB **contract-FK** to prod `public.employees.id` — app-enforced, **no DB FK** (employees is a separate database). Mirrors `records.persons.employee_ref` / `ops.persons.employee_ref`.
- **control-plane-api = pip + requirements.txt (NOT uv).** Wire the package as `-e ../../packages/learning-capture`. **Do NOT commit any `uv.lock`** (a `uv run` byproduct — `git rm` + `.gitignore` it if it appears).
- **DB password discipline:** `source /home/olares/code/apex/apex-power-ops-platform/infra/.env` to get `DEV_PG_PASSWORD` (UNQUOTED). NEVER `grep|cut` it (the §259 split-brain bug).
- **Host file edits:** write the file locally then `ssh olares-mesh 'cat > <abs-dest>' < <localfile>` (heredocs break on code quotes). **ssh commit messages must avoid apostrophes** (or `git commit -F <file>`).
- **uv on PATH for tests:** `export PATH="$HOME/.local/bin:$PATH"`.
- **Lane:** branch `learning/slice2-capture`, host worktree `/home/olares/code/apex/apex-learning-lane` (off main `82c3b97b`; `infra/.env` is symlinked there already).

---

### Task 0: One-time host setup (throwaway test DB)

**Files:** none (host setup only).

- [ ] **Step 1: Create the throwaway `learning_test` DB (idempotent)**

Run:
```bash
ssh olares-mesh 'source /home/olares/code/apex/apex-power-ops-platform/infra/.env; \
  PGPASSWORD=$DEV_PG_PASSWORD psql -h 127.0.0.1 -p 5432 -U postgres -tAc \
  "select 1 from pg_database where datname='"'"'learning_test'"'"'" | grep -q 1 \
  || PGPASSWORD=$DEV_PG_PASSWORD psql -h 127.0.0.1 -p 5432 -U postgres -c "CREATE DATABASE learning_test;"'
```
Expected: prints `CREATE DATABASE` (first run) or nothing (already exists). This DB is reused across runs; every test tears its objects down via the down-migrations.

---

### Task 1: Migration lane scaffold + `001` person bridge

**Files:**
- Create: `infra/database/migrations/learning/test_prereq.sql`
- Create: `infra/database/migrations/learning/conftest.py`
- Create: `infra/database/migrations/learning/001_person_bridge.sql`
- Create: `infra/database/migrations/learning/001_person_bridge_down.sql`
- Create: `infra/database/migrations/learning/MANIFEST.md`
- Test: `infra/database/migrations/learning/test_001_person_bridge.py`

**Interfaces:**
- Consumes: a `learning_test` DB (Task 0). The test DSN defaults to `dbname=learning_test`.
- Produces: `public.user_profiles.employee_id uuid null` (partial-unique, no DB FK). `test_prereq.sql` + `conftest.py` are reused by Task 2 and Task 3.

- [ ] **Step 1: Write `test_prereq.sql` (idempotent stubs for the throwaway DB)**

```sql
-- Throwaway learning_test bootstrap. Minimal stand-ins for the baseline tables the learning
-- migrations reference (the real learning_dev has the full frozen baseline). Idempotent so it
-- can be applied repeatedly by the migration- and package-test fixtures.
create table if not exists public.user_profiles (
  id    uuid primary key default gen_random_uuid(),
  email text not null default 'seed@example.com'
);
create table if not exists public.study_content (
  id    uuid primary key default gen_random_uuid(),
  title text
);
insert into public.user_profiles (id, email) values
  ('00000000-0000-0000-0000-000000000001', 'tech1@example.com')
  on conflict (id) do nothing;
insert into public.study_content (id, title) values
  ('00000000-0000-0000-0000-000000000010', 'Seed content')
  on conflict (id) do nothing;
```

- [ ] **Step 2: Write `conftest.py` (DSN default + session prereq)**

```python
"""Host-portable defaults + throwaway-DB bootstrap for the learning migration tests.

Runs against a THROWAWAY learning_test (NEVER learning_dev). learning_events FKs reference
public.user_profiles + public.study_content, which a bare test DB lacks -- so this session-scoped
autouse fixture applies test_prereq.sql (idempotent stub tables + seed rows) before any migration.
Create the DB first (Task 0):
  source infra/.env; PGPASSWORD=$DEV_PG_PASSWORD psql -h 127.0.0.1 -U postgres -c "CREATE DATABASE learning_test;"
"""
import os
import pathlib

import psycopg
import pytest

DSN = os.environ.get("LEARNING_TEST_DSN") or (
    "host=127.0.0.1 port=5432 dbname=learning_test user=postgres "
    f"password={os.environ.get('LEARNING_TEST_PGPASSWORD') or os.environ.get('LEARNING_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD', '')} "
    "sslmode=disable"
)
HERE = pathlib.Path(__file__).parent
PREREQ = HERE / "test_prereq.sql"


def _exec_file(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session", autouse=True)
def _prereq():
    _exec_file(PREREQ)
    yield
```

- [ ] **Step 3: Write the failing test `test_001_person_bridge.py`**

```python
"""learning migration 001 -- person bridge (public.user_profiles.employee_id): TDD.

Cross-DB contract-FK to prod public.employees.id (app-enforced, NO db FK -- employees is a
separate database). Mirrors records.persons.employee_ref / ops.persons.employee_ref. Runs against
a THROWAWAY learning_test (conftest applies test_prereq.sql first).

Run (host, from infra/database/migrations/learning/):
  export PATH="$HOME/.local/bin:$PATH"; source ../../../infra/.env
  LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD \
    uv run --with "psycopg[binary]" --with pytest pytest test_001_person_bridge.py -q
"""
import pathlib

import psycopg
import pytest

from conftest import DSN

HERE = pathlib.Path(__file__).parent
UP = HERE / "001_person_bridge.sql"
DOWN = HERE / "001_person_bridge_down.sql"


def _exec_file(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


def _scalar(sql, params=None):
    with psycopg.connect(DSN, autocommit=True) as c:
        row = c.execute(sql, params).fetchone()
        return row[0] if row else None


@pytest.fixture(scope="module", autouse=True)
def migrate():
    _exec_file(DOWN)   # clean slate (user_profiles exists from the prereq fixture)
    _exec_file(UP)
    yield
    _exec_file(DOWN)


def test_employee_id_exists_and_nullable():
    assert _scalar(
        "select is_nullable from information_schema.columns "
        "where table_schema='public' and table_name='user_profiles' and column_name='employee_id'"
    ) == "YES"


def test_employee_id_has_no_db_fk():
    n = _scalar(
        "select count(*) from pg_constraint con "
        "join pg_attribute a on a.attrelid=con.conrelid and a.attnum = any(con.conkey) "
        "where con.conrelid='public.user_profiles'::regclass and con.contype='f' and a.attname='employee_id'"
    )
    assert n == 0


def test_employee_id_partial_unique():
    emp = "11111111-1111-1111-1111-111111111111"
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute("insert into public.user_profiles (employee_id) values (%s::uuid)", (emp,))
        try:
            with pytest.raises(psycopg.errors.UniqueViolation):
                c.execute("insert into public.user_profiles (employee_id) values (%s::uuid)", (emp,))
        finally:
            c.execute("delete from public.user_profiles where employee_id = %s::uuid", (emp,))


def test_two_null_employee_ids_allowed():
    # partial unique (WHERE employee_id IS NOT NULL) -> multiple NULLs are fine.
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute("insert into public.user_profiles (email) values ('a@x.io'), ('b@x.io')")
        c.execute("delete from public.user_profiles where email in ('a@x.io','b@x.io')")
```

- [ ] **Step 4: Run the test, verify it fails**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/infra/database/migrations/learning; source ../../../infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest pytest test_001_person_bridge.py -q'
```
Expected: FAIL — `001_person_bridge.sql` does not exist (the `migrate` fixture errors reading the file), or column not found.

- [ ] **Step 5: Write `001_person_bridge.sql`**

```sql
-- ============================================================================
-- learning migration 001 -- person bridge (public.user_profiles.employee_id).
-- Phase-5 additive identity slice / learning Slice 2a.
-- Authority: docs/superpowers/specs/2026-06-20-learning-slice2-capture-path-design.md;
--            .claude/PLATFORM/INTEGRATION_BACKBONE_IDENTITY_CONTRACT_2026-06-20.md (C1/D2).
-- Dev DB: learning_dev (local PG). Nothing applied to prod. Mirrors the column the prod
-- migration additive_person_spine_prod already added to public.user_profiles -- but here it is
-- a cross-DB CONTRACT-FK to prod public.employees.id (app-enforced, NO db FK: employees lives
-- in a different database).
-- ============================================================================

alter table public.user_profiles
  add column if not exists employee_id uuid null;   -- contract-FK -> prod public.employees.id (NOT a db FK)

create unique index if not exists uq_user_profiles_employee_id
  on public.user_profiles (employee_id) where employee_id is not null;

comment on column public.user_profiles.employee_id is
  'Cross-DB contract-FK to prod public.employees.id; app-enforced, no DB FK (employees is a separate database). Learning Slice 2a.';
```

- [ ] **Step 6: Write `001_person_bridge_down.sql`**

```sql
-- ============================================================================
-- learning migration 001 DOWN -- reverse 001_person_bridge.sql. Drops the bridge column
-- (and its partial-unique index, which the column drop removes). Requires public.user_profiles
-- to exist (the real learning_dev baseline / the test prereq).
-- ============================================================================
drop index if exists public.uq_user_profiles_employee_id;
alter table public.user_profiles drop column if exists employee_id;
```

- [ ] **Step 7: Write `MANIFEST.md`**

```markdown
# learning migrations — manifest

Learning / enablement lane. Dev DB: `learning_dev` (host PG17 `apex-dev-pg`). The baseline content
was loaded from a frozen prod dump (NOT migrations); this lane holds the **additive** Slice 2+ changes.
**Nothing here is applied to prod.** Objects live in the `public` schema (lane isolation = the database,
per separate-DB-per-lane D-ARCH-1).

| # | Up | Down | What | Slice | Status |
|---|---|---|---|---|---|
| 001 | `001_person_bridge.sql` | `001_person_bridge_down.sql` | `public.user_profiles.employee_id` cross-DB contract-FK to prod `public.employees.id` (app-enforced, no DB FK; partial-unique). Mirrors `additive_person_spine_prod`. | 2a | validated on `learning_test` |
| 002 | `002_learning_events.sql` | `002_learning_events_down.sql` | append-only `public.learning_events` capture ledger (event_type CHECK vocab; FKs user CASCADE / study_content SET NULL; `neta_section` work-context; payload jsonb; UPDATE/DELETE-blocking trigger). | 2a | validated on `learning_test` |

## Test harness
`test_prereq.sql` creates minimal stub `user_profiles` + `study_content` (+ seed rows) so the throwaway
`learning_test` carries the tables the FKs reference. `conftest.py` applies it once per session.
Create the DB first: `psql -U postgres -c "CREATE DATABASE learning_test;"`. Run a migration test:
`LEARNING_TEST_PGPASSWORD=<pw> uv run --with "psycopg[binary]" --with pytest pytest test_001_person_bridge.py -q`.

## Conventions
- Each migration ships a reversible `_down`. Validation gate = down → up → invariant tests → down clean.
- After `learning_test` passes, apply to `learning_dev` (additive/safe): `psql -d learning_dev -f <up>.sql`.

## Deferred (later sub-slices)
2b: derive `user_study_progress` / `user_test_attempts` projections + management dashboards · 2c: ROI
correlation (learning_events → records/ops field output via `employee_id` + NETA section).
```

- [ ] **Step 8: Run the test, verify it passes**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/infra/database/migrations/learning; source ../../../infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest pytest test_001_person_bridge.py -q'
```
Expected: PASS (4 passed).

- [ ] **Step 9: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git add infra/database/migrations/learning/ && git commit -F - <<"EOF"
feat(learning): migration lane + 001 person bridge

New infra/database/migrations/learning lane. 001 adds public.user_profiles.employee_id
(cross-DB contract-FK to prod employees; partial-unique, no db FK) -- mirrors the prod
additive person spine into the frozen learning baseline. Validated on throwaway learning_test.
EOF'
```

---

### Task 2: `002` append-only `learning_events` + apply both to `learning_dev`

**Files:**
- Create: `infra/database/migrations/learning/002_learning_events.sql`
- Create: `infra/database/migrations/learning/002_learning_events_down.sql`
- Test: `infra/database/migrations/learning/test_002_learning_events.py`

**Interfaces:**
- Consumes: `test_prereq.sql` (stub `user_profiles` + `study_content`); the seed UUIDs `…0001` (user) and `…0010` (study_content).
- Produces: `public.learning_events` — columns `event_id uuid pk`, `user_id uuid not null`, `event_type text`, `study_content_id uuid null`, `neta_section text null`, `occurred_at timestamptz`, `payload jsonb`, `created_at timestamptz`. Append-only (UPDATE/DELETE blocked). Task 3's package INSERTs/SELECTs these columns.

- [ ] **Step 1: Write the failing test `test_002_learning_events.py`**

```python
"""learning migration 002 -- append-only learning_events ledger: TDD.

Capture substrate for Slice 2a. Immutable (UPDATE/DELETE blocked by a trigger). Runs against the
throwaway learning_test (conftest applies test_prereq.sql -> stub user_profiles + study_content +
seed rows 0001 / 0010).

Run (host, from infra/database/migrations/learning/):
  export PATH="$HOME/.local/bin:$PATH"; source ../../../infra/.env
  LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD \
    uv run --with "psycopg[binary]" --with pytest pytest test_002_learning_events.py -q
"""
import pathlib

import psycopg
import pytest

from conftest import DSN

HERE = pathlib.Path(__file__).parent
UP = HERE / "002_learning_events.sql"
DOWN = HERE / "002_learning_events_down.sql"

USER = "00000000-0000-0000-0000-000000000001"
CONTENT = "00000000-0000-0000-0000-000000000010"


def _exec_file(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


def _scalar(sql, params=None):
    with psycopg.connect(DSN, autocommit=True) as c:
        row = c.execute(sql, params).fetchone()
        return row[0] if row else None


@pytest.fixture(scope="module", autouse=True)
def migrate():
    _exec_file(DOWN)
    _exec_file(UP)
    yield
    _exec_file(DOWN)


@pytest.fixture
def conn():
    with psycopg.connect(DSN, autocommit=True) as c:
        yield c


def _insert(c, etype, content=None, section=None):
    return c.execute(
        "insert into public.learning_events (user_id, event_type, study_content_id, neta_section) "
        "values (%s::uuid, %s, %s, %s) returning event_id",
        (USER, etype, content, section),
    ).fetchone()[0]


def test_table_exists():
    assert _scalar("select to_regclass('public.learning_events') is not null") is True


def test_accepts_the_four_event_types(conn):
    for etype in ("resource_viewed", "resource_completed", "assessment_completed", "self_assessment"):
        eid = _insert(conn, etype)
        assert eid is not None


def test_rejects_unknown_event_type(conn):
    with pytest.raises(psycopg.errors.CheckViolation):
        _insert(conn, "bogus_event")


def test_three_indexes_present():
    n = _scalar(
        "select count(*) from pg_indexes where schemaname='public' and tablename='learning_events' "
        "and indexname in ('ix_learning_events_user_time','ix_learning_events_section','ix_learning_events_type')"
    )
    assert n == 3


def test_append_only_blocks_update(conn):
    eid = _insert(conn, "resource_viewed")
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("update public.learning_events set neta_section='x' where event_id=%s", (eid,))


def test_append_only_blocks_delete(conn):
    eid = _insert(conn, "resource_viewed")
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("delete from public.learning_events where event_id=%s", (eid,))


def test_study_content_fk_set_null_semantics():
    # study_content_id is a real FK with ON DELETE SET NULL; the column is nullable.
    rule = _scalar(
        "select confdeltype from pg_constraint "
        "where conrelid='public.learning_events'::regclass and contype='f' "
        "and conname like '%study_content%'"
    )
    assert rule == "n"  # 'n' = SET NULL


def test_user_fk_cascade_semantics():
    rule = _scalar(
        "select confdeltype from pg_constraint "
        "where conrelid='public.learning_events'::regclass and contype='f' "
        "and conname like '%user_id%'"
    )
    assert rule == "c"  # 'c' = CASCADE
```

- [ ] **Step 2: Run the test, verify it fails**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/infra/database/migrations/learning; source ../../../infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest pytest test_002_learning_events.py -q'
```
Expected: FAIL — `002_learning_events.sql` does not exist.

- [ ] **Step 3: Write `002_learning_events.sql`**

```sql
-- ============================================================================
-- learning migration 002 -- append-only learning_events capture ledger. Slice 2a.
-- Authority: docs/superpowers/specs/2026-06-20-learning-slice2-capture-path-design.md.
-- Dev DB: learning_dev. Nothing applied to prod. The immutable substrate every later projection
-- (user_study_progress / user_test_attempts) and ROI metric derives from. event_type is a text
-- CHECK vocab (extensible, per the records-lane preference); payload jsonb is the open extension
-- point (score_percent, duration_seconds, source surface, apparatus_type, ...).
-- ============================================================================

create table if not exists public.learning_events (
  event_id         uuid        primary key default gen_random_uuid(),
  user_id          uuid        not null references public.user_profiles(id) on delete cascade,
  event_type       text        not null,
  study_content_id uuid        null references public.study_content(id) on delete set null,
  neta_section     text        null,
  occurred_at      timestamptz not null default now(),
  payload          jsonb       not null default '{}'::jsonb,
  created_at       timestamptz not null default now(),
  constraint learning_events_event_type_check check (event_type in
    ('resource_viewed', 'resource_completed', 'assessment_completed', 'self_assessment'))
);

create index if not exists ix_learning_events_user_time on public.learning_events (user_id, occurred_at);
create index if not exists ix_learning_events_section   on public.learning_events (neta_section);
create index if not exists ix_learning_events_type      on public.learning_events (event_type);

comment on table public.learning_events is
  'Append-only learning capture ledger (Slice 2a). Immutable: UPDATE/DELETE blocked by a trigger. '
  'neta_section is the cross-lane work-context contract; payload jsonb is the open extension point.';

-- append-only guard: the ledger is immutable.
create or replace function public.learning_events_block_mutation() returns trigger
  language plpgsql as $fn$
begin
  raise exception 'learning_events is append-only (% blocked)', tg_op;
end;
$fn$;

drop trigger if exists trg_learning_events_append_only on public.learning_events;
create trigger trg_learning_events_append_only
  before update or delete on public.learning_events
  for each row execute function public.learning_events_block_mutation();
```

- [ ] **Step 4: Write `002_learning_events_down.sql`**

```sql
-- ============================================================================
-- learning migration 002 DOWN -- reverse 002_learning_events.sql. Drop the table (its trigger
-- and indexes go with it), then the guard function. Explicit order; idempotent.
-- ============================================================================
drop table if exists public.learning_events;
drop function if exists public.learning_events_block_mutation();
```

- [ ] **Step 5: Run the test, verify it passes**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/infra/database/migrations/learning; source ../../../infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest pytest test_002_learning_events.py -q'
```
Expected: PASS (8 passed).

- [ ] **Step 6: Apply `001` + `002` to `learning_dev` (additive/safe) and verify**

Run:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane; source infra/.env; export PGPASSWORD=$DEV_PG_PASSWORD; \
  psql -h 127.0.0.1 -U postgres -d learning_dev -f infra/database/migrations/learning/001_person_bridge.sql; \
  psql -h 127.0.0.1 -U postgres -d learning_dev -f infra/database/migrations/learning/002_learning_events.sql; \
  psql -h 127.0.0.1 -U postgres -d learning_dev -c "select column_name from information_schema.columns where table_name='"'"'user_profiles'"'"' and column_name='"'"'employee_id'"'"'"; \
  psql -h 127.0.0.1 -U postgres -d learning_dev -c "select to_regclass('"'"'public.learning_events'"'"')"'
```
Expected: `ALTER TABLE` / `CREATE TABLE` etc.; the verification queries print `employee_id` and `public.learning_events`. (Re-running is safe — both migrations are idempotent.)

- [ ] **Step 7: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git add infra/database/migrations/learning/ && git commit -F - <<"EOF"
feat(learning): 002 append-only learning_events ledger

Immutable capture substrate (UPDATE/DELETE blocked by trigger; event_type CHECK vocab;
user CASCADE / study_content SET NULL FKs; neta_section work-context; payload jsonb).
Validated on learning_test (8/8); 001+002 applied to learning_dev (additive).
EOF'
```

---

### Task 3: `packages/learning-capture` (record/list events + users + CLI)

**Files:**
- Create: `packages/learning-capture/pyproject.toml`
- Create: `packages/learning-capture/src/learning_capture/__init__.py`
- Create: `packages/learning-capture/src/learning_capture/db.py`
- Create: `packages/learning-capture/src/learning_capture/models.py`
- Create: `packages/learning-capture/src/learning_capture/capture.py`
- Create: `packages/learning-capture/src/learning_capture/cli.py`
- Create: `packages/learning-capture/tests/conftest.py`
- Create: `packages/learning-capture/tests/test_capture.py`
- Create: `packages/learning-capture/tests/test_cli.py`

**Interfaces:**
- Consumes: the migrated `learning_test` schema (Task 1+2 SQL files, applied by the package conftest); seed UUIDs `…0001` (user) / `…0010` (study_content).
- Produces:
  - `record_event(user_id: str, event_type: str, *, study_content_id: str | None = None, neta_section: str | None = None, payload: dict | None = None) -> CapturedEvent`
  - `list_events(user_id: str | None = None, limit: int = 50) -> list[CapturedEvent]`
  - `list_users(limit: int = 100) -> list[dict]` (`{"id": str, "email": str}`)
  - `CapturedEvent` dataclass: `event_id, user_id, event_type, study_content_id, neta_section, occurred_at, payload, created_at`
  - `CaptureError(ValueError)`
  - `EVENT_TYPES: frozenset[str]`
  Task 4's API imports `record_event`, `list_events`, `list_users`, `CaptureError`.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "learning-capture"
version = "0.1.0"
description = "Learning capture path (learning Slice 2a; writes the learning_dev learning_events ledger)"
requires-python = ">=3.11"
dependencies = ["psycopg[binary]>=3.1"]

[project.optional-dependencies]
test = ["pytest>=8.0.0"]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[project.scripts]
learning-capture = "learning_capture.cli:main"
```

- [ ] **Step 2: Write `db.py` (read-WRITE connect)**

```python
"""learning_dev connection (read-WRITE) for the capture path. DSN pinned so ambient PG env
(which points at prod) cannot redirect us -- mirrors learning-resolver/ops-intake, but withOUT the
read-only session: capture writes."""
import os

import psycopg


def dsn() -> str:
    return os.environ.get("LEARNING_DEV_DSN") or (
        "host=127.0.0.1 port=5432 dbname=learning_dev user=postgres "
        f"password={os.environ.get('LEARNING_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD', '')} "
        "sslmode=disable"
    )


def connect() -> "psycopg.Connection":
    # autocommit: each INSERT commits immediately; no idle transaction.
    return psycopg.connect(dsn(), autocommit=True)
```

- [ ] **Step 3: Write `models.py`**

```python
from dataclasses import dataclass
from datetime import datetime

EVENT_TYPES = frozenset(
    {"resource_viewed", "resource_completed", "assessment_completed", "self_assessment"}
)


@dataclass
class CapturedEvent:
    event_id: str
    user_id: str
    event_type: str
    study_content_id: str | None
    neta_section: str | None
    occurred_at: datetime
    payload: dict
    created_at: datetime
```

- [ ] **Step 4: Write the package test conftest (`tests/conftest.py`)**

```python
"""Apply the learning migrations to a throwaway learning_test, then point the package at it.

The package reads LEARNING_DEV_DSN; tests override it to learning_test so capture writes never
touch learning_dev. We apply test_prereq.sql + 001 + 002 (idempotent) from the migrations lane so
the package's required schema is present without duplicating DDL.
"""
import os
import pathlib

import psycopg
import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]          # tests -> learning-capture -> packages -> repo root
MIG = REPO / "infra" / "database" / "migrations" / "learning"

_PW = os.environ.get("LEARNING_TEST_PGPASSWORD") or os.environ.get("LEARNING_DEV_PGPASSWORD") or os.environ.get("PGPASSWORD", "")
TEST_DSN = os.environ.get("LEARNING_TEST_DSN") or (
    f"host=127.0.0.1 port=5432 dbname=learning_test user=postgres password={_PW} sslmode=disable"
)
# The package's db.connect() reads LEARNING_DEV_DSN -- pin it to learning_test for the whole run.
os.environ["LEARNING_DEV_DSN"] = TEST_DSN

USER = "00000000-0000-0000-0000-000000000001"
CONTENT = "00000000-0000-0000-0000-000000000010"


def _exec_file(path):
    with psycopg.connect(TEST_DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session", autouse=True)
def _schema():
    _exec_file(MIG / "test_prereq.sql")
    _exec_file(MIG / "002_learning_events_down.sql")   # clean slate
    _exec_file(MIG / "001_person_bridge_down.sql")
    _exec_file(MIG / "001_person_bridge.sql")
    _exec_file(MIG / "002_learning_events.sql")
    yield
    _exec_file(MIG / "002_learning_events_down.sql")
```

- [ ] **Step 5: Write the failing test `tests/test_capture.py`**

```python
import psycopg
import pytest

from learning_capture import CaptureError, list_events, list_users, record_event
from learning_capture.models import CapturedEvent
from tests.conftest import CONTENT, USER


def test_record_event_returns_captured_event():
    ev = record_event(USER, "resource_viewed", study_content_id=CONTENT, neta_section="7.2.1.1")
    assert isinstance(ev, CapturedEvent)
    assert ev.event_id
    assert ev.user_id == USER
    assert ev.event_type == "resource_viewed"
    assert ev.study_content_id == CONTENT
    assert ev.neta_section == "7.2.1.1"


def test_record_event_assessment_payload_roundtrips():
    ev = record_event(USER, "assessment_completed", payload={"score_percent": 80, "correct": 8})
    assert ev.payload["score_percent"] == 80
    assert ev.payload["correct"] == 8


def test_record_event_rejects_unknown_type():
    with pytest.raises(CaptureError):
        record_event(USER, "bogus")


def test_record_event_rejects_unknown_user():
    with pytest.raises(CaptureError):
        record_event("22222222-2222-2222-2222-222222222222", "resource_viewed")


def test_record_event_rejects_unknown_content():
    with pytest.raises(CaptureError):
        record_event(USER, "resource_viewed", study_content_id="33333333-3333-3333-3333-333333333333")


def test_list_events_filters_by_user_and_orders_desc():
    record_event(USER, "resource_viewed")
    record_event(USER, "resource_completed")
    rows = list_events(user_id=USER, limit=2)
    assert len(rows) == 2
    assert rows[0].occurred_at >= rows[1].occurred_at


def test_list_users_returns_seed_user():
    users = list_users()
    assert any(u["id"] == USER for u in users)
```

- [ ] **Step 6: Run the test, verify it fails**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/packages/learning-capture; source ../../infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests/test_capture.py -q'
```
Expected: FAIL — `capture.py` has no `record_event` (ImportError).

- [ ] **Step 7: Write `capture.py`**

```python
"""Capture path: append events to the learning_dev learning_events ledger. INSERT/SELECT only
(the DB trigger backs the append-only invariant)."""
from psycopg.types.json import Json

from .db import connect
from .models import EVENT_TYPES, CapturedEvent

_COLS = ("event_id", "user_id", "event_type", "study_content_id",
         "neta_section", "occurred_at", "payload", "created_at")

_INSERT = (
    "insert into learning_events (user_id, event_type, study_content_id, neta_section, payload) "
    "values (%(user_id)s::uuid, %(event_type)s, %(study_content_id)s::uuid, %(neta_section)s, %(payload)s) "
    "returning " + ", ".join(_COLS)
)


class CaptureError(ValueError):
    """Invalid capture request (unknown event_type / missing referenced row)."""


def _row_to_event(r) -> CapturedEvent:
    (event_id, user_id, event_type, study_content_id, neta_section, occurred_at, payload, created_at) = r
    return CapturedEvent(
        event_id=str(event_id),
        user_id=str(user_id),
        event_type=event_type,
        study_content_id=str(study_content_id) if study_content_id is not None else None,
        neta_section=neta_section,
        occurred_at=occurred_at,
        payload=payload or {},
        created_at=created_at,
    )


def record_event(user_id, event_type, *, study_content_id=None, neta_section=None, payload=None) -> CapturedEvent:
    if event_type not in EVENT_TYPES:
        raise CaptureError(f"unknown event_type {event_type!r}; allowed: {sorted(EVENT_TYPES)}")
    with connect() as conn:
        if conn.execute("select 1 from user_profiles where id = %s::uuid", (user_id,)).fetchone() is None:
            raise CaptureError(f"no such user_profiles.id {user_id!r}")
        if study_content_id is not None and \
                conn.execute("select 1 from study_content where id = %s::uuid", (study_content_id,)).fetchone() is None:
            raise CaptureError(f"no such study_content.id {study_content_id!r}")
        row = conn.execute(_INSERT, {
            "user_id": user_id,
            "event_type": event_type,
            "study_content_id": study_content_id,
            "neta_section": neta_section,
            "payload": Json(payload or {}),
        }).fetchone()
    return _row_to_event(row)


def list_events(user_id=None, limit=50) -> list[CapturedEvent]:
    sql = "select " + ", ".join(_COLS) + " from learning_events "
    with connect() as conn:
        if user_id is not None:
            rows = conn.execute(
                sql + "where user_id = %s::uuid order by occurred_at desc, event_id limit %s",
                (user_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(sql + "order by occurred_at desc, event_id limit %s", (limit,)).fetchall()
    return [_row_to_event(r) for r in rows]


def list_users(limit=100) -> list[dict]:
    with connect() as conn:
        rows = conn.execute("select id, email from user_profiles order by email limit %s", (limit,)).fetchall()
    return [{"id": str(i), "email": e} for i, e in rows]
```

- [ ] **Step 8: Write `__init__.py`**

```python
from .capture import CaptureError, list_events, list_users, record_event
from .models import EVENT_TYPES, CapturedEvent

__all__ = [
    "record_event", "list_events", "list_users",
    "CaptureError", "CapturedEvent", "EVENT_TYPES",
]
```

- [ ] **Step 9: Run the test, verify it passes**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/packages/learning-capture; source ../../infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests/test_capture.py -q'
```
Expected: PASS (7 passed).

- [ ] **Step 10: Write the failing CLI test `tests/test_cli.py`**

```python
import json

from learning_capture.cli import main
from tests.conftest import USER


def test_cli_record_prints_event_id(capsys):
    rc = main(["record", "--user", USER, "--type", "resource_viewed", "--section", "7.2.1.1"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "event_id" in out


def test_cli_list_json(capsys):
    main(["record", "--user", USER, "--type", "resource_completed"])
    rc = main(["list", "--user", USER, "--limit", "5", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert isinstance(data, list)
    assert all("event_type" in r for r in data)
```

- [ ] **Step 11: Run the CLI test, verify it fails**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/packages/learning-capture; source ../../infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests/test_cli.py -q'
```
Expected: FAIL — `cli.py` has no `main` (ImportError).

- [ ] **Step 12: Write `cli.py`**

```python
import argparse
import dataclasses
import json
import sys

from .capture import list_events, record_event


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="learning-capture",
                                 description="Record / list learning capture events (learning_dev)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("record", help="append a learning event")
    rec.add_argument("--user", required=True)
    rec.add_argument("--type", required=True, dest="event_type")
    rec.add_argument("--content", default=None, dest="study_content_id")
    rec.add_argument("--section", default=None, dest="neta_section")
    rec.add_argument("--payload", default=None, help="JSON object string")

    lst = sub.add_parser("list", help="list recent events")
    lst.add_argument("--user", default=None)
    lst.add_argument("--limit", type=int, default=50)
    lst.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)

    if args.cmd == "record":
        payload = json.loads(args.payload) if args.payload else None
        ev = record_event(args.user, args.event_type, study_content_id=args.study_content_id,
                          neta_section=args.neta_section, payload=payload)
        print(json.dumps({"event_id": ev.event_id, "event_type": ev.event_type}, ensure_ascii=False))
        return 0
    if args.cmd == "list":
        rows = list_events(user_id=args.user, limit=args.limit)
        dicts = [dataclasses.asdict(r) for r in rows]
        if args.json:
            print(json.dumps(dicts, ensure_ascii=False, default=str))
        else:
            for r in rows:
                print(f"{r.occurred_at}  {r.event_type:>20}  {r.neta_section or '-'}  {r.event_id}")
        return 0
    return 1
```

- [ ] **Step 13: Run the full package suite, verify it passes**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/packages/learning-capture; source ../../infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests -q'
```
Expected: PASS (9 passed: 7 capture + 2 cli).

- [ ] **Step 14: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git add packages/learning-capture/ && git commit -F - <<"EOF"
feat(learning): learning-capture package (record/list events + users + CLI)

record_event/list_events/list_users over the learning_dev learning_events ledger; read-WRITE db
connect (mirrors learning-resolver without the read-only session); validates event_type vocab and
referenced user/content; INSERT/SELECT only. CLI record/list. 9 tests against throwaway learning_test.
EOF'
```

---

### Task 4: control-plane-api — `POST/GET /events` + `GET /users`

**Files:**
- Modify: `apps/control-plane-api/services/learning/router.py`
- Modify: `apps/control-plane-api/services/learning/schemas.py`
- Modify: `apps/control-plane-api/requirements.txt`
- Test: `apps/control-plane-api/tests/test_learning_events.py`

**Interfaces:**
- Consumes: `learning_capture.record_event / list_events / list_users / CaptureError`.
- Produces:
  - `POST /api/v1/learning/events` body `{user_id, event_type, study_content_id?, neta_section?, payload?}` → `201 {event}`; `400` on `CaptureError`.
  - `GET /api/v1/learning/events?user_id=&limit=` → `{events: [...]}`.
  - `GET /api/v1/learning/users?limit=` → `{users: [{id, email}]}`.
  The existing `learning_router` is already registered in `main.py` (line 97) — extending it needs NO `main.py` change.

- [ ] **Step 1: Add the editable dep to `requirements.txt`**

Add a line directly under the existing `-e ../../packages/learning-resolver` so the block reads:
```
-e ../../packages/calc-engine
-e ../../packages/learning-resolver
-e ../../packages/learning-capture
```

- [ ] **Step 2: Install the editable package into the host `.venv`**

Run:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && .venv/bin/pip install -e packages/learning-capture 2>&1 | tail -3 || /home/olares/code/apex/apex-power-ops-platform/.venv/bin/pip install -e packages/learning-capture 2>&1 | tail -3'
```
Expected: `Successfully installed learning-capture-0.1.0`. (Note: the worktree may not have its own `.venv`; if `.venv` is missing, use the platform-root `.venv` shown in the fallback. Whichever venv runs the API tests must have the package installed.)

- [ ] **Step 3: Write the failing test `tests/test_learning_events.py`**

```python
"""control-plane-api learning capture routes (Slice 2a). The route layer calls the
learning-capture package, which writes the learning_test DB (LEARNING_DEV_DSN is pinned to
learning_test by the run command). A valid DATABASE_URL must be importable for config.py.
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

USER = "00000000-0000-0000-0000-000000000001"
CONTENT = "00000000-0000-0000-0000-000000000010"


def test_post_event_returns_201():
    r = client.post("/api/v1/learning/events", json={
        "user_id": USER, "event_type": "resource_viewed",
        "study_content_id": CONTENT, "neta_section": "7.2.1.1",
    })
    assert r.status_code == 201
    body = r.json()["event"]
    assert body["event_type"] == "resource_viewed"
    assert body["user_id"] == USER


def test_post_event_bad_type_is_400():
    r = client.post("/api/v1/learning/events", json={"user_id": USER, "event_type": "bogus"})
    assert r.status_code == 400


def test_post_event_unknown_user_is_400():
    r = client.post("/api/v1/learning/events",
                    json={"user_id": "22222222-2222-2222-2222-222222222222", "event_type": "resource_viewed"})
    assert r.status_code == 400


def test_get_events_reads_back():
    client.post("/api/v1/learning/events", json={"user_id": USER, "event_type": "resource_completed"})
    r = client.get("/api/v1/learning/events", params={"user_id": USER, "limit": 10})
    assert r.status_code == 200
    events = r.json()["events"]
    assert len(events) >= 1
    assert {"event_id", "event_type", "user_id"} <= set(events[0].keys())


def test_get_users_lists_seed_user():
    r = client.get("/api/v1/learning/users")
    assert r.status_code == 200
    assert any(u["id"] == USER for u in r.json()["users"])
```

- [ ] **Step 4: Run the test, verify it fails**

Run (bootstrap `learning_test` schema first, then the test):
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane; source infra/.env; export PGPASSWORD=$DEV_PG_PASSWORD; \
  M=infra/database/migrations/learning; \
  for f in test_prereq.sql 002_learning_events_down.sql 001_person_bridge_down.sql 001_person_bridge.sql 002_learning_events.sql; do psql -h 127.0.0.1 -U postgres -d learning_test -f $M/$f >/dev/null 2>&1; done; \
  VENV=$( [ -x .venv/bin/python ] && echo .venv || echo /home/olares/code/apex/apex-power-ops-platform/.venv ); \
  cd apps/control-plane-api; \
  DATABASE_URL="postgresql://postgres:$DEV_PG_PASSWORD@127.0.0.1:5432/learning_test" \
  LEARNING_DEV_DSN="host=127.0.0.1 port=5432 dbname=learning_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable" \
    ../../$VENV/bin/python -m pytest tests/test_learning_events.py -q'
```
Expected: FAIL — `POST /events` returns 404/405 (route not defined yet).

- [ ] **Step 5: Extend `schemas.py`**

Append to `apps/control-plane-api/services/learning/schemas.py`:
```python
class EventIn(BaseModel):
    user_id: str
    event_type: str
    study_content_id: str | None = None
    neta_section: str | None = None
    payload: dict = {}


class EventOut(BaseModel):
    event_id: str
    user_id: str
    event_type: str
    study_content_id: str | None = None
    neta_section: str | None = None
    occurred_at: datetime
    payload: dict
    created_at: datetime


class EventCreatedResponse(BaseModel):
    event: EventOut


class EventsResponse(BaseModel):
    events: list[EventOut]


class UsersResponse(BaseModel):
    users: list[dict]
```
And add the import at the top of `schemas.py` (it currently imports only `from pydantic import BaseModel`):
```python
from datetime import datetime

from pydantic import BaseModel
```

- [ ] **Step 6: Extend `router.py`**

Append to `apps/control-plane-api/services/learning/router.py` (the file already defines `router` and imports from `.schemas`):
```python
from fastapi import HTTPException, status

from learning_capture import CaptureError, list_events, list_users, record_event

from .schemas import EventCreatedResponse, EventIn, EventOut, EventsResponse, UsersResponse


@router.post("/events", response_model=EventCreatedResponse, status_code=status.HTTP_201_CREATED)
def post_event(body: EventIn) -> EventCreatedResponse:
    try:
        ev = record_event(
            body.user_id, body.event_type,
            study_content_id=body.study_content_id,
            neta_section=body.neta_section,
            payload=body.payload,
        )
    except CaptureError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return EventCreatedResponse(event=EventOut(**vars(ev)))


@router.get("/events", response_model=EventsResponse)
def get_events(
    user_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> EventsResponse:
    rows = list_events(user_id=user_id, limit=limit)
    return EventsResponse(events=[EventOut(**vars(r)) for r in rows])


@router.get("/users", response_model=UsersResponse)
def get_users(limit: int = Query(default=100, ge=1, le=500)) -> UsersResponse:
    return UsersResponse(users=list_users(limit=limit))
```
Note: `Query` is already imported in `router.py` (Slice 1's `from fastapi import APIRouter, Query`). Add `HTTPException, status` to that import or use the separate import line shown above — either is fine; do not duplicate `Query`.

- [ ] **Step 7: Run the test, verify it passes**

Run (same env as Step 4):
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane; source infra/.env; export PGPASSWORD=$DEV_PG_PASSWORD; \
  VENV=$( [ -x .venv/bin/python ] && echo .venv || echo /home/olares/code/apex/apex-power-ops-platform/.venv ); \
  cd apps/control-plane-api; \
  DATABASE_URL="postgresql://postgres:$DEV_PG_PASSWORD@127.0.0.1:5432/learning_test" \
  LEARNING_DEV_DSN="host=127.0.0.1 port=5432 dbname=learning_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable" \
    ../../$VENV/bin/python -m pytest tests/test_learning_events.py -q'
```
Expected: PASS (5 passed).

- [ ] **Step 8: Confirm Slice 1 learning tests still pass (no regression)**

Run:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane; source infra/.env; export PGPASSWORD=$DEV_PG_PASSWORD; \
  VENV=$( [ -x .venv/bin/python ] && echo .venv || echo /home/olares/code/apex/apex-power-ops-platform/.venv ); \
  cd apps/control-plane-api; \
  DATABASE_URL="postgresql://postgres:$DEV_PG_PASSWORD@127.0.0.1:5432/learning_dev" \
  LEARNING_DEV_PGPASSWORD=$DEV_PG_PASSWORD \
    ../../$VENV/bin/python -m pytest tests/test_learning_resources.py -q'
```
Expected: PASS (3 passed) — Slice 1 reads real `learning_dev` (curated `7.2.1.1`), unaffected by the capture routes.

- [ ] **Step 9: Verify no `uv.lock` got created; commit**

Run:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git status --porcelain | grep -i "uv.lock" && echo "REMOVE THESE" || echo "clean of uv.lock"'
```
If any `uv.lock` appears, `git rm --cached` it and add to `.gitignore`. Then:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git add apps/control-plane-api/services/learning/router.py apps/control-plane-api/services/learning/schemas.py apps/control-plane-api/requirements.txt apps/control-plane-api/tests/test_learning_events.py && git commit -F - <<"EOF"
feat(learning): control-plane-api capture routes (events + users)

POST /api/v1/learning/events (201; 400 on CaptureError) + GET /events (read-back) + GET /users,
extending the Slice 1 learning router. Calls the learning-capture package (editable dep via
requirements.txt, mirroring learning-resolver). 5 route tests against learning_test; Slice 1
resource tests still green.
EOF'
```

---

### Task 5: operations-web — capture panel on `/learning-demo`

**Files:**
- Create: `apps/operations-web/lib/learning-capture.ts`
- Modify: `apps/operations-web/app/learning-demo/page.tsx`
- Test: `apps/operations-web/e2e/learning-capture.spec.ts` (thin smoke)

**Interfaces:**
- Consumes: `POST/GET /api/v1/learning/events` + `GET /api/v1/learning/users` (Task 4); `browserEnv.controlPlaneBaseUrl`.
- Produces: a capture panel where the user is picked from `/users`, a resolver-surfaced resource is marked viewed/completed (or an assessment/self-assessment recorded), and the captured-events list refreshes.

- [ ] **Step 1: Write `lib/learning-capture.ts`**

```ts
import { browserEnv } from './browser-env'

export type LearningUser = { id: string; email: string }

export type LearningEvent = {
  event_id: string
  user_id: string
  event_type: string
  study_content_id: string | null
  neta_section: string | null
  occurred_at: string
  payload: Record<string, unknown>
  created_at: string
}

export class LearningCaptureError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'LearningCaptureError'
    this.status = status
  }
}

const base = () => browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')

async function parse(response: Response) {
  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }
  if (!response.ok) {
    const detail =
      typeof payload === 'object' && payload !== null
        ? ((payload as { detail?: unknown }).detail as string | undefined) ?? null
        : null
    throw new LearningCaptureError(detail ?? `Request failed with status ${response.status}`, response.status)
  }
  return payload
}

export async function fetchLearningUsers(limit = 100): Promise<LearningUser[]> {
  const r = await fetch(`${base()}/api/v1/learning/users?limit=${limit}`, { headers: { Accept: 'application/json' } })
  return ((await parse(r)) as { users: LearningUser[] }).users
}

export async function fetchLearningEvents(userId: string, limit = 20): Promise<LearningEvent[]> {
  const params = new URLSearchParams({ user_id: userId, limit: String(limit) })
  const r = await fetch(`${base()}/api/v1/learning/events?${params.toString()}`, { headers: { Accept: 'application/json' } })
  return ((await parse(r)) as { events: LearningEvent[] }).events
}

export async function recordLearningEvent(input: {
  user_id: string
  event_type: string
  study_content_id?: string | null
  neta_section?: string | null
  payload?: Record<string, unknown>
}): Promise<LearningEvent> {
  const r = await fetch(`${base()}/api/v1/learning/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(input),
  })
  return ((await parse(r)) as { event: LearningEvent }).event
}
```

- [ ] **Step 2: Extend `app/learning-demo/page.tsx` with a capture panel**

Replace the file with the version below (keeps the Slice 1 resolve panel intact; adds users load, a per-resource "Viewed / Completed" capture, a self-assessment button, and a captured-events list). Reuses the existing `resource-*` / `notes-card` / `btn` classes.

```tsx
'use client'

import { useEffect, useState } from 'react'
import { fetchLearningResources, LearningResource, LearningResourcesError } from '../../lib/learning-resources'
import {
  fetchLearningEvents,
  fetchLearningUsers,
  LearningCaptureError,
  LearningEvent,
  LearningUser,
  recordLearningEvent,
} from '../../lib/learning-capture'

export default function LearningDemoPage() {
  const [section, setSection] = useState('7.2.1.1')
  const [level, setLevel] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [resources, setResources] = useState<LearningResource[] | null>(null)

  const [users, setUsers] = useState<LearningUser[]>([])
  const [userId, setUserId] = useState('')
  const [events, setEvents] = useState<LearningEvent[]>([])
  const [captureMessage, setCaptureMessage] = useState<string | null>(null)

  useEffect(() => {
    fetchLearningUsers()
      .then((u) => {
        setUsers(u)
        if (u.length && !userId) setUserId(u[0].id)
      })
      .catch(() => setUsers([]))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function refreshEvents(uid: string) {
    if (!uid) return
    try {
      setEvents(await fetchLearningEvents(uid, 20))
    } catch {
      setEvents([])
    }
  }

  useEffect(() => {
    refreshEvents(userId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId])

  async function run() {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const data = await fetchLearningResources(section.trim(), level || undefined, 20)
      setResources(data.resources)
    } catch (error) {
      setErrorMessage(
        error instanceof LearningResourcesError ? error.message : 'The learning resolver could not be reached.',
      )
      setResources([])
    } finally {
      setIsLoading(false)
    }
  }

  async function capture(eventType: string, r?: LearningResource) {
    if (!userId) {
      setCaptureMessage('Pick a technician first.')
      return
    }
    setCaptureMessage(null)
    const ref = r?.reference as { kind?: string; id?: string } | undefined
    try {
      await recordLearningEvent({
        user_id: userId,
        event_type: eventType,
        study_content_id: ref?.kind === 'study_content' ? ref.id ?? null : null,
        neta_section: section.trim() || null,
      })
      setCaptureMessage(`Recorded ${eventType}.`)
      await refreshEvents(userId)
    } catch (error) {
      setCaptureMessage(
        error instanceof LearningCaptureError ? error.message : 'Capture failed.',
      )
    }
  }

  return (
    <main className="shell-page">
      <section className="hero-card">
        <p className="eyebrow">Learning &rarr; Slice 2 capture</p>
        <h1>Surface resources, then capture engagement.</h1>
      </section>

      <section className="notes-card">
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <label>NETA section
            <input value={section} onChange={(e) => setSection(e.target.value)} placeholder="7.6.1.1.1" />
          </label>
          <label>Level
            <select value={level} onChange={(e) => setLevel(e.target.value)}>
              <option value="">Any</option>
              <option value="II">II</option>
              <option value="III">III</option>
              <option value="IV">IV</option>
            </select>
          </label>
          <label>Technician
            <select value={userId} onChange={(e) => setUserId(e.target.value)}>
              {users.length === 0 ? <option value="">(no users)</option> : null}
              {users.map((u) => (
                <option key={u.id} value={u.id}>{u.email}</option>
              ))}
            </select>
          </label>
          <button className="btn" onClick={run} disabled={isLoading}>Resolve</button>
        </div>

        {captureMessage ? <p className="resource-banner resource-banner-neutral">{captureMessage}</p> : null}
        {isLoading ? <p className="resource-banner resource-banner-neutral">Resolving&hellip;</p> : null}
        {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

        {resources && !isLoading && !errorMessage ? (
          <div className="resource-results">
            {resources.length === 0 ? (
              <p className="resource-banner resource-banner-neutral">No linked resources for this section yet.</p>
            ) : (
              <div className="resource-grid">
                {resources.map((r, i) => (
                  <article className="resource-item" key={i}>
                    <div className="resource-item-row">
                      <span className="resource-chip">{r.source === 'curated' ? 'Curated' : 'Section match'}</span>
                      {r.is_primary ? <span className="resource-chip">Primary</span> : null}
                      {r.cert_level ? <span className="resource-chip">Level {r.cert_level}</span> : null}
                    </div>
                    <h3>{r.title}</h3>
                    <p>{r.why}</p>
                    <div className="resource-item-row">
                      <button className="btn" onClick={() => capture('resource_viewed', r)}>Mark viewed</button>
                      <button className="btn" onClick={() => capture('resource_completed', r)}>Mark completed</button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        ) : null}

        <div className="resource-item-row" style={{ marginTop: '1rem' }}>
          <button className="btn" onClick={() => capture('self_assessment')}>Log self-assessment for this section</button>
        </div>
      </section>

      <section className="notes-card">
        <h2>Captured events</h2>
        {events.length === 0 ? (
          <p className="resource-banner resource-banner-neutral">No events captured for this technician yet.</p>
        ) : (
          <div className="resource-grid">
            {events.map((e) => (
              <article className="resource-item" key={e.event_id}>
                <div className="resource-item-row">
                  <span className="resource-chip">{e.event_type}</span>
                  {e.neta_section ? <span className="resource-chip">NETA {e.neta_section}</span> : null}
                </div>
                <p>{new Date(e.occurred_at).toLocaleString()}</p>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}
```

- [ ] **Step 3: Typecheck**

Run:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane/apps/operations-web && . $HOME/.nvm/nvm.sh && pnpm run typecheck 2>&1 | tail -15'
```
Expected: no type errors (exit 0). If `pnpm` is unavailable, enable it with `corepack enable` first (per §261). Fix any type errors before continuing.

- [ ] **Step 4: Write a thin browser smoke `e2e/learning-capture.spec.ts`**

```ts
import { test, expect } from '@playwright/test'

// Thin smoke: the capture panel renders with the resolve control and a captured-events section.
test('learning-demo capture panel renders', async ({ page }) => {
  await page.goto('/learning-demo')
  await expect(page.getByRole('button', { name: 'Resolve' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Captured events' })).toBeVisible()
})
```

- [ ] **Step 5: Run the smoke (build + playwright)**

Run:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane/apps/operations-web && . $HOME/.nvm/nvm.sh && pnpm run smoke:browser 2>&1 | tail -20'
```
Expected: the `learning-capture` spec passes. (If the broader smoke suite has unrelated pre-existing failures, confirm the new spec itself passes and note the unrelated ones — do not fix orthogonal failures here.)

- [ ] **Step 6: Confirm no `uv.lock`; commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git add apps/operations-web/lib/learning-capture.ts apps/operations-web/app/learning-demo/page.tsx apps/operations-web/e2e/learning-capture.spec.ts && git commit -F - <<"EOF"
feat(learning): operations-web capture panel on /learning-demo

Closes the resolve to capture loop on one screen: pick a technician, resolve resources (Slice 1),
mark a surfaced resource viewed/completed or log a self-assessment, watch the captured-events list
refresh. New lib/learning-capture.ts client + a thin browser smoke. Typecheck clean.
EOF'
```

---

## Self-Review

**1. Spec coverage:**
- Spec §2 boundaries (learning_dev-only, deferred 2b/2c) → Global Constraints + MANIFEST "Deferred". ✓
- Spec §4 `001` person bridge → Task 1. ✓
- Spec §4 `002` append-only `learning_events` (CHECK vocab, guard trigger, indexes, FK semantics) → Task 2. ✓
- Spec §5.1 `learning-capture` package (record/list, read-WRITE db, vocab+existence validation, CLI) → Task 3 (plus `list_users`, spec §5.3's "user picker"). ✓
- Spec §5.2 `POST/GET /events` extending the Slice 1 module + editable dep → Task 4 (plus `GET /users`). ✓
- Spec §5.3 capture panel extending `/learning-demo` → Task 5. ✓
- Spec §7 testing (migration throwaway, package, API, UI smoke) → tests in every task. ✓
- Spec §3 NETA-section contract + person bridge → carried in `neta_section` column + `employee_id`. ✓

**2. Placeholder scan:** No TBD/TODO; every code step shows complete code; every command shows expected output. ✓

**3. Type consistency:** `CapturedEvent` fields (Task 3 `models.py`) == `EventOut` fields (Task 4 `schemas.py`) == `LearningEvent` TS type (Task 5) — `event_id, user_id, event_type, study_content_id, neta_section, occurred_at, payload, created_at`. `record_event` signature identical in spec §5.1, Task 3 interface, Task 3 `capture.py`, and the Task 4 call site. `EVENT_TYPES` 4 values identical in `models.py`, the `002` CHECK, and the demo buttons. Seed UUIDs (`…0001`, `…0010`) identical across `test_prereq.sql`, both migration tests, and the package/API tests. ✓
