# RESA Power - Unified Database Schema

## Comprehensive Platform Design
**Version:** 1.0  
**Date:** December 5, 2025  
**Purpose:** Single source of truth for all RESA Power operations

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RESA POWER UNIFIED PLATFORM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   CLIENTS    │  │  EMPLOYEES   │  │  EQUIPMENT   │  │   VEHICLES   │   │
│  │   & SITES    │  │   & CERTS    │  │  & ASSETS    │  │   & FLEET    │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │            │
│         └────────────┬────┴────────┬────────┴────────┬────────┘            │
│                      │             │                 │                      │
│              ┌───────▼─────────────▼─────────────────▼───────┐             │
│              │              PROJECTS / JOBS                   │             │
│              │    (Field Testing, PSS Studies, Services)      │             │
│              └───────┬─────────────┬─────────────────┬───────┘             │
│                      │             │                 │                      │
│         ┌────────────┴───┐   ┌─────┴─────┐   ┌──────┴──────────┐          │
│         │                │   │           │   │                  │          │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌─────▼─────┐  ┌────────────▼────┐    │
│  │   SCOPES    │  │ PSS STUDIES │  │  BILLING  │  │   SCHEDULING    │    │
│  │   TASKS     │  │ DOCUMENTS   │  │  REVENUE  │  │   DISPATCHING   │    │
│  │  APPARATUS  │  │    RFIs     │  │  EXPENSES │  │   TIME ENTRIES  │    │
│  └─────────────┘  └─────────────┘  └───────────┘  └─────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Entity Relationship Diagram

```
                              ┌─────────────┐
                              │   CLIENTS   │
                              └──────┬──────┘
                                     │ 1:N
                     ┌───────────────┼───────────────┐
                     │               │               │
              ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
              │    SITES    │ │  CONTACTS   │ │   PORTAL    │
              │  (Locations)│ │  (People)   │ │   USERS     │
              └──────┬──────┘ └─────────────┘ └─────────────┘
                     │ 1:N
              ┌──────▼──────┐
              │  PROJECTS   │◄────────────────────────────────┐
              │   (Jobs)    │                                 │
              └──────┬──────┘                                 │
                     │                                        │
      ┌──────────────┼──────────────┬─────────────────┐      │
      │ 1:N          │ 1:N          │ 1:N             │      │
┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐    ┌──────▼──────┐
│  SCOPES   │  │PSS_STUDIES│  │ SCHEDULES │    │  ENGINEERS  │
│(Deliverbl)│  │(Study Prj)│  │(Dispatch) │    │  (Vendors)  │
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘    └─────────────┘
      │ 1:N          │ 1:N          │ 1:N
┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
│   TASKS   │  │ DOCUMENTS │  │TIME_ENTRY │
│(Work Item)│  │  & RFIs   │  │ EXPENSES  │
└─────┬─────┘  └───────────┘  └───────────┘
      │ 1:N
┌─────▼─────┐
│ APPARATUS │
│ REVENUE   │
└───────────┘

         ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
         │  EMPLOYEES  │      │  EQUIPMENT  │      │  VEHICLES   │
         │   (Staff)   │      │  (Assets)   │      │   (Fleet)   │
         └──────┬──────┘      └──────┬──────┘      └──────┬──────┘
                │ 1:N                │ 1:N                │ 1:N
         ┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
         │   CERTS &   │      │ CALIBRATION │      │ MAINTENANCE │
         │  TRAINING   │      │   RECORDS   │      │   RECORDS   │
         └─────────────┘      └─────────────┘      └─────────────┘
```

---

## 3. Complete Schema Definition (PostgreSQL)

```sql
-- ============================================================================
-- RESA POWER - UNIFIED DATABASE SCHEMA
-- ============================================================================
-- Platform: PostgreSQL / Supabase
-- Version: 1.0
-- Date: December 5, 2025
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- ============================================================================
-- SECTION 1: ORGANIZATION & PEOPLE
-- ============================================================================

-- 1.1 CLIENTS (Customer Companies)
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    name TEXT NOT NULL,
    code TEXT UNIQUE,                    -- "ROSENDIN", "LASNAP", etc.
    
    -- Contact Info
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    phone TEXT,
    website TEXT,
    
    -- Classification
    client_type TEXT DEFAULT 'CUSTOMER' CHECK (client_type IN (
        'CUSTOMER', 'CONTRACTOR', 'UTILITY', 'GOVERNMENT', 'INTERNAL'
    )),
    industry TEXT,                       -- "Manufacturing", "Healthcare", etc.
    
    -- Relationship
    account_manager_id UUID,             -- FK to employees
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 1.2 SITES (Physical Locations)
CREATE TABLE sites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    
    -- Identity
    name TEXT NOT NULL,
    code TEXT,                           -- "LASNAP16", "SWA-TECH-OPS"
    
    -- Location
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Site Details
    site_type TEXT,                      -- "Industrial", "Commercial", "Data Center"
    utility_provider TEXT,               -- "APS", "SRP", etc.
    
    -- Metadata
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 1.3 CONTACTS (People at Client/Vendor Companies)
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
    engineer_id UUID,                    -- FK to engineers table
    
    -- Flags
    is_primary BOOLEAN DEFAULT FALSE,
    is_billing_contact BOOLEAN DEFAULT FALSE,
    receives_notifications BOOLEAN DEFAULT TRUE,
    
    -- Portal Access
    portal_user_id UUID,                 -- FK to users table
    
    -- Metadata
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 1.4 EMPLOYEES (RESA Staff)
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    employee_number TEXT UNIQUE,         -- "EMP-001"
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    full_name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    mobile TEXT,
    
    -- Employment
    title TEXT,
    department TEXT CHECK (department IN (
        'FIELD_OPERATIONS', 'ENGINEERING', 'PROJECT_MANAGEMENT', 
        'SALES', 'ADMINISTRATION', 'EXECUTIVE'
    )),
    employee_type TEXT DEFAULT 'FULL_TIME' CHECK (employee_type IN (
        'FULL_TIME', 'PART_TIME', 'CONTRACTOR', 'INTERN'
    )),
    hire_date DATE,
    termination_date DATE,
    
    -- Supervisor
    reports_to_id UUID REFERENCES employees(id),
    
    -- Rates & Billing
    hourly_rate DECIMAL(8, 2),
    bill_rate DECIMAL(8, 2),
    overtime_multiplier DECIMAL(3, 2) DEFAULT 1.5,
    
    -- Skills & Qualifications
    skill_level TEXT CHECK (skill_level IN (
        'APPRENTICE', 'JOURNEYMAN', 'SENIOR', 'LEAD', 'SUPERVISOR'
    )),
    can_lead_crew BOOLEAN DEFAULT FALSE,
    max_arc_flash_ppe_level INTEGER,     -- 1, 2, 3, 4
    
    -- System Access
    auth_user_id UUID,                   -- Links to Supabase auth.users
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 1.5 EMPLOYEE CERTIFICATIONS
CREATE TABLE employee_certifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    
    -- Certification Details
    certification_type TEXT NOT NULL,    -- "NETA_LEVEL_3", "OSHA_30", etc.
    certification_name TEXT NOT NULL,
    issuing_organization TEXT,
    certification_number TEXT,
    
    -- Dates
    issue_date DATE,
    expiration_date DATE,
    
    -- Status
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN (
        'ACTIVE', 'EXPIRED', 'REVOKED', 'PENDING_RENEWAL'
    )),
    
    -- Documentation
    document_url TEXT,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 1.6 EMPLOYEE TRAINING RECORDS
CREATE TABLE employee_training (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    
    -- Training Details
    training_type TEXT NOT NULL,
    training_name TEXT NOT NULL,
    provider TEXT,
    
    -- Dates
    completion_date DATE NOT NULL,
    expiration_date DATE,
    
    -- Results
    passed BOOLEAN DEFAULT TRUE,
    score DECIMAL(5, 2),
    
    -- Documentation
    certificate_url TEXT,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SECTION 2: EQUIPMENT & FLEET
-- ============================================================================

-- 2.1 EQUIPMENT CATEGORIES (Lookup)
CREATE TABLE equipment_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,           -- "Test Equipment", "PPE", "Tools"
    description TEXT,
    requires_calibration BOOLEAN DEFAULT FALSE,
    calibration_interval_days INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.2 EQUIPMENT (Test Sets, Tools, PPE)
CREATE TABLE equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    asset_tag TEXT UNIQUE NOT NULL,      -- "TE-001", "PPE-042"
    serial_number TEXT,
    name TEXT NOT NULL,
    description TEXT,
    
    -- Classification
    category_id UUID REFERENCES equipment_categories(id),
    equipment_type TEXT,                 -- "Megger", "Hi-Pot", "Multimeter"
    manufacturer TEXT,
    model TEXT,
    
    -- Acquisition
    purchase_date DATE,
    purchase_price DECIMAL(10, 2),
    vendor TEXT,
    warranty_expiration DATE,
    
    -- Location & Assignment
    current_location TEXT,               -- "Warehouse", "Vehicle-001", "Job Site"
    assigned_to_employee_id UUID REFERENCES employees(id),
    assigned_to_vehicle_id UUID,         -- FK to vehicles
    
    -- Calibration (for test equipment)
    requires_calibration BOOLEAN DEFAULT FALSE,
    last_calibration_date DATE,
    next_calibration_date DATE,
    calibration_vendor TEXT,
    
    -- Status
    status TEXT DEFAULT 'AVAILABLE' CHECK (status IN (
        'AVAILABLE', 'IN_USE', 'IN_CALIBRATION', 'IN_REPAIR', 
        'OUT_OF_SERVICE', 'RETIRED'
    )),
    condition TEXT CHECK (condition IN (
        'NEW', 'EXCELLENT', 'GOOD', 'FAIR', 'POOR'
    )),
    
    -- Metadata
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.3 EQUIPMENT CALIBRATION RECORDS
CREATE TABLE equipment_calibrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_id UUID REFERENCES equipment(id) ON DELETE CASCADE,
    
    -- Calibration Details
    calibration_date DATE NOT NULL,
    due_date DATE NOT NULL,
    performed_by TEXT,                   -- Vendor name or employee
    calibration_vendor TEXT,
    
    -- Results
    passed BOOLEAN DEFAULT TRUE,
    adjustment_required BOOLEAN DEFAULT FALSE,
    
    -- Documentation
    certificate_number TEXT,
    certificate_url TEXT,
    
    -- Cost
    cost DECIMAL(10, 2),
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.4 VEHICLES (Fleet)
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    vehicle_number TEXT UNIQUE NOT NULL, -- "V-001"
    vin TEXT UNIQUE,
    license_plate TEXT,
    
    -- Details
    year INTEGER,
    make TEXT,
    model TEXT,
    color TEXT,
    vehicle_type TEXT CHECK (vehicle_type IN (
        'TRUCK', 'VAN', 'SUV', 'SEDAN', 'TRAILER'
    )),
    
    -- Capacity
    passenger_capacity INTEGER,
    cargo_capacity_lbs INTEGER,
    towing_capacity_lbs INTEGER,
    
    -- Assignment
    assigned_to_employee_id UUID REFERENCES employees(id),
    home_location TEXT,
    
    -- Tracking
    current_mileage INTEGER,
    last_mileage_update DATE,
    gps_tracker_id TEXT,
    
    -- Registration & Insurance
    registration_expiration DATE,
    insurance_policy_number TEXT,
    insurance_expiration DATE,
    
    -- Status
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN (
        'ACTIVE', 'IN_MAINTENANCE', 'OUT_OF_SERVICE', 'SOLD'
    )),
    
    -- Metadata
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2.5 VEHICLE MAINTENANCE RECORDS
CREATE TABLE vehicle_maintenance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE CASCADE,
    
    -- Service Details
    service_date DATE NOT NULL,
    service_type TEXT NOT NULL,          -- "Oil Change", "Tires", "Brakes"
    description TEXT,
    mileage_at_service INTEGER,
    
    -- Vendor
    service_provider TEXT,
    invoice_number TEXT,
    
    -- Cost
    parts_cost DECIMAL(10, 2),
    labor_cost DECIMAL(10, 2),
    total_cost DECIMAL(10, 2),
    
    -- Next Service
    next_service_date DATE,
    next_service_mileage INTEGER,
    
    -- Documentation
    receipt_url TEXT,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SECTION 3: PROJECTS & WORK
-- ============================================================================

-- 3.1 PROJECTS (Master Jobs)
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    project_number TEXT UNIQUE NOT NULL, -- "629266", "LASNAP16-001"
    name TEXT NOT NULL,
    description TEXT,
    
    -- Relationships
    client_id UUID REFERENCES clients(id),
    site_id UUID REFERENCES sites(id),
    
    -- Classification
    project_type TEXT NOT NULL CHECK (project_type IN (
        'FIELD_TESTING',        -- Standard NETA testing
        'PSS_STUDY',            -- Power System Study
        'ARC_FLASH_STUDY',      -- Arc Flash Analysis
        'MAINTENANCE',          -- Preventive maintenance
        'EMERGENCY',            -- Emergency callout
        'COMMISSIONING',        -- New equipment commissioning
        'ENGINEERING'           -- Engineering services
    )),
    
    -- Status & Stage
    status TEXT DEFAULT 'NOT_STARTED' CHECK (status IN (
        'NOT_STARTED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED'
    )),
    
    -- Dates
    order_date DATE,
    start_date DATE,
    target_completion_date DATE,
    actual_completion_date DATE,
    
    -- Team
    project_manager_id UUID REFERENCES employees(id),
    lead_technician_id UUID REFERENCES employees(id),
    
    -- Financial
    budget DECIMAL(12, 2),
    po_number TEXT,
    po_amount DECIMAL(12, 2),
    po_date DATE,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3.2 PROJECT TEAM ASSIGNMENTS
CREATE TABLE project_team (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    
    role TEXT NOT NULL,                  -- "Lead", "Technician", "PM", "Engineer"
    assigned_date DATE DEFAULT CURRENT_DATE,
    removed_date DATE,
    
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(project_id, employee_id, role)
);

-- 3.3 SCOPES (Deliverables within Field Testing Projects)
CREATE TABLE scopes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Identity
    scope_number TEXT NOT NULL,          -- "1.0", "2.0"
    name TEXT NOT NULL,
    description TEXT,
    
    -- NETA Standard
    neta_standard TEXT CHECK (neta_standard IN ('ATS', 'MTS')),
    
    -- Status
    status TEXT DEFAULT 'NOT_STARTED' CHECK (status IN (
        'NOT_STARTED', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CANCELLED'
    )),
    
    -- Financial
    budget DECIMAL(12, 2),
    multiplier DECIMAL(5, 3) DEFAULT 1.000,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(project_id, scope_number)
);

-- 3.4 SCOPE LABOR RATES
CREATE TABLE scope_labor_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID REFERENCES scopes(id) ON DELETE CASCADE UNIQUE,
    
    -- Tech Labor
    tech_bill_rate DECIMAL(8, 2),
    tech_percent DECIMAL(5, 2),
    
    -- PM Labor
    pm_bill_rate DECIMAL(8, 2),
    pm_percent DECIMAL(5, 2),
    
    -- Report Writing
    report_bill_rate DECIMAL(8, 2),
    report_percent DECIMAL(5, 2),
    
    -- Travel
    travel_bill_rate DECIMAL(8, 2),
    travel_percent DECIMAL(5, 2),
    
    -- Effective Rate (calculated)
    effective_labor_rate DECIMAL(8, 2) GENERATED ALWAYS AS (
        COALESCE(tech_bill_rate * tech_percent / 100, 0) +
        COALESCE(pm_bill_rate * pm_percent / 100, 0) +
        COALESCE(report_bill_rate * report_percent / 100, 0) +
        COALESCE(travel_bill_rate * travel_percent / 100, 0)
    ) STORED,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3.5 APPARATUS TYPES (Master List)
CREATE TABLE apparatus_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    name TEXT NOT NULL UNIQUE,
    category TEXT,                       -- "Switchgear", "Transformer", "Cable"
    neta_section TEXT,                   -- NETA reference section
    
    -- Default Values
    default_hours DECIMAL(6, 2),
    default_priority TEXT DEFAULT 'MEDIUM',
    
    -- Metadata
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3.6 TASKS (Work Items within Scopes)
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope_id UUID REFERENCES scopes(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES tasks(id),
    
    -- Identity
    task_id TEXT NOT NULL,               -- "1.1.1", "1.1.2"
    name TEXT NOT NULL,
    
    -- Apparatus
    apparatus_type_id UUID REFERENCES apparatus_types(id),
    designation TEXT,                    -- Equipment designation
    drawing TEXT,                        -- Drawing reference
    
    -- Status
    status TEXT DEFAULT 'NOT_STARTED' CHECK (status IN (
        'NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD', 'SKIPPED'
    )),
    availability TEXT DEFAULT 'READY' CHECK (availability IN (
        'READY', 'ON_HOLD', 'NOT_AVAILABLE'
    )),
    priority TEXT DEFAULT 'MEDIUM' CHECK (priority IN (
        'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    )),
    percent_complete DECIMAL(5, 2) DEFAULT 0 
        CHECK (percent_complete >= 0 AND percent_complete <= 100),
    
    -- Dates
    date_due DATE,
    date_completed DATE,
    
    -- Hours
    apparatus_hours DECIMAL(6, 2),
    actual_hours DECIMAL(6, 2),
    
    -- Results
    assessment TEXT CHECK (assessment IN (
        'ACCEPTABLE', 'MINOR_DEFICIENCY', 'MAJOR_DEFICIENCY', 'NON_SERVICEABLE'
    )),
    datasheet TEXT CHECK (datasheet IN ('YES', 'NO', 'N/A')),
    
    -- Delay Tracking
    delay_hours DECIMAL(6, 2) DEFAULT 0,
    delay_reason TEXT,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(scope_id, task_id)
);

-- 3.7 APPARATUS REVENUE (Revenue Recognition per Task)
CREATE TABLE apparatus_revenue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE UNIQUE,
    
    -- Source Data
    apparatus_hours DECIMAL(6, 2),
    delay_hours DECIMAL(6, 2) DEFAULT 0,
    effective_labor_rate DECIMAL(8, 2),
    
    -- Calculated Revenue
    base_revenue DECIMAL(12, 2) GENERATED ALWAYS AS (
        apparatus_hours * effective_labor_rate
    ) STORED,
    delay_adjustment DECIMAL(12, 2) GENERATED ALWAYS AS (
        delay_hours * effective_labor_rate
    ) STORED,
    total_revenue DECIMAL(12, 2) GENERATED ALWAYS AS (
        (apparatus_hours - COALESCE(delay_hours, 0)) * effective_labor_rate
    ) STORED,
    
    -- Status
    revenue_status TEXT DEFAULT 'PENDING' CHECK (revenue_status IN (
        'PENDING', 'RECOGNIZED', 'INVOICED', 'PAID', 'ADJUSTED'
    )),
    
    -- Dates
    recognition_date DATE,
    invoice_date DATE,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SECTION 4: PSS PORTAL (Power System Studies)
-- ============================================================================

-- 4.1 ENGINEERS (External Engineering Vendors)
CREATE TABLE engineers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    company_name TEXT NOT NULL,
    code TEXT UNIQUE,                    -- "SHAW"
    
    -- Contact
    address TEXT,
    city TEXT,
    state TEXT,
    phone TEXT,
    email TEXT,
    
    -- Sharing
    dropbox_link TEXT,
    shared_folder_path TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    accepts_new_projects BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add FK for contacts.engineer_id
ALTER TABLE contacts ADD CONSTRAINT fk_contacts_engineer 
    FOREIGN KEY (engineer_id) REFERENCES engineers(id) ON DELETE SET NULL;

-- 4.2 PSS STUDIES (Linked to Projects)
CREATE TABLE pss_studies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    
    -- Assignment
    engineer_id UUID REFERENCES engineers(id),
    
    -- Study Details
    study_type TEXT NOT NULL CHECK (study_type IN (
        'PSS', 'ARC_FLASH', 'PSS_ARC_FLASH', 'COORDINATION'
    )),
    
    -- Status (PSS-specific workflow)
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
    data_collection_by TEXT CHECK (data_collection_by IN (
        'RESA', 'CLIENT', 'ENGINEER'
    )),
    stickers_by TEXT CHECK (stickers_by IN (
        'RESA', 'CLIENT', 'ENGINEER', 'N/A'
    )),
    
    -- Key Dates
    target_report_date DATE,
    report_sent_date DATE,
    report_approved_date DATE,
    stickers_applied_date DATE,
    
    -- Status Tracking
    last_status_change TIMESTAMPTZ DEFAULT NOW(),
    days_in_current_status INTEGER GENERATED ALWAYS AS (
        EXTRACT(DAY FROM (NOW() - last_status_change))::INTEGER
    ) STORED,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.3 DOCUMENT TEMPLATES (Master Checklist)
CREATE TABLE document_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity
    name TEXT NOT NULL,
    description TEXT,
    
    -- Applicability
    study_types TEXT[] NOT NULL,         -- {"PSS", "ARC_FLASH"}
    is_required BOOLEAN DEFAULT TRUE,
    
    -- Guidance
    example_notes TEXT,
    
    -- Display
    sort_order INTEGER DEFAULT 0,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.4 PSS DOCUMENTS (Per-Study Document Tracking)
CREATE TABLE pss_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pss_study_id UUID REFERENCES pss_studies(id) ON DELETE CASCADE,
    template_id UUID REFERENCES document_templates(id),
    
    -- Document Details
    document_name TEXT,
    filename TEXT,
    file_url TEXT,
    
    -- Status
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
    
    -- Tracking
    days_outstanding INTEGER GENERATED ALWAYS AS (
        CASE WHEN status = 'REQUESTED' AND requested_date IS NOT NULL
             THEN EXTRACT(DAY FROM (NOW() - requested_date))::INTEGER
             ELSE NULL
        END
    ) STORED,
    
    -- Metadata
    notes TEXT,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.5 RFIs (Requests for Information)
CREATE TABLE rfis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pss_study_id UUID REFERENCES pss_studies(id) ON DELETE CASCADE,
    
    -- Identity
    rfi_number TEXT NOT NULL,            -- "RFI-629266-001"
    
    -- Content
    subject TEXT NOT NULL,
    question TEXT NOT NULL,
    related_document_id UUID REFERENCES pss_documents(id),
    
    -- Status
    priority TEXT DEFAULT 'MEDIUM' CHECK (priority IN (
        'LOW', 'MEDIUM', 'HIGH', 'URGENT'
    )),
    status TEXT DEFAULT 'OPEN' CHECK (status IN (
        'OPEN', 'RESPONDED', 'CLOSED'
    )),
    
    -- Submission
    submitted_by_contact_id UUID REFERENCES contacts(id),
    submitted_date TIMESTAMPTZ DEFAULT NOW(),
    
    -- Response
    response TEXT,
    response_by_contact_id UUID REFERENCES contacts(id),
    response_date TIMESTAMPTZ,
    response_attachments TEXT[],
    
    -- Tracking
    days_open INTEGER GENERATED ALWAYS AS (
        CASE WHEN status = 'OPEN'
             THEN EXTRACT(DAY FROM (NOW() - submitted_date))::INTEGER
             ELSE NULL
        END
    ) STORED,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4.6 ACTIVITY LOG (Communication History)
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- References (polymorphic - link to various entities)
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
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SECTION 5: SCHEDULING & TIME TRACKING
-- ============================================================================

-- 5.1 SCHEDULES (Dispatching)
CREATE TABLE schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    scope_id UUID REFERENCES scopes(id),
    
    -- Schedule Details
    scheduled_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    
    -- Assignment
    lead_employee_id UUID REFERENCES employees(id),
    
    -- Status
    status TEXT DEFAULT 'SCHEDULED' CHECK (status IN (
        'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'RESCHEDULED'
    )),
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5.2 SCHEDULE CREW ASSIGNMENTS
CREATE TABLE schedule_crew (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schedule_id UUID REFERENCES schedules(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    
    role TEXT,                           -- "Lead", "Technician", "Helper"
    confirmed BOOLEAN DEFAULT FALSE,
    
    UNIQUE(schedule_id, employee_id)
);

-- 5.3 SCHEDULE EQUIPMENT ASSIGNMENTS
CREATE TABLE schedule_equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schedule_id UUID REFERENCES schedules(id) ON DELETE CASCADE,
    equipment_id UUID REFERENCES equipment(id) ON DELETE CASCADE,
    
    checked_out BOOLEAN DEFAULT FALSE,
    checked_out_date TIMESTAMPTZ,
    returned BOOLEAN DEFAULT FALSE,
    returned_date TIMESTAMPTZ,
    
    UNIQUE(schedule_id, equipment_id)
);

-- 5.4 TIME ENTRIES
CREATE TABLE time_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- References
    project_id UUID REFERENCES projects(id),
    scope_id UUID REFERENCES scopes(id),
    task_id UUID REFERENCES tasks(id),
    schedule_id UUID REFERENCES schedules(id),
    
    -- Employee
    employee_id UUID REFERENCES employees(id) NOT NULL,
    
    -- Time
    entry_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    hours DECIMAL(5, 2) NOT NULL,
    
    -- Classification
    entry_type TEXT NOT NULL CHECK (entry_type IN (
        'LABOR', 'TRAVEL', 'PM', 'REPORT_WRITING', 'TRAINING', 'ADMIN'
    )),
    billable BOOLEAN DEFAULT TRUE,
    
    -- Approval
    status TEXT DEFAULT 'PENDING' CHECK (status IN (
        'PENDING', 'APPROVED', 'REJECTED', 'INVOICED'
    )),
    approved_by_id UUID REFERENCES employees(id),
    approved_date TIMESTAMPTZ,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5.5 EXPENSES
CREATE TABLE expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- References
    project_id UUID REFERENCES projects(id),
    scope_id UUID REFERENCES scopes(id),
    schedule_id UUID REFERENCES schedules(id),
    
    -- Employee
    employee_id UUID REFERENCES employees(id) NOT NULL,
    
    -- Expense Details
    expense_date DATE NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'HOTEL', 'MEALS', 'PER_DIEM', 'MILEAGE', 'FUEL',
        'RENTAL_CAR', 'AIRFARE', 'PARKING', 'TOLLS', 
        'EQUIPMENT', 'SUPPLIES', 'OTHER'
    )),
    amount DECIMAL(10, 2) NOT NULL,
    description TEXT,
    
    -- Mileage-specific
    miles DECIMAL(8, 2),
    mileage_rate DECIMAL(4, 3),
    
    -- Receipt
    receipt_url TEXT,
    
    -- Reimbursement
    billable BOOLEAN DEFAULT TRUE,
    reimbursable BOOLEAN DEFAULT TRUE,
    status TEXT DEFAULT 'PENDING' CHECK (status IN (
        'PENDING', 'APPROVED', 'REJECTED', 'REIMBURSED'
    )),
    
    -- Approval
    approved_by_id UUID REFERENCES employees(id),
    approved_date TIMESTAMPTZ,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SECTION 6: PORTAL USERS & ACCESS CONTROL
-- ============================================================================

-- 6.1 PORTAL USERS
CREATE TABLE portal_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Auth
    email TEXT UNIQUE NOT NULL,
    auth_user_id UUID UNIQUE,            -- Links to Supabase auth.users
    
    -- Links
    contact_id UUID REFERENCES contacts(id),
    employee_id UUID REFERENCES employees(id),
    
    -- Role
    role TEXT NOT NULL CHECK (role IN (
        'RESA_ADMIN', 'RESA_STAFF', 'CLIENT', 'ENGINEER'
    )),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_user_id UUID REFERENCES portal_users(id)
);

-- Add FK back to contacts
ALTER TABLE contacts ADD CONSTRAINT fk_contacts_portal_user 
    FOREIGN KEY (portal_user_id) REFERENCES portal_users(id);

-- ============================================================================
-- SECTION 7: INDEXES FOR PERFORMANCE
-- ============================================================================

-- Core lookups
CREATE INDEX idx_projects_client ON projects(client_id);
CREATE INDEX idx_projects_site ON projects(site_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_number ON projects(project_number);

CREATE INDEX idx_scopes_project ON scopes(project_id);
CREATE INDEX idx_tasks_scope ON tasks(scope_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_task_id ON tasks(task_id);

-- PSS Portal
CREATE INDEX idx_pss_studies_project ON pss_studies(project_id);
CREATE INDEX idx_pss_studies_engineer ON pss_studies(engineer_id);
CREATE INDEX idx_pss_studies_status ON pss_studies(pss_status);
CREATE INDEX idx_pss_documents_study ON pss_documents(pss_study_id);
CREATE INDEX idx_pss_documents_status ON pss_documents(status);
CREATE INDEX idx_rfis_study ON rfis(pss_study_id);
CREATE INDEX idx_rfis_status ON rfis(status);

-- Time & Expenses
CREATE INDEX idx_time_entries_employee ON time_entries(employee_id);
CREATE INDEX idx_time_entries_date ON time_entries(entry_date);
CREATE INDEX idx_time_entries_project ON time_entries(project_id);
CREATE INDEX idx_expenses_employee ON expenses(employee_id);
CREATE INDEX idx_expenses_date ON expenses(expense_date);

-- Equipment & Fleet
CREATE INDEX idx_equipment_category ON equipment(category_id);
CREATE INDEX idx_equipment_status ON equipment(status);
CREATE INDEX idx_employee_certs_employee ON employee_certifications(employee_id);
CREATE INDEX idx_vehicle_maintenance_vehicle ON vehicle_maintenance(vehicle_id);

-- Activity Log
CREATE INDEX idx_activity_log_project ON activity_log(project_id);
CREATE INDEX idx_activity_log_created ON activity_log(created_at DESC);

-- Full-text search
CREATE INDEX idx_projects_name_search ON projects USING gin(to_tsvector('english', name));
CREATE INDEX idx_clients_name_search ON clients USING gin(to_tsvector('english', name));

-- ============================================================================
-- SECTION 8: ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on sensitive tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE scopes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE pss_studies ENABLE ROW LEVEL SECURITY;
ALTER TABLE pss_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE rfis ENABLE ROW LEVEL SECURITY;
ALTER TABLE time_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;

-- Example policies (expand based on your auth model)

-- RESA Admin/Staff can see everything
CREATE POLICY "RESA staff full access" ON projects
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM portal_users pu
            WHERE pu.auth_user_id = auth.uid()
            AND pu.role IN ('RESA_ADMIN', 'RESA_STAFF')
        )
    );

-- Clients can only see their own projects
CREATE POLICY "Clients see own projects" ON projects
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM portal_users pu
            JOIN contacts c ON c.portal_user_id = pu.id
            WHERE pu.auth_user_id = auth.uid()
            AND pu.role = 'CLIENT'
            AND c.client_id = projects.client_id
        )
    );

-- Engineers see assigned projects
CREATE POLICY "Engineers see assigned projects" ON pss_studies
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM portal_users pu
            JOIN contacts c ON c.portal_user_id = pu.id
            WHERE pu.auth_user_id = auth.uid()
            AND pu.role = 'ENGINEER'
            AND c.engineer_id = pss_studies.engineer_id
        )
    );

-- ============================================================================
-- SECTION 9: USEFUL VIEWS
-- ============================================================================

-- Project Dashboard Summary
CREATE VIEW v_project_dashboard AS
SELECT 
    p.id,
    p.project_number,
    p.name AS project_name,
    p.project_type,
    p.status,
    c.name AS client_name,
    s.name AS site_name,
    pm.full_name AS project_manager,
    p.order_date,
    p.target_completion_date,
    p.budget,
    p.po_amount,
    COALESCE(scope_count.cnt, 0) AS scope_count,
    COALESCE(task_stats.total_tasks, 0) AS total_tasks,
    COALESCE(task_stats.completed_tasks, 0) AS completed_tasks,
    CASE WHEN COALESCE(task_stats.total_tasks, 0) > 0 
         THEN ROUND(task_stats.completed_tasks::DECIMAL / task_stats.total_tasks * 100, 1)
         ELSE 0 
    END AS percent_complete
FROM projects p
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN sites s ON p.site_id = s.id
LEFT JOIN employees pm ON p.project_manager_id = pm.id
LEFT JOIN (
    SELECT project_id, COUNT(*) AS cnt
    FROM scopes
    GROUP BY project_id
) scope_count ON p.id = scope_count.project_id
LEFT JOIN (
    SELECT sc.project_id,
           COUNT(t.id) AS total_tasks,
           COUNT(t.id) FILTER (WHERE t.status = 'COMPLETED') AS completed_tasks
    FROM scopes sc
    LEFT JOIN tasks t ON t.scope_id = sc.id
    GROUP BY sc.project_id
) task_stats ON p.id = task_stats.project_id;

-- PSS Portal Dashboard
CREATE VIEW v_pss_dashboard AS
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
    COALESCE(doc_stats.total_docs, 0) AS total_documents,
    COALESCE(doc_stats.received_docs, 0) AS received_documents,
    COALESCE(doc_stats.outstanding_docs, 0) AS outstanding_documents,
    COALESCE(rfi_stats.open_rfis, 0) AS open_rfis
FROM pss_studies ps
JOIN projects p ON ps.project_id = p.id
LEFT JOIN clients c ON p.client_id = c.id
LEFT JOIN engineers e ON ps.engineer_id = e.id
LEFT JOIN (
    SELECT pss_study_id,
           COUNT(*) AS total_docs,
           COUNT(*) FILTER (WHERE status IN ('RECEIVED', 'ACCEPTED')) AS received_docs,
           COUNT(*) FILTER (WHERE status = 'REQUESTED') AS outstanding_docs
    FROM pss_documents
    GROUP BY pss_study_id
) doc_stats ON ps.id = doc_stats.pss_study_id
LEFT JOIN (
    SELECT pss_study_id,
           COUNT(*) FILTER (WHERE status = 'OPEN') AS open_rfis
    FROM rfis
    GROUP BY pss_study_id
) rfi_stats ON ps.id = rfi_stats.pss_study_id;

-- Employee Availability View
CREATE VIEW v_employee_availability AS
SELECT 
    e.id,
    e.full_name,
    e.title,
    e.skill_level,
    e.is_active,
    COALESCE(today_schedule.scheduled_today, FALSE) AS scheduled_today,
    today_schedule.project_name AS todays_project,
    COALESCE(cert_status.active_certs, 0) AS active_certifications,
    COALESCE(cert_status.expiring_soon, 0) AS certs_expiring_30_days
FROM employees e
LEFT JOIN (
    SELECT sc.lead_employee_id AS employee_id,
           TRUE AS scheduled_today,
           p.name AS project_name
    FROM schedules sc
    JOIN projects p ON sc.project_id = p.id
    WHERE sc.scheduled_date = CURRENT_DATE
    AND sc.status = 'SCHEDULED'
) today_schedule ON e.id = today_schedule.employee_id
LEFT JOIN (
    SELECT employee_id,
           COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active_certs,
           COUNT(*) FILTER (WHERE expiration_date BETWEEN CURRENT_DATE AND CURRENT_DATE + 30) AS expiring_soon
    FROM employee_certifications
    GROUP BY employee_id
) cert_status ON e.id = cert_status.employee_id
WHERE e.is_active = TRUE;

-- Equipment Due for Calibration
CREATE VIEW v_equipment_calibration_due AS
SELECT 
    eq.id,
    eq.asset_tag,
    eq.name,
    eq.equipment_type,
    eq.manufacturer,
    eq.model,
    eq.last_calibration_date,
    eq.next_calibration_date,
    eq.next_calibration_date - CURRENT_DATE AS days_until_due,
    eq.status,
    emp.full_name AS assigned_to
FROM equipment eq
LEFT JOIN employees emp ON eq.assigned_to_employee_id = emp.id
WHERE eq.requires_calibration = TRUE
AND eq.is_active = TRUE
AND eq.next_calibration_date IS NOT NULL
ORDER BY eq.next_calibration_date;
```

---

## 4. Summary: Table Count by Category

| Category | Tables | Purpose |
|----------|--------|---------|
| **Organization** | 6 | Clients, Sites, Contacts, Employees, Certs, Training |
| **Equipment & Fleet** | 5 | Equipment, Categories, Calibrations, Vehicles, Maintenance |
| **Projects & Work** | 7 | Projects, Team, Scopes, Labor Rates, Apparatus Types, Tasks, Revenue |
| **PSS Portal** | 6 | Engineers, Studies, Document Templates, Documents, RFIs, Activity Log |
| **Scheduling** | 5 | Schedules, Crew, Equipment Assignments, Time Entries, Expenses |
| **Access Control** | 1 | Portal Users |
| **TOTAL** | **30 tables** | |

---

## 5. Implementation Recommendation

### Phase 1: Core Foundation (Week 1-2)
- Set up Supabase project
- Deploy schema sections 1-3 (Org, Equipment, Projects)
- Connect NocoDB for immediate CRUD interface
- Migrate existing Dataverse data

### Phase 2: PSS Portal (Week 3-4)
- Deploy schema section 4 (PSS tables)
- Build client/engineer portal UI (Softr, Retool, or custom)
- Implement email notifications (Supabase Edge Functions)

### Phase 3: Field Operations (Week 5-6)
- Deploy scheduling tables
- Build mobile-responsive field app
- Implement time entry and expense tracking

### Phase 4: Analytics & Polish (Week 7-8)
- Build dashboards and reports
- Implement automation rules
- User training and rollout
