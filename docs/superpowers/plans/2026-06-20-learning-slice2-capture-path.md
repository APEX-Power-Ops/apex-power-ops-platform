# Learning Slice 2a — Capture Path — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Rev 2 (2026-06-20):** revised after a technical-authority review of `de5de202` (9 findings). Changes: a lane charter is now Task 1 (lane SSoT); the `learning_dev` schema apply is a deferred human-approval **gate**, not an unattended step; all `source` paths are absolute; API tests run via `uv run --with-requirements` (no venv path juggling); the browser smoke lives under `tests/` (the real `testDir`) and **proves capture** via route-mocking instead of static render; package + UI now carry per-event-type **payload** (assessment score / self-assessment confidence).
>
> **Rev 3 (2026-06-20):** a second technical-authority review found 7 gaps in the **merged Slice 1** (resolver/API/demo) that this lane builds on — several are Slice 1 not matching its own spec. Operator chose "fold into this lane." Two **Slice-1 hardening tasks** (1a resolver, 1b API) are prepended (verify-before-build), and the demo (Task 6) gains source-grouping + a seeded section typeahead. Findings: #1 curated `neta_procedure` refs dropped the target id; #2 `get_resources` returned 422/200 not 400 for missing/blank + accepted any `level`; #3 learning routes registered unconditionally → 500 on Render (no `LEARNING_DEV_DSN` in `render.yaml`); #4 demo lacked typeahead + source-grouping; #5 no browser smoke (now covered by Task 6's proving smoke); #6 dedupe/merge tests were data-coincidence false-green; #7 level-rerank test asserted membership only.
>
> **Execution order:** Task 0 → Task 1 → **Task 1a → Task 1b** → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Gated activation.

**Goal:** Build the end-to-end mechanism that lets a real tech record the first real learning event — an append-only `learning_events` ledger, a `learning-capture` package, write/read API routes, and a capture panel on the Slice 1 demo.

**Architecture:** A write vertical mirroring Slice 1's read vertical (`resolve → API → demo`). A new additive migration lane (`infra/database/migrations/learning/`) adds a person-spine bridge column to `user_profiles` and an append-only `learning_events` table. A `learning-capture` Python package (mirroring `learning-resolver`, but read-WRITE) exposes `record_event` / `list_events` / `list_users`. The existing `control-plane-api` learning router is extended with `POST/GET /events` + `GET /users`. The `operations-web /learning-demo` page gains a capture panel so the resolve→capture loop is one screen.

**Tech Stack:** PostgreSQL 17 (`learning_dev` / throwaway `learning_test` on host `127.0.0.1:5432`), Python 3.11 + `psycopg[binary]>=3.1`, FastAPI (control-plane-api), Next.js + Playwright (operations-web). All work on the Olares host over mesh SSH (`ssh olares-mesh`).

## Global Constraints

- **Lane discipline (SSoT):** this lane MUST be chartered in `docs/lanes/README.md` (Task 1) before code lands — worktree + branch + dev DB + write-boundary + gates. Lane: `learning`; branch `learning/slice2-capture`; worktree `/home/olares/code/apex/apex-learning-lane` (off main `82c3b97b`; `infra/.env` symlinked there already).
- **All DB writes target `learning_dev` only** (or throwaway `learning_test` for tests). NO prod writes.
- **`schema` is a human-approval GATE.** All build/test runs against the throwaway `learning_test`. Applying `001`+`002` to `learning_dev` is a **separate, operator-approved gated step** (see "Gated activation" at the end) — never an unattended plan step. Nothing in the build/test flow requires `learning_dev` to be migrated.
- **Promotion (merge to main) is operator-gated** — land via PR.
- **Migration tests run against `learning_test`, never `learning_dev`.** `learning_events` FKs reference `public.user_profiles` + `public.study_content`, which a bare test DB lacks → an idempotent `test_prereq.sql` creates minimal stub tables + seed rows first.
- **The ledger is append-only:** a DB trigger raises on UPDATE/DELETE; the package issues INSERT/SELECT only.
- **Event-type vocab is exactly 4 text values** (CHECK, not an enum): `resource_viewed`, `resource_completed`, `assessment_completed`, `self_assessment`. **Payload shape is the package's job** (per the spec): `assessment_completed` requires numeric `score_percent` (0–100); `self_assessment` requires int `confidence` (1–5); the two resource events ignore payload.
- **The integration contract is the NETA section** — `neta_section` on an event is the same `records.neta_procedures.section` / `study_content.neta_section_primary` key Slice 1 resolves on.
- **The person-spine bridge** `public.user_profiles.employee_id` is a cross-DB **contract-FK** to prod `public.employees.id` — app-enforced, **no DB FK** (employees is a separate database). Mirrors `records.persons.employee_ref` / `ops.persons.employee_ref`.
- **control-plane-api = pip + requirements.txt (NOT uv) for deploy**, but **tests run via `uv run --with-requirements requirements-dev.txt`** (self-contained; the worktree has no `.venv`). Wire the package as `-e ../../packages/learning-capture`. **Do NOT commit any `uv.lock`** (a `uv run` byproduct — `git rm` + `.gitignore` if it appears).
- **DB password discipline:** always `source /home/olares/code/apex/apex-learning-lane/infra/.env` (ABSOLUTE path — relative `../../../infra/.env` from a migrations subdir resolves wrong) to get `DEV_PG_PASSWORD` (UNQUOTED). NEVER `grep|cut` it (the §259 split-brain bug).
- **Host file edits:** write the file locally then `ssh olares-mesh 'cat > <abs-dest>' < <localfile>` (heredocs break on code quotes). **ssh commit messages must avoid apostrophes** (use `git commit -F`).
- **uv on PATH for tests:** `export PATH="$HOME/.local/bin:$PATH"`. Node/pnpm for operations-web: `. $HOME/.nvm/nvm.sh` (and `corepack enable` if pnpm is missing).

---

### Task 0: One-time host setup (throwaway test DB)

**Files:** none (host setup only).

- [ ] **Step 1: Create the throwaway `learning_test` DB (idempotent)**

Run:
```bash
ssh olares-mesh 'source /home/olares/code/apex/apex-learning-lane/infra/.env; \
  PGPASSWORD=$DEV_PG_PASSWORD psql -h 127.0.0.1 -p 5432 -U postgres -tAc \
  "select 1 from pg_database where datname='"'"'learning_test'"'"'" | grep -q 1 \
  || PGPASSWORD=$DEV_PG_PASSWORD psql -h 127.0.0.1 -p 5432 -U postgres -c "CREATE DATABASE learning_test;"'
```
Expected: prints `CREATE DATABASE` (first run) or nothing (already exists).

---

### Task 1: Charter the `learning` lane in the lane SSoT

**Files:**
- Modify: `docs/lanes/README.md` (add a `### Lane: learning` block under `## Active lanes`).

**Interfaces:**
- Consumes: nothing.
- Produces: the lane charter (write-boundary + gates) that governs every later task. No code depends on it, but the lane is not "real" until it is recorded here (SSoT-not-chat).

- [ ] **Step 1: Add the learning lane charter**

Insert this block in `docs/lanes/README.md` immediately AFTER the `### Lane: ops` block's `- **Status:**` line and BEFORE the `> Merged/closed lanes` note:

```markdown
### Lane: learning (enablement / capture + ROI)
- **Scope:** the flagship learning lane — contextual resource surfacing (Slice 1, merged) + the capture/tracking path (Slice 2) — DEV ONLY.
- **Branch:** `learning/slice2-capture`   **Worktree:** `/home/olares/code/apex/apex-learning-lane`
- **Dev DB / schema:** `learning_dev` → `public.*` (frozen rev-2.3/2.4 baseline; lane isolation = the database, per separate-DB-per-lane D-ARCH-1)
- **Write-boundary (OWNS):** `infra/database/migrations/learning/**`, `packages/learning-capture/**`,
  `packages/learning-resolver/**` (Slice-1 hardening), `apps/control-plane-api/services/learning/**`
  (+ the `-e ../../packages/learning-capture` line in `requirements.txt`; + the learning-router guard in `main.py`),
  `apps/operations-web/app/learning-demo/**`, `apps/operations-web/lib/learning-*.ts`,
  `apps/operations-web/tests/learning-*.spec.ts`, `docs/superpowers/{specs,plans}/2026-06-20-learning-slice2-*`.
- **Must NOT touch:** `records.*` / `ops.*` migrations + packages; the parallel `packages/power-test-converters/**` WIP; prod Supabase.
- **Gates (human-approval):** `schema` (the `learning_dev` apply of `001`/`002` — see the plan's gated activation step); promotion (merge to main) is operator-gated.
- **Escalation / owner:** CC (technical authority); operator gates schema apply + merge.
- **Status:** active (Slice 2a built on `learning_test`; `learning_dev` apply + PR operator-gated).
```

- [ ] **Step 2: Verify the charter is present**

Run:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && grep -n "Lane: learning" docs/lanes/README.md && grep -c "Gates" docs/lanes/README.md'
```
Expected: the `### Lane: learning` heading line prints; `Gates` count is now 3 (records, ops, learning).

- [ ] **Step 3: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git add docs/lanes/README.md && git commit -F - <<"EOF"
docs(lanes): charter the learning lane

Records the learning lane in the lane SSoT (worktree + branch + learning_dev + write-boundary +
schema gate), per docs/lanes/README.md. Required before Slice 2 code lands.
EOF'
```

---

### Task 1a: Resolver hardening (Slice-1 findings #1, #6, #7 + sections source)

**Files:**
- Modify: `packages/learning-resolver/src/learning_resolver/resolver.py`
- Modify: `packages/learning-resolver/src/learning_resolver/__init__.py`
- Test: `packages/learning-resolver/tests/test_hardening.py`

**Interfaces:**
- Produces: curated `neta_procedure` references now include `id` (the `neta_procedure_id`); new `list_sections(limit: int = 500) -> list[str]` (distinct `neta_procedures.section_number`). Task 1b's `GET /sections` and Task 6's typeahead consume `list_sections`.

- [ ] **Step 1: Write the failing test `tests/test_hardening.py`**

```python
"""Slice-1 resolver hardening: target-id in curated neta_procedure refs (#1), dedup exclusion (#6),
level-rerank math (#7), and list_sections for the typeahead (#4 support). The first three use a fake
connection so they are deterministic (no data coincidence); list_sections hits learning_dev (read).

Run (host, from packages/learning-resolver/):
  export PATH="$HOME/.local/bin:$PATH"; source /home/olares/code/apex/apex-learning-lane/infra/.env
  LEARNING_DEV_PGPASSWORD=$DEV_PG_PASSWORD \
    uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests/test_hardening.py -q
"""
from learning_resolver.resolver import _curated, _level_boost, _section_match, list_sections


class FakeConn:
    """Minimal psycopg-like stand-in: execute(...).fetchall()/fetchone() return canned rows."""
    def __init__(self, rows):
        self._rows = rows
    def execute(self, sql, params=None):
        return self
    def fetchall(self):
        return self._rows
    def fetchone(self):
        return self._rows[0] if self._rows else None


def test_curated_neta_procedure_ref_includes_id():
    # _curated row: (rtype, is_primary, is_mandatory, display_order, sc_id, np_id, url, rname,
    #                sc_title, sc_slug, sc_summary, sc_level, np_title, np_section)
    row = ("procedure", True, False, 0, None, "np-uuid-1", None, None,
           None, None, None, None, "Inspect breaker", "7.2.1.1")
    out = _curated(FakeConn([row]), ["apt-1"])
    assert out[0].reference == {"kind": "neta_procedure", "section": "7.2.1.1", "id": "np-uuid-1"}


def test_section_match_excludes_curated_study_content_ids():
    # _section_match row: (sc_id, title, slug, summary, level, primary_hit, quality_tier)
    rows = [
        ("dup-sc", "Dup", "dup", "s", "II", True, "gold"),
        ("keep-sc", "Keep", "keep", "s", "II", True, "gold"),
    ]
    out = _section_match(FakeConn(rows), "7.2.1.1", exclude_sc_ids={"dup-sc"})
    assert {r.reference["id"] for r in out} == {"keep-sc"}   # the curated duplicate is removed


def test_level_boost_exact_values():
    assert _level_boost("III", "III") == 30.0   # exact
    assert _level_boost("II", "III") == 10.0    # one level off
    assert _level_boost("II", "IV") == 0.0      # two off
    assert _level_boost(None, "III") == 0.0     # unknown -> no boost


def test_list_sections_returns_known_section():
    sections = list_sections()
    assert isinstance(sections, list) and sections
    assert "7.2.1.1" in sections
```

- [ ] **Step 2: Run the test, verify it fails**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/packages/learning-resolver; source /home/olares/code/apex/apex-learning-lane/infra/.env; LEARNING_DEV_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests/test_hardening.py -q'
```
Expected: FAIL — `ImportError: cannot import name 'list_sections'`; and the curated-ref test fails (ref lacks `id`).

- [ ] **Step 3: Fix `resolver.py` — add the target id + `list_sections`**

In `_curated`, change the `neta_procedure` branch from:
```python
        elif np_id is not None:
            title, ref, level = np_title, {"kind": "neta_procedure", "section": np_section}, None
```
to:
```python
        elif np_id is not None:
            title, ref, level = np_title, {"kind": "neta_procedure", "section": np_section, "id": str(np_id)}, None
```
Append `list_sections` to `resolver.py`:
```python
def list_sections(limit: int = 500) -> list[str]:
    """Distinct NETA section numbers (seeds the demo typeahead). Read-only."""
    with connect() as conn:
        rows = conn.execute(
            "select distinct section_number from neta_procedures "
            "where section_number is not null order by section_number limit %s",
            (limit,),
        ).fetchall()
    return [r[0] for r in rows]
```

- [ ] **Step 4: Update `__init__.py` to export `list_sections`**

```python
from .models import ResolvedResource
from .resolver import list_sections, resolve

__all__ = ["resolve", "list_sections", "ResolvedResource"]
```

- [ ] **Step 5: Run the test, verify it passes**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/packages/learning-resolver; source /home/olares/code/apex/apex-learning-lane/infra/.env; LEARNING_DEV_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests/test_hardening.py -q'
```
Expected: PASS (4 passed). Also run the full resolver suite to confirm no regression:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/packages/learning-resolver; source /home/olares/code/apex/apex-learning-lane/infra/.env; LEARNING_DEV_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests -q'
```
Expected: PASS (18 passed: the 14 Slice-1 tests + 4 hardening).

- [ ] **Step 6: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git add packages/learning-resolver/ && git commit -F - <<"EOF"
fix(learning): resolver hardening (target-id, dedup + rerank rigor, sections)

Slice-1 review fixes: curated neta_procedure references now carry the concrete neta_procedure_id
(#1); deterministic fake-conn tests prove dedup exclusion (#6) and exact level-rerank math (#7);
new list_sections() seeds the demo section typeahead (#4 support). 18 resolver tests green.
EOF'
```

---

### Task 1b: API hardening (Slice-1 findings #2, #3 + GET /sections)

**Files:**
- Modify: `apps/control-plane-api/services/learning/router.py`
- Modify: `apps/control-plane-api/services/learning/schemas.py`
- Modify: `apps/control-plane-api/main.py`
- Test: `apps/control-plane-api/tests/test_learning_resources.py`

**Interfaces:**
- Consumes: `learning_resolver.list_sections` (Task 1a).
- Produces: `get_resources` returns `400` for missing/blank `neta_section` and invalid `level`; `GET /api/v1/learning/sections -> {sections: [str]}`; the learning router registers ONLY when `LEARNING_DEV_DSN`/`LEARNING_DEV_PGPASSWORD` is set (prod-safe — no 500ing routes on Render). **Task 5 (capture routes) appends to this same `router.py`/`schemas.py`; its fastapi import (`HTTPException, status`) is already added here.** Task 6's typeahead consumes `GET /sections`.

- [ ] **Step 1: Write the failing tests (REPLACE the contradictory `test_missing_section_is_400` + add cases)**

In `apps/control-plane-api/tests/test_learning_resources.py`, replace the existing `test_missing_section_is_400` body (it asserts `422`) and append the new cases:
```python
def test_missing_section_is_400():
    assert client.get("/api/v1/learning/resources").status_code == 400


def test_blank_section_is_400():
    assert client.get("/api/v1/learning/resources", params={"neta_section": "   "}).status_code == 400


def test_invalid_level_is_400():
    r = client.get("/api/v1/learning/resources", params={"neta_section": "7.2.1.1", "level": "banana"})
    assert r.status_code == 400


def test_sections_endpoint_lists_known_section():
    r = client.get("/api/v1/learning/sections")
    assert r.status_code == 200
    assert "7.2.1.1" in r.json()["sections"]


def test_learning_routes_guarded_by_env(monkeypatch):
    from main import _learning_routes_enabled
    monkeypatch.delenv("LEARNING_DEV_DSN", raising=False)
    monkeypatch.delenv("LEARNING_DEV_PGPASSWORD", raising=False)
    assert _learning_routes_enabled() is False
    monkeypatch.setenv("LEARNING_DEV_DSN", "host=127.0.0.1 dbname=learning_dev")
    assert _learning_routes_enabled() is True
```
Keep the existing `test_unknown_section_returns_empty_200` and `test_known_section_returns_ranked_resources`.

- [ ] **Step 2: Run the tests, verify they fail**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/apps/control-plane-api; source /home/olares/code/apex/apex-learning-lane/infra/.env; \
  DATABASE_URL="postgresql://postgres:$DEV_PG_PASSWORD@127.0.0.1:5432/learning_dev" \
  LEARNING_DEV_PGPASSWORD=$DEV_PG_PASSWORD \
    uv run --with-requirements requirements-dev.txt pytest tests/test_learning_resources.py -q'
```
Expected: FAIL — missing-section returns 422 not 400; `/sections` 404; `_learning_routes_enabled` import error.

- [ ] **Step 3: Add `SectionsResponse` to `schemas.py`**

Append to `apps/control-plane-api/services/learning/schemas.py`:
```python
class SectionsResponse(BaseModel):
    sections: list[str]
```

- [ ] **Step 4: Harden `router.py` (validation + `/sections`)**

Change the existing imports at the top of `router.py` from:
```python
from fastapi import APIRouter, Query

from learning_resolver import resolve

from .schemas import ResolvedResourceOut, ResourcesContext, ResourcesResponse
```
to:
```python
from fastapi import APIRouter, HTTPException, Query, status

from learning_resolver import list_sections, resolve

from .schemas import ResolvedResourceOut, ResourcesContext, ResourcesResponse, SectionsResponse
```
Replace the existing `get_resources` function with the validated version, and add `get_sections`:
```python
@router.get("/resources", response_model=ResourcesResponse)
def get_resources(
    neta_section: str | None = Query(default=None),
    level: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> ResourcesResponse:
    if not neta_section or not neta_section.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="neta_section is required")
    if level is not None and level not in {"II", "III", "IV"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="level must be II, III, or IV")
    section = neta_section.strip()
    items = resolve(section, level=level, limit=limit)
    return ResourcesResponse(
        context=ResourcesContext(neta_section=section, level=level, limit=limit),
        resources=[ResolvedResourceOut(**vars(r)) for r in items],
    )


@router.get("/sections", response_model=SectionsResponse)
def get_sections(limit: int = Query(default=500, ge=1, le=2000)) -> SectionsResponse:
    return SectionsResponse(sections=list_sections(limit=limit))
```

- [ ] **Step 5: Guard the learning router in `main.py` (prod-safe)**

Add a predicate near the other helpers in `apps/control-plane-api/main.py` (it imports `os` already):
```python
def _learning_routes_enabled() -> bool:
    # learning_dev is host-only (mesh PG17); on Render no learning DSN is set -> do not expose
    # routes that would 500. Keyed on the learning-specific config, NOT the generic PGPASSWORD.
    return bool(os.environ.get("LEARNING_DEV_DSN") or os.environ.get("LEARNING_DEV_PGPASSWORD"))
```
Replace the unconditional `app.include_router(learning_router)` (currently line ~97) with:
```python
if _learning_routes_enabled():
    app.include_router(learning_router)
```

- [ ] **Step 6: Run the tests, verify they pass**

Run (same command as Step 2):
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/apps/control-plane-api; source /home/olares/code/apex/apex-learning-lane/infra/.env; \
  DATABASE_URL="postgresql://postgres:$DEV_PG_PASSWORD@127.0.0.1:5432/learning_dev" \
  LEARNING_DEV_PGPASSWORD=$DEV_PG_PASSWORD \
    uv run --with-requirements requirements-dev.txt pytest tests/test_learning_resources.py -q'
```
Expected: PASS (8 passed: 3 original-style + 5 new).

- [ ] **Step 7: Verify no `uv.lock`; commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && (git status --porcelain | grep -i "uv.lock" && echo "REMOVE THESE" || echo "clean") && git add apps/control-plane-api/services/learning/router.py apps/control-plane-api/services/learning/schemas.py apps/control-plane-api/main.py apps/control-plane-api/tests/test_learning_resources.py && git commit -F - <<"EOF"
fix(learning): API hardening (400 validation, route guard, GET sections)

Slice-1 review fixes: get_resources returns 400 for missing/blank neta_section and invalid level
(#2); the learning router registers only when LEARNING_DEV_DSN/PGPASSWORD is set so the hosted
Render deploy does not expose 500ing routes (#3); new GET /api/v1/learning/sections seeds the demo
typeahead (#4). 8 resource tests green.
EOF'
```

---

### Task 2: Migration lane scaffold + `001` person bridge

**Files:**
- Create: `infra/database/migrations/learning/test_prereq.sql`
- Create: `infra/database/migrations/learning/conftest.py`
- Create: `infra/database/migrations/learning/001_person_bridge.sql`
- Create: `infra/database/migrations/learning/001_person_bridge_down.sql`
- Create: `infra/database/migrations/learning/MANIFEST.md`
- Test: `infra/database/migrations/learning/test_001_person_bridge.py`

**Interfaces:**
- Consumes: a `learning_test` DB (Task 0). The test DSN defaults to `dbname=learning_test`.
- Produces: `public.user_profiles.employee_id uuid null` (partial-unique, no DB FK). `test_prereq.sql` + `conftest.py` are reused by Task 3 and Task 4.

- [ ] **Step 1: Write `test_prereq.sql` (idempotent stubs for the throwaway DB)**

```sql
-- Throwaway learning_test bootstrap. Minimal stand-ins for the baseline tables the learning
-- migrations reference (the real learning_dev has the full frozen baseline). Idempotent so the
-- migration- and package-test fixtures can apply it repeatedly.
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
Create the DB first (Task 0).
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
  export PATH="$HOME/.local/bin:$PATH"; source /home/olares/code/apex/apex-learning-lane/infra/.env
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
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/infra/database/migrations/learning; source /home/olares/code/apex/apex-learning-lane/infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest pytest test_001_person_bridge.py -q'
```
Expected: FAIL — `001_person_bridge.sql` does not exist (the `migrate` fixture errors reading the file).

- [ ] **Step 5: Write `001_person_bridge.sql`**

```sql
-- ============================================================================
-- learning migration 001 -- person bridge (public.user_profiles.employee_id).
-- Phase-5 additive identity slice / learning Slice 2a.
-- Authority: docs/superpowers/specs/2026-06-20-learning-slice2-capture-path-design.md;
--            .claude/PLATFORM/INTEGRATION_BACKBONE_IDENTITY_CONTRACT_2026-06-20.md (C1/D2).
-- Dev DB: learning_dev (apply is an operator-gated step; tests use learning_test). Nothing to prod.
-- Mirrors the column the prod migration additive_person_spine_prod already added to
-- public.user_profiles -- but here it is a cross-DB CONTRACT-FK to prod public.employees.id
-- (app-enforced, NO db FK: employees lives in a different database).
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
per separate-DB-per-lane D-ARCH-1). **`learning_dev` apply is an operator-gated `schema` step**
(see the Slice 2a plan); validation runs on the throwaway `learning_test`.

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
- Each migration ships a reversible `_down`. Validation gate = down → up → invariant tests → down clean on `learning_test`.
- Applying to `learning_dev` is a SEPARATE operator-approved `schema` gate (additive/idempotent).

## Deferred (later sub-slices)
2b: derive `user_study_progress` / `user_test_attempts` projections + management dashboards · 2c: ROI
correlation (learning_events → records/ops field output via `employee_id` + NETA section).
```

- [ ] **Step 8: Run the test, verify it passes**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/infra/database/migrations/learning; source /home/olares/code/apex/apex-learning-lane/infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest pytest test_001_person_bridge.py -q'
```
Expected: PASS (4 passed).

- [ ] **Step 9: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git add infra/database/migrations/learning/ && git commit -F - <<"EOF"
feat(learning): migration lane + 001 person bridge

New infra/database/migrations/learning lane. 001 adds public.user_profiles.employee_id
(cross-DB contract-FK to prod employees; partial-unique, no db FK). Validated on throwaway
learning_test; learning_dev apply is a gated step.
EOF'
```

---

### Task 3: `002` append-only `learning_events`

**Files:**
- Create: `infra/database/migrations/learning/002_learning_events.sql`
- Create: `infra/database/migrations/learning/002_learning_events_down.sql`
- Test: `infra/database/migrations/learning/test_002_learning_events.py`

**Interfaces:**
- Consumes: `test_prereq.sql` (stub `user_profiles` + `study_content`); seed UUIDs `…0001` (user) / `…0010` (study_content).
- Produces: `public.learning_events` — `event_id uuid pk`, `user_id uuid not null`, `event_type text`, `study_content_id uuid null`, `neta_section text null`, `occurred_at timestamptz`, `payload jsonb`, `created_at timestamptz`. Append-only (UPDATE/DELETE blocked). Task 4's package INSERTs/SELECTs these columns.

- [ ] **Step 1: Write the failing test `test_002_learning_events.py`**

```python
"""learning migration 002 -- append-only learning_events ledger: TDD.

Capture substrate for Slice 2a. Immutable (UPDATE/DELETE blocked by a trigger). Runs against the
throwaway learning_test (conftest applies test_prereq.sql -> stub user_profiles + study_content +
seed rows 0001 / 0010).

Run (host, from infra/database/migrations/learning/):
  export PATH="$HOME/.local/bin:$PATH"; source /home/olares/code/apex/apex-learning-lane/infra/.env
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
        assert _insert(conn, etype) is not None


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
    rule = _scalar(
        "select confdeltype from pg_constraint "
        "where conrelid='public.learning_events'::regclass and contype='f' and conname like '%study_content%'"
    )
    assert rule == "n"  # 'n' = SET NULL


def test_user_fk_cascade_semantics():
    rule = _scalar(
        "select confdeltype from pg_constraint "
        "where conrelid='public.learning_events'::regclass and contype='f' and conname like '%user_id%'"
    )
    assert rule == "c"  # 'c' = CASCADE
```

- [ ] **Step 2: Run the test, verify it fails**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/infra/database/migrations/learning; source /home/olares/code/apex/apex-learning-lane/infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest pytest test_002_learning_events.py -q'
```
Expected: FAIL — `002_learning_events.sql` does not exist.

- [ ] **Step 3: Write `002_learning_events.sql`**

```sql
-- ============================================================================
-- learning migration 002 -- append-only learning_events capture ledger. Slice 2a.
-- Authority: docs/superpowers/specs/2026-06-20-learning-slice2-capture-path-design.md.
-- Dev DB: learning_dev (apply gated). The immutable substrate every later projection
-- (user_study_progress / user_test_attempts) and ROI metric derives from. event_type is a text
-- CHECK vocab (extensible, per the records-lane preference); payload jsonb is the open extension
-- point (score_percent, confidence, duration_seconds, source surface, apparatus_type, ...).
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
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/infra/database/migrations/learning; source /home/olares/code/apex/apex-learning-lane/infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest pytest test_002_learning_events.py -q'
```
Expected: PASS (8 passed).

- [ ] **Step 6: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git add infra/database/migrations/learning/ && git commit -F - <<"EOF"
feat(learning): 002 append-only learning_events ledger

Immutable capture substrate (UPDATE/DELETE blocked by trigger; event_type CHECK vocab;
user CASCADE / study_content SET NULL FKs; neta_section work-context; payload jsonb).
Validated on learning_test (8/8). learning_dev apply is a gated step.
EOF'
```

---

### Task 4: `packages/learning-capture` (record/list events + users + CLI + payload rules)

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
- Consumes: the migrated `learning_test` schema (Task 2+3 SQL files, applied by the package conftest); seed UUIDs `…0001` / `…0010`.
- Produces:
  - `record_event(user_id: str, event_type: str, *, study_content_id: str | None = None, neta_section: str | None = None, payload: dict | None = None) -> CapturedEvent`
  - `list_events(user_id: str | None = None, limit: int = 50) -> list[CapturedEvent]`
  - `list_users(limit: int = 100) -> list[dict]` (`{"id": str, "email": str}`)
  - `CapturedEvent` dataclass: `event_id, user_id, event_type, study_content_id, neta_section, occurred_at, payload, created_at`
  - `CaptureError(ValueError)`; `EVENT_TYPES: frozenset[str]`
  - **Payload rules:** `assessment_completed` requires numeric `score_percent` in [0,100]; `self_assessment` requires int `confidence` in [1,5]; resource events ignore payload.
  Task 5's API imports `record_event`, `list_events`, `list_users`, `CaptureError`.

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


def test_record_event_rejects_unknown_type():
    with pytest.raises(CaptureError):
        record_event(USER, "bogus")


def test_record_event_rejects_unknown_user():
    with pytest.raises(CaptureError):
        record_event("22222222-2222-2222-2222-222222222222", "resource_viewed")


def test_record_event_rejects_unknown_content():
    with pytest.raises(CaptureError):
        record_event(USER, "resource_viewed", study_content_id="33333333-3333-3333-3333-333333333333")


def test_assessment_requires_score_percent():
    with pytest.raises(CaptureError):
        record_event(USER, "assessment_completed")                       # no payload
    with pytest.raises(CaptureError):
        record_event(USER, "assessment_completed", payload={"score_percent": 150})  # out of range
    ev = record_event(USER, "assessment_completed", payload={"score_percent": 80})
    assert ev.payload["score_percent"] == 80


def test_self_assessment_requires_confidence():
    with pytest.raises(CaptureError):
        record_event(USER, "self_assessment")                            # no payload
    with pytest.raises(CaptureError):
        record_event(USER, "self_assessment", payload={"confidence": 9})  # out of range
    ev = record_event(USER, "self_assessment", payload={"confidence": 3})
    assert ev.payload["confidence"] == 3


def test_list_events_filters_by_user_and_orders_desc():
    record_event(USER, "resource_viewed")
    record_event(USER, "resource_completed")
    rows = list_events(user_id=USER, limit=2)
    assert len(rows) == 2
    assert rows[0].occurred_at >= rows[1].occurred_at


def test_list_users_returns_seed_user():
    assert any(u["id"] == USER for u in list_users())
```

- [ ] **Step 6: Run the test, verify it fails**

Run:
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/packages/learning-capture; source /home/olares/code/apex/apex-learning-lane/infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests/test_capture.py -q'
```
Expected: FAIL — `capture.py` has no `record_event` (ImportError).

- [ ] **Step 7: Write `capture.py`**

```python
"""Capture path: append events to the learning_dev learning_events ledger. INSERT/SELECT only
(the DB trigger backs the append-only invariant). Payload shape per event_type is enforced here
(the design assigns payload validation to the package)."""
from numbers import Real

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
    """Invalid capture request (unknown event_type / missing referenced row / bad payload)."""


def _validate_payload(event_type, payload):
    if event_type == "assessment_completed":
        score = payload.get("score_percent")
        if not isinstance(score, Real) or isinstance(score, bool) or not (0 <= float(score) <= 100):
            raise CaptureError("assessment_completed requires numeric payload.score_percent in [0,100]")
    elif event_type == "self_assessment":
        conf = payload.get("confidence")
        if not isinstance(conf, int) or isinstance(conf, bool) or not (1 <= conf <= 5):
            raise CaptureError("self_assessment requires int payload.confidence in [1,5]")


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
    payload = payload or {}
    _validate_payload(event_type, payload)
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
            "payload": Json(payload),
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
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/packages/learning-capture; source /home/olares/code/apex/apex-learning-lane/infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests/test_capture.py -q'
```
Expected: PASS (8 passed).

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
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/packages/learning-capture; source /home/olares/code/apex/apex-learning-lane/infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests/test_cli.py -q'
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
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/packages/learning-capture; source /home/olares/code/apex/apex-learning-lane/infra/.env; LEARNING_TEST_PGPASSWORD=$DEV_PG_PASSWORD uv run --with "psycopg[binary]" --with pytest --with-editable . pytest tests -q'
```
Expected: PASS (10 passed: 8 capture + 2 cli).

- [ ] **Step 14: Commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git add packages/learning-capture/ && git commit -F - <<"EOF"
feat(learning): learning-capture package (record/list events + users + CLI)

record_event/list_events/list_users over the learning_dev learning_events ledger; read-WRITE db
connect (mirrors learning-resolver without the read-only session); validates event_type vocab,
referenced user/content, and per-type payload (assessment score_percent / self_assessment
confidence); INSERT/SELECT only. CLI record/list. 10 tests against throwaway learning_test.
EOF'
```

---

### Task 5: control-plane-api — `POST/GET /events` + `GET /users`

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
  The existing `learning_router` is already registered in `main.py` — extending it needs NO `main.py` change.

- [ ] **Step 1: Add the editable dep to `requirements.txt`**

Add a line directly under the existing `-e ../../packages/learning-resolver` so the block reads:
```
-e ../../packages/calc-engine
-e ../../packages/learning-resolver
-e ../../packages/learning-capture
```

- [ ] **Step 2: Bootstrap + verify the `learning_test` schema (no error suppression)**

The API tests write to `learning_test` (the package conftest is not in this dir, so apply the schema explicitly here). This step is idempotent and VERIFIED — do not suppress its output:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane; source infra/.env; export PGPASSWORD=$DEV_PG_PASSWORD; M=infra/database/migrations/learning; \
  for f in test_prereq.sql 002_learning_events_down.sql 001_person_bridge_down.sql 001_person_bridge.sql 002_learning_events.sql; do \
    echo "applying $f"; psql -h 127.0.0.1 -U postgres -d learning_test -v ON_ERROR_STOP=1 -f $M/$f || exit 1; done; \
  psql -h 127.0.0.1 -U postgres -d learning_test -tAc "select to_regclass('"'"'public.learning_events'"'"')"'
```
Expected: each `applying …` line succeeds; the final query prints `public.learning_events`. If any apply errors, STOP (do not proceed to test against stale state).

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


def test_post_self_assessment_requires_confidence():
    bad = client.post("/api/v1/learning/events", json={"user_id": USER, "event_type": "self_assessment"})
    assert bad.status_code == 400
    ok = client.post("/api/v1/learning/events",
                     json={"user_id": USER, "event_type": "self_assessment", "payload": {"confidence": 4}})
    assert ok.status_code == 201
    assert ok.json()["event"]["payload"]["confidence"] == 4


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

Run (self-contained via `uv run --with-requirements`; run from the app dir so the editable paths and `from main import app` resolve):
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/apps/control-plane-api; source /home/olares/code/apex/apex-learning-lane/infra/.env; \
  DATABASE_URL="postgresql://postgres:$DEV_PG_PASSWORD@127.0.0.1:5432/learning_test" \
  LEARNING_DEV_DSN="host=127.0.0.1 port=5432 dbname=learning_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable" \
    uv run --with-requirements requirements-dev.txt pytest tests/test_learning_events.py -q'
```
Expected: FAIL — `POST /events` returns 404/405 (route not defined yet).

- [ ] **Step 5: Extend `schemas.py`**

Change the top import of `apps/control-plane-api/services/learning/schemas.py` from `from pydantic import BaseModel` to:
```python
from datetime import datetime

from pydantic import BaseModel
```
Then append:
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

- [ ] **Step 6: Extend `router.py`**

Task 1b already changed the fastapi import to `from fastapi import APIRouter, HTTPException, Query, status` — **do not re-edit it**. Append to the file (it already defines `router`, imports from `.schemas`, and after 1b imports `list_sections, resolve` from `learning_resolver`):
```python
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

- [ ] **Step 7: Run the test, verify it passes**

Run (same command as Step 4):
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/apps/control-plane-api; source /home/olares/code/apex/apex-learning-lane/infra/.env; \
  DATABASE_URL="postgresql://postgres:$DEV_PG_PASSWORD@127.0.0.1:5432/learning_test" \
  LEARNING_DEV_DSN="host=127.0.0.1 port=5432 dbname=learning_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable" \
    uv run --with-requirements requirements-dev.txt pytest tests/test_learning_events.py -q'
```
Expected: PASS (6 passed).

- [ ] **Step 8: Confirm Slice 1 learning tests still pass (no regression)**

Run (points the resolver at the real `learning_dev`, which it reads):
```bash
ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH"; cd /home/olares/code/apex/apex-learning-lane/apps/control-plane-api; source /home/olares/code/apex/apex-learning-lane/infra/.env; \
  DATABASE_URL="postgresql://postgres:$DEV_PG_PASSWORD@127.0.0.1:5432/learning_dev" \
  LEARNING_DEV_PGPASSWORD=$DEV_PG_PASSWORD \
    uv run --with-requirements requirements-dev.txt pytest tests/test_learning_resources.py -q'
```
Expected: PASS (3 passed). (Slice 1 reads curated `7.2.1.1` from `learning_dev`, unaffected by the capture routes.)

- [ ] **Step 9: Verify no `uv.lock` got created; commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && (git status --porcelain | grep -i "uv.lock" && echo "REMOVE THESE (git rm --cached + gitignore)" || echo "clean of uv.lock")'
```
If any `uv.lock` appears, `git rm --cached` it and add to `.gitignore`. Then:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git add apps/control-plane-api/services/learning/router.py apps/control-plane-api/services/learning/schemas.py apps/control-plane-api/requirements.txt apps/control-plane-api/tests/test_learning_events.py && git commit -F - <<"EOF"
feat(learning): control-plane-api capture routes (events + users)

POST /api/v1/learning/events (201; 400 on CaptureError, incl. payload rules) + GET /events
(read-back) + GET /users, extending the Slice 1 learning router. Calls the learning-capture
package (editable dep via requirements.txt). 6 route tests against learning_test; Slice 1
resource tests still green.
EOF'
```

---

### Task 6: operations-web — capture panel on `/learning-demo` + proving smoke

**Files:**
- Create: `apps/operations-web/lib/learning-capture.ts`
- Modify: `apps/operations-web/app/learning-demo/page.tsx`
- Test: `apps/operations-web/tests/learning-capture.smoke.spec.ts` (Playwright `testDir` is `./tests`)

**Interfaces:**
- Consumes: `POST/GET /api/v1/learning/events`, `GET /api/v1/learning/users`, `GET /api/v1/learning/sections` (Task 1b); `browserEnv.controlPlaneBaseUrl`.
- Produces: a capture panel — pick a tech from `/users`, a **seeded NETA-section typeahead** (datalist from `/sections`, finding #4), resolve resources **grouped by source** (Curated, then Section matches — finding #4), mark a surfaced resource viewed/completed, log a self-assessment (confidence) or an assessment (score), and watch the captured-events list refresh. The smoke **route-mocks the API and proves the POST body + re-render** (deterministic; no live API or DB needed — the API+DB path is covered by Task 5; this also covers Slice-1 finding #5).

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

export async function fetchLearningSections(limit = 500): Promise<string[]> {
  const r = await fetch(`${base()}/api/v1/learning/sections?limit=${limit}`, { headers: { Accept: 'application/json' } })
  return ((await parse(r)) as { sections: string[] }).sections
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

- [ ] **Step 2: Replace `app/learning-demo/page.tsx` with the capture-enabled version**

Keeps the Slice 1 resolve panel; adds a tech picker, per-resource viewed/completed capture, a self-assessment (confidence) control, an assessment (score) control, and a captured-events list. Reuses the existing `resource-*` / `notes-card` / `btn` classes.

```tsx
'use client'

import { useEffect, useState } from 'react'
import { fetchLearningResources, LearningResource, LearningResourcesError } from '../../lib/learning-resources'
import {
  fetchLearningEvents,
  fetchLearningSections,
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
  const [sections, setSections] = useState<string[]>([])
  const [events, setEvents] = useState<LearningEvent[]>([])
  const [captureMessage, setCaptureMessage] = useState<string | null>(null)
  const [confidence, setConfidence] = useState('3')
  const [score, setScore] = useState('80')

  useEffect(() => {
    fetchLearningUsers()
      .then((u) => {
        setUsers(u)
        if (u.length) setUserId((prev) => prev || u[0].id)
      })
      .catch(() => setUsers([]))
    fetchLearningSections().then(setSections).catch(() => setSections([]))
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

  async function capture(eventType: string, opts?: { resource?: LearningResource; payload?: Record<string, unknown> }) {
    if (!userId) {
      setCaptureMessage('Pick a technician first.')
      return
    }
    setCaptureMessage(null)
    const ref = opts?.resource?.reference as { kind?: string; id?: string } | undefined
    try {
      await recordLearningEvent({
        user_id: userId,
        event_type: eventType,
        study_content_id: ref?.kind === 'study_content' ? ref.id ?? null : null,
        neta_section: section.trim() || null,
        payload: opts?.payload,
      })
      setCaptureMessage(`Recorded ${eventType}.`)
      await refreshEvents(userId)
    } catch (error) {
      setCaptureMessage(error instanceof LearningCaptureError ? error.message : 'Capture failed.')
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
            <input list="neta-sections" value={section} onChange={(e) => setSection(e.target.value)} placeholder="7.6.1.1.1" />
            <datalist id="neta-sections">
              {sections.map((s) => <option key={s} value={s} />)}
            </datalist>
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
              [
                { key: 'curated', label: 'Curated', items: resources.filter((r) => r.source === 'curated') },
                { key: 'section', label: 'Section matches', items: resources.filter((r) => r.source !== 'curated') },
              ]
                .filter((g) => g.items.length > 0)
                .map((g) => (
                  <div key={g.key}>
                    <p className="eyebrow">{g.label}</p>
                    <div className="resource-grid">
                      {g.items.map((r, i) => (
                        <article className="resource-item" key={`${g.key}-${i}`}>
                          <div className="resource-item-row">
                            <span className="resource-chip">{r.source === 'curated' ? 'Curated' : 'Section match'}</span>
                            {r.is_primary ? <span className="resource-chip">Primary</span> : null}
                            {r.cert_level ? <span className="resource-chip">Level {r.cert_level}</span> : null}
                          </div>
                          <h3>{r.title}</h3>
                          <p>{r.why}</p>
                          <div className="resource-item-row">
                            <button className="btn" onClick={() => capture('resource_viewed', { resource: r })}>Mark viewed</button>
                            <button className="btn" onClick={() => capture('resource_completed', { resource: r })}>Mark completed</button>
                          </div>
                        </article>
                      ))}
                    </div>
                  </div>
                ))
            )}
          </div>
        ) : null}

        <div className="resource-item-row" style={{ marginTop: '1rem', gap: '0.75rem', alignItems: 'flex-end' }}>
          <label>Confidence
            <select value={confidence} onChange={(e) => setConfidence(e.target.value)}>
              {[1, 2, 3, 4, 5].map((n) => <option key={n} value={String(n)}>{n}</option>)}
            </select>
          </label>
          <button className="btn" onClick={() => capture('self_assessment', { payload: { confidence: Number(confidence) } })}>
            Log self-assessment
          </button>
          <label>Assessment score
            <input value={score} onChange={(e) => setScore(e.target.value)} style={{ width: '5rem' }} />
          </label>
          <button className="btn" onClick={() => capture('assessment_completed', { payload: { score_percent: Number(score) } })}>
            Record assessment
          </button>
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
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane/apps/operations-web && . $HOME/.nvm/nvm.sh && (command -v pnpm >/dev/null || corepack enable) && pnpm run typecheck 2>&1 | tail -15'
```
Expected: no type errors (exit 0). Fix any before continuing.

- [ ] **Step 4: Write the failing proving smoke `tests/learning-capture.smoke.spec.ts`**

Route-mocks the control-plane API (no live API/DB needed) and proves: users load → resolve renders → "Mark viewed" POSTs the correct body → the returned event renders; and a self-assessment POSTs its `confidence` payload.

```ts
import { test, expect } from '@playwright/test'

const USER = '00000000-0000-0000-0000-000000000001'
const SC = 'aaaaaaaa-1111-1111-1111-111111111111'

test.describe('learning-demo capture loop', () => {
  test('marks a resource viewed and renders the captured event', async ({ page }) => {
    const captured: Array<Record<string, unknown>> = []

    await page.route('**/api/v1/learning/users**', (route) =>
      route.fulfill({ json: { users: [{ id: USER, email: 'tech1@example.com' }] } }),
    )
    await page.route('**/api/v1/learning/sections**', (route) =>
      route.fulfill({ json: { sections: ['7.2.1.1', '7.6.1.1.1'] } }),
    )
    await page.route('**/api/v1/learning/resources**', (route) =>
      route.fulfill({
        json: {
          context: { neta_section: '7.2.1.1', level: null, limit: 20 },
          resources: [{
            resource_type: 'study_content', title: 'Breaker basics', source: 'curated',
            reference: { kind: 'study_content', id: SC }, is_primary: true, is_mandatory: false,
            cert_level: 'II', score: 1100, why: 'curated resource for this apparatus type',
          }],
        },
      }),
    )
    await page.route('**/api/v1/learning/events**', async (route) => {
      const req = route.request()
      if (req.method() === 'POST') {
        const body = req.postDataJSON() as Record<string, unknown>
        captured.push(body)
        await route.fulfill({
          json: {
            event: {
              event_id: `e${captured.length}`, user_id: body.user_id, event_type: body.event_type,
              study_content_id: body.study_content_id ?? null, neta_section: body.neta_section ?? null,
              occurred_at: new Date().toISOString(), payload: body.payload ?? {}, created_at: new Date().toISOString(),
            },
          },
        })
      } else {
        await route.fulfill({
          json: {
            events: captured.map((b, i) => ({
              event_id: `e${i + 1}`, user_id: b.user_id, event_type: b.event_type,
              study_content_id: b.study_content_id ?? null, neta_section: b.neta_section ?? null,
              occurred_at: new Date().toISOString(), payload: b.payload ?? {}, created_at: new Date().toISOString(),
            })),
          },
        })
      }
    })

    await page.goto('/learning-demo')
    await page.getByRole('button', { name: 'Resolve' }).click()
    await expect(page.getByRole('heading', { name: 'Breaker basics' })).toBeVisible()

    await page.getByRole('button', { name: 'Mark viewed' }).first().click()
    await expect.poll(() => captured.length).toBeGreaterThan(0)
    expect(captured[0]).toMatchObject({
      user_id: USER, event_type: 'resource_viewed', neta_section: '7.2.1.1', study_content_id: SC,
    })
    await expect(page.getByText('resource_viewed').first()).toBeVisible()

    await page.getByRole('button', { name: 'Log self-assessment' }).click()
    await expect.poll(() => captured.length).toBeGreaterThan(1)
    expect(captured[captured.length - 1]).toMatchObject({
      event_type: 'self_assessment', payload: { confidence: 3 },
    })
  })
})
```

- [ ] **Step 5: Run the smoke, verify it fails then passes**

Run (build + Playwright; the spec lives in `./tests`, the real `testDir`):
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane/apps/operations-web && . $HOME/.nvm/nvm.sh && (command -v pnpm >/dev/null || corepack enable) && pnpm run smoke:browser 2>&1 | tail -25'
```
First run (before Step 2 is in place / if the page lacks the panel): the new spec FAILS. After Steps 1–2: the `learning-capture` spec PASSES. (If the broader smoke suite has unrelated pre-existing failures, confirm the `learning-capture` spec itself passes — run `pnpm exec playwright test tests/learning-capture.smoke.spec.ts` to isolate it — and note any orthogonal failures; do not fix them here.)

- [ ] **Step 6: Confirm no `uv.lock`; commit**

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && (git status --porcelain | grep -i "uv.lock" && echo "REMOVE THESE" || echo "clean of uv.lock") && git add apps/operations-web/lib/learning-capture.ts apps/operations-web/app/learning-demo/page.tsx apps/operations-web/tests/learning-capture.smoke.spec.ts && git commit -F - <<"EOF"
feat(learning): operations-web capture panel on /learning-demo

Closes the resolve to capture loop on one screen: pick a technician, resolve resources (Slice 1),
mark a surfaced resource viewed/completed, log a self-assessment (confidence) or assessment (score),
watch the captured-events list refresh. New lib/learning-capture.ts client + a route-mocked browser
smoke that PROVES the POST body and re-render. Typecheck clean.
EOF'
```

---

## Gated activation (operator-approved `schema` step — NOT part of the build/test flow)

After all tasks pass and the lane is reviewed, applying `001`+`002` to **`learning_dev`** turns the demo into a live capture surface against the real baseline (the data-acquisition enabler). This is the lane's `schema` gate — **requires the operator's explicit go** and is run as its own step (or routed through `apex-jobs` if stricter run-accounting is wanted), never silently:

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane; source infra/.env; export PGPASSWORD=$DEV_PG_PASSWORD; \
  psql -h 127.0.0.1 -U postgres -d learning_dev -v ON_ERROR_STOP=1 -f infra/database/migrations/learning/001_person_bridge.sql; \
  psql -h 127.0.0.1 -U postgres -d learning_dev -v ON_ERROR_STOP=1 -f infra/database/migrations/learning/002_learning_events.sql; \
  psql -h 127.0.0.1 -U postgres -d learning_dev -c "select column_name from information_schema.columns where table_name='"'"'user_profiles'"'"' and column_name='"'"'employee_id'"'"'"; \
  psql -h 127.0.0.1 -U postgres -d learning_dev -c "select to_regclass('"'"'public.learning_events'"'"')"'
```
Both migrations are additive/idempotent; verification prints `employee_id` and `public.learning_events`.

---

## Self-Review

**1. Spec coverage:**
- Spec §2 boundaries (learning_dev-only, deferred 2b/2c) → Global Constraints + MANIFEST "Deferred". ✓
- Spec §4 `001` person bridge → Task 2. ✓
- Spec §4 `002` append-only `learning_events` (CHECK vocab, guard trigger, indexes, FK semantics) → Task 3. ✓
- Spec §5.1 `learning-capture` package (record/list, read-WRITE db, vocab + existence + **payload-shape** validation, CLI) → Task 4 (+ `list_users`). ✓
- Spec §5.2 `POST/GET /events` extending the Slice 1 module + editable dep → Task 5 (+ `GET /users`). ✓
- Spec §5.3 capture panel extending `/learning-demo` (user picker, viewed/completed, self/assessment payload) → Task 6. ✓
- Spec §7 testing (migration throwaway, package, API, UI **proving** smoke) → tests in every task. ✓
- Spec §3 NETA-section contract + person bridge → `neta_section` column + `employee_id`. ✓
- Governance: lane chartered (Task 1); `schema` apply gated (Gated activation). ✓
- Slice-1 review findings: #1 target-id (Task 1a `_curated` np-branch + test); #2 400 validation + #3 route guard (Task 1b `get_resources` + `main._learning_routes_enabled` + tests); #4 typeahead + source-grouping (Task 1a `list_sections` → Task 1b `GET /sections` → Task 6 datalist + grouped render); #5 browser smoke (Task 6 proving smoke); #6 dedup + #7 rerank rigor (Task 1a fake-conn unit tests). ✓

**2. Placeholder scan:** No TBD/TODO; every code step shows complete code; every command shows expected output. ✓

**3. Type consistency:** `CapturedEvent` fields (Task 4 `models.py`) == `EventOut` fields (Task 5 `schemas.py`) == `LearningEvent` TS type (Task 6) — `event_id, user_id, event_type, study_content_id, neta_section, occurred_at, payload, created_at`. `record_event` signature identical in spec §5.1, Task 4 interface, Task 4 `capture.py`, and the Task 5 call site. `EVENT_TYPES` 4 values identical in `models.py`, the `002` CHECK, and the demo. Payload rules identical in `capture.py`, the package tests, the API test, and the demo controls (`confidence` 1–5; `score_percent` 0–100). Seed UUIDs (`…0001`, `…0010`) identical across `test_prereq.sql`, both migration tests, the package conftest, and the API tests. Sections path consistent: `list_sections` (Task 1a) → `SectionsResponse {sections: list[str]}` + `GET /sections` (Task 1b) → `fetchLearningSections(): Promise<string[]>` → datalist (Task 6). The route-guard predicate is `_learning_routes_enabled()` in both `main.py` and its test. ✓
