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
