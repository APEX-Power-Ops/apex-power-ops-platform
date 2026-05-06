-- =============================================================================
-- RESA Power Platform - Schema Additions
-- =============================================================================
-- File: 09_schema_additions.sql
-- Generated: 2025-12-11
-- Purpose: Add missing fields identified from Excel tracker analysis
-- Run: AFTER existing schema is deployed
-- =============================================================================

-- =============================================================================
-- NEW ENUM: Apparatus Availability
-- =============================================================================
-- This drives daily operational visibility - "what can we work on today?"

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'apparatus_availability') THEN
        CREATE TYPE apparatus_availability AS ENUM (
            'Ready',           -- Equipment accessible, ready to test
            'On Hold',         -- Blocked by external factor (customer, parts, etc.)
            'Not Available'    -- Not yet accessible (construction, scheduling)
        );
    END IF;
END $$;

COMMENT ON TYPE apparatus_availability IS 'Operational availability for daily scheduling';

-- =============================================================================
-- APPARATUS TABLE ADDITIONS
-- =============================================================================
-- Fields identified from Excel tracker (tbl_PowerBI_Data)

ALTER TABLE apparatus ADD COLUMN IF NOT EXISTS availability apparatus_availability DEFAULT 'Not Available';
ALTER TABLE apparatus ADD COLUMN IF NOT EXISTS date_due DATE;
ALTER TABLE apparatus ADD COLUMN IF NOT EXISTS designation VARCHAR(100);
ALTER TABLE apparatus ADD COLUMN IF NOT EXISTS drawing_reference VARCHAR(200);
ALTER TABLE apparatus ADD COLUMN IF NOT EXISTS datasheet_complete BOOLEAN DEFAULT false;
ALTER TABLE apparatus ADD COLUMN IF NOT EXISTS task_delays INTEGER DEFAULT 0;
ALTER TABLE apparatus ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 0;  -- 1=High, 2=Medium, 3=Low, 0=None

-- Comments
COMMENT ON COLUMN apparatus.availability IS 'Operational availability: Ready/On Hold/Not Available';
COMMENT ON COLUMN apparatus.date_due IS 'Target completion date from schedule';
COMMENT ON COLUMN apparatus.designation IS 'Equipment designation (e.g., SWGR-001-A)';
COMMENT ON COLUMN apparatus.drawing_reference IS 'Reference to electrical drawing';
COMMENT ON COLUMN apparatus.datasheet_complete IS 'Whether datasheet has been filled out';
COMMENT ON COLUMN apparatus.task_delays IS 'Number of times this item has been delayed';
COMMENT ON COLUMN apparatus.priority IS 'Work priority: 1=High, 2=Medium, 3=Low, 0=None';

-- =============================================================================
-- TASK TABLE ADDITIONS - Rollup Date Fields
-- =============================================================================

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS date_due DATE;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS earliest_apparatus_due DATE;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS latest_apparatus_due DATE;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS earliest_apparatus_start DATE;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS latest_apparatus_start DATE;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS earliest_apparatus_complete DATE;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS latest_apparatus_complete DATE;

COMMENT ON COLUMN tasks.date_due IS 'Task-level due date';
COMMENT ON COLUMN tasks.earliest_apparatus_due IS 'MIN(apparatus.date_due) - earliest item due';
COMMENT ON COLUMN tasks.latest_apparatus_due IS 'MAX(apparatus.date_due) - latest item due';
COMMENT ON COLUMN tasks.earliest_apparatus_start IS 'MIN(apparatus.actual_start) - first work started';
COMMENT ON COLUMN tasks.latest_apparatus_start IS 'MAX(apparatus.actual_start) - last work started';
COMMENT ON COLUMN tasks.earliest_apparatus_complete IS 'MIN(apparatus.actual_end) - first item done';
COMMENT ON COLUMN tasks.latest_apparatus_complete IS 'MAX(apparatus.actual_end) - last item done';

-- =============================================================================
-- SCOPE TABLE ADDITIONS - Rollup Date Fields
-- =============================================================================

ALTER TABLE scopes ADD COLUMN IF NOT EXISTS date_due DATE;
ALTER TABLE scopes ADD COLUMN IF NOT EXISTS earliest_task_due DATE;
ALTER TABLE scopes ADD COLUMN IF NOT EXISTS latest_task_due DATE;
ALTER TABLE scopes ADD COLUMN IF NOT EXISTS earliest_task_start DATE;
ALTER TABLE scopes ADD COLUMN IF NOT EXISTS latest_task_start DATE;
ALTER TABLE scopes ADD COLUMN IF NOT EXISTS earliest_task_complete DATE;
ALTER TABLE scopes ADD COLUMN IF NOT EXISTS latest_task_complete DATE;

COMMENT ON COLUMN scopes.date_due IS 'Scope-level due date';
COMMENT ON COLUMN scopes.earliest_task_due IS 'MIN(tasks.date_due) - earliest task due';
COMMENT ON COLUMN scopes.latest_task_due IS 'MAX(tasks.date_due) - latest task due';
COMMENT ON COLUMN scopes.earliest_task_start IS 'MIN(tasks.actual_start) - first task started';
COMMENT ON COLUMN scopes.latest_task_start IS 'MAX(tasks.actual_start) - last task started';
COMMENT ON COLUMN scopes.earliest_task_complete IS 'MIN(tasks.actual_end) - first task done';
COMMENT ON COLUMN scopes.latest_task_complete IS 'MAX(tasks.actual_end) - last task done';

-- =============================================================================
-- PROJECT TABLE ADDITIONS - Rollup Date Fields
-- =============================================================================

ALTER TABLE projects ADD COLUMN IF NOT EXISTS date_due DATE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS earliest_scope_due DATE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS latest_scope_due DATE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS earliest_scope_start DATE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS latest_scope_start DATE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS earliest_scope_complete DATE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS latest_scope_complete DATE;

COMMENT ON COLUMN projects.date_due IS 'Project-level due date (contractual)';
COMMENT ON COLUMN projects.earliest_scope_due IS 'MIN(scopes.date_due) - earliest scope due';
COMMENT ON COLUMN projects.latest_scope_due IS 'MAX(scopes.date_due) - latest scope due';
COMMENT ON COLUMN projects.earliest_scope_start IS 'MIN(scopes.actual_start) - first scope started';
COMMENT ON COLUMN projects.latest_scope_start IS 'MAX(scopes.actual_start) - last scope started';
COMMENT ON COLUMN projects.earliest_scope_complete IS 'MIN(scopes.actual_end) - first scope done';
COMMENT ON COLUMN projects.latest_scope_complete IS 'MAX(scopes.actual_end) - last scope done';

-- =============================================================================
-- INDEXES FOR DASHBOARD PERFORMANCE
-- =============================================================================

-- Apparatus operational queries (daily scheduling)
CREATE INDEX IF NOT EXISTS idx_apparatus_availability ON apparatus(availability) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_apparatus_status_avail ON apparatus(status, availability) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_apparatus_date_due ON apparatus(date_due) WHERE is_active = true AND status != 'Complete';

-- Project dashboard queries
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_scopes_status ON scopes(status) WHERE is_active = true;

-- =============================================================================
-- OPERATIONAL DASHBOARD VIEW
-- =============================================================================
-- This provides the "what can we work on today" view

CREATE OR REPLACE VIEW v_apparatus_operational WITH (security_invoker = true) AS
SELECT 
    a.id,
    a.apparatus_designation,
    a.apparatus_name,
    a.apparatus_type,
    a.status,
    a.availability,
    a.assessment,
    a.percent_complete,
    a.date_due,
    a.actual_start,
    a.actual_end,
    a.quoted_hours,
    a.actual_hours,
    a.notes,
    a.datasheet_complete,
    a.task_delays,
    a.priority,
    t.task_name,
    t.task_number,
    s.scope_name,
    s.scope_number,
    p.project_name,
    p.project_number,
    c.client_name,
    si.site_name,
    -- Calculated fields
    CASE 
        WHEN a.date_due < CURRENT_DATE AND a.status != 'Complete' THEN 'Overdue'
        WHEN a.date_due = CURRENT_DATE THEN 'Due Today'
        WHEN a.date_due <= CURRENT_DATE + 7 THEN 'Due This Week'
        ELSE 'Upcoming'
    END AS due_status,
    a.date_due - CURRENT_DATE AS days_until_due
FROM apparatus a
LEFT JOIN tasks t ON a.task_id = t.id
LEFT JOIN scopes s ON a.scope_id = s.id
LEFT JOIN projects p ON s.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN sites si ON p.site_id = si.id
WHERE a.is_active = true;

COMMENT ON VIEW v_apparatus_operational IS 'Daily operational view - what can be worked, status, schedule';

-- =============================================================================
-- ROLLUP DATE VIEW - Task Level
-- =============================================================================

CREATE OR REPLACE VIEW v_task_rollup_dates WITH (security_invoker = true) AS
SELECT 
    t.id AS task_id,
    t.task_name,
    t.task_number,
    t.scope_id,
    t.status,
    t.percent_complete,
    -- Rollup calculations
    MIN(a.date_due) AS earliest_apparatus_due,
    MAX(a.date_due) AS latest_apparatus_due,
    MIN(a.actual_start) AS earliest_apparatus_start,
    MAX(a.actual_start) AS latest_apparatus_start,
    MIN(a.actual_end) AS earliest_apparatus_complete,
    MAX(a.actual_end) AS latest_apparatus_complete,
    -- Counts
    COUNT(a.id) AS total_apparatus,
    COUNT(a.id) FILTER (WHERE a.status = 'Complete') AS completed_apparatus,
    COUNT(a.id) FILTER (WHERE a.availability = 'Ready') AS ready_apparatus,
    COUNT(a.id) FILTER (WHERE a.availability = 'On Hold') AS on_hold_apparatus
FROM tasks t
LEFT JOIN apparatus a ON a.task_id = t.id AND a.is_active = true
WHERE t.is_active = true
GROUP BY t.id, t.task_name, t.task_number, t.scope_id, t.status, t.percent_complete;

COMMENT ON VIEW v_task_rollup_dates IS 'Task-level date rollups from apparatus';

-- =============================================================================
-- ROLLUP DATE VIEW - Scope Level
-- =============================================================================

CREATE OR REPLACE VIEW v_scope_rollup_dates WITH (security_invoker = true) AS
SELECT 
    s.id AS scope_id,
    s.scope_name,
    s.scope_number,
    s.project_id,
    s.status,
    s.percent_complete,
    -- Rollup from tasks
    MIN(t.date_due) AS earliest_task_due,
    MAX(t.date_due) AS latest_task_due,
    MIN(t.actual_start) AS earliest_task_start,
    MAX(t.actual_start) AS latest_task_start,
    MIN(t.actual_end) AS earliest_task_complete,
    MAX(t.actual_end) AS latest_task_complete,
    -- Direct apparatus rollups (bypassing task level)
    MIN(a.date_due) AS earliest_apparatus_due,
    MAX(a.date_due) AS latest_apparatus_due,
    MIN(a.actual_start) AS earliest_work_start,
    MAX(a.actual_end) AS latest_work_complete,
    -- Counts
    COUNT(DISTINCT t.id) AS total_tasks,
    COUNT(DISTINCT t.id) FILTER (WHERE t.status = 'Complete') AS completed_tasks,
    COUNT(a.id) AS total_apparatus,
    COUNT(a.id) FILTER (WHERE a.status = 'Complete') AS completed_apparatus
FROM scopes s
LEFT JOIN tasks t ON t.scope_id = s.id AND t.is_active = true
LEFT JOIN apparatus a ON a.scope_id = s.id AND a.is_active = true
WHERE s.is_active = true
GROUP BY s.id, s.scope_name, s.scope_number, s.project_id, s.status, s.percent_complete;

COMMENT ON VIEW v_scope_rollup_dates IS 'Scope-level date rollups from tasks and apparatus';

-- =============================================================================
-- ROLLUP DATE VIEW - Project Level
-- =============================================================================

CREATE OR REPLACE VIEW v_project_rollup_dates WITH (security_invoker = true) AS
SELECT 
    p.id AS project_id,
    p.project_name,
    p.project_number,
    p.status,
    p.percent_complete,
    p.start_date AS planned_start,
    p.end_date AS planned_end,
    p.date_due AS contractual_due,
    c.client_name,
    l.location_name,
    -- Rollup from scopes
    MIN(s.planned_start) AS earliest_scope_planned,
    MAX(s.planned_end) AS latest_scope_planned,
    MIN(s.actual_start) AS earliest_scope_start,
    MAX(s.actual_end) AS latest_scope_complete,
    -- Direct apparatus rollups
    MIN(a.date_due) AS earliest_apparatus_due,
    MAX(a.date_due) AS latest_apparatus_due,
    MIN(a.actual_start) AS earliest_work_start,
    MAX(a.actual_end) AS latest_work_complete,
    -- Counts
    COUNT(DISTINCT s.id) AS total_scopes,
    COUNT(DISTINCT s.id) FILTER (WHERE s.status = 'Complete') AS completed_scopes,
    COUNT(a.id) AS total_apparatus,
    COUNT(a.id) FILTER (WHERE a.status = 'Complete') AS completed_apparatus,
    -- Calculated progress
    ROUND(
        CASE WHEN COUNT(a.id) > 0 
        THEN COUNT(a.id) FILTER (WHERE a.status = 'Complete')::numeric / COUNT(a.id) * 100 
        ELSE 0 
        END, 2
    ) AS calculated_percent_complete
FROM projects p
LEFT JOIN scopes s ON s.project_id = p.id AND s.is_active = true
LEFT JOIN apparatus a ON a.scope_id = s.id AND a.is_active = true
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN locations l ON p.location_id = l.id
WHERE p.is_active = true
GROUP BY p.id, p.project_name, p.project_number, p.status, p.percent_complete, 
         p.start_date, p.end_date, p.date_due, c.client_name, l.location_name;

COMMENT ON VIEW v_project_rollup_dates IS 'Project-level dashboard view with all date rollups';

-- =============================================================================
-- SCHEDULE HEALTH VIEW
-- =============================================================================
-- Identifies projects/scopes at risk based on due dates vs progress

CREATE OR REPLACE VIEW v_schedule_health WITH (security_invoker = true) AS
SELECT 
    p.project_number,
    p.project_name,
    p.date_due AS project_due,
    s.scope_name,
    s.date_due AS scope_due,
    ROUND(
        CASE WHEN COUNT(a.id) > 0 
        THEN COUNT(a.id) FILTER (WHERE a.status = 'Complete')::numeric / COUNT(a.id) * 100 
        ELSE 0 
        END, 2
    ) AS percent_complete,
    COUNT(a.id) FILTER (WHERE a.status != 'Complete' AND a.date_due < CURRENT_DATE) AS overdue_items,
    COUNT(a.id) FILTER (WHERE a.availability = 'On Hold') AS on_hold_items,
    COUNT(a.id) FILTER (WHERE a.availability = 'Not Available') AS not_available_items,
    CASE 
        WHEN COUNT(a.id) FILTER (WHERE a.status != 'Complete' AND a.date_due < CURRENT_DATE) > 0 THEN 'At Risk'
        WHEN COUNT(a.id) FILTER (WHERE a.availability = 'On Hold') > COUNT(a.id) * 0.2 THEN 'Blocked'
        ELSE 'On Track'
    END AS health_status
FROM projects p
LEFT JOIN scopes s ON s.project_id = p.id AND s.is_active = true
LEFT JOIN apparatus a ON a.scope_id = s.id AND a.is_active = true
WHERE p.is_active = true
  AND p.status IN ('Active', 'Won')
GROUP BY p.project_number, p.project_name, p.date_due, s.scope_name, s.date_due;

COMMENT ON VIEW v_schedule_health IS 'Dashboard view showing project/scope health based on schedule';

-- =============================================================================
-- PROJECT-LEVEL APPARATUS SUMMARY (Your Excel Dashboard)
-- =============================================================================
-- Recreates your Excel KPI header + category breakdown per project/scope

CREATE OR REPLACE VIEW v_project_apparatus_summary WITH (security_invoker = true) AS
SELECT 
    p.id AS project_id,
    p.project_number,
    p.project_name,
    s.id AS scope_id,
    s.scope_name,
    -- KPI Header Metrics
    COUNT(a.id) AS total_apparatus,
    COUNT(a.id) FILTER (WHERE a.status = 'Complete') AS total_completed,
    COUNT(a.id) FILTER (WHERE a.status != 'Complete') AS total_remaining,
    ROUND(
        CASE WHEN COUNT(a.id) > 0 
        THEN COUNT(a.id) FILTER (WHERE a.status = 'Complete')::numeric / COUNT(a.id) * 100 
        ELSE 0 END, 2
    ) AS completion_percent,
    COUNT(a.id) FILTER (WHERE a.availability = 'Ready' AND a.status != 'Complete') AS ready_to_work,
    COUNT(a.id) FILTER (WHERE a.availability IN ('On Hold', 'Not Available') AND a.status != 'Complete') AS blocked,
    COUNT(a.id) FILTER (WHERE a.assessment::text IN ('Non-Serviceable', 'Fail', 'Needs Repair')) AS issues_failed,
    COUNT(a.id) FILTER (WHERE a.date_due <= CURRENT_DATE AND a.status != 'Complete') AS past_due,
    COUNT(a.id) FILTER (WHERE a.date_due BETWEEN CURRENT_DATE AND CURRENT_DATE + 7 AND a.status != 'Complete') AS due_this_week,
    -- Hours
    COALESCE(SUM(a.quoted_hours), 0) AS total_quoted_hours,
    COALESCE(SUM(a.actual_hours), 0) AS total_actual_hours,
    COALESCE(SUM(a.quoted_hours) FILTER (WHERE a.status != 'Complete'), 0) AS remaining_hours
FROM projects p
LEFT JOIN scopes s ON s.project_id = p.id AND s.is_active = true
LEFT JOIN apparatus a ON a.scope_id = s.id AND a.is_active = true
WHERE p.is_active = true
GROUP BY p.id, p.project_number, p.project_name, s.id, s.scope_name;

COMMENT ON VIEW v_project_apparatus_summary IS 'Project/scope KPI dashboard - ready to work, blocked, completion %';

-- =============================================================================
-- APPARATUS BY CATEGORY (Your Category Breakdown Table)
-- =============================================================================

CREATE OR REPLACE VIEW v_apparatus_by_category WITH (security_invoker = true) AS
SELECT 
    p.id AS project_id,
    p.project_number,
    s.id AS scope_id,
    s.scope_name,
    COALESCE(a.apparatus_type, 'Unspecified') AS apparatus_category,
    COUNT(a.id) AS total_count,
    COUNT(a.id) FILTER (WHERE a.status = 'Complete') AS completed,
    COUNT(a.id) FILTER (WHERE a.status != 'Complete') AS remaining,
    ROUND(
        CASE WHEN COUNT(a.id) > 0 
        THEN COUNT(a.id) FILTER (WHERE a.status = 'Complete')::numeric / COUNT(a.id) * 100 
        ELSE 0 END, 2
    ) AS percent_complete,
    COUNT(a.id) FILTER (WHERE a.availability = 'Ready' AND a.status != 'Complete') AS ready_to_work,
    COUNT(a.id) FILTER (WHERE a.availability IN ('On Hold', 'Not Available') AND a.status != 'Complete') AS blocked
FROM projects p
LEFT JOIN scopes s ON s.project_id = p.id AND s.is_active = true
LEFT JOIN apparatus a ON a.scope_id = s.id AND a.is_active = true
WHERE p.is_active = true
GROUP BY p.id, p.project_number, s.id, s.scope_name, a.apparatus_type
ORDER BY remaining DESC;

COMMENT ON VIEW v_apparatus_by_category IS 'Apparatus breakdown by type - matches Excel category table';

-- =============================================================================
-- MASTER OPERATIONS DASHBOARD (Multi-Project View)
-- =============================================================================
-- THE VIEW THAT CHANGES EVERYTHING: See ALL projects at once
-- This is what enables resource allocation across 10-15 active projects

CREATE OR REPLACE VIEW v_master_operations WITH (security_invoker = true) AS
SELECT 
    p.id AS project_id,
    p.project_number,
    p.project_name,
    p.status AS project_status,
    c.client_name,
    l.location_name AS resa_location,
    si.city AS site_city,
    p.date_due AS project_due,
    -- Rollup Metrics
    COUNT(DISTINCT s.id) AS scope_count,
    COUNT(a.id) AS total_apparatus,
    COUNT(a.id) FILTER (WHERE a.status = 'Complete') AS completed,
    COUNT(a.id) FILTER (WHERE a.status != 'Complete') AS remaining,
    ROUND(
        CASE WHEN COUNT(a.id) > 0 
        THEN COUNT(a.id) FILTER (WHERE a.status = 'Complete')::numeric / COUNT(a.id) * 100 
        ELSE 0 END, 2
    ) AS completion_percent,
    -- Actionable Metrics
    COUNT(a.id) FILTER (WHERE a.availability = 'Ready' AND a.status != 'Complete') AS ready_to_work,
    COUNT(a.id) FILTER (WHERE a.availability = 'On Hold' AND a.status != 'Complete') AS on_hold,
    COUNT(a.id) FILTER (WHERE a.availability = 'Not Available' AND a.status != 'Complete') AS not_available,
    COUNT(a.id) FILTER (WHERE a.assessment::text IN ('Non-Serviceable', 'Fail', 'Needs Repair')) AS issues,
    COUNT(a.id) FILTER (WHERE a.date_due < CURRENT_DATE AND a.status != 'Complete') AS overdue,
    COUNT(a.id) FILTER (WHERE a.date_due = CURRENT_DATE AND a.status != 'Complete') AS due_today,
    COUNT(a.id) FILTER (WHERE a.date_due BETWEEN CURRENT_DATE + 1 AND CURRENT_DATE + 7 AND a.status != 'Complete') AS due_this_week,
    -- Hours for resource planning
    COALESCE(SUM(a.quoted_hours) FILTER (WHERE a.availability = 'Ready' AND a.status != 'Complete'), 0) AS ready_hours,
    COALESCE(SUM(a.quoted_hours) FILTER (WHERE a.status != 'Complete'), 0) AS remaining_hours,
    -- Schedule Health
    CASE 
        WHEN COUNT(a.id) FILTER (WHERE a.date_due < CURRENT_DATE AND a.status != 'Complete') > 0 THEN 'OVERDUE'
        WHEN COUNT(a.id) FILTER (WHERE a.availability = 'On Hold') > COUNT(a.id) * 0.3 THEN 'BLOCKED'
        WHEN COUNT(a.id) FILTER (WHERE a.status = 'Complete')::numeric / NULLIF(COUNT(a.id), 0) < 0.25 
             AND p.date_due < CURRENT_DATE + 30 THEN 'AT RISK'
        ELSE 'ON TRACK'
    END AS health_status
FROM projects p
LEFT JOIN scopes s ON s.project_id = p.id AND s.is_active = true
LEFT JOIN apparatus a ON a.scope_id = s.id AND a.is_active = true
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN sites si ON p.site_id = si.id
LEFT JOIN locations l ON p.location_id = l.id
WHERE p.is_active = true
    AND p.status::text IN ('Active', 'Won', 'In Progress')
GROUP BY p.id, p.project_number, p.project_name, p.status, p.date_due,
         c.client_name, l.location_name, si.city
ORDER BY 
    CASE WHEN COUNT(a.id) FILTER (WHERE a.date_due < CURRENT_DATE AND a.status != 'Complete') > 0 THEN 0 ELSE 1 END,
    p.date_due NULLS LAST;

COMMENT ON VIEW v_master_operations IS 'Multi-project operations dashboard - resource allocation across all active work';

-- =============================================================================
-- RESOURCE ALLOCATION VIEW
-- =============================================================================
-- Answers: "Where should I send people tomorrow?"

CREATE OR REPLACE VIEW v_resource_allocation WITH (security_invoker = true) AS
SELECT 
    l.location_name AS resa_location,
    p.project_number,
    p.project_name,
    c.client_name,
    si.city AS job_site,
    COUNT(a.id) FILTER (WHERE a.availability = 'Ready' AND a.status != 'Complete') AS ready_items,
    COALESCE(SUM(a.quoted_hours) FILTER (WHERE a.availability = 'Ready' AND a.status != 'Complete'), 0) AS ready_hours,
    -- Estimate techs needed (rough: 8 hrs/day/tech)
    CEIL(COALESCE(SUM(a.quoted_hours) FILTER (WHERE a.availability = 'Ready' AND a.status != 'Complete'), 0) / 8) AS tech_days_ready,
    COUNT(a.id) FILTER (WHERE a.date_due <= CURRENT_DATE AND a.status != 'Complete') AS overdue_items,
    COUNT(a.id) FILTER (WHERE a.date_due BETWEEN CURRENT_DATE + 1 AND CURRENT_DATE + 7 AND a.status != 'Complete') AS due_this_week,
    -- What's blocking us?
    COUNT(a.id) FILTER (WHERE a.availability = 'On Hold') AS on_hold_count,
    COUNT(a.id) FILTER (WHERE a.availability = 'Not Available') AS not_available_count
FROM projects p
LEFT JOIN scopes s ON s.project_id = p.id AND s.is_active = true
LEFT JOIN apparatus a ON a.scope_id = s.id AND a.is_active = true
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN sites si ON p.site_id = si.id
LEFT JOIN locations l ON p.location_id = l.id
WHERE p.is_active = true
  AND p.status IN ('Active', 'Won')
GROUP BY l.location_name, p.project_number, p.project_name, c.client_name, si.city
HAVING COUNT(a.id) FILTER (WHERE a.availability = 'Ready' AND a.status != 'Complete') > 0
    OR COUNT(a.id) FILTER (WHERE a.date_due <= CURRENT_DATE + 7 AND a.status != 'Complete') > 0
ORDER BY ready_hours DESC;

COMMENT ON VIEW v_resource_allocation IS 'Where to send resources - ready work by project/location';

-- =============================================================================
-- EQUIPMENT NEEDS VIEW
-- =============================================================================
-- Answers: "What test equipment do I need where?"

CREATE OR REPLACE VIEW v_equipment_needs WITH (security_invoker = true) AS
SELECT 
    p.project_number,
    p.project_name,
    si.city AS job_site,
    a.apparatus_type,
    COUNT(a.id) FILTER (WHERE a.availability = 'Ready' AND a.status != 'Complete') AS ready_count,
    COALESCE(SUM(a.quoted_hours) FILTER (WHERE a.availability = 'Ready' AND a.status != 'Complete'), 0) AS ready_hours
FROM projects p
LEFT JOIN scopes s ON s.project_id = p.id AND s.is_active = true
LEFT JOIN apparatus a ON a.scope_id = s.id AND a.is_active = true
LEFT JOIN sites si ON p.site_id = si.id
WHERE p.is_active = true
  AND p.status IN ('Active', 'Won')
  AND a.availability = 'Ready'
  AND a.status != 'Complete'
GROUP BY p.project_number, p.project_name, si.city, a.apparatus_type
HAVING COUNT(a.id) > 0
ORDER BY p.project_number, ready_hours DESC;

COMMENT ON VIEW v_equipment_needs IS 'Test equipment needs by project and apparatus type';

-- =============================================================================
-- BLOCKER SUMMARY VIEW
-- =============================================================================
-- Answers: "What's stopping us from working?"

CREATE OR REPLACE VIEW v_blockers_summary WITH (security_invoker = true) AS
SELECT 
    p.project_number,
    p.project_name,
    a.apparatus_type,
    a.availability,
    COUNT(a.id) AS blocked_count,
    COALESCE(SUM(a.quoted_hours), 0) AS blocked_hours,
    -- Sample notes from blocked items (first 3)
    STRING_AGG(DISTINCT a.notes, ' | ') FILTER (WHERE a.notes IS NOT NULL AND a.notes != '') AS sample_notes
FROM projects p
LEFT JOIN scopes s ON s.project_id = p.id AND s.is_active = true
LEFT JOIN apparatus a ON a.scope_id = s.id AND a.is_active = true
WHERE p.is_active = true
  AND p.status IN ('Active', 'Won')
  AND a.availability IN ('On Hold', 'Not Available')
  AND a.status != 'Complete'
GROUP BY p.project_number, p.project_name, a.apparatus_type, a.availability
ORDER BY blocked_hours DESC;

COMMENT ON VIEW v_blockers_summary IS 'What is blocking work - grouped by reason';

