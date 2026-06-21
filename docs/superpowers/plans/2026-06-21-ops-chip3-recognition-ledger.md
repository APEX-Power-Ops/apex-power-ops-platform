# Ops Chip 3 — Recognition Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the append-only, apparatus-grain revenue-recognition ledger on the clean `ops.*` substrate (migration `005`), so a tech-lead's gated approval of a completed apparatus produces a durable recognized-revenue event honoring the recognition firewall.

**Architecture:** One SQL migration `005_recognition_ledger.sql` (+ `_down` + `test_005_recognition_ledger.py`), built test-first against a throwaway `ops_test`. The migration is one file executed whole (the lane's convention); each task appends its objects to the `up` and the matching drops to the `down`, and adds its tests. Spec: `docs/superpowers/specs/2026-06-21-ops-chip3-recognition-ledger-design.md` (commit `79eca1f1`).

**Tech Stack:** PostgreSQL 17 (host `ops_dev`/`ops_test`), PL/pgSQL, pytest via `uv run --with "psycopg[binary]" --with pytest`. All work on the Olares host (worktree `/home/olares/code/apex/apex-ops-chip3`, branch `ops/chip3-recognition-ledger`) over mesh SSH.

## Global Constraints

- **Law 3 firewall:** NO recognized-$ columns on existing tables; recognized $ live only in `ops.revenue_recognition_event`. Frozen quote (`apparatus.quoted_*`, `scope_quote.*`) is read, never mutated.
- **Migration number is `005`** (001/002/003/004 taken). `_down` drops ONLY Chip-3 objects (idempotent `IF EXISTS`), never the `ops` schema or Chips 1/2/4.
- **Hard person FK:** `actor_person_id uuid NOT NULL REFERENCES ops.persons(person_id)`.
- **Gate = lead approval** via `ops.approve_and_recognize`; recognition is gated by `apparatus.status='Complete'`, assessment-independent, active-row-only (apparatus+scope+project `is_active` and non-`Cancelled`), on a frozen valid quote basis; **both** clearances required.
- **Money columns are unscaled `numeric`**; `recognized_amount` mirrors `apparatus.quoted_revenue` exactly.
- **Tests pin `OPS_DEV_DSN`/`OPS_DEV_PGPASSWORD` at `ops_test`, NOT `ops_dev`** (the fixture down-then-ups, and `ops_dev` holds the 5,344 Miner apparatus). SQL is lowercase, `$$`-quoted plpgsql, matching `002_quote_model.sql`.
- **Run a task's tests:** from the migrations dir, `OPS_DEV_PGPASSWORD=<host pw> OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=<pw> sslmode=disable" uv run --with "psycopg[binary]" --with pytest pytest test_005_recognition_ledger.py -q`. (Get the host pw from `infra/.env` `DEV_PG_PASSWORD` — SOURCE it, do not grep/cut.)

---

## File Structure

- `infra/database/migrations/ops/005_recognition_ledger.sql` — the migration (grows per task).
- `infra/database/migrations/ops/005_recognition_ledger_down.sql` — reverse drops (grows per task).
- `infra/database/migrations/ops/test_005_recognition_ledger.py` — the 24-case suite (grows per task).
- `infra/database/migrations/ops/MANIFEST.md` — add row 005 (Task 7).
- `reference/ops/00-MASTER-INDEX.md` — record the substrate-fork D-OPS decision + Chip 3 rules (Task 7).

All five live in the worktree on the host; author them there (over SSH) so the lane branch stays the single source.

---

## Task 1: Scaffold + ledger table + CHECKs + append-only + indexes

**Files:**
- Create: `infra/database/migrations/ops/005_recognition_ledger.sql`
- Create: `infra/database/migrations/ops/005_recognition_ledger_down.sql`
- Create (test): `infra/database/migrations/ops/test_005_recognition_ledger.py`

**Interfaces:**
- Consumes (from Chips 1/2/4): `ops.apparatus(id, scope_id, status, is_active, quoted_hours, quoted_revenue, assessment)`, `ops.scopes(id, project_id, is_active, status)`, `ops.projects(id, is_active, status)`, `ops.scope_quote(scope_id, is_frozen, frozen_at, blended_rate, adjusted_total, total_quoted_hours, onsite_labor,…)`, `ops.scope_quote_line(id, scope_id, qty, hrs_per_unit)`, `ops.persons(person_id)`, enum `ops.apparatus_assessment`.
- Produces: table `ops.revenue_recognition_event`, enums `ops.recognition_event_type`/`ops.obligation_clearance`, the `_seed_recognizable(conn,…)` test helper, the `apply_migrations` fixture chaining `001→002→004→005`.

- [ ] **Step 1: Write the test harness + Task-1 failing tests.** Create `test_005_recognition_ledger.py`:

```python
"""ops Chip 3 — recognition ledger: invariants + reversibility (TDD).

Builds on Chips 1 (001), 2 (002), 4 (004). Run against a THROWAWAY ops_test (NOT ops_dev,
which holds the 5,344 Miner apparatus). The fixture chains 001->002->004->005 then down-nukes.

Run (host):
  OPS_DEV_PGPASSWORD=<host pw> \
  OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=<pw> sslmode=disable" \
    uv run --with "psycopg[binary]" --with pytest pytest test_005_recognition_ledger.py -q
"""
import os
import pathlib
import uuid
from decimal import Decimal

import psycopg
import pytest

DSN = os.environ.get("OPS_DEV_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD','')} "
    "sslmode=disable"
)
HERE = pathlib.Path(__file__).parent
UP1, DOWN1 = HERE / "001_identity_skeleton.sql", HERE / "001_identity_skeleton_down.sql"
UP2 = HERE / "002_quote_model.sql"
UP4 = HERE / "004_person_anchor.sql"
UP5, DOWN5 = HERE / "005_recognition_ledger.sql", HERE / "005_recognition_ledger_down.sql"


def _exec_file(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))


def _scalar(sql, params=None):
    with psycopg.connect(DSN, autocommit=True) as c:
        row = c.execute(sql, params).fetchone()
        return row[0] if row else None


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    _exec_file(DOWN1)            # drop schema ops cascade -> clean slate
    _exec_file(UP1); _exec_file(UP2); _exec_file(UP4); _exec_file(UP5)
    yield
    _exec_file(DOWN1)


@pytest.fixture
def conn():
    with psycopg.connect(DSN) as c:
        try:
            yield c
        finally:
            c.rollback()


def _seed_recognizable(c, *, status="Complete", is_active=True, frozen=True,
                       scope_active=True, scope_status="In Progress",
                       project_active=True, project_status="Active",
                       quoted_hours=5, quoted_revenue=500):
    """Seed project->scope->scope_quote(blended_rate=100)->apparatus->person. Returns the ids PLUS the
    frozen basis (frozen_at, blended_rate, quoted_hours, quoted_revenue) so raw-insert tests can build
    rows the Task-4 insert trigger accepts. Default basis: blended_rate=100, quoted_revenue=500. NB: the
    Task-5 freeze guard forbids un-freezing — never set is_frozen=false on a frozen seed; pass frozen=False
    or set quote/apparatus values via the params instead."""
    pid = c.execute("insert into ops.projects (project_number, project_name, is_active, status) "
                    "values (%s,'t',%s,%s) returning id",
                    (f"P-{uuid.uuid4().hex[:8]}", project_active, project_status)).fetchone()[0]
    sid = c.execute("insert into ops.scopes (project_id, scope_name, is_active, status) "
                    "values (%s,'s',%s,%s) returning id",
                    (pid, scope_active, scope_status)).fetchone()[0]
    # scope_quote: P3=1000 (onsite), M4=N4=1 -> P4=1000; total_quoted_hours=10 -> blended_rate=100
    c.execute("insert into ops.scope_quote (scope_id, onsite_labor, unit_multiplier, pct_adjust, total_quoted_hours) "
              "values (%s,1000,1,1,10)", (sid,))
    if frozen:
        c.execute("update ops.scope_quote set is_frozen=true, frozen_at=now() where scope_id=%s", (sid,))
    aid = c.execute("insert into ops.apparatus (scope_id, apparatus_designation, status, is_active, "
                    "assessment, quoted_hours, quoted_revenue) values (%s,'A-1',%s,%s,'Pass',%s,%s) returning id",
                    (sid, status, is_active, quoted_hours, quoted_revenue)).fetchone()[0]
    person = c.execute("insert into ops.persons (display_name) values ('Lead') returning person_id").fetchone()[0]
    fz, br = c.execute("select frozen_at, blended_rate from ops.scope_quote where scope_id=%s", (sid,)).fetchone()
    return {"project": pid, "scope": sid, "apparatus": aid, "person": person,
            "frozen_at": fz, "blended_rate": br, "quoted_hours": quoted_hours, "quoted_revenue": quoted_revenue}


def _insert_recognized(c, s, **over):
    """Raw-insert a recognized row consistent with seed s's frozen basis; `over` replaces fields to drive
    one specific CHECK/FK while leaving everything else valid (so the Task-4 trigger passes it through to
    the constraint under test). Returns the new event id when the insert succeeds."""
    cols = dict(apparatus_id=s["apparatus"], scope_id=s["scope"], project_id=s["project"],
                event_type="recognized", recognized_amount=s["quoted_revenue"],
                quoted_hours=s["quoted_hours"], blended_rate=s["blended_rate"],
                basis_frozen_at=s["frozen_at"], actor_person_id=s["person"],
                datasheet_clearance="not_applicable", datasheet_ref=None,
                cx_clearance="not_applicable", cx_ref=None)
    cols.update(over)
    keys = ", ".join(cols.keys()); ph = ", ".join(["%s"] * len(cols))
    return c.execute(f"insert into ops.revenue_recognition_event ({keys}) values ({ph}) returning id",
                     tuple(cols.values())).fetchone()[0]


# ---- Task 1: structure + CHECKs + append-only ----
# These raw-insert negative tests build a basis-consistent row via _insert_recognized and override ONE
# field, so the Task-4 insert trigger (added later) passes the row through to the constraint under test.

def test_event_table_and_enums_exist():
    assert _scalar("select to_regclass('ops.revenue_recognition_event') is not null") is True
    labels = _scalar(
        "select array_agg(e.enumlabel order by e.enumsortorder) from pg_enum e join pg_type t on t.oid=e.enumtypid "
        "join pg_namespace n on n.oid=t.typnamespace where n.nspname='ops' and t.typname='obligation_clearance'")
    assert labels == ["provided", "not_applicable"]


def test_actor_fk_targets_persons(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        _insert_recognized(conn, s, actor_person_id=str(uuid.uuid4()))


def test_recognized_requires_both_clearances(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.CheckViolation):       # cx_clearance NULL on a recognized row
        _insert_recognized(conn, s, datasheet_clearance="provided", datasheet_ref="FS-1", cx_clearance=None)


def test_clearance_ref_coherence(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.CheckViolation):       # provided + blank ref
        _insert_recognized(conn, s, datasheet_clearance="provided", datasheet_ref="   ")


def test_append_only_blocks_update_and_delete(conn):
    s = _seed_recognizable(conn)
    eid = _insert_recognized(conn, s)
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("update ops.revenue_recognition_event set reason='x' where id=%s", (eid,))
    conn.rollback()
    eid = _insert_recognized(conn, s)
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("delete from ops.revenue_recognition_event where id=%s", (eid,))
```

- [ ] **Step 2: Run — verify the Task-1 tests fail** (migration file empty/missing).

Run: `… pytest test_005_recognition_ledger.py -q`
Expected: errors (UP5 file missing / `ops.revenue_recognition_event` does not exist).

- [ ] **Step 3: Write the migration head (enums + table + CHECKs + append-only + indexes).** Create `005_recognition_ledger.sql`:

```sql
-- ============================================================================
-- ops Chip 3 — recognition ledger (append-only revenue recognition on ops.*).
-- Builds on Chips 1/2/4. Dev DB: ops_dev / ops_test. Nothing applied to prod.
-- Law 3 firewall: recognized $ live ONLY here; frozen quote is read, never mutated.
-- Spec: docs/superpowers/specs/2026-06-21-ops-chip3-recognition-ledger-design.md
-- ============================================================================

create type ops.recognition_event_type as enum ('recognized','reversal');
create type ops.obligation_clearance  as enum ('provided','not_applicable');

create table ops.revenue_recognition_event (
  id                  uuid primary key default gen_random_uuid(),
  apparatus_id        uuid not null references ops.apparatus(id),
  scope_id            uuid not null references ops.scopes(id),
  project_id          uuid not null references ops.projects(id),
  event_type          ops.recognition_event_type not null,
  recognized_amount   numeric not null,                      -- signed; mirrors apparatus.quoted_revenue
  quoted_hours        numeric,                               -- basis snapshot (required on recognized)
  blended_rate        numeric,                               -- basis snapshot (required on recognized)
  basis_frozen_at     timestamptz,                           -- scope_quote.frozen_at (required on recognized)
  assessment          ops.apparatus_assessment,              -- stamped, non-gating
  actor_person_id     uuid not null references ops.persons(person_id),
  datasheet_clearance ops.obligation_clearance,
  datasheet_ref       text,
  cx_clearance        ops.obligation_clearance,
  cx_ref              text,
  reverses_event_id   uuid references ops.revenue_recognition_event(id),
  reason              text,
  recognized_at       timestamptz not null default now(),
  created_at          timestamptz not null default now(),
  constraint ck_revrec_event_shape check (
    case event_type
      when 'recognized' then
        recognized_amount > 0 and reverses_event_id is null
        and datasheet_clearance is not null and cx_clearance is not null
        and quoted_hours is not null and quoted_hours > 0
        and blended_rate is not null and basis_frozen_at is not null
      when 'reversal' then
        recognized_amount < 0 and reverses_event_id is not null
        and reason is not null and btrim(reason) <> ''
    end
  ),
  constraint ck_revrec_datasheet_ref check (
    datasheet_clearance is distinct from 'provided'
    or (datasheet_ref is not null and btrim(datasheet_ref) <> '')
  ),
  constraint ck_revrec_cx_ref check (
    cx_clearance is distinct from 'provided'
    or (cx_ref is not null and btrim(cx_ref) <> '')
  )
);
comment on table ops.revenue_recognition_event is
  'Append-only apparatus-grain recognized-revenue ledger (Chip 3). recognized + reversal as signed rows; net per apparatus = sum(recognized_amount). Law 3 firewall.';

-- append-only: block UPDATE/DELETE
create or replace function ops.trg_revrec_immutable() returns trigger language plpgsql as $$
begin
  raise exception 'ops.revenue_recognition_event is append-only (% blocked)', tg_op;
end;
$$;
create trigger revrec_immutable before update or delete on ops.revenue_recognition_event
  for each row execute function ops.trg_revrec_immutable();

create index ix_revrec_apparatus on ops.revenue_recognition_event(apparatus_id);
create index ix_revrec_scope     on ops.revenue_recognition_event(scope_id);
create index ix_revrec_project   on ops.revenue_recognition_event(project_id);
create unique index uq_revrec_one_reversal
  on ops.revenue_recognition_event(reverses_event_id) where event_type='reversal';
```

- [ ] **Step 4: Write the down head.** Create `005_recognition_ledger_down.sql`:

```sql
-- ============================================================================
-- DOWN — ops Chip 3 recognition ledger. Undoes ONLY Chip 3 (leaves Chips 1/2/4
-- intact). Idempotent (IF EXISTS). Order: views -> parent-table guards -> the two
-- recognition functions -> event table (cascade drops its triggers) -> enums.
-- ============================================================================
drop view if exists ops.v_project_recognition;
drop view if exists ops.v_scope_recognition;
drop view if exists ops.v_apparatus_recognition;
drop view if exists ops.v_recognition_review_queue;

drop trigger if exists apparatus_protect_recognition on ops.apparatus;
drop trigger if exists apparatus_freeze_guard        on ops.apparatus;
drop trigger if exists scope_protect_recognition     on ops.scopes;
drop trigger if exists project_protect_recognition   on ops.projects;
drop trigger if exists scope_quote_freeze_guard      on ops.scope_quote;
drop function if exists ops.trg_apparatus_protect_recognition() cascade;
drop function if exists ops.trg_apparatus_freeze_guard()        cascade;
drop function if exists ops.trg_scope_protect_recognition()     cascade;
drop function if exists ops.trg_project_protect_recognition()   cascade;
drop function if exists ops.trg_scope_quote_freeze_guard()      cascade;

drop function if exists ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text) cascade;
drop function if exists ops.reverse_recognition(uuid,uuid,text) cascade;

drop table if exists ops.revenue_recognition_event cascade;
drop function if exists ops.trg_revrec_immutable() cascade;
drop function if exists ops.trg_revrec_insert_integrity() cascade;

drop type if exists ops.obligation_clearance;
drop type if exists ops.recognition_event_type;
```

- [ ] **Step 5: Run — verify the Task-1 tests pass.**

Run: `… pytest test_005_recognition_ledger.py -q`
Expected: 5 passed.

- [ ] **Step 6: Commit.**

```bash
git add infra/database/migrations/ops/005_recognition_ledger.sql \
        infra/database/migrations/ops/005_recognition_ledger_down.sql \
        infra/database/migrations/ops/test_005_recognition_ledger.py
git commit -m "feat(ops): Chip 3 task 1 — recognition ledger table + CHECKs + append-only"
```

---

## Task 2: `ops.approve_and_recognize`

**Files:**
- Modify: `infra/database/migrations/ops/005_recognition_ledger.sql` (append the function)
- Modify (test): `infra/database/migrations/ops/test_005_recognition_ledger.py`

**Interfaces:**
- Produces: `ops.approve_and_recognize(p_apparatus_id uuid, p_actor_person_id uuid, p_datasheet_clearance ops.obligation_clearance, p_datasheet_ref text, p_cx_clearance ops.obligation_clearance, p_cx_ref text) returns uuid`.

- [ ] **Step 1: Append the Task-2 failing tests** to `test_005_recognition_ledger.py`:

```python
# ---- Task 2: approve_and_recognize ----

def _recognize(c, s, ds=("not_applicable", None), cx=("not_applicable", None)):
    return c.execute("select ops.approve_and_recognize(%s,%s,%s,%s,%s,%s)",
                     (s["apparatus"], s["person"], ds[0], ds[1], cx[0], cx[1])).fetchone()[0]


def test_recognize_happy_path(conn):
    s = _seed_recognizable(conn)
    eid = _recognize(conn, s, ds=("provided", "FS-1"), cx=("provided", "CX-1"))
    row = conn.execute("select event_type, recognized_amount, quoted_hours, blended_rate, basis_frozen_at, "
                       "actor_person_id from ops.revenue_recognition_event where id=%s", (eid,)).fetchone()
    assert row[0] == "recognized"
    assert row[1] == Decimal("500") and row[2] == Decimal("5") and row[3] == Decimal("100")
    assert row[4] is not None and row[5] == s["person"]
    net = conn.execute("select sum(recognized_amount) from ops.revenue_recognition_event where apparatus_id=%s",
                       (s["apparatus"],)).fetchone()[0]
    assert net == Decimal("500")


def test_recognize_requires_complete(conn):
    s = _seed_recognizable(conn, status="In Progress")
    with pytest.raises(psycopg.errors.RaiseException, match="not testing-complete"):
        _recognize(conn, s)


def test_recognize_assessment_independent(conn):
    s = _seed_recognizable(conn)
    conn.execute("update ops.apparatus set assessment='Fail' where id=%s", (s["apparatus"],))
    eid = _recognize(conn, s)
    assert eid is not None


def test_recognize_requires_frozen_basis(conn):
    s = _seed_recognizable(conn, frozen=False)
    with pytest.raises(psycopg.errors.RaiseException, match="not frozen"):
        _recognize(conn, s)


def test_recognize_requires_valid_quote(conn):
    s = _seed_recognizable(conn, quoted_revenue=None)   # frozen basis, but apparatus has no quoted_revenue
    with pytest.raises(psycopg.errors.RaiseException, match="invalid quote basis"):
        _recognize(conn, s)


def test_recognize_requires_both_clearances_fn(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.RaiseException, match="clearances required"):
        conn.execute("select ops.approve_and_recognize(%s,%s,null,null,%s,%s)",
                     (s["apparatus"], s["person"], "not_applicable", None))


def test_recognize_active_row_gate(conn):
    s = _seed_recognizable(conn, scope_status="Cancelled")
    with pytest.raises(psycopg.errors.RaiseException, match="inactive/cancelled"):
        _recognize(conn, s)


def test_recognize_actor_fk(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        conn.execute("select ops.approve_and_recognize(%s,%s,%s,%s,%s,%s)",
                     (s["apparatus"], str(uuid.uuid4()), "not_applicable", None, "not_applicable", None))


def test_recognize_idempotent(conn):
    s = _seed_recognizable(conn)
    _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException, match="already recognized"):
        _recognize(conn, s)
```

- [ ] **Step 2: Run — verify they fail** (`function ops.approve_and_recognize does not exist`).

- [ ] **Step 3: Append the function** to `005_recognition_ledger.sql`:

```sql
-- ---- gated recognition primitive -------------------------------------------
create or replace function ops.approve_and_recognize(
  p_apparatus_id        uuid,
  p_actor_person_id     uuid,
  p_datasheet_clearance ops.obligation_clearance,
  p_datasheet_ref       text,
  p_cx_clearance        ops.obligation_clearance,
  p_cx_ref              text
) returns uuid language plpgsql as $$
declare a record; sq record; v_net numeric; v_id uuid;
begin
  select a2.scope_id, a2.status, a2.is_active, a2.quoted_hours, a2.quoted_revenue, a2.assessment,
         s.project_id, s.is_active as scope_active, s.status as scope_status,
         p.is_active as project_active, p.status as project_status
    into a
    from ops.apparatus a2
    join ops.scopes s   on s.id = a2.scope_id
    join ops.projects p on p.id = s.project_id
   where a2.id = p_apparatus_id
   for update of a2;                                 -- row lock serializes concurrent approvals
  if not found then raise exception 'apparatus % not found', p_apparatus_id; end if;
  if a.status <> 'Complete' then
    raise exception 'apparatus % not testing-complete (status=%)', p_apparatus_id, a.status;
  end if;
  if not (a.is_active and a.scope_active and a.project_active
          and a.scope_status <> 'Cancelled' and a.project_status <> 'Cancelled') then
    raise exception 'apparatus % inactive/cancelled chain cannot recognize', p_apparatus_id;
  end if;
  select sq2.is_frozen, sq2.frozen_at, sq2.blended_rate into sq
    from ops.scope_quote sq2 where sq2.scope_id = a.scope_id;
  if not found or not sq.is_frozen or sq.frozen_at is null then
    raise exception 'scope % quote basis not frozen', a.scope_id;
  end if;
  if a.quoted_hours is null or a.quoted_hours <= 0
     or a.quoted_revenue is null or a.quoted_revenue <= 0 then
    raise exception 'apparatus % invalid quote basis', p_apparatus_id;
  end if;
  if p_datasheet_clearance is null or p_cx_clearance is null then
    raise exception 'both datasheet and cx clearances required';
  end if;
  select coalesce(sum(recognized_amount),0) into v_net
    from ops.revenue_recognition_event where apparatus_id = p_apparatus_id;
  if v_net > 0 then raise exception 'apparatus % already recognized', p_apparatus_id; end if;
  insert into ops.revenue_recognition_event
    (apparatus_id, scope_id, project_id, event_type, recognized_amount,
     quoted_hours, blended_rate, basis_frozen_at, assessment, actor_person_id,
     datasheet_clearance, datasheet_ref, cx_clearance, cx_ref)
  values
    (p_apparatus_id, a.scope_id, a.project_id, 'recognized', a.quoted_revenue,
     a.quoted_hours, sq.blended_rate, sq.frozen_at, a.assessment, p_actor_person_id,
     p_datasheet_clearance, p_datasheet_ref, p_cx_clearance, p_cx_ref)
  returning id into v_id;
  return v_id;
end;
$$;
```

- [ ] **Step 4: Run — verify all Task 1+2 tests pass.** Expected: 14 passed.

- [ ] **Step 5: Commit.**

```bash
git add -A && git commit -m "feat(ops): Chip 3 task 2 — approve_and_recognize gated primitive"
```

---

## Task 3: `ops.reverse_recognition`

**Files:** Modify `005_recognition_ledger.sql` (append) + the test file.

**Interfaces:**
- Produces: `ops.reverse_recognition(p_event_id uuid, p_actor_person_id uuid, p_reason text) returns uuid`.

- [ ] **Step 1: Append the Task-3 failing tests:**

```python
# ---- Task 3: reverse_recognition ----

def test_reversal_then_rerecognize(conn):
    s = _seed_recognizable(conn)
    eid = _recognize(conn, s)
    rid = conn.execute("select ops.reverse_recognition(%s,%s,%s)", (eid, s["person"], "rework")).fetchone()[0]
    net = conn.execute("select coalesce(sum(recognized_amount),0) from ops.revenue_recognition_event "
                       "where apparatus_id=%s", (s["apparatus"],)).fetchone()[0]
    assert net == Decimal("0")
    rev = conn.execute("select event_type, recognized_amount, reverses_event_id from "
                       "ops.revenue_recognition_event where id=%s", (rid,)).fetchone()
    assert rev[0] == "reversal" and rev[1] == Decimal("-500") and rev[2] == eid
    eid2 = _recognize(conn, s)   # re-recognition allowed at net 0
    assert eid2 is not None


def test_reversal_requires_reason(conn):
    s = _seed_recognizable(conn)
    eid = _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException, match="reason required"):
        conn.execute("select ops.reverse_recognition(%s,%s,%s)", (eid, s["person"], "   "))


def test_one_reversal_per_event(conn):
    s = _seed_recognizable(conn)
    eid = _recognize(conn, s)
    conn.execute("select ops.reverse_recognition(%s,%s,%s)", (eid, s["person"], "first"))
    with pytest.raises(psycopg.errors.RaiseException, match="already reversed"):
        conn.execute("select ops.reverse_recognition(%s,%s,%s)", (eid, s["person"], "second"))
```

- [ ] **Step 2: Run — verify they fail** (`function ops.reverse_recognition does not exist`).

- [ ] **Step 3: Append the function** to `005_recognition_ledger.sql`:

```sql
-- ---- reversal primitive ----------------------------------------------------
create or replace function ops.reverse_recognition(
  p_event_id uuid, p_actor_person_id uuid, p_reason text
) returns uuid language plpgsql as $$
declare e record; v_id uuid;
begin
  if p_reason is null or btrim(p_reason) = '' then raise exception 'reason required for reversal'; end if;
  select apparatus_id, scope_id, project_id, event_type, recognized_amount into e
    from ops.revenue_recognition_event where id = p_event_id for update;
  if not found then raise exception 'event % not found', p_event_id; end if;
  if e.event_type <> 'recognized' then
    raise exception 'can only reverse a recognized event (% is %)', p_event_id, e.event_type;
  end if;
  perform 1 from ops.apparatus where id = e.apparatus_id for update;   -- coordinate with approve
  if exists (select 1 from ops.revenue_recognition_event where reverses_event_id = p_event_id) then
    raise exception 'event % already reversed', p_event_id;
  end if;
  insert into ops.revenue_recognition_event
    (apparatus_id, scope_id, project_id, event_type, recognized_amount,
     actor_person_id, reverses_event_id, reason)
  values
    (e.apparatus_id, e.scope_id, e.project_id, 'reversal', -e.recognized_amount,
     p_actor_person_id, p_event_id, p_reason)
  returning id into v_id;
  return v_id;
end;
$$;
```

- [ ] **Step 4: Run — verify Tasks 1–3 pass.** Expected: 17 passed.

- [ ] **Step 5: Commit.** `git add -A && git commit -m "feat(ops): Chip 3 task 3 — reverse_recognition"`

---

## Task 4: BEFORE INSERT invariant trigger

**Files:** Modify `005_recognition_ledger.sql` (append the trigger) + the test file.

**Interfaces:**
- Produces: `ops.trg_revrec_insert_integrity()` + trigger `revrec_insert_integrity`. After this, ANY direct insert must satisfy lineage + (recognized: active chain, Complete, frozen basis, `recognized_amount = apparatus.quoted_revenue`, snapshot match, **idempotency — no second open recognition per apparatus**) + (reversal: target is a recognized event for the same apparatus, `recognized_amount = -(original)`). The trigger takes `FOR UPDATE` on the apparatus row in the recognized branch, serializing concurrent direct inserts the same way the function does, and then rejects the insert when prior net recognized > 0. The direct-insert path therefore cannot bypass idempotency enforcement. The function keeps its own net-check as the friendlier-error path; both coexist. The functions already produce conforming rows.

- [ ] **Step 1: Append the Task-4 failing tests:**

```python
# ---- Task 4: insert-invariant trigger ----

def _base_recognized_cols(s):
    return ("apparatus_id, scope_id, project_id, event_type, recognized_amount, quoted_hours, blended_rate, "
            "basis_frozen_at, actor_person_id, datasheet_clearance, cx_clearance")


def test_insert_lineage_mismatch(conn):
    s = _seed_recognizable(conn)
    other_scope = _seed_recognizable(conn)["scope"]
    with pytest.raises(psycopg.errors.RaiseException, match="lineage"):
        conn.execute(
            f"insert into ops.revenue_recognition_event ({_base_recognized_cols(s)}) "
            "values (%s,%s,%s,'recognized',500,5,100,now(),%s,'not_applicable','not_applicable')",
            (s["apparatus"], other_scope, s["project"], s["person"]))   # scope_id != apparatus lineage


def test_insert_recognized_requires_complete(conn):
    s = _seed_recognizable(conn, status="In Progress")
    with pytest.raises(psycopg.errors.RaiseException, match="non-complete"):
        conn.execute(
            f"insert into ops.revenue_recognition_event ({_base_recognized_cols(s)}) "
            "values (%s,%s,%s,'recognized',500,5,100,now(),%s,'not_applicable','not_applicable')",
            (s["apparatus"], s["scope"], s["project"], s["person"]))


def test_insert_recognized_amount_must_match_quote(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.RaiseException, match="quoted_revenue"):
        conn.execute(
            f"insert into ops.revenue_recognition_event ({_base_recognized_cols(s)}) "
            "values (%s,%s,%s,'recognized',499,5,100,now(),%s,'not_applicable','not_applicable')",  # 499 != 500
            (s["apparatus"], s["scope"], s["project"], s["person"]))


def test_insert_recognized_snapshot_must_match(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.RaiseException, match="snapshot"):
        conn.execute(
            f"insert into ops.revenue_recognition_event ({_base_recognized_cols(s)}) "
            "values (%s,%s,%s,'recognized',500,5,999,now(),%s,'not_applicable','not_applicable')",  # blended 999 != 100
            (s["apparatus"], s["scope"], s["project"], s["person"]))


def test_insert_reversal_amount_must_equal_negative_original(conn):
    s = _seed_recognizable(conn)
    eid = _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException, match="reversal amount"):
        conn.execute(
            "insert into ops.revenue_recognition_event "
            "(apparatus_id, scope_id, project_id, event_type, recognized_amount, actor_person_id, reverses_event_id, reason) "
            "values (%s,%s,%s,'reversal',-499,%s,%s,'bad')",   # -499 != -500
            (s["apparatus"], s["scope"], s["project"], s["person"], eid))
```

- [ ] **Step 2: Run — verify they fail** (no trigger yet → the bad rows insert successfully, so the `pytest.raises` blocks fail).

- [ ] **Step 3: Append the trigger** to `005_recognition_ledger.sql`:

```sql
-- ---- insert integrity: direct inserts cannot bypass the function gate -------
create or replace function ops.trg_revrec_insert_integrity() returns trigger language plpgsql as $$
declare v_scope uuid; a record; sq record; orig record;
begin
  -- lineage (all rows)
  select scope_id into v_scope from ops.apparatus where id = new.apparatus_id;
  if not found then raise exception 'apparatus % not found', new.apparatus_id; end if;
  if new.scope_id <> v_scope then raise exception 'scope_id lineage mismatch'; end if;
  if new.project_id <> (select project_id from ops.scopes where id = new.scope_id) then
    raise exception 'project_id lineage mismatch';
  end if;

  if new.event_type = 'recognized' then
    select a2.status, a2.is_active, a2.quoted_hours, a2.quoted_revenue,
           s.is_active as scope_active, s.status as scope_status,
           p.is_active as project_active, p.status as project_status
      into a
      from ops.apparatus a2 join ops.scopes s on s.id=a2.scope_id join ops.projects p on p.id=s.project_id
     where a2.id = new.apparatus_id
     for update of a2;                         -- FIX-A: lock serializes concurrent direct inserts
    if not (a.is_active and a.scope_active and a.project_active
            and a.scope_status <> 'Cancelled' and a.project_status <> 'Cancelled') then
      raise exception 'recognized row for inactive/cancelled chain';
    end if;
    if a.status <> 'Complete' then raise exception 'recognized row for non-complete apparatus'; end if;
    select is_frozen, frozen_at, blended_rate into sq from ops.scope_quote where scope_id = new.scope_id;
    if not found or not sq.is_frozen or sq.frozen_at is null then
      raise exception 'recognized row on unfrozen basis';
    end if;
    if new.recognized_amount is distinct from a.quoted_revenue then  -- FIX-B: null-safe comparison
      raise exception 'recognized_amount must equal apparatus.quoted_revenue';
    end if;
    if new.quoted_hours is distinct from a.quoted_hours
       or new.blended_rate is distinct from sq.blended_rate
       or new.basis_frozen_at is distinct from sq.frozen_at then
      raise exception 'recognized row snapshot does not match current basis';
    end if;
    -- FIX-A: idempotency gate — reject if apparatus already has an open net recognition
    -- (BEFORE INSERT fires before the new row exists, so sum reflects only prior rows)
    if (select coalesce(sum(recognized_amount),0)
          from ops.revenue_recognition_event where apparatus_id = new.apparatus_id) > 0 then
      raise exception 'apparatus % already has an open recognition', new.apparatus_id;
    end if;
  elsif new.event_type = 'reversal' then
    select apparatus_id, recognized_amount into orig
      from ops.revenue_recognition_event where id = new.reverses_event_id and event_type='recognized';
    if not found then raise exception 'reversal target is not a recognized event'; end if;
    if orig.apparatus_id <> new.apparatus_id then raise exception 'reversal apparatus mismatch'; end if;
    if new.recognized_amount <> -orig.recognized_amount then raise exception 'reversal amount must equal -(original)'; end if;
  end if;
  return new;
end;
$$;
create trigger revrec_insert_integrity before insert on ops.revenue_recognition_event
  for each row execute function ops.trg_revrec_insert_integrity();
```

**Note (post-review fix waves):** The live trigger above reflects two fix waves applied after the initial implementation: FIX-A adds `for update of a2` on the recognized-branch apparatus select (serializes concurrent direct inserts, same as the function) and appends an idempotency gate at the end of the recognized branch (rejects a second recognized insert when prior net > 0); FIX-B changes the `recognized_amount` equality check from `<>` to `is distinct from` for null-safety. The trigger therefore enforces idempotency directly — the direct-insert path cannot bypass it. The function keeps its own net-check as a friendlier-error path; both coexist.

- [ ] **Step 4: Run — verify all Tasks 1–4 pass.** Expected: 22 passed (+ 5 net-new tests from the two fix waves covering idempotency/null-safety/ceiling-grain hardening; final suite = 36 after all fix-wave tests added). (The Task-1 CHECK tests still pass — `_insert_recognized` keeps every other field basis-consistent, so the insert trigger passes the row through and the targeted CHECK/FK fires; the function tests still pass — functions emit conforming rows.)

- [ ] **Step 5: Commit.** `git add -A && git commit -m "feat(ops): Chip 3 task 4 — insert-invariant trigger"`

---

## Task 5: Lifecycle protection + frozen-basis immutability guards

**Files:** Modify `005_recognition_ledger.sql` (append the five guard functions/triggers) + the test file.

**Interfaces:**
- Produces guard triggers: `apparatus_protect_recognition` + `apparatus_freeze_guard` on `ops.apparatus`; `scope_protect_recognition` on `ops.scopes`; `project_protect_recognition` on `ops.projects`; `scope_quote_freeze_guard` on `ops.scope_quote`.

- [ ] **Step 1: Append the Task-5 failing tests:**

```python
# ---- Task 5: protection + freeze-immutability guards ----

def test_protect_apparatus_uncomplete_and_deactivate(conn):
    s = _seed_recognizable(conn)
    eid = _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException, match="open recognition"):
        conn.execute("update ops.apparatus set status='In Progress' where id=%s", (s["apparatus"],))
    conn.rollback()
    s = _seed_recognizable(conn); eid = _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException, match="open recognition"):
        conn.execute("update ops.apparatus set is_active=false where id=%s", (s["apparatus"],))
    conn.rollback()
    s = _seed_recognizable(conn); eid = _recognize(conn, s)
    conn.execute("select ops.reverse_recognition(%s,%s,%s)", (eid, s["person"], "x"))
    conn.execute("update ops.apparatus set status='In Progress' where id=%s", (s["apparatus"],))  # ok after reverse


def test_protect_scope_and_project(conn):
    s = _seed_recognizable(conn)
    _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException, match="open recognition"):
        conn.execute("update ops.scopes set status='Cancelled' where id=%s", (s["scope"],))
    conn.rollback()
    s = _seed_recognizable(conn); _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException, match="open recognition"):
        conn.execute("update ops.projects set is_active=false where id=%s", (s["project"],))


def test_basis_immutability_guard(conn):
    s = _seed_recognizable(conn)   # already frozen
    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        conn.execute("update ops.scope_quote set onsite_labor=2000 where scope_id=%s", (s["scope"],))
    conn.rollback()
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        conn.execute("update ops.apparatus set quoted_revenue=999 where id=%s", (s["apparatus"],))
    conn.rollback()
    # before freeze: edit allowed
    s = _seed_recognizable(conn, frozen=False)
    conn.execute("update ops.scope_quote set onsite_labor=2000 where scope_id=%s", (s["scope"],))  # ok


def test_post_freeze_line_edit_blocked(conn):
    # build a scope with a line driving J3, then freeze, then edit the line -> transitive block
    pid = conn.execute("insert into ops.projects (project_number, project_name) values (%s,'t') returning id",
                       (f"P-{uuid.uuid4().hex[:8]}",)).fetchone()[0]
    sid = conn.execute("insert into ops.scopes (project_id, scope_name) values (%s,'s') returning id",
                       (pid,)).fetchone()[0]
    conn.execute("insert into ops.scope_quote (scope_id, onsite_labor, unit_multiplier, pct_adjust) values (%s,1000,1,1)", (sid,))
    lid = conn.execute("insert into ops.scope_quote_line (scope_id, apparatus_type, qty, hrs_per_unit) "
                       "values (%s,'A',2,5) returning id", (sid,)).fetchone()[0]   # J3 -> 10
    conn.execute("update ops.scope_quote set is_frozen=true, frozen_at=now() where scope_id=%s", (sid,))
    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        conn.execute("update ops.scope_quote_line set hrs_per_unit=9 where id=%s", (lid,))  # J3 recompute hits frozen guard
```

- [ ] **Step 2: Run — verify they fail** (no guards yet → the updates succeed, `pytest.raises` blocks fail).

- [ ] **Step 3: Append the five guards** to `005_recognition_ledger.sql`:

```sql
-- ---- Component 4: recognition-protection guards (reverse-first) -------------
create or replace function ops.trg_apparatus_protect_recognition() returns trigger language plpgsql as $$
declare v_net numeric;
begin
  if (old.status='Complete' and new.status<>'Complete') or (old.is_active and not new.is_active) then
    select coalesce(sum(recognized_amount),0) into v_net
      from ops.revenue_recognition_event where apparatus_id = new.id;
    if v_net > 0 then raise exception 'apparatus % has open recognition; reverse first', new.id; end if;
  end if;
  return new;
end;
$$;
create trigger apparatus_protect_recognition before update on ops.apparatus
  for each row execute function ops.trg_apparatus_protect_recognition();

create or replace function ops.trg_scope_protect_recognition() returns trigger language plpgsql as $$
declare v_net numeric;
begin
  if (old.is_active and not new.is_active) or (new.status='Cancelled' and old.status<>'Cancelled') then
    select coalesce(sum(recognized_amount),0) into v_net
      from ops.revenue_recognition_event where scope_id = new.id;
    if v_net > 0 then raise exception 'scope % has open recognition; reverse first', new.id; end if;
  end if;
  return new;
end;
$$;
create trigger scope_protect_recognition before update on ops.scopes
  for each row execute function ops.trg_scope_protect_recognition();

create or replace function ops.trg_project_protect_recognition() returns trigger language plpgsql as $$
declare v_net numeric;
begin
  if (old.is_active and not new.is_active) or (new.status='Cancelled' and old.status<>'Cancelled') then
    select coalesce(sum(recognized_amount),0) into v_net
      from ops.revenue_recognition_event where project_id = new.id;
    if v_net > 0 then raise exception 'project % has open recognition; reverse first', new.id; end if;
  end if;
  return new;
end;
$$;
create trigger project_protect_recognition before update on ops.projects
  for each row execute function ops.trg_project_protect_recognition();

-- ---- Component 5: frozen-basis immutability (completes the Chip 2 freeze) ---
create or replace function ops.trg_scope_quote_freeze_guard() returns trigger language plpgsql as $$
begin
  if old.is_frozen and (
       new.onsite_labor       is distinct from old.onsite_labor
    or new.offsite_labor      is distinct from old.offsite_labor
    or new.travel             is distinct from old.travel
    or new.outside_services   is distinct from old.outside_services
    or new.unit_multiplier    is distinct from old.unit_multiplier
    or new.pct_adjust         is distinct from old.pct_adjust
    or new.total_quoted_hours is distinct from old.total_quoted_hours
    or new.is_frozen          is distinct from old.is_frozen
    or new.frozen_at          is distinct from old.frozen_at) then
    raise exception 'frozen quote basis is immutable (scope %)', old.scope_id;
  end if;
  return new;
end;
$$;
create trigger scope_quote_freeze_guard before update on ops.scope_quote
  for each row execute function ops.trg_scope_quote_freeze_guard();

create or replace function ops.trg_apparatus_freeze_guard() returns trigger language plpgsql as $$
declare v_frozen boolean;
begin
  if new.quoted_hours   is distinct from old.quoted_hours
     or new.quoted_revenue is distinct from old.quoted_revenue
     or new.quote_line_id  is distinct from old.quote_line_id then
    select is_frozen into v_frozen from ops.scope_quote where scope_id = old.scope_id;
    if coalesce(v_frozen,false) then
      raise exception 'apparatus quote columns immutable once scope quote frozen (apparatus %)', old.id;
    end if;
  end if;
  return new;
end;
$$;
create trigger apparatus_freeze_guard before update on ops.apparatus
  for each row execute function ops.trg_apparatus_freeze_guard();
```

- [ ] **Step 4: Run — verify all Tasks 1–5 pass.** Expected: 26 passed.

- [ ] **Step 5: Commit.** `git add -A && git commit -m "feat(ops): Chip 3 task 5 — lifecycle protection + frozen-basis immutability guards"`

---

## Task 6: Views + rollups

**Files:** Modify `005_recognition_ledger.sql` (append the four views) + the test file.

**Interfaces:**
- Produces views: `ops.v_recognition_review_queue`, `ops.v_apparatus_recognition`, `ops.v_scope_recognition`, `ops.v_project_recognition`.

- [ ] **Step 1: Append the Task-6 failing tests:**

```python
# ---- Task 6: views + rollups ----

def test_review_queue_lists_complete_unrecognized(conn):
    s = _seed_recognizable(conn)
    n = conn.execute("select count(*) from ops.v_recognition_review_queue where apparatus_id=%s",
                     (s["apparatus"],)).fetchone()[0]
    assert n == 1
    _recognize(conn, s)
    n2 = conn.execute("select count(*) from ops.v_recognition_review_queue where apparatus_id=%s",
                      (s["apparatus"],)).fetchone()[0]
    assert n2 == 0   # leaves the queue once recognized


def test_apparatus_recognition_view(conn):
    s = _seed_recognizable(conn)
    _recognize(conn, s)
    row = conn.execute("select net_recognized, is_recognized, actor_person_id "
                       "from ops.v_apparatus_recognition where apparatus_id=%s", (s["apparatus"],)).fetchone()
    assert row[0] == Decimal("500") and row[1] is True and row[2] == s["person"]


def test_scope_recognition_surfaces_synthetic_residual(conn):
    # the default seed IS synthetic-residual: scope adjusted_total=1000 (P4) but the single
    # apparatus ceiling is 500 -> residual 500. (No un-freeze needed; the freeze guard forbids it.)
    s = _seed_recognizable(conn)
    _recognize(conn, s)
    row = conn.execute("select recognized_total, apparatus_ceiling, scope_adjusted_total, residual "
                       "from ops.v_scope_recognition where scope_id=%s", (s["scope"],)).fetchone()
    assert row[0] == Decimal("500") and row[1] == Decimal("500")
    assert row[2] == Decimal("1000") and row[3] == Decimal("500")   # 1000 - 500
    assert row[0] <= row[1]   # recognized never exceeds the apparatus ceiling


def test_project_recognition_rollup(conn):
    s = _seed_recognizable(conn)
    _recognize(conn, s)
    rec = conn.execute("select recognized_total from ops.v_project_recognition where project_id=%s",
                       (s["project"],)).fetchone()[0]
    assert rec == Decimal("500")
```

- [ ] **Step 2: Run — verify they fail** (`relation ops.v_recognition_review_queue does not exist`).

- [ ] **Step 3: Append the views** to `005_recognition_ledger.sql`:

```sql
-- ---- Component 6: views ----------------------------------------------------
create view ops.v_recognition_review_queue as
select a.id as apparatus_id, a.apparatus_designation, a.scope_id, s.project_id,
       a.quoted_revenue, a.quoted_hours, a.date_due, a.assessment
from ops.apparatus a
join ops.scopes s   on s.id = a.scope_id
join ops.projects p on p.id = s.project_id
where a.status='Complete' and a.is_active and s.is_active and p.is_active
  and s.status <> 'Cancelled' and p.status <> 'Cancelled'
  and coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e
               where e.apparatus_id = a.id), 0) <= 0;

create view ops.v_apparatus_recognition as
select a.id as apparatus_id, a.scope_id, a.status, a.quoted_revenue,
       coalesce(n.net, 0) as net_recognized,
       coalesce(n.net, 0) > 0 as is_recognized,
       r.id as recognized_event_id, r.actor_person_id, r.recognized_at,
       r.datasheet_clearance, r.datasheet_ref, r.cx_clearance, r.cx_ref,
       r.quoted_hours, r.blended_rate, r.basis_frozen_at
from ops.apparatus a
left join lateral (
  select sum(recognized_amount) as net from ops.revenue_recognition_event where apparatus_id = a.id
) n on true
left join lateral (
  select e.* from ops.revenue_recognition_event e
  where e.apparatus_id = a.id and e.event_type='recognized'
    and not exists (select 1 from ops.revenue_recognition_event x where x.reverses_event_id = e.id)
  order by e.recognized_at desc limit 1
) r on true;

create view ops.v_scope_recognition as
select s.id as scope_id, s.project_id,
       coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e where e.scope_id=s.id),0) as recognized_total,
       coalesce((select sum(a.quoted_revenue) from ops.apparatus a where a.scope_id=s.id and a.is_active and a.status <> 'Cancelled'),0) as apparatus_ceiling,  -- FIX-C
       sq.adjusted_total as scope_adjusted_total,
       sq.adjusted_total
         - coalesce((select sum(a.quoted_revenue) from ops.apparatus a where a.scope_id=s.id and a.is_active and a.status <> 'Cancelled'),0) as residual,  -- FIX-C
       coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e where e.scope_id=s.id),0)
         / NULLIF(coalesce((select sum(a.quoted_revenue) from ops.apparatus a where a.scope_id=s.id and a.is_active and a.status <> 'Cancelled'),0), 0) as pct_of_ceiling,  -- FIX-C
       coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e where e.scope_id=s.id),0)
         / NULLIF(sq.adjusted_total, 0) as pct_of_scope
from ops.scopes s
join ops.projects p on p.id = s.project_id
left join ops.scope_quote sq on sq.scope_id = s.id
where s.is_active and s.status <> 'Cancelled' and p.is_active and p.status <> 'Cancelled';

create view ops.v_project_recognition as
select p.id as project_id,
       coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e where e.project_id=p.id),0) as recognized_total,
       coalesce((select sum(a.quoted_revenue) from ops.apparatus a                              -- FIX-C: add scope+cancelled filters
                 join ops.scopes s on s.id=a.scope_id where s.project_id=p.id and a.is_active
                 and s.is_active and s.status <> 'Cancelled' and a.status <> 'Cancelled'),0) as apparatus_ceiling,
       coalesce((select sum(sq.adjusted_total) from ops.scope_quote sq
                 join ops.scopes s on s.id=sq.scope_id
                 where s.project_id=p.id and s.is_active and s.status <> 'Cancelled'),0) as scope_adjusted_total,
       coalesce((select sum(sq.adjusted_total) from ops.scope_quote sq
                 join ops.scopes s on s.id=sq.scope_id
                 where s.project_id=p.id and s.is_active and s.status <> 'Cancelled'),0)
         - coalesce((select sum(a.quoted_revenue) from ops.apparatus a                          -- FIX-C: add scope+cancelled filters
                     join ops.scopes s on s.id=a.scope_id where s.project_id=p.id and a.is_active
                     and s.is_active and s.status <> 'Cancelled' and a.status <> 'Cancelled'),0) as residual,
       coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e where e.project_id=p.id),0)
         / NULLIF(coalesce((select sum(a.quoted_revenue) from ops.apparatus a                   -- FIX-C: add scope+cancelled filters
                            join ops.scopes s on s.id=a.scope_id where s.project_id=p.id and a.is_active
                            and s.is_active and s.status <> 'Cancelled' and a.status <> 'Cancelled'),0), 0) as pct_of_ceiling,
       coalesce((select sum(recognized_amount) from ops.revenue_recognition_event e where e.project_id=p.id),0)
         / NULLIF(coalesce((select sum(sq.adjusted_total) from ops.scope_quote sq
                            join ops.scopes s on s.id=sq.scope_id
                            where s.project_id=p.id and s.is_active and s.status <> 'Cancelled'),0), 0) as pct_of_scope
from ops.projects p
where p.is_active and p.status <> 'Cancelled';
```

- [ ] **Step 4: Run — verify all Tasks 1–6 pass.** Expected: 30 passed.

- [ ] **Step 5: Commit.** `git add -A && git commit -m "feat(ops): Chip 3 task 6 — recognition views + rollups"`

---

## Task 7: Firewall + revenue identity + reversibility + docs

**Files:**
- Modify (test): `test_005_recognition_ledger.py`
- Modify: `infra/database/migrations/ops/MANIFEST.md`
- Modify: `reference/ops/00-MASTER-INDEX.md`

**Interfaces:** Consumes everything above. Produces the closing invariants + the SSoT docs.

- [ ] **Step 1: Append the closing tests:**

```python
# ---- Task 7: firewall, revenue identity, reversibility ----

def test_firewall_no_recognized_dollar_columns(conn):
    s = _seed_recognizable(conn)
    before = conn.execute("select quoted_hours, quoted_revenue from ops.apparatus where id=%s",
                          (s["apparatus"],)).fetchone()
    _recognize(conn, s)
    after = conn.execute("select quoted_hours, quoted_revenue from ops.apparatus where id=%s",
                         (s["apparatus"],)).fetchone()
    assert before == after   # apparatus quote columns untouched by recognition
    # no recognized-$ column leaked onto apparatus
    cols = {r[0] for r in conn.execute(
        "select column_name from information_schema.columns where table_schema='ops' and table_name='apparatus'")}
    assert not {"recognized_revenue", "recognized_amount"} & cols


def test_rollup_revenue_identity(conn):
    # two apparatus in one scope, both recognized -> recognized_total == apparatus_ceiling
    s = _seed_recognizable(conn)
    a2 = conn.execute("insert into ops.apparatus (scope_id, apparatus_designation, status, quoted_hours, quoted_revenue) "
                      "values (%s,'A-2','Complete',5,500) returning id", (s["scope"],)).fetchone()[0]
    conn.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
                 (s["apparatus"], s["person"]))
    conn.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
                 (a2, s["person"]))
    row = conn.execute("select recognized_total, apparatus_ceiling from ops.v_scope_recognition where scope_id=%s",
                       (s["scope"],)).fetchone()
    assert row[0] == row[1] == Decimal("1000")


def test_migration_reversible():
    _exec_file(DOWN5)
    assert _scalar("select to_regclass('ops.revenue_recognition_event')") is None
    # Chips 1/2/4 intact
    assert _scalar("select to_regclass('ops.apparatus')") is not None
    assert _scalar("select to_regclass('ops.scope_quote')") is not None
    assert _scalar("select to_regclass('ops.persons')") is not None
    _exec_file(UP5)
    assert _scalar("select to_regclass('ops.revenue_recognition_event')") is not None
```

- [ ] **Step 2: Run — verify the full suite passes.** Expected: 33 tests passed at this point (the spec's 24 named cases — some consolidated, e.g. the basis-snapshot CHECK is exercised by the Task-4 snapshot-match test); two post-review fix waves added `pct`/`residual` columns + idempotency/null-safety/ceiling-grain hardening and 5 additional tests (final suite = 36). Confirm no warnings.

Run: `… pytest test_005_recognition_ledger.py -q`

- [ ] **Step 3: Update `MANIFEST.md`.** Add row 005 to the table and remove the recognition ledger from "Deferred":

```markdown
| 005 | `005_recognition_ledger.sql` | `005_recognition_ledger_down.sql` | append-only `revenue_recognition_event` ledger (signed recognized/reversal rows) + gated `approve_and_recognize`/`reverse_recognition` + insert-integrity & append-only triggers + lifecycle-protection guards (apparatus/scope/project) + frozen-basis immutability guard + 4 recognition views | 3 | validated on `ops_test` |
```

And edit the "Deferred (later chips)" line to drop the recognition **ledger** (keep progress billing Chip 4 / UI / convergence).

- [ ] **Step 4: Update `reference/ops/00-MASTER-INDEX.md`.** In the decisions section (§8 D-OPS), append a decision recording:
  - **Substrate fork (2026-06-20):** Chip 3 recognition is built on the clean `ops.*` substrate (durable preferred), NOT the deployed `seam.apparatus_revenue_events`; `public`/`seam` = concept-reference; a later bounded packet bridges `ops.*` recognition → the deployed `/pm-review` surface.
  - **Recognition rules:** apparatus-grain; gated by lead approval (`approve_and_recognize`) + `status='Complete'`; assessment-independent; active-row-only; frozen valid quote basis; both obligation clearances (`provided`/`not_applicable`); hard `ops.persons(person_id)` actor FK; append-only firewall; reverse-first lifecycle protection.

  (Match the file's existing decision-entry format; keep it to a short numbered/bulleted entry.)

- [ ] **Step 5: Commit.**

```bash
git add -A && git commit -m "feat(ops): Chip 3 task 7 — firewall/identity/reversibility tests + MANIFEST + SSoT decision"
```

---

## Self-Review (author checklist — completed)

- **Spec coverage:** every spec component maps to a task — enums/table/CHECKs/append-only/indexes (T1), `approve_and_recognize` + all gates (T2), `reverse_recognition` (T3), insert-invariant trigger (T4), protection + freeze guards incl. transitive line block (T5), four views + residual (T6), firewall + revenue identity + reversibility + MANIFEST + SSoT decision (T7). All 24 spec test cases are covered; the basis-snapshot CHECK (spec case) is intentionally exercised by the Task-4 snapshot-match trigger test rather than a standalone CHECK test, because the BEFORE-INSERT trigger is strictly stronger than that CHECK and would shadow it. Two post-review fix waves (FIX-A: idempotency gate + `FOR UPDATE` in insert trigger; FIX-B: null-safe `is distinct from`; FIX-C: cancelled-apparatus ceiling filter + `pct_of_ceiling`/`pct_of_scope`/`residual` columns in both rollup views) added 5 tests; final suite = 36.
- **Type/signature consistency:** `approve_and_recognize(uuid,uuid,obligation_clearance,text,obligation_clearance,text)` and `reverse_recognition(uuid,uuid,text)` are used identically in tests, SQL, and the `_down` drops. Column names match `002_quote_model.sql` (`quoted_hours`/`quoted_revenue`/`adjusted_total`/`blended_rate`/`is_frozen`/`frozen_at`/`total_quoted_hours`) and `004` (`person_id`).
- **No placeholders:** every step carries full SQL or full test code and an exact run/commit command.
- **Ordering note:** the insert-invariant trigger (T4) is stricter than the recognized-amount CHECK; the T1 CHECK tests deliberately target fields the trigger does not police (clearance presence, ref coherence, basis-snapshot presence), so both layers are exercised without collision.
