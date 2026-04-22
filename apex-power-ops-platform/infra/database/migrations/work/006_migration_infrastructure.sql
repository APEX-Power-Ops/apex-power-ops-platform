-- =============================================================================
-- PM/Work Domain — Migration Infrastructure
-- Packet: 2026-04-13-pm-schema-009a
-- Authority: 2026-04-13-pm-schema-009-legacy-migration-planning-handoff.md
-- Purpose: Staging-only mapping tables, enum conversion functions, and audit
--          logging to support a future V1→V2 dry-run migration.
-- Target: Local PostgreSQL staging database `apex_pm_stage` ONLY
-- =============================================================================

-- =============================================================================
-- 1. MIGRATION SCHEMA
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS migration;

COMMENT ON SCHEMA migration IS
    'Staging-only migration infrastructure for V1→V2 PM/work domain migration. '
    'Not deployed to production. Created by packet 009a.';

-- =============================================================================
-- 2. TIMEZONE CONVERSION RULE
-- =============================================================================
-- Decision: Use America/Denver as the default timezone for V1 date→timestamptz
-- conversion. RESA Power is headquartered in Denver; V1 dates have no timezone.
-- This can be overridden per-row if project-specific timezone data becomes
-- available.

-- Store the default as a migration configuration parameter
CREATE TABLE migration.config (
    config_key   TEXT PRIMARY KEY,
    config_value TEXT NOT NULL,
    description  TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE migration.config IS
    'Key-value configuration for migration parameters.';

INSERT INTO migration.config (config_key, config_value, description) VALUES
    ('default_timezone', 'America/Denver', 'Default TZ for V1 date→timestamptz conversion. RESA HQ is Denver.'),
    ('migration_source', 'v1_supabase', 'Source system identifier for provenance tracking.'),
    ('packet_authority', '2026-04-13-pm-schema-009a', 'Packet that created this infrastructure.');

-- =============================================================================
-- 3. SCOPE-TO-WORK-PACKAGE MAPPING TABLE
-- =============================================================================

CREATE TABLE migration.scope_to_wp_mapping (
    v1_scope_id         UUID NOT NULL,
    v1_scope_number     TEXT,
    v1_project_id       UUID,
    v2_work_package_id  UUID,
    v2_project_id       UUID,
    mapping_status      TEXT NOT NULL DEFAULT 'pending'
                        CHECK (mapping_status IN ('pending', 'mapped', 'skipped', 'error')),
    mapping_notes       TEXT,
    mapped_at           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT pk_scope_to_wp_mapping PRIMARY KEY (v1_scope_id),
    CONSTRAINT uq_scope_to_wp_v2_wp UNIQUE (v2_work_package_id)
);

COMMENT ON TABLE migration.scope_to_wp_mapping IS
    'Lookup table mapping V1 scopes.id to V2 work.work_packages.work_package_id. '
    'Populated from V1 source data before dry-run migration.';

CREATE INDEX idx_scope_wp_mapping_status ON migration.scope_to_wp_mapping (mapping_status);
CREATE INDEX idx_scope_wp_mapping_v1_project ON migration.scope_to_wp_mapping (v1_project_id);

-- =============================================================================
-- 4. PROJECT ID MAPPING TABLE
-- =============================================================================
-- V1 projects.id is preserved as V2 work.projects.project_id in the mapping
-- rules, but we track the mapping explicitly for audit and reconciliation.

CREATE TABLE migration.project_id_mapping (
    v1_project_id       UUID NOT NULL,
    v1_project_number   TEXT,
    v2_project_id       UUID NOT NULL,
    v2_project_code     TEXT,
    mapping_status      TEXT NOT NULL DEFAULT 'pending'
                        CHECK (mapping_status IN ('pending', 'mapped', 'skipped', 'error')),
    mapping_notes       TEXT,
    mapped_at           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT pk_project_id_mapping PRIMARY KEY (v1_project_id),
    CONSTRAINT uq_project_mapping_v2 UNIQUE (v2_project_id)
);

COMMENT ON TABLE migration.project_id_mapping IS
    'Tracks V1→V2 project ID mapping for reconciliation and audit.';

-- =============================================================================
-- 5. TASK ID MAPPING TABLE
-- =============================================================================

CREATE TABLE migration.task_id_mapping (
    v1_task_id          UUID NOT NULL,
    v1_task_number      TEXT,
    v1_scope_id         UUID,
    v2_task_id          UUID NOT NULL,
    v2_work_package_id  UUID,
    mapping_status      TEXT NOT NULL DEFAULT 'pending'
                        CHECK (mapping_status IN ('pending', 'mapped', 'skipped', 'error')),
    mapping_notes       TEXT,
    mapped_at           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT pk_task_id_mapping PRIMARY KEY (v1_task_id),
    CONSTRAINT uq_task_mapping_v2 UNIQUE (v2_task_id)
);

COMMENT ON TABLE migration.task_id_mapping IS
    'Tracks V1→V2 task ID mapping including scope→WP resolution.';

CREATE INDEX idx_task_mapping_v1_scope ON migration.task_id_mapping (v1_scope_id);

-- =============================================================================
-- 6. ASSIGNMENT MAPPING TABLE
-- =============================================================================

CREATE TABLE migration.assignment_mapping (
    v1_assignment_id    UUID NOT NULL,
    v1_scope_id         UUID,
    v1_project_id       UUID,
    v2_assignment_id    UUID NOT NULL,
    v2_work_package_id  UUID,
    mapping_status      TEXT NOT NULL DEFAULT 'pending'
                        CHECK (mapping_status IN ('pending', 'mapped', 'skipped', 'error')),
    mapping_notes       TEXT,
    mapped_at           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT pk_assignment_mapping PRIMARY KEY (v1_assignment_id),
    CONSTRAINT uq_assignment_mapping_v2 UNIQUE (v2_assignment_id)
);

COMMENT ON TABLE migration.assignment_mapping IS
    'Tracks V1 resource_assignments → V2 work.assignments mapping.';

-- =============================================================================
-- 7. UNMAPPABLE RECORDS LOG
-- =============================================================================

CREATE TABLE migration.unmappable_records (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_table        TEXT NOT NULL,
    source_id           UUID NOT NULL,
    target_table        TEXT NOT NULL,
    failure_reason      TEXT NOT NULL,
    source_data_json    JSONB,
    resolution_status   TEXT NOT NULL DEFAULT 'open'
                        CHECK (resolution_status IN ('open', 'resolved', 'accepted', 'dropped')),
    resolution_notes    TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at         TIMESTAMPTZ
);

COMMENT ON TABLE migration.unmappable_records IS
    'Records that cannot be automatically mapped during migration. '
    'Requires human review for resolution.';

CREATE INDEX idx_unmappable_source ON migration.unmappable_records (source_table, source_id);
CREATE INDEX idx_unmappable_status ON migration.unmappable_records (resolution_status);

-- =============================================================================
-- 8. MIGRATION AUDIT LOG
-- =============================================================================

CREATE TABLE migration.audit_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_run_id    UUID NOT NULL,
    operation           TEXT NOT NULL
                        CHECK (operation IN (
                            'start_run', 'end_run',
                            'migrate_projects', 'migrate_scopes', 'migrate_tasks', 'migrate_assignments',
                            'validate_counts', 'validate_fk_integrity', 'validate_enum_distribution',
                            'rollback', 'error', 'warning', 'info'
                        )),
    source_table        TEXT,
    target_table        TEXT,
    rows_affected       INTEGER,
    rows_skipped        INTEGER,
    rows_errored        INTEGER,
    details             JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE migration.audit_log IS
    'Append-only audit trail for migration runs. Every migration operation '
    'is logged for traceability and reconciliation.';

CREATE INDEX idx_audit_log_run ON migration.audit_log (migration_run_id, created_at);
CREATE INDEX idx_audit_log_operation ON migration.audit_log (operation);

-- =============================================================================
-- 9. ENUM CONVERSION FUNCTIONS
-- =============================================================================

-- 9.1 V1 project_status → V2 work.project_status_enum
CREATE OR REPLACE FUNCTION migration.convert_project_status(v1_status TEXT)
RETURNS work.project_status_enum
LANGUAGE sql IMMUTABLE STRICT AS $$
    SELECT CASE v1_status
        WHEN 'Draft'     THEN 'draft'::work.project_status_enum
        WHEN 'Quoted'    THEN 'draft'::work.project_status_enum       -- pre-award collapses to draft
        WHEN 'Won'       THEN 'active'::work.project_status_enum      -- post-award → active
        WHEN 'Active'    THEN 'active'::work.project_status_enum
        WHEN 'On Hold'   THEN 'on_hold'::work.project_status_enum
        WHEN 'Complete'  THEN 'complete'::work.project_status_enum
        WHEN 'Cancelled' THEN 'cancelled'::work.project_status_enum
        ELSE NULL  -- unmappable values return NULL for human review
    END
$$;

COMMENT ON FUNCTION migration.convert_project_status(TEXT) IS
    'Maps V1 project_status enum values to V2 work.project_status_enum. '
    'Quoted→draft, Won→active per packet-009 mapping §2.5.';

-- 9.2 V1 scope_status → V2 work.wp_lifecycle_enum
CREATE OR REPLACE FUNCTION migration.convert_scope_status(v1_status TEXT)
RETURNS work.wp_lifecycle_enum
LANGUAGE sql IMMUTABLE STRICT AS $$
    SELECT CASE v1_status
        WHEN 'Not Started'  THEN 'draft'::work.wp_lifecycle_enum
        WHEN 'In Progress'  THEN 'active'::work.wp_lifecycle_enum
        WHEN 'On Hold'      THEN 'blocked'::work.wp_lifecycle_enum    -- best available match
        WHEN 'Complete'     THEN 'complete'::work.wp_lifecycle_enum
        WHEN 'Cancelled'    THEN 'cancelled'::work.wp_lifecycle_enum
        ELSE NULL
    END
$$;

COMMENT ON FUNCTION migration.convert_scope_status(TEXT) IS
    'Maps V1 scope_status to V2 wp_lifecycle_enum. On Hold→blocked per packet-009 §2.5.';

-- 9.3 V1 task_status → V2 work.task_lifecycle_enum
CREATE OR REPLACE FUNCTION migration.convert_task_status(v1_status TEXT)
RETURNS work.task_lifecycle_enum
LANGUAGE sql IMMUTABLE STRICT AS $$
    SELECT CASE v1_status
        WHEN 'Not Started'  THEN 'not_started'::work.task_lifecycle_enum
        WHEN 'In Progress'  THEN 'active'::work.task_lifecycle_enum
        WHEN 'On Hold'      THEN 'on_hold'::work.task_lifecycle_enum
        WHEN 'Complete'     THEN 'complete'::work.task_lifecycle_enum
        WHEN 'Cancelled'    THEN 'cancelled'::work.task_lifecycle_enum
        ELSE NULL
    END
$$;

COMMENT ON FUNCTION migration.convert_task_status(TEXT) IS
    'Maps V1 task_status to V2 task_lifecycle_enum. Clean 1:1 mapping per packet-009 §2.5.';

-- 9.4 V1 scope_type → V2 work.work_type_enum
CREATE OR REPLACE FUNCTION migration.convert_scope_type(v1_type TEXT)
RETURNS work.work_type_enum
LANGUAGE sql IMMUTABLE STRICT AS $$
    SELECT CASE v1_type
        WHEN 'OTHER' THEN 'other'::work.work_type_enum
        ELSE 'testing'::work.work_type_enum  -- all NETA apparatus categories → testing
    END
$$;

COMMENT ON FUNCTION migration.convert_scope_type(TEXT) IS
    'Maps V1 scope_type (15 apparatus categories) to V2 work_type_enum. '
    'Almost all RESA work is testing. Original scope_type preserved in apparatus_cluster_ref.';

-- 9.5 V1 scope_type → apparatus_cluster_ref (preserve equipment classification)
CREATE OR REPLACE FUNCTION migration.scope_type_to_apparatus_cluster(v1_type TEXT)
RETURNS TEXT
LANGUAGE sql IMMUTABLE STRICT AS $$
    SELECT CASE v1_type
        WHEN 'ATS'   THEN 'ats'
        WHEN 'SWGR'  THEN 'switchgear'
        WHEN 'XFMR'  THEN 'transformer'
        WHEN 'PDC'   THEN 'power-distribution-center'
        WHEN 'MCC'   THEN 'motor-control-center'
        WHEN 'CB'    THEN 'circuit-breaker'
        WHEN 'RELAY' THEN 'relay'
        WHEN 'CABLE' THEN 'cable'
        WHEN 'BATT'  THEN 'battery'
        WHEN 'UPS'   THEN 'ups'
        WHEN 'GEN'   THEN 'generator'
        WHEN 'VFD'   THEN 'vfd'
        WHEN 'CAP'   THEN 'capacitor'
        WHEN 'GND'   THEN 'ground'
        WHEN 'OTHER' THEN 'other'
        ELSE v1_type  -- pass through unknown values
    END
$$;

COMMENT ON FUNCTION migration.scope_type_to_apparatus_cluster(TEXT) IS
    'Preserves V1 scope_type equipment classification as apparatus_cluster_ref text '
    'on work_packages, since work_type collapses all to testing.';

-- 9.6 V1 assignment_type → V2 work.assignment_role_enum
CREATE OR REPLACE FUNCTION migration.convert_assignment_type(v1_type TEXT)
RETURNS work.assignment_role_enum
LANGUAGE sql IMMUTABLE STRICT AS $$
    SELECT CASE v1_type
        WHEN 'Primary'    THEN 'primary'::work.assignment_role_enum
        WHEN 'Secondary'  THEN 'secondary'::work.assignment_role_enum
        WHEN 'Observer'   THEN 'observer'::work.assignment_role_enum
        WHEN 'Consultant' THEN 'support'::work.assignment_role_enum   -- closest match
        ELSE NULL
    END
$$;

COMMENT ON FUNCTION migration.convert_assignment_type(TEXT) IS
    'Maps V1 assignment_type to V2 assignment_role_enum. Consultant→support per packet-009 §2.5.';

-- =============================================================================
-- 10. DATE CONVERSION HELPER
-- =============================================================================

CREATE OR REPLACE FUNCTION migration.date_to_timestamptz(
    v1_date DATE,
    tz TEXT DEFAULT NULL
)
RETURNS TIMESTAMPTZ
LANGUAGE sql STABLE AS $$
    SELECT CASE WHEN v1_date IS NULL THEN NULL
    ELSE
        (v1_date::TEXT || ' 00:00:00')::TIMESTAMP
        AT TIME ZONE COALESCE(
            tz,
            (SELECT config_value FROM migration.config WHERE config_key = 'default_timezone')
        )
    END
$$;

COMMENT ON FUNCTION migration.date_to_timestamptz(DATE, TEXT) IS
    'Converts V1 date columns to timestamptz using the configured default timezone '
    '(America/Denver) or a per-call override. Midnight local time is assumed.';

-- =============================================================================
-- 11. MIGRATION RUN HELPER
-- =============================================================================

CREATE OR REPLACE FUNCTION migration.start_run(run_label TEXT DEFAULT NULL)
RETURNS UUID
LANGUAGE plpgsql AS $$
DECLARE
    new_run_id UUID := gen_random_uuid();
BEGIN
    INSERT INTO migration.audit_log (migration_run_id, operation, details)
    VALUES (new_run_id, 'start_run', jsonb_build_object(
        'label', COALESCE(run_label, 'unnamed'),
        'started_at', now()::TEXT
    ));
    RETURN new_run_id;
END;
$$;

COMMENT ON FUNCTION migration.start_run(TEXT) IS
    'Initializes a new migration run and returns the run UUID for subsequent log entries.';

CREATE OR REPLACE FUNCTION migration.end_run(run_id UUID, outcome TEXT DEFAULT 'success')
RETURNS VOID
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO migration.audit_log (migration_run_id, operation, details)
    VALUES (run_id, 'end_run', jsonb_build_object(
        'outcome', outcome,
        'ended_at', now()::TEXT
    ));
END;
$$;

COMMENT ON FUNCTION migration.end_run(UUID, TEXT) IS
    'Closes a migration run with an outcome label for the audit trail.';

-- =============================================================================
-- 12. DRY-RUN READINESS VIEW
-- =============================================================================

CREATE OR REPLACE VIEW migration.v_dry_run_readiness AS
SELECT
    'scope_to_wp_mapping_populated' AS check_name,
    CASE WHEN (SELECT count(*) FROM migration.scope_to_wp_mapping) > 0
         THEN 'READY' ELSE 'BLOCKED — no V1 scope data loaded'
    END AS status,
    (SELECT count(*) FROM migration.scope_to_wp_mapping) AS detail_count

UNION ALL
SELECT
    'project_id_mapping_populated',
    CASE WHEN (SELECT count(*) FROM migration.project_id_mapping) > 0
         THEN 'READY' ELSE 'BLOCKED — no V1 project data loaded'
    END,
    (SELECT count(*) FROM migration.project_id_mapping)

UNION ALL
SELECT
    'task_id_mapping_populated',
    CASE WHEN (SELECT count(*) FROM migration.task_id_mapping) > 0
         THEN 'READY' ELSE 'BLOCKED — no V1 task data loaded'
    END,
    (SELECT count(*) FROM migration.task_id_mapping)

UNION ALL
SELECT
    'enum_functions_exist',
    CASE WHEN (
        SELECT count(*) FROM information_schema.routines
        WHERE routine_schema = 'migration'
          AND routine_name LIKE 'convert_%'
    ) >= 4 THEN 'READY' ELSE 'BLOCKED — conversion functions missing'
    END,
    (SELECT count(*) FROM information_schema.routines
     WHERE routine_schema = 'migration' AND routine_name LIKE 'convert_%')

UNION ALL
SELECT
    'audit_log_exists',
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'migration' AND table_name = 'audit_log'
    ) THEN 'READY' ELSE 'BLOCKED — audit_log table missing'
    END,
    NULL

UNION ALL
SELECT
    'work_schema_validated',
    CASE WHEN (
        SELECT count(*) FROM information_schema.tables
        WHERE table_schema = 'work' AND table_type = 'BASE TABLE'
    ) = 8 THEN 'READY' ELSE 'BLOCKED — work schema incomplete'
    END,
    (SELECT count(*) FROM information_schema.tables
     WHERE table_schema = 'work' AND table_type = 'BASE TABLE')

UNION ALL
SELECT
    'timezone_config_set',
    CASE WHEN EXISTS (
        SELECT 1 FROM migration.config WHERE config_key = 'default_timezone'
    ) THEN 'READY' ELSE 'BLOCKED — timezone not configured'
    END,
    NULL;

COMMENT ON VIEW migration.v_dry_run_readiness IS
    'Pre-flight checklist for dry-run migration readiness. '
    'All checks must show READY before a dry-run migration packet can execute.';
