# NETA Records Domain SQL Migration Manifest
## Packet: 2026-06-12-records-001
## Lane: NETA field-records platform — Chip 1 (data model foundation)
## Authority: `reference/records/00-MASTER-INDEX.md` §4, `01-OFFLINE-SYNC-ARCHITECTURE.md`

The `records` schema is the in-house replacement for the legacy field-test datastore:
asset register, NETA data sheets, test results, and PM tracking. This Chip 1 set
lands the foundation tables only — no data seed, no cross-schema FK activation
(both are later chips).

**Generalized 2026-06-15 (records chip):** the original `neta.*` sketch is renamed to `records.*` and the `datasheet_*` tables to `form_*` with a `form_type` discriminator (`neta_datasheet` | `jha` | `safety` | `sop` | `inspection`), plus a deferred `assets.equipment_model_id` soft seam to the `core` identity spine. NETA data sheets are one `form_type`; the engine is generic. Applied + down/up-validated on a local Postgres `records_dev`.

The model was validated against the legacy field-test baseline — the capability
floor recorded in `reference/records/02-LEGACY-BASELINE.md`. Refinements
folded in: sheet-level As-Found/As-Left, GPS + site location hierarchy on assets,
the `job_number` external join key, a `graph` result kind, and the field_schema
control model.

## Execution Order

Execute in strict sequential order against the target database:

| Order | File | Contents | Dependencies |
| --- | --- | --- | --- |
| 1 | `001_records_enums.sql` | `records` schema + 12 enum types | None (`gen_random_uuid()` support) |
| 2 | `002_records_tables.sql` | 8 foundation tables with PKs, internal FKs, CHECK + UNIQUE constraints, sync-contract columns, and the reciprocal form_submissions↔pm_events FK | Requires 001 |
| 3 | `003_records_indexes.sql` | FK-join + filter indexes; partial unique index for one current template version per code | Requires 002 |
| 4 | `004_records_triggers_and_views.sql` | `updated_at` auto-maintenance on all 8 tables + 2 read views (`v_asset_test_history`, `v_pm_due`) | Requires 002 |

Each file has a matching `_down.sql` that reverses it in dependency order.

## Quick Execution

```bash
# Against a local staging database
psql -d apex_neta_stage -f 001_records_enums.sql
psql -d apex_neta_stage -f 002_records_tables.sql
psql -d apex_neta_stage -f 003_records_indexes.sql
psql -d apex_neta_stage -f 004_records_triggers_and_views.sql

# Roll back (reverse order)
psql -d apex_neta_stage -f 004_records_triggers_and_views_down.sql
psql -d apex_neta_stage -f 003_records_indexes_down.sql
psql -d apex_neta_stage -f 002_records_tables_down.sql
psql -d apex_neta_stage -f 001_records_enums_down.sql
```

> Not yet applied to the governed Supabase project — this lands as reviewable SQL
> first (per the operator's "talk about how it works before migration steps" gate).

## Object Summary

| Category | Count | Details |
| --- | --- | --- |
| Schema | 1 | `records` |
| Enum types | 12 | provenance_source, provenance_status, asset_status, asset_condition, neta_standard, form_status, form_type, as_found_as_left, assessment_result, field_value_kind, pm_interval_unit, pm_event_status |
| Tables | 8 | asset_classes, assets, form_templates, form_submissions, form_field_values, pm_programs, pm_schedules, pm_events |
| Indexes | 25 | FK-join + filter; incl. partial `uq_form_templates_current` and partial `ix_pm_schedules_due` |
| Trigger functions | 1 | `records.fn_set_updated_at` |
| Triggers | 8 | `updated_at` on every table |
| Views | 2 | `v_asset_test_history`, `v_pm_due` |

## Deferred (NOT in Chip 1)

- **Cross-schema FK activation** — `site_ref`, `client_ref`, `project_ref`,
  `work_package_ref`, `apparatus_ref` are soft UUID columns (no hard FK) to avoid
  seed-ordering coupling. Activation = punch-list Chip 8.
- **Data seed** — templates/asset-class catalog = Chip 2.
- **Sync rules + uploadData connector** (PowerSync) = Chip 3, not a SQL migration.
