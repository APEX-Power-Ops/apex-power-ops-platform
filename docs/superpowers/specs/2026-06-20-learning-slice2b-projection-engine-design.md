# Learning Slice 2b — Projection Engine (design)

**Status:** approved design (brainstorm 2026-06-20); hardened against a 4-lens adversarial review. Lane `learning/slice2b-projections` (host worktree `apex-learning-lane`), off main `ddacc237`.

**Goal:** A read-only, compute-on-read projection layer that derives four management/learner read-models from the live append-only `learning_events` ledger, exposed as a Python package plus control-plane-api GET routes. No dashboard UI, no persisted projections, no writes, **no production migration**.

**Architecture:** `packages/learning-projections` (Python, mirrors `learning-resolver`) issues aggregation SQL against `learning_dev` and returns read-model dataclasses; control-plane-api adds four guarded GET routes that call it. The append-only ledger is the source of truth; every read-model is computed live from it joined to the frozen baseline graph — so there is no projection drift, replay, or sync logic.

**Tech stack:** Python 3.11+, `psycopg[binary]>=3.1`, FastAPI (control-plane-api), pytest. Dev DB `learning_dev` (host PG17 `apex-dev-pg`). Tests run on throwaway `learning_test`.

## Global Constraints

- **Read-only.** The package opens a read-only session (mirror `learning-resolver/db.py`: pinned `learning_dev` DSN + `default_transaction_read_only`/`SET TRANSACTION READ ONLY`). It MUST NOT write. Nothing in 2b writes to the baseline `user_study_progress`/`user_test_attempts` tables — those stay frozen/legacy. **This no-write guarantee is itself tested** (see Testing).
- **No new DB objects, no migration.** Compute-on-read only. (The mini-graph DDL exists ONLY in the test fixture for `learning_test`.)
- **DSN env:** `LEARNING_DEV_DSN` or `LEARNING_DEV_PGPASSWORD` (pinned, identical to resolver/capture).
- **Dependency wiring vs test harness (not a contradiction):** *runtime/deploy* dependency management is pip + `requirements.txt`, sibling editable `-e ../../packages/learning-projections`, no `uv.lock` committed. `uv` appears ONLY as the *local test runner* for the worktree-without-`.venv` case — it is never a runtime/deploy dependency.
- **Route guard:** the learning router already registers only when `LEARNING_DEV_DSN`/`LEARNING_DEV_PGPASSWORD` is set (prod-safe; Render has no learning DSN). New routes inherit that guard — no separate guard.
- **Naming discipline (load-bearing):** competency fields are `covered_ksas` / `coverage_percent` / `evidence_event_count` — **engagement coverage, never mastery.** The token `mastered`/`mastery` MUST NOT appear in any field name, response key, or doc string. Score-thresholded mastery is explicitly 2c.
- **Non-silent level resolution (load-bearing):** every competency response carries `resolved_level`, `level_source`, and `levels_in_scope` so an all-level fallback denominator can never be silently presented as level-specific coverage.
- **NETA section** remains the cross-lane work-context key; **`user_profiles.employee_id`** remains the (app-enforced) workforce bridge. 2b reads them; it neither adds nor enforces either.

## Verified schema ground truth (live `learning_dev`, 2026-06-20; re-confirmed by adversarial schema lens)

These are confirmed against the live DB; the derivations below depend on them.

- `learning_events(event_id, user_id, event_type, study_content_id, neta_section, occurred_at, payload jsonb, created_at)`. `event_type ∈ {resource_viewed, resource_completed, assessment_completed, self_assessment}`. `study_content_id` is **nullable** (section-only events allowed). `study_content_id → study_content.id`.
- **Payload key contract** (set by the Slice 2a capture validation): `assessment_completed` carries `payload.score_percent` (numeric 0–100); `self_assessment` carries `payload.confidence` (int 1–5). Access via `payload->>'score_percent'` / `payload->>'confidence'` (cast to numeric/int). `resource_viewed`/`resource_completed` carry no required payload key. Derivations treat a missing key defensively (excluded from that aggregate).
- `study_content(id uuid PK, title varchar, neta_section_primary varchar, certification_level, content_id varchar, …)`.
- `content_concept_links(content_id uuid → study_content.id, concept_id text → concepts.concept_id, …)`. **Key column is `content_id`, not `study_content_id`.** 14,961 rows, 0 orphans on the content side.
- `concepts(concept_id text PK, concept_description text, domain, …)`. **No `name` column — use `concept_id` + `concept_description`.**
- `edition_ksa_map(concept_id text, ksa_code text, level text, edition text, is_active bool, …)`. Editions = `{2022, 2026}`; levels = `{II, III, IV}`. 966 rows; **30 rows reference a `ksa_code` absent from `ksas`** (orphans — excluded by the inner join to `ksas`). **All 966 are `is_active=true` today, but the competency join filters `is_active` so a future inactive mapping never counts as coverage.** `ekm.level` agrees with `ksas.certification_level` for every joined row (0 disagreements).
- `ksas(id uuid, ksa_code varchar, certification_level certification_level enum, description, …)`. **`ksa_code` is globally unique** (`ksas_ksa_code_key`); each code belongs to exactly one `certification_level` (0 codes span multiple levels). Counts: **II=144, III=169, IV=170**.
- `certification_level` enum = `{I, II, III, IV}`. **Level I has zero KSAs** ⇒ its denominator is 0 ⇒ `coverage_percent` MUST be `null` (never 0/0).
- `user_profiles(id uuid, target_certification_level cert?, current_certification_level cert?, is_active bool, …)`. Both level columns are nullable.

## Component 1 — `packages/learning-projections`

Layout mirrors `learning-resolver`:

```
packages/learning-projections/
  pyproject.toml            # name=learning-projections; deps psycopg[binary]>=3.1; pytest extra
  src/learning_projections/
    __init__.py             # exports the 4 funcs + dataclasses + ProjectionError
    db.py                   # read-only learning_dev session (copied from resolver)
    models.py               # dataclasses (below)
    projections.py          # content_progress / assessment_summary / competency_rollup / cohort_aggregate
    cli.py                  # thin wrapper: subcommands progress|assessments|competency|cohort (no logic of its own)
  tests/
    __init__.py
    conftest.py             # applies projections_prereq.sql once/session (LEARNING_TEST_DSN)
    projections_prereq.sql  # full mini-graph DDL + deterministic seed (below)
    test_db_readonly.py     # the no-write guarantee
    test_content_progress.py
    test_assessment_summary.py
    test_competency_rollup.py
    test_cohort_aggregate.py
```

### Read-models (dataclasses, `models.py`)

```python
@dataclass
class ContentProgress:
    study_content_id: str
    title: str
    neta_section: str | None
    view_count: int
    is_completed: bool
    status: str                 # 'completed' | 'in_progress'
    first_seen_at: str          # ISO
    last_activity_at: str

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
    last_activity_at: str

@dataclass
class ConceptRef:
    concept_id: str
    concept_description: str | None

@dataclass
class LevelCoverage:
    level: str                  # 'I'|'II'|'III'|'IV'
    total_ksas_at_level: int
    covered_ksas: int
    coverage_percent: float | None   # null when total_ksas_at_level == 0

@dataclass
class CompetencyRollup:
    user_id: str
    resolved_level: str         # 'II'|'III'|'IV'|'I'|'all'
    level_source: str           # 'explicit'|'target'|'current'|'all'
    levels_in_scope: list[str]  # e.g. ['II'] or ['II','III','IV'] for all
    evidence_event_count: int   # resource_completed + assessment_completed events w/ content
    coverage: list[LevelCoverage]   # one entry per level in scope
    engaged_concepts: list[ConceptRef]   # NOT level-filtered coverage; see derivation

@dataclass
class CohortAggregate:
    level: str | None           # explicit filter, or null = each user's resolved level
    user_count: int             # active users
    mean_completed_content: float       # over ALL active users (no-completion = 0)
    mean_latest_score: float | None     # over scored users only
    scored_user_count: int
    mean_coverage_percent: float | None # per-user coverage averaged over non-null users
    coverage_user_count: int
```

### User-existence probe (all three user-scoped functions)

`content_progress`, `assessment_summary`, and `competency_rollup` first run `select 1 from user_profiles where id = %(user_id)s`. **If absent → raise `ProjectionError('user not found')` (the route maps it to 404).** Only if the user exists do they compute — so "unknown user" (404) is distinct from "user with no activity" (200 + empty/zeroed). Ordering is always: existence probe → 404 first, then the aggregation → 200 (possibly empty). `cohort_aggregate` takes no `user_id` and has no probe.

### Derivations (`projections.py`)

**`content_progress(user_id) -> list[ContentProgress]`** — per content with a `resource_viewed`/`resource_completed` event (study_content_id not null):

```sql
select sc.id, sc.title, sc.neta_section_primary,
       count(*) filter (where e.event_type='resource_viewed')      as view_count,
       bool_or(e.event_type='resource_completed')                  as is_completed,
       min(e.occurred_at) as first_seen_at, max(e.occurred_at) as last_activity_at
from learning_events e
join study_content sc on sc.id = e.study_content_id
where e.user_id = %(user_id)s
  and e.event_type in ('resource_viewed','resource_completed')
group by sc.id, sc.title, sc.neta_section_primary
order by max(e.occurred_at) desc;
```
`status = 'completed' if is_completed else 'in_progress'`.

**`assessment_summary(user_id) -> list[AssessmentSummary]`** — per content (study_content_id not null) from `assessment_completed` (objective `score_percent`) + `self_assessment` (subjective `confidence`). Section-only `self_assessment` events (null `study_content_id`) are **intentionally excluded** (per-content grain; a section-level confidence model is a documented future slice).

```sql
select sc.id, sc.title, sc.neta_section_primary,
  count(*) filter (where e.event_type='assessment_completed')                       as assessment_attempts,
  (array_agg((e.payload->>'score_percent')::numeric order by e.occurred_at desc)
     filter (where e.event_type='assessment_completed' and e.payload ? 'score_percent'))[1] as latest_score_percent,
  avg((e.payload->>'score_percent')::numeric)
     filter (where e.event_type='assessment_completed' and e.payload ? 'score_percent')      as mean_score_percent,
  count(*) filter (where e.event_type='self_assessment')                            as self_assessment_count,
  (array_agg((e.payload->>'confidence')::int order by e.occurred_at desc)
     filter (where e.event_type='self_assessment' and e.payload ? 'confidence'))[1] as latest_confidence,
  avg((e.payload->>'confidence')::numeric)
     filter (where e.event_type='self_assessment' and e.payload ? 'confidence')      as mean_confidence,
  max(e.occurred_at) as last_activity_at
from learning_events e
join study_content sc on sc.id = e.study_content_id
where e.user_id = %(user_id)s and e.event_type in ('assessment_completed','self_assessment')
group by sc.id, sc.title, sc.neta_section_primary
order by max(e.occurred_at) desc;
```
`latest_*` = most recent by `occurred_at`; means ignore rows whose payload lacks the key (the `? key` guard).

**`competency_rollup(user_id, level=None) -> CompetencyRollup`** — after the existence probe, resolve the level:
- `level` arg given (∈ {I,II,III,IV}) → `resolved_level=level`, `level_source='explicit'`, `levels_in_scope=[level]`.
- else `target_certification_level` not null → `'target'`, `[target]`.
- else `current_certification_level` not null → `'current'`, `[current]`.
- else (row present, both level cols null) → `resolved_level='all'`, `level_source='all'`, `levels_in_scope=['II','III','IV']` (the levels that have KSAs).

Evidence + covered (edition ignored → distinct `ksa_code` across editions; inner join to `ksas` drops the 30 orphan codes and supplies the authoritative level):

```sql
with evidence as (
  select distinct e.study_content_id as content_id
  from learning_events e
  where e.user_id=%(user_id)s
    and e.event_type in ('resource_completed','assessment_completed')
    and e.study_content_id is not null
),
covered as (
  select distinct k.ksa_code, k.certification_level
  from evidence ev
  join content_concept_links ccl on ccl.content_id = ev.content_id
  join edition_ksa_map ekm       on ekm.concept_id = ccl.concept_id and ekm.is_active
  join ksas k                    on k.ksa_code = ekm.ksa_code and k.certification_level::text = ekm.level
)
```
(`ekm.is_active` future-proofs against retired mappings; the explicit `level` predicate is safe — 0 live disagreements — and makes the level-pinning legible even though `ksa_code` is globally unique.)

Per level `L` in `levels_in_scope`:
- `total_ksas_at_level = (select count(distinct ksa_code) from ksas where certification_level=L)`
- `covered_ksas = (select count(distinct ksa_code) from covered where certification_level=L)`
- `coverage_percent = round(100.0*covered/total, 1) if total>0 else None` (e.g. Level I → 0 denominator → `None`).

`evidence_event_count` = count of the user's `resource_completed`+`assessment_completed` events with non-null `study_content_id`.

`engaged_concepts` — **named distinctly from "covered" on purpose** (it is broader than KSA coverage; never present it as level-scoped coverage in the field/UI). Concept-grain, defined independently of the KSA path: distinct `concepts.concept_id` + `concept_description` reachable from `evidence` via `content_concept_links` (joined to `concepts` for the description). It intentionally **includes orphan-only concepts** (a concept whose only `ksa_code` mappings are orphaned/inactive still appears here, even though it contributes 0 to `covered_ksas`), and is **deliberately NOT level-filtered and NOT gated on the `ksas` join**. It is the audit/debug "concepts the user has engaged evidence for" signal — explicitly distinct from the level-scoped `covered_ksas`/`coverage_percent`.

**`cohort_aggregate(level=None) -> CohortAggregate`** — over `user_profiles.is_active = true`. Compute per-user first, then aggregate:
- `user_count` = active users.
- `mean_completed_content` = mean over **all** active users of their distinct completed-content count; **users with no completions contribute 0**.
- `mean_latest_score` = mean over **only** users with ≥1 `assessment_completed` score, of that user's latest score; also return `scored_user_count`. `null` if `scored_user_count==0`.
- `mean_coverage_percent` = each user's `coverage_percent` (at `level` if given, else the user's resolved level) computed first, then averaged over users whose coverage is **non-null**; also return `coverage_user_count`. `null` if none. **`level='I'` is valid but degenerate**: every per-user coverage is `null` (0 denominator) → `mean_coverage_percent=null`, `coverage_user_count=0`.

Implementation note: at this scale (single-digit→low-hundreds users) cohort iterates active users and reuses the per-user computations, then aggregates in Python — simplest and provably matches "compute per-user first."

### CLI (`cli.py`)
A thin wrapper with subcommands `progress|assessments|competency|cohort` (`--user`, `--level`, `--json` as applicable) for ops/debugging, mirroring the resolver/capture CLIs. **No logic of its own** — each subcommand is a pure pass-through to the matching projection function.

## Component 2 — control-plane-api routes

Extend the existing learning service module (`apps/control-plane-api/services/learning/`), behind the existing `_learning_routes_enabled()` guard. Add `-e ../../packages/learning-projections` to `requirements.txt`.

| Route | Returns | Params |
|---|---|---|
| `GET /api/v1/learning/progress` | `ContentProgress[]` | `user_id` (req) |
| `GET /api/v1/learning/assessments` | `AssessmentSummary[]` | `user_id` (req) |
| `GET /api/v1/learning/competency` | `CompetencyRollup` | `user_id` (req), `level` (opt, ∈ {I,II,III,IV}) |
| `GET /api/v1/learning/cohort` | `CohortAggregate` | `level` (opt, ∈ {I,II,III,IV}) |

Pydantic response schemas in `schemas.py` mirror **all six** dataclasses: the four top-level read-models (`ContentProgress`, `AssessmentSummary`, `CompetencyRollup`, `CohortAggregate`) **plus the two nested** (`LevelCoverage`, `ConceptRef`). The route maps `ProjectionError('user not found')` → 404.

## Error handling (scoped per route)

| Route(s) | Condition | Result |
|---|---|---|
| progress / assessments / competency | `user_id` missing / blank / not a UUID | **400** |
| progress / assessments / competency | `user_id` valid UUID, absent from `user_profiles` (existence probe) | **404** |
| progress / assessments / competency | `user_id` exists, no matching events | **200**, empty list (progress/assessments) / zeroed rollup (competency: `evidence_event_count=0`, all `covered_ksas=0`) |
| competency / cohort | `level` present but ∉ {I,II,III,IV} | **400** |
| competency / cohort | `level` = `I` (0 KSAs) | **200**, `coverage_percent`/`mean_coverage_percent` = `null` (never 0/0) |
| cohort | (no `user_id` param exists) valid call | **200** |
| any | guard env unset | router not registered → 404 (existing prod-safe behavior) |
| any | payload missing `score_percent`/`confidence` | excluded from that mean (defensive; capture validation should prevent it) |

## Testing (TDD)

**Mini-graph fixture** (`projections_prereq.sql`, applied once/session to `learning_test`): creates the **full DDL** (not just rows) for `user_profiles`, `study_content`, `concepts`, `ksas`, `edition_ksa_map`, `content_concept_links`, then applies migration `002_learning_events.sql`, then seeds a deterministic graph designed to exercise every rule. **Test denominators are the FIXTURE KSA counts (e.g. II=4, III=3, IV=0-or-seeded), deliberately decoupled from the live II=144/III=169/IV=170** — assertions are written against the fixture, not the live DB.

- **Users (level-fallback cases, mandatory):** `U_target` (target=II, current=null), `U_current` (target=null, current=III), `U_all` (both null → all-level fallback), plus an inactive user for cohort `is_active` filtering.
- **KSAs:** a small known set per level (e.g. II:4, III:3) so coverage percentages are hand-computable; **Level I left empty** (to exercise the 0-denominator/null rule).
- **edition_ksa_map:** includes (a) the same concept→ksa_code under **both** editions (proves edition-aggregation = distinct code), (b) one **orphan** ksa_code absent from `ksas` (proves exclusion from `covered_ksas` AND inclusion of its concept in `engaged_concepts`), and (c) one **inactive** (`is_active=false`) mapping to an otherwise-valid ksa_code (proves the `is_active` filter excludes it from `covered_ksas`).
- **content_concept_links / study_content / concepts:** wire content → concept → ksa so a chosen evidence set yields a known covered count.
- **learning_events:** per-user events producing known content_progress (views + completion), assessment_summary (objective score + self-assessment confidence, incl. a section-only self_assessment that must NOT appear in per-content output), competency coverage, and cohort inputs (incl. a user with 0 completions and a user with no score).

**Assertions (per function + edge):**
- **read-only guarantee:** `test_db_readonly.py` opens the `learning-projections` session and asserts a trivial `INSERT`/`UPDATE` raises a read-only-transaction error — pins the no-write boundary the whole slice depends on.
- content_progress: view_count, is_completed/status, first/last timestamps; events without `study_content_id` excluded.
- assessment_summary: latest vs mean score, latest vs mean confidence, attempt/self counts, `last_activity_at`; section-only self_assessment excluded.
- competency_rollup: exact `covered_ksas`/`total_ksas_at_level`/`coverage_percent` for `U_target` (II, fixture denominator); `level_source` correctness for target/current/all; `levels_in_scope=['II','III','IV']` on all-fallback; **explicit `level='I'` → `resolved_level='I'`, `levels_in_scope=['I']`, one `LevelCoverage` with `total_ksas_at_level=0` and `coverage_percent=None`**; orphan code excluded from `covered_ksas` while its concept still appears in `engaged_concepts`; **inactive `edition_ksa_map` mapping excluded from `covered_ksas`**; edition de-dup; `evidence_event_count`; unknown user → 404 (API layer).
- cohort_aggregate: `mean_completed_content` counts no-completion users as 0; `mean_latest_score` excludes no-score users and returns `scored_user_count`; `mean_coverage_percent` is per-user-then-averaged over non-null users; inactive user excluded; **`level='I'` → `mean_coverage_percent=None`, `coverage_user_count=0`**.
- API tests: shapes, 400 (bad user_id / bad level), 404 (unknown user — progress/assessments/competency), cohort takes no user_id, and the guard-disabled (router-absent) case.

## Out of scope (explicit)

operations-web dashboard UI · persisted/materialized projections + any projector/replay/idempotency machinery · writing the baseline `user_study_progress`/`user_test_attempts` tables · 2c ROI correlation · real data acquisition · edition-specific competency rollup · section-level confidence model · score-thresholded mastery.

## Integration & durable notes

- `db.py` is the resolver's read-only session verbatim (pinned DSN so ambient prod PG env can't redirect; read-only transaction).
- New worktrees lack gitignored files — recreate `infra/.env` from the main clone; package tests need `uv` on PATH (`export PATH="$HOME/.local/bin:$PATH"`) + `LEARNING_TEST_PGPASSWORD`/`LEARNING_TEST_DSN`. (`uv` is the test runner only; runtime wiring is pip/requirements.txt with no `uv.lock` — see Global Constraints.)
- control-plane-api tests run self-contained via `uv run --with-requirements requirements-dev.txt` (worktree has no `.venv`).
- Host file writes via write-local-then-`ssh 'cat > dest'`; ssh commit messages avoid apostrophes (or `git commit -F`).
- No migration ⇒ no `learning_dev` schema gate this slice; merge to main stays operator-gated.
