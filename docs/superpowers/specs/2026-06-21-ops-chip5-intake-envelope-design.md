# Ops Chip 5 — Estimator Intake Envelope (design spec)

**Status:** approved-shape, operator-redirected (D1–D7 + structural review-payload addition + testing matrix). Pre-plan.
**Lane:** Operations (PM). Branch `ops/chip5-intake-envelope` off `main@94db4727` (Chips 1–4 merged). Host worktree `/home/olares/code/apex/apex-ops-chip5`.
**Dev DB:** tests on throwaway `ops_test`; `ops_dev` for operator review only. **Nothing applied to prod.** Merge to main is operator-gated.
**SSoT:** `reference/ops/00-MASTER-INDEX.md` §7 (Chip 5) + §8 decisions. This chip also CORRECTS the stale §6/G6 + §7 text (the extractor exists; this chip is the envelope/lifecycle/UI around it).

---

## 1. Goal

Turn the working-but-bare Miner loader into a **server-side, governed, multi-project intake product**:

> upload an Estimator `.xlsm` → server parses → validate → persist an auditable **intake run** → PM reviews/edits the **scope → task → apparatus** tree → **identity-gated approve** materializes & freezes the quote → operational.

The operational `ops.*` revenue substrate (Chips 1–4) is written **only at approve**. Everything before approve lives in the intake **envelope** and is fully reversible by discarding the run.

## 2. Context — what already exists (verified)

- **The intake engine exists and produced the live data.** `packages/ops-intake/` (`extract.py` → `validate.py` → `load.py` → `cli.py`, real-Miner e2e) loaded the **$4.69M / 5,344-apparatus** Miner project into `ops_dev`. The SSoT §6/G6 ("intake extraction code does not exist") is **stale** — this chip fixes it.
- **What the engine is missing** (the Chip 5 gap):
  1. **No envelope** — no `intake_runs`/`source_files`/`validation_findings`; findings (`Check[]`) are computed then discarded.
  2. **Writes ops.\* immediately** — `load.py` upserts the domain rows on load, with an inline `--approve` flag; there is no staged review and no separation of parse from materialization.
  3. **Hard-coded to Miner** — `_SOURCE='miner_rev10.xlsm'`, `source='project-miner'`.
  4. **No task level** — `ops.tasks` + `ops.apparatus.task_id` exist (Chip 1) but the loader never populates them; the `section` grouping is dropped.
  5. **Approve is a CLI flag** — no `ops.persons` actor; no revision story (re-intake of a frozen project now hard-fails the `005` immutability triggers).
  6. **Writes the `standard_hours` catalog from the upload** (`load.py:43`) — upload-driven mutation of a shared, universal catalog.
- **The macro is the extraction spec.** `Reference_Files/Excel/Estimator VBA Modules/DataverseExport.bas` encodes which cells map to which fields (scope sheets `Scope1..Scope20`; `J3`=hours, `M4`=multiplier, `P3`=unadjusted grand total; financial rows 14/19/26/33; apparatus rows 6–488 with bold-header **`section`** detection; the `Dataverse_Import` metadata sheet for client/site/project). Its JSON output (`_DATAVERSE_IMPORT_*.json`) is the de-facto payload shape. **Reference only** — we do not rebuild the Dataverse/RESA-web-app workflow.
- **PowerBI v1 (`RESA_Dashboard.pbix`) — reference concepts (out of scope):** the reporting grain is exactly scope→task→apparatus; completion rolls up hours-weighted; the field view **deliberately hides every dollar column** (the firewall as UX). Harvested into D7; the dashboards themselves are a later serving chip.

## 3. Scope & non-goals

**In scope (the full vertical, dev-validated):**
- Migration **007** — the envelope tables + DB guards + minimal source columns.
- `packages/ops-intake` generalization — parse/validate/persist-envelope (no domain writes), identity-gated approve (the only domain writer), revision refusal, macro-parity parsing incl. `section`→task + N4.
- **control-plane API** — host-gated intake routes (upload/preview/edit/approve), registered only when `OPS_DEV_DSN` is present (mirrors the learning routes; never on the prod Render deploy).
- **operations-web** — upload → review/edit tree → approve UI, against the host control-plane API → `ops_dev`. Branding from `resa-complete-theme.json`.

**Explicitly OUT (named so nothing silently expands):**
- Reporting dashboards / KPIs / work-queue / Gantt (the PowerBI concepts) → a later **serving** chip.
- `standard_hours` catalog seeding (universal; D-OPS-7) — and Chip 5 **removes** the existing upload-driven catalog mutation.
- Normalized client/site CRM tables.
- CPM/P6 scheduling.
- **Production multi-user rollout** — `ops.*` is host-only today; broad rollout rides the deferred `public/seam → ops` convergence (Chip N). Chip 5 *proves* the product on dev; it is *rolled out* later.
- Automated reverse/supersede of an already-recognized/billed project (D5: detect + refuse only).

## 4. The intake contract

### 4.1 Front door
- **Server-side `.xlsm` parse is the product.** Operators upload the workbook; the server extracts it. The parser is brought to **macro-parity** (the `DataverseExport.bas` mapping is the spec), adding what the engine currently drops: `section`→task, client/site, the metadata sheet, and **N4**.
- **JSON-upload is a retained alternate input** (the macro's existing output), normalized to the same canonical payload. It is not the path handed to others.
- **`source_format` discriminator** classified at the boundary: `decomposed_scope_sheet` (full support, loadable) · `flat_quote` (no apparatus decomposition) and `unsupported` → the run is recorded as **`rejected`** with a boundary finding and never materializes. Reject not-yet-ready quotes at the door.

### 4.2 Canonical payload (versioned)
The parser emits a **canonical payload** (`payload_schema_version`, e.g. `"1"`), superset of the current `IntakePayload`, adding:
- `project.client_name`, `project.site_{name,address,city,state,zip,contact_name,contact_phone,contact_email}` (from the metadata sheet / JSON `client`+`site`).
- per-scope `pct_adjust` (**N4**) alongside `unit_multiplier` (M4).
- per-apparatus-line `section` (drives task grouping).
The raw uploaded bytes + sha256 are preserved separately (provenance); the canonical payload is the derived, immutable parse output.

### 4.3 N4 fidelity (D3, strengthened)
- For `.xlsm`: **N4 is parsed and validated, not optional.** It maps to `scope_quote.pct_adjust` (`002_quote_model.sql`). Validation requires per-scope `P3 × M4 × N4 == quotedAmount` and `Σ adjusted == contract_value` within tolerance.
- For the JSON fallback: N4 may default to `1`, but this **emits a `fidelity` finding**, and **approve requires the totals to reconcile** (the finding must be resolved/acknowledged or the parse re-sourced) — a default-1 that breaks reconciliation blocks approval.

## 5. Data model — migration 007

Additive + reversible. `007_intake_envelope_down.sql` drops only 007 objects; **Chips 1–6 survive DOWN**.

### 5.1 Envelope tables

```
ops.intake_run_status        enum: parsed | reviewing | approved | rejected | revision_blocked
ops.intake_conflict_kind     enum: none | frozen | recognized | billed
ops.intake_source_format     enum: decomposed_scope_sheet | flat_quote | unsupported

ops.intake_runs
  id                     uuid pk
  project_number         text not null              -- the natural key parsed from the source
  project_id             uuid null references ops.projects(id)   -- set only at/after approve (or link to an existing project)
  source_format          ops.intake_source_format not null
  status                 ops.intake_run_status not null default 'parsed'
  conflict_kind          ops.intake_conflict_kind not null default 'none'
  payload_schema_version text not null
  parser_version         text not null
  canonical_payload_json jsonb not null             -- immutable: the parser output
  review_payload_json    jsonb not null             -- editable working copy (starts == canonical)
  review_payload_version int  not null default 1    -- bumped on each PATCH
  uploaded_by            uuid not null references ops.persons(person_id)
  uploaded_at            timestamptz not null default now()
  approved_by            uuid null references ops.persons(person_id)   -- D6: hard FK
  approved_at            timestamptz null
  rejected_reason        text null
  created_at/updated_at  timestamptz

ops.intake_source_files
  id            uuid pk
  run_id        uuid not null references ops.intake_runs(id) on delete cascade
  filename      text not null
  content_type  text not null              -- xlsx / json
  byte_size     bigint not null
  sha256        text not null              -- hex; provenance + dedupe signal
  raw_bytes     bytea null                 -- the uploaded artifact (or a storage ref); keep-vs-discard is an operator call, default keep
  created_at    timestamptz

ops.intake_validation_findings
  id              uuid pk
  run_id          uuid not null references ops.intake_runs(id) on delete cascade
  payload_version int  not null            -- which review_payload_version this was computed against
  severity        text not null            -- 'blocking' | 'fidelity' | 'info'
  code            text not null            -- machine code, e.g. 'j3_mismatch', 'contract_total', 'n4_default', 'unsupported_format'
  ok              boolean not null
  detail          text not null default ''
  created_at      timestamptz
  -- a finding is "open" if severity='blocking' and ok=false at the current review_payload_version
```

Immutability: `canonical_payload_json`, `source_format`, `payload_schema_version`, `parser_version`, `uploaded_by` are write-once (trigger rejects UPDATE of these). `approved_by`/`approved_at` set-once at approve.

### 5.2 DB guards (D1)

The schema lets `apparatus.task_id` point at a task in a **different** scope, and `apparatus.scope_id` is immutable (`trg_apparatus_scope_immutable`, `001`) but `tasks.scope_id` is not. 007 adds:
- **`trg_apparatus_task_same_scope`** (`before insert or update on ops.apparatus`): if `new.task_id is not null`, require `(select scope_id from ops.tasks where id = new.task_id) = new.scope_id`, else `raise exception`.
- **`trg_task_scope_immutable`** (`before update on ops.tasks`): if any apparatus references the task (or, simpler, unconditionally once a row exists), reject changes to `tasks.scope_id`. Keeps the task→scope binding stable so the apparatus guard cannot be defeated by moving the task.

### 5.3 Minimal source columns (D2)

Add to `ops.projects` (marked source-derived, **not** canonical CRM):
- `source_client_name text null`
- `source_site_name text null`, `source_site_address text null`, `source_site_city text null`, `source_site_state text null`, `source_site_zip text null`
The full client/site/contact set is retained in `intake_runs.canonical_payload_json` / `intake_source_files`. No client/site/contact tables.

## 6. The package — `ops-intake` generalization

### 6.1 Parse → envelope (NO operational writes)
- De-Miner-ize: source identity comes from the run, not `_SOURCE`/`'project-miner'` literals.
- Parser to macro-parity: `section`→task, client/site, metadata sheet, N4; `source_format` classification.
- New `envelope.py`: `create_run(dsn, *, uploaded_by, filename, raw_bytes, content_type) -> run_id` — parse → classify → persist `intake_runs` (canonical==review payload v1) + `intake_source_files` (sha256) + `intake_validation_findings`. **Touches only envelope tables.**
- **No domain writes** before approve: parse/validate/persist-envelope never INSERT/UPDATE `ops.projects|scopes|tasks|apparatus|scope_quote|scope_quote_line`.

### 6.2 Review/edit
- `validate_payload(review_payload) -> Check[]` (the existing 3 checks + N4 reconciliation + format) computed against the **review** payload at its version; re-persisted as findings at the new `payload_version` on each PATCH.
- Edits permitted on the review payload: task rename/regroup, **move apparatus between tasks within a scope**, edit `hrs_per_unit`, edit metadata. **Forbidden: move apparatus across scopes** (Law 1) — rejected in the package and unreachable in the UI.

### 6.3 Approve (the only domain writer; D6 identity-gated)
- `approve_run(dsn, run_id, *, approved_by) -> ApproveResult`, transactional:
  1. Re-validate the current `review_payload`; **refuse if any `blocking` finding is open** (incl. N4 reconciliation).
  2. Refuse if `status = revision_blocked` (D5).
  3. Materialize the review payload into `ops.*` scoped to the project (the current `load.py` upsert logic, now creating **tasks** from `section` and linking `apparatus.task_id`; `apparatus.scope_id` set from its scope).
  4. Freeze: set `scope_quote.is_frozen/frozen_at`, compute `apparatus.quoted_revenue = round(quoted_hours × blended_rate, 2)`, set `provenance_status='approved'` — **project-scoped** (never touches other projects).
  5. Set `intake_runs.status='approved'`, `approved_by/at`, link `project_id`.
- **Removes upload-driven `standard_hours` mutation** (D4): the catalog is not written by intake at all.

### 6.4 Revision detection & refusal (D5, stricter)
At `create_run`, look up `ops.projects` by `project_number`:
- **none** → `conflict_kind='none'`, status `parsed` → normal flow.
- **exists, no frozen scope_quote, no recognition, no billing** → `none` → updatable draft (still materialized only at approve).
- **exists AND (any `scope_quote.is_frozen` for its scopes, OR `ops.revenue_recognition_event` net>0, OR any `ops.billing_application` for `project_id`)** → classify `conflict_kind` = `billed` > `recognized` > `frozen` (most-downstream wins), set `status='revision_blocked'`, persist the run as a **proposed revision**, and **refuse operational writes**. Surface the diff. **Do not** automate reverse/supersede — that is an explicit, separate operator action outside Chip 5.
  - Conflict inspection covers **both** ledgers: recognition (`ops.revenue_recognition_event`) **and** billing (`ops.billing_application.project_id`), not recognition alone.

## 7. The control-plane API (host-gated)

Routes register **only when `OPS_DEV_DSN` is set** (env-gated like the learning routes; absent on the prod Render deploy → no 500ing routes). All calls require an `actor_person_id` resolvable to `ops.persons`.
- `POST /api/v1/ops/intake` — multipart `.xlsm`/`.json` upload → `create_run` → returns `{run_id, status, conflict_kind, preview_tree, findings}`. **No domain writes.**
- `GET /api/v1/ops/intake/{run_id}` — run + `review_payload` tree + findings.
- `PATCH /api/v1/ops/intake/{run_id}` — edit the **review payload only** (task regroup, hrs_per_unit, metadata) → bump `review_payload_version` → re-validate → new findings. Enforces PM authority (cross-scope apparatus moves rejected 4xx).
- `POST /api/v1/ops/intake/{run_id}/approve` — identity-gated `approve_run`. 409 if `revision_blocked`; 422 if open blocking findings.
- `POST /api/v1/ops/intake/{run_id}/reject` — record `rejected` + reason.

## 8. The UI — operations-web

A new intake surface (against the host control-plane API → `ops_dev`):
1. **Upload** — drop the `.xlsm`; show parse result + `source_format` + findings.
2. **Review tree** — scope → task → apparatus, editable task groupings and `hrs_per_unit`, inline validation findings, run status. Cross-scope moves not offered.
3. **Approve** — identity-gated; disabled while blocking findings are open or `revision_blocked` (shows the conflict + diff instead).
- **D7 firewall:** the review/approve surface shows **structure, hours, validation, status — no dollars.** `quoted_revenue` is computed at approve and lives behind the finance gate.
- Branding from `resa-complete-theme.json`.

## 9. Laws & invariants honored
- **Law 1** (scope→apparatus fixed): no cross-scope apparatus moves; the 007 task-scope guard backstops it in the DB.
- **Law 3** (recognition firewall): no dollars in review; `quoted_revenue` materialized only at approve; the `005` frozen-basis immutability triggers are respected (intake never mutates a frozen project — it refuses).
- **No operational writes before approve** (the central new invariant).
- Identity (`ops.persons`) on `uploaded_by` + `approved_by` (D6).

## 10. Testing matrix (TDD, throwaway `ops_test`; `ops_dev` for operator review only)

Migration + package + API tests pin `OPS_DEV_DSN` at `ops_test` (the fixture truncates/down-nukes). Required cases:
- **No operational writes before approve** — parse + PATCH leave `ops.projects|scopes|tasks|apparatus|scope_quote|scope_quote_line` row-counts unchanged; only envelope tables grow.
- **Task-scope guard** — `apparatus.task_id` cross-scope INSERT/UPDATE rejected; `tasks.scope_id` change rejected once referenced.
- **Frozen-project revision refusal** — re-parse of a frozen/recognized/billed project → `status=revision_blocked`, `conflict_kind` correct, **zero domain writes**, approve 409.
- **Recognition/billing conflict classification** — `frozen`-only vs `recognized` vs `billed` each classified correctly (billing checked independently of recognition).
- **N4 parity** — `.xlsm` N4 parsed and totals reconcile (P3×M4×N4==quotedAmount, Σadjusted==contract_value); JSON default-1 emits a `fidelity` finding; approval blocked when default-1 breaks reconciliation.
- **Route guard disabled when `OPS_DEV_DSN` absent** — import-isolated subprocess proves the intake routes do not register.
- **Identity-gated approve** — approve requires a valid `ops.persons` actor; the FK is enforced.
- **Source-format rejection** — `unsupported`/`flat_quote` → `rejected` run + boundary finding, no materialization.
- **Full e2e** — upload a decomposed workbook → review/edit (regroup a task, override an `hrs_per_unit`) → approve → `ops.*` materialized with tasks + `apparatus.task_id` set + frozen quote; Σ apparatus quoted_revenue == scope P4.
- **Idempotent re-parse pre-approval** — re-uploading before approve creates a new run (or updates the draft) without duplicating domain rows (there are none yet).
- **DOWN** — `007_down` removes 007 objects; `001`–`006` schema + any data intact.

## 11. Housekeeping (part of "done")
- Fix SSoT `00-MASTER-INDEX.md` §6/G6 + §7 (extractor exists; Chip 5 = envelope/lifecycle/UI), add a **D-OPS** decision row (parse/envelope/approve separation · no-writes-before-approve · revision-refusal incl. billing · N4 mandatory for `.xlsm`).
- MANIFEST row 007.
- RESUME_HERE + `project_ops_pm_lane` memory at the merge checkpoint.

## 12. Open questions for operator review
1. **Raw artifact retention** — keep `intake_source_files.raw_bytes` (enables re-parse + chain-of-custody) vs discard post-parse (store only sha256)? Default: keep.
2. **`flat_quote` disposition** — reject as not-ready (current lean) vs accept as a single-scope estimate (like the Miner chiller `is_estimate` lump)?
3. **Draft update vs new project** — when re-intaking an existing *unfrozen* project, update in place at approve vs always create a distinct revision? Default: update in place (only frozen/recognized/billed triggers `revision_blocked`).
