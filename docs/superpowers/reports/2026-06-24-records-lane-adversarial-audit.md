# Records Lane Adversarial Audit - 2026-06-24

Status: adversarial review, not approval

Packaging status: records-specific review artifact on branch `codex/records-lane-audit-cleanup`. This version supersedes the earlier untracked report copy that was first placed in the estimator worktree.

Reviewer posture: assume the lane is promising but not final. This review looks for correctness gaps, product risks, operational risks, migration risks, and better paths forward. It does not treat current schema, packets, or plans as concrete.

## Scope And Evidence

Authoritative host access used:

- SSH over mesh: `olares-mesh`
- Consolidated target repo: `/home/olares/code/apex/apex-power-ops-platform`
- Records lane checkout: `/home/olares/code/apex/apex-records-lane`
- No repo copy to Windows was used for the audit.

Observed snapshot metadata:

This section is for reproducibility, not standing authority. Branch names and commit SHAs can drift. The durable authority claim for this report is narrower: the Olares platform checkout contains the consolidated records lane through migrations `001`-`044`, while the detached `apex-records-lane` checkout observed during review stops at `042`.

- `/home/olares/code/apex/apex-records-lane`
  - `HEAD`: `b6980b28e4ea69a3633b72a94ea7ae450f66c4ee`
  - State: detached HEAD, clean
  - Contains records migrations through `042`
  - Contains Chip 10c `.dtax` ingest work
- `/home/olares/code/apex/apex-power-ops-platform`
  - Initial audit snapshot: `9e26c789d2726a3f34c25135a4eeae8db71b2672`
  - Cleanup branch base observed later: `ed6b760d8c9941497d9a98fee36be2544fa2a836`
  - Initial active branch observed: `estimator/envelope-ops-mapping`
  - Cleanup branch: `codex/records-lane-audit-cleanup`
  - Contains `b6980b28`, `063ee8ba`, and `5ee2444b` by ancestry
  - Contains records migrations through `044`

Because the platform checkout contains the records-lane Chip 10c work plus later records migrations `043` and `044`, this report treats `/home/olares/code/apex/apex-power-ops-platform` as the consolidated audit target. The detached `/home/olares/code/apex/apex-records-lane` checkout is itself called out as a source-of-truth risk.

Key artifacts reviewed:

- `reference/records/00-MASTER-INDEX.md`
- `reference/records/01-OFFLINE-SYNC-ARCHITECTURE.md`
- `reference/records/02-LEGACY-BASELINE.md`
- `reference/records/14-CAPTURE-MODE-IMPORT-SPEC.md`
- `reference/records/PUNCHLIST.md`
- `infra/database/migrations/records/MANIFEST.md`
- Records migrations `001` through `044`
- `packages/records-import`
- `packages/power-test-converters`
- `apps/field-surface`
- `apps/operations-web/app/pm-review/durable-field-record-placeholder`
- `apps/mutation-seam` durable field record slice
- `reference/records/CURRENT-STATE.md`

## Validated / Not Validated

Validated in this pass:

- Focused parser/proposal/mapping tests passed:
  - `PYTHONPATH=packages/power-test-converters/src:packages/records-import/src .venv/bin/pytest packages/power-test-converters/tests/test_dtax_read.py packages/power-test-converters/tests/test_ptm_to_dtax.py packages/records-import/tests/test_smoke.py packages/records-import/tests/test_review_proposal.py packages/records-import/tests/test_ptm_transformer_mapping.py -q`
  - Result: `20 passed`
- This validates only the focused converter/import proposal surface covered by those tests.

Not validated by that test run:

- `records-import` DB write behavior
- records migration replay
- records RLS/grants or tenant/security posture
- PowerSync/offline capture and reconciliation
- import sessions, source hashes, reviewer decisions, or audit-grade import history
- idempotent source-file reimport semantics
- acceptance/tolerance resolver behavior

Not run:

- DB-backed migration/integration tests. Local Postgres was reachable on Olares, but the default password attempted from shell context failed. No `.env` or secret files were read to recover credentials.
- Bulk records migration replay, because the records manifest warns that some down/up paths and read-live migrations are order-sensitive and not safe as a casual whole-directory replay.

## Executive Verdict

The records lane has a coherent strategic spine: records are treated as an offline-first field substrate, not just office paperwork; forms are intended to be source-backed and provenance-aware; and import/review is correctly recognized as a trust boundary rather than a blind parser.

The implementation is not ready to be treated as final or production-governed. The highest risk is that the lane now has enough migrations, seeded templates, import code, and tests to look more complete than it is. Security posture, offline runtime proof, provenance depth, value typing, source-rights posture, import idempotency, and state-of-truth documentation are still open design surfaces.

Recommended stance: keep building from this foundation, but label it as prototype/foundation state until the gates in this report are closed.

## Severity Summary

P0:

- Source-of-truth and maturity state are split across the lane checkout, platform checkout, stale punchlist, and stale design docs.

P1:

- Records schema has no production security boundary yet.
- Runtime value model is narrower than the seeded templates and capture/import aspirations.
- Import write path does not yet meet the review, provenance, idempotency, or audit model described by the design.
- Offline-first architecture is well described but not proven end to end.
- Source-derived records/reference content needs an explicit restricted-source and redistribution posture before wider serving.

P2:

- `.dtax` support exists but is partial and should be represented as such.
- Unit normalization and instrument semantics need a first-class conversion contract.
- Template authoring and migration strategy are brittle.
- MTS template coverage is not the same as domain correctness.
- Acceptance/tolerance resolution is deferred but central to records value.
- PM durable field records can be confused with records-lane durable records.
- Several domain-model constraints are intentionally loose and need explicit lifecycle gates.
- Test posture is useful but underpowered for schema replay, RLS, offline sync, and import audit behavior.

P3:

- Documentation statuses are stale enough to cause planning mistakes.

## Findings

### P0 - Source Of Truth And Current State Are Split

Evidence:

- `/home/olares/code/apex/apex-records-lane` is detached at `b6980b28` and contains records migrations through `042`.
- `/home/olares/code/apex/apex-power-ops-platform` contains `b6980b28` plus records migrations `043` and `044`.
- `reference/records/PUNCHLIST.md` still says Chip 10b/10c are next, even though Chip 10c code and tests exist.
- `reference/records/14-CAPTURE-MODE-IMPORT-SPEC.md` still begins as design/not-built, while the same document also contains as-built notes for Chip 10a and the repo contains Chip 10c work.
- The platform repo's active branch name is `estimator/envelope-ops-mapping`, which does not communicate that it contains the current records union.

Why this matters:

The lane can now be read in at least three incompatible ways:

- The lane checkout says "through 042 plus Chip 10c."
- The platform checkout says "through 044 plus Chip 10c."
- The docs say "some of this is still next/design."

That is a real operational risk. A reviewer, implementer, or future Codex run could audit the wrong checkout, skip `043`/`044`, or treat deferred design as implemented behavior.

Recommendation:

- Add a short `reference/records/CURRENT-STATE.md` with:
  - authoritative checkout/branch/commit
  - latest records migration
  - implemented chips
  - intentionally deferred chips
  - "not production-ready until" gates
- Update `PUNCHLIST.md` and `14-CAPTURE-MODE-IMPORT-SPEC.md` statuses immediately.
- Either move the records-lane checkout forward to the platform union or explicitly mark it as a stale/detached lane worktree.

### P1 - Records Has No Production Security Boundary Yet

Evidence:

- Records migrations do not include RLS enablement or grants/revokes for the records tables reviewed.
- `043_neta_table_source_links.sql` explicitly omits RLS/grants.
- `044_person_anchor.sql` explicitly omits RLS/grants.
- Adjacent mutation-seam migrations do use RLS and revoke direct anon/authenticated access, proving the broader codebase already recognizes this as a required posture for governed surfaces.

Why this matters:

Records data includes field observations, job linkage, technicians, equipment, source references, and eventually attachments/imported instrument data. Without explicit RLS and grants, the schema is not ready for:

- Supabase exposure
- PowerSync sync publication
- browser-facing review UI
- direct operational writes
- cross-customer or multi-tenant deployment

The absence may be acceptable during schema shaping, but it must stay visibly gated. It should not be normalized as "we will add security later" once APIs or sync rules begin to land.

Recommendation:

- Add a lane-level security design before expanding runtime surfaces.
- Define least-privilege roles for:
  - server mutation seam
  - field sync reader/writer
  - office reviewer
  - admin/reference curator
  - auditor/read-only
- Add RLS tests that prove cross-site/customer isolation, technician visibility, reviewer visibility, and service-role bypass behavior.
- Keep `043` and `044` explicitly internal until policies exist.

### P1 - Value Model Is Narrower Than Templates And Product Intent

Evidence:

- `field_value_kind_enum` includes `numeric`, `boolean`, `text`, `selection`, and `graph`.
- Seeded templates include or imply field kinds such as `date`, `multiselect`, and `attachment`.
- `records.form_field_values` stores `value_numeric`, `value_text`, `value_boolean`, and `unit`.
- There is no `value_date`, `value_jsonb`, attachment reference, source-file reference, exactly-one-value constraint, or DB-level field-key/schema validation.

Why this matters:

The schema can accept today's minimal values, but the templates already describe richer forms than the value table can faithfully store. That mismatch creates several failure modes:

- A field looks valid in template JSON but has no durable representation.
- Import code may push data into `notes` or text fields because no proper column exists.
- Attachments can be designed into forms before attachment storage, sync, retention, and security are governed.
- Review UI can render controls that the persistence model cannot validate.

Recommendation:

- Introduce a value-model v2 before broadening template usage.
- Add explicit support for:
  - date/time
  - multi-select
  - structured JSON for domain-specific row values
  - attachment/file references
  - measured/corrected value pairs
  - source/import metadata
- Add a CHECK or trigger ensuring exactly one compatible value payload is present for each field kind.
- Add a template validator that fails CI when `field_schema` uses unsupported kinds.

### P1 - Import Provenance And Review Gate Are Not Yet Strong Enough

Evidence:

- The import spec calls for mandatory review before commit, source-file idempotency, measured vs corrected preservation, instrument metadata, serial/software/calibration details, correction factors, grade/assessment, and partial-fill marking.
- Current `records-import` proposal values contain only field key, optional test group, numeric/text value, unit, measured time, origin device, and notes.
- Current DB commit path upserts directly into `records.form_field_values` on `(form_submission_id, field_key)`.
- The DB commit uses autocommit and loops values one at a time, so a mid-import error can leave partial writes.
- The current persistence model has no import session table, source file identity, source hash, review decision table, revision model, or per-value provenance table.

Why this matters:

Import is a trust boundary. For test records, "this number came from a file" is not enough. The system must answer:

- Which source file produced this value?
- What parser version produced it?
- What instrument and calibration state produced it?
- Was the value measured, corrected, converted, or manually overridden?
- Who reviewed it?
- What changed on reimport?
- Can we reconstruct the proposal that was accepted?

The current code is useful as an ingestion prototype, but it is not yet an audit-grade import system.

Recommendation:

- Add `records.import_sessions` or equivalent:
  - source file name
  - source file hash
  - parser package/version
  - parser options
  - source format
  - instrument metadata
  - submitted by / reviewed by
  - review status
- Add `records.import_proposed_values`:
  - raw value
  - normalized value
  - unit conversion
  - confidence/status
  - mapping rule
  - accepted/rejected/edited state
- Add transaction-scoped commit behavior.
- Change idempotency from only `(submission, field_key)` to a model that includes source identity, proposal revision, and reviewer acceptance.
- Preserve overwrite history instead of silently replacing values.

### P1 - Offline-First Architecture Is Described But Not Proved

Evidence:

- `01-OFFLINE-SYNC-ARCHITECTURE.md` correctly states offline use is load-bearing.
- PowerSync is selected as the intended local-first substrate.
- Sync rules are sketched as asset subtree and acceptance-window buckets.
- The field surface app is explicitly a prototype with in-memory queue behavior.
- Punchlist still marks sync substrate and field PWA as TODO.
- The office durable-field-record placeholder explicitly avoids live mutation calls.

Why this matters:

The lane's defining product promise is not "a records schema exists"; it is "a field user can safely capture records offline and reconcile them later." That requires proof across:

- installable app shell
- local storage
- conflict detection
- upload transaction
- idempotency
- server validation
- retry behavior
- user-visible reconcile state
- attachment behavior

The current architecture is a good direction, but the runtime proof has not landed.

Recommendation:

- Build a single narrow offline proof before expanding form coverage:
  - one asset
  - one PM/form submission
  - one acceptance lookup
  - one offline capture
  - one sync upload
  - one stale edit conflict
  - one reviewer-visible result
- Test it with network disabled/enabled in an automated browser flow.
- Do not mark records lane as operational until this proof passes.

### P1 - Source-Derived Content Needs A Clear Restricted-Source Policy

Evidence:

- The lane seeds many standard-aware forms and reference rows.
- `043_neta_table_source_links.sql` is careful to avoid excerpts and stores source locator/provenance instead.
- Earlier migrations and templates still contain standard-derived labels, sections, and field schemas.

Why this matters:

The source-link approach in `043` is prudent, but it does not by itself settle the posture for already-seeded template content. The risk is not only legal; it is operational. The team needs to know what content can be:

- committed to repo
- served through APIs
- synchronized to field devices
- exported in reports
- shown in customer-facing UI
- distributed outside licensed users

Recommendation:

- Create a `reference/records/SOURCE_CONTENT_POLICY.md`.
- Classify each content type:
  - internal locator only
  - licensed internal reference
  - derived operational label
  - customer-visible report text
  - redistributable template metadata
- Add tests or scripts that prevent accidental excerpts where the policy forbids them.
- Keep `043` source links internal until RLS and content policy are both present.

### P2 - DTAX Support Exists But Is Partial

Evidence:

- `packages/power-test-converters` now reads `.dtax` into the PTM model.
- `records-import` exposes `propose_dtax`.
- The end-to-end `.dtax` test explicitly documents that only overall power-factor rows map through the existing records importer.
- TTR/WR rows are not mapped because measurement names are missing.
- Excitation rows are not mapped because phase labels arrive as `PhaseA`, `PhaseB`, and `PhaseC`, while the mapper expects `A`, `B`, and `C`.

Why this matters:

The existence of `.dtax` support can easily be overstated. It is not yet a general `.dtax` import path; it is a partial path that proves parser plumbing and one class of mapped values.

Recommendation:

- Label current `.dtax` capability as "partial proposal support."
- Add a mapping normalization layer between `PtmModel` and records fields:
  - phase aliases
  - blank measurement-name handling
  - winding/terminal derivation
  - row identity from structure, not only string names
- Add fixtures for realistic transformer `.dtax` files when available.

### P2 - Unit Normalization Is Under-Specified

Evidence:

- The PTM/DTAX converter normalizes some values into SI-like model units.
- Records import emits capacitance values with unit `F`.
- Records import emits excitation current values with unit `A`.
- Records templates commonly expect field units such as `pF` and `mA`.
- Existing tests prove current behavior, but not domain-correct presentation or acceptance comparison.

Why this matters:

Field records are only useful if values, units, tolerances, and display behavior agree. A number imported as `1e-12 F` can be mathematically equivalent to `1 pF`, but it may fail human review, tolerance matching, report formatting, or comparison to template metadata.

Recommendation:

- Add a unit normalization contract:
  - canonical storage unit
  - display unit
  - accepted input units
  - conversion precision
  - tolerance comparison unit
- Store both raw/source unit and normalized unit for imports.
- Add tests that assert not only numeric values but also domain display expectations.

### P2 - Template Authoring And Migration Strategy Are Brittle

Evidence:

- Large form schemas are embedded directly in SQL migrations as JSONB.
- Some migrations are read-live/order-sensitive.
- The manifest warns against casual bulk migration down/up.
- Template field schemas are described as arrays in an early comment, but generated templates are JSON objects with section structures.
- There is no obvious canonical JSON/YAML source layer with schema validation and digest checking.

Why this matters:

SQL-embedded giant JSON makes review, diffing, validation, and regeneration harder. Read-live migrations also make replay and future environment bootstrapping more fragile.

Recommendation:

- Move template definitions to canonical versioned JSON/YAML files.
- Generate SQL seed migrations from those files.
- Add a schema validator for template structure and value kinds.
- Store content digests in migration comments or manifest output.
- Add an ephemeral DB replay gate for all records migrations in canonical order.
- Treat read-live migrations as temporary scaffolding unless they are explicitly promoted.

### P2 - MTS Coverage Is Not The Same As MTS Correctness

Evidence:

- MTS chips add many templates by adapting/reusing ATS-like sections.
- The manifest describes MTS migrations as standard-aware and generated.
- Tests appear focused on coverage and basic template presence, not SME-level correctness.

Why this matters:

Template presence can satisfy a coverage invariant while still encoding wrong fields, wrong units, wrong section semantics, or wrong applicability. MTS needs domain review, not just generated completeness.

Recommendation:

- Add a field coverage matrix per apparatus/test family:
  - source section
  - template section
  - field key
  - value kind
  - unit
  - acceptance source
  - SME review status
- Add `domain_review_status` or equivalent metadata for generated templates.
- Keep generated templates visually marked as draft until reviewed.

### P2 - Acceptance/Tolerance Resolution Is Deferred But Central

Evidence:

- Legacy baseline requires acceptance windows and pass/fail.
- `041_form_submission_standard.sql` adds `neta_standard` to submissions.
- Comments say render/validate layers will resolve coverage/acceptance.
- `form_field_values` includes min/max/status-ish acceptance columns, but no resolver is implemented in the reviewed lane.

Why this matters:

Records without acceptance interpretation are incomplete for NETA-style operational use. The system must decide which standard applies, which table applies, which row applies, what unit conversion applies, and how result status is derived.

Recommendation:

- Build a narrow acceptance resolver before expanding reporting.
- Inputs:
  - apparatus kind
  - test type
  - standard
  - field key
  - unit/value
  - source table locator
- Outputs:
  - min/max/expected
  - status
  - source link id
  - resolver version
- Persist the resolver version and source link used for each interpreted value.

### P2 - PM Durable Field Records Can Be Confused With Records Lane Durable Records

Evidence:

- `apps/mutation-seam` has `pm.durable_field_records`, scoped narrowly to Temp Power field-start readiness.
- `apps/operations-web` contains a durable-field-record placeholder page that intentionally sends no live mutations.
- The records lane has a broader durable field-record/form-submission concept.

Why this matters:

The same phrase can now refer to two different things:

- PM readiness proof in the mutation seam
- Long-lived equipment/form/test records in `records.*`

That naming overlap can cause design and audit confusion.

Recommendation:

- Rename or document the PM slice as `pm.field_start_readiness_records` unless the broader term is intentional.
- Add a cross-lane glossary entry explaining the boundary.
- Do not let PM placeholder UX imply records-lane persistence exists.

### P2 - Domain Model Gaps Need Explicit Lifecycle Gates

Evidence:

- `asset_tag` is globally unique, which may be too strict across customers/sites/sources.
- Legacy baseline calls out soft-delete, but current core tables do not consistently show soft-delete semantics.
- `044_person_anchor.sql` improves technician identity but leaves broader reviewer/approver/person linkage unresolved.
- `form_submissions.pm_event_id` and `pm_events.form_submission_id` are reciprocal nullable links and can drift without a consistency rule.
- Attachments are deferred even though templates already refer to attachment-like fields.
- Field nameplate correction and multi-tech capture are explicitly deferred.
- Hard FKs to external operational tables are deferred.

Why this matters:

Many of these are reasonable early choices. The risk is not that they are wrong today; the risk is that they become de facto final because they are already in migrations.

Recommendation:

- Add lifecycle states to model decisions:
  - prototype
  - internal governed
  - production governed
  - customer-facing
- For each deferred model area, state the promotion gate.
- Revisit `asset_tag` uniqueness before importing legacy/customer data.
- Add a consistency check or service-layer invariant for PM/form reciprocal links.

### P2 - Test Posture Is Useful But Underpowered

Evidence:

- Focused non-DB import/converter tests passed.
- Records migration tests exist, but the manifest warns against bulk execution and read-live migration dependencies.
- DB-backed tests were not run in this audit because credentials were not available in environment and secrets were not read.
- RLS/security tests are absent because RLS/security is absent.
- Offline sync tests are not present for the intended PowerSync workflow.

Why this matters:

Current tests protect recent parser/mapping work, but they do not prove the lane's hardest guarantees:

- secure access
- full migration replay
- sync conflict behavior
- import auditability
- acceptance interpretation
- template/value compatibility

Recommendation:

- Create an ephemeral records DB replay job.
- Add schema validation over all `field_schema` JSON.
- Add tests that compare template field kinds to persistence support.
- Add RLS tests when policies land.
- Add import transactionality and reimport tests.
- Add offline browser tests for one representative workflow.

### P3 - Documentation Statuses Are Stale

Evidence:

- `PUNCHLIST.md` says Chip 10b/10c are next while Chip 10c exists.
- `14-CAPTURE-MODE-IMPORT-SPEC.md` still opens as design/not-built while as-built notes and code exist.
- `AGENTS.md` in the records-lane checkout still points to older Windows local assumptions, while current instruction is Olares source-of-truth over mesh.

Why this matters:

Stale docs in this lane are not harmless. They directly affect which repo, branch, and maturity state a reviewer will trust.

Recommendation:

- Add status banners to all major records docs:
  - current
  - stale
  - design-only
  - implemented partial
  - superseded
- Update path authority docs to reflect Olares mesh workflow.
- Keep design docs, as-built notes, and migration manifest in sync after every chip.

## Enhancement Roadmap

The following sequence is intentionally conservative. It aims to reduce false confidence before expanding feature scope.

### Gate 1 - Reconcile Current State

Deliverables:

- `reference/records/CURRENT-STATE.md`
- Updated `PUNCHLIST.md`
- Updated capture/import spec status
- Decision on whether `/home/olares/code/apex/apex-records-lane` should move forward or be marked stale

Exit criteria:

- A new reviewer can identify the authoritative checkout, latest records migration, implemented chips, and deferred gates in under five minutes.

### Gate 2 - Security Posture

Deliverables:

- Records RLS/grants design
- Internal service roles
- RLS migration
- Security tests

Exit criteria:

- No browser/sync-facing role can read or write cross-scope records.
- Internal-only source link and person-anchor tables have explicit policies or are explicitly blocked from exposure.

### Gate 3 - Value Model V2

Deliverables:

- Supported field kind registry
- Persistence support for date/multiselect/attachment/structured values
- Template validator
- Exactly-one-value checks or trigger validation

Exit criteria:

- Every field kind used by seeded templates is either persistable or rejected by CI.

### Gate 4 - Import Session And Review Model

Deliverables:

- Import session table
- Proposed value table
- Transactional commit path
- Source hash and parser version capture
- Review accept/reject/edit state
- Reimport behavior

Exit criteria:

- The system can reconstruct what was proposed, what was accepted, who accepted it, and what changed on reimport.

### Gate 5 - Offline Proof

Deliverables:

- One full records capture in an installable field surface
- Offline local persistence
- Upload/reconcile through mutation seam
- Conflict detection
- Review visibility

Exit criteria:

- An automated test proves capture offline, reconnect, sync, and review.

### Gate 6 - Template Source And Replay

Deliverables:

- Canonical JSON/YAML templates
- SQL generation
- Field schema validator
- Ephemeral full migration replay
- Content digest tracking

Exit criteria:

- A clean DB can be built from migrations in canonical order and template validity is machine-checked.

### Gate 7 - Acceptance Resolver

Deliverables:

- Standard/table resolver
- Unit-aware comparison
- Persisted source link and resolver version
- Result status derivation

Exit criteria:

- A numeric imported or manual value can be interpreted against an explicitly sourced acceptance window.

### Gate 8 - Restricted Source Policy

Deliverables:

- Source content policy
- Internal/customer/export classifications
- Excerpt prevention checks where needed

Exit criteria:

- Everyone knows which content can be stored, served, synced, exported, or shown.

## Recommended Near-Term Edits

High leverage, low blast radius:

1. Add `reference/records/CURRENT-STATE.md`.
2. Update `reference/records/PUNCHLIST.md` so Chip 10c and migrations `043`/`044` are represented accurately.
3. Add a warning banner to `14-CAPTURE-MODE-IMPORT-SPEC.md`: implemented partial, not audit-grade import.
4. Add a test that scans all `field_schema` values for unsupported field kinds.
5. Add a short ADR for records RLS/grants before any new UI/sync write work.
6. Add a `.dtax` capability note that says PF mapping is currently proven; TTR/WR/excitation mapping remains incomplete.
7. Add a unit-normalization issue/ADR before more import mappings are added.

## Bottom Line

This lane should continue, but it should be treated as a foundation in active design, not a nearly-finished records product.

The best parts are the architectural direction, the source-link caution in `043`, the technician-person anchor in `044`, and the early converter/import tests. The biggest risks are state drift, missing security posture, a value model that lags the templates, import provenance that is too shallow, and offline behavior that has not been proven.

The next phase should be less about adding more templates and more about hardening the trust boundary: current-state clarity, security, value compatibility, import sessions, and one real offline proof.
