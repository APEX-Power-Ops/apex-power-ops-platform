# Ops Chip 5 — Estimator Intake Envelope (design spec)

**Status:** approved-shape; **v2** after operator review #2 (findings finance-redaction · task idempotency key · supersede lifecycle · full-replacement materialization · raw-bytes posture). Pre-plan.
**Lane:** Operations (PM). Branch `ops/chip5-intake-envelope` off `main@94db4727` (Chips 1–4 merged). Host worktree `/home/olares/code/apex/apex-ops-chip5`.
**Dev DB:** tests on throwaway `ops_test`; `ops_dev` for operator review only. **Nothing applied to prod.** Merge to main is operator-gated.
**SSoT:** `reference/ops/00-MASTER-INDEX.md` §7 (Chip 5) + §8 decisions. This chip also CORRECTS the stale §6/G6 + §7 text (the extractor exists; this chip is the envelope/lifecycle/UI around it).

---

## 1. Goal

Turn the working-but-bare Miner loader into a **server-side, governed, multi-project intake product**:

> upload an Estimator `.xlsm` → server parses → validate → persist an auditable **intake run** → PM reviews/edits the **scope → task → line** tree (apparatus are the QTY-expansion materialized at approve, shown read-only) → **identity-gated approve** materializes & freezes the quote → operational.

The operational `ops.*` revenue substrate (Chips 1–4) is written **only at approve**. Everything before approve lives in the intake **envelope** and is fully reversible by discarding the run.

## 2. Context — what already exists (verified)

- **The intake engine exists and produced the live data.** `packages/ops-intake/` (`extract.py` → `validate.py` → `load.py` → `cli.py`, real-Miner e2e) loaded the **$4.69M / 5,344-apparatus** Miner project into `ops_dev`. The SSoT §6/G6 ("intake extraction code does not exist") is **stale** — this chip fixes it.
- **What the engine is missing** (the Chip 5 gap):
  1. **No envelope** — no `intake_runs`/`source_files`/`validation_findings`; findings (`Check[]`) are computed then discarded.
  2. **Writes ops.\* immediately** — `load.py` upserts the domain rows on load, with an inline `--approve` flag; no staged review, no separation of parse from materialization.
  3. **Hard-coded to Miner** — `_SOURCE='miner_rev10.xlsm'`, `source='project-miner'`.
  4. **No task level** — `ops.tasks` + `ops.apparatus.task_id` exist (Chip 1) but the loader never populates them; the `section` grouping is dropped.
  5. **Approve is a CLI flag** — no `ops.persons` actor; no revision story (re-intake of a frozen project now hard-fails the `005` immutability triggers).
  6. **Writes the `standard_hours` catalog from the upload** (`load.py:43`) — upload-driven mutation of a shared, universal catalog.
- **The macro is the extraction spec.** `Reference_Files/Excel/Estimator VBA Modules/DataverseExport.bas` encodes which cells map to which fields (scope sheets `Scope1..Scope20`; `J3`=hours, `M4`=multiplier, `P3`=unadjusted grand total; financial rows 14/19/26/33; apparatus rows 6–488 with bold-header **`section`** detection; the `Dataverse_Import` metadata sheet for client/site/project). Its JSON output (`_DATAVERSE_IMPORT_*.json`) is the de-facto payload shape. **Reference only** — we do not rebuild the Dataverse/RESA-web-app workflow.
- **PowerBI v1 (`RESA_Dashboard.pbix`) — reference concepts (out of scope):** reporting grain is exactly scope→task→apparatus; completion rolls up hours-weighted; the field view **deliberately hides every dollar column** (the firewall as UX). Harvested into D7; dashboards are a later serving chip.

## 3. Scope & non-goals

**In scope (the full vertical, dev-validated):**
- Migration **007** — the envelope tables + DB guards + minimal source columns.
- `packages/ops-intake` generalization — parse/validate/persist-envelope (no domain writes), identity-gated approve (the only domain writer), revision refusal, macro-parity parsing incl. `section`→task + N4.
- **control-plane API** — host-gated intake routes (upload/preview/edit/approve), registered only when `OPS_DEV_DSN` is present (mirrors the learning routes; never on the prod Render deploy).
- **operations-web** — upload → review/edit tree → approve UI, against the host control-plane API → `ops_dev`. Branding from `resa-complete-theme.json`.

**Explicitly OUT (named so nothing silently expands):**
- Reporting dashboards / KPIs / work-queue / Gantt → a later **serving** chip.
- `standard_hours` catalog seeding (universal; D-OPS-7) — Chip 5 **removes** the existing upload-driven catalog mutation.
- Normalized client/site CRM tables.
- CPM/P6 scheduling.
- **Production multi-user rollout** — `ops.*` is host-only today; broad rollout rides the deferred `public/seam → ops` convergence (Chip N). Chip 5 *proves* the product on dev; it is *rolled out* later.
- Automated reverse/supersede of an already-recognized/billed project (D5: detect + refuse only).

## 4. The intake contract

### 4.1 Front door
- **Server-side `.xlsm` parse is the product.** Operators upload the workbook; the server extracts it. The parser is brought to **macro-parity** (the `DataverseExport.bas` mapping is the spec), adding what the engine currently drops: `section`→task, client/site, the metadata sheet, and **N4**.
- **JSON-upload is a retained alternate input** (the macro's existing output), normalized to the same canonical payload. Not the path handed to others.
- **Security posture:** the server reads the workbook **as data** (`openpyxl`, `data_only=True` → cached cell values; Excel-owns-compute). **VBA/macros are never executed server-side.** Uploads over a **size cap** (default 25 MB) are rejected at the boundary.
- **`source_format` discriminator** classified at the boundary: `decomposed_scope_sheet` (any scope bears apparatus lines → full support, loadable) · `flat_quote` (scopes present, none bear lines) · `unsupported` (no scopes at all). **`flat_quote` and `unsupported` are both REJECTED** — the run is recorded `rejected` with a boundary finding and never materializes (flat quotes lack the apparatus decomposition the recognition grain requires). Classification keys **only** on whether any scope bears lines — a missing/zero contract total is a `contract_total` reconciliation FINDING (§4.3), never a format rejection, so a parse glitch can't silently reject a loadable project.

### 4.2 Canonical payload (versioned)
The parser emits a **canonical payload** (`payload_schema_version`, e.g. `"1"`), a superset of the current `IntakePayload`, adding:
- `project.client_name`, `project.site_{name,address,city,state,zip,contact_name,contact_phone,contact_email}` (from the metadata sheet / JSON `client`+`site`).
- per-scope `pct_adjust` (**N4**) alongside `unit_multiplier` (M4).
- per-apparatus-line `section` (drives task grouping; the stable task key — see §5.2).
The raw uploaded bytes + sha256 are preserved separately (provenance); the canonical payload is the derived, immutable parse output.

### 4.3 N4 fidelity (D3) + finding severity model
- For `.xlsm`: **N4 is parsed and validated, not optional.** It maps to `scope_quote.pct_adjust` (`002`). Validation requires per-scope `P3 × M4 × N4 == quotedAmount` and `Σ adjusted == contract_value` (reusing the existing `validate.py` tolerances: `0.01` hrs, `$1` contract).
- For the JSON fallback: N4 may default to `1`. This emits an **`info` (fidelity) finding** — informational, **never blocking on its own**.
- **Severity model (three levels):** `blocking` (must be `ok` to approve — J3 mismatch, contract-total mismatch, unsupported format), `fidelity`/`info` (recorded, never blocks). A default-1 N4 that *breaks reconciliation* surfaces as a **separate `blocking` reconciliation finding** — so the failure blocks approve while the bare default does not. No acknowledgement/disposition workflow is needed (resolved by re-sourcing, not by acking).

## 5. Data model — migration 007

Additive + reversible. `007_..._down.sql` drops only 007 objects; **Chips 1–6 survive DOWN**.

### 5.1 Envelope tables

```
ops.intake_run_status        enum: parsed | reviewing | approved | rejected | revision_blocked | superseded
ops.intake_conflict_kind     enum: none | frozen | recognized | billed
ops.intake_source_format     enum: decomposed_scope_sheet | flat_quote | unsupported

ops.intake_runs
  id                     uuid pk
  project_number         text not null                  -- natural key parsed from the source
  project_id             uuid null references ops.projects(id)   -- set at/after approve
  source_format          ops.intake_source_format not null
  status                 ops.intake_run_status not null default 'parsed'
  conflict_kind          ops.intake_conflict_kind not null default 'none'
  payload_schema_version text not null
  parser_version         text not null
  canonical_payload_json jsonb not null                 -- immutable: parser output
  review_payload_json    jsonb not null                 -- editable working copy (starts == canonical)
  review_payload_version int  not null default 1        -- bumped on each review edit (POST /review)
  uploaded_by            uuid not null references ops.persons(person_id)
  uploaded_at            timestamptz not null default now()
  approved_by            uuid null references ops.persons(person_id)   -- D6 hard FK
  approved_at            timestamptz null
  rejected_reason        text null
  created_at/updated_at  timestamptz
  -- one approvable active run per project_number (backstop for the supersede lifecycle, §6.4):
  --   create unique index uq_intake_one_active on ops.intake_runs (project_number)
  --     where status in ('parsed','reviewing');

ops.intake_source_files
  id            uuid pk
  run_id        uuid not null references ops.intake_runs(id) on delete cascade
  filename      text not null
  content_type  text not null              -- discriminator: 'xlsm' | 'json'
  byte_size     bigint not null            -- CHECK (>0 and <= 25 MB) -- audit-envelope guard, not only the API boundary
  sha256        text not null              -- hex; provenance + dedupe signal (identical re-upload detectable)
  raw_bytes     bytea not null             -- Chip 5 KEEPS the artifact; CHECK octet_length(raw_bytes)=byte_size; no storage_ref path
  created_at    timestamptz

ops.intake_validation_findings
  id               uuid pk
  run_id           uuid not null references ops.intake_runs(id) on delete cascade
  payload_version  int  not null            -- the review_payload_version this was computed against
  severity         text not null            -- 'blocking' | 'fidelity' | 'info'
  code             text not null            -- 'j3_mismatch' | 'contract_total' | 'n4_reconcile' | 'n4_default' | 'unsupported_format' ...
  ok               boolean not null
  message          text not null default '' -- PM-SAFE display text — NO dollar values
  diagnostic_detail text null               -- finance-only: may contain money (P3/P4/contract totals). NOT returned to the PM surface.
  created_at       timestamptz
  -- "open" finding = severity='blocking' and ok=false at the current review_payload_version
```

**Finance redaction (Important):** every finding carries a **PM-safe `message`** (never dollars) and an optional **finance-only `diagnostic_detail`** (may carry P3/P4/contract figures). The operations-web/PM response returns only `{code, severity, ok, message}`; `diagnostic_detail` is withheld from the PM review surface (a future finance surface may expose it). This keeps the D7 firewall intact even though reconciliation reasons about money.

Immutability (trigger `trg_intake_run_immutable`, **BEFORE INSERT OR UPDATE**): `canonical_payload_json`, `source_format`, `payload_schema_version`, `parser_version`, `uploaded_by`, **`project_number`** are write-once; `approved_by`/`approved_at` set-once at approve. The **approval shape is enforced on insert too** — `approved_by`/`approved_at` set together, and `status='approved'` IFF `approved_by` is set — so a direct insert cannot fabricate an `approved` run with a null actor.

### 5.2 DB guards + task idempotency key (D1 + Important)

The schema lets `apparatus.task_id` point at a task in a **different** scope, `apparatus.scope_id` is immutable (`trg_apparatus_scope_immutable`, `001`), but `tasks.scope_id` is not, and **`ops.tasks` has no intake idempotency key** (003 covers scopes/quote_lines/apparatus, not tasks). 007 adds:
- **`trg_apparatus_task_same_scope`** (`before insert or update on ops.apparatus`): if `new.task_id is not null`, require `(select scope_id from ops.tasks where id = new.task_id) = new.scope_id`, else `raise exception`.
- **`trg_task_scope_immutable`** (`before update on ops.tasks`): reject changes to `tasks.scope_id` once the row exists. Keeps the task→scope binding stable so the apparatus guard cannot be defeated by moving the task.
- **`uq_ops_tasks_intake`** — `create unique index ... on ops.tasks (scope_id, legacy_source_id) where legacy_source_id is not null`. **Stable section key:** `tasks.legacy_source_id = <section>` (the bold-header section text within the scope; unique within a scope). Prevents retry/re-approval task duplication, matching the 003 pattern for scopes/lines/apparatus.

### 5.3 Minimal source columns (D2)

Add to `ops.projects` (marked source-derived, **not** canonical CRM):
- `source_client_name text null`
- `source_site_name/address/city/state/zip text null`
The full client/site/contact set is retained in `intake_runs.canonical_payload_json` / `intake_source_files`. No client/site/contact tables.

## 6. The package — `ops-intake` generalization

### 6.1 Parse → envelope (NO operational writes)
- De-Miner-ize: source identity comes from the run, not `_SOURCE`/`'project-miner'` literals.
- Parser to macro-parity: `section`→task, client/site, metadata sheet, N4; `source_format` classification; size-cap + macro-free read (§4.1).
- New `envelope.py`: `create_run(dsn, *, uploaded_by, filename, raw_bytes, content_type) -> run_id` — parse → classify → persist `intake_runs` (canonical==review payload v1) + `intake_source_files` (sha256) + `intake_validation_findings`. **Touches only envelope tables.**
- **No domain writes** before approve: parse/validate/persist-envelope never INSERT/UPDATE `ops.projects|scopes|tasks|apparatus|scope_quote|scope_quote_line`.

### 6.2 Review/edit
- `validate_payload(review_payload) -> Check[]` (the 3 existing checks + N4 reconciliation + format) computed against the **review** payload at its version; re-persisted as findings at the new `payload_version` on each review edit (each finding split into `message` + `diagnostic_detail`).
- Edits permitted on the review payload: task rename/regroup, **move a LINE between tasks within a scope**, edit `hrs_per_unit`. **Forbidden: move a line across scopes** (Law 1) and any other mutation. Enforced by a **default-deny allowlist diff against canonical** (`_assert_review_within_allowlist`): same `project_number`, same scope-name set, the **exact same `line_uid` multiset** (no add/delete/duplicate); each review line is matched to its canonical line **by `line_uid`** (not position), and per line **only `section` + `hrs_per_unit` are mutable** (qty/apparatus_type/test_standard/line_number pinned); at the scope level **every `scope_quote` field** must equal canonical — the 4 dollar categories AND `unit_multiplier`/`pct_adjust`/`total_quoted_hours`/`is_estimate` (M4/N4/J3 drive `blended_rate=P4/J3`); every project field pinned — plus the `line_uid`-keyed cross-scope guard. So approve can never materialize a doctored basis. Project/site metadata is read-only (persisted at approve); apparatus are the QTY-expansion at approve and are never individually edited.

### 6.3 Approve — the only domain writer (D6 identity-gated; full-replacement materialization)
`approve_run(dsn, run_id, *, approved_by) -> ApproveResult`, transactional. **Lock order: advisory(`project_number`) → intake_run row → project → apparatus** — matches `create_run`'s order (advisory **before** the run row), which is what prevents the create-vs-approve deadlock:
0. `SELECT project_number FROM ops.intake_runs WHERE id=run_id` (NO lock), then `pg_advisory_xact_lock(hashtext(project_number))`, **then** `SELECT ... FROM ops.intake_runs WHERE id=run_id FOR UPDATE` and re-read status. Without advisory-before-run-row, approve could hold the run row while waiting on the advisory lock that a concurrent `create_run` holds while waiting to supersede (lock) that very run row → deadlock. Also serializes concurrent approves of the same run.
1. Re-validate the current `review_payload`; **refuse (422) if any `blocking` finding is open** (incl. N4 reconciliation).
2. Refuse (409) if `status != active` (not in `parsed`/`reviewing`) — e.g. a stale/superseded run (§6.4).
3. Refuse (409) if `status = revision_blocked` (D5).
4. With the advisory lock already held (step 0), upsert+`SELECT ... FOR UPDATE` the project row (create if new), then **`SELECT id FROM ops.apparatus WHERE <project> FOR UPDATE`** — so an in-flight Chip-3 `approve_and_recognize` (which locks apparatus rows, NOT the project) serializes and its event becomes visible to the re-check. **Re-check conflict under the lock** (frozen / **any** `revenue_recognition_event` exists / any `billing_application`) — if a conflict now exists that did not at `create_run`, **commit the `status='revision_blocked'` transition and RETURN that outcome** (the API maps it to 409); **do NOT raise-and-rollback** (a raise undoes the status write). This closes the create→approve TOCTOU; the `005` FK is the final backstop, so even an un-serialized interleaving **fails safe** — the delete aborts on the FK rather than dropping a recognized row.
4b. **Foreign-source guard:** if the project bears any scope with `source IS DISTINCT FROM 'ops-intake'` (e.g. legacy Miner rows stamped `miner_rev10.xlsm`), abort **409** — intake will not manage a project it does not own (prevents the marker-scoped delete from orphaning foreign rows). See §12.4.
5. **Full replacement of intake-owned children**: `DELETE` the project's **intake-owned** scopes (`source='ops-intake'` — the materialize step stamps this exclusive owner marker on every row it writes; NOT the generic `legacy_source_id`, which is a per-row key) → cascades tasks/scope_quote/scope_quote_line/apparatus → then `INSERT` fresh from the review payload, creating **tasks** from `section` (with `legacy_source_id=<section>`) and linking `apparatus.task_id`. Guarantees **no stale rows** for re-intake of an unfrozen project; safe because steps 3–4 guarantee no recognition/billing FK references exist. Project row updated in place (stable `project_id`).
6. Freeze: set `scope_quote.is_frozen/frozen_at`, compute `apparatus.quoted_revenue = round(quoted_hours × blended_rate, 2)`, `provenance_status='approved'` — **project-scoped** (never touches other projects).
7. Set `intake_runs.status='approved'`, `approved_by/at`, link `project_id`.
- **Removes upload-driven `standard_hours` mutation** (D4): the catalog is not written by intake at all.

### 6.4 Revision detection, refusal, and supersede lifecycle (D5 + Important)
At `create_run`, within the same txn (take `pg_advisory_xact_lock(hashtext(project_number))` first so concurrent uploads of the same project serialize and the supersede sees committed prior runs; a residual `uq_intake_one_active` violation maps to **409**, never a raw 500), **parse and classify FIRST, then supersede only if the new run is itself approvable-active**:
1. **Parse + classify** — determine the new run's resulting status:
   - **`rejected`** if `source_format ∈ {flat_quote, unsupported}` (§4.1).
   - else look up `ops.projects` by `project_number`:
     - **none** → `conflict_kind='none'`, status `parsed`.
     - **exists, no frozen scope_quote, NO `revenue_recognition_event` row for the project, no billing** → `conflict_kind='none'`, status `parsed` → updatable at approve via the §6.3 full replacement.
     - **exists AND (any `scope_quote.is_frozen` for its scopes, OR ANY `ops.revenue_recognition_event` EXISTS for the project, OR any `ops.billing_application` for `project_id`)** → `conflict_kind` = `billed` > `recognized` > `frozen` (most-downstream wins), `status='revision_blocked'`, persisted as a **proposed revision**, **operational writes refused**, diff surfaced. **No automated reverse/supersede.**
2. **Supersede — only if the new run is approvable-active** (its status is `parsed`/`reviewing`): set any prior **active** runs (`status in ('parsed','reviewing')`) for the same `project_number` to `superseded` (DB-backstopped by `uq_intake_one_active`). A `rejected` or `revision_blocked` new run is **recorded without displacing the current active draft** — an accidental bad upload never strands a good draft.

**`recognized` is membership, not balance** (Important): the conflict is **any `revenue_recognition_event` row EXISTING** for the project, **not** `net > 0`. The ledger is append-only with hard FKs to apparatus/scopes/projects (`005`); a recognized-then-fully-reversed apparatus nets 0 but its event rows persist and still reference the very rows the §6.3 full-replacement delete would remove. So *any* historical recognition makes the project a revision (and the FKs protect those rows from deletion).

## 7. The control-plane API (host-gated)

Routes register **only when `OPS_DEV_DSN` is set** (env-gated like the learning routes; absent on the prod Render deploy → no 500ing routes). All calls require an `actor_person_id` resolvable to `ops.persons`.
- `POST /api/v1/ops/intake` — multipart `.xlsm`/`.json` (size-capped) → `create_run` → `{run_id, status, conflict_kind, preview_tree, findings}`. Findings carry **PM-safe `message` only** (no `diagnostic_detail`). **No domain writes.**
- `GET /api/v1/ops/intake/{run_id}` — run + `review_payload` tree + findings (PM-safe).
- `POST /api/v1/ops/intake/{run_id}/review` — edit the **review payload only** → bump version → re-validate → new findings. Cross-scope **line** moves rejected 4xx. 409 if the run is not active. **(POST not PATCH** — the global CORS allows only GET/POST/OPTIONS, so PATCH is preflight-blocked.)
- `POST /api/v1/ops/intake/{run_id}/approve` — identity-gated `approve_run`. 409 if `revision_blocked` or not-active/superseded; 422 if open blocking findings.
- `POST /api/v1/ops/intake/{run_id}/reject` — record `rejected` + reason.

## 8. The UI — operations-web

A new intake surface (against the host control-plane API → `ops_dev`):
1. **Upload** — drop the `.xlsm`; show parse result + `source_format` + findings (**PM-safe `message` only**).
2. **Review tree** — scope → task → **line** (apparatus = QTY-expansion at approve, shown read-only), editable task groupings and `hrs_per_unit`, inline findings, run status. Cross-scope moves not offered.
3. **Approve** — identity-gated; disabled while blocking findings are open or `revision_blocked` (shows the conflict + diff).
- **D7 firewall:** the review/approve surface shows **structure, hours, validation, status — no dollars.** `quoted_revenue` is computed at approve and lives behind the finance gate; finding money values live only in the withheld `diagnostic_detail`.
- Branding from `resa-complete-theme.json`.

## 9. Laws & invariants honored
- **Law 1** (scope→apparatus fixed): no cross-scope **line** moves (lines carry the apparatus); the guard keys on `line_uid`, and the 007 task-scope guard backstops it in the DB.
- **Law 3** (recognition firewall): no dollars in review (findings finance-redacted); `quoted_revenue` materialized only at approve; the `005` frozen-basis immutability triggers are respected (intake never mutates a frozen project — it refuses).
- **No operational writes before approve** (the central new invariant).
- Identity (`ops.persons`) on `uploaded_by` + `approved_by` (D6).
- **Single active approvable run per `project_number`** (supersede lifecycle).
- **Lock order** (deadlock-free, DAG-verified across Chips 3/4/5): `advisory(project_number) → intake_run → billing_application → project → recognition_event → apparatus`. `create_run` and `approve_run` both take the project advisory lock **before any row lock**.

## 10. Testing matrix (TDD, throwaway `ops_test`; `ops_dev` for operator review only)

Migration + package + API tests pin `OPS_DEV_DSN` at `ops_test` (the fixture truncates/down-nukes). Required cases:
- **No operational writes before approve** — parse + review-edit leave `ops.projects|scopes|tasks|apparatus|scope_quote|scope_quote_line` row-counts unchanged; only envelope tables grow.
- **Task-scope guard** — cross-scope `apparatus.task_id` rejected; `tasks.scope_id` change rejected once the row exists.
- **Task idempotency** — re-approval / retry does not duplicate tasks (the `uq_ops_tasks_intake` key holds; `legacy_source_id=<section>`).
- **Full-replacement materialization** — re-intake + approve of an unfrozen project removes scopes/tasks/lines/apparatus dropped from the new payload (no stale rows); count matches the new payload exactly.
- **Supersede lifecycle** — a second *approvable* upload for the same `project_number` sets the prior active run `superseded`; only one active run; approving the stale/superseded run → 409. **A `rejected`/`unsupported` or `revision_blocked` upload does NOT displace the current active draft** (the good draft stays the single active run).
- **Frozen-project revision refusal** — re-parse of a frozen/recognized/billed project → `status=revision_blocked`, `conflict_kind` correct, **zero domain writes**, approve 409.
- **Recognition is EXISTS, not net** — recognized → fully reversed (net 0) → no billing **still** yields `revision_blocked` / `conflict_kind=recognized` (the append-only event rows persist with FKs to the apparatus/scopes).
- **Recognition/billing conflict classification** — `frozen`-only vs `recognized` vs `billed` each classified correctly (billing checked independently of recognition).
- **Approve-time conflict re-check (TOCTOU)** — a run created clean (`parsed`) whose project becomes frozen/recognized/billed before approve → approve aborts 409 + marks `revision_blocked` (no delete attempted).
- **N4 parity** — `.xlsm` N4 parsed and totals reconcile; JSON default-1 emits an `info` fidelity finding (non-blocking); when default-1 breaks reconciliation, a `blocking` finding blocks approve.
- **Findings finance-redaction** — the PM/API response contains `message` but **never `diagnostic_detail`**; no dollar value appears in any PM-surface finding field.
- **Route guard disabled when `OPS_DEV_DSN` absent** — import-isolated subprocess proves the intake routes do not register.
- **Identity-gated approve** — approve requires a valid `ops.persons` actor; the FK is enforced.
- **Source-format rejection** — `unsupported`/`flat_quote` → `rejected` run + boundary finding, no materialization.
- **Full e2e** — upload a decomposed workbook → review/edit (regroup a task, override an `hrs_per_unit`) → approve → `ops.*` materialized with tasks + `apparatus.task_id` set + frozen quote; Σ apparatus quoted_revenue == scope P4.
- **Size cap / macro-free** — an over-cap upload is rejected; the parser reads cached values without executing VBA.
- **Real payload carries `line_uid`** — `asdict(extract_workbook(...))` lines all carry a unique `line_uid`; the cross-scope guard keyed on `line_uid` rejects a move (not a no-op).
- **Foreign-source refusal** — approve of a `project_number` carrying any `source<>'ops-intake'` scope (legacy Miner) → 409, zero deletes; foreign rows survive.
- **Approve-time TOCTOU (mandatory)** — a clean `parsed` run whose project is frozen/recognized/billed between create_run and approve → approve 409 + `revision_blocked`, domain counts unchanged (no partial delete).
- **Recognition race vs approve** — an in-flight `approve_and_recognize` on the project's apparatus serializes (apparatus `FOR UPDATE`); approve aborts cleanly, never a raw FK 500.
- **Two-project apparatus key** — approving two distinct projects sharing a `scope_name` does not collide on the GLOBAL `uq_ops_apparatus_intake` (apparatus key is project-qualified).
- **`create_run` concurrency** — two racing uploads of one `project_number` → exactly one active run; a genuine race maps to 409, never a raw `UniqueViolation`/500.
- **Null-section idempotency** — re-approving a `section=None` line does not grow the task count (`__ungrouped__` fallback is stable).
- **conftest guard fires** — a non-`ops_test` DSN makes `_dsn()`/`clean_ops` raise before any TRUNCATE.
- **Metadata persisted** — after approve, `ops.projects.source_client_name/source_site_*` are populated from the review payload.
- **Review-payload allowlist** — `patch_review` rejects a qty/apparatus_type/test_standard/scope-dollar/`project_number` tamper and any added/deleted/duplicated `line_uid`; it accepts a `section` (task regroup) + `hrs_per_unit` edit.
- **create-vs-approve no deadlock** — a two-connection regression: `create_run` (holding the project advisory lock, about to supersede) vs `approve_run` (acquiring advisory before the run row) completes without a deadlock error.
- **Direct-insert approval shape** — a direct `INSERT` of `status='approved'` with null `approved_by`/`approved_at` is rejected by the BEFORE-INSERT trigger; `project_number` cannot be UPDATEd.
- **DOWN** — `007_down` removes 007 objects; `001`–`006` schema + any data intact.

## 11. Housekeeping (part of "done")
- Fix SSoT `00-MASTER-INDEX.md` §6/G6 + §7 (extractor exists; Chip 5 = envelope/lifecycle/UI), add a **D-OPS** decision row (parse/envelope/approve separation · no-writes-before-approve · revision-refusal incl. billing · N4 mandatory for `.xlsm` · supersede lifecycle · full-replacement materialization · findings finance-redaction).
- MANIFEST row 007.
- RESUME_HERE + `project_ops_pm_lane` memory at the merge checkpoint.

## 12. Resolved decisions (operator review #2)
1. **Raw artifact retention** — **keep** `intake_source_files.raw_bytes` for Chip 5 (re-parse + chain-of-custody). Enforce a **size cap** (default 25 MB) at the boundary; `sha256` is the dedupe/identical-re-upload signal; **never execute macros** (data-only read).
2. **`flat_quote`** — **reject** (lacks the apparatus decomposition the recognition grain needs).
3. **Unfrozen existing project** — **update in place at approve via full replacement** of intake-owned rows under a project lock (§6.3): delete intake-owned children (cascade) and re-materialize, so removed scopes/tasks/lines/apparatus do not accumulate as stale rows.
4. **Legacy Miner coexistence** — the existing `ops_dev` Miner rows carry `source='miner_rev10.xlsm'`, not `'ops-intake'`. They are treated as **frozen / out-of-Chip-5-lifecycle**. Approve **refuses (409)** any project bearing non-`'ops-intake'` rows (§6.3 step 4b) rather than risk the marker-scoped delete orphaning them; there is **no automatic backfill/restamp** (a deliberate restamp migration is a separate, later decision if the live Miner project is ever brought into the intake lifecycle).
5. **Line identity** — the cross-scope guard and materialize idempotency key on a parse-time, scope-independent **`line_uid`** on each payload line (minted at extract, e.g. `{scope}:row{n}`), which is distinct from the DB-synthesized `scope_quote_line.legacy_source_id`. (Resolves the false-green where the guard keyed on a `legacy_source_id` absent from payload lines.)
