# Ops Chip 5 — Estimator Intake Envelope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wrap the existing `ops-intake` engine in a server-side, governed, multi-project intake envelope — upload `.xlsm` → parse → review/edit the **scope→task→line** tree (the PM regroups lines into tasks + edits hours; apparatus are the QTY-expansion materialized at approve, shown read-only) → identity-gated approve materializes & freezes the quote — with `ops.*` written **only at approve**.

**Architecture:** Four layers on `main@94db4727` (Chips 1–4): (A) migration `007` adds the envelope tables + DB guards; (B) `packages/ops-intake` is generalized so parse persists only to the envelope and approve is the sole domain writer (full-replacement under a project lock, with an approve-time conflict re-check); (C) a host-gated control-plane API exposes upload/preview/review/approve/reject with findings finance-redaction; (D) an `operations-web` page gives the upload→review→approve UI (no dollars).

**Tech Stack:** PostgreSQL (host `ops_dev` / throwaway `ops_test`), Python 3.11 + `psycopg[binary]` + `openpyxl` (`uv run`), FastAPI (control-plane-api), Next 16 / React 19 / Playwright (operations-web). All work on the Olares host over mesh SSH (`ssh olares-mesh`); the worktree is `/home/olares/code/apex/apex-ops-chip5` on branch `ops/chip5-intake-envelope`.

## Global Constraints

- **Dev-only.** Nothing is applied to `ops_dev`/prod by the build. Migration/package/API tests run on **throwaway `ops_test`**; `ops_dev` is for operator review only. Merge to main is **operator-gated**.
- **Test DSN pinning (hard safety rule):** every test that applies/tears-down schema or truncates pins the DSN at **`ops_test`** and **refuses any DSN whose dbname is not `ops_test`**. The migration-test idiom (`infra/database/migrations/ops/test_006_progress_billing.py`) is the template: `DSN = os.environ.get("OPS_DEV_DSN") or "...dbname=ops_test..."`.
- **No operational writes before approve.** Parse/validate/review-edit touch only the envelope tables (`ops.intake_runs|intake_source_files|intake_validation_findings`). `ops.projects|scopes|tasks|apparatus|scope_quote|scope_quote_line|standard_hours` are written **only** inside `approve_run`.
- **Approve is the only domain writer** and is **identity-gated** by `ops.persons(person_id)`. It takes `SELECT ... FOR UPDATE` on the **intake_run row first, then the project row** (fixed order; serializes concurrent approves of the same run before any status/conflict read).
- **Intake ownership marker:** rows materialized by approve are stamped `source='ops-intake'`; full-replacement deletes the project's scopes **`where source='ops-intake'`** (cascade) — never the generic `legacy_source_id is not null`, which is a per-row stable key (used by the 003/007 unique indexes), not an exclusive owner marker.
- **`recognized` conflict is membership, not balance:** any `ops.revenue_recognition_event` row existing for the project (EXISTS), never `net > 0`.
- **Finance redaction:** findings carry a PM-safe `message` (no dollars) and a finance-only `diagnostic_detail`; API/UI return only `message`.
- **Law 1:** apparatus never move across scopes; the DB guard backstops it.
- **Reversible:** `007_..._down.sql` drops only 007 objects; Chips 1–6 survive DOWN.
- **Migration chain (test fixtures):** `001 → 002 → 003 → 004 → 005 → 006 → 007` (note `003_intake_unique_keys` — the prior intake unique keys — IS required for Chip 5 and must be in the chain; `test_006` omitted it).
- **Tooling:** `export PATH=$HOME/.local/bin:$PATH`; `uv run --with "psycopg[binary]" --with pytest` (migration tests) / `uv run --extra test` or `--with` for package tests. Source `infra/.env` for `DEV_PG_PASSWORD`. No apostrophes in ssh commit messages.
- **Parser security:** read workbooks with `openpyxl load_workbook(..., data_only=True, read_only=True)` (cached values; VBA never executed); reject uploads > 25 MB at the boundary.

---

## File Structure

**Layer A — migration (`infra/database/migrations/ops/`):**
- Create `007_intake_envelope.sql` — enums, 3 envelope tables, immutability + guard triggers, indexes, source columns.
- Create `007_intake_envelope_down.sql` — reverse-dependency drops (007 only).
- Create `test_007_intake_envelope.py` — structure/guard/reversibility tests (pins `ops_test`).
- Modify `MANIFEST.md` — add row 007.

**Layer B — package (`packages/ops-intake/`):**
- Modify `src/ops_intake/model.py` — canonical payload superset (client/site, N4, section, versions).
- Modify `src/ops_intake/extract.py` — macro-parity parse (section, client/site, N4) + `data_only/read_only`.
- Create `src/ops_intake/classify.py` — `source_format` discriminator.
- Modify `src/ops_intake/validate.py` — findings model (`message`+`diagnostic_detail`, severity, N4 reconciliation).
- Create `src/ops_intake/envelope.py` — `create_run` (parse→classify→supersede→conflict→persist; no domain writes), `patch_review`, `get_run`.
- Create `src/ops_intake/approve.py` — `approve_run` (identity-gated, full-replacement under project lock, TOCTOU re-check, freeze).
- Modify `src/ops_intake/load.py` — keep the row-builder helpers, called by `approve.py`; remove standard_hours write + the inline `_approve`.
- Modify `src/ops_intake/cli.py` — `extract` / `intake` (create_run) / `approve` subcommands.
- Modify `tests/conftest.py` — guarded `apply_migrations` (001–007) session fixture + extended truncate + an `ops_test` guard.
- Modify `tests/fixtures/build_fixture.py` — the synthetic workbook carries sections, N4, and a `Dataverse_Import` metadata sheet.
- Create `tests/test_classify.py`, `tests/test_findings.py`, `tests/test_envelope.py`, `tests/test_approve_envelope.py`; modify `tests/test_model.py`, `tests/test_extract.py`.
- Modify `pyproject.toml` — description (drop Miner-specific wording).

**Layer C — API (`apps/control-plane-api/`):**
- Create `api/ops_intake_router.py` (or the dir the existing `ops_router` lives in — mirror it) — the 5 routes.
- Modify `main.py` — `_ops_intake_enabled()` + conditional `app.include_router(ops_intake_router)` (mirror `main.py:100-106`).
- Modify `requirements.txt` — add `-e ../../packages/ops-intake`.
- Create `tests/test_ops_intake_routes.py` + a route-guard subprocess test (mirror the learning route tests).

**Layer D — UI (`apps/operations-web/`):**
- Create `lib/estimator-intake.ts` — typed API client + tree/finding view-model (PM-safe).
- Create `app/pm-review/estimator-intake/page.tsx` — upload → review tree → approve.
- Create `tests/estimator-intake.unit.spec.ts` (pure view-model) + `tests/browser-shell.estimator-intake.smoke.spec.ts` (route-mocked).

**Layer E — docs:**
- Modify `reference/ops/00-MASTER-INDEX.md` (§6/G6 + §7 + a D-OPS row); `RESUME_HERE.md` + memory at the merge checkpoint (final task).

---

## Invariant → Task coverage map

| Spec requirement | Task(s) |
|---|---|
| Envelope tables + enums + payload columns + immutability | 1 |
| one-active-run partial unique | 1 |
| task-scope guard + tasks.scope_id immutable + uq_ops_tasks_intake + source columns | 2 |
| reversibility (DOWN, Chips 1–6 survive) | 3 |
| canonical payload superset (client/site, N4, section, versions) | 4 |
| macro-parity parse + data_only/read_only | 5 |
| source_format classify + reject flat/unsupported | 6 |
| findings: message/diagnostic split + severity + N4 reconciliation (info vs blocking) | 7 |
| create_run: no domain writes + sha256 + supersede-only-if-active + conflict (recognized=EXISTS, +billing) | 8 |
| review edit (POST /review): version bump, re-validate, allowlist diff + no cross-scope moves | 9 |
| approve: identity-gated, full-replacement under lock, TOCTOU re-check, freeze, no standard_hours | 10 |
| stable `line_uid` line key + cross-scope guard keyed on it (not legacy_source_id) | 4, 5, 9 |
| foreign-source refusal + Miner coexistence decision | 10, 16 |
| concurrency: create_run advisory lock + approve apparatus-lock + UniqueViolation→409 | 8, 10 |
| project-qualified apparatus key + `__ungrouped__` null-section fallback + metadata write | 10 |
| CLI | 11 |
| API host-gating + route guard + editable install | 12 |
| API routes + finance-redaction | 13 |
| UI client (PM-safe) | 14 |
| UI page + no-dollars smoke | 15 |
| SSoT/MANIFEST/RESUME/memory housekeeping | 16 |

---

## Task 1: Migration 007 — envelope tables, enums, immutability, one-active-run

**Files:**
- Create: `infra/database/migrations/ops/007_intake_envelope.sql`
- Create: `infra/database/migrations/ops/007_intake_envelope_down.sql` (stub now; completed in Task 3)
- Test: `infra/database/migrations/ops/test_007_intake_envelope.py`

**Interfaces:**
- Produces: tables `ops.intake_runs`, `ops.intake_source_files`, `ops.intake_validation_findings`; enums `ops.intake_run_status`, `ops.intake_conflict_kind`, `ops.intake_source_format`; index `uq_intake_one_active`. Columns named exactly as in the spec §5.1.

- [ ] **Step 1: Write the failing test** — `test_007_intake_envelope.py` (header mirrors `test_006`):

```python
"""ops Chip 5 -- intake envelope: structure, guards, reversibility (TDD). Throwaway ops_test ONLY."""
import os, pathlib, uuid
import psycopg, pytest

DSN = os.environ.get("OPS_DEV_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD','')} sslmode=disable")
assert "dbname=ops_test" in DSN, "Chip 5 migration tests must run on ops_test only"
HERE = pathlib.Path(__file__).parent
DOWN1 = HERE/"001_identity_skeleton_down.sql"
CHAIN = ["001_identity_skeleton.sql","002_quote_model.sql","003_intake_unique_keys.sql",
         "004_person_anchor.sql","005_recognition_ledger.sql","006_progress_billing.sql","007_intake_envelope.sql"]
DOWN7 = HERE/"007_intake_envelope_down.sql"

def _exec(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(pathlib.Path(path).read_text(encoding="utf-8"))

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    _exec(DOWN1)
    for f in CHAIN: _exec(HERE/f)
    yield
    _exec(DOWN1)

@pytest.fixture
def conn():
    with psycopg.connect(DSN) as c:
        try: yield c
        finally: c.rollback()

def test_tables_and_enums_exist(conn):
    for t in ("intake_runs","intake_source_files","intake_validation_findings"):
        assert conn.execute("select to_regclass(%s)", (f"ops.{t}",)).fetchone()[0] is not None
    for typ, labels in [
        ("intake_run_status", ["parsed","reviewing","approved","rejected","revision_blocked","superseded"]),
        ("intake_conflict_kind", ["none","frozen","recognized","billed"]),
        ("intake_source_format", ["decomposed_scope_sheet","flat_quote","unsupported"])]:
        got = conn.execute(
            "select array_agg(e.enumlabel order by e.enumsortorder) from pg_enum e "
            "join pg_type t on t.oid=e.enumtypid join pg_namespace n on n.oid=t.typnamespace "
            "where n.nspname='ops' and t.typname=%s", (typ,)).fetchone()[0]
        assert sorted(got) == sorted(labels), (typ, got)

def _person(c):
    return c.execute("insert into ops.persons (display_name) values ('U') returning person_id").fetchone()[0]

def test_canonical_payload_immutable(conn):
    pn = f"P-{uuid.uuid4().hex[:6]}"; who = _person(conn)
    rid = conn.execute(
        "insert into ops.intake_runs (project_number, source_format, payload_schema_version, parser_version, "
        "canonical_payload_json, review_payload_json, uploaded_by) "
        "values (%s,'decomposed_scope_sheet','1','t',%s,%s,%s) returning id",
        (pn, '{}', '{}', who)).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("update ops.intake_runs set canonical_payload_json='{\"x\":1}' where id=%s", (rid,))

def test_one_active_run_per_project(conn):
    pn = f"P-{uuid.uuid4().hex[:6]}"; who = _person(conn)
    def mk(status):
        return conn.execute(
            "insert into ops.intake_runs (project_number, status, source_format, payload_schema_version, "
            "parser_version, canonical_payload_json, review_payload_json, uploaded_by) "
            "values (%s,%s,'decomposed_scope_sheet','1','t','{}','{}',%s) returning id",
            (pn, status, who)).fetchone()[0]
    mk("parsed")
    with pytest.raises(psycopg.errors.UniqueViolation):
        mk("reviewing")

# NB: each failing statement aborts the txn, so a single test cannot chain two pytest.raises on the
# same `conn` (the 2nd would see InFailedSqlTransaction, not the specific error). Split per assertion.
def test_approved_at_is_set_once(conn):
    who = _person(conn)
    rid = conn.execute(
        "insert into ops.intake_runs (project_number, status, source_format, payload_schema_version, parser_version,"
        " canonical_payload_json, review_payload_json, uploaded_by, approved_by, approved_at) "
        "values ('PA','approved','decomposed_scope_sheet','1','t','{}','{}',%s,%s, now()) returning id",
        (who, who)).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):                      # approved_at is set-once
        conn.execute("update ops.intake_runs set approved_at = now() + interval '1 day' where id=%s", (rid,))

def test_source_file_byte_size_integrity(conn):
    who = _person(conn)
    rid = conn.execute(
        "insert into ops.intake_runs (project_number, source_format, payload_schema_version, parser_version,"
        " canonical_payload_json, review_payload_json, uploaded_by) "
        "values ('PB','decomposed_scope_sheet','1','t','{}','{}',%s) returning id", (who,)).fetchone()[0]
    with pytest.raises(psycopg.errors.CheckViolation):                     # octet_length(raw_bytes) must == byte_size
        conn.execute(
            "insert into ops.intake_source_files (run_id, filename, content_type, byte_size, sha256, raw_bytes) "
            "values (%s,'f.xlsm','xlsm', 999, 'x', %s)", (rid, b"short"))
```

- [ ] **Step 2: Run it — expect FAIL** (`to_regclass` returns None / undefined relation). Command:

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-chip5/infra/database/migrations/ops && export PATH=$HOME/.local/bin:$PATH && set -a && . /home/olares/code/apex/apex-ops-chip5/infra/.env && set +a && OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable" uv run --with "psycopg[binary]" --with pytest pytest test_007_intake_envelope.py -q'
```

- [ ] **Step 3: Write `007_intake_envelope.sql`** (this part — tables/enums/immutability/active-run; guards added in Task 2):

```sql
-- ops migration 007 -- Estimator intake envelope (Chip 5). Additive + reversible. Dev-only.
-- Builds on 001-006. The operational ops.* substrate is written ONLY by approve_run (the package);
-- this migration adds the audit/lifecycle envelope + guards + minimal source columns.

create type ops.intake_run_status   as enum ('parsed','reviewing','approved','rejected','revision_blocked','superseded');
create type ops.intake_conflict_kind as enum ('none','frozen','recognized','billed');
create type ops.intake_source_format as enum ('decomposed_scope_sheet','flat_quote','unsupported');

create table ops.intake_runs (
  id                     uuid primary key default gen_random_uuid(),
  project_number         text not null,
  project_id             uuid references ops.projects(id),
  source_format          ops.intake_source_format not null,
  status                 ops.intake_run_status not null default 'parsed',
  conflict_kind          ops.intake_conflict_kind not null default 'none',
  payload_schema_version text not null,
  parser_version         text not null,
  canonical_payload_json jsonb not null,
  review_payload_json    jsonb not null,
  review_payload_version int  not null default 1,
  uploaded_by            uuid not null references ops.persons(person_id),
  uploaded_at            timestamptz not null default now(),
  approved_by            uuid references ops.persons(person_id),
  approved_at            timestamptz,
  rejected_reason        text,
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now()
);

create table ops.intake_source_files (
  id           uuid primary key default gen_random_uuid(),
  run_id       uuid not null references ops.intake_runs(id) on delete cascade,
  filename     text not null,
  content_type text not null check (content_type in ('xlsm','json')),
  byte_size    bigint not null check (byte_size > 0 and byte_size <= 26214400),  -- 25 MB audit-envelope cap
  sha256       text not null,
  raw_bytes    bytea not null check (octet_length(raw_bytes) = byte_size),       -- stored artifact integrity
  created_at   timestamptz not null default now()
);

create table ops.intake_validation_findings (
  id                uuid primary key default gen_random_uuid(),
  run_id            uuid not null references ops.intake_runs(id) on delete cascade,
  payload_version   int  not null,
  severity          text not null check (severity in ('blocking','fidelity','info')),
  code              text not null,
  ok                boolean not null,
  message           text not null default '',     -- PM-safe: NO dollar values
  diagnostic_detail text,                          -- finance-only; never returned to the PM surface
  created_at        timestamptz not null default now()
);
create index ix_intake_findings_run on ops.intake_validation_findings (run_id, payload_version);
create index ix_intake_source_files_run on ops.intake_source_files (run_id);

-- one approvable active run per project_number (supersede lifecycle backstop)
create unique index uq_intake_one_active on ops.intake_runs (project_number)
  where status in ('parsed','reviewing');

-- write-once provenance fields on intake_runs
create or replace function ops.trg_intake_run_immutable() returns trigger language plpgsql as $$
begin
  -- approval shape (INSERT *and* UPDATE): by/at set together; status='approved' IFF approved_by set
  -- (blocks a direct insert of status='approved' with null actor, and approval fields on a non-approved row).
  if (new.approved_by is null) <> (new.approved_at is null) then
    raise exception 'intake_runs: approved_by and approved_at must be set together';
  end if;
  if (new.status = 'approved') <> (new.approved_by is not null) then
    raise exception 'intake_runs: status=approved iff approved_by is set';
  end if;
  if tg_op = 'UPDATE' then
    if new.canonical_payload_json   is distinct from old.canonical_payload_json
       or new.source_format         is distinct from old.source_format
       or new.payload_schema_version is distinct from old.payload_schema_version
       or new.parser_version         is distinct from old.parser_version
       or new.uploaded_by            is distinct from old.uploaded_by
       or new.project_number         is distinct from old.project_number then   -- project_number write-once
      raise exception 'intake_runs provenance fields are immutable (run %)', old.id;
    end if;
    if old.approved_by is not null and new.approved_by is distinct from old.approved_by then
      raise exception 'intake_runs.approved_by is set-once (run %)', old.id;
    end if;
    if old.approved_at is not null and new.approved_at is distinct from old.approved_at then
      raise exception 'intake_runs.approved_at is set-once (run %)', old.id;
    end if;
    new.updated_at := now();
  end if;
  return new;
end $$;
create trigger trg_intake_run_immutable before insert or update on ops.intake_runs
  for each row execute function ops.trg_intake_run_immutable();
```

- [ ] **Step 4: Write `007_intake_envelope_down.sql` (stub)** — enough to let the session fixture tear down on re-run (full version in Task 3):

```sql
drop trigger if exists trg_intake_run_immutable on ops.intake_runs;
drop function if exists ops.trg_intake_run_immutable();
drop table if exists ops.intake_validation_findings;
drop table if exists ops.intake_source_files;
drop table if exists ops.intake_runs;
drop type if exists ops.intake_source_format;
drop type if exists ops.intake_conflict_kind;
drop type if exists ops.intake_run_status;
```

- [ ] **Step 5: Run the test — expect PASS.** (same command as Step 2)
- [ ] **Step 6: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-chip5 && git add infra/database/migrations/ops/007_intake_envelope.sql infra/database/migrations/ops/007_intake_envelope_down.sql infra/database/migrations/ops/test_007_intake_envelope.py && git commit -q -m "feat(ops): Chip 5 mig 007 -- envelope tables, enums, immutability, one-active-run"'
```

---

## Task 2: Migration 007 — DB guards + source columns

**Files:**
- Modify: `infra/database/migrations/ops/007_intake_envelope.sql` (append)
- Modify: `infra/database/migrations/ops/007_intake_envelope_down.sql` (prepend the new drops)
- Test: `infra/database/migrations/ops/test_007_intake_envelope.py` (add cases)

**Interfaces:**
- Produces: triggers `trg_apparatus_task_same_scope`, `trg_task_scope_immutable`; index `uq_ops_tasks_intake`; columns `ops.projects.source_client_name`, `source_site_name|address|city|state|zip`.

- [ ] **Step 1: Write failing tests** (append to `test_007_intake_envelope.py`):

```python
def _proj_scope(c):
    pid = c.execute("insert into ops.projects (project_number, project_name) values (%s,'p') returning id",
                    (f"P-{uuid.uuid4().hex[:6]}",)).fetchone()[0]
    s1 = c.execute("insert into ops.scopes (project_id, scope_name) values (%s,'s1') returning id",(pid,)).fetchone()[0]
    s2 = c.execute("insert into ops.scopes (project_id, scope_name) values (%s,'s2') returning id",(pid,)).fetchone()[0]
    return pid, s1, s2

def test_apparatus_task_must_match_scope(conn):
    _, s1, s2 = _proj_scope(conn)
    t1 = conn.execute("insert into ops.tasks (scope_id, task_name) values (%s,'t') returning id",(s1,)).fetchone()[0]
    # same scope: ok
    conn.execute("insert into ops.apparatus (scope_id, apparatus_designation, task_id) values (%s,'A',%s)",(s1,t1))
    # cross scope: rejected
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("insert into ops.apparatus (scope_id, apparatus_designation, task_id) values (%s,'B',%s)",(s2,t1))

def test_task_scope_immutable(conn):
    _, s1, s2 = _proj_scope(conn)
    t1 = conn.execute("insert into ops.tasks (scope_id, task_name) values (%s,'t') returning id",(s1,)).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("update ops.tasks set scope_id=%s where id=%s",(s2,t1))

def test_tasks_intake_unique(conn):
    _, s1, _ = _proj_scope(conn)
    conn.execute("insert into ops.tasks (scope_id, task_name, legacy_source_id) values (%s,'t','SEC-A')",(s1,))
    with pytest.raises(psycopg.errors.UniqueViolation):
        conn.execute("insert into ops.tasks (scope_id, task_name, legacy_source_id) values (%s,'t2','SEC-A')",(s1,))

def test_source_columns_exist(conn):
    cols = conn.execute(
        "select column_name from information_schema.columns where table_schema='ops' and table_name='projects' "
        "and column_name like 'source_%'").fetchall()
    names = {r[0] for r in cols}
    assert {'source_client_name','source_site_name','source_site_address','source_site_city',
            'source_site_state','source_site_zip'} <= names
```

- [ ] **Step 2: Run — expect FAIL** (cross-scope insert succeeds today; columns absent). (same command, `-k "task or source or scope"`)
- [ ] **Step 3: Append to `007_intake_envelope.sql`:**

```sql
-- D1: apparatus.task_id must reference a task in the SAME scope.
create or replace function ops.trg_apparatus_task_same_scope() returns trigger language plpgsql as $$
declare v_task_scope uuid;
begin
  if new.task_id is not null then
    select scope_id into v_task_scope from ops.tasks where id = new.task_id;
    if v_task_scope is null or v_task_scope <> new.scope_id then
      raise exception 'apparatus % task_id must be a task in scope % (got task scope %)',
        coalesce(new.apparatus_designation,'?'), new.scope_id, v_task_scope;
    end if;
  end if;
  return new;
end $$;
create trigger trg_apparatus_task_same_scope before insert or update on ops.apparatus
  for each row execute function ops.trg_apparatus_task_same_scope();

-- D1: tasks.scope_id is immutable once the row exists.
create or replace function ops.trg_task_scope_immutable() returns trigger language plpgsql as $$
begin
  if new.scope_id is distinct from old.scope_id then
    raise exception 'ops.tasks.scope_id is immutable (task %)', old.id;
  end if;
  return new;
end $$;
create trigger trg_task_scope_immutable before update on ops.tasks
  for each row execute function ops.trg_task_scope_immutable();

-- Intake idempotency for tasks (003 covered scopes/lines/apparatus but not tasks). Section is the stable key.
create unique index uq_ops_tasks_intake on ops.tasks (scope_id, legacy_source_id)
  where legacy_source_id is not null;

-- D2: minimal source-derived project columns (NOT canonical CRM).
alter table ops.projects
  add column if not exists source_client_name   text,
  add column if not exists source_site_name     text,
  add column if not exists source_site_address  text,
  add column if not exists source_site_city     text,
  add column if not exists source_site_state    text,
  add column if not exists source_site_zip      text;
```

- [ ] **Step 4: Prepend the new drops to `007_intake_envelope_down.sql`:**

```sql
drop trigger if exists trg_apparatus_task_same_scope on ops.apparatus;
drop function if exists ops.trg_apparatus_task_same_scope();
drop trigger if exists trg_task_scope_immutable on ops.tasks;
drop function if exists ops.trg_task_scope_immutable();
drop index if exists ops.uq_ops_tasks_intake;
alter table ops.projects
  drop column if exists source_client_name, drop column if exists source_site_name,
  drop column if exists source_site_address, drop column if exists source_site_city,
  drop column if exists source_site_state, drop column if exists source_site_zip;
```

- [ ] **Step 5: Run — expect PASS.**
- [ ] **Step 6: Commit** (`-m "feat(ops): Chip 5 mig 007 -- task-scope guard, task immutability, tasks intake key, source columns"`)

---

## Task 3: Migration 007 — reversibility

**Files:** Modify `007_intake_envelope_down.sql`; add a DOWN/UP test to `test_007_intake_envelope.py`.

**Interfaces:** Produces a complete `007_..._down.sql` that drops only 007 objects.

- [ ] **Step 1: Write failing test:**

```python
def test_down_then_up_is_idempotent_and_chips_survive():
    # apply down (007 only) then re-up; 006 objects (e.g. ops.billing_application) survive throughout.
    _exec(HERE/"007_intake_envelope_down.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        assert c.execute("select to_regclass('ops.intake_runs')").fetchone()[0] is None
        assert c.execute("select to_regclass('ops.billing_application')").fetchone()[0] is not None  # Chip 4 intact
        assert c.execute("select to_regclass('ops.scopes')").fetchone()[0] is not None               # Chip 1 intact
    _exec(HERE/"007_intake_envelope.sql")
    with psycopg.connect(DSN, autocommit=True) as c:
        assert c.execute("select to_regclass('ops.intake_runs')").fetchone()[0] is not None
```

- [ ] **Step 2: Run — expect FAIL** if the down is incomplete (re-running `007.sql` errors on existing types, or down leaves an object). 
- [ ] **Step 3: Verify `007_intake_envelope_down.sql` is complete** (Tasks 1+2 drops cover every 007 object: 3 tables, 3 enums, 2 immutability fns/triggers, 2 guard fns/triggers, 2 indexes created outside the tables [`uq_intake_one_active`, `uq_ops_tasks_intake`], 6 columns). Add the missing index drop:

```sql
drop index if exists ops.uq_intake_one_active;
```

- [ ] **Step 4: Run — expect PASS.**
- [ ] **Step 5: Commit** (`-m "feat(ops): Chip 5 mig 007 -- complete reversible down"`)

---

## Task 4: Canonical payload model + workbook fixture

**Files:**
- Modify: `packages/ops-intake/src/ops_intake/model.py`
- Modify: `packages/ops-intake/tests/fixtures/build_fixture.py` (synthetic workbook gains sections, N4, metadata sheet)
- Test: `packages/ops-intake/tests/test_model.py`

**Interfaces:**
- Produces: `PAYLOAD_SCHEMA_VERSION = "1"`, `PARSER_VERSION` constant; `QuoteLineIn.section: str | None` (the bold-header task-group label — **mutable**, it IS the regroup key) and **`QuoteLineIn.line_uid: str | None`** (a **stable, scope-independent, write-once payload line identity** minted at parse — the key the cross-scope guard AND materialize idempotency hang on; distinct from the DB-synthesized `scope_quote_line.legacy_source_id`); `ScopeQuoteIn.pct_adjust` already exists — confirm; `ProjectIn.client_name`, `site_name/address/city/state/zip/contact_name/contact_phone/contact_email`. `IntakePayload` unchanged shape (project/scopes/standard_hours) + these fields. **Why `line_uid`:** the canonical/review payload is `dataclasses.asdict(IntakePayload)`, so the cross-scope guard can only key on a field that actually exists on the line dict — `section` is mutable and `line_number` is scope-relative (collides on a move), so neither works; `line_uid` is the one stable anchor.

- [ ] **Step 1: Write failing test** (`test_model.py` — add):

```python
from ops_intake.model import ProjectIn, QuoteLineIn, PAYLOAD_SCHEMA_VERSION

def test_project_carries_client_site():
    p = ProjectIn(project_number="J1", project_name="N", client_name="Garney", site_city="Mesa")
    assert p.client_name == "Garney" and p.site_city == "Mesa"

def test_line_carries_section():
    assert QuoteLineIn(apparatus_type="X", test_standard="ATS", qty=1, hrs_per_unit=2.0,
                       section="SES-00-001").section == "SES-00-001"

def test_line_carries_stable_uid():
    l = QuoteLineIn(apparatus_type="X", test_standard="ATS", qty=1, hrs_per_unit=2.0,
                    section="SES-00-001", line_uid="ScopeA:row7")
    assert l.line_uid == "ScopeA:row7"

def test_schema_version_constant():
    assert PAYLOAD_SCHEMA_VERSION == "1"
```

- [ ] **Step 2: Run — FAIL** (`section`/`client_name` unexpected kwarg; `PAYLOAD_SCHEMA_VERSION` missing).
- [ ] **Step 3: Edit `model.py`** — add at top `PAYLOAD_SCHEMA_VERSION = "1"` and `PARSER_VERSION = "ops-intake/0.2.0"`; add `section: str | None = None` **and `line_uid: str | None = None`** to `QuoteLineIn`; add to `ProjectIn`: `client_name: str | None = None`, `site_name/site_address/site_city/site_state/site_zip/site_contact_name/site_contact_phone/site_contact_email: str | None = None`. (`ScopeQuoteIn.pct_adjust` already exists.)
- [ ] **Step 4: Extend `build_fixture.py`** — the synthetic scope sheet writes a bold `section` header row above its apparatus rows; set `N4` (the pct-adjust cell) explicitly = 1.0; add a `Dataverse_Import` sheet with `Client:`/`Site City:`/`Job #:` label-value rows. Keep the existing reconciliation (5 apparatus × 5h, P4 = 1000) intact.
- [ ] **Step 5: Run the model + a fixture sanity test — PASS.** Command:

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-chip5/packages/ops-intake && export PATH=$HOME/.local/bin:$PATH && uv run --with openpyxl --with "psycopg[binary]" --with pytest python -m pytest tests/test_model.py -q'
```

- [ ] **Step 6: Commit** (`-m "feat(ops-intake): canonical payload superset (client/site, section, versions) + richer fixture"`)

---

## Task 5: Macro-parity parser

**Files:** Modify `src/ops_intake/extract.py`; Test `tests/test_extract.py`.

**Interfaces:**
- Consumes: `model` fields from Task 4.
- Produces: `extract_workbook(path) -> IntakePayload` now fills `line.section` (from the bold section header above each apparatus block), `project.client_name`/`site_*` (from the `Dataverse_Import` sheet when present), and per-scope `pct_adjust` (N4 cell). Reads with `load_workbook(path, data_only=True, read_only=True)`.

- [ ] **Step 1: Write failing test** (`test_extract.py` — add, using `mini_workbook`):

```python
from ops_intake.extract import extract_workbook

def test_extract_sections_and_metadata(mini_workbook):
    p = extract_workbook(mini_workbook)
    s = p.scopes[0]
    assert any(l.section for l in s.lines)              # section captured
    assert all(l.line_uid for l in s.lines)             # stable per-line identity minted at parse
    assert len({l.line_uid for sc in p.scopes for l in sc.lines}) == sum(len(sc.lines) for sc in p.scopes)  # unique
    assert abs(s.quote.pct_adjust - 1.0) < 1e-9         # N4 read
    assert p.project.client_name is not None            # metadata sheet read
```

- [ ] **Step 2: Run — FAIL** (sections/metadata not populated).
- [ ] **Step 3: Implement** — in `extract.py`: switch `load_workbook` to `data_only=True, read_only=True`; in the apparatus-row loop, track the current bold `section` header (mirror `DataverseExport.bas` `BuildApparatusJSON` section detection) and set `line.section`; **set `line.line_uid = f"{scope_name}:row{line_number}"`** (write-once; encodes the line's origin scope so a later cross-scope move is detectable, and is unique within the payload); add `_extract_metadata(wb)` reading the `Dataverse_Import` label/value rows (`Client:`, `Site Name`/`Project:`, `Site Address:`, `Site City:`, etc.) onto `ProjectIn`; read the N4 cell into `ScopeQuoteIn.pct_adjust` (the macro reads only `M4`; N4 is the adjacent pct-adjust cell — confirm the cell ref against the real Rev10 workbook, default 1.0 if blank).
- [ ] **Step 4: Run — PASS** (+ the skip-gated `test_extract_real_workbook.py` if `MINER_WORKBOOK` is set on the host).
- [ ] **Step 5: Commit** (`-m "feat(ops-intake): macro-parity parse -- section, client/site, N4; data_only read"`)

---

## Task 6: source_format classifier

**Files:** Create `src/ops_intake/classify.py`; Test `tests/test_classify.py`.

**Interfaces:**
- Produces: `classify(payload: IntakePayload) -> str` returning `'decomposed_scope_sheet' | 'flat_quote' | 'unsupported'`. Rule: **any scope bears apparatus `lines` → `decomposed_scope_sheet`** (regardless of contract_value — a 0/missing total is a `contract_total` blocking finding in Task 7, NOT a format rejection, so a parse glitch never silently rejects a loadable project); scopes present but none bear lines → `flat_quote`; **no scopes at all → `unsupported`**.

- [ ] **Step 1: Write failing test:**

```python
from ops_intake.classify import classify
from ops_intake.model import IntakePayload, ProjectIn, ScopeIn, QuoteLineIn

def _proj(): return ProjectIn(project_number="J", project_name="N", contract_value=100.0)

def test_decomposed():
    s = ScopeIn(scope_name="A", lines=[QuoteLineIn("X","ATS",1,2.0)])
    assert classify(IntakePayload(_proj(), [s])) == "decomposed_scope_sheet"

def test_decomposed_even_with_zero_contract():
    s = ScopeIn(scope_name="A", lines=[QuoteLineIn("X","ATS",1,2.0)])
    p = IntakePayload(ProjectIn(project_number="J", project_name="N", contract_value=0.0), [s])
    assert classify(p) == "decomposed_scope_sheet"   # 0 total is a finding, not a format rejection

def test_flat_quote():
    assert classify(IntakePayload(_proj(), [ScopeIn(scope_name="A")])) == "flat_quote"

def test_unsupported():
    assert classify(IntakePayload(ProjectIn(project_number="J", project_name="N"), [])) == "unsupported"
```

- [ ] **Step 2: Run — FAIL** (module missing).
- [ ] **Step 3: Implement `classify.py`** per the rule above.
- [ ] **Step 4: Run — PASS.**
- [ ] **Step 5: Commit** (`-m "feat(ops-intake): source_format classifier"`)

---

## Task 7: Findings model (message/diagnostic split, severity, N4 reconciliation)

**Files:** Modify `src/ops_intake/validate.py`; Test `tests/test_findings.py`.

**Interfaces:**
- Produces: `@dataclass Finding(code:str, severity:str, ok:bool, message:str, diagnostic_detail:str|None=None)`; `validate_payload(p: IntakePayload, *, source_format: str, n4_defaulted: bool=False) -> list[Finding]`. Severity: `blocking` (j3_mismatch, contract_total, n4_reconcile, unsupported_format), `info`/`fidelity` (n4_default). **`message` never contains a dollar amount; numeric/financial detail goes in `diagnostic_detail`.**

- [ ] **Step 1: Write failing test:**

```python
from ops_intake.validate import validate_payload, Finding
from ops_intake.model import IntakePayload, ProjectIn, ScopeIn, ScopeQuoteIn, QuoteLineIn

def _mismatch_payload():
    q = ScopeQuoteIn(onsite_labor=1000, total_quoted_hours=5)  # P4=1000
    s = ScopeIn(scope_name="A", quote=q, lines=[QuoteLineIn("X","ATS",1,2.0)])  # line hrs=2 != J3=5
    return IntakePayload(ProjectIn(project_number="J", project_name="N", contract_value=1000.0), [s])

def test_blocking_has_no_dollars_in_message():
    fs = validate_payload(_mismatch_payload(), source_format="decomposed_scope_sheet")
    bad = [f for f in fs if not f.ok and f.severity == "blocking"]
    assert bad
    for f in bad:
        assert "$" not in f.message              # no currency symbol in PM-safe text
        assert "1000" not in f.message           # the P4 figure lives only in diagnostic_detail
        assert f.message                         # PM-safe message non-empty
        assert f.diagnostic_detail               # the numbers are captured for finance

def test_n4_default_is_info_when_reconciles():
    q = ScopeQuoteIn(onsite_labor=1000, unit_multiplier=1, pct_adjust=1, total_quoted_hours=2)
    s = ScopeIn(scope_name="A", quote=q, lines=[QuoteLineIn("X","ATS",1,2.0)])
    p = IntakePayload(ProjectIn(project_number="J", project_name="N", contract_value=1000.0), [s])
    fs = validate_payload(p, source_format="decomposed_scope_sheet", n4_defaulted=True)
    n4 = [f for f in fs if f.code == "n4_default"][0]
    assert n4.severity in ("info","fidelity") and n4.ok is True
    assert all(f.ok for f in fs if f.severity == "blocking")
```

- [ ] **Step 2: Run — FAIL** (`Finding`/`validate_payload` missing).
- [ ] **Step 3: Implement** — port the existing 3 checks (`J3==Σline_hours`, `Σadjusted==contract_value`, unique names; tolerances `0.01` hrs, `$1` contract) into `Finding`s with PM-safe `message` (e.g. `"Scope A hours do not reconcile"`) and the numbers in `diagnostic_detail` (e.g. `"J3=5 vs Σline=2"`); add `unsupported_format` (blocking) when `source_format != decomposed_scope_sheet`; add `n4_default` (info) when `n4_defaulted`; when a default-1 N4 breaks the contract/scope reconciliation, the existing reconciliation checks already emit their `blocking` finding (no extra code).
- [ ] **Step 4: Run — PASS.**
- [ ] **Step 5: Commit** (`-m "feat(ops-intake): findings model -- message/diagnostic split, severity, N4 reconciliation"`)

---

## Task 8: Envelope writer — create_run (no domain writes; supersede; conflict classification)

**Files:** Create `src/ops_intake/envelope.py`; modify `tests/conftest.py` (guarded `apply_migrations` + extended truncate); Test `tests/test_envelope.py`.

**Interfaces:**
- Consumes: `extract_workbook`, `classify`, `validate_payload`, `Finding`, model versions.
- Produces:
  - `create_run(dsn, *, uploaded_by: uuid, filename: str, raw_bytes: bytes, content_type: str) -> dict` returning `{"run_id", "status", "conflict_kind", "source_format", "findings": [...], "review_payload": {...}}`. Persists `intake_runs` (+ `intake_source_files` with `sha256=hashlib.sha256(raw_bytes).hexdigest()`, `byte_size`) + `intake_validation_findings`. **No INSERT/UPDATE on any ops domain table.**
  - `get_run(dsn, run_id) -> dict`.
  - Helper `_classify_conflict(cur, project_number) -> (project_id|None, conflict_kind)` — `recognized` if **any** `ops.revenue_recognition_event` row references the project; `billed` if any `ops.billing_application.project_id`; `frozen` if any `ops.scope_quote.is_frozen` for the project's scopes; precedence `billed>recognized>frozen`.

- [ ] **Step 1: Update `conftest.py`** — (a) add a session **`apply_migrations` fixture with `autouse=True`** (chains 001–007, DOWN1 teardown); (b) extend `_OPS_TRUNCATE` to include `ops.tasks, ops.intake_validation_findings, ops.intake_source_files, ops.intake_runs`; (c) add a helper **`_require_ops_test(dsn)`** that parses the conninfo (`from psycopg.conninfo import conninfo_to_dict`) and asserts `conninfo_to_dict(dsn).get("dbname") == "ops_test"` (**exact** match — a substring check false-passes on `ops_test_backup`/`ops_test2`), and call it at the TOP of `_dsn()` AND inside `clean_ops` **before the truncate** (not only in `apply_migrations`). The conftest's `_dsn()` default is `ops_dev` and `clean_ops` truncates immediately ([conftest.py:30]); the guard must fire before any truncate so a mis-pinned run fails loudly instead of nuking Miner data. Exposing it as a named helper lets a test assert it raises.

- [ ] **Step 2: Write failing test** (`test_envelope.py`):

```python
import hashlib, psycopg
from ops_intake.envelope import create_run, get_run

def _bytes(mini_workbook): return mini_workbook.read_bytes()

def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute("insert into ops.persons (display_name) values ('PM') returning person_id").fetchone()[0]

def test_create_run_persists_envelope_only(mini_workbook, clean_ops):
    dsn = clean_ops; who = _person(dsn)
    out = create_run(dsn, uploaded_by=who, filename="mini.xlsm",
                     raw_bytes=_bytes(mini_workbook), content_type="xlsm")
    assert out["status"] == "parsed" and out["conflict_kind"] == "none"
    assert out["source_format"] == "decomposed_scope_sheet"
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.intake_runs").fetchone()[0] == 1
        assert c.execute("select count(*) from ops.intake_source_files").fetchone()[0] == 1
        # NO domain writes
        for t in ("projects","scopes","tasks","apparatus","scope_quote","scope_quote_line"):
            assert c.execute(f"select count(*) from ops.{t}").fetchone()[0] == 0, t
        (sha,) = c.execute("select sha256 from ops.intake_source_files").fetchone()
        assert sha == hashlib.sha256(_bytes(mini_workbook)).hexdigest()

def test_second_active_upload_supersedes(mini_workbook, clean_ops):
    dsn = clean_ops; who = _person(dsn)
    r1 = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=_bytes(mini_workbook), content_type="xlsm")
    r2 = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=_bytes(mini_workbook), content_type="xlsm")
    with psycopg.connect(dsn) as c:
        assert c.execute("select status from ops.intake_runs where id=%s",(r1["run_id"],)).fetchone()[0]=="superseded"
        assert c.execute("select status from ops.intake_runs where id=%s",(r2["run_id"],)).fetchone()[0]=="parsed"

def test_dsn_guard_blocks_non_ops_test():
    """The conftest ops_test guard must raise for any non-ops_test DSN (protects ops_dev Miner data)."""
    import pytest
    from conftest import _require_ops_test
    with pytest.raises(AssertionError):
        _require_ops_test("host=127.0.0.1 port=5432 dbname=ops_dev user=postgres sslmode=disable")
```

- [ ] **Step 3: Run — FAIL** (module missing).
- [ ] **Step 4: Implement `envelope.py`** — `create_run` in one txn: **first `cur.execute("select pg_advisory_xact_lock(hashtext(%s))", (project_number,))`** (serializes concurrent uploads of the same project so the supersede sees committed prior runs); then extract→classify→`validate_payload`→`_classify_conflict`; decide status (`rejected` if format∈{flat_quote,unsupported}; else `revision_blocked` if conflict≠none; else `parsed`); **supersede prior active runs only if the new status is parsed/reviewing**; insert `intake_runs` (canonical==review payload via `dataclasses.asdict`), `intake_source_files` (`sha256`, `byte_size`, `raw_bytes`), findings. Catch a residual `psycopg.errors.UniqueViolation` on `uq_intake_one_active` and raise a clean `ActiveRunExists` (→409), never a raw 500. No domain writes. `get_run` reads the run + findings (PM-safe shaping at the API layer).
- [ ] **Step 5: Run — PASS.**
- [ ] **Step 6: Commit** (`-m "feat(ops-intake): create_run envelope writer -- no domain writes, sha256, supersede, conflict classification"`)

---

## Task 9: Review/edit — patch_review

**Files:** Modify `src/ops_intake/envelope.py`; Test `tests/test_envelope.py` (add).

**Interfaces:**
- Produces: `patch_review(dsn, run_id, *, review_payload: dict) -> dict` — replaces `review_payload_json`, bumps `review_payload_version`, re-runs `validate_payload`, replaces findings at the new version; returns the updated run. Only valid on `parsed`/`reviewing` runs (else `ValueError`/409 at the API). Exposes a pure helper `_assert_no_cross_scope_move(canonical: dict, review: dict) -> None` that builds a `line_uid → scope_name` map from each payload and raises `ValueError("cross-scope line move forbidden")` when any `line_uid` sits under a different `scope_name` in `review` than in `canonical`. The review tree is **line-grain** (scope→task→line); apparatus are the QTY-expansion materialized at approve and are not individually edited. **The guard keys on `line_uid`** (the stable parse-time identity from Task 4) — NOT `legacy_source_id` (absent from payload lines — it is synthesized only at DB write) and NOT `line_number` (scope-relative, collides on a move).
- **Also exposes `_assert_review_within_allowlist(canonical: dict, review: dict) -> None`** — the integrity gate, **default-deny** (pin everything except an explicit mutable set). The review payload may differ from canonical ONLY in allowed ways: same `project_number`; same set of `scope_name`s; the **exact same multiset of `line_uid`s** (no added/deleted/duplicated line); **each review line is joined to its canonical line BY `line_uid`** (a `line_uid→line` map, NOT positional — task regroup reorders lines; a positional diff would both false-reject regroups and miss a same-scope content swap), and per line **only `section` and `hrs_per_unit` are mutable** (`qty`/`apparatus_type`/`test_standard`/`line_number`/everything else pinned). At the **scope level, EVERY `scope_quote` field must equal canonical** — not just the 4 dollar categories but `unit_multiplier` (M4), `pct_adjust` (N4), `total_quoted_hours` (J3), `is_estimate` (M4/N4/J3 drive `blended_rate=P4/J3`, so a non-dollar tamper corrupts `quoted_revenue` just like a dollar one). Every project field pinned. Task names may be renamed. Any other drift raises `ValueError`. `patch_review` calls **both** guards before persisting — so approve can never materialize a doctored basis.

- [ ] **Step 1: Write failing test:**

```python
import pytest
from dataclasses import asdict
from ops_intake.extract import extract_workbook
from ops_intake.envelope import (create_run, patch_review,
                                 _assert_no_cross_scope_move, _assert_review_within_allowlist)

def test_patch_bumps_version_and_revalidates(mini_workbook, clean_ops):
    dsn = clean_ops; who = _person(dsn)
    r = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    rp = r["review_payload"]; rp["scopes"][0]["lines"][0]["hrs_per_unit"] = 3.0
    out = patch_review(dsn, r["run_id"], review_payload=rp)
    assert out["review_payload_version"] == 2

def test_real_payload_lines_carry_line_uid(mini_workbook):
    """Guard the guard: the REAL asdict payload must expose line_uid, else the cross-scope check is a no-op."""
    p = asdict(extract_workbook(mini_workbook))
    assert all(l.get("line_uid") for s in p["scopes"] for l in s["lines"])

def test_cross_scope_move_rejected():
    canon = {"scopes": [{"scope_name": "A", "lines": [{"line_uid": "A:row1"}]},
                        {"scope_name": "B", "lines": []}]}
    moved = {"scopes": [{"scope_name": "A", "lines": []},
                        {"scope_name": "B", "lines": [{"line_uid": "A:row1"}]}]}
    with pytest.raises(ValueError):
        _assert_no_cross_scope_move(canon, moved)

def test_within_scope_regroup_ok():
    """Changing a line's section (task regroup) inside its own scope is allowed."""
    canon = {"scopes": [{"scope_name": "A", "lines": [{"line_uid": "A:row1", "section": "old"}]}]}
    same  = {"scopes": [{"scope_name": "A", "lines": [{"line_uid": "A:row1", "section": "NEW TASK"}]}]}
    _assert_no_cross_scope_move(canon, same)  # must not raise

def _canon():
    return {"project": {"project_number": "P1"},
            "scopes": [{"scope_name": "A",
                        "quote": {"onsite_labor": 1000, "offsite_labor": 0, "travel": 0, "outside_services": 0,
                                  "unit_multiplier": 1, "pct_adjust": 1, "total_quoted_hours": 7},
                        "lines": [{"line_uid": "A:row1", "qty": 1, "apparatus_type": "X",
                                   "test_standard": "ATS", "hrs_per_unit": 2.0, "section": "old"},
                                  {"line_uid": "A:row2", "qty": 5, "apparatus_type": "Y",
                                   "test_standard": "ATS", "hrs_per_unit": 1.0, "section": "old"}]}]}

def test_allowlist_blocks_qty_and_dollar_tamper():
    bad = _canon(); bad["scopes"][0]["lines"][0]["qty"] = 99
    with pytest.raises(ValueError):
        _assert_review_within_allowlist(_canon(), bad)
    bad2 = _canon(); bad2["scopes"][0]["quote"]["onsite_labor"] = 5000
    with pytest.raises(ValueError):
        _assert_review_within_allowlist(_canon(), bad2)

def test_allowlist_blocks_multiplier_and_j3_tamper():
    """M4/N4/J3 are NOT dollars but drive blended_rate=P4/J3 -- default-deny must pin them too."""
    for field in ("unit_multiplier", "pct_adjust", "total_quoted_hours"):
        bad = _canon(); bad["scopes"][0]["quote"][field] = 9
        with pytest.raises(ValueError):
            _assert_review_within_allowlist(_canon(), bad)

def test_allowlist_blocks_same_scope_content_swap():
    """Swapping two lines' qty/type while keeping their line_uids is caught by the line_uid-keyed diff."""
    swap = _canon(); a, b = swap["scopes"][0]["lines"]
    a["qty"], b["qty"] = b["qty"], a["qty"]                                  # row1 now carries row2's qty
    a["apparatus_type"], b["apparatus_type"] = b["apparatus_type"], a["apparatus_type"]
    with pytest.raises(ValueError):
        _assert_review_within_allowlist(_canon(), swap)

def test_allowlist_blocks_added_or_duplicated_line():
    add = _canon(); add["scopes"][0]["lines"].append({"line_uid": "A:row3", "qty": 1})
    with pytest.raises(ValueError):
        _assert_review_within_allowlist(_canon(), add)
    dup = _canon(); dup["scopes"][0]["lines"].append({**_canon()["scopes"][0]["lines"][0]})  # duplicate line_uid
    with pytest.raises(ValueError):
        _assert_review_within_allowlist(_canon(), dup)

def test_allowlist_allows_section_and_hours_edit():
    ok = _canon(); ok["scopes"][0]["lines"][0]["section"] = "NEW"; ok["scopes"][0]["lines"][0]["hrs_per_unit"] = 3.5
    _assert_review_within_allowlist(_canon(), ok)  # must not raise
```

- [ ] **Step 2: Run — FAIL.**
- [ ] **Step 3: Implement** `patch_review` — status guard (active runs only); run **`_assert_review_within_allowlist`** (build `line_uid→line` maps from canonical + review and compare each line **by `line_uid`**, not position; scope.quote is **default-deny** — pin all 8 fields) then **`_assert_no_cross_scope_move`** against `canonical_payload_json`; replace `review_payload_json`; bump `review_payload_version`; re-run `validate_payload` and replace findings at the new version.
- [ ] **Step 4: Run — PASS.**
- [ ] **Step 5: Commit** (`-m "feat(ops-intake): patch_review -- version bump, re-validate, cross-scope guard"`)

---

## Task 10: Approve — the only domain writer

**Files:** Create `src/ops_intake/approve.py`; modify `src/ops_intake/load.py` (extract reusable row-builders; drop standard_hours write + inline `_approve`); Test `tests/test_approve_envelope.py`.

**Interfaces:**
- Consumes: the run + `review_payload_json`; `load.py` row-builders.
- Produces: `approve_run(dsn, run_id, *, approved_by: uuid) -> dict`. Transactional. **Global lock order: intake_runs → projects → apparatus** (record this in the SSoT, Task 16). Steps per spec §6.3:
  - **(0) Lock order = advisory(`project_number`) → intake_run row → project → apparatus** (must match `create_run`'s order). First `SELECT project_number FROM ops.intake_runs WHERE id=run_id` (NO lock — just read the key), then `pg_advisory_xact_lock(hashtext(project_number))`, **then** `SELECT ... FROM ops.intake_runs WHERE id=run_id FOR UPDATE` and re-read status. Taking the advisory lock **before** the run-row lock is what prevents the create-vs-approve deadlock — else approve holds the run row while waiting on the advisory lock, and a concurrent `create_run` holds the advisory lock while waiting to supersede (lock) that run row. (Serializes concurrent approves of the same run too.)
  - **(1)** refuse 422 if any open `blocking` finding; **(2)** refuse 409 if run not active; **(3)** refuse 409 if `revision_blocked`.
  - **(4)** with the advisory lock already held (step 0), upsert+`SELECT ... FOR UPDATE` the project row (create if new — the advisory lock covers the brand-new-project case where no row exists to `FOR UPDATE`), **then `SELECT id FROM ops.apparatus WHERE <project> FOR UPDATE`** so any in-flight Chip-3 `approve_and_recognize` (which locks apparatus rows, not the project) serializes and its event becomes visible. Then **re-check conflict** (frozen / **any** `revenue_recognition_event` EXISTS / any `billing_application`) → if now-conflicted: **commit the `status='revision_blocked'` transition and RETURN that outcome** (the API maps it to 409). **Do NOT raise-and-rollback** — a raise in the same txn would roll back the status write, so the conflict outcome must be a committed result the API converts to 409 (same pattern for the 422-blocking-findings and 409-not-active paths).
  - **(4b) foreign-source guard:** if the project has any scope with `source IS DISTINCT FROM 'ops-intake'` (e.g. legacy Miner rows stamped `miner_rev10.xlsm`), **abort 409** — refuse to manage a project the intake engine does not own (prevents delete-by-marker from orphaning foreign rows). See the Miner-coexistence decision (Task 16 / spec §12).
  - **(5) full replacement:** delete the project's scopes `where source='ops-intake'` (cascade), insert fresh from `review_payload`, **stamping `source='ops-intake'`** on every scope/task/scope_quote_line/apparatus **and on the project row**; create tasks from `section`, with a deterministic **`__ungrouped__`** fallback for null-section lines (so `tasks.legacy_source_id` is never null and `uq_ops_tasks_intake` always applies); set `scope_quote_line.legacy_source_id = line_uid` and `apparatus.legacy_source_id = f"{project_number}:{line_uid}:u{i}"` (**project-qualified** — `uq_ops_apparatus_intake` is GLOBALLY unique, so a bare scope-relative key collides across projects); link `apparatus.task_id`; write `ops.projects.source_client_name/source_site_*` from `review_payload.project`.
  - **(6) freeze** (`is_frozen`, `quoted_revenue = round(quoted_hours*blended_rate,2)`, `provenance_status='approved'`); **(7)** set run `approved` + `approved_by/at` + `project_id`. **No `standard_hours` write.**
- **Return contract:** `approve_run` returns `{outcome, run_id, ...}` with `outcome ∈ {approved, revision_blocked, blocked_findings, not_active, foreign_source}`. Each non-approved outcome **commits** any status transition it made and returns it (the API maps outcome→HTTP: `approved`→200, `revision_blocked`/`not_active`/`foreign_source`→409, `blocked_findings`→422). It **raises** only on genuine errors (unknown run_id, DB failure) — never to signal a business outcome (which would roll back the committed status write).
- Exposes `materialize(cur, project_number, review_payload) -> None` (project upsert stamping `source='ops-intake'` + delete `source='ops-intake'` scopes cascade + insert fresh with the marker + tasks from `section`/`__ungrouped__` + `apparatus.legacy_source_id` project-qualified + source_* columns), unit-testable directly.

- [ ] **Step 1: Write failing tests** (`test_approve_envelope.py`):

```python
import psycopg
from ops_intake.envelope import create_run
from ops_intake.approve import approve_run

def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute("insert into ops.persons (display_name) values ('Lead') returning person_id").fetchone()[0]

def test_approve_materializes_tasks_and_freezes(mini_workbook, clean_ops):
    dsn = clean_ops; who = _person(dsn)
    r = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    approve_run(dsn, r["run_id"], approved_by=who)
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.tasks where legacy_source_id is not null").fetchone()[0] >= 1
        assert c.execute("select count(*) from ops.apparatus where task_id is not null").fetchone()[0] >= 1
        assert c.execute("select bool_and(is_frozen) from ops.scope_quote").fetchone()[0] is True
        assert c.execute("select count(*) from ops.standard_hours").fetchone()[0] == 0  # D4: no catalog write
        assert c.execute("select status from ops.intake_runs where id=%s",(r["run_id"],)).fetchone()[0]=="approved"

def test_materialize_full_replacement_removes_all_children_and_spares_foreign(clean_ops):
    """Full replacement removes ALL intake-owned children via the source='ops-intake' scope cascade; foreign rows survive."""
    from ops_intake.approve import materialize
    dsn = clean_ops
    line  = {"apparatus_type":"X","test_standard":"ATS","qty":2,"hrs_per_unit":2.0,
             "section":"S1","line_number":1,"line_uid":"A:row1"}
    scope = {"scope_name":"A","legacy_source_id":"A",
             "quote":{"onsite_labor":1000,"unit_multiplier":1,"pct_adjust":1,"total_quoted_hours":4},
             "lines":[line]}
    payload = {"project":{"project_number":"FR-1","project_name":"N","contract_value":1000.0}, "scopes":[scope]}
    with psycopg.connect(dsn) as c:
        pid = c.execute("insert into ops.projects (project_number,project_name,source) "
                        "values ('OTHER','o','manual') returning id").fetchone()[0]
        c.execute("insert into ops.scopes (project_id,scope_name,source) values (%s,'keep','manual')", (pid,))  # FOREIGN
        materialize(c, "FR-1", payload); c.commit()
        counts = lambda: {t: c.execute(f"select count(*) from ops.{t}").fetchone()[0]
                          for t in ("scope_quote","scope_quote_line","tasks","apparatus")}
        before = counts()
        materialize(c, "FR-1", {**payload, "scopes": []}); c.commit()                       # drop the WHOLE scope
        after = counts()
        intake_scopes = c.execute("select count(*) from ops.scopes where source='ops-intake'").fetchone()[0]
        foreign       = c.execute("select count(*) from ops.scopes where source='manual'").fetchone()[0]
    assert before["apparatus"] == 2 and before["tasks"] >= 1
    assert intake_scopes == 0 and all(v == 0 for v in after.values())   # every intake child gone, zero orphans
    assert foreign == 1                                                  # the foreign scope was never touched

def test_null_section_lines_are_idempotent(clean_ops):
    """Lines with section=None get a deterministic __ungrouped__ task; re-materialize does not grow tasks."""
    from ops_intake.approve import materialize
    dsn = clean_ops
    scope = {"scope_name":"A","legacy_source_id":"A",
             "quote":{"onsite_labor":1000,"unit_multiplier":1,"pct_adjust":1,"total_quoted_hours":2},
             "lines":[{"apparatus_type":"X","test_standard":"ATS","qty":1,"hrs_per_unit":2.0,
                       "section":None,"line_number":1,"line_uid":"A:row1"}]}
    payload = {"project":{"project_number":"NS-1","project_name":"N","contract_value":1000.0}, "scopes":[scope]}
    with psycopg.connect(dsn) as c:
        materialize(c, "NS-1", payload); c.commit()
        t1 = c.execute("select count(*) from ops.tasks").fetchone()[0]
        materialize(c, "NS-1", payload); c.commit()
        t2 = c.execute("select count(*) from ops.tasks").fetchone()[0]
    assert t1 == 1 and t2 == 1   # exactly one __ungrouped__ task, not duplicated on re-approve

def test_recognized_then_reversed_still_blocks(mini_workbook, clean_ops):
    """recognized -> fully reversed (net 0) -> re-intake still revision_blocked/recognized (EXISTS, not net)."""
    dsn = clean_ops; who = _person(dsn)
    r = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    approve_run(dsn, r["run_id"], approved_by=who)
    with psycopg.connect(dsn, autocommit=True) as c:
        aid = c.execute("select id from ops.apparatus limit 1").fetchone()[0]
        c.execute("update ops.apparatus set status='Complete' where id=%s", (aid,))
        ev = c.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
                       (aid, who)).fetchone()[0]
        c.execute("select ops.reverse_recognition(%s,%s,'correction')", (ev, who))  # confirm arg order vs 005
    out = create_run(dsn, uploaded_by=who, filename="m.xlsm", raw_bytes=mini_workbook.read_bytes(), content_type="xlsm")
    assert out["conflict_kind"] == "recognized" and out["status"] == "revision_blocked"
```

- [ ] **Step 2: Run — FAIL.**
- [ ] **Step 3: Implement `approve.py`** per the interface; refactor `load.py` so the per-row insert helpers (project upsert, scope, scope_quote, scope_quote_line, apparatus, **task**) are importable and **stamp `source='ops-intake'`** on scope/task/scope_quote_line/apparatus; delete the standard_hours loop and the inline `_approve`; the materialize step deletes the project's `source='ops-intake'` scopes (cascade), inserts fresh, creates tasks keyed on `section`, and sets `apparatus.task_id`.
- [ ] **Step 4: Flesh out the `recognized-then-reversed` test** using the Chip 3 `ops.approve_and_recognize` + `ops.reverse_recognition` functions (see `test_006` `_recognize` helper), asserting the re-`create_run` returns `conflict_kind='recognized'`, `status='revision_blocked'`, and zero new domain writes.
- [ ] **Step 5: Run — PASS.**
- [ ] **Step 6: Commit** (`-m "feat(ops-intake): approve_run -- sole domain writer, full-replacement under lock, TOCTOU re-check, freeze; drop catalog write"`)

---

## Task 11: CLI

**Files:** Modify `src/ops_intake/cli.py`; Test `tests/test_cli.py`.

**Interfaces:** `extract <xlsm> --out` (unchanged) · `intake <xlsm> --dsn --uploaded-by` (calls `create_run`, prints run_id/status/conflict) · `approve <run_id> --dsn --approved-by` (calls `approve_run`). Drop the old `load --approve`.

- [ ] **Step 1: Write failing test** (`test_cli.py`): invoke `main(["intake", str(mini_workbook), "--dsn", dsn, "--uploaded-by", str(who)])` → returns 0, a run exists with status `parsed`.
- [ ] **Step 2: Run — FAIL.** 
- [ ] **Step 3: Implement** the `intake`/`approve` subcommands.
- [ ] **Step 4: Run — PASS.**
- [ ] **Step 5: Commit** (`-m "feat(ops-intake): CLI intake/approve subcommands"`)

---

## Task 12: control-plane API — host-gating, editable install, route guard

**Files:**
- Modify: `apps/control-plane-api/requirements.txt` (add `-e ../../packages/ops-intake`)
- Create: `apps/control-plane-api/api/ops_intake_router.py` (mirror the dir/module the existing `ops_router` lives in — find it from `main.py` imports)
- Modify: `apps/control-plane-api/main.py` — add `_ops_intake_enabled()` + conditional `include_router` (mirror `main.py:100-106`)
- Test: `apps/control-plane-api/tests/test_ops_intake_routes.py` (route-guard subprocess test)

**Interfaces:**
- Produces: an `APIRouter` `ops_intake_router` registered at `/api/v1/ops/intake` **only when `OPS_DEV_DSN` is set**; gated exactly like the learning router (`_learning_enabled()` at `main.py:100-106`). DB connection from `OPS_DEV_DSN` (host PG17), not the prod `resolve_database_url()`.

- [ ] **Step 1: Write failing route-guard test** (mirror the learning guard subprocess test): import the app in a subprocess with `OPS_DEV_DSN` **unset** → assert no route path starts with `/api/v1/ops/intake`; with it set → routes present.
- [ ] **Step 2: Run — FAIL** (router not present / not gated).
- [ ] **Step 3: Implement** — add `-e ../../packages/ops-intake` to `requirements.txt`; create the router module (skeleton, routes filled in Task 13); add to `main.py`:

```python
def _ops_intake_enabled() -> bool:
    return bool(os.environ.get("OPS_DEV_DSN"))

if _ops_intake_enabled():
    from api.ops_intake_router import router as ops_intake_router  # import-gated like learning
    app.include_router(ops_intake_router)
```

- [ ] **Step 4: Run — PASS.**
- [ ] **Step 5: Commit** (`-m "feat(control-plane): host-gated ops intake router skeleton + editable ops-intake install"`)

---

## Task 13: control-plane API — routes + finance-redaction

**Files:** Modify `api/ops_intake_router.py`; Test `apps/control-plane-api/tests/test_ops_intake_routes.py`.

**Interfaces (request/response, all under `/api/v1/ops/intake`):**
- `POST ` (multipart `file`, form `uploaded_by`, `content_type`) — 413 if > 25 MB; → `{run_id, status, conflict_kind, source_format, review_payload, findings:[{code,severity,ok,message}]}` (**no `diagnostic_detail`**). Calls `ops_intake.envelope.create_run`.
- `GET /{run_id}` → `{run..., review_payload, findings (PM-safe)}`.
- `POST /{run_id}/review` body `{review_payload}` → updated run; 409 if not active; 400 on cross-scope move. **(POST, not PATCH** — the global CORS at `main.py:78` allows only GET/POST/OPTIONS, so a PATCH verb would be preflight-blocked in the browser.)
- `POST /{run_id}/approve` body `{approved_by}` → 200 `{status:'approved'}`; 422 open blocking; 409 revision_blocked/not-active. Calls `approve_run`.
- `POST /{run_id}/reject` body `{reason}` → `{status:'rejected'}`.

- [ ] **Step 1: Write failing tests** (FastAPI `TestClient`, `OPS_DEV_DSN=ops_test`, schema applied): upload `mini.xlsm` bytes → 200 + `status=parsed`; **assert no response field anywhere contains the substring `diagnostic_detail` and no finding `message` contains `$`**; approve → `approved`.
- [ ] **Step 2: Run — FAIL.**
- [ ] **Step 3: Implement** the 5 handlers; map package exceptions to 400/409/422; shape findings to PM-safe (`{code,severity,ok,message}` only — drop `diagnostic_detail`); enforce the 25 MB cap before reading.
- [ ] **Step 4: Run — PASS.**
- [ ] **Step 5: Commit** (`-m "feat(control-plane): ops intake routes -- upload/preview/review/approve/reject + finance-redaction"`)

---

## Task 14: operations-web — intake API client + view-model

**Files:** Create `apps/operations-web/lib/estimator-intake.ts`; Test `apps/operations-web/tests/estimator-intake.unit.spec.ts`.

**Interfaces:**
- Produces: types `IntakeRun`, `IntakeFinding` (`{code, severity, ok, message}` — no money), `ScopeNode/TaskNode/LineNode`; `buildTree(reviewPayload): ScopeNode[]` (scope→task→**line**, hours only; each line shows its apparatus-type × qty); `fetchRun/uploadWorkbook/editReview/approveRun/rejectRun` calling `/api/v1/ops/intake*` (base URL via `lib/browser-env.ts`); `editReview` issues **POST `/{run_id}/review`** (not PATCH — CORS).

- [ ] **Step 1: Write failing unit test** — `buildTree` groups apparatus under tasks under scopes and exposes `hoursPerUnit`/`totalHours` but **no dollar fields**; a finding view-model carries `message` only.
- [ ] **Step 2: Run — FAIL** (`pnpm --filter operations-web test:unit` or the repo's unit runner; see `package.json`).
- [ ] **Step 3: Implement** `estimator-intake.ts` (mirror `lib/revenue-recognition.ts` / `lib/learning-resources.ts` client style).
- [ ] **Step 4: Run — PASS.**
- [ ] **Step 5: Commit** (`-m "feat(operations-web): estimator-intake API client + PM-safe tree view-model"`)

---

## Task 15: operations-web — intake page + no-dollars smoke

**Files:** Create `apps/operations-web/app/pm-review/estimator-intake/page.tsx`; Test `apps/operations-web/tests/browser-shell.estimator-intake.smoke.spec.ts`.

**Interfaces:** Consumes `lib/estimator-intake.ts`. A client page: upload control → on response render the scope→task→line tree (apparatus shown read-only as a per-line qty/expansion) + findings (`message`) + status; editable `hrs_per_unit` + line regroup into tasks (within scope); an Approve button disabled while any blocking finding is open or status is `revision_blocked`. **No dollar values anywhere.**

- [ ] **Step 1: Write failing route-mocked smoke** (mirror `tests/browser-shell.pm-import-admission-plan.smoke.spec.ts`): `page.route('**/api/v1/ops/intake', ...)` returns a fixed run with a 2-scope tree + one blocking + one info finding; assert the tree renders, the Approve button is disabled (blocking open), and **`await expect(page.locator('body')).not.toContainText('$')`** (no dollars).
- [ ] **Step 2: Run — FAIL** (page 404). Command: `pnpm --filter operations-web build && pnpm --filter operations-web exec playwright test browser-shell.estimator-intake -g "estimator"` (confirm exact scripts in `apps/operations-web/package.json`).
- [ ] **Step 3: Implement** `page.tsx` (mirror an existing `pm-review/*/page.tsx` client page + `route-navigation` registration if the pm-review nav requires it).
- [ ] **Step 4: Run — PASS.**
- [ ] **Step 5: Commit** (`-m "feat(operations-web): estimator-intake upload/review/approve page + no-dollars smoke"`)

---

## Task 16: Housekeeping — SSoT, MANIFEST, decisions

**Files:** Modify `reference/ops/00-MASTER-INDEX.md`, `infra/database/migrations/ops/MANIFEST.md`.

- [ ] **Step 1:** In `00-MASTER-INDEX.md`: §6/G6 → mark the extractor as existing; §7 Chip 5 → "envelope/lifecycle/UI (extractor pre-existing)"; add a **D-OPS** row capturing: parse/envelope/approve separation · no-writes-before-approve · revision-refusal (recognized=EXISTS, +billing) · N4 mandatory for `.xlsm` · supersede lifecycle · full-replacement materialization · findings finance-redaction · **global lock order `advisory(project_number) → intake_run → billing_application → project → recognition_event → apparatus`** (the verified partial order across Chips 3/4/5 — Chip 5 acquires advisory→run→project→apparatus; record the full chain so future writers respect it) · **`source='ops-intake'` ownership marker + foreign-source refusal** · **Miner-coexistence decision** (legacy Miner rows are frozen/out-of-lifecycle; approve refuses a project bearing non-`ops-intake` rows; no auto-backfill) · **`line_uid`** payload line identity (distinct from the DB `legacy_source_id`).
- [ ] **Step 2:** MANIFEST.md → add row `007 | intake_envelope | Chip 5 | ...`.
- [ ] **Step 3: Commit** (`-m "docs(ops): Chip 5 SSoT + MANIFEST -- intake envelope decisions"`). (RESUME_HERE + memory updates happen at the merge checkpoint, in the finish-branch task.)

---

## Notes for the executor
- **No domain writes before approve** is the spine — Task 8's "all domain tables count == 0 after create_run" assertion and Task 10's materialization are the two ends of it; keep both green.
- The package tests need the **full 001–007 schema** on `ops_test`; the guarded `apply_migrations` conftest fixture (Task 8) provides it and **must refuse any non-`ops_test` DSN** (it DOWN-nukes the schema on teardown — running it against `ops_dev` would destroy the Miner data).
- **The package `conftest._dsn()` default is `ops_dev`** — every DB-touching package test MUST be run with `OPS_DEV_DSN` pinned to `ops_test`. Canonical command:
  ```bash
  ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-chip5/packages/ops-intake && export PATH=$HOME/.local/bin:$PATH && set -a && . /home/olares/code/apex/apex-ops-chip5/infra/.env && set +a && OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable" uv run --with openpyxl --with "psycopg[binary]" --with pytest python -m pytest -q'
  ```
- For API/UI tasks, **read the cited neighbor first** (`main.py` ops/learning routers; `lib/revenue-recognition.ts`; `tests/browser-shell.pm-import-admission-plan.smoke.spec.ts`) and mirror its exact idiom rather than inventing one.
