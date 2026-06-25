# Estimator Native Renderer (`/estimator`) + Line-Metadata Promotion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a thin `/estimator` authoring screen that compiles an ephemeral estimate draft via `@apex/estimator-core`, submits it to the native intake API (`POST /native` → `POST /{run_id}/approve`), and surfaces the resulting project in the recognition lifecycle — and promote line `description` (alongside the already-present `designation`/`notes`) end-to-end from the draft grid through to `ops.scope_quote_line`.

**Architecture:** Two coupled slices on lane `estimator/native-renderer` (host worktree `/home/olares/code/apex/apex-estimator-renderer`, HEAD `a1ae8a82` on `main 767e37ef`).
- **Slice A — metadata promotion:** thread three line-metadata fields (`designation`, `notes`, `description`) through estimator-core (`LineDraft`/`LineC`/`compile`), the native pivot (`native.py`), the loader (`load.py`), and one additive migration (`011`, **`description` column only** — `designation`+`notes` already exist on `ops.scope_quote_line` from mig 002).
- **Slice B — renderer UI:** an estimator-core authoring helper (`buildNativeEnvelope`, pure + vitest-tested) plus `apps/operations-web/lib/estimator.ts` and `apps/operations-web/app/estimator/page.tsx` that build the draft, compile+validate, force `project_number = DEMO-NATIVE-001`, and drive native → approve.

**Tech Stack:** TypeScript / Next 16 (operations-web, `transpilePackages: ['@apex/estimator-core']`); `@apex/estimator-core` (source-only ESM, vitest); Python 3 / psycopg (ops-intake, pytest); PostgreSQL (ops migrations); pnpm@10 workspaces.

## Global Constraints

- **TDD where a runner exists.** estimator-core → `vitest run`; ops-intake + migrations → `pytest` on throwaway **`ops_test`**. **operations-web has NO unit-test runner** (scripts: dev/build/start/typecheck/smoke:*) — Slice B UI tasks (`lib/estimator.ts`, `page.tsx`) are verified by `pnpm --filter operations-web typecheck` + `build`; behavioral proof is the Task 7 hosted smoke. All economic/metadata logic lives in estimator-core (vitest) — NOT in operations-web.
- **NEVER run the migration + package + API suites in one combined or parallel pytest invocation against `ops_test`** — their session-scoped fixtures collide on `pg_namespace`. Run each suite sequentially.
- **Demo data discipline (load-bearing):** `approve_run` is FULL-REPLACEMENT, scoped to `delete from ops.scopes where project_id=%s and source='ops-intake'` (cascade). The UI MUST hard-pin `project_number` to **`DEMO-NATIVE-001`** (the reserved live-demo project). The **Task 7 hosted smoke MUST use a DISPOSABLE project (`DEMO-RENDERER-SMOKE-001`), NOT `DEMO-NATIVE-001` and NEVER `MINER-PHX-AB-MV`** — a `/native→/approve` freezes a project, so burning `DEMO-NATIVE-001` in CI would block the operator's live demo (a 2nd native run vs a frozen/approved project returns `revision_blocked`/409).
- **Metadata fields are economic-NEUTRAL.** They MUST NOT enter `content_hash` (preview must equal approved). `content-hash.ts::lineToken` is a FIXED explicit array — adding fields to `LineC` does NOT auto-include them. Keep it that way; Task 1 adds a regression test proving hash-stability.
- **Migration 011 is additive + reversible** (`description text` add; down drops it). Conftest chain extends to 011. Mirror the existing `test_010_native_envelope_intake.py` harness structure.
- **Merge to main + ops_dev apply are OPERATOR-GATED; prod BLOCKED behind the `ops_app` role boundary.** All host work over `ssh olares-mesh`. `DEV_PG_PASSWORD` sourced from governed `infra/.env` via `set -a; . infra/.env; set +a` — NEVER echo/print/log/interpolate it or an expanded DSN. Verify pytest by exit code, not `| tail` masking.
- **No float money in UI logic** — money is integer cents via estimator-core primitives; a compiled envelope reconciles by construction.

**Host command preamble (every host task):** read/run via `ssh olares-mesh '...'`. Node toolchain: `export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH` (node v20.20.2, pnpm 10.0.0). Worktree: `/home/olares/code/apex/apex-estimator-renderer`. For ops_test pytest: `export OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"` after sourcing `infra/.env` (the conftest `_require_ops_test` guard rejects any non-`ops_test` dbname).

---

## File Structure

**Slice A:**
- Modify `packages/estimator-core/src/schema/draft.ts` — `LineDraft += description?: string`.
- Modify `packages/estimator-core/src/schema/envelope.ts` — `LineC += designation/notes/description: string | null`.
- Modify `packages/estimator-core/src/compile/compile.ts` — `emptyLineC` passes the three through.
- Create/extend `packages/estimator-core/src/compile/metadata.test.ts` — compile carry + hash-stability.
- Create `infra/database/migrations/ops/011_scope_quote_line_description.sql` + `_down.sql`.
- Create `infra/database/migrations/ops/test_011_scope_quote_line_description.py`.
- Modify `packages/ops-intake/tests/conftest.py` — chain to 011 (up list + both down sequences).
- Modify `infra/database/migrations/ops/MANIFEST.md` — 011 row.
- Modify `packages/ops-intake/src/ops_intake/model.py` — `QuoteLineIn += description`.
- Modify `packages/ops-intake/src/ops_intake/native.py` — pivot sets designation/notes/description.
- Modify `packages/ops-intake/src/ops_intake/load.py` — INSERT adds `notes`, `description`.
- Create `packages/ops-intake/tests/test_native_metadata.py` — envelope→approve survival.

**Slice B:**
- Create `packages/estimator-core/src/authoring/build-native-envelope.ts` + `.test.ts`.
- Modify `packages/estimator-core/src/index.ts` — export the authoring helper + `EQUIPMENT_MODELS_SEED` + `createDefaultCatalogResolver`.
- Create `apps/operations-web/lib/estimator.ts` — native client + force-project wiring.
- Create `apps/operations-web/app/estimator/page.tsx` — thin authoring screen.
- Modify the `/pm-review` nav component — add an `/estimator` link (mirror the #80 recognition link).
- Create `apps/operations-web/scripts/smoke-estimator-native.mjs` — hosted smoke against ops_dev (disposable project).

---

## Interfaces (cross-task contract)

- `LineDraft` gains `description?: string` (already has `designation?`, `notes?`).
- `LineC` gains `designation: string | null`, `notes: string | null`, `description: string | null`.
- `QuoteLineIn` gains `description: str | None = None` (already has `designation`, `notes`).
- `ops.scope_quote_line` gains `description text` (already has `designation varchar`, `notes text`).
- estimator-core exports: `buildNativeEnvelope(input: NativeEnvelopeInput): { envelope: EstimateEnvelope; findings: Finding[] }`, `EQUIPMENT_MODELS_SEED: EquipmentModel[]`, `createDefaultCatalogResolver(): CatalogResolver`.
- `lib/estimator.ts` exports: `submitNative(envelope, uploadedBy): Promise<NativeRunResult>`, `approveRun(runId, approvedBy): Promise<{status,run_id}>`, `DEMO_PROJECT_NUMBER = 'DEMO-NATIVE-001'`.

---

### Task 1: estimator-core — line metadata fields + compile pass-through + hash-stability

**Files:**
- Modify: `packages/estimator-core/src/schema/draft.ts` (LineDraft, ~line 13-14)
- Modify: `packages/estimator-core/src/schema/envelope.ts` (LineC, after `line_kind` ~line 16)
- Modify: `packages/estimator-core/src/compile/compile.ts` (`emptyLineC`, ~lines 32-64)
- Test: `packages/estimator-core/src/compile/metadata.test.ts` (new)

**Interfaces:**
- Produces: `LineDraft.description?`, `LineC.{designation,notes,description}: string|null`, and the guarantee that these are **excluded from `content_hash`** (Task 4 + Slice B rely on this).

- [ ] **Step 1: Write the failing test** — `packages/estimator-core/src/compile/metadata.test.ts`. Model the draft + resolver setup on `src/compile/compile.test.ts` (which does `import seed from '../catalog/equipment-models.seed.json'` and `createCatalogResolver(seed)`). Pick a real catalog `ref` from the seed that is valid for `ATS` (e.g. one used in `compile.test.ts`).

```typescript
import { describe, expect, it } from 'vitest'
import seed from '../catalog/equipment-models.seed.json'
import { createCatalogResolver } from '../catalog/resolver'
import { compile } from './compile'
import { computeContentHash } from './content-hash'
import { makeDraft } from '../schema/draft'
import type { EquipmentModel } from '../catalog/types'
import type { LineDraft } from '../schema/draft'

const resolver = createCatalogResolver(seed as EquipmentModel[])
const REF = (seed as EquipmentModel[]).find((m) => m.lifecycle_status === 'active' && m.ref_hours.ATS != null)!.ref

function draftWith(meta: Partial<Pick<LineDraft, 'designation' | 'notes' | 'description'>>) {
  return makeDraft({
    draft_id: 'd1',
    estimator_ref: 'e1',
    scopes: [{
      scope_id: 'S1', name: 'Scope A', neta_standard: 'ATS',
      replication_m4: 1, adjustment_multiplier_n4: 1,
      lines: [{ line_uid: 'S1:r1', line_kind: 'catalog', included: true, equipment_model_ref: REF, base_qty: 2, ...meta }],
      labor_allocation: [],
    }],
  })
}

describe('line metadata promotion', () => {
  it('compile carries designation/notes/description onto LineC', () => {
    const env = compile(draftWith({ designation: 'D-1', notes: 'n', description: 'CB tested' }), 'r1', resolver)
    const line = env.scopes[0].lines[0]
    expect(line.designation).toBe('D-1')
    expect(line.notes).toBe('n')
    expect(line.description).toBe('CB tested')
  })

  it('metadata is economic-neutral: content_hash is identical regardless of the three fields', () => {
    const a = compile(draftWith({}), 'r1', resolver)
    const b = compile(draftWith({ designation: 'D-9', notes: 'whatever', description: 'long text here' }), 'r1', resolver)
    expect(computeContentHash(a)).toBe(computeContentHash(b))
    expect(a.content_hash).toBe(b.content_hash)
  })
})
```

(If `makeDraft`'s scope/line input shape differs from the above, read `src/schema/draft.ts::makeDraft` and `ScopeDraft` and adapt the literal — the assertions are the contract.)

- [ ] **Step 2: Run test to verify it fails**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm --filter @apex/estimator-core test -- metadata 2>&1 | tail -30'`
Expected: FAIL — `line.description` is `undefined` (and likely a TS error: `description` not on `LineDraft`/`LineC`).

- [ ] **Step 3: Add `description` to `LineDraft`** in `src/schema/draft.ts`, immediately after `notes?: string`:

```typescript
  designation?: string
  notes?: string
  description?: string
```

- [ ] **Step 4: Add the three fields to `LineC`** in `src/schema/envelope.ts`, immediately after `line_kind: LineKind`:

```typescript
export interface LineC {
  line_uid: string
  line_kind: LineKind
  designation: string | null
  notes: string | null
  description: string | null
  included: boolean
  // ... rest unchanged
```

- [ ] **Step 5: Pass the three through in `emptyLineC`** (`src/compile/compile.ts`), adding to the returned object (placement is free — the hash array is explicit):

```typescript
    line_uid: d.line_uid,
    line_kind: d.line_kind,
    designation: d.designation ?? null,
    notes: d.notes ?? null,
    description: d.description ?? null,
    included: d.included,
    // ... rest unchanged
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm --filter @apex/estimator-core test 2>&1 | tail -20'`
Expected: PASS — all suites (the existing 64 + the new 2) green. **Do NOT touch `content-hash.ts`** — the existing `lineToken` array already excludes the new fields; the hash-stability test proves it.

- [ ] **Step 7: Typecheck**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm --filter @apex/estimator-core typecheck'`
Expected: exit 0.

- [ ] **Step 8: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && git add packages/estimator-core/src && git commit -m "feat(estimator-core): line designation/notes/description through compile, excluded from content_hash"'
```

---

### Task 2: migration 011 — `ops.scope_quote_line.description` (additive) + conftest chain + MANIFEST

**Files:**
- Create: `infra/database/migrations/ops/011_scope_quote_line_description.sql`
- Create: `infra/database/migrations/ops/011_scope_quote_line_description_down.sql`
- Create: `infra/database/migrations/ops/test_011_scope_quote_line_description.py`
- Modify: `packages/ops-intake/tests/conftest.py`
- Modify: `infra/database/migrations/ops/MANIFEST.md`

**Interfaces:**
- Produces: `ops.scope_quote_line.description text` (nullable). Task 3's INSERT depends on this column existing on `ops_test`.

- [ ] **Step 1: Write the migration test** — `test_011_scope_quote_line_description.py`. Mirror the harness style of the existing `test_010_native_envelope_intake.py` (read it first for the exact `_apply`/`_revert` helper + connection pattern). The behavioral assertions:

```python
import os, pathlib, psycopg

MIG = pathlib.Path(__file__).resolve().parent
def _dsn():
    return os.environ["OPS_DEV_DSN"]  # conftest guard ensures ops_test

def _col(conn):
    return conn.execute(
        "select data_type from information_schema.columns "
        "where table_schema='ops' and table_name='scope_quote_line' and column_name='description'"
    ).fetchone()

def test_description_present_after_chain():
    # conftest applied the full 001..011 chain at session scope
    with psycopg.connect(_dsn()) as c:
        row = _col(c)
    assert row is not None and row[0] == 'text'

def test_011_reversible():
    # down drops it, up re-adds it; leave the column present (matches session chain state)
    with psycopg.connect(_dsn(), autocommit=True) as c:
        c.execute((MIG / '011_scope_quote_line_description_down.sql').read_text(encoding='utf-8'))
        assert _col(c) is None
        c.execute((MIG / '011_scope_quote_line_description.sql').read_text(encoding='utf-8'))
        assert _col(c) is not None
```

- [ ] **Step 2: Run it to verify it fails**

Run (source env first): `ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && set -a; . infra/.env; set +a; export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH; export OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"; cd infra/database/migrations/ops && uv run --with "psycopg[binary]" --with pytest pytest test_011_scope_quote_line_description.py -q; echo EXIT=$?'`
Expected: FAIL / collection error — the `.sql` files don't exist yet (and the column is absent).

- [ ] **Step 3: Write the up migration** — `011_scope_quote_line_description.sql`:

```sql
-- 011_scope_quote_line_description.sql
-- Additive: line-level free-text `description` on ops.scope_quote_line.
-- `designation` (varchar) and `notes` (text) already exist from 002 — this adds the THIRD
-- distinct grid column. Reversible. Chips 1-10 survive DOWN. Nothing to prod (ops_app gate).
alter table ops.scope_quote_line
  add column if not exists description text;
```

- [ ] **Step 4: Write the down migration** — `011_scope_quote_line_description_down.sql`:

```sql
-- 011_scope_quote_line_description_down.sql
-- Reverse of 011. Drops the description column (and any data in it — acceptable: dev/ops_test only).
alter table ops.scope_quote_line
  drop column if exists description;
```

- [ ] **Step 5: Extend the conftest migration chain** (`packages/ops-intake/tests/conftest.py`). Three edits:

(a) In `up_migrations` list, append after `"010_native_envelope_intake.sql"`:
```python
        "010_native_envelope_intake.sql",
        "011_scope_quote_line_description.sql",
    ]
```
(b) In the **pre-up reset** block, add the 011 down BEFORE the 010 down (downs run newest-first):
```python
        if _ops_schema_exists(c):
            c.execute("delete from ops.intake_runs")  # R1-2: clear native rows so 010 down's data-loss guard passes
            _run_sql(c, mig_dir / "011_scope_quote_line_description_down.sql")
            _run_sql(c, mig_dir / "010_native_envelope_intake_down.sql")
            _run_sql(c, mig_dir / "009_recognition_bridge_down.sql")
```
(c) In the **teardown** block (after `yield`), make the identical change (add the 011 down line before the 010 down line).

- [ ] **Step 6: Run the migration test to verify it passes**

Run the same command as Step 2. Expected: 2 passed, EXIT=0. (The conftest in `infra/database/migrations/ops/` for these `test_0NN` files governs the chain — if these migration tests use the package conftest, the chain edit in Step 5 covers them; if they use a local conftest, mirror the chain there too. Read how `test_010` bootstraps the schema and match it.)

- [ ] **Step 7: Add the MANIFEST row** — in `infra/database/migrations/ops/MANIFEST.md`, after the 010 row:

```
| 011 | `011_scope_quote_line_description.sql` | `011_scope_quote_line_description_down.sql` | additive `description text` column on `ops.scope_quote_line` (line-level free-text; `designation`+`notes` already exist from 002 — completes the 3 distinct grid columns). Reversible — Chips 1–10 survive DOWN. | Estimator native renderer / metadata promotion | validated on `ops_test`; dev-only (prod blocked behind `ops_app` gate). |
```

- [ ] **Step 8: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && git add infra/database/migrations/ops packages/ops-intake/tests/conftest.py && git commit -m "feat(ops/mig-011): additive ops.scope_quote_line.description + conftest chain to 011"'
```

---

### Task 3: ops-intake — thread metadata through pivot + loader (envelope → ops.scope_quote_line)

**Files:**
- Modify: `packages/ops-intake/src/ops_intake/model.py` (`QuoteLineIn`)
- Modify: `packages/ops-intake/src/ops_intake/native.py` (`pivot_to_intake_payload`)
- Modify: `packages/ops-intake/src/ops_intake/load.py` (`insert_scope_quote_line`)
- Test: `packages/ops-intake/tests/test_native_metadata.py` (new)

**Interfaces:**
- Consumes: `ops.scope_quote_line.description` (Task 2).
- Produces: native envelope line `designation`/`notes`/`description` land in the materialized `ops.scope_quote_line` row after `approve_run`.

- [ ] **Step 1: Write the failing survival test** — `packages/ops-intake/tests/test_native_metadata.py`. Reuse the valid reconciling envelope template `_catalog_env` from `tests/test_native_envelope.py` (import or copy it), add the three metadata keys to its line, run the real create→approve path, assert the row.

```python
import copy, psycopg
from ops_intake.native import create_run_native
from ops_intake.approve import approve_run
from ops_intake.tests.test_native_envelope import _catalog_env  # or copy the literal if not importable

PM = "0a000000-0000-4000-8000-000000000001"  # ops.persons PK on ops_test seed; if absent, insert one in the test

def test_native_metadata_lands_in_scope_quote_line(clean_ops):
    dsn = clean_ops
    env = copy.deepcopy(_catalog_env())  # _catalog_env may be a dict literal or factory — adapt
    line = env["scopes"][0]["lines"][0]
    line["designation"] = "CB-12"
    line["notes"] = "torque verified"
    line["description"] = "Medium-voltage breaker, primary injection"
    run = create_run_native(dsn, uploaded_by=PM, envelope=env)
    assert run["status"] == "parsed", run["findings"]
    res = approve_run(dsn, run["run_id"], approved_by=PM)
    assert res["outcome"] == "approved", res
    with psycopg.connect(dsn) as c:
        row = c.execute(
            "select designation, notes, description from ops.scope_quote_line "
            "where source='ops-intake' and legacy_source_id=%s",
            (line["line_uid"],),
        ).fetchone()
    assert row == ("CB-12", "torque verified", "Medium-voltage breaker, primary injection")
```

(Confirm `_catalog_env`'s real shape/exports by reading `tests/test_native_envelope.py`; ensure the chosen `equipment_model_ref` resolves on `ops_test` and a valid `ops.persons` row exists — insert one in the test if the fixture doesn't seed `PM`.)

- [ ] **Step 2: Run it to verify it fails**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && set -a; . infra/.env; set +a; export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH; export OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"; cd packages/ops-intake && uv run pytest tests/test_native_metadata.py -q; echo EXIT=$?'`
Expected: FAIL — `notes`/`description` come back `None` (the pivot doesn't set them and the INSERT omits them).

- [ ] **Step 3: Add `description` to `QuoteLineIn`** (`model.py`), after `notes`:

```python
    designation: str | None = None
    notes: str | None = None
    description: str | None = None
```

- [ ] **Step 4: Set the three fields in the pivot** (`native.py::pivot_to_intake_payload`, the `lines.append(QuoteLineIn(...))` block) — add to the constructor call:

```python
            lines.append(QuoteLineIn(
                apparatus_type=ln["equipment_model_ref"],
                test_standard=sc.get("neta_standard"),
                qty=int(_dec(ln["base_qty"])),
                hrs_per_unit=_rrh,
                catalog_default_hours=_rrh,
                line_uid=ln.get("line_uid"),
                section=None,
                designation=ln.get("designation"),
                notes=ln.get("notes"),
                description=ln.get("description"),
            ))
```

- [ ] **Step 5: Add `notes` + `description` to the INSERT** (`load.py::insert_scope_quote_line`):

```python
    return cur.execute(
        """
        insert into ops.scope_quote_line (scope_id, apparatus_type, test_standard, qty,
            hrs_per_unit, catalog_default_hours, designation, notes, description, line_number,
            source, legacy_source_id, provenance_status)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'draft')
        returning id
        """,
        (
            scope_id,
            line["apparatus_type"],
            line.get("test_standard"),
            line.get("qty", 1),
            line["hrs_per_unit"],
            line.get("catalog_default_hours"),
            line.get("designation"),
            line.get("notes"),
            line.get("description"),
            line.get("line_number"),
            _SOURCE,
            line.get("line_uid"),
        ),
    ).fetchone()[0]
```

(Placeholder/column count check: 13 columns, 12 `%s` + literal `'draft'`, values tuple has 12 entries.)

- [ ] **Step 6: Run the survival test — passes**

Run the Step 2 command. Expected: 1 passed, EXIT=0.

- [ ] **Step 7: Regression — run the full ops-intake package suite** (proves nothing else broke; SEQUENTIAL, not combined with the migration tests)

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && set -a; . infra/.env; set +a; export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH; export OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable"; cd packages/ops-intake && uv run pytest -q; echo EXIT=$?'`
Expected: all pass, EXIT=0.

- [ ] **Step 8: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && git add packages/ops-intake && git commit -m "feat(ops-intake): thread line designation/notes/description native pivot -> load -> ops.scope_quote_line"'
```

---

### Task 4: estimator-core — `buildNativeEnvelope` authoring helper + seed/default-resolver exports

**Files:**
- Create: `packages/estimator-core/src/authoring/build-native-envelope.ts`
- Create: `packages/estimator-core/src/authoring/build-native-envelope.test.ts`
- Modify: `packages/estimator-core/src/index.ts`

**Interfaces:**
- Produces (the Slice-B contract):
```typescript
export interface NativeLineInput { ref: string; qty: number; designation?: string; notes?: string; description?: string }
export interface NativeScopeInput { name: string; netaStandard: NetaStandard; lines: NativeLineInput[] }
export interface NativeEnvelopeInput { projectNumber: string; quoteVersion?: number; scopes: NativeScopeInput[] }
export function buildNativeEnvelope(input: NativeEnvelopeInput): { envelope: EstimateEnvelope; findings: Finding[] }
export const EQUIPMENT_MODELS_SEED: EquipmentModel[]
export function createDefaultCatalogResolver(): CatalogResolver
```
- The returned `envelope` MUST satisfy the server's `validate_envelope`: `source_kind === 'native'`, `project_number` + `quote_version` set, `totals.bid_cents > 0`, each scope `replication_m4 === 1`, `scope_totals.adjusted_cents` present and reconciling, lines `line_kind: 'catalog'` with `base_qty === project_intake_qty`.

- [ ] **Step 1: Write the failing test** — `build-native-envelope.test.ts`:

```typescript
import { describe, expect, it } from 'vitest'
import { buildNativeEnvelope, EQUIPMENT_MODELS_SEED, createDefaultCatalogResolver } from '../index'
import { computeContentHash } from '../compile/content-hash'

const REF = EQUIPMENT_MODELS_SEED.find((m) => m.lifecycle_status === 'active' && m.ref_hours.ATS != null)!.ref

describe('buildNativeEnvelope', () => {
  it('produces a native, reconciling envelope with non-zero bid', () => {
    const { envelope, findings } = buildNativeEnvelope({
      projectNumber: 'DEMO-NATIVE-001',
      scopes: [{ name: 'Scope A', netaStandard: 'ATS', lines: [{ ref: REF, qty: 3, description: 'CB' }] }],
    })
    expect(findings.filter((f) => f.severity === 'error')).toEqual([])
    expect(envelope.source_kind).toBe('native')
    expect(envelope.project_number).toBe('DEMO-NATIVE-001')
    expect(envelope.quote_version).toBe(1)
    expect(envelope.totals.bid_cents).toBeGreaterThan(0)
    expect(envelope.scopes[0].replication_m4).toBe(1)
    expect(envelope.content_hash).toBe(computeContentHash(envelope))
    expect(envelope.scopes[0].lines[0].description).toBe('CB')
  })

  it('default resolver resolves the seed refs', () => {
    expect(createDefaultCatalogResolver().tryResolve(REF)?.ref).toBeTruthy()
  })
})
```

- [ ] **Step 2: Run to verify it fails**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm --filter @apex/estimator-core test -- build-native 2>&1 | tail -30'`
Expected: FAIL — module/exports not found.

- [ ] **Step 3: Implement `build-native-envelope.ts`.** Build a valid `EstimateDraft` and compile it. **Read `src/corpus/cases/case-b-labor-split-cost.json` + `src/corpus/harness.ts` + `src/compile/compile.ts` (the labor section + `CompileOptions`) first** to mirror the exact draft shape that yields populated `scope_totals.onsite_labor_cents` and a reconciling `bid_cents`. Construction outline (adapt field names to the real `makeDraft`/`ScopeDraft`/`labor_allocation` shapes):

```typescript
import seed from '../catalog/equipment-models.seed.json'
import { createCatalogResolver, type CatalogResolver } from '../catalog/resolver'
import type { EquipmentModel, NetaStandard } from '../catalog/types'
import { makeDraft } from '../schema/draft'
import { compile } from './compile' /* or '../compile/compile' */
import { validateEnvelope } from '../validate/validator'
import type { EstimateEnvelope } from '../schema/envelope'
import type { Finding } from '../validate/findings'

export const EQUIPMENT_MODELS_SEED = seed as EquipmentModel[]
export function createDefaultCatalogResolver(): CatalogResolver { return createCatalogResolver(EQUIPMENT_MODELS_SEED) }

export interface NativeLineInput { ref: string; qty: number; designation?: string; notes?: string; description?: string }
export interface NativeScopeInput { name: string; netaStandard: NetaStandard; lines: NativeLineInput[] }
export interface NativeEnvelopeInput { projectNumber: string; quoteVersion?: number; scopes: NativeScopeInput[] }

export function buildNativeEnvelope(input: NativeEnvelopeInput): { envelope: EstimateEnvelope; findings: Finding[] } {
  const resolver = createDefaultCatalogResolver()
  const draft = makeDraft({
    draft_id: `draft-${input.projectNumber}`,
    estimator_ref: input.projectNumber,
    scopes: input.scopes.map((s, si) => ({
      scope_id: `S${si + 1}`, name: s.name, neta_standard: s.netaStandard,
      replication_m4: 1, adjustment_multiplier_n4: 1,
      lines: s.lines.map((l, li) => ({
        line_uid: `S${si + 1}:r${li + 1}`, line_kind: 'catalog', included: true,
        equipment_model_ref: l.ref, base_qty: l.qty,
        designation: l.designation, notes: l.notes, description: l.description,
      })),
      // labor_allocation: derive onsite labor from total catalog hours @ baseline rate — mirror corpus case-b
      labor_allocation: [/* ... per harness/case-b ... */],
    })),
  })
  // ensure source_kind 'native' via CompileOptions if available, else set post-compile
  const envelope = compile(draft, 'r1', resolver /*, { sourceKind: 'native' } */)
  envelope.source_kind = 'native'
  envelope.project_number = input.projectNumber
  envelope.quote_version = input.quoteVersion ?? 1
  const findings = validateEnvelope(envelope)
  return { envelope, findings }
}
```

Key requirement: the labor model MUST produce `onsite_labor_cents > 0` so `bid_cents > 0` and the scope reconciles. Use the rate-card path the corpus uses (`BASELINE_RATE_CARD` / `resolveRateCard`). Setting `project_number`/`quote_version` after compile is safe — `canonicalPreimage` excludes them, so `content_hash` stays valid.

- [ ] **Step 4: Add exports to `index.ts`:**

```typescript
// Authoring (renderer)
export { buildNativeEnvelope, EQUIPMENT_MODELS_SEED, createDefaultCatalogResolver } from './authoring/build-native-envelope'
export type { NativeEnvelopeInput, NativeScopeInput, NativeLineInput } from './authoring/build-native-envelope'
```

- [ ] **Step 5: Run the test — passes; then full suite + typecheck**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm --filter @apex/estimator-core test 2>&1 | tail -15 && pnpm --filter @apex/estimator-core typecheck'`
Expected: all green, typecheck exit 0. (If JSON import fails typecheck, ensure `packages/estimator-core/tsconfig.json` has `"resolveJsonModule": true` — it already imports the seed in tests, so this should already be set; add it if missing.)

- [ ] **Step 6: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && git add packages/estimator-core/src && git commit -m "feat(estimator-core): buildNativeEnvelope authoring helper + seed/default-resolver exports"'
```

---

### Task 5: operations-web — `lib/estimator.ts` native client

**Files:**
- Create: `apps/operations-web/lib/estimator.ts`

**Interfaces:**
- Consumes: `buildNativeEnvelope`, `EQUIPMENT_MODELS_SEED`, `createDefaultCatalogResolver` (Task 4); `browserEnv.controlPlaneBaseUrl` (`lib/browser-env.ts`, fallback `http://127.0.0.1:8010`).
- Produces: `submitNative`, `approveRun`, `buildDemoEnvelope`, `DEMO_PROJECT_NUMBER`, `catalogRefs()` for the page.

- [ ] **Step 1: Implement `lib/estimator.ts`.** Mirror the `lib/estimator-intake.ts` pattern exactly: an `intakeBase()` URL helper, an inline `parseResponse<T>()`, direct `fetch()` calls (no shared helper). Hard-pin the demo project number here so the page can't override it.

```typescript
import { browserEnv } from './browser-env'
import {
  buildNativeEnvelope, EQUIPMENT_MODELS_SEED, type EstimateEnvelope, type Finding, type NativeScopeInput,
} from '@apex/estimator-core'

export const DEMO_PROJECT_NUMBER = 'DEMO-NATIVE-001'
export const PM_ACTOR_ID = process.env.NEXT_PUBLIC_OPS_DEV_PM_ID || '00000000-0000-0000-0000-000000000001'

export class EstimatorError extends Error {
  constructor(message: string, public status: number) { super(message) }
}
function intakeBase(): string { return `${browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')}/api/v1/ops/intake` }
async function parseResponse<T>(res: Response): Promise<T> {
  let payload: unknown = null
  try { payload = await res.json() } catch { payload = null }
  if (!res.ok) {
    const detail = (payload as { detail?: unknown })?.detail
    throw new EstimatorError(typeof detail === 'string' ? detail : `Request failed with status ${res.status}`, res.status)
  }
  return payload as T
}

export interface NativeRunResult { run_id: string; status: string; conflict_kind: string | null; source_format: string; findings: { code: string; severity: string; ok: boolean; message: string }[] }

export function catalogRefs(): string[] {
  return EQUIPMENT_MODELS_SEED.filter((m) => m.lifecycle_status === 'active').map((m) => m.ref).sort()
}

/** Always pins project_number = DEMO_PROJECT_NUMBER (never Miner; never caller-supplied). */
export function buildDemoEnvelope(scopes: NativeScopeInput[]): { envelope: EstimateEnvelope; findings: Finding[] } {
  return buildNativeEnvelope({ projectNumber: DEMO_PROJECT_NUMBER, quoteVersion: 1, scopes })
}

export async function submitNative(envelope: EstimateEnvelope, uploadedBy = PM_ACTOR_ID): Promise<NativeRunResult> {
  const res = await fetch(`${intakeBase()}/native`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ uploaded_by: uploadedBy, envelope }),
  })
  return parseResponse<NativeRunResult>(res)
}

export async function approveRun(runId: string, approvedBy = PM_ACTOR_ID): Promise<{ status: string; run_id: string }> {
  const res = await fetch(`${intakeBase()}/${runId}/approve`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ approved_by: approvedBy }),
  })
  return parseResponse<{ status: string; run_id: string }>(res)
}
```

(If `@apex/estimator-core` does not re-export `NativeScopeInput`/`EstimateEnvelope`/`Finding`/`EquipmentModel` types needed here, add the missing `export type` lines to estimator-core `index.ts` — Task 4 already exports the input types and `EstimateEnvelope`/`LineC` are exported per the grounding.)

- [ ] **Step 2: Typecheck**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm --filter operations-web typecheck'`
Expected: exit 0 (proves the estimator-core API usage compiles through `transpilePackages`).

- [ ] **Step 3: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && git add apps/operations-web/lib/estimator.ts && git commit -m "feat(operations-web): lib/estimator native client (pins DEMO-NATIVE-001)"'
```

---

### Task 6: operations-web — `app/estimator/page.tsx` thin authoring screen + nav link

**Files:**
- Create: `apps/operations-web/app/estimator/page.tsx`
- Modify: the nav component used by `/pm-review/*` (find it; add an `/estimator` link as in #80)

**Interfaces:**
- Consumes: `lib/estimator.ts` (Task 5). One client component (`'use client'`).

- [ ] **Step 1: Implement `app/estimator/page.tsx`** — a `'use client'` page: one scope (NETA standard select ATS/MTS), an add-line control (catalog `ref` `<select>` from `catalogRefs()`, `qty` number, and `Description` / `Designation` / `Notes` text inputs — grid order **`Qty | Description | Apparatus | Designation | Notes`**), a read-only `Project: DEMO-NATIVE-001` banner, and a "Compile & Submit" button. On submit: `buildDemoEnvelope(scopes)` → show client `findings`; if no error findings, `submitNative(envelope)` → if `status==='parsed'`, `approveRun(run_id)` → show the approved `run_id` + a link to `/pm-review/recognition`. Surface API errors verbatim (esp. a 409 → "DEMO-NATIVE-001 already has a frozen quote — reset it to re-run the demo"). Model table/input styling on `app/pm-review/estimator-intake/page.tsx` (Tailwind `px-3 py-1.5`, `<input>`/`<select>`). Keep it minimal — no scope-deletion, no persistence; the draft is ephemeral component state.

- [ ] **Step 2: Add the nav link.** Locate the nav/sidebar component that lists the `/pm-review/*` routes (grep for `pm-review/recognition` under `apps/operations-web/app` / `components`) and add an `Estimator → /estimator` entry, mirroring how the recognition link was added in #80.

- [ ] **Step 3: Typecheck + build**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH && pnpm --filter operations-web typecheck && pnpm --filter operations-web build 2>&1 | tail -25'`
Expected: typecheck exit 0; build succeeds and lists `/estimator` among the routes.

- [ ] **Step 4: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && git add apps/operations-web/app/estimator apps/operations-web && git commit -m "feat(operations-web): thin /estimator native renderer page + nav link"'
```

---

### Task 7: hosted smoke — full client path against ops_dev (DISPOSABLE project)

**Files:**
- Create: `apps/operations-web/scripts/smoke-estimator-native.mjs`

**Interfaces:**
- Consumes: the live control-plane API on `:8010` (host, `OPS_DEV_DSN` set) + `lib/estimator.ts` building logic. This is the Slice-B integration proof and the demo rehearsal.

- [ ] **Step 1: Implement `scripts/smoke-estimator-native.mjs`.** Mirror an existing `scripts/smoke-*.mjs` (e.g. `smoke-pm-intake-hosted.mjs`) for the node-fetch + assert style. It MUST:
  - Use `const PROJECT = 'DEMO-RENDERER-SMOKE-001'` — a **disposable** name. **NEVER `DEMO-NATIVE-001` (reserved) and NEVER `MINER-PHX-AB-MV`.** Import `buildNativeEnvelope` directly from `@apex/estimator-core` and override `projectNumber: PROJECT` (do NOT use `buildDemoEnvelope`, which pins DEMO-NATIVE-001).
  - Pre-clean only its own disposable project's native rows so it is re-runnable: before submit, if a prior `DEMO-RENDERER-SMOKE-001` run is frozen, clear its native intake rows (documented in a comment) — or accept a 409 and exit non-zero with a clear "reset the disposable smoke project" message.
  - Pipeline: build envelope (1 ATS scope, ≥1 catalog line carrying `designation`/`notes`/`description`) → `POST /native` (assert `status==='parsed'`) → `POST /{run_id}/approve` (assert `approved`) → `GET /api/v1/ops/recognition/worklist?project_number=DEMO-RENDERER-SMOKE-001` (assert rows) → assert the materialized `ops.scope_quote_line` carries the three metadata values (via a small read; if the smoke can't reach the DB, assert via an API/worklist field instead).
  - Print PASS/FAIL with a one-line summary; exit non-zero on any failed assertion.

- [ ] **Step 2: Run the smoke against a live host stack.** Start the API on `:8010` (one ssh session so uvicorn inherits `OPS_DEV_DSN` against **ops_dev**), then run the smoke:

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer/apps/control-plane-api && set -a; . ../../infra/.env; set +a; export OPS_DEV_DSN="host=127.0.0.1 port=5432 dbname=ops_dev user=postgres password=$DEV_PG_PASSWORD sslmode=disable"; pkill -f "uvicorn main:app" 2>/dev/null; sleep 1; nohup ../../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8010 > /tmp/cpapi_estsmoke.log 2>&1 & sleep 6; export PATH=$HOME/.local/bin:/home/olares/.nvm/versions/node/v20.20.2/bin:$PATH; cd .. && node operations-web/scripts/smoke-estimator-native.mjs; echo SMOKE_EXIT=$?; pkill -f "uvicorn main:app"'
```
Expected: smoke prints PASS, `SMOKE_EXIT=0`. **Verify Miner + DEMO-NATIVE-001 untouched** afterward (read-only count of `MINER-PHX-AB-MV` apparatus = 5344; `DEMO-NATIVE-001` still absent).

- [ ] **Step 3: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-estimator-renderer && git add apps/operations-web/scripts/smoke-estimator-native.mjs && git commit -m "test(operations-web): hosted estimator native smoke (disposable project; Miner + DEMO-NATIVE-001 untouched)"'
```

---

## Post-build (after all tasks green)

- **Whole-branch review** (opus + Codex cross-engine per IRP) over `main..estimator/native-renderer`.
- **finishing-a-development-branch** → operator-gated merge to main + operator-gated ops_dev apply of mig 011 (prod stays blocked behind `ops_app`).
- The operator-driven **live demo** uses the `/estimator` page against the reserved fresh `DEMO-NATIVE-001` (the page's pinned default) — once, intentionally, then surfaced in `/pm-review/recognition`.

## Self-Review notes
- **Spec coverage:** thin path (project pinned, ephemeral draft, compile via packaged core, native→approve, surface-after-approve) → Tasks 5-7; metadata promotion (LineDraft→LineC→pivot→load→column, excluded from hash) → Tasks 1-4. Demo-data discipline (force DEMO-NATIVE-001, disposable smoke, never Miner) → Global Constraints + Tasks 5/7.
- **Hash-neutrality** is the load-bearing invariant — proven by Task 1 Step 1's second test and re-asserted in Task 4.
- **Reconciliation is by construction** (compiled envelope satisfies `validate_envelope`'s arithmetic) — Task 4 owns producing non-zero, reconciling labor; the corpus cases are the working reference.
- **Known soft spot:** the labor-allocation construction inside `buildNativeEnvelope` (Task 4 Step 3) is specified by reference to corpus case-b rather than verbatim, because the exact `labor_allocation` shape lives in files the implementer must read; the test assertions (non-zero bid, no error findings, hash match) are the hard contract.
