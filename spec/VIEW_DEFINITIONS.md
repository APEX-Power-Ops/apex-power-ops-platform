# View Definitions

**Version:** 1.0.0  
**Created:** December 5, 2025  
**Author:** Desktop Claude  
**Purpose:** PostgreSQL view definitions for reporting and data access

---

## Overview

Views provide:

1. **Simplified Queries:** Pre-joined data for common access patterns
2. **Denormalized Access:** Flattened hierarchies for reporting
3. **Security Layer:** Controlled data exposure for different roles
4. **Performance:** Materialized views for expensive calculations

---

## Project Management Views

### v_projects_full
**Purpose:** Complete project information with client/site/location names

```sql
CREATE OR REPLACE VIEW v_projects_full AS
SELECT 
    p.id,
    p.project_number,
    p.project_name,
    p.status,
    p.project_type,
    p.start_date,
    p.end_date,
    p.contract_value,
    p.po_number,
    p.project_lead,
    p.percent_complete,
    p.total_apparatus_count,
    p.completed_apparatus_count,
    -- Client info
    c.id AS client_id,
    c.client_name,
    c.client_code,
    -- Site info
    s.id AS site_id,
    s.site_name,
    s.city AS site_city,
    s.state AS site_state,
    -- Location info
    l.id AS location_id,
    l.location_name AS branch_name,
    l.abbreviation AS branch_code,
    -- Timestamps
    p.created_at,
    p.updated_at
FROM projects p
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN sites s ON p.site_id = s.id
LEFT JOIN locations l ON p.location_id = l.id
WHERE p.is_active = true;

COMMENT ON VIEW v_projects_full IS 'Complete project data with related entity names';
```

---

### v_projects_summary
**Purpose:** Dashboard-ready project summary with financial metrics

```sql
CREATE OR REPLACE VIEW v_projects_summary AS
SELECT 
    p.id,
    p.project_number,
    p.project_name,
    p.status,
    c.client_name,
    l.location_name AS branch,
    p.start_date,
    p.end_date,
    p.contract_value,
    p.percent_complete,
    p.total_apparatus_count,
    p.completed_apparatus_count,
    -- Financial summary
    COALESCE(pfs.total_recognized_revenue, 0) AS recognized_revenue,
    COALESCE(pfs.revenue_recognition_percent, 0) AS revenue_percent,
    COALESCE(pfs.total_actual_hours, 0) AS actual_hours,
    COALESCE(pfs.gross_margin_percent, 0) AS margin_percent,
    -- Scope counts
    (SELECT COUNT(*) FROM scopes WHERE project_id = p.id AND is_active = true) AS scope_count,
    (SELECT COUNT(*) FROM scopes WHERE project_id = p.id AND status = 'Complete' AND is_active = true) AS completed_scopes
FROM projects p
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN locations l ON p.location_id = l.id
LEFT JOIN project_financial_summaries pfs ON pfs.project_id = p.id
WHERE p.is_active = true;

COMMENT ON VIEW v_projects_summary IS 'Dashboard summary of projects with key metrics';
```

---

### v_projects_active
**Purpose:** Active projects for operational dashboards

```sql
CREATE OR REPLACE VIEW v_projects_active AS
SELECT 
    p.id,
    p.project_number,
    p.project_name,
    c.client_name,
    s.site_name,
    l.location_name AS branch,
    p.start_date,
    p.end_date,
    p.percent_complete,
    p.total_apparatus_count - p.completed_apparatus_count AS remaining_apparatus,
    CASE 
        WHEN p.end_date < CURRENT_DATE THEN 'Overdue'
        WHEN p.end_date < CURRENT_DATE + INTERVAL '7 days' THEN 'Due Soon'
        ELSE 'On Track'
    END AS schedule_status
FROM projects p
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN sites s ON p.site_id = s.id
LEFT JOIN locations l ON p.location_id = l.id
WHERE p.status = 'Active' AND p.is_active = true
ORDER BY p.end_date ASC;

COMMENT ON VIEW v_projects_active IS 'Currently active projects with schedule status';
```

---

## Scope & Task Views

### v_scopes_full
**Purpose:** Complete scope information with project context

```sql
CREATE OR REPLACE VIEW v_scopes_full AS
SELECT 
    sc.id,
    sc.scope_number,
    sc.scope_name,
    sc.scope_type,
    sc.status,
    sc.percent_complete,
    sc.planned_start,
    sc.planned_end,
    sc.actual_start,
    sc.actual_end,
    sc.quoted_hours,
    sc.actual_hours,
    sc.quoted_revenue,
    sc.actual_revenue,
    sc.total_apparatus_count,
    sc.completed_apparatus_count,
    -- Project info
    p.id AS project_id,
    p.project_number,
    p.project_name,
    -- Client info
    c.id AS client_id,
    c.client_name,
    -- Timestamps
    sc.created_at,
    sc.updated_at
FROM scopes sc
JOIN projects p ON sc.project_id = p.id
LEFT JOIN clients c ON sc.client_id = c.id
WHERE sc.is_active = true;

COMMENT ON VIEW v_scopes_full IS 'Complete scope data with project and client context';
```

---

### v_tasks_with_scope
**Purpose:** Tasks with parent scope and project information

```sql
CREATE OR REPLACE VIEW v_tasks_with_scope AS
SELECT 
    t.id,
    t.task_number,
    t.task_name,
    t.task_type,
    t.status,
    t.percent_complete,
    t.planned_start,
    t.planned_end,
    t.estimated_hours,
    t.actual_hours,
    t.apparatus_count,
    -- Scope info
    sc.id AS scope_id,
    sc.scope_number,
    sc.scope_name,
    -- Project info
    p.id AS project_id,
    p.project_number,
    -- Hierarchy
    t.parent_task_id,
    pt.task_name AS parent_task_name
FROM tasks t
JOIN scopes sc ON t.scope_id = sc.id
JOIN projects p ON sc.project_id = p.id
LEFT JOIN tasks pt ON t.parent_task_id = pt.id
WHERE t.is_active = true;

COMMENT ON VIEW v_tasks_with_scope IS 'Tasks with full hierarchy context';
```

---

## Apparatus Views

### v_apparatus_full
**Purpose:** Complete apparatus information with full hierarchy

```sql
CREATE OR REPLACE VIEW v_apparatus_full AS
SELECT 
    a.id,
    a.apparatus_designation,
    a.apparatus_name,
    a.apparatus_type,
    a.equipment_type,
    a.manufacturer,
    a.model,
    a.serial_number,
    a.status,
    a.assessment,
    a.percent_complete,
    a.anticipated_start,
    a.actual_start,
    a.actual_end,
    a.quoted_hours,
    a.actual_hours,
    a.quoted_revenue,
    a.actual_revenue,
    a.building,
    a.floor,
    a.room,
    -- Task info
    t.id AS task_id,
    t.task_name,
    -- Scope info
    sc.id AS scope_id,
    sc.scope_number,
    sc.scope_name,
    -- Project info
    p.id AS project_id,
    p.project_number,
    p.project_name,
    -- Client info
    c.client_name,
    -- Site info
    s.site_name,
    -- Timestamps
    a.created_at,
    a.updated_at
FROM apparatus a
JOIN scopes sc ON a.scope_id = sc.id
JOIN projects p ON sc.project_id = p.id
LEFT JOIN tasks t ON a.task_id = t.id
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN sites s ON p.site_id = s.id
WHERE a.is_active = true;

COMMENT ON VIEW v_apparatus_full IS 'Complete apparatus with full project hierarchy';
```

---

### v_apparatus_testing_status
**Purpose:** Apparatus testing progress for field crews

```sql
CREATE OR REPLACE VIEW v_apparatus_testing_status AS
SELECT 
    a.id,
    a.apparatus_designation,
    a.apparatus_type,
    a.status,
    a.assessment,
    a.anticipated_start,
    a.actual_start,
    a.building || ' ' || COALESCE(a.floor, '') || ' ' || COALESCE(a.room, '') AS location,
    p.project_number,
    sc.scope_name,
    CASE 
        WHEN a.status = 'Complete' THEN 'Done'
        WHEN a.status = 'In Progress' THEN 'Testing'
        WHEN a.anticipated_start <= CURRENT_DATE THEN 'Ready'
        ELSE 'Scheduled'
    END AS work_status
FROM apparatus a
JOIN scopes sc ON a.scope_id = sc.id
JOIN projects p ON sc.project_id = p.id
WHERE a.is_active = true
  AND sc.is_active = true
  AND p.status = 'Active';

COMMENT ON VIEW v_apparatus_testing_status IS 'Field crew view of apparatus testing queue';
```

---

## Financial Views

### v_scope_financials
**Purpose:** Scope-level financial details

```sql
CREATE OR REPLACE VIEW v_scope_financials AS
SELECT 
    sc.id AS scope_id,
    sc.scope_number,
    sc.scope_name,
    p.project_number,
    p.project_name,
    c.client_name,
    -- Quoted
    COALESCE(sfs.total_quoted_revenue, 0) AS quoted_revenue,
    COALESCE(sfs.total_quoted_hours, 0) AS quoted_hours,
    -- Actual
    COALESCE(sfs.total_recognized_revenue, 0) AS recognized_revenue,
    COALESCE(sfs.total_actual_hours, 0) AS actual_hours,
    -- Variances
    COALESCE(sfs.revenue_recognition_percent, 0) AS revenue_percent,
    COALESCE(sfs.hours_variance, 0) AS hours_variance,
    -- Margins
    COALESCE(sfs.total_labor_cost, 0) AS labor_cost,
    COALESCE(sfs.gross_margin, 0) AS gross_margin,
    COALESCE(sfs.gross_margin_percent, 0) AS margin_percent,
    -- Status
    sc.status,
    sfs.last_calculated_at
FROM scopes sc
JOIN projects p ON sc.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN scope_financial_summaries sfs ON sfs.scope_id = sc.id
WHERE sc.is_active = true;

COMMENT ON VIEW v_scope_financials IS 'Scope-level financial performance';
```

---

### v_project_financials
**Purpose:** Project-level financial summary

```sql
CREATE OR REPLACE VIEW v_project_financials AS
SELECT 
    p.id AS project_id,
    p.project_number,
    p.project_name,
    c.client_name,
    l.location_name AS branch,
    p.contract_value,
    -- Revenue
    COALESCE(pfs.total_quoted_revenue, 0) AS quoted_revenue,
    COALESCE(pfs.total_recognized_revenue, 0) AS recognized_revenue,
    COALESCE(pfs.revenue_recognition_percent, 0) AS revenue_percent,
    -- Hours
    COALESCE(pfs.total_quoted_hours, 0) AS quoted_hours,
    COALESCE(pfs.total_actual_hours, 0) AS actual_hours,
    -- Costs
    COALESCE(pfs.total_labor_cost, 0) AS labor_cost,
    COALESCE(pfs.total_expense_cost, 0) AS expense_cost,
    COALESCE(pfs.total_cost, 0) AS total_cost,
    -- Margin
    COALESCE(pfs.gross_margin, 0) AS gross_margin,
    COALESCE(pfs.gross_margin_percent, 0) AS margin_percent,
    -- Progress
    p.percent_complete,
    pfs.total_scopes,
    pfs.completed_scopes,
    p.status,
    pfs.last_calculated_at
FROM projects p
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN locations l ON p.location_id = l.id
LEFT JOIN project_financial_summaries pfs ON pfs.project_id = p.id
WHERE p.is_active = true;

COMMENT ON VIEW v_project_financials IS 'Project-level financial performance';
```

---

### v_revenue_by_apparatus
**Purpose:** Revenue recognition detail by apparatus

```sql
CREATE OR REPLACE VIEW v_revenue_by_apparatus AS
SELECT 
    ar.id AS revenue_id,
    ar.revenue_type,
    ar.quoted_amount,
    ar.recognized_amount,
    ar.recognition_date,
    ar.recognition_percent,
    a.apparatus_designation,
    a.apparatus_type,
    a.status AS apparatus_status,
    sc.scope_name,
    p.project_number,
    p.project_name,
    c.client_name
FROM apparatus_revenue ar
JOIN apparatus a ON ar.apparatus_id = a.id
JOIN scopes sc ON a.scope_id = sc.id
JOIN projects p ON sc.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id;

COMMENT ON VIEW v_revenue_by_apparatus IS 'Revenue recognition detail by apparatus';
```

---

## Employee & Resource Views

### v_employees_full
**Purpose:** Complete employee information

```sql
CREATE OR REPLACE VIEW v_employees_full AS
SELECT 
    e.id,
    e.employee_number,
    e.first_name,
    e.last_name,
    e.first_name || ' ' || e.last_name AS full_name,
    e.email,
    e.phone,
    e.job_title,
    e.department,
    e.role_type,
    e.hourly_rate,
    e.neta_certified,
    e.neta_level,
    e.certification_expiry,
    CASE 
        WHEN e.certification_expiry < CURRENT_DATE THEN 'Expired'
        WHEN e.certification_expiry < CURRENT_DATE + INTERVAL '90 days' THEN 'Expiring Soon'
        ELSE 'Current'
    END AS cert_status,
    l.id AS location_id,
    l.location_name AS branch,
    e.hire_date,
    e.is_active
FROM employees e
LEFT JOIN locations l ON e.location_id = l.id;

COMMENT ON VIEW v_employees_full IS 'Complete employee information with certification status';
```

---

### v_resource_assignments_full
**Purpose:** Resource assignments with names

```sql
CREATE OR REPLACE VIEW v_resource_assignments_full AS
SELECT 
    ra.id,
    ra.assignment_type,
    ra.start_date,
    ra.end_date,
    ra.allocated_hours,
    ra.actual_hours,
    ra.is_primary,
    -- Employee
    e.id AS employee_id,
    e.first_name || ' ' || e.last_name AS employee_name,
    e.role_type,
    -- Project
    p.id AS project_id,
    p.project_number,
    p.project_name,
    -- Scope (optional)
    sc.id AS scope_id,
    sc.scope_name
FROM resource_assignments ra
JOIN employees e ON ra.employee_id = e.id
LEFT JOIN projects p ON ra.project_id = p.id
LEFT JOIN scopes sc ON ra.scope_id = sc.id
WHERE ra.is_active = true;

COMMENT ON VIEW v_resource_assignments_full IS 'Resource assignments with employee and project names';
```

---

## PSS Portal Views

### v_pss_studies_full
**Purpose:** Complete PSS study information

```sql
CREATE OR REPLACE VIEW v_pss_studies_full AS
SELECT 
    ps.id,
    ps.study_number,
    ps.study_name,
    ps.study_type,
    ps.status,
    ps.priority,
    ps.requested_date,
    ps.due_date,
    ps.completed_date,
    CASE 
        WHEN ps.status = 'Completed' THEN 'Done'
        WHEN ps.due_date < CURRENT_DATE THEN 'Overdue'
        WHEN ps.due_date < CURRENT_DATE + INTERVAL '7 days' THEN 'Due Soon'
        ELSE 'On Track'
    END AS schedule_status,
    -- Engineer
    eng.id AS engineer_id,
    eng.engineer_name,
    eng.company AS engineer_company,
    -- Project
    p.id AS project_id,
    p.project_number,
    p.project_name,
    -- Client
    c.client_name,
    -- Document counts
    (SELECT COUNT(*) FROM pss_documents WHERE study_id = ps.id AND is_active = true) AS document_count,
    (SELECT COUNT(*) FROM pss_rfis WHERE study_id = ps.id AND status = 'Open') AS open_rfi_count,
    -- Timestamps
    ps.created_at,
    ps.updated_at
FROM pss_studies ps
LEFT JOIN pss_engineers eng ON ps.engineer_id = eng.id
LEFT JOIN projects p ON ps.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id
WHERE ps.is_active = true;

COMMENT ON VIEW v_pss_studies_full IS 'Complete PSS study information with status';
```

---

### v_pss_dashboard
**Purpose:** PSS portal dashboard summary

```sql
CREATE OR REPLACE VIEW v_pss_dashboard AS
SELECT 
    ps.id,
    ps.study_number,
    ps.study_name,
    ps.study_type,
    ps.status,
    ps.priority,
    ps.due_date,
    eng.engineer_name,
    p.project_number,
    c.client_name,
    CASE 
        WHEN ps.status IN ('Completed', 'Cancelled') THEN 0
        WHEN ps.due_date < CURRENT_DATE THEN 1
        WHEN ps.due_date < CURRENT_DATE + INTERVAL '7 days' THEN 2
        ELSE 3
    END AS sort_priority,
    (SELECT COUNT(*) FROM pss_rfis WHERE study_id = ps.id AND status = 'Open') AS open_rfis
FROM pss_studies ps
LEFT JOIN pss_engineers eng ON ps.engineer_id = eng.id
LEFT JOIN projects p ON ps.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id
WHERE ps.is_active = true
  AND ps.status NOT IN ('Completed', 'Cancelled')
ORDER BY sort_priority, ps.due_date;

COMMENT ON VIEW v_pss_dashboard IS 'PSS dashboard ordered by urgency';
```

---

## Location/Branch Views

### v_branch_summary
**Purpose:** Branch-level summary for management

```sql
CREATE OR REPLACE VIEW v_branch_summary AS
SELECT 
    l.id AS location_id,
    l.location_name AS branch,
    l.abbreviation AS branch_code,
    l.manager,
    -- Counts
    (SELECT COUNT(*) FROM projects WHERE location_id = l.id AND status = 'Active') AS active_projects,
    (SELECT COUNT(*) FROM employees WHERE location_id = l.id AND is_active = true) AS employee_count,
    (SELECT COUNT(*) FROM equipment WHERE location_id = l.id AND is_active = true) AS equipment_count,
    -- Revenue (current month)
    (SELECT COALESCE(SUM(pfs.total_recognized_revenue), 0)
     FROM project_financial_summaries pfs
     JOIN projects p ON pfs.project_id = p.id
     WHERE p.location_id = l.id
       AND pfs.last_calculated_at >= DATE_TRUNC('month', CURRENT_DATE)
    ) AS mtd_revenue
FROM locations l
WHERE l.is_active = true;

COMMENT ON VIEW v_branch_summary IS 'Branch-level operational summary';
```

---

## Materialized Views

### mv_project_kpis
**Purpose:** Pre-computed project KPIs (refresh periodically)

```sql
CREATE MATERIALIZED VIEW mv_project_kpis AS
SELECT 
    p.id AS project_id,
    p.project_number,
    p.status,
    l.location_name AS branch,
    -- Progress
    p.percent_complete,
    p.total_apparatus_count,
    p.completed_apparatus_count,
    -- Schedule
    p.start_date,
    p.end_date,
    CURRENT_DATE - p.start_date AS days_elapsed,
    p.end_date - CURRENT_DATE AS days_remaining,
    -- Financial
    COALESCE(pfs.total_recognized_revenue, 0) AS recognized_revenue,
    COALESCE(pfs.revenue_recognition_percent, 0) AS revenue_percent,
    COALESCE(pfs.gross_margin_percent, 0) AS margin_percent,
    -- Efficiency
    CASE 
        WHEN COALESCE(pfs.total_quoted_hours, 0) > 0
        THEN (pfs.total_actual_hours / pfs.total_quoted_hours * 100)
        ELSE 0
    END AS hours_efficiency,
    -- Computed at
    NOW() AS computed_at
FROM projects p
LEFT JOIN locations l ON p.location_id = l.id
LEFT JOIN project_financial_summaries pfs ON pfs.project_id = p.id
WHERE p.is_active = true;

CREATE UNIQUE INDEX idx_mv_project_kpis_id ON mv_project_kpis(project_id);

-- Refresh command (run via scheduled job)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_project_kpis;

COMMENT ON MATERIALIZED VIEW mv_project_kpis IS 'Pre-computed project KPIs - refresh hourly';
```

---

## View Refresh Strategy

| View Type | Refresh Method | Frequency |
|-----------|----------------|-----------|
| Regular views | Real-time | N/A |
| mv_project_kpis | REFRESH MATERIALIZED VIEW | Hourly |

**Refresh Script:**

```sql
-- Create refresh function
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_project_kpis;
    -- Add other materialized views here
END;
$$ LANGUAGE plpgsql;

-- Schedule via pg_cron (Supabase extension)
SELECT cron.schedule('refresh-kpis', '0 * * * *', 'SELECT refresh_materialized_views()');
```

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-05 | Desktop Claude | Initial creation |

---

*View Definitions v1.0.0 | RESA Power Supabase Migration*
