-- =============================================================================
-- RESA Power Platform - ENUM Type Definitions
-- =============================================================================
-- File: 00_enums.sql
-- Generated: 2025-12-05
-- Source: spec/ENUM_DEFINITIONS.md v1.0.0
-- Run: FIRST (before tables)
-- =============================================================================

-- Drop existing types if recreating (uncomment if needed)
-- DROP TYPE IF EXISTS project_status CASCADE;
-- DROP TYPE IF EXISTS scope_status CASCADE;
-- ... etc

-- =============================================================================
-- PROJECT/WORK STATUS ENUMS
-- =============================================================================

CREATE TYPE project_status AS ENUM (
    'Draft',
    'Quoted',
    'Won',
    'Active',
    'On Hold',
    'Complete',
    'Cancelled'
);
COMMENT ON TYPE project_status IS 'Project lifecycle states';

CREATE TYPE scope_status AS ENUM (
    'Not Started',
    'In Progress',
    'On Hold',
    'Complete',
    'Cancelled'
);
COMMENT ON TYPE scope_status IS 'Scope/phase lifecycle states';

CREATE TYPE task_status AS ENUM (
    'Not Started',
    'In Progress',
    'On Hold',
    'Complete',
    'Cancelled'
);
COMMENT ON TYPE task_status IS 'Task lifecycle states';

CREATE TYPE apparatus_status AS ENUM (
    'Not Started',
    'In Progress',
    'Pending Review',
    'Complete',
    'Cancelled'
);
COMMENT ON TYPE apparatus_status IS 'Apparatus testing states';

CREATE TYPE apparatus_assessment AS ENUM (
    'Pass',
    'Fail',
    'Marginal',
    'Needs Repair',
    'Deferred',
    'Not Tested'
);
COMMENT ON TYPE apparatus_assessment IS 'Test result classifications';

-- =============================================================================
-- EMPLOYEE/RESOURCE ENUMS
-- =============================================================================

CREATE TYPE role_type AS ENUM (
    'Field Tech',
    'Lead Tech',
    'Engineer',
    'Project Manager',
    'Estimator',
    'Admin',
    'Executive'
);
COMMENT ON TYPE role_type IS 'Employee role categories';

CREATE TYPE neta_level AS ENUM (
    'Level I',
    'Level II',
    'Level III',
    'Level IV'
);
COMMENT ON TYPE neta_level IS 'NETA certification levels';

CREATE TYPE assignment_type AS ENUM (
    'Primary',
    'Secondary',
    'Observer',
    'Consultant'
);
COMMENT ON TYPE assignment_type IS 'Resource assignment roles';

-- =============================================================================
-- EQUIPMENT ENUMS
-- =============================================================================

CREATE TYPE equipment_status AS ENUM (
    'Available',
    'Assigned',
    'Calibration',
    'Maintenance',
    'Retired'
);
COMMENT ON TYPE equipment_status IS 'Company equipment availability states';

-- =============================================================================
-- PSS PORTAL ENUMS
-- =============================================================================

CREATE TYPE study_type AS ENUM (
    'Short Circuit',
    'Arc Flash',
    'Coordination',
    'Load Flow',
    'Motor Starting',
    'Harmonic',
    'Power Quality',
    'Grounding',
    'Transient',
    'Comprehensive'
);
COMMENT ON TYPE study_type IS 'Power system study classifications';

CREATE TYPE study_status AS ENUM (
    'Pending',
    'Data Collection',
    'In Progress',
    'Review',
    'Client Review',
    'Revisions',
    'Completed',
    'On Hold',
    'Cancelled'
);
COMMENT ON TYPE study_status IS 'PSS study lifecycle states';

CREATE TYPE document_type AS ENUM (
    'Study Report',
    'One-Line Diagram',
    'Data Collection',
    'Calculations',
    'Equipment Schedule',
    'Arc Flash Labels',
    'Short Circuit Report',
    'Coordination Curves',
    'Cover Letter',
    'Appendix'
);
COMMENT ON TYPE document_type IS 'PSS document classifications';

CREATE TYPE document_status AS ENUM (
    'Draft',
    'In Review',
    'Approved',
    'Superseded',
    'Archived'
);
COMMENT ON TYPE document_status IS 'Document review states';

CREATE TYPE rfi_status AS ENUM (
    'Open',
    'In Progress',
    'Pending Info',
    'Answered',
    'Closed',
    'Void'
);
COMMENT ON TYPE rfi_status IS 'RFI lifecycle states';

CREATE TYPE priority_level AS ENUM (
    'Critical',
    'High',
    'Medium',
    'Low'
);
COMMENT ON TYPE priority_level IS 'Priority classifications';

CREATE TYPE activity_type AS ENUM (
    'Created',
    'Updated',
    'Deleted',
    'Status Change',
    'Document Upload',
    'Document Download',
    'Assignment',
    'Comment',
    'Approval',
    'Rejection'
);
COMMENT ON TYPE activity_type IS 'Audit log activity types';

-- =============================================================================
-- FINANCIAL ENUMS
-- =============================================================================

CREATE TYPE revenue_type AS ENUM (
    'Testing',
    'Travel',
    'Per Diem',
    'Materials',
    'Equipment',
    'Engineering',
    'Report',
    'Other'
);
COMMENT ON TYPE revenue_type IS 'Revenue line item categories';

CREATE TYPE labor_category AS ENUM (
    'Field Tech',
    'Lead Tech',
    'Engineer',
    'Project Manager',
    'Travel',
    'Overtime',
    'Double Time'
);
COMMENT ON TYPE labor_category IS 'Labor cost categories';

-- =============================================================================
-- REFERENCE DATA ENUMS
-- =============================================================================

CREATE TYPE scope_type AS ENUM (
    'ATS',
    'SWGR',
    'XFMR',
    'PDC',
    'MCC',
    'CB',
    'RELAY',
    'CABLE',
    'BATT',
    'UPS',
    'GEN',
    'VFD',
    'CAP',
    'GND',
    'OTHER'
);
COMMENT ON TYPE scope_type IS 'Equipment/scope type codes';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

SELECT 'ENUM types created successfully!' AS status;
SELECT typname, typtype FROM pg_type WHERE typtype = 'e' ORDER BY typname;
-- =============================================================================
-- RESA Power Platform - Table Definitions
-- =============================================================================
-- File: 01_tables.sql
-- Generated: 2025-12-05
-- Source: spec/DATA_DICTIONARY.md v1.0.0
-- Run: AFTER 00_enums.sql
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- CATEGORY 1: CORE TABLES
-- =============================================================================

-- 1.1 Locations (RESA branch offices)
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_name VARCHAR(100) NOT NULL,
    abbreviation VARCHAR(10),
    code VARCHAR(20),
    region VARCHAR(50),
    manager VARCHAR(100),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE locations IS 'RESA branch offices';

-- 1.2 Clients (customer companies)
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_name VARCHAR(200) NOT NULL,
    client_code VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    country VARCHAR(100) DEFAULT 'USA',
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE clients IS 'Customer companies';

-- 1.3 Sites (client facility locations)
CREATE TABLE IF NOT EXISTS sites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID,
    site_name VARCHAR(200) NOT NULL,
    site_code VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    country VARCHAR(100) DEFAULT 'USA',
    contact_name VARCHAR(100),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE sites IS 'Client facility locations';

-- 1.4 Employees (RESA staff)
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_number VARCHAR(50) UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    location_id UUID,
    job_title VARCHAR(100),
    department VARCHAR(100),
    role_type role_type,
    hourly_rate DECIMAL(10,2),
    overtime_rate DECIMAL(10,2),
    burden_rate DECIMAL(5,2),
    neta_certified BOOLEAN DEFAULT false,
    neta_level neta_level,
    certification_expiry DATE,
    hire_date DATE,
    termination_date DATE,
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE employees IS 'RESA staff members';

-- 1.5 Projects (main work tracking)
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_number VARCHAR(50) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    client_id UUID,
    site_id UUID,
    location_id UUID,
    status project_status DEFAULT 'Draft',
    project_type VARCHAR(100),
    business_unit VARCHAR(100),
    quote_date DATE,
    quote_revision VARCHAR(20),
    start_date DATE,
    end_date DATE,
    contract_value DECIMAL(15,2),
    po_number VARCHAR(100),
    project_lead VARCHAR(100),
    estimator VARCHAR(100),
    description TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    -- Rollup fields (trigger-maintained)
    total_apparatus_count INTEGER DEFAULT 0,
    completed_apparatus_count INTEGER DEFAULT 0,
    percent_complete DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE projects IS 'Main project tracking entity';

-- 1.6 Scopes (project phases/work packages)
CREATE TABLE IF NOT EXISTS scopes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL,
    client_id UUID,
    site_id UUID,
    scope_number VARCHAR(50),
    scope_name VARCHAR(200) NOT NULL,
    scope_type scope_type,
    status scope_status DEFAULT 'Not Started',
    percent_complete DECIMAL(5,2) DEFAULT 0,
    planned_start DATE,
    planned_end DATE,
    actual_start DATE,
    actual_end DATE,
    quoted_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2) DEFAULT 0,
    quoted_revenue DECIMAL(15,2),
    actual_revenue DECIMAL(15,2) DEFAULT 0,
    labor_cost DECIMAL(15,2) DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    -- Rollup fields (trigger-maintained)
    total_apparatus_count INTEGER DEFAULT 0,
    completed_apparatus_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE scopes IS 'Project phases/work packages';

-- 1.7 Tasks (work items within scopes)
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID NOT NULL,
    task_number VARCHAR(50),
    task_name VARCHAR(200) NOT NULL,
    task_type VARCHAR(100),
    status task_status DEFAULT 'Not Started',
    percent_complete DECIMAL(5,2) DEFAULT 0,
    planned_start DATE,
    planned_end DATE,
    actual_start DATE,
    actual_end DATE,
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2) DEFAULT 0,
    parent_task_id UUID,
    sort_order INTEGER DEFAULT 0,
    description TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    -- Rollup fields (trigger-maintained)
    apparatus_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE tasks IS 'Work items within scopes';

-- 1.8 Apparatus (equipment being tested)
CREATE TABLE IF NOT EXISTS apparatus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID NOT NULL,
    task_id UUID,
    apparatus_designation VARCHAR(100) NOT NULL,
    apparatus_name VARCHAR(200),
    apparatus_type VARCHAR(100),
    equipment_type VARCHAR(100),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    status apparatus_status DEFAULT 'Not Started',
    assessment apparatus_assessment,
    percent_complete DECIMAL(5,2) DEFAULT 0,
    anticipated_start DATE,
    actual_start DATE,
    actual_end DATE,
    quoted_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2) DEFAULT 0,
    quoted_revenue DECIMAL(12,2),
    actual_revenue DECIMAL(12,2) DEFAULT 0,
    building VARCHAR(100),
    floor VARCHAR(50),
    room VARCHAR(100),
    sort_order INTEGER DEFAULT 0,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE apparatus IS 'Equipment being tested - revenue recognition driver';

-- 1.9 Equipment (company-owned test equipment)
CREATE TABLE IF NOT EXISTS equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_number VARCHAR(50) UNIQUE,
    equipment_name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    location_id UUID,
    assigned_employee_id UUID,
    status equipment_status DEFAULT 'Available',
    calibration_date DATE,
    calibration_due DATE,
    purchase_date DATE,
    purchase_cost DECIMAL(12,2),
    daily_rate DECIMAL(10,2),
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE equipment IS 'Company-owned test equipment';

-- 1.10 Resource Assignments
CREATE TABLE IF NOT EXISTS resource_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL,
    project_id UUID,
    scope_id UUID,
    assignment_type assignment_type,
    start_date DATE,
    end_date DATE,
    allocated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2) DEFAULT 0,
    is_primary BOOLEAN DEFAULT false,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE resource_assignments IS 'Employee-to-project/scope assignments';

-- =============================================================================
-- CATEGORY 2: FINANCIAL TABLES
-- =============================================================================

-- 2.1 Estimators
CREATE TABLE IF NOT EXISTS estimators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    estimator_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    location_id UUID,
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE estimators IS 'Quote creators and rate configuration';

-- 2.2 Apparatus Revenue
CREATE TABLE IF NOT EXISTS apparatus_revenue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    apparatus_id UUID NOT NULL,
    scope_id UUID,
    revenue_type revenue_type,
    quoted_amount DECIMAL(12,2),
    recognized_amount DECIMAL(12,2) DEFAULT 0,
    recognition_date DATE,
    recognition_percent DECIMAL(5,2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE apparatus_revenue IS 'Revenue recognition per apparatus';

-- 2.3 Scope Labor Details
CREATE TABLE IF NOT EXISTS scope_labor_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID NOT NULL,
    labor_category labor_category,
    labor_description VARCHAR(200),
    quoted_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2) DEFAULT 0,
    rate DECIMAL(10,2),
    cost DECIMAL(12,2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE scope_labor_details IS 'Labor line items per scope';

-- 2.4 Scope Financial Summaries
CREATE TABLE IF NOT EXISTS scope_financial_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID UNIQUE NOT NULL,
    total_quoted_revenue DECIMAL(15,2) DEFAULT 0,
    total_recognized_revenue DECIMAL(15,2) DEFAULT 0,
    revenue_recognition_percent DECIMAL(5,2) DEFAULT 0,
    total_quoted_hours DECIMAL(10,2) DEFAULT 0,
    total_actual_hours DECIMAL(10,2) DEFAULT 0,
    hours_variance DECIMAL(10,2) DEFAULT 0,
    total_labor_cost DECIMAL(15,2) DEFAULT 0,
    total_expense_cost DECIMAL(15,2) DEFAULT 0,
    gross_margin DECIMAL(15,2) DEFAULT 0,
    gross_margin_percent DECIMAL(5,2) DEFAULT 0,
    last_calculated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE scope_financial_summaries IS 'Aggregated scope-level financials';

-- 2.5 Project Financial Summaries
CREATE TABLE IF NOT EXISTS project_financial_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID UNIQUE NOT NULL,
    total_quoted_revenue DECIMAL(15,2) DEFAULT 0,
    total_recognized_revenue DECIMAL(15,2) DEFAULT 0,
    revenue_recognition_percent DECIMAL(5,2) DEFAULT 0,
    total_quoted_hours DECIMAL(10,2) DEFAULT 0,
    total_actual_hours DECIMAL(10,2) DEFAULT 0,
    total_labor_cost DECIMAL(15,2) DEFAULT 0,
    total_expense_cost DECIMAL(15,2) DEFAULT 0,
    total_cost DECIMAL(15,2) DEFAULT 0,
    gross_margin DECIMAL(15,2) DEFAULT 0,
    gross_margin_percent DECIMAL(5,2) DEFAULT 0,
    total_scopes INTEGER DEFAULT 0,
    completed_scopes INTEGER DEFAULT 0,
    last_calculated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE project_financial_summaries IS 'Aggregated project-level financials';

-- 2.6 NETA Test Templates
CREATE TABLE IF NOT EXISTS neta_test_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_code VARCHAR(50) NOT NULL,
    template_name VARCHAR(200) NOT NULL,
    apparatus_type VARCHAR(100),
    test_category VARCHAR(100),
    description TEXT,
    estimated_hours DECIMAL(10,2),
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE neta_test_templates IS 'Standard NETA test procedures';

-- =============================================================================
-- CATEGORY 3: REFERENCE TABLES
-- =============================================================================

-- 3.1 Apparatus Types
CREATE TABLE IF NOT EXISTS apparatus_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type_code VARCHAR(50) NOT NULL UNIQUE,
    type_name VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    default_hours DECIMAL(10,2),
    default_rate DECIMAL(10,2),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE apparatus_types IS 'Equipment type master list';

-- =============================================================================
-- CATEGORY 4: PSS PORTAL TABLES
-- =============================================================================

-- 4.1 PSS Engineers
CREATE TABLE IF NOT EXISTS pss_engineers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engineer_name VARCHAR(100) NOT NULL,
    company VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(50),
    specialization VARCHAR(100),
    pe_license VARCHAR(50),
    pe_state VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE pss_engineers IS 'External PSS engineers';

-- 4.2 PSS Document Templates
CREATE TABLE IF NOT EXISTS pss_document_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_code VARCHAR(50) NOT NULL,
    template_name VARCHAR(200) NOT NULL,
    document_type document_type,
    file_path TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE pss_document_templates IS 'Document templates for PSS';

-- 4.3 PSS Studies
CREATE TABLE IF NOT EXISTS pss_studies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID,
    study_number VARCHAR(50) NOT NULL,
    study_name VARCHAR(200) NOT NULL,
    study_type study_type,
    status study_status DEFAULT 'Pending',
    priority priority_level,
    engineer_id UUID,
    requested_date DATE,
    due_date DATE,
    completed_date DATE,
    description TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE pss_studies IS 'Power System Studies tracking';

-- 4.4 PSS Documents
CREATE TABLE IF NOT EXISTS pss_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    study_id UUID NOT NULL,
    template_id UUID,
    document_name VARCHAR(200) NOT NULL,
    document_type document_type,
    version VARCHAR(20),
    status document_status DEFAULT 'Draft',
    file_path TEXT,
    file_size INTEGER,
    uploaded_by UUID,
    uploaded_at TIMESTAMPTZ,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE pss_documents IS 'Study documents';

-- 4.5 PSS RFIs
CREATE TABLE IF NOT EXISTS pss_rfis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    study_id UUID NOT NULL,
    rfi_number VARCHAR(50) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    question TEXT,
    response TEXT,
    status rfi_status DEFAULT 'Open',
    priority priority_level,
    requested_by UUID,
    assigned_to UUID,
    requested_date DATE,
    due_date DATE,
    responded_date DATE,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE pss_rfis IS 'Requests for Information';

-- 4.6 PSS Activity Log
CREATE TABLE IF NOT EXISTS pss_activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    study_id UUID,
    activity_type activity_type NOT NULL,
    activity_description TEXT,
    entity_type VARCHAR(50),
    entity_id UUID,
    old_value TEXT,
    new_value TEXT,
    performed_by UUID,
    performed_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
COMMENT ON TABLE pss_activity_log IS 'Audit trail for PSS portal';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

SELECT 'All tables created successfully!' AS status;
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;
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
-- =============================================================================
-- RESA Power Platform - Triggers
-- =============================================================================
-- File: 03_triggers.sql
-- Generated: 2025-12-05
-- Source: spec/TRIGGER_FLOWS.md v1.0.0
-- Run: AFTER 02_relationships.sql
-- =============================================================================

-- =============================================================================
-- 1. TIMESTAMP TRIGGERS
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
DO $$
DECLARE
    tbl TEXT;
    tables TEXT[] := ARRAY[
        'locations', 'clients', 'sites', 'employees', 'projects', 
        'scopes', 'tasks', 'apparatus', 'equipment', 'resource_assignments',
        'estimators', 'apparatus_revenue', 'scope_labor_details',
        'scope_financial_summaries', 'project_financial_summaries',
        'neta_test_templates', 'apparatus_types', 'pss_engineers',
        'pss_document_templates', 'pss_studies', 'pss_documents', 'pss_rfis'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%s_updated_at ON %s;
            CREATE TRIGGER update_%s_updated_at
            BEFORE UPDATE ON %s
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', tbl, tbl, tbl, tbl);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 2. APPARATUS COUNT ROLLUPS
-- =============================================================================

-- 2.1 Task Apparatus Count
CREATE OR REPLACE FUNCTION update_task_apparatus_count()
RETURNS TRIGGER AS $$
DECLARE
    v_task_id UUID;
    v_old_task_id UUID;
BEGIN
    -- Handle DELETE
    IF TG_OP = 'DELETE' THEN
        v_task_id := OLD.task_id;
        IF v_task_id IS NOT NULL THEN
            UPDATE tasks 
            SET apparatus_count = (
                SELECT COUNT(*) FROM apparatus 
                WHERE task_id = v_task_id AND is_active = true
            )
            WHERE id = v_task_id;
        END IF;
        RETURN OLD;
    END IF;
    
    -- Handle UPDATE with task change
    IF TG_OP = 'UPDATE' AND OLD.task_id IS DISTINCT FROM NEW.task_id THEN
        -- Update old task
        IF OLD.task_id IS NOT NULL THEN
            UPDATE tasks 
            SET apparatus_count = (
                SELECT COUNT(*) FROM apparatus 
                WHERE task_id = OLD.task_id AND is_active = true
            )
            WHERE id = OLD.task_id;
        END IF;
    END IF;
    
    -- Update new/current task
    IF NEW.task_id IS NOT NULL THEN
        UPDATE tasks 
        SET apparatus_count = (
            SELECT COUNT(*) FROM apparatus 
            WHERE task_id = NEW.task_id AND is_active = true
        )
        WHERE id = NEW.task_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_apparatus_count_on_task
    AFTER INSERT OR UPDATE OR DELETE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION update_task_apparatus_count();

-- 2.2 Scope Apparatus Count and Percent Complete
CREATE OR REPLACE FUNCTION update_scope_apparatus_counts()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_id UUID;
    v_total INTEGER;
    v_completed INTEGER;
BEGIN
    -- Determine scope_id
    v_scope_id := COALESCE(NEW.scope_id, OLD.scope_id);
    
    -- Handle scope change on UPDATE
    IF TG_OP = 'UPDATE' AND OLD.scope_id IS DISTINCT FROM NEW.scope_id THEN
        -- Update old scope
        SELECT COUNT(*), COUNT(*) FILTER (WHERE status = 'Complete')
        INTO v_total, v_completed
        FROM apparatus WHERE scope_id = OLD.scope_id AND is_active = true;
        
        UPDATE scopes SET
            total_apparatus_count = v_total,
            completed_apparatus_count = v_completed,
            percent_complete = CASE WHEN v_total > 0 THEN (v_completed::DECIMAL / v_total * 100) ELSE 0 END
        WHERE id = OLD.scope_id;
    END IF;
    
    -- Update current scope
    SELECT COUNT(*), COUNT(*) FILTER (WHERE status = 'Complete')
    INTO v_total, v_completed
    FROM apparatus WHERE scope_id = v_scope_id AND is_active = true;
    
    UPDATE scopes SET
        total_apparatus_count = v_total,
        completed_apparatus_count = v_completed,
        percent_complete = CASE WHEN v_total > 0 THEN (v_completed::DECIMAL / v_total * 100) ELSE 0 END
    WHERE id = v_scope_id;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_apparatus_count_on_scope
    AFTER INSERT OR UPDATE OR DELETE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION update_scope_apparatus_counts();

-- 2.3 Project Apparatus Count (triggered by scope changes)
CREATE OR REPLACE FUNCTION update_project_apparatus_counts()
RETURNS TRIGGER AS $$
DECLARE
    v_project_id UUID;
    v_total INTEGER;
    v_completed INTEGER;
BEGIN
    v_project_id := NEW.project_id;
    
    SELECT 
        COALESCE(SUM(total_apparatus_count), 0),
        COALESCE(SUM(completed_apparatus_count), 0)
    INTO v_total, v_completed
    FROM scopes WHERE project_id = v_project_id AND is_active = true;
    
    UPDATE projects SET
        total_apparatus_count = v_total,
        completed_apparatus_count = v_completed,
        percent_complete = CASE WHEN v_total > 0 THEN (v_completed::DECIMAL / v_total * 100) ELSE 0 END
    WHERE id = v_project_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_project_counts_from_scope
    AFTER UPDATE OF total_apparatus_count, completed_apparatus_count ON scopes
    FOR EACH ROW EXECUTE FUNCTION update_project_apparatus_counts();

-- =============================================================================
-- 3. HOURS ROLLUPS
-- =============================================================================

-- 3.1 Scope Hours from Apparatus
CREATE OR REPLACE FUNCTION update_scope_hours_from_apparatus()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_id UUID;
BEGIN
    v_scope_id := COALESCE(NEW.scope_id, OLD.scope_id);
    
    UPDATE scopes
    SET actual_hours = (
        SELECT COALESCE(SUM(actual_hours), 0)
        FROM apparatus
        WHERE scope_id = v_scope_id AND is_active = true
    )
    WHERE id = v_scope_id;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_scope_hours_from_apparatus
    AFTER INSERT OR UPDATE OF actual_hours OR DELETE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION update_scope_hours_from_apparatus();

-- =============================================================================
-- 4. REVENUE RECOGNITION
-- =============================================================================

CREATE OR REPLACE FUNCTION create_revenue_on_apparatus_complete()
RETURNS TRIGGER AS $$
BEGIN
    -- Only trigger when status changes TO 'Complete'
    IF NEW.status = 'Complete' AND (OLD.status IS NULL OR OLD.status != 'Complete') THEN
        -- Check if revenue record already exists
        IF NOT EXISTS (
            SELECT 1 FROM apparatus_revenue 
            WHERE apparatus_id = NEW.id AND revenue_type = 'Testing'
        ) THEN
            INSERT INTO apparatus_revenue (
                apparatus_id,
                scope_id,
                revenue_type,
                quoted_amount,
                recognized_amount,
                recognition_date,
                recognition_percent
            ) VALUES (
                NEW.id,
                NEW.scope_id,
                'Testing',
                COALESCE(NEW.quoted_revenue, 0),
                COALESCE(NEW.actual_revenue, NEW.quoted_revenue, 0),
                CURRENT_DATE,
                CASE WHEN COALESCE(NEW.quoted_revenue, 0) > 0 
                    THEN (COALESCE(NEW.actual_revenue, NEW.quoted_revenue, 0) / NEW.quoted_revenue * 100)
                    ELSE 100
                END
            );
        ELSE
            -- Update existing revenue record
            UPDATE apparatus_revenue
            SET recognized_amount = COALESCE(NEW.actual_revenue, NEW.quoted_revenue, 0),
                recognition_date = CURRENT_DATE,
                recognition_percent = CASE WHEN COALESCE(NEW.quoted_revenue, 0) > 0 
                    THEN (COALESCE(NEW.actual_revenue, NEW.quoted_revenue, 0) / NEW.quoted_revenue * 100)
                    ELSE 100
                END,
                updated_at = NOW()
            WHERE apparatus_id = NEW.id AND revenue_type = 'Testing';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_revenue_on_apparatus_complete
    AFTER UPDATE OF status ON apparatus
    FOR EACH ROW EXECUTE FUNCTION create_revenue_on_apparatus_complete();

-- =============================================================================
-- 5. FINANCIAL SUMMARY TRIGGERS
-- =============================================================================

-- 5.1 Scope Financial Summary
CREATE OR REPLACE FUNCTION update_scope_financial_summary()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_id UUID;
    v_quoted_rev DECIMAL(15,2);
    v_recognized_rev DECIMAL(15,2);
    v_labor_cost DECIMAL(15,2);
    v_quoted_hrs DECIMAL(10,2);
    v_actual_hrs DECIMAL(10,2);
BEGIN
    v_scope_id := COALESCE(NEW.scope_id, OLD.scope_id);
    
    -- Get revenue totals
    SELECT COALESCE(SUM(quoted_amount), 0), COALESCE(SUM(recognized_amount), 0)
    INTO v_quoted_rev, v_recognized_rev
    FROM apparatus_revenue WHERE scope_id = v_scope_id;
    
    -- Get labor cost
    SELECT COALESCE(SUM(cost), 0)
    INTO v_labor_cost
    FROM scope_labor_details WHERE scope_id = v_scope_id;
    
    -- Get hours from scope
    SELECT COALESCE(quoted_hours, 0), COALESCE(actual_hours, 0)
    INTO v_quoted_hrs, v_actual_hrs
    FROM scopes WHERE id = v_scope_id;
    
    -- Upsert financial summary
    INSERT INTO scope_financial_summaries (
        scope_id,
        total_quoted_revenue,
        total_recognized_revenue,
        revenue_recognition_percent,
        total_quoted_hours,
        total_actual_hours,
        hours_variance,
        total_labor_cost,
        gross_margin,
        gross_margin_percent,
        last_calculated_at
    ) VALUES (
        v_scope_id,
        v_quoted_rev,
        v_recognized_rev,
        CASE WHEN v_quoted_rev > 0 THEN (v_recognized_rev / v_quoted_rev * 100) ELSE 0 END,
        v_quoted_hrs,
        v_actual_hrs,
        v_actual_hrs - v_quoted_hrs,
        v_labor_cost,
        v_recognized_rev - v_labor_cost,
        CASE WHEN v_recognized_rev > 0 THEN ((v_recognized_rev - v_labor_cost) / v_recognized_rev * 100) ELSE 0 END,
        NOW()
    )
    ON CONFLICT (scope_id) DO UPDATE SET
        total_quoted_revenue = EXCLUDED.total_quoted_revenue,
        total_recognized_revenue = EXCLUDED.total_recognized_revenue,
        revenue_recognition_percent = EXCLUDED.revenue_recognition_percent,
        total_quoted_hours = EXCLUDED.total_quoted_hours,
        total_actual_hours = EXCLUDED.total_actual_hours,
        hours_variance = EXCLUDED.hours_variance,
        total_labor_cost = EXCLUDED.total_labor_cost,
        gross_margin = EXCLUDED.gross_margin,
        gross_margin_percent = EXCLUDED.gross_margin_percent,
        last_calculated_at = NOW(),
        updated_at = NOW();
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_scope_financial_from_revenue
    AFTER INSERT OR UPDATE OR DELETE ON apparatus_revenue
    FOR EACH ROW EXECUTE FUNCTION update_scope_financial_summary();

CREATE TRIGGER trg_scope_financial_from_labor
    AFTER INSERT OR UPDATE OR DELETE ON scope_labor_details
    FOR EACH ROW EXECUTE FUNCTION update_scope_financial_summary();

-- 5.2 Project Financial Summary
CREATE OR REPLACE FUNCTION update_project_financial_summary()
RETURNS TRIGGER AS $$
DECLARE
    v_project_id UUID;
BEGIN
    -- Get project_id from scope
    SELECT project_id INTO v_project_id
    FROM scopes WHERE id = NEW.scope_id;
    
    IF v_project_id IS NULL THEN
        RETURN NEW;
    END IF;
    
    -- Upsert project financial summary
    INSERT INTO project_financial_summaries (
        project_id,
        total_quoted_revenue,
        total_recognized_revenue,
        revenue_recognition_percent,
        total_quoted_hours,
        total_actual_hours,
        total_labor_cost,
        total_expense_cost,
        total_cost,
        gross_margin,
        gross_margin_percent,
        total_scopes,
        completed_scopes,
        last_calculated_at
    )
    SELECT 
        v_project_id,
        COALESCE(SUM(sfs.total_quoted_revenue), 0),
        COALESCE(SUM(sfs.total_recognized_revenue), 0),
        CASE WHEN SUM(sfs.total_quoted_revenue) > 0
            THEN (SUM(sfs.total_recognized_revenue) / SUM(sfs.total_quoted_revenue) * 100)
            ELSE 0
        END,
        COALESCE(SUM(sfs.total_quoted_hours), 0),
        COALESCE(SUM(sfs.total_actual_hours), 0),
        COALESCE(SUM(sfs.total_labor_cost), 0),
        COALESCE(SUM(sfs.total_expense_cost), 0),
        COALESCE(SUM(sfs.total_labor_cost), 0) + COALESCE(SUM(sfs.total_expense_cost), 0),
        COALESCE(SUM(sfs.gross_margin), 0),
        CASE WHEN SUM(sfs.total_recognized_revenue) > 0
            THEN (SUM(sfs.gross_margin) / SUM(sfs.total_recognized_revenue) * 100)
            ELSE 0
        END,
        (SELECT COUNT(*) FROM scopes WHERE project_id = v_project_id AND is_active = true),
        (SELECT COUNT(*) FROM scopes WHERE project_id = v_project_id AND status = 'Complete' AND is_active = true),
        NOW()
    FROM scope_financial_summaries sfs
    JOIN scopes s ON s.id = sfs.scope_id
    WHERE s.project_id = v_project_id AND s.is_active = true
    ON CONFLICT (project_id) DO UPDATE SET
        total_quoted_revenue = EXCLUDED.total_quoted_revenue,
        total_recognized_revenue = EXCLUDED.total_recognized_revenue,
        revenue_recognition_percent = EXCLUDED.revenue_recognition_percent,
        total_quoted_hours = EXCLUDED.total_quoted_hours,
        total_actual_hours = EXCLUDED.total_actual_hours,
        total_labor_cost = EXCLUDED.total_labor_cost,
        total_expense_cost = EXCLUDED.total_expense_cost,
        total_cost = EXCLUDED.total_cost,
        gross_margin = EXCLUDED.gross_margin,
        gross_margin_percent = EXCLUDED.gross_margin_percent,
        total_scopes = EXCLUDED.total_scopes,
        completed_scopes = EXCLUDED.completed_scopes,
        last_calculated_at = NOW(),
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_project_financial_from_scope
    AFTER INSERT OR UPDATE ON scope_financial_summaries
    FOR EACH ROW EXECUTE FUNCTION update_project_financial_summary();

-- =============================================================================
-- 6. PSS PORTAL TRIGGERS
-- =============================================================================

-- 6.1 Log Study Status Changes
CREATE OR REPLACE FUNCTION log_pss_study_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO pss_activity_log (
            study_id,
            activity_type,
            activity_description,
            entity_type,
            entity_id,
            old_value,
            new_value,
            performed_at
        ) VALUES (
            NEW.id,
            'Status Change',
            'Study status changed from ' || COALESCE(OLD.status::TEXT, 'NULL') || ' to ' || NEW.status::TEXT,
            'pss_studies',
            NEW.id,
            OLD.status::TEXT,
            NEW.status::TEXT,
            NOW()
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_study_status
    AFTER UPDATE OF status ON pss_studies
    FOR EACH ROW EXECUTE FUNCTION log_pss_study_status_change();

-- 6.2 Log Document Uploads
CREATE OR REPLACE FUNCTION log_pss_document_upload()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO pss_activity_log (
        study_id,
        activity_type,
        activity_description,
        entity_type,
        entity_id,
        new_value,
        performed_by,
        performed_at
    ) VALUES (
        NEW.study_id,
        'Document Upload',
        'Document uploaded: ' || NEW.document_name,
        'pss_documents',
        NEW.id,
        NEW.document_name,
        NEW.uploaded_by,
        NOW()
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_document_upload
    AFTER INSERT ON pss_documents
    FOR EACH ROW EXECUTE FUNCTION log_pss_document_upload();

-- =============================================================================
-- VERIFICATION
-- =============================================================================

SELECT 'All triggers created successfully!' AS status;

SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_timing
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;
-- =============================================================================
-- RESA Power Platform - Views
-- =============================================================================
-- File: 04_views.sql
-- Generated: 2025-12-05
-- Source: spec/VIEW_DEFINITIONS.md v1.0.0
-- Run: AFTER 03_triggers.sql
-- =============================================================================

-- =============================================================================
-- PROJECT MANAGEMENT VIEWS
-- =============================================================================

-- v_projects_full: Complete project information
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
    c.id AS client_id,
    c.client_name,
    c.client_code,
    s.id AS site_id,
    s.site_name,
    s.city AS site_city,
    s.state AS site_state,
    l.id AS location_id,
    l.location_name AS branch_name,
    l.abbreviation AS branch_code,
    p.created_at,
    p.updated_at
FROM projects p
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN sites s ON p.site_id = s.id
LEFT JOIN locations l ON p.location_id = l.id
WHERE p.is_active = true;

COMMENT ON VIEW v_projects_full IS 'Complete project data with related entity names';

-- v_projects_summary: Dashboard-ready summary
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
    COALESCE(pfs.total_recognized_revenue, 0) AS recognized_revenue,
    COALESCE(pfs.revenue_recognition_percent, 0) AS revenue_percent,
    COALESCE(pfs.total_actual_hours, 0) AS actual_hours,
    COALESCE(pfs.gross_margin_percent, 0) AS margin_percent,
    (SELECT COUNT(*) FROM scopes WHERE project_id = p.id AND is_active = true) AS scope_count,
    (SELECT COUNT(*) FROM scopes WHERE project_id = p.id AND status = 'Complete' AND is_active = true) AS completed_scopes
FROM projects p
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN locations l ON p.location_id = l.id
LEFT JOIN project_financial_summaries pfs ON pfs.project_id = p.id
WHERE p.is_active = true;

COMMENT ON VIEW v_projects_summary IS 'Dashboard summary of projects with key metrics';

-- v_projects_active: Active projects for operations
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

-- =============================================================================
-- SCOPE & TASK VIEWS
-- =============================================================================

-- v_scopes_full: Complete scope information
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
    p.id AS project_id,
    p.project_number,
    p.project_name,
    c.id AS client_id,
    c.client_name,
    sc.created_at,
    sc.updated_at
FROM scopes sc
JOIN projects p ON sc.project_id = p.id
LEFT JOIN clients c ON sc.client_id = c.id
WHERE sc.is_active = true;

COMMENT ON VIEW v_scopes_full IS 'Complete scope data with project and client context';

-- v_tasks_with_scope: Tasks with hierarchy
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
    sc.id AS scope_id,
    sc.scope_number,
    sc.scope_name,
    p.id AS project_id,
    p.project_number,
    t.parent_task_id,
    pt.task_name AS parent_task_name
FROM tasks t
JOIN scopes sc ON t.scope_id = sc.id
JOIN projects p ON sc.project_id = p.id
LEFT JOIN tasks pt ON t.parent_task_id = pt.id
WHERE t.is_active = true;

COMMENT ON VIEW v_tasks_with_scope IS 'Tasks with full hierarchy context';

-- =============================================================================
-- APPARATUS VIEWS
-- =============================================================================

-- v_apparatus_full: Complete apparatus with hierarchy
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
    t.id AS task_id,
    t.task_name,
    sc.id AS scope_id,
    sc.scope_number,
    sc.scope_name,
    p.id AS project_id,
    p.project_number,
    p.project_name,
    c.client_name,
    s.site_name,
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

-- v_apparatus_testing_status: Field crew view
CREATE OR REPLACE VIEW v_apparatus_testing_status AS
SELECT 
    a.id,
    a.apparatus_designation,
    a.apparatus_type,
    a.status,
    a.assessment,
    a.anticipated_start,
    a.actual_start,
    CONCAT_WS(' ', a.building, a.floor, a.room) AS location,
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

-- =============================================================================
-- FINANCIAL VIEWS
-- =============================================================================

-- v_scope_financials: Scope-level financial details
CREATE OR REPLACE VIEW v_scope_financials AS
SELECT 
    sc.id AS scope_id,
    sc.scope_number,
    sc.scope_name,
    p.project_number,
    p.project_name,
    c.client_name,
    COALESCE(sfs.total_quoted_revenue, 0) AS quoted_revenue,
    COALESCE(sfs.total_quoted_hours, 0) AS quoted_hours,
    COALESCE(sfs.total_recognized_revenue, 0) AS recognized_revenue,
    COALESCE(sfs.total_actual_hours, 0) AS actual_hours,
    COALESCE(sfs.revenue_recognition_percent, 0) AS revenue_percent,
    COALESCE(sfs.hours_variance, 0) AS hours_variance,
    COALESCE(sfs.total_labor_cost, 0) AS labor_cost,
    COALESCE(sfs.gross_margin, 0) AS gross_margin,
    COALESCE(sfs.gross_margin_percent, 0) AS margin_percent,
    sc.status,
    sfs.last_calculated_at
FROM scopes sc
JOIN projects p ON sc.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN scope_financial_summaries sfs ON sfs.scope_id = sc.id
WHERE sc.is_active = true;

COMMENT ON VIEW v_scope_financials IS 'Scope-level financial performance';

-- v_project_financials: Project-level financial summary
CREATE OR REPLACE VIEW v_project_financials AS
SELECT 
    p.id AS project_id,
    p.project_number,
    p.project_name,
    c.client_name,
    l.location_name AS branch,
    p.contract_value,
    COALESCE(pfs.total_quoted_revenue, 0) AS quoted_revenue,
    COALESCE(pfs.total_recognized_revenue, 0) AS recognized_revenue,
    COALESCE(pfs.revenue_recognition_percent, 0) AS revenue_percent,
    COALESCE(pfs.total_quoted_hours, 0) AS quoted_hours,
    COALESCE(pfs.total_actual_hours, 0) AS actual_hours,
    COALESCE(pfs.total_labor_cost, 0) AS labor_cost,
    COALESCE(pfs.total_expense_cost, 0) AS expense_cost,
    COALESCE(pfs.total_cost, 0) AS total_cost,
    COALESCE(pfs.gross_margin, 0) AS gross_margin,
    COALESCE(pfs.gross_margin_percent, 0) AS margin_percent,
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

-- v_revenue_by_apparatus: Revenue detail
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

-- =============================================================================
-- EMPLOYEE & RESOURCE VIEWS
-- =============================================================================

-- v_employees_full: Complete employee info
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

-- v_resource_assignments_full: Assignments with names
CREATE OR REPLACE VIEW v_resource_assignments_full AS
SELECT 
    ra.id,
    ra.assignment_type,
    ra.start_date,
    ra.end_date,
    ra.allocated_hours,
    ra.actual_hours,
    ra.is_primary,
    e.id AS employee_id,
    e.first_name || ' ' || e.last_name AS employee_name,
    e.role_type,
    p.id AS project_id,
    p.project_number,
    p.project_name,
    sc.id AS scope_id,
    sc.scope_name
FROM resource_assignments ra
JOIN employees e ON ra.employee_id = e.id
LEFT JOIN projects p ON ra.project_id = p.id
LEFT JOIN scopes sc ON ra.scope_id = sc.id
WHERE ra.is_active = true;

COMMENT ON VIEW v_resource_assignments_full IS 'Resource assignments with employee and project names';

-- =============================================================================
-- PSS PORTAL VIEWS
-- =============================================================================

-- v_pss_studies_full: Complete study info
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
    eng.id AS engineer_id,
    eng.engineer_name,
    eng.company AS engineer_company,
    p.id AS project_id,
    p.project_number,
    p.project_name,
    c.client_name,
    (SELECT COUNT(*) FROM pss_documents WHERE study_id = ps.id AND is_active = true) AS document_count,
    (SELECT COUNT(*) FROM pss_rfis WHERE study_id = ps.id AND status = 'Open') AS open_rfi_count,
    ps.created_at,
    ps.updated_at
FROM pss_studies ps
LEFT JOIN pss_engineers eng ON ps.engineer_id = eng.id
LEFT JOIN projects p ON ps.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id
WHERE ps.is_active = true;

COMMENT ON VIEW v_pss_studies_full IS 'Complete PSS study information with status';

-- v_pss_dashboard: PSS dashboard summary
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

-- =============================================================================
-- BRANCH SUMMARY VIEW
-- =============================================================================

CREATE OR REPLACE VIEW v_branch_summary AS
SELECT 
    l.id AS location_id,
    l.location_name AS branch,
    l.abbreviation AS branch_code,
    l.manager,
    (SELECT COUNT(*) FROM projects WHERE location_id = l.id AND status = 'Active') AS active_projects,
    (SELECT COUNT(*) FROM employees WHERE location_id = l.id AND is_active = true) AS employee_count,
    (SELECT COUNT(*) FROM equipment WHERE location_id = l.id AND is_active = true) AS equipment_count,
    (SELECT COALESCE(SUM(pfs.total_recognized_revenue), 0)
     FROM project_financial_summaries pfs
     JOIN projects p ON pfs.project_id = p.id
     WHERE p.location_id = l.id
       AND pfs.last_calculated_at >= DATE_TRUNC('month', CURRENT_DATE)
    ) AS mtd_revenue
FROM locations l
WHERE l.is_active = true;

COMMENT ON VIEW v_branch_summary IS 'Branch-level operational summary';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

SELECT 'All views created successfully!' AS status;

SELECT table_name AS view_name
FROM information_schema.views
WHERE table_schema = 'public'
ORDER BY table_name;
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
-- =============================================================================
-- RESA Power Platform - Seed Data (Reference Tables)
-- =============================================================================
-- File: 10_seed_data.sql
-- Generated: 2025-12-05
-- Purpose: Populate reference/master tables with initial data
-- Run: AFTER all schema files (00-05)
-- =============================================================================

-- =============================================================================
-- 1. LOCATIONS (RESA Branch Offices)
-- =============================================================================

INSERT INTO locations (id, location_name, abbreviation, code, region, city, state, zip, is_active, sort_order) VALUES
('10000000-0000-0000-0000-000000000001', 'Fenton', 'FEN', 'FENTON', 'Midwest', 'Fenton', 'MO', '63026', true, 1),
('10000000-0000-0000-0000-000000000002', 'Dallas', 'DAL', 'DALLAS', 'Southwest', 'Dallas', 'TX', '75201', true, 2),
('10000000-0000-0000-0000-000000000003', 'Houston', 'HOU', 'HOUSTON', 'Southwest', 'Houston', 'TX', '77001', true, 3),
('10000000-0000-0000-0000-000000000004', 'Phoenix', 'PHX', 'PHOENIX', 'Southwest', 'Phoenix', 'AZ', '85001', true, 4),
('10000000-0000-0000-0000-000000000005', 'Atlanta', 'ATL', 'ATLANTA', 'Southeast', 'Atlanta', 'GA', '30301', true, 5);

-- =============================================================================
-- 2. APPARATUS TYPES (Equipment Categories)
-- =============================================================================

INSERT INTO apparatus_types (id, type_code, type_name, category, default_hours, default_rate, description, is_active, sort_order) VALUES
-- Transformers
('20000000-0000-0000-0000-000000000001', 'XFMR-DRY', 'Dry-Type Transformer', 'Transformer', 4.0, 175.00, 'Dry-type transformer testing per NETA 7.2', true, 10),
('20000000-0000-0000-0000-000000000002', 'XFMR-OIL', 'Oil-Filled Transformer', 'Transformer', 8.0, 175.00, 'Liquid-filled transformer testing per NETA 7.2', true, 11),
('20000000-0000-0000-0000-000000000003', 'XFMR-PAD', 'Pad-Mount Transformer', 'Transformer', 6.0, 175.00, 'Pad-mounted transformer testing', true, 12),

-- Switchgear
('20000000-0000-0000-0000-000000000010', 'SWGR-MV', 'Medium Voltage Switchgear', 'Switchgear', 6.0, 185.00, 'MV switchgear testing per NETA 7.3', true, 20),
('20000000-0000-0000-0000-000000000011', 'SWGR-LV', 'Low Voltage Switchgear', 'Switchgear', 4.0, 175.00, 'LV switchgear testing per NETA 7.3', true, 21),
('20000000-0000-0000-0000-000000000012', 'SWGR-ARC', 'Arc-Resistant Switchgear', 'Switchgear', 8.0, 195.00, 'Arc-resistant switchgear testing', true, 22),

-- Circuit Breakers
('20000000-0000-0000-0000-000000000020', 'CB-MV-VAC', 'MV Vacuum Circuit Breaker', 'Circuit Breaker', 3.0, 185.00, 'Medium voltage vacuum breaker per NETA 7.6', true, 30),
('20000000-0000-0000-0000-000000000021', 'CB-MV-SF6', 'MV SF6 Circuit Breaker', 'Circuit Breaker', 4.0, 195.00, 'SF6 circuit breaker testing', true, 31),
('20000000-0000-0000-0000-000000000022', 'CB-LV-ACB', 'LV Air Circuit Breaker', 'Circuit Breaker', 2.0, 175.00, 'Low voltage ACB testing per NETA 7.6', true, 32),
('20000000-0000-0000-0000-000000000023', 'CB-LV-MCCB', 'Molded Case Circuit Breaker', 'Circuit Breaker', 1.0, 165.00, 'MCCB testing per NETA 7.6', true, 33),
('20000000-0000-0000-0000-000000000024', 'CB-LV-ICCB', 'Insulated Case Circuit Breaker', 'Circuit Breaker', 1.5, 175.00, 'ICCB testing per NETA 7.6', true, 34),

-- Protective Relays
('20000000-0000-0000-0000-000000000030', 'RELAY-ELEC', 'Electromechanical Relay', 'Protective Relay', 2.0, 185.00, 'Electromechanical relay testing per NETA 7.9', true, 40),
('20000000-0000-0000-0000-000000000031', 'RELAY-SOLID', 'Solid-State Relay', 'Protective Relay', 2.5, 185.00, 'Solid-state relay testing per NETA 7.9', true, 41),
('20000000-0000-0000-0000-000000000032', 'RELAY-MICRO', 'Microprocessor Relay', 'Protective Relay', 3.0, 195.00, 'Microprocessor relay testing per NETA 7.9', true, 42),

-- Motor Control
('20000000-0000-0000-0000-000000000040', 'MCC-UNIT', 'MCC Unit', 'Motor Control', 1.5, 165.00, 'Motor control center unit testing', true, 50),
('20000000-0000-0000-0000-000000000041', 'MCC-SECT', 'MCC Section', 'Motor Control', 4.0, 175.00, 'MCC section testing', true, 51),
('20000000-0000-0000-0000-000000000042', 'VFD', 'Variable Frequency Drive', 'Motor Control', 2.0, 185.00, 'VFD testing and commissioning', true, 52),
('20000000-0000-0000-0000-000000000043', 'STARTER', 'Motor Starter', 'Motor Control', 1.0, 165.00, 'Motor starter testing', true, 53),

-- Transfer Switches
('20000000-0000-0000-0000-000000000050', 'ATS-AUTO', 'Automatic Transfer Switch', 'Transfer Switch', 3.0, 175.00, 'ATS testing per NETA 7.22', true, 60),
('20000000-0000-0000-0000-000000000051', 'ATS-MAN', 'Manual Transfer Switch', 'Transfer Switch', 1.5, 165.00, 'Manual transfer switch testing', true, 61),
('20000000-0000-0000-0000-000000000052', 'ATS-BYPASS', 'Bypass Isolation Switch', 'Transfer Switch', 2.0, 175.00, 'Bypass isolation switch testing', true, 62),

-- Cables
('20000000-0000-0000-0000-000000000060', 'CABLE-MV', 'Medium Voltage Cable', 'Cable', 2.0, 175.00, 'MV cable testing per NETA 7.3.2', true, 70),
('20000000-0000-0000-0000-000000000061', 'CABLE-LV', 'Low Voltage Cable', 'Cable', 1.0, 165.00, 'LV cable testing', true, 71),

-- Batteries & UPS
('20000000-0000-0000-0000-000000000070', 'BATT-VRLA', 'VRLA Battery System', 'Battery', 4.0, 175.00, 'VRLA battery testing per NETA 7.24', true, 80),
('20000000-0000-0000-0000-000000000071', 'BATT-FLOOD', 'Flooded Battery System', 'Battery', 6.0, 175.00, 'Flooded cell battery testing', true, 81),
('20000000-0000-0000-0000-000000000072', 'UPS-STATIC', 'Static UPS', 'UPS', 4.0, 185.00, 'Static UPS testing per NETA 7.25', true, 82),
('20000000-0000-0000-0000-000000000073', 'UPS-ROTARY', 'Rotary UPS', 'UPS', 6.0, 195.00, 'Rotary UPS testing', true, 83),

-- Generators
('20000000-0000-0000-0000-000000000080', 'GEN-DIESEL', 'Diesel Generator', 'Generator', 6.0, 185.00, 'Diesel generator testing per NETA 7.21', true, 90),
('20000000-0000-0000-0000-000000000081', 'GEN-GAS', 'Natural Gas Generator', 'Generator', 6.0, 185.00, 'Natural gas generator testing', true, 91),

-- Grounding
('20000000-0000-0000-0000-000000000090', 'GND-SYSTEM', 'Grounding System', 'Grounding', 4.0, 175.00, 'Grounding system testing per NETA 7.13', true, 100),
('20000000-0000-0000-0000-000000000091', 'GND-GRID', 'Ground Grid', 'Grounding', 8.0, 185.00, 'Ground grid testing', true, 101),

-- Other
('20000000-0000-0000-0000-000000000100', 'CAP-BANK', 'Capacitor Bank', 'Capacitor', 3.0, 175.00, 'Capacitor bank testing per NETA 7.8', true, 110),
('20000000-0000-0000-0000-000000000101', 'PDC', 'Power Distribution Center', 'Distribution', 4.0, 175.00, 'PDC testing', true, 111),
('20000000-0000-0000-0000-000000000102', 'PANEL', 'Panelboard', 'Distribution', 1.5, 165.00, 'Panelboard testing per NETA 7.5', true, 112);

-- =============================================================================
-- 3. NETA TEST TEMPLATES
-- =============================================================================

INSERT INTO neta_test_templates (id, template_code, template_name, apparatus_type, test_category, description, estimated_hours, is_active, sort_order) VALUES
-- Transformer Tests
('30000000-0000-0000-0000-000000000001', 'NETA-7.2.1', 'Transformer Visual Inspection', 'Transformer', 'Visual', 'Visual and mechanical inspection per NETA ATS 7.2.1', 0.5, true, 1),
('30000000-0000-0000-0000-000000000002', 'NETA-7.2.2', 'Transformer Insulation Resistance', 'Transformer', 'Electrical', 'Insulation resistance testing per NETA ATS 7.2.2', 1.0, true, 2),
('30000000-0000-0000-0000-000000000003', 'NETA-7.2.3', 'Transformer Turns Ratio', 'Transformer', 'Electrical', 'Turns ratio testing per NETA ATS 7.2.3', 1.0, true, 3),
('30000000-0000-0000-0000-000000000004', 'NETA-7.2.4', 'Transformer Winding Resistance', 'Transformer', 'Electrical', 'Winding resistance per NETA ATS 7.2.4', 1.0, true, 4),
('30000000-0000-0000-0000-000000000005', 'NETA-7.2.5', 'Transformer Oil Analysis', 'Transformer', 'Oil', 'Insulating liquid tests per NETA ATS 7.2.5', 0.5, true, 5),

-- Switchgear Tests
('30000000-0000-0000-0000-000000000010', 'NETA-7.3.1', 'Switchgear Visual Inspection', 'Switchgear', 'Visual', 'Visual and mechanical inspection per NETA ATS 7.3.1', 1.0, true, 10),
('30000000-0000-0000-0000-000000000011', 'NETA-7.3.2', 'Switchgear Insulation Resistance', 'Switchgear', 'Electrical', 'Insulation resistance testing per NETA ATS 7.3.2', 1.5, true, 11),
('30000000-0000-0000-0000-000000000012', 'NETA-7.3.3', 'Switchgear Contact Resistance', 'Switchgear', 'Electrical', 'Contact resistance testing per NETA ATS 7.3.3', 1.0, true, 12),

-- Circuit Breaker Tests
('30000000-0000-0000-0000-000000000020', 'NETA-7.6.1', 'Breaker Visual Inspection', 'Circuit Breaker', 'Visual', 'Visual and mechanical inspection per NETA ATS 7.6.1', 0.5, true, 20),
('30000000-0000-0000-0000-000000000021', 'NETA-7.6.2', 'Breaker Contact Resistance', 'Circuit Breaker', 'Electrical', 'Contact resistance per NETA ATS 7.6.2', 0.5, true, 21),
('30000000-0000-0000-0000-000000000022', 'NETA-7.6.3', 'Breaker Insulation Resistance', 'Circuit Breaker', 'Electrical', 'Insulation resistance per NETA ATS 7.6.3', 0.5, true, 22),
('30000000-0000-0000-0000-000000000023', 'NETA-7.6.4', 'Breaker Trip Testing', 'Circuit Breaker', 'Functional', 'Trip unit testing per NETA ATS 7.6.4', 1.0, true, 23),
('30000000-0000-0000-0000-000000000024', 'NETA-7.6.5', 'Breaker Timing', 'Circuit Breaker', 'Timing', 'Operating time testing per NETA ATS 7.6.5', 0.5, true, 24),

-- Relay Tests
('30000000-0000-0000-0000-000000000030', 'NETA-7.9.1', 'Relay Visual Inspection', 'Protective Relay', 'Visual', 'Visual inspection per NETA ATS 7.9.1', 0.25, true, 30),
('30000000-0000-0000-0000-000000000031', 'NETA-7.9.2', 'Relay Settings Verification', 'Protective Relay', 'Settings', 'Settings verification per NETA ATS 7.9.2', 0.5, true, 31),
('30000000-0000-0000-0000-000000000032', 'NETA-7.9.3', 'Relay Pickup Testing', 'Protective Relay', 'Functional', 'Pickup testing per NETA ATS 7.9.3', 1.0, true, 32),
('30000000-0000-0000-0000-000000000033', 'NETA-7.9.4', 'Relay Timing Testing', 'Protective Relay', 'Timing', 'Timing curve verification per NETA ATS 7.9.4', 1.0, true, 33),

-- Cable Tests
('30000000-0000-0000-0000-000000000040', 'NETA-7.3.2.1', 'Cable Insulation Resistance', 'Cable', 'Electrical', 'Cable insulation resistance per NETA ATS', 0.5, true, 40),
('30000000-0000-0000-0000-000000000041', 'NETA-7.3.2.2', 'Cable Hi-Pot Testing', 'Cable', 'Electrical', 'Cable DC hi-pot testing', 1.0, true, 41),
('30000000-0000-0000-0000-000000000042', 'NETA-7.3.2.3', 'Cable VLF Testing', 'Cable', 'Electrical', 'VLF withstand testing', 1.5, true, 42),

-- ATS Tests
('30000000-0000-0000-0000-000000000050', 'NETA-7.22.1', 'ATS Visual Inspection', 'Transfer Switch', 'Visual', 'Visual inspection per NETA ATS 7.22', 0.5, true, 50),
('30000000-0000-0000-0000-000000000051', 'NETA-7.22.2', 'ATS Transfer Testing', 'Transfer Switch', 'Functional', 'Transfer operation testing', 1.0, true, 51),
('30000000-0000-0000-0000-000000000052', 'NETA-7.22.3', 'ATS Timing Verification', 'Transfer Switch', 'Timing', 'Transfer timing verification', 0.5, true, 52),

-- Battery Tests
('30000000-0000-0000-0000-000000000060', 'NETA-7.24.1', 'Battery Visual Inspection', 'Battery', 'Visual', 'Visual inspection per NETA ATS 7.24', 0.5, true, 60),
('30000000-0000-0000-0000-000000000061', 'NETA-7.24.2', 'Battery Impedance Testing', 'Battery', 'Electrical', 'Cell impedance testing', 2.0, true, 61),
('30000000-0000-0000-0000-000000000062', 'NETA-7.24.3', 'Battery Capacity Testing', 'Battery', 'Capacity', 'Discharge capacity testing', 4.0, true, 62),

-- UPS Tests
('30000000-0000-0000-0000-000000000070', 'NETA-7.25.1', 'UPS Visual Inspection', 'UPS', 'Visual', 'Visual inspection per NETA ATS 7.25', 0.5, true, 70),
('30000000-0000-0000-0000-000000000071', 'NETA-7.25.2', 'UPS Functional Testing', 'UPS', 'Functional', 'Transfer and bypass testing', 2.0, true, 71),
('30000000-0000-0000-0000-000000000072', 'NETA-7.25.3', 'UPS Load Bank Testing', 'UPS', 'Load', 'Load bank testing', 2.0, true, 72),

-- Generator Tests
('30000000-0000-0000-0000-000000000080', 'NETA-7.21.1', 'Generator Visual Inspection', 'Generator', 'Visual', 'Visual inspection per NETA ATS 7.21', 0.5, true, 80),
('30000000-0000-0000-0000-000000000081', 'NETA-7.21.2', 'Generator Insulation Resistance', 'Generator', 'Electrical', 'Stator insulation resistance', 1.0, true, 81),
('30000000-0000-0000-0000-000000000082', 'NETA-7.21.3', 'Generator Load Bank Test', 'Generator', 'Load', 'Load bank testing', 2.0, true, 82),

-- Grounding Tests
('30000000-0000-0000-0000-000000000090', 'NETA-7.13.1', 'Ground Resistance Testing', 'Grounding', 'Electrical', 'Ground resistance per NETA ATS 7.13', 1.0, true, 90),
('30000000-0000-0000-0000-000000000091', 'NETA-7.13.2', 'Ground Grid Testing', 'Grounding', 'Electrical', 'Ground grid integrity testing', 2.0, true, 91);

-- =============================================================================
-- 4. PSS DOCUMENT TEMPLATES
-- =============================================================================

INSERT INTO pss_document_templates (id, template_code, template_name, document_type, description, is_active, sort_order) VALUES
('40000000-0000-0000-0000-000000000001', 'PSS-RPT-AF', 'Arc Flash Study Report', 'Study Report', 'Standard arc flash analysis report template', true, 1),
('40000000-0000-0000-0000-000000000002', 'PSS-RPT-SC', 'Short Circuit Study Report', 'Short Circuit Report', 'Short circuit analysis report template', true, 2),
('40000000-0000-0000-0000-000000000003', 'PSS-RPT-COORD', 'Coordination Study Report', 'Study Report', 'Protective device coordination report template', true, 3),
('40000000-0000-0000-0000-000000000004', 'PSS-DWG-OL', 'One-Line Diagram', 'One-Line Diagram', 'Electrical one-line diagram template', true, 4),
('40000000-0000-0000-0000-000000000005', 'PSS-TCC', 'Time-Current Curves', 'Coordination Curves', 'TCC curve package template', true, 5),
('40000000-0000-0000-0000-000000000006', 'PSS-LBL-AF', 'Arc Flash Labels', 'Arc Flash Labels', 'Arc flash warning label package', true, 6),
('40000000-0000-0000-0000-000000000007', 'PSS-DATA', 'Data Collection Form', 'Data Collection', 'Field data collection template', true, 7),
('40000000-0000-0000-0000-000000000008', 'PSS-EQUIP', 'Equipment Schedule', 'Equipment Schedule', 'Equipment data schedule template', true, 8);

-- =============================================================================
-- 5. ESTIMATORS (Sample)
-- =============================================================================

INSERT INTO estimators (id, estimator_name, email, location_id, is_active) VALUES
('50000000-0000-0000-0000-000000000001', 'Standard Field Rate', 'estimating@resapower.com', '10000000-0000-0000-0000-000000000001', true),
('50000000-0000-0000-0000-000000000002', 'Premium Rate', 'estimating@resapower.com', '10000000-0000-0000-0000-000000000001', true),
('50000000-0000-0000-0000-000000000003', 'Emergency Rate', 'estimating@resapower.com', '10000000-0000-0000-0000-000000000001', true);

-- =============================================================================
-- VERIFICATION
-- =============================================================================

SELECT 'Seed data inserted successfully!' AS status;

SELECT 'Locations' AS table_name, COUNT(*) AS row_count FROM locations
UNION ALL
SELECT 'Apparatus Types', COUNT(*) FROM apparatus_types
UNION ALL
SELECT 'NETA Templates', COUNT(*) FROM neta_test_templates
UNION ALL
SELECT 'PSS Doc Templates', COUNT(*) FROM pss_document_templates
UNION ALL
SELECT 'Estimators', COUNT(*) FROM estimators;
-- =============================================================================
-- RESA Power Platform - LASNAP16 Test Data
-- =============================================================================
-- File: 11_test_data.sql
-- Generated: 2025-12-05
-- Source: spec/TEST_DATA_PLAN.md, LASNAP16/RESA Power - LASNAP16 MASTER.xlsm
-- Run: AFTER 10_seed_data.sql
-- =============================================================================

-- UUID Pattern: {prefix}-0000-0000-0000-{seq}
-- Prefix key:
--   11111111 = clients
--   22222222 = sites
--   33333333 = projects
--   44444444 = scopes
--   55555555 = tasks
--   66666666 = apparatus
--   77777777 = employees
--   88888888 = resource_assignments
--   99999999 = apparatus_revenue
--   AAAAAAAA = scope_labor_details
-- 
-- Reference IDs from 10_seed_data.sql:
--   10000000-...-00000000000X = locations (Fenton=001)
--   20000000-...-00000000000X = apparatus_types

BEGIN;

-- =============================================================================
-- EMPLOYEES (5 test employees)
-- =============================================================================

INSERT INTO employees (id, employee_number, first_name, last_name, email, phone, location_id, job_title, role_type, hourly_rate, overtime_rate, neta_certified, neta_level, is_active) VALUES
('77777777-0000-0000-0000-000000000001', 'EMP001', 'Mike', 'Johnson', 'mike.johnson@resapower.com', '314-555-0101', '10000000-0000-0000-0000-000000000001', 'Lead Technician', 'Lead Tech', 95.00, 142.50, true, 'Level III', true),
('77777777-0000-0000-0000-000000000002', 'EMP002', 'Sarah', 'Chen', 'sarah.chen@resapower.com', '314-555-0102', '10000000-0000-0000-0000-000000000001', 'Field Technician', 'Field Tech', 75.00, 112.50, true, 'Level II', true),
('77777777-0000-0000-0000-000000000003', 'EMP003', 'David', 'Martinez', 'david.martinez@resapower.com', '314-555-0103', '10000000-0000-0000-0000-000000000001', 'Field Technician', 'Field Tech', 75.00, 112.50, true, 'Level II', true),
('77777777-0000-0000-0000-000000000004', 'EMP004', 'Jennifer', 'Williams', 'jennifer.williams@resapower.com', '314-555-0104', '10000000-0000-0000-0000-000000000001', 'Project Manager', 'Project Manager', 125.00, 187.50, false, NULL, true),
('77777777-0000-0000-0000-000000000005', 'EMP005', 'Robert', 'Taylor', 'robert.taylor@resapower.com', '314-555-0105', '10000000-0000-0000-0000-000000000001', 'Engineer', 'Engineer', 110.00, 165.00, true, 'Level IV', true);

-- =============================================================================
-- CLIENT
-- =============================================================================

INSERT INTO clients (id, client_name, client_code, address, city, state, zip, phone, email, is_active) VALUES
('11111111-0000-0000-0000-000000000001', 'Louisiana Snap Foods Corporation', 'LASNAP', '1234 Industrial Pkwy', 'Baton Rouge', 'LA', '70801', '225-555-1000', 'facilities@lasnapfoods.com', true);

-- =============================================================================
-- SITE
-- =============================================================================

INSERT INTO sites (id, client_id, site_name, site_code, address, city, state, zip, contact_name, contact_phone, contact_email, is_active) VALUES
('22222222-0000-0000-0000-000000000001', '11111111-0000-0000-0000-000000000001', 'LASNAP Main Manufacturing Plant', 'LASNAP16-MAIN', '5678 Plant Road', 'Baton Rouge', 'LA', '70802', 'Tom Richards', '225-555-1100', 'trichards@lasnapfoods.com', true);

-- =============================================================================
-- PROJECT
-- =============================================================================

INSERT INTO projects (id, project_number, project_name, client_id, site_id, location_id, status, project_type, business_unit, quote_date, start_date, end_date, contract_value, po_number, project_lead, estimator, description, is_active) VALUES
('33333333-0000-0000-0000-000000000001', 'LASNAP16', 'LASNAP Foods - Annual Maintenance Testing 2016', '11111111-0000-0000-0000-000000000001', '22222222-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'Active', 'Annual Maintenance', 'Electrical Testing', '2016-01-15', '2016-02-01', '2016-06-30', 187500.00, 'PO-2016-4521', 'Mike Johnson', 'Jennifer Williams', 'Comprehensive annual NETA maintenance testing for main manufacturing facility including substations, switchgear, transformers, and motor control centers.', true);

-- =============================================================================
-- SCOPES (4 scopes for LASNAP16)
-- =============================================================================

INSERT INTO scopes (id, project_id, client_id, site_id, scope_number, scope_name, scope_type, status, planned_start, planned_end, quoted_hours, quoted_revenue, sort_order, is_active) VALUES
('44444444-0000-0000-0000-000000000001', '33333333-0000-0000-0000-000000000001', '11111111-0000-0000-0000-000000000001', '22222222-0000-0000-0000-000000000001', 'LASNAP16-01', 'Main Substation Testing', 'SWGR', 'In Progress', '2016-02-01', '2016-02-28', 120.00, 52500.00, 1, true),
('44444444-0000-0000-0000-000000000002', '33333333-0000-0000-0000-000000000001', '11111111-0000-0000-0000-000000000001', '22222222-0000-0000-0000-000000000001', 'LASNAP16-02', 'Transformer Testing', 'XFMR', 'Not Started', '2016-03-01', '2016-03-31', 80.00, 45000.00, 2, true),
('44444444-0000-0000-0000-000000000003', '33333333-0000-0000-0000-000000000001', '11111111-0000-0000-0000-000000000001', '22222222-0000-0000-0000-000000000001', 'LASNAP16-03', 'MCC Testing Building A', 'MCC', 'Not Started', '2016-04-01', '2016-04-30', 100.00, 47500.00, 3, true),
('44444444-0000-0000-0000-000000000004', '33333333-0000-0000-0000-000000000001', '11111111-0000-0000-0000-000000000001', '22222222-0000-0000-0000-000000000001', 'LASNAP16-04', 'MCC Testing Building B', 'MCC', 'Not Started', '2016-05-01', '2016-05-31', 90.00, 42500.00, 4, true);

-- =============================================================================
-- TASKS (12 tasks across scopes)
-- =============================================================================

-- Scope 1: Main Substation Tasks
INSERT INTO tasks (id, scope_id, task_number, task_name, task_type, status, estimated_hours, sort_order, is_active) VALUES
('55555555-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000001', 'T-001', 'Main Switchgear Visual & Mechanical', 'Inspection', 'In Progress', 24.00, 1, true),
('55555555-0000-0000-0000-000000000002', '44444444-0000-0000-0000-000000000001', 'T-002', 'Main Switchgear Electrical Testing', 'Testing', 'Not Started', 48.00, 2, true),
('55555555-0000-0000-0000-000000000003', '44444444-0000-0000-0000-000000000001', 'T-003', 'Protective Relay Testing', 'Testing', 'Not Started', 48.00, 3, true);

-- Scope 2: Transformer Tasks
INSERT INTO tasks (id, scope_id, task_number, task_name, task_type, status, estimated_hours, sort_order, is_active) VALUES
('55555555-0000-0000-0000-000000000004', '44444444-0000-0000-0000-000000000002', 'T-004', 'Main Transformer T1 Testing', 'Testing', 'Not Started', 24.00, 1, true),
('55555555-0000-0000-0000-000000000005', '44444444-0000-0000-0000-000000000002', 'T-005', 'Main Transformer T2 Testing', 'Testing', 'Not Started', 24.00, 2, true),
('55555555-0000-0000-0000-000000000006', '44444444-0000-0000-0000-000000000002', 'T-006', 'Dry-Type Transformer Testing', 'Testing', 'Not Started', 32.00, 3, true);

-- Scope 3: MCC Building A Tasks
INSERT INTO tasks (id, scope_id, task_number, task_name, task_type, status, estimated_hours, sort_order, is_active) VALUES
('55555555-0000-0000-0000-000000000007', '44444444-0000-0000-0000-000000000003', 'T-007', 'MCC-A1 Testing', 'Testing', 'Not Started', 32.00, 1, true),
('55555555-0000-0000-0000-000000000008', '44444444-0000-0000-0000-000000000003', 'T-008', 'MCC-A2 Testing', 'Testing', 'Not Started', 32.00, 2, true),
('55555555-0000-0000-0000-000000000009', '44444444-0000-0000-0000-000000000003', 'T-009', 'MCC-A3 Testing', 'Testing', 'Not Started', 36.00, 3, true);

-- Scope 4: MCC Building B Tasks
INSERT INTO tasks (id, scope_id, task_number, task_name, task_type, status, estimated_hours, sort_order, is_active) VALUES
('55555555-0000-0000-0000-000000000010', '44444444-0000-0000-0000-000000000004', 'T-010', 'MCC-B1 Testing', 'Testing', 'Not Started', 30.00, 1, true),
('55555555-0000-0000-0000-000000000011', '44444444-0000-0000-0000-000000000004', 'T-011', 'MCC-B2 Testing', 'Testing', 'Not Started', 30.00, 2, true),
('55555555-0000-0000-0000-000000000012', '44444444-0000-0000-0000-000000000004', 'T-012', 'MCC-B3 Testing', 'Testing', 'Not Started', 30.00, 3, true);

-- =============================================================================
-- APPARATUS (47 equipment items)
-- =============================================================================

-- Scope 1 Apparatus: Main Substation (15 items)
INSERT INTO apparatus (id, scope_id, task_id, apparatus_designation, apparatus_name, apparatus_type, manufacturer, model, status, quoted_hours, quoted_revenue, building, room, sort_order, is_active) VALUES
-- Main Switchgear Visual/Mechanical (Task 1)
('66666666-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000001', 'SWGR-001', '15kV Main Switchgear', 'Switchgear', 'Square D', 'QED2', 'In Progress', 4.00, 1750.00, 'Substation', 'Main', 1, true),
('66666666-0000-0000-0000-000000000002', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000001', 'SWGR-002', '15kV Tie Switchgear', 'Switchgear', 'Square D', 'QED2', 'Not Started', 4.00, 1750.00, 'Substation', 'Main', 2, true),
('66666666-0000-0000-0000-000000000003', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000001', 'SWGR-003', '15kV Feeder Switchgear', 'Switchgear', 'Square D', 'QED2', 'Not Started', 4.00, 1750.00, 'Substation', 'Main', 3, true),
-- Main Switchgear Electrical Testing (Task 2)
('66666666-0000-0000-0000-000000000004', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000002', 'CB-001', '15kV Main CB 52-1', 'Circuit Breaker', 'Square D', 'VR', 'Not Started', 6.00, 2625.00, 'Substation', 'Main', 4, true),
('66666666-0000-0000-0000-000000000005', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000002', 'CB-002', '15kV Tie CB 52-T', 'Circuit Breaker', 'Square D', 'VR', 'Not Started', 6.00, 2625.00, 'Substation', 'Main', 5, true),
('66666666-0000-0000-0000-000000000006', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000002', 'CB-003', '15kV Feeder CB 52-2', 'Circuit Breaker', 'Square D', 'VR', 'Not Started', 6.00, 2625.00, 'Substation', 'Main', 6, true),
('66666666-0000-0000-0000-000000000007', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000002', 'CB-004', '15kV Feeder CB 52-3', 'Circuit Breaker', 'Square D', 'VR', 'Not Started', 6.00, 2625.00, 'Substation', 'Main', 7, true),
('66666666-0000-0000-0000-000000000008', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000002', 'CB-005', '15kV Feeder CB 52-4', 'Circuit Breaker', 'Square D', 'VR', 'Not Started', 6.00, 2625.00, 'Substation', 'Main', 8, true),
('66666666-0000-0000-0000-000000000009', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000002', 'CB-006', '15kV Spare CB', 'Circuit Breaker', 'Square D', 'VR', 'Not Started', 6.00, 2625.00, 'Substation', 'Main', 9, true),
-- Protective Relay Testing (Task 3)
('66666666-0000-0000-0000-000000000010', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000003', 'RLY-001', 'Main Overcurrent Relay 51-1', 'Protective Relay', 'SEL', '751', 'Not Started', 8.00, 3500.00, 'Substation', 'Relay Room', 10, true),
('66666666-0000-0000-0000-000000000011', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000003', 'RLY-002', 'Tie Overcurrent Relay 51-T', 'Protective Relay', 'SEL', '751', 'Not Started', 8.00, 3500.00, 'Substation', 'Relay Room', 11, true),
('66666666-0000-0000-0000-000000000012', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000003', 'RLY-003', 'Feeder Overcurrent Relay 51-2', 'Protective Relay', 'SEL', '751', 'Not Started', 8.00, 3500.00, 'Substation', 'Relay Room', 12, true),
('66666666-0000-0000-0000-000000000013', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000003', 'RLY-004', 'Feeder Overcurrent Relay 51-3', 'Protective Relay', 'SEL', '751', 'Not Started', 8.00, 3500.00, 'Substation', 'Relay Room', 13, true),
('66666666-0000-0000-0000-000000000014', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000003', 'RLY-005', 'Feeder Overcurrent Relay 51-4', 'Protective Relay', 'SEL', '751', 'Not Started', 8.00, 3500.00, 'Substation', 'Relay Room', 14, true),
('66666666-0000-0000-0000-000000000015', '44444444-0000-0000-0000-000000000001', '55555555-0000-0000-0000-000000000003', 'RLY-006', 'Bus Differential Relay 87B', 'Protective Relay', 'SEL', '487E', 'Not Started', 8.00, 3500.00, 'Substation', 'Relay Room', 15, true);

-- Scope 2 Apparatus: Transformers (8 items)
INSERT INTO apparatus (id, scope_id, task_id, apparatus_designation, apparatus_name, apparatus_type, manufacturer, model, status, quoted_hours, quoted_revenue, building, room, sort_order, is_active) VALUES
-- Main Transformer T1 Testing (Task 4)
('66666666-0000-0000-0000-000000000016', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000004', 'XFMR-001', 'Main Transformer T1', 'Transformer', 'ABB', 'PTG-3', 'Not Started', 12.00, 5250.00, 'Substation', 'Yard', 1, true),
('66666666-0000-0000-0000-000000000017', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000004', 'XFMR-001-LTC', 'T1 Load Tap Changer', 'LTC', 'ABB', 'UZF', 'Not Started', 6.00, 2625.00, 'Substation', 'Yard', 2, true),
('66666666-0000-0000-0000-000000000018', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000004', 'XFMR-001-FAN', 'T1 Cooling Fans', 'Cooling System', 'ABB', 'Standard', 'Not Started', 2.00, 875.00, 'Substation', 'Yard', 3, true),
-- Main Transformer T2 Testing (Task 5)
('66666666-0000-0000-0000-000000000019', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000005', 'XFMR-002', 'Main Transformer T2', 'Transformer', 'ABB', 'PTG-3', 'Not Started', 12.00, 5250.00, 'Substation', 'Yard', 4, true),
('66666666-0000-0000-0000-000000000020', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000005', 'XFMR-002-LTC', 'T2 Load Tap Changer', 'LTC', 'ABB', 'UZF', 'Not Started', 6.00, 2625.00, 'Substation', 'Yard', 5, true),
('66666666-0000-0000-0000-000000000021', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000005', 'XFMR-002-FAN', 'T2 Cooling Fans', 'Cooling System', 'ABB', 'Standard', 'Not Started', 2.00, 875.00, 'Substation', 'Yard', 6, true),
-- Dry-Type Transformer Testing (Task 6)
('66666666-0000-0000-0000-000000000022', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000006', 'DRY-001', 'Building A Main Dry Transformer', 'Dry Transformer', 'Square D', 'EE', 'Not Started', 4.00, 1750.00, 'Building A', 'Electrical', 7, true),
('66666666-0000-0000-0000-000000000023', '44444444-0000-0000-0000-000000000002', '55555555-0000-0000-0000-000000000006', 'DRY-002', 'Building B Main Dry Transformer', 'Dry Transformer', 'Square D', 'EE', 'Not Started', 4.00, 1750.00, 'Building B', 'Electrical', 8, true);

-- Scope 3 Apparatus: MCC Building A (12 items)
INSERT INTO apparatus (id, scope_id, task_id, apparatus_designation, apparatus_name, apparatus_type, manufacturer, model, status, quoted_hours, quoted_revenue, building, room, sort_order, is_active) VALUES
-- MCC-A1 Testing (Task 7)
('66666666-0000-0000-0000-000000000024', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000007', 'MCC-A1', 'MCC-A1 Bus/Structure', 'MCC', 'Allen Bradley', 'CENTERLINE', 'Not Started', 4.00, 1750.00, 'Building A', 'MCC Room 1', 1, true),
('66666666-0000-0000-0000-000000000025', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000007', 'MCC-A1-01', 'MCC-A1 Bucket 01 - Chiller 1', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 1', 2, true),
('66666666-0000-0000-0000-000000000026', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000007', 'MCC-A1-02', 'MCC-A1 Bucket 02 - Chiller 2', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 1', 3, true),
('66666666-0000-0000-0000-000000000027', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000007', 'MCC-A1-03', 'MCC-A1 Bucket 03 - AHU-1', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 1', 4, true),
-- MCC-A2 Testing (Task 8)
('66666666-0000-0000-0000-000000000028', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000008', 'MCC-A2', 'MCC-A2 Bus/Structure', 'MCC', 'Allen Bradley', 'CENTERLINE', 'Not Started', 4.00, 1750.00, 'Building A', 'MCC Room 2', 5, true),
('66666666-0000-0000-0000-000000000029', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000008', 'MCC-A2-01', 'MCC-A2 Bucket 01 - Pump 1', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 2', 6, true),
('66666666-0000-0000-0000-000000000030', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000008', 'MCC-A2-02', 'MCC-A2 Bucket 02 - Pump 2', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 2', 7, true),
('66666666-0000-0000-0000-000000000031', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000008', 'MCC-A2-03', 'MCC-A2 Bucket 03 - Compressor', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 2', 8, true),
-- MCC-A3 Testing (Task 9)
('66666666-0000-0000-0000-000000000032', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000009', 'MCC-A3', 'MCC-A3 Bus/Structure', 'MCC', 'Allen Bradley', 'CENTERLINE', 'Not Started', 4.00, 1750.00, 'Building A', 'MCC Room 3', 9, true),
('66666666-0000-0000-0000-000000000033', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000009', 'MCC-A3-01', 'MCC-A3 Bucket 01 - Conveyor 1', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 3', 10, true),
('66666666-0000-0000-0000-000000000034', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000009', 'MCC-A3-02', 'MCC-A3 Bucket 02 - Conveyor 2', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 3', 11, true),
('66666666-0000-0000-0000-000000000035', '44444444-0000-0000-0000-000000000003', '55555555-0000-0000-0000-000000000009', 'MCC-A3-03', 'MCC-A3 Bucket 03 - Mixer', 'Motor Starter', 'Allen Bradley', '509', 'Not Started', 2.00, 875.00, 'Building A', 'MCC Room 3', 12, true);

-- Scope 4 Apparatus: MCC Building B (12 items)
INSERT INTO apparatus (id, scope_id, task_id, apparatus_designation, apparatus_name, apparatus_type, manufacturer, model, status, quoted_hours, quoted_revenue, building, room, sort_order, is_active) VALUES
-- MCC-B1 Testing (Task 10)
('66666666-0000-0000-0000-000000000036', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000010', 'MCC-B1', 'MCC-B1 Bus/Structure', 'MCC', 'Siemens', 'TiaSTAR', 'Not Started', 4.00, 1750.00, 'Building B', 'MCC Room 1', 1, true),
('66666666-0000-0000-0000-000000000037', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000010', 'MCC-B1-01', 'MCC-B1 Bucket 01 - Boiler Feed', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 1', 2, true),
('66666666-0000-0000-0000-000000000038', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000010', 'MCC-B1-02', 'MCC-B1 Bucket 02 - Condensate', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 1', 3, true),
('66666666-0000-0000-0000-000000000039', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000010', 'MCC-B1-03', 'MCC-B1 Bucket 03 - Blower', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 1', 4, true),
-- MCC-B2 Testing (Task 11)
('66666666-0000-0000-0000-000000000040', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000011', 'MCC-B2', 'MCC-B2 Bus/Structure', 'MCC', 'Siemens', 'TiaSTAR', 'Not Started', 4.00, 1750.00, 'Building B', 'MCC Room 2', 5, true),
('66666666-0000-0000-0000-000000000041', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000011', 'MCC-B2-01', 'MCC-B2 Bucket 01 - Package 1', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 2', 6, true),
('66666666-0000-0000-0000-000000000042', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000011', 'MCC-B2-02', 'MCC-B2 Bucket 02 - Package 2', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 2', 7, true),
('66666666-0000-0000-0000-000000000043', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000011', 'MCC-B2-03', 'MCC-B2 Bucket 03 - Package 3', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 2', 8, true),
-- MCC-B3 Testing (Task 12)
('66666666-0000-0000-0000-000000000044', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000012', 'MCC-B3', 'MCC-B3 Bus/Structure', 'MCC', 'Siemens', 'TiaSTAR', 'Not Started', 4.00, 1750.00, 'Building B', 'MCC Room 3', 9, true),
('66666666-0000-0000-0000-000000000045', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000012', 'MCC-B3-01', 'MCC-B3 Bucket 01 - Warehouse Fan', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 3', 10, true),
('66666666-0000-0000-0000-000000000046', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000012', 'MCC-B3-02', 'MCC-B3 Bucket 02 - Dock Door', 'Motor Starter', 'Siemens', '3TF', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 3', 11, true),
('66666666-0000-0000-0000-000000000047', '44444444-0000-0000-0000-000000000004', '55555555-0000-0000-0000-000000000012', 'MCC-B3-03', 'MCC-B3 Bucket 03 - Lighting Panel', 'Panel', 'Siemens', 'P1', 'Not Started', 2.00, 875.00, 'Building B', 'MCC Room 3', 12, true);

-- =============================================================================
-- RESOURCE ASSIGNMENTS (8 assignments)
-- =============================================================================

INSERT INTO resource_assignments (id, employee_id, project_id, scope_id, assignment_type, start_date, end_date, allocated_hours, is_primary, is_active) VALUES
-- Project-level assignments
('88888888-0000-0000-0000-000000000001', '77777777-0000-0000-0000-000000000004', '33333333-0000-0000-0000-000000000001', NULL, 'Primary', '2016-02-01', '2016-06-30', 40.00, true, true),
('88888888-0000-0000-0000-000000000002', '77777777-0000-0000-0000-000000000001', '33333333-0000-0000-0000-000000000001', NULL, 'Primary', '2016-02-01', '2016-06-30', 200.00, true, true),
-- Scope-level assignments
('88888888-0000-0000-0000-000000000003', '77777777-0000-0000-0000-000000000001', '33333333-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000001', 'Primary', '2016-02-01', '2016-02-28', 60.00, true, true),
('88888888-0000-0000-0000-000000000004', '77777777-0000-0000-0000-000000000002', '33333333-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000001', 'Secondary', '2016-02-01', '2016-02-28', 60.00, false, true),
('88888888-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000001', '33333333-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000002', 'Primary', '2016-03-01', '2016-03-31', 40.00, true, true),
('88888888-0000-0000-0000-000000000006', '77777777-0000-0000-0000-000000000003', '33333333-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000002', 'Secondary', '2016-03-01', '2016-03-31', 40.00, false, true),
('88888888-0000-0000-0000-000000000007', '77777777-0000-0000-0000-000000000002', '33333333-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000003', 'Primary', '2016-04-01', '2016-04-30', 100.00, true, true),
('88888888-0000-0000-0000-000000000008', '77777777-0000-0000-0000-000000000003', '33333333-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000004', 'Primary', '2016-05-01', '2016-05-31', 90.00, true, true);

-- =============================================================================
-- SCOPE LABOR DETAILS (labor breakdown per scope)
-- =============================================================================

INSERT INTO scope_labor_details (id, scope_id, labor_category, labor_description, quoted_hours, rate, is_active) VALUES
-- Scope 1: Main Substation
('AAAAAAAA-0000-0000-0000-000000000001', '44444444-0000-0000-0000-000000000001', 'Lead Tech', 'Lead Technician Hours', 60.00, 95.00, true),
('AAAAAAAA-0000-0000-0000-000000000002', '44444444-0000-0000-0000-000000000001', 'Field Tech', 'Field Technician Hours', 60.00, 75.00, true),
-- Scope 2: Transformer
('AAAAAAAA-0000-0000-0000-000000000003', '44444444-0000-0000-0000-000000000002', 'Lead Tech', 'Lead Technician Hours', 40.00, 95.00, true),
('AAAAAAAA-0000-0000-0000-000000000004', '44444444-0000-0000-0000-000000000002', 'Field Tech', 'Field Technician Hours', 40.00, 75.00, true),
-- Scope 3: MCC Building A
('AAAAAAAA-0000-0000-0000-000000000005', '44444444-0000-0000-0000-000000000003', 'Field Tech', 'Field Technician Hours', 100.00, 75.00, true),
-- Scope 4: MCC Building B
('AAAAAAAA-0000-0000-0000-000000000006', '44444444-0000-0000-0000-000000000004', 'Field Tech', 'Field Technician Hours', 90.00, 75.00, true);

-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================

-- Verify record counts
SELECT 'Test Data Verification' AS section;
SELECT 'clients' AS entity, COUNT(*) AS count FROM clients WHERE id LIKE '11111111%'
UNION ALL SELECT 'sites', COUNT(*) FROM sites WHERE id LIKE '22222222%'
UNION ALL SELECT 'projects', COUNT(*) FROM projects WHERE id LIKE '33333333%'
UNION ALL SELECT 'scopes', COUNT(*) FROM scopes WHERE id LIKE '44444444%'
UNION ALL SELECT 'tasks', COUNT(*) FROM tasks WHERE id LIKE '55555555%'
UNION ALL SELECT 'apparatus', COUNT(*) FROM apparatus WHERE id LIKE '66666666%'
UNION ALL SELECT 'employees', COUNT(*) FROM employees WHERE id LIKE '77777777%'
UNION ALL SELECT 'resource_assignments', COUNT(*) FROM resource_assignments WHERE id LIKE '88888888%'
UNION ALL SELECT 'scope_labor_details', COUNT(*) FROM scope_labor_details WHERE id LIKE 'AAAAAAAA%';

-- Verify FK integrity
SELECT 'FK Integrity Check' AS section;
SELECT 'orphan_scopes' AS check_name, COUNT(*) AS orphan_count 
FROM scopes WHERE project_id NOT IN (SELECT id FROM projects)
UNION ALL
SELECT 'orphan_tasks', COUNT(*) FROM tasks WHERE scope_id NOT IN (SELECT id FROM scopes)
UNION ALL
SELECT 'orphan_apparatus', COUNT(*) FROM apparatus WHERE scope_id NOT IN (SELECT id FROM scopes);

COMMIT;

-- =============================================================================
-- POST-INSERT: Trigger Verification
-- =============================================================================
-- After running, verify rollup triggers worked:
-- SELECT project_number, total_apparatus_count FROM projects WHERE project_number = 'LASNAP16';
-- Expected: total_apparatus_count = 47

-- SELECT scope_number, total_apparatus_count FROM scopes WHERE project_id = '33333333-0000-0000-0000-000000000001';
-- Expected: Scope 1 = 15, Scope 2 = 8, Scope 3 = 12, Scope 4 = 12
-- =============================================================================
-- RESA Power Platform - PSS Portal Test Data
-- =============================================================================
-- File: 12_pss_test_data.sql
-- Generated: 2025-12-05
-- Source: spec/TEST_DATA_PLAN.md
-- Run: AFTER 11_test_data.sql
-- =============================================================================

-- UUID Pattern: {prefix}-0000-0000-0000-{seq}
-- Prefix key:
--   BBBBBBBB = pss_engineers
--   CCCCCCCC = pss_document_templates
--   DDDDDDDD = pss_studies
--   EEEEEEEE = pss_documents
--   FFFFFFFF = pss_rfis

BEGIN;

-- =============================================================================
-- PSS ENGINEERS (3 external engineers)
-- =============================================================================

INSERT INTO pss_engineers (id, engineer_name, company, email, phone, specialization, pe_license, pe_state, is_active) VALUES
('BBBBBBBB-0000-0000-0000-000000000001', 'Dr. James Patterson', 'Patterson Power Engineering', 'jpatterson@ppegroup.com', '512-555-0201', 'Arc Flash Analysis', 'PE-48291', 'TX', true),
('BBBBBBBB-0000-0000-0000-000000000002', 'Maria Rodriguez, PE', 'Southwest Engineering Solutions', 'mrodriguez@swes.com', '480-555-0202', 'Coordination Studies', 'PE-33847', 'AZ', true),
('BBBBBBBB-0000-0000-0000-000000000003', 'Robert Chang, PE', 'Chang Consulting Engineers', 'rchang@cce-power.com', '314-555-0203', 'Short Circuit Analysis', 'PE-52910', 'MO', true);

-- =============================================================================
-- PSS DOCUMENT TEMPLATES (8 templates)
-- =============================================================================

INSERT INTO pss_document_templates (id, template_code, template_name, document_type, description, sort_order, is_active) VALUES
('CCCCCCCC-0000-0000-0000-000000000001', 'TPL-SR', 'Study Report Template', 'Study Report', 'Standard template for comprehensive study reports', 1, true),
('CCCCCCCC-0000-0000-0000-000000000002', 'TPL-OLD', 'One-Line Diagram Template', 'One-Line Diagram', 'AutoCAD template for electrical one-line diagrams', 2, true),
('CCCCCCCC-0000-0000-0000-000000000003', 'TPL-DC', 'Data Collection Form', 'Data Collection', 'Field data collection form for equipment parameters', 3, true),
('CCCCCCCC-0000-0000-0000-000000000004', 'TPL-CALC', 'Calculation Sheet', 'Calculations', 'Excel template for engineering calculations', 4, true),
('CCCCCCCC-0000-0000-0000-000000000005', 'TPL-ES', 'Equipment Schedule Template', 'Equipment Schedule', 'Equipment database schedule template', 5, true),
('CCCCCCCC-0000-0000-0000-000000000006', 'TPL-AFL', 'Arc Flash Label Template', 'Arc Flash Labels', 'NFPA 70E compliant arc flash label template', 6, true),
('CCCCCCCC-0000-0000-0000-000000000007', 'TPL-CC', 'Coordination Curves Template', 'Coordination Curves', 'SKM/ETAP coordination curve export template', 7, true),
('CCCCCCCC-0000-0000-0000-000000000008', 'TPL-CVR', 'Cover Letter Template', 'Cover Letter', 'Standard project transmittal cover letter', 8, true);

-- =============================================================================
-- PSS STUDIES (5 studies across different statuses)
-- =============================================================================

INSERT INTO pss_studies (id, project_id, study_number, study_name, study_type, status, priority, engineer_id, requested_date, due_date, completed_date, description, is_active) VALUES
-- Study 1: Completed Arc Flash
('DDDDDDDD-0000-0000-0000-000000000001', '33333333-0000-0000-0000-000000000001', 'PSS-2016-001', 'LASNAP Foods Arc Flash Analysis', 'Arc Flash', 'Completed', 'High', 'BBBBBBBB-0000-0000-0000-000000000001', '2016-01-15', '2016-02-15', '2016-02-10', 'Comprehensive arc flash hazard analysis for main substation and building MCCs per IEEE 1584-2018 and NFPA 70E-2024.', true),

-- Study 2: In Progress Coordination
('DDDDDDDD-0000-0000-0000-000000000002', '33333333-0000-0000-0000-000000000001', 'PSS-2016-002', 'LASNAP Foods Protective Device Coordination', 'Coordination', 'In Progress', 'High', 'BBBBBBBB-0000-0000-0000-000000000002', '2016-02-01', '2016-03-15', NULL, 'Time-current coordination study for main-tie-main switchgear and downstream protection. Includes relay settings recommendations.', true),

-- Study 3: Pending Short Circuit
('DDDDDDDD-0000-0000-0000-000000000003', '33333333-0000-0000-0000-000000000001', 'PSS-2016-003', 'LASNAP Foods Short Circuit Study', 'Short Circuit', 'Pending', 'Medium', 'BBBBBBBB-0000-0000-0000-000000000003', '2016-02-15', '2016-04-01', NULL, 'Short circuit analysis to verify equipment ratings and determine available fault currents at key points in the distribution system.', true),

-- Study 4: Data Collection Load Flow
('DDDDDDDD-0000-0000-0000-000000000004', '33333333-0000-0000-0000-000000000001', 'PSS-2016-004', 'LASNAP Foods Load Flow Analysis', 'Load Flow', 'Data Collection', 'Low', NULL, '2016-03-01', '2016-05-01', NULL, 'Load flow study to identify voltage drop issues and optimize transformer tap settings. Pending field measurements.', true),

-- Study 5: On Hold Comprehensive
('DDDDDDDD-0000-0000-0000-000000000005', NULL, 'PSS-2016-005', 'Generic Facility Comprehensive Study', 'Comprehensive', 'On Hold', 'Low', NULL, '2016-01-01', '2016-06-01', NULL, 'Comprehensive study template for future projects. Currently on hold pending project assignment.', true);

-- =============================================================================
-- PSS DOCUMENTS (15 documents, ~3 per study)
-- =============================================================================

INSERT INTO pss_documents (id, study_id, template_id, document_name, document_type, version, status, file_path, file_size, uploaded_by, uploaded_at, is_active) VALUES
-- Study 1: Arc Flash (Completed) - 4 documents
('EEEEEEEE-0000-0000-0000-000000000001', 'DDDDDDDD-0000-0000-0000-000000000001', 'CCCCCCCC-0000-0000-0000-000000000001', 'LASNAP16 Arc Flash Study Report v2.1', 'Study Report', '2.1', 'Approved', '/studies/PSS-2016-001/LASNAP16_ArcFlash_Report_v2.1.pdf', 4521890, '77777777-0000-0000-0000-000000000005', '2016-02-08 14:30:00', true),
('EEEEEEEE-0000-0000-0000-000000000002', 'DDDDDDDD-0000-0000-0000-000000000001', 'CCCCCCCC-0000-0000-0000-000000000002', 'LASNAP16 One-Line Diagram', 'One-Line Diagram', '1.0', 'Approved', '/studies/PSS-2016-001/LASNAP16_OneLine.dwg', 2145678, '77777777-0000-0000-0000-000000000005', '2016-01-20 09:15:00', true),
('EEEEEEEE-0000-0000-0000-000000000003', 'DDDDDDDD-0000-0000-0000-000000000001', 'CCCCCCCC-0000-0000-0000-000000000006', 'LASNAP16 Arc Flash Labels Package', 'Arc Flash Labels', '1.0', 'Approved', '/studies/PSS-2016-001/LASNAP16_ArcFlash_Labels.pdf', 892456, '77777777-0000-0000-0000-000000000005', '2016-02-09 16:45:00', true),
('EEEEEEEE-0000-0000-0000-000000000004', 'DDDDDDDD-0000-0000-0000-000000000001', 'CCCCCCCC-0000-0000-0000-000000000005', 'LASNAP16 Equipment Schedule', 'Equipment Schedule', '1.2', 'Approved', '/studies/PSS-2016-001/LASNAP16_Equipment_Schedule.xlsx', 456789, '77777777-0000-0000-0000-000000000005', '2016-02-05 11:20:00', true),

-- Study 2: Coordination (In Progress) - 4 documents
('EEEEEEEE-0000-0000-0000-000000000005', 'DDDDDDDD-0000-0000-0000-000000000002', 'CCCCCCCC-0000-0000-0000-000000000003', 'LASNAP16 Data Collection - Relay Settings', 'Data Collection', '1.0', 'Approved', '/studies/PSS-2016-002/LASNAP16_Data_RelaySettings.xlsx', 234567, '77777777-0000-0000-0000-000000000002', '2016-02-05 10:00:00', true),
('EEEEEEEE-0000-0000-0000-000000000006', 'DDDDDDDD-0000-0000-0000-000000000002', 'CCCCCCCC-0000-0000-0000-000000000007', 'LASNAP16 Coordination Curves - Draft', 'Coordination Curves', '0.9', 'In Review', '/studies/PSS-2016-002/LASNAP16_Coordination_Draft.pdf', 1567890, '77777777-0000-0000-0000-000000000005', '2016-02-28 15:30:00', true),
('EEEEEEEE-0000-0000-0000-000000000007', 'DDDDDDDD-0000-0000-0000-000000000002', 'CCCCCCCC-0000-0000-0000-000000000001', 'LASNAP16 Coordination Report - Draft', 'Study Report', '0.8', 'Draft', '/studies/PSS-2016-002/LASNAP16_Coordination_Report_Draft.docx', 2345678, '77777777-0000-0000-0000-000000000005', '2016-03-01 09:00:00', true),
('EEEEEEEE-0000-0000-0000-000000000008', 'DDDDDDDD-0000-0000-0000-000000000002', 'CCCCCCCC-0000-0000-0000-000000000004', 'LASNAP16 TCC Calculations', 'Calculations', '1.0', 'In Review', '/studies/PSS-2016-002/LASNAP16_TCC_Calcs.xlsx', 567890, '77777777-0000-0000-0000-000000000005', '2016-02-25 14:00:00', true),

-- Study 3: Short Circuit (Pending) - 3 documents
('EEEEEEEE-0000-0000-0000-000000000009', 'DDDDDDDD-0000-0000-0000-000000000003', 'CCCCCCCC-0000-0000-0000-000000000002', 'LASNAP16 One-Line (Copy for SC Study)', 'One-Line Diagram', '1.0', 'Approved', '/studies/PSS-2016-003/LASNAP16_OneLine_SC.dwg', 2145678, '77777777-0000-0000-0000-000000000005', '2016-02-16 10:00:00', true),
('EEEEEEEE-0000-0000-0000-000000000010', 'DDDDDDDD-0000-0000-0000-000000000003', 'CCCCCCCC-0000-0000-0000-000000000003', 'LASNAP16 Data Collection - Utility Info', 'Data Collection', '1.0', 'Draft', '/studies/PSS-2016-003/LASNAP16_Data_Utility.xlsx', 123456, '77777777-0000-0000-0000-000000000002', '2016-02-18 11:30:00', true),
('EEEEEEEE-0000-0000-0000-000000000011', 'DDDDDDDD-0000-0000-0000-000000000003', 'CCCCCCCC-0000-0000-0000-000000000005', 'LASNAP16 Equipment Schedule (Copy)', 'Equipment Schedule', '1.2', 'Approved', '/studies/PSS-2016-003/LASNAP16_Equipment_Schedule_SC.xlsx', 456789, '77777777-0000-0000-0000-000000000005', '2016-02-16 10:05:00', true),

-- Study 4: Load Flow (Data Collection) - 3 documents
('EEEEEEEE-0000-0000-0000-000000000012', 'DDDDDDDD-0000-0000-0000-000000000004', 'CCCCCCCC-0000-0000-0000-000000000003', 'LASNAP16 Data Collection - Load Data', 'Data Collection', '0.5', 'Draft', '/studies/PSS-2016-004/LASNAP16_Data_Loads.xlsx', 234567, '77777777-0000-0000-0000-000000000002', '2016-03-05 09:00:00', true),
('EEEEEEEE-0000-0000-0000-000000000013', 'DDDDDDDD-0000-0000-0000-000000000004', 'CCCCCCCC-0000-0000-0000-000000000002', 'LASNAP16 One-Line (Load Flow)', 'One-Line Diagram', '1.0', 'Approved', '/studies/PSS-2016-004/LASNAP16_OneLine_LF.dwg', 2145678, '77777777-0000-0000-0000-000000000005', '2016-03-02 14:00:00', true),

-- Study 5: Comprehensive (On Hold) - 1 document
('EEEEEEEE-0000-0000-0000-000000000014', 'DDDDDDDD-0000-0000-0000-000000000005', 'CCCCCCCC-0000-0000-0000-000000000001', 'Comprehensive Study Template', 'Study Report', '1.0', 'Draft', '/templates/Comprehensive_Study_Template.docx', 345678, '77777777-0000-0000-0000-000000000005', '2016-01-02 08:00:00', true);

-- =============================================================================
-- PSS RFIs (10 RFIs across studies)
-- =============================================================================

INSERT INTO pss_rfis (id, study_id, rfi_number, subject, question, response, status, priority, requested_by, assigned_to, requested_date, due_date, responded_date, is_active) VALUES
-- Study 1: Arc Flash RFIs (Closed)
('FFFFFFFF-0000-0000-0000-000000000001', 'DDDDDDDD-0000-0000-0000-000000000001', 'RFI-001', 'Utility Available Fault Current', 'Please provide the available fault current from the utility at the main service entrance (Point of Common Coupling).', 'Per utility letter dated 2016-01-25: Available 3-phase fault current is 12,500 amps at 13.8kV. X/R ratio = 15.', 'Closed', 'High', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000004', '2016-01-18', '2016-01-25', '2016-01-25', true),
('FFFFFFFF-0000-0000-0000-000000000002', 'DDDDDDDD-0000-0000-0000-000000000001', 'RFI-002', 'Transformer T1 Impedance', 'What is the nameplate impedance of Main Transformer T1? Field data shows tag is unreadable.', 'Confirmed with ABB: T1 impedance is 5.75% on 2500 kVA base. See attached factory test report.', 'Closed', 'High', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000002', '2016-01-20', '2016-01-27', '2016-01-24', true),

-- Study 2: Coordination RFIs (Mix of statuses)
('FFFFFFFF-0000-0000-0000-000000000003', 'DDDDDDDD-0000-0000-0000-000000000002', 'RFI-003', 'Existing Relay Settings', 'Please provide current relay settings for SEL-751 relays at main switchgear positions 52-1, 52-T, and 52-2.', 'Settings provided via email on 2016-02-10. See attached Excel file with complete settings summary.', 'Closed', 'High', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000002', '2016-02-05', '2016-02-12', '2016-02-10', true),
('FFFFFFFF-0000-0000-0000-000000000004', 'DDDDDDDD-0000-0000-0000-000000000002', 'RFI-004', 'Motor Starting Current Data', 'Need locked rotor current and starting time for Chiller 1 and Chiller 2 motors for coordination with MCC feeder breakers.', 'Working with facilities to obtain motor data sheets. Expected by 2016-03-10.', 'In Progress', 'Medium', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000002', '2016-02-28', '2016-03-10', NULL, true),
('FFFFFFFF-0000-0000-0000-000000000005', 'DDDDDDDD-0000-0000-0000-000000000002', 'RFI-005', 'Future Expansion Plans', 'Are there any planned additions to the electrical system in the next 5 years that should be considered in the coordination study?', NULL, 'Open', 'Low', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000004', '2016-03-01', '2016-03-15', NULL, true),

-- Study 3: Short Circuit RFIs (Pending)
('FFFFFFFF-0000-0000-0000-000000000006', 'DDDDDDDD-0000-0000-0000-000000000003', 'RFI-006', 'Cable Lengths Main Feeder', 'Please provide cable lengths and sizes for feeders from main switchgear to Building A and Building B MCCs.', NULL, 'Open', 'High', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000002', '2016-02-20', '2016-03-01', NULL, true),
('FFFFFFFF-0000-0000-0000-000000000007', 'DDDDDDDD-0000-0000-0000-000000000003', 'RFI-007', 'Transformer T2 Test Report', 'Please provide factory test report for Transformer T2 showing impedance values.', NULL, 'Pending Info', 'Medium', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000004', '2016-02-22', '2016-03-05', NULL, true),

-- Study 4: Load Flow RFIs (Data Collection)
('FFFFFFFF-0000-0000-0000-000000000008', 'DDDDDDDD-0000-0000-0000-000000000004', 'RFI-008', 'Peak Demand Data', 'Please provide 12 months of peak demand data from utility bills for load flow baseline.', NULL, 'Open', 'Medium', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000004', '2016-03-05', '2016-03-20', NULL, true),
('FFFFFFFF-0000-0000-0000-000000000009', 'DDDDDDDD-0000-0000-0000-000000000004', 'RFI-009', 'Motor Load List', 'Please provide complete motor load list including HP ratings and duty cycles for all motors > 10 HP.', NULL, 'Open', 'Medium', '77777777-0000-0000-0000-000000000005', '77777777-0000-0000-0000-000000000002', '2016-03-05', '2016-03-20', NULL, true),

-- Study 5: Generic
('FFFFFFFF-0000-0000-0000-000000000010', 'DDDDDDDD-0000-0000-0000-000000000005', 'RFI-010', 'Template Review Request', 'Please review comprehensive study template and provide feedback on section organization.', 'Template approved with minor formatting suggestions. See marked-up PDF.', 'Answered', 'Low', '77777777-0000-0000-0000-000000000004', '77777777-0000-0000-0000-000000000005', '2016-01-05', '2016-01-15', '2016-01-12', true);

-- =============================================================================
-- PSS ACTIVITY LOG (25 audit entries)
-- =============================================================================

INSERT INTO pss_activity_log (id, study_id, activity_type, activity_description, entity_type, entity_id, old_value, new_value, performed_by, performed_at) VALUES
-- Study 1: Arc Flash Activity
('00000001-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Created', 'Study created', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000001', NULL, 'Pending', '77777777-0000-0000-0000-000000000004', '2016-01-15 09:00:00'),
('00000002-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Status Change', 'Study status changed', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000001', 'Pending', 'In Progress', '77777777-0000-0000-0000-000000000005', '2016-01-18 10:30:00'),
('00000003-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Document Upload', 'One-line diagram uploaded', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000002', NULL, 'LASNAP16_OneLine.dwg', '77777777-0000-0000-0000-000000000005', '2016-01-20 09:15:00'),
('00000004-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Assignment', 'Engineer assigned to study', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000001', NULL, 'Dr. James Patterson', '77777777-0000-0000-0000-000000000004', '2016-01-16 11:00:00'),
('00000005-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Status Change', 'Study status changed', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000001', 'In Progress', 'Review', '77777777-0000-0000-0000-000000000005', '2016-02-05 16:00:00'),
('00000006-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Document Upload', 'Final report uploaded', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000001', NULL, 'LASNAP16_ArcFlash_Report_v2.1.pdf', '77777777-0000-0000-0000-000000000005', '2016-02-08 14:30:00'),
('00000007-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Approval', 'Study report approved', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000001', 'In Review', 'Approved', '77777777-0000-0000-0000-000000000004', '2016-02-09 10:00:00'),
('00000008-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000001', 'Status Change', 'Study completed', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000001', 'Review', 'Completed', '77777777-0000-0000-0000-000000000004', '2016-02-10 09:00:00'),

-- Study 2: Coordination Activity
('00000009-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Created', 'Study created', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000002', NULL, 'Pending', '77777777-0000-0000-0000-000000000004', '2016-02-01 08:00:00'),
('00000010-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Assignment', 'Engineer assigned', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000002', NULL, 'Maria Rodriguez, PE', '77777777-0000-0000-0000-000000000004', '2016-02-02 09:00:00'),
('00000011-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Status Change', 'Data collection started', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000002', 'Pending', 'Data Collection', '77777777-0000-0000-0000-000000000005', '2016-02-03 10:00:00'),
('00000012-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Document Upload', 'Relay settings data uploaded', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000005', NULL, 'LASNAP16_Data_RelaySettings.xlsx', '77777777-0000-0000-0000-000000000002', '2016-02-05 10:00:00'),
('00000013-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Status Change', 'Engineering work started', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000002', 'Data Collection', 'In Progress', '77777777-0000-0000-0000-000000000005', '2016-02-15 08:00:00'),
('00000014-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Document Upload', 'Draft coordination curves', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000006', NULL, 'LASNAP16_Coordination_Draft.pdf', '77777777-0000-0000-0000-000000000005', '2016-02-28 15:30:00'),
('00000015-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000002', 'Comment', 'Review comments added to draft report', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000007', NULL, '3 comments added', '77777777-0000-0000-0000-000000000004', '2016-03-02 11:00:00'),

-- Study 3: Short Circuit Activity
('00000016-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000003', 'Created', 'Study created', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000003', NULL, 'Pending', '77777777-0000-0000-0000-000000000004', '2016-02-15 14:00:00'),
('00000017-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000003', 'Assignment', 'Engineer assigned', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000003', NULL, 'Robert Chang, PE', '77777777-0000-0000-0000-000000000004', '2016-02-16 09:00:00'),
('00000018-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000003', 'Document Upload', 'One-line diagram copied', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000009', NULL, 'LASNAP16_OneLine_SC.dwg', '77777777-0000-0000-0000-000000000005', '2016-02-16 10:00:00'),

-- Study 4: Load Flow Activity
('00000019-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000004', 'Created', 'Study created', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000004', NULL, 'Pending', '77777777-0000-0000-0000-000000000004', '2016-03-01 10:00:00'),
('00000020-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000004', 'Status Change', 'Data collection phase', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000004', 'Pending', 'Data Collection', '77777777-0000-0000-0000-000000000005', '2016-03-02 08:00:00'),
('00000021-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000004', 'Document Upload', 'Load data form uploaded', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000012', NULL, 'LASNAP16_Data_Loads.xlsx', '77777777-0000-0000-0000-000000000002', '2016-03-05 09:00:00'),

-- Study 5: Generic Activity
('00000022-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000005', 'Created', 'Template study created', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000005', NULL, 'Pending', '77777777-0000-0000-0000-000000000005', '2016-01-01 08:00:00'),
('00000023-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000005', 'Document Upload', 'Template uploaded', 'pss_documents', 'EEEEEEEE-0000-0000-0000-000000000014', NULL, 'Comprehensive_Study_Template.docx', '77777777-0000-0000-0000-000000000005', '2016-01-02 08:00:00'),
('00000024-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000005', 'Status Change', 'Study placed on hold', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000005', 'Pending', 'On Hold', '77777777-0000-0000-0000-000000000004', '2016-01-10 15:00:00'),
('00000025-0000-0000-0000-AAAAAAAAAAAA', 'DDDDDDDD-0000-0000-0000-000000000005', 'Comment', 'On hold pending project assignment', 'pss_studies', 'DDDDDDDD-0000-0000-0000-000000000005', NULL, 'Awaiting Q2 project assignments', '77777777-0000-0000-0000-000000000004', '2016-01-10 15:05:00');

-- =============================================================================
-- VALIDATION QUERIES
-- =============================================================================

SELECT 'PSS Test Data Verification' AS section;
SELECT 'pss_engineers' AS entity, COUNT(*) AS count FROM pss_engineers WHERE id LIKE 'BBBBBBBB%'
UNION ALL SELECT 'pss_document_templates', COUNT(*) FROM pss_document_templates WHERE id LIKE 'CCCCCCCC%'
UNION ALL SELECT 'pss_studies', COUNT(*) FROM pss_studies WHERE id LIKE 'DDDDDDDD%'
UNION ALL SELECT 'pss_documents', COUNT(*) FROM pss_documents WHERE id LIKE 'EEEEEEEE%'
UNION ALL SELECT 'pss_rfis', COUNT(*) FROM pss_rfis WHERE id LIKE 'FFFFFFFF%'
UNION ALL SELECT 'pss_activity_log', COUNT(*) FROM pss_activity_log;

-- Verify FK integrity
SELECT 'PSS FK Integrity Check' AS section;
SELECT 'orphan_studies' AS check_name, COUNT(*) AS orphan_count 
FROM pss_studies WHERE project_id IS NOT NULL AND project_id NOT IN (SELECT id FROM projects)
UNION ALL
SELECT 'orphan_documents', COUNT(*) FROM pss_documents WHERE study_id NOT IN (SELECT id FROM pss_studies)
UNION ALL
SELECT 'orphan_rfis', COUNT(*) FROM pss_rfis WHERE study_id NOT IN (SELECT id FROM pss_studies);

-- Study summary by status
SELECT 'PSS Studies by Status' AS section;
SELECT status, COUNT(*) as count FROM pss_studies GROUP BY status ORDER BY count DESC;

-- RFIs by status
SELECT 'RFIs by Status' AS section;
SELECT status, COUNT(*) as count FROM pss_rfis GROUP BY status ORDER BY count DESC;

COMMIT;

-- =============================================================================
-- VERIFICATION: View Test
-- =============================================================================
-- After running, verify PSS views work:
-- SELECT * FROM v_pss_studies_full;
-- SELECT * FROM v_pss_dashboard;
