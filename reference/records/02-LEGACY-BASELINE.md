# NETA Records — Legacy Baseline (Capabilities to Replace)

> **The capability floor the platform must replace and surpass — not a blueprint.**
> The incumbent NETA field-test datastore is the current industry standard; this
> doc records *what it does* so we can clear that bar and move past it. It is the
> baseline, **not the goal**. We do not embed a copy of the incumbent's schema or
> name it as a target — the platform is designed on its own terms.

- **Status:** CAPTURED 2026-06-13 (capability review of the incumbent field-test datastore)
- **Owner:** APEX NETA Records lane
- **Home:** `reference/records/` (cited by `00-MASTER-INDEX.md` and the `records/` migrations)

---

## 1. Capabilities the platform must absorb (the floor)

The incumbent is what testing firms run on today. To replace it, the platform must
at minimum do all of this — these are requirements, stated as concepts, not a copy
of any vendor's tables:

- **Equipment register** — a persistent record per piece of equipment under test,
  with nameplate (mfr / model / serial / ratings / year), a location hierarchy, GPS,
  status, and condition. Everything else hangs off this.
- **Standardized test-form catalog** — a versioned library of blank test forms, one
  per equipment category, aligned to NETA standards.
- **Filled test instances** — a captured form bound to one asset on one job visit,
  with technician, date, conditions, an **As-Found / As-Left** classification, and a
  rolled-up pass/fail.
- **Typed per-field readings** — each measured value carries its kind (numeric /
  boolean / text / selection / graph), its unit, an acceptance window, and a pass/
  fail assessment — so pass/fail is self-contained.
- **Preventive-maintenance cadence** — a maintenance interval per equipment type,
  per-asset schedules with a next-due, and recorded maintenance occurrences.
- **Job / customer / site linkage** — work tied to a job, a customer, and a site,
  joined across systems by a human-readable **job number**.
- **Operational hygiene** — soft-delete, region scoping, audit timestamps.

## 2. Equipment categories to cover (NETA-aligned)

The platform's `asset_classes` must span the field's equipment categories. These map
to NETA §7 sections (industry standard, not vendor-specific):

circuit breakers (7.6) · protective relays (7.9) · cables (7.3) · transformers
(7.2) · instrument transformers (7.10) · motor control centers (7.16) ·
switchboards/switchgear (7.1) · grounding systems (7.13) · switches (7.5) ·
transfer switches (7.11) · generators (7.15) · batteries (7.17) · power-factor
tests · infrared/thermography · insulating fluids. (Circuit breakers, relays,
cables, and transformers are the highest-volume families — sequence Chip 2 there.)

## 3. The field/control model (why `field_schema` is shaped as it is)

A test form is not a flat list — it is a **hierarchy of controls** (sections /
subforms). Each control carries: a stable **tag**, a **control type** (text /
numeric / dropdown / graphic / subform), a **data source** (entered vs inherited
from the job vs computed), read-only-ness, and a unit. The platform captures this in
`records.form_templates.field_schema` (JSONB) so the catalog is data, not code.

**Inherited fields are not stored per sheet** — they come from the job (job number,
customer, site, page). The platform resolves them via `project_ref`, not as
`form_field_values` rows.

> The complete field inventory = every form × its controls. Proving 100% coverage is
> **Chip 2** (the field-coverage matrix); the schema is the open container that holds it.

## 4. Where the platform must EXCEED the baseline (the goal)

The incumbent sets the floor. The platform's reason to exist is to clear it:

| Baseline limitation | Platform target |
|---|---|
| Per-tech local copies + manual sync; changes invisible until sync | Offline-first capture reconciling to **one source of truth** (see `01`) |
| Vendor-locked, Windows-centric, closed datastore | Open Postgres data, queryable, no lock-in, web/PWA cross-platform |
| Duplicate data entry across estimator / PM / field tools (the #1 bottleneck) | Provision once from project/work; field inherits it |
| Test data siloed in a separate tool | Results flow into the project/work, TCC, and reporting lanes |
| Read-only/manual reporting | Native report/export from completed sheets (`forms-engine`) |

## 5. Refinements this baseline forced into Chip 1

| # | Baseline observation | Schema change |
|---|---|---|
| R1 | As-Found / As-Left is a **sheet-level** classification | `as_found_as_left_enum` + `form_submissions.as_found_as_left` (a maintenance visit = two sheets) |
| R2 | Assets carry a site location hierarchy + GPS | `assets.region/jobsite/plant/substation` + `gps_lat`/`gps_long`; tree stays on `parent_asset_id` |
| R3 | Readings split by type incl. embedded graphs | `field_value_kind = numeric|boolean|text|selection|graph` |
| R4 | A human-readable job number is the cross-system key | `form_submissions.job_number` (+ index), alongside soft `project_ref` |
| R5 | Test status is richer than pass/fail | `form_submissions.test_status_label` beside `overall_assessment` |
| R6 | Forms are a hierarchical control tree | `field_schema` ruled to the control model (§3) |
| R7 | Maintenance interval lives on the equipment type | confirms `pm_programs.template_id` + interval (no change) |

## 6. Legacy-data migration (a later chip, not a copy here)

Replacing the incumbent includes a **one-time import** of existing records, keyed by
job number, landing as `source = legacy_import` with `legacy_source_id` preserved for
dedupe/round-trip. The detailed legacy field-to-`records` mapping is derived **at that
chip, from the operator-held source export** — it is deliberately **not committed to
this repo** (no copy of the incumbent lives here).

## 7. Open / deferred (honesty register)

- **Field-coverage matrix** (Chip 2) — per-form `field_schema` population is not done;
  coverage is *structurally* possible, not yet *proven*.
- **Custom/extension fields** — the incumbent exposes generic user-defined columns;
  candidate model is a `custom_fields jsonb` (not yet added).
- **Compliance / attributes**, **archive/history** — not yet mapped; later.
