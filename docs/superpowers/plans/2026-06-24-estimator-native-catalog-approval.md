# Native Catalog EstimateEnvelope Approval — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Approve a compiled (catalog-only) `EstimateEnvelope` into `ops.*` through the existing `approve_run` materializer — a second producer of the Chip-5 intake envelope — with everything non-catalog failing closed.

**Architecture:** A native envelope is validated + fail-closed-guarded, then **pivoted to the existing flat `IntakePayload` dict** (catalog lines only) and persisted as an `ops.intake_runs` row (`source_format='native'`) whose `canonical_payload_json` == `review_payload_json` (so `patch_review` works unchanged) with the raw envelope in a new `estimate_envelope_json` sidecar. **`approve_run` / `materialize` / `load.py` are unchanged** — the pivoted flat payload flows through them exactly like a workbook run. A new ops migration `010` adds the enum value, the identity columns, the immutability-trigger extension, and the partial-unique indexes.

**Tech Stack:** Python 3 + psycopg3 (`packages/ops-intake`), PostgreSQL 17 (`ops_test`/`ops_dev`), FastAPI (`apps/control-plane-api`), pytest. Pinned contract: `docs/spec/estimator-envelope-ops-mapping/_pinned-estimator-core/` (estimator-core @ `c051c02`).

## Global Constraints

- **Source of truth = the packet's "Instance Review Corrections" C1–C7** (`docs/spec/estimator-envelope-ops-mapping/FIELD_MAPPING_PACKET.md`). C1–C7 OVERRIDE the body §2/§4/§11.
- **`approve_run` is the SOLE `ops.*` writer** — this slice adds NO new writer and changes neither `approve.py` nor `load.py`.
- **Migration `010` (additive):** `ALTER TYPE ops.intake_source_format ADD VALUE 'native'`; `ADD COLUMN estimate_envelope_json jsonb`; `ADD COLUMN`s `envelope_id`/`quote_version`/`content_hash`/`source_draft_id`/`source_revision_id`; **NO `source_kind`**; extend `ops.trg_intake_run_immutable` to protect the new identity cols + `estimate_envelope_json` (write-once); partial-unique indexes `WHERE source_format='native'` (on `content_hash`; on `(project_number, quote_version)`); a **real down story** (RAISE if any `source_format='native'` rows exist, then rebuild the enum type without `'native'`).
- **Native persist:** the pivoted **flat `IntakePayload`** goes in BOTH `canonical_payload_json` AND `review_payload_json`; the raw `EstimateEnvelope` goes ONLY in `estimate_envelope_json`; `payload_schema_version='estimate_envelope_v1'`; `parser_version='estimator-core/c051c02'`.
- **Fail-closed governed findings** (PM-safe message, NO `$`; finance figures only in `diagnostic_detail`), NEVER a downstream `KeyError`/`NOT NULL`: `missing_project_number`, `missing_required_catalog_field`, `invalid_line_state`, `content_hash_mismatch` (server-recompute model — see Task 3 note), `non_catalog_line`, `nonzero_service`, `nonzero_cost`, `m4_unsupported` (`replication_m4 != 1`).
- **Money:** cents→dollars at the pivot boundary using `Decimal` (NEVER float); `±1¢` reconciliation in tests (`bid_cents`↔`Σ scope_quote.adjusted_total`; `scope.adjusted_cents`↔`scope_quote.adjusted_total`).
- **`ops_test` only** for TDD (the conftest `_require_ops_test` guard refuses any other DSN). **Merge to `main` and `ops_dev` apply are OPERATOR-GATED. Prod is BLOCKED behind the `ops_app` role-boundary gate — out of scope.**
- All work on host lane `estimator/envelope-ops-mapping` over `ssh olares-mesh`; CC owns host commits.

## Plan Review Corrections (R1, 2026-06-24)

Operator plan-review patched 7 task-level mechanics (architecture unchanged — still native catalog-only through the existing `approve_run`):
- **R1-1 (High):** migration `010` partial indexes use `source_format::text = 'native'`, so the new enum value is not *used* in the same transaction it is *added* (the conftest runs the whole file via one `conn.execute`).
- **R1-2 (High):** the conftest reset blocks `delete from ops.intake_runs` before `010` down, so teardown after Task-6 native rows does not trip the down-migration's data-loss guard.
- **R1-3 (High):** Task 3 imports/defines `validate_envelope` ONLY; the pivot + `recompute_content_hash` move to Task 4 (no forward reference → Task 3 passes alone).
- **R1-4 (High):** `create_run_native` writes the governed rejected run WITHOUT the strict pivot/hash (they would `KeyError` on a malformed envelope); pivot/hash run only on the happy path.
- **R1-5 (Med):** the validator uses `Decimal(str(...))` comparisons (accepts `1.0`, never truncates) and checks scope-level `service_hours`.
- **R1-6 (Med):** the immutability test uses per-column typed drift values (`quote_version=2`, text cols `'zz'`), not a single `'zzz'` that fails on integer cast.
- **R1-7 (Med):** the API route test extends the real `apps/control-plane-api/tests/test_ops_intake_routes.py` harness (its `apply_migrations`/`client`/`person_id` fixtures) through `010`.

---

## File Structure

| File | Responsibility |
|---|---|
| `docs/spec/estimator-envelope-ops-mapping/FIELD_MAPPING_PACKET.md` (modify) | Task 1: strike/mark superseded §2/§4/§11 lines |
| `infra/database/migrations/ops/010_native_envelope_intake.sql` (create) | enum value + columns + trigger extension + indexes (up) |
| `infra/database/migrations/ops/010_native_envelope_intake_down.sql` (create) | real reversible down (guard + enum rebuild) |
| `infra/database/migrations/ops/test_010_native_envelope_intake.py` (create) | migration-level pytest |
| `infra/database/migrations/ops/MANIFEST.md` (modify) | register 010 |
| `packages/ops-intake/src/ops_intake/native.py` (create) | envelope validate + §3 guards + content_hash recompute + pivot→IntakePayload |
| `packages/ops-intake/src/ops_intake/envelope.py` (modify) | add `create_run_native(...)` |
| `packages/ops-intake/tests/conftest.py` (modify) | chain `010` in `apply_migrations` |
| `packages/ops-intake/tests/test_native_envelope.py` (create) | unit + e2e TDD for the native path |
| `apps/control-plane-api/services/ops/intake_router.py` (modify) | `POST /api/v1/ops/intake/native` |

**Interfaces produced (referenced across tasks):**
- `native.validate_envelope(env: dict) -> list[Finding]` — Task 3
- `native.recompute_content_hash(env: dict) -> str` — Task 3
- `native.pivot_to_intake_payload(env: dict) -> dict` — Task 4 (returns a plain dict, `IntakePayload`-shaped, suitable for `_payload_from_dict`)
- `envelope.create_run_native(dsn, *, uploaded_by, envelope: dict) -> dict` — Task 5 (same return shape as `create_run`)

---

### Task 1: Normalize the packet from C1–C7 (doc-only)

**Files:** Modify `docs/spec/estimator-envelope-ops-mapping/FIELD_MAPPING_PACKET.md`

- [ ] **Step 1: Mark the superseded body lines.** In §2, append to the `canonical_payload_json` row and the `source_format`/`source_kind` framing: `**[SUPERSEDED BY C1/C2 — see Instance Review Corrections]**`. In §4, mark the `source_kind` column line and the bare DDL block: `**[SUPERSEDED BY C1/C4 — enum value + estimate_envelope_json + trigger extension are mandatory; no source_kind]**`. In §11, add at the top of the build-slice list: `**Authoritative scope = Instance Review Corrections "Build-plan deltas".**`

- [ ] **Step 2: Commit.**
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git add docs/spec/estimator-envelope-ops-mapping/FIELD_MAPPING_PACKET.md && git commit -m "docs(estimator): mark §2/§4/§11 superseded by C1-C7"'
```

---

### Task 2: Migration 010 — enum value, identity columns, immutability extension, partial indexes

**Files:**
- Create: `infra/database/migrations/ops/010_native_envelope_intake.sql`
- Create: `infra/database/migrations/ops/010_native_envelope_intake_down.sql`
- Create: `infra/database/migrations/ops/test_010_native_envelope_intake.py`
- Modify: `packages/ops-intake/tests/conftest.py` (chain 010)
- Modify: `infra/database/migrations/ops/MANIFEST.md`

**Interfaces — Produces:** the `'native'` enum value; `ops.intake_runs` columns `envelope_id text, quote_version int, content_hash text, source_draft_id text, source_revision_id text, estimate_envelope_json jsonb`; partial-unique indexes `uq_intake_runs_content_hash_native`, `uq_intake_runs_proj_quote_version_native`; the extended `trg_intake_run_immutable`.

**Grounding note:** `007` created `ops.intake_source_format` and `ops.trg_intake_run_immutable()`. `ALTER TYPE ... ADD VALUE` cannot run inside a transaction block that later uses the new value, and is irreversible in place — hence the down rebuild. The conftest applies migrations with `autocommit=True`, so `ADD VALUE` is fine.

- [ ] **Step 1: Write the failing migration test.** Create `infra/database/migrations/ops/test_010_native_envelope_intake.py`:
```python
import os
import pathlib
import psycopg
import pytest

MIG = pathlib.Path(__file__).resolve().parent

def _dsn():
    d = os.environ.get("OPS_DEV_DSN") or (
        "host=127.0.0.1 port=5432 dbname=ops_test user=postgres "
        "password={} sslmode=disable".format(os.environ.get("OPS_DEV_PGPASSWORD") or os.environ.get("PGPASSWORD", ""))
    )
    from psycopg.conninfo import conninfo_to_dict
    assert conninfo_to_dict(d).get("dbname") == "ops_test", "test must target ops_test"
    return d

def test_010_adds_native_enum_and_columns():
    with psycopg.connect(_dsn(), autocommit=True) as c:
        vals = [r[0] for r in c.execute(
            "select e.enumlabel from pg_enum e join pg_type t on t.oid=e.enumtypid"
            " where t.typname='intake_source_format'").fetchall()]
        assert "native" in vals
        cols = [r[0] for r in c.execute(
            "select column_name from information_schema.columns"
            " where table_schema='ops' and table_name='intake_runs'").fetchall()]
        for col in ("envelope_id","quote_version","content_hash","source_draft_id",
                    "source_revision_id","estimate_envelope_json"):
            assert col in cols, col
        assert "source_kind" not in cols  # C1: no source_kind

def test_010_identity_columns_are_immutable():
    """trg_intake_run_immutable must reject UPDATE drift on the new identity cols."""
    with psycopg.connect(_dsn(), autocommit=True) as c:
        pid = c.execute("insert into ops.persons (display_name) values ('m10') returning person_id").fetchone()[0]
        rid = c.execute(
            "insert into ops.intake_runs (project_number, source_format, status, conflict_kind,"
            " payload_schema_version, parser_version, canonical_payload_json, review_payload_json,"
            " uploaded_by, content_hash, quote_version, envelope_id)"
            " values ('P10','native'::ops.intake_source_format,'parsed','none','estimate_envelope_v1',"
            " 'estimator-core/c051c02','{}'::jsonb,'{}'::jsonb,%s,'h1',1,'e1') returning id",
            (pid,)).fetchone()[0]
        # R1-6: typed drift per column — quote_version is integer, so a 'zzz' there fails on CAST, not the
        # trigger. Each value is valid for its type but DIFFERENT from the inserted row, so the trigger fires.
        drift = {"content_hash": "'zz'", "envelope_id": "'zz'", "source_revision_id": "'zz'",
                 "source_draft_id": "'zz'", "quote_version": "2"}
        for col, val in drift.items():
            with pytest.raises(psycopg.errors.RaiseException):
                c.execute(f"update ops.intake_runs set {col}={val} where id=%s", (rid,))

def test_010_partial_unique_native_only():
    with psycopg.connect(_dsn(), autocommit=True) as c:
        idx = [r[0] for r in c.execute(
            "select indexname from pg_indexes where schemaname='ops' and tablename='intake_runs'").fetchall()]
        assert "uq_intake_runs_content_hash_native" in idx
        assert "uq_intake_runs_proj_quote_version_native" in idx
```

- [ ] **Step 2: Run it to verify it fails.**
Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && set -a; . infra/.env; set +a; OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable" .venv/bin/python -m pytest infra/database/migrations/ops/test_010_native_envelope_intake.py -x -q'`
Expected: FAIL (`assert "native" in vals` — column/enum/index absent). *(`ops_test` must first be built by the conftest chain; run the package suite once to create it, or apply 001–009 first.)*

- [ ] **Step 3: Write the up migration.** Create `infra/database/migrations/ops/010_native_envelope_intake.sql`:
```sql
-- ops migration 010 -- Native estimator EstimateEnvelope intake (catalog-only v1). Additive + reversible. Dev-only.
-- Adds the 'native' source_format, the envelope identity provenance columns, the raw-envelope sidecar,
-- the write-once trigger extension, and the native-only partial-unique indexes. NO source_kind (C1).

alter type ops.intake_source_format add value if not exists 'native';

alter table ops.intake_runs
  add column if not exists envelope_id           text,
  add column if not exists quote_version          integer,
  add column if not exists content_hash           text,
  add column if not exists source_draft_id        text,
  add column if not exists source_revision_id     text,
  add column if not exists estimate_envelope_json jsonb;

-- C4: the new identity/provenance cols are write-once (extend the existing immutability trigger).
create or replace function ops.trg_intake_run_immutable() returns trigger language plpgsql as $$
begin
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
       or new.project_number         is distinct from old.project_number
       or new.envelope_id            is distinct from old.envelope_id            -- 010 (write-once)
       or new.quote_version          is distinct from old.quote_version          -- 010
       or new.content_hash           is distinct from old.content_hash           -- 010
       or new.source_draft_id        is distinct from old.source_draft_id        -- 010
       or new.source_revision_id     is distinct from old.source_revision_id     -- 010
       or new.estimate_envelope_json is distinct from old.estimate_envelope_json -- 010
    then
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

-- C4: idempotency — one native run per compiled-envelope content_hash.
-- R1-1: the predicate casts source_format::text = 'native' (NOT 'native'::ops.intake_source_format) so it
-- does not USE the just-ADDed enum value in the same transaction (the conftest runs this whole file in one
-- conn.execute; Postgres forbids using a newly-added enum value in the txn that added it).
create unique index if not exists uq_intake_runs_content_hash_native
  on ops.intake_runs (content_hash)
  where source_format::text = 'native' and content_hash is not null;

-- C4: one native run per (project_number, quote_version); supersede = a new quote_version.
create unique index if not exists uq_intake_runs_proj_quote_version_native
  on ops.intake_runs (project_number, quote_version)
  where source_format::text = 'native' and quote_version is not null;
```

- [ ] **Step 4: Write the down migration.** Create `infra/database/migrations/ops/010_native_envelope_intake_down.sql`:
```sql
-- ops migration 010 DOWN. Reverses the columns/indexes; rebuilds the enum WITHOUT 'native'.
-- Refuses if any native run exists (an enum value cannot be dropped while in use, and silently
-- dropping native runs would be data loss).

do $$
begin
  if exists (select 1 from ops.intake_runs where source_format = 'native') then
    raise exception 'refusing 010 down: native intake_runs exist (drop them first)';
  end if;
end $$;

drop index if exists ops.uq_intake_runs_proj_quote_version_native;
drop index if exists ops.uq_intake_runs_content_hash_native;

-- restore the 007 trigger body (drop the 010 identity-col checks)
create or replace function ops.trg_intake_run_immutable() returns trigger language plpgsql as $$
begin
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
       or new.project_number         is distinct from old.project_number then
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

alter table ops.intake_runs
  drop column if exists estimate_envelope_json,
  drop column if exists source_revision_id,
  drop column if exists source_draft_id,
  drop column if exists content_hash,
  drop column if exists quote_version,
  drop column if exists envelope_id;

-- rebuild the enum without 'native' (no DROP VALUE in Postgres)
alter type ops.intake_source_format rename to intake_source_format_old;
create type ops.intake_source_format as enum ('decomposed_scope_sheet','flat_quote','unsupported');
alter table ops.intake_runs
  alter column source_format type ops.intake_source_format
  using source_format::text::ops.intake_source_format;
drop type ops.intake_source_format_old;
```

- [ ] **Step 5: Chain 010 in the conftest.** In `packages/ops-intake/tests/conftest.py`, add `"010_native_envelope_intake.sql"` to the end of the `up_migrations` list, and in BOTH pre-up and post-yield reset blocks add a guarded down BEFORE the `009` down:
```python
        if _ops_schema_exists(c):
            c.execute("delete from ops.intake_runs")  # R1-2: clear native rows so 010 down's data-loss guard passes in teardown
            _run_sql(c, mig_dir / "010_native_envelope_intake_down.sql")
            _run_sql(c, mig_dir / "009_recognition_bridge_down.sql")
```
(Apply to both reset blocks; `010` down RAISEs only if native rows exist — clean `ops_test` has none, so it is a safe no-op there.)

- [ ] **Step 6: Run the migration test to verify it passes.**
Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && set -a; . infra/.env; set +a; OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable" .venv/bin/python -m pytest packages/ops-intake/tests/ infra/database/migrations/ops/test_010_native_envelope_intake.py -q'`
Expected: PASS (the package conftest builds `ops_test` through `010`, then the migration tests pass). Confirm the existing suite is still green.

- [ ] **Step 7: Register 010 in MANIFEST + commit.** Add the `010` up/down/test entry to `infra/database/migrations/ops/MANIFEST.md` mirroring the `009` entry, then:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git add infra/database/migrations/ops/010_native_envelope_intake.sql infra/database/migrations/ops/010_native_envelope_intake_down.sql infra/database/migrations/ops/test_010_native_envelope_intake.py infra/database/migrations/ops/MANIFEST.md packages/ops-intake/tests/conftest.py && git commit -m "feat(ops): migration 010 native envelope intake columns + enum + guards"'
```

---

### Task 3: `native.validate_envelope` + `recompute_content_hash` (the fail-closed gate)

**Files:**
- Create: `packages/ops-intake/src/ops_intake/native.py`
- Create/extend: `packages/ops-intake/tests/test_native_envelope.py`

**Interfaces — Consumes:** `validate.Finding`. **Produces:** `validate_envelope(env: dict) -> list[Finding]`, `recompute_content_hash(env: dict) -> str`.

**C6 note (decision flagged for the operator):** v1 computes a **server-side** `content_hash` = `sha256` of a deterministic canonical serialization of the *pivoted* payload, and uses THAT as the idempotency key — so a client-supplied hash is never trusted. Exact-match verification against the envelope's own `content_hash` (which would require porting estimator-core `content-hash.ts` to Python) is **Task 3b (optional)** below. `validate_envelope` still emits `content_hash_mismatch` IF the envelope carries a `content_hash` that disagrees with a *structurally* recomputed one once 3b lands; until then it is a no-op placeholder that never blocks.

- [ ] **Step 1: Write failing tests for the reject matrix.** In `packages/ops-intake/tests/test_native_envelope.py` (R1-3: import `validate_envelope` ONLY here — pivot/hash arrive in Task 4):
```python
from ops_intake.native import validate_envelope

def _catalog_env(**over):
    env = {
        "project_number": "JOB-1", "envelope_id": "env-1", "quote_version": 1,
        "content_hash": "abc", "source_draft_id": "d1", "source_revision_id": "r1",
        "totals": {"bid_cents": 100000, "service_hours": 0},
        "scopes": [{
            "scope_id": "S1", "name": "A1", "neta_standard": "ATS",
            "replication_m4": 1, "adjustment_multiplier_n4": 1,
            "scope_totals": {"onsite_labor_cents": 100000, "offsite_labor_cents": 0,
                             "cost_cents": 0, "service_cents": 0, "quoted_app_hours": 6,
                             "adjusted_cents": 100000},
            "lines": [{
                "line_uid": "S1:row1", "line_kind": "catalog", "included": True,
                "equipment_model_ref": "MV-CB-01", "base_qty": 3, "project_intake_qty": 3,
                "resolved_ref_hours": 2.0, "resolved_hours": 6.0,
            }],
        }],
    }
    env.update(over)
    return env

def _codes(findings):
    return {f.code for f in findings if not f.ok}

def test_clean_catalog_envelope_has_no_blocking():
    assert _codes(validate_envelope(_catalog_env())) == set()

def test_missing_project_number_rejects():
    assert "missing_project_number" in _codes(validate_envelope(_catalog_env(project_number=None)))

def test_non_catalog_line_rejects():
    env = _catalog_env()
    env["scopes"][0]["lines"][0]["line_kind"] = "service"
    assert "non_catalog_line" in _codes(validate_envelope(env))

def test_nonzero_service_total_rejects():
    env = _catalog_env()
    env["scopes"][0]["scope_totals"]["service_cents"] = 500
    assert "nonzero_service" in _codes(validate_envelope(env))

def test_nonzero_cost_total_rejects():
    env = _catalog_env()
    env["scopes"][0]["scope_totals"]["cost_cents"] = 500
    assert "nonzero_cost" in _codes(validate_envelope(env))

def test_m4_not_one_rejects():
    env = _catalog_env()
    env["scopes"][0]["replication_m4"] = 2
    assert "m4_unsupported" in _codes(validate_envelope(env))

def test_missing_required_catalog_field_rejects():
    env = _catalog_env()
    del env["scopes"][0]["lines"][0]["resolved_ref_hours"]
    assert "missing_required_catalog_field" in _codes(validate_envelope(env))

def test_invalid_line_state_rejects():
    env = _catalog_env()
    env["scopes"][0]["lines"][0]["line_kind"] = "not_a_kind"
    assert "invalid_line_state" in _codes(validate_envelope(env))

def test_findings_are_pm_dollar_safe():
    env = _catalog_env(project_number=None)
    for f in validate_envelope(env):
        assert "$" not in f.message
```

- [ ] **Step 2: Run to verify failure.**
Run: `ssh olares-mesh '...OPS_DEV_DSN=... .venv/bin/python -m pytest packages/ops-intake/tests/test_native_envelope.py -x -q'` (use the same env-var preamble as Task 2 Step 6.)
Expected: FAIL — `ModuleNotFoundError: No module named 'ops_intake.native'`.

- [ ] **Step 3: Implement `native.py` (validate only).** Create `packages/ops-intake/src/ops_intake/native.py` (R1-3: validate + helpers only — pivot + `recompute_content_hash` arrive in Task 4, no forward reference. R1-5: numeric guards use `Decimal`):
```python
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from .validate import Finding

NATIVE_SCHEMA_VERSION = "estimate_envelope_v1"
NATIVE_PARSER_VERSION = "estimator-core/c051c02"
_LINE_KINDS = {"catalog", "custom_equipment", "service", "cost"}
_REQUIRED_CATALOG_FIELDS = ("equipment_model_ref", "base_qty", "project_intake_qty", "resolved_ref_hours")


def _pm(msg: str) -> str:
    return msg.replace("$", "")


def _f(code, message, *, ok=False, severity="blocking", detail=None) -> Finding:
    return Finding(code=code, severity=severity, ok=ok, message=_pm(message), diagnostic_detail=detail)


def _dec(v):
    """Decimal(str(v)), or None if not numeric (None/'' -> None). Lets 1 == 1.0 and never truncates."""
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError):
        return None


def validate_envelope(env: dict) -> list[Finding]:
    """Catalog-only fail-closed gate (C3/C5/C7). Blocking findings, never a crash."""
    out: list[Finding] = []
    if not env.get("project_number"):
        out.append(_f("missing_project_number", "Envelope has no project number"))
    for i, sc in enumerate(env.get("scopes", []) or [], start=1):
        st = sc.get("scope_totals", {}) or {}
        svc_cents = _dec(st.get("service_cents", 0)) or Decimal(0)
        svc_hours = _dec(st.get("service_hours", 0)) or Decimal(0)   # R1-5: scope-level service_hours too
        if svc_cents != 0 or svc_hours != 0:
            out.append(_f("nonzero_service", f"Scope #{i} carries service work (not supported in v1)",
                          detail=f"scope={sc.get('scope_id')!r}"))
        if (_dec(st.get("cost_cents", 0)) or Decimal(0)) != 0:
            out.append(_f("nonzero_cost", f"Scope #{i} carries cost lines (not supported in v1)",
                          detail=f"scope={sc.get('scope_id')!r}"))
        m4 = _dec(sc.get("replication_m4"))
        if m4 is None or m4 != Decimal(1):   # R1-5: Decimal so 1.0 passes; 1.5/2 reject
            out.append(_f("m4_unsupported", f"Scope #{i} replication is not 1 (deferred)",
                          detail=f"replication_m4={sc.get('replication_m4')!r}"))
        for ln in sc.get("lines", []) or []:
            if not ln.get("included", True):
                continue
            kind = ln.get("line_kind")
            if kind not in _LINE_KINDS:
                out.append(_f("invalid_line_state", f"Scope #{i} has a line with an unknown kind",
                              detail=f"line_uid={ln.get('line_uid')!r}; line_kind={kind!r}"))
                continue
            if kind != "catalog":
                out.append(_f("non_catalog_line", f"Scope #{i} has a non-catalog line (not supported in v1)",
                              detail=f"line_uid={ln.get('line_uid')!r}; line_kind={kind!r}"))
                continue
            for fld in _REQUIRED_CATALOG_FIELDS:
                if ln.get(fld) in (None, ""):
                    out.append(_f("missing_required_catalog_field",
                                  f"Scope #{i} catalog line is missing a required field",
                                  detail=f"line_uid={ln.get('line_uid')!r}; field={fld}"))
    return out
```

- [ ] **Step 4: Run to verify the validate tests pass.**
Run: `ssh olares-mesh '...OPS_DEV_DSN=... .venv/bin/python -m pytest packages/ops-intake/tests/test_native_envelope.py -k "not pivot and not approve and not reconcile and not idempot" -q'`
Expected: the `validate_envelope` tests PASS.

- [ ] **Step 5: Commit.**
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git add packages/ops-intake/src/ops_intake/native.py packages/ops-intake/tests/test_native_envelope.py && git commit -m "feat(ops-intake): native envelope fail-closed validator (C3/C5/C7)"'
```

---

### Task 4: `native.pivot_to_intake_payload` (envelope → flat IntakePayload, Decimal money)

**Files:** Modify `packages/ops-intake/src/ops_intake/native.py`; extend `test_native_envelope.py`.

**Interfaces — Produces:** `pivot_to_intake_payload(env: dict) -> dict` — a plain dict shaped exactly like `dataclasses.asdict(IntakePayload)` (so `envelope._payload_from_dict` and `patch_review` consume it unchanged).

- [ ] **Step 1: Write failing pivot tests.** First extend the import at the top of `test_native_envelope.py` to `from ops_intake.native import validate_envelope, pivot_to_intake_payload, recompute_content_hash`, then append:
```python
def test_pivot_maps_catalog_line_fields():
    p = pivot_to_intake_payload(_catalog_env())
    assert p["project"]["project_number"] == "JOB-1"
    assert p["project"]["project_name"] == "JOB-1"              # Q-2 fallback to project_number
    assert p["project"]["contract_value"] == "1000.00"          # 100000 cents -> Decimal dollars
    s = p["scopes"][0]
    assert s["scope_name"] == "A1"
    assert s["quote"]["onsite_labor"] == "1000.00"
    assert s["quote"]["travel"] == "0" and s["quote"]["outside_services"] == "0"
    assert s["quote"]["unit_multiplier"] == "1" and s["quote"]["pct_adjust"] == "1"
    assert s["quote"]["total_quoted_hours"] == 6
    ln = s["lines"][0]
    assert ln["apparatus_type"] == "MV-CB-01"                   # model-key string (re-resolved at approve)
    assert ln["test_standard"] == "ATS"                         # scope.neta_standard fan-out
    assert ln["qty"] == 3                                       # base_qty (== project_intake_qty at M4==1)
    assert ln["hrs_per_unit"] == 2.0                            # resolved_ref_hours
    assert ln["catalog_default_hours"] == 2.0
    assert ln["line_uid"] == "S1:row1"
    assert ln["section"] is None                                # envelope has no section -> __ungrouped__

def test_pivot_output_is_intake_payload_shaped():
    from ops_intake.envelope import _payload_from_dict
    obj = _payload_from_dict(pivot_to_intake_payload(_catalog_env()))
    assert obj.project.project_number == "JOB-1"
    assert obj.scopes[0].lines[0].apparatus_type == "MV-CB-01"

def test_content_hash_is_deterministic_and_ignores_client_hash():
    a = recompute_content_hash(_catalog_env(content_hash="abc"))
    b = recompute_content_hash(_catalog_env(content_hash="DIFFERENT"))
    assert a == b and len(a) == 64
```

- [ ] **Step 2: Run to verify failure.** Same pytest invocation, `-k "pivot or content_hash"`. Expected: FAIL (`pivot_to_intake_payload` not defined).

- [ ] **Step 3: Implement the pivot + the content hash.** First add to the TOP of `native.py` the imports the pivot/hash need (R1-3): `import hashlib`, `import json`, `import dataclasses`, and `from .model import IntakePayload, ProjectIn, ScopeIn, ScopeQuoteIn, QuoteLineIn`. Then append:
```python
def _cents_to_dollars(cents) -> str:
    return str((Decimal(int(cents or 0)) / Decimal(100)).quantize(Decimal("0.01")))


def pivot_to_intake_payload(env: dict) -> dict:
    """Catalog-only pivot. Callers MUST validate_envelope() first (this is strict: it dereferences
    required catalog fields). Money: integer cents -> Decimal dollars (str-encoded, no float)."""
    pn = env.get("project_number")
    project = ProjectIn(
        project_number=pn,
        project_name=pn or "",                     # Q-2: envelope has no name; fall back to project_number
        contract_value=Decimal(int((env.get("totals", {}) or {}).get("bid_cents", 0) or 0)) / Decimal(100),
    )
    scopes = []
    for sc in env.get("scopes", []) or []:
        st = sc.get("scope_totals", {}) or {}
        quote = ScopeQuoteIn(
            onsite_labor=Decimal(int(st.get("onsite_labor_cents", 0) or 0)) / Decimal(100),
            offsite_labor=Decimal(int(st.get("offsite_labor_cents", 0) or 0)) / Decimal(100),
            travel=Decimal(0),
            outside_services=Decimal(0),
            unit_multiplier=Decimal(str(sc.get("replication_m4", 1))),
            pct_adjust=Decimal(str(sc.get("adjustment_multiplier_n4", 1))),
            total_quoted_hours=st.get("quoted_app_hours", 0),
        )
        lines = []
        for ln in sc.get("lines", []) or []:
            if not ln.get("included", True) or ln.get("line_kind") != "catalog":
                continue
            lines.append(QuoteLineIn(
                apparatus_type=ln["equipment_model_ref"],          # model-key; resolve_models -> uuid at approve
                test_standard=sc.get("neta_standard"),             # scope -> line fan-out
                qty=int(ln["base_qty"]),                           # == project_intake_qty at M4==1
                hrs_per_unit=ln["resolved_ref_hours"],
                catalog_default_hours=ln["resolved_ref_hours"],
                line_uid=ln.get("line_uid"),
                section=None,                                      # envelope has no section -> __ungrouped__ task
            ))
        scopes.append(ScopeIn(scope_name=sc["name"], scope_type="OTHER", sort_order=0, quote=quote, lines=lines))
    return json.loads(json.dumps(dataclasses.asdict(IntakePayload(project=project, scopes=scopes)), default=str))


def recompute_content_hash(env: dict) -> str:
    """Server-side idempotency hash over the pivoted economic payload (C6: never trust the client hash).
    Deterministic (sort_keys). Call only on a validated envelope (the pivot is strict)."""
    blob = json.dumps(pivot_to_intake_payload(env), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
```
*(The `json.loads(json.dumps(..., default=str))` round-trip encodes `Decimal` as strings and yields the same plain-dict shape `create_run` stores, so the `±1¢` test parses the stored strings back via `Decimal`.)*

- [ ] **Step 4: Run to verify pass.** Same pytest, `-k "pivot or content_hash"`. Expected: PASS.

- [ ] **Step 5: Commit.**
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git add packages/ops-intake/src/ops_intake/native.py packages/ops-intake/tests/test_native_envelope.py && git commit -m "feat(ops-intake): native envelope->IntakePayload pivot (Decimal money, C2/C7)"'
```

---

### Task 5: `envelope.create_run_native` (persist the native run)

**Files:** Modify `packages/ops-intake/src/ops_intake/envelope.py`; extend `test_native_envelope.py`.

**Interfaces — Consumes:** `native.validate_envelope`, `native.recompute_content_hash`, `native.pivot_to_intake_payload`, the existing `_classify_conflict`. **Produces:** `create_run_native(dsn, *, uploaded_by, envelope) -> dict` (same shape as `create_run`).

- [ ] **Step 1: Write failing persistence tests.** Append to `test_native_envelope.py`:
```python
import psycopg
from ops_intake.envelope import create_run_native

def _person(dsn):
    with psycopg.connect(dsn, autocommit=True) as c:
        return c.execute("insert into ops.persons (display_name) values ('N') returning person_id").fetchone()[0]

def test_create_run_native_persists_columns(clean_ops):
    dsn = clean_ops; who = _person(dsn)
    out = create_run_native(dsn, uploaded_by=who, envelope=_catalog_env())
    assert out["status"] == "parsed" and out["source_format"] == "native"
    with psycopg.connect(dsn) as c:
        row = c.execute(
            "select source_format, payload_schema_version, parser_version, envelope_id, quote_version,"
            " content_hash, source_draft_id, source_revision_id,"
            " canonical_payload_json = review_payload_json as same, estimate_envelope_json is not null as has_sidecar"
            " from ops.intake_runs where id=%s", (out["run_id"],)).fetchone()
    assert row[0] == "native" and row[1] == "estimate_envelope_v1" and row[3] == "env-1" and row[4] == 1
    assert row[8] is True            # canonical == review (C2: patch_review compatibility)
    assert row[9] is True            # raw envelope only in the sidecar

def test_create_run_native_rejects_non_catalog_without_domain_writes(clean_ops):
    dsn = clean_ops; who = _person(dsn)
    env = _catalog_env(); env["scopes"][0]["lines"][0]["line_kind"] = "service"
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "rejected"
    assert any(f["code"] == "non_catalog_line" and not f["ok"] for f in out["findings"])
    with psycopg.connect(dsn) as c:
        assert c.execute("select count(*) from ops.scopes").fetchone()[0] == 0   # no domain writes

def test_create_run_native_idempotent_on_content_hash(clean_ops):
    dsn = clean_ops; who = _person(dsn)
    create_run_native(dsn, uploaded_by=who, envelope=_catalog_env())
    import pytest
    from ops_intake.envelope import ActiveRunExists
    with pytest.raises((ActiveRunExists, psycopg.errors.UniqueViolation)):
        create_run_native(dsn, uploaded_by=who, envelope=_catalog_env())  # same content_hash
```

- [ ] **Step 2: Run to verify failure.** pytest `-k create_run_native`. Expected: FAIL (`create_run_native` undefined).

- [ ] **Step 3: Implement `create_run_native`.** Add to `envelope.py` (imports `from .native import validate_envelope, recompute_content_hash, pivot_to_intake_payload, NATIVE_SCHEMA_VERSION, NATIVE_PARSER_VERSION`):
```python
def create_run_native(dsn, *, uploaded_by, envelope):
    """Native (estimator) catalog-only envelope intake. Pivots to a flat IntakePayload, persists an
    intake_run (source_format='native') with canonical==review==pivoted and the raw envelope in the
    estimate_envelope_json sidecar. approve_run materializes it unchanged. Fail-closed: any blocking
    finding -> a GOVERNED rejected run with NO domain writes (mirrors _create_rejected_parse_envelope)."""
    findings = validate_envelope(envelope)
    blocking = [f for f in findings if f.severity == "blocking" and not f.ok]
    raw_json = json.dumps(envelope, default=str)
    pn = envelope.get("project_number") or ("UNRESOLVED:" + str(envelope.get("envelope_id") or "native"))[:200]
    # identity provenance cols are TOP-LEVEL envelope fields -> safe even for a malformed (rejected) envelope
    ev_id, qv = envelope.get("envelope_id"), envelope.get("quote_version")
    sdid, srid = envelope.get("source_draft_id"), envelope.get("source_revision_id")

    def _finding_rows(cur, run_id, version):
        for f in findings:
            cur.execute(
                "insert into ops.intake_validation_findings"
                " (run_id, payload_version, severity, code, ok, message, diagnostic_detail)"
                " values (%s,%s,%s,%s,%s,%s,%s)",
                (run_id, version, f.severity, f.code, f.ok, f.message, f.diagnostic_detail))

    if blocking:
        # R1-4: governed rejected run — NO advisory lock, NO domain writes, and NO strict pivot/hash
        # (they dereference required fields and would KeyError on a malformed envelope). canonical/review
        # = '{}' (not approvable); content_hash NULL (a reject never takes the idempotency index).
        with psycopg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "insert into ops.intake_runs (project_number, source_format, status, conflict_kind,"
                " payload_schema_version, parser_version, canonical_payload_json, review_payload_json,"
                " uploaded_by, envelope_id, quote_version, content_hash, source_draft_id,"
                " source_revision_id, estimate_envelope_json) values"
                " (%s,'native'::ops.intake_source_format,'rejected','none',%s,%s,'{}'::jsonb,'{}'::jsonb,"
                " %s,%s,%s,NULL,%s,%s,%s::jsonb) returning id",
                (pn, NATIVE_SCHEMA_VERSION, NATIVE_PARSER_VERSION, str(uploaded_by),
                 ev_id, qv, sdid, srid, raw_json))
            run_id = str(cur.fetchone()[0])
            _finding_rows(cur, run_id, 1)
            conn.commit()
        return {"run_id": run_id, "status": "rejected", "conflict_kind": "none", "source_format": "native",
                "findings": [{"code": f.code, "severity": f.severity, "ok": f.ok, "message": f.message} for f in findings]}

    # happy path: validate_envelope guaranteed catalog completeness, so the strict pivot/hash are safe now.
    content_hash = recompute_content_hash(envelope)
    pivoted_json = json.dumps(pivot_to_intake_payload(envelope), default=str)
    try:
        with psycopg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("select pg_advisory_xact_lock(hashtext(%s))", (pn,))
            project_id, conflict_kind = _classify_conflict(cur, pn)
            status = "revision_blocked" if conflict_kind != "none" else "parsed"
            if status == "parsed":
                cur.execute(
                    "update ops.intake_runs set status='superseded'::ops.intake_run_status, updated_at=now()"
                    " where project_number=%s and status in ('parsed'::ops.intake_run_status,'reviewing'::ops.intake_run_status)",
                    (pn,))
            cur.execute(
                "insert into ops.intake_runs (project_number, project_id, source_format, status, conflict_kind,"
                " payload_schema_version, parser_version, canonical_payload_json, review_payload_json,"
                " uploaded_by, envelope_id, quote_version, content_hash, source_draft_id,"
                " source_revision_id, estimate_envelope_json) values"
                " (%s,%s,'native'::ops.intake_source_format,%s::ops.intake_run_status,%s::ops.intake_conflict_kind,"
                " %s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s,%s::jsonb) returning id",
                (pn, project_id, status, conflict_kind, NATIVE_SCHEMA_VERSION, NATIVE_PARSER_VERSION,
                 pivoted_json, pivoted_json, str(uploaded_by), ev_id, qv, content_hash, sdid, srid, raw_json))
            run_id = str(cur.fetchone()[0])
            _finding_rows(cur, run_id, 1)
            conn.commit()
    except psycopg.errors.UniqueViolation as exc:
        if "uq_intake_one_active" in str(exc) or "uq_intake_runs_content_hash_native" in str(exc):
            raise ActiveRunExists("An active/duplicate native run already exists for " + repr(pn)) from exc
        raise
    return {"run_id": run_id, "status": status, "conflict_kind": conflict_kind, "source_format": "native",
            "findings": [{"code": f.code, "severity": f.severity, "ok": f.ok, "message": f.message} for f in findings],
            "review_payload": json.loads(pivoted_json)}
```

- [ ] **Step 4: Run to verify pass.** pytest `-k create_run_native`. Expected: PASS.

- [ ] **Step 5: Commit.**
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git add packages/ops-intake/src/ops_intake/envelope.py packages/ops-intake/tests/test_native_envelope.py && git commit -m "feat(ops-intake): create_run_native (governed reject + native columns, C1-C6)"'
```

---

### Task 6: End-to-end approve + `±1¢` reconciliation + patch_review compatibility

**Files:** Extend `packages/ops-intake/tests/test_native_envelope.py` (no production code — proves the seam against the unchanged `approve_run`).

**Interfaces — Consumes:** `create_run_native`, `approve_run`, the live `ops.*` schema. Uses a catalog model-key that exists in `core.equipment_models` (resolve it from the seed; the `008` seed key `"Capcitors - Per Unit"` is used by `test_approve_envelope.py`).

- [ ] **Step 1: Write the e2e + reconciliation test.** Append:
```python
from decimal import Decimal
from ops_intake.approve import approve_run

def _seeded_env(model_key="Capcitors - Per Unit"):
    env = _catalog_env()
    env["scopes"][0]["lines"][0]["equipment_model_ref"] = model_key
    return env

def test_native_approve_materializes_and_reconciles(clean_ops):
    dsn = clean_ops; who = _person(dsn)
    env = _seeded_env()
    out = create_run_native(dsn, uploaded_by=who, envelope=env)
    assert out["status"] == "parsed", out["findings"]
    res = approve_run(dsn, out["run_id"], approved_by=who)
    assert res["outcome"] == "approved", res
    with psycopg.connect(dsn) as c:
        # exact projection: 3 apparatus (base_qty=3, M4=1), one scope_quote_line, frozen quote
        assert c.execute("select count(*) from ops.apparatus").fetchone()[0] == 3
        assert c.execute("select count(*) from ops.scope_quote_line").fetchone()[0] == 1
        assert c.execute("select bool_and(is_frozen) from ops.scope_quote").fetchone()[0] is True
        assert c.execute("select status from ops.intake_runs where id=%s", (out["run_id"],)).fetchone()[0] == "approved"
        # +/-1c reconciliation: envelope bid_cents vs sum(scope_quote.adjusted_total)
        adj = c.execute("select coalesce(sum(adjusted_total),0) from ops.scope_quote").fetchone()[0]
    bid = Decimal(env["totals"]["bid_cents"]) / Decimal(100)
    assert abs(Decimal(adj) - bid) <= Decimal("0.01"), (adj, bid)

def test_native_patch_review_compatible(clean_ops):
    """canonical==review flat shape -> patch_review's allowlist accepts an editable-field change."""
    dsn = clean_ops; who = _person(dsn)
    from ops_intake.envelope import get_run, patch_review
    out = create_run_native(dsn, uploaded_by=who, envelope=_seeded_env())
    run = get_run(dsn, out["run_id"])
    review = run["review_payload"]
    review["scopes"][0]["lines"][0]["hrs_per_unit"] = 2.5    # _LINE_MUTABLE field -> allowed
    patched = patch_review(dsn, out["run_id"], review_payload=review)
    assert patched["review_payload_version"] == 2
```

- [ ] **Step 2: Run to verify.** pytest `-k "native_approve or patch_review_compatible"`. Expected: PASS. *(If `±1¢` fails, the divergence is a real defect — float leak or a basis error per C7, not a tolerance to widen; debug with `superpowers:systematic-debugging`.)*

- [ ] **Step 3: Run the full ops-intake suite (no regressions).**
Run: `ssh olares-mesh '...OPS_DEV_DSN=... .venv/bin/python -m pytest packages/ops-intake/tests/ -q'`
Expected: all green (existing workbook tests + the new native tests).

- [ ] **Step 4: Commit.**
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git add packages/ops-intake/tests/test_native_envelope.py && git commit -m "test(ops-intake): native approve e2e + ±1c reconciliation + patch_review compat"'
```

---

### Task 7: API endpoint `POST /api/v1/ops/intake/native`

**Files:** Modify `apps/control-plane-api/services/ops/intake_router.py`.

**Interfaces — Consumes:** `create_run_native`, `_dsn`, `_pm_findings`.

- [ ] **Step 1: Extend the real harness + write the failing route test.** R1-7: add this to the EXISTING `apps/control-plane-api/tests/test_ops_intake_routes.py`, reusing its `apply_migrations`/`client`/`person_id` fixtures + the `_contains_substring` helper. First extend that file's `apply_migrations`: append `"010_native_envelope_intake.sql"` to `up_migrations`; in the post-`yield` teardown add (before the `008` down) `c.execute("delete from ops.intake_runs")` then `_run_sql(c, mig_dir / "010_native_envelope_intake_down.sql")`; and in the pre-up reset add the same delete + `010` down before the `008` down. Then append:
```python
def _catalog_envelope():
    return {
        "project_number": "API-1", "envelope_id": "api-env-1", "quote_version": 1,
        "source_draft_id": "d", "source_revision_id": "r",
        "totals": {"bid_cents": 165000, "service_hours": 0},
        "scopes": [{
            "scope_id": "S1", "name": "A1", "neta_standard": "ATS",
            "replication_m4": 1, "adjustment_multiplier_n4": 1,
            "scope_totals": {"onsite_labor_cents": 165000, "offsite_labor_cents": 0,
                             "cost_cents": 0, "service_cents": 0, "service_hours": 0,
                             "quoted_app_hours": 10, "adjusted_cents": 165000},
            "lines": [{"line_uid": "S1:r1", "line_kind": "catalog", "included": True,
                       "equipment_model_ref": "Capcitors - Per Unit", "base_qty": 1,
                       "project_intake_qty": 1, "resolved_ref_hours": 10.0}],
        }],
    }


class TestNativeIntake:
    """POST /api/v1/ops/intake/native"""

    def test_native_returns_200_pm_safe(self, client, person_id):
        resp = client.post("/api/v1/ops/intake/native",
                           json={"uploaded_by": person_id, "envelope": _catalog_envelope()})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["source_format"] == "native" and body["status"] == "parsed"
        assert not _contains_substring(body, "$")               # finance redaction
        for f in body["findings"]:
            assert set(f) == {"code", "severity", "ok", "message"}   # no diagnostic_detail

    def test_native_non_catalog_rejected(self, client, person_id):
        env = _catalog_envelope(); env["scopes"][0]["lines"][0]["line_kind"] = "service"
        resp = client.post("/api/v1/ops/intake/native",
                           json={"uploaded_by": person_id, "envelope": env})
        assert resp.status_code == 200, resp.text          # a governed reject is 200 with status='rejected'
        assert resp.json()["status"] == "rejected"
```

- [ ] **Step 2: Run to verify failure.** Run (with the `ops_test` DSN preamble from Task 2 Step 6): `… .venv/bin/python -m pytest apps/control-plane-api/tests/test_ops_intake_routes.py -k Native -x -q`. Expected: FAIL (404 — route not mounted).

- [ ] **Step 3: Implement the route.** In `intake_router.py`, import `create_run_native` from `ops_intake.envelope` and add:
```python
@router.post("/native", status_code=status.HTTP_200_OK)
async def upload_native_envelope(request: Request) -> JSONResponse:
    """Create a native (estimator) intake run from a compiled EstimateEnvelope (catalog-only v1).
    Body: {uploaded_by: uuid, envelope: <EstimateEnvelope JSON>}. Returns the PM-safe run summary."""
    body: dict[str, Any] = await request.json()
    uploaded_by = body.get("uploaded_by")
    envelope = body.get("envelope")
    if not uploaded_by or not isinstance(envelope, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="uploaded_by and envelope (object) are required")
    try:
        result = create_run_native(_dsn(), uploaded_by=uploaded_by, envelope=envelope)
    except ActiveRunExists as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except psycopg.errors.ForeignKeyViolation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="uploaded_by is not a known person")
    return JSONResponse({
        "run_id": result["run_id"], "status": result["status"],
        "conflict_kind": result["conflict_kind"], "source_format": result["source_format"],
        "findings": _pm_findings(result["findings"]),
    })
```

- [ ] **Step 4: Run to verify pass.** Same pytest. Expected: PASS.

- [ ] **Step 5: Commit.**
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git add apps/control-plane-api/services/ops/intake_router.py apps/control-plane-api/tests/test_ops_intake_routes.py && git commit -m "feat(control-plane-api): POST /ops/intake/native (PM-safe native envelope intake)"'
```

---

### Task 8: Whole-branch review + finish (operator-gated)

**Files:** none (review + finish only).

- [ ] **Step 1:** Run the full ops-intake + migration suite once more, green.
- [ ] **Step 2:** Whole-branch review — `superpowers:requesting-code-review` (opus) + the **Codex cross-engine pass** (`apex-jobs review-run --review-head estimator/envelope-ops-mapping --base-ref main`); fold findings.
- [ ] **Step 3:** `superpowers:finishing-a-development-branch` — present options. **Merge to `main` and the `ops_dev` apply are OPERATOR-GATED** (do not merge/apply without an explicit go). **Prod stays BLOCKED behind the `ops_app` role-boundary gate.**

---

## Open decisions to surface (with leans)

- **C6 exact-match (Task 3 note):** v1 uses a server-side recompute for idempotency (never trusts the client hash). *Lean: ship that; add exact-match verification of the envelope's own `content_hash` (port `content-hash.ts`) as a fast-follow only if finance wants the integrity cross-check.*
- **Q-2 `project_name` (Task 4):** falls back to `project_number` (the envelope has no name). *Lean: accept for v1; wire the draft display-name when the native UI lands.*
- **Optional Task 3b — exact-match content_hash:** port estimator-core's canonical-economic-content hash to Python so `content_hash_mismatch` becomes a real integrity gate. Include now only on request.

## Self-Review

**Spec coverage (C1–C7):** C1 = Task 2 (enum `add value`, no `source_kind`, partial indexes on `source_format='native'`, real down rebuild). C2 = Task 4/5 (flat `IntakePayload` in canonical+review; raw in `estimate_envelope_json`) + Task 6 (`patch_review` compat test). C3 = Task 3 (`missing_project_number`). C4 = Task 2 (trigger extension + drift tests). C5 = Task 3 (`missing_required_catalog_field`, `invalid_line_state`). C6 = Task 4 (server recompute; exact-match flagged). C7 = Task 3 (`m4_unsupported`, Decimal) + Task 4 (M4==1 mapping) + Task 6 (`±1¢`). Global constraints (Decimal money, PM-safe findings, ops_test, operator-gated) covered in Tasks 3/4/6/8. **No gap found.**

**Placeholder scan:** every code step carries real code; commands use the `ops_test` DSN preamble; no "TBD"/"handle edge cases". (R1-3 removed the earlier Task-3→Task-4 forward reference — `recompute_content_hash` and the pivot now both live in Task 4, so Task 3 imports/defines only `validate_envelope`.)

**Type consistency:** `Finding(code, severity, ok, message, diagnostic_detail)` used consistently; `create_run_native` returns the `create_run` dict shape; pivot output is `IntakePayload`-shaped (verified by `_payload_from_dict` in Task 4). `apparatus_type` carries the model-key string in both pivot and `load.insert_scope_quote_line`/`insert_apparatus`, matching `resolve_models`.
