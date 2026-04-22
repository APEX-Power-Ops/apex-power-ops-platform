-- =============================================================================
-- PM/Work Domain — Indexes
-- Packet: 2026-04-13-pm-schema-007
-- Authority: PM-DOMAIN-IMPLEMENTATION-READY-SCHEMA-SPEC-2026-04-12.md §11
-- Landing Lane: infra/database/migrations/work/
-- =============================================================================

-- ---------------------------------------------------------------------------
-- projects
-- ---------------------------------------------------------------------------
-- PK and UNIQUE on project_code already create implicit indexes.
-- Additional indexes on status for dashboard filtering:
CREATE INDEX idx_projects_status ON work.projects (status);

-- ---------------------------------------------------------------------------
-- wbs_nodes
-- ---------------------------------------------------------------------------
-- PK and UNIQUE(project_id, wbs_code) already create implicit indexes.
-- Hierarchy traversal:
CREATE INDEX idx_wbs_nodes_project_parent
    ON work.wbs_nodes (project_id, parent_wbs_node_id);

-- ---------------------------------------------------------------------------
-- work_packages
-- ---------------------------------------------------------------------------
-- PK and UNIQUE(project_id, work_package_code) already create implicit indexes.

-- Parent project lookup:
CREATE INDEX idx_work_packages_project_id
    ON work.work_packages (project_id);

-- Dashboard filtering by lifecycle state:
CREATE INDEX idx_work_packages_lifecycle_state
    ON work.work_packages (lifecycle_state);

-- Crew workload queries:
CREATE INDEX idx_work_packages_assigned_crew_id
    ON work.work_packages (assigned_crew_id)
    WHERE assigned_crew_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- tasks
-- ---------------------------------------------------------------------------
-- PK and UNIQUE(work_package_id, task_code) already create implicit indexes.

-- Parent work package lookup:
CREATE INDEX idx_tasks_work_package_id
    ON work.tasks (work_package_id);

-- Status queries:
CREATE INDEX idx_tasks_lifecycle_state
    ON work.tasks (lifecycle_state);

-- Import reconciliation (P6 task binding):
CREATE INDEX idx_tasks_p6_task_id
    ON work.tasks (p6_task_id)
    WHERE p6_task_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- dependencies
-- ---------------------------------------------------------------------------
-- PK and UNIQUE(predecessor, successor, type) already create implicit indexes.

-- Dependency traversal:
CREATE INDEX idx_dependencies_predecessor
    ON work.dependencies (predecessor_task_id);

CREATE INDEX idx_dependencies_successor
    ON work.dependencies (successor_task_id);

-- ---------------------------------------------------------------------------
-- assignments
-- ---------------------------------------------------------------------------

-- Assignment lookup by work package:
CREATE INDEX idx_assignments_work_package_id
    ON work.assignments (work_package_id)
    WHERE work_package_id IS NOT NULL;

-- Assignment lookup by task:
CREATE INDEX idx_assignments_task_id
    ON work.assignments (task_id)
    WHERE task_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- execution_issues
-- ---------------------------------------------------------------------------

-- Issue dashboard (package + status):
CREATE INDEX idx_execution_issues_wp_status
    ON work.execution_issues (work_package_id, status)
    WHERE work_package_id IS NOT NULL;

-- Blocking issue fast-path:
CREATE INDEX idx_execution_issues_blocks_completion
    ON work.execution_issues (work_package_id)
    WHERE blocks_completion = true AND status NOT IN ('resolved', 'closed');

-- ---------------------------------------------------------------------------
-- progress_snapshots
-- ---------------------------------------------------------------------------

-- Period reporting:
CREATE INDEX idx_progress_snapshots_project_period
    ON work.progress_snapshots (project_id, snapshot_period_end);

-- Work-package-level snapshots:
CREATE INDEX idx_progress_snapshots_wp_id
    ON work.progress_snapshots (work_package_id)
    WHERE work_package_id IS NOT NULL;
