# PM Recognized-Revenue Read Surface — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface recognized + billable revenue per project/scope in the operations-web PM management end, derived live from apparatus completion × quoted revenue, as a read-only bounded packet.

**Architecture:** A new read-only control-plane endpoint `GET /api/v1/ops/revenue-recognition` derives `recognized = Σ quoted_revenue WHERE apparatus.status='Complete'` (scope grain) from `public.apparatus/scopes/projects`; operations-web consumes it via a typed `lib/` helper and renders a promoted `/pm-review/finance` route. No prod DDL, no writes, no new authority. Design spec: `docs/superpowers/specs/2026-06-19-pm-recognized-revenue-read-surface-design.md`.

**Tech Stack:** control-plane-api (FastAPI + SQLAlchemy Core `text()` + Pydantic v2, Python 3.12 venv); operations-web (Next 16 / React 19 / TypeScript, relative imports, Playwright tests); host dev-pg (PG17) for the integration slice.

## Global Constraints

- **Read-only.** GET only; no POST/PUT/PATCH/DELETE; no writes; no new authority columns; no mutation-seam calls.
- **No prod DDL.** Recognized revenue is DERIVED on read; the empty `apparatus_revenue` / `apparatus_revenue_events` ledgers are NOT touched.
- **Recognition predicate is exactly** `apparatus.status = 'Complete'::public.apparatus_status`, over `projects p ⋈ scopes s (s.is_active) ⋈ apparatus a (a.is_active) WHERE p.is_active` — identical to `public.v_project_apparatus_summary` so the money view agrees with the completion counts.
- **Held boundaries untouched:** customer-billing, source-writeback, financial-handoff (write), invoice/payroll/accounting/external-sync stay placeholder. The only branch admitted is the finance READ.
- **Honesty label required** on the UI: recognized is derived from completion, not a persisted ledger; billable = recognized − billed, billed = 0 (billing not admitted).
- **Endpoint:** `GET /api/v1/ops/revenue-recognition?limit=N` (default 25, 1–100), scope-grain rows.
- **Repo/branch:** all work in the host clone `/home/olares/code/apex/apex-power-ops-platform` on branch `ops/recognized-revenue`.
- **Run control-plane tests:** `cd apps/control-plane-api && .venv/bin/python -m pytest <path> -v`.
- **Run operations-web smokes:** the Playwright webServer runs `next start -p 3030`, so a build must exist first: `pnpm --filter @apex/operations-web exec next build && pnpm --filter @apex/operations-web exec playwright test <smoke>`. **Run pure-logic unit specs** without a server by setting a hosted base URL (skips the webServer): `OPERATIONS_WEB_BROWSER_SMOKE_BASE_URL=http://127.0.0.1:9 pnpm --filter @apex/operations-web exec playwright test <unit>`. Toolchain established in Task 0.

## File Structure

- `apps/control-plane-api/services/ops/router.py` — **modify**: add `RevenueRecognitionRow` model, `REVENUE_RECOGNITION_SQL` constant, and the `revenue_recognition_summary` endpoint (alongside the existing ops read endpoints; router already mounted at `/api/v1/ops`).
- `apps/control-plane-api/tests/test_ops_revenue_recognition.py` — **create**: mocked-DB unit test (routing/shape/limit).
- `apps/control-plane-api/tests/test_ops_revenue_recognition_integration.py` — **create**: `@pytest.mark.integration` test proving the recognition math against the seeded slice (imports the SAME SQL constant).
- `infra/database/dev-fixtures/pm_public_slice.sql` — **create**: minimal `public` enums + `projects/scopes/apparatus` + deterministic seed for the integration test.
- `apps/operations-web/lib/revenue-recognition.ts` — **create**: types, `RevenueRecognitionError`, `fetchRevenueRecognition`, pure `rollupByProject`.
- `apps/operations-web/tests/revenue-recognition.unit.spec.ts` — **create**: unit test for `rollupByProject`.
- `apps/operations-web/app/pm-review/finance/page.tsx` — **create**: the admitted read-only finance view.
- `apps/operations-web/app/pm-review/finance-placeholder/page.tsx` — **modify**: additive pointer to the admitted read view (write branches stay held).
- `apps/operations-web/tests/browser-shell.pm-finance.smoke.spec.ts` — **create**: smoke for the new route.
- `apps/operations-web/tests/browser-shell.pm-finance-placeholder.smoke.spec.ts` — **modify**: add one assertion for the new pointer link.

---

### Task 0: Branch + toolchain readiness

**Files:** none (environment + branch).

**Interfaces:**
- Produces: branch `ops/recognized-revenue`; a working control-plane pytest invocation; a working operations-web Playwright invocation (`pnpm` or `npx`).

- [ ] **Step 1: Create the feature branch**

```bash
cd /home/olares/code/apex/apex-power-ops-platform
git checkout main && git pull --ff-only
git checkout -b ops/recognized-revenue
```

- [ ] **Step 2: Verify the control-plane test toolchain (baseline green)**

Run: `cd /home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api && .venv/bin/python -m pytest tests/test_ops_master_operations.py -q`
Expected: PASS (existing ops endpoint tests pass with the venv).

- [ ] **Step 3: Establish the frontend toolchain**

The host has Node 18.19 + npm 9 + Playwright browsers, but no pnpm and Node 18 is below Next 16's floor (Node 20.9+). Install Node 20 LTS user-level via nvm (no sudo) and enable pnpm:

```bash
# Node 20 via nvm (user-level; skip if `node -v` already >= v20.9)
command -v nvm >/dev/null 2>&1 || curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
nvm install 20 && nvm use 20
corepack enable   # repo pins pnpm@10.0.0 via package.json "packageManager"
node -v && pnpm -v
```

If nvm install is blocked in this environment, this is the build-to-need toolchain step (§256) — stop and flag to the operator; the operations-web tasks (2–3) cannot run their tests until Node 20 + pnpm are available (host or the laptop Windows checkout per `apps/operations-web/README.md`).

- [ ] **Step 4: Install operations-web deps + baseline smoke green**

```bash
cd /home/olares/code/apex/apex-power-ops-platform
pnpm install
pnpm --filter @apex/operations-web exec next build
pnpm --filter @apex/operations-web exec playwright test tests/browser-shell.pm-finance-placeholder.smoke.spec.ts
```
Expected: PASS (existing finance-placeholder smoke is green on the toolchain). This proves the frontend test loop before we add to it.

- [ ] **Step 5: Commit the branch point (no code yet)**

No commit needed; the branch is created. Proceed to Task 1.

---

### Task 1: Control-plane recognized-revenue endpoint (derived, read-only)

**Files:**
- Modify: `apps/control-plane-api/services/ops/router.py`
- Create: `apps/control-plane-api/tests/test_ops_revenue_recognition.py`
- Create: `apps/control-plane-api/tests/test_ops_revenue_recognition_integration.py`
- Create: `infra/database/dev-fixtures/pm_public_slice.sql`

**Interfaces:**
- Produces: `GET /api/v1/ops/revenue-recognition?limit=N` → `list[RevenueRecognitionRow]`; module constant `REVENUE_RECOGNITION_SQL`; model `RevenueRecognitionRow` with fields `project_id:str, project_number:str|None, project_name:str|None, scope_id:str|None, scope_name:str|None, quoted_revenue:float, recognized_revenue:float, recognition_percent:float, billable_now:float, total_apparatus:int, completed_apparatus:int`.

- [ ] **Step 1: Write the seed fixture**

Create `infra/database/dev-fixtures/pm_public_slice.sql`:

```sql
-- Minimal public slice for hermetic recognized-revenue tests (DEV ONLY).
-- Apply to a dedicated test DB on host dev-pg, e.g.:
--   docker exec apex-dev-pg psql -U postgres -c "CREATE DATABASE revenue_recognition_test"
--   docker exec -i apex-dev-pg psql -U postgres -d revenue_recognition_test < infra/database/dev-fixtures/pm_public_slice.sql
DO $$ BEGIN
  CREATE TYPE public.apparatus_status AS ENUM ('Not Started','In Progress','Complete');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS public.projects (
  id uuid PRIMARY KEY,
  project_number text,
  project_name text,
  is_active boolean NOT NULL DEFAULT true
);
CREATE TABLE IF NOT EXISTS public.scopes (
  id uuid PRIMARY KEY,
  project_id uuid NOT NULL REFERENCES public.projects(id),
  scope_name text,
  is_active boolean NOT NULL DEFAULT true
);
CREATE TABLE IF NOT EXISTS public.apparatus (
  id uuid PRIMARY KEY,
  scope_id uuid NOT NULL REFERENCES public.scopes(id),
  status public.apparatus_status NOT NULL,
  quoted_revenue numeric NOT NULL DEFAULT 0,
  is_active boolean NOT NULL DEFAULT true
);

TRUNCATE public.apparatus, public.scopes, public.projects CASCADE;

INSERT INTO public.projects (id, project_number, project_name, is_active) VALUES
  ('11111111-1111-1111-1111-111111111111','P-001','Test Project A', true);
INSERT INTO public.scopes (id, project_id, scope_name, is_active) VALUES
  ('22222222-2222-2222-2222-222222222221','11111111-1111-1111-1111-111111111111','Scope One', true),
  ('22222222-2222-2222-2222-222222222222','11111111-1111-1111-1111-111111111111','Scope Two', true);
-- Scope One: 3 apparatus, 2 Complete  => quoted 6000, recognized 3000, 50.00%
-- Scope Two: 2 apparatus, 0 Complete  => quoted 5000, recognized 0, 0.00%
INSERT INTO public.apparatus (id, scope_id, status, quoted_revenue, is_active) VALUES
  ('33333333-3333-3333-3333-333333333301','22222222-2222-2222-2222-222222222221','Complete',1000,true),
  ('33333333-3333-3333-3333-333333333302','22222222-2222-2222-2222-222222222221','Complete',2000,true),
  ('33333333-3333-3333-3333-333333333303','22222222-2222-2222-2222-222222222221','In Progress',3000,true),
  ('33333333-3333-3333-3333-333333333304','22222222-2222-2222-2222-222222222222','In Progress',2500,true),
  ('33333333-3333-3333-3333-333333333305','22222222-2222-2222-2222-222222222222','Not Started',2500,true);
```

- [ ] **Step 2: Create the test DB + apply the slice**

```bash
cd /home/olares/code/apex/apex-power-ops-platform
docker exec apex-dev-pg psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='revenue_recognition_test'" | grep -q 1 \
  || docker exec apex-dev-pg psql -U postgres -c "CREATE DATABASE revenue_recognition_test"
docker exec -i apex-dev-pg psql -U postgres -d revenue_recognition_test < infra/database/dev-fixtures/pm_public_slice.sql
```
Expected: `CREATE TYPE` / `CREATE TABLE` / `INSERT 0 N` with no errors.

- [ ] **Step 3: Write the failing integration test (drives the SQL)**

Create `apps/control-plane-api/tests/test_ops_revenue_recognition_integration.py`:

```python
"""Recognition-math integration test against a seeded public slice (dev only).

Runs the SAME SQL constant the endpoint runs, so the derivation is proven
end-to-end. Skipped unless RECOGNITION_TEST_DSN points at the seeded slice.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text  # noqa: E402

RECOGNITION_TEST_DSN = os.environ.get("RECOGNITION_TEST_DSN")

pytestmark = pytest.mark.integration


@pytest.mark.skipif(not RECOGNITION_TEST_DSN, reason="RECOGNITION_TEST_DSN not set")
def test_recognition_math_against_seeded_slice():
    from services.ops.router import REVENUE_RECOGNITION_SQL

    engine = create_engine(RECOGNITION_TEST_DSN)
    with engine.connect() as conn:
        rows = conn.execute(text(REVENUE_RECOGNITION_SQL), {"limit": 25}).mappings().all()

    by_scope = {r["scope_name"]: r for r in rows}

    one = by_scope["Scope One"]
    assert float(one["quoted_revenue"]) == 6000.0
    assert float(one["recognized_revenue"]) == 3000.0
    assert float(one["recognition_percent"]) == 50.0
    assert float(one["billable_now"]) == 3000.0
    assert one["total_apparatus"] == 3
    assert one["completed_apparatus"] == 2

    two = by_scope["Scope Two"]
    assert float(two["quoted_revenue"]) == 5000.0
    assert float(two["recognized_revenue"]) == 0.0
    assert float(two["recognition_percent"]) == 0.0
    assert two["completed_apparatus"] == 0
```

- [ ] **Step 4: Run the integration test to verify it fails**

```bash
cd /home/olares/code/apex/apex-power-ops-platform
set -a; . infra/.env; set +a
export RECOGNITION_TEST_DSN="postgresql+psycopg2://postgres:${DEV_PG_PASSWORD}@127.0.0.1:5432/revenue_recognition_test?sslmode=disable"
cd apps/control-plane-api && .venv/bin/python -m pytest tests/test_ops_revenue_recognition_integration.py -v
```
Expected: FAIL with `ImportError: cannot import name 'REVENUE_RECOGNITION_SQL'`.

- [ ] **Step 5: Add the SQL constant + model + endpoint**

In `apps/control-plane-api/services/ops/router.py`, add the constant + model near the other response models, and the endpoint near `project_apparatus_summary`:

```python
REVENUE_RECOGNITION_SQL = """
SELECT
    p.id AS project_id,
    p.project_number,
    p.project_name,
    s.id AS scope_id,
    s.scope_name,
    COALESCE(SUM(a.quoted_revenue), 0) AS quoted_revenue,
    COALESCE(SUM(a.quoted_revenue) FILTER (WHERE a.status = 'Complete'::public.apparatus_status), 0) AS recognized_revenue,
    round(
        CASE
            WHEN COALESCE(SUM(a.quoted_revenue), 0) > 0
            THEN COALESCE(SUM(a.quoted_revenue) FILTER (WHERE a.status = 'Complete'::public.apparatus_status), 0)
                 / SUM(a.quoted_revenue) * 100
            ELSE 0
        END, 2) AS recognition_percent,
    -- billable_now = recognized - billed; billing is not admitted, so billed = 0.
    COALESCE(SUM(a.quoted_revenue) FILTER (WHERE a.status = 'Complete'::public.apparatus_status), 0) AS billable_now,
    count(a.id) AS total_apparatus,
    count(a.id) FILTER (WHERE a.status = 'Complete'::public.apparatus_status) AS completed_apparatus
FROM public.projects p
LEFT JOIN public.scopes s ON s.project_id = p.id AND s.is_active = true
LEFT JOIN public.apparatus a ON a.scope_id = s.id AND a.is_active = true
WHERE p.is_active = true
GROUP BY p.id, p.project_number, p.project_name, s.id, s.scope_name
ORDER BY p.project_number, s.scope_name
LIMIT :limit
"""


class RevenueRecognitionRow(BaseModel):
    """Derived recognized-revenue row (scope grain), read-only.

    recognized = sum(quoted_revenue) for apparatus with status='Complete'
    (binary, at completion). Derived live; NOT a persisted ledger.
    billable_now = recognized - billed; billing not admitted => billed = 0.
    """

    project_id: str
    project_number: Optional[str] = None
    project_name: Optional[str] = None
    scope_id: Optional[str] = None
    scope_name: Optional[str] = None
    quoted_revenue: float
    recognized_revenue: float
    recognition_percent: float
    billable_now: float
    total_apparatus: int
    completed_apparatus: int


@router.get(
    "/revenue-recognition",
    response_model=list[RevenueRecognitionRow],
    summary="Operations Visibility recognized-revenue rollup, scope grain (read-only, derived).",
)
def revenue_recognition_summary(
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[RevenueRecognitionRow]:
    """Return bounded scope-grain recognized-revenue rows.

    Recognized revenue is derived on read; the dedicated recognition tables are
    not populated. Strictly read-only: no writes, no new authority.
    """
    rows = (
        db.execute(text(REVENUE_RECOGNITION_SQL), {"limit": limit})
        .mappings()
        .all()
    )
    return [RevenueRecognitionRow(**row) for row in rows]
```

- [ ] **Step 6: Run the integration test to verify it passes**

```bash
cd /home/olares/code/apex/apex-power-ops-platform
set -a; . infra/.env; set +a
export RECOGNITION_TEST_DSN="postgresql+psycopg2://postgres:${DEV_PG_PASSWORD}@127.0.0.1:5432/revenue_recognition_test?sslmode=disable"
cd apps/control-plane-api && .venv/bin/python -m pytest tests/test_ops_revenue_recognition_integration.py -v
```
Expected: PASS (1 passed).

- [ ] **Step 7: Write the failing mocked unit test (routing/shape/limit)**

Create `apps/control-plane-api/tests/test_ops_revenue_recognition.py`:

```python
"""Ops Router — Revenue Recognition view unit tests (mocked DB).

Validates routing, GET-only, response shape, and limit forwarding without a
live database, mirroring tests/test_ops_master_operations.py.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from config import get_db  # noqa: E402


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _FakeDB:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, statement, params):
        self.calls.append((str(statement), params))
        return _FakeResult(self.rows)


@pytest.fixture
def client():
    os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
    from main import app

    fake_rows = [
        {
            "project_id": "11111111-1111-1111-1111-111111111111",
            "project_number": "P-001",
            "project_name": "Test Project A",
            "scope_id": "22222222-2222-2222-2222-222222222221",
            "scope_name": "Scope One",
            "quoted_revenue": 6000.0,
            "recognized_revenue": 3000.0,
            "recognition_percent": 50.0,
            "billable_now": 3000.0,
            "total_apparatus": 3,
            "completed_apparatus": 2,
        }
    ]
    fake_db = _FakeDB(fake_rows)

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app), fake_db
    app.dependency_overrides.clear()


def test_endpoint_responds_200(client):
    test_client, _ = client
    assert test_client.get("/api/v1/ops/revenue-recognition").status_code == 200


def test_endpoint_not_under_work_prefix(client):
    test_client, _ = client
    assert test_client.get("/api/v1/work/revenue-recognition").status_code == 404


def test_response_shape(client):
    test_client, _ = client
    body = test_client.get("/api/v1/ops/revenue-recognition").json()
    assert len(body) == 1
    assert set(body[0].keys()) == {
        "project_id", "project_number", "project_name", "scope_id", "scope_name",
        "quoted_revenue", "recognized_revenue", "recognition_percent", "billable_now",
        "total_apparatus", "completed_apparatus",
    }


def test_limit_is_forwarded(client):
    test_client, fake_db = client
    assert test_client.get("/api/v1/ops/revenue-recognition?limit=7").status_code == 200
    assert fake_db.calls[-1][1] == {"limit": 7}


def test_non_get_verbs_rejected(client):
    test_client, _ = client
    for method in ("post", "put", "patch", "delete"):
        assert getattr(test_client, method)("/api/v1/ops/revenue-recognition").status_code == 405
```

- [ ] **Step 8: Run the unit test to verify it passes**

Run: `cd /home/olares/code/apex/apex-power-ops-platform/apps/control-plane-api && .venv/bin/python -m pytest tests/test_ops_revenue_recognition.py -v`
Expected: PASS (5 passed).

- [ ] **Step 9: Commit**

```bash
cd /home/olares/code/apex/apex-power-ops-platform
git add apps/control-plane-api/services/ops/router.py apps/control-plane-api/tests/test_ops_revenue_recognition.py apps/control-plane-api/tests/test_ops_revenue_recognition_integration.py infra/database/dev-fixtures/pm_public_slice.sql
git commit -m "feat(ops): derived recognized-revenue read endpoint (/api/v1/ops/revenue-recognition)"
```

---

### Task 2: operations-web lib helper + rollup

**Files:**
- Create: `apps/operations-web/lib/revenue-recognition.ts`
- Create: `apps/operations-web/tests/revenue-recognition.unit.spec.ts`

**Interfaces:**
- Consumes: `lib/browser-env` (`browserEnv.controlPlaneBaseUrl`); the endpoint from Task 1.
- Produces: `RevenueRecognitionRow` type; `RevenueRecognitionError`; `fetchRevenueRecognition(limit=12): Promise<RevenueRecognitionRow[]>`; `rollupByProject(rows): ProjectRevenueRollup[]` and `ProjectRevenueRollup` type.

- [ ] **Step 1: Write the failing unit test**

Create `apps/operations-web/tests/revenue-recognition.unit.spec.ts`:

```ts
import { expect, test } from '@playwright/test'

import { rollupByProject, RevenueRecognitionRow } from '../lib/revenue-recognition'

const scopeRow = (over: Partial<RevenueRecognitionRow>): RevenueRecognitionRow => ({
  project_id: 'p1', project_number: 'P-001', project_name: 'Project A',
  scope_id: 's', scope_name: 'Scope', quoted_revenue: 0, recognized_revenue: 0,
  recognition_percent: 0, billable_now: 0, total_apparatus: 0, completed_apparatus: 0,
  ...over,
})

test('rollupByProject sums scopes and recomputes the project percent', () => {
  const rows = [
    scopeRow({ scope_id: 's1', scope_name: 'One', quoted_revenue: 6000, recognized_revenue: 3000, billable_now: 3000, total_apparatus: 3, completed_apparatus: 2 }),
    scopeRow({ scope_id: 's2', scope_name: 'Two', quoted_revenue: 5000, recognized_revenue: 0, billable_now: 0, total_apparatus: 2, completed_apparatus: 0 }),
  ]
  const result = rollupByProject(rows)
  expect(result).toHaveLength(1)
  const p = result[0]
  expect(p.quoted_revenue).toBe(11000)
  expect(p.recognized_revenue).toBe(3000)
  expect(p.billable_now).toBe(3000)
  expect(p.recognition_percent).toBeCloseTo(27.27, 2)
  expect(p.total_apparatus).toBe(5)
  expect(p.completed_apparatus).toBe(2)
  expect(p.scopes).toHaveLength(2)
})

test('rollupByProject yields 0 percent when nothing is quoted', () => {
  const result = rollupByProject([scopeRow({ quoted_revenue: 0, recognized_revenue: 0 })])
  expect(result[0].recognition_percent).toBe(0)
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /home/olares/code/apex/apex-power-ops-platform && OPERATIONS_WEB_BROWSER_SMOKE_BASE_URL=http://127.0.0.1:9 pnpm --filter @apex/operations-web exec playwright test tests/revenue-recognition.unit.spec.ts`
Expected: FAIL — cannot resolve `../lib/revenue-recognition`.

- [ ] **Step 3: Implement the lib helper**

Create `apps/operations-web/lib/revenue-recognition.ts`:

```ts
import { browserEnv } from './browser-env'

export type RevenueRecognitionRow = {
  project_id: string
  project_number: string | null
  project_name: string | null
  scope_id: string | null
  scope_name: string | null
  quoted_revenue: number
  recognized_revenue: number
  recognition_percent: number
  billable_now: number
  total_apparatus: number
  completed_apparatus: number
}

export type ProjectRevenueRollup = {
  project_id: string
  project_number: string | null
  project_name: string | null
  quoted_revenue: number
  recognized_revenue: number
  recognition_percent: number
  billable_now: number
  total_apparatus: number
  completed_apparatus: number
  scopes: RevenueRecognitionRow[]
}

export class RevenueRecognitionError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'RevenueRecognitionError'
    this.status = status
  }
}

function getErrorDetail(payload: unknown, fallback: string) {
  if (typeof payload !== 'object' || payload === null) {
    return fallback
  }
  const detail = (payload as { detail?: unknown }).detail
  return typeof detail === 'string' && detail.trim().length > 0 ? detail : fallback
}

export async function fetchRevenueRecognition(limit = 12): Promise<RevenueRecognitionRow[]> {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  const response = await fetch(`${baseUrl}/api/v1/ops/revenue-recognition?limit=${limit}`, {
    headers: { Accept: 'application/json' },
  })

  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    throw new RevenueRecognitionError(
      getErrorDetail(payload, `Request failed with status ${response.status}`),
      response.status,
    )
  }

  return payload as RevenueRecognitionRow[]
}

export function rollupByProject(rows: RevenueRecognitionRow[]): ProjectRevenueRollup[] {
  const byId = new Map<string, ProjectRevenueRollup>()
  for (const row of rows) {
    let project = byId.get(row.project_id)
    if (!project) {
      project = {
        project_id: row.project_id,
        project_number: row.project_number,
        project_name: row.project_name,
        quoted_revenue: 0,
        recognized_revenue: 0,
        recognition_percent: 0,
        billable_now: 0,
        total_apparatus: 0,
        completed_apparatus: 0,
        scopes: [],
      }
      byId.set(row.project_id, project)
    }
    project.quoted_revenue += row.quoted_revenue
    project.recognized_revenue += row.recognized_revenue
    project.billable_now += row.billable_now
    project.total_apparatus += row.total_apparatus
    project.completed_apparatus += row.completed_apparatus
    project.scopes.push(row)
  }
  for (const project of byId.values()) {
    project.recognition_percent =
      project.quoted_revenue > 0
        ? Math.round((project.recognized_revenue / project.quoted_revenue) * 10000) / 100
        : 0
  }
  return Array.from(byId.values())
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd /home/olares/code/apex/apex-power-ops-platform && OPERATIONS_WEB_BROWSER_SMOKE_BASE_URL=http://127.0.0.1:9 pnpm --filter @apex/operations-web exec playwright test tests/revenue-recognition.unit.spec.ts`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
cd /home/olares/code/apex/apex-power-ops-platform
git add apps/operations-web/lib/revenue-recognition.ts apps/operations-web/tests/revenue-recognition.unit.spec.ts
git commit -m "feat(operations-web): revenue-recognition lib helper + project rollup"
```

---

### Task 3: operations-web finance route + placeholder pointer

**Files:**
- Create: `apps/operations-web/app/pm-review/finance/page.tsx`
- Modify: `apps/operations-web/app/pm-review/finance-placeholder/page.tsx`
- Create: `apps/operations-web/tests/browser-shell.pm-finance.smoke.spec.ts`
- Modify: `apps/operations-web/tests/browser-shell.pm-finance-placeholder.smoke.spec.ts`

**Interfaces:**
- Consumes: `fetchRevenueRecognition`, `rollupByProject`, `RevenueRecognitionError` from Task 2.
- Produces: route `/pm-review/finance`.

- [ ] **Step 1: Write the failing smoke test for the new route**

Create `apps/operations-web/tests/browser-shell.pm-finance.smoke.spec.ts`:

```ts
import { expect, test } from '@playwright/test'

test('pm finance route renders derived recognized revenue (read-only)', async ({ page }) => {
  const mutationRequests: string[] = []
  await page.route('**/api/v1/mutations/**', async (route) => {
    mutationRequests.push(route.request().url())
    await route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'no mutations' }) })
  })

  await page.route('**/api/v1/ops/revenue-recognition*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          project_id: '11111111-1111-1111-1111-111111111111',
          project_number: 'P-001', project_name: 'Test Project A',
          scope_id: 's1', scope_name: 'Scope One',
          quoted_revenue: 6000, recognized_revenue: 3000, recognition_percent: 50,
          billable_now: 3000, total_apparatus: 3, completed_apparatus: 2,
        },
      ]),
    })
  })

  const response = await page.goto('/pm-review/finance', { waitUntil: 'networkidle' })
  expect(response?.ok()).toBeTruthy()

  await expect(page.getByRole('heading', { name: /Recognized revenue/i })).toBeVisible()
  await expect(page.getByText(/derived from apparatus completion/i)).toBeVisible()
  await expect(page.getByText('Test Project A')).toBeVisible()
  await expect(page.getByText('Scope One')).toBeVisible()
  expect(mutationRequests).toHaveLength(0)
})
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd /home/olares/code/apex/apex-power-ops-platform && pnpm --filter @apex/operations-web exec next build && pnpm --filter @apex/operations-web exec playwright test tests/browser-shell.pm-finance.smoke.spec.ts`
Expected: FAIL — `/pm-review/finance` returns 404 (route does not exist).

- [ ] **Step 3: Implement the finance route**

Create `apps/operations-web/app/pm-review/finance/page.tsx`:

```tsx
'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

import {
  fetchRevenueRecognition,
  rollupByProject,
  ProjectRevenueRollup,
  RevenueRecognitionError,
} from '../../../lib/revenue-recognition'

const usd = (value: number) =>
  value.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

export default function FinancePage() {
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [projects, setProjects] = useState<ProjectRevenueRollup[]>([])

  useEffect(() => {
    let isActive = true
    async function load() {
      setIsLoading(true)
      setErrorMessage(null)
      try {
        const rows = await fetchRevenueRecognition()
        if (isActive) setProjects(rollupByProject(rows))
      } catch (error) {
        if (!isActive) return
        setErrorMessage(
          error instanceof RevenueRecognitionError
            ? error.message
            : 'The governed recognized-revenue seam could not be reached from the browser shell.',
        )
        setProjects([])
      } finally {
        if (isActive) setIsLoading(false)
      }
    }
    void load()
    return () => {
      isActive = false
    }
  }, [])

  return (
    <main className="shell-page pm-review-page">
      <section className="hero-card pm-review-hero">
        <p className="eyebrow">PM Execution → Billing</p>
        <div className="hero-grid pm-review-hero-grid">
          <div>
            <h1>Recognized revenue by project (read-only).</h1>
            <p className="lede">
              Recognized = quoted revenue of apparatus marked Complete (binary, at completion),
              derived from apparatus completion — not yet a persisted recognition ledger. Billable =
              recognized − billed; billing is not admitted, so billable equals recognized. This route
              is read-only: it admits no billing, invoice, payroll, accounting, export, or source
              writeback.
            </p>
          </div>
          <dl className="contract-panel">
            <div><dt>Promoted route</dt><dd>/pm-review/finance</dd></div>
            <div><dt>Current route class</dt><dd>Read-only derived recognized-revenue view</dd></div>
            <div><dt>Authority posture</dt><dd>Finance READ admitted; finance writes remain held</dd></div>
          </dl>
        </div>
      </section>

      <section className="notes-card pm-review-card">
        <div className="pm-review-header">
          <div>
            <h2>Recognized Revenue</h2>
            <p>Derived live through the governed control-plane API; no direct browser database reads.</p>
          </div>
          <p className="pm-review-link-row">
            <Link href="/pm-review">Return to PM drivers</Link>
            <Link href="/pm-review/project-overview">Project overview</Link>
            <Link href="/pm-review/finance-placeholder">Finance placeholder (writes held)</Link>
          </p>
        </div>

        {isLoading ? <p className="resource-banner resource-banner-neutral">Loading recognized revenue…</p> : null}
        {errorMessage ? <p className="resource-banner resource-banner-error">{errorMessage}</p> : null}

        {!isLoading && !errorMessage ? (
          <div className="resource-results">
            {projects.length === 0 ? (
              <p className="resource-banner resource-banner-neutral">No active projects with quoted revenue yet.</p>
            ) : null}
            <div className="resource-grid">
              {projects.map((project) => (
                <article className="resource-item" key={project.project_id}>
                  <div className="resource-item-row">
                    <span className="resource-chip">{project.recognition_percent.toFixed(2)}% recognized</span>
                    <span className="resource-chip resource-chip-muted">
                      {project.completed_apparatus}/{project.total_apparatus} apparatus complete
                    </span>
                  </div>
                  <h3>
                    {[project.project_number, project.project_name]
                      .filter((value) => typeof value === 'string' && value.trim().length > 0)
                      .join(' · ') || 'Unnamed project'}
                  </h3>
                  <dl>
                    <div><dt>Quoted</dt><dd>{usd(project.quoted_revenue)}</dd></div>
                    <div><dt>Recognized</dt><dd>{usd(project.recognized_revenue)}</dd></div>
                    <div><dt>Billable now</dt><dd>{usd(project.billable_now)}</dd></div>
                  </dl>
                  <ul>
                    {project.scopes.map((scope) => (
                      <li key={scope.scope_id ?? scope.scope_name ?? 'scope'}>
                        {scope.scope_name ?? 'Unnamed scope'}: {usd(scope.recognized_revenue)} of {usd(scope.quoted_revenue)} ({scope.recognition_percent.toFixed(2)}%)
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>
        ) : null}
      </section>
    </main>
  )
}
```

- [ ] **Step 4: Run the smoke to verify it passes**

Run: `cd /home/olares/code/apex/apex-power-ops-platform && pnpm --filter @apex/operations-web exec next build && pnpm --filter @apex/operations-web exec playwright test tests/browser-shell.pm-finance.smoke.spec.ts`
Expected: PASS (1 passed).

- [ ] **Step 5: Add the placeholder pointer (additive) + assertion**

In `apps/operations-web/app/pm-review/finance-placeholder/page.tsx`, inside the `pm-review-link-row` paragraph (the one with the existing Links), add this Link as the first child so the existing copy/headings are unchanged:

```tsx
            <Link href="/pm-review/finance">Recognized revenue (read-only, admitted)</Link>
```

- [ ] **Step 6: Add one assertion to the existing placeholder smoke**

In `apps/operations-web/tests/browser-shell.pm-finance-placeholder.smoke.spec.ts`, add this line just before the final `expect(mutationRequests).toHaveLength(0)`:

```ts
  await expect(page.getByRole('link', { name: /Recognized revenue \(read-only, admitted\)/i })).toHaveAttribute('href', '/pm-review/finance')
```

- [ ] **Step 7: Run both finance smokes**

Run: `cd /home/olares/code/apex/apex-power-ops-platform && pnpm --filter @apex/operations-web exec next build && pnpm --filter @apex/operations-web exec playwright test tests/browser-shell.pm-finance.smoke.spec.ts tests/browser-shell.pm-finance-placeholder.smoke.spec.ts`
Expected: PASS (2 passed).

- [ ] **Step 8: Commit**

```bash
cd /home/olares/code/apex/apex-power-ops-platform
git add apps/operations-web/app/pm-review/finance/page.tsx apps/operations-web/app/pm-review/finance-placeholder/page.tsx apps/operations-web/tests/browser-shell.pm-finance.smoke.spec.ts apps/operations-web/tests/browser-shell.pm-finance-placeholder.smoke.spec.ts
git commit -m "feat(operations-web): /pm-review/finance recognized-revenue read view + placeholder pointer"
```

---

## Definition of done

- `GET /api/v1/ops/revenue-recognition` returns scope-grain derived recognized revenue; unit test (mocked) + integration test (seeded slice, exact math) green.
- `/pm-review/finance` renders project/scope recognized revenue with the honesty label; smoke green; no mutation calls.
- `finance-placeholder` points to the admitted read view; its smoke (incl. the new assertion) green.
- No prod DDL, no writes, no new authority; held branches untouched.
- Branch `ops/recognized-revenue` ready for review/merge (operator-gated, like the records lane).
