-- ============================================================================
-- RESA POWER - SUPABASE MIGRATION SCHEMA
-- ============================================================================
-- Version: 1.0.0
-- Date: December 5, 2025
-- Target: Supabase PostgreSQL
-- Source: Dataverse V2 (v1.0.0.5) + V1.5.1.3 missing tables + PSS Portal
-- ============================================================================
-- TABLES: 22 total
--   Core PM (12): Client, Site, Location, Project, Scope, Task, Apparatus,
--                 Estimator, ScopeLaborDetail, ApparatusRevenue,
--                 ScopeFinancialSummary, ProjectFinancialSummary
--   Missing (3):  ApparatusTypeMaster, BusinessUnit, Employee
--   PSS Portal (7): Engineer, Contact, PSSStudy, DocumentTemplate,
--                   PSSDocument, RFI, ActivityLog
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- SECTION 1: LOOKUP / MASTER TABLES
-- ============================================================================

-- 1.1 BUSINESS UNIT (Multi-location support - Phoenix, Dallas, etc.)
CREATE TABLE business_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    name TEXT NOT NULL UNIQUE,           -- "Phoenix", "Dallas", "Houston"
    code TEXT UNIQUE,                    -- "PHX", "DAL", "HOU"
    region TEXT,                         -- "Southwest", "Texas"
    
    manager_name TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    phone TEXT,
    
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 1.2 APPARATUS TYPE MASTER (Standard hours lookup)
CREATE TABLE apparatus_type_master (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    name TEXT NOT NULL UNIQUE,           -- "15kV VCB", "LV Breaker", "Transformer"
    category TEXT,                       -- "Switchgear", "Transformer", "Cable"
    neta_section TEXT,                   -- "7.1", "7.2", etc.
    
    -- Default values for new apparatus
    default_hours DECIMAL(6,2),
    default_priority TEXT DEFAULT 'MEDIUM',
    
    -- Flags
    requires_datasheet BOOLEAN DEFAULT TRUE,
    requires_ir_scan BOOLEAN DEFAULT FALSE,
    
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SECTION 2: ORGANIZATION (Clients, Sites, Employees)
-- ============================================================================

-- 2.1 CLIENTS
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity (matching Dataverse field names for compatibility)
    name TEXT NOT NULL,                  -- cr950_clientname
    code TEXT UNIQUE,                    -- cr950_clientcode
    
    -- Contact Info
    address TEXT,                        -- cr950_clientaddress
    city TEXT,                           -- cr950_clientcity
    state TEXT,                          -- cr950_clientstate
    zip TEXT,                            -- cr950_clientzip
    country TEXT,                        -- cr950_clientcountry
    phone TEXT,                          -- cr950_clientphone
    email TEXT,                          -- cr950_clientemail
    website TEXT,                        -- cr950_clientwebsite
    
    -- Classification
    client_type TEXT DEFAULT 'CUSTOMER' CHECK (client_type IN (
        'CUSTOMER', 'CONTRACTOR', 'UTILITY', 'GOVERNMENT', 'INTERNAL'
    )),
    industry TEXT,
    
    -- Relationship
    account_manager TEXT,
    
    -- Metadata
    notes TEXT,                          -- cr950_clientnotes
    is_active BOOLEAN DEFAULT TRUE,      -- cr950_clientactive
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.2 SITES
CREATE TABLE sites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Identity
    name TEXT NOT NULL,                  -- cr950_sitename
    code TEXT,                           -- cr950_sitecode
    
    -- Location
    address TEXT,                        -- cr950_siteaddress
    city TEXT,                           -- cr950_sitecity
    state TEXT,                          -- cr950_sitestate
    zip TEXT,                            -- cr950_sitezip
    country TEXT,                        -- cr950_sitecountry
    
    -- Contact
    contact_name TEXT,                   -- cr950_sitecontactname
    contact_phone TEXT,                  -- cr950_sitecontactphone
    contact_email TEXT,                  -- cr950_sitecontactemail
    
    -- Metadata
    notes TEXT,                          -- cr950_sitenotes
    is_active BOOLEAN DEFAULT TRUE,      -- cr950_siteactive
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.3 LOCATIONS (RESA Office Locations)
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_unit_id UUID REFERENCES business_units(id),
    
    name TEXT NOT NULL,                  -- cr950_location_name
    abbreviation TEXT,                   -- cr950_location_abbreviation
    code TEXT UNIQUE,                    -- cr950_location_code
    region TEXT,                         -- cr950_location_region
    manager TEXT,                        -- cr950_location_manager
    address TEXT,                        -- cr950_location_address
    
    is_active BOOLEAN DEFAULT TRUE,      -- cr950_location_active
    sort_order INTEGER DEFAULT 0,        -- cr950_location_sortorder
    notes TEXT,                          -- cr950_location_notes
    
    created_at TIMESTAMPTZ DEFAULT NOW()
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
    department TEXT CHECK (department IN (
        'FIELD_OPERATIONS', 'ENGINEERING', 'PROJECT_MANAGEMENT',
        'SALES', 'ADMINISTRATION', 'EXECUTIVE'
    )),
    location_id UUID REFERENCES locations(id),
    business_unit_id UUID REFERENCES business_units(id),
    reports_to_id UUID REFERENCES employees(id),
    hire_date DATE,
    
    -- Rates
    hourly_rate DECIMAL(8,2),
    bill_rate DECIMAL(8,2),
    overtime_multiplier DECIMAL(3,2) DEFAULT 1.5,
    
    -- Skills
    skill_level TEXT CHECK (skill_level IN (
        'APPRENTICE', 'JOURNEYMAN', 'SENIOR', 'LEAD', 'SUPERVISOR'
    )),
    can_lead_crew BOOLEAN DEFAULT FALSE,
    
    -- Auth
    auth_user_id UUID,                   -- Links to Supabase auth.users
    
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.5 ENGINEERS (External Engineering Vendors - for PSS Portal)
CREATE TABLE engineers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    company_name TEXT NOT NULL,          -- "Shaw Engineering"
    code TEXT UNIQUE,                    -- "SHAW"
    
    address TEXT,
    city TEXT,
    state TEXT,
    phone TEXT,
    email TEXT,
    
    -- File Sharing
    dropbox_link TEXT,
    shared_folder_path TEXT,
    
    is_active BOOLEAN DEFAULT TRUE,
    accepts_new_projects BOOLEAN DEFAULT TRUE,
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.6 CONTACTS (People at Client/Vendor companies)
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
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
    contact_type TEXT NOT NULL CHECK (contact_type IN (
        'CLIENT', 'ENGINEER', 'VENDOR', 'UTILITY', 'OTHER'
    )),
    
    -- Relationships
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    engineer_id UUID REFERENCES engineers(id) ON DELETE SET NULL,
    
    -- Flags
    is_primary BOOLEAN DEFAULT FALSE,
    is_billing_contact BOOLEAN DEFAULT FALSE,
    receives_notifications BOOLEAN DEFAULT TRUE,
    
    -- Portal Access
    auth_user_id UUID,                   -- Links to Supabase auth.users
    portal_role TEXT CHECK (portal_role IN ('CLIENT', 'ENGINEER', 'RESA_ADMIN', 'RESA_STAFF')),
    
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);



-- ============================================================================
-- SECTION 3: PROJECTS & WORK
-- ============================================================================

-- 3.1 PROJECTS
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    project_number TEXT UNIQUE NOT NULL, -- cr950_projectnumber (e.g., "629266")
    name TEXT NOT NULL,                  -- cr950_projectname
    description TEXT,                    -- cr950_projectdescription
    
    -- Relationships
    client_id UUID REFERENCES clients(id),
    site_id UUID REFERENCES sites(id),
    location_id UUID REFERENCES locations(id),
    
    -- Classification
    project_type TEXT NOT NULL DEFAULT 'FIELD_TESTING' CHECK (project_type IN (
        'FIELD_TESTING', 'PSS_STUDY', 'ARC_FLASH_STUDY', 
        'MAINTENANCE', 'EMERGENCY', 'COMMISSIONING', 'ENGINEERING'
    )),
    business_unit TEXT,                  -- cr950_project_business_unit
    
    -- Status
    status TEXT DEFAULT 'NOT_STARTED' CHECK (status IN (
        'NOT_STARTED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED'
    )),
    is_active BOOLEAN DEFAULT TRUE,      -- cr950_projectactive
    
    -- Dates
    quote_date DATE,                     -- cr950_project_quote_date
    quote_revision TEXT,                 -- cr950_project_quote_revision
    start_date DATE,                     -- cr950_projectstartdate
    end_date DATE,                       -- cr950_projectenddate
    
    -- Financial
    po_number TEXT,                      -- cr950_projectponumber
    contract_value DECIMAL(12,2),        -- cr950_projectcontractvalue
    
    -- Team
    project_lead TEXT,                   -- cr950_project_lead
    project_manager_id UUID REFERENCES employees(id),
    lead_technician_id UUID REFERENCES employees(id),
    
    -- Metadata
    notes TEXT,                          -- cr950_projectnotes
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3.2 SCOPES (Deliverables within Projects)
CREATE TABLE scopes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id),
    site_id UUID REFERENCES sites(id),
    
    -- Identity
    scope_number TEXT NOT NULL,          -- cr950_scopenumber (e.g., "1.0", "2.0")
    name TEXT NOT NULL,                  -- cr950_scopename
    description TEXT,                    -- cr950_scopedescription
    
    -- Type
    scope_type TEXT,                     -- cr950_scopetype (ATS, MTS, etc.)
    
    -- Status
    status TEXT DEFAULT 'NOT_STARTED' CHECK (status IN (
        'NOT_STARTED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED'
    )),
    is_active BOOLEAN DEFAULT TRUE,      -- cr950_scopeactive
    due_date DATE,                       -- cr950_scopeduedate
    
    -- Financial
    labor_total DECIMAL(12,2),           -- cr950_scopelabortotal
    material_total DECIMAL(12,2),        -- cr950_scopematerialtotal
    revenue_total DECIMAL(12,2),         -- cr950_scoperevenuetotal
    margin_percent DECIMAL(5,2),         -- cr950_scopemarginpercent
    
    -- Metadata
    notes TEXT,                          -- cr950_scopenotes
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(project_id, scope_number)
);

-- 3.3 SCOPE LABOR DETAIL (Rate configuration per scope)
CREATE TABLE scope_labor_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID REFERENCES scopes(id) ON DELETE CASCADE UNIQUE,
    
    -- Identity
    name TEXT,                           -- cr950_scopelaborname
    source TEXT,                         -- cr950_scopelaborsource
    is_active BOOLEAN DEFAULT TRUE,      -- cr950_scopelaboractive
    
    -- Hours & Multiplier
    total_hours DECIMAL(8,2),            -- cr950_scopelabortotalhours
    multiplier DECIMAL(5,3) DEFAULT 1.000, -- cr950_scopelabormultiplier
    
    -- Rate Components
    onsite_rate DECIMAL(8,2),            -- cr950_scopelaboronsiterate
    onsite_total DECIMAL(12,2),          -- cr950_scopelaboronsitetotal
    offsite_rate DECIMAL(8,2),           -- cr950_scopelaboroffsiterate
    offsite_total DECIMAL(12,2),         -- cr950_scopelaboroffsitetotal
    travel_rate DECIMAL(8,2),            -- cr950_scopelabortravelrate
    travel_total DECIMAL(12,2),          -- cr950_scopelabortraveltotal
    outside_rate DECIMAL(8,2),           -- cr950_scopelaboroutsiderate
    outside_total DECIMAL(12,2),         -- cr950_scopelaboroutsidetotal
    
    -- Calculated (was missing in V2)
    sum_of_rates DECIMAL(12,2),          -- cr950_scopelaborsumofrates
    effective_rate DECIMAL(8,2) GENERATED ALWAYS AS (
        CASE WHEN total_hours > 0 
             THEN (COALESCE(onsite_total,0) + COALESCE(offsite_total,0) + 
                   COALESCE(travel_total,0) + COALESCE(outside_total,0)) / total_hours
             ELSE 0 
        END
    ) STORED,
    
    -- Quoted Amounts
    quoted_amount DECIMAL(12,2),         -- cr950_scopelaborquotedamount
    adjusted DECIMAL(12,2),              -- cr950_scopelaboradjusted
    not_adjusted DECIMAL(12,2),          -- cr950_scopelabornotadjusted
    
    notes TEXT,                          -- cr950_scopelabornotes
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3.4 TASKS (Work Items within Scopes)
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID REFERENCES scopes(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id),
    client_id UUID REFERENCES clients(id),
    site_id UUID REFERENCES sites(id),
    
    -- Identity
    task_number TEXT NOT NULL,           -- cr950_tasknumber (e.g., "1.1.1")
    name TEXT NOT NULL,                  -- cr950_taskname
    task_type TEXT,                      -- cr950_tasktype
    
    -- Status
    status TEXT DEFAULT 'NOT_STARTED' CHECK (status IN (
        'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD', 'SKIPPED'
    )),
    is_active BOOLEAN DEFAULT TRUE,      -- cr950_taskactive
    sequence INTEGER DEFAULT 0,          -- cr950_tasksequence
    
    -- Work Details
    quantity INTEGER DEFAULT 1,          -- cr950_taskquantity
    unit_price DECIMAL(10,2),            -- cr950_taskunitprice
    labor_hours DECIMAL(6,2),            -- cr950_tasklaborhours
    labor_rate DECIMAL(8,2),             -- cr950_tasklaborrate
    labor_total DECIMAL(12,2),           -- cr950_tasklabortotal
    task_total DECIMAL(12,2),            -- cr950_tasktotal
    
    -- Assignment
    assigned_to TEXT,                    -- cr950_task_assigned_to
    assigned_employee_id UUID REFERENCES employees(id),
    
    notes TEXT,                          -- cr950_tasknotes
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(scope_id, task_number)
);

-- 3.5 APPARATUS (Equipment being tested)
CREATE TABLE apparatus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID REFERENCES scopes(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id),
    project_id UUID REFERENCES projects(id),
    client_id UUID REFERENCES clients(id),
    site_id UUID REFERENCES sites(id),
    apparatus_type_id UUID REFERENCES apparatus_type_master(id),
    
    -- Identity
    name TEXT NOT NULL,                  -- cr950_apparatusname
    apparatus_type TEXT,                 -- cr950_apparatustype
    
    -- Equipment Details
    manufacturer TEXT,                   -- cr950_apparatusmanufacturer
    model TEXT,                          -- cr950_apparatusmodel
    serial TEXT,                         -- cr950_apparatusserial
    voltage TEXT,                        -- cr950_apparatusvoltage
    amperage TEXT,                       -- cr950_apparatusamperage
    
    -- Location in Facility
    location TEXT,                       -- cr950_apparatuslocation
    section TEXT,                        -- cr950_apparatussection
    row TEXT,                            -- cr950_apparatusrow
    
    -- Status
    status TEXT DEFAULT 'NOT_STARTED' CHECK (status IN (
        'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD', 'SKIPPED'
    )),
    completion_status TEXT CHECK (completion_status IN (
        'PLANNED', 'IN_PROGRESS', 'COMPLETE'
    )),                                  -- cr950_completion_status
    is_active BOOLEAN DEFAULT TRUE,      -- cr950_apparatusactive
    sequence INTEGER DEFAULT 0,          -- cr950_apparatussequence
    
    -- Hours & Revenue
    quantity INTEGER DEFAULT 1,          -- cr950_apparatusquantity
    hours_per_unit DECIMAL(6,2),         -- cr950_apparatushoursperunit
    total_hours DECIMAL(6,2),            -- cr950_apparatustotalhours
    delay_hours DECIMAL(6,2) DEFAULT 0,  -- cr950_delayhours
    revenue DECIMAL(12,2),               -- cr950_apparatusrevenue
    
    -- Results
    result TEXT,                         -- cr950_apparatusresult
    test_date DATE,                      -- cr950_apparatustestdate
    date_completed DATE,                 -- cr950_datecompleted
    
    -- Assignment
    assigned_to TEXT,                    -- cr950_apparatus_assigned_to
    assigned_employee_id UUID REFERENCES employees(id),
    
    notes TEXT,                          -- cr950_apparatusnotes
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);



-- ============================================================================
-- SECTION 4: REVENUE RECOGNITION
-- ============================================================================

-- 4.1 APPARATUS REVENUE (Revenue per completed apparatus)
CREATE TABLE apparatus_revenue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    apparatus_id UUID REFERENCES apparatus(id) ON DELETE CASCADE,
    scope_id UUID REFERENCES scopes(id),
    project_id UUID REFERENCES projects(id),
    scope_labor_detail_id UUID REFERENCES scope_labor_details(id),
    
    -- Identity
    name TEXT,                           -- cr950_name
    
    -- Hours
    planned_hours DECIMAL(6,2),          -- cr950_plannedhours
    actual_hours DECIMAL(6,2),           -- cr950_actualhours
    delay_hours DECIMAL(6,2) DEFAULT 0,  -- cr950_delayhours
    
    -- Calculated Total Hours (was missing in V2!)
    total_hours DECIMAL(6,2) GENERATED ALWAYS AS (
        COALESCE(planned_hours, 0) - COALESCE(delay_hours, 0)
    ) STORED,
    
    -- Rates
    labor_rate_applied DECIMAL(8,2),     -- cr950_laborrateapplied
    
    -- Revenue (was missing calculated field in V2!)
    revenue_amount DECIMAL(12,2) GENERATED ALWAYS AS (
        (COALESCE(planned_hours, 0) - COALESCE(delay_hours, 0)) * COALESCE(labor_rate_applied, 0)
    ) STORED,
    
    -- Status
    revenue_status TEXT DEFAULT 'PENDING' CHECK (revenue_status IN (
        'PENDING', 'RECOGNIZED', 'INVOICED', 'PAID', 'ADJUSTED'
    )),                                  -- cr950_revenuestatus
    
    -- Dates
    recognition_date DATE,               -- cr950_recognitiondate
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.2 SCOPE FINANCIAL SUMMARY (Aggregated revenue per scope)
CREATE TABLE scope_financial_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID REFERENCES scopes(id) ON DELETE CASCADE UNIQUE,
    
    name TEXT,                           -- cr950_name
    
    -- Counts
    apparatus_revenue_count INTEGER DEFAULT 0, -- cr950_apparatusrevenuecount
    
    -- Revenue Totals
    estimated_revenue DECIMAL(12,2),     -- cr950_estimatedrevenue
    total_revenue_recognized DECIMAL(12,2) DEFAULT 0, -- cr950_totalrevenuerecognized
    total_revenue_pending DECIMAL(12,2) DEFAULT 0,    -- cr950_totalrevenuepending
    revenue_variance DECIMAL(12,2) GENERATED ALWAYS AS (
        COALESCE(total_revenue_recognized, 0) - COALESCE(estimated_revenue, 0)
    ) STORED,                            -- cr950_revenuevariance
    
    -- Hours Totals
    total_planned_hours DECIMAL(8,2) DEFAULT 0, -- cr950_totalplannedhours
    total_actual_hours DECIMAL(8,2) DEFAULT 0,  -- cr950_totalactualhours
    
    -- Latest Date
    latest_revenue_date DATE,            -- cr950_latestrevenue_date
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.3 PROJECT FINANCIAL SUMMARY (Aggregated revenue per project)
CREATE TABLE project_financial_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    
    name TEXT,                           -- cr950_name
    
    -- Counts
    scope_count INTEGER DEFAULT 0,       -- cr950_scopecount
    apparatus_revenue_count INTEGER DEFAULT 0, -- cr950_apparatusrevenuecount
    
    -- Revenue Totals
    total_estimated_revenue DECIMAL(12,2), -- cr950_totalestimatedrevenue
    total_revenue_recognized DECIMAL(12,2) DEFAULT 0, -- cr950_totalrevenuerecognized
    total_revenue_pending DECIMAL(12,2) DEFAULT 0,    -- cr950_totalrevenuepending
    total_variance DECIMAL(12,2) GENERATED ALWAYS AS (
        COALESCE(total_revenue_recognized, 0) - COALESCE(total_estimated_revenue, 0)
    ) STORED,                            -- cr950_totalvariance
    
    -- Hours Totals
    total_project_hours DECIMAL(10,2) DEFAULT 0, -- cr950_totalprojecthours
    
    -- Latest Date
    latest_revenue_date DATE,            -- cr950_latestrevenue_date
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SECTION 5: ESTIMATOR (SharePoint Integration)
-- ============================================================================

CREATE TABLE estimators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    name TEXT,                           -- cr950_estimator_name
    project_name TEXT,                   -- cr950_estimator_projectname
    
    -- Relationships
    client_id UUID REFERENCES clients(id),
    project_id UUID REFERENCES projects(id),
    location_id UUID REFERENCES locations(id),
    
    -- SharePoint Data
    file_name TEXT,                      -- cr950_estimator_filename
    file_url TEXT,                       -- cr950_estimator_fileurl
    
    -- Dates
    estimate_date DATE,                  -- cr950_estimator_estimatedate
    extracted_at TIMESTAMPTZ,            -- cr950_estimator_extractedat
    last_modified TIMESTAMPTZ,           -- cr950_estimator_lastmodified
    
    -- Revision
    current_revision INTEGER DEFAULT 1,  -- cr950_estimator_currentrevision
    
    -- Summary
    scope_count INTEGER DEFAULT 0,       -- cr950_estimator_scopecount
    total_amount DECIMAL(12,2),          -- cr950_estimator_totalamount
    scope_json JSONB,                    -- cr950_estimator_scopejson (JSONB is better in PostgreSQL)
    
    -- Conversion
    converted_to_project BOOLEAN DEFAULT FALSE, -- cr950_estimator_convertedtoproject
    converted_date TIMESTAMPTZ,          -- cr950_estimator_converteddate
    
    notes TEXT,                          -- cr950_estimator_notes
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);



-- ============================================================================
-- SECTION 6: PSS PORTAL (Power System Studies)
-- ============================================================================

-- 6.1 DOCUMENT TEMPLATES (Master checklist of required documents)
CREATE TABLE document_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    name TEXT NOT NULL,                  -- "One-Line Diagram", "Load Study", etc.
    description TEXT,
    
    -- Applicability (which study types need this document)
    study_types TEXT[] NOT NULL DEFAULT ARRAY['PSS', 'ARC_FLASH'],
    is_required BOOLEAN DEFAULT TRUE,
    
    -- Guidance
    example_notes TEXT,
    
    -- Display
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6.2 PSS STUDIES (Power System Study tracking, linked to Projects)
CREATE TABLE pss_studies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    engineer_id UUID REFERENCES engineers(id),
    
    -- Study Type
    study_type TEXT NOT NULL CHECK (study_type IN (
        'PSS', 'ARC_FLASH', 'PSS_ARC_FLASH', 'COORDINATION'
    )),
    
    -- Status (PSS-specific 11-stage workflow)
    pss_status TEXT DEFAULT 'NEW_REQUEST' CHECK (pss_status IN (
        'NEW_REQUEST',
        'AWAITING_DOCUMENTS',
        'PARTIAL_DOCUMENTS',
        'READY_FOR_ENGINEER',
        'IN_PROGRESS',
        'RFI_PENDING',
        'DRAFT_SUBMITTED',
        'REVISIONS_REQUESTED',
        'REPORT_APPROVED',
        'STICKERS_PENDING',
        'CLOSED'
    )),
    
    -- Data Collection
    data_collection_by TEXT CHECK (data_collection_by IN ('RESA', 'CLIENT', 'ENGINEER')),
    stickers_by TEXT CHECK (stickers_by IN ('RESA', 'CLIENT', 'ENGINEER', 'N/A')),
    
    -- Key Dates
    target_report_date DATE,
    report_sent_date DATE,
    report_approved_date DATE,
    stickers_applied_date DATE,
    
    -- Status Tracking
    last_status_change TIMESTAMPTZ DEFAULT NOW(),
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6.3 PSS DOCUMENTS (Document tracking per study)
CREATE TABLE pss_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pss_study_id UUID REFERENCES pss_studies(id) ON DELETE CASCADE,
    template_id UUID REFERENCES document_templates(id),
    
    -- Document Details
    document_name TEXT,
    filename TEXT,
    file_url TEXT,
    
    -- Status (7-stage workflow)
    status TEXT DEFAULT 'NOT_REQUESTED' CHECK (status IN (
        'NOT_REQUESTED', 'REQUESTED', 'RECEIVED', 'UNDER_REVIEW',
        'REJECTED', 'ACCEPTED', 'N/A'
    )),
    
    -- Dates
    requested_date DATE,
    received_date DATE,
    reviewed_date DATE,
    
    -- People
    uploaded_by_contact_id UUID REFERENCES contacts(id),
    reviewed_by_contact_id UUID REFERENCES contacts(id),
    
    -- Metadata
    rejection_reason TEXT,
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6.4 RFIs (Requests for Information)
CREATE TABLE rfis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pss_study_id UUID REFERENCES pss_studies(id) ON DELETE CASCADE,
    related_document_id UUID REFERENCES pss_documents(id),
    
    -- Identity
    rfi_number TEXT NOT NULL,            -- "RFI-629266-001"
    
    -- Content
    subject TEXT NOT NULL,
    question TEXT NOT NULL,
    
    -- Status
    priority TEXT DEFAULT 'MEDIUM' CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')),
    status TEXT DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'RESPONDED', 'CLOSED')),
    
    -- Submission
    submitted_by_contact_id UUID REFERENCES contacts(id),
    submitted_date TIMESTAMPTZ DEFAULT NOW(),
    
    -- Response
    response TEXT,
    response_by_contact_id UUID REFERENCES contacts(id),
    response_date TIMESTAMPTZ,
    response_attachments TEXT[],
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6.5 ACTIVITY LOG (Communication history)
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Polymorphic references
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    pss_study_id UUID REFERENCES pss_studies(id) ON DELETE CASCADE,
    rfi_id UUID REFERENCES rfis(id) ON DELETE CASCADE,
    document_id UUID REFERENCES pss_documents(id) ON DELETE CASCADE,
    
    -- Activity Details
    activity_type TEXT NOT NULL CHECK (activity_type IN (
        'STATUS_CHANGE', 'DOCUMENT_UPLOADED', 'DOCUMENT_REVIEWED',
        'RFI_SUBMITTED', 'RFI_RESPONDED', 'EMAIL_SENT', 'EMAIL_RECEIVED',
        'PHONE_CALL', 'NOTE_ADDED', 'REMINDER_SENT'
    )),
    description TEXT NOT NULL,
    
    -- Who
    performed_by_contact_id UUID REFERENCES contacts(id),
    performed_by_employee_id UUID REFERENCES employees(id),
    
    -- Attachments
    attachments TEXT[],
    
    -- Visibility
    visible_to_client BOOLEAN DEFAULT TRUE,
    visible_to_engineer BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);



-- ============================================================================
-- SECTION 7: INDEXES
-- ============================================================================

-- Core Lookups
CREATE INDEX idx_sites_client ON sites(client_id);
CREATE INDEX idx_projects_client ON projects(client_id);
CREATE INDEX idx_projects_site ON projects(site_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_number ON projects(project_number);
CREATE INDEX idx_projects_type ON projects(project_type);

CREATE INDEX idx_scopes_project ON scopes(project_id);
CREATE INDEX idx_scopes_status ON scopes(status);
CREATE INDEX idx_tasks_scope ON tasks(scope_id);
CREATE INDEX idx_tasks_status ON tasks(status);

CREATE INDEX idx_apparatus_scope ON apparatus(scope_id);
CREATE INDEX idx_apparatus_task ON apparatus(task_id);
CREATE INDEX idx_apparatus_status ON apparatus(status);
CREATE INDEX idx_apparatus_completion ON apparatus(completion_status);

-- Revenue
CREATE INDEX idx_apparatus_revenue_apparatus ON apparatus_revenue(apparatus_id);
CREATE INDEX idx_apparatus_revenue_scope ON apparatus_revenue(scope_id);
CREATE INDEX idx_apparatus_revenue_project ON apparatus_revenue(project_id);
CREATE INDEX idx_apparatus_revenue_status ON apparatus_revenue(revenue_status);

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

-- Contacts
CREATE INDEX idx_contacts_client ON contacts(client_id);
CREATE INDEX idx_contacts_engineer ON contacts(engineer_id);
CREATE INDEX idx_contacts_type ON contacts(contact_type);

-- Full-text search
CREATE INDEX idx_projects_name_search ON projects USING gin(to_tsvector('english', name));
CREATE INDEX idx_clients_name_search ON clients USING gin(to_tsvector('english', name));

-- ============================================================================
-- SECTION 8: VIEWS (Dashboard Queries)
-- ============================================================================

-- 8.1 Project Dashboard View
CREATE OR REPLACE VIEW v_project_dashboard AS
SELECT 
    p.id,
    p.project_number,
    p.name AS project_name,
    p.project_type,
    p.status,
    c.name AS client_name,
    s.name AS site_name,
    l.name AS location_name,
    p.project_lead,
    p.start_date,
    p.end_date,
    p.contract_value,
    p.po_number,
    COALESCE(scope_stats.scope_count, 0) AS scope_count,
    COALESCE(scope_stats.total_tasks, 0) AS total_tasks,
    COALESCE(scope_stats.completed_tasks, 0) AS completed_tasks,
    COALESCE(scope_stats.total_apparatus, 0) AS total_apparatus,
    COALESCE(scope_stats.completed_apparatus, 0) AS completed_apparatus,
    CASE WHEN COALESCE(scope_stats.total_apparatus, 0) > 0 
         THEN ROUND(scope_stats.completed_apparatus::DECIMAL / scope_stats.total_apparatus * 100, 1)
         ELSE 0 
    END AS percent_complete,
    p.created_at,
    p.updated_at
FROM projects p
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN sites s ON p.site_id = s.id
LEFT JOIN locations l ON p.location_id = l.id
LEFT JOIN (
    SELECT 
        sc.project_id,
        COUNT(DISTINCT sc.id) AS scope_count,
        COUNT(DISTINCT t.id) AS total_tasks,
        COUNT(DISTINCT t.id) FILTER (WHERE t.status = 'COMPLETED') AS completed_tasks,
        COUNT(DISTINCT a.id) AS total_apparatus,
        COUNT(DISTINCT a.id) FILTER (WHERE a.completion_status = 'COMPLETE') AS completed_apparatus
    FROM scopes sc
    LEFT JOIN tasks t ON t.scope_id = sc.id
    LEFT JOIN apparatus a ON a.scope_id = sc.id
    GROUP BY sc.project_id
) scope_stats ON p.id = scope_stats.project_id;

-- 8.2 Scope Progress View
CREATE OR REPLACE VIEW v_scope_progress AS
SELECT 
    sc.id,
    sc.scope_number,
    sc.name AS scope_name,
    sc.status,
    p.project_number,
    p.name AS project_name,
    c.name AS client_name,
    sc.revenue_total AS estimated_revenue,
    sld.effective_rate,
    sld.total_hours AS planned_hours,
    COALESCE(app_stats.total_apparatus, 0) AS total_apparatus,
    COALESCE(app_stats.completed_apparatus, 0) AS completed_apparatus,
    COALESCE(app_stats.total_hours, 0) AS total_apparatus_hours,
    COALESCE(app_stats.completed_hours, 0) AS completed_hours,
    COALESCE(rev_stats.recognized_revenue, 0) AS recognized_revenue,
    COALESCE(rev_stats.pending_revenue, 0) AS pending_revenue,
    sc.created_at
FROM scopes sc
LEFT JOIN projects p ON sc.project_id = p.id
LEFT JOIN clients c ON sc.client_id = c.id
LEFT JOIN scope_labor_details sld ON sld.scope_id = sc.id
LEFT JOIN (
    SELECT 
        scope_id,
        COUNT(*) AS total_apparatus,
        COUNT(*) FILTER (WHERE completion_status = 'COMPLETE') AS completed_apparatus,
        SUM(total_hours) AS total_hours,
        SUM(total_hours) FILTER (WHERE completion_status = 'COMPLETE') AS completed_hours
    FROM apparatus
    GROUP BY scope_id
) app_stats ON sc.id = app_stats.scope_id
LEFT JOIN (
    SELECT 
        scope_id,
        SUM(revenue_amount) FILTER (WHERE revenue_status = 'RECOGNIZED') AS recognized_revenue,
        SUM(revenue_amount) FILTER (WHERE revenue_status = 'PENDING') AS pending_revenue
    FROM apparatus_revenue
    GROUP BY scope_id
) rev_stats ON sc.id = rev_stats.scope_id;

-- 8.3 PSS Portal Dashboard View
CREATE OR REPLACE VIEW v_pss_dashboard AS
SELECT 
    ps.id,
    p.project_number,
    p.name AS project_name,
    c.name AS client_name,
    e.company_name AS engineer_name,
    ps.study_type,
    ps.pss_status,
    ps.target_report_date,
    EXTRACT(DAY FROM (NOW() - ps.last_status_change))::INTEGER AS days_in_status,
    COALESCE(doc_stats.total_docs, 0) AS total_documents,
    COALESCE(doc_stats.received_docs, 0) AS received_documents,
    COALESCE(doc_stats.outstanding_docs, 0) AS outstanding_documents,
    COALESCE(rfi_stats.open_rfis, 0) AS open_rfis,
    ps.created_at
FROM pss_studies ps
JOIN projects p ON ps.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN engineers e ON ps.engineer_id = e.id
LEFT JOIN (
    SELECT 
        pss_study_id,
        COUNT(*) AS total_docs,
        COUNT(*) FILTER (WHERE status IN ('RECEIVED', 'ACCEPTED')) AS received_docs,
        COUNT(*) FILTER (WHERE status = 'REQUESTED') AS outstanding_docs
    FROM pss_documents
    GROUP BY pss_study_id
) doc_stats ON ps.id = doc_stats.pss_study_id
LEFT JOIN (
    SELECT 
        pss_study_id,
        COUNT(*) FILTER (WHERE status = 'OPEN') AS open_rfis
    FROM rfis
    GROUP BY pss_study_id
) rfi_stats ON ps.id = rfi_stats.pss_study_id;

-- 8.4 Outstanding Documents View
CREATE OR REPLACE VIEW v_outstanding_documents AS
SELECT 
    pd.id,
    p.project_number,
    p.name AS project_name,
    c.name AS client_name,
    dt.name AS document_type,
    pd.status,
    pd.requested_date,
    EXTRACT(DAY FROM (NOW() - pd.requested_date))::INTEGER AS days_outstanding,
    ps.pss_status
FROM pss_documents pd
JOIN pss_studies ps ON pd.pss_study_id = ps.id
JOIN projects p ON ps.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN document_templates dt ON pd.template_id = dt.id
WHERE pd.status = 'REQUESTED'
ORDER BY pd.requested_date ASC;

-- 8.5 Revenue Recognition View
CREATE OR REPLACE VIEW v_revenue_recognition AS
SELECT 
    ar.id,
    p.project_number,
    p.name AS project_name,
    c.name AS client_name,
    sc.scope_number,
    sc.name AS scope_name,
    a.name AS apparatus_name,
    ar.planned_hours,
    ar.delay_hours,
    ar.total_hours,
    ar.labor_rate_applied,
    ar.revenue_amount,
    ar.revenue_status,
    ar.recognition_date,
    ar.created_at
FROM apparatus_revenue ar
LEFT JOIN apparatus a ON ar.apparatus_id = a.id
LEFT JOIN scopes sc ON ar.scope_id = sc.id
LEFT JOIN projects p ON ar.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id
ORDER BY ar.created_at DESC;



-- ============================================================================
-- SECTION 9: TRIGGERS (Automatic Updates)
-- ============================================================================

-- 9.1 Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER tr_clients_updated_at BEFORE UPDATE ON clients 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_sites_updated_at BEFORE UPDATE ON sites 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_employees_updated_at BEFORE UPDATE ON employees 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_projects_updated_at BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_scopes_updated_at BEFORE UPDATE ON scopes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_tasks_updated_at BEFORE UPDATE ON tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_apparatus_updated_at BEFORE UPDATE ON apparatus 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_apparatus_revenue_updated_at BEFORE UPDATE ON apparatus_revenue 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_pss_studies_updated_at BEFORE UPDATE ON pss_studies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_pss_documents_updated_at BEFORE UPDATE ON pss_documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_rfis_updated_at BEFORE UPDATE ON rfis 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- 9.2 PSS Status change tracker
CREATE OR REPLACE FUNCTION track_pss_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.pss_status IS DISTINCT FROM NEW.pss_status THEN
        NEW.last_status_change = NOW();
        
        -- Log the status change
        INSERT INTO activity_log (
            pss_study_id,
            activity_type,
            description
        ) VALUES (
            NEW.id,
            'STATUS_CHANGE',
            'Status changed from ' || COALESCE(OLD.pss_status, 'NULL') || ' to ' || NEW.pss_status
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_pss_status_change BEFORE UPDATE ON pss_studies
    FOR EACH ROW EXECUTE FUNCTION track_pss_status_change();

-- 9.3 Revenue Recognition on Apparatus Completion
CREATE OR REPLACE FUNCTION create_revenue_on_completion()
RETURNS TRIGGER AS $$
DECLARE
    v_scope_labor scope_labor_details%ROWTYPE;
BEGIN
    -- Only trigger when apparatus is marked complete
    IF NEW.completion_status = 'COMPLETE' AND 
       (OLD.completion_status IS NULL OR OLD.completion_status != 'COMPLETE') THEN
        
        -- Get the scope labor details for the rate
        SELECT * INTO v_scope_labor 
        FROM scope_labor_details 
        WHERE scope_id = NEW.scope_id;
        
        -- Create revenue record if it doesn't exist
        INSERT INTO apparatus_revenue (
            apparatus_id,
            scope_id,
            project_id,
            scope_labor_detail_id,
            name,
            planned_hours,
            delay_hours,
            labor_rate_applied,
            revenue_status,
            recognition_date
        ) VALUES (
            NEW.id,
            NEW.scope_id,
            NEW.project_id,
            v_scope_labor.id,
            'REV-' || NEW.name,
            NEW.total_hours,
            COALESCE(NEW.delay_hours, 0),
            COALESCE(v_scope_labor.effective_rate, 0),
            'RECOGNIZED',
            NEW.date_completed
        )
        ON CONFLICT (apparatus_id) DO UPDATE SET
            delay_hours = EXCLUDED.delay_hours,
            recognition_date = EXCLUDED.recognition_date,
            revenue_status = 'RECOGNIZED',
            updated_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_apparatus_completion AFTER UPDATE ON apparatus
    FOR EACH ROW EXECUTE FUNCTION create_revenue_on_completion();

-- ============================================================================
-- SECTION 10: ROW LEVEL SECURITY (Foundation)
-- ============================================================================

-- Enable RLS on key tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE scopes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE apparatus ENABLE ROW LEVEL SECURITY;
ALTER TABLE pss_studies ENABLE ROW LEVEL SECURITY;
ALTER TABLE pss_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE rfis ENABLE ROW LEVEL SECURITY;

-- Default policy: Allow all for authenticated users (customize later)
CREATE POLICY "Allow all for authenticated" ON projects FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Allow all for authenticated" ON scopes FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Allow all for authenticated" ON tasks FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Allow all for authenticated" ON apparatus FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Allow all for authenticated" ON pss_studies FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Allow all for authenticated" ON pss_documents FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Allow all for authenticated" ON rfis FOR ALL USING (auth.role() = 'authenticated');

-- ============================================================================
-- SECTION 11: SEED DATA
-- ============================================================================

-- 11.1 Business Units
INSERT INTO business_units (name, code, region, city, state) VALUES
('Phoenix', 'PHX', 'Southwest', 'Phoenix', 'AZ'),
('Dallas', 'DAL', 'Texas', 'Dallas', 'TX'),
('Houston', 'HOU', 'Texas', 'Houston', 'TX'),
('Denver', 'DEN', 'Mountain', 'Denver', 'CO');

-- 11.2 Apparatus Type Master
INSERT INTO apparatus_type_master (name, category, default_hours, neta_section) VALUES
('15kV VCB', 'Switchgear', 4.0, '7.6.1'),
('15kV Metal-Clad Switchgear', 'Switchgear', 6.0, '7.6.1'),
('5kV VCB', 'Switchgear', 3.5, '7.6.1'),
('LV Air Circuit Breaker', 'Switchgear', 2.0, '7.6.1'),
('LV Molded Case Breaker', 'Switchgear', 0.5, '7.6.1'),
('Dry-Type Transformer', 'Transformer', 3.0, '7.2'),
('Oil-Filled Transformer', 'Transformer', 4.0, '7.2'),
('Pad-Mount Transformer', 'Transformer', 3.5, '7.2'),
('MV Cable (per 100ft)', 'Cable', 1.5, '7.3'),
('LV Cable (per 100ft)', 'Cable', 1.0, '7.3'),
('Protective Relay', 'Protective Devices', 2.5, '7.9'),
('Motor Control Center', 'MCC', 4.0, '7.16'),
('MCC Bucket', 'MCC', 0.75, '7.16'),
('ATS - Automatic Transfer Switch', 'Transfer Switch', 3.0, '7.22'),
('UPS System', 'UPS', 4.0, '7.24'),
('Battery Bank', 'DC Systems', 2.5, '7.5'),
('Ground Grid', 'Grounding', 3.0, '7.13');

-- 11.3 Document Templates (for PSS Portal)
INSERT INTO document_templates (name, study_types, is_required, sort_order, example_notes) VALUES
('One-Line Diagram', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH'], TRUE, 1, 'Single-line showing all equipment from utility to loads'),
('Utility Bill / Rate Schedule', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH'], TRUE, 2, 'Recent utility bill showing kVA demand'),
('Transformer Nameplate Data', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH'], TRUE, 3, 'kVA, voltage, impedance for all transformers'),
('Equipment Nameplate Photos', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH'], TRUE, 4, 'Photos of all breaker/relay nameplates'),
('Relay Settings', ARRAY['PSS', 'COORDINATION', 'PSS_ARC_FLASH'], TRUE, 5, 'Current relay/trip unit settings'),
('Cable Schedule', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH'], FALSE, 6, 'Size, length, and type of all cables'),
('Short Circuit Study', ARRAY['ARC_FLASH', 'PSS_ARC_FLASH'], FALSE, 7, 'Previous short circuit study if available'),
('Panel Schedules', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH'], FALSE, 8, 'Panel schedules for distribution panels'),
('Utility Letter', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH'], FALSE, 9, 'Available fault current from utility'),
('Motor List', ARRAY['PSS', 'PSS_ARC_FLASH'], FALSE, 10, 'HP, voltage, FLA for all motors > 50HP'),
('Load Study', ARRAY['PSS', 'PSS_ARC_FLASH'], FALSE, 11, 'Load flow data if available'),
('Site Layout / Plot Plan', ARRAY['PSS', 'ARC_FLASH', 'PSS_ARC_FLASH'], FALSE, 12, 'Building layout showing equipment locations');

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
-- Total Tables: 22
-- Total Views: 5
-- Total Triggers: 13
-- 
-- To deploy:
-- 1. Create new Supabase project
-- 2. Open SQL Editor
-- 3. Paste this entire file
-- 4. Run
-- ============================================================================

