-- =============================================================================
-- RESA Power Platform - Foreign Key Relationships
-- =============================================================================
-- File: 02_relationships.sql
-- Generated: 2025-12-05
-- Source: spec/ENTITY_RELATIONSHIPS.md v1.0.0
-- Run: AFTER 01_tables.sql
-- =============================================================================

-- =============================================================================
-- CORE TABLE RELATIONSHIPS
-- =============================================================================

-- Sites → Clients
ALTER TABLE sites
    ADD CONSTRAINT fk_sites_client
    FOREIGN KEY (client_id) 
    REFERENCES clients(id) 
    ON DELETE CASCADE;

-- Employees → Locations
ALTER TABLE employees
    ADD CONSTRAINT fk_employees_location
    FOREIGN KEY (location_id) 
    REFERENCES locations(id)
    ON DELETE SET NULL;

-- Projects → Clients, Sites, Locations
ALTER TABLE projects
    ADD CONSTRAINT fk_projects_client
    FOREIGN KEY (client_id) 
    REFERENCES clients(id)
    ON DELETE SET NULL;

ALTER TABLE projects
    ADD CONSTRAINT fk_projects_site
    FOREIGN KEY (site_id) 
    REFERENCES sites(id)
    ON DELETE SET NULL;

ALTER TABLE projects
    ADD CONSTRAINT fk_projects_location
    FOREIGN KEY (location_id) 
    REFERENCES locations(id)
    ON DELETE SET NULL;

-- Scopes → Projects, Clients, Sites
ALTER TABLE scopes
    ADD CONSTRAINT fk_scopes_project
    FOREIGN KEY (project_id) 
    REFERENCES projects(id) 
    ON DELETE CASCADE;

ALTER TABLE scopes
    ADD CONSTRAINT fk_scopes_client
    FOREIGN KEY (client_id) 
    REFERENCES clients(id)
    ON DELETE SET NULL;

ALTER TABLE scopes
    ADD CONSTRAINT fk_scopes_site
    FOREIGN KEY (site_id) 
    REFERENCES sites(id)
    ON DELETE SET NULL;

-- Tasks → Scopes, Tasks (self-reference)
ALTER TABLE tasks
    ADD CONSTRAINT fk_tasks_scope
    FOREIGN KEY (scope_id) 
    REFERENCES scopes(id) 
    ON DELETE CASCADE;

ALTER TABLE tasks
    ADD CONSTRAINT fk_tasks_parent
    FOREIGN KEY (parent_task_id) 
    REFERENCES tasks(id) 
    ON DELETE SET NULL;

-- Apparatus → Scopes, Tasks
ALTER TABLE apparatus
    ADD CONSTRAINT fk_apparatus_scope
    FOREIGN KEY (scope_id) 
    REFERENCES scopes(id) 
    ON DELETE CASCADE;

ALTER TABLE apparatus
    ADD CONSTRAINT fk_apparatus_task
    FOREIGN KEY (task_id) 
    REFERENCES tasks(id) 
    ON DELETE SET NULL;

-- Equipment → Locations, Employees
ALTER TABLE equipment
    ADD CONSTRAINT fk_equipment_location
    FOREIGN KEY (location_id) 
    REFERENCES locations(id)
    ON DELETE SET NULL;

ALTER TABLE equipment
    ADD CONSTRAINT fk_equipment_employee
    FOREIGN KEY (assigned_employee_id) 
    REFERENCES employees(id)
    ON DELETE SET NULL;

-- Resource Assignments → Employees, Projects, Scopes
ALTER TABLE resource_assignments
    ADD CONSTRAINT fk_resource_employee
    FOREIGN KEY (employee_id) 
    REFERENCES employees(id)
    ON DELETE CASCADE;

ALTER TABLE resource_assignments
    ADD CONSTRAINT fk_resource_project
    FOREIGN KEY (project_id) 
    REFERENCES projects(id)
    ON DELETE CASCADE;

ALTER TABLE resource_assignments
    ADD CONSTRAINT fk_resource_scope
    FOREIGN KEY (scope_id) 
    REFERENCES scopes(id)
    ON DELETE SET NULL;

-- =============================================================================
-- FINANCIAL TABLE RELATIONSHIPS
-- =============================================================================

-- Estimators → Locations
ALTER TABLE estimators
    ADD CONSTRAINT fk_estimators_location
    FOREIGN KEY (location_id) 
    REFERENCES locations(id)
    ON DELETE SET NULL;

-- Apparatus Revenue → Apparatus, Scopes
ALTER TABLE apparatus_revenue
    ADD CONSTRAINT fk_apparatus_revenue_apparatus
    FOREIGN KEY (apparatus_id) 
    REFERENCES apparatus(id) 
    ON DELETE CASCADE;

ALTER TABLE apparatus_revenue
    ADD CONSTRAINT fk_apparatus_revenue_scope
    FOREIGN KEY (scope_id) 
    REFERENCES scopes(id)
    ON DELETE SET NULL;

-- Scope Labor Details → Scopes
ALTER TABLE scope_labor_details
    ADD CONSTRAINT fk_scope_labor_scope
    FOREIGN KEY (scope_id) 
    REFERENCES scopes(id) 
    ON DELETE CASCADE;

-- Scope Financial Summaries → Scopes
ALTER TABLE scope_financial_summaries
    ADD CONSTRAINT fk_scope_financial_scope
    FOREIGN KEY (scope_id) 
    REFERENCES scopes(id) 
    ON DELETE CASCADE;

-- Project Financial Summaries → Projects
ALTER TABLE project_financial_summaries
    ADD CONSTRAINT fk_project_financial_project
    FOREIGN KEY (project_id) 
    REFERENCES projects(id) 
    ON DELETE CASCADE;

-- =============================================================================
-- PSS PORTAL RELATIONSHIPS
-- =============================================================================

-- PSS Studies → Projects, Engineers
ALTER TABLE pss_studies
    ADD CONSTRAINT fk_pss_studies_project
    FOREIGN KEY (project_id) 
    REFERENCES projects(id)
    ON DELETE SET NULL;

ALTER TABLE pss_studies
    ADD CONSTRAINT fk_pss_studies_engineer
    FOREIGN KEY (engineer_id) 
    REFERENCES pss_engineers(id)
    ON DELETE SET NULL;

-- PSS Documents → Studies, Templates, Employees
ALTER TABLE pss_documents
    ADD CONSTRAINT fk_pss_documents_study
    FOREIGN KEY (study_id) 
    REFERENCES pss_studies(id) 
    ON DELETE CASCADE;

ALTER TABLE pss_documents
    ADD CONSTRAINT fk_pss_documents_template
    FOREIGN KEY (template_id) 
    REFERENCES pss_document_templates(id)
    ON DELETE SET NULL;

ALTER TABLE pss_documents
    ADD CONSTRAINT fk_pss_documents_employee
    FOREIGN KEY (uploaded_by) 
    REFERENCES employees(id)
    ON DELETE SET NULL;

-- PSS RFIs → Studies, Employees
ALTER TABLE pss_rfis
    ADD CONSTRAINT fk_pss_rfis_study
    FOREIGN KEY (study_id) 
    REFERENCES pss_studies(id) 
    ON DELETE CASCADE;

ALTER TABLE pss_rfis
    ADD CONSTRAINT fk_pss_rfis_requested_by
    FOREIGN KEY (requested_by) 
    REFERENCES employees(id)
    ON DELETE SET NULL;

ALTER TABLE pss_rfis
    ADD CONSTRAINT fk_pss_rfis_assigned_to
    FOREIGN KEY (assigned_to) 
    REFERENCES employees(id)
    ON DELETE SET NULL;

-- PSS Activity Log → Studies, Employees
ALTER TABLE pss_activity_log
    ADD CONSTRAINT fk_pss_activity_study
    FOREIGN KEY (study_id) 
    REFERENCES pss_studies(id) 
    ON DELETE CASCADE;

ALTER TABLE pss_activity_log
    ADD CONSTRAINT fk_pss_activity_employee
    FOREIGN KEY (performed_by) 
    REFERENCES employees(id)
    ON DELETE SET NULL;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

SELECT 'All foreign key constraints created successfully!' AS status;

-- List all foreign keys
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, tc.constraint_name;
