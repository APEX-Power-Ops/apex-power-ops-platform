-- =============================================================================
-- NETA Records Domain — Enum Types  (PowerDB replacement, Chip 1)
-- Packet: 2026-06-12-neta-records-001
-- Authority: reference/neta-records/00-MASTER-INDEX.md  §3 (data model),
--            reference/neta-records/POWERDB-PARITY-PUNCHLIST.md  Chip 1
-- Landing Lane: infra/database/migrations/neta/
--
-- Establishes the `neta` schema and the type-safe enums for the four
-- PowerDB-replacement pillars:
--   1. Asset register      (the equipment under test — PowerDB "test objects")
--   2. NETA data sheets    (the test-form instances bound to an asset + job)
--   3. Test results        (the measured readings + pass/fail assessment)
--   4. PM tracking         (preventive-maintenance programs / schedules / events)
--
-- Scope invariants preserved by this migration:
--   * New schema `neta` is introduced for NETA field-test record data. It is
--     distinct from the runtime `pm` schema (which holds POST idempotency
--     infra only) — the maintenance *domain* data lives here as `neta.pm_*`.
--   * No existing schema (org, work, tcc, pm, identity) is touched.
--   * Cross-schema references to org.* and work.* are carried as DEFERRED soft
--     UUID columns in 002 (no hard FK) to avoid load-ordering coupling, mirroring
--     the work→org deferred-FK pattern (work/007). Activation is a later chip.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS neta;

COMMENT ON SCHEMA neta IS
    'NETA field-test record domain (PowerDB replacement): asset register, data '
    'sheets, test results, and preventive-maintenance tracking. Distinct from the '
    'pm schema, which holds API idempotency infrastructure only.';

-- ---------------------------------------------------------------------------
-- Provenance enums (re-declared local to neta; mirror work.* semantics)
-- ---------------------------------------------------------------------------

CREATE TYPE neta.provenance_source_enum AS ENUM (
    'manual',
    'powerdb_import',   -- migrated from a legacy PowerDB instance
    'api',
    'automation',
    'migration',
    'bulk_upload'
);

COMMENT ON TYPE neta.provenance_source_enum IS
    'Origin system for a neta record. powerdb_import flags rows carried over '
    'from the legacy PowerDB datastore during the parity-migration chip.';

CREATE TYPE neta.provenance_status_enum AS ENUM (
    'curated',
    'imported',
    'provisional',
    'validated',
    'rejected'
);

COMMENT ON TYPE neta.provenance_status_enum IS
    'Quality/trust level of a neta record relative to its provenance source.';

-- ---------------------------------------------------------------------------
-- Pillar 1: Asset register
-- ---------------------------------------------------------------------------

CREATE TYPE neta.asset_status_enum AS ENUM (
    'in_service',
    'out_of_service',
    'spare',
    'decommissioned',
    'unknown'
);

COMMENT ON TYPE neta.asset_status_enum IS
    'Operational state of a tested asset (PowerDB equipment lifecycle).';

CREATE TYPE neta.asset_condition_enum AS ENUM (
    'good',
    'acceptable',
    'deteriorated',
    'defective',
    'not_assessed'
);

COMMENT ON TYPE neta.asset_condition_enum IS
    'Most-recent overall condition assessment rolled up from test results.';

-- ---------------------------------------------------------------------------
-- Pillar 2: NETA data sheets
-- ---------------------------------------------------------------------------

CREATE TYPE neta.neta_standard_enum AS ENUM (
    'ats',   -- Acceptance Testing Specifications
    'mts',   -- Maintenance Testing Specifications
    'ecs',   -- Commissioning Specifications
    'ett',   -- Technician certification / general
    'other'
);

COMMENT ON TYPE neta.neta_standard_enum IS
    'NETA standard a data-sheet template is aligned to.';

CREATE TYPE neta.datasheet_status_enum AS ENUM (
    'draft',
    'in_progress',
    'complete',
    'reviewed',
    'approved',
    'superseded',
    'voided'
);

COMMENT ON TYPE neta.datasheet_status_enum IS
    'Lifecycle of a filled NETA data sheet (PowerDB form state).';

-- ---------------------------------------------------------------------------
-- Pillar 3: Test results
-- ---------------------------------------------------------------------------

CREATE TYPE neta.assessment_result_enum AS ENUM (
    'pass',
    'fail',
    'marginal',
    'needs_repair',
    'not_tested',
    'informational'
);

COMMENT ON TYPE neta.assessment_result_enum IS
    'Pass/fail-style assessment of a single test result or of a data sheet.';

CREATE TYPE neta.result_value_kind_enum AS ENUM (
    'numeric',
    'boolean',
    'text',
    'selection'
);

COMMENT ON TYPE neta.result_value_kind_enum IS
    'Shape of a captured test-result value; selects which value column is '
    'authoritative for a given neta.test_results row.';

-- ---------------------------------------------------------------------------
-- Pillar 4: PM tracking
-- ---------------------------------------------------------------------------

CREATE TYPE neta.pm_interval_unit_enum AS ENUM (
    'months',
    'years',
    'operations',   -- mechanical operation count (e.g. breaker cycles)
    'runtime_hours'
);

COMMENT ON TYPE neta.pm_interval_unit_enum IS
    'Unit a preventive-maintenance recurrence interval is expressed in.';

CREATE TYPE neta.pm_event_status_enum AS ENUM (
    'scheduled',
    'due',
    'overdue',
    'in_progress',
    'completed',
    'skipped',
    'cancelled'
);

COMMENT ON TYPE neta.pm_event_status_enum IS
    'Lifecycle of an individual preventive-maintenance occurrence.';
