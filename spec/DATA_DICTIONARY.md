# Data Dictionary

**Version:** 1.0.0  
**Created:** December 5, 2025  
**Author:** Desktop Claude  
**Purpose:** Complete field-level documentation for RESA Power Supabase schema

---

## Overview

This dictionary documents all 25 Phase 1 tables across 4 categories:
- **Core (10):** Business entities and project management
- **Financial (6):** Revenue tracking and cost management  
- **Reference (2):** Master data and templates
- **PSS Portal (6):** Power System Studies tracking (NEW)

Deferred to Phase 2: apparatus_submissions, apparatus_test_checklists, quotes

---

## Naming Conventions

| Pattern | PostgreSQL | Example |
|---------|------------|---------|
| Table names | snake_case, plural | `apparatus_types` |
| Column names | snake_case | `project_number` |
| Primary keys | `id` (UUID) | `id UUID PRIMARY KEY` |
| Foreign keys | `{table}_id` | `project_id` |
| Timestamps | `created_at`, `updated_at` | TIMESTAMPTZ |
| Booleans | `is_` prefix | `is_active` |
| Counts | `_count` suffix | `apparatus_count` |
| Percentages | `_percent` suffix | `percent_complete` |

---

## Category 1: Core Tables

### 1.1 locations
**Purpose:** RESA branch offices  
**Dataverse Source:** cr950_BusinessUnit  
**Record Count:** ~5-10 branches

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| location_name | VARCHAR(100) | NOT NULL | Branch name (e.g., "Fenton") |
| abbreviation | VARCHAR(10) | | Short code (e.g., "FEN") |
| code | VARCHAR(20) | | Location code |
| region | VARCHAR(50) | | Geographic region |
| manager | VARCHAR(100) | | Branch manager name |
| address | TEXT | | Street address |
| city | VARCHAR(100) | | City |
| state | VARCHAR(50) | | State/Province |
| zip | VARCHAR(20) | | Postal code |
| is_active | BOOLEAN | DEFAULT true | Soft delete flag |
| sort_order | INTEGER | DEFAULT 0 | Display ordering |
| notes | TEXT | | General notes |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 1.2 clients
**Purpose:** Customer companies  
**Dataverse Source:** cr950_Client  
**Record Count:** ~50-200 customers

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| client_name | VARCHAR(200) | NOT NULL | Company name |
| client_code | VARCHAR(50) | | Internal code |
| address | TEXT | | Street address |
| city | VARCHAR(100) | | City |
| state | VARCHAR(50) | | State/Province |
| zip | VARCHAR(20) | | Postal code |
| country | VARCHAR(100) | DEFAULT 'USA' | Country |
| phone | VARCHAR(50) | | Main phone |
| email | VARCHAR(255) | | Main email |
| website | VARCHAR(255) | | Company website |
| is_active | BOOLEAN | DEFAULT true | Soft delete flag |
| notes | TEXT | | General notes |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 1.3 sites
**Purpose:** Client facility locations  
**Dataverse Source:** cr950_Site  
**Relationship:** Many sites per client

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| client_id | UUID | FK → clients(id) ON DELETE CASCADE | Parent client |
| site_name | VARCHAR(200) | NOT NULL | Facility name |
| site_code | VARCHAR(50) | | Internal code |
| address | TEXT | | Street address |
| city | VARCHAR(100) | | City |
| state | VARCHAR(50) | | State/Province |
| zip | VARCHAR(20) | | Postal code |
| country | VARCHAR(100) | DEFAULT 'USA' | Country |
| contact_name | VARCHAR(100) | | Site contact person |
| contact_phone | VARCHAR(50) | | Contact phone |
| contact_email | VARCHAR(255) | | Contact email |
| is_active | BOOLEAN | DEFAULT true | Soft delete flag |
| notes | TEXT | | General notes |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 1.4 employees
**Purpose:** RESA staff members  
**Dataverse Source:** cr950_Employee  
**Record Count:** ~50-100 employees

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| employee_number | VARCHAR(50) | UNIQUE | HR employee ID |
| first_name | VARCHAR(100) | NOT NULL | First name |
| last_name | VARCHAR(100) | NOT NULL | Last name |
| email | VARCHAR(255) | | Work email |
| phone | VARCHAR(50) | | Work phone |
| location_id | UUID | FK → locations(id) | Home branch |
| job_title | VARCHAR(100) | | Position title |
| department | VARCHAR(100) | | Department |
| role_type | VARCHAR(50) | | Role category (see ENUM) |
| hourly_rate | DECIMAL(10,2) | | Standard hourly rate |
| overtime_rate | DECIMAL(10,2) | | OT hourly rate |
| burden_rate | DECIMAL(5,2) | | Burden percentage |
| neta_certified | BOOLEAN | DEFAULT false | NETA certification status |
| neta_level | VARCHAR(20) | | NETA level (I, II, III, IV) |
| certification_expiry | DATE | | Cert expiration date |
| hire_date | DATE | | Employment start |
| termination_date | DATE | | Employment end (if applicable) |
| is_active | BOOLEAN | DEFAULT true | Currently employed |
| notes | TEXT | | General notes |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 1.5 projects
**Purpose:** Main work tracking entity  
**Dataverse Source:** cr950_Projects  
**Key Entity:** Central to all operations

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| project_number | VARCHAR(50) | NOT NULL, UNIQUE | Project ID (e.g., "LASNAP16") |
| project_name | VARCHAR(200) | NOT NULL | Descriptive name |
| client_id | UUID | FK → clients(id) | Customer |
| site_id | UUID | FK → sites(id) | Work location |
| location_id | UUID | FK → locations(id) | RESA branch |
| status | VARCHAR(50) | DEFAULT 'Draft' | Project status (see ENUM) |
| project_type | VARCHAR(100) | | Type classification |
| business_unit | VARCHAR(100) | | Business segment |
| quote_date | DATE | | Quote creation date |
| quote_revision | VARCHAR(20) | | Quote version |
| start_date | DATE | | Planned start |
| end_date | DATE | | Planned end |
| contract_value | DECIMAL(15,2) | | Total contract amount |
| po_number | VARCHAR(100) | | Customer PO |
| project_lead | VARCHAR(100) | | Lead technician/PM |
| estimator | VARCHAR(100) | | Quote creator |
| description | TEXT | | Project description |
| notes | TEXT | | General notes |
| is_active | BOOLEAN | DEFAULT true | Soft delete flag |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 1.6 scopes
**Purpose:** Project phases/work packages  
**Dataverse Source:** cr950_ProjectScope  
**Relationship:** Many scopes per project

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| project_id | UUID | NOT NULL, FK → projects(id) ON DELETE CASCADE | Parent project |
| client_id | UUID | FK → clients(id) | Client (denormalized) |
| site_id | UUID | FK → sites(id) | Site (denormalized) |
| scope_number | VARCHAR(50) | | Scope identifier |
| scope_name | VARCHAR(200) | NOT NULL | Scope description |
| scope_type | VARCHAR(100) | | Equipment category |
| status | VARCHAR(50) | DEFAULT 'Not Started' | Scope status (see ENUM) |
| percent_complete | DECIMAL(5,2) | DEFAULT 0 | Completion percentage |
| planned_start | DATE | | Scheduled start |
| planned_end | DATE | | Scheduled end |
| actual_start | DATE | | Real start date |
| actual_end | DATE | | Real end date |
| quoted_hours | DECIMAL(10,2) | | Budgeted hours |
| actual_hours | DECIMAL(10,2) | DEFAULT 0 | Hours worked |
| quoted_revenue | DECIMAL(15,2) | | Budgeted revenue |
| actual_revenue | DECIMAL(15,2) | DEFAULT 0 | Recognized revenue |
| labor_cost | DECIMAL(15,2) | DEFAULT 0 | Labor expense |
| sort_order | INTEGER | DEFAULT 0 | Display ordering |
| notes | TEXT | | General notes |
| is_active | BOOLEAN | DEFAULT true | Soft delete flag |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 1.7 tasks
**Purpose:** Work items within scopes  
**Dataverse Source:** cr950_Tasks  
**Relationship:** Many tasks per scope

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| scope_id | UUID | NOT NULL, FK → scopes(id) ON DELETE CASCADE | Parent scope |
| task_number | VARCHAR(50) | | Task identifier |
| task_name | VARCHAR(200) | NOT NULL | Task description |
| task_type | VARCHAR(100) | | Task category |
| status | VARCHAR(50) | DEFAULT 'Not Started' | Task status (see ENUM) |
| percent_complete | DECIMAL(5,2) | DEFAULT 0 | Completion percentage |
| planned_start | DATE | | Scheduled start |
| planned_end | DATE | | Scheduled end |
| actual_start | DATE | | Real start date |
| actual_end | DATE | | Real end date |
| estimated_hours | DECIMAL(10,2) | | Budgeted hours |
| actual_hours | DECIMAL(10,2) | DEFAULT 0 | Hours worked |
| parent_task_id | UUID | FK → tasks(id) | Parent task (hierarchy) |
| sort_order | INTEGER | DEFAULT 0 | Display ordering |
| description | TEXT | | Task description |
| notes | TEXT | | General notes |
| is_active | BOOLEAN | DEFAULT true | Soft delete flag |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 1.8 apparatus
**Purpose:** Equipment being tested  
**Dataverse Source:** cr950_Apparatus  
**Key Entity:** Revenue recognition driver

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| scope_id | UUID | NOT NULL, FK → scopes(id) ON DELETE CASCADE | Parent scope |
| task_id | UUID | FK → tasks(id) | Associated task |
| apparatus_designation | VARCHAR(100) | NOT NULL | Equipment ID (e.g., "ATS-01") |
| apparatus_name | VARCHAR(200) | | Descriptive name |
| apparatus_type | VARCHAR(100) | | Type from master |
| equipment_type | VARCHAR(100) | | Equipment category |
| manufacturer | VARCHAR(100) | | OEM |
| model | VARCHAR(100) | | Model number |
| serial_number | VARCHAR(100) | | Serial number |
| status | VARCHAR(50) | DEFAULT 'Not Started' | Testing status (see ENUM) |
| assessment | VARCHAR(50) | | Test result (see ENUM) |
| percent_complete | DECIMAL(5,2) | DEFAULT 0 | Completion percentage |
| anticipated_start | DATE | | Planned test date |
| actual_start | DATE | | Real start date |
| actual_end | DATE | | Real end date |
| quoted_hours | DECIMAL(10,2) | | Budgeted hours |
| actual_hours | DECIMAL(10,2) | DEFAULT 0 | Hours worked |
| quoted_revenue | DECIMAL(12,2) | | Budgeted revenue |
| actual_revenue | DECIMAL(12,2) | DEFAULT 0 | Recognized revenue |
| building | VARCHAR(100) | | Building location |
| floor | VARCHAR(50) | | Floor level |
| room | VARCHAR(100) | | Room/area |
| sort_order | INTEGER | DEFAULT 0 | Display ordering |
| notes | TEXT | | General notes |
| is_active | BOOLEAN | DEFAULT true | Soft delete flag |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 1.9 equipment
**Purpose:** Company-owned test equipment  
**Dataverse Source:** cr950_Equipment  
**Relationship:** Assigned to employees/locations

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| equipment_number | VARCHAR(50) | UNIQUE | Asset tag |
| equipment_name | VARCHAR(200) | NOT NULL | Equipment name |
| category | VARCHAR(100) | | Equipment category |
| manufacturer | VARCHAR(100) | | OEM |
| model | VARCHAR(100) | | Model number |
| serial_number | VARCHAR(100) | | Serial number |
| location_id | UUID | FK → locations(id) | Home location |
| assigned_employee_id | UUID | FK → employees(id) | Current assignee |
| status | VARCHAR(50) | DEFAULT 'Available' | Availability status |
| calibration_date | DATE | | Last calibration |
| calibration_due | DATE | | Next calibration due |
| purchase_date | DATE | | Acquisition date |
| purchase_cost | DECIMAL(12,2) | | Original cost |
| daily_rate | DECIMAL(10,2) | | Internal charge rate |
| notes | TEXT | | General notes |
| is_active | BOOLEAN | DEFAULT true | Soft delete flag |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 1.10 resource_assignments
**Purpose:** Employee-to-project assignments  
**Dataverse Source:** cr950_ResourceAssignment  
**Relationship:** Links employees to projects/scopes

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| employee_id | UUID | NOT NULL, FK → employees(id) | Assigned employee |
| project_id | UUID | FK → projects(id) | Assigned project |
| scope_id | UUID | FK → scopes(id) | Assigned scope |
| assignment_type | VARCHAR(50) | | Role on assignment |
| start_date | DATE | | Assignment start |
| end_date | DATE | | Assignment end |
| allocated_hours | DECIMAL(10,2) | | Planned hours |
| actual_hours | DECIMAL(10,2) | DEFAULT 0 | Hours worked |
| is_primary | BOOLEAN | DEFAULT false | Primary resource flag |
| notes | TEXT | | General notes |
| is_active | BOOLEAN | DEFAULT true | Active assignment |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

## Category 2: Financial Tables

### 2.1 estimators
**Purpose:** Quote creators and rate configuration  
**Dataverse Source:** cr950_estimator

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| estimator_name | VARCHAR(100) | NOT NULL | Estimator name |
| email | VARCHAR(255) | | Email address |
| phone | VARCHAR(50) | | Phone number |
| location_id | UUID | FK → locations(id) | Home branch |
| is_active | BOOLEAN | DEFAULT true | Active status |
| notes | TEXT | | General notes |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 2.2 apparatus_revenue
**Purpose:** Detailed revenue recognition per apparatus  
**Dataverse Source:** cr950_ApparatusRevenue  
**Trigger:** Created on apparatus completion

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| apparatus_id | UUID | NOT NULL, FK → apparatus(id) ON DELETE CASCADE | Parent apparatus |
| scope_id | UUID | FK → scopes(id) | Parent scope (denormalized) |
| revenue_type | VARCHAR(100) | | Category (Testing, Travel, etc.) |
| quoted_amount | DECIMAL(12,2) | | Budgeted amount |
| recognized_amount | DECIMAL(12,2) | DEFAULT 0 | Actual revenue |
| recognition_date | DATE | | When recognized |
| recognition_percent | DECIMAL(5,2) | DEFAULT 0 | % of quoted |
| notes | TEXT | | General notes |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 2.3 scope_labor_details
**Purpose:** Labor line items per scope  
**Dataverse Source:** cr950_scopelabordetails

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| scope_id | UUID | NOT NULL, FK → scopes(id) ON DELETE CASCADE | Parent scope |
| labor_category | VARCHAR(100) | | Role category |
| labor_description | VARCHAR(200) | | Line item description |
| quoted_hours | DECIMAL(10,2) | | Budgeted hours |
| actual_hours | DECIMAL(10,2) | DEFAULT 0 | Hours worked |
| rate | DECIMAL(10,2) | | Hourly rate |
| cost | DECIMAL(12,2) | DEFAULT 0 | Total cost |
| notes | TEXT | | General notes |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 2.4 scope_financial_summaries
**Purpose:** Aggregated scope-level financials  
**Dataverse Source:** cr950_scopefinancialsummary  
**Trigger:** Updated on child record changes

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| scope_id | UUID | UNIQUE, NOT NULL, FK → scopes(id) ON DELETE CASCADE | Parent scope |
| total_quoted_revenue | DECIMAL(15,2) | DEFAULT 0 | Budgeted revenue |
| total_recognized_revenue | DECIMAL(15,2) | DEFAULT 0 | Actual revenue |
| revenue_recognition_percent | DECIMAL(5,2) | DEFAULT 0 | % recognized |
| total_quoted_hours | DECIMAL(10,2) | DEFAULT 0 | Budgeted hours |
| total_actual_hours | DECIMAL(10,2) | DEFAULT 0 | Hours worked |
| hours_variance | DECIMAL(10,2) | DEFAULT 0 | Over/under hours |
| total_labor_cost | DECIMAL(15,2) | DEFAULT 0 | Labor expense |
| total_expense_cost | DECIMAL(15,2) | DEFAULT 0 | Other expenses |
| gross_margin | DECIMAL(15,2) | DEFAULT 0 | Revenue - Cost |
| gross_margin_percent | DECIMAL(5,2) | DEFAULT 0 | Margin % |
| last_calculated_at | TIMESTAMPTZ | DEFAULT NOW() | Last recalc |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 2.5 project_financial_summaries
**Purpose:** Aggregated project-level financials  
**Dataverse Source:** cr950_projectfinancialsummary  
**Trigger:** Updated on scope changes

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| project_id | UUID | UNIQUE, NOT NULL, FK → projects(id) ON DELETE CASCADE | Parent project |
| total_quoted_revenue | DECIMAL(15,2) | DEFAULT 0 | Budgeted revenue |
| total_recognized_revenue | DECIMAL(15,2) | DEFAULT 0 | Actual revenue |
| revenue_recognition_percent | DECIMAL(5,2) | DEFAULT 0 | % recognized |
| total_quoted_hours | DECIMAL(10,2) | DEFAULT 0 | Budgeted hours |
| total_actual_hours | DECIMAL(10,2) | DEFAULT 0 | Hours worked |
| total_labor_cost | DECIMAL(15,2) | DEFAULT 0 | Labor expense |
| total_expense_cost | DECIMAL(15,2) | DEFAULT 0 | Other expenses |
| total_cost | DECIMAL(15,2) | DEFAULT 0 | All costs |
| gross_margin | DECIMAL(15,2) | DEFAULT 0 | Revenue - Cost |
| gross_margin_percent | DECIMAL(5,2) | DEFAULT 0 | Margin % |
| total_scopes | INTEGER | DEFAULT 0 | Scope count |
| completed_scopes | INTEGER | DEFAULT 0 | Completed scope count |
| last_calculated_at | TIMESTAMPTZ | DEFAULT NOW() | Last recalc |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 2.6 neta_test_templates
**Purpose:** Standard NETA test procedures  
**Dataverse Source:** cr950_netatesttemplate  
**Used By:** Apparatus testing workflow

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| template_code | VARCHAR(50) | NOT NULL | Template identifier |
| template_name | VARCHAR(200) | NOT NULL | Template name |
| apparatus_type | VARCHAR(100) | | Applicable equipment type |
| test_category | VARCHAR(100) | | Test category |
| description | TEXT | | Procedure description |
| estimated_hours | DECIMAL(10,2) | | Default hours |
| is_active | BOOLEAN | DEFAULT true | Active template |
| sort_order | INTEGER | DEFAULT 0 | Display ordering |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

## Category 3: Reference Tables

### 3.1 apparatus_types
**Purpose:** Equipment type master list  
**Dataverse Source:** cr950_ApparatusTypeMaster  
**Used By:** Apparatus type selection

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| type_code | VARCHAR(50) | NOT NULL, UNIQUE | Type code |
| type_name | VARCHAR(100) | NOT NULL | Type name |
| category | VARCHAR(100) | | Equipment category |
| default_hours | DECIMAL(10,2) | | Standard hours |
| default_rate | DECIMAL(10,2) | | Standard rate |
| description | TEXT | | Type description |
| is_active | BOOLEAN | DEFAULT true | Active type |
| sort_order | INTEGER | DEFAULT 0 | Display ordering |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

## Category 4: PSS Portal Tables (NEW)

### 4.1 pss_studies
**Purpose:** Power System Studies tracking  
**Dataverse Source:** N/A (NEW)  
**Key Entity:** PSS Portal primary entity

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| project_id | UUID | FK → projects(id) | Related project |
| study_number | VARCHAR(50) | NOT NULL | Study identifier |
| study_name | VARCHAR(200) | NOT NULL | Study name |
| study_type | VARCHAR(100) | | Type (see ENUM) |
| status | VARCHAR(50) | DEFAULT 'Pending' | Study status (see ENUM) |
| priority | VARCHAR(20) | | Priority level |
| engineer_id | UUID | FK → pss_engineers(id) | Lead engineer |
| requested_date | DATE | | Request date |
| due_date | DATE | | Target completion |
| completed_date | DATE | | Actual completion |
| description | TEXT | | Study description |
| notes | TEXT | | General notes |
| is_active | BOOLEAN | DEFAULT true | Active study |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 4.2 pss_engineers
**Purpose:** External PSS engineers  
**Dataverse Source:** N/A (NEW)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| engineer_name | VARCHAR(100) | NOT NULL | Full name |
| company | VARCHAR(200) | | Company/firm |
| email | VARCHAR(255) | | Email address |
| phone | VARCHAR(50) | | Phone number |
| specialization | VARCHAR(100) | | Area of expertise |
| pe_license | VARCHAR(50) | | PE license number |
| pe_state | VARCHAR(50) | | PE license state |
| is_active | BOOLEAN | DEFAULT true | Active status |
| notes | TEXT | | General notes |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 4.3 pss_documents
**Purpose:** Study documents  
**Dataverse Source:** N/A (NEW)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| study_id | UUID | NOT NULL, FK → pss_studies(id) ON DELETE CASCADE | Parent study |
| template_id | UUID | FK → pss_document_templates(id) | Template used |
| document_name | VARCHAR(200) | NOT NULL | Document name |
| document_type | VARCHAR(100) | | Document type (see ENUM) |
| version | VARCHAR(20) | | Version number |
| status | VARCHAR(50) | DEFAULT 'Draft' | Document status |
| file_path | TEXT | | Storage location |
| file_size | INTEGER | | Size in bytes |
| uploaded_by | UUID | FK → employees(id) | Uploader |
| uploaded_at | TIMESTAMPTZ | | Upload timestamp |
| notes | TEXT | | General notes |
| is_active | BOOLEAN | DEFAULT true | Active document |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 4.4 pss_document_templates
**Purpose:** Document templates for PSS  
**Dataverse Source:** N/A (NEW)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| template_code | VARCHAR(50) | NOT NULL | Template code |
| template_name | VARCHAR(200) | NOT NULL | Template name |
| document_type | VARCHAR(100) | | Document category |
| file_path | TEXT | | Template location |
| description | TEXT | | Template description |
| is_active | BOOLEAN | DEFAULT true | Active template |
| sort_order | INTEGER | DEFAULT 0 | Display ordering |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 4.5 pss_rfis
**Purpose:** Requests for Information  
**Dataverse Source:** N/A (NEW)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| study_id | UUID | NOT NULL, FK → pss_studies(id) ON DELETE CASCADE | Parent study |
| rfi_number | VARCHAR(50) | NOT NULL | RFI identifier |
| subject | VARCHAR(200) | NOT NULL | RFI subject |
| question | TEXT | | Question text |
| response | TEXT | | Response text |
| status | VARCHAR(50) | DEFAULT 'Open' | RFI status (see ENUM) |
| priority | VARCHAR(20) | | Priority level |
| requested_by | UUID | FK → employees(id) | Requester |
| assigned_to | UUID | FK → employees(id) | Assignee |
| requested_date | DATE | | Request date |
| due_date | DATE | | Response due |
| responded_date | DATE | | Response date |
| notes | TEXT | | General notes |
| is_active | BOOLEAN | DEFAULT true | Active RFI |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last modification |

---

### 4.6 pss_activity_log
**Purpose:** Audit trail for PSS portal  
**Dataverse Source:** N/A (NEW)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | Unique identifier |
| study_id | UUID | FK → pss_studies(id) ON DELETE CASCADE | Related study |
| activity_type | VARCHAR(50) | NOT NULL | Activity type (see ENUM) |
| activity_description | TEXT | | Description |
| entity_type | VARCHAR(50) | | Affected entity type |
| entity_id | UUID | | Affected entity ID |
| old_value | TEXT | | Previous value |
| new_value | TEXT | | New value |
| performed_by | UUID | FK → employees(id) | Actor |
| performed_at | TIMESTAMPTZ | DEFAULT NOW() | When performed |
| ip_address | VARCHAR(50) | | Client IP |
| user_agent | TEXT | | Browser info |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |

---

## Index Reference

| Index Name | Table | Columns | Purpose |
|------------|-------|---------|---------|
| idx_sites_client | sites | client_id | Client site lookup |
| idx_projects_client | projects | client_id | Client projects |
| idx_projects_site | projects | site_id | Site projects |
| idx_projects_location | projects | location_id | Branch projects |
| idx_projects_status | projects | status | Status filtering |
| idx_scopes_project | scopes | project_id | Project scopes |
| idx_tasks_scope | tasks | scope_id | Scope tasks |
| idx_apparatus_scope | apparatus | scope_id | Scope apparatus |
| idx_apparatus_task | apparatus | task_id | Task apparatus |
| idx_apparatus_revenue_apparatus | apparatus_revenue | apparatus_id | Revenue lookup |
| idx_scope_labor_scope | scope_labor_details | scope_id | Labor lookup |
| idx_employees_location | employees | location_id | Branch employees |
| idx_equipment_location | equipment | location_id | Branch equipment |
| idx_pss_studies_project | pss_studies | project_id | Project studies |
| idx_pss_documents_study | pss_documents | study_id | Study documents |
| idx_pss_rfis_study | pss_rfis | study_id | Study RFIs |
| idx_pss_activity_study | pss_activity_log | study_id | Study activity |

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-05 | Desktop Claude | Initial creation |

---

*Data Dictionary v1.0.0 | RESA Power Supabase Migration*
