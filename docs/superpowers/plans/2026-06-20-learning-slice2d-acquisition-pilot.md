# Learning Slice 2d — Controlled Acquisition Pilot — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement
> this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the first real, auditable learning evidence exist in `learning_dev` and prove it flows
through all four Slice 2b read models — via a guarded capture helper + a rehearsal acquisition run —
without new event types, without a schema migration, and without any prod write.

**Architecture:** One new guarded helper (`record_acquired_event`) wraps the existing 2a `record_event`
and structurally enforces a provenance envelope. A small CLI subcommand exposes it. SQL scripts
provision the rehearsal cohort (idempotent; non-destructive reversal). A cross-package e2e test proves
the real engine moves to a pre-registered manifest on `learning_test`. The live rehearsal run (Task 6)
is operator-gated (the `data_write` gate) and produces a redacted evidence packet.

**Tech stack:** Python 3.12 (`packages/learning-capture`), Postgres `learning_dev`/`learning_test`
(host PG17 :5432), the existing `control-plane-api` learning GET routes, `pytest`, `uv`.

## Global Constraints

- **DEV-ONLY.** All automated work runs against throwaway `learning_test`; only Task 6 writes
  `learning_dev`, and only under the operator `data_write` gate. **No prod write, ever.** The helper
  hard-refuses any DSN that is not `learning_dev`/`learning_test` (aborts on `*.supabase.co` or the
  prod ref `fxoyniqnrlkxfligbxmg`).
- **No schema migration; no new DB objects.** All provenance metadata rides the existing
  `learning_events.payload` jsonb. The 4 event types are a hard DB CHECK invariant — never add a 5th.
- **No raw `INSERT` into `learning_events`.** Event capture goes only through the helper. Raw SQL is
  allowed only for `user_profiles` cohort provisioning.
- **Provenance envelope is mandatory** on every captured event: `acquisition_run_id`, `source_surface`
  (`cli` | `operations-web/learning-demo` | `manual-runbook`), `observed_by` (handle/initials),
  `evidence_ref` (opaque pointer — never PII), `data_fidelity` (`synthetic` | `rehearsal` |
  `authentic`). Exact payload keys: `score_percent` (numeric 0–100) for `assessment_completed`,
  `confidence` (int 1–5) for `self_assessment`.
- **Acquisition events are content-bound.** `record_acquired_event` requires a non-null
  `study_content_id` for **every** event type — all four read models are per-content, so a
  content-less acquisition event would silently vanish from the proof. (This is a 2d tightening over
  the base 2a `record_event`, which still permits section-only capture.) The envelope is a fixed set
  of keys; the helper takes **no** free-form `extra` payload (no silent-typo vector).
- **Engagement-not-mastery.** Generated code/docs never use `mastered`/`mastery`. `coverage_percent`
  is annotated as mapping-breadth, not competence.
- **Redaction.** Committable artifacts carry handles only. The real person↔handle map + observation
  notes stay in private `.claude/PLATFORM/` (operator-held), referenced by `evidence_ref`.
- **Non-destructive reversal in `learning_dev`:** retire (`is_active=false`), never delete (FK cascade
  into the immutable ledger trips the append-only trigger). Destructive teardown is `learning_test`-only.
- **Git:** exact `git add <paths>` only — never `git add -A` (sweeps gitignored `.superpowers/`).
  Commit messages contain no apostrophes.

---

## File Structure

- `docs/lanes/README.md` — **modify** (Task 0): active branch + `data_write` gate.
- `packages/learning-capture/src/learning_capture/acquisition.py` — **create** (Task 1): the helper.
- `packages/learning-capture/tests/test_acquisition.py` — **create** (Task 1): helper unit tests.
- `packages/learning-capture/src/learning_capture/cli.py` — **modify** (Task 2): `acquire` subcommand.
- `packages/learning-capture/tests/test_cli.py` — **modify** (Task 2): `acquire` parse/dispatch test.
- `scripts/learning/slice2d_provision_cohort.sql` — **create** (Task 3): idempotent cohort provisioning.
- `scripts/learning/slice2d_retire_cohort.sql` — **create** (Task 3): non-destructive reversal.
- `packages/learning-capture/tests/test_provision_cohort.py` — **create** (Task 3): provisioning test.
- `packages/learning-projections/tests/acquisition_prereq.sql` — **create** (Task 4): fixture extension
  + negative-control subjects.
- `packages/learning-projections/tests/test_acquisition_run.py` — **create** (Task 4): cross-package
  e2e manifest test.
- `packages/learning-projections/pyproject.toml` — **modify** (Task 4): add `learning-capture` test dep.
- `docs/learning/slice2d/runbook.md` — **create** (Task 5): the operator run protocol.
- `docs/learning/slice2d/evidence_packet.template.md` — **create** (Task 5): redacted packet template.
- `scripts/learning/redaction_check.sh` — **create** (Task 5): mechanical pre-commit PII guard.
- `packages/learning-capture/tests/test_redaction_check.py` — **create** (Task 5): guard test.

---

## Task 0: Lane charter — active branch + data_write gate

**Files:** Modify `docs/lanes/README.md` (the learning lane block).

- [ ] **Step 1: Update the Branch and Gates lines.** In the `### Lane: learning` block, set the Branch
  line to the active branch and add the `data_write` gate:

Replace the Branch line with:
```
- **Branch:** `learning/slice2d-acquisition-pilot`   **Worktree:** `/home/olares/code/apex/apex-learning-lane`
```
Replace the Gates line with:
```
- **Gates (human-approval):** `schema` (each `learning_dev` migration apply; `001`/`002` **DONE 2026-06-20**); `data_write` (**NEW** — Slice 2d writes business data: cohort provisioning + event capture into `learning_dev` are operator-approved, distinct from schema apply); promotion (merge to main) is operator-gated.
```
**Extend the Write-boundary (OWNS) list** — the plan creates files the current boundary excludes.
Append to the `Write-boundary (OWNS)` bullet:
```
`scripts/learning/**`, `docs/learning/slice2d/**`, `docs/superpowers/{specs,plans}/2026-06-20-learning-slice2d-*`
```

Update the Status line to append:
```
NEXT = Slice 2d controlled acquisition pilot (in progress; spec `2c9521d8`).
```

- [ ] **Step 2: Commit.**
```bash
git add docs/lanes/README.md
git commit -m "docs(lanes): Slice 2d active branch + data_write gate"
```

---

## Task 1: Guarded acquisition helper (`record_acquired_event`)

**Files:**
- Create: `packages/learning-capture/src/learning_capture/acquisition.py`
- Test: `packages/learning-capture/tests/test_acquisition.py`

**Interfaces:**
- Consumes: `learning_capture.capture.record_event(user_id, event_type, *, study_content_id, neta_section, payload) -> CapturedEvent`; `learning_capture.capture.CaptureError`; `learning_capture.db.dsn() -> str`.
- Produces: `record_acquired_event(*, user_id, event_type, acquisition_run_id, source_surface, observed_by, evidence_ref, data_fidelity, study_content_id=None, neta_section=None, score_percent=None, confidence=None) -> CapturedEvent`; module constants `SOURCE_SURFACES`, `DATA_FIDELITIES`.

The existing `conftest.py` pins `LEARNING_DEV_DSN` to `learning_test` and seeds `user_profiles.id =
00000000-0000-0000-0000-000000000001` + `study_content.id = 00000000-0000-0000-0000-000000000010`.

- [ ] **Step 1: Write the failing tests.**
```python
# packages/learning-capture/tests/test_acquisition.py
import os
import pytest
from learning_capture.acquisition import record_acquired_event, SOURCE_SURFACES, DATA_FIDELITIES
from learning_capture.capture import CaptureError, list_events

USER = "00000000-0000-0000-0000-000000000001"
CONTENT = "00000000-0000-0000-0000-000000000010"
ENV = dict(acquisition_run_id="run-T", source_surface="cli", observed_by="JS",
           evidence_ref="notes#L1", data_fidelity="rehearsal")


def test_happy_path_writes_envelope_into_payload():
    ev = record_acquired_event(user_id=USER, event_type="resource_completed",
                               study_content_id=CONTENT, neta_section="7.1", **ENV)
    assert ev.payload["acquisition_run_id"] == "run-T"
    assert ev.payload["source_surface"] == "cli"
    assert ev.payload["observed_by"] == "JS"
    assert ev.payload["evidence_ref"] == "notes#L1"
    assert ev.payload["data_fidelity"] == "rehearsal"


@pytest.mark.parametrize("missing", list(ENV))
def test_each_envelope_key_required_nonempty(missing):
    bad = dict(ENV, **{missing: "  "})
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="resource_viewed",
                              study_content_id=CONTENT, **bad)


def test_bad_source_surface_and_fidelity_rejected():
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="resource_viewed", study_content_id=CONTENT,
                              **dict(ENV, source_surface="curl"))
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="resource_viewed", study_content_id=CONTENT,
                              **dict(ENV, data_fidelity="real"))


def test_assessment_requires_score_and_self_requires_confidence():
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="assessment_completed",
                              study_content_id=CONTENT, **ENV)  # no score_percent
    ev = record_acquired_event(user_id=USER, event_type="assessment_completed",
                               study_content_id=CONTENT, score_percent=88, **ENV)
    assert ev.payload["score_percent"] == 88
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="self_assessment",
                              study_content_id=CONTENT, **ENV)  # no confidence


@pytest.mark.parametrize("et", ["resource_viewed", "resource_completed",
                                "assessment_completed", "self_assessment"])
def test_content_id_required_for_every_event_type(et):
    kw = dict(ENV)
    if et == "assessment_completed":
        kw["score_percent"] = 80
    if et == "self_assessment":
        kw["confidence"] = 3
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type=et, study_content_id=None, **kw)


def test_prod_isolation_guard_refuses_supabase_host(monkeypatch):
    monkeypatch.setenv("LEARNING_DEV_DSN",
                       "host=db.fxoyniqnrlkxfligbxmg.supabase.co dbname=postgres user=postgres")
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="resource_viewed", study_content_id=CONTENT, **ENV)


def test_prod_isolation_guard_refuses_non_dev_dbname(monkeypatch):
    monkeypatch.setenv("LEARNING_DEV_DSN", "host=127.0.0.1 dbname=postgres user=postgres")
    with pytest.raises(CaptureError):
        record_acquired_event(user_id=USER, event_type="resource_viewed", study_content_id=CONTENT, **ENV)
```

- [ ] **Step 2: Run to verify they fail.**
Run (from `packages/learning-capture`, with `LEARNING_DEV_DSN`/`LEARNING_TEST_DSN` → `learning_test`):
`uv run pytest tests/test_acquisition.py -v`
Expected: FAIL — `ModuleNotFoundError: learning_capture.acquisition`.

- [ ] **Step 3: Write the helper.**
```python
# packages/learning-capture/src/learning_capture/acquisition.py
"""Slice 2d acquisition helper: a guarded wrapper over record_event that STRUCTURALLY enforces the
provenance envelope, so a captured event is auditable -- not byte-indistinguishable from fabricated
data. Refuses any target that is not learning_dev / learning_test, and requires every acquisition
event to be content-bound (study_content_id) so the evidence is always projection-visible. Stricter
than the base 2a record_event by design."""
from psycopg.conninfo import conninfo_to_dict

from .capture import CaptureError, record_event
from .db import dsn

SOURCE_SURFACES = frozenset({"cli", "operations-web/learning-demo", "manual-runbook"})
DATA_FIDELITIES = frozenset({"synthetic", "rehearsal", "authentic"})
_ENVELOPE = ("acquisition_run_id", "source_surface", "observed_by", "evidence_ref", "data_fidelity")


def _guard_target() -> None:
    # Parse the DSN robustly (keyword OR url form) instead of brittle substring matching.
    info = conninfo_to_dict(dsn())
    host = (info.get("host") or "").lower()
    db = (info.get("dbname") or "").lower()
    if host.endswith(".supabase.co") or "fxoyniqnrlkxfligbxmg" in f"{host} {db}":
        raise CaptureError("acquisition refuses a prod-looking target")
    if db not in ("learning_dev", "learning_test"):
        raise CaptureError(f"acquisition dbname must be learning_dev/learning_test, got {db!r}")
    if host and host not in ("127.0.0.1", "localhost"):
        raise CaptureError(f"acquisition host must be local, got {host!r}")


def record_acquired_event(*, user_id, event_type, acquisition_run_id, source_surface, observed_by,
                          evidence_ref, data_fidelity, study_content_id=None, neta_section=None,
                          score_percent=None, confidence=None):
    _guard_target()
    env = {"acquisition_run_id": acquisition_run_id, "source_surface": source_surface,
           "observed_by": observed_by, "evidence_ref": evidence_ref, "data_fidelity": data_fidelity}
    for k in _ENVELOPE:
        if not isinstance(env[k], str) or not env[k].strip():
            raise CaptureError(f"acquisition envelope key {k!r} is required and must be non-empty")
    if source_surface not in SOURCE_SURFACES:
        raise CaptureError(f"source_surface {source_surface!r} not in {sorted(SOURCE_SURFACES)}")
    if data_fidelity not in DATA_FIDELITIES:
        raise CaptureError(f"data_fidelity {data_fidelity!r} not in {sorted(DATA_FIDELITIES)}")
    if study_content_id is None:
        raise CaptureError("acquisition events must be content-bound (study_content_id required) so "
                           "the evidence is projection-visible")
    if event_type == "assessment_completed" and score_percent is None:
        raise CaptureError("assessment_completed requires score_percent")
    if event_type == "self_assessment" and confidence is None:
        raise CaptureError("self_assessment requires confidence")
    payload = dict(env)
    if score_percent is not None:
        payload["score_percent"] = score_percent
    if confidence is not None:
        payload["confidence"] = confidence
    # record_event enforces the event_type vocab, user/content existence, and score/confidence
    # ranges, and never passes occurred_at (server now() only -> no backdating). The fixed-kwarg
    # envelope means a typoed key is a TypeError, not a silently-accepted payload field.
    return record_event(user_id, event_type, study_content_id=study_content_id,
                        neta_section=neta_section, payload=payload)
```
Also export from `packages/learning-capture/src/learning_capture/__init__.py` if it re-exports the
public surface (append `record_acquired_event` alongside existing exports; check the file first —
if it has no `__all__`/re-exports, skip).

- [ ] **Step 4: Run to verify pass.** `uv run pytest tests/test_acquisition.py -v` → all PASS.
- [ ] **Step 5: Commit.**
```bash
git add packages/learning-capture/src/learning_capture/acquisition.py packages/learning-capture/tests/test_acquisition.py
git commit -m "feat(learning-capture): guarded acquisition helper with provenance envelope (Slice 2d)"
```

---

## Task 2: CLI `acquire` subcommand

**Files:**
- Modify: `packages/learning-capture/src/learning_capture/cli.py`
- Test: `packages/learning-capture/tests/test_cli.py` (extend)

**Interfaces:** Consumes `record_acquired_event` (Task 1). Produces a `learning-capture acquire` subcommand.

- [ ] **Step 1: Write the failing test** (append to `test_cli.py`):
```python
def test_acquire_subcommand_records_with_envelope(capsys):
    from learning_capture.cli import main
    rc = main(["acquire", "--user", "00000000-0000-0000-0000-000000000001",
               "--type", "resource_completed", "--content", "00000000-0000-0000-0000-000000000010",
               "--section", "7.1", "--run-id", "run-CLI", "--observed-by", "JS",
               "--evidence-ref", "notes#L9", "--fidelity", "rehearsal"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "event_id" in out
```

- [ ] **Step 2: Run to verify it fails.** `uv run pytest tests/test_cli.py::test_acquire_subcommand_records_with_envelope -v` → FAIL (`invalid choice: 'acquire'`).

- [ ] **Step 3: Add the subcommand.** In `cli.py`, import `record_acquired_event` and add a parser +
dispatch:
```python
from .acquisition import record_acquired_event  # add to imports

    acq = sub.add_parser("acquire", help="append a learning event with a provenance envelope (Slice 2d)")
    acq.add_argument("--user", required=True)
    acq.add_argument("--type", required=True, dest="event_type")
    acq.add_argument("--content", default=None, dest="study_content_id")
    acq.add_argument("--section", default=None, dest="neta_section")
    acq.add_argument("--run-id", required=True, dest="acquisition_run_id")
    acq.add_argument("--source-surface", default="cli", dest="source_surface")
    acq.add_argument("--observed-by", required=True, dest="observed_by")
    acq.add_argument("--evidence-ref", required=True, dest="evidence_ref")
    acq.add_argument("--fidelity", required=True, dest="data_fidelity")
    acq.add_argument("--score", type=float, default=None, dest="score_percent")
    acq.add_argument("--confidence", type=int, default=None, dest="confidence")
```
And in the dispatch block (after the existing `record`/`list` handlers):
```python
    if args.cmd == "acquire":
        ev = record_acquired_event(
            user_id=args.user, event_type=args.event_type, study_content_id=args.study_content_id,
            neta_section=args.neta_section, acquisition_run_id=args.acquisition_run_id,
            source_surface=args.source_surface, observed_by=args.observed_by,
            evidence_ref=args.evidence_ref, data_fidelity=args.data_fidelity,
            score_percent=args.score_percent, confidence=args.confidence)
        print(json.dumps({"event_id": ev.event_id, "event_type": ev.event_type}, ensure_ascii=False))
        return 0
```

- [ ] **Step 4: Run to verify pass.** `uv run pytest tests/test_cli.py -v` → all PASS.
- [ ] **Step 5: Commit.**
```bash
git add packages/learning-capture/src/learning_capture/cli.py packages/learning-capture/tests/test_cli.py
git commit -m "feat(learning-capture): CLI acquire subcommand for guarded capture (Slice 2d)"
```

---

## Task 3: Cohort provisioning + non-destructive reversal scripts

**Files:**
- Create: `scripts/learning/slice2d_provision_cohort.sql`
- Create: `scripts/learning/slice2d_retire_cohort.sql`
- Test: `packages/learning-capture/tests/test_provision_cohort.py`

The rehearsal cohort user uses a fixed synthetic uuid `a0000000-2d00-4000-8000-000000000001`.

- [ ] **Step 1: Write the failing test.**
```python
# packages/learning-capture/tests/test_provision_cohort.py
import pathlib
import psycopg
import pytest
from learning_capture.db import dsn

REPO = pathlib.Path(__file__).resolve().parents[3]
PROVISION = REPO / "scripts" / "learning" / "slice2d_provision_cohort.sql"
RETIRE = REPO / "scripts" / "learning" / "slice2d_retire_cohort.sql"
COHORT = "a0000000-2d00-4000-8000-000000000001"


def _run(sql_path):
    with psycopg.connect(dsn(), autocommit=True) as c:  # dsn() -> learning_test under conftest
        c.execute(sql_path.read_text(encoding="utf-8"))


def _row():
    with psycopg.connect(dsn(), autocommit=True) as c:
        return c.execute(
            "select target_certification_level::text, employee_id, is_active, "
            "study_preferences->>'data_fidelity' from user_profiles where id=%s", (COHORT,)).fetchone()


def test_provision_is_idempotent_and_shapes_the_cohort_row():
    _run(PROVISION)
    _run(PROVISION)  # second apply must not error or duplicate
    level, employee_id, is_active, fidelity = _row()
    assert level == "III"
    assert employee_id is None          # deferred per spec
    assert is_active is True
    assert fidelity == "rehearsal"


def test_retire_deactivates_without_deleting():
    _run(PROVISION)
    _run(RETIRE)
    level, employee_id, is_active, fidelity = _row()  # row STILL EXISTS
    assert is_active is False
```
Note: this test needs `user_profiles` to carry `role`/`employee_id`/`study_preferences`. The
`learning-capture` conftest builds them via `001` (adds `employee_id`); `role`/`study_preferences`
are added by the provisioning script's own `do $$ ... alter table ... $$` preflight (Step 3) so the
script is self-sufficient on the minimal capture fixture.

- [ ] **Step 2: Run to verify it fails.** `uv run pytest tests/test_provision_cohort.py -v` → FAIL
(file not found / missing columns).

- [ ] **Step 3: Write the scripts.**
`scripts/learning/slice2d_provision_cohort.sql`:
```sql
-- Slice 2d rehearsal cohort provisioning. Idempotent. Synthetic handles only -- NO PII.
-- Reversal is NON-DESTRUCTIVE (see slice2d_retire_cohort.sql): set is_active=false, NEVER delete
-- (a delete cascades into the append-only learning_events ledger and trips its immutability trigger).
-- Preflight is SELF-SUFFICIENT + idempotent: it creates the certification_level enum and every column
-- this script writes IF MISSING. This is a full no-op on learning_dev (all objects already exist) and
-- bootstraps the minimal learning_test capture fixture (which has only id/email/employee_id).
-- DB-IDENTITY GUARD: refuse to run anywhere but learning_dev/learning_test -- a copied command
-- cannot write outside the lane even if pointed at the wrong connection.
do $$ begin
  if current_database() not in ('learning_dev','learning_test') then
    raise exception 'Slice 2d provisioning refuses to run on %; expected learning_dev/learning_test', current_database();
  end if;
end $$;
do $$ begin
  if not exists (select 1 from pg_type where typname = 'certification_level') then
    create type certification_level as enum ('I','II','III','IV');
  end if;
end $$;
alter table public.user_profiles add column if not exists full_name text;
alter table public.user_profiles add column if not exists role text default 'technician';
alter table public.user_profiles add column if not exists target_certification_level  certification_level;
alter table public.user_profiles add column if not exists current_certification_level certification_level;
alter table public.user_profiles add column if not exists is_active boolean default true;
alter table public.user_profiles add column if not exists employee_id uuid;
alter table public.user_profiles add column if not exists study_preferences jsonb default '{}'::jsonb;

insert into public.user_profiles
  (id, email, full_name, role, target_certification_level, current_certification_level,
   is_active, employee_id, study_preferences)
values
  ('a0000000-2d00-4000-8000-000000000001', 'rehearsal-01@learning.invalid', 'Rehearsal Tech 01',
   'technician', 'III', null, true, null,
   '{"data_fidelity":"rehearsal","acquisition_run_id":"slice2d-rehearsal-01"}'::jsonb)
on conflict (id) do nothing;
```
`scripts/learning/slice2d_retire_cohort.sql`:
```sql
-- Slice 2d NON-DESTRUCTIVE reversal: deactivate the rehearsal cohort. NEVER delete (FK cascade into
-- the immutable learning_events ledger trips the append-only trigger -- evidence is immutable).
do $$ begin
  if current_database() not in ('learning_dev','learning_test') then
    raise exception 'Slice 2d retire refuses to run on %; expected learning_dev/learning_test', current_database();
  end if;
end $$;
update public.user_profiles set is_active = false
where id = 'a0000000-2d00-4000-8000-000000000001';
```

- [ ] **Step 4: Run to verify pass.** `uv run pytest tests/test_provision_cohort.py -v` → PASS.
- [ ] **Step 5: Commit.**
```bash
git add scripts/learning/slice2d_provision_cohort.sql scripts/learning/slice2d_retire_cohort.sql packages/learning-capture/tests/test_provision_cohort.py
git commit -m "feat(learning): Slice 2d cohort provisioning + non-destructive reversal scripts"
```

---

## Task 4: Cross-package e2e manifest test (the deterministic proof)

**Files:**
- Create: `packages/learning-projections/tests/acquisition_prereq.sql`
- Create: `packages/learning-projections/tests/test_acquisition_run.py`
- Modify: `packages/learning-projections/pyproject.toml` (add `learning-capture` test dep)

**Interfaces:** Consumes `learning_capture.acquisition.record_acquired_event` (Task 1) and the four
`learning_projections` functions (`content_progress`, `assessment_summary`, `competency_rollup`,
`cohort_aggregate`). Reuses the 2b projections fixture (`projections_prereq.sql`): content
`22222222-…-0001` links concept-1 (II `SA1,SA2`) + concept-2 (III `SB1,SB2`); III total KSAs = 3.

The projections `conftest._fixture` (session-autouse) already applies `projections_prereq.sql` +
`002` + the 12-event seed; it pins nothing — the runner sets `LEARNING_DEV_DSN` → `learning_test`.
This test provisions a FRESH cohort user (uuid `a0000000-…-0001`, isolated from seed users 1–9) so
per-user assertions are clean; cohort assertions use before/after deltas.

- [ ] **Step 1: Add the test dependency.** In `packages/learning-projections/pyproject.toml`:
```toml
[project.optional-dependencies]
test = ["pytest>=8.0.0", "learning-capture"]

[tool.uv.sources]
learning-capture = { path = "../learning-capture", editable = true }
```

- [ ] **Step 2: Write the fixture extension** `packages/learning-projections/tests/acquisition_prereq.sql`:
```sql
-- Slice 2d fixture extension over the 2b mini-graph: bring user_profiles to learning_dev parity
-- (role / employee_id / study_preferences) and add the negative-control subjects. learning_test only.
alter table public.user_profiles add column if not exists role text default 'technician';
alter table public.user_profiles add column if not exists employee_id uuid;
alter table public.user_profiles add column if not exists study_preferences jsonb default '{}'::jsonb;

-- Negative controls: a leveled user with NO content-linked evidence, and a Level-I user (0 KSAs).
insert into public.user_profiles (id, email, target_certification_level, is_active) values
  ('a0000000-2d00-4000-8000-000000000002','neg-noevidence@learning.invalid','III', true),
  ('a0000000-2d00-4000-8000-000000000003','neg-leveli@learning.invalid','I', true)
on conflict (id) do nothing;
```

- [ ] **Step 3: Write the failing e2e test** `packages/learning-projections/tests/test_acquisition_run.py`:
```python
import pathlib
import psycopg
import pytest
from learning_projections.db import dsn as _dsn
from learning_projections import (content_progress, assessment_summary, competency_rollup,
                                   cohort_aggregate)
from learning_capture.acquisition import record_acquired_event

HERE = pathlib.Path(__file__).parent
REPO = HERE.parents[2]
MIG = REPO / "infra" / "database" / "migrations" / "learning"
PREREQ = HERE / "projections_prereq.sql"
MIG_002 = MIG / "002_learning_events.sql"
EVENTS = HERE / "projections_events_seed.sql"
ACQ_PREREQ = HERE / "acquisition_prereq.sql"
PROVISION = REPO / "scripts" / "learning" / "slice2d_provision_cohort.sql"

COHORT = "a0000000-2d00-4000-8000-000000000001"
NEG_NOEV = "a0000000-2d00-4000-8000-000000000002"
NEG_LVL1 = "a0000000-2d00-4000-8000-000000000003"
C1 = "22222222-0000-0000-0000-000000000001"   # concept-1 (II SA1,SA2) + concept-2 (III SB1,SB2)
C2 = "22222222-0000-0000-0000-000000000002"   # concept-3 -> orphan only (progress, not competency)
ENV = dict(acquisition_run_id="slice2d-rehearsal-01", source_surface="cli",
           observed_by="JS", evidence_ref="runbook#run01", data_fidelity="rehearsal")


def _apply(*paths):
    with psycopg.connect(_dsn(), autocommit=True) as c:
        for p in paths:
            c.execute(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module", autouse=True)
def _acq(_fixture):
    # ISOLATED rebuild WITHOUT the 12-event seed so cohort numbers are absolute + exactly pinnable.
    # Active users after this = 4 seed (user9 is inactive) + 2 negative-control + 1 cohort = 7.
    _apply(PREREQ, MIG_002, ACQ_PREREQ, PROVISION)
    yield
    # restore the standard seeded state for the other projection test modules in this session.
    _apply(PREREQ, MIG_002, EVENTS)


def _scalar(sql, *args):
    with psycopg.connect(_dsn(), autocommit=True) as c:
        return c.execute(sql, args).fetchone()


def test_rehearsal_run_moves_all_four_read_models_to_manifest():
    # replay the rehearsal sequence through the guarded helper (all events content-bound)
    record_acquired_event(user_id=COHORT, event_type="resource_viewed", study_content_id=C2,
                          neta_section="7.2", **ENV)                        # in_progress on C2
    record_acquired_event(user_id=COHORT, event_type="resource_viewed", study_content_id=C1,
                          neta_section="7.1", **ENV)
    record_acquired_event(user_id=COHORT, event_type="resource_completed", study_content_id=C1,
                          neta_section="7.1", **ENV)                        # completed + competency
    record_acquired_event(user_id=COHORT, event_type="assessment_completed", study_content_id=C1,
                          neta_section="7.1", score_percent=88, **ENV)

    # --- content_progress: C1 completed (view_count 1), C2 in_progress ---
    progress = {p.study_content_id: p for p in content_progress(COHORT)}
    assert progress[C1].status == "completed" and progress[C1].is_completed is True
    assert progress[C1].view_count == 1
    assert progress[C2].status == "in_progress" and progress[C2].is_completed is False

    # --- assessment_summary: latest 88 on C1, one attempt ---
    asmt = {a.study_content_id: a for a in assessment_summary(COHORT)}
    assert asmt[C1].latest_score_percent == 88.0 and asmt[C1].assessment_attempts == 1

    # --- competency_rollup: III, total 3, covered 2, pct 66.7, evidence 2 ---
    comp = competency_rollup(COHORT)
    assert comp.resolved_level == "III" and comp.level_source == "target"
    iii = [lc for lc in comp.coverage if lc.level == "III"][0]
    assert iii.total_ksas_at_level == 3
    assert iii.covered_ksas == 2
    assert iii.coverage_percent == 66.7
    assert comp.evidence_event_count == 2   # resource_completed + assessment_completed on C1

    # --- independent KSA-code manifest (the engine exposes only a count, not the set) ---
    codes = _scalar(
        """select array_agg(distinct k.ksa_code order by k.ksa_code)
           from learning_events le
           join content_concept_links ccl on ccl.content_id = le.study_content_id
           join edition_ksa_map ekm on ekm.concept_id = ccl.concept_id and ekm.is_active
           join ksas k on k.ksa_code = ekm.ksa_code and k.certification_level::text = ekm.level
           where le.user_id = %s and le.event_type in ('resource_completed','assessment_completed')
             and le.study_content_id is not null and k.certification_level::text = 'III'""", COHORT)[0]
    assert codes == ["SB1", "SB2"]

    # --- cohort_aggregate(III): exact absolute manifest over the 7 active users ---
    cohort = cohort_aggregate(level="III")
    assert cohort.user_count == 7
    assert cohort.mean_completed_content == 0.1      # 1 completed content / 7 users
    assert cohort.scored_user_count == 1
    assert cohort.mean_latest_score == 88.0
    assert cohort.coverage_user_count == 7           # every active user has non-null III coverage
    assert cohort.mean_coverage_percent == 9.5       # (66.7 + 0.0*6) / 7

    # --- provenance envelope present on EVERY run event; occurred_at ~ created_at (no backdating) ---
    with psycopg.connect(_dsn(), autocommit=True) as c:
        rows = c.execute(
            "select payload, extract(epoch from (occurred_at - created_at)) "
            "from learning_events where user_id=%s", (COHORT,)).fetchall()
    assert len(rows) == 4
    for payload, drift in rows:
        assert all(payload.get(k) for k in ("acquisition_run_id", "source_surface", "observed_by",
                                            "evidence_ref", "data_fidelity"))
        assert payload["acquisition_run_id"] == "slice2d-rehearsal-01"
        assert abs(drift) < 2            # server now() for both timestamps -> no client backdating


def test_negative_controls():
    neg = competency_rollup(NEG_NOEV)         # leveled, no content-linked evidence -> 0 / 0.0
    iii = [lc for lc in neg.coverage if lc.level == "III"][0]
    assert iii.covered_ksas == 0 and iii.coverage_percent == 0.0
    lvl1 = competency_rollup(NEG_LVL1)        # Level I -> 0 KSAs -> null coverage
    i = [lc for lc in lvl1.coverage if lc.level == "I"][0]
    assert i.total_ksas_at_level == 0 and i.coverage_percent is None
```

- [ ] **Step 4: Run to verify it fails, then passes.** With `LEARNING_DEV_DSN` → `learning_test`:
`uv run --extra test pytest tests/test_acquisition_run.py -v`
First run FAILS (no `acquisition_prereq.sql` / dep). After Steps 1–3 land, re-run → all PASS. If the
projections suite is normally driven by a different runner, use that runner; the only requirement is
`learning-capture` importable + `LEARNING_DEV_DSN` pointed at `learning_test`. Confirm the full
projections suite still passes: `uv run --extra test pytest -v`.

- [ ] **Step 5: Commit.**
```bash
git add packages/learning-projections/tests/acquisition_prereq.sql packages/learning-projections/tests/test_acquisition_run.py packages/learning-projections/pyproject.toml
git commit -m "test(learning-projections): Slice 2d e2e acquisition manifest proof + negative controls"
```

---

## Task 5: Runbook, evidence-packet template, redaction guard

**Files:**
- Create: `docs/learning/slice2d/runbook.md`
- Create: `docs/learning/slice2d/evidence_packet.template.md`
- Create: `scripts/learning/redaction_check.sh`
- Test: `packages/learning-capture/tests/test_redaction_check.py`

- [ ] **Step 1: Write the redaction-guard failing test.**
```python
# packages/learning-capture/tests/test_redaction_check.py
import pathlib, subprocess
REPO = pathlib.Path(__file__).resolve().parents[3]
GUARD = REPO / "scripts" / "learning" / "redaction_check.sh"


def _check(text, tmp_path):
    f = tmp_path / "packet.md"; f.write_text(text, encoding="utf-8")
    return subprocess.run(["bash", str(GUARD), str(f)], capture_output=True, text=True)


def test_rejects_email_and_passes_clean(tmp_path):
    assert _check("observed_by: jane.doe@apexpowerops.com", tmp_path).returncode != 0
    assert _check("observed_by: JS  evidence_ref: runbook#run01", tmp_path).returncode == 0


def test_operator_denylist_file_rejects_named_terms(tmp_path, monkeypatch):
    deny = tmp_path / "deny.txt"; deny.write_text("Jane Doe\n", encoding="utf-8")
    monkeypatch.setenv("REDACTION_DENYLIST", str(deny))
    assert _check("the rehearsal subject was Jane Doe", tmp_path).returncode != 0
```

- [ ] **Step 2: Run to verify it fails.** `uv run pytest tests/test_redaction_check.py -v` → FAIL (no script).

- [ ] **Step 3: Write the guard** `scripts/learning/redaction_check.sh`:
```bash
#!/usr/bin/env bash
# Mechanical pre-commit redaction guard for Slice 2d committable artifacts. Rejects (1) email-shaped
# PII and (2) any literal term in an OPERATOR-HELD denylist file at $REDACTION_DENYLIST (kept OUT of
# git -- e.g. the real cohort names under .claude/PLATFORM/). The denylist is optional; without it,
# only the email check runs. Usage: [REDACTION_DENYLIST=path] redaction_check.sh FILE...
set -euo pipefail
status=0
for f in "$@"; do
  if grep -InE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "$f" | grep -viE '@learning\.invalid'; then
    echo "REDACTION FAIL: email-like PII in $f" >&2
    status=1
  fi
  if [ -n "${REDACTION_DENYLIST:-}" ] && [ -s "${REDACTION_DENYLIST:-}" ]; then
    if grep -Inf "$REDACTION_DENYLIST" "$f"; then
      echo "REDACTION FAIL: denylisted term in $f" >&2
      status=1
    fi
  fi
done
exit $status
```
(The synthetic `@learning.invalid` handles are allowed; real domains are rejected. The name denylist
stays operator-held so no real name is committed to enforce redaction.)

- [ ] **Step 4: Run to verify pass.** `uv run pytest tests/test_redaction_check.py -v` → PASS.

- [ ] **Step 5: Write the runbook** `docs/learning/slice2d/runbook.md` — the operator protocol for the
gated live run (Task 6). It MUST contain, as prose + exact commands:
  - The `data_write` gate notice (operator approval before any `learning_dev` write).
  - Provision: `psql … learning_dev -f scripts/learning/slice2d_provision_cohort.sql` (sourcing
    `infra/.env` for `DEV_PG_PASSWORD`; the helper/CLI read `LEARNING_DEV_DSN` or the default).
  - The event sequence as `learning-capture acquire …` commands (the real person engages SCADA content
    `9c47a9ed-c46b-4d1d-a604-7c68647c913c`; observer records each with `--run-id slice2d-rehearsal-01
    --observed-by <initials> --evidence-ref <pointer> --fidelity rehearsal`; `--score` from the real
    graded instrument).
  - The genuine-engagement evidence requirement: each event's `evidence_ref` points to an
    operator-held note (kept in `.claude/PLATFORM/`, never git) recording who/what/when/channel + an
    observer attestation; an event with no retrievable evidence is excluded.
  - Verification: the four GET routes (`/progress`,`/assessments`,`/competency`,`/cohort`) captured
    before/after; the independent SQL manifest for the exact KSA set; the `occurred_at ≈ created_at`
    backdating check.
  - Reversal note: retire via `slice2d_retire_cohort.sql` (never delete).
  - Run `scripts/learning/redaction_check.sh` over the packet before committing.

- [ ] **Step 6: Write the evidence-packet template** `docs/learning/slice2d/evidence_packet.template.md`
with: a header line stating `data_fidelity: rehearsal` and the breadth-not-mastery annotation
(`coverage_percent = content→KSA mapping breadth, NOT demonstrated competence`); slots for before/after
JSON of each of the four read models; the manifest assertion table (expected vs observed, incl. the
exact `ksa_code` set from the SQL manifest); a per-fidelity breakdown; the negative-control result.

- [ ] **Step 7: Commit.**
```bash
git add docs/learning/slice2d/runbook.md docs/learning/slice2d/evidence_packet.template.md scripts/learning/redaction_check.sh packages/learning-capture/tests/test_redaction_check.py
git commit -m "docs(learning): Slice 2d runbook, evidence-packet template, redaction guard"
```

---

## Task 6: GATED live rehearsal run (operator-executed — NOT a subagent task)

> **Subagent-driven-development STOPS before this task.** It writes business data into `learning_dev`
> and involves a real human, so it runs under the operator `data_write` gate, in a working session
> (not a dispatched subagent). The controller presents readiness; the operator approves and supplies
> the real rehearsal subject out-of-band.

- [ ] **Step 1:** Operator approves the `data_write` gate.
- [ ] **Step 2:** Provision the cohort against `learning_dev` (provisioning script).
- [ ] **Step 3:** Run the rehearsal: the real person genuinely engages the SCADA content; the observer
  records the event sequence via `learning-capture acquire` with the full envelope + `evidence_ref`
  pointing to operator-held notes.
- [ ] **Step 4:** Capture before/after of the four GET routes + the independent SQL manifest +
  the backdating check; assert each matches the live SCADA manifest (competency III `covered_ksas=2`,
  `coverage_percent=round(100*2/169,1)=1.2`, the exact set `{KSA-III-SC-002, KSA-III-SC-003}` via SQL).
- [ ] **Step 5:** Fill the redacted evidence packet (`docs/learning/slice2d/evidence_packet.md`); run
  `redaction_check.sh`; commit the packet. Store the real person↔handle map + observation notes in
  private `.claude/PLATFORM/` (never git).
- [ ] **Step 6:** Use superpowers:finishing-a-development-branch to land the branch via the operator
  merge gate (PR, like Slices 1/2a/2b).
