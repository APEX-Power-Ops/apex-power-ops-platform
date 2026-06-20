# Learning Slice 2b — Projection Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only, compute-on-read projection layer (`packages/learning-projections` + four guarded control-plane-api GET routes) that derives content-progress, assessment-summary, competency-rollup, and cohort-aggregate read-models from the live `learning_events` ledger.

**Architecture:** A new Python package mirrors `learning-resolver` (read-only pinned session). Four functions issue aggregation SQL over `learning_events` joined to the frozen baseline graph and return dataclasses; four control-plane-api routes call them behind the existing learning-router guard. No DB migration. TDD on throwaway `learning_test` with a full mini-graph DDL fixture.

**Tech Stack:** Python 3.11+, `psycopg[binary]>=3.1`, FastAPI, pytest, host PG17 `learning_dev`/`learning_test`. All work on the Olares host over `ssh olares-mesh`; edit via write-local-then-`ssh 'cat > dest'`; commit with `git commit -F` (no apostrophes in messages).

## Global Constraints (every task inherits these — values verbatim from the spec)

- **Read-only.** `db.py` is the resolver's read-only session verbatim: pinned DSN + `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`. Nothing writes; the baseline `user_study_progress`/`user_test_attempts` tables are never touched. The no-write guarantee is itself tested.
- **No new DB objects, no migration.** Compute-on-read only. Mini-graph DDL exists ONLY in the test fixture for `learning_test`.
- **Naming discipline (load-bearing):** competency fields are `covered_ksas` / `coverage_percent` / `evidence_event_count`; the concept list is `engaged_concepts` (broader than coverage). The token `mastered`/`mastery` MUST NOT appear in any **generated package/API field name, response key, or docstring** (it may appear in plan/spec prose explaining the rule).
- **Non-silent level resolution (load-bearing):** every competency response carries `resolved_level`, `level_source`, `levels_in_scope`.
- **Payload contract:** `assessment_completed.payload.score_percent` (numeric 0–100); `self_assessment.payload.confidence` (int 1–5). Missing key → excluded from that aggregate.
- **Competency math:** denominator = `count(distinct ksa_code) from ksas where certification_level=L`; covered = distinct reachable `ksa_code` via `content_concept_links → edition_ksa_map (is_active, level=cert) → ksas`; edition ignored (distinct code); Level I has 0 KSAs → `coverage_percent = null`.
- **Dependency wiring vs test harness:** runtime/deploy = pip + `requirements.txt` (`-e ../../packages/learning-projections`), no `uv.lock` committed. `uv` is ONLY the local test runner.
- **Route guard:** new routes ride the existing `_learning_routes_enabled()` guard, which lives in `main.py` and wraps `include_router` (keyed on `LEARNING_DEV_DSN`/`LEARNING_DEV_PGPASSWORD`); no separate guard. Note `router.py` is imported unconditionally at `main.py` top level, so `learning_projections` becomes a hard import dependency of the API at process start — which is exactly why Task 8 Step 1 (the `-e ../../packages/learning-projections` line in `requirements.txt`) is mandatory, not optional.
- **Test-DB safety:** the package's `db.py` DEFAULTS to `dbname=learning_dev`. Test runs MUST export `LEARNING_DEV_DSN` pointing at `learning_test`; the fixture conftest MUST refuse to run if its target DSN does not contain `learning_test`.

---

## File Structure

**New package `packages/learning-projections/`:**
- `pyproject.toml` — package metadata + `learning-projections` console script.
- `src/learning_projections/db.py` — read-only `learning_dev` session (verbatim from resolver).
- `src/learning_projections/models.py` — 6 dataclasses + `ProjectionError`/`UserNotFoundError`.
- `src/learning_projections/projections.py` — the 4 functions + shared helpers.
- `src/learning_projections/cli.py` — thin argparse wrapper.
- `src/learning_projections/__init__.py` — exports.
- `tests/conftest.py` — session-autouse fixture builder (test-DB-guarded).
- `tests/projections_prereq.sql` — full mini-graph DDL + deterministic graph seed.
- `tests/projections_events_seed.sql` — deterministic `learning_events` seed.
- `tests/test_db_readonly.py`, `test_fixture_smoke.py`, `test_content_progress.py`, `test_assessment_summary.py`, `test_competency_rollup.py`, `test_cohort_aggregate.py`, `test_cli.py`.

**Modified control-plane-api (`apps/control-plane-api/`):**
- `services/learning/router.py` — +4 routes.
- `services/learning/schemas.py` — +6 Pydantic models + wrappers.
- `requirements.txt` — +`-e ../../packages/learning-projections`.
- `tests/test_learning_projections.py` — route tests.

---

## Deterministic mini-graph fixture (the seed every test asserts against)

This data is fixed; later tasks reference these exact values. **Built fresh each session** (drop+create) so assertions are exact regardless of prior state.

**Users** (`user_profiles`): all `is_active=true` except `U_inactive`.
| key | id | target | current |
|---|---|---|---|
| U_target | `11111111-0000-0000-0000-000000000001` | II | (null) |
| U_current | `11111111-0000-0000-0000-000000000002` | (null) | III |
| U_all | `11111111-0000-0000-0000-000000000003` | (null) | (null) |
| U_none | `11111111-0000-0000-0000-000000000004` | II | (null) |
| U_inactive (`is_active=false`) | `11111111-0000-0000-0000-000000000009` | II | (null) |

**study_content:** `C1=22222222-…01` ('Content 1', §7.1), `C2=…02` ('Content 2', §7.2), `C3=…03` ('Content 3', §7.3).

**concepts:** `concept-1` ('Concept One'), `concept-2` ('Concept Two'), `concept-3` ('Concept Three' — orphan-only).

**ksas** (`ksa_code`, level): II → `SA1,SA2,SA3,SA4` (4); III → `SB1,SB2,SB3` (3); IV → `SC1,SC2` (2); **I → none**.

**edition_ksa_map** (concept_id, ksa_code, level, edition, is_active):
- `concept-1 → SA1` (II, 2022, t), `concept-1 → SA1` (II, 2026, t) [dup edition], `concept-1 → SA2` (II, 2026, t)
- `concept-2 → SB1` (III, 2026, t), `concept-2 → SB2` (III, 2026, t), `concept-2 → SA3` (II, 2026, **f** — inactive)
- `concept-3 → ORPHAN1` (II, 2026, t) [orphan: not in `ksas`]

**content_concept_links** (content_id, concept_id): `C1→concept-1`, `C1→concept-2`, `C2→concept-3`, `C3→concept-1`.

**learning_events** (per user):
- **U_target:** `resource_viewed C1`, `resource_completed C1`, `assessment_completed C1` `{score_percent:80}`, `resource_viewed C2`, `self_assessment C1` `{confidence:4}`, **and a section-only `self_assessment` with NULL `study_content_id`** `{confidence:3}` (must be excluded from per-content assessment_summary).
- **U_current:** `resource_completed C1`, `resource_completed C2`, `assessment_completed C1` `{score_percent:90}`.
- **U_all:** `resource_completed C1`.
- **U_none:** `resource_viewed C1`.
- **U_inactive:** `resource_completed C1`.

**Hand-computed expected values (the assertions):**
- `content_progress(U_target)` → 2 rows: C1 (view_count 1, completed, status completed), C2 (view_count 1, not completed, in_progress).
- `assessment_summary(U_target)` → 1 row (C1): attempts 1, latest_score 80, mean_score 80, self_count 1, latest_confidence 4, mean_confidence 4.
- `competency_rollup(U_target)` → resolved II / source target / scope [II]; coverage [II: total 4, covered 2 (SA1,SA2), 50.0]; evidence_event_count 2; engaged_concepts {concept-1, concept-2}.
- `competency_rollup(U_current)` → resolved III / source current / scope [III]; coverage [III: total 3, covered 2 (SB1,SB2), 66.7]; evidence_event_count 3; engaged_concepts {concept-1, concept-2, **concept-3**} (orphan-only concept present); SA3 excluded (inactive), ORPHAN1 excluded (orphan).
- `competency_rollup(U_all)` → resolved all / source all / scope [II,III,IV]; coverage [II:4/2/50.0, III:3/2/66.7, IV:2/0/0.0]; evidence_event_count 1.
- `competency_rollup(U_target, level='I')` → resolved I / source explicit / scope [I]; coverage [I: total 0, covered 0, **None**].
- `competency_rollup(U_none)` → coverage [II:4/0/0.0]; evidence_event_count 0; engaged_concepts [].
- `cohort_aggregate()` → user_count 4; mean_completed_content 1.0; mean_latest_score 85.0 / scored_user_count 2; mean_coverage_percent 38.9 (per-user: U_target 50.0, U_current 66.7, U_all null→excluded, U_none 0.0) / coverage_user_count 3.
- `cohort_aggregate(level='II')` → mean_coverage_percent 37.5 (50,50,50,0) / coverage_user_count 4.
- `cohort_aggregate(level='I')` → mean_coverage_percent None / coverage_user_count 0 (mean_completed 1.0, mean_latest_score 85.0 unchanged).

---

## Task 0: Lane setup + baseline

**Files:** none (environment only).

- [ ] **Step 1: Confirm the worktree + branch.**
Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && git branch --show-current && git log --oneline -1'`
Expected: branch `learning/slice2b-projections` (rebased on current `main`, which already owns `packages/learning-projections/**` in the lane charter).

- [ ] **Step 2: Fix the lane charter `Branch:` line + commit.** The merged-and-pruned `learning/slice2-capture` is stale; point the learning lane at this branch. (OWNS already lists `packages/learning-projections/**`.)
Edit `docs/lanes/README.md`: change the learning lane's `- **Branch:** ` + `` `learning/slice2-capture` `` to `` `learning/slice2b-projections` ``.
```bash
git add docs/lanes/README.md
git commit -F - <<'EOF'
docs(lanes): point the learning lane at slice2b-projections

slice2-capture merged + was pruned; the active learning branch is the
projection-engine slice.
EOF
```
Expected: one commit on the lane branch.

- [ ] **Step 3: Ensure `infra/.env` exists in the worktree** (new worktrees lack gitignored files).
Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && test -f infra/.env && echo OK || (cp /home/olares/code/apex/apex-power-ops-platform/infra/.env infra/.env && echo COPIED)'`
Expected: `OK` or `COPIED`.

- [ ] **Step 4: Create the throwaway `learning_test` DB if absent (idempotent).**
Run:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && set -a && . ./infra/.env && set +a && export PGPASSWORD=$DEV_PG_PASSWORD && psql -h 127.0.0.1 -U postgres -tAc "select 1 from pg_database where datname='"'"'learning_test'"'"'" | grep -q 1 || psql -h 127.0.0.1 -U postgres -c "create database learning_test"'
```
Expected: silent success. The `datname='learning_test'` **string literal** (single-quoted, escaped through ssh as `'"'"'learning_test'"'"'`) makes the existence check correct — a double-quoted `"learning_test"` would be parsed as an identifier and error, defeating idempotency. `create database` runs only when absent.

- [ ] **Step 5: Verify `uv` + `psql` on PATH.**
Run: `ssh olares-mesh 'export PATH="$HOME/.local/bin:$PATH" && uv --version && psql --version'`
Expected: versions print.

- [ ] **Step 6: Baseline — existing learning suites green** (sanity that the worktree is clean).
Run: `ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane/packages/learning-resolver && export PATH="$HOME/.local/bin:$PATH" && PYTHONPATH=src uv run --no-project --with "psycopg[binary]" --with pytest pytest -q'` (resolver tests run against live `learning_dev`).
Expected: PASS (or the known-green count). If the resolver tests need `LEARNING_DEV_PGPASSWORD`, export it from `infra/.env` first.

No commit (environment only).

---

## Task 1: Package skeleton + read-only `db.py` + models

**Files:**
- Create: `packages/learning-projections/pyproject.toml`, `src/learning_projections/db.py`, `src/learning_projections/models.py`, `src/learning_projections/__init__.py`
- Test: `packages/learning-projections/tests/__init__.py`, `tests/test_db_readonly.py`

**Interfaces:**
- Produces: `db.dsn() -> str`, `db.connect() -> psycopg.Connection` (read-only); dataclasses `ContentProgress`, `AssessmentSummary`, `ConceptRef`, `LevelCoverage`, `CompetencyRollup`, `CohortAggregate`; exceptions `ProjectionError(Exception)`, `UserNotFoundError(ProjectionError)`.

- [ ] **Step 1: Write `pyproject.toml`.**
```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "learning-projections"
version = "0.1.0"
description = "Read-only projection engine over the learning_events ledger (learning Slice 2b)"
requires-python = ">=3.11"
dependencies = ["psycopg[binary]>=3.1"]

[project.optional-dependencies]
test = ["pytest>=8.0.0"]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[project.scripts]
learning-projections = "learning_projections.cli:main"
```

- [ ] **Step 2: Write `src/learning_projections/db.py`** (verbatim read-only session from the resolver).
```python
"""learning_dev connection (read-only). DSN pinned so ambient PG env (which points at
prod) cannot redirect us -- mirrors learning-resolver. Slice 2b is read-only: every read-model
is computed live; nothing is written."""
import os

import psycopg


def dsn() -> str:
    return os.environ.get("LEARNING_DEV_DSN") or (
        "host=127.0.0.1 port=5432 dbname=learning_dev user=postgres "
        f"password={os.environ.get('LEARNING_DEV_PGPASSWORD') or os.environ.get('PGPASSWORD', '')} "
        "sslmode=disable"
    )


def connect() -> "psycopg.Connection":
    conn = psycopg.connect(dsn(), autocommit=True)
    conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
    return conn
```

- [ ] **Step 3: Write `src/learning_projections/models.py`.**
```python
from dataclasses import dataclass


class ProjectionError(Exception):
    """Base error for the projection engine."""


class UserNotFoundError(ProjectionError):
    """Raised when a user_id is absent from user_profiles (route maps to 404)."""


@dataclass
class ContentProgress:
    study_content_id: str
    title: str
    neta_section: str | None
    view_count: int
    is_completed: bool
    status: str
    first_seen_at: str | None
    last_activity_at: str | None


@dataclass
class AssessmentSummary:
    study_content_id: str
    title: str
    neta_section: str | None
    assessment_attempts: int
    latest_score_percent: float | None
    mean_score_percent: float | None
    self_assessment_count: int
    latest_confidence: int | None
    mean_confidence: float | None
    last_activity_at: str | None


@dataclass
class ConceptRef:
    concept_id: str
    concept_description: str | None


@dataclass
class LevelCoverage:
    level: str
    total_ksas_at_level: int
    covered_ksas: int
    coverage_percent: float | None


@dataclass
class CompetencyRollup:
    user_id: str
    resolved_level: str
    level_source: str
    levels_in_scope: list[str]
    evidence_event_count: int
    coverage: list[LevelCoverage]
    engaged_concepts: list[ConceptRef]


@dataclass
class CohortAggregate:
    level: str | None
    user_count: int
    mean_completed_content: float
    mean_latest_score: float | None
    scored_user_count: int
    mean_coverage_percent: float | None
    coverage_user_count: int
```

- [ ] **Step 4: Write `src/learning_projections/__init__.py`** (functions added in later tasks; import lazily to keep this task self-contained).
```python
from .models import (
    AssessmentSummary,
    CohortAggregate,
    CompetencyRollup,
    ConceptRef,
    ContentProgress,
    LevelCoverage,
    ProjectionError,
    UserNotFoundError,
)

__all__ = [
    "AssessmentSummary", "CohortAggregate", "CompetencyRollup", "ConceptRef",
    "ContentProgress", "LevelCoverage", "ProjectionError", "UserNotFoundError",
]
```

- [ ] **Step 5: Write the empty `tests/__init__.py`** (so `from tests... ` imports work, matching the capture package).
```python
```

- [ ] **Step 6: Write the failing read-only test `tests/test_db_readonly.py`.**
```python
"""The slice's central discipline: the projection session cannot write."""
import psycopg
import pytest

from learning_projections.db import connect


def test_session_is_read_only():
    with connect() as conn:
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute("create table _ro_probe (i int)")
```

- [ ] **Step 7: Run it to verify it passes** (the implementation — `db.py` — already exists; this test proves the read-only session). Point the DSN at `learning_test`.
Run:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && set -a && . ./infra/.env && set +a && export PATH="$HOME/.local/bin:$PATH" PGPASSWORD=$DEV_PG_PASSWORD LEARNING_DEV_DSN="host=127.0.0.1 port=5432 dbname=learning_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable" && cd packages/learning-projections && PYTHONPATH=src uv run --no-project --with "psycopg[binary]" --with pytest pytest tests/test_db_readonly.py -q'
```
Expected: `1 passed`.

- [ ] **Step 8: Commit.**
```bash
git add packages/learning-projections/pyproject.toml packages/learning-projections/src packages/learning-projections/tests/__init__.py packages/learning-projections/tests/test_db_readonly.py
git commit -F - <<'EOF'
feat(learning-projections): package skeleton + read-only session

db.py (read-only), the six read-model dataclasses, ProjectionError /
UserNotFoundError, and a test proving the session rejects writes.
EOF
```

---

## Task 2: Mini-graph test fixture

**Files:**
- Create: `packages/learning-projections/tests/projections_prereq.sql`, `tests/projections_events_seed.sql`, `tests/conftest.py`, `tests/test_fixture_smoke.py`

**Interfaces:**
- Consumes: the repo migration `infra/database/migrations/learning/002_learning_events.sql` (applied by the conftest to create the ledger).
- Produces: a deterministically-seeded `learning_test` DB (the data table above) for all later tests.

- [ ] **Step 1: Write `tests/projections_prereq.sql`** (drop+create the mini-graph DDL + seed; NO `learning_events` — that comes from mig 002).
```sql
-- learning_test mini-graph for the projection-engine tests. Built fresh each session.
drop table if exists public.learning_events, public.content_concept_links,
  public.edition_ksa_map, public.ksas, public.concepts,
  public.study_content, public.user_profiles cascade;

do $$ begin
  if not exists (select 1 from pg_type where typname = 'certification_level') then
    create type certification_level as enum ('I','II','III','IV');
  end if;
end $$;

create table public.user_profiles (
  id uuid primary key,
  email text not null default 'seed@example.com',
  full_name text,
  target_certification_level  certification_level,
  current_certification_level certification_level,
  is_active boolean not null default true
);
create table public.study_content (
  id uuid primary key,
  title text,
  neta_section_primary text
);
create table public.concepts (
  concept_id text primary key,
  concept_description text
);
create table public.ksas (
  id uuid primary key default gen_random_uuid(),
  ksa_code varchar unique,
  certification_level certification_level
);
create table public.edition_ksa_map (
  id uuid primary key default gen_random_uuid(),
  concept_id text,
  ksa_code text,
  level text,
  edition text,
  is_active boolean not null default true
);
create table public.content_concept_links (
  id uuid primary key default gen_random_uuid(),
  content_id uuid,
  concept_id text
);

insert into public.user_profiles (id, email, target_certification_level, current_certification_level, is_active) values
  ('11111111-0000-0000-0000-000000000001','t1@x','II',  null, true),
  ('11111111-0000-0000-0000-000000000002','t2@x', null,'III', true),
  ('11111111-0000-0000-0000-000000000003','t3@x', null, null, true),
  ('11111111-0000-0000-0000-000000000004','t4@x','II',  null, true),
  ('11111111-0000-0000-0000-000000000009','t9@x','II',  null, false);

insert into public.study_content (id, title, neta_section_primary) values
  ('22222222-0000-0000-0000-000000000001','Content 1','7.1'),
  ('22222222-0000-0000-0000-000000000002','Content 2','7.2'),
  ('22222222-0000-0000-0000-000000000003','Content 3','7.3');

insert into public.concepts (concept_id, concept_description) values
  ('concept-1','Concept One'),('concept-2','Concept Two'),('concept-3','Concept Three');

insert into public.ksas (ksa_code, certification_level) values
  ('SA1','II'),('SA2','II'),('SA3','II'),('SA4','II'),
  ('SB1','III'),('SB2','III'),('SB3','III'),
  ('SC1','IV'),('SC2','IV');

insert into public.edition_ksa_map (concept_id, ksa_code, level, edition, is_active) values
  ('concept-1','SA1','II','2022', true),
  ('concept-1','SA1','II','2026', true),
  ('concept-1','SA2','II','2026', true),
  ('concept-2','SB1','III','2026', true),
  ('concept-2','SB2','III','2026', true),
  ('concept-2','SA3','II','2026', false),
  ('concept-3','ORPHAN1','II','2026', true);

insert into public.content_concept_links (content_id, concept_id) values
  ('22222222-0000-0000-0000-000000000001','concept-1'),
  ('22222222-0000-0000-0000-000000000001','concept-2'),
  ('22222222-0000-0000-0000-000000000002','concept-3'),
  ('22222222-0000-0000-0000-000000000003','concept-1');
```

- [ ] **Step 2: Write `tests/projections_events_seed.sql`** (inserted AFTER mig 002 creates the ledger).
```sql
-- explicit monotonic occurred_at so 'latest' (array_agg order by occurred_at desc) and
-- 'order by max(occurred_at)' are deterministic (not now()-tie-dependent).
insert into public.learning_events (user_id, event_type, study_content_id, neta_section, occurred_at, payload) values
  ('11111111-0000-0000-0000-000000000001','resource_viewed',     '22222222-0000-0000-0000-000000000001','7.1','2026-06-01 09:00:00+00','{}'),
  ('11111111-0000-0000-0000-000000000001','resource_completed',  '22222222-0000-0000-0000-000000000001','7.1','2026-06-01 09:01:00+00','{}'),
  ('11111111-0000-0000-0000-000000000001','assessment_completed','22222222-0000-0000-0000-000000000001','7.1','2026-06-01 09:02:00+00','{"score_percent":80}'),
  ('11111111-0000-0000-0000-000000000001','resource_viewed',     '22222222-0000-0000-0000-000000000002','7.2','2026-06-01 09:03:00+00','{}'),
  ('11111111-0000-0000-0000-000000000001','self_assessment',     '22222222-0000-0000-0000-000000000001','7.1','2026-06-01 09:04:00+00','{"confidence":4}'),
  ('11111111-0000-0000-0000-000000000002','resource_completed',  '22222222-0000-0000-0000-000000000001','7.1','2026-06-01 09:05:00+00','{}'),
  ('11111111-0000-0000-0000-000000000002','resource_completed',  '22222222-0000-0000-0000-000000000002','7.2','2026-06-01 09:06:00+00','{}'),
  ('11111111-0000-0000-0000-000000000002','assessment_completed','22222222-0000-0000-0000-000000000001','7.1','2026-06-01 09:07:00+00','{"score_percent":90}'),
  ('11111111-0000-0000-0000-000000000003','resource_completed',  '22222222-0000-0000-0000-000000000001','7.1','2026-06-01 09:08:00+00','{}'),
  ('11111111-0000-0000-0000-000000000004','resource_viewed',     '22222222-0000-0000-0000-000000000001','7.1','2026-06-01 09:09:00+00','{}'),
  ('11111111-0000-0000-0000-000000000009','resource_completed',  '22222222-0000-0000-0000-000000000001','7.1','2026-06-01 09:10:00+00','{}'),
  -- section-only self_assessment (NULL study_content_id): must be EXCLUDED from per-content
  -- assessment_summary (the spec-required null-content exclusion case).
  ('11111111-0000-0000-0000-000000000001','self_assessment',     null,                                   '7.5','2026-06-01 09:11:00+00','{"confidence":3}');
```

- [ ] **Step 3: Write `tests/conftest.py`** (test-DB-guarded; applies prereq → mig 002 → events seed once per session).
```python
"""Builds the deterministic mini-graph on a THROWAWAY learning_test DB. Refuses to run on any
DB whose DSN is not learning_test (db.py defaults to learning_dev -- this guard prevents nuking
the frozen baseline). Point LEARNING_DEV_DSN at learning_test before running these tests."""
import pathlib

import psycopg
import pytest

from learning_projections.db import dsn as _dsn

HERE = pathlib.Path(__file__).parent
REPO = HERE.parents[2]
MIG_002 = REPO / "infra" / "database" / "migrations" / "learning" / "002_learning_events.sql"
PREREQ = HERE / "projections_prereq.sql"
EVENTS = HERE / "projections_events_seed.sql"


def _target() -> str:
    d = _dsn()
    if "learning_test" not in d:
        raise RuntimeError(f"refusing to build the projections fixture on a non-test DB: {d!r}")
    return d


@pytest.fixture(scope="session", autouse=True)
def _fixture():
    d = _target()
    with psycopg.connect(d, autocommit=True) as c:
        c.execute(PREREQ.read_text(encoding="utf-8"))
        c.execute(MIG_002.read_text(encoding="utf-8"))
        c.execute(EVENTS.read_text(encoding="utf-8"))
    yield
```

- [ ] **Step 4: Write the failing smoke test `tests/test_fixture_smoke.py`.**
```python
import psycopg

from learning_projections.db import dsn


def _scalar(sql):
    with psycopg.connect(dsn(), autocommit=True) as c:
        return c.execute(sql).fetchone()[0]


def test_fixture_rows_seeded():
    assert _scalar("select count(*) from user_profiles") == 5
    assert _scalar("select count(*) from ksas where certification_level='II'") == 4
    assert _scalar("select count(*) from learning_events") == 12
    assert _scalar("select count(*) from learning_events where study_content_id is null") == 1
    assert _scalar("select count(*) from edition_ksa_map where is_active=false") == 1


def test_fixture_refuses_non_test_db(monkeypatch):
    monkeypatch.setenv("LEARNING_DEV_DSN", "host=127.0.0.1 dbname=learning_dev user=postgres")
    from tests.conftest import _target
    import pytest
    with pytest.raises(RuntimeError):
        _target()
```

- [ ] **Step 5: Run to verify it passes** (the conftest builds the fixture).
Run (export block as in Task 1 Step 7, then):
```bash
cd packages/learning-projections && PYTHONPATH=src uv run --no-project --with "psycopg[binary]" --with pytest pytest tests/test_fixture_smoke.py -q
```
Expected: `2 passed`.

- [ ] **Step 6: Commit.**
```bash
git add packages/learning-projections/tests
git commit -F - <<'EOF'
test(learning-projections): deterministic mini-graph fixture

projections_prereq.sql (full DDL + graph seed) + events seed, applied via a
test-DB-guarded session conftest that refuses any non-learning_test DSN.
EOF
```

---

## Task 3: `content_progress`

**Files:**
- Create: `src/learning_projections/projections.py` (with `content_progress` + the shared `_require_user` helper)
- Modify: `src/learning_projections/__init__.py` (export `content_progress`)
- Test: `tests/test_content_progress.py`

**Interfaces:**
- Produces: `content_progress(user_id: str) -> list[ContentProgress]`; helper `_require_user(conn, user_id)` raising `UserNotFoundError`.

- [ ] **Step 1: Write the failing test `tests/test_content_progress.py`.**
```python
import pytest

from learning_projections import UserNotFoundError, content_progress

U_TARGET = "11111111-0000-0000-0000-000000000001"
C1 = "22222222-0000-0000-0000-000000000001"
C2 = "22222222-0000-0000-0000-000000000002"


def _by_id(rows):
    return {r.study_content_id: r for r in rows}


def test_content_progress_target():
    rows = _by_id(content_progress(U_TARGET))
    assert set(rows) == {C1, C2}
    assert rows[C1].view_count == 1 and rows[C1].is_completed and rows[C1].status == "completed"
    assert rows[C2].view_count == 1 and not rows[C2].is_completed and rows[C2].status == "in_progress"
    assert rows[C1].title == "Content 1" and rows[C1].neta_section == "7.1"


def test_content_progress_unknown_user_raises():
    with pytest.raises(UserNotFoundError):
        content_progress("99999999-9999-9999-9999-999999999999")
```

- [ ] **Step 2: Run to verify it fails.**
Run: `pytest tests/test_content_progress.py -q` (with the export block).
Expected: FAIL (`ImportError: cannot import name 'content_progress'`).

- [ ] **Step 3: Write `src/learning_projections/projections.py`.**
```python
from .db import connect
from .models import ContentProgress, UserNotFoundError


def _require_user(conn, user_id: str) -> None:
    if conn.execute("select 1 from user_profiles where id = %s", (user_id,)).fetchone() is None:
        raise UserNotFoundError(f"user not found: {user_id}")


def _iso(v) -> str | None:
    return v.isoformat() if v is not None else None


def content_progress(user_id: str) -> list[ContentProgress]:
    with connect() as conn:
        _require_user(conn, user_id)
        rows = conn.execute(
            """
            select sc.id::text, sc.title, sc.neta_section_primary,
                   count(*) filter (where e.event_type='resource_viewed')     as view_count,
                   bool_or(e.event_type='resource_completed')                 as is_completed,
                   min(e.occurred_at) as first_seen_at, max(e.occurred_at) as last_activity_at
            from learning_events e
            join study_content sc on sc.id = e.study_content_id
            where e.user_id = %s and e.event_type in ('resource_viewed','resource_completed')
            group by sc.id, sc.title, sc.neta_section_primary
            order by max(e.occurred_at) desc
            """,
            (user_id,),
        ).fetchall()
    return [
        ContentProgress(
            study_content_id=r[0], title=r[1], neta_section=r[2],
            view_count=r[3], is_completed=r[4],
            status="completed" if r[4] else "in_progress",
            first_seen_at=_iso(r[5]), last_activity_at=_iso(r[6]),
        )
        for r in rows
    ]
```

- [ ] **Step 4: Add the export to `src/learning_projections/__init__.py`** — add `from .projections import content_progress` and add `"content_progress"` to `__all__`.

- [ ] **Step 5: Run to verify it passes.**
Run: `pytest tests/test_content_progress.py -q`
Expected: `2 passed`.

- [ ] **Step 6: Commit.**
```bash
git add packages/learning-projections/src packages/learning-projections/tests/test_content_progress.py
git commit -F - <<'EOF'
feat(learning-projections): content_progress read-model

Per-content view/completion derived from resource_viewed/resource_completed,
with the user-existence probe (UserNotFoundError -> 404 at the route).
EOF
```

---

## Task 4: `assessment_summary`

**Files:**
- Modify: `src/learning_projections/projections.py` (+`assessment_summary`), `src/learning_projections/__init__.py`
- Test: `tests/test_assessment_summary.py`

**Interfaces:**
- Consumes: `_require_user`, `_iso` from Task 3.
- Produces: `assessment_summary(user_id: str) -> list[AssessmentSummary]`.

- [ ] **Step 1: Write the failing test `tests/test_assessment_summary.py`.**
```python
from learning_projections import assessment_summary

U_TARGET = "11111111-0000-0000-0000-000000000001"
C1 = "22222222-0000-0000-0000-000000000001"


def test_assessment_summary_target():
    rows = assessment_summary(U_TARGET)
    assert len(rows) == 1
    a = rows[0]
    assert a.study_content_id == C1
    assert a.assessment_attempts == 1
    assert a.latest_score_percent == 80 and a.mean_score_percent == 80
    assert a.self_assessment_count == 1
    assert a.latest_confidence == 4 and a.mean_confidence == 4
    # the section-only self_assessment (NULL study_content_id) is excluded: still 1 row and
    # self_assessment_count stays 1 (would be 2 / a null row if the null-content event leaked in).
    assert all(r.study_content_id is not None for r in rows)
```

- [ ] **Step 2: Run to verify it fails.**
Expected: FAIL (`ImportError`).

- [ ] **Step 3: Add `assessment_summary` to `projections.py`** (import `AssessmentSummary`).
```python
def assessment_summary(user_id: str) -> list[AssessmentSummary]:
    with connect() as conn:
        _require_user(conn, user_id)
        rows = conn.execute(
            """
            select sc.id::text, sc.title, sc.neta_section_primary,
              count(*) filter (where e.event_type='assessment_completed') as assessment_attempts,
              (array_agg((e.payload->>'score_percent')::numeric order by e.occurred_at desc)
                 filter (where e.event_type='assessment_completed' and e.payload ? 'score_percent'))[1] as latest_score,
              avg((e.payload->>'score_percent')::numeric)
                 filter (where e.event_type='assessment_completed' and e.payload ? 'score_percent') as mean_score,
              count(*) filter (where e.event_type='self_assessment') as self_count,
              (array_agg((e.payload->>'confidence')::int order by e.occurred_at desc)
                 filter (where e.event_type='self_assessment' and e.payload ? 'confidence'))[1] as latest_conf,
              avg((e.payload->>'confidence')::numeric)
                 filter (where e.event_type='self_assessment' and e.payload ? 'confidence') as mean_conf,
              max(e.occurred_at) as last_activity_at
            from learning_events e
            join study_content sc on sc.id = e.study_content_id
            where e.user_id = %s and e.event_type in ('assessment_completed','self_assessment')
            group by sc.id, sc.title, sc.neta_section_primary
            order by max(e.occurred_at) desc
            """,
            (user_id,),
        ).fetchall()
    return [
        AssessmentSummary(
            study_content_id=r[0], title=r[1], neta_section=r[2],
            assessment_attempts=r[3],
            latest_score_percent=float(r[4]) if r[4] is not None else None,
            mean_score_percent=round(float(r[5]), 1) if r[5] is not None else None,
            self_assessment_count=r[6],
            latest_confidence=int(r[7]) if r[7] is not None else None,
            mean_confidence=round(float(r[8]), 1) if r[8] is not None else None,
            last_activity_at=_iso(r[9]),
        )
        for r in rows
    ]
```
Add `AssessmentSummary` to the `from .models import ...` line.

- [ ] **Step 4: Export** `assessment_summary` in `__init__.py`.

- [ ] **Step 5: Run to verify it passes.**
Expected: `1 passed`.

- [ ] **Step 6: Commit.**
```bash
git add packages/learning-projections/src packages/learning-projections/tests/test_assessment_summary.py
git commit -F - <<'EOF'
feat(learning-projections): assessment_summary read-model

Objective score (assessment_completed.score_percent) + subjective confidence
(self_assessment.confidence) per content; section-only self-assessments excluded.
EOF
```

---

## Task 5: `competency_rollup`

**Files:**
- Modify: `src/learning_projections/projections.py` (+`competency_rollup` + `_resolve_level`), `__init__.py`
- Test: `tests/test_competency_rollup.py`

**Interfaces:**
- Produces: `competency_rollup(user_id: str, level: str | None = None) -> CompetencyRollup`.

- [ ] **Step 1: Write the failing test `tests/test_competency_rollup.py`.**
```python
from learning_projections import competency_rollup

U_TARGET = "11111111-0000-0000-0000-000000000001"
U_CURRENT = "11111111-0000-0000-0000-000000000002"
U_ALL = "11111111-0000-0000-0000-000000000003"
U_NONE = "11111111-0000-0000-0000-000000000004"


def _cov(r):
    return {c.level: c for c in r.coverage}


def test_target_level_ii():
    r = competency_rollup(U_TARGET)
    assert (r.resolved_level, r.level_source, r.levels_in_scope) == ("II", "target", ["II"])
    c = _cov(r)["II"]
    assert (c.total_ksas_at_level, c.covered_ksas, c.coverage_percent) == (4, 2, 50.0)
    assert r.evidence_event_count == 2
    assert {c.concept_id for c in r.engaged_concepts} == {"concept-1", "concept-2"}


def test_current_orphan_and_inactive_excluded():
    r = competency_rollup(U_CURRENT)
    assert (r.resolved_level, r.level_source) == ("III", "current")
    c = _cov(r)["III"]
    assert (c.total_ksas_at_level, c.covered_ksas, c.coverage_percent) == (3, 2, 66.7)
    # orphan-only concept-3 appears in engaged_concepts though it adds 0 covered ksas:
    assert {c.concept_id for c in r.engaged_concepts} == {"concept-1", "concept-2", "concept-3"}
    assert r.evidence_event_count == 3


def test_all_fallback():
    r = competency_rollup(U_ALL)
    assert (r.resolved_level, r.level_source, r.levels_in_scope) == ("all", "all", ["II", "III", "IV"])
    c = _cov(r)
    assert (c["II"].covered_ksas, c["II"].coverage_percent) == (2, 50.0)
    assert (c["III"].covered_ksas, c["III"].coverage_percent) == (2, 66.7)
    assert (c["IV"].total_ksas_at_level, c["IV"].covered_ksas, c["IV"].coverage_percent) == (2, 0, 0.0)


def test_explicit_level_i_is_null_coverage():
    r = competency_rollup(U_TARGET, level="I")
    assert (r.resolved_level, r.level_source, r.levels_in_scope) == ("I", "explicit", ["I"])
    c = _cov(r)["I"]
    assert (c.total_ksas_at_level, c.covered_ksas, c.coverage_percent) == (0, 0, None)


def test_no_evidence_zero():
    r = competency_rollup(U_NONE)
    c = _cov(r)["II"]
    assert (c.covered_ksas, c.coverage_percent) == (0, 0.0)
    assert r.evidence_event_count == 0 and r.engaged_concepts == []
```

- [ ] **Step 2: Run to verify it fails.** Expected: FAIL (`ImportError`).

- [ ] **Step 3: Add `_resolve_level` + `competency_rollup` to `projections.py`** (import `CompetencyRollup, LevelCoverage, ConceptRef`).
```python
ALL_LEVELS = ["II", "III", "IV"]


def _resolve_level(conn, user_id, level):
    if level is not None:
        return level, "explicit", [level]
    row = conn.execute(
        "select target_certification_level, current_certification_level from user_profiles where id=%s",
        (user_id,),
    ).fetchone()
    target, current = row
    if target is not None:
        return target, "target", [target]
    if current is not None:
        return current, "current", [current]
    return "all", "all", list(ALL_LEVELS)


def competency_rollup(user_id: str, level: str | None = None) -> CompetencyRollup:
    with connect() as conn:
        _require_user(conn, user_id)
        resolved, source, scope = _resolve_level(conn, user_id, level)

        evidence_event_count = conn.execute(
            """select count(*) from learning_events
               where user_id=%s and event_type in ('resource_completed','assessment_completed')
                 and study_content_id is not null""",
            (user_id,),
        ).fetchone()[0]

        # covered ksa_code grouped by level (active maps, level-pinned, orphans dropped by the
        # inner join). NOTE: this is computed across ALL reachable levels; the `scope` loop below
        # is what filters to levels_in_scope -- the SQL is intentionally not scope-pinned.
        covered_rows = conn.execute(
            """
            with evidence as (
              select distinct study_content_id as content_id from learning_events
              where user_id=%s and event_type in ('resource_completed','assessment_completed')
                and study_content_id is not null
            ),
            covered as (
              select distinct k.ksa_code, k.certification_level::text as lvl
              from evidence ev
              join content_concept_links ccl on ccl.content_id = ev.content_id
              join edition_ksa_map ekm on ekm.concept_id = ccl.concept_id and ekm.is_active
              join ksas k on k.ksa_code = ekm.ksa_code and k.certification_level::text = ekm.level
            )
            select lvl, count(distinct ksa_code) from covered group by lvl
            """,
            (user_id,),
        ).fetchall()
        covered_by_level = {lvl: n for lvl, n in covered_rows}

        totals = dict(
            conn.execute(
                "select certification_level::text, count(distinct ksa_code) from ksas group by 1"
            ).fetchall()
        )

        engaged = conn.execute(
            """
            with evidence as (
              select distinct study_content_id as content_id from learning_events
              where user_id=%s and event_type in ('resource_completed','assessment_completed')
                and study_content_id is not null
            )
            select distinct c.concept_id, c.concept_description
            from evidence ev
            join content_concept_links ccl on ccl.content_id = ev.content_id
            join concepts c on c.concept_id = ccl.concept_id
            order by c.concept_id
            """,
            (user_id,),
        ).fetchall()

    coverage = []
    for lvl in scope:
        total = totals.get(lvl, 0)
        cov = covered_by_level.get(lvl, 0)
        pct = round(100.0 * cov / total, 1) if total > 0 else None
        coverage.append(LevelCoverage(level=lvl, total_ksas_at_level=total, covered_ksas=cov, coverage_percent=pct))

    return CompetencyRollup(
        user_id=user_id, resolved_level=resolved, level_source=source, levels_in_scope=scope,
        evidence_event_count=evidence_event_count, coverage=coverage,
        engaged_concepts=[ConceptRef(concept_id=r[0], concept_description=r[1]) for r in engaged],
    )
```
Add `CompetencyRollup, LevelCoverage, ConceptRef` to the models import.

- [ ] **Step 4: Export** `competency_rollup`.

- [ ] **Step 5: Run to verify it passes.** Expected: `5 passed`.

- [ ] **Step 6: Commit.**
```bash
git add packages/learning-projections/src packages/learning-projections/tests/test_competency_rollup.py
git commit -F - <<'EOF'
feat(learning-projections): competency_rollup read-model

Per-level covered/total/coverage_percent over the active, level-pinned KSA
graph (orphans + inactive maps excluded; editions de-duped; Level I -> null);
non-silent resolved_level/level_source/levels_in_scope; engaged_concepts.
EOF
```

---

## Task 6: `cohort_aggregate`

**Files:**
- Modify: `src/learning_projections/projections.py` (+`cohort_aggregate`), `__init__.py`
- Test: `tests/test_cohort_aggregate.py`

**Interfaces:**
- Produces: `cohort_aggregate(level: str | None = None) -> CohortAggregate`.

- [ ] **Step 1: Write the failing test `tests/test_cohort_aggregate.py`.**
```python
from learning_projections import cohort_aggregate


def test_cohort_no_level():
    a = cohort_aggregate()
    assert a.user_count == 4                      # active only (U_inactive excluded)
    assert a.mean_completed_content == 1.0        # (1+2+1+0)/4
    assert a.mean_latest_score == 85.0 and a.scored_user_count == 2
    assert a.mean_coverage_percent == 38.9 and a.coverage_user_count == 3   # U_all 'all' excluded


def test_cohort_explicit_level_ii():
    a = cohort_aggregate(level="II")
    assert a.coverage_user_count == 4
    assert a.mean_coverage_percent == 37.5        # (50+50+50+0)/4


def test_cohort_level_i_degenerate():
    a = cohort_aggregate(level="I")
    assert a.mean_coverage_percent is None and a.coverage_user_count == 0
    assert a.mean_completed_content == 1.0 and a.mean_latest_score == 85.0
```

- [ ] **Step 2: Run to verify it fails.** Expected: FAIL (`ImportError`).

- [ ] **Step 3: Add `cohort_aggregate` to `projections.py`** (reuses `competency_rollup` per-user; aggregates in Python).
```python
def cohort_aggregate(level: str | None = None) -> CohortAggregate:
    with connect() as conn:
        users = [r[0] for r in conn.execute(
            "select id::text from user_profiles where is_active order by id").fetchall()]
        completed = dict(conn.execute(
            """select user_id::text, count(distinct study_content_id)
               from learning_events where event_type='resource_completed' and study_content_id is not null
               group by 1""").fetchall())
        latest = dict(conn.execute(
            """select user_id::text,
                 (array_agg((payload->>'score_percent')::numeric order by occurred_at desc)
                   filter (where payload ? 'score_percent'))[1]
               from learning_events where event_type='assessment_completed' group by 1""").fetchall())

    completed_counts = [completed.get(u, 0) for u in users]
    scores = [float(latest[u]) for u in users if latest.get(u) is not None]

    per_user_cov = []
    for u in users:
        roll = competency_rollup(u, level=level)
        if level is not None:
            pct = roll.coverage[0].coverage_percent
        elif roll.resolved_level == "all":
            pct = None                      # 'all'-resolved users have no single coverage_percent
        else:
            pct = roll.coverage[0].coverage_percent
        if pct is not None:
            per_user_cov.append(pct)

    n = len(users)
    return CohortAggregate(
        level=level,
        user_count=n,
        mean_completed_content=round(sum(completed_counts) / n, 1) if n else 0.0,
        mean_latest_score=round(sum(scores) / len(scores), 1) if scores else None,
        scored_user_count=len(scores),
        mean_coverage_percent=round(sum(per_user_cov) / len(per_user_cov), 1) if per_user_cov else None,
        coverage_user_count=len(per_user_cov),
    )
```
Add `CohortAggregate` to the models import.

- [ ] **Step 4: Export** `cohort_aggregate`.

- [ ] **Step 5: Run to verify it passes.** Expected: `3 passed`.

- [ ] **Step 6: Run the WHOLE package suite.**
Run: `pytest tests/ -q`
Expected: all pass (read-only, fixture-smoke, 4 read-models).

- [ ] **Step 7: Commit.**
```bash
git add packages/learning-projections/src packages/learning-projections/tests/test_cohort_aggregate.py
git commit -F - <<'EOF'
feat(learning-projections): cohort_aggregate read-model

Active-user aggregate: mean_completed_content (0 for non-completers),
mean_latest_score over scored users, per-user-then-averaged coverage
(all-resolved + level-I excluded); computed per-user then aggregated.
EOF
```

---

## Task 7: CLI + final exports

**Files:**
- Create: `src/learning_projections/cli.py`
- Modify: `src/learning_projections/__init__.py` (already exports the 4 funcs)
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: the 4 projection functions.
- Produces: `cli.main(argv) -> int`.

- [ ] **Step 1: Write the failing test `tests/test_cli.py`.**
```python
import json

from learning_projections.cli import main

U_TARGET = "11111111-0000-0000-0000-000000000001"


def test_cli_competency_json(capsys):
    rc = main(["competency", "--user", U_TARGET])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["resolved_level"] == "II"
    assert out["coverage"][0]["covered_ksas"] == 2


def test_cli_cohort_json(capsys):
    rc = main(["cohort"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["user_count"] == 4
```

- [ ] **Step 2: Run to verify it fails.** Expected: FAIL (`ModuleNotFoundError: learning_projections.cli`).

- [ ] **Step 3: Write `src/learning_projections/cli.py`** (thin pass-through, no logic).
```python
import argparse
import dataclasses
import json
import sys

from .projections import assessment_summary, cohort_aggregate, competency_rollup, content_progress


def _dump(obj):
    if isinstance(obj, list):
        return [dataclasses.asdict(o) for o in obj]
    return dataclasses.asdict(obj)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="learning-projections",
                                 description="Read-model projections over learning_events (learning_dev); prints JSON")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("progress", "assessments", "competency"):
        p = sub.add_parser(name)
        p.add_argument("--user", required=True)
        if name == "competency":
            p.add_argument("--level", default=None, choices=["I", "II", "III", "IV"])
    pc = sub.add_parser("cohort")
    pc.add_argument("--level", default=None, choices=["I", "II", "III", "IV"])
    args = ap.parse_args(argv)

    if args.cmd == "progress":
        result = content_progress(args.user)
    elif args.cmd == "assessments":
        result = assessment_summary(args.user)
    elif args.cmd == "competency":
        result = competency_rollup(args.user, level=args.level)
    elif args.cmd == "cohort":
        result = cohort_aggregate(level=args.level)
    else:
        return 1
    print(json.dumps(_dump(result), ensure_ascii=False, default=str))
    return 0
```

- [ ] **Step 4: Run to verify it passes.** Expected: `2 passed`.

- [ ] **Step 5: Run the whole package suite again.** Expected: all pass.

- [ ] **Step 6: Commit.**
```bash
git add packages/learning-projections/src/learning_projections/cli.py packages/learning-projections/tests/test_cli.py
git commit -F - <<'EOF'
feat(learning-projections): thin CLI wrapper

progress|assessments|competency|cohort subcommands, pure pass-through to the
four projection functions (no logic of their own).
EOF
```

---

## Task 8: control-plane-api routes

**Files:**
- Modify: `apps/control-plane-api/services/learning/router.py`, `services/learning/schemas.py`, `requirements.txt`
- Test: `apps/control-plane-api/tests/test_learning_projections.py`

**Interfaces:**
- Consumes: `learning_projections.{content_progress, assessment_summary, competency_rollup, cohort_aggregate, UserNotFoundError}`.
- Produces: `GET /api/v1/learning/{progress,assessments,competency,cohort}`.

- [ ] **Step 1: Add `-e ../../packages/learning-projections` to `requirements.txt`** (after the `learning-capture` line).

- [ ] **Step 2: Add the 6 Pydantic models to `services/learning/schemas.py`.**
```python
class ContentProgressOut(BaseModel):
    study_content_id: str
    title: str | None = None
    neta_section: str | None = None
    view_count: int
    is_completed: bool
    status: str
    first_seen_at: str | None = None
    last_activity_at: str | None = None


class AssessmentSummaryOut(BaseModel):
    study_content_id: str
    title: str | None = None
    neta_section: str | None = None
    assessment_attempts: int
    latest_score_percent: float | None = None
    mean_score_percent: float | None = None
    self_assessment_count: int
    latest_confidence: int | None = None
    mean_confidence: float | None = None
    last_activity_at: str | None = None


class ConceptRefOut(BaseModel):
    concept_id: str
    concept_description: str | None = None


class LevelCoverageOut(BaseModel):
    level: str
    total_ksas_at_level: int
    covered_ksas: int
    coverage_percent: float | None = None


class CompetencyRollupOut(BaseModel):
    user_id: str
    resolved_level: str
    level_source: str
    levels_in_scope: list[str]
    evidence_event_count: int
    coverage: list[LevelCoverageOut]
    engaged_concepts: list[ConceptRefOut]


class CohortAggregateOut(BaseModel):
    level: str | None = None
    user_count: int
    mean_completed_content: float
    mean_latest_score: float | None = None
    scored_user_count: int
    mean_coverage_percent: float | None = None
    coverage_user_count: int


class ProgressResponse(BaseModel):
    items: list[ContentProgressOut]


class AssessmentsResponse(BaseModel):
    items: list[AssessmentSummaryOut]
```

- [ ] **Step 3: Add the 4 routes to `services/learning/router.py`.** Extend the existing imports and add the routes. New import line:
```python
from learning_projections import (
    assessment_summary, cohort_aggregate, competency_rollup, content_progress, UserNotFoundError,
)
```
Add a UUID validator + routes:
```python
import uuid as _uuid


def _valid_user(user_id: str | None) -> str:
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")
    try:
        _uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id must be a UUID")
    return user_id


def _valid_level(level: str | None) -> str | None:
    if level is not None and level not in {"I", "II", "III", "IV"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="level must be I, II, III, or IV")
    return level


@router.get("/progress", response_model=ProgressResponse)
def get_progress(user_id: str | None = Query(default=None)) -> ProgressResponse:
    uid = _valid_user(user_id)
    try:
        rows = content_progress(uid)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return ProgressResponse(items=[ContentProgressOut(**vars(r)) for r in rows])


@router.get("/assessments", response_model=AssessmentsResponse)
def get_assessments(user_id: str | None = Query(default=None)) -> AssessmentsResponse:
    uid = _valid_user(user_id)
    try:
        rows = assessment_summary(uid)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return AssessmentsResponse(items=[AssessmentSummaryOut(**vars(r)) for r in rows])


@router.get("/competency", response_model=CompetencyRollupOut)
def get_competency(user_id: str | None = Query(default=None),
                   level: str | None = Query(default=None)) -> CompetencyRollupOut:
    uid = _valid_user(user_id)
    _valid_level(level)
    try:
        roll = competency_rollup(uid, level=level)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return CompetencyRollupOut(
        user_id=roll.user_id, resolved_level=roll.resolved_level, level_source=roll.level_source,
        levels_in_scope=roll.levels_in_scope, evidence_event_count=roll.evidence_event_count,
        coverage=[LevelCoverageOut(**vars(c)) for c in roll.coverage],
        engaged_concepts=[ConceptRefOut(**vars(c)) for c in roll.engaged_concepts],
    )


@router.get("/cohort", response_model=CohortAggregateOut)
def get_cohort(level: str | None = Query(default=None)) -> CohortAggregateOut:
    _valid_level(level)
    return CohortAggregateOut(**vars(cohort_aggregate(level=level)))
```
Add the new schema names to the `from .schemas import (...)` block: `AssessmentsResponse, AssessmentSummaryOut, CohortAggregateOut, CompetencyRollupOut, ConceptRefOut, ContentProgressOut, LevelCoverageOut, ProgressResponse`.

- [ ] **Step 4: Write the failing route test `apps/control-plane-api/tests/test_learning_projections.py`.**
```python
"""control-plane-api Slice 2b projection routes. LEARNING_DEV_DSN is pinned to learning_test by
the run command (the mini-graph fixture must be applied there first)."""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
U_TARGET = "11111111-0000-0000-0000-000000000001"


def test_progress_ok():
    r = client.get("/api/v1/learning/progress", params={"user_id": U_TARGET})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 2


def test_progress_missing_user_400():
    assert client.get("/api/v1/learning/progress").status_code == 400


def test_progress_bad_uuid_400():
    assert client.get("/api/v1/learning/progress", params={"user_id": "nope"}).status_code == 400


def test_progress_unknown_user_404():
    r = client.get("/api/v1/learning/progress", params={"user_id": "99999999-9999-9999-9999-999999999999"})
    assert r.status_code == 404


def test_competency_ok():
    r = client.get("/api/v1/learning/competency", params={"user_id": U_TARGET})
    body = r.json()
    assert r.status_code == 200
    assert body["resolved_level"] == "II" and body["coverage"][0]["covered_ksas"] == 2


def test_competency_bad_level_400():
    assert client.get("/api/v1/learning/competency",
                      params={"user_id": U_TARGET, "level": "Z"}).status_code == 400


def test_cohort_ok():
    r = client.get("/api/v1/learning/cohort")
    assert r.status_code == 200
    assert r.json()["user_count"] == 4


U_NONE = "11111111-0000-0000-0000-000000000004"
UNKNOWN = "99999999-9999-9999-9999-999999999999"


def test_assessments_empty_200_for_view_only_user():
    # U_none has only a resource_viewed event -> known user, zero assessments -> 200 + []
    r = client.get("/api/v1/learning/assessments", params={"user_id": U_NONE})
    assert r.status_code == 200 and r.json()["items"] == []


def test_assessments_unknown_user_404():
    assert client.get("/api/v1/learning/assessments", params={"user_id": UNKNOWN}).status_code == 404


def test_competency_unknown_user_404():
    assert client.get("/api/v1/learning/competency", params={"user_id": UNKNOWN}).status_code == 404


def test_competency_is_bare_object_not_wrapped():
    # competency/cohort intentionally return the bare *Out, not an {items: [...]} wrapper
    body = client.get("/api/v1/learning/competency", params={"user_id": U_TARGET}).json()
    assert "items" not in body and "coverage" in body


def test_competency_level_param_passthrough():
    r = client.get("/api/v1/learning/competency", params={"user_id": U_TARGET, "level": "I"})
    body = r.json()
    assert r.status_code == 200
    assert body["resolved_level"] == "I" and body["coverage"][0]["coverage_percent"] is None


def test_cohort_level_param_passthrough():
    r = client.get("/api/v1/learning/cohort", params={"level": "II"})
    assert r.status_code == 200
    assert r.json()["mean_coverage_percent"] == 37.5


def test_learning_routes_absent_when_guard_disabled():
    # spec error matrix: guard env unset -> router not registered -> 404. The guard runs at
    # main-import time, so monkeypatching after `from main import app` is too late -- run an
    # import-isolated subprocess with the learning DSN/PGPASSWORD cleared.
    import os
    import subprocess
    import sys

    env = dict(os.environ)
    env.pop("LEARNING_DEV_DSN", None)
    env.pop("LEARNING_DEV_PGPASSWORD", None)
    snippet = (
        "from fastapi.testclient import TestClient; from main import app; "
        "c = TestClient(app); "
        "r = c.get('/api/v1/learning/progress', params={'user_id': '11111111-0000-0000-0000-000000000001'}); "
        "assert r.status_code == 404, r.status_code; print('GUARD_OK')"
    )
    api_dir = os.path.dirname(os.path.dirname(__file__))  # apps/control-plane-api
    proc = subprocess.run([sys.executable, "-c", snippet], cwd=api_dir, env=env,
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "GUARD_OK" in proc.stdout
```

- [ ] **Step 5: Run to verify it fails** (routes not added / package not installed), then passes after Steps 1-3. Apply the fixture to `learning_test`, then run with the learning DSN pinned there:
```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-learning-lane && set -a && . ./infra/.env && set +a && export PATH="$HOME/.local/bin:$PATH" PGPASSWORD=$DEV_PG_PASSWORD && \
  P=packages/learning-projections/tests && \
  psql -h 127.0.0.1 -U postgres -d learning_test -f $P/projections_prereq.sql -q && \
  psql -h 127.0.0.1 -U postgres -d learning_test -f infra/database/migrations/learning/002_learning_events.sql -q && \
  psql -h 127.0.0.1 -U postgres -d learning_test -f $P/projections_events_seed.sql -q && \
  cd apps/control-plane-api && \
  export DATABASE_URL="postgresql://postgres:$DEV_PG_PASSWORD@127.0.0.1:5432/learning_test" \
         LEARNING_DEV_DSN="host=127.0.0.1 port=5432 dbname=learning_test user=postgres password=$DEV_PG_PASSWORD sslmode=disable" && \
  uv run --with-requirements requirements-dev.txt --with ../../packages/learning-projections pytest tests/test_learning_projections.py -q'
```
Expected: `14 passed`. (If `DATABASE_URL` form differs, copy the working value from the existing `test_learning_events.py` run in the Slice 2a notes.)

- [ ] **Step 6: Commit.**
```bash
git add apps/control-plane-api/services/learning apps/control-plane-api/requirements.txt apps/control-plane-api/tests/test_learning_projections.py
git commit -F - <<'EOF'
feat(control-plane-api): Slice 2b projection routes

GET /api/v1/learning/{progress,assessments,competency,cohort} over the
learning-projections package, behind the existing learning-router guard;
400 on bad user_id/level, 404 (UserNotFoundError) on unknown user.
EOF
```

---

## Self-Review (run before handing off)

**1. Spec coverage:** content_progress (T3), assessment_summary (T4), competency_rollup (T5), cohort_aggregate (T6), CLI (T7), 4 routes + 6 Pydantic models (T8), read-only test (T1), mini-graph fixture incl. inactive map + orphan + level-fallback users (T2), error matrix 400/404/empty (T8 tests), payload contract (T4 SQL), engaged_concepts naming (T5). The fixture exercises is_active exclusion, orphan exclusion, edition de-dup, Level-I null, and the target/current/all fallbacks.

**2. Placeholder scan:** every code step contains complete code; every run step has an exact command + expected output. No TBD/TODO.

**3. Type consistency:** dataclass field names (T1) ↔ SQL column aliases (T3-T6) ↔ Pydantic `*Out` fields (T8) ↔ test assertions all use the same names (`covered_ksas`, `coverage_percent`, `evidence_event_count`, `engaged_concepts`, `mean_coverage_percent`, `coverage_user_count`). `UserNotFoundError` raised in T3-T5, mapped to 404 in T8. No `mastered`/`mastery` token in any generated field name, response key, or docstring (the rule is scoped to generated artifacts, not this plan's prose).

**4. Error/guard matrix:** 400 (missing/blank/bad-uuid user_id, bad level), 404 (unknown user — /progress, /assessments, /competency), 200-empty (/assessments for a view-only user), bare-object vs wrapped contract, level passthrough, and the **guard-disabled router-absent 404** (import-isolated subprocess) are all route-tested (T8). The section-only `self_assessment` exclusion is fixtured (T2) and asserted (T4). Lane charter `Branch:` corrected before any code (T0 Step 2).

**Note on cohort 'all'-resolved users:** a spec detail made explicit here — in a no-level cohort call, a user whose resolved level is `all` contributes `null` (excluded) to `mean_coverage_percent`. This is implemented in T6 and asserted by `test_cohort_no_level` (U_all excluded → coverage_user_count 3).
