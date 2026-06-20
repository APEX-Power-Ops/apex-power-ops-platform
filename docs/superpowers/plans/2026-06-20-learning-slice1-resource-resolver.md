# Learning Slice 1 — Contextual Resource Resolver — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable resolver that, given a NETA section (+ optional cert level), returns ranked relevant learning resources — exposed via a `control-plane-api` route and shown in a thin `operations-web` demo page.

**Architecture:** A Python package `packages/learning-resolver` owns all `learning_dev` access and the hybrid ranking (curated `apparatus_type_resources` first, then `study_content` section-join, optional soft level re-rank). A thin FastAPI route in `control-plane-api` imports the package and serializes its output (it does NOT use the shared `get_db()` — that points at the platform DB, not `learning_dev`). A `'use client'` Next.js page in `operations-web` calls the route and renders the ranked list with the existing `.resource-*` CSS classes.

**Tech Stack:** Python 3.11+ / setuptools / uv / `psycopg[binary]` / pytest (package); FastAPI / Pydantic v2 (route); Next.js 16 app-router / React 19 / TypeScript (UI). All work is on the Olares host over `ssh olares-mesh`; worktree root `/home/olares/code/apex/apex-learning-lane`; branch `learning/slice1-resolver`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-06-20-learning-slice1-resource-resolver-design.md`.
- `learning_dev`-only, **read-only**, dev-stage. No writes, no prod, no auth/RLS.
- The NETA **section** is the integration contract; do NOT add a records↔learning class crosswalk.
- DSN env: `LEARNING_DEV_DSN` (full DSN) overrides; else built from `LEARNING_DEV_PGPASSWORD` → `PGPASSWORD` → `""`. Pin `host=127.0.0.1 port=5432 dbname=learning_dev user=postgres sslmode=disable` (ambient PG env points at prod — never inherit it).
- `study_content` filter: `is_active AND status = 'published'`. Cert levels: `II|III|IV`. `neta_sections_secondary` is `text[]`.
- Package name `learning-resolver`; module `learning_resolver`; mirror `packages/ops-intake` layout (`src/<module>/`, `tests/`, `[project.scripts]`).
- Run tests with `uv run pytest -q` from the package dir. Frequent commits (one per task). Commit messages must avoid apostrophes (host commits via `git commit -F -` over ssh) and end with the `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` trailer.
- All file edits land in the worktree `/home/olares/code/apex/apex-learning-lane`. Author files locally + transfer via `ssh olares-mesh 'cat > <dest>' < <localfile>` (heredocs break on apostrophes), or edit on host.

---

## File Structure

```
packages/learning-resolver/
  pyproject.toml                         # name=learning-resolver, dep psycopg[binary], script learning-resolver=learning_resolver.cli:main
  src/learning_resolver/__init__.py      # exports resolve, ResolvedResource
  src/learning_resolver/db.py            # dsn() helper + connect()
  src/learning_resolver/models.py        # ResolvedResource dataclass
  src/learning_resolver/resolver.py      # resolve() — the 5-step hybrid algorithm
  src/learning_resolver/cli.py           # argparse CLI: resolve --section ... [--level] [--limit] [--json]
  tests/conftest.py                      # dsn fixture + discovery fixtures (section_with_curated, section_study_only)
  tests/test_resolver.py                 # ranking invariants
  tests/test_cli.py                      # CLI smoke

apps/control-plane-api/
  services/learning/__init__.py
  services/learning/schemas.py           # Pydantic ResolvedResourceOut, ResourcesResponse
  services/learning/router.py            # GET /api/v1/learning/resources (no auth dep; public dev endpoint)
  main.py                                # MODIFY: include_router(learning_router)
  pyproject.toml                         # MODIFY: add learning-resolver path dependency
  tests/test_learning_resources.py       # TestClient: 200 shape, 400 missing param, empty-list section

apps/operations-web/
  lib/learning-resources.ts              # fetchLearningResources(section, level?, limit?)
  app/learning-demo/page.tsx             # thin demo page (mirrors pm-review/finance/page.tsx)
```

---

## Task 1: Scaffold `learning-resolver` package + DB access

**Files:**
- Create: `packages/learning-resolver/pyproject.toml`
- Create: `packages/learning-resolver/src/learning_resolver/__init__.py`
- Create: `packages/learning-resolver/src/learning_resolver/db.py`
- Create: `packages/learning-resolver/tests/conftest.py`
- Test: `packages/learning-resolver/tests/test_db.py`

**Interfaces:**
- Produces: `learning_resolver.db.dsn() -> str`; `learning_resolver.db.connect()` (a `psycopg` connection to `learning_dev`).

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "learning-resolver"
version = "0.1.0"
description = "Contextual learning-resource resolver (learning Slice 1; reads learning_dev)"
requires-python = ">=3.11"
dependencies = ["psycopg[binary]>=3.1"]

[project.optional-dependencies]
test = ["pytest>=8.0.0"]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[project.scripts]
learning-resolver = "learning_resolver.cli:main"
```

- [ ] **Step 2: Write `db.py`**

```python
"""learning_dev connection (read-only). DSN pinned so ambient PG env (which points at
prod) cannot redirect us -- mirrors the ops-intake pattern."""
import os

import psycopg


def dsn() -> str:
    return os.environ.get("LEARNING_DEV_DSN") or (
        "host=127.0.0.1 port=5432 dbname=learning_dev user=postgres "
        f"password={os.environ.get('LEARNING_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD', '')} "
        "sslmode=disable"
    )


def connect() -> "psycopg.Connection":
    # read-only by intent; autocommit avoids leaving idle transactions open.
    return psycopg.connect(dsn(), autocommit=True)
```

- [ ] **Step 3: Write `tests/conftest.py`** (DSN + discovery fixtures used across the suite)

```python
import os

import psycopg
import pytest

from learning_resolver.db import dsn as _dsn


@pytest.fixture(scope="session")
def dsn() -> str:
    return _dsn()


def _scalar(d, sql):
    with psycopg.connect(d, autocommit=True) as c:
        row = c.execute(sql).fetchone()
        return row[0] if row else None


@pytest.fixture(scope="session")
def section_with_curated(dsn) -> str:
    """A NETA section whose apparatus_type carries the most curated resources."""
    return _scalar(dsn, """
        select np.section_number
        from neta_procedures np
        join apparatus_type_resources atr
          on atr.apparatus_type_id = np.apparatus_type_id and atr.is_active
        where np.section_number is not null
        group by np.section_number order by count(*) desc limit 1
    """)


@pytest.fixture(scope="session")
def section_study_only(dsn) -> str:
    """A study_content section with NO curated link via a procedure (section-join only)."""
    return _scalar(dsn, """
        select sc.neta_section_primary
        from study_content sc
        where sc.neta_section_primary is not null and sc.is_active and sc.status = 'published'
          and not exists (
            select 1 from neta_procedures np
            join apparatus_type_resources atr on atr.apparatus_type_id = np.apparatus_type_id
            where np.section_number = sc.neta_section_primary)
        group by sc.neta_section_primary limit 1
    """)
```

- [ ] **Step 4: Write the failing test `tests/test_db.py`**

```python
import psycopg

from learning_resolver.db import connect, dsn


def test_dsn_targets_learning_dev():
    assert "dbname=learning_dev" in dsn()


def test_connect_reads_baseline(dsn):
    with connect() as c:
        n = c.execute("select count(*) from study_content").fetchone()[0]
    assert n > 0  # the frozen baseline is populated (967 rows)
```

- [ ] **Step 5: Verify it fails, then passes**

Run (host):
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane/packages/learning-resolver && set -a && . ../../infra/.env && set +a && export LEARNING_DEV_PGPASSWORD="$DEV_PG_PASSWORD" && uv run --extra test pytest -q'
```
Expected: first run before `db.py` exists FAILS (ImportError); after Steps 1-3 PASSES (2 passed).

- [ ] **Step 6: Commit**

```bash
ssh olares-mesh "cd /home/olares/code/apex/apex-learning-lane && git add packages/learning-resolver && git commit -q -F -" <<'MSG'
feat(learning-resolver): scaffold package + learning_dev DSN access

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
```

---

## Task 2: `ResolvedResource` model + section→apparatus_type + curated tier

**Files:**
- Create: `packages/learning-resolver/src/learning_resolver/models.py`
- Create: `packages/learning-resolver/src/learning_resolver/resolver.py`
- Test: `packages/learning-resolver/tests/test_resolver.py`

**Interfaces:**
- Produces: `ResolvedResource` dataclass `{resource_type:str, title:str, source:str, reference:dict, is_primary:bool, is_mandatory:bool, cert_level:str|None, score:float, why:str}`; `resolver._apparatus_type_ids(conn, section) -> list[str]`; `resolver._curated(conn, apt_ids) -> list[ResolvedResource]`.

- [ ] **Step 1: Write `models.py`**

```python
from dataclasses import dataclass, field


@dataclass
class ResolvedResource:
    resource_type: str
    title: str
    source: str               # "curated" | "section_match"
    reference: dict = field(default_factory=dict)   # {kind, id?/url?/section?, slug?, summary?}
    is_primary: bool = False
    is_mandatory: bool = False
    cert_level: str | None = None
    score: float = 0.0
    why: str = ""
```

- [ ] **Step 2: Write the failing test (curated tier)** in `tests/test_resolver.py`

```python
from learning_resolver.db import connect
from learning_resolver import resolver


def test_apparatus_type_ids_for_known_section(section_with_curated):
    with connect() as c:
        ids = resolver._apparatus_type_ids(c, section_with_curated)
    assert ids and all(isinstance(i, str) for i in ids)


def test_curated_tier_orders_primary_first(section_with_curated):
    with connect() as c:
        ids = resolver._apparatus_type_ids(c, section_with_curated)
        items = resolver._curated(c, ids)
    assert items, "the curated section should yield curated resources"
    assert all(r.source == "curated" for r in items)
    # is_primary resources rank ahead of non-primary; mandatory ahead of non-mandatory.
    keys = [(not r.is_primary, not r.is_mandatory) for r in items]
    assert keys == sorted(keys), "curated order must be is_primary then is_mandatory"
```

- [ ] **Step 3: Run it — expect FAIL** (`AttributeError: module ... has no attribute '_apparatus_type_ids'`).

- [ ] **Step 4: Implement `resolver.py` (section→apt + curated)**

```python
"""Hybrid contextual resource resolver over learning_dev. Read-only."""
from .db import connect
from .models import ResolvedResource

_CURATED_BASE = 1000.0
_SECTION_BASE = 500.0


def _apparatus_type_ids(conn, section: str) -> list[str]:
    rows = conn.execute(
        "select distinct apparatus_type_id from neta_procedures "
        "where section_number = %(s)s and apparatus_type_id is not null",
        {"s": section},
    ).fetchall()
    return [str(r[0]) for r in rows]


def _curated(conn, apt_ids: list[str]) -> list[ResolvedResource]:
    if not apt_ids:
        return []
    rows = conn.execute(
        """
        select atr.resource_type, atr.is_primary, atr.is_mandatory, atr.display_order,
               atr.study_content_id, atr.neta_procedure_id, atr.resource_url, atr.resource_name,
               sc.title as sc_title, sc.slug as sc_slug, sc.summary as sc_summary,
               sc.certification_level as sc_level,
               np.title as np_title, np.section_number as np_section
        from apparatus_type_resources atr
        left join study_content sc on sc.id = atr.study_content_id
        left join neta_procedures np on np.id = atr.neta_procedure_id
        where atr.apparatus_type_id = any(%(ids)s) and atr.is_active
        order by atr.is_primary desc, atr.is_mandatory desc, atr.display_order asc nulls last
        """,
        {"ids": apt_ids},
    ).fetchall()
    out: list[ResolvedResource] = []
    for i, r in enumerate(rows):
        (rtype, is_primary, is_mandatory, display_order, sc_id, np_id, url, rname,
         sc_title, sc_slug, sc_summary, sc_level, np_title, np_section) = r
        if sc_id is not None:
            title, ref, level = sc_title, {"kind": "study_content", "id": str(sc_id),
                                           "slug": sc_slug, "summary": sc_summary}, sc_level
        elif np_id is not None:
            title, ref, level = np_title, {"kind": "neta_procedure", "section": np_section}, None
        else:
            title, ref, level = (rname or "Linked resource"), {"kind": "url", "url": url}, None
        score = (_CURATED_BASE + (100 if is_primary else 0) + (50 if is_mandatory else 0)
                 - (display_order or 0))
        out.append(ResolvedResource(
            resource_type=rtype, title=title or "Untitled", source="curated", reference=ref,
            is_primary=bool(is_primary), is_mandatory=bool(is_mandatory), cert_level=level,
            score=float(score), why="curated resource for this apparatus type",
        ))
    return out
```

- [ ] **Step 5: Run — expect PASS** (3 passed). Commit.

```bash
ssh olares-mesh "cd /home/olares/code/apex/apex-learning-lane && git add packages/learning-resolver && git commit -q -F -" <<'MSG'
feat(learning-resolver): ResolvedResource model + section-to-apparatus + curated tier

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
```

---

## Task 3: Section-join tier + dedupe against curated

**Files:**
- Modify: `packages/learning-resolver/src/learning_resolver/resolver.py`
- Test: `packages/learning-resolver/tests/test_resolver.py`

**Interfaces:**
- Consumes: `_curated` (Task 2).
- Produces: `resolver._section_match(conn, section, exclude_sc_ids: set[str]) -> list[ResolvedResource]`.

- [ ] **Step 1: Write the failing test**

```python
def test_section_match_tier(section_study_only):
    from learning_resolver import resolver
    from learning_resolver.db import connect
    with connect() as c:
        items = resolver._section_match(c, section_study_only, exclude_sc_ids=set())
    assert items, "a study-only section should yield section matches"
    assert all(r.source == "section_match" for r in items)
    # primary-section matches outrank secondary-section matches
    scores = [r.score for r in items]
    assert scores == sorted(scores, reverse=True)


def test_section_match_excludes_already_curated(section_study_only):
    from learning_resolver import resolver
    from learning_resolver.db import connect
    with connect() as c:
        full = resolver._section_match(c, section_study_only, exclude_sc_ids=set())
        first_id = full[0].reference["id"]
        pruned = resolver._section_match(c, section_study_only, exclude_sc_ids={first_id})
    assert all(r.reference["id"] != first_id for r in pruned)
    assert len(pruned) == len(full) - 1
```

- [ ] **Step 2: Run — expect FAIL** (`_section_match` undefined).

- [ ] **Step 3: Implement `_section_match` in `resolver.py`**

```python
def _section_match(conn, section: str, exclude_sc_ids: set[str]) -> list[ResolvedResource]:
    rows = conn.execute(
        """
        select sc.id, sc.title, sc.slug, sc.summary, sc.certification_level,
               (sc.neta_section_primary = %(s)s) as primary_hit
        from study_content sc
        where (sc.neta_section_primary = %(s)s or %(s)s = any(sc.neta_sections_secondary))
          and sc.is_active and sc.status = 'published'
        order by (sc.neta_section_primary = %(s)s) desc, sc.title asc
        """,
        {"s": section},
    ).fetchall()
    out: list[ResolvedResource] = []
    for sc_id, title, slug, summary, level, primary_hit in rows:
        if str(sc_id) in exclude_sc_ids:
            continue
        score = _SECTION_BASE + (50 if primary_hit else 0)
        out.append(ResolvedResource(
            resource_type="study_content", title=title or "Untitled", source="section_match",
            reference={"kind": "study_content", "id": str(sc_id), "slug": slug, "summary": summary},
            cert_level=level, score=float(score),
            why=("NETA " + section + " primary-section study content") if primary_hit
                 else ("NETA " + section + " related (secondary) study content"),
        ))
    return out
```

- [ ] **Step 4: Run — expect PASS. Commit.**

```bash
ssh olares-mesh "cd /home/olares/code/apex/apex-learning-lane && git add packages/learning-resolver && git commit -q -F -" <<'MSG'
feat(learning-resolver): study_content section-join tier with curated dedupe

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
```

---

## Task 4: Public `resolve()` — level re-rank + merge + sort + cap

**Files:**
- Modify: `packages/learning-resolver/src/learning_resolver/resolver.py`
- Modify: `packages/learning-resolver/src/learning_resolver/__init__.py`
- Test: `packages/learning-resolver/tests/test_resolver.py`

**Interfaces:**
- Produces: `learning_resolver.resolve(neta_section: str, level: str | None = None, limit: int = 20) -> list[ResolvedResource]`.

- [ ] **Step 1: Write the failing tests**

```python
def test_resolve_curated_before_section(section_with_curated):
    from learning_resolver import resolve
    items = resolve(section_with_curated, limit=50)
    assert items
    first_section_idx = next((i for i, r in enumerate(items) if r.source == "section_match"), len(items))
    assert all(r.source == "curated" for r in items[:first_section_idx])


def test_resolve_dedupes_study_content(section_with_curated):
    from learning_resolver import resolve
    ids = [r.reference.get("id") for r in resolve(section_with_curated, limit=200)
           if r.reference.get("kind") == "study_content"]
    ids = [i for i in ids if i]
    assert len(ids) == len(set(ids)), "a study_content must appear at most once"


def test_resolve_level_changes_order_not_membership(section_study_only):
    from learning_resolver import resolve
    base = resolve(section_study_only, limit=200)
    leveled = resolve(section_study_only, level="IV", limit=200)
    key = lambda rs: {r.reference.get("id") or r.reference.get("url") for r in rs}
    assert key(base) == key(leveled), "level must not change MEMBERSHIP (soft re-rank only)"


def test_resolve_caps_at_limit(section_with_curated):
    from learning_resolver import resolve
    assert len(resolve(section_with_curated, limit=3)) <= 3


def test_resolve_unknown_section_is_empty():
    from learning_resolver import resolve
    assert resolve("9.9.9.9-nope") == []
```

- [ ] **Step 2: Run — expect FAIL** (`resolve` undefined).

- [ ] **Step 3: Implement `resolve()` + level boost in `resolver.py`**

```python
_LEVEL_RANK = {"II": 2, "III": 3, "IV": 4}


def _level_boost(resource_level: str | None, want: str | None) -> float:
    if not want or not resource_level:
        return 0.0
    rl, wl = _LEVEL_RANK.get(resource_level), _LEVEL_RANK.get(want)
    if rl is None or wl is None:
        return 0.0
    diff = abs(rl - wl)
    return 30.0 if diff == 0 else (10.0 if diff == 1 else 0.0)


def resolve(neta_section: str, level: str | None = None, limit: int = 20) -> list[ResolvedResource]:
    if not neta_section or not neta_section.strip():
        return []
    with connect() as conn:
        apt_ids = _apparatus_type_ids(conn, neta_section)
        curated = _curated(conn, apt_ids)
        seen = {r.reference["id"] for r in curated if r.reference.get("kind") == "study_content"}
        section = _section_match(conn, neta_section, exclude_sc_ids=seen)
    items = curated + section
    if level:
        for r in items:
            r.score += _level_boost(r.cert_level, level)
    items.sort(key=lambda r: (-r.score, r.title))
    return items[:limit]
```

- [ ] **Step 4: Update `__init__.py`**

```python
from .models import ResolvedResource
from .resolver import resolve

__all__ = ["resolve", "ResolvedResource"]
```

- [ ] **Step 5: Run full suite — expect PASS. Commit.**

```bash
ssh olares-mesh "cd /home/olares/code/apex/apex-learning-lane && git add packages/learning-resolver && git commit -q -F -" <<'MSG'
feat(learning-resolver): public resolve() with soft level re-rank, merge, cap

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
```

---

## Task 5: CLI

**Files:**
- Create: `packages/learning-resolver/src/learning_resolver/cli.py`
- Test: `packages/learning-resolver/tests/test_cli.py`

**Interfaces:**
- Consumes: `resolve` (Task 4).
- Produces: `learning_resolver.cli.main(argv: list[str] | None = None) -> int`.

- [ ] **Step 1: Write the failing test**

```python
import json

from learning_resolver.cli import main


def test_cli_json_output(capsys, section_with_curated):
    rc = main(["resolve", "--section", section_with_curated, "--limit", "5", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list) and len(payload) <= 5
    assert {"resource_type", "title", "source", "score"} <= set(payload[0].keys())


def test_cli_unknown_section_empty(capsys):
    rc = main(["resolve", "--section", "9.9.9.9-nope", "--json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out) == []
```

- [ ] **Step 2: Run — expect FAIL** (ImportError).

- [ ] **Step 3: Implement `cli.py`**

```python
import argparse
import dataclasses
import json
import sys

from .resolver import resolve


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="learning-resolver",
                                 description="Contextual learning-resource resolver (learning_dev)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    rv = sub.add_parser("resolve", help="rank resources for a NETA section")
    rv.add_argument("--section", required=True)
    rv.add_argument("--level", choices=["II", "III", "IV"], default=None)
    rv.add_argument("--limit", type=int, default=20)
    rv.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "resolve":
        items = resolve(args.section, level=args.level, limit=args.limit)
        if args.json:
            json.dump([dataclasses.asdict(r) for r in items], sys.stdout, ensure_ascii=False)
        else:
            for r in items:
                print(f"[{r.source:>13}] {r.score:7.1f}  {r.title}  -- {r.why}")
        return 0
    return 1
```

- [ ] **Step 4: Run — expect PASS. Commit.**

```bash
ssh olares-mesh "cd /home/olares/code/apex/apex-learning-lane && git add packages/learning-resolver && git commit -q -F -" <<'MSG'
feat(learning-resolver): argparse CLI (resolve --section/--level/--limit/--json)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
```

---

## Task 6: control-plane-api route `GET /api/v1/learning/resources`

**Files:**
- Create: `apps/control-plane-api/services/learning/__init__.py` (empty)
- Create: `apps/control-plane-api/services/learning/schemas.py`
- Create: `apps/control-plane-api/services/learning/router.py`
- Modify: `apps/control-plane-api/main.py` (register router)
- Modify: `apps/control-plane-api/pyproject.toml` (add the resolver as a path dependency)
- Test: `apps/control-plane-api/tests/test_learning_resources.py`

**Interfaces:**
- Consumes: `learning_resolver.resolve` (Task 4).
- Produces: HTTP `GET /api/v1/learning/resources?neta_section=&level=&limit=` → `{context, resources[]}`.

**Note:** this route does NOT take `db: Session = Depends(get_db)` — the shared session targets the platform DB, not `learning_dev`. It calls the package, which owns the `learning_dev` connection. It also omits `Depends(get_current_user)` → public dev endpoint (read-only, non-PII learning content).

- [ ] **Step 1: Add the path dependency in `apps/control-plane-api/pyproject.toml`**

Under `[project] dependencies`, add: `"learning-resolver"`, and add a uv source so it resolves from the sibling package:
```toml
[tool.uv.sources]
learning-resolver = { path = "../../packages/learning-resolver", editable = true }
```
(If the file has no `[tool.uv.sources]`, append the block. Verify the API resolves it: `ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane/apps/control-plane-api && uv run python -c "import learning_resolver; print(learning_resolver.resolve)"'`.)

- [ ] **Step 2: Write `schemas.py`**

```python
from pydantic import BaseModel


class ResolvedResourceOut(BaseModel):
    resource_type: str
    title: str
    source: str
    reference: dict
    is_primary: bool
    is_mandatory: bool
    cert_level: str | None = None
    score: float
    why: str


class ResourcesContext(BaseModel):
    neta_section: str
    level: str | None = None
    limit: int


class ResourcesResponse(BaseModel):
    context: ResourcesContext
    resources: list[ResolvedResourceOut]
```

- [ ] **Step 3: Write the failing test `tests/test_learning_resources.py`**

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_missing_section_is_400():
    assert client.get("/api/v1/learning/resources").status_code == 422  # FastAPI required-param

def test_unknown_section_returns_empty_200():
    r = client.get("/api/v1/learning/resources", params={"neta_section": "9.9.9.9-nope"})
    assert r.status_code == 200
    body = r.json()
    assert body["context"]["neta_section"] == "9.9.9.9-nope"
    assert body["resources"] == []

def test_known_section_returns_ranked_resources():
    # 7.2.1.1 has curated links in the frozen baseline.
    r = client.get("/api/v1/learning/resources", params={"neta_section": "7.2.1.1", "limit": 5})
    assert r.status_code == 200
    res = r.json()["resources"]
    assert 0 < len(res) <= 5
    assert {"resource_type", "title", "source", "score"} <= set(res[0].keys())
    assert res == sorted(res, key=lambda x: -x["score"])
```
(Note: a missing required `Query(...)` yields FastAPI's `422`, which is the documented "missing param" behavior here — the spec's "400" intent is satisfied by FastAPI validation. If a literal 400 is required, make `neta_section` `Query(default=None)` and raise `HTTPException(400)` when blank; keep the test in sync.)

- [ ] **Step 4: Run — expect FAIL** (route not registered → 404). 

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane/apps/control-plane-api && set -a && . ../../infra/.env && set +a && export LEARNING_DEV_PGPASSWORD="$DEV_PG_PASSWORD" && uv run pytest tests/test_learning_resources.py -v'`

- [ ] **Step 5: Write `router.py`**

```python
from fastapi import APIRouter, Query

from learning_resolver import resolve

from .schemas import ResolvedResourceOut, ResourcesContext, ResourcesResponse

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


@router.get("/resources", response_model=ResourcesResponse)
def get_resources(
    neta_section: str = Query(..., min_length=1),
    level: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> ResourcesResponse:
    items = resolve(neta_section, level=level, limit=limit)
    return ResourcesResponse(
        context=ResourcesContext(neta_section=neta_section, level=level, limit=limit),
        resources=[ResolvedResourceOut(**vars(r)) for r in items],
    )
```

- [ ] **Step 6: Register in `main.py`** — add alongside the other router imports/includes:

```python
from services.learning.router import router as learning_router
# ... after app = FastAPI(...)
app.include_router(learning_router)
```

- [ ] **Step 7: Run — expect PASS. Commit** (`git add apps/control-plane-api`).

```bash
ssh olares-mesh "cd /home/olares/code/apex/apex-learning-lane && git add apps/control-plane-api && git commit -q -F -" <<'MSG'
feat(control-plane-api): GET /api/v1/learning/resources (public, reads learning_dev via resolver)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
```

---

## Task 7: operations-web `/learning-demo` thin page

**Files:**
- Create: `apps/operations-web/lib/learning-resources.ts`
- Create: `apps/operations-web/app/learning-demo/page.tsx`

**Interfaces:**
- Consumes: `GET /api/v1/learning/resources` (Task 6); `browserEnv.controlPlaneBaseUrl` (existing).

- [ ] **Step 1: Write `lib/learning-resources.ts`** (mirrors `lib/revenue-recognition.ts`)

```ts
import { browserEnv } from './browser-env'

export type LearningResource = {
  resource_type: string
  title: string
  source: 'curated' | 'section_match'
  reference: Record<string, unknown>
  is_primary: boolean
  is_mandatory: boolean
  cert_level: string | null
  score: number
  why: string
}

export type LearningResourcesResponse = {
  context: { neta_section: string; level: string | null; limit: number }
  resources: LearningResource[]
}

export class LearningResourcesError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'LearningResourcesError'
    this.status = status
  }
}

export async function fetchLearningResources(
  netaSection: string,
  level?: string,
  limit = 20,
): Promise<LearningResourcesResponse> {
  const baseUrl = browserEnv.controlPlaneBaseUrl.replace(/\/$/, '')
  const params = new URLSearchParams({ neta_section: netaSection, limit: String(limit) })
  if (level) params.set('level', level)
  const response = await fetch(`${baseUrl}/api/v1/learning/resources?${params.toString()}`, {
    headers: { Accept: 'application/json' },
  })
  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }
  if (!response.ok) {
    throw new LearningResourcesError(`Request failed with status ${response.status}`, response.status)
  }
  return payload as LearningResourcesResponse
}
```

- [ ] **Step 2: Write `app/learning-demo/page.tsx`** (mirrors `pm-review/finance/page.tsx`; reuses `.shell-page`, `.hero-card`, `.notes-card`, `.resource-banner`, `.resource-grid`, `.resource-item`, `.resource-chip`)

```tsx
'use client'

import { useState } from 'react'
import { fetchLearningResources, LearningResource, LearningResourcesError } from '../../lib/learning-resources'

export default function LearningDemoPage() {
  const [section, setSection] = useState('7.2.1.1')
  const [level, setLevel] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [resources, setResources] = useState<LearningResource[] | null>(null)

  async function run() {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const data = await fetchLearningResources(section.trim(), level || undefined, 20)
      setResources(data.resources)
    } catch (error) {
      setErrorMessage(
        error instanceof LearningResourcesError
          ? error.message
          : 'The learning resolver could not be reached.',
      )
      setResources([])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="shell-page">
      <section className="hero-card">
        <p className="eyebrow">Learning &rarr; Slice 1 demo</p>
        <h1>Contextual resources for a NETA section.</h1>
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
          <button className="btn" onClick={run} disabled={isLoading}>Resolve</button>
        </div>

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
                      {r.is_mandatory ? <span className="resource-chip">Mandatory</span> : null}
                      {r.cert_level ? <span className="resource-chip">Level {r.cert_level}</span> : null}
                    </div>
                    <h3>{r.title}</h3>
                    <p>{r.why}</p>
                  </article>
                ))}
              </div>
            )}
          </div>
        ) : null}
      </section>
    </main>
  )
}
```

- [ ] **Step 3: Type-check**

Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && pnpm --filter @apex/operations-web typecheck'`
Expected: passes (0 errors). If `.btn`/input styles are missing, the page still renders (styling is cosmetic for the demo).

- [ ] **Step 4: Manual smoke (optional, both servers up)** — start control-plane-api (`uvicorn main:app --app-dir apps/control-plane-api --port 8010` with `LEARNING_DEV_*` set) + `pnpm --filter @apex/operations-web dev` with `NEXT_PUBLIC_CONTROL_PLANE_BASE_URL=http://localhost:8010`; open `/learning-demo`, enter `7.2.1.1`, confirm ranked resources render.

- [ ] **Step 5: Commit**

```bash
ssh olares-mesh "cd /home/olares/code/apex/apex-learning-lane && git add apps/operations-web && git commit -q -F -" <<'MSG'
feat(operations-web): /learning-demo thin page for the Slice 1 resolver

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
MSG
```

---

## Self-Review

**1. Spec coverage:** resolver core (Tasks 2-4) ✓; CLI (Task 5) ✓; endpoint (Task 6) ✓; thin UI (Task 7) ✓; hybrid ranking curated→section ✓; soft level re-rank ✓; NETA section as contract ✓; dedupe ✓; empty/unknown → empty ✓; read-only/dev-stage/no-prod ✓; TDD against `learning_dev` ✓. The spec's `study_content.status='published'` filter and `II/III/IV` levels are pinned from live data.

**2. Placeholder scan:** no TBD/TODO; every code step is concrete. The one judgment call (missing-param `422` vs literal `400`) is documented inline with the exact alternative.

**3. Type consistency:** `resolve(neta_section, level, limit)` is identical across package, CLI, and route; `ResolvedResource` fields map 1:1 to `ResolvedResourceOut` (router builds it via `ResolvedResourceOut(**vars(r))`); the TS `LearningResource` type mirrors those fields. `reference` is a `dict`/`Record<string,unknown>` everywhere.

**Open impl-time check (named, not a gap):** confirm `apps/control-plane-api/pyproject.toml` uses uv (it does, per the pattern scan) so the `[tool.uv.sources]` path-dep resolves; if the API instead uses a plain requirements install, fall back to adding `packages/learning-resolver/src` to `PYTHONPATH` for the route import. Verified by the Step-1 import check.
