-- =============================================================================
-- RESA Power Platform - Supabase/PostgreSQL Schema
-- =============================================================================
-- Generated: 2025-01-15
-- Purpose: Complete database schema for RESA Power operations
-- Compatible: PostgreSQL 15+, Supabase
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- CATEGORY 1: CORE LOCATION/ORGANIZATION HIERARCHY
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

-- 1.3 Sites (client facility locations)
CREATE TABLE IF NOT EXISTS sites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
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

-- =============================================================================
-- CATEGORY 2: PROJECT MANAGEMENT
-- =============================================================================

-- 2.1 Projects (main work tracking)
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_number VARCHAR(50) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    client_id UUID REFERENCES clients(id),
    site_id UUID REFERENCES sites(id),
    location_id UUID REFERENCES locations(id),
    
    -- Status and Type
    status VARCHAR(50) DEFAULT 'Draft',  -- Draft, Quoted, Won, Active, Complete, Cancelled
    project_type VARCHAR(100),
    business_unit VARCHAR(100),
    
    -- Dates
    quote_date DATE,
    quote_revision VARCHAR(20),
    start_date DATE,
    end_date DATE,
    
    -- Financial
    contract_value DECIMAL(15, 2),
    po_number VARCHAR(100),
    
    -- People
    project_lead VARCHAR(100),
    estimator VARCHAR(100),
    
    -- Details
    description TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.2 Scopes (project phases/work packages)
CREATE TABLE IF NOT EXISTS scopes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id),
    site_id UUID REFERENCES sites(id),
    
    scope_number VARCHAR(50),
    scope_name VARCHAR(200) NOT NULL,
    scope_type VARCHAR(100),  -- ATS, SWGR, XFMR, PDC, etc.
    
    -- Status
    status VARCHAR(50) DEFAULT 'Not Started',
    percent_complete DECIMAL(5, 2) DEFAULT 0,
    
    -- Dates
    planned_start DATE,
    planned_end DATE,
    actual_start DATE,
    actual_end DATE,
    
    -- Financial
    quoted_hours DECIMAL(10, 2),
    actual_hours DECIMAL(10, 2) DEFAULT 0,
    quoted_revenue DECIMAL(15, 2),
    actual_revenue DECIMAL(15, 2) DEFAULT 0,
    labor_cost DECIMAL(15, 2) DEFAULT 0,
    
    -- Details
    sort_order INTEGER DEFAULT 0,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.3 Tasks (work items within scopes)
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID NOT NULL REFERENCES scopes(id) ON DELETE CASCADE,
    
    task_number VARCHAR(50),
    task_name VARCHAR(200) NOT NULL,
    task_type VARCHAR(100),
    
    -- Status
    status VARCHAR(50) DEFAULT 'Not Started',
    percent_complete DECIMAL(5, 2) DEFAULT 0,
    
    -- Dates
    planned_start DATE,
    planned_end DATE,
    actual_start DATE,
    actual_end DATE,
    
    -- Hours
    estimated_hours DECIMAL(10, 2),
    actual_hours DECIMAL(10, 2) DEFAULT 0,
    
    -- Hierarchy
    parent_task_id UUID REFERENCES tasks(id),
    sort_order INTEGER DEFAULT 0,
    
    -- Details
    description TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.4 Apparatus (equipment being tested)
CREATE TABLE IF NOT EXISTS apparatus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID NOT NULL REFERENCES scopes(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id),
    
    -- Identification
    apparatus_designation VARCHAR(100) NOT NULL,  -- e.g., "ATS-01", "SWGR-A"
    apparatus_name VARCHAR(200),
    apparatus_type VARCHAR(100),  -- From Apparatus Type Master
    equipment_type VARCHAR(100),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    
    -- Status
    status VARCHAR(50) DEFAULT 'Not Started',
    assessment VARCHAR(50),  -- Pass, Fail, Needs Work, etc.
    percent_complete DECIMAL(5, 2) DEFAULT 0,
    
    -- Dates
    anticipated_start DATE,
    actual_start DATE,
    actual_end DATE,
    
    -- Hours
    quoted_hours DECIMAL(10, 2),
    actual_hours DECIMAL(10, 2) DEFAULT 0,
    
    -- Revenue
    quoted_revenue DECIMAL(12, 2),
    actual_revenue DECIMAL(12, 2) DEFAULT 0,
    
    -- Location within site
    building VARCHAR(100),
    floor VARCHAR(50),
    room VARCHAR(100),
    
    -- Details
    sort_order INTEGER DEFAULT 0,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- CATEGORY 3: FINANCIAL TRACKING
-- =============================================================================

-- 3.1 Apparatus Revenue (detailed revenue recognition)
CREATE TABLE IF NOT EXISTS apparatus_revenue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    apparatus_id UUID NOT NULL REFERENCES apparatus(id) ON DELETE CASCADE,
    scope_id UUID REFERENCES scopes(id),
    
    revenue_type VARCHAR(100),  -- Testing, Travel, Materials, etc.
    quoted_amount DECIMAL(12, 2),
    recognized_amount DECIMAL(12, 2) DEFAULT 0,
    recognition_date DATE,
    recognition_percent DECIMAL(5, 2) DEFAULT 0,
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3.2 Scope Financial Summary (aggregated scope financials)
CREATE TABLE IF NOT EXISTS scope_financial_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID UNIQUE NOT NULL REFERENCES scopes(id) ON DELETE CASCADE,
    
    -- Revenue
    total_quoted_revenue DECIMAL(15, 2) DEFAULT 0,
    total_recognized_revenue DECIMAL(15, 2) DEFAULT 0,
    revenue_recognition_percent DECIMAL(5, 2) DEFAULT 0,
    
    -- Hours
    total_quoted_hours DECIMAL(10, 2) DEFAULT 0,
    total_actual_hours DECIMAL(10, 2) DEFAULT 0,
    hours_variance DECIMAL(10, 2) DEFAULT 0,
    
    -- Costs
    total_labor_cost DECIMAL(15, 2) DEFAULT 0,
    total_expense_cost DECIMAL(15, 2) DEFAULT 0,
    
    -- Margins
    gross_margin DECIMAL(15, 2) DEFAULT 0,
    gross_margin_percent DECIMAL(5, 2) DEFAULT 0,
    
    last_calculated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3.3 Project Financial Summary (aggregated project financials)
CREATE TABLE IF NOT EXISTS project_financial_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID UNIQUE NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Revenue
    total_quoted_revenue DECIMAL(15, 2) DEFAULT 0,
    total_recognized_revenue DECIMAL(15, 2) DEFAULT 0,
    revenue_recognition_percent DECIMAL(5, 2) DEFAULT 0,
    
    -- Hours
    total_quoted_hours DECIMAL(10, 2) DEFAULT 0,
    total_actual_hours DECIMAL(10, 2) DEFAULT 0,
    
    -- Costs
    total_labor_cost DECIMAL(15, 2) DEFAULT 0,
    total_expense_cost DECIMAL(15, 2) DEFAULT 0,
    total_cost DECIMAL(15, 2) DEFAULT 0,
    
    -- Margins
    gross_margin DECIMAL(15, 2) DEFAULT 0,
    gross_margin_percent DECIMAL(5, 2) DEFAULT 0,
    
    -- Scope counts
    total_scopes INTEGER DEFAULT 0,
    completed_scopes INTEGER DEFAULT 0,
    
    last_calculated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3.4 Scope Labor Details (labor line items)
CREATE TABLE IF NOT EXISTS scope_labor_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID NOT NULL REFERENCES scopes(id) ON DELETE CASCADE,
    
    labor_category VARCHAR(100),  -- Field Tech, Engineer, PM, etc.
    labor_description VARCHAR(200),
    quoted_hours DECIMAL(10, 2),
    actual_hours DECIMAL(10, 2) DEFAULT 0,
    rate DECIMAL(10, 2),
    cost DECIMAL(12, 2) DEFAULT 0,
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- CATEGORY 4: REFERENCE/MASTER DATA
-- =============================================================================

-- 4.1 Estimators (for quotes and projects)
CREATE TABLE IF NOT EXISTS estimators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    estimator_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    location_id UUID REFERENCES locations(id),
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.2 Apparatus Type Master (equipment categories)
CREATE TABLE IF NOT EXISTS apparatus_type_master (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type_code VARCHAR(50) NOT NULL UNIQUE,
    type_name VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    default_hours DECIMAL(10, 2),
    default_rate DECIMAL(10, 2),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.3 NETA Test Templates (standard test procedures)
CREATE TABLE IF NOT EXISTS neta_test_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_code VARCHAR(50) NOT NULL,
    template_name VARCHAR(200) NOT NULL,
    apparatus_type VARCHAR(100),
    test_category VARCHAR(100),
    description TEXT,
    estimated_hours DECIMAL(10, 2),
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- CATEGORY 5: COMPANY RESOURCES (for future expansion)
-- =============================================================================

-- 5.1 Employees
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_number VARCHAR(50) UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    location_id UUID REFERENCES locations(id),
    
    -- Role
    job_title VARCHAR(100),
    department VARCHAR(100),
    role_type VARCHAR(50),  -- Field Tech, Engineer, PM, Admin
    
    -- Rates
    hourly_rate DECIMAL(10, 2),
    overtime_rate DECIMAL(10, 2),
    burden_rate DECIMAL(5, 2),
    
    -- Certifications
    neta_certified BOOLEAN DEFAULT false,
    neta_level VARCHAR(20),
    certification_expiry DATE,
    
    -- Status
    hire_date DATE,
    termination_date DATE,
    is_active BOOLEAN DEFAULT true,
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5.2 Equipment (company-owned equipment)
CREATE TABLE IF NOT EXISTS equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_number VARCHAR(50) UNIQUE,
    equipment_name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    
    -- Location
    location_id UUID REFERENCES locations(id),
    assigned_employee_id UUID REFERENCES employees(id),
    
    -- Status
    status VARCHAR(50) DEFAULT 'Available',
    calibration_date DATE,
    calibration_due DATE,
    
    -- Financials
    purchase_date DATE,
    purchase_cost DECIMAL(12, 2),
    daily_rate DECIMAL(10, 2),
    
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

CREATE INDEX idx_sites_client ON sites(client_id);
CREATE INDEX idx_projects_client ON projects(client_id);
CREATE INDEX idx_projects_site ON projects(site_id);
CREATE INDEX idx_projects_location ON projects(location_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_scopes_project ON scopes(project_id);
CREATE INDEX idx_tasks_scope ON tasks(scope_id);
CREATE INDEX idx_apparatus_scope ON apparatus(scope_id);
CREATE INDEX idx_apparatus_task ON apparatus(task_id);
CREATE INDEX idx_apparatus_revenue_apparatus ON apparatus_revenue(apparatus_id);
CREATE INDEX idx_scope_labor_scope ON scope_labor_details(scope_id);
CREATE INDEX idx_employees_location ON employees(location_id);
CREATE INDEX idx_equipment_location ON equipment(location_id);

-- =============================================================================
-- TRIGGERS FOR UPDATED_AT
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        AND table_name IN (
            'locations', 'clients', 'sites', 'projects', 'scopes', 
            'tasks', 'apparatus', 'apparatus_revenue', 'scope_financial_summary',
            'project_financial_summary', 'scope_labor_details', 'estimators',
            'apparatus_type_master', 'neta_test_templates', 'employees', 'equipment'
        )
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%s_updated_at ON %s;
            CREATE TRIGGER update_%s_updated_at
            BEFORE UPDATE ON %s
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', t, t, t, t);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- SUCCESS MESSAGE
-- =============================================================================
SELECT 'RESA Power schema created successfully!' as message;
