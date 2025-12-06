-- ============================================================================
-- RESA POWER - COMPLETE UNIFIED DATABASE SCHEMA
-- ============================================================================
-- Platform: PostgreSQL / Supabase
-- Version: 1.0.0
-- Created: December 5, 2025
-- Source: Merged from Dataverse V1.5.1.3 + V2 + PSS Portal Requirements
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- SECTION 1: ENUMS (Option Sets from Dataverse)
-- ============================================================================

-- Project Status
CREATE TYPE project_status AS ENUM (
    'NOT_STARTED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED'
);

-- Project Type
CREATE TYPE project_type AS ENUM (
    'FIELD_TESTING', 'PSS_STUDY', 'ARC_FLASH_STUDY', 'MAINTENANCE', 
    'EMERGENCY', 'COMMISSIONING', 'ENGINEERING', 'OTHER'
);

-- Scope Status
CREATE TYPE scope_status AS ENUM (
    'NOT_STARTED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED'
);

-- Task Status
CREATE TYPE task_status AS ENUM (
    'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD', 'SKIPPED'
);

-- Task Availability
CREATE TYPE task_availability AS ENUM (
    'READY', 'ON_HOLD', 'NOT_AVAILABLE'
);

-- Completion Status (Apparatus)
CREATE TYPE completion_status AS ENUM (
    'PLANNED', 'IN_PROGRESS', 'COMPLETE', 'DEFERRED', 'CANCELLED'
);

-- Apparatus Assessment
CREATE TYPE apparatus_assessment AS ENUM (
    'ACCEPTABLE', 'MINOR_DEFICIENCY', 'MAJOR_DEFICIENCY', 'NON_SERVICEABLE', 'NOT_TESTED'
);

-- Checklist Status
CREATE TYPE checklist_status AS ENUM (
    'NOT_STARTED', 'IN_PROGRESS', 'SUBMITTED', 'APPROVED', 'REJECTED'
);

-- Revenue Status
CREATE TYPE revenue_status AS ENUM (
    'PENDING', 'RECOGNIZED', 'INVOICED', 'PAID', 'ADJUSTED', 'CANCELLED'
);

-- PSS Study Status
CREATE TYPE pss_status AS ENUM (
    'NEW_REQUEST', 'AWAITING_DOCUMENTS', 'PARTIAL_DOCUMENTS', 'READY_FOR_ENGINEER',
    'IN_PROGRESS', 'RFI_PENDING', 'DRAFT_SUBMITTED', 'REVISIONS_REQUESTED',
    'REPORT_APPROVED', 'STICKERS_PENDING', 'CLOSED'
);

-- PSS Study Type
CREATE TYPE pss_study_type AS ENUM (
    'PSS', 'ARC_FLASH', 'PSS_ARC_FLASH', 'COORDINATION'
);

-- Document Status
CREATE TYPE document_status AS ENUM (
    'NOT_REQUESTED', 'REQUESTED', 'RECEIVED', 'UNDER_REVIEW',
    'REJECTED', 'ACCEPTED', 'N_A'
);

-- RFI Status
CREATE TYPE rfi_status AS ENUM (
    'OPEN', 'RESPONDED', 'CLOSED'
);

-- RFI Priority
CREATE TYPE rfi_priority AS ENUM (
    'LOW', 'MEDIUM', 'HIGH', 'URGENT'
);

-- Contact Type
CREATE TYPE contact_type AS ENUM (
    'CLIENT', 'ENGINEER', 'VENDOR', 'UTILITY', 'INTERNAL', 'OTHER'
);

-- Portal User Role
CREATE TYPE portal_role AS ENUM (
    'RESA_ADMIN', 'RESA_PM', 'RESA_TECH', 'CLIENT', 'ENGINEER'
);

-- Employee Department
CREATE TYPE employee_department AS ENUM (
    'FIELD_OPERATIONS', 'ENGINEERING', 'PROJECT_MANAGEMENT',
    'SALES', 'ADMINISTRATION', 'EXECUTIVE'
);

-- Skill Level
CREATE TYPE skill_level AS ENUM (
    'APPRENTICE', 'JOURNEYMAN', 'SENIOR', 'LEAD', 'SUPERVISOR'
);



-- ============================================================================
-- SECTION 2: ORGANIZATION TABLES
-- ============================================================================

-- 2.1 LOCATIONS (Business Units - Phoenix, Dallas, etc.)
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    name TEXT NOT NULL,
    abbreviation TEXT,
    code TEXT UNIQUE,
    
    -- Details
    region TEXT,
    manager TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    phone TEXT,
    
    -- Display
    sort_order INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.2 CLIENTS
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    
    -- Contact Info
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    country TEXT DEFAULT 'USA',
    phone TEXT,
    email TEXT,
    website TEXT,
    
    -- Billing
    billing_address TEXT,
    billing_city TEXT,
    billing_state TEXT,
    billing_zip TEXT,
    
    -- Classification
    client_type TEXT,
    industry TEXT,
    
    -- Relationship
    account_manager TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.3 SITES (Physical Locations belonging to Clients)
CREATE TABLE sites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Identity
    name TEXT NOT NULL,
    code TEXT,
    
    -- Location
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    country TEXT DEFAULT 'USA',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Site Contact
    contact_name TEXT,
    contact_phone TEXT,
    contact_email TEXT,
    
    -- Classification
    site_type TEXT,
    utility_provider TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.4 EMPLOYEES (RESA Staff)
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    employee_number TEXT UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    full_name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
    email TEXT UNIQUE,
    phone TEXT,
    mobile TEXT,
    
    -- Employment
    title TEXT,
    department employee_department,
    skill_level skill_level,
    location_id UUID REFERENCES locations(id),
    
    -- Supervision
    reports_to_id UUID REFERENCES employees(id),
    
    -- Dates
    hire_date DATE,
    termination_date DATE,
    
    -- Rates & Billing
    hourly_rate DECIMAL(8, 2),
    bill_rate DECIMAL(8, 2),
    overtime_multiplier DECIMAL(3, 2) DEFAULT 1.5,
    
    -- Capabilities
    can_lead_crew BOOLEAN DEFAULT FALSE,
    max_arc_flash_ppe INTEGER,
    
    -- Auth
    auth_user_id UUID UNIQUE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.5 CONTACTS (People at Client/Vendor companies)
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Links
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    engineer_id UUID,  -- FK added after engineers table
    
    -- Identity
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    full_name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
    email TEXT,
    phone TEXT,
    mobile TEXT,
    
    -- Role
    title TEXT,
    department TEXT,
    contact_type contact_type NOT NULL DEFAULT 'CLIENT',
    
    -- Flags
    is_primary BOOLEAN DEFAULT FALSE,
    is_billing_contact BOOLEAN DEFAULT FALSE,
    receives_notifications BOOLEAN DEFAULT TRUE,
    
    -- Portal
    portal_user_id UUID,  -- FK added after portal_users table
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);



-- ============================================================================
-- SECTION 3: APPARATUS TYPE MASTER (from V1.5.1.3)
-- ============================================================================

-- 3.1 APPARATUS TYPES (Standard hours, categories)
CREATE TABLE apparatus_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    name TEXT NOT NULL UNIQUE,
    code TEXT UNIQUE,
    category TEXT,
    
    -- NETA Reference
    neta_section TEXT,
    neta_table TEXT,
    
    -- Default Values
    default_hours DECIMAL(6, 2),
    default_priority TEXT DEFAULT 'MEDIUM',
    
    -- Pricing
    default_unit_price DECIMAL(10, 2),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    
    -- Metadata
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SECTION 4: PROJECT HIERARCHY
-- ============================================================================

-- 4.1 PROJECTS
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    project_number TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    
    -- Relationships
    client_id UUID REFERENCES clients(id),
    site_id UUID REFERENCES sites(id),
    location_id UUID REFERENCES locations(id),
    
    -- Classification
    project_type project_type DEFAULT 'FIELD_TESTING',
    business_unit TEXT,
    
    -- Status
    status project_status DEFAULT 'NOT_STARTED',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Team
    project_lead TEXT,
    project_manager_id UUID REFERENCES employees(id),
    lead_technician_id UUID REFERENCES employees(id),
    
    -- Dates
    quote_date DATE,
    quote_revision TEXT,
    order_date DATE,
    start_date DATE,
    target_end_date DATE,
    actual_end_date DATE,
    
    -- Financial
    contract_value DECIMAL(12, 2),
    po_number TEXT,
    po_amount DECIMAL(12, 2),
    po_date DATE,
    
    -- ===== ROLLUP FIELDS (Calculated via triggers/views) =====
    -- Apparatus Counts
    total_apparatus_count INTEGER DEFAULT 0,
    completed_apparatus_count INTEGER DEFAULT 0,
    
    -- Hours
    total_apparatus_hours DECIMAL(10, 2) DEFAULT 0,
    total_completed_hours DECIMAL(10, 2) DEFAULT 0,
    total_actual_hours DECIMAL(10, 2) DEFAULT 0,
    total_delay_hours DECIMAL(10, 2) DEFAULT 0,
    total_remaining_hours DECIMAL(10, 2) DEFAULT 0,
    
    -- Dates (Min/Max from apparatus)
    earliest_actual_start DATE,
    latest_actual_start DATE,
    earliest_anticipated_start DATE,
    latest_anticipated_start DATE,
    earliest_completion_date DATE,
    latest_completion_date DATE,
    
    -- Calculated
    percent_complete DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE WHEN total_apparatus_count > 0 
             THEN ROUND((completed_apparatus_count::DECIMAL / total_apparatus_count) * 100, 2)
             ELSE 0 
        END
    ) STORED,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.2 SCOPES (Deliverables within Projects)
CREATE TABLE scopes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Denormalized for convenience (from V1.5.1.3 pattern)
    client_id UUID REFERENCES clients(id),
    site_id UUID REFERENCES sites(id),
    
    -- Identity
    scope_number TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    
    -- Classification
    scope_type TEXT,  -- "ATS", "MTS", "Commissioning", etc.
    neta_standard TEXT,
    
    -- Status
    status scope_status DEFAULT 'NOT_STARTED',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Dates
    due_date DATE,
    completion_date DATE,
    
    -- Financial Estimates
    labor_total DECIMAL(12, 2) DEFAULT 0,
    material_total DECIMAL(12, 2) DEFAULT 0,
    revenue_total DECIMAL(12, 2) DEFAULT 0,
    margin_percent DECIMAL(5, 2),
    multiplier DECIMAL(5, 3) DEFAULT 1.000,
    
    -- ===== ROLLUP FIELDS =====
    total_apparatus_count INTEGER DEFAULT 0,
    completed_apparatus_count INTEGER DEFAULT 0,
    total_apparatus_hours DECIMAL(10, 2) DEFAULT 0,
    total_completed_hours DECIMAL(10, 2) DEFAULT 0,
    total_actual_hours DECIMAL(10, 2) DEFAULT 0,
    total_delay_hours DECIMAL(10, 2) DEFAULT 0,
    total_remaining_hours DECIMAL(10, 2) DEFAULT 0,
    
    earliest_actual_start DATE,
    latest_actual_start DATE,
    earliest_anticipated_start DATE,
    latest_anticipated_start DATE,
    earliest_completion_date DATE,
    latest_completion_date DATE,
    
    percent_complete DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE WHEN total_apparatus_count > 0 
             THEN ROUND((completed_apparatus_count::DECIMAL / total_apparatus_count) * 100, 2)
             ELSE 0 
        END
    ) STORED,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(project_id, scope_number)
);



-- 4.3 SCOPE LABOR DETAILS (Rate configuration per scope)
CREATE TABLE scope_labor_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID REFERENCES scopes(id) ON DELETE CASCADE UNIQUE,
    
    -- Identity
    name TEXT,
    source TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Hours
    total_hours DECIMAL(10, 2) DEFAULT 0,
    
    -- Multiplier
    multiplier DECIMAL(5, 3) DEFAULT 1.000,
    
    -- Onsite Labor
    onsite_rate DECIMAL(10, 2),
    onsite_total DECIMAL(12, 2),
    
    -- Offsite Labor
    offsite_rate DECIMAL(10, 2),
    offsite_total DECIMAL(12, 2),
    
    -- Travel
    travel_rate DECIMAL(10, 2),
    travel_total DECIMAL(12, 2),
    
    -- Outside Services
    outside_rate DECIMAL(10, 2),
    outside_total DECIMAL(12, 2),
    
    -- Calculated Rates
    sum_of_rates DECIMAL(12, 2),
    effective_rate DECIMAL(10, 2) GENERATED ALWAYS AS (
        CASE WHEN total_hours > 0 
             THEN ROUND((COALESCE(onsite_total, 0) + COALESCE(offsite_total, 0) + 
                         COALESCE(travel_total, 0) + COALESCE(outside_total, 0)) / total_hours, 2)
             ELSE 0 
        END
    ) STORED,
    
    -- Quoted vs Adjusted
    quoted_amount DECIMAL(12, 2),
    adjusted_amount DECIMAL(12, 2),
    not_adjusted_amount DECIMAL(12, 2),
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.4 TASKS (Work items within Scopes)
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID REFERENCES scopes(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES tasks(id),
    
    -- Denormalized references
    project_id UUID REFERENCES projects(id),
    client_id UUID REFERENCES clients(id),
    site_id UUID REFERENCES sites(id),
    
    -- Identity
    task_number TEXT NOT NULL,
    name TEXT NOT NULL,
    task_type TEXT,
    
    -- Equipment Details
    apparatus_type_id UUID REFERENCES apparatus_types(id),
    designation TEXT,
    drawing TEXT,
    
    -- Status
    status task_status DEFAULT 'NOT_STARTED',
    availability task_availability DEFAULT 'READY',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Priority
    priority TEXT DEFAULT 'MEDIUM',
    
    -- Scheduling
    sequence INTEGER DEFAULT 0,
    
    -- Dates
    date_due DATE,
    date_completed DATE,
    
    -- Quantities & Hours
    quantity INTEGER DEFAULT 1,
    hours_per_unit DECIMAL(6, 2),
    labor_hours DECIMAL(10, 2),
    actual_hours DECIMAL(10, 2),
    delay_hours DECIMAL(10, 2) DEFAULT 0,
    
    -- Pricing
    unit_price DECIMAL(10, 2),
    labor_rate DECIMAL(10, 2),
    labor_total DECIMAL(12, 2),
    task_total DECIMAL(12, 2),
    
    -- Assignment
    assigned_to TEXT,
    assigned_employee_id UUID REFERENCES employees(id),
    
    -- ===== ROLLUP FIELDS =====
    total_apparatus_count INTEGER DEFAULT 0,
    completed_apparatus_count INTEGER DEFAULT 0,
    total_apparatus_hours DECIMAL(10, 2) DEFAULT 0,
    total_completed_hours DECIMAL(10, 2) DEFAULT 0,
    total_actual_hours DECIMAL(10, 2) DEFAULT 0,
    total_delay_hours DECIMAL(10, 2) DEFAULT 0,
    
    percent_complete DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE WHEN total_apparatus_count > 0 
             THEN ROUND((completed_apparatus_count::DECIMAL / total_apparatus_count) * 100, 2)
             ELSE 0 
        END
    ) STORED,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(scope_id, task_number)
);



-- 4.5 APPARATUS (Individual equipment items - core work unit)
CREATE TABLE apparatus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Hierarchy Links
    scope_id UUID REFERENCES scopes(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id),
    
    -- Denormalized references (from V1.5.1.3 pattern)
    project_id UUID REFERENCES projects(id),
    client_id UUID REFERENCES clients(id),
    site_id UUID REFERENCES sites(id),
    
    -- Identity
    apparatus_number INTEGER,
    name TEXT NOT NULL,
    designation TEXT,
    
    -- Equipment Type
    apparatus_type_id UUID REFERENCES apparatus_types(id),
    apparatus_type TEXT,  -- Denormalized for quick access
    
    -- Equipment Details
    manufacturer TEXT,
    model TEXT,
    serial_number TEXT,
    voltage TEXT,
    amperage TEXT,
    
    -- Location in Facility
    location_in_facility TEXT,
    section TEXT,
    row TEXT,
    drawing TEXT,
    
    -- Status & Completion
    status task_status DEFAULT 'NOT_STARTED',
    completion_status completion_status DEFAULT 'PLANNED',
    availability task_availability DEFAULT 'READY',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Assessment
    assessment apparatus_assessment,
    checklist_status checklist_status DEFAULT 'NOT_STARTED',
    datasheet TEXT,  -- 'YES', 'NO', 'N/A'
    
    -- Scheduling
    sequence INTEGER DEFAULT 0,
    priority TEXT DEFAULT 'MEDIUM',
    
    -- Dates
    anticipated_start DATE,
    actual_start DATE,
    date_completed DATE,
    approval_date DATE,
    
    -- Hours
    quantity INTEGER DEFAULT 1,
    hours_per_unit DECIMAL(6, 2),
    apparatus_hours DECIMAL(10, 2),  -- Planned hours
    actual_hours DECIMAL(10, 2),
    delay_hours DECIMAL(10, 2) DEFAULT 0,
    delay_reason TEXT,
    
    -- Calculated Hours
    completed_hours DECIMAL(10, 2) GENERATED ALWAYS AS (
        CASE WHEN completion_status = 'COMPLETE' THEN apparatus_hours ELSE 0 END
    ) STORED,
    remaining_hours DECIMAL(10, 2) GENERATED ALWAYS AS (
        CASE WHEN completion_status != 'COMPLETE' THEN apparatus_hours ELSE 0 END
    ) STORED,
    
    -- Revenue
    unit_price DECIMAL(10, 2),
    revenue_amount DECIMAL(12, 2),
    
    -- Assignment
    assigned_to TEXT,
    assigned_employee_id UUID REFERENCES employees(id),
    
    -- Test Results
    result TEXT,
    test_date DATE,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.6 APPARATUS REVENUE (Revenue recognition per apparatus)
CREATE TABLE apparatus_revenue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Links
    apparatus_id UUID REFERENCES apparatus(id) ON DELETE CASCADE,
    scope_id UUID REFERENCES scopes(id),
    project_id UUID REFERENCES projects(id),
    scope_labor_detail_id UUID REFERENCES scope_labor_details(id),
    
    -- Identity
    name TEXT,
    revenue_record_id TEXT UNIQUE,
    
    -- Source Data (copied from apparatus at recognition time)
    planned_hours DECIMAL(10, 2),
    actual_hours DECIMAL(10, 2),
    delay_hours DECIMAL(10, 2) DEFAULT 0,
    
    -- Rate Applied (from scope labor detail)
    labor_rate_applied DECIMAL(10, 2),
    
    -- Calculated Revenue
    total_hours DECIMAL(10, 2) GENERATED ALWAYS AS (
        COALESCE(planned_hours, 0) + COALESCE(delay_hours, 0)
    ) STORED,
    base_revenue DECIMAL(12, 2) GENERATED ALWAYS AS (
        COALESCE(planned_hours, 0) * COALESCE(labor_rate_applied, 0)
    ) STORED,
    delay_adjustment DECIMAL(12, 2) GENERATED ALWAYS AS (
        COALESCE(delay_hours, 0) * COALESCE(labor_rate_applied, 0)
    ) STORED,
    revenue_amount DECIMAL(12, 2) GENERATED ALWAYS AS (
        (COALESCE(planned_hours, 0) + COALESCE(delay_hours, 0)) * COALESCE(labor_rate_applied, 0)
    ) STORED,
    
    -- Status
    revenue_status revenue_status DEFAULT 'PENDING',
    
    -- Dates
    recognition_date DATE,
    invoice_date DATE,
    payment_date DATE,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);



-- 4.7 SCOPE FINANCIAL SUMMARY (Aggregated revenue per scope)
CREATE TABLE scope_financial_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID REFERENCES scopes(id) ON DELETE CASCADE UNIQUE,
    
    -- Identity
    name TEXT,
    
    -- Counts
    apparatus_revenue_count INTEGER DEFAULT 0,
    
    -- Hours
    total_planned_hours DECIMAL(10, 2) DEFAULT 0,
    total_actual_hours DECIMAL(10, 2) DEFAULT 0,
    total_delay_hours DECIMAL(10, 2) DEFAULT 0,
    total_billable_hours DECIMAL(10, 2) DEFAULT 0,
    
    -- Revenue
    estimated_revenue DECIMAL(12, 2) DEFAULT 0,
    total_revenue_recognized DECIMAL(12, 2) DEFAULT 0,
    total_revenue_pending DECIMAL(12, 2) DEFAULT 0,
    revenue_variance DECIMAL(12, 2) GENERATED ALWAYS AS (
        COALESCE(total_revenue_recognized, 0) - COALESCE(estimated_revenue, 0)
    ) STORED,
    
    -- Rates
    average_labor_rate DECIMAL(10, 2),
    
    -- Dates
    latest_revenue_date DATE,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.8 PROJECT FINANCIAL SUMMARY (Aggregated revenue per project)
CREATE TABLE project_financial_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    
    -- Identity
    name TEXT,
    
    -- Counts
    scope_count INTEGER DEFAULT 0,
    apparatus_revenue_count INTEGER DEFAULT 0,
    
    -- Hours
    total_project_hours DECIMAL(10, 2) DEFAULT 0,
    total_planned_hours DECIMAL(10, 2) DEFAULT 0,
    total_actual_hours DECIMAL(10, 2) DEFAULT 0,
    total_delay_hours DECIMAL(10, 2) DEFAULT 0,
    
    -- Revenue
    total_estimated_revenue DECIMAL(12, 2) DEFAULT 0,
    total_revenue_recognized DECIMAL(12, 2) DEFAULT 0,
    total_revenue_pending DECIMAL(12, 2) DEFAULT 0,
    total_variance DECIMAL(12, 2) GENERATED ALWAYS AS (
        COALESCE(total_revenue_recognized, 0) - COALESCE(total_estimated_revenue, 0)
    ) STORED,
    
    -- Dates
    latest_revenue_date DATE,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SECTION 5: ESTIMATOR (SharePoint Import)
-- ============================================================================

CREATE TABLE estimators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    name TEXT NOT NULL,
    project_name TEXT,
    
    -- Links
    client_id UUID REFERENCES clients(id),
    project_id UUID REFERENCES projects(id),
    location_id UUID REFERENCES locations(id),
    
    -- Source File
    file_name TEXT,
    file_url TEXT,
    
    -- Dates
    estimate_date DATE,
    extracted_at TIMESTAMPTZ,
    last_modified TIMESTAMPTZ,
    
    -- Revision
    current_revision INTEGER DEFAULT 1,
    
    -- Summary
    scope_count INTEGER DEFAULT 0,
    total_amount DECIMAL(12, 2),
    
    -- Data
    scope_json JSONB,
    
    -- Conversion Status
    converted_to_project BOOLEAN DEFAULT FALSE,
    converted_date DATE,
    
    -- Import Tracking
    import_id TEXT,
    sync_status TEXT,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);



-- ============================================================================
-- SECTION 6: PSS PORTAL TABLES
-- ============================================================================

-- 6.1 ENGINEERS (External Engineering Vendors like Shaw)
CREATE TABLE engineers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    company_name TEXT NOT NULL,
    code TEXT UNIQUE,
    
    -- Contact
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    phone TEXT,
    email TEXT,
    website TEXT,
    
    -- Sharing/Collaboration
    dropbox_link TEXT,
    shared_folder_path TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    accepts_new_projects BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add FK from contacts to engineers
ALTER TABLE contacts 
    ADD CONSTRAINT fk_contacts_engineer 
    FOREIGN KEY (engineer_id) REFERENCES engineers(id) ON DELETE SET NULL;

-- 6.2 PSS STUDIES (Power System Study projects)
CREATE TABLE pss_studies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Assignment
    engineer_id UUID REFERENCES engineers(id),
    
    -- Study Details
    study_type pss_study_type NOT NULL,
    
    -- Status
    pss_status pss_status DEFAULT 'NEW_REQUEST',
    last_status_change TIMESTAMPTZ DEFAULT NOW(),
    
    -- Data Collection
    data_collection_by TEXT,
    stickers_by TEXT,
    
    -- Key Dates
    target_report_date DATE,
    report_sent_date DATE,
    report_approved_date DATE,
    stickers_applied_date DATE,
    
    -- Calculated
    days_in_current_status INTEGER GENERATED ALWAYS AS (
        EXTRACT(DAY FROM (NOW() - last_status_change))::INTEGER
    ) STORED,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6.3 DOCUMENT TEMPLATES (Master checklist of required documents)
CREATE TABLE document_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    description TEXT,
    
    -- Applicability
    study_types pss_study_type[],
    is_required BOOLEAN DEFAULT TRUE,
    
    -- Guidance
    example_notes TEXT,
    
    -- Display
    sort_order INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6.4 PSS DOCUMENTS (Per-study document tracking)
CREATE TABLE pss_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pss_study_id UUID REFERENCES pss_studies(id) ON DELETE CASCADE,
    template_id UUID REFERENCES document_templates(id),
    
    -- Document Details
    document_name TEXT,
    filename TEXT,
    file_url TEXT,
    file_size_bytes BIGINT,
    mime_type TEXT,
    
    -- Status
    status document_status DEFAULT 'NOT_REQUESTED',
    
    -- Dates
    requested_date DATE,
    received_date DATE,
    reviewed_date DATE,
    
    -- People
    uploaded_by_contact_id UUID REFERENCES contacts(id),
    reviewed_by_contact_id UUID REFERENCES contacts(id),
    reviewed_by_employee_id UUID REFERENCES employees(id),
    
    -- Review
    rejection_reason TEXT,
    
    -- Calculated
    days_outstanding INTEGER GENERATED ALWAYS AS (
        CASE WHEN status = 'REQUESTED' AND requested_date IS NOT NULL
             THEN EXTRACT(DAY FROM (NOW() - requested_date::TIMESTAMP))::INTEGER
             ELSE NULL
        END
    ) STORED,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6.5 RFIs (Requests for Information)
CREATE TABLE rfis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pss_study_id UUID REFERENCES pss_studies(id) ON DELETE CASCADE,
    
    -- Identity
    rfi_number TEXT NOT NULL,
    
    -- Content
    subject TEXT NOT NULL,
    question TEXT NOT NULL,
    related_document_id UUID REFERENCES pss_documents(id),
    
    -- Classification
    priority rfi_priority DEFAULT 'MEDIUM',
    status rfi_status DEFAULT 'OPEN',
    
    -- Submission
    submitted_by_contact_id UUID REFERENCES contacts(id),
    submitted_by_employee_id UUID REFERENCES employees(id),
    submitted_date TIMESTAMPTZ DEFAULT NOW(),
    
    -- Response
    response TEXT,
    response_by_contact_id UUID REFERENCES contacts(id),
    response_by_employee_id UUID REFERENCES employees(id),
    response_date TIMESTAMPTZ,
    response_attachments TEXT[],
    
    -- Calculated
    days_open INTEGER GENERATED ALWAYS AS (
        CASE WHEN status = 'OPEN'
             THEN EXTRACT(DAY FROM (NOW() - submitted_date))::INTEGER
             ELSE NULL
        END
    ) STORED,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(pss_study_id, rfi_number)
);

-- 6.6 ACTIVITY LOG (Communication/action history)
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Polymorphic References
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    pss_study_id UUID REFERENCES pss_studies(id) ON DELETE CASCADE,
    scope_id UUID REFERENCES scopes(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    apparatus_id UUID REFERENCES apparatus(id) ON DELETE CASCADE,
    rfi_id UUID REFERENCES rfis(id) ON DELETE CASCADE,
    document_id UUID REFERENCES pss_documents(id) ON DELETE CASCADE,
    
    -- Activity Details
    activity_type TEXT NOT NULL,
    description TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    
    -- Who
    performed_by_contact_id UUID REFERENCES contacts(id),
    performed_by_employee_id UUID REFERENCES employees(id),
    
    -- Attachments
    attachments TEXT[],
    
    -- Visibility
    visible_to_client BOOLEAN DEFAULT TRUE,
    visible_to_engineer BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);



-- ============================================================================
-- SECTION 7: PORTAL USERS & ACCESS
-- ============================================================================

CREATE TABLE portal_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Auth
    email TEXT UNIQUE NOT NULL,
    auth_user_id UUID UNIQUE,  -- Links to Supabase auth.users
    
    -- Links
    contact_id UUID REFERENCES contacts(id),
    employee_id UUID REFERENCES employees(id),
    
    -- Role
    role portal_role NOT NULL,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_user_id UUID REFERENCES portal_users(id)
);

-- Add FK from contacts to portal_users
ALTER TABLE contacts 
    ADD CONSTRAINT fk_contacts_portal_user 
    FOREIGN KEY (portal_user_id) REFERENCES portal_users(id);

-- ============================================================================
-- SECTION 8: INDEXES FOR PERFORMANCE
-- ============================================================================

-- Clients & Sites
CREATE INDEX idx_sites_client ON sites(client_id);
CREATE INDEX idx_clients_name ON clients(name);
CREATE INDEX idx_clients_code ON clients(code);

-- Projects
CREATE INDEX idx_projects_client ON projects(client_id);
CREATE INDEX idx_projects_site ON projects(site_id);
CREATE INDEX idx_projects_location ON projects(location_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_number ON projects(project_number);
CREATE INDEX idx_projects_type ON projects(project_type);

-- Scopes
CREATE INDEX idx_scopes_project ON scopes(project_id);
CREATE INDEX idx_scopes_client ON scopes(client_id);
CREATE INDEX idx_scopes_status ON scopes(status);

-- Tasks
CREATE INDEX idx_tasks_scope ON tasks(scope_id);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_employee_id);

-- Apparatus
CREATE INDEX idx_apparatus_scope ON apparatus(scope_id);
CREATE INDEX idx_apparatus_task ON apparatus(task_id);
CREATE INDEX idx_apparatus_project ON apparatus(project_id);
CREATE INDEX idx_apparatus_status ON apparatus(completion_status);
CREATE INDEX idx_apparatus_type ON apparatus(apparatus_type_id);
CREATE INDEX idx_apparatus_assigned ON apparatus(assigned_employee_id);

-- Revenue
CREATE INDEX idx_apparatus_revenue_apparatus ON apparatus_revenue(apparatus_id);
CREATE INDEX idx_apparatus_revenue_scope ON apparatus_revenue(scope_id);
CREATE INDEX idx_apparatus_revenue_project ON apparatus_revenue(project_id);
CREATE INDEX idx_apparatus_revenue_status ON apparatus_revenue(revenue_status);

-- Financial Summaries
CREATE INDEX idx_scope_fin_scope ON scope_financial_summaries(scope_id);
CREATE INDEX idx_project_fin_project ON project_financial_summaries(project_id);

-- PSS Portal
CREATE INDEX idx_pss_studies_project ON pss_studies(project_id);
CREATE INDEX idx_pss_studies_engineer ON pss_studies(engineer_id);
CREATE INDEX idx_pss_studies_status ON pss_studies(pss_status);
CREATE INDEX idx_pss_documents_study ON pss_documents(pss_study_id);
CREATE INDEX idx_pss_documents_status ON pss_documents(status);
CREATE INDEX idx_rfis_study ON rfis(pss_study_id);
CREATE INDEX idx_rfis_status ON rfis(status);

-- Activity Log
CREATE INDEX idx_activity_log_project ON activity_log(project_id);
CREATE INDEX idx_activity_log_pss ON activity_log(pss_study_id);
CREATE INDEX idx_activity_log_created ON activity_log(created_at DESC);

-- Employees
CREATE INDEX idx_employees_location ON employees(location_id);
CREATE INDEX idx_employees_dept ON employees(department);
CREATE INDEX idx_employees_active ON employees(is_active);

-- Contacts
CREATE INDEX idx_contacts_client ON contacts(client_id);
CREATE INDEX idx_contacts_engineer ON contacts(engineer_id);
CREATE INDEX idx_contacts_type ON contacts(contact_type);

-- Estimators
CREATE INDEX idx_estimators_client ON estimators(client_id);
CREATE INDEX idx_estimators_project ON estimators(project_id);
CREATE INDEX idx_estimators_converted ON estimators(converted_to_project);

-- Full-text search
CREATE INDEX idx_projects_name_search ON projects USING gin(to_tsvector('english', name));
CREATE INDEX idx_clients_name_search ON clients USING gin(to_tsvector('english', name));
CREATE INDEX idx_apparatus_name_search ON apparatus USING gin(to_tsvector('english', name));



-- ============================================================================
-- SECTION 9: VIEWS FOR DASHBOARDS
-- ============================================================================

-- 9.1 PROJECT DASHBOARD VIEW
CREATE OR REPLACE VIEW v_project_dashboard AS
SELECT 
    p.id,
    p.project_number,
    p.name AS project_name,
    p.project_type,
    p.status,
    p.is_active,
    c.name AS client_name,
    c.id AS client_id,
    s.name AS site_name,
    l.name AS location_name,
    p.project_lead,
    p.order_date,
    p.start_date,
    p.target_end_date,
    p.contract_value,
    p.po_number,
    p.po_amount,
    p.total_apparatus_count,
    p.completed_apparatus_count,
    p.percent_complete,
    p.total_apparatus_hours,
    p.total_completed_hours,
    p.total_delay_hours,
    pfs.total_revenue_recognized,
    pfs.total_revenue_pending,
    pfs.total_estimated_revenue,
    p.created_at,
    p.updated_at
FROM projects p
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN sites s ON p.site_id = s.id
LEFT JOIN locations l ON p.location_id = l.id
LEFT JOIN project_financial_summaries pfs ON p.id = pfs.project_id;

-- 9.2 SCOPE DASHBOARD VIEW
CREATE OR REPLACE VIEW v_scope_dashboard AS
SELECT 
    sc.id,
    sc.scope_number,
    sc.name AS scope_name,
    sc.scope_type,
    sc.status,
    p.project_number,
    p.name AS project_name,
    p.id AS project_id,
    c.name AS client_name,
    sc.due_date,
    sc.completion_date,
    sc.total_apparatus_count,
    sc.completed_apparatus_count,
    sc.percent_complete,
    sc.total_apparatus_hours,
    sc.total_completed_hours,
    sc.total_delay_hours,
    sld.effective_rate,
    sfs.total_revenue_recognized,
    sfs.total_revenue_pending,
    sfs.estimated_revenue,
    sc.created_at
FROM scopes sc
JOIN projects p ON sc.project_id = p.id
LEFT JOIN clients c ON sc.client_id = c.id
LEFT JOIN scope_labor_details sld ON sc.id = sld.scope_id
LEFT JOIN scope_financial_summaries sfs ON sc.id = sfs.scope_id;

-- 9.3 APPARATUS TRACKING VIEW
CREATE OR REPLACE VIEW v_apparatus_tracking AS
SELECT 
    a.id,
    a.apparatus_number,
    a.name AS apparatus_name,
    a.designation,
    a.apparatus_type,
    a.completion_status,
    a.assessment,
    a.anticipated_start,
    a.actual_start,
    a.date_completed,
    a.apparatus_hours,
    a.actual_hours,
    a.delay_hours,
    a.delay_reason,
    a.assigned_to,
    t.task_number,
    t.name AS task_name,
    sc.scope_number,
    sc.name AS scope_name,
    p.project_number,
    p.name AS project_name,
    c.name AS client_name,
    ar.revenue_status,
    ar.revenue_amount,
    ar.recognition_date,
    a.created_at,
    a.updated_at
FROM apparatus a
LEFT JOIN tasks t ON a.task_id = t.id
LEFT JOIN scopes sc ON a.scope_id = sc.id
LEFT JOIN projects p ON a.project_id = p.id
LEFT JOIN clients c ON a.client_id = c.id
LEFT JOIN apparatus_revenue ar ON a.id = ar.apparatus_id;

-- 9.4 PSS PORTAL DASHBOARD VIEW
CREATE OR REPLACE VIEW v_pss_dashboard AS
SELECT 
    ps.id,
    p.project_number,
    p.name AS project_name,
    c.name AS client_name,
    e.company_name AS engineer_name,
    ps.study_type,
    ps.pss_status,
    ps.days_in_current_status,
    ps.target_report_date,
    ps.report_sent_date,
    ps.report_approved_date,
    ps.data_collection_by,
    ps.stickers_by,
    (SELECT COUNT(*) FROM pss_documents pd WHERE pd.pss_study_id = ps.id) AS total_documents,
    (SELECT COUNT(*) FROM pss_documents pd WHERE pd.pss_study_id = ps.id AND pd.status IN ('RECEIVED', 'ACCEPTED')) AS received_documents,
    (SELECT COUNT(*) FROM pss_documents pd WHERE pd.pss_study_id = ps.id AND pd.status = 'REQUESTED') AS outstanding_documents,
    (SELECT COUNT(*) FROM rfis r WHERE r.pss_study_id = ps.id AND r.status = 'OPEN') AS open_rfis,
    ps.created_at,
    ps.updated_at
FROM pss_studies ps
JOIN projects p ON ps.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN engineers e ON ps.engineer_id = e.id;

-- 9.5 REVENUE RECOGNITION VIEW
CREATE OR REPLACE VIEW v_revenue_summary AS
SELECT 
    p.id AS project_id,
    p.project_number,
    p.name AS project_name,
    c.name AS client_name,
    COUNT(DISTINCT sc.id) AS scope_count,
    COUNT(a.id) AS apparatus_count,
    COUNT(a.id) FILTER (WHERE a.completion_status = 'COMPLETE') AS completed_count,
    SUM(a.apparatus_hours) AS total_planned_hours,
    SUM(a.actual_hours) AS total_actual_hours,
    SUM(a.delay_hours) AS total_delay_hours,
    SUM(ar.revenue_amount) FILTER (WHERE ar.revenue_status = 'RECOGNIZED') AS recognized_revenue,
    SUM(ar.revenue_amount) FILTER (WHERE ar.revenue_status = 'PENDING') AS pending_revenue,
    SUM(ar.revenue_amount) AS total_revenue,
    MAX(ar.recognition_date) AS latest_recognition_date
FROM projects p
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN scopes sc ON p.id = sc.project_id
LEFT JOIN apparatus a ON sc.id = a.scope_id
LEFT JOIN apparatus_revenue ar ON a.id = ar.apparatus_id
GROUP BY p.id, p.project_number, p.name, c.name;

-- 9.6 OUTSTANDING DOCUMENTS VIEW (PSS)
CREATE OR REPLACE VIEW v_outstanding_documents AS
SELECT 
    pd.id,
    pd.document_name,
    dt.name AS template_name,
    pd.status,
    pd.requested_date,
    pd.days_outstanding,
    ps.pss_status,
    p.project_number,
    p.name AS project_name,
    c.name AS client_name,
    e.company_name AS engineer_name
FROM pss_documents pd
JOIN pss_studies ps ON pd.pss_study_id = ps.id
JOIN projects p ON ps.project_id = p.id
LEFT JOIN document_templates dt ON pd.template_id = dt.id
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN engineers e ON ps.engineer_id = e.id
WHERE pd.status = 'REQUESTED'
ORDER BY pd.days_outstanding DESC NULLS LAST;

-- 9.7 OPEN RFIs VIEW
CREATE OR REPLACE VIEW v_open_rfis AS
SELECT 
    r.id,
    r.rfi_number,
    r.subject,
    r.priority,
    r.status,
    r.submitted_date,
    r.days_open,
    ps.pss_status,
    p.project_number,
    p.name AS project_name,
    c.name AS client_name,
    e.company_name AS engineer_name,
    ct.full_name AS submitted_by
FROM rfis r
JOIN pss_studies ps ON r.pss_study_id = ps.id
JOIN projects p ON ps.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN engineers e ON ps.engineer_id = e.id
LEFT JOIN contacts ct ON r.submitted_by_contact_id = ct.id
WHERE r.status = 'OPEN'
ORDER BY 
    CASE r.priority 
        WHEN 'URGENT' THEN 1 
        WHEN 'HIGH' THEN 2 
        WHEN 'MEDIUM' THEN 3 
        ELSE 4 
    END,
    r.days_open DESC NULLS LAST;



-- ============================================================================
-- SECTION 10: TRIGGERS FOR AUTOMATED UPDATES
-- ============================================================================

-- 10.1 Updated_at Trigger Function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all major tables
CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sites_updated_at BEFORE UPDATE ON sites 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scopes_updated_at BEFORE UPDATE ON scopes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_apparatus_updated_at BEFORE UPDATE ON apparatus 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pss_studies_updated_at BEFORE UPDATE ON pss_studies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 10.2 PSS Status Change Tracking
CREATE OR REPLACE FUNCTION track_pss_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.pss_status IS DISTINCT FROM NEW.pss_status THEN
        NEW.last_status_change = NOW();
        
        -- Log the status change
        INSERT INTO activity_log (
            pss_study_id,
            activity_type,
            description,
            old_value,
            new_value
        ) VALUES (
            NEW.id,
            'STATUS_CHANGE',
            'PSS Study status changed from ' || OLD.pss_status || ' to ' || NEW.pss_status,
            OLD.pss_status::TEXT,
            NEW.pss_status::TEXT
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pss_status_change_trigger
    BEFORE UPDATE ON pss_studies
    FOR EACH ROW EXECUTE FUNCTION track_pss_status_change();

-- 10.3 Apparatus Completion → Revenue Recognition
CREATE OR REPLACE FUNCTION create_revenue_on_completion()
RETURNS TRIGGER AS $$
DECLARE
    v_labor_rate DECIMAL(10, 2);
    v_scope_labor_detail_id UUID;
BEGIN
    -- Only trigger when completion_status changes to 'COMPLETE'
    IF NEW.completion_status = 'COMPLETE' AND 
       (OLD.completion_status IS NULL OR OLD.completion_status != 'COMPLETE') THEN
        
        -- Get the effective labor rate from scope labor details
        SELECT id, effective_rate INTO v_scope_labor_detail_id, v_labor_rate
        FROM scope_labor_details
        WHERE scope_id = NEW.scope_id;
        
        -- Create revenue record if doesn't exist
        INSERT INTO apparatus_revenue (
            apparatus_id,
            scope_id,
            project_id,
            scope_labor_detail_id,
            name,
            planned_hours,
            actual_hours,
            delay_hours,
            labor_rate_applied,
            revenue_status,
            recognition_date
        ) VALUES (
            NEW.id,
            NEW.scope_id,
            NEW.project_id,
            v_scope_labor_detail_id,
            NEW.name || ' Revenue',
            NEW.apparatus_hours,
            NEW.actual_hours,
            COALESCE(NEW.delay_hours, 0),
            COALESCE(v_labor_rate, 0),
            'RECOGNIZED',
            CURRENT_DATE
        )
        ON CONFLICT (apparatus_id) DO UPDATE SET
            actual_hours = EXCLUDED.actual_hours,
            delay_hours = EXCLUDED.delay_hours,
            revenue_status = 'RECOGNIZED',
            recognition_date = CURRENT_DATE,
            updated_at = NOW();
        
        -- Log the activity
        INSERT INTO activity_log (
            project_id,
            scope_id,
            apparatus_id,
            activity_type,
            description
        ) VALUES (
            NEW.project_id,
            NEW.scope_id,
            NEW.id,
            'STATUS_CHANGE',
            'Apparatus "' || NEW.name || '" completed. Revenue recognized.'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER apparatus_completion_trigger
    AFTER UPDATE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION create_revenue_on_completion();

-- Also trigger on insert if already complete
CREATE TRIGGER apparatus_completion_insert_trigger
    AFTER INSERT ON apparatus
    FOR EACH ROW 
    WHEN (NEW.completion_status = 'COMPLETE')
    EXECUTE FUNCTION create_revenue_on_completion();



-- 10.4 Rollup Functions: Apparatus → Task → Scope → Project
CREATE OR REPLACE FUNCTION update_task_rollups()
RETURNS TRIGGER AS $$
DECLARE
    v_task_id UUID;
BEGIN
    -- Determine which task to update
    IF TG_OP = 'DELETE' THEN
        v_task_id := OLD.task_id;
    ELSE
        v_task_id := NEW.task_id;
    END IF;
    
    IF v_task_id IS NOT NULL THEN
        UPDATE tasks SET
            total_apparatus_count = (SELECT COUNT(*) FROM apparatus WHERE task_id = v_task_id),
            completed_apparatus_count = (SELECT COUNT(*) FROM apparatus WHERE task_id = v_task_id AND completion_status = 'COMPLETE'),
            total_apparatus_hours = (SELECT COALESCE(SUM(apparatus_hours), 0) FROM apparatus WHERE task_id = v_task_id),
            total_completed_hours = (SELECT COALESCE(SUM(apparatus_hours), 0) FROM apparatus WHERE task_id = v_task_id AND completion_status = 'COMPLETE'),
            total_actual_hours = (SELECT COALESCE(SUM(actual_hours), 0) FROM apparatus WHERE task_id = v_task_id),
            total_delay_hours = (SELECT COALESCE(SUM(delay_hours), 0) FROM apparatus WHERE task_id = v_task_id)
        WHERE id = v_task_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER apparatus_rollup_to_task
    AFTER INSERT OR UPDATE OR DELETE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION update_task_rollups();

-- Rollup: Task → Scope
CREATE OR REPLACE FUNCTION update_scope_rollups()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_id UUID;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_scope_id := OLD.scope_id;
    ELSE
        v_scope_id := NEW.scope_id;
    END IF;
    
    IF v_scope_id IS NOT NULL THEN
        UPDATE scopes SET
            total_apparatus_count = (SELECT COALESCE(SUM(total_apparatus_count), 0) FROM tasks WHERE scope_id = v_scope_id),
            completed_apparatus_count = (SELECT COALESCE(SUM(completed_apparatus_count), 0) FROM tasks WHERE scope_id = v_scope_id),
            total_apparatus_hours = (SELECT COALESCE(SUM(total_apparatus_hours), 0) FROM tasks WHERE scope_id = v_scope_id),
            total_completed_hours = (SELECT COALESCE(SUM(total_completed_hours), 0) FROM tasks WHERE scope_id = v_scope_id),
            total_actual_hours = (SELECT COALESCE(SUM(total_actual_hours), 0) FROM tasks WHERE scope_id = v_scope_id),
            total_delay_hours = (SELECT COALESCE(SUM(total_delay_hours), 0) FROM tasks WHERE scope_id = v_scope_id)
        WHERE id = v_scope_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER task_rollup_to_scope
    AFTER INSERT OR UPDATE OR DELETE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_scope_rollups();

-- Rollup: Scope → Project
CREATE OR REPLACE FUNCTION update_project_rollups()
RETURNS TRIGGER AS $$
DECLARE
    v_project_id UUID;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_project_id := OLD.project_id;
    ELSE
        v_project_id := NEW.project_id;
    END IF;
    
    IF v_project_id IS NOT NULL THEN
        UPDATE projects SET
            total_apparatus_count = (SELECT COALESCE(SUM(total_apparatus_count), 0) FROM scopes WHERE project_id = v_project_id),
            completed_apparatus_count = (SELECT COALESCE(SUM(completed_apparatus_count), 0) FROM scopes WHERE project_id = v_project_id),
            total_apparatus_hours = (SELECT COALESCE(SUM(total_apparatus_hours), 0) FROM scopes WHERE project_id = v_project_id),
            total_completed_hours = (SELECT COALESCE(SUM(total_completed_hours), 0) FROM scopes WHERE project_id = v_project_id),
            total_actual_hours = (SELECT COALESCE(SUM(total_actual_hours), 0) FROM scopes WHERE project_id = v_project_id),
            total_delay_hours = (SELECT COALESCE(SUM(total_delay_hours), 0) FROM scopes WHERE project_id = v_project_id)
        WHERE id = v_project_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER scope_rollup_to_project
    AFTER INSERT OR UPDATE OR DELETE ON scopes
    FOR EACH ROW EXECUTE FUNCTION update_project_rollups();

-- 10.5 Financial Summary Updates
CREATE OR REPLACE FUNCTION update_scope_financial_summary()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_id UUID;
BEGIN
    IF TG_OP = 'DELETE' THEN
        v_scope_id := OLD.scope_id;
    ELSE
        v_scope_id := NEW.scope_id;
    END IF;
    
    IF v_scope_id IS NOT NULL THEN
        INSERT INTO scope_financial_summaries (scope_id, name)
        VALUES (v_scope_id, 'Financial Summary')
        ON CONFLICT (scope_id) DO NOTHING;
        
        UPDATE scope_financial_summaries SET
            apparatus_revenue_count = (SELECT COUNT(*) FROM apparatus_revenue WHERE scope_id = v_scope_id),
            total_planned_hours = (SELECT COALESCE(SUM(planned_hours), 0) FROM apparatus_revenue WHERE scope_id = v_scope_id),
            total_actual_hours = (SELECT COALESCE(SUM(actual_hours), 0) FROM apparatus_revenue WHERE scope_id = v_scope_id),
            total_delay_hours = (SELECT COALESCE(SUM(delay_hours), 0) FROM apparatus_revenue WHERE scope_id = v_scope_id),
            total_revenue_recognized = (SELECT COALESCE(SUM(revenue_amount), 0) FROM apparatus_revenue WHERE scope_id = v_scope_id AND revenue_status = 'RECOGNIZED'),
            total_revenue_pending = (SELECT COALESCE(SUM(revenue_amount), 0) FROM apparatus_revenue WHERE scope_id = v_scope_id AND revenue_status = 'PENDING'),
            latest_revenue_date = (SELECT MAX(recognition_date) FROM apparatus_revenue WHERE scope_id = v_scope_id),
            updated_at = NOW()
        WHERE scope_id = v_scope_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER revenue_update_scope_summary
    AFTER INSERT OR UPDATE OR DELETE ON apparatus_revenue
    FOR EACH ROW EXECUTE FUNCTION update_scope_financial_summary();

-- Project Financial Summary from Scope Summaries
CREATE OR REPLACE FUNCTION update_project_financial_summary()
RETURNS TRIGGER AS $$
DECLARE
    v_project_id UUID;
BEGIN
    -- Get project_id from scope
    SELECT project_id INTO v_project_id FROM scopes WHERE id = NEW.scope_id;
    
    IF v_project_id IS NOT NULL THEN
        INSERT INTO project_financial_summaries (project_id, name)
        VALUES (v_project_id, 'Project Financial Summary')
        ON CONFLICT (project_id) DO NOTHING;
        
        UPDATE project_financial_summaries SET
            scope_count = (SELECT COUNT(*) FROM scopes WHERE project_id = v_project_id),
            apparatus_revenue_count = (SELECT COALESCE(SUM(apparatus_revenue_count), 0) FROM scope_financial_summaries sfs JOIN scopes s ON sfs.scope_id = s.id WHERE s.project_id = v_project_id),
            total_planned_hours = (SELECT COALESCE(SUM(total_planned_hours), 0) FROM scope_financial_summaries sfs JOIN scopes s ON sfs.scope_id = s.id WHERE s.project_id = v_project_id),
            total_revenue_recognized = (SELECT COALESCE(SUM(total_revenue_recognized), 0) FROM scope_financial_summaries sfs JOIN scopes s ON sfs.scope_id = s.id WHERE s.project_id = v_project_id),
            total_revenue_pending = (SELECT COALESCE(SUM(total_revenue_pending), 0) FROM scope_financial_summaries sfs JOIN scopes s ON sfs.scope_id = s.id WHERE s.project_id = v_project_id),
            latest_revenue_date = (SELECT MAX(latest_revenue_date) FROM scope_financial_summaries sfs JOIN scopes s ON sfs.scope_id = s.id WHERE s.project_id = v_project_id),
            updated_at = NOW()
        WHERE project_id = v_project_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER scope_summary_update_project
    AFTER INSERT OR UPDATE ON scope_financial_summaries
    FOR EACH ROW EXECUTE FUNCTION update_project_financial_summary();



-- ============================================================================
-- SECTION 11: ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on sensitive tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE scopes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE apparatus ENABLE ROW LEVEL SECURITY;
ALTER TABLE apparatus_revenue ENABLE ROW LEVEL SECURITY;
ALTER TABLE pss_studies ENABLE ROW LEVEL SECURITY;
ALTER TABLE pss_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE rfis ENABLE ROW LEVEL SECURITY;

-- RESA Staff can see/edit everything
CREATE POLICY "RESA staff full access to projects" ON projects
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM portal_users pu
            WHERE pu.auth_user_id = auth.uid()
            AND pu.role IN ('RESA_ADMIN', 'RESA_PM', 'RESA_TECH')
        )
    );

-- Clients can only see their own projects
CREATE POLICY "Clients see own projects" ON projects
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM portal_users pu
            JOIN contacts c ON c.portal_user_id = pu.id
            WHERE pu.auth_user_id = auth.uid()
            AND pu.role = 'CLIENT'
            AND c.client_id = projects.client_id
        )
    );

-- Engineers see assigned PSS studies
CREATE POLICY "Engineers see assigned studies" ON pss_studies
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM portal_users pu
            JOIN contacts c ON c.portal_user_id = pu.id
            WHERE pu.auth_user_id = auth.uid()
            AND pu.role = 'ENGINEER'
            AND c.engineer_id = pss_studies.engineer_id
        )
    );

-- Engineers can update their assigned studies
CREATE POLICY "Engineers update assigned studies" ON pss_studies
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM portal_users pu
            JOIN contacts c ON c.portal_user_id = pu.id
            WHERE pu.auth_user_id = auth.uid()
            AND pu.role = 'ENGINEER'
            AND c.engineer_id = pss_studies.engineer_id
        )
    );

-- ============================================================================
-- SECTION 12: SEED DATA
-- ============================================================================

-- 12.1 LOCATIONS (Business Units)
INSERT INTO locations (name, abbreviation, code, region, sort_order) VALUES
('Phoenix', 'PHX', 'PHX', 'Southwest', 1),
('Dallas', 'DFW', 'DFW', 'Texas', 2),
('Austin', 'AUS', 'AUS', 'Texas', 3),
('Los Angeles', 'LAX', 'LAX', 'West', 4),
('Denver', 'DEN', 'DEN', 'Mountain', 5);

-- 12.2 APPARATUS TYPES (Equipment Categories with Standard Hours)
INSERT INTO apparatus_types (name, code, category, default_hours, neta_section) VALUES
-- Switchgear
('Low Voltage Switchgear', 'LVSW', 'Switchgear', 4.0, '7.6'),
('Medium Voltage Switchgear', 'MVSW', 'Switchgear', 6.0, '7.6'),
('Metal-Enclosed Switchgear', 'MESW', 'Switchgear', 5.0, '7.6'),
('Switchboard', 'SWBD', 'Switchgear', 3.0, '7.6'),
('Motor Control Center', 'MCC', 'Switchgear', 2.0, '7.6'),
('Panelboard', 'PNL', 'Switchgear', 1.5, '7.6'),

-- Circuit Breakers
('Low Voltage Circuit Breaker', 'LVCB', 'Circuit Breakers', 2.0, '7.6.1'),
('Medium Voltage Circuit Breaker', 'MVCB', 'Circuit Breakers', 4.0, '7.6.1'),
('Molded Case Circuit Breaker', 'MCCB', 'Circuit Breakers', 0.5, '7.6.1'),
('Insulated Case Circuit Breaker', 'ICCB', 'Circuit Breakers', 1.5, '7.6.1'),

-- Transformers
('Liquid-Filled Transformer', 'XFMR-LIQ', 'Transformers', 6.0, '7.2'),
('Dry-Type Transformer', 'XFMR-DRY', 'Transformers', 4.0, '7.2'),
('Pad-Mounted Transformer', 'XFMR-PAD', 'Transformers', 5.0, '7.2'),
('Unit Substation Transformer', 'XFMR-SUB', 'Transformers', 5.0, '7.2'),

-- Cables
('Medium Voltage Cable', 'MV-CABLE', 'Cables', 2.0, '7.3'),
('Low Voltage Cable', 'LV-CABLE', 'Cables', 1.0, '7.3'),
('Shielded Power Cable', 'SPC', 'Cables', 2.5, '7.3'),

-- Protective Relays
('Electromechanical Relay', 'RELAY-EM', 'Protective Relays', 2.0, '7.9'),
('Solid-State Relay', 'RELAY-SS', 'Protective Relays', 2.5, '7.9'),
('Microprocessor Relay', 'RELAY-MP', 'Protective Relays', 3.0, '7.9'),

-- Grounding
('Ground Grid', 'GND-GRID', 'Grounding', 4.0, '7.13'),
('Ground Rod', 'GND-ROD', 'Grounding', 1.0, '7.13'),
('Grounding System', 'GND-SYS', 'Grounding', 3.0, '7.13'),

-- Motors & Generators
('AC Induction Motor', 'MTR-AC', 'Motors', 2.0, '7.15'),
('DC Motor', 'MTR-DC', 'Motors', 2.5, '7.15'),
('Generator', 'GEN', 'Generators', 6.0, '7.1'),
('Emergency Generator', 'GEN-EMER', 'Generators', 6.0, '7.1'),

-- UPS & Battery
('UPS System', 'UPS', 'UPS', 4.0, '7.4'),
('Battery System', 'BATT', 'Batteries', 3.0, '7.4'),
('Battery Charger', 'BC', 'Batteries', 2.0, '7.4'),

-- Other
('Automatic Transfer Switch', 'ATS', 'Transfer Switches', 3.0, '7.8'),
('Manual Transfer Switch', 'MTS', 'Transfer Switches', 2.0, '7.8'),
('Capacitor Bank', 'CAP', 'Power Factor', 2.0, '7.11'),
('Surge Protective Device', 'SPD', 'Surge Protection', 1.0, '7.12'),
('Current Transformer', 'CT', 'Instrument Transformers', 1.0, '7.10'),
('Potential Transformer', 'PT', 'Instrument Transformers', 1.0, '7.10');

-- 12.3 DOCUMENT TEMPLATES (PSS Portal)
INSERT INTO document_templates (name, code, description, study_types, is_required, sort_order) VALUES
('Single Line Diagram', 'SLD', 'Electrical single line diagram showing system configuration', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH']::pss_study_type[], TRUE, 1),
('Utility Bill', 'UTIL-BILL', 'Recent utility bill showing demand and usage', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH']::pss_study_type[], TRUE, 2),
('Utility Letter', 'UTIL-LTR', 'Letter from utility with fault current info', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH']::pss_study_type[], TRUE, 3),
('Transformer Nameplate', 'XFMR-NP', 'Photos of transformer nameplates', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH']::pss_study_type[], TRUE, 4),
('Breaker Nameplate', 'BKR-NP', 'Photos of breaker nameplates', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH']::pss_study_type[], TRUE, 5),
('Relay Settings', 'RELAY-SET', 'Current protective relay settings', ARRAY['PSS', 'COORDINATION']::pss_study_type[], TRUE, 6),
('Cable Schedule', 'CABLE-SCH', 'Cable sizes, lengths, and types', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH']::pss_study_type[], FALSE, 7),
('Panel Schedules', 'PNL-SCH', 'Panel schedules with breaker sizes', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH']::pss_study_type[], FALSE, 8),
('Motor Schedules', 'MTR-SCH', 'Motor HP, voltage, and FLA', ARRAY['PSS']::pss_study_type[], FALSE, 9),
('Previous Study', 'PREV-STUDY', 'Previous arc flash or coordination study', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH']::pss_study_type[], FALSE, 10),
('Site Photos', 'PHOTOS', 'General site and equipment photos', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH']::pss_study_type[], FALSE, 11),
('Equipment List', 'EQUIP-LIST', 'List of all electrical equipment', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH']::pss_study_type[], FALSE, 12);

-- 12.4 ENGINEERS (PSS Vendors)
INSERT INTO engineers (company_name, code, city, state, is_active) VALUES
('Shaw Engineering', 'SHAW', 'Phoenix', 'AZ', TRUE),
('Power Studies Inc', 'PSI', 'Dallas', 'TX', TRUE),
('Electrical Consultants', 'EC', 'Denver', 'CO', TRUE);



-- ============================================================================
-- SECTION 13: HELPER FUNCTIONS
-- ============================================================================

-- Generate project number
CREATE OR REPLACE FUNCTION generate_project_number()
RETURNS TEXT AS $$
DECLARE
    v_year TEXT := TO_CHAR(CURRENT_DATE, 'YY');
    v_seq INTEGER;
BEGIN
    SELECT COALESCE(MAX(
        CASE WHEN project_number ~ '^[0-9]{6}$' 
             THEN SUBSTRING(project_number FROM 3)::INTEGER 
             ELSE 0 
        END
    ), 0) + 1 INTO v_seq
    FROM projects
    WHERE project_number LIKE v_year || '%';
    
    RETURN v_year || LPAD(v_seq::TEXT, 4, '0');
END;
$$ LANGUAGE plpgsql;

-- Generate RFI number
CREATE OR REPLACE FUNCTION generate_rfi_number(p_project_number TEXT)
RETURNS TEXT AS $$
DECLARE
    v_seq INTEGER;
BEGIN
    SELECT COALESCE(MAX(
        SUBSTRING(rfi_number FROM 'RFI-' || p_project_number || '-([0-9]+)')::INTEGER
    ), 0) + 1 INTO v_seq
    FROM rfis r
    JOIN pss_studies ps ON r.pss_study_id = ps.id
    JOIN projects p ON ps.project_id = p.id
    WHERE p.project_number = p_project_number;
    
    RETURN 'RFI-' || p_project_number || '-' || LPAD(v_seq::TEXT, 3, '0');
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SCHEMA COMPLETE - SUMMARY
-- ============================================================================

/*
RESA POWER UNIFIED SCHEMA v1.0.0
================================

TABLE COUNT: 24 tables
-----------------------
Organization (6):
  1. locations          - Business units (Phoenix, Dallas, etc.)
  2. clients            - Customer companies
  3. sites              - Physical locations
  4. employees          - RESA staff
  5. contacts           - External people
  6. portal_users       - Authentication/access

Equipment Types (1):
  7. apparatus_types    - Standard equipment categories & hours

Project Hierarchy (8):
  8. projects                    - Master jobs
  9. scopes                      - Deliverables within projects
  10. scope_labor_details        - Rate configuration per scope
  11. tasks                      - Work items within scopes
  12. apparatus                  - Individual equipment (core work unit)
  13. apparatus_revenue          - Revenue recognition per apparatus
  14. scope_financial_summaries  - Aggregated per scope
  15. project_financial_summaries - Aggregated per project

PSS Portal (6):
  16. engineers          - External engineering vendors
  17. pss_studies        - Power system study projects
  18. document_templates - Master document checklist
  19. pss_documents      - Per-study document tracking
  20. rfis               - Requests for information
  21. activity_log       - Communication history

Import (1):
  22. estimators         - SharePoint import staging

Views (7):
  - v_project_dashboard
  - v_scope_dashboard
  - v_apparatus_tracking
  - v_pss_dashboard
  - v_revenue_summary
  - v_outstanding_documents
  - v_open_rfis

Triggers:
  - Auto-update timestamps
  - PSS status change tracking
  - Revenue recognition on apparatus completion
  - Rollup aggregation (apparatus → task → scope → project)
  - Financial summary updates

Seed Data:
  - 5 locations (Phoenix, Dallas, Austin, LA, Denver)
  - 35 apparatus types with standard hours
  - 12 document templates for PSS
  - 3 engineering vendors

*/

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
