# Estimator `EstimateEnvelope` → `ops.*` Field-Mapping Packet

**Lane:** `estimator/envelope-ops-mapping` (off `main @ 36eeb15b`)
**Date:** 2026-06-24
**Status:** Contract artifact for operator ratification → then `writing-plans` for the first build slice. **Nothing applied to `ops_dev`; nothing on prod.**

## Provenance (both sides verified)

- **Estimator side (the contract):** pinned read-only snapshot at `./_pinned-estimator-core/` — verbatim bytes of `jasonlswenson-sys/estimator-ui-staging` @ `c051c0229aea0bd6fc3f79571ade17eb0348f1b6` (short `c051c02`), `packages/estimator-core/src/{schema,catalog,pricing}`. Cite these files, not the Windows working copy.
- **Writer side (the target):** live `ops_dev` (`apex-dev-pg`, PG17) grounded 2026-06-24 — `approve.py`/`load.py`/`catalog.py` in `packages/ops-intake/src/ops_intake/` + `information_schema` column inventory. Object names below are **as they exist live**, not as prior docs named them.

## Decisions locked (operator, 2026-06-24)

| # | Decision |
|---|---|
| D1 | **β — one writer, one *versioned canonical materialization input*.** `approve_run` stays the sole `ops.*` writer; the envelope is pivoted into a schema-versioned canonical payload (default-deny on unknown fields), not a loosely "widened" `review_payload`. |
| D2 | **cents → numeric dollars at the writer boundary, using `Decimal`** (never float) + `±1¢` reconciliation tests. |
| D3 | **catalog-only v1**, **fail closed** on `custom_equipment`, `service`, `cost`. |
| D4 | **additive migration first** — `quote_version`/`content_hash`/`source_kind`/`envelope_id`/`source_draft_id`/`source_revision_id` become first-class `ops.intake_runs` columns + a partial-uniqueness strategy. |
| D5 | **author + build in `apex-power-ops-platform`** (where `approve_run`, the migrations, and `ops_dev` tests live). |

**First build slice (named):** *"native catalog `EstimateEnvelope` approval into the existing ops-intake materializer."* Service/cost grain-widening (4b.3) and custom catalog-requests (4b.4) are explicit **later** slices. **Prod apply stays parked behind the `ops_app` role-boundary gate.**

---

## Instance Review Corrections (pre-plan — BLOCKING)

Folds the Codex cross-engine pass + operator review + the one salvageable Claude-IRP finding. **These OVERRIDE the body sections below where they conflict; `writing-plans` consumes THIS section as the source of truth.** Review provenance: Codex `apex-jobs review-run` (on-target, C1–C3); operator review (C4–C6); Claude-side IRP **misfired** (audited `@apex/estimator-core`, not this packet) — only C7 salvaged. Claude-side packet audit not obtained (re-runnable). All claims grounded against live `ops_dev` 2026-06-24 + the ops-intake writer.

- **C1 [High] — `source_format` enum lacks `'native'`.** Live `ops.intake_source_format` = `{decomposed_scope_sheet, flat_quote, unsupported}`; `'native'::ops.intake_source_format` would fail before any native run persists. D4 MUST `ALTER TYPE ops.intake_source_format ADD VALUE 'native'`. Key the partial-unique indexes on `source_format='native'` and **drop the redundant `source_kind` column** (resolves Q-1). Down-path: `ADD VALUE` is irreversible in place → the down migration must (a) `RAISE` if any `intake_runs.source_format='native'` rows exist, then (b) rebuild the type (new type without `'native'` → `ALTER COLUMN … TYPE … USING` → drop/recreate dependents). Test both directions.
- **C2 [High] — canonical/review shape must match `patch_review`.** `patch_review` (`envelope.py:190`) compares `review_payload_json` vs `canonical_payload_json` as the **same flat `IntakePayload`** (`_payload_from_dict` + `_assert_review_within_allowlist` + `_assert_no_cross_scope_move`). So the native pivot target IS the existing flat `IntakePayload` dict (catalog-only), written to **both** `canonical_payload_json` and `review_payload_json`; the raw `EstimateEnvelope` goes in a **new `estimate_envelope_json jsonb` column** (audit sidecar). This keeps `approve_run`, the allowlist, and the cross-scope guard working unchanged. **Supersedes §2's "canonical = raw envelope."** `payload_schema_version='estimate_envelope_v1'` selects only the added §3 native field-guards.
- **C3 [High] — null `project_number` must reject.** `EstimateEnvelope.project_number` is nullable but routes to `intake_runs.project_number`/`projects.project_number` (both `NOT NULL`) and the `pg_advisory_xact_lock(hashtext(project_number))` key. Add §3 reject **`missing_project_number`** (blocking finding) at the pivot/validator, before any DB write. (`JobNumberResolver` stays deferred; this is the governed fail-closed until it lands.)
- **C4 [High] — new identity columns must be immutable.** `trg_intake_run_immutable` (verified) blocks UPDATE drift on `{canonical_payload_json, source_format, payload_schema_version, parser_version, uploaded_by, project_number}`. D4 MUST add `envelope_id, quote_version, content_hash, source_draft_id, source_revision_id, estimate_envelope_json` to that `IS DISTINCT FROM` block (write-once). Tests assert UPDATE-drift on each raises.
- **C5 [Med] — native required-field guards.** §3 gains governed blocking findings (not downstream `KeyError`/`NOT NULL`) for catalog lines missing `equipment_model_ref` / `base_qty` / `project_intake_qty` / `resolved_ref_hours`, or with an invalid `included`/`line_kind` combination. Codes: `missing_required_catalog_field`, `invalid_line_state`.
- **C6 [Med] — `content_hash` trust boundary.** The server MUST recompute `content_hash` from a deterministic canonical serialization and verify it equals the envelope's `content_hash` before using it as the idempotency key; reject on mismatch (`content_hash_mismatch`). Never trust a client-supplied hash for the uniqueness index.
- **C7 [Med] — M4-baked block-cents basis (salvaged Claude-IRP F2).** estimator-core bakes M4 into block-level `*_cents` (`compile.ts:106`: `onsite_labor_cents` = M4 × pre-M4), but the workbook P14 is pre-M4 (`WORKBOOK_CHARACTERIZATION:35`). v1 is correct **only because M4==1** (post==pre). §6/§8 must state the cents→numeric mapping assumes M4==1; the **4b.2 (M4>1)** slice must reconcile the envelope's M4-baked block cents against ops' per-line-hours × apparatus-count × rate (which re-applies M4 via QTY expansion — double-M4 risk). Do not treat `onsite_labor_cents` as the workbook P14 in any finance reconciliation.

**Build-plan deltas (for §11):** the migration slice now also = `ADD VALUE 'native'` (+ rebuild down) · drop `source_kind` · add `estimate_envelope_json` · extend `trg_intake_run_immutable` + drift tests; the validator slice adds reject codes `missing_project_number`, `missing_required_catalog_field`, `invalid_line_state`, `content_hash_mismatch`; the pivot writes the flat `IntakePayload` to canonical+review with the raw envelope in the sidecar; the server recomputes `content_hash`.

**Logged separately (NOT this packet):** estimator-core hardening — F3 (`compile()` `RangeError` on non-integer M4), F4 (`allocateByLargestRemainder` wrong sum on negative weights), F1 (overstated "reproduces the workbook" corpus claim). Tracked on the `estimator-ui-staging` lane.

---

## §1 — The seam is a 3-layer pivot

```
EstimateEnvelope (estimator-core, immutable compiled value)
   │   ── PIVOT (this packet): the versioned canonical materialization input
   ▼
ops.intake_runs.review_payload_json  (+ source_format='native', payload_schema_version='estimate_envelope_v1')
   │   ── approve_run(dsn, run_id, approved_by)   [the SOLE ops.* writer]
   ▼
ops.projects · ops.scopes · ops.scope_quote · ops.scope_quote_line · ops.tasks · ops.apparatus
```

`approve_run` does **not** consume the envelope object directly. It reads `ops.intake_runs.review_payload_json` (persisted at `create_run` time) and `materialize()`s it. So the native estimator path must (a) **compile** the selected revision to an `EstimateEnvelope`, (b) **pivot** it to the canonical payload + persist an `intake_run` row, (c) call the existing `approve_run`. The pivot is the deliverable; the writer is reused unchanged except for the additive columns (§4) and the fail-closed gate (§3).

### Invariants `approve_run` already enforces (the packet binds *into* these — it does not re-implement them)

- **Lock order** `advisory(project_number) → intake_run row → project → apparatus` (matches `create_run`; deadlock-free). *(`approve.py:` `approve_run`.)*
- **Full-replacement** materialization: deletes only this project's `source='ops-intake'` scopes (cascade), never foreign rows. *(`materialize` / `_SOURCE`.)*
- **Approve-time TOCTOU re-check** → `revision_blocked` if billed / recognized / frozen. *(`_conflict_kind`, `_block_to_revision`.)*
- **Foreign-source guard** → `foreign_source` if any scope of the project is not intake-owned.
- **Strict M4 gate** (`m4_ok` → `Decimal('1')` exactly) + **resolve-all-or-reject** via `core.v_equipment_models_resolved` (`resolve_models`), both emitting **blocking findings** (PM-`$`-safe via `_pm_safe`).
- **Quote freeze**: `apparatus.quoted_revenue = round(quoted_hours × scope.blended_rate, 2)`, `scope_quote.is_frozen`, `provenance_status='approved'`. `blended_rate` is a **GENERATED** column — read, never written.

---

## §2 — D1 β: the versioned canonical materialization input

The hooks already exist on `ops.intake_runs` (no new payload plumbing needed):

| existing column | native use |
|---|---|
| `source_format` (enum) | add value `'native'` (workbook path keeps its existing value) |
| `payload_schema_version text NOT NULL` | `'estimate_envelope_v1'` — the version that selects the **envelope-shaped** validator |
| `review_payload_json jsonb NOT NULL` | the canonical materialization input (envelope → payload, §5–§7) |
| `canonical_payload_json jsonb NOT NULL` | the **un-pivoted** compiled `EstimateEnvelope` (audit/idempotency source) |
| `review_payload_version integer NOT NULL` | per-run finding-version cursor (unchanged) |

**Default-deny:** the `estimate_envelope_v1` validator rejects unknown top-level/line keys (a workbook-era field appearing in a native payload is a hard validation error, not a silent ignore). The existing flat-apparatus validator is **not** widened in place — it is selected by `payload_schema_version`, so the two contracts never blur.

---

## §3 — Fail-closed v1 gate (catalog-only) — REJECT MATRIX

The native pivot/validator MUST reject (blocking finding, PM-`$`-safe, no `ops.*` rows written) when **any** of the following hold. These run in/alongside the existing precheck, **before** `materialize`:

| code | condition | why it cannot materialize today |
|---|---|---|
| `non_catalog_line` | any `LineC.line_kind != 'catalog'` (incl. `custom_equipment`, `service`, `cost`) | `scope_quote_line.apparatus_type` is `NOT NULL`; no `line_kind`/`unit_kind` column; no service sibling object; no `ops.catalog_requests` |
| `nonzero_service` | `ScopeC.scope_totals.service_cents != 0` or any `service_hours != 0` | no service recognition grain (4b.3) |
| `nonzero_cost` | `ScopeC.scope_totals.cost_cents != 0` (→ would map to `travel`/`outside_services`) | `outside_services` feeds the **generated** `blended_rate`; cost lines need 4b.3 |
| `m4_unsupported` | `ScopeC.replication_m4 != 1` (via `m4_ok`) | M4≠1 materialization deferred to 4b.2 |
| `uncatalogued_apparatus` | any catalog line whose `equipment_model_ref` model-key does not resolve **terminal-active** | `resolve_models` would drop it → `materialize` `KeyError` |
| `unresolved_provisional` | any `provisional_token` present / `equipment_model_ref` null | custom mint-at-approve is 4b.4 |

Rejecting on `nonzero_service`/`nonzero_cost` at the **totals** level (not just line presence) is deliberate: it fail-closes even a malformed payload that zeroes out its service/cost *lines* but carries nonzero service/cost *totals*.

---

## §4 — D4: additive migration (must land before the writer slice)

`ops.intake_runs` today has **none** of the envelope identity/version fields first-class. Additive-only migration (new nullable columns; backfill not required for existing workbook runs):

```sql
-- ops migration NNN (additive; ops_test → operator-gated ops_dev; prod parked)
alter table ops.intake_runs
  add column envelope_id        text,
  add column source_kind        text,        -- 'native' | 'workbook_intake' (mirrors envelope.source_kind)
  add column quote_version       integer,
  add column content_hash        text,
  add column source_draft_id     text,
  add column source_revision_id  text;

-- idempotency: same compiled envelope ⇒ same run (native only)
create unique index uq_intake_runs_content_hash_native
  on ops.intake_runs (content_hash)
  where source_kind = 'native' and content_hash is not null;

-- quote-version uniqueness per project (native only; supersede = new version, full-replace)
create unique index uq_intake_runs_proj_quote_version_native
  on ops.intake_runs (project_number, quote_version)
  where source_kind = 'native' and quote_version is not null;
```

Notes:
- **Partial** indexes (`where source_kind='native'`) so existing/ongoing workbook runs are untouched — they carry NULLs in these columns and never collide.
- `source_kind` is distinct from the existing `source_format` enum: `source_format` is the upload *mechanism*; `source_kind` mirrors `envelope.source_kind` and is what the partial indexes key on. (Open Q-1 below: collapse vs keep both.)
- `quote_version` here is the integer audit/uniqueness key; `ops.projects.quote_revision` (existing `varchar`) may carry `str(quote_version)` for display but is **not** the uniqueness anchor.
- Supersede semantics reuse the existing **full-replacement** behavior: a higher `quote_version` for the same `project_number` produces a fresh run; `re_bid_supersede` is recorded by the version bump, not a new mutation path.

---

## §5 — Header mapping: `EstimateEnvelope` → `ops.projects` + `ops.intake_runs`

| envelope field | → target | rule / note |
|---|---|---|
| `project_number` | `projects.project_number` (conflict key) + `intake_runs.project_number` | canonicalized; the advisory-lock anchor |
| `totals.bid_cents` | `projects.contract_value` | `Decimal(cents)/100` (§8) — the commercial bid $ |
| `quote_version` | `intake_runs.quote_version` (+ `projects.quote_revision = str(...)`) | new (§4) |
| `envelope_id` | `intake_runs.envelope_id` | new (§4) |
| `content_hash` | `intake_runs.content_hash` | new (§4); idempotency key |
| `source_kind` | `intake_runs.source_kind` (`'native'`) + `source_format='native'` | new (§4) |
| `source_draft_id` | `intake_runs.source_draft_id` | new (§4) |
| `source_revision_id` | `intake_runs.source_revision_id` | new (§4); only the **selected** revision compiles |
| `pricing_card_version` | (provenance; → `intake_runs` or payload) | retained for audit; rates already baked into cents |
| `compiled_at` | (payload metadata) | informational |
| — | `projects.project_name` **NOT NULL** | **GAP (Q-2):** the envelope has no `project_name`. Source from the draft (`opportunity_ref`/estimate name) at pivot time, or require it on the native payload. Must not be null. |
| `job_number_source_ref` | (deferred) | `JobNumberResolver` contract is out of scope (spec §8.A.2). |

CRM columns (`source_client_name`/`source_site_*`) are **not** in the envelope → NULL on the native path (nullable; deferred).

---

## §6 — Scope mapping: `ScopeC` → `ops.scopes` + `ops.scope_quote`

`ops.scopes` (one row per envelope scope):

| `ScopeC` | → `ops.scopes` | rule |
|---|---|---|
| `name` | `scope_name` (NOT NULL) | |
| `scope_id` | `legacy_source_id` | stable scope identity for re-materialize idempotency |
| — | `scope_type` | default `'OTHER'` (envelope has no scope_type) |
| `neta_standard` | **no `scopes` column** | **fan out to each line's `scope_quote_line.test_standard`** (§7) — `neta_standard` is per-line in ops, per-scope in the envelope |

`ops.scope_quote` (1:1 with scope; money is `numeric` dollars; `blended_rate` GENERATED/read-only):

| source | → `scope_quote` | rule |
|---|---|---|
| `scope_totals.onsite_labor_cents` | `onsite_labor` | `Decimal(cents)/100` |
| `scope_totals.offsite_labor_cents` | `offsite_labor` | `Decimal(cents)/100` |
| `0` (fail-closed) | `travel` | v1 rejects nonzero cost; feeds generated `blended_rate` |
| `0` (fail-closed) | `outside_services` | v1 rejects nonzero cost |
| `replication_m4` (==1) | `unit_multiplier` | gated `Decimal('1')` by `m4_ok` |
| `adjustment_multiplier_n4` | `pct_adjust` | the N4 adjustment |
| `scope_totals.quoted_app_hours` | `total_quoted_hours` | seed value; then **maintained by the J3 line-hours trigger** as lines insert |
| — | `blended_rate`, `unadjusted_total`, `adjusted_total` | GENERATED/derived — never written; used for §8 reconciliation |

---

## §7 — Line mapping (catalog only): `LineC` → `ops.scope_quote_line` + `ops.apparatus`

Only `line_kind='catalog'`, `included=true` lines reach here (others rejected §3 / skipped). For each such line:

`ops.scope_quote_line` (one row per line; `apparatus_type` **NOT NULL**):

| `LineC` | → `scope_quote_line` | rule |
|---|---|---|
| `equipment_model_ref` (model-key string) | `apparatus_type` (NOT NULL) | the catalog model-key; **also** re-resolved to a uuid for apparatus (§9) |
| `ScopeC.neta_standard` | `test_standard` | scope→line fan-out |
| `base_qty` | `qty` (NOT NULL) | M4==1 ⇒ `qty == project_intake_qty` |
| `resolved_ref_hours` | `hrs_per_unit` (NOT NULL) | per-unit hours; `line_hours` is derived |
| `resolved_ref_hours` | `catalog_default_hours` | catalog reference (drift baseline) |
| `line_uid` | `legacy_source_id` | **stable bid→actuals join key** |
| — | `designation`, `line_number` | optional; from `LineC` ordering / null |

`ops.apparatus` — **QTY-expanded**: insert `project_intake_qty` rows (== `base_qty`, since M4==1), `i = 0 .. n-1`:

| source | → `apparatus` | rule |
|---|---|---|
| `f"{apparatus_type} {i+1}"` | `apparatus_designation` (NOT NULL) | matches existing `materialize` convention |
| `equipment_model_ref` model-key | `apparatus_type` | same model-key string |
| **resolved terminal-active uuid** | `equipment_model_ref` (uuid, required on live path) | from `resolve_models` (§9) |
| `resolved_ref_hours` | `quoted_hours` | per-unit; `quoted_revenue` set at freeze |
| `scope_quote_line.id` | `quote_line_id` | FK back to the quote line |
| `f"{project_number}:{line_uid}:u{i}"` | `legacy_source_id` | **project-qualified** unit identity (idempotent re-materialize) |
| `'Not Started'` | `status` | constant |
| — | `drawing_reference` | **GAP (Q-3):** envelope `LineC` has no `drawing` field → NULL on native path (workbook path supplies `line.drawing`) |

---

## §8 — Money boundary (D2)

- **One direction, one place:** integer cents → `numeric` dollars happens **only** at the pivot/writer boundary, using Python `Decimal` (never float): `Decimal(cents) / Decimal(100)`, quantized to 2 places.
- **No re-pricing in ops:** ops stores the converted dollars; `blended_rate`/`unadjusted_total`/`adjusted_total` are GENERATED. The envelope is the single rounding boundary (cents) per the spec's P14/P19/P26/P33/P4 cascade; ops inherits the already-rounded result.
- **±1¢ reconciliation (acceptance test):** after materialization+freeze, assert `abs(Decimal(envelope.totals.bid_cents)/100 − Σ scope.adjusted_total) ≤ 0.01` and per-scope `abs(Decimal(scope_totals.adjusted_cents)/100 − scope_quote.adjusted_total) ≤ 0.01`. A larger gap is a build defect (float leak or a mismapped basis), not a tolerance.
- **Full cents migration of `ops.*` money columns is deferred** (the live recognition/billing spine — Miner $4.69M — runs on `numeric` today). Recorded as the principled end-state; not in this slice.

---

## §9 — Identity & resolution

- `LineC.equipment_model_ref` is the catalog **model-key** (`EquipmentModel.ref`, a string), **not** a uuid. The native path:
  1. `scope_quote_line.apparatus_type ← model-key` (the existing column semantics: a string the resolver maps).
  2. **Re-resolve at approve** via `resolve_models([model-key]) → core.v_equipment_models_resolved (requested_model_key → resolved_id)` → terminal-active uuid → `apparatus.equipment_model_ref`.
- Re-resolving (rather than trusting an envelope-carried uuid) preserves the **TOCTOU** guarantee: a model deprecated/merged between compile and approve is caught here (`uncatalogued_apparatus` reject), identical to the workbook path. The schema-role invariant holds — the estimator never writes canonical identity; approve resolves it.

---

## §10 — Invariants honored / `line_uid` lineage

- **`line_uid` stability:** `line_uid → scope_quote_line.legacy_source_id`; apparatus units carry `f"{project_number}:{line_uid}:u{i}"`. This is the bid→actuals join key; it must survive re-materialize (full-replace re-derives the same keys from the same `line_uid`).
- **Advisory lock / supersede:** reuse `advisory(project_number)`; a new `quote_version` is a fresh run, full-replace (§4).
- **Service carve-out:** N/A in v1 (service rejected §3). When 4b.3 lands, service hours must **not** join `total_quoted_hours`/`blended_rate` (the sibling-object rule); recorded here so the later slice cannot regress it.
- **Idempotency:** equal `content_hash` ⇒ unique index collision ⇒ the run is not duplicated.

---

## §11 — First build slice (for `writing-plans`)

**"Native catalog `EstimateEnvelope` approval into the existing ops-intake materializer."**

Scope (TDD on `ops_test`, then operator-gated `ops_dev`):
1. **D4 additive migration** (§4) + its down-migration; partial-unique index tests.
2. **`estimate_envelope_v1` validator** + default-deny + the §3 reject matrix (each code unit-tested with a PM-`$`-safe finding).
3. **Pivot** `EstimateEnvelope` → canonical `review_payload_json` (§5–§7), `Decimal` money (§8).
4. **`create_run` native entry** persisting the run (`source_kind='native'`, `payload_schema_version='estimate_envelope_v1'`, `canonical_payload_json`=raw envelope).
5. **`approve_run` reuse** — confirm no writer change needed beyond reading the new columns; one `materialize` path.
6. **Acceptance:** a catalog-only Cupertino-shaped envelope → approve → assert exact `ops.*` row projection + `±1¢` reconciliation + idempotent re-run + every fail-closed reject.

Out of slice (later, explicit): 4b.2 M4≠1 · 4b.3 service/cost grain + Chip-4 guard · 4b.4 custom catalog-requests · full cents migration · `JobNumberResolver` · RLS/role-projection/redaction. **Prod stays parked behind the `ops_app` role-boundary gate.**

---

## §12 — Open questions for operator ratification

- **Q-1 `source_kind` vs `source_format`:** **RESOLVED (C1)** — add `'native'` to the `source_format` enum, key the partial indexes on `source_format='native'`, and drop the `source_kind` column (a `NOT NULL` enum already forces a value for native runs, so a second column is redundant).
- **Q-2 `projects.project_name` source** (NOT NULL; envelope has none): derive from the draft (`opportunity_ref`/estimate name) at pivot, or require it on the native payload? *Lean: pivot derives from the draft; validator rejects if absent.*
- **Q-3 `apparatus.drawing_reference`** (envelope `LineC` has no `drawing`): leave NULL for native v1, or add a drawing field to the line contract? *Lean: NULL for v1; revisit if estimators need it.*
- **Q-4 task grouping:** the envelope dropped `section` → native lines fall to one `__ungrouped__` task per scope. Accept for v1, or derive grouping from `designation`? *Lean: `__ungrouped__` for v1.*

## Appendix — grounding references

- Contract: `_pinned-estimator-core/schema/{envelope,draft,enums}.ts`, `catalog/types.ts`, `pricing/rate-card.ts` @ `c051c02`.
- Writer: `packages/ops-intake/src/ops_intake/{approve,load,catalog}.py` (`approve_run`, `materialize`, `_freeze`, `_conflict_kind`; `upsert_project`/`insert_scope`/`insert_scope_quote`/`insert_task`/`insert_scope_quote_line`/`insert_apparatus`; `resolve_models`/`m4_ok`).
- Live `ops_dev` columns: `ops.{intake_runs,projects,scopes,scope_quote,scope_quote_line,tasks,apparatus}`; `core.{equipment_models,v_equipment_models_resolved}`. Grounded 2026-06-24.
