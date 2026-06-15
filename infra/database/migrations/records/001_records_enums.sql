-- =============================================================================
-- Records Domain — Enum Types  (Chip 1)
-- Packet: 2026-06-12-records-001
-- Authority: reference/records/00-MASTER-INDEX.md  §3 (data model),
--            reference/records/PUNCHLIST.md  Chip 1
-- Landing Lane: infra/database/migrations/records/
--
-- Establishes the `records` schema and the type-safe enums for the four pillars of
-- the NETA field-records platform (the in-house replacement for the legacy
-- field-test datastore):
--   1. Asset register      (the equipment under test)
--   2. NETA data sheets    (the test-form instances bound to an asset + job)
--   3. Test results        (the measured readings + pass/fail assessment)
--   4. PM tracking         (preventive-maintenance programs / schedules / events)
--
-- Scope invariants preserved by this migration:
--   * New schema `records` is introduced for NETA field-test record data. It is
--     distinct from the runtime `pm` schema (which holds POST idempotency
--     infra only) — the maintenance *domain* data lives here as `records.pm_*`.
--   * No existing schema (org, work, tcc, pm, identity) is touched.
--   * Cross-schema references to org.* and work.* are carried as DEFERRED soft
--     UUID columns in 002 (no hard FK) to avoid load-ordering coupling, mirroring
--     the work→org deferred-FK pattern (work/007). Activation is a later chip.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS records;

COMMENT ON SCHEMA records IS
    'NETA field-test record domain: asset register, data sheets, test results, '
    'and preventive-maintenance tracking. Distinct from the pm schema, which '
    'holds API idempotency infrastructure only.';

-- ---------------------------------------------------------------------------
-- Provenance enums (re-declared local to records; mirror work.* semantics)
-- ---------------------------------------------------------------------------

CREATE TYPE records.provenance_source_enum AS ENUM (
    'manual',
    'legacy_import',    -- migrated from the legacy field-test datastore
    'api',
    'automation',
    'migration',
    'bulk_upload'
);

COMMENT ON TYPE records.provenance_source_enum IS
    'Origin system for a records-domain record. legacy_import flags rows carried over from '
    'the legacy field-test datastore during the one-time migration chip.';

CREATE TYPE records.provenance_status_enum AS ENUM (
    'curated',
    'imported',
    'provisional',
    'validated',
    'rejected'
);

COMMENT ON TYPE records.provenance_status_enum IS
    'Quality/trust level of a records-domain record relative to its provenance source.';

-- ---------------------------------------------------------------------------
-- Pillar 1: Asset register
-- ---------------------------------------------------------------------------

CREATE TYPE records.asset_status_enum AS ENUM (
    'in_service',
    'out_of_service',
    'spare',
    'decommissioned',
    'unknown'
);

COMMENT ON TYPE records.asset_status_enum IS
    'Operational state of a tested asset.';

CREATE TYPE records.asset_condition_enum AS ENUM (
    'good',
    'acceptable',
    'deteriorated',
    'defective',
    'not_assessed'
);

COMMENT ON TYPE records.asset_condition_enum IS
    'Most-recent overall condition assessment rolled up from test results.';

-- ---------------------------------------------------------------------------
-- Pillar 2: NETA data sheets
-- ---------------------------------------------------------------------------

CREATE TYPE records.neta_standard_enum AS ENUM (
    'ats',   -- Acceptance Testing Specifications
    'mts',   -- Maintenance Testing Specifications
    'ecs',   -- Commissioning Specifications
    'ett',   -- Technician certification / general
    'other'
);

COMMENT ON TYPE records.neta_standard_enum IS
    'NETA standard a data-sheet template is aligned to.';

CREATE TYPE records.form_status_enum AS ENUM (
    'draft',
    'in_progress',
    'complete',
    'reviewed',
    'approved',
    'superseded',
    'voided'
);

COMMENT ON TYPE records.form_status_enum IS
    'Lifecycle of a filled form submission (e.g. a NETA data sheet).';

CREATE TYPE records.form_type_enum AS ENUM (
    'neta_datasheet',   -- a NETA acceptance/maintenance test data sheet
    'jha',              -- job hazard analysis
    'safety',           -- safety form (toolbox talk, permit, etc.)
    'sop',              -- standard operating procedure checklist
    'inspection'        -- general inspection form
);

COMMENT ON TYPE records.form_type_enum IS
    'Discriminator for the kind of form a template defines. A NETA data sheet is '
    'one form_type alongside JHA / safety / SOP / inspection — the records engine '
    'is generic; form_type + field_schema specialize it.';

CREATE TYPE records.as_found_as_left_enum AS ENUM (
    'as_found',         -- condition/readings before any adjustment
    'as_left',          -- condition/readings after maintenance/adjustment
    'not_applicable'    -- acceptance test, single capture (no AF/AL split)
);

COMMENT ON TYPE records.as_found_as_left_enum IS
    'Sheet-level As-Found / As-Left classification: a maintenance visit yields '
    'two sheets (one as_found, one as_left) for the same asset + form.';

-- ---------------------------------------------------------------------------
-- Pillar 3: Test results
-- ---------------------------------------------------------------------------

CREATE TYPE records.assessment_result_enum AS ENUM (
    'pass',
    'fail',
    'marginal',
    'needs_repair',
    'not_tested',
    'informational'
);

COMMENT ON TYPE records.assessment_result_enum IS
    'Pass/fail-style assessment of a single test result or of a data sheet.';

CREATE TYPE records.field_value_kind_enum AS ENUM (
    'numeric',          -- real-valued reading
    'boolean',          -- pass/fail or yes/no reading
    'text',             -- free-text reading
    'selection',        -- dropdown / enumerated choice
    'graph'             -- embedded trace/plot payload
);

COMMENT ON TYPE records.field_value_kind_enum IS
    'Shape of a captured test-result value; selects which value column is '
    'authoritative for a given records.form_field_values row.';

-- ---------------------------------------------------------------------------
-- Pillar 4: PM tracking
-- ---------------------------------------------------------------------------

CREATE TYPE records.pm_interval_unit_enum AS ENUM (
    'months',
    'years',
    'operations',   -- mechanical operation count (e.g. breaker cycles)
    'runtime_hours'
);

COMMENT ON TYPE records.pm_interval_unit_enum IS
    'Unit a preventive-maintenance recurrence interval is expressed in.';

CREATE TYPE records.pm_event_status_enum AS ENUM (
    'scheduled',
    'due',
    'overdue',
    'in_progress',
    'completed',
    'skipped',
    'cancelled'
);

COMMENT ON TYPE records.pm_event_status_enum IS
    'Lifecycle of an individual preventive-maintenance occurrence.';
