# Learning Slice 2a — Capture Path — Design

**Date:** 2026-06-20
**Lane:** `learning/slice2-capture` (host worktree `apex-learning-lane`, off `main` `82c3b97b`)
**Status:** Approved (brainstorm) — pending spec review → writing-plans
**Predecessor:** Slice 1 (contextual resource resolver) — MERGED to main (PR #22 → `82c3b97b`)

---

## 1. Goal

Deliver the **capture path**: the mechanism that lets a real technician record the first real
learning event, end-to-end. This is the **data-acquisition unblocker** for the flagship learning
lane — until a tech can record "I engaged with this resource" or "I completed this assessment,"
no real learning data ever exists, and management visibility + ROI correlation stay theoretical
forever. Capture is also the only Slice-2 subsystem that is fully testable *now* (real writes,
real invariants) rather than being analytics on an empty table.

The flagship value thesis (operator): put the right resource at a tech's disposal at the point of
work (Slice 1, done), then **track engagement and measure competency gain** so the ramp can be
sold as capacity. Slice 2a builds the capture substrate that the measurement layers derive from.

## 2. Scope & boundaries

**In Slice 2a:**
- A new additive migration lane for `learning_dev` (none existed — the baseline was loaded from a
  frozen dump).
- A bridge column tying the learner identity to the workforce/person spine.
- An **append-only `learning_events` log** — the immutable capture substrate.
- A write package (`learning-capture`), a write API route, and a capture panel on the Slice 1 demo.

**Explicitly deferred** (later sub-slices — so we never build analytics on emptiness):
- **2b** — projections (`user_study_progress` / `user_test_attempts` derived from events) +
  management visibility / dashboards.
- **2c** — ROI correlation (learning → records/ops field output).
- Production hardening of the write path (auth, real session-derived tech identity). The dev
  surface is unauthenticated, exactly like the Slice 1 read demo.

**Boundaries (hard):**
- **All writes target `learning_dev` only.** No prod writes; no prod-governance gate either way.
- The prod `public.user_profiles.employee_id` bridge already exists (PR #21 / migration
  `additive_person_spine_prod`); this slice mirrors that *column* into the frozen dev baseline.
- **Honest caveat:** this delivers the *pipe*. Provisioning real techs (`user_profiles` rows with
  `employee_id`) and capturing real evidence is a separate operator-driven operational step — the
  slice makes it possible, it does not fabricate data.

## 3. Architecture

A vertical mirroring Slice 1 (`resolve` → API → demo), but the *write* direction:

```
demo capture panel (operations-web)
        |  POST /api/v1/learning/events
        v
control-plane-api  services/learning/  (extends the Slice 1 module)
        |  learning_capture.record_event(...)
        v
packages/learning-capture  (read-WRITE connect to learning_dev)
        |  INSERT
        v
learning_dev  public.learning_events   (append-only)
```

Read-back closes the loop: `GET /api/v1/learning/events?user_id=` → the panel re-renders the
captured-events list after each write.

### Integration contract (unchanged from Slice 1)
The **NETA section** remains the cross-lane join key. A capture event carries an optional
`neta_section` (the same `records.neta_procedures.section` / `study_content.neta_section_primary`
contract Slice 1 resolves on), so engagement is recorded *in work-context* — the link that makes
later learning→field ROI possible without a records↔learning class crosswalk.

### Person-spine bridge
`user_profiles` is learning's own learner identity. Slice 2a adds a nullable `employee_id` —
the **cross-DB contract-FK** to prod `public.employees.id`. It is app-enforced with **no DB FK**
(employees lives in a different database; same pattern as `records.persons.employee_ref` /
`ops.persons.employee_ref`). Every learner can thus be traced to a real tech — the attribution
ROI needs later — without coupling the two databases.

## 4. Data model — two additive migrations (new `learning` lane)

New directory `infra/database/migrations/learning/` following the records/ops pattern
(`NNN_name.sql` + `NNN_name_down.sql` + `test_NNN_name.py` + `MANIFEST.md`). Tests run against a
**throwaway `learning_test`** DB (down→up→down), never `learning_dev`.

> Schema note: the learning baseline lives in the **`public`** schema within its own
> `learning_dev` database (lane isolation is the database, per separate-DB-per-lane D-ARCH-1), so
> the new objects also live in `public`. The migration *directory* is named for the `learning`
> lane.

### `001_person_bridge.sql`
```sql
alter table public.user_profiles
  add column if not exists employee_id uuid null;          -- cross-DB contract-FK -> prod public.employees.id (NOT a DB FK)
create unique index if not exists uq_user_profiles_employee_id
  on public.user_profiles (employee_id) where employee_id is not null;  -- partial unique (mirrors prod UNIQUE)
comment on column public.user_profiles.employee_id is
  'Cross-DB contract-FK to prod public.employees.id; app-enforced, no DB FK (employees is a separate database).';
```
Down: drop the index, drop the column.

### `002_learning_events.sql`
```sql
create table if not exists public.learning_events (
  event_id         uuid        primary key default gen_random_uuid(),
  user_id          uuid        not null references public.user_profiles(id) on delete cascade,
  event_type       text        not null,
  study_content_id uuid        null references public.study_content(id) on delete set null,
  neta_section     text        null,                       -- Slice 1 work-context contract
  occurred_at      timestamptz not null default now(),
  payload          jsonb       not null default '{}'::jsonb,
  created_at       timestamptz not null default now(),
  constraint learning_events_event_type_check check (event_type in
    ('resource_viewed','resource_completed','assessment_completed','self_assessment'))
);
create index if not exists ix_learning_events_user_time on public.learning_events (user_id, occurred_at);
create index if not exists ix_learning_events_section   on public.learning_events (neta_section);
create index if not exists ix_learning_events_type      on public.learning_events (event_type);

-- append-only guard: the ledger is immutable
create or replace function public.learning_events_block_mutation() returns trigger
  language plpgsql as $$
begin
  raise exception 'learning_events is append-only (% blocked)', tg_op;
end;
$$;
create trigger trg_learning_events_append_only
  before update or delete on public.learning_events
  for each row execute function public.learning_events_block_mutation();
```
Down: drop the trigger, the function, then the table (CASCADE-free, explicit order).

**Event-type vocab (text CHECK, not an enum — extensible, matches the records-lane preference):**
- `resource_viewed` — opened a surfaced resource
- `resource_completed` — finished it
- `assessment_completed` — completed a quiz/self-test (payload: `score_percent`, `total_questions`,
  `correct_answers`, `duration_seconds`)
- `self_assessment` — tech self-rates confidence on a section/content (payload: `confidence`)

`payload` is the open extension point (source surface, `apparatus_type`, etc.) so new fields never
need a migration. Validation of payload *shape per event_type* is the package's job, not the DB's.

## 5. Components

### 5.1 `packages/learning-capture/` (Python — mirrors `learning-resolver`)
```
src/learning_capture/
  __init__.py
  db.py        # read-WRITE connect to learning_dev; env LEARNING_DEV_DSN / LEARNING_DEV_PGPASSWORD
  models.py    # CapturedEvent dataclass (mirrors the row); EVENT_TYPES frozenset
  capture.py   # record_event(...) + list_events(...)
  cli.py       # `learning-capture record ...` / `learning-capture list ...`
tests/
```
Core interfaces:
```python
def record_event(
    user_id: str,
    event_type: str,
    *,
    study_content_id: str | None = None,
    neta_section: str | None = None,
    payload: dict | None = None,
) -> CapturedEvent: ...
def list_events(user_id: str | None = None, limit: int = 50) -> list[CapturedEvent]: ...
```
- `db.py` reuses the resolver's env contract (`LEARNING_DEV_DSN` / `LEARNING_DEV_PGPASSWORD`, pinned
  host=127.0.0.1 dbname=learning_dev) but **without** the resolver's read-only session — capture
  writes.
- `record_event` validates `event_type ∈ EVENT_TYPES`, that `user_id` exists, and (if given) that
  `study_content_id` exists; raises a typed error otherwise. Returns the inserted row.
- The package issues **INSERT/SELECT only** — never UPDATE/DELETE (and the DB guard backs that).

### 5.2 `apps/control-plane-api/services/learning/` (extend the Slice 1 module)
- `POST /api/v1/learning/events` — body `{user_id, event_type, study_content_id?, neta_section?, payload?}`
  → `201 {event}`. Calls `learning_capture.record_event` (not `get_db`, exactly as the resolver
  route calls the package). Validation errors → `400`/`422`.
- `GET /api/v1/learning/events?user_id=&limit=` → `{events: [...]}` (read-back for the demo).
- Editable dependency wired via `requirements.txt` line `-e ../../packages/learning-capture`
  (mirroring how `learning-resolver` / `calc-engine` are wired — pip + requirements.txt, **not**
  uv; the repo commits no `uv.lock`).

### 5.3 `apps/operations-web/app/learning-demo/` (extend)
- Add a **capture panel** beside the Slice 1 resolver results: on a surfaced resource, "mark
  viewed / completed"; a small assessment + self-assessment form; a user picker (dev: choose a
  `user_profiles` row). Submit → `POST /events` → the captured-events list (from `GET /events`)
  refreshes.
- Reuses `browserEnv.controlPlaneBaseUrl` and the existing demo styling. This makes the
  **resolve → capture loop** one screen: Slice 1 surfaces the resource, Slice 2 records engagement
  with it, at the point of work.

## 6. Data flow

1. Tech (demo) picks a user + resource/section, clicks an event action.
2. `POST /api/v1/learning/events` → `record_event` validates → `INSERT public.learning_events`.
3. `201 {event}` → demo issues `GET /api/v1/learning/events?user_id=` → re-renders the list.

## 7. Testing strategy

- **Migration tests** (`learning_test`, throwaway, down→up→down):
  - `001`: `employee_id` exists, nullable, partial-unique, **no DB FK**; reversibility.
  - `002`: table shape; `event_type` CHECK accepts the 4 values and rejects others; the three
    indexes exist; **append-only guard raises on UPDATE and on DELETE**; FK behaviors
    (`user_id` CASCADE, `study_content_id` SET NULL); reversibility.
- **Package tests** (`learning_test`): `record_event` happy path per event_type; rejects unknown
  vocab / nonexistent user / nonexistent content; INSERT-only confirmed (the guard blocks any
  stray mutation); `list_events` ordering + `user_id` filter + `limit`.
- **API tests**: `201` shape, `4xx` on bad vocab / missing user, `GET` read-back shape + filter.
- **UI**: typecheck clean + one thin browser smoke of the resolve→capture loop.

## 8. Durable constraints carried from Slice 1

- New host worktrees lack gitignored files — `infra/.env` is symlinked in `apex-learning-lane`
  (already present); `pip install` / `pnpm install` per app as needed.
- **control-plane-api = pip + requirements.txt (NOT uv)**; deploys via `render.yaml`
  `pip install -r requirements.txt`; sibling packages wired `-e ../../packages/<x>`; **do not
  commit `uv.lock`** (a `uv run` byproduct — remove if it appears).
- Package tests need `uv` on PATH (`export PATH="$HOME/.local/bin:$PATH"`) and
  `LEARNING_DEV_PGPASSWORD` sourced; migration tests need a `learning_test` DB created first.
- Subagents edit host files via write-local-then-`ssh 'cat > dest' < local` (heredocs break on
  code quotes); ssh commit messages must avoid apostrophes (or `git commit -F`).

## 9. Deferred / open (recorded, not built here)

- **2b**: derive `user_study_progress` / `user_test_attempts` projections from the event log;
  management dashboards (cert-ladder position, coverage gaps, per-KSA progress).
- **2c**: ROI correlation joining `learning_events` → records field results / ops production via
  the `employee_id` bridge + NETA section.
- Real **data acquisition**: provision real techs and capture real evidence (operator-driven).
- Write-path auth / real tech identity from session (prod hardening).
