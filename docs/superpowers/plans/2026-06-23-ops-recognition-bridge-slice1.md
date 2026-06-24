# Ops Recognition Bridge — Slice 1 Implementation Plan (TDD)

**Date:** 2026-06-23
**Lane:** `ops/recognition-bridge` (host worktree `~/code/apex/apex-ops-recognition`)
**Spec:** `docs/superpowers/specs/2026-06-23-ops-recognition-bridge-design.md` (DESIGN round-4, operator-ratified D1–D4 + predicate-transition guard)
**Migration:** ops `009` (ONE up file + ONE down file, built INCREMENTALLY across T0–T6).

---

## Goal

Make the built-but-inert Chip-3 recognition engine reachable and live through the PM UI by introducing a governed **completion-for-recognition attestation** as the explicit, audited source of `ops.apparatus.status='Complete'`. The slice ships the full vertical: `009` (DB authority) → `packages/ops-intake` wrappers (seam) → `recognition_router.py` (host-gated API) → `/pm-review/recognition` (UI). Recognition only — no billing, no production tracking. Dev-only on `ops_dev` behind a hard prod release gate.

## Architecture

- **DB authority (`009`):** one migration adds `ops.completion_attestation` (with an immutability trigger), a predicate-transition completion guard on `ops.apparatus`, `attest_apparatus_complete` / `revoke_completion_attestation` mutation functions, a recognition-event trace column, the firewall touch to `approve_and_recognize` + `trg_revrec_insert_integrity`, and two read views. The migration is the sole sanctioned writer of governed-complete state.
- **Package seam:** thin wrappers in `packages/ops-intake/src/ops_intake/recognition.py` call the `009` functions and map DB exceptions to typed, value-free errors (the `ops.*` sole-writer discipline already lives in this package).
- **API:** a new host-gated `recognition_router.py` (sibling to `intake_router.py`), registered only when `OPS_DEV_DSN` is set, path-distinct from the prod derive-on-read `GET /api/v1/ops/revenue-recognition`.
- **UI:** `/pm-review/recognition` — worklist table with flag-gated action buttons, enum-constrained clearance inputs, a recognized-$ rollup panel, route-mocked Playwright smoke.

## Tech Stack

- **DB:** PostgreSQL 17 (host `apex-dev-pg`), schema `ops`, throwaway test DB `ops_test`. Migrations are plain `.sql` applied via `psycopg` autocommit (lane idiom).
- **Migration tests:** Python `pytest` + `psycopg[binary]` run via `uv` (`uv run --with "psycopg[binary]" --with pytest pytest <file>`), DSN pinned to `ops_test`.
- **Package:** `packages/ops-intake` (`uv`, `psycopg`); tests via the package `conftest.py` migration fixture against `ops_test`.
- **API:** `apps/control-plane-api` — FastAPI, `pip` + `requirements.txt` (NOT uv); sibling pkgs wired `-e ../../packages/<x>`; tests need `OPS_DEV_DSN` (→ `ops_test`) exported; `fastapi.testclient.TestClient`.
- **UI:** `apps/operations-web` — Next.js 16 + React 19 + TypeScript; node20 via nvm + pnpm; Playwright (`next build` precedes browser smokes; `*.unit.spec.ts` skip the server).

## Global Constraints

These apply to EVERY task; each task implicitly includes them.

1. **DDL runs on throwaway `ops_test` ONLY.** Every migration test asserts `current_database()=='ops_test'` before any DDL and pins the DSN via `conninfo_to_dict` (mirror `test_008_core_equipment_models.py`). NEVER `ops_dev` in tests.
2. **Eligibility predicate is `provenance_status='approved'`** (NOT `source='ops-intake'`). The live Miner rows are `source='miner_rev10.xlsm'`; all 5,344 are `provenance_status='approved'`. A `source`-keyed predicate would match 0 Miner rows.
3. **`obligation_clearance` enum values are exactly `{'provided','not_applicable'}`** (005:9).
4. **Lock order is APPARATUS BEFORE ledger/attestation rows** (D-OPS-12). `revoke` must lock the apparatus FIRST and never row-lock `ops.revenue_recognition_event`.
5. **The down migration restores `approve_and_recognize` + `trg_revrec_insert_integrity` to their VERBATIM 005-up bodies**, preserving the review-fixed `is distinct from` null-safety and the `for update of a2` serialization. A `pg_get_functiondef` source-diff test proves it (a happy-path recognize is NOT sufficient).
6. **Errors crossing the package/API boundary are VALUE-FREE** — no dollar amounts, no internal text; generic 400/409.
7. **UI copy is `Attest testing complete - for recognition` everywhere; NEVER `production complete`.**
8. **HARD PROD RELEASE GATE:** `009` may merge to `main` and apply to `ops_dev` on the interim posture (host-gating + the misuse guards). `009` and any `ops.*` recognition path MUST NOT reach prod until the `ops_app` role boundary is applied: `REVOKE INSERT, UPDATE(status, source, provenance_status) ON ops.apparatus`; no direct DML on `ops.completion_attestation` or the recognition ledger; mutation functions become `SECURITY DEFINER` owned by the object owner with `set search_path = ops, pg_temp` (NOT `public`); `REVOKE CREATE ON SCHEMA public FROM PUBLIC`. The ctx-guard is forgeable, so the role boundary is a *precondition of prod apply*, not a follow-up. This is restated as the final non-code gate item (T10, item G).
9. **Merge to `main` + `ops_dev` apply are OPERATOR-GATED.**

### Toolchain command facts

- **Migration + package tests (uv):**
  ```
  export PATH=$HOME/.local/bin:$PATH
  set -a; . infra/.env; set +a           # sources the governed 0600 .env for DEV_PG_PASSWORD; NEVER echo it
  export OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"
  uv run --with "psycopg[binary]" --with pytest pytest <path>
  ```
  (The migration test files also embed a default `ops_test` DSN, so the assert holds even if `OPS_DEV_DSN` is unset; sourcing `infra/.env` supplies the password.)
- **API tests (pip):**
  ```
  cd apps/control-plane-api
  python -m pip install -r requirements.txt -r requirements-dev.txt   # sibling pkgs wired -e
  export OPS_DEV_DSN="...dbname=ops_test..."
  python -m pytest tests/test_ops_recognition_routes.py
  ```
- **UI:**
  ```
  . $HOME/.nvm/nvm.sh
  cd apps/operations-web
  pnpm install
  pnpm typecheck
  pnpm exec playwright test tests/recognition.unit.spec.ts             # pure-logic, no server
  pnpm exec playwright test tests/browser-shell.pm-recognition.smoke.spec.ts   # next build runs via webServer
  ```
- **Subagents edit host files via write-local-then-ssh** (`ssh olares-mesh 'cat > dest' < local`); heredocs break on code quotes.

---

## File Structure

```
infra/database/migrations/ops/
  009_recognition_bridge.sql              (NEW — built incrementally T0–T6)
  009_recognition_bridge_down.sql         (NEW — built incrementally T0–T6)
  test_009_recognition_bridge.py          (NEW — migration TDD harness, T0–T7)

packages/ops-intake/
  src/ops_intake/recognition.py           (NEW — T8 wrappers + typed value-free errors)
  tests/test_recognition_wrappers.py      (NEW — T8 wrapper tests)
  tests/test_approve_envelope.py          (MODIFY — T8, line ~72: reach 'Complete' via attest fn)

apps/control-plane-api/
  services/ops/recognition_router.py      (NEW — T9 APIRouter)
  main.py                                 (MODIFY — T9, register the host-gated router)
  tests/test_ops_recognition_routes.py    (NEW — T9 API tests)

apps/operations-web/
  app/pm-review/recognition/page.tsx      (NEW — T10 UI page)
  lib/recognition.ts                      (NEW — T10 typed API client + view-model)
  tests/recognition.unit.spec.ts          (NEW — T10 pure-logic unit spec)
  tests/browser-shell.pm-recognition.smoke.spec.ts  (NEW — T10 route-mocked Playwright smoke)
```

---

## Task 0 — Test harness + `009` skeleton (table + active-unique index + comment)

**Files**
- Create: `infra/database/migrations/ops/test_009_recognition_bridge.py`
- Create: `infra/database/migrations/ops/009_recognition_bridge.sql`
- Create: `infra/database/migrations/ops/009_recognition_bridge_down.sql`

**Interfaces**
- Consumes: `ops.apparatus(id)`, `ops.persons(person_id)`, `ops.apparatus_status` (001/004); the 001..008 chain.
- Produces: table `ops.completion_attestation`; partial-unique index `uq_completion_attestation_active`; a session pytest fixture chaining 001..009 on `ops_test`.

**Steps**

- [ ] Write the test harness `test_009_recognition_bridge.py` (mirror `test_008` DSN guard + chain + `_clean_slate`; appended to in T1–T7). Create locally then push:
  ```python
  # test_009_recognition_bridge.py — MIRRORS test_008's DSN/guard/fixture idiom; runs on ops_test ONLY.
  import os, pathlib, uuid
  import psycopg, pytest
  from psycopg.conninfo import conninfo_to_dict
  HERE = pathlib.Path(__file__).parent
  DSN = os.environ.get("OPS_DEV_DSN") or (
      "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
      f"password={os.environ.get('OPS_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD','')} sslmode=disable")
  assert conninfo_to_dict(DSN).get("dbname") == "ops_test", "009 migration tests run on ops_test ONLY"
  DOWN1 = HERE / "001_identity_skeleton_down.sql"
  CHAIN = ["001_identity_skeleton.sql","002_quote_model.sql","003_intake_unique_keys.sql",
           "004_person_anchor.sql","005_recognition_ledger.sql","006_progress_billing.sql",
           "007_intake_envelope.sql","008_core_equipment_models.sql","009_recognition_bridge.sql"]
  UP   = HERE / "009_recognition_bridge.sql"
  DOWN = HERE / "009_recognition_bridge_down.sql"

  def _exec(path):
      with psycopg.connect(DSN, autocommit=True) as c:
          c.execute(pathlib.Path(path).read_text(encoding="utf-8"))

  def _clean_slate():
      with psycopg.connect(DSN, autocommit=True) as c:
          c.execute("drop schema if exists core cascade")
      _exec(DOWN1)

  @pytest.fixture(scope="session", autouse=True)
  def apply_migrations():
      with psycopg.connect(DSN) as c, c.cursor() as cur:        # hard runtime guard
          cur.execute("select current_database()")
          assert cur.fetchone()[0] == "ops_test", "REFUSING DDL: current_database() != ops_test"
      _clean_slate()
      for f in CHAIN: _exec(HERE / f)                           # applies 001..009
      yield
      _clean_slate()

  @pytest.fixture
  def conn():
      with psycopg.connect(DSN) as c:
          try: yield c
          finally: c.rollback()

  # ---- helpers: seed an eligible (approved, frozen, positive-basis) apparatus ----
  def _seed_person(cur, name="PM"):
      cur.execute("insert into ops.persons (display_name) values (%s) returning person_id", (name,))
      return cur.fetchone()[0]

  def _seed_eligible_apparatus(cur, *, status="Not Started", provenance="approved",
                               scope_status="In Progress", project_status="Active",
                               is_active=True, scope_active=True, project_active=True,
                               frozen=True, quoted_hours=10, quoted_revenue=1500):
      """Seed project->scope->scope_quote(frozen)->apparatus; returns apparatus_id.
      blended_rate is GENERATED (P4); onsite_labor + total_quoted_hours make it positive."""
      cur.execute("insert into ops.projects (project_number, project_name, status, provenance_status, is_active)"
                  " values (%s,'P',%s,'approved',%s) returning id",
                  (f"P-{uuid.uuid4().hex[:8]}", project_status, project_active))
      pid = cur.fetchone()[0]
      cur.execute("insert into ops.scopes (project_id, scope_name, status, provenance_status, is_active, source)"
                  " values (%s,'S',%s,'approved',%s,'ops-intake') returning id",
                  (pid, scope_status, scope_active))
      sid = cur.fetchone()[0]
      cur.execute("insert into ops.scope_quote (scope_id, onsite_labor, unit_multiplier, pct_adjust,"
                  " total_quoted_hours, is_frozen, frozen_at)"
                  " values (%s,1500,1,1,%s,%s, case when %s then now() else null end)",
                  (sid, quoted_hours, frozen, frozen))
      cur.execute("insert into ops.apparatus (scope_id, apparatus_designation, status, provenance_status,"
                  " is_active, quoted_hours, quoted_revenue, source)"
                  " values (%s,'A-1',%s,%s,%s,%s,%s,'ops-intake') returning id",
                  (sid, status, provenance, is_active, quoted_hours, quoted_revenue))
      return cur.fetchone()[0]

  def test_db_is_ops_test(conn):
      with conn.cursor() as cur:
          cur.execute("select current_database()"); assert cur.fetchone()[0] == "ops_test"

  def test_chain_applies_through_009_table_and_index_present(conn):
      with conn.cursor() as cur:
          cur.execute("select 1 from information_schema.tables where table_schema='ops' and table_name='completion_attestation'")
          assert cur.fetchone()
          cur.execute("select 1 from pg_indexes where schemaname='ops' and indexname='uq_completion_attestation_active'")
          assert cur.fetchone()
          cur.execute("select obj_description('ops.completion_attestation'::regclass)")
          assert 'FOR RECOGNITION' in (cur.fetchone()[0] or '')

  def test_active_unique_one_per_apparatus(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s")
          who = _seed_person(cur)
          aid = _seed_eligible_apparatus(cur)
          cur.execute("insert into ops.completion_attestation (apparatus_id, attested_by, reason, prior_status)"
                      " values (%s,%s,'r','Not Started')", (aid, who))
          try:
              cur.execute("insert into ops.completion_attestation (apparatus_id, attested_by, reason, prior_status)"
                          " values (%s,%s,'r2','Not Started')", (aid, who))
              assert False, "second active attestation accepted — partial-unique index missing"
          except psycopg.errors.UniqueViolation:
              pass
          cur.execute("rollback to savepoint s")

  def test_down_then_reup_idempotent():
      _exec(DOWN)
      with psycopg.connect(DSN) as c, c.cursor() as cur:
          cur.execute("select 1 from information_schema.tables where table_schema='ops' and table_name='completion_attestation'")
          assert cur.fetchone() is None, "009 down did not drop completion_attestation"
          cur.execute("select count(*) from ops.apparatus")   # 001-008 survive
      _exec(UP)
      with psycopg.connect(DSN) as c, c.cursor() as cur:
          cur.execute("select 1 from information_schema.tables where table_schema='ops' and table_name='completion_attestation'")
          assert cur.fetchone(), "009 re-up did not recreate the table"

  def test_down_is_idempotent_double_down():
      """Running the 009 DOWN migration TWICE in a row (after a full 001..009 up) must be a
      clean no-op the second time — proving the IF-EXISTS / create-or-replace idempotency of
      every down block (T6 drop view if exists; T5 create or replace + alter ... drop column
      if exists; T4/T3 drop function if exists; T2/T1 drop trigger if exists + drop function
      if exists; T0 drop table if exists). A double-down must raise NOTHING. Restores the
      full 001..009 session state afterward so later tests are unaffected."""
      _exec(DOWN)            # first down: tears 009 back to the 001..008 baseline
      _exec(DOWN)            # second down on the already-torn-down state: MUST be a clean no-op
      with psycopg.connect(DSN) as c, c.cursor() as cur:
          cur.execute("select 1 from information_schema.tables where table_schema='ops' and table_name='completion_attestation'")
          assert cur.fetchone() is None, "table present after double-down"
          cur.execute("select count(*) from ops.apparatus")   # 001-008 still intact
      _exec(UP)             # restore the 001..009 session post-state for the remaining tests
      with psycopg.connect(DSN) as c, c.cursor() as cur:
          cur.execute("select 1 from information_schema.tables where table_schema='ops' and table_name='completion_attestation'")
          assert cur.fetchone(), "009 re-up after double-down did not recreate the table"
  ```

- [ ] Run to verify fail (the CHAIN references a missing `009_recognition_bridge.sql`):
  ```
  export PATH=$HOME/.local/bin:$PATH; set -a; . infra/.env; set +a
  export OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q
  ```
  Expected: fixture error — `FileNotFoundError: ...009_recognition_bridge.sql`.

- [ ] Implement `009_recognition_bridge.sql` (T0 segment — table + index + comment, spec 5.1):
  ```sql
  -- ============================================================================
  -- ops migration 009 — recognition bridge (completion attestation -> recognize).
  -- Built INCREMENTALLY across plan tasks T0..T6; each task appends one block to
  -- THIS file and the matching teardown to 009_recognition_bridge_down.sql.
  -- Dev DB: ops_dev / ops_test. Nothing applied to prod (blocked behind the §5.11
  -- ops_app role-boundary RELEASE GATE). Builds on 001-008.
  -- ============================================================================

  -- ---- T0: completion attestation table + one-active-per-apparatus index -----
  create table ops.completion_attestation (
    id            uuid primary key default gen_random_uuid(),
    apparatus_id  uuid not null references ops.apparatus(id),
    attested_by   uuid not null references ops.persons(person_id),
    reason        text not null check (btrim(reason) <> ''),
    provenance    text not null default 'pm_recognition_attestation'
                    check (provenance in ('pm_recognition_attestation')),
    prior_status  ops.apparatus_status not null,
    attested_at   timestamptz not null default now(),
    revoked_at    timestamptz,
    revoked_by    uuid references ops.persons(person_id),
    revoke_reason text
  );
  create unique index uq_completion_attestation_active
    on ops.completion_attestation (apparatus_id) where revoked_at is null;
  comment on table ops.completion_attestation is
    'Governed PM attestation that an apparatus is testing-complete FOR RECOGNITION. NOT production truth, NOT customer-facing. Sole sanctioned writer of ops.apparatus.status=Complete for approved apparatus. A future production-tracking authority supersedes via provenance=production_tracking.';
  ```

- [ ] Implement `009_recognition_bridge_down.sql` (T0 segment — drop the table):
  ```sql
  -- ============================================================================
  -- DOWN — ops migration 009 recognition bridge. Undoes ONLY 009 (leaves 001-008
  -- intact). FULLY IDEMPOTENT: every block uses `if exists` / `create or replace`, so
  -- running this down TWICE in a row is a clean no-op (proven by
  -- test_down_is_idempotent_double_down). Built incrementally across T0..T6: each task
  -- PREPENDS its teardown so the down runs in reverse dependency order. Final order
  -- (T6 top -> T0 bottom): drop views; drop completion guard; drop attestation-
  -- immutability trigger/fn; create-or-replace the two 005 fns VERBATIM; drop the
  -- trace column; drop revoke fn; drop attest fn; drop completion_attestation.
  -- ============================================================================

  -- ---- T0: drop the completion attestation table -----------------------------
  drop table if exists ops.completion_attestation cascade;
  ```

- [ ] Run to verify pass:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q
  ```
  Expected: 5 passed (`test_db_is_ops_test`, `test_chain_applies_through_009_table_and_index_present`, `test_active_unique_one_per_apparatus`, `test_down_then_reup_idempotent`, `test_down_is_idempotent_double_down`).

- [ ] Commit:
  ```
  git add infra/database/migrations/ops/009_recognition_bridge.sql infra/database/migrations/ops/009_recognition_bridge_down.sql infra/database/migrations/ops/test_009_recognition_bridge.py
  git commit -m "feat(ops/009): T0 completion_attestation table + active-unique index + migration harness"
  ```

---

## Task 1 — Attestation immutability trigger (spec 5.1)

**Files**
- Modify: `infra/database/migrations/ops/009_recognition_bridge.sql` (append T1 block)
- Modify: `infra/database/migrations/ops/009_recognition_bridge_down.sql` (prepend T1 teardown)
- Modify: `infra/database/migrations/ops/test_009_recognition_bridge.py` (append T1 tests)

**Interfaces**
- Produces: function `ops.trg_completion_attestation_immutable()`; trigger `completion_attestation_immutable` (BEFORE UPDATE OR DELETE on `ops.completion_attestation`).
- Invariant: core fields immutable; DELETE blocked; the ONLY permitted UPDATE is a single well-formed revoke (`revoked_at` + `revoked_by` + non-blank `revoke_reason` all set together, from an all-NULL prior state).

**Steps**

- [ ] Write failing tests (append to `test_009_recognition_bridge.py`):
  ```python
  def _seed_attestation(cur, who, aid, reason="r"):
      cur.execute("insert into ops.completion_attestation (apparatus_id, attested_by, reason, prior_status)"
                  " values (%s,%s,%s,'Not Started') returning id", (aid, who, reason))
      return cur.fetchone()[0]

  def test_immutable_core_field_update_fails(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur); aid=_seed_eligible_apparatus(cur)
          att=_seed_attestation(cur, who, aid)
          try:
              cur.execute("update ops.completion_attestation set reason='changed' where id=%s",(att,))
              assert False, "core-field UPDATE accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_immutable_delete_fails(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur); aid=_seed_eligible_apparatus(cur)
          att=_seed_attestation(cur, who, aid)
          try:
              cur.execute("delete from ops.completion_attestation where id=%s",(att,))
              assert False, "DELETE accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_immutable_partial_revoke_fails_missing_revoked_at(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur); aid=_seed_eligible_apparatus(cur)
          att=_seed_attestation(cur, who, aid)
          try:
              cur.execute("update ops.completion_attestation set revoked_by=%s where id=%s",(who,att))
              assert False, "partial revoke (revoked_by w/o revoked_at) accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_immutable_blank_revoke_reason_fails(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur); aid=_seed_eligible_apparatus(cur)
          att=_seed_attestation(cur, who, aid)
          try:
              cur.execute("update ops.completion_attestation set revoked_at=now(), revoked_by=%s, revoke_reason='  '"
                          " where id=%s",(who,att))
              assert False, "blank revoke_reason accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_immutable_wellformed_revoke_succeeds_then_double_revoke_fails(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur); aid=_seed_eligible_apparatus(cur)
          att=_seed_attestation(cur, who, aid)
          cur.execute("update ops.completion_attestation set revoked_at=now(), revoked_by=%s, revoke_reason='superseded'"
                      " where id=%s",(who,att))
          cur.execute("select revoked_at is not null from ops.completion_attestation where id=%s",(att,))
          assert cur.fetchone()[0] is True
          try:
              cur.execute("update ops.completion_attestation set revoke_reason='again' where id=%s",(att,))
              assert False, "double-revoke / post-revoke mutation accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")
  ```

- [ ] Run to verify fail:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q -k immutable
  ```
  Expected: every `test_immutable_*` FAILS at the `assert False` (the trigger does not exist yet, so the raw UPDATE/DELETE succeeds).

- [ ] Implement — append to `009_recognition_bridge.sql`:
  ```sql
  -- ---- T1: attestation immutability (append-only completion proof) -----------
  create function ops.trg_completion_attestation_immutable() returns trigger language plpgsql as $$
  begin
    if tg_op = 'DELETE' then raise exception 'ops.completion_attestation is append-only (DELETE blocked)'; end if;
    if new.id is distinct from old.id or new.apparatus_id is distinct from old.apparatus_id
       or new.attested_by is distinct from old.attested_by or new.reason is distinct from old.reason
       or new.provenance is distinct from old.provenance or new.prior_status is distinct from old.prior_status
       or new.attested_at is distinct from old.attested_at then
      raise exception 'ops.completion_attestation core fields are immutable (id %)', old.id;
    end if;
    -- the ONLY permitted UPDATE is a single, well-formed revoke transition:
    -- all revoke fields NULL -> all populated together (revoked_at + revoked_by + non-blank revoke_reason).
    if old.revoked_at is not null or old.revoked_by is not null or old.revoke_reason is not null then
      raise exception 'ops.completion_attestation % already revoked (immutable)', old.id;
    end if;
    if not (new.revoked_at is not null and new.revoked_by is not null
            and btrim(coalesce(new.revoke_reason,'')) <> '') then
      raise exception 'ops.completion_attestation %: only a complete revoke is permitted (revoked_at + revoked_by + non-blank reason set together)', old.id;
    end if;
    return new;
  end; $$;
  create trigger completion_attestation_immutable before update or delete on ops.completion_attestation
    for each row execute function ops.trg_completion_attestation_immutable();
  ```

- [ ] Implement — PREPEND the T1 teardown above the T0 block in `009_recognition_bridge_down.sql` (so the down drops the trigger/fn before the table):
  ```sql
  -- ---- T1: drop attestation-immutability trigger + function ------------------
  drop trigger if exists completion_attestation_immutable on ops.completion_attestation;
  drop function if exists ops.trg_completion_attestation_immutable() cascade;
  ```

- [ ] Run to verify pass:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q
  ```
  Expected: all T0 + T1 tests pass.

- [ ] Commit:
  ```
  git add infra/database/migrations/ops/009_recognition_bridge.sql infra/database/migrations/ops/009_recognition_bridge_down.sql infra/database/migrations/ops/test_009_recognition_bridge.py
  git commit -m "feat(ops/009): T1 attestation immutability trigger (append-only, well-formed-revoke-only)"
  ```

---

## Task 2 — Completion guard trigger (predicate-transition aware, spec 5.7)

**Files**
- Modify: `infra/database/migrations/ops/009_recognition_bridge.sql` (append T2 block)
- Modify: `infra/database/migrations/ops/009_recognition_bridge_down.sql` (prepend T2 teardown)
- Modify: `infra/database/migrations/ops/test_009_recognition_bridge.py` (append T2 tests)

**Interfaces**
- Produces: function `ops.trg_apparatus_completion_guard()`; trigger `apparatus_completion_guard` (BEFORE INSERT OR UPDATE on `ops.apparatus`).
- Invariant: a row may enter/leave governed-complete `g := (status='Complete' AND provenance_status='approved')` only when the txn-local GUC `ops.completion_ctx='1'` is set (the attest/revoke functions set it). Misuse guard, not a security boundary.

**Steps**

- [ ] Write failing tests (append to `test_009_recognition_bridge.py`):
  ```python
  def test_guard_insert_as_governed_complete_fails(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s")
          # build chain manually so we can attempt the bypass INSERT directly on apparatus
          cur.execute("insert into ops.projects (project_number, project_name, provenance_status)"
                      " values (%s,'P','approved') returning id",(f"P-{uuid.uuid4().hex[:8]}",))
          pid=cur.fetchone()[0]
          cur.execute("insert into ops.scopes (project_id, scope_name, provenance_status) values (%s,'S','approved') returning id",(pid,))
          sid=cur.fetchone()[0]
          try:
              cur.execute("insert into ops.apparatus (scope_id, apparatus_designation, status, provenance_status)"
                          " values (%s,'X','Complete','approved')",(sid,))
              assert False, "INSERT as governed-complete (no ctx) accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_guard_draft_complete_then_flip_provenance_fails(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s")
          cur.execute("insert into ops.projects (project_number, project_name, provenance_status)"
                      " values (%s,'P','approved') returning id",(f"P-{uuid.uuid4().hex[:8]}",))
          pid=cur.fetchone()[0]
          cur.execute("insert into ops.scopes (project_id, scope_name, provenance_status) values (%s,'S','approved') returning id",(pid,))
          sid=cur.fetchone()[0]
          # INSERT status=Complete, provenance=draft is NOT g -> allowed
          cur.execute("insert into ops.apparatus (scope_id, apparatus_designation, status, provenance_status)"
                      " values (%s,'X','Complete','draft') returning id",(sid,))
          aid=cur.fetchone()[0]
          # flipping provenance to 'approved' ENTERS g without ctx -> must fail on the 2nd stmt
          try:
              cur.execute("update ops.apparatus set provenance_status='approved' where id=%s",(aid,))
              assert False, "draft-Complete -> flip-provenance bypass accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_guard_normal_intake_insert_succeeds(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s")
          aid=_seed_eligible_apparatus(cur, status="Not Started", provenance="approved")  # not g -> allowed
          cur.execute("select status, provenance_status from ops.apparatus where id=%s",(aid,))
          assert cur.fetchone()==("Not Started","approved")
          cur.execute("rollback to savepoint s")

  def test_guard_direct_update_status_complete_fails(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s")
          aid=_seed_eligible_apparatus(cur, status="In Progress", provenance="approved")
          try:
              cur.execute("update ops.apparatus set status='Complete' where id=%s",(aid,))
              assert False, "direct UPDATE status=Complete (no ctx) accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_guard_ctx_path_update_succeeds(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s")
          aid=_seed_eligible_apparatus(cur, status="In Progress", provenance="approved")
          cur.execute("select set_config('ops.completion_ctx','1', true)")  # txn-local, mimics attest fn
          cur.execute("update ops.apparatus set status='Complete' where id=%s",(aid,))
          cur.execute("select status from ops.apparatus where id=%s",(aid,))
          assert cur.fetchone()[0]=="Complete"
          cur.execute("rollback to savepoint s")
  ```

- [ ] Run to verify fail:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q -k guard
  ```
  Expected: the four bypass/`fails` tests FAIL at `assert False` (no guard yet); `test_guard_ctx_path_update_succeeds` already passes.

- [ ] Implement — append to `009_recognition_bridge.sql`:
  ```sql
  -- ---- T2: completion guard — predicate-transition aware (governed-complete) --
  create function ops.trg_apparatus_completion_guard() returns trigger language plpgsql as $$
  declare
    new_g boolean := (new.status='Complete' and new.provenance_status='approved');
    old_g boolean;
  begin
    if tg_op = 'INSERT' then
      if new_g and current_setting('ops.completion_ctx', true) is distinct from '1' then
        raise exception 'apparatus %: governed-complete may be entered only via attest', new.id;
      end if;
    else  -- UPDATE
      old_g := (old.status='Complete' and old.provenance_status='approved');
      if (new_g is distinct from old_g) and current_setting('ops.completion_ctx', true) is distinct from '1' then
        raise exception 'apparatus %: governed-complete may change only via attest/revoke', new.id;
      end if;
    end if;
    return new;
  end; $$;
  create trigger apparatus_completion_guard before insert or update on ops.apparatus
    for each row execute function ops.trg_apparatus_completion_guard();
  ```

- [ ] Implement — PREPEND the T2 teardown (above T1) in `009_recognition_bridge_down.sql`:
  ```sql
  -- ---- T2: drop completion guard trigger + function -------------------------
  drop trigger if exists apparatus_completion_guard on ops.apparatus;
  drop function if exists ops.trg_apparatus_completion_guard() cascade;
  ```

- [ ] Run to verify pass:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q
  ```
  Expected: all T0–T2 tests pass.

- [ ] Commit:
  ```
  git add infra/database/migrations/ops/009_recognition_bridge.sql infra/database/migrations/ops/009_recognition_bridge_down.sql infra/database/migrations/ops/test_009_recognition_bridge.py
  git commit -m "feat(ops/009): T2 predicate-transition completion guard (INSERT+UPDATE, ctx-gated governed-complete)"
  ```

---

## Task 3 — `ops.attest_apparatus_complete` function (spec 5.3)

**Files**
- Modify: `infra/database/migrations/ops/009_recognition_bridge.sql` (append T3 block)
- Modify: `infra/database/migrations/ops/009_recognition_bridge_down.sql` (prepend T3 teardown)
- Modify: `infra/database/migrations/ops/test_009_recognition_bridge.py` (append T3 tests)

**Interfaces**
- Produces: `ops.attest_apparatus_complete(p_apparatus_id uuid, p_attested_by uuid, p_reason text) returns uuid`.
- Behavior: validate eligibility (`provenance_status='approved'`, active non-cancelled chain, status NOT IN Complete/Cancelled, frozen + positive basis, known actor, non-blank reason) under `FOR UPDATE`; capture `prior_status`; set ctx; flip status to `'Complete'`; insert the attestation; return its id. Second active attestation -> unique violation.

**Steps**

- [ ] Write failing tests (append to `test_009_recognition_bridge.py`):
  ```python
  def test_attest_success_sets_complete_and_captures_prior(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'tested ok')",(aid,who))
          att=cur.fetchone()[0]
          cur.execute("select status from ops.apparatus where id=%s",(aid,)); assert cur.fetchone()[0]=="Complete"
          cur.execute("select prior_status, attested_by, reason from ops.completion_attestation where id=%s",(att,))
          ps, ab, r = cur.fetchone(); assert ps=="In Progress" and ab==who and r=="tested ok"
          cur.execute("rollback to savepoint s")

  def test_attest_rejects_unapproved_provenance(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, provenance="draft")
          try:
              cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,who)); assert False
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_attest_rejects_cancelled_chain(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, scope_status="Cancelled")
          try:
              cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,who)); assert False
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_attest_rejects_inactive(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, is_active=False)
          try:
              cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,who)); assert False
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_attest_rejects_already_complete(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,who))   # now Complete + active attestation
          # revoke nothing; a second attest must fail (status already Complete AND unique index)
          try:
              cur.execute("select ops.attest_apparatus_complete(%s,%s,'y')",(aid,who)); assert False
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_attest_rejects_unfrozen_basis(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, frozen=False)
          try:
              cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,who)); assert False
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_attest_rejects_nonpositive_basis(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, quoted_revenue=0)
          try:
              cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,who)); assert False
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_attest_rejects_unknown_actor(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s")
          aid=_seed_eligible_apparatus(cur)
          try:
              cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid,str(uuid.uuid4()))); assert False
          except (psycopg.errors.RaiseException, psycopg.errors.ForeignKeyViolation): pass
          cur.execute("rollback to savepoint s")

  def test_attest_rejects_blank_reason(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur)
          try:
              cur.execute("select ops.attest_apparatus_complete(%s,%s,'   ')",(aid,who)); assert False
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")
  ```

- [ ] Run to verify fail:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q -k attest
  ```
  Expected: all `test_attest_*` error (function `ops.attest_apparatus_complete` does not exist -> `UndefinedFunction`).

- [ ] Implement — append to `009_recognition_bridge.sql`:
  ```sql
  -- ---- T3: attest_apparatus_complete (sole sanctioned status=Complete writer) -
  create function ops.attest_apparatus_complete(
    p_apparatus_id uuid, p_attested_by uuid, p_reason text
  ) returns uuid language plpgsql as $$
  declare a record; sq record; v_prior ops.apparatus_status; v_id uuid;
  begin
    if p_reason is null or btrim(p_reason) = '' then raise exception 'reason required'; end if;
    if not exists (select 1 from ops.persons where person_id = p_attested_by) then
      raise exception 'unknown actor %', p_attested_by;
    end if;
    select a2.scope_id, a2.status, a2.is_active, a2.provenance_status,
           a2.quoted_hours, a2.quoted_revenue,
           s.is_active as scope_active, s.status as scope_status,
           p.is_active as project_active, p.status as project_status
      into a
      from ops.apparatus a2
      join ops.scopes s   on s.id = a2.scope_id
      join ops.projects p on p.id = s.project_id
     where a2.id = p_apparatus_id
     for update of a2;
    if not found then raise exception 'apparatus % not found', p_apparatus_id; end if;
    if a.provenance_status <> 'approved' then
      raise exception 'apparatus % not approved (provenance_status=%)', p_apparatus_id, a.provenance_status;
    end if;
    if not (a.is_active and a.scope_active and a.project_active
            and a.scope_status <> 'Cancelled' and a.project_status <> 'Cancelled') then
      raise exception 'apparatus % inactive/cancelled chain cannot attest', p_apparatus_id;
    end if;
    if a.status in ('Complete','Cancelled') then
      raise exception 'apparatus % cannot attest from status %', p_apparatus_id, a.status;
    end if;
    select sq2.is_frozen, sq2.frozen_at into sq from ops.scope_quote sq2 where sq2.scope_id = a.scope_id;
    if not found or not sq.is_frozen or sq.frozen_at is null then
      raise exception 'scope % quote basis not frozen', a.scope_id;
    end if;
    if a.quoted_hours is null or a.quoted_hours <= 0
       or a.quoted_revenue is null or a.quoted_revenue <= 0 then
      raise exception 'apparatus % invalid quote basis', p_apparatus_id;
    end if;
    v_prior := a.status;
    perform set_config('ops.completion_ctx','1', true);
    update ops.apparatus set status='Complete', updated_at=now() where id=p_apparatus_id;
    insert into ops.completion_attestation (apparatus_id, attested_by, reason, prior_status)
      values (p_apparatus_id, p_attested_by, p_reason, v_prior)
      returning id into v_id;
    return v_id;
  end; $$;
  ```

- [ ] Implement — PREPEND the T3 teardown (above T2) in `009_recognition_bridge_down.sql`:
  ```sql
  -- ---- T3: drop attest function ---------------------------------------------
  drop function if exists ops.attest_apparatus_complete(uuid,uuid,text) cascade;
  ```

- [ ] Run to verify pass:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q
  ```
  Expected: all T0–T3 tests pass (including the second-active-attest unique conflict via `test_attest_rejects_already_complete`).

- [ ] Commit:
  ```
  git add infra/database/migrations/ops/009_recognition_bridge.sql infra/database/migrations/ops/009_recognition_bridge_down.sql infra/database/migrations/ops/test_009_recognition_bridge.py
  git commit -m "feat(ops/009): T3 attest_apparatus_complete (eligibility gates + ctx + prior_status capture)"
  ```

---

## Task 4 — `ops.revoke_completion_attestation` function (deadlock-safe, spec 5.4)

**Files**
- Modify: `infra/database/migrations/ops/009_recognition_bridge.sql` (append T4 block)
- Modify: `infra/database/migrations/ops/009_recognition_bridge_down.sql` (prepend T4 teardown)
- Modify: `infra/database/migrations/ops/test_009_recognition_bridge.py` (append T4 tests)

**Interfaces**
- Produces: `ops.revoke_completion_attestation(p_attestation_id uuid, p_revoked_by uuid, p_reason text) returns uuid`.
- Lock order (D-OPS-12): resolve `apparatus_id` UNLOCKED -> lock the apparatus `FOR UPDATE` FIRST -> re-select the active attestation `FOR UPDATE` + revalidate `apparatus_id` -> net-recognition gate -> ctx -> restore `prior_status` -> mark revoked. NEVER row-lock `revenue_recognition_event`.
- (The 2-connection deadlock/race proofs live in T7.)

**Steps**

- [ ] Write failing tests (append to `test_009_recognition_bridge.py`):
  ```python
  def test_revoke_blocked_when_net_positive(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
          cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
          try:
              cur.execute("select ops.revoke_completion_attestation(%s,%s,'oops')",(att,who))
              assert False, "revoke with open recognition accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_revoke_after_reverse_restores_prior_and_marks_revoked(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
          cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
          ev=cur.fetchone()[0]
          cur.execute("select ops.reverse_recognition(%s,%s,'correction')",(ev,who))   # net back to 0
          cur.execute("select ops.revoke_completion_attestation(%s,%s,'superseded')",(att,who))
          cur.execute("select status from ops.apparatus where id=%s",(aid,)); assert cur.fetchone()[0]=="In Progress"
          cur.execute("select revoked_at is not null, revoked_by, revoke_reason from ops.completion_attestation where id=%s",(att,))
          ra, rb, rr = cur.fetchone(); assert ra is True and rb==who and rr=="superseded"
          cur.execute("rollback to savepoint s")

  def test_revoke_unknown_actor_rejected(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
          try:
              cur.execute("select ops.revoke_completion_attestation(%s,%s,'x')",(att,str(uuid.uuid4()))); assert False
          except (psycopg.errors.RaiseException, psycopg.errors.ForeignKeyViolation): pass
          cur.execute("rollback to savepoint s")

  def test_revoke_blank_reason_rejected(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
          try:
              cur.execute("select ops.revoke_completion_attestation(%s,%s,'  ')",(att,who)); assert False
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")
  ```

- [ ] Run to verify fail:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q -k revoke
  ```
  Expected: all `test_revoke_*` error (`ops.revoke_completion_attestation` does not exist -> `UndefinedFunction`).

- [ ] Implement — append to `009_recognition_bridge.sql`:
  ```sql
  -- ---- T4: revoke_completion_attestation (deadlock-safe: apparatus locked FIRST)
  create function ops.revoke_completion_attestation(
    p_attestation_id uuid, p_revoked_by uuid, p_reason text
  ) returns uuid language plpgsql as $$
  declare v_app uuid; v_att record; v_net numeric;
  begin
    if p_reason is null or btrim(p_reason) = '' then raise exception 'reason required'; end if;
    if not exists (select 1 from ops.persons where person_id = p_revoked_by) then
      raise exception 'unknown actor %', p_revoked_by;
    end if;
    -- (2) resolve apparatus WITHOUT locking the attestation (taking the attestation
    --     lock first would invert approve_and_recognize's apparatus-first order -> deadlock).
    select apparatus_id into v_app from ops.completion_attestation
      where id = p_attestation_id and revoked_at is null;
    if not found then raise exception 'no active attestation %', p_attestation_id; end if;
    -- (3) lock the apparatus FIRST (D-OPS-12; matches approve_and_recognize 005:81).
    perform 1 from ops.apparatus where id = v_app for update;
    -- (4) re-select the active attestation FOR UPDATE + revalidate (a concurrent revoke
    --     may have won between steps 2-3).
    select id, apparatus_id, prior_status into v_att from ops.completion_attestation
      where id = p_attestation_id and revoked_at is null for update;
    if not found then raise exception 'attestation % no longer active', p_attestation_id; end if;
    if v_att.apparatus_id <> v_app then raise exception 'attestation apparatus mismatch'; end if;
    -- (5) net-recognition gate (deterministic under the apparatus lock).
    select coalesce(sum(recognized_amount),0) into v_net
      from ops.revenue_recognition_event where apparatus_id = v_app;
    if v_net > 0 then raise exception 'apparatus has open recognition; reverse first'; end if;
    -- (6-8) ctx -> restore prior_status -> mark revoked (immutability trigger permits this exact shape).
    perform set_config('ops.completion_ctx','1', true);
    update ops.apparatus set status=v_att.prior_status, updated_at=now() where id=v_app;
    update ops.completion_attestation
      set revoked_at=now(), revoked_by=p_revoked_by, revoke_reason=p_reason
      where id=p_attestation_id;
    return p_attestation_id;
  end; $$;
  ```

- [ ] Implement — PREPEND the T4 teardown (above T3) in `009_recognition_bridge_down.sql`:
  ```sql
  -- ---- T4: drop revoke function ---------------------------------------------
  drop function if exists ops.revoke_completion_attestation(uuid,uuid,text) cascade;
  ```

- [ ] Run to verify pass:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q
  ```
  Expected: all T0–T4 tests pass.

- [ ] Commit:
  ```
  git add infra/database/migrations/ops/009_recognition_bridge.sql infra/database/migrations/ops/009_recognition_bridge_down.sql infra/database/migrations/ops/test_009_recognition_bridge.py
  git commit -m "feat(ops/009): T4 revoke_completion_attestation (apparatus-first lock, net-gate, prior_status restore)"
  ```

---

## Task 5 — THE FIREWALL TOUCH (FOCUSED REVIEW) — trace column + `approve_and_recognize` + `trg_revrec_insert_integrity` (spec 5.2/5.5/5.6/5.9)

**Files**
- Modify: `infra/database/migrations/ops/009_recognition_bridge.sql` (append T5 block)
- Modify: `infra/database/migrations/ops/009_recognition_bridge_down.sql` (prepend T5 teardown — VERBATIM 005 bodies embedded)
- Modify: `infra/database/migrations/ops/test_009_recognition_bridge.py` (append T5 tests)

**Interfaces**
- Produces (up): column `ops.revenue_recognition_event.completion_attestation_id uuid references ops.completion_attestation(id)`; `create or replace ops.approve_and_recognize(...)` (verbatim 005 body + active-attestation lookup + threads `completion_attestation_id` into the recognized insert); `create or replace ops.trg_revrec_insert_integrity()` (verbatim 005 body + on `recognized` require non-null attestation `revoked_at IS NULL AND apparatus_id=new.apparatus_id`; on `reversal` require NULL).
- Produces (down): `create or replace` BOTH functions back to their VERBATIM 005-up bodies (005-down DROPs them — there is no body to "restore," so the verbatim bodies are EMBEDDED here) + drop the column.
- **Constraint 5:** the down must preserve the 005 `is distinct from` null-safety and the `for update of a2` serialization byte-for-byte (modulo `pg_get_functiondef` normalization).

**Steps**

- [ ] Write failing tests (append to `test_009_recognition_bridge.py`):
  ```python
  def _recognize(cur, who, *, status="In Progress"):
      aid=_seed_eligible_apparatus(cur, status=status)
      cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
      cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
      ev=cur.fetchone()[0]
      return aid, att, ev

  def test_recognize_populates_completion_attestation_id(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid, att, ev=_recognize(cur, who)
          cur.execute("select completion_attestation_id from ops.revenue_recognition_event where id=%s",(ev,))
          assert cur.fetchone()[0]==att
          cur.execute("rollback to savepoint s")

  def test_approve_and_recognize_rejects_when_no_active_attestation(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select set_config('ops.completion_ctx','1', true)")   # flip to Complete WITHOUT an attestation
          cur.execute("update ops.apparatus set status='Complete' where id=%s",(aid,))
          try:
              cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
              assert False, "recognize with no active attestation accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def _direct_recognized_insert(cur, aid, sid, pid, amount, qh, br, frozen_at, att_id):
      cur.execute("insert into ops.revenue_recognition_event"
                  " (apparatus_id, scope_id, project_id, event_type, recognized_amount, quoted_hours,"
                  "  blended_rate, basis_frozen_at, actor_person_id, datasheet_clearance, cx_clearance,"
                  "  completion_attestation_id)"
                  " select %s,%s,%s,'recognized',%s,%s,%s,%s, (select person_id from ops.persons limit 1),"
                  " 'not_applicable','not_applicable',%s",
                  (aid, sid, pid, amount, qh, br, frozen_at, att_id))

  def _chain_ids(cur, aid):
      cur.execute("select a.scope_id, s.project_id, a.quoted_revenue, a.quoted_hours, sq.blended_rate, sq.frozen_at"
                  " from ops.apparatus a join ops.scopes s on s.id=a.scope_id"
                  " join ops.scope_quote sq on sq.scope_id=a.scope_id where a.id=%s",(aid,))
      return cur.fetchone()

  def test_integrity_rejects_recognized_with_null_attestation(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who))   # Complete + active att
          sid,pid,rev,qh,br,fa=_chain_ids(cur,aid)
          try:
              _direct_recognized_insert(cur, aid, sid, pid, rev, qh, br, fa, None); assert False
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_integrity_rejects_recognized_with_foreign_attestation(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who))
          sid,pid,rev,qh,br,fa=_chain_ids(cur,aid)
          try:
              _direct_recognized_insert(cur, aid, sid, pid, rev, qh, br, fa, str(uuid.uuid4())); assert False
          except (psycopg.errors.RaiseException, psycopg.errors.ForeignKeyViolation): pass
          cur.execute("rollback to savepoint s")

  def test_integrity_rejects_recognized_with_revoked_attestation(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
          # revoke it (net 0, no recognition yet) -> now revoked; status restored to prior
          cur.execute("select ops.revoke_completion_attestation(%s,%s,'r')",(att,who))
          # re-flip to Complete via ctx so the integrity trigger's status check is not the blocker
          cur.execute("select set_config('ops.completion_ctx','1', true)")
          cur.execute("update ops.apparatus set status='Complete' where id=%s",(aid,))
          sid,pid,rev,qh,br,fa=_chain_ids(cur,aid)
          try:
              _direct_recognized_insert(cur, aid, sid, pid, rev, qh, br, fa, att); assert False, "revoked attestation accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  def test_integrity_rejects_recognized_with_cross_apparatus_attestation(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid1=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'a1')",(aid1,who)); att1=cur.fetchone()[0]
          aid2=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'a2')",(aid2,who))   # aid2 Complete + own att
          sid,pid,rev,qh,br,fa=_chain_ids(cur,aid2)
          try:
              _direct_recognized_insert(cur, aid2, sid, pid, rev, qh, br, fa, att1)   # att1 belongs to aid1
              assert False, "cross-apparatus attestation accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint s")

  # ---- FIREWALL REGRESSION: every original 005 recognized-integrity check still raises ----
  def test_firewall_regression_005_checks_still_raise(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
          sid,pid,rev,qh,br,fa=_chain_ids(cur,aid)
          # (a) lineage: wrong scope_id
          cur.execute("savepoint c")
          try:
              _direct_recognized_insert(cur, aid, str(uuid.uuid4()), pid, rev, qh, br, fa, att); assert False
          except (psycopg.errors.RaiseException, psycopg.errors.ForeignKeyViolation): pass
          cur.execute("rollback to savepoint c")
          # (b) recognized_amount distinct-from quoted_revenue
          cur.execute("savepoint c")
          try:
              _direct_recognized_insert(cur, aid, sid, pid, rev+1, qh, br, fa, att); assert False
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint c")
          # (c) basis-snapshot mismatch (wrong quoted_hours)
          cur.execute("savepoint c")
          try:
              _direct_recognized_insert(cur, aid, sid, pid, rev, qh+1, br, fa, att); assert False
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint c")
          # (d) status not Complete (revoke restores prior, leaving an active... so test on a non-complete app)
          aid2=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'x')",(aid2,who)); att2=cur.fetchone()[0]
          cur.execute("select ops.revoke_completion_attestation(%s,%s,'r')",(att2,who))  # status back to In Progress, att2 revoked
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'y')",(aid2,who)); att2b=cur.fetchone()[0]  # Complete again
          cur.execute("select set_config('ops.completion_ctx','1', true)")
          cur.execute("update ops.apparatus set status='Pending Review' where id=%s",(aid2,))  # leave g via ctx
          s2,p2,r2,h2,b2,f2=_chain_ids(cur,aid2)
          cur.execute("savepoint c")
          try:
              _direct_recognized_insert(cur, aid2, s2, p2, r2, h2, b2, f2, att2b); assert False, "non-complete accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint c")
          # (e) open-net idempotency: a real recognize, then a second direct recognized insert
          cur.execute("savepoint c")
          cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
          try:
              _direct_recognized_insert(cur, aid, sid, pid, rev, qh, br, fa, att); assert False, "double-recognize accepted"
          except psycopg.errors.RaiseException: pass
          cur.execute("rollback to savepoint c")
          cur.execute("rollback to savepoint s")

  # ---- DOWN SOURCE-DIFF: after 009-down, both 005 fns equal the 005-up defs (normalized) ----
  def _functiondef(dsn, signature):
      with psycopg.connect(dsn) as c, c.cursor() as cur:
          cur.execute("select pg_get_functiondef(%s::regprocedure)", (signature,))
          return cur.fetchone()[0]

  def _normalize(sql):
      import re
      return re.sub(r"\s+", " ", sql).strip()

  def test_down_restores_005_function_bodies_byte_for_byte():
      AR = "ops.approve_and_recognize(uuid,uuid,ops.obligation_clearance,text,ops.obligation_clearance,text)"
      II = "ops.trg_revrec_insert_integrity()"
      # capture the 009-up (modified) defs, then run 009-down, then capture the restored defs
      _exec(DOWN)
      restored_ar = _normalize(_functiondef(DSN, AR))
      restored_ii = _normalize(_functiondef(DSN, II))
      # rebuild a pristine 005-only baseline in a savepoint-free way: drop ops, apply 001..005,
      # read those defs, then restore the full 001..009 session state.
      _clean_slate()
      for f in ["001_identity_skeleton.sql","002_quote_model.sql","003_intake_unique_keys.sql",
                "004_person_anchor.sql","005_recognition_ledger.sql"]:
          _exec(HERE / f)
      baseline_ar = _normalize(_functiondef(DSN, AR))
      baseline_ii = _normalize(_functiondef(DSN, II))
      # restore the session post-state (001..009) for the remaining tests
      _clean_slate()
      for f in CHAIN: _exec(HERE / f)
      assert restored_ar == baseline_ar, "approve_and_recognize down-restore != 005-up definition"
      assert restored_ii == baseline_ii, "trg_revrec_insert_integrity down-restore != 005-up definition"
  ```

- [ ] Run to verify fail:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q -k "recognize or integrity or firewall or down_restores"
  ```
  Expected: column does not exist -> `test_recognize_populates_completion_attestation_id` errors (`UndefinedColumn`); the integrity/no-attestation tests `assert False` (the unmodified 005 trigger accepts NULL attestations); `test_down_restores...` fails (the 009-down does not yet replace the bodies).

- [ ] Implement — append the T5 UP block to `009_recognition_bridge.sql` (column + both `create or replace`; the embedded bodies are the verbatim 005 bodies with the two additions marked `-- 009:`):
  ```sql
  -- ---- T5: firewall touch — recognition trace column + the two Chip-3 fns -----
  alter table ops.revenue_recognition_event
    add column completion_attestation_id uuid references ops.completion_attestation(id);

  create or replace function ops.approve_and_recognize(
    p_apparatus_id        uuid,
    p_actor_person_id     uuid,
    p_datasheet_clearance ops.obligation_clearance,
    p_datasheet_ref       text,
    p_cx_clearance        ops.obligation_clearance,
    p_cx_ref              text
  ) returns uuid language plpgsql as $$
  declare a record; sq record; v_net numeric; v_id uuid; v_att uuid;   -- 009: v_att added
  begin
    select a2.scope_id, a2.status, a2.is_active, a2.quoted_hours, a2.quoted_revenue, a2.assessment,
           s.project_id, s.is_active as scope_active, s.status as scope_status,
           p.is_active as project_active, p.status as project_status
      into a
      from ops.apparatus a2
      join ops.scopes s   on s.id = a2.scope_id
      join ops.projects p on p.id = s.project_id
     where a2.id = p_apparatus_id
     for update of a2;
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
    -- 009: resolve the active completion attestation (required for a recognized row).
    select id into v_att from ops.completion_attestation
      where apparatus_id = p_apparatus_id and revoked_at is null;
    if not found then raise exception 'apparatus % has no active completion attestation', p_apparatus_id; end if;
    insert into ops.revenue_recognition_event
      (apparatus_id, scope_id, project_id, event_type, recognized_amount,
       quoted_hours, blended_rate, basis_frozen_at, assessment, actor_person_id,
       datasheet_clearance, datasheet_ref, cx_clearance, cx_ref, completion_attestation_id)  -- 009: column
    values
      (p_apparatus_id, a.scope_id, a.project_id, 'recognized', a.quoted_revenue,
       a.quoted_hours, sq.blended_rate, sq.frozen_at, a.assessment, p_actor_person_id,
       p_datasheet_clearance, p_datasheet_ref, p_cx_clearance, p_cx_ref, v_att)            -- 009: value
    returning id into v_id;
    return v_id;
  end;
  $$;

  create or replace function ops.trg_revrec_insert_integrity() returns trigger language plpgsql as $$
  declare v_scope uuid; a record; sq record; orig record;
  begin
    select scope_id into v_scope from ops.apparatus where id = new.apparatus_id;
    if not found then raise exception 'apparatus % not found', new.apparatus_id; end if;
    if new.scope_id <> v_scope then raise exception 'scope_id lineage mismatch'; end if;
    if new.project_id <> (select project_id from ops.scopes where id = new.scope_id) then
      raise exception 'project_id lineage mismatch';
    end if;

    if new.event_type = 'recognized' then
      -- 009: a recognized row MUST carry an active attestation for THIS apparatus.
      if new.completion_attestation_id is null then
        raise exception 'recognized row requires completion_attestation_id';
      end if;
      if not exists (select 1 from ops.completion_attestation
                     where id = new.completion_attestation_id
                       and revoked_at is null and apparatus_id = new.apparatus_id) then
        raise exception 'recognized row attestation invalid (revoked / wrong apparatus)';
      end if;
      select a2.status, a2.is_active, a2.quoted_hours, a2.quoted_revenue,
             s.is_active as scope_active, s.status as scope_status,
             p.is_active as project_active, p.status as project_status
        into a
        from ops.apparatus a2 join ops.scopes s on s.id=a2.scope_id join ops.projects p on p.id=s.project_id
       where a2.id = new.apparatus_id
       for update of a2;
      if not (a.is_active and a.scope_active and a.project_active
              and a.scope_status <> 'Cancelled' and a.project_status <> 'Cancelled') then
        raise exception 'recognized row for inactive/cancelled chain';
      end if;
      if a.status <> 'Complete' then raise exception 'recognized row for non-complete apparatus'; end if;
      select is_frozen, frozen_at, blended_rate into sq from ops.scope_quote where scope_id = new.scope_id;
      if not found or not sq.is_frozen or sq.frozen_at is null then
        raise exception 'recognized row on unfrozen basis';
      end if;
      if new.recognized_amount is distinct from a.quoted_revenue then
        raise exception 'recognized_amount must equal apparatus.quoted_revenue';
      end if;
      if new.quoted_hours is distinct from a.quoted_hours
         or new.blended_rate is distinct from sq.blended_rate
         or new.basis_frozen_at is distinct from sq.frozen_at then
        raise exception 'recognized row snapshot does not match current basis';
      end if;
      if (select coalesce(sum(recognized_amount),0)
            from ops.revenue_recognition_event where apparatus_id = new.apparatus_id) > 0 then
        raise exception 'apparatus % already has an open recognition', new.apparatus_id;
      end if;
    elsif new.event_type = 'reversal' then
      -- 009: reversal rows carry NO attestation (the trace is active-at-write on recognized only).
      if new.completion_attestation_id is not null then
        raise exception 'reversal row must not carry completion_attestation_id';
      end if;
      select apparatus_id, recognized_amount into orig
        from ops.revenue_recognition_event where id = new.reverses_event_id and event_type='recognized';
      if not found then raise exception 'reversal target is not a recognized event'; end if;
      if orig.apparatus_id <> new.apparatus_id then raise exception 'reversal apparatus mismatch'; end if;
      if new.recognized_amount <> -orig.recognized_amount then raise exception 'reversal amount must equal -(original)'; end if;
    end if;
    return new;
  end;
  $$;
  ```

- [ ] Implement — PREPEND the T5 teardown (above T4) in `009_recognition_bridge_down.sql`. This `create or replace`s BOTH functions back to their **VERBATIM 005-up bodies** (copied from `005_recognition_ledger.sql`), then drops the column:
  ```sql
  -- ---- T5: restore the two Chip-3 functions to their VERBATIM 005-up bodies ---
  -- (005-down DROPs these; there is no body to "restore," so the 005-up bodies are
  --  EMBEDDED here verbatim — preserving the FIX-A/FIX-B null-safety + serialization.
  --  A pg_get_functiondef source-diff test (T5) proves byte-equality, normalized.)
  -- PROVENANCE: the two function bodies below are a VERBATIM copy of
  --   infra/database/migrations/ops/005_recognition_ledger.sql (the SOURCE OF TRUTH).
  --   Do NOT hand-edit them here — edit 005 and re-copy. The drift guard is
  --   test_down_restores_005_function_bodies_byte_for_byte in test_009_recognition_bridge.py
  --   (pg_get_functiondef source-diff), which FAILS if these drift from the 005-up defs.
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

  alter table ops.revenue_recognition_event drop column if exists completion_attestation_id;
  ```

- [ ] Run to verify pass:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q
  ```
  Expected: all T0–T5 tests pass, including `test_firewall_regression_005_checks_still_raise` and `test_down_restores_005_function_bodies_byte_for_byte`.

- [ ] Commit:
  ```
  git add infra/database/migrations/ops/009_recognition_bridge.sql infra/database/migrations/ops/009_recognition_bridge_down.sql infra/database/migrations/ops/test_009_recognition_bridge.py
  git commit -m "feat(ops/009): T5 firewall touch — trace column + attestation-gated recognize/integrity + verbatim-005 down source-diff"
  ```

---

## Task 6 — Read views: worklist + rollup (spec 5.8)

**Files**
- Modify: `infra/database/migrations/ops/009_recognition_bridge.sql` (append T6 block)
- Modify: `infra/database/migrations/ops/009_recognition_bridge_down.sql` (prepend T6 teardown — drop BOTH views FIRST)
- Modify: `infra/database/migrations/ops/test_009_recognition_bridge.py` (append T6 tests)

**Interfaces**
- Produces: `ops.v_completion_recognition_worklist` (per-eligible-apparatus row with attestation, recognition state, and the `can_attest/can_recognize/can_revoke/can_reverse` flags); `ops.v_completion_recognition_rollup` (per `(project_number, scope_id, project_id)` recognized-$ + counts, joining `ops.projects` for `project_number`).

**Steps**

- [ ] Write failing tests (append to `test_009_recognition_bridge.py`):
  ```python
  def test_worklist_flags_across_states(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          # (1) fresh eligible -> can_attest only
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select can_attest, can_recognize, can_revoke, can_reverse"
                      " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
          assert cur.fetchone()==(True, False, False, False)
          # (2) attested -> can_recognize + can_revoke
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
          cur.execute("select can_attest, can_recognize, can_revoke, can_reverse"
                      " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
          assert cur.fetchone()==(False, True, True, False)
          # (3) recognized -> can_reverse only
          cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
          ev=cur.fetchone()[0]
          cur.execute("select can_attest, can_recognize, can_revoke, can_reverse"
                      " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
          assert cur.fetchone()==(False, False, False, True)
          # (4) reversed -> re-recognize + revoke again
          cur.execute("select ops.reverse_recognition(%s,%s,'corr')",(ev,who))
          cur.execute("select can_attest, can_recognize, can_revoke, can_reverse"
                      " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
          assert cur.fetchone()==(False, True, True, False)
          cur.execute("rollback to savepoint s")

  def test_worklist_carries_project_number_and_basis(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); _seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress", quoted_revenue=1500, quoted_hours=10)
          cur.execute("select project_number, status, quoted_hours, quoted_revenue, net_recognized, is_recognized"
                      " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
          pn, st, qh, qr, net, isr = cur.fetchone()
          assert pn is not None and st=="In Progress" and float(qr)==1500 and isr is False
          cur.execute("rollback to savepoint s")

  def test_worklist_exposes_attestation_and_recognition_columns(conn):
      """The worklist must surface the attestation identity (attested_by/attested_at/
      attest_reason) and the recognition trace (recognized_event_id) correctly:
        - fresh eligible  -> all four NULL
        - after attest    -> attested_by=actor, attested_at set, attest_reason=reason; event still NULL
        - after recognize -> recognized_event_id non-null
        - after reverse   -> recognized_event_id NULL again (v_apparatus_recognition nulls it)."""
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
          # (1) fresh eligible: no active attestation, no recognition.
          cur.execute("select attested_by, attested_at, attest_reason, recognized_event_id"
                      " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
          ab, at_, ar_, rev = cur.fetchone()
          assert ab is None and at_ is None and ar_ is None and rev is None
          # (2) after attest: attestation columns populated; recognition still empty.
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'tested ok')",(aid,who))
          cur.execute("select attested_by, attested_at, attest_reason, recognized_event_id"
                      " from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
          ab, at_, ar_, rev = cur.fetchone()
          assert ab==who and at_ is not None and ar_=="tested ok" and rev is None
          # (3) after recognize: recognized_event_id is non-null.
          cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
          ev=cur.fetchone()[0]
          cur.execute("select recognized_event_id from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
          assert cur.fetchone()[0]==ev, "recognized_event_id not exposed after recognize"
          # (4) after reverse: recognized_event_id goes NULL (per v_apparatus_recognition).
          cur.execute("select ops.reverse_recognition(%s,%s,'corr')",(ev,who))
          cur.execute("select recognized_event_id, attested_by from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
          rev2, ab2 = cur.fetchone()
          assert rev2 is None and ab2==who, "recognized_event_id not cleared on reverse / attestation lost"
          cur.execute("rollback to savepoint s")

  def test_rollup_sums_recognized_and_resolves_project_number(conn):
      with conn.cursor() as cur:
          cur.execute("savepoint s"); who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress", quoted_revenue=1500)
          cur.execute("select project_number from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid,))
          pn=cur.fetchone()[0]
          cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who))
          cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
          cur.execute("select project_number, recognized_total, recognized_count"
                      " from ops.v_completion_recognition_rollup where project_number=%s",(pn,))
          rpn, rtot, rcnt = cur.fetchone()
          assert rpn==pn and float(rtot)==1500 and rcnt==1
          cur.execute("rollback to savepoint s")

  def test_rollup_eligible_count_uses_full_worklist_predicate(conn):
      """eligible_count must use the SAME eligibility predicate as the worklist:
      provenance_status='approved' AND a.is_active AND active non-cancelled scope/project
      chain AND sq.is_frozen. An unfrozen-basis or cancelled-scope apparatus must NOT be
      counted as eligible (and must not appear in the rollup row scope at all)."""
      with conn.cursor() as cur:
          cur.execute("savepoint s"); _seed_person(cur)
          # (1) one fully-eligible apparatus -> eligible_count == 1, and it appears in the worklist.
          aid_ok=_seed_eligible_apparatus(cur, status="In Progress")
          cur.execute("select project_number from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid_ok,))
          pn=cur.fetchone()[0]
          cur.execute("select eligible_count from ops.v_completion_recognition_rollup where project_number=%s",(pn,))
          assert cur.fetchone()[0]==1, "fully-eligible apparatus not counted in eligible_count"
          # (2) an UNFROZEN-basis apparatus is NOT eligible -> excluded from eligible_count.
          aid_unfrozen=_seed_eligible_apparatus(cur, status="In Progress", frozen=False)
          cur.execute("select project_number from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid_unfrozen,))
          assert cur.fetchone() is None, "unfrozen-basis apparatus leaked into the worklist"
          cur.execute("select coalesce(max(eligible_count),0) from ops.v_completion_recognition_rollup"
                      " where scope_id=(select scope_id from ops.apparatus where id=%s)",(aid_unfrozen,))
          assert cur.fetchone()[0]==0, "unfrozen-basis apparatus counted as eligible"
          # (3) a CANCELLED-scope apparatus is NOT eligible -> excluded from eligible_count.
          aid_cancelled=_seed_eligible_apparatus(cur, status="In Progress", scope_status="Cancelled")
          cur.execute("select project_number from ops.v_completion_recognition_worklist where apparatus_id=%s",(aid_cancelled,))
          assert cur.fetchone() is None, "cancelled-scope apparatus leaked into the worklist"
          cur.execute("select coalesce(max(eligible_count),0) from ops.v_completion_recognition_rollup"
                      " where scope_id=(select scope_id from ops.apparatus where id=%s)",(aid_cancelled,))
          assert cur.fetchone()[0]==0, "cancelled-scope apparatus counted as eligible"
          cur.execute("rollback to savepoint s")
  ```

- [ ] Run to verify fail:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q -k "worklist or rollup"
  ```
  Expected: views do not exist -> `UndefinedTable` on `ops.v_completion_recognition_worklist` / `ops.v_completion_recognition_rollup`.

- [ ] Implement — append to `009_recognition_bridge.sql`:
  ```sql
  -- ---- T6: read models — worklist + rollup ----------------------------------
  create view ops.v_completion_recognition_worklist as
  select a.id as apparatus_id, a.apparatus_designation, a.scope_id, s.project_id, p.project_number,
         a.status, a.quoted_hours, a.quoted_revenue,
         att.id as attestation_id, att.attested_by, att.attested_at, att.reason as attest_reason,
         ar.net_recognized, ar.is_recognized, ar.recognized_event_id,
         (a.status not in ('Complete','Cancelled') and att.id is null
           and a.quoted_hours > 0 and a.quoted_revenue > 0)                 as can_attest,
         (a.status = 'Complete' and att.id is not null
           and a.quoted_hours > 0 and a.quoted_revenue > 0
           and not ar.is_recognized)                                        as can_recognize,
         (att.id is not null and not ar.is_recognized)                      as can_revoke,
         ar.is_recognized                                                   as can_reverse
  from ops.apparatus a
  join ops.scopes s   on s.id = a.scope_id
  join ops.projects p on p.id = s.project_id
  join ops.scope_quote sq on sq.scope_id = a.scope_id
  left join ops.completion_attestation att
    on att.apparatus_id = a.id and att.revoked_at is null
  join ops.v_apparatus_recognition ar on ar.apparatus_id = a.id
  where a.provenance_status = 'approved' and a.is_active
    and s.is_active and s.status <> 'Cancelled'
    and p.is_active and p.status <> 'Cancelled'
    and sq.is_frozen;

  -- eligible_count + the row scope use the SAME eligibility predicate as
  -- v_completion_recognition_worklist (provenance_status='approved' AND a.is_active
  -- AND active non-cancelled scope/project chain AND sq.is_frozen). The outer WHERE
  -- restricts the row set to eligible apparatus so recognized_total/recognized_count
  -- and eligible_count all read the identical population the worklist exposes — an
  -- unfrozen-basis or cancelled-scope apparatus is excluded from eligible_count.
  create view ops.v_completion_recognition_rollup as
  select p.project_number, s.id as scope_id, p.id as project_id,
         coalesce(sum(ar.net_recognized), 0)                          as recognized_total,
         count(*) filter (where ar.is_recognized)                      as recognized_count,
         count(*) filter (where a.provenance_status = 'approved'
                            and a.is_active
                            and s.is_active and s.status <> 'Cancelled'
                            and p.is_active and p.status <> 'Cancelled'
                            and sq.is_frozen)                          as eligible_count
  from ops.apparatus a
  join ops.scopes s   on s.id = a.scope_id
  join ops.projects p on p.id = s.project_id
  join ops.scope_quote sq on sq.scope_id = a.scope_id
  join ops.v_apparatus_recognition ar on ar.apparatus_id = a.id
  where a.provenance_status = 'approved' and a.is_active
    and s.is_active and s.status <> 'Cancelled'
    and p.is_active and p.status <> 'Cancelled'
    and sq.is_frozen
  group by p.project_number, s.id, p.id;
  ```

- [ ] Implement — PREPEND the T6 teardown (top of file, above T5) in `009_recognition_bridge_down.sql` — drop BOTH views first (they depend on everything below):
  ```sql
  -- ---- T6: drop the read views (first in down order) ------------------------
  drop view if exists ops.v_completion_recognition_rollup;
  drop view if exists ops.v_completion_recognition_worklist;
  ```

- [ ] Run to verify pass:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q
  ```
  Expected: all T0–T6 tests pass (the down source-diff test still passes — dropping the views first lets the `create or replace` of the 005 fns succeed).

- [ ] Commit:
  ```
  git add infra/database/migrations/ops/009_recognition_bridge.sql infra/database/migrations/ops/009_recognition_bridge_down.sql infra/database/migrations/ops/test_009_recognition_bridge.py
  git commit -m "feat(ops/009): T6 worklist + rollup views (flag-gated, project_number-resolving)"
  ```

---

## Task 7 — Concurrency proofs (real 2-connection psycopg interleaving, test-only)

**Files**
- Modify: `infra/database/migrations/ops/test_009_recognition_bridge.py` (append T7 tests — NO migration changes)

**Interfaces**
- Consumes: the `009` functions + the partial-unique index (already built T0–T6). No new DDL — these tests prove the concurrency invariants of the existing objects.

**Steps**

- [ ] Write failing tests (append to `test_009_recognition_bridge.py`). These use two autocommit-OFF connections with explicit `BEGIN`, each carrying a **bounded `statement_timeout`** so a lock-order regression raises `QueryCanceled` (or `LockNotAvailable`) and the test FAILS deterministically rather than hanging on an unresolved lock wait:
  ```python
  import threading, time

  # Bounded per-statement timeout for every concurrent connection. A real deadlock is
  # auto-detected by PG (DeadlockDetected); a NON-deadlock lock-order regression that would
  # otherwise hang forever instead trips this timeout -> QueryCanceled -> the assertion FAILS.
  # Larger than the 0.5s interleave sleep, far smaller than the 15-20s thread joins.
  _STMT_TIMEOUT_MS = 4000

  def _concurrent_conn():
      """A fresh autocommit-OFF connection with a bounded statement_timeout (set on its own
      txn-less statement before the test BEGIN), so a hung lock-wait fails instead of hanging."""
      c = psycopg.connect(DSN)
      c.autocommit = True
      with c.cursor() as cur:
          cur.execute(f"set session statement_timeout = {_STMT_TIMEOUT_MS}")
      c.autocommit = False
      return c

  def _seed_for_concurrency():
      """Seed one eligible apparatus + a person OUTSIDE a savepoint (committed), return ids."""
      with psycopg.connect(DSN, autocommit=True) as c, c.cursor() as cur:
          who=_seed_person(cur)
          aid=_seed_eligible_apparatus(cur, status="In Progress")
      return aid, who

  def _cleanup(aid):
      with psycopg.connect(DSN, autocommit=True) as c, c.cursor() as cur:
          # tear the committed concurrency fixture rows down via the sanctioned ctx path
          cur.execute("select scope_id from ops.apparatus where id=%s",(aid,))
          row=cur.fetchone()
          if row:
              sid=row[0]
              cur.execute("select project_id from ops.scopes where id=%s",(sid,)); pid=cur.fetchone()[0]
              cur.execute("delete from ops.revenue_recognition_event where apparatus_id=%s",(aid,))
              cur.execute("delete from ops.completion_attestation where apparatus_id=%s",(aid,))
              cur.execute("set local ops.completion_ctx='1'")
              cur.execute("delete from ops.apparatus where id=%s",(aid,))
              cur.execute("delete from ops.scope_quote where scope_id=%s",(sid,))
              cur.execute("delete from ops.scopes where id=%s",(sid,))
              cur.execute("delete from ops.projects where id=%s",(pid,))

  def test_concurrent_attest_partial_unique_race():
      """Two concurrent attests on one apparatus -> exactly one commits, the other unique-violates."""
      aid, who = _seed_for_concurrency()
      try:
          c1=_concurrent_conn(); c2=_concurrent_conn()   # bounded statement_timeout each
          results={}
          def run(tag, conn, barrier):
              try:
                  with conn.cursor() as cur:
                      cur.execute("begin")
                      barrier.wait(timeout=10)
                      cur.execute("select ops.attest_apparatus_complete(%s,%s,%s)",(aid,who,f"r-{tag}"))
                      cur.execute("commit"); results[tag]="ok"
              except psycopg.errors.UniqueViolation:
                  conn.rollback(); results[tag]="unique"
              except psycopg.Error as e:
                  conn.rollback(); results[tag]=type(e).__name__
          b=threading.Barrier(2)
          t1=threading.Thread(target=run,args=("A",c1,b)); t2=threading.Thread(target=run,args=("B",c2,b))
          t1.start(); t2.start(); t1.join(15); t2.join(15)
          c1.close(); c2.close()
          assert sorted(results.values())==["ok","unique"], f"expected one ok + one unique, got {results}"
      finally:
          _cleanup(aid)

  def test_concurrent_revoke_and_recognize_no_deadlock():
      """Interleave revoke + approve_and_recognize on the same apparatus -> NO deadlock; both
      serialize on the apparatus FOR UPDATE (one waits, neither raises a DeadlockDetected)."""
      aid, who = _seed_for_concurrency()
      try:
          # pre-state: attested but NOT recognized (so revoke is allowed, recognize is allowed)
          with psycopg.connect(DSN, autocommit=True) as c, c.cursor() as cur:
              cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
          c1=_concurrent_conn(); c2=_concurrent_conn()   # bounded statement_timeout each
          errs={}
          def do_recognize():
              try:
                  with c1.cursor() as cur:
                      cur.execute("begin")
                      cur.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",(aid,who))
                      time.sleep(0.5); cur.execute("commit")
                  errs["recognize"]=None
              except psycopg.Error as e:
                  c1.rollback(); errs["recognize"]=type(e).__name__
          def do_revoke():
              try:
                  time.sleep(0.1)
                  with c2.cursor() as cur:
                      cur.execute("begin")
                      cur.execute("select ops.revoke_completion_attestation(%s,%s,'x')",(att,who))
                      cur.execute("commit")
                  errs["revoke"]=None
              except psycopg.Error as e:
                  c2.rollback(); errs["revoke"]=type(e).__name__
          t1=threading.Thread(target=do_recognize); t2=threading.Thread(target=do_revoke)
          t1.start(); t2.start(); t1.join(20); t2.join(20)
          c1.close(); c2.close()
          # the KEY assertion: neither side hit a deadlock NOR a hung lock-wait. One business
          # outcome may fail (revoke blocked by the now-open recognition) but NOT via
          # DeadlockDetected and NOT via QueryCanceled/LockNotAvailable (a lock-order regression
          # that would otherwise hang trips the bounded statement_timeout -> QueryCanceled here).
          _bad = {"DeadlockDetected", "QueryCanceled", "LockNotAvailable"}
          assert errs.get("recognize") not in _bad and errs.get("revoke") not in _bad, \
              f"deadlock or hung lock-wait under the apparatus-first order: {errs}"
      finally:
          _cleanup(aid)

  def test_concurrent_double_revoke_one_loser():
      """Two concurrent revokes of the same active attestation -> exactly one wins; the loser
      sees revoked_at IS NULL fail at the FOR UPDATE re-select (clean error, not a wrong success)."""
      aid, who = _seed_for_concurrency()
      try:
          with psycopg.connect(DSN, autocommit=True) as c, c.cursor() as cur:
              cur.execute("select ops.attest_apparatus_complete(%s,%s,'done')",(aid,who)); att=cur.fetchone()[0]
          c1=_concurrent_conn(); c2=_concurrent_conn()   # bounded statement_timeout each
          results={}
          def run(tag, conn, barrier):
              try:
                  with conn.cursor() as cur:
                      cur.execute("begin")
                      barrier.wait(timeout=10)
                      cur.execute("select ops.revoke_completion_attestation(%s,%s,%s)",(att,who,f"r-{tag}"))
                      cur.execute("commit"); results[tag]="ok"
              except psycopg.Error as e:
                  conn.rollback(); results[tag]="err:"+type(e).__name__
          b=threading.Barrier(2)
          t1=threading.Thread(target=run,args=("A",c1,b)); t2=threading.Thread(target=run,args=("B",c2,b))
          t1.start(); t2.start(); t1.join(15); t2.join(15)
          c1.close(); c2.close()
          oks=[v for v in results.values() if v=="ok"]
          assert len(oks)==1, f"expected exactly one winning revoke, got {results}"
      finally:
          _cleanup(aid)
  ```

- [ ] Run to verify fail FIRST against a deliberately-broken hypothesis (sanity): run only T7 and confirm they PASS against the correctly-built `009` (the proof tests assert the invariant holds). If a proof fails, the migration is wrong — fix `009`, not the test:
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q -k concurrent
  ```
  Expected (TDD note): T7 are *property* proofs of T0–T6 objects. To honor red-green, first run them against an intentionally attestation-first revoke (swap steps 2–3 in a scratch copy of `revoke_completion_attestation`) and observe `test_concurrent_revoke_and_recognize_no_deadlock` FAIL — either with `DeadlockDetected` (PG auto-detects the cycle) OR, if the regression manifests as a non-detected lock-wait, with `QueryCanceled` once the bounded `statement_timeout` (`_STMT_TIMEOUT_MS`, 4s) trips. Either way the test fails deterministically (never hangs). Then restore the apparatus-first body and observe it PASS. Document this red-green in the commit body.

- [ ] Run to verify pass (against the shipped apparatus-first `009`):
  ```
  uv run --with "psycopg[binary]" --with pytest pytest infra/database/migrations/ops/test_009_recognition_bridge.py -q
  ```
  Expected: all T0–T7 tests pass.

- [ ] Commit:
  ```
  git add infra/database/migrations/ops/test_009_recognition_bridge.py
  git commit -m "test(ops/009): T7 concurrency proofs — partial-unique race, revoke/recognize no-deadlock, double-revoke loser"
  ```

---

## Task 8 — Package wrappers `recognition.py` + migrate the envelope test (spec 6)

**Files**
- Create: `packages/ops-intake/src/ops_intake/recognition.py`
- Create: `packages/ops-intake/tests/test_recognition_wrappers.py`
- Modify: `packages/ops-intake/tests/test_approve_envelope.py` (line ~72: reach `'Complete'` via the attest fn)

**Interfaces**
- Produces: `attest_complete(dsn, apparatus_id, attested_by, reason) -> str`; `recognize(dsn, apparatus_id, actor, datasheet_clearance, datasheet_ref, cx_clearance, cx_ref) -> str`; `reverse(dsn, event_id, actor, reason) -> str`; `revoke(dsn, attestation_id, actor, reason) -> str`. Typed VALUE-FREE errors: `RecognitionInputError` (bad input / unknown actor / blank reason / out-of-enum), `RecognitionConflict` (active attestation exists / already recognized / open recognition), `RecognitionStateError` (ineligible / not-found state).
- Consumes: the `009` functions via `psycopg`. Maps `UniqueViolation -> RecognitionConflict`; `ForeignKeyViolation -> RecognitionInputError`; `RaiseException` whose `SQLSTATE='P0001'` -> classified by a SMALL allowlist of stable substrings to Conflict vs State vs Input, with a value-free fallback message (NEVER `str(exc)`).

**Steps**

- [ ] Write failing tests (`packages/ops-intake/tests/test_recognition_wrappers.py`):
  ```python
  import uuid
  import psycopg, pytest
  from ops_intake import recognition as rec

  def _person(dsn):
      with psycopg.connect(dsn, autocommit=True) as c:
          return str(c.execute("insert into ops.persons (display_name) values ('PM') returning person_id").fetchone()[0])

  def _eligible(dsn, status="In Progress"):
      with psycopg.connect(dsn, autocommit=True) as c, c.cursor() as cur:
          cur.execute("insert into ops.projects (project_number,project_name,status,provenance_status)"
                      " values (%s,'P','Active','approved') returning id",(f"P-{uuid.uuid4().hex[:8]}",))
          pid=cur.fetchone()[0]
          cur.execute("insert into ops.scopes (project_id,scope_name,status,provenance_status,source)"
                      " values (%s,'S','In Progress','approved','ops-intake') returning id",(pid,))
          sid=cur.fetchone()[0]
          cur.execute("insert into ops.scope_quote (scope_id,onsite_labor,unit_multiplier,pct_adjust,"
                      "total_quoted_hours,is_frozen,frozen_at) values (%s,1500,1,1,10,true,now())",(sid,))
          cur.execute("insert into ops.apparatus (scope_id,apparatus_designation,status,provenance_status,"
                      "quoted_hours,quoted_revenue,source) values (%s,'A',%s,'approved',10,1500,'ops-intake') returning id",
                      (sid,status))
          return str(cur.fetchone()[0])

  def test_attest_then_recognize_then_reverse_then_revoke(clean_ops):
      dsn=clean_ops; who=_person(dsn); aid=_eligible(dsn)
      att=rec.attest_complete(dsn, aid, who, "tested ok"); assert isinstance(att,str)
      ev=rec.recognize(dsn, aid, who, "not_applicable", None, "not_applicable", None); assert isinstance(ev,str)
      rv=rec.reverse(dsn, ev, who, "correction"); assert isinstance(rv,str)
      out=rec.revoke(dsn, att, who, "superseded"); assert out==att

  def test_second_active_attest_raises_conflict_value_free(clean_ops):
      dsn=clean_ops; who=_person(dsn); aid=_eligible(dsn)
      rec.attest_complete(dsn, aid, who, "x")
      with pytest.raises(rec.RecognitionConflict) as ei:
          rec.attest_complete(dsn, aid, who, "y")
      assert "$" not in str(ei.value) and "1500" not in str(ei.value)

  def test_unknown_actor_raises_input_error_value_free(clean_ops):
      dsn=clean_ops; aid=_eligible(dsn)
      with pytest.raises(rec.RecognitionInputError) as ei:
          rec.attest_complete(dsn, aid, str(uuid.uuid4()), "x")
      assert "$" not in str(ei.value)

  def test_blank_reason_raises_input_error(clean_ops):
      dsn=clean_ops; who=_person(dsn); aid=_eligible(dsn)
      with pytest.raises(rec.RecognitionInputError):
          rec.attest_complete(dsn, aid, who, "   ")

  def test_revoke_open_recognition_raises_conflict(clean_ops):
      dsn=clean_ops; who=_person(dsn); aid=_eligible(dsn)
      att=rec.attest_complete(dsn, aid, who, "x")
      rec.recognize(dsn, aid, who, "not_applicable", None, "not_applicable", None)
      with pytest.raises(rec.RecognitionConflict):
          rec.revoke(dsn, att, who, "nope")

  def test_recognize_without_attestation_raises_state_error(clean_ops):
      dsn=clean_ops; who=_person(dsn); aid=_eligible(dsn)
      # flip to Complete via the sanctioned ctx path but skip attest -> recognize must reject
      with psycopg.connect(dsn, autocommit=True) as c, c.cursor() as cur:
          cur.execute("set local ops.completion_ctx='1'")
          cur.execute("update ops.apparatus set status='Complete' where id=%s",(aid,))
      with pytest.raises(rec.RecognitionStateError):
          rec.recognize(dsn, aid, who, "not_applicable", None, "not_applicable", None)

  def test_intake_apparatus_insert_still_succeeds_under_completion_guard(clean_ops):
      """REGRESSION (Chip-5 intake must not break under the T2 apparatus_completion_guard):
      the merged ops-intake approve_run materialization inserts apparatus at status='Not Started'
      (insert_apparatus in load.py) and approve.py later stamps provenance_status='approved'.
      Neither the 'Not Started' insert NOR the post-approve 'approved' state is governed-complete
      (g := status='Complete' AND provenance_status='approved'), so the T2 guard MUST NOT fire and
      the apparatus row MUST exist. This pins that 009 does not regress intake. We drive a direct
      INSERT mirroring approve.py's post-approval apparatus state (provenance_status='approved',
      status='Not Started') after 009 is applied, with NO completion ctx set."""
      dsn=clean_ops
      with psycopg.connect(dsn, autocommit=True) as c, c.cursor() as cur:
          cur.execute("insert into ops.projects (project_number,project_name,status,provenance_status)"
                      " values (%s,'P','Active','approved') returning id",(f"P-{uuid.uuid4().hex[:8]}",))
          pid=cur.fetchone()[0]
          cur.execute("insert into ops.scopes (project_id,scope_name,status,provenance_status,source)"
                      " values (%s,'S','In Progress','approved','ops-intake') returning id",(pid,))
          sid=cur.fetchone()[0]
          # mirrors approve.py's post-approval apparatus row: approved + NOT governed-complete.
          # NO ops.completion_ctx is set -> the guard must allow this because it is not entering g.
          cur.execute("insert into ops.apparatus (scope_id,apparatus_designation,status,provenance_status,"
                      "quoted_hours,quoted_revenue,source) values (%s,'A-1','Not Started','approved',10,1500,'ops-intake')"
                      " returning id",(sid,))
          aid=cur.fetchone()[0]
          cur.execute("select status, provenance_status from ops.apparatus where id=%s",(aid,))
          assert cur.fetchone()==("Not Started","approved"), "intake-style approved/Not-Started insert was blocked by the guard"
  ```

- [ ] Run to verify fail:
  ```
  export PATH=$HOME/.local/bin:$PATH; set -a; . infra/.env; set +a
  export OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"
  cd packages/ops-intake
  uv run --with "psycopg[binary]" --with pytest pytest tests/test_recognition_wrappers.py -q
  ```
  Expected: `ModuleNotFoundError: ops_intake.recognition` (the module does not exist).
  NOTE: the package `conftest.py` migration fixture chains 001..008 only — for these tests it must also apply 009. Add `"009_recognition_bridge.sql"` to the `up_migrations` list in `packages/ops-intake/tests/conftest.py` and add the 009-down to the pre/post reset (prepend `009_recognition_bridge_down.sql` before the 008 down in both the pre-up reset and teardown). Do this as the first edit of this task.

- [ ] Implement `packages/ops-intake/src/ops_intake/recognition.py`:
  ```python
  from __future__ import annotations
  """Thin, value-free wrappers over the ops 009 recognition-bridge functions.

  Sole-writer discipline: these call ops.attest_apparatus_complete / approve_and_recognize /
  reverse_recognition / revoke_completion_attestation and translate DB exceptions into a small
  set of typed, VALUE-FREE errors (no dollar amounts, no internal text). The API maps these to
  generic 400/409; the raw DB message is NEVER surfaced.
  """
  import psycopg

  class RecognitionError(Exception):
      """Base — message is always a fixed, value-free string."""

  class RecognitionInputError(RecognitionError):
      """Bad/zero input: unknown actor, blank reason, out-of-enum clearance. -> API 400."""

  class RecognitionConflict(RecognitionError):
      """State conflict: active attestation already exists / already recognized / open recognition. -> API 409."""

  class RecognitionStateError(RecognitionError):
      """Ineligible or wrong-state target (not approved, cancelled chain, no active attestation). -> API 409."""

  # Stable, value-free substrings emitted by the 009 functions (P0001). Matched on the DB
  # message ONLY to CLASSIFY; the surfaced message is always one of the fixed strings below.
  _CONFLICT_HINTS = ("already recognized", "open recognition", "no longer active",
                     "already revoked", "already has an open recognition")
  _STATE_HINTS    = ("not approved", "inactive/cancelled", "cannot attest", "cannot recognize",
                     "no active completion attestation", "not found", "not testing-complete",
                     "cannot attest from status", "basis not frozen", "invalid quote basis")
  _INPUT_HINTS    = ("reason required", "unknown actor", "clearances required")

  def _classify(exc: psycopg.Error) -> RecognitionError:
      if isinstance(exc, psycopg.errors.UniqueViolation):
          return RecognitionConflict("a conflicting recognition state already exists")
      if isinstance(exc, psycopg.errors.ForeignKeyViolation):
          return RecognitionInputError("invalid input reference")
      msg = (getattr(getattr(exc, "diag", None), "message_primary", None) or str(exc)).lower()
      if any(h in msg for h in _INPUT_HINTS):
          return RecognitionInputError("invalid input")
      if any(h in msg for h in _CONFLICT_HINTS):
          return RecognitionConflict("recognition state conflict")
      if any(h in msg for h in _STATE_HINTS):
          return RecognitionStateError("apparatus not in a valid state for this action")
      # value-free fallback — NEVER str(exc)
      return RecognitionStateError("recognition action rejected")

  def _call_scalar(dsn: str, sql: str, params: tuple) -> str:
      try:
          with psycopg.connect(dsn, autocommit=True) as c, c.cursor() as cur:
              cur.execute(sql, params)
              return str(cur.fetchone()[0])
      except psycopg.Error as exc:
          raise _classify(exc) from None

  def attest_complete(dsn: str, apparatus_id: str, attested_by: str, reason: str) -> str:
      return _call_scalar(dsn, "select ops.attest_apparatus_complete(%s,%s,%s)",
                          (apparatus_id, attested_by, reason))

  def recognize(dsn: str, apparatus_id: str, actor: str,
                datasheet_clearance: str, datasheet_ref, cx_clearance: str, cx_ref) -> str:
      return _call_scalar(
          dsn,
          "select ops.approve_and_recognize(%s,%s,%s::ops.obligation_clearance,%s,"
          "%s::ops.obligation_clearance,%s)",
          (apparatus_id, actor, datasheet_clearance, datasheet_ref, cx_clearance, cx_ref))

  def reverse(dsn: str, event_id: str, actor: str, reason: str) -> str:
      return _call_scalar(dsn, "select ops.reverse_recognition(%s,%s,%s)", (event_id, actor, reason))

  def revoke(dsn: str, attestation_id: str, actor: str, reason: str) -> str:
      return _call_scalar(dsn, "select ops.revoke_completion_attestation(%s,%s,%s)",
                          (attestation_id, actor, reason))
  ```

- [ ] Implement the cross-task envelope-test migration (spec M3) — `test_approve_envelope.py` line ~72 currently does `c.execute("update ops.apparatus set status='Complete' where id=%s", (aid,))` inside `test_recognized_then_reversed_still_blocks`; the T2 guard now rejects that direct set. Replace it so the apparatus reaches `'Complete'` via the sanctioned attest fn (the apparatus from `approve_run` is `provenance_status='approved'`, so it is attest-eligible). Change:
  ```python
          aid = c.execute("select id from ops.apparatus limit 1").fetchone()[0]
          c.execute("update ops.apparatus set status='Complete' where id=%s", (aid,))
          ev = c.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
                         (aid, who)).fetchone()[0]
  ```
  to (EXPLICIT setup so the attest call cannot raise on a hidden ineligibility — pin every
  gate `ops.attest_apparatus_complete` enforces: approved provenance, frozen scope_quote,
  positive quoted_hours/quoted_revenue, status NOT IN (Complete,Cancelled), known actor):
  ```python
          # pick an apparatus that provably satisfies EVERY attest-eligibility gate, so the
          # sanctioned attest fn (T2 guard path) cannot fail on a hidden ineligibility.
          aid = c.execute(
              "select a.id from ops.apparatus a"
              " join ops.scopes s   on s.id = a.scope_id"
              " join ops.projects p on p.id = s.project_id"
              " join ops.scope_quote sq on sq.scope_id = a.scope_id"
              " where a.provenance_status='approved' and a.is_active"
              "   and a.status not in ('Complete','Cancelled')"
              "   and a.quoted_hours > 0 and a.quoted_revenue > 0"
              "   and s.is_active and s.status <> 'Cancelled'"
              "   and p.is_active and p.status <> 'Cancelled'"
              "   and sq.is_frozen and sq.frozen_at is not null"
              " limit 1"
          ).fetchone()[0]
          # assert the eligibility preconditions explicitly (fail loudly here, not inside attest).
          prov, st, qh, qr, frozen = c.execute(
              "select a.provenance_status, a.status, a.quoted_hours, a.quoted_revenue, sq.is_frozen"
              " from ops.apparatus a join ops.scope_quote sq on sq.scope_id=a.scope_id"
              " where a.id=%s", (aid,)).fetchone()
          assert prov == 'approved' and st not in ('Complete','Cancelled') and qh > 0 and qr > 0 and frozen
          # `who` is the approve_run actor; ensure it is a known ops.persons row (attest gate 1).
          assert c.execute("select 1 from ops.persons where person_id=%s", (who,)).fetchone() is not None
          c.execute("select ops.attest_apparatus_complete(%s,%s,'tested')", (aid, who))  # sanctioned status=Complete (T2 guard)
          ev = c.execute("select ops.approve_and_recognize(%s,%s,'not_applicable',null,'not_applicable',null)",
                         (aid, who)).fetchone()[0]
  ```

- [ ] Run to verify pass (wrappers + the migrated envelope test + the rest of the package suite unaffected):
  ```
  cd packages/ops-intake
  uv run --with "psycopg[binary]" --with pytest pytest tests/test_recognition_wrappers.py tests/test_approve_envelope.py -q
  ```
  Expected: all wrapper tests pass; `test_recognized_then_reversed_still_blocks` still passes (now via attest); no regressions in `test_approve_envelope.py`.

- [ ] Commit:
  ```
  git add packages/ops-intake/src/ops_intake/recognition.py packages/ops-intake/tests/test_recognition_wrappers.py packages/ops-intake/tests/test_approve_envelope.py packages/ops-intake/tests/conftest.py
  git commit -m "feat(ops-intake): recognition wrappers (value-free typed errors) + 009 in test chain + envelope test via attest fn"
  ```

---

## Task 9 — API: host-gated `recognition_router.py` (spec 7)

**Files**
- Create: `apps/control-plane-api/services/ops/recognition_router.py`
- Modify: `apps/control-plane-api/main.py` (register the router under the existing `_ops_intake_enabled()` host gate)
- Create: `apps/control-plane-api/tests/test_ops_recognition_routes.py`

**Interfaces**
- Produces: `APIRouter(prefix="/api/v1/ops/recognition")` with 6 routes (spec 7): `POST /completion/attest`, `POST /completion/{attestation_id}/revoke`, `POST /events/recognize`, `POST /events/{event_id}/reverse`, `GET /worklist`, `GET /rollup`. Host-gated on `OPS_DEV_DSN` like `intake_router`; actor-gated via the package wrappers (unknown actor -> value-free 400); `obligation_clearance` validated against `{'provided','not_applicable'}` -> value-free 400 on out-of-enum.
- Consumes: `ops_intake.recognition` (T8 wrappers); `ops.v_completion_recognition_worklist` / `ops.v_completion_recognition_rollup` via `psycopg`.
- Error mapping: `RecognitionInputError -> 400`; `RecognitionConflict -> 409`; `RecognitionStateError -> 409`. Detail strings are the wrappers' fixed value-free messages.

**Steps**

- [ ] Write failing tests (`apps/control-plane-api/tests/test_ops_recognition_routes.py`) — mirror `test_ops_intake_routes.py` migration setup but chain through `009`; add the host-gating disabled-subprocess test:
  ```python
  from __future__ import annotations
  import os, pathlib, subprocess, sys, uuid
  import psycopg, pytest

  _MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parents[3] / "infra/database/migrations/ops"

  def _require_ops_test(dsn):
      from psycopg.conninfo import conninfo_to_dict
      assert conninfo_to_dict(dsn).get("dbname") == "ops_test", "must target ops_test"

  def _dsn(): return os.environ["OPS_DEV_DSN"]

  _CHAIN = ["001_identity_skeleton.sql","002_quote_model.sql","003_intake_unique_keys.sql",
            "004_person_anchor.sql","005_recognition_ledger.sql","006_progress_billing.sql",
            "007_intake_envelope.sql","008_core_equipment_models.sql","009_recognition_bridge.sql"]

  @pytest.fixture(scope="session", autouse=True)
  def apply_migrations():
      d=_dsn(); _require_ops_test(d)
      def run(c,p): c.execute(pathlib.Path(p).read_text(encoding="utf-8"))
      with psycopg.connect(d, autocommit=True) as c:
          c.execute("drop schema if exists core cascade")
          run(c, _MIGRATIONS_DIR/"001_identity_skeleton_down.sql")
      with psycopg.connect(d, autocommit=True) as c:
          for n in _CHAIN: run(c, _MIGRATIONS_DIR/n)
      yield
      with psycopg.connect(d, autocommit=True) as c:
          c.execute("drop schema if exists core cascade")
          run(c, _MIGRATIONS_DIR/"001_identity_skeleton_down.sql")

  @pytest.fixture
  def person_id():
      with psycopg.connect(_dsn(), autocommit=True) as c:
          return str(c.execute("insert into ops.persons (display_name) values ('PM') returning person_id").fetchone()[0])

  @pytest.fixture
  def eligible(person_id):
      with psycopg.connect(_dsn(), autocommit=True) as c, c.cursor() as cur:
          cur.execute("insert into ops.projects (project_number,project_name,status,provenance_status)"
                      " values (%s,'P','Active','approved') returning id, project_number",(f"P-{uuid.uuid4().hex[:8]}",))
          pid, pnum=cur.fetchone()
          cur.execute("insert into ops.scopes (project_id,scope_name,status,provenance_status,source)"
                      " values (%s,'S','In Progress','approved','ops-intake') returning id",(pid,))
          sid=cur.fetchone()[0]
          cur.execute("insert into ops.scope_quote (scope_id,onsite_labor,unit_multiplier,pct_adjust,"
                      "total_quoted_hours,is_frozen,frozen_at) values (%s,1500,1,1,10,true,now())",(sid,))
          cur.execute("insert into ops.apparatus (scope_id,apparatus_designation,status,provenance_status,"
                      "quoted_hours,quoted_revenue,source) values (%s,'A','In Progress','approved',10,1500,'ops-intake') returning id",(sid,))
          aid=str(cur.fetchone()[0])
      return {"apparatus_id": aid, "project_number": pnum}

  @pytest.fixture(scope="session")
  def client(apply_migrations):
      from fastapi.testclient import TestClient
      from main import app
      return TestClient(app)

  def _contains(obj, sub):
      if isinstance(obj,str): return sub in obj
      if isinstance(obj,dict): return any(_contains(v,sub) for v in obj.values())
      if isinstance(obj,(list,tuple)): return any(_contains(v,sub) for v in obj)
      return False

  def test_recognition_router_host_gated_subprocess():
      """With OPS_DEV_DSN unset, the recognition routes are NOT mounted (404), mirroring the
      intake host-gating. Run a fresh interpreter with the env var removed."""
      env={k:v for k,v in os.environ.items() if k!="OPS_DEV_DSN"}
      code=("import os; os.environ.pop('OPS_DEV_DSN',None);"
            "from fastapi.testclient import TestClient; from main import app;"
            "c=TestClient(app);"
            "import sys; sys.exit(0 if c.post('/api/v1/ops/recognition/completion/attest',json={}).status_code==404 else 1)")
      r=subprocess.run([sys.executable,"-c",code], cwd=str(pathlib.Path(__file__).resolve().parents[1]), env=env)
      assert r.returncode==0, "recognition routes must be absent when OPS_DEV_DSN is unset"

  def test_attest_recognize_reverse_revoke_happy_path(client, eligible, person_id):
      aid=eligible["apparatus_id"]
      r=client.post("/api/v1/ops/recognition/completion/attest",
                    json={"apparatus_id":aid,"attested_by":person_id,"reason":"tested ok"})
      assert r.status_code==200, r.text; att=r.json()["attestation_id"]
      r=client.post("/api/v1/ops/recognition/events/recognize",
                    json={"apparatus_id":aid,"recognized_by":person_id,
                          "datasheet_clearance":"not_applicable","datasheet_ref":None,
                          "cx_clearance":"not_applicable","cx_ref":None})
      assert r.status_code==200, r.text; ev=r.json()["event_id"]
      r=client.post(f"/api/v1/ops/recognition/events/{ev}/reverse",
                    json={"reversed_by":person_id,"reason":"correction"})
      assert r.status_code==200, r.text
      r=client.post(f"/api/v1/ops/recognition/completion/{att}/revoke",
                    json={"revoked_by":person_id,"reason":"superseded"})
      assert r.status_code==200, r.text

  def test_attest_unknown_actor_returns_400(client, eligible):
      r=client.post("/api/v1/ops/recognition/completion/attest",
                    json={"apparatus_id":eligible["apparatus_id"],"attested_by":str(uuid.uuid4()),"reason":"x"})
      assert r.status_code==400, r.text

  def test_recognize_out_of_enum_clearance_returns_400_value_free(client, eligible, person_id):
      aid=eligible["apparatus_id"]
      client.post("/api/v1/ops/recognition/completion/attest",
                  json={"apparatus_id":aid,"attested_by":person_id,"reason":"x"})
      r=client.post("/api/v1/ops/recognition/events/recognize",
                    json={"apparatus_id":aid,"recognized_by":person_id,
                          "datasheet_clearance":"bogus_value","datasheet_ref":None,
                          "cx_clearance":"not_applicable","cx_ref":None})
      assert r.status_code==400, r.text
      assert not _contains(r.json(),"bogus_value") and not _contains(r.json(),"$")

  def test_second_active_attest_returns_409(client, eligible, person_id):
      aid=eligible["apparatus_id"]
      client.post("/api/v1/ops/recognition/completion/attest",
                  json={"apparatus_id":aid,"attested_by":person_id,"reason":"x"})
      r=client.post("/api/v1/ops/recognition/completion/attest",
                    json={"apparatus_id":aid,"attested_by":person_id,"reason":"y"})
      assert r.status_code==409, r.text

  def test_worklist_and_rollup_read(client, eligible, person_id):
      aid=eligible["apparatus_id"]; pnum=eligible["project_number"]
      client.post("/api/v1/ops/recognition/completion/attest",
                  json={"apparatus_id":aid,"attested_by":person_id,"reason":"x"})
      client.post("/api/v1/ops/recognition/events/recognize",
                  json={"apparatus_id":aid,"recognized_by":person_id,
                        "datasheet_clearance":"not_applicable","datasheet_ref":None,
                        "cx_clearance":"not_applicable","cx_ref":None})
      w=client.get(f"/api/v1/ops/recognition/worklist?project_number={pnum}")
      assert w.status_code==200 and any(row["apparatus_id"]==aid for row in w.json())
      ro=client.get(f"/api/v1/ops/recognition/rollup?project_number={pnum}")
      assert ro.status_code==200 and any(float(r["recognized_total"])>0 for r in ro.json())
  ```

- [ ] Run to verify fail:
  ```
  cd apps/control-plane-api
  python -m pip install -r requirements.txt -r requirements-dev.txt
  export OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"
  python -m pytest tests/test_ops_recognition_routes.py -q
  ```
  Expected: all route tests 404/error (router not registered; module does not exist); `test_recognition_router_host_gated_subprocess` already passes.

- [ ] Implement `apps/control-plane-api/services/ops/recognition_router.py`:
  ```python
  """Ops Recognition Router — host-gated ops_dev bridge (Slice 1).

  6 routes under /api/v1/ops/recognition, distinct from the prod derive-on-read
  /api/v1/ops/revenue-recognition. Mounted only when OPS_DEV_DSN is set (main.py
  _ops_intake_enabled). All mutations flow through the ops_intake.recognition
  wrappers (sole-writer); errors are VALUE-FREE generic 400/409.
  """
  from __future__ import annotations
  import os
  from typing import Any

  import psycopg
  from fastapi import APIRouter, HTTPException, Request, status
  from fastapi.responses import JSONResponse

  from ops_intake import recognition as rec

  router = APIRouter(prefix="/api/v1/ops/recognition", tags=["ops-recognition"])

  _CLEARANCE_ENUM = {"provided", "not_applicable"}

  def _dsn() -> str:
      return os.environ["OPS_DEV_DSN"]

  def _map(exc: rec.RecognitionError) -> HTTPException:
      if isinstance(exc, rec.RecognitionInputError):
          return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
      # RecognitionConflict + RecognitionStateError -> 409
      return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

  def _require(body: dict, *keys: str) -> None:
      for k in keys:
          if body.get(k) in (None, ""):
              raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{k} is required")

  @router.post("/completion/attest", status_code=status.HTTP_200_OK)
  async def attest(request: Request) -> JSONResponse:
      body: dict[str, Any] = await request.json()
      _require(body, "apparatus_id", "attested_by", "reason")
      try:
          att = rec.attest_complete(_dsn(), body["apparatus_id"], body["attested_by"], body["reason"])
      except rec.RecognitionError as e:
          raise _map(e)
      return JSONResponse({"attestation_id": att})

  @router.post("/completion/{attestation_id}/revoke", status_code=status.HTTP_200_OK)
  async def revoke(attestation_id: str, request: Request) -> JSONResponse:
      body: dict[str, Any] = await request.json()
      _require(body, "revoked_by", "reason")
      try:
          out = rec.revoke(_dsn(), attestation_id, body["revoked_by"], body["reason"])
      except rec.RecognitionError as e:
          raise _map(e)
      return JSONResponse({"attestation_id": out})

  @router.post("/events/recognize", status_code=status.HTTP_200_OK)
  async def recognize(request: Request) -> JSONResponse:
      body: dict[str, Any] = await request.json()
      _require(body, "apparatus_id", "recognized_by", "datasheet_clearance", "cx_clearance")
      # value-free enum validation at the boundary (never a raw PG cast error)
      for k in ("datasheet_clearance", "cx_clearance"):
          if body[k] not in _CLEARANCE_ENUM:
              raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                  detail="clearance must be one of: provided, not_applicable")
      try:
          ev = rec.recognize(_dsn(), body["apparatus_id"], body["recognized_by"],
                             body["datasheet_clearance"], body.get("datasheet_ref"),
                             body["cx_clearance"], body.get("cx_ref"))
      except rec.RecognitionError as e:
          raise _map(e)
      return JSONResponse({"event_id": ev})

  @router.post("/events/{event_id}/reverse", status_code=status.HTTP_200_OK)
  async def reverse(event_id: str, request: Request) -> JSONResponse:
      body: dict[str, Any] = await request.json()
      _require(body, "reversed_by", "reason")
      try:
          rv = rec.reverse(_dsn(), event_id, body["reversed_by"], body["reason"])
      except rec.RecognitionError as e:
          raise _map(e)
      return JSONResponse({"reversal_id": rv})

  def _read_view(view: str, project_number: str | None) -> list[dict]:
      sql = f"select * from ops.{view}"
      params: tuple = ()
      if project_number:
          sql += " where project_number = %s"
          params = (project_number,)
      with psycopg.connect(_dsn()) as c, c.cursor() as cur:
          cur.execute(sql, params)
          cols = [d.name for d in cur.description]
          return [dict(zip(cols, [str(v) if hasattr(v, "isoformat") or isinstance(v, (bytes,)) else v for v in row]))
                  for row in cur.fetchall()]

  @router.get("/worklist", status_code=status.HTTP_200_OK)
  def worklist(project_number: str | None = None) -> JSONResponse:
      return JSONResponse(_read_view("v_completion_recognition_worklist", project_number))

  @router.get("/rollup", status_code=status.HTTP_200_OK)
  def rollup(project_number: str | None = None) -> JSONResponse:
      return JSONResponse(_read_view("v_completion_recognition_rollup", project_number))
  ```
  (UUID/numeric values from the views are JSON-serialized; cast `uuid`/`timestamptz` to `str` as above so `JSONResponse` does not choke. `recognized_total` is a numeric -> returned as a number/str the UI parses with `Number()`.)

- [ ] Implement the registration in `main.py` — extend the existing host gate block so the recognition router mounts alongside intake:
  ```python
  if _ops_intake_enabled():
      from services.ops.intake_router import router as ops_intake_router  # import-gated
      app.include_router(ops_intake_router)
      from services.ops.recognition_router import router as ops_recognition_router  # import-gated
      app.include_router(ops_recognition_router)
  ```

- [ ] Run to verify pass:
  ```
  cd apps/control-plane-api
  python -m pytest tests/test_ops_recognition_routes.py -q
  ```
  Expected: all recognition route tests pass.

- [ ] Commit:
  ```
  git add apps/control-plane-api/services/ops/recognition_router.py apps/control-plane-api/main.py apps/control-plane-api/tests/test_ops_recognition_routes.py
  git commit -m "feat(api): host-gated /api/v1/ops/recognition router (6 routes, value-free errors, clearance-enum 400)"
  ```

---

## Task 10 — UI: `/pm-review/recognition` page + lib client + final prod-gate item (spec 8)

**Files**
- Create: `apps/operations-web/lib/recognition.ts`
- Create: `apps/operations-web/app/pm-review/recognition/page.tsx`
- Create: `apps/operations-web/tests/recognition.unit.spec.ts`
- Create: `apps/operations-web/tests/browser-shell.pm-recognition.smoke.spec.ts`

**Interfaces**
- Produces (`lib/recognition.ts`): types `WorklistRow`, `RollupRow`; client fns `fetchWorklist(projectNumber?)`, `fetchRollup(projectNumber?)`, `attestComplete(apparatusId, attestedBy, reason)`, `recognize(apparatusId, recognizedBy, datasheetClearance, datasheetRef, cxClearance, cxRef)`, `reverseEvent(eventId, reversedBy, reason)`, `revokeAttestation(attestationId, revokedBy, reason)`; pure helper `actionFlags(row)` returning `{canAttest, canRecognize, canRevoke, canReverse}` straight from the view flags. Base URL via `browserEnv.controlPlaneBaseUrl`. NO dollar fields in any type except the rollup `recognizedTotal` (operator-authoritative per §261).
- Produces (`page.tsx`): `'use client'` page — worklist table grouped by scope; per-row buttons gated by `actionFlags`; Attest modal (reason required); Recognize modal (clearance `<select>` constrained to `provided | not_applicable`); Revoke / Reverse (reason required); a rollup panel showing recognized $. Copy: `Attest testing complete - for recognition` (never `production complete`).

**Steps**

- [ ] Write the failing unit spec `tests/recognition.unit.spec.ts` (pure logic — no server; mirrors `estimator-intake.unit.spec.ts` import idiom):
  ```ts
  import { expect, test } from '@playwright/test'
  import {
    actionFlags,
    CLEARANCE_VALUES,
    ATTEST_COPY,
    type WorklistRow,
  } from '../lib/recognition'

  function row(over: Partial<WorklistRow>): WorklistRow {
    return {
      apparatus_id: 'a1', apparatus_designation: 'A-1', scope_id: 's1', project_id: 'p1',
      project_number: 'PN-1', status: 'In Progress', quoted_hours: 10, quoted_revenue: 1500,
      attestation_id: null, attested_by: null, attested_at: null, attest_reason: null,
      net_recognized: 0, is_recognized: false, recognized_event_id: null,
      can_attest: false, can_recognize: false, can_revoke: false, can_reverse: false,
      ...over,
    }
  }

  test('actionFlags passes the view flags through verbatim', () => {
    const f = actionFlags(row({ can_attest: true }))
    expect(f).toEqual({ canAttest: true, canRecognize: false, canRevoke: false, canReverse: false })
  })

  test('recognized row exposes only reverse', () => {
    const f = actionFlags(row({ is_recognized: true, can_reverse: true }))
    expect(f).toEqual({ canAttest: false, canRecognize: false, canRevoke: false, canReverse: true })
  })

  test('clearance enum is exactly provided|not_applicable', () => {
    expect([...CLEARANCE_VALUES].sort()).toEqual(['not_applicable', 'provided'])
  })

  test('attest copy is for-recognition, never production complete', () => {
    expect(ATTEST_COPY).toContain('for recognition')
    expect(ATTEST_COPY.toLowerCase()).not.toContain('production complete')
  })
  ```

- [ ] Run to verify fail:
  ```
  . $HOME/.nvm/nvm.sh; cd apps/operations-web; pnpm install
  pnpm exec playwright test tests/recognition.unit.spec.ts
  ```
  Expected: import error — `lib/recognition.ts` does not exist.

- [ ] Implement `apps/operations-web/lib/recognition.ts`:
  ```ts
  /**
   * recognition.ts — typed client + view-model for the ops recognition bridge.
   * Routes (base via browserEnv.controlPlaneBaseUrl):
   *   POST /api/v1/ops/recognition/completion/attest
   *   POST /api/v1/ops/recognition/completion/{attestation_id}/revoke
   *   POST /api/v1/ops/recognition/events/recognize
   *   POST /api/v1/ops/recognition/events/{event_id}/reverse
   *   GET  /api/v1/ops/recognition/worklist?project_number=
   *   GET  /api/v1/ops/recognition/rollup?project_number=
   * Dollar-free EXCEPT rollup.recognizedTotal (operator-authoritative, §261).
   */
  import { browserEnv } from './browser-env'

  export const CLEARANCE_VALUES = ['provided', 'not_applicable'] as const
  export type Clearance = (typeof CLEARANCE_VALUES)[number]

  export const ATTEST_COPY = 'Attest testing complete - for recognition'

  export interface WorklistRow {
    apparatus_id: string
    apparatus_designation: string
    scope_id: string
    project_id: string
    project_number: string
    status: string
    quoted_hours: number
    quoted_revenue: number
    attestation_id: string | null
    attested_by: string | null
    attested_at: string | null
    attest_reason: string | null
    net_recognized: number
    is_recognized: boolean
    recognized_event_id: string | null
    can_attest: boolean
    can_recognize: boolean
    can_revoke: boolean
    can_reverse: boolean
  }

  export interface RollupRow {
    project_number: string
    scope_id: string
    project_id: string
    recognized_total: number | string
    recognized_count: number
    eligible_count: number
  }

  export interface ActionFlags {
    canAttest: boolean
    canRecognize: boolean
    canRevoke: boolean
    canReverse: boolean
  }

  /** Pure pass-through of the DB view flags (the DB is the single source of truth). */
  export function actionFlags(row: WorklistRow): ActionFlags {
    return {
      canAttest: !!row.can_attest,
      canRecognize: !!row.can_recognize,
      canRevoke: !!row.can_revoke,
      canReverse: !!row.can_reverse,
    }
  }

  export class RecognitionApiError extends Error {
    status: number
    constructor(message: string, status: number) {
      super(message)
      this.status = status
    }
  }

  function base(): string {
    return `${browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')}/api/v1/ops/recognition`
  }

  async function parse<T>(res: Response): Promise<T> {
    let payload: unknown = null
    try { payload = await res.json() } catch { payload = null }
    if (!res.ok) {
      const detail =
        payload && typeof payload === 'object' && 'detail' in payload
          ? String((payload as { detail: unknown }).detail)
          : `Request failed (${res.status})`
      throw new RecognitionApiError(detail, res.status)
    }
    return payload as T
  }

  async function postJson<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${base()}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
    })
    return parse<T>(res)
  }

  export async function fetchWorklist(projectNumber?: string): Promise<WorklistRow[]> {
    const q = projectNumber ? `?project_number=${encodeURIComponent(projectNumber)}` : ''
    return parse<WorklistRow[]>(await fetch(`${base()}/worklist${q}`, { headers: { Accept: 'application/json' } }))
  }

  export async function fetchRollup(projectNumber?: string): Promise<RollupRow[]> {
    const q = projectNumber ? `?project_number=${encodeURIComponent(projectNumber)}` : ''
    return parse<RollupRow[]>(await fetch(`${base()}/rollup${q}`, { headers: { Accept: 'application/json' } }))
  }

  export async function attestComplete(apparatusId: string, attestedBy: string, reason: string) {
    return postJson<{ attestation_id: string }>('/completion/attest', {
      apparatus_id: apparatusId, attested_by: attestedBy, reason,
    })
  }

  export async function revokeAttestation(attestationId: string, revokedBy: string, reason: string) {
    return postJson<{ attestation_id: string }>(`/completion/${attestationId}/revoke`, {
      revoked_by: revokedBy, reason,
    })
  }

  export async function recognize(
    apparatusId: string, recognizedBy: string,
    datasheetClearance: Clearance, datasheetRef: string | null,
    cxClearance: Clearance, cxRef: string | null,
  ) {
    return postJson<{ event_id: string }>('/events/recognize', {
      apparatus_id: apparatusId, recognized_by: recognizedBy,
      datasheet_clearance: datasheetClearance, datasheet_ref: datasheetRef,
      cx_clearance: cxClearance, cx_ref: cxRef,
    })
  }

  export async function reverseEvent(eventId: string, reversedBy: string, reason: string) {
    return postJson<{ reversal_id: string }>(`/events/${eventId}/reverse`, {
      reversed_by: reversedBy, reason,
    })
  }
  ```

- [ ] Implement the page `apps/operations-web/app/pm-review/recognition/page.tsx` (a `'use client'` page using the lib; the smoke spec below pins the load-bearing structure — file input is NOT used here; the page fetches the worklist on a project-number submit). Minimum structure the smoke asserts: a project-number input + Load button; a worklist table (one row per apparatus, designation + status visible); per-row action buttons gated by `actionFlags` and labelled `Attest`, `Recognize`, `Revoke`, `Reverse`; a rollup panel; the literal copy `Attest testing complete - for recognition`; and NEVER the string `production complete`. **Per spec §8, action entry is a real `role="dialog"` modal — NO `window.prompt`:** Attest/Revoke/Reverse open a reason-required modal (a `<textarea aria-label="reason">`; Confirm disabled until non-blank), and Recognize opens a modal with two enum-constrained `<select>` clearance inputs (`aria-label="datasheet clearance"` / `aria-label="cx clearance"`), each offering exactly the two options `provided` / `not_applicable` (rendered from `CLEARANCE_VALUES`). The selected clearance is carried into the `recognize()` POST body. (Full component code: standard React table + modal pattern from `estimator-intake/page.tsx`; the PM actor id comes from `process.env.NEXT_PUBLIC_OPS_DEV_PM_ID || '00000000-0000-0000-0000-000000000001'` as in that page.)
  ```tsx
  'use client'
  import * as React from 'react'
  import {
    actionFlags, fetchWorklist, fetchRollup, attestComplete, recognize,
    reverseEvent, revokeAttestation, CLEARANCE_VALUES, ATTEST_COPY,
    type WorklistRow, type RollupRow, type Clearance,
  } from '../../../lib/recognition'

  const { useCallback, useMemo, useState } = React
  const PM_ACTOR_ID = process.env.NEXT_PUBLIC_OPS_DEV_PM_ID || '00000000-0000-0000-0000-000000000001'

  // Modal descriptor: which action is pending on which row. Spec §8 mandates a
  // reason-required modal (attest/revoke/reverse) and enum-constrained clearance
  // <select>s (recognize) — NO window.prompt anywhere.
  type ModalKind = 'attest' | 'recognize' | 'revoke' | 'reverse'
  interface ModalState { kind: ModalKind; row: WorklistRow }

  export default function RecognitionPage() {
    const [pn, setPn] = useState('')
    const [rows, setRows] = useState<WorklistRow[]>([])
    const [rollup, setRollup] = useState<RollupRow[]>([])
    const [busy, setBusy] = useState(false)
    const [err, setErr] = useState<string | null>(null)
    const [modal, setModal] = useState<ModalState | null>(null)

    const load = useCallback(async (project?: string) => {
      setBusy(true); setErr(null)
      try {
        const [w, r] = await Promise.all([fetchWorklist(project), fetchRollup(project)])
        setRows(w); setRollup(r)
      } catch (e) { setErr(e instanceof Error ? e.message : 'load failed') }
      finally { setBusy(false) }
    }, [])

    // Action buttons OPEN the modal; the modal's submit performs the API call.
    const openModal = useCallback((kind: ModalKind, row: WorklistRow) => {
      setErr(null); setModal({ kind, row })
    }, [])

    // Submit handler invoked by the modal with the collected, validated inputs.
    const submitModal = useCallback(async (
      kind: ModalKind, row: WorklistRow,
      reason: string, ds: Clearance, cx: Clearance,
    ) => {
      try {
        if (kind === 'attest') await attestComplete(row.apparatus_id, PM_ACTOR_ID, reason)
        else if (kind === 'recognize') await recognize(row.apparatus_id, PM_ACTOR_ID, ds, null, cx, null)
        else if (kind === 'revoke') { if (!row.attestation_id) return; await revokeAttestation(row.attestation_id, PM_ACTOR_ID, reason) }
        else if (kind === 'reverse') { if (!row.recognized_event_id) return; await reverseEvent(row.recognized_event_id, PM_ACTOR_ID, reason) }
        setModal(null)
        await load(pn || undefined)
      } catch (e) { setErr(e instanceof Error ? e.message : `${kind} failed`) }
    }, [load, pn])

    const grouped = useMemo(() => {
      const m = new Map<string, WorklistRow[]>()
      for (const r of rows) { const k = r.scope_id; (m.get(k) ?? m.set(k, []).get(k)!).push(r) }
      return [...m.entries()]
    }, [rows])

    return (
      <main className="p-6">
        <h1 className="text-xl font-semibold">Recognition — {ATTEST_COPY}</h1>
        <div className="mt-4 flex gap-2">
          <input aria-label="project number" value={pn} onChange={(e) => setPn(e.target.value)}
                 placeholder="project number" className="rounded border px-2 py-1" />
          <button onClick={() => load(pn || undefined)} disabled={busy}
                  className="rounded bg-gray-800 px-3 py-1 text-white">Load</button>
        </div>
        {err && <p role="alert" className="mt-2 text-red-700">{err}</p>}

        {modal && (
          <ActionModal
            kind={modal.kind}
            row={modal.row}
            onCancel={() => setModal(null)}
            onSubmit={submitModal}
          />
        )}

        <section className="mt-6">
          <h2 className="font-medium">Recognized $ rollup</h2>
          <table className="mt-2 w-full text-sm">
            <thead><tr><th className="text-left">Project</th><th className="text-right">Recognized $</th>
              <th className="text-right">Recognized</th><th className="text-right">Eligible</th></tr></thead>
            <tbody>
              {rollup.map((r) => (
                <tr key={`${r.project_number}-${r.scope_id}`} className="border-t">
                  <td>{r.project_number}</td>
                  <td className="text-right">{Number(r.recognized_total).toLocaleString()}</td>
                  <td className="text-right">{r.recognized_count}</td>
                  <td className="text-right">{r.eligible_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="mt-6">
          <h2 className="font-medium">Worklist</h2>
          {grouped.map(([scopeId, scopeRows]) => (
            <div key={scopeId} className="mt-3">
              <table className="w-full text-sm">
                <thead><tr><th className="text-left">Apparatus</th><th className="text-left">Status</th>
                  <th className="text-left">Actions</th></tr></thead>
                <tbody>
                  {scopeRows.map((row) => {
                    const f = actionFlags(row)
                    return (
                      <tr key={row.apparatus_id} className="border-t">
                        <td>{row.apparatus_designation}</td>
                        <td>{row.status}</td>
                        <td className="flex gap-2">
                          <button disabled={!f.canAttest} onClick={() => openModal('attest', row)}
                                  className="rounded border px-2 py-0.5 disabled:opacity-40">Attest</button>
                          <button disabled={!f.canRecognize} onClick={() => openModal('recognize', row)}
                                  className="rounded border px-2 py-0.5 disabled:opacity-40">Recognize</button>
                          <button disabled={!f.canRevoke} onClick={() => openModal('revoke', row)}
                                  className="rounded border px-2 py-0.5 disabled:opacity-40">Revoke</button>
                          <button disabled={!f.canReverse} onClick={() => openModal('reverse', row)}
                                  className="rounded border px-2 py-0.5 disabled:opacity-40">Reverse</button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ))}
        </section>
      </main>
    )
  }

  // ---- Reason-required modal + enum-constrained clearance <select>s (spec §8) ----
  const MODAL_TITLE: Record<ModalKind, string> = {
    attest: ATTEST_COPY,                 // 'Attest testing complete - for recognition' (never 'production complete')
    recognize: 'Recognize revenue',
    revoke: 'Revoke attestation',
    reverse: 'Reverse recognition',
  }

  function ActionModal(props: {
    kind: ModalKind
    row: WorklistRow
    onCancel: () => void
    onSubmit: (kind: ModalKind, row: WorklistRow, reason: string, ds: Clearance, cx: Clearance) => void | Promise<void>
  }) {
    const { kind, row, onCancel, onSubmit } = props
    const [reason, setReason] = useState('')
    const [ds, setDs] = useState<Clearance>('not_applicable')
    const [cx, setCx] = useState<Clearance>('not_applicable')
    const isRecognize = kind === 'recognize'
    // attest/revoke/reverse REQUIRE a non-blank reason; recognize requires two enum clearances.
    const canSubmit = isRecognize
      ? CLEARANCE_VALUES.includes(ds) && CLEARANCE_VALUES.includes(cx)
      : reason.trim().length > 0

    return (
      <div role="dialog" aria-modal="true" aria-label={MODAL_TITLE[kind]}
           className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
        <div className="w-[28rem] rounded bg-white p-4 shadow-lg">
          <h3 className="font-semibold">{MODAL_TITLE[kind]}</h3>
          <p className="mt-1 text-sm text-gray-600">{row.apparatus_designation}</p>

          {isRecognize ? (
            <div className="mt-3 grid grid-cols-2 gap-3">
              <label className="text-sm">Datasheet clearance
                <select aria-label="datasheet clearance" value={ds}
                        onChange={(e) => setDs(e.target.value as Clearance)}
                        className="mt-1 w-full rounded border px-2 py-1">
                  {CLEARANCE_VALUES.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </label>
              <label className="text-sm">Cx clearance
                <select aria-label="cx clearance" value={cx}
                        onChange={(e) => setCx(e.target.value as Clearance)}
                        className="mt-1 w-full rounded border px-2 py-1">
                  {CLEARANCE_VALUES.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </label>
            </div>
          ) : (
            <label className="mt-3 block text-sm">Reason (required)
              <textarea aria-label="reason" value={reason} onChange={(e) => setReason(e.target.value)}
                        className="mt-1 w-full rounded border px-2 py-1" rows={3} />
            </label>
          )}

          <div className="mt-4 flex justify-end gap-2">
            <button onClick={onCancel} className="rounded border px-3 py-1">Cancel</button>
            <button aria-label="confirm" disabled={!canSubmit}
                    onClick={() => onSubmit(kind, row, reason.trim(), ds, cx)}
                    className="rounded bg-gray-800 px-3 py-1 text-white disabled:opacity-40">Confirm</button>
          </div>
        </div>
      </div>
    )
  }
  ```

- [ ] Write the failing route-mocked smoke `tests/browser-shell.pm-recognition.smoke.spec.ts` (mirror the estimator-intake smoke; mock both GET routes; assert render + flag-gated buttons + the for-recognition copy + POST body on Attest):
  ```ts
  import { expect, test } from '@playwright/test'

  const WORKLIST = [
    { apparatus_id: 'a1', apparatus_designation: 'CB-1', scope_id: 's1', project_id: 'p1',
      project_number: 'PN-1', status: 'Complete', quoted_hours: 10, quoted_revenue: 1500,
      attestation_id: 'att1', attested_by: 'pm', attested_at: '2026-06-23', attest_reason: 'done',
      net_recognized: 0, is_recognized: false, recognized_event_id: null,
      can_attest: false, can_recognize: true, can_revoke: true, can_reverse: false },
    { apparatus_id: 'a2', apparatus_designation: 'DS-1', scope_id: 's1', project_id: 'p1',
      project_number: 'PN-1', status: 'In Progress', quoted_hours: 4, quoted_revenue: 600,
      attestation_id: null, attested_by: null, attested_at: null, attest_reason: null,
      net_recognized: 0, is_recognized: false, recognized_event_id: null,
      can_attest: true, can_recognize: false, can_revoke: false, can_reverse: false },
  ]
  const ROLLUP = [{ project_number: 'PN-1', scope_id: 's1', project_id: 'p1',
    recognized_total: 0, recognized_count: 0, eligible_count: 2 }]

  test('recognition page: renders worklist, gates buttons by flags, modal attest + recognize post, for-recognition copy', async ({ page }) => {
    await page.route('**/api/v1/ops/recognition/worklist*', (r) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(WORKLIST) }))
    await page.route('**/api/v1/ops/recognition/rollup*', (r) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ROLLUP) }))
    let attestBody: unknown = null
    await page.route('**/api/v1/ops/recognition/completion/attest', async (r) => {
      attestBody = r.request().postDataJSON()
      await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ attestation_id: 'att2' }) })
    })
    let recognizeBody: unknown = null
    await page.route('**/api/v1/ops/recognition/events/recognize', async (r) => {
      recognizeBody = r.request().postDataJSON()
      await r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ event_id: 'ev1' }) })
    })

    const resp = await page.goto('/pm-review/recognition', { waitUntil: 'networkidle' })
    expect(resp?.ok()).toBeTruthy()
    await expect(page.getByText('for recognition')).toBeVisible()
    await expect(page.locator('body')).not.toContainText('production complete')

    await page.getByLabel('project number').fill('PN-1')
    await page.getByRole('button', { name: 'Load' }).click()
    await expect(page.getByText('CB-1')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText('DS-1')).toBeVisible()

    // a1 is Complete+attested -> Recognize enabled, Attest disabled; a2 -> Attest enabled
    const row1 = page.getByRole('row', { name: /CB-1/ })
    await expect(row1.getByRole('button', { name: 'Recognize' })).toBeEnabled()
    await expect(row1.getByRole('button', { name: 'Attest' })).toBeDisabled()
    const row2 = page.getByRole('row', { name: /DS-1/ })
    await expect(row2.getByRole('button', { name: 'Attest' })).toBeEnabled()

    // --- ATTEST: opens a reason-required modal (NO window.prompt); Confirm posts the typed reason ---
    await row2.getByRole('button', { name: 'Attest' }).click()
    const attestModal = page.getByRole('dialog')
    await expect(attestModal).toBeVisible()
    await expect(attestModal).toContainText('for recognition')
    await expect(attestModal).not.toContainText('production complete')
    // Confirm is disabled until a non-blank reason is entered.
    await expect(attestModal.getByRole('button', { name: 'Confirm' })).toBeDisabled()
    await attestModal.getByLabel('reason').fill('tested ok')
    await attestModal.getByRole('button', { name: 'Confirm' }).click()
    await expect.poll(() => attestBody).not.toBeNull()
    expect((attestBody as { apparatus_id: string }).apparatus_id).toBe('a2')
    expect((attestBody as { reason: string }).reason).toBe('tested ok')

    // --- RECOGNIZE: opens a modal with two enum-constrained <select>s; POST carries the chosen value ---
    await row1.getByRole('button', { name: 'Recognize' }).click()
    const recModal = page.getByRole('dialog')
    await expect(recModal).toBeVisible()
    const dsSelect = recModal.getByLabel('datasheet clearance')
    // the <select> offers EXACTLY provided | not_applicable
    await expect(dsSelect.locator('option')).toHaveText(['provided', 'not_applicable'])
    await dsSelect.selectOption('provided')
    await recModal.getByLabel('cx clearance').selectOption('not_applicable')
    await recModal.getByRole('button', { name: 'Confirm' }).click()
    await expect.poll(() => recognizeBody).not.toBeNull()
    expect((recognizeBody as { apparatus_id: string }).apparatus_id).toBe('a1')
    expect((recognizeBody as { datasheet_clearance: string }).datasheet_clearance).toBe('provided')
    expect((recognizeBody as { cx_clearance: string }).cx_clearance).toBe('not_applicable')
  })
  ```

- [ ] Run to verify fail:
  ```
  . $HOME/.nvm/nvm.sh; cd apps/operations-web
  pnpm typecheck                                   # fails: lib/recognition.ts + page not yet present
  pnpm exec playwright test tests/browser-shell.pm-recognition.smoke.spec.ts   # next build -> route 404
  ```
  Expected: typecheck error (missing module) BEFORE the lib is written; after writing the lib + page, run again.

- [ ] Run to verify pass (typecheck + unit + smoke):
  ```
  . $HOME/.nvm/nvm.sh; cd apps/operations-web
  pnpm typecheck
  pnpm exec playwright test tests/recognition.unit.spec.ts
  pnpm exec playwright test tests/browser-shell.pm-recognition.smoke.spec.ts
  ```
  Expected: typecheck clean; unit spec 4 passed; smoke spec passes (render + flag-gating + reason-required modal attest POST body + recognize modal `<select>` two-option enum + recognize POST clearance value + for-recognition copy + no `production complete`).

- [ ] Commit:
  ```
  git add apps/operations-web/lib/recognition.ts apps/operations-web/app/pm-review/recognition/page.tsx apps/operations-web/tests/recognition.unit.spec.ts apps/operations-web/tests/browser-shell.pm-recognition.smoke.spec.ts
  git commit -m "feat(operations-web): /pm-review/recognition worklist+rollup UI (flag-gated, enum clearance, for-recognition copy)"
  ```

---

## Final gate items (non-code)

These are NOT code commits — they are the operator-gated release controls. Do not perform them autonomously; surface them and STOP.

- [ ] **G (HARD PROD RELEASE GATE — restate + enforce).** `009` and any `ops.*` recognition path MUST NOT reach prod until the `ops_app` role-boundary hardening packet (spec 5.11) is authored and applied: `REVOKE INSERT, UPDATE (status, source, provenance_status) ON ops.apparatus`; no direct DML on `ops.completion_attestation` or `ops.revenue_recognition_event`; the mutation functions (`attest_apparatus_complete`, `revoke_completion_attestation`, `approve_and_recognize`) become `SECURITY DEFINER` owned by the object owner with `set search_path = ops, pg_temp` (NOT `public`); `REVOKE CREATE ON SCHEMA public FROM PUBLIC`; and a test running AS `ops_app` proves a direct `UPDATE … status='Complete'` / `INSERT` raises *permission denied* while the function path succeeds. The ctx-guard is forgeable, so this is a *precondition of prod apply*, not a follow-up. This slice ships dev-only behind this gate.

- [ ] **Operator gate — merge + `ops_dev` apply.** Run the full migration + package + API + UI suites green on `ops_test`, run the IRP cross-engine pass (the §5.5/5.6 firewall touch + §5.9 down-restore get dedicated focused-review lenses), then surface to the operator for the merge-to-`main` + `ops_dev`-apply decision. Do NOT merge or apply autonomously.

---
