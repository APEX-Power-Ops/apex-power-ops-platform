-- =============================================================================
-- PM/Work Domain — Core Tables
-- Packet: 2026-04-13-pm-schema-007
-- Authority: PM-DOMAIN-IMPLEMENTATION-READY-SCHEMA-SPEC-2026-04-12.md §4
-- Landing Lane: infra/database/migrations/work/
--
-- Dependency order:
--   projects → wbs_nodes → work_packages → tasks → dependencies →
--   assignments → execution_issues → progress_snapshots
--
-- DEFERRED CROSS-DOMAIN FKs:
--   All FK references to org.*, identity.*, asset.*, integration.*, and
--   audit.* schemas are omitted because those schemas do not yet exist in
--   the clean staging environment. Columns are created with the correct
--   type and nullability. A follow-up migration will add the FK constraints
--   when the target domains are ready.
--
--   Deferred FKs:
--     projects.client_id        → org.clients
--     projects.site_id          → org.sites
--     projects.business_unit_id → org.business_units
--     projects.contract_id      → org.contracts
--     work_packages.client_id   → org.clients
--     work_packages.site_id     → org.sites
--     work_packages.assigned_crew_id    → identity.crews
--     work_packages.asset_class_id      → asset.asset_classes
--     assignments.employee_id   → identity.employees
--     assignments.crew_id       → identity.crews
--     execution_issues.reported_by → identity.users
--     execution_issues.assigned_to → identity.users
--     progress_snapshots.approved_by → identity.users
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 4.1 projects
-- ---------------------------------------------------------------------------

CREATE TABLE work.projects (
    project_id              uuid            NOT NULL DEFAULT gen_random_uuid(),
    project_code            text            NOT NULL,
    title                   text            NOT NULL,
    status                  work.project_status_enum NOT NULL DEFAULT 'draft',
    client_id               uuid            NOT NULL,        -- DEFERRED FK → org.clients
    site_id                 uuid            NOT NULL,        -- DEFERRED FK → org.sites
    business_unit_id        uuid            NULL,            -- DEFERRED FK → org.business_units
    description             text            NULL,
    contract_id             uuid            NULL,            -- DEFERRED FK → org.contracts
    planned_start_at        timestamptz     NULL,
    planned_end_at          timestamptz     NULL,
    actual_start_at         timestamptz     NULL,
    actual_end_at           timestamptz     NULL,
    project_priority        text            NULL,
    created_from_source     work.provenance_source_enum NOT NULL DEFAULT 'manual',
    provenance_status       work.provenance_status_enum NOT NULL DEFAULT 'curated',
    p6_project_id           text            NULL,
    p6_short_name           text            NULL,
    p6_data_date            timestamptz     NULL,
    created_at              timestamptz     NOT NULL DEFAULT now(),
    updated_at              timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_projects PRIMARY KEY (project_id),
    CONSTRAINT uq_projects_project_code UNIQUE (project_code),
    CONSTRAINT ck_projects_planned_dates
        CHECK (planned_end_at IS NULL OR planned_start_at IS NULL OR planned_end_at > planned_start_at)
);

COMMENT ON TABLE work.projects IS
    'Top-level project container. Parent of work packages, WBS nodes, and progress snapshots.';

-- ---------------------------------------------------------------------------
-- 4.4 wbs_nodes  (before work_packages — WP references wbs_nodes)
-- ---------------------------------------------------------------------------

CREATE TABLE work.wbs_nodes (
    wbs_node_id             uuid            NOT NULL DEFAULT gen_random_uuid(),
    project_id              uuid            NOT NULL,
    parent_wbs_node_id      uuid            NULL,
    wbs_code                text            NOT NULL,
    title                   text            NOT NULL,
    sort_order              integer         NULL,
    p6_wbs_id               text            NULL,
    p6_parent_wbs_id        text            NULL,
    created_from_source     work.provenance_source_enum NOT NULL DEFAULT 'manual',
    created_at              timestamptz     NOT NULL DEFAULT now(),
    updated_at              timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_wbs_nodes PRIMARY KEY (wbs_node_id),
    CONSTRAINT fk_wbs_nodes_project
        FOREIGN KEY (project_id) REFERENCES work.projects (project_id),
    CONSTRAINT fk_wbs_nodes_parent
        FOREIGN KEY (parent_wbs_node_id) REFERENCES work.wbs_nodes (wbs_node_id),
    CONSTRAINT uq_wbs_nodes_project_code UNIQUE (project_id, wbs_code)
);

COMMENT ON TABLE work.wbs_nodes IS
    'N-level work breakdown structure hierarchy within a project. Imported from P6 XER or manually created.';

-- ---------------------------------------------------------------------------
-- 4.2 work_packages  (the primary operating object)
-- ---------------------------------------------------------------------------

CREATE TABLE work.work_packages (
    work_package_id         uuid            NOT NULL DEFAULT gen_random_uuid(),
    project_id              uuid            NOT NULL,
    work_package_code       text            NOT NULL,
    title                   text            NOT NULL,
    work_type               work.work_type_enum NOT NULL,
    lifecycle_state         work.wp_lifecycle_enum NOT NULL DEFAULT 'draft',
    priority                work.priority_enum NOT NULL DEFAULT 'normal',
    client_id               uuid            NOT NULL,        -- DEFERRED FK → org.clients
    site_id                 uuid            NOT NULL,        -- DEFERRED FK → org.sites
    primary_wbs_node_id     uuid            NULL,
    scope_source_ref        uuid            NULL,            -- legacy scopes.scope_id traceability
    asset_class_id          uuid            NULL,            -- DEFERRED FK → asset.asset_classes
    apparatus_cluster_ref   text            NULL,
    assigned_crew_id        uuid            NULL,            -- DEFERRED FK → identity.crews
    scheduled_start_at      timestamptz     NULL,
    scheduled_end_at        timestamptz     NULL,
    actual_start_at         timestamptz     NULL,
    actual_end_at           timestamptz     NULL,
    progress_percent        numeric(5,2)    NULL,
    billing_state           work.billing_state_enum NULL,
    execution_summary       text            NULL,
    created_from_source     work.provenance_source_enum NOT NULL DEFAULT 'manual',
    provenance_status       work.provenance_status_enum NOT NULL DEFAULT 'curated',
    created_at              timestamptz     NOT NULL DEFAULT now(),
    updated_at              timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_work_packages PRIMARY KEY (work_package_id),
    CONSTRAINT fk_work_packages_project
        FOREIGN KEY (project_id) REFERENCES work.projects (project_id),
    CONSTRAINT fk_work_packages_wbs_node
        FOREIGN KEY (primary_wbs_node_id) REFERENCES work.wbs_nodes (wbs_node_id),
    CONSTRAINT uq_work_packages_project_code UNIQUE (project_id, work_package_code),
    CONSTRAINT ck_work_packages_scheduled_dates
        CHECK (scheduled_end_at IS NULL OR scheduled_start_at IS NULL OR scheduled_end_at > scheduled_start_at),
    CONSTRAINT ck_work_packages_progress
        CHECK (progress_percent IS NULL OR (progress_percent >= 0 AND progress_percent <= 100))
);

COMMENT ON TABLE work.work_packages IS
    'Primary operating object of the PM/work domain. Replaces the legacy scopes table. Spec §4.2.';
COMMENT ON COLUMN work.work_packages.scope_source_ref IS
    'Preserved legacy scopes.scope_id for traceability during V1→V2 migration. Not a FK.';

-- ---------------------------------------------------------------------------
-- 4.3 tasks
-- ---------------------------------------------------------------------------

CREATE TABLE work.tasks (
    task_id                     uuid            NOT NULL DEFAULT gen_random_uuid(),
    work_package_id             uuid            NOT NULL,
    task_code                   text            NULL,
    title                       text            NOT NULL,
    task_type                   work.task_type_enum NOT NULL DEFAULT 'task',
    lifecycle_state             work.task_lifecycle_enum NOT NULL DEFAULT 'not_started',
    planned_start_at            timestamptz     NULL,
    planned_end_at              timestamptz     NULL,
    actual_start_at             timestamptz     NULL,
    actual_end_at               timestamptz     NULL,
    early_start_at              timestamptz     NULL,            -- P6 planning truth
    early_end_at                timestamptz     NULL,            -- P6 planning truth
    late_start_at               timestamptz     NULL,            -- P6 planning truth
    late_end_at                 timestamptz     NULL,            -- P6 planning truth
    duration_hours              numeric(10,2)   NULL,            -- calendar duration, NOT labor
    remaining_duration_hours    numeric(10,2)   NULL,
    estimated_labor_hours       numeric(10,2)   NULL,
    actual_labor_hours          numeric(10,2)   NULL,
    total_float_hours           numeric(10,2)   NULL,
    schedule_priority_override  work.priority_enum NULL,
    primary_wbs_node_id         uuid            NULL,
    p6_task_id                  text            NULL,
    p6_activity_id              text            NULL,
    p6_calendar_id              text            NULL,
    created_from_source         work.provenance_source_enum NOT NULL DEFAULT 'manual',
    provenance_status           work.provenance_status_enum NOT NULL DEFAULT 'curated',
    created_at                  timestamptz     NOT NULL DEFAULT now(),
    updated_at                  timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_tasks PRIMARY KEY (task_id),
    CONSTRAINT fk_tasks_work_package
        FOREIGN KEY (work_package_id) REFERENCES work.work_packages (work_package_id),
    CONSTRAINT fk_tasks_wbs_node
        FOREIGN KEY (primary_wbs_node_id) REFERENCES work.wbs_nodes (wbs_node_id),
    CONSTRAINT uq_tasks_wp_code UNIQUE (work_package_id, task_code),
    CONSTRAINT ck_tasks_planned_dates
        CHECK (planned_end_at IS NULL OR planned_start_at IS NULL OR planned_end_at > planned_start_at)
);

COMMENT ON TABLE work.tasks IS
    'Schedulable unit of work within a work package. Aligned with P6 activities. Spec §4.3.';
COMMENT ON COLUMN work.tasks.early_start_at IS 'P6 planning truth — early start from CPM forward pass.';
COMMENT ON COLUMN work.tasks.total_float_hours IS 'P6 schedule-risk indicator. Float = 0 means critical path.';

-- ---------------------------------------------------------------------------
-- 4.5 dependencies
-- ---------------------------------------------------------------------------

CREATE TABLE work.dependencies (
    dependency_id           uuid            NOT NULL DEFAULT gen_random_uuid(),
    predecessor_task_id     uuid            NOT NULL,
    successor_task_id       uuid            NOT NULL,
    relationship_type       work.dependency_type_enum NOT NULL DEFAULT 'FS',
    lag_hours               numeric(10,2)   NULL DEFAULT 0,
    source_system           work.provenance_source_enum NOT NULL DEFAULT 'manual',
    p6_relationship_id      text            NULL,
    is_active               boolean         NOT NULL DEFAULT true,
    created_from_source     work.provenance_source_enum NOT NULL DEFAULT 'manual',
    created_at              timestamptz     NOT NULL DEFAULT now(),
    updated_at              timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_dependencies PRIMARY KEY (dependency_id),
    CONSTRAINT fk_dependencies_predecessor
        FOREIGN KEY (predecessor_task_id) REFERENCES work.tasks (task_id),
    CONSTRAINT fk_dependencies_successor
        FOREIGN KEY (successor_task_id) REFERENCES work.tasks (task_id),
    CONSTRAINT uq_dependencies_relationship
        UNIQUE (predecessor_task_id, successor_task_id, relationship_type)
);

COMMENT ON TABLE work.dependencies IS
    'Task-to-task schedule relationships (FS/SS/SF/FF with optional lag). Spec §4.5.';

-- ---------------------------------------------------------------------------
-- 4.6 assignments
-- ---------------------------------------------------------------------------

CREATE TABLE work.assignments (
    assignment_id           uuid            NOT NULL DEFAULT gen_random_uuid(),
    work_package_id         uuid            NULL,
    task_id                 uuid            NULL,
    employee_id             uuid            NULL,            -- DEFERRED FK → identity.employees
    crew_id                 uuid            NULL,            -- DEFERRED FK → identity.crews
    assignment_role         work.assignment_role_enum NOT NULL DEFAULT 'primary',
    planned_hours           numeric(10,2)   NULL,
    actual_hours            numeric(10,2)   NULL,
    start_at                timestamptz     NULL,
    end_at                  timestamptz     NULL,
    p6_task_resource_id     text            NULL,
    p6_resource_id          text            NULL,
    is_actual_participation boolean         NOT NULL DEFAULT false,
    created_from_source     work.provenance_source_enum NOT NULL DEFAULT 'manual',
    created_at              timestamptz     NOT NULL DEFAULT now(),
    updated_at              timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_assignments PRIMARY KEY (assignment_id),
    CONSTRAINT fk_assignments_work_package
        FOREIGN KEY (work_package_id) REFERENCES work.work_packages (work_package_id),
    CONSTRAINT fk_assignments_task
        FOREIGN KEY (task_id) REFERENCES work.tasks (task_id),
    CONSTRAINT ck_assignments_at_least_one_parent
        CHECK (work_package_id IS NOT NULL OR task_id IS NOT NULL)
);

COMMENT ON TABLE work.assignments IS
    'Resource assignments at work-package or task level. Spec §4.6.';
COMMENT ON COLUMN work.assignments.is_actual_participation IS
    'True if this assignment reflects actual field participation, false if scheduled/planned only.';

-- ---------------------------------------------------------------------------
-- 4.7 execution_issues
-- ---------------------------------------------------------------------------

CREATE TABLE work.execution_issues (
    execution_issue_id      uuid            NOT NULL DEFAULT gen_random_uuid(),
    work_package_id         uuid            NULL,
    task_id                 uuid            NULL,
    apparatus_ref           uuid            NULL,            -- asset-side linkage (not FK — asset domain not yet available)
    issue_type              work.issue_type_enum NOT NULL,
    severity                work.severity_enum NOT NULL,
    status                  work.issue_status_enum NOT NULL DEFAULT 'open',
    blocks_completion       boolean         NOT NULL DEFAULT false,
    summary                 text            NOT NULL,
    details                 text            NULL,
    reported_by             uuid            NULL,            -- DEFERRED FK → identity.users
    assigned_to             uuid            NULL,            -- DEFERRED FK → identity.users
    resolution_type         work.resolution_type_enum NULL,
    opened_at               timestamptz     NOT NULL DEFAULT now(),
    resolved_at             timestamptz     NULL,
    closed_at               timestamptz     NULL,
    created_from_source     work.provenance_source_enum NOT NULL DEFAULT 'manual',
    created_at              timestamptz     NOT NULL DEFAULT now(),
    updated_at              timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_execution_issues PRIMARY KEY (execution_issue_id),
    CONSTRAINT fk_execution_issues_work_package
        FOREIGN KEY (work_package_id) REFERENCES work.work_packages (work_package_id),
    CONSTRAINT fk_execution_issues_task
        FOREIGN KEY (task_id) REFERENCES work.tasks (task_id)
);

COMMENT ON TABLE work.execution_issues IS
    'Field execution issues (equipment not ready, test failures, safety holds, etc.). Spec §4.7.';
COMMENT ON COLUMN work.execution_issues.blocks_completion IS
    'When true, the parent work package or task cannot transition to complete until this issue is resolved.';

-- ---------------------------------------------------------------------------
-- 4.8 progress_snapshots
-- ---------------------------------------------------------------------------

CREATE TABLE work.progress_snapshots (
    progress_snapshot_id    uuid            NOT NULL DEFAULT gen_random_uuid(),
    project_id              uuid            NOT NULL,
    work_package_id         uuid            NULL,
    task_id                 uuid            NULL,
    snapshot_period_start   date            NOT NULL,
    snapshot_period_end     date            NOT NULL,
    snapshot_status         work.snapshot_status_enum NOT NULL DEFAULT 'draft',
    completed_apparatus_count integer       NULL,
    total_apparatus_count   integer         NULL,
    percent_complete        numeric(5,2)    NULL,
    actual_labor_hours      numeric(10,2)   NULL,
    billable_amount         numeric(12,2)   NULL,
    billing_reference       text            NULL,
    approved_by             uuid            NULL,            -- DEFERRED FK → identity.users
    approved_at             timestamptz     NULL,
    supersedes_snapshot_id  uuid            NULL,
    source_data_date        timestamptz     NULL,
    created_from_source     work.provenance_source_enum NOT NULL DEFAULT 'manual',
    created_at              timestamptz     NOT NULL DEFAULT now(),
    updated_at              timestamptz     NOT NULL DEFAULT now(),

    CONSTRAINT pk_progress_snapshots PRIMARY KEY (progress_snapshot_id),
    CONSTRAINT fk_progress_snapshots_project
        FOREIGN KEY (project_id) REFERENCES work.projects (project_id),
    CONSTRAINT fk_progress_snapshots_work_package
        FOREIGN KEY (work_package_id) REFERENCES work.work_packages (work_package_id),
    CONSTRAINT fk_progress_snapshots_task
        FOREIGN KEY (task_id) REFERENCES work.tasks (task_id),
    CONSTRAINT fk_progress_snapshots_supersedes
        FOREIGN KEY (supersedes_snapshot_id) REFERENCES work.progress_snapshots (progress_snapshot_id),
    CONSTRAINT ck_progress_snapshots_period
        CHECK (snapshot_period_end >= snapshot_period_start),
    CONSTRAINT ck_progress_snapshots_percent
        CHECK (percent_complete IS NULL OR (percent_complete >= 0 AND percent_complete <= 100)),
    CONSTRAINT ck_progress_snapshots_apparatus_counts
        CHECK (
            (completed_apparatus_count IS NULL OR completed_apparatus_count >= 0)
            AND (total_apparatus_count IS NULL OR total_apparatus_count >= 0)
        )
);

COMMENT ON TABLE work.progress_snapshots IS
    'Period-truth progress reporting with approval workflow and snapshot superseding. Spec §4.8.';
COMMENT ON COLUMN work.progress_snapshots.supersedes_snapshot_id IS
    'Points to an earlier approved snapshot that this snapshot corrects. Original retains its approved status.';
