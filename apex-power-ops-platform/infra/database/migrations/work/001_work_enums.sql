-- =============================================================================
-- PM/Work Domain — Enum Types
-- Packet: 2026-04-13-pm-schema-007
-- Authority: PM-DOMAIN-IMPLEMENTATION-READY-SCHEMA-SPEC-2026-04-12.md §4–§5
-- Landing Lane: infra/database/migrations/work/
-- =============================================================================

-- Create the work schema if it does not exist
CREATE SCHEMA IF NOT EXISTS work;

-- ---------------------------------------------------------------------------
-- 5.1 Provenance Enums (shared across all PM/work entities)
-- ---------------------------------------------------------------------------

CREATE TYPE work.provenance_source_enum AS ENUM (
    'manual',
    'p6_import',
    'api',
    'automation',
    'migration',
    'bulk_upload'
);

COMMENT ON TYPE work.provenance_source_enum IS
    'Origin system for a record. Every PM/work entity tracks how it was created.';

CREATE TYPE work.provenance_status_enum AS ENUM (
    'curated',
    'imported',
    'provisional',
    'validated',
    'rejected'
);

COMMENT ON TYPE work.provenance_status_enum IS
    'Quality/trust level of a record relative to its provenance source.';

-- ---------------------------------------------------------------------------
-- 4.1 Project Enums
-- ---------------------------------------------------------------------------

CREATE TYPE work.project_status_enum AS ENUM (
    'draft',
    'active',
    'on_hold',
    'complete',
    'closed',
    'cancelled'
);

COMMENT ON TYPE work.project_status_enum IS
    'Project lifecycle states. Spec §4.1.';

-- ---------------------------------------------------------------------------
-- 4.2 Work Package Enums
-- ---------------------------------------------------------------------------

CREATE TYPE work.wp_lifecycle_enum AS ENUM (
    'draft',
    'planned',
    'ready',
    'active',
    'blocked',
    'awaiting_review',
    'complete',
    'closed',
    'cancelled'
);

COMMENT ON TYPE work.wp_lifecycle_enum IS
    'Work-package 9-state lifecycle model. Spec §4.2.';

CREATE TYPE work.work_type_enum AS ENUM (
    'testing',
    'commissioning',
    'maintenance',
    'inspection',
    'study',
    'other'
);

COMMENT ON TYPE work.work_type_enum IS
    'Execution classification for a work package. Spec §4.2.';

CREATE TYPE work.priority_enum AS ENUM (
    'critical',
    'high',
    'normal',
    'low'
);

COMMENT ON TYPE work.priority_enum IS
    'Business priority level. Used on work_packages and as computed schedule priority on tasks.';

CREATE TYPE work.billing_state_enum AS ENUM (
    'not_billable',
    'pending',
    'invoiced',
    'paid',
    'disputed'
);

COMMENT ON TYPE work.billing_state_enum IS
    'Financial workflow state for a work package. Spec §4.2.';

-- ---------------------------------------------------------------------------
-- 4.3 Task Enums
-- ---------------------------------------------------------------------------

CREATE TYPE work.task_lifecycle_enum AS ENUM (
    'not_started',
    'ready',
    'active',
    'on_hold',
    'awaiting_review',
    'complete',
    'cancelled'
);

COMMENT ON TYPE work.task_lifecycle_enum IS
    'Task 7-state lifecycle model. Spec §4.3.';

CREATE TYPE work.task_type_enum AS ENUM (
    'task',
    'milestone',
    'finish_milestone',
    'level_of_effort',
    'wbs_summary'
);

COMMENT ON TYPE work.task_type_enum IS
    'Task type classification, aligned with P6 activity types. Spec §4.3.';

-- ---------------------------------------------------------------------------
-- 4.5 Dependency Enums
-- ---------------------------------------------------------------------------

CREATE TYPE work.dependency_type_enum AS ENUM (
    'FS',
    'SS',
    'SF',
    'FF'
);

COMMENT ON TYPE work.dependency_type_enum IS
    'Schedule relationship types: Finish-Start, Start-Start, Start-Finish, Finish-Finish. Spec §4.5.';

-- ---------------------------------------------------------------------------
-- 4.6 Assignment Enums
-- ---------------------------------------------------------------------------

CREATE TYPE work.assignment_role_enum AS ENUM (
    'primary',
    'secondary',
    'lead',
    'observer',
    'support'
);

COMMENT ON TYPE work.assignment_role_enum IS
    'Role classification for resource assignments. Spec §4.6.';

-- ---------------------------------------------------------------------------
-- 4.7 Execution Issue Enums
-- ---------------------------------------------------------------------------

CREATE TYPE work.issue_type_enum AS ENUM (
    'equipment_not_ready',
    'test_failure',
    'settings_incorrect',
    'access_blocked',
    'safety_hold',
    'material_missing',
    'documentation_gap',
    'other'
);

COMMENT ON TYPE work.issue_type_enum IS
    'Classification of execution issues encountered during field work. Spec §4.7.';

CREATE TYPE work.severity_enum AS ENUM (
    'critical',
    'major',
    'minor',
    'info'
);

COMMENT ON TYPE work.severity_enum IS
    'Issue severity level. Spec §4.7.';

CREATE TYPE work.issue_status_enum AS ENUM (
    'open',
    'in_review',
    'escalated',
    'resolved',
    'closed'
);

COMMENT ON TYPE work.issue_status_enum IS
    'Execution issue 5-state model. Spec §4.7.';

CREATE TYPE work.resolution_type_enum AS ENUM (
    'repaired',
    'retested_passed',
    'deferred',
    'accepted_as_is',
    'replaced',
    'not_applicable'
);

COMMENT ON TYPE work.resolution_type_enum IS
    'Disposition of a resolved execution issue. Spec §4.7.';

-- ---------------------------------------------------------------------------
-- 4.8 Progress Snapshot Enums
-- ---------------------------------------------------------------------------

CREATE TYPE work.snapshot_status_enum AS ENUM (
    'draft',
    'submitted',
    'approved',
    'rejected'
);

COMMENT ON TYPE work.snapshot_status_enum IS
    'Progress snapshot 4-state approval model. Spec §4.8.';
