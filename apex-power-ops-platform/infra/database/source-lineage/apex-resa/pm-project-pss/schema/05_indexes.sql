-- =============================================================================
-- RESA Power Platform - Indexes
-- =============================================================================
-- File: 05_indexes.sql
-- Generated: 2025-12-05
-- Source: spec/DATA_DICTIONARY.md, spec/ENTITY_RELATIONSHIPS.md
-- Run: AFTER 04_views.sql
-- =============================================================================

-- =============================================================================
-- FOREIGN KEY INDEXES
-- =============================================================================
-- PostgreSQL automatically indexes PRIMARY KEYs but NOT foreign keys.
-- These indexes improve JOIN and WHERE clause performance.

-- Sites
CREATE INDEX IF NOT EXISTS idx_sites_client ON sites(client_id);

-- Employees
CREATE INDEX IF NOT EXISTS idx_employees_location ON employees(location_id);

-- Projects
CREATE INDEX IF NOT EXISTS idx_projects_client ON projects(client_id);
CREATE INDEX IF NOT EXISTS idx_projects_site ON projects(site_id);
CREATE INDEX IF NOT EXISTS idx_projects_location ON projects(location_id);

-- Scopes
CREATE INDEX IF NOT EXISTS idx_scopes_project ON scopes(project_id);
CREATE INDEX IF NOT EXISTS idx_scopes_client ON scopes(client_id);
CREATE INDEX IF NOT EXISTS idx_scopes_site ON scopes(site_id);

-- Tasks
CREATE INDEX IF NOT EXISTS idx_tasks_scope ON tasks(scope_id);
CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id);

-- Apparatus
CREATE INDEX IF NOT EXISTS idx_apparatus_scope ON apparatus(scope_id);
CREATE INDEX IF NOT EXISTS idx_apparatus_task ON apparatus(task_id);

-- Equipment
CREATE INDEX IF NOT EXISTS idx_equipment_location ON equipment(location_id);
CREATE INDEX IF NOT EXISTS idx_equipment_employee ON equipment(assigned_employee_id);

-- Resource Assignments
CREATE INDEX IF NOT EXISTS idx_resource_assignments_employee ON resource_assignments(employee_id);
CREATE INDEX IF NOT EXISTS idx_resource_assignments_project ON resource_assignments(project_id);
CREATE INDEX IF NOT EXISTS idx_resource_assignments_scope ON resource_assignments(scope_id);

-- Financial Tables
CREATE INDEX IF NOT EXISTS idx_apparatus_revenue_apparatus ON apparatus_revenue(apparatus_id);
CREATE INDEX IF NOT EXISTS idx_apparatus_revenue_scope ON apparatus_revenue(scope_id);
CREATE INDEX IF NOT EXISTS idx_scope_labor_scope ON scope_labor_details(scope_id);
CREATE INDEX IF NOT EXISTS idx_estimators_location ON estimators(location_id);

-- PSS Portal
CREATE INDEX IF NOT EXISTS idx_pss_studies_project ON pss_studies(project_id);
CREATE INDEX IF NOT EXISTS idx_pss_studies_engineer ON pss_studies(engineer_id);
CREATE INDEX IF NOT EXISTS idx_pss_documents_study ON pss_documents(study_id);
CREATE INDEX IF NOT EXISTS idx_pss_documents_template ON pss_documents(template_id);
CREATE INDEX IF NOT EXISTS idx_pss_documents_uploaded_by ON pss_documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_pss_rfis_study ON pss_rfis(study_id);
CREATE INDEX IF NOT EXISTS idx_pss_rfis_requested_by ON pss_rfis(requested_by);
CREATE INDEX IF NOT EXISTS idx_pss_rfis_assigned_to ON pss_rfis(assigned_to);
CREATE INDEX IF NOT EXISTS idx_pss_activity_study ON pss_activity_log(study_id);
CREATE INDEX IF NOT EXISTS idx_pss_activity_performed_by ON pss_activity_log(performed_by);

-- =============================================================================
-- STATUS/FILTER INDEXES
-- =============================================================================
-- For common WHERE clauses on status fields

-- Project status filtering
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_active_status ON projects(status) WHERE is_active = true;

-- Scope status filtering
CREATE INDEX IF NOT EXISTS idx_scopes_status ON scopes(status);
CREATE INDEX IF NOT EXISTS idx_scopes_active_status ON scopes(status) WHERE is_active = true;

-- Task status filtering
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- Apparatus status filtering
CREATE INDEX IF NOT EXISTS idx_apparatus_status ON apparatus(status);
CREATE INDEX IF NOT EXISTS idx_apparatus_active ON apparatus(status) WHERE is_active = true;

-- PSS status filtering
CREATE INDEX IF NOT EXISTS idx_pss_studies_status ON pss_studies(status);
CREATE INDEX IF NOT EXISTS idx_pss_rfis_status ON pss_rfis(status);

-- Employee active filtering
CREATE INDEX IF NOT EXISTS idx_employees_active ON employees(is_active);

-- Equipment status filtering
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status);

-- =============================================================================
-- UNIQUE CONSTRAINT INDEXES
-- =============================================================================
-- These are for business-logic unique constraints beyond PKs

-- Project number must be unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_number_unique 
ON projects(project_number);

-- Employee number must be unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_employees_number_unique 
ON employees(employee_number) WHERE employee_number IS NOT NULL;

-- Equipment number must be unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_equipment_number_unique 
ON equipment(equipment_number) WHERE equipment_number IS NOT NULL;

-- Apparatus type code must be unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_apparatus_types_code_unique 
ON apparatus_types(type_code);

-- =============================================================================
-- DATE/RANGE INDEXES
-- =============================================================================
-- For date-based queries and reporting

-- Project date ranges
CREATE INDEX IF NOT EXISTS idx_projects_start_date ON projects(start_date);
CREATE INDEX IF NOT EXISTS idx_projects_end_date ON projects(end_date);
CREATE INDEX IF NOT EXISTS idx_projects_date_range ON projects(start_date, end_date);

-- Scope date ranges
CREATE INDEX IF NOT EXISTS idx_scopes_planned_dates ON scopes(planned_start, planned_end);
CREATE INDEX IF NOT EXISTS idx_scopes_actual_dates ON scopes(actual_start, actual_end);

-- Apparatus dates
CREATE INDEX IF NOT EXISTS idx_apparatus_anticipated_start ON apparatus(anticipated_start);

-- PSS due dates
CREATE INDEX IF NOT EXISTS idx_pss_studies_due_date ON pss_studies(due_date);
CREATE INDEX IF NOT EXISTS idx_pss_rfis_due_date ON pss_rfis(due_date);

-- Equipment calibration tracking
CREATE INDEX IF NOT EXISTS idx_equipment_calibration_due ON equipment(calibration_due);

-- Employee certification expiry
CREATE INDEX IF NOT EXISTS idx_employees_cert_expiry ON employees(certification_expiry);

-- Activity log timestamp
CREATE INDEX IF NOT EXISTS idx_pss_activity_performed_at ON pss_activity_log(performed_at);

-- Revenue recognition date
CREATE INDEX IF NOT EXISTS idx_apparatus_revenue_recognition_date ON apparatus_revenue(recognition_date);

-- =============================================================================
-- COMPOSITE INDEXES
-- =============================================================================
-- For common multi-column queries

-- Active projects by location and status
CREATE INDEX IF NOT EXISTS idx_projects_location_status 
ON projects(location_id, status) WHERE is_active = true;

-- Scopes by project and status
CREATE INDEX IF NOT EXISTS idx_scopes_project_status 
ON scopes(project_id, status) WHERE is_active = true;

-- Apparatus by scope and status
CREATE INDEX IF NOT EXISTS idx_apparatus_scope_status 
ON apparatus(scope_id, status) WHERE is_active = true;

-- Employees by location and role
CREATE INDEX IF NOT EXISTS idx_employees_location_role 
ON employees(location_id, role_type) WHERE is_active = true;

-- PSS Studies by status and due date (for dashboard)
CREATE INDEX IF NOT EXISTS idx_pss_studies_status_due 
ON pss_studies(status, due_date) WHERE is_active = true;

-- =============================================================================
-- TEXT SEARCH INDEXES
-- =============================================================================
-- For LIKE/ILIKE searches on name fields

-- GIN indexes for full-text search capability
CREATE INDEX IF NOT EXISTS idx_projects_name_gin 
ON projects USING gin(to_tsvector('english', project_name));

CREATE INDEX IF NOT EXISTS idx_clients_name_gin 
ON clients USING gin(to_tsvector('english', client_name));

CREATE INDEX IF NOT EXISTS idx_apparatus_designation_btree 
ON apparatus(apparatus_designation);

-- =============================================================================
-- PARTIAL INDEXES FOR COMMON FILTERS
-- =============================================================================

-- Only active records (most common filter)
CREATE INDEX IF NOT EXISTS idx_projects_active 
ON projects(id) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_scopes_active 
ON scopes(id) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_tasks_active 
ON tasks(id) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_apparatus_active_only 
ON apparatus(id) WHERE is_active = true;

-- Open RFIs only
CREATE INDEX IF NOT EXISTS idx_pss_rfis_open 
ON pss_rfis(study_id, due_date) WHERE status = 'Open';

-- Non-completed studies
CREATE INDEX IF NOT EXISTS idx_pss_studies_pending 
ON pss_studies(due_date) 
WHERE status NOT IN ('Completed', 'Cancelled') AND is_active = true;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

SELECT 'All indexes created successfully!' AS status;

-- List all indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
