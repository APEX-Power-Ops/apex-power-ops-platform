# Ops Chip 4 — Progress Billing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Build `006_progress_billing.sql` (+ `_down` + `test_006_progress_billing.py`) on the clean `ops.*`
substrate — the membership-line progress-billing layer that records what RESA invoiced against Chip 3's
recognized revenue, with line-grain retainage, a function-owned write API, and a trigger invariant backstop.

**Architecture:** One reversible SQL migration on `ops_dev`/`ops_test`, building on Chips 1/2/3 (`001/002/004/005`).
A `billing_application` header (issued|voided) + `billing_application_line` (one per recognition event,
the immutable "invoiced" marker) + a non-financial `billing_application_draft`. Four PL/pgSQL functions
(`record`/`issue`/`discard`/`void`) are the **sole write path** (a txn-local `ops.billing_ctx` flag the
mutation triggers require); triggers + a deferred constraint assert the structural invariants on committed state.

**Tech Stack:** PostgreSQL 17 (host) / 18; PL/pgSQL; pytest via `uv run --with "psycopg[binary]" --with pytest`.
All work on the Olares host over mesh SSH (`ssh olares-mesh`, worktree `/home/olares/code/apex/apex-ops-chip4`).

## Global Constraints

- **Canonical spec (authoritative source for all DDL/logic):** `docs/superpowers/specs/2026-06-21-ops-chip4-progress-billing-design.md` (commit `ee5155e3`). Every task's SQL must match it; when in doubt, the spec governs.
- **Dev-only.** Nothing applied to `ops_dev`/prod by this plan; tests run on **throwaway `ops_test`** (the fixture `drop schema ops cascade`-nukes it). Merge to main is **operator-gated**.
- **Law 3 — recognition firewall.** No recognized-$ column on any Chip 1–3 table; Chip 4 only references `ops.revenue_recognition_event` (never mutates it).
- **Money is `numeric(14,2)`; round per line/event then sum.** `amount = round(event.recognized_amount,2)`; `billable_hours = round(quoted_hours,2)`; retainage at **line grain** (`round(amount*pct,2)`).
- **Function-only mutation gate is a misuse-guard, not a security boundary** (app role is superuser/BYPASSRLS). The four functions set `set_config('ops.billing_ctx','1',true)` at entry and reset to `'0'` before return; the **mutation** triggers require it; the **deferred** assertion trigger does NOT (it fires at COMMIT).
- **Billing timezone is `America/Phoenix`** (no DST) for the `period_through` cutoff.
- **Canonical credit-release order:** `ORDER BY orig-event.recognized_at, recognition_event_id`.
- **Commits:** message body via `ssh olares-mesh` must contain **no apostrophes** (use plain ASCII). Co-author trailer per repo convention.
- **Test DSN pinning (never `ops_dev`):** `OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"`.
- **Deferred-constraint test idiom (binding):** to test a `deferrable initially deferred` constraint, do the inserts in the `conn` fixture's txn and fire it with **`conn.execute("set constraints all immediate")`** inside `pytest.raises`. Do NOT use `with conn.transaction()` (a SAVEPOINT — deferred constraints fire at top-level COMMIT, not savepoint release → false-green) and do NOT commit on a separate connection (leaks seed rows into `ops_test`). The fixture rollback then cleans up.

**Run the suite (host):**
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-chip4/infra/database/migrations/ops && \
  export PATH=$HOME/.local/bin:$PATH && set -a && . /home/olares/code/apex/apex-ops-chip4/infra/.env && set +a && \
  OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable" \
  uv run --with "psycopg[binary]" --with pytest pytest test_006_progress_billing.py -q'
```

---

## File Structure

All under `infra/database/migrations/ops/`:
- **`006_progress_billing.sql`** — the migration (built up task-by-task; one file, appended in dependency order).
- **`006_progress_billing_down.sql`** — idempotent `drop … if exists` in reverse-dependency order (views → triggers+functions → tables line→application→draft → enum → `projects.retainage_pct`). Leaves Chips 1/2/3 intact.
- **`test_006_progress_billing.py`** — pytest suite (~45 cases); session fixture chains `001→002→004→005→006` then down-nukes; per-test `conn` rollback fixture; `Decimal` assertions.
- **`MANIFEST.md`** — add row 006 (Task 10).
- **`../../../../reference/ops/00-MASTER-INDEX.md`** — mark Chip 4 / D-OPS-3 done (Task 10).

The migration is a single file because the fixture applies it atomically; tasks **append** sections to it in
dependency order (tables → mutation/immutability triggers → functions → insert-integrity + deferred consistency →
retainage → credits → void → draft → views). Each task keeps the file in an applyable state and the suite green.

---

### Task 1: Scaffold — schema, constraints, down migration, test harness

**Files:**
- Create: `infra/database/migrations/ops/006_progress_billing.sql`
- Create: `infra/database/migrations/ops/006_progress_billing_down.sql`
- Create (Test): `infra/database/migrations/ops/test_006_progress_billing.py`

**Interfaces:**
- Consumes (Chip 1–3): `ops.projects(id,is_active,status,contract_value)`, `ops.scopes(id,project_id,is_active,status)`, `ops.scope_quote(scope_id,is_frozen,frozen_at,blended_rate,adjusted_total)`, `ops.apparatus(id,scope_id,status,is_active,quoted_hours,quoted_revenue)`, `ops.persons(person_id)`, `ops.revenue_recognition_event(id,apparatus_id,scope_id,project_id,event_type,recognized_amount,quoted_hours,reverses_event_id,recognized_at)`, enum `ops.recognition_event_type`, function `ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)`, `ops.reverse_recognition(uuid,uuid,text)`.
- Produces: `ops.projects.retainage_pct`; enum `ops.billing_application_status`; tables `ops.billing_application`, `ops.billing_application_line`, `ops.billing_application_draft`; indexes `uq_billline_active_event`, `uq_billapp_issued_ref`; test harness `apply_migrations`, `conn`, `_set_ctx`, `_seed_recognizable`, `_recognize`.

- [ ] **Step 1: Write the failing harness + first schema tests** (`test_006_progress_billing.py`)

Mirror Chip 3's harness exactly (see `test_005_recognition_ledger.py`). Key parts:

```python
"""ops Chip 4 — progress billing: invariants + reversibility (TDD). Throwaway ops_test ONLY."""
import os, pathlib, uuid
from decimal import Decimal
import psycopg, pytest

DSN = os.environ.get("OPS_DEV_DSN") or (
    "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
    f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD','')} sslmode=disable")
HERE = pathlib.Path(__file__).parent
UP1, DOWN1 = HERE/"001_identity_skeleton.sql", HERE/"001_identity_skeleton_down.sql"
UP2, UP4, UP5 = HERE/"002_quote_model.sql", HERE/"004_person_anchor.sql", HERE/"005_recognition_ledger.sql"
UP6, DOWN6 = HERE/"006_progress_billing.sql", HERE/"006_progress_billing_down.sql"

def _exec_file(path):
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(path.read_text(encoding="utf-8"))

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    _exec_file(DOWN1)
    for f in (UP1, UP2, UP4, UP5, UP6): _exec_file(f)
    yield
    _exec_file(DOWN1)

@pytest.fixture
def conn():
    with psycopg.connect(DSN) as c:
        try: yield c
        finally: c.rollback()

def _set_ctx(c):
    """Mark the txn as 'inside a billing function' so the mutation gate (Task 2) permits raw DML in tests."""
    c.execute("select set_config('ops.billing_ctx','1',true)")

def _seed_recognizable(c, *, pct=0, quoted_hours=5, quoted_revenue=500, status="Complete", is_active=True):
    """project->scope->scope_quote(blended_rate=100, frozen)->apparatus->person. retainage_pct=pct.
    Returns dict(project, scope, apparatus, person)."""
    pid = c.execute("insert into ops.projects (project_number,project_name,is_active,status,retainage_pct) "
                    "values (%s,'t',true,'Active',%s) returning id",
                    (f"P-{uuid.uuid4().hex[:8]}", pct)).fetchone()[0]
    sid = c.execute("insert into ops.scopes (project_id,scope_name,is_active,status) "
                    "values (%s,'s',true,'In Progress') returning id", (pid,)).fetchone()[0]
    c.execute("insert into ops.scope_quote (scope_id,onsite_labor,unit_multiplier,pct_adjust,total_quoted_hours) "
              "values (%s,1000,1,1,10)", (sid,))
    c.execute("update ops.scope_quote set is_frozen=true, frozen_at=now() where scope_id=%s", (sid,))
    aid = c.execute("insert into ops.apparatus (scope_id,apparatus_designation,status,is_active,assessment,"
                    "quoted_hours,quoted_revenue) values (%s,'A-1',%s,%s,'Pass',%s,%s) returning id",
                    (sid, status, is_active, quoted_hours, quoted_revenue)).fetchone()[0]
    person = c.execute("insert into ops.persons (display_name) values ('Lead') returning person_id").fetchone()[0]
    return {"project": pid, "scope": sid, "apparatus": aid, "person": person}

def _recognize(c, s):
    """Recognize the seeded apparatus via the Chip 3 gated function (provided clearances). Returns event id."""
    return c.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
                     (s["apparatus"], s["person"])).fetchone()[0]

def test_tables_exist(conn):
    for t in ("billing_application", "billing_application_line", "billing_application_draft"):
        assert conn.execute("select to_regclass(%s)", (f"ops.{t}",)).fetchone()[0] is not None

def test_retainage_pct_bounds(conn):
    s = _seed_recognizable(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("update ops.projects set retainage_pct=1.0 where id=%s", (s["project"],))

def test_withheld_cap_check(conn):
    _set_ctx(conn)
    s = _seed_recognizable(conn); _recognize(conn, s)
    # raw header with withheld>positive_gross must violate ck_billapp_withheld_cap
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
                     "external_invoice_ref,billable_hours,gross_amount,positive_gross,retainage_withheld,"
                     "net_invoiced,actor_person_id) values (%s,1,'issued',current_date,'INV',5,500,500,600,-100,%s)",
                     (s["project"], s["person"]))
```

- [ ] **Step 2: Run the harness test — verify it fails** (no `006` file yet)

Run the suite (see Global Constraints). Expected: FAIL — `006_progress_billing.sql` missing / `to_regclass` returns NULL.

- [ ] **Step 3: Write `006_progress_billing.sql` §6a–6d (schema)** — copy the spec's §6a (retainage_pct column), §6b (enum), §6c (`billing_application` + all CHECKs + `uq_billapp_issued_ref`), §6d (`billing_application_line` + `uq_billline_active_event` + the FK/CHECK), §6e (`billing_application_draft`) **verbatim from the spec**. No triggers/functions/views yet. Each `numeric(14,2)`; enum `('issued','voided')`; `retainage_pct numeric(6,5)`.

- [ ] **Step 4: Write `006_progress_billing_down.sql`** (idempotent, reverse order):

```sql
-- DOWN — ops Chip 4 progress billing. Undoes ONLY Chip 4 (leaves Chips 1/2/3 intact). Idempotent.
drop view if exists ops.v_project_billing;
drop view if exists ops.v_billing_application_sov;
drop view if exists ops.v_draft_preview;
drop view if exists ops.v_unbilled_recognition;
-- (triggers + their functions dropped here once Tasks 2-9 add them; keep this list in sync)
drop function if exists ops.record_billing_application(uuid,uuid,date,text,uuid[],numeric) cascade;
drop function if exists ops.issue_billing_application(uuid,uuid,text) cascade;
drop function if exists ops.discard_draft_billing_application(uuid,uuid) cascade;
drop function if exists ops.void_billing_application(uuid,uuid,text) cascade;
drop table if exists ops.billing_application_line cascade;
drop table if exists ops.billing_application cascade;
drop table if exists ops.billing_application_draft cascade;
drop type if exists ops.billing_application_status;
alter table if exists ops.projects drop column if exists retainage_pct;
```
(Trigger-function drops are added by their tasks; Task 10 reconciles the full list.)

- [ ] **Step 5: Run schema + down→up tests — verify they pass**

Add `test_down_up_clean` (apply DOWN6 then UP6 in autocommit, assert tables still resolve). Run the suite. Expected: PASS (schema tests + CHECK tests + reversibility green).

- [ ] **Step 6: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-ops-chip4 && git add infra/database/migrations/ops/006_progress_billing.sql infra/database/migrations/ops/006_progress_billing_down.sql infra/database/migrations/ops/test_006_progress_billing.py && git commit -q -m "feat(ops): Chip 4 Task 1 -- progress-billing schema + down + harness" -m "3 tables, enum, retainage_pct, uq indexes, CHECKs; reversible; test harness chains 001-006 on ops_test."'
```

---

### Task 2: Mutation gate + immutability triggers (no functions yet)

**Files:** Modify `006_progress_billing.sql` (append §8.0/§8.1/§8.2 triggers + draft gate); Modify `006_progress_billing_down.sql` (add their function drops); Modify the test file.

**Interfaces:**
- Produces: trigger functions `ops.trg_billapp_immutable()`, `ops.trg_billline_immutable()`, `ops.trg_billdraft_gate()` + their triggers. The **gate clause** `if current_setting('ops.billing_ctx',true) is distinct from '1' then raise exception 'ops billing tables are function-only (set ops.billing_ctx)'; end if;` opens every mutation trigger.
- Note: the §8.1 **void-dependency guard** clause is added in Task 7 (it needs credits); Task 2 builds header immutability + the void **line-cascade** + void-shape only.

- [ ] **Step 1: Write failing tests**

```python
def test_gate_blocks_unflagged_insert(conn):
    s = _seed_recognizable(conn); _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException):   # no _set_ctx -> gate rejects
        conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
                     "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
                     "values (%s,1,'issued',current_date,'INV',5,500,500,500,%s)", (s["project"], s["person"]))

def test_header_delete_blocked_with_ctx(conn):
    _set_ctx(conn); s = _seed_recognizable(conn); _recognize(conn, s)
    aid = conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
        "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV',5,500,500,500,%s) returning id",(s["project"],s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("delete from ops.billing_application where id=%s", (aid,))

def test_illegal_header_update_blocked(conn):
    _set_ctx(conn); s = _seed_recognizable(conn); _recognize(conn, s)
    aid = conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
        "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV',5,500,500,500,%s) returning id",(s["project"],s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("update ops.billing_application set gross_amount=999 where id=%s", (aid,))
```

- [ ] **Step 2: Run — verify fail** (triggers absent → inserts succeed, no raise). Expected: FAIL.

- [ ] **Step 3: Implement §8.0/§8.1/§8.2 triggers** in `006_progress_billing.sql` per spec: header `before update or delete` (gate clause; DELETE always raise; UPDATE only `issued→voided` writing exactly `status/voided_at/voided_by/void_reason`; on that transition cascade `update ops.billing_application_line set is_voided=true where application_id=old.id and is_voided=false`); line `before update or delete` (gate; DELETE raise; UPDATE only `is_voided false→true`); draft `before insert or update or delete` (gate only).

- [ ] **Step 4: Run — verify pass.** Expected: PASS (gate + immutability green; Task 1 raw-insert tests still pass because `_set_ctx` is set in them).

- [ ] **Step 5: Commit** (`feat(ops): Chip 4 Task 2 -- function-only mutation gate + immutability triggers`).

---

### Task 3: `record`/`issue` — the positive-branch sweep (no retainage, no credits, no draft)

**Files:** Modify `006_progress_billing.sql` (append §7a/§7b functions, positive-only); Modify test file.

**Interfaces:**
- Produces: `ops.record_billing_application(p_project_id uuid, p_actor_person_id uuid, p_period_through date, p_external_invoice_ref text default null, p_exclude_apparatus uuid[] default '{}', p_retainage_draw_request numeric default 0) returns uuid` and `ops.issue_billing_application(...)`. With a ref → issues + returns the application id. Each sets/resets `ops.billing_ctx`.
- This task: positive branch only — `retainage_pct` is 0 in seeds so withheld=0; credits/draft are later tasks. Implement the full §7b skeleton (project lock; monotonic period; preliminary sweep; **event `FOR UPDATE` lock + re-validate**; build positive lines; aggregates; `application_no`; nothing-to-bill) but leave the credit walk + draw cap as no-ops where pct=0/no credits.

- [ ] **Step 1: Write failing tests** — key cases:

```python
def _issue(c, project, person, period="current_date", ref="'INV-1'", exclude="'{}'::uuid[]", draw=0):
    return c.execute(f"select ops.record_billing_application(%s,%s,{period},{ref},{exclude},{draw})",
                     (project, person)).fetchone()[0]

def test_single_apparatus_issue(conn):
    s = _seed_recognizable(conn, quoted_revenue=500, quoted_hours=5); _recognize(conn, s)
    app = _issue(conn, s["project"], s["person"])
    row = conn.execute("select status,application_no,gross_amount,positive_gross,billable_hours,net_invoiced "
                       "from ops.billing_application where id=%s", (app,)).fetchone()
    assert row[0] == "issued" and row[1] == 1
    assert row[2] == Decimal("500.00") and row[3] == Decimal("500.00")
    assert row[4] == Decimal("5.00") and row[5] == Decimal("500.00")
    assert conn.execute("select count(*) from ops.billing_application_line where application_id=%s",(app,)).fetchone()[0]==1

def test_nothing_to_bill_raises(conn):
    s = _seed_recognizable(conn)  # recognized NOTHING
    with pytest.raises(psycopg.errors.RaiseException):
        _issue(conn, s["project"], s["person"])

def test_period_cutoff_excludes_future_recognition(conn):
    s = _seed_recognizable(conn); _recognize(conn, s)
    # recognition is stamped now(); a period_through FIRMLY in the past excludes it DETERMINISTICALLY
    # (current_date-1 is flaky near the Phoenix-midnight boundary — audit finding).
    with pytest.raises(psycopg.errors.RaiseException):
        _issue(conn, s["project"], s["person"], period="'2000-01-01'::date")

def test_monotonic_period_rejected(conn):
    s = _seed_recognizable(conn); _recognize(conn, s)
    _issue(conn, s["project"], s["person"], ref="'INV-1'", period="current_date")
    a2 = conn.execute("insert into ops.apparatus (scope_id,apparatus_designation,status,is_active,assessment,"
        "quoted_hours,quoted_revenue) values (%s,'A-2','Complete',true,'Pass',5,500) returning id",(s["scope"],)).fetchone()[0]
    conn.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(a2,s["person"]))
    with pytest.raises(psycopg.errors.RaiseException):   # earlier period than a prior issued app
        _issue(conn, s["project"], s["person"], ref="'INV-2'", period="current_date - 5")

def test_exclude_holds_apparatus_back(conn):
    s = _seed_recognizable(conn); _recognize(conn, s)
    with pytest.raises(psycopg.errors.RaiseException):   # exclude the only recognized apparatus -> nothing to bill
        conn.execute("select ops.record_billing_application(%s,%s,current_date,'INV',array[%s]::uuid[],0)",
                     (s["project"], s["person"], s["apparatus"]))

def test_application_no_sequential(conn):
    s = _seed_recognizable(conn); _recognize(conn, s); _issue(conn, s["project"], s["person"], ref="'INV-1'")
    # second recognizable apparatus in same project
    a2 = conn.execute("insert into ops.apparatus (scope_id,apparatus_designation,status,is_active,assessment,"
        "quoted_hours,quoted_revenue) values (%s,'A-2','Complete',true,'Pass',5,500) returning id",(s["scope"],)).fetchone()[0]
    conn.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(a2,s["person"]))
    app2 = _issue(conn, s["project"], s["person"], ref="'INV-2'")
    assert conn.execute("select application_no from ops.billing_application where id=%s",(app2,)).fetchone()[0]==2

def test_flag_containment_success(conn):
    s = _seed_recognizable(conn); _recognize(conn, s); _issue(conn, s["project"], s["person"])
    # after the function returns it reset ops.billing_ctx -> a raw insert now is rejected
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
                     "apparatus_id,scope_id,project_id,amount,billable_hours) values "
                     "(gen_random_uuid(),gen_random_uuid(),'recognized',%s,%s,%s,1,1)",
                     (s["apparatus"], s["scope"], s["project"]))

def test_flag_containment_exception_savepoint(conn):
    s = _seed_recognizable(conn)  # nothing recognized -> issue raises
    conn.execute("savepoint sp")
    try: _issue(conn, s["project"], s["person"])
    except psycopg.errors.RaiseException: pass
    conn.execute("rollback to savepoint sp")
    with pytest.raises(psycopg.errors.RaiseException):  # flag cleared by subtxn rollback
        conn.execute("insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
                     "apparatus_id,scope_id,project_id,amount,billable_hours) values "
                     "(gen_random_uuid(),gen_random_uuid(),'recognized',%s,%s,%s,1,1)",(s["apparatus"],s["scope"],s["project"]))
```

- [ ] **Step 2: Run — verify fail** (functions absent). Expected: FAIL with "function ops.record_billing_application does not exist".

- [ ] **Step 3: Implement §7a/§7b** (positive branch). The function body must: `set_config('ops.billing_ctx','1',true)`; lock the project; monotonic-period check; preliminary positive sweep (recognized events, not reversed, no active line, `recognized_at < (p_period_through+1)::timestamp at time zone 'America/Phoenix'`, apparatus not in `p_exclude_apparatus`); `perform 1 from ops.revenue_recognition_event where id = any(candidate_ids) order by id for update`; re-evaluate eligibility; build lines (`amount=round(recognized_amount,2)`, `billable_hours=round(quoted_hours,2)`, retainage 0 for now); aggregates; `application_no=coalesce(max,0)+1`; raise if empty & draw 0; insert header+lines; `set_config('ops.billing_ctx','0',true)`; return id. (Credit walk + draw cap are added in Tasks 5/6 — guard them so pct=0/no-credits is a no-op.)

- [ ] **Step 4: Run — verify pass.** Expected: PASS.

- [ ] **Step 5: Commit** (`feat(ops): Chip 4 Task 3 -- record/issue positive-branch sweep + Chip-3 event lock + flag containment`).

---

### Task 4: Header + line insert-integrity + deferred header=Σlines

**Files:** Modify `006_progress_billing.sql` (append §8.3, §8.4, §8.5-part-1); test file.

**Interfaces:**
- Produces: `ops.trg_billapp_insert_integrity()` (project FOR UPDATE; ref non-blank; `application_no=max+1`; monotonic period; `retainage_drawn ≤ held_to_date` upper-bound), `ops.trg_billline_insert_integrity()` (committed-state lineage; `amount=round(recognized_amount,2)` + sign by branch; `billable_hours` rounded; retainage rules; **branch eligibility** — positive unreversed, credit original issued-active; `amount>0`/`<0`), and the deferred `ops.trg_billing_consistency()` constraint trigger asserting `header=Σ active lines` for issued apps + `held≥0` over issued (held part fully exercised in Task 5/6).

- [ ] **Step 1: Write failing tests** (all `_set_ctx`-flagged raw inserts):

```python
def test_line_lineage_mismatch_rejected(conn):
    _set_ctx(conn); s = _seed_recognizable(conn); ev = _recognize(conn, s)
    other = _seed_recognizable(conn)
    app = conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
        "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV',5,500,500,500,%s) returning id",(s["project"],s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):  # scope_id of OTHER seed mismatches the event
        conn.execute("insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
            "apparatus_id,scope_id,project_id,amount,billable_hours) values (%s,%s,'recognized',%s,%s,%s,500,5)",
            (app, ev, s["apparatus"], other["scope"], s["project"]))

def test_header_neq_sum_lines_deferred_fires(conn):
    # DEFERRED-CONSTRAINT TEST IDIOM (audit fix): do the mismatched inserts in THIS conn's txn, then fire the
    # deferred constraint NOW with `set constraints all immediate`. This (a) avoids the savepoint false-green
    # (`with conn.transaction()` is a SAVEPOINT, and deferred constraints fire at top-level COMMIT, not savepoint
    # release) and (b) needs no separate committed connection, so the fixture rollback cleans up — no ops_test leak.
    _set_ctx(conn); s = _seed_recognizable(conn); ev = _recognize(conn, s)
    app = conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
        "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV',5,999,999,999,%s) returning id",(s["project"],s["person"])).fetchone()[0]
    conn.execute("insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
        "apparatus_id,scope_id,project_id,amount,billable_hours) values (%s,%s,'recognized',%s,%s,%s,500,5)",
        (app, ev, s["apparatus"], s["scope"], s["project"]))
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("set constraints all immediate")   # header gross 999 != Σ lines 500 -> fires now

def test_line_withheld_must_match_pct(conn):   # audit: §8.4 positive-branch withheld validation (Task-4 gap)
    _set_ctx(conn); s = _seed_recognizable(conn, pct=Decimal("0.10")); ev = _recognize(conn, s)
    app = conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
        "external_invoice_ref,billable_hours,gross_amount,positive_gross,retainage_withheld,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV',5,500,500,50,450,%s) returning id",(s["project"],s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):   # withheld 0 but pct=0.10 on amount 500 -> must be 50.00
        conn.execute("insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
            "apparatus_id,scope_id,project_id,amount,billable_hours,retainage_withheld) values (%s,%s,'recognized',%s,%s,%s,500,5,0)",
            (app, ev, s["apparatus"], s["scope"], s["project"]))

def test_positive_line_after_reversal_rejected(conn):  # audit: §8.4 branch eligibility (gate-bypassed)
    _set_ctx(conn); s = _seed_recognizable(conn); ev = _recognize(conn, s)
    conn.execute("select ops.reverse_recognition(%s,%s,'x')", (ev, s["person"]))   # event now reversed
    app = conn.execute("insert into ops.billing_application (project_id,application_no,status,period_through,"
        "external_invoice_ref,billable_hours,gross_amount,positive_gross,net_invoiced,actor_person_id) "
        "values (%s,1,'issued',current_date,'INV',5,500,500,500,%s) returning id",(s["project"],s["person"])).fetchone()[0]
    with pytest.raises(psycopg.errors.RaiseException):   # positive line for a now-reversed recognition
        conn.execute("insert into ops.billing_application_line (application_id,recognition_event_id,event_type,"
            "apparatus_id,scope_id,project_id,amount,billable_hours) values (%s,%s,'recognized',%s,%s,%s,500,5)",
            (app, ev, s["apparatus"], s["scope"], s["project"]))
```

- [ ] **Step 2: Run — verify fail.** Expected: FAIL (no integrity/deferred triggers → both inserts succeed).

- [ ] **Step 3: Implement §8.3/§8.4/§8.5** per spec. The deferred trigger: `create constraint trigger … after insert or update on ops.billing_application` and on `…_line`, `deferrable initially deferred`; body re-aggregates per touched issued `application_id` (resolve via `line.application_id` ∪ header rows) and asserts the five Σ equalities; per touched `project_id` asserts `held_to_date ≥ 0` over `status='issued'` apps.

- [ ] **Step 4: Run — verify pass.** Re-run the Task 3 happy-path too (the function's own rows satisfy the new triggers). Expected: PASS.

- [ ] **Step 5: Commit** (`feat(ops): Chip 4 Task 4 -- header/line insert-integrity + deferred header=sum-lines + held>=0`).

---

### Task 5: Retainage withholding + explicit draw

**Files:** Modify `006_progress_billing.sql` (extend §7b: positive-line withholding + draw cap; the held aggregation); test file.

**Interfaces:**
- Consumes: `projects.retainage_pct`. Produces: positive line `retainage_withheld=round(amount*pct,2)`; header `retainage_withheld=Σ`; `retainage_drawn` (validated `0 ≤ draw ≤ held_before − Σ this-app releases`); `net = gross − withheld + released + drawn`.

- [ ] **Step 1: Write failing tests:**

```python
def test_withholding_line_grain(conn):
    s = _seed_recognizable(conn, pct=Decimal("0.10"), quoted_revenue=500); _recognize(conn, s)
    app = _issue(conn, s["project"], s["person"])
    h = conn.execute("select retainage_withheld,net_invoiced from ops.billing_application where id=%s",(app,)).fetchone()
    assert h[0] == Decimal("50.00") and h[1] == Decimal("450.00")  # 500*0.10 withheld; net 450
    ln = conn.execute("select retainage_withheld from ops.billing_application_line where application_id=%s",(app,)).fetchone()
    assert ln[0] == Decimal("50.00")

def test_pure_draw_app_issues(conn):
    s = _seed_recognizable(conn, pct=Decimal("0.10")); _recognize(conn, s); _issue(conn, s["project"], s["person"], ref="'INV-1'")
    # held_to_date is 50; a pure draw of 50 with empty sweep issues
    app2 = _issue(conn, s["project"], s["person"], ref="'INV-2'", draw=50)
    assert conn.execute("select retainage_drawn,net_invoiced from ops.billing_application where id=%s",(app2,)).fetchone() == (Decimal("50.00"), Decimal("50.00"))

def test_over_draw_rejected(conn):
    s = _seed_recognizable(conn, pct=Decimal("0.10")); _recognize(conn, s); _issue(conn, s["project"], s["person"], ref="'INV-1'")
    with pytest.raises(psycopg.errors.RaiseException):
        _issue(conn, s["project"], s["person"], ref="'INV-2'", draw=999)
```

- [ ] **Step 2: Run — verify fail** (pct ignored → withheld 0). **Step 3: Implement** the withholding + draw-cap logic. **Step 4: Run — verify pass.** **Step 5: Commit** (`feat(ops): Chip 4 Task 5 -- line-grain retainage withholding + explicit capped draw`).

---

### Task 6: Credits — branch + line-grain auto-release (canonical order)

**Files:** Modify `006_progress_billing.sql` (extend §7b/§5 credit branch + the canonical release walk; §8.4 credit-line rules); test file.

**Interfaces:** Produces: the credit branch (reversal events whose original is issued-billed and which are unbilled), credit line `amount<0`, `billable_hours=−round(orig.quoted_hours,2)`, `retainage_released=LEAST(orig-line.retainage_withheld, remaining_held)` walked in canonical order; header `retainage_released=Σ`.

- [ ] **Step 1: Write failing tests:**

```python
def test_credit_returns_gross_plus_retainage(conn):
    s = _seed_recognizable(conn, pct=Decimal("0.10"), quoted_revenue=500); ev = _recognize(conn, s)
    _issue(conn, s["project"], s["person"], ref="'INV-1'")              # bill: net 450, held 50
    conn.execute("select ops.reverse_recognition(%s,%s,'rework')", (ev, s["person"]))
    app2 = _issue(conn, s["project"], s["person"], ref="'INV-2'")        # credit
    h = conn.execute("select gross_amount,retainage_released,net_invoiced from ops.billing_application where id=%s",(app2,)).fetchone()
    assert h == (Decimal("-500.00"), Decimal("50.00"), Decimal("-450.00"))  # net-credit = -(net originally billed)
    held = conn.execute("select coalesce(sum(retainage_withheld-retainage_released-retainage_drawn),0) "
                        "from ops.billing_application where project_id=%s and status='issued'",(s["project"],)).fetchone()[0]
    assert held == Decimal("0.00")

def test_pure_credit_app_issues(conn):   # C-1 fix: withheld cap=positive_gross, not LEAST(.,gross)
    s = _seed_recognizable(conn, pct=Decimal("0.10")); ev = _recognize(conn, s)
    _issue(conn, s["project"], s["person"], ref="'INV-1'")
    conn.execute("select ops.reverse_recognition(%s,%s,'x')",(ev,s["person"]))
    app2 = _issue(conn, s["project"], s["person"], ref="'INV-2'")
    assert conn.execute("select gross_amount from ops.billing_application where id=%s",(app2,)).fetchone()[0] < 0

def test_bill_draw_reverse_no_wedge(conn):  # C-2 fix
    s = _seed_recognizable(conn, pct=Decimal("0.10")); ev = _recognize(conn, s)
    _issue(conn, s["project"], s["person"], ref="'INV-1'")               # held 50
    _issue(conn, s["project"], s["person"], ref="'INV-2'", draw=50)      # held 0
    conn.execute("select ops.reverse_recognition(%s,%s,'x')",(ev,s["person"]))
    app3 = _issue(conn, s["project"], s["person"], ref="'INV-3'")        # credit: released=LEAST(50,0)=0
    h = conn.execute("select retainage_released,net_invoiced from ops.billing_application where id=%s",(app3,)).fetchone()
    assert h == (Decimal("0.00"), Decimal("-500.00"))   # full gross credited; no wedge
```

- [ ] **Step 2: Run — verify fail.** **Step 3: Implement** the credit branch + canonical-order release walk + §8.4 credit rules. **Step 4: Run — verify pass.** **Step 5: Commit** (`feat(ops): Chip 4 Task 6 -- credit branch + line-grain auto-release; close bill-draw-reverse wedge`).

---

### Task 7: `void` + void-dependency guard + line-cascade

**Files:** Modify `006_progress_billing.sql` (§7d function + add the §8.1 void-dependency guard clause); test file.

**Interfaces:** Produces: `ops.void_billing_application(uuid,uuid,text)`; the §8.1 trigger gains the standing-credit guard. Void releases lines (`is_voided=true`) → events return to unbilled; `application_no` stays burned.

- [ ] **Step 1: Write failing tests:**

```python
def test_void_releases_events_to_unbilled(conn):
    s = _seed_recognizable(conn); ev = _recognize(conn, s); app = _issue(conn, s["project"], s["person"])
    conn.execute("select ops.void_billing_application(%s,%s,'mis-invoiced')", (app, s["person"]))
    assert conn.execute("select status from ops.billing_application where id=%s",(app,)).fetchone()[0]=="voided"
    assert conn.execute("select bool_and(is_voided) from ops.billing_application_line where application_id=%s",(app,)).fetchone()[0] is True
    # event re-billable
    app2 = _issue(conn, s["project"], s["person"], ref="'INV-2'")
    assert app2 is not None

def test_void_blocked_by_standing_credit(conn):
    s = _seed_recognizable(conn); ev = _recognize(conn, s); app1 = _issue(conn, s["project"], s["person"], ref="'INV-1'")
    conn.execute("select ops.reverse_recognition(%s,%s,'x')",(ev,s["person"]))
    _issue(conn, s["project"], s["person"], ref="'INV-2'")   # standing credit on app2
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("select ops.void_billing_application(%s,%s,'late')", (app1, s["person"]))
```

- [ ] **Step 2: Run — verify fail.** **Step 3: Implement** §7d + the §8.1 standing-credit guard. **Step 4: Run — verify pass.** **Step 5: Commit** (`feat(ops): Chip 4 Task 7 -- void function + void-dependency guard + line-cascade`).

---

### Task 8: Draft = intent (record→draft, issue-from-draft, discard)

**Files:** Modify `006_progress_billing.sql` (§7a draft path, §7b draft promotion, §7c discard); test file.

**Interfaces:** Produces: `record` with no ref → a `billing_application_draft` row (returns its id, no number/lines/totals); a NEW **3-param overload** `issue_billing_application(draft_id uuid, actor uuid, ref text)` that loads the draft's params and **delegates to the Task-3 6-param `issue_billing_application(project,actor,period,ref,exclude,draw)` worker** (then deletes the draft) — Postgres allows the two arities to coexist; `create` the new arity (not `create or replace`). `discard_draft_billing_application(draft_id, actor)` deletes a draft. **Add a SECOND down-migration drop line** for the 3-param `issue_billing_application(uuid,uuid,text)` (the existing drop is signature-specific to the 6-param form).

**API staging (audit clarification):** Task 3 already shipped the 6-param `issue_billing_application` as the **issue worker** (called by `record`); the public 3-param draft-promotion overload is deferred to here (Task 8). Both share the worker — there is no second sweep implementation.

- [ ] **Step 1: Write failing tests:**

```python
def test_draft_saved_then_issued_fresh(conn):
    s = _seed_recognizable(conn); _recognize(conn, s)
    d = conn.execute("select ops.record_billing_application(%s,%s,current_date,null,'{}'::uuid[],0)",
                     (s["project"], s["person"])).fetchone()[0]
    assert conn.execute("select count(*) from ops.billing_application_draft where id=%s",(d,)).fetchone()[0]==1
    assert conn.execute("select count(*) from ops.billing_application where project_id=%s",(s["project"],)).fetchone()[0]==0
    app = conn.execute("select ops.issue_billing_application(%s,%s,'INV-1')",(d,s["person"])).fetchone()[0]
    assert conn.execute("select status from ops.billing_application where id=%s",(app,)).fetchone()[0]=="issued"
    assert conn.execute("select count(*) from ops.billing_application_draft where id=%s",(d,)).fetchone()[0]==0  # consumed

def test_draft_reserves_nothing(conn):
    s = _seed_recognizable(conn); _recognize(conn, s)
    conn.execute("select ops.record_billing_application(%s,%s,current_date,null,'{}'::uuid[],0)",(s["project"],s["person"]))
    # apparatus still appears unbilled (drafts reserve nothing)
    assert conn.execute("select count(*) from ops.v_unbilled_recognition where apparatus_id=%s",(s["apparatus"],)).fetchone()[0] >= 1
```
(Note: `v_unbilled_recognition` lands in Task 9; if running Task 8 before it, assert against an inline query equivalent and switch to the view in Task 9.)

- [ ] **Step 2: Run — verify fail.** **Step 3: Implement** the draft path. **Step 4: Run — verify pass.** **Step 5: Commit** (`feat(ops): Chip 4 Task 8 -- draft intent table + issue-from-draft + discard`).

---

### Task 9: Views (4)

**Files:** Modify `006_progress_billing.sql` (append §9 views); test file.

**Interfaces:** Produces: `ops.v_unbilled_recognition`, `ops.v_draft_preview`, `ops.v_billing_application_sov`, `ops.v_project_billing` (all per spec §9; `recognized_to_date = Σ round(recognized_amount,2)` over ALL events incl. reversals).

- [ ] **Step 1: Write failing tests** — the headline reconciliation tie-out with non-2dp revenue:

```python
def test_reconciliation_ties_to_cent(conn):
    # quoted_hours=3, blended_rate=100 -> quoted_revenue stored 300; but use a non-2dp case via 2 apparatus
    s = _seed_recognizable(conn, quoted_revenue=Decimal("333.335"), quoted_hours=3); _recognize(conn, s)
    _issue(conn, s["project"], s["person"])
    r = conn.execute("select recognized_to_date, billed_gross_to_date, unbilled_recognized "
                     "from ops.v_project_billing where project_id=%s", (s["project"],)).fetchone()
    assert r[0] == r[1] + r[2]   # recognized == billed + unbilled, to the cent

def test_unbilled_view_matches_sweep(conn):
    s = _seed_recognizable(conn); _recognize(conn, s)
    assert conn.execute("select count(*) from ops.v_unbilled_recognition where apparatus_id=%s",(s["apparatus"],)).fetchone()[0]==1
    _issue(conn, s["project"], s["person"])
    assert conn.execute("select count(*) from ops.v_unbilled_recognition where apparatus_id=%s",(s["apparatus"],)).fetchone()[0]==0
```

- [ ] **Step 2: Run — verify fail.** **Step 3: Implement** the 4 views. **Step 4: Run — verify pass** (and back-fill the Task 8 view assertion). **Step 5: Commit** (`feat(ops): Chip 4 Task 9 -- the 4 reconciliation/SOV/unbilled/draft views`).

---

### Task 10: Reversibility + firewall + docs + full suite

**Files:** Modify `006_progress_billing_down.sql` (reconcile ALL trigger/function drops); Modify `MANIFEST.md`; Modify `reference/ops/00-MASTER-INDEX.md`; test file (firewall + full down→up→down).

- [ ] **Step 1: Write failing tests:**

```python
def test_recognition_firewall_intact(conn):
    # no recognized-$ column leaked onto Chip 1-3 tables by Chip 4
    cols = conn.execute("select count(*) from information_schema.columns where table_schema='ops' "
        "and table_name in ('apparatus','scopes','projects') and column_name like '%recognized%'").fetchone()[0]
    assert cols == 0

def _regclass(c, name):
    return c.execute("select to_regclass(%s)", (name,)).fetchone()[0]

def test_full_down_up_down_clean():
    # idempotent both directions; Chip 4 recreates; a Chip-4 DOWN must NOT touch Chips 1-3.
    _exec_file(DOWN6); _exec_file(UP6); _exec_file(DOWN6); _exec_file(UP6)   # round-trips cleanly
    with psycopg.connect(DSN, autocommit=True) as c:
        assert _regclass(c, "ops.billing_application") is not None            # Chip 4 present after re-up
        _exec_file(DOWN6)
        assert _regclass(c, "ops.billing_application") is None                # Chip 4 dropped
        assert _regclass(c, "ops.revenue_recognition_event") is not None      # Chip 3 SURVIVES
        assert _regclass(c, "ops.apparatus") is not None                      # Chip 1 SURVIVES
        assert c.execute("select 1 from ops.scope_quote limit 1") is not None # Chip 2 SURVIVES
        _exec_file(UP6)                                                       # restore for any later test
```

- [ ] **Step 2: Run — verify fail** (down list incomplete → dangling objects on re-up). **Step 3:** Reconcile `006_down` to drop every trigger-function added in Tasks 2–9 (header/line/draft immutability, insert-integrity, the deferred consistency constraint, the 4 functions) before the tables; add the MANIFEST row 006 and mark D-OPS-3 / Chip 4 in the MASTER-INDEX. **Step 4: Run the FULL ~45-case suite — verify all pass.** **Step 5: Commit** (`feat(ops): Chip 4 Task 10 -- reversibility + firewall assertion + MANIFEST/MASTER-INDEX`).

---

## Plan Self-Review

- **Spec coverage:** §6a–6e → T1; §8.0/8.1/8.2 → T2 (+ void guard T7); §7a/7b positive → T3; §8.3/8.4/8.5 → T4; retainage §6c/§7b → T5; credits §5/§7b → T6; void §7d → T7; draft §6e/§7a/7b/7c → T8; views §9 → T9; reversibility §10 + firewall + docs → T10. §11 test list distributed across T1–T10. **No gaps.**
- **Type consistency:** the `issue_billing_application` API is staged: T3 ships the **6-param worker** `(uuid,uuid,date,text,uuid[],numeric)` (called by `record`); T8 adds the **3-param overload** `(uuid,uuid,text)` for draft promotion (a thin wrapper around the worker — two arities coexist; T8 `create`s the new one + adds its own down-drop). `discard_draft_billing_application(uuid,uuid)`, `void_billing_application(uuid,uuid,text)` per spec.
- **Placeholder scan:** the per-task SQL points to the committed spec as the canonical block and inlines the test code; no "TBD"/"add error handling" placeholders. The implementer must copy the spec's DDL/function/trigger bodies exactly.
- **Ordering caveat (call out to implementers):** the mutation gate (T2) makes raw inserts require `_set_ctx`; every raw-insert test helper sets it from T1 so no test churns. `issue`'s credit/draw branches are stubbed as no-ops in T3 and filled in T5/T6 — they must not raise when pct=0/no credits.

## Invariant → Task test-coverage map (audit: pin each v6 invariant to a concrete task test)

| Invariant | Task / test |
|---|---|
| duplicate RESA invoice ref blocked among issued (reuse OK after void) | **T7** `test_dup_ref_blocked` + `test_ref_reusable_after_void` |
| gate-bypassed positive line whose event is reversed → rejected (§8.4 eligibility) | **T4** `test_positive_line_after_reversal_rejected` |
| line `retainage_withheld = round(amount*pct,2)` (§8.4) | **T4** `test_line_withheld_must_match_pct` |
| credit line `amount < 0` enforced; sub-cent credit skipped | **T6** `test_credit_amount_negative` + `test_sub_cent_credit_skipped` |
| `exclude[]` holds positive apparatus back; credit non-excludable (B-6) | **T3** `test_exclude_holds_apparatus_back`; **T6** `test_credit_non_excludable` |
| monotonic period_through rejection | **T3** `test_monotonic_period_rejected` |
| held-negative void rejected (deferred held≥0) | **T7** `test_void_blocked_when_held_would_go_negative` |
| `application_no` burned after void | **T7** `test_application_no_burned_after_void` |
| deferred-constraint tests fire deterministically (no savepoint false-green, no leak) | **all** — use the **`set constraints all immediate`** idiom (see T4 `test_header_neq_sum_lines_deferred_fires`) |
