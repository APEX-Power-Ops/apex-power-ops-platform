# Learning Slice 2d — Controlled Acquisition Pilot — Design

**Goal:** Make the first real, auditable learning evidence exist in `learning_dev` and prove it
flows end-to-end through the Slice 2a capture path into all four Slice 2b read models — without
new event types, without a schema migration, and without any prod write.

**Architecture:** A *controlled acquisition pilot*, not a feature layer. The pipe (2a `record_event`
/ append-only `learning_events`) and the read models (2b `learning-projections`) already exist and
are green. The only missing thing is real data. 2d provisions a tiny operator-approved cohort,
records a deliberately-designed event sequence through the existing 2a path with a *structurally
enforced provenance envelope*, and verifies each of the four read models moves to a
**pre-registered, independently-computed expected result** — then ships a redacted evidence
packet/runbook. The single new artifact is a thin guarded capture helper.

**Tech stack:** Python (`packages/learning-capture`), Postgres `learning_dev` (host PG17 :5432),
the existing `control-plane-api` learning routes, `pytest` on throwaway `learning_test`.

---

## Locked decisions (operator, 2026-06-20)

- **Fidelity = REHEARSAL.** The first run uses a real person (operator or a colleague) genuinely
  engaging one real content item; an observer records it via the CLI with full provenance and an
  `evidence_ref` to operator-held observation notes. Every event is tagged `data_fidelity:
  "rehearsal"`. This exercises the entire loop honestly — plumbing, provenance, *and*
  genuine-engagement evidence — with no workforce-PII/consent weight and no overclaim. The phrase
  "real workforce evidence" is reserved for a later `authentic`-tier run.
- **`employee_id` = DEFERRED.** The pilot cohort is provisioned with `employee_id = NULL`. All four
  projections key off `user_id`; `employee_id` is the bridge for the out-of-scope ROI/2c work, and
  attaching a real one would import a learner→employee→pay-rate re-identification key into the
  D8-parked, RLS-locked `public.employees` table for zero 2d value. Real binding is reserved for the
  gated person-spine slice.

---

## Current baseline (grounded, 2026-06-20)

- `learning_dev`: `user_profiles` = 1 (seed `174b1feb-…`, `is_active=true`,
  `target_certification_level`/`current_certification_level`/`employee_id` all NULL → competency
  resolves to `level_source='all'`, contributing NULL coverage to cohort). `learning_events` = 3
  seed rows only; `user_study_progress` = 0; `user_test_attempts` = 0.
- prod Supabase (`fxoyniqnrlkxfligbxmg`, read-only): `employees` = 5; `user_profiles` = 8 (all
  `technician`, 0 with a target level, 0 bridged); `study_content` = 967; tracking tables = 0;
  `tcc_test_results` = 0.
- **The tracking layer has never captured real data anywhere.** No backfill source exists; a
  deliberate first-acquisition loop is the right instrument.

---

## Scope

### In scope
1. Provision a small operator-approved cohort as **new** `user_profiles` rows (never mutate the
   frozen seed): synthetic handle, non-routable email, `role='technician'`, `is_active=true`,
   `target_certification_level` set (II/III/IV — never I), `employee_id = NULL`,
   `study_preferences` jsonb carrying `{ "data_fidelity": "rehearsal", "acquisition_run_id": … }`.
2. Define one acquisition run: `(user, NETA section, selected content, expected event sequence,
   pre-registered expected projection manifest, evidence notes)`.
3. Capture real events through the existing Slice 2a path (`record_event`) via a new **guarded
   helper** that structurally enforces the provenance envelope.
4. Add lightweight payload metadata (`acquisition_run_id`, `source_surface`, `observed_by`,
   `evidence_ref`, `data_fidelity`) **without a schema migration** (jsonb payload).
5. Verify all four read models move to their pre-registered expected values, plus a negative
   control, via the four `control-plane-api` GET routes (and a ledger readback SQL).
6. Produce a **redacted** runbook + evidence packet (handles only), not a dashboard.

### Out of scope
- New event types (the 4 are a hard DB CHECK invariant — a 5th = migration → STOP + escalate).
- New DB objects of any kind unless a hard gap appears (none is anticipated).
- ROI correlation into records/ops (Slice 2c); production auth/RLS; management UI; any prod write.
- Real `employee_id` binding (deferred to the person-spine slice).
- An `authentic`-tier real-workforce run (a clean fast-follow once the loop is proven).

---

## Acquisition protocol

### Content selection (live-verified)
- **Primary (single-level proof):** content `9c47a9ed-c46b-4d1d-a604-7c68647c913c`
  ("SCADA IEC61850 Automation") covers exactly 4 KSAs: Level III `{KSA-III-SC-002, KSA-III-SC-003}`,
  Level IV `{KSA-IV-SC-002, KSA-IV-SC-003}`, and **zero** Level-II KSAs — a clean, auditable
  per-KSA delta.
- **Secondary (in_progress state):** a *second*, distinct linked content item for a
  `resource_viewed`-only step (proves `content_progress.status='in_progress'`). Any item from the
  linkable set (879/967 carry concept links) at the cohort level; record its id in the run manifest.
- The protocol **must pre-flight** that the chosen content resolves through
  `content_concept_links → edition_ksa_map (is_active) → ksas` at the cohort's target level before
  recording, and record the expected `covered_ksas` in the manifest.

### Cohort / level
- Provision the rehearsal learner at `target_certification_level = 'III'` (matched to the SCADA
  content's covered levels), so `competency_rollup` returns a single Level-III coverage row and the
  user counts toward `cohort_aggregate.coverage_user_count`.
- Level I is forbidden for any cohort member (0 KSAs → null coverage → proves nothing).

### Event sequence (rehearsal run)
Recorded in monotonic `occurred_at` order through the guarded helper (`source_surface='cli'`):
1. `resource_viewed` on the **secondary** content → `content_progress` in_progress + `view_count`.
2. `resource_viewed` then `resource_completed` on **SCADA** → `content_progress` completed;
   `competency_rollup` Level III coverage 0→2 KSAs (the exact set `{KSA-III-SC-002, KSA-III-SC-003}`
   is what the SQL manifest enumerates; the API exposes only the *count* `covered_ksas=2`),
   `coverage_percent` 0→`round(100*2/169,1)=1.2`. `evidence_event_count` counts qualifying *events*
   (not distinct content) and reaches **2** by end-of-run: this `resource_completed` + the step-3
   `assessment_completed` on SCADA.
3. `assessment_completed` on SCADA with `payload.score_percent` = the real graded score →
   `assessment_summary` latest/mean score; feeds `cohort_aggregate.scored_user_count`.
4. (optional) `self_assessment` on SCADA with `payload.confidence` (int 1–5, matching the seed
   scale) → `assessment_summary` self-assessment confidence (must carry `study_content_id` to appear).

### Payload / provenance contract (exact)
Every captured event payload **must** carry, and the helper **must** enforce non-empty:
- `acquisition_run_id` (uuid/slug), `source_surface` (enum: `cli` | `operations-web/learning-demo` |
  `manual-runbook`), `observed_by` (operator handle/initials — never a full name/email),
  `evidence_ref` (pointer to operator-held proof outside git — never PII), `data_fidelity`
  (`synthetic` | `rehearsal` | `authentic`).
- For `assessment_completed`: `score_percent` (numeric 0–100) — **this exact key**, or
  `assessment_summary` silently returns NULL.
- For `self_assessment`: `confidence` (int 1–5) — **this exact key**.
- The helper **forbids a client-supplied `occurred_at`** (server `now()` only) to prevent backdating;
  `created_at` (server clock) is the authoritative audit timestamp.

---

## The guarded helper (the only new code)

`packages/learning-capture/src/learning_capture/acquisition.py`

```
record_acquired_event(
    *, user_id, event_type, acquisition_run_id, source_surface, observed_by,
    evidence_ref, data_fidelity, study_content_id=None, neta_section=None,
    score_percent=None, confidence=None,
) -> event_id
```

Behavior:
- Requires `acquisition_run_id`, `source_surface`, `observed_by`, `evidence_ref`, `data_fidelity`
  all non-empty; `data_fidelity` ∈ the enum; `source_surface` ∈ the enum. Raises `CaptureError`
  otherwise.
- Rejects unknown metadata keys (no silent typos like `acquisiton_run_id`).
- `assessment_completed` requires `score_percent` (numeric 0–100); `self_assessment` requires
  `confidence` (int 1–5); both also require `study_content_id` to be projection-visible.
- Injects the provenance envelope into `payload`, then calls the existing `record_event` (reusing
  its user-exists / content-exists / range checks). Never passes `occurred_at`.
- **Prod-isolation guard:** hard-refuses to run unless the resolved DSN host/db matches the
  `learning_dev` (or `learning_test`) signature; aborts on any `*.supabase.co` host or the prod
  project ref `fxoyniqnrlkxfligbxmg`.

Justification: the existing capture path has **no provenance enforcement** (`EventIn.payload` is an
untyped `dict = {}`, `POST /events` has no auth, `record_event` validates only existence + ranges).
Without structural enforcement, a hand-written event is byte-indistinguishable from a real one and
"auditable" is dishonest. This ~30–40-line wrapper is the proportionate fix and stays within the
"small guarded helper" latitude.

---

## Verification (correctness, not "it moved")

Because 91% of content covers ≥1 KSA and one item maps to a **median of 54 KSAs**, "projections
moved" is near-tautological and `coverage_percent` is inflated. Therefore:

1. **Pre-register an expected manifest** computed by an *independent* query (enumerate the exact
   `ksa_code` set `content_concept_links → edition_ksa_map → ksas` yields for the chosen content at
   the user's level; the exact covered count and `coverage_percent` against denominators
   II=144 / III=169 / IV=170).
2. **Assert exact equality** (engine output == manifest) for each of the four read models, captured
   as before/after JSON in the evidence packet:
   - `GET /api/v1/learning/progress?user_id=U` — new `ContentProgressOut` for SCADA with
     `status='completed'`/`is_completed=true`; secondary content `in_progress`; `view_count` correct.
   - `GET /assessments?user_id=U` — attempts +1; `latest_score_percent == captured score`.
   - `GET /competency?user_id=U` — `resolved_level='III'`, `level_source='target'`,
     `covered_ksas == 2` (the API returns a COUNT, not the code set), `coverage_percent == 1.2`,
     `evidence_event_count == 2` (the projection counts qualifying *events*, not distinct content).
     The exact `ksa_code` set `{KSA-III-SC-002, KSA-III-SC-003}` is asserted by the independent SQL
     manifest (below), **not** the API — the 2b response does not expose KSA codes.
   - `GET /cohort?level=III` — `coverage_user_count` includes U; `mean_coverage_percent`,
     `mean_latest_score`, `mean_completed_content`, `scored_user_count` as pre-registered.
3. **Negative control (named subject, `learning_test` only):** the live `learning_dev` run
   provisions a single rehearsal learner (the positive proof), so the negative control is provisioned
   in the **`learning_test` acquisition fixture** — a leveled user with no content-linked evidence
   must show `covered_ksas=0`/`coverage_percent` per the formula, and a Level-I user must remain null
   (0 KSAs). The dev run does not add a second cohort row just to be empty.
4. **Breadth-not-mastery annotation:** the packet states in its header that `coverage_percent`
   reflects content-to-KSA mapping *breadth*, NOT demonstrated competence — so "one completion =
   1.2% of Level III" (and the latent ~37%-from-one-resource fan-out) is never read as mastery.
5. **Backdating assertion:** for every run row, `occurred_at` is within tolerance of `created_at`.

---

## Privacy / governance gates

- **Redaction contract (committable vs operator-held).** Committable (handles only):
  `acquisition_run_id`, `source_surface`, `observed_by` (initials), `evidence_ref` (opaque pointer),
  `data_fidelity`, learners referenced by synthetic handle or `learning_dev` `user_profiles.id`
  (dev-local uuid). **Never committable:** any `full_name`/`email`/`phone`, any prod `employee_id`,
  any financial field, any free text that re-identifies a real person. A mechanical pre-commit grep
  guard (reject `@`-domains + a name denylist) checks redaction, not the eye. The real
  person↔handle / observation notes live in private `.claude/PLATFORM/` substrate, referenced by
  `evidence_ref`, never in `docs/`.
- **`data_fidelity` everywhere.** On every event payload and on the cohort row
  (`study_preferences` jsonb) and in the evidence-packet header. Verification reports a per-fidelity
  breakdown so demo/rehearsal rows can never be silently promoted downstream as `authentic`.
- **Dev-only / no prod write.** Capture goes only through the guarded helper (with the prod-isolation
  guard); **raw `INSERT` into `learning_events` is forbidden** (raw SQL is allowed only for
  `user_profiles` cohort provisioning). `learning_dev` schema-apply remains gated; 2d flips no gate.
- **Data-write gate (NEW for 2d).** Unlike Slices 1/2a/2b (code + schema only), 2d writes *business
  data* into `learning_dev` (cohort rows + captured events). That data write is itself
  operator-approved — a distinct gate from `schema` apply and from `promotion` (merge). The plan's
  **Task 0** updates the lane charter (`docs/lanes/README.md`) to record the active
  `learning/slice2d-acquisition-pilot` branch and add this `data_write` gate, before any
  implementation task runs.
- **Hard-gap escape clause.** The only thing forcing a migration is an event semantic not
  expressible as one of `{resource_viewed, resource_completed, assessment_completed,
  self_assessment}` (the `learning_events_event_type_check` constraint). If the pilot hits that, it
  STOPS and escalates rather than widening the constraint.

---

## Tests
Reuse, do not duplicate, the 2b scaffolding (the `learning_test` conftest guard that refuses any
non-`learning_test` DSN; the read-only guard test; the deterministic mini-graph fixture). **The 2b
mini-graph `user_profiles` lacks `role`, `employee_id`, and `study_preferences`, which 2d uses** —
add a small **acquisition prereq extension** (`tests/acquisition_prereq.sql`) that `ALTER TABLE`s the
fixture `user_profiles` to add those columns (parity with `learning_dev`), applied after the 2b
prereq. Do not fork the whole fixture.
- `acquisition.py` helper unit tests: required-key enforcement; unknown-key rejection;
  `score_percent`/`confidence` requirement + range; no `occurred_at` passthrough; prod-isolation
  guard refuses a non-dev DSN.
- An acquisition fixture extending the 2b mini-graph: record the run sequence, then assert the four
  read models equal the pre-registered manifest (exact), plus the negative control.
- Backdating assertion test (`occurred_at ≈ created_at`).
- Optional: one thin browser smoke through `operations-web/app/learning-demo` only if the panel is
  named as a capture surface for the run (otherwise skip — the API tests cover it).

---

## Deliverables
- **Committable:** this spec; the redacted runbook (`docs/learning/slice2d/runbook.md`); the redacted
  evidence packet (before/after JSON + manifest assertions); the guarded helper + its tests; a
  committed, **idempotent** cohort-provisioning SQL script (synthetic handles).
  **Reversal rule (non-destructive in `learning_dev`):** reversal = **retire/deactivate** the cohort
  row (`is_active=false`), NEVER delete it. Deleting a cohort row cascades to `learning_events`
  (FK `on delete cascade`) and trips the append-only DELETE-blocking trigger — which is *correct*:
  captured evidence is immutable. Destructive teardown (DROP/recreate) is reserved for the throwaway
  `learning_test` DB only.
- **Operator-held (never committed):** the real person↔handle mapping, the genuine-engagement
  observation notes (the `evidence_ref` target), any DSN.
- `learning_dev` remains schema-apply-gated and dev-only; merge of the committable artifacts follows
  the standard operator merge gate used for Slices 1 / 2a / 2b.
