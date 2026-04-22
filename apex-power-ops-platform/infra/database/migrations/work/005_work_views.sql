-- =============================================================================
-- PM/Work Domain — Views
-- Packet: 2026-04-13-pm-schema-007
-- Authority: PM-DOMAIN-IMPLEMENTATION-READY-SCHEMA-SPEC-2026-04-12.md §8
-- Landing Lane: infra/database/migrations/work/
--
-- DEFERRED VIEW:
--   v_p6_binding_status (§8.6): DEFERRED because it requires a join to
--   integration.p6_sync_log which does not yet exist. The view can be
--   added in a follow-up migration when the integration domain is available.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 8.1 v_work_package_status — Operational dashboard view
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW work.v_work_package_status AS
SELECT
    wp.*,
    -- Derived: is_overdue
    CASE
        WHEN wp.scheduled_end_at < now()
             AND wp.lifecycle_state IN ('active', 'blocked', 'awaiting_review')
        THEN true
        ELSE false
    END AS is_overdue,
    -- Derived: is_at_risk (based on child tasks with low float)
    EXISTS (
        SELECT 1 FROM work.tasks t
        WHERE t.work_package_id = wp.work_package_id
          AND t.total_float_hours IS NOT NULL
          AND t.total_float_hours > 0
          AND t.total_float_hours <= 80
          AND t.lifecycle_state NOT IN ('complete', 'cancelled')
    ) AS is_at_risk,
    -- Derived: is_blocked_by_issue
    EXISTS (
        SELECT 1 FROM work.execution_issues ei
        WHERE ei.work_package_id = wp.work_package_id
          AND ei.blocks_completion = true
          AND ei.status NOT IN ('resolved', 'closed')
    ) AS is_blocked_by_issue,
    -- Active issue count
    (
        SELECT COUNT(*)::integer FROM work.execution_issues ei
        WHERE ei.work_package_id = wp.work_package_id
          AND ei.status NOT IN ('closed')
    ) AS active_issue_count,
    -- Task completion percent
    work.fn_compute_wp_progress(wp.work_package_id) AS task_completion_percent,
    -- Joined: project title
    p.title AS project_title
FROM work.work_packages wp
JOIN work.projects p ON p.project_id = wp.project_id;

COMMENT ON VIEW work.v_work_package_status IS
    'Operational dashboard view: stored WP state + derived overdue/risk/blocking indicators. Spec §8.1.';

-- ---------------------------------------------------------------------------
-- 8.2 v_task_schedule — Schedule-focused view with P6 data
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW work.v_task_schedule AS
SELECT
    t.*,
    -- Derived: schedule_priority_computed
    work.fn_compute_schedule_priority(t.total_float_hours) AS schedule_priority_computed,
    -- Derived: effective_priority
    COALESCE(
        t.schedule_priority_override,
        work.fn_compute_schedule_priority(t.total_float_hours),
        'normal'::work.priority_enum
    ) AS effective_priority,
    -- Derived: is_overdue
    CASE
        WHEN t.planned_end_at < now()
             AND t.lifecycle_state NOT IN ('complete', 'cancelled')
        THEN true
        ELSE false
    END AS is_overdue,
    -- Derived: is_critical_path
    CASE
        WHEN t.total_float_hours IS NOT NULL AND t.total_float_hours = 0
        THEN true
        ELSE false
    END AS is_critical_path,
    -- Joined
    wp.title AS work_package_title,
    wp.lifecycle_state AS work_package_lifecycle_state
FROM work.tasks t
JOIN work.work_packages wp ON wp.work_package_id = t.work_package_id;

COMMENT ON VIEW work.v_task_schedule IS
    'Schedule-focused task view with computed priority from float thresholds. Spec §8.2.';

-- ---------------------------------------------------------------------------
-- 8.3 v_wbs_hierarchy — Recursive WBS display
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW work.v_wbs_hierarchy AS
WITH RECURSIVE wbs_tree AS (
    -- Base case: root nodes (no parent)
    SELECT
        wn.wbs_node_id,
        wn.project_id,
        wn.parent_wbs_node_id,
        wn.wbs_code,
        wn.title,
        wn.sort_order,
        wn.p6_wbs_id,
        wn.p6_parent_wbs_id,
        wn.created_from_source,
        wn.created_at,
        wn.updated_at,
        0 AS depth,
        wn.wbs_code AS path
    FROM work.wbs_nodes wn
    WHERE wn.parent_wbs_node_id IS NULL

    UNION ALL

    -- Recursive case: children
    SELECT
        child.wbs_node_id,
        child.project_id,
        child.parent_wbs_node_id,
        child.wbs_code,
        child.title,
        child.sort_order,
        child.p6_wbs_id,
        child.p6_parent_wbs_id,
        child.created_from_source,
        child.created_at,
        child.updated_at,
        parent.depth + 1,
        parent.path || '.' || child.wbs_code
    FROM work.wbs_nodes child
    JOIN wbs_tree parent ON parent.wbs_node_id = child.parent_wbs_node_id
)
SELECT
    wt.*,
    (
        SELECT COUNT(*)::integer
        FROM work.work_packages wp
        WHERE wp.primary_wbs_node_id = wt.wbs_node_id
    ) AS work_package_count
FROM wbs_tree wt;

COMMENT ON VIEW work.v_wbs_hierarchy IS
    'Recursive WBS hierarchy with computed depth, materialized path, and aligned work-package count. Spec §8.3.';

-- ---------------------------------------------------------------------------
-- 8.4 v_execution_issue_dashboard — Issue monitoring view
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW work.v_execution_issue_dashboard AS
SELECT
    ei.*,
    -- Joined
    wp.title AS work_package_title,
    t.title AS task_title,
    -- Derived: days_open
    EXTRACT(DAY FROM (now() - ei.opened_at))::integer AS days_open,
    -- Derived: escalation_level
    CASE
        WHEN ei.severity = 'critical' AND EXTRACT(DAY FROM (now() - ei.opened_at)) > 1
            THEN 'immediate'
        WHEN ei.severity = 'critical'
            THEN 'high'
        WHEN ei.severity = 'major' AND EXTRACT(DAY FROM (now() - ei.opened_at)) > 3
            THEN 'high'
        WHEN ei.severity = 'major'
            THEN 'standard'
        WHEN EXTRACT(DAY FROM (now() - ei.opened_at)) > 7
            THEN 'standard'
        ELSE 'low'
    END AS escalation_level
FROM work.execution_issues ei
LEFT JOIN work.work_packages wp ON wp.work_package_id = ei.work_package_id
LEFT JOIN work.tasks t ON t.task_id = ei.task_id;

COMMENT ON VIEW work.v_execution_issue_dashboard IS
    'Issue monitoring view with blocking-effect context and computed escalation level. Spec §8.4.';

-- ---------------------------------------------------------------------------
-- 8.5 v_progress_current — Current-period progress resolving supersedes
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW work.v_progress_current AS
SELECT
    ps.*,
    -- Derived: is_latest_for_period
    NOT EXISTS (
        SELECT 1 FROM work.progress_snapshots newer
        WHERE newer.supersedes_snapshot_id = ps.progress_snapshot_id
    ) AS is_latest_for_period,
    -- Joined
    wp.title AS work_package_title,
    p.title AS project_title
FROM work.progress_snapshots ps
LEFT JOIN work.work_packages wp ON wp.work_package_id = ps.work_package_id
JOIN work.projects p ON p.project_id = ps.project_id;

COMMENT ON VIEW work.v_progress_current IS
    'Current-period progress view resolving snapshot superseding chains. Spec §8.5.';

-- ---------------------------------------------------------------------------
-- 8.6 v_p6_binding_status — DEFERRED
--
-- This view requires a join to integration.p6_sync_log which does not yet
-- exist. It will be created in a follow-up migration when the integration
-- domain is available.
--
-- Required columns per spec §8.6:
--   entity_type, entity_id, entity_title, has_p6_binding,
--   p6_identifier, last_sync_at, sync_status
-- ---------------------------------------------------------------------------
