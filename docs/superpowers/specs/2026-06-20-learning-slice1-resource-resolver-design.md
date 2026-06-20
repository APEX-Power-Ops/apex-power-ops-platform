# Learning Slice 1 — Contextual Resource Resolver — Design

**Status:** Approved design (brainstorming output), 2026-06-20.
**Lane:** `learning/slice1-resolver`.  **Dev DB:** `learning_dev` (host PG17 `apex-dev-pg`).  **Nothing is applied to prod.**
**Flagship lane:** learning/enablement — putting the right knowledge at a tech's disposal exactly when relevant, scaled to experience (a workforce multiplier for short-supply NETA techs). This slice is the contextual **resource-linking** half; the tracking/ROI half is a later slice.

## Goal

Given a tech's work context — the **NETA section** they are testing — return the **ranked, relevant learning resources**. Deliver a reusable resolver, an HTTP endpoint, and a thin demo UI.

## Scope

**In:**
- `packages/learning-resolver` — the reusable resolver core + a CLI.
- A read route in `control-plane-api` — `GET /api/v1/learning/resources`.
- A thin demo page in `operations-web`.
- TDD against the populated `learning_dev` baseline.

**Out (YAGNI — deferred to later slices):**
- Progress / ROI tracking (the tracking trio is greenfield; not this slice).
- Competency-data-driven personalization — `level` is a **manual parameter** (real competency data is empty: 0 user rows; the person spine was just wired but is unpopulated).
- Embedding into the records datasheet / lvbreakertcc UI.
- Any prod write; any auth/RLS (dev-stage, internal).

## Baseline facts (verified 2026-06-20 against `learning_dev`)

**The join key is the NETA section number**, shared across both domains:
- records: `records.neta_procedures.section` (the work-spine anchor; e.g. `7.6.1.1.1`).
- learning: `neta_procedures.section_number`, `study_content.neta_section_primary` (+ `neta_sections_secondary` array), `apparatus_types.neta_section_{ats,mts,ecs,ett}`.

Keying on the NETA section **sidesteps the vocab mismatch** between records `class_code` (`cb_lv`) and learning `type_code` (`XFMR-DRY`) — no crosswalk table needed.

**Two resource sources in `learning_dev`:**
1. `apparatus_type_resources` — **189 curated links**. Polymorphic: `resource_type` in {`neta_procedure`, `sop`, `safety_document`, `datasheet`, `document`, `video`, `checklist`, `study_guide`, `practice_test`, `reference_sheet`}; reference columns {`neta_procedure_id`, `sop_id`, `safety_document_id`, `datasheet_id`, `study_content_id`, `resource_url`} gated by a CHECK; editorial signals `is_primary`, `is_mandatory`, `display_order`, `is_active`.
2. `study_content` — **967 rows**. Each tagged `neta_section_primary` (+ `neta_sections_secondary[]`), `certification_level`, `status`, `quality_tier`, `title`, `summary`, `slug`, `body_markdown`.

**Section → apparatus_type:** `neta_procedures.section_number = :section -> apparatus_type_id` resolves a section to its apparatus_type(s) (note `section_number` is NOT unique — an ATS and an MTS row may share it; take DISTINCT apparatus_type_id, normally one).

## Architecture

Three components with clean boundaries, following platform conventions (Python packages -> `control-plane-api` HTTP -> Next surface):

```
work context (NETA section [+ level])
        |  caller = the records work-spine, which already knows its section
        v
control-plane-api  GET /api/v1/learning/resources   (thin wrapper)
        v
packages/learning-resolver   resolve(...)            (the brain; learning_dev-only)
        v
learning_dev  (apparatus_type_resources + study_content + neta_procedures)
        ^
operations-web /learning-demo  -- calls the endpoint, renders ranked resources
```

The resolver is **`learning_dev`-only**; records integration is purely the API contract (caller passes the NETA section). No cross-DB coupling.

## Component 1 — `packages/learning-resolver` (Python)

**Responsibility:** resolve a work context to ranked resources. Pure, testable, reusable.

**Public interface:**
- `resolve(neta_section: str, level: str | None = None, limit: int = 20) -> list[ResolvedResource]`
- `ResolvedResource`: `{ resource_type, title, source: "curated" | "section_match", reference, is_primary, is_mandatory, cert_level, score, why }`
  - `reference` = the concrete target (`study_content_id`, `neta_procedure_id`, or `resource_url`) plus a `slug`/`summary` where available.
  - `why` = a short human string explaining the match (e.g. `"primary curated resource for Dry-Type Transformer"`, `"NETA 7.6.1.1.1 primary-section study content"`).
- CLI: `learning-resolver resolve --section 7.6.1.1.1 [--level III] [--limit 20] [--json]`.

**Config:** `LEARNING_DEV_DSN` / `LEARNING_DEV_PGPASSWORD` env (mirrors `ops-intake`'s pinned-DSN pattern — ambient PG env points at prod, so the local DSN is pinned). `psycopg[binary]`.

**Layout:** `packages/learning-resolver/{pyproject.toml, learning_resolver/__init__.py, resolver.py, db.py, cli.py, models.py, tests/}`.

## The resolver algorithm (hybrid + optional level)

1. **Context -> apparatus_type(s).** `SELECT DISTINCT apparatus_type_id FROM neta_procedures WHERE section_number = :section AND apparatus_type_id IS NOT NULL`.
2. **Curated tier** (`source="curated"`). For those apparatus_type_id(s): `apparatus_type_resources` WHERE `is_active`, ordered `is_primary DESC, is_mandatory DESC, display_order ASC`. Resolve each polymorphic row to its target (join `study_content` when `study_content_id` is set; else `resource_url`/name). Base score high; `why` cites the curation.
3. **Section-join tier** (`source="section_match"`). `study_content` WHERE (`neta_section_primary = :section` OR `:section = ANY(neta_sections_secondary)`) AND `is_active` AND published `status`. **Dedupe** against any study_content already surfaced in tier 2. Score: primary-section > secondary; `quality_tier` as a tiebreak.
4. **Level re-rank (soft).** If `level` given, add a boost to items whose `certification_level`/`levels` match or are adjacent — **never hard-filter** (a Level II tech can still see a III resource, just ranked lower).
5. **Merge -> sort by score -> cap at `limit`.** Each item carries `source`, `score`, `why`, and the editorial flags.

**Edge cases (all return cleanly, never error):** section with no apparatus_type (skip tier 2, section-join only); section with curated but no study_content (tier 2 only); section with neither -> empty list; unknown/garbage section -> empty list; a study_content that is both curated and section-matched appears **once** (as curated).

## Component 2 — `control-plane-api` route

`GET /api/v1/learning/resources?neta_section={s}&level={II|III|IV}&limit={n}`
- `200 { "context": { "neta_section", "level", "limit" }, "resources": ResolvedResource[] }`.
- `400` when `neta_section` is missing/blank.
- Empty `resources: []` (NOT `404`) when nothing matches — "no resources" is a valid, expected answer the UI renders distinctly.
- Thin wrapper: validate params -> call `learning_resolver.resolve(...)` -> serialize. Connects to `learning_dev` (dev-stage DSN; documented as dev-only until learning data has a hosted home).

## Component 3 — `operations-web` demo page

Route `/learning-demo` (clearly labeled a Slice-1 demo).
- Inputs: a **NETA section** typeahead (seeded from the procedures list) + an optional **level** selector (II/III/IV/none).
- Renders the ranked resources grouped by `source` (Curated first, then Section matches), each with title, `why`, and badges (`primary`, `mandatory`, cert level). Empty state renders a clear "no linked resources for this section yet."
- **Eventual production home = `field-surface`** (the point-of-work surface) in a later slice; `operations-web` is chosen here only because it is the established Next app with the API-client pattern already in place.

## Data flow

Caller supplies `neta_section` (the records work-spine already knows it) -> endpoint validates -> resolver queries `learning_dev` (3 steps) -> ranked JSON -> UI renders. No write path; no `records_dev` read; no prod.

## Testing strategy (TDD against the populated `learning_dev` baseline)

- **Curated-first ordering** — a section with curated links returns them ahead of section-matches, in `is_primary`/`is_mandatory`/`display_order` order.
- **Section-join fallback** — a section with `study_content` but no curated links returns section-matches.
- **Dedupe** — a `study_content` that is both curated and section-matched appears once, labeled `curated`.
- **Level re-rank** — passing `level` changes ORDER but not MEMBERSHIP (no hard filter).
- **Empty/unknown section** — returns `[]`, no exception; endpoint returns `200 {resources: []}`.
- **Primary vs secondary section** — a `study_content` matched only via `neta_sections_secondary` ranks below a primary match.
- API-level: `400` on missing `neta_section`; shape of the `200` payload.
- The resolver tests pin `LEARNING_DEV_DSN` to `learning_dev` (read-only queries; no fixtures mutate the baseline).

## Assumptions & decisions

- **NETA section is the integration contract.** `asset_class` is intentionally NOT a resolver input in Slice 1 (the section is authoritative); it may become a future ranking hint.
- **Read-only, dev-stage.** No auth, no RLS, no writes; `learning_dev` is internal. A hosted/prod home for learning data is a separate future decision.
- **`level` is a manual param**, not competency-derived — competency data is empty. The hook is built so that, once techs are provisioned and competency is populated (person spine, PR #21), the caller can pass the tech's real level with zero resolver change.
- **Resolver is Python** (matches `ops-intake`/`calc-engine`); **UI is Next** (matches `operations-web`).

## Out-of-scope / later slices (named, so nothing is silently dropped)

Tracking + ROI module · competency-personalized ranking (needs populated competency) · records/lvbreakertcc embedding · `field-surface` production home · auth/RLS + a hosted learning datastore · asset_class-aware ranking.
