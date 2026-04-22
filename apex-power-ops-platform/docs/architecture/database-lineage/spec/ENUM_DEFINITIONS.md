# ENUM Definitions

**Version:** 1.0.0  
**Created:** December 5, 2025  
**Author:** Desktop Claude  
**Purpose:** PostgreSQL ENUM type definitions for RESA Power schema

---

## Overview

ENUMs provide data integrity for status fields and categorical data. These replace Dataverse OptionSets with PostgreSQL native ENUM types.

**Benefits:**
- Database-level validation (no invalid values)
- Self-documenting (valid values visible in schema)
- Efficient storage (integers internally)
- Type safety in queries

---

## Project/Work Status ENUMs

### project_status
**Used By:** projects.status  
**Dataverse Source:** cr950_projectstatus OptionSet

```sql
CREATE TYPE project_status AS ENUM (
    'Draft',           -- Initial creation, not yet quoted
    'Quoted',          -- Quote sent to customer
    'Won',             -- Contract awarded
    'Active',          -- Work in progress
    'On Hold',         -- Temporarily paused
    'Complete',        -- All work finished
    'Cancelled'        -- Project cancelled
);
```

| Value | Description | Typical Next |
|-------|-------------|--------------|
| Draft | New project, preparing quote | Quoted |
| Quoted | Quote submitted | Won, Cancelled |
| Won | Contract signed | Active |
| Active | Work underway | Complete, On Hold |
| On Hold | Temporarily suspended | Active, Cancelled |
| Complete | All work done | - |
| Cancelled | Project cancelled | - |

---

### scope_status
**Used By:** scopes.status  
**Dataverse Source:** cr950_scopestatus OptionSet

```sql
CREATE TYPE scope_status AS ENUM (
    'Not Started',     -- Scope created, no work begun
    'In Progress',     -- Work actively underway
    'On Hold',         -- Temporarily paused
    'Complete',        -- All apparatus tested
    'Cancelled'        -- Scope cancelled
);
```

---

### task_status
**Used By:** tasks.status  
**Dataverse Source:** cr950_taskstatus OptionSet

```sql
CREATE TYPE task_status AS ENUM (
    'Not Started',     -- Task created, no work begun
    'In Progress',     -- Work actively underway
    'On Hold',         -- Temporarily paused
    'Complete',        -- Task finished
    'Cancelled'        -- Task cancelled
);
```

---

### apparatus_status
**Used By:** apparatus.status  
**Dataverse Source:** cr950_apparatusstatus OptionSet

```sql
CREATE TYPE apparatus_status AS ENUM (
    'Not Started',     -- Scheduled but not begun
    'In Progress',     -- Testing underway
    'Pending Review',  -- Testing done, awaiting review
    'Complete',        -- Testing complete, approved
    'Cancelled'        -- Testing cancelled
);
```

---

### apparatus_assessment
**Used By:** apparatus.assessment  
**Dataverse Source:** cr950_assessment OptionSet

```sql
CREATE TYPE apparatus_assessment AS ENUM (
    'Pass',            -- All tests passed
    'Fail',            -- Critical failures found
    'Marginal',        -- Minor issues, acceptable
    'Needs Repair',    -- Repairs required
    'Deferred',        -- Testing deferred
    'Not Tested'       -- Could not be tested
);
```

---

## Employee/Resource ENUMs

### role_type
**Used By:** employees.role_type  
**Dataverse Source:** cr950_roletype OptionSet

```sql
CREATE TYPE role_type AS ENUM (
    'Field Tech',      -- Field testing technician
    'Lead Tech',       -- Senior field technician
    'Engineer',        -- Engineering staff
    'Project Manager', -- PM role
    'Estimator',       -- Quote/estimation role
    'Admin',           -- Administrative staff
    'Executive'        -- Management
);
```

---

### neta_level
**Used By:** employees.neta_level  
**Dataverse Source:** cr950_netalevel OptionSet

```sql
CREATE TYPE neta_level AS ENUM (
    'Level I',         -- Entry level
    'Level II',        -- Intermediate
    'Level III',       -- Senior
    'Level IV'         -- Expert
);
```

---

### assignment_type
**Used By:** resource_assignments.assignment_type

```sql
CREATE TYPE assignment_type AS ENUM (
    'Primary',         -- Lead resource
    'Secondary',       -- Supporting resource
    'Observer',        -- Training/observation
    'Consultant'       -- External consultant
);
```

---

## Equipment ENUMs

### equipment_status
**Used By:** equipment.status

```sql
CREATE TYPE equipment_status AS ENUM (
    'Available',       -- Ready for assignment
    'Assigned',        -- Currently in use
    'Calibration',     -- Out for calibration
    'Maintenance',     -- Under repair
    'Retired'          -- No longer in service
);
```

---

### calibration_status
**Used By:** Derived from equipment.calibration_due

```sql
-- Note: This is computed, not stored
-- calibration_due < CURRENT_DATE → 'Overdue'
-- calibration_due < CURRENT_DATE + 30 → 'Due Soon'
-- Otherwise → 'Current'
```

---

## PSS Portal ENUMs

### study_type
**Used By:** pss_studies.study_type

```sql
CREATE TYPE study_type AS ENUM (
    'Short Circuit',       -- Fault current analysis
    'Arc Flash',           -- Arc flash hazard analysis
    'Coordination',        -- Protective device coordination
    'Load Flow',           -- Power flow analysis
    'Motor Starting',      -- Motor starting study
    'Harmonic',            -- Harmonic analysis
    'Power Quality',       -- Power quality assessment
    'Grounding',           -- Grounding system study
    'Transient',           -- Transient stability
    'Comprehensive'        -- Multiple study types
);
```

---

### study_status
**Used By:** pss_studies.status

```sql
CREATE TYPE study_status AS ENUM (
    'Pending',         -- Awaiting start
    'Data Collection', -- Gathering information
    'In Progress',     -- Analysis underway
    'Review',          -- Internal review
    'Client Review',   -- Customer review
    'Revisions',       -- Making changes
    'Completed',       -- Finished
    'On Hold',         -- Paused
    'Cancelled'        -- Cancelled
);
```

---

### document_type
**Used By:** pss_documents.document_type

```sql
CREATE TYPE document_type AS ENUM (
    'Study Report',        -- Main study document
    'One-Line Diagram',    -- Electrical one-line
    'Data Collection',     -- Field data sheets
    'Calculations',        -- Supporting calculations
    'Equipment Schedule',  -- Equipment list
    'Arc Flash Labels',    -- Label package
    'Short Circuit Report',-- SC analysis report
    'Coordination Curves', -- TCC curves
    'Cover Letter',        -- Transmittal
    'Appendix'             -- Supporting material
);
```

---

### document_status
**Used By:** pss_documents.status

```sql
CREATE TYPE document_status AS ENUM (
    'Draft',           -- Initial version
    'In Review',       -- Being reviewed
    'Approved',        -- Ready for delivery
    'Superseded',      -- Replaced by newer version
    'Archived'         -- Historical only
);
```

---

### rfi_status
**Used By:** pss_rfis.status

```sql
CREATE TYPE rfi_status AS ENUM (
    'Open',            -- Awaiting response
    'In Progress',     -- Being worked on
    'Pending Info',    -- Waiting for more info
    'Answered',        -- Response provided
    'Closed',          -- Resolved
    'Void'             -- Cancelled/invalid
);
```

---

### priority_level
**Used By:** pss_studies.priority, pss_rfis.priority

```sql
CREATE TYPE priority_level AS ENUM (
    'Critical',        -- Immediate attention
    'High',            -- Urgent
    'Medium',          -- Normal priority
    'Low'              -- When time permits
);
```

---

### activity_type
**Used By:** pss_activity_log.activity_type

```sql
CREATE TYPE activity_type AS ENUM (
    'Created',         -- Record created
    'Updated',         -- Record modified
    'Deleted',         -- Record removed
    'Status Change',   -- Status transition
    'Document Upload', -- File uploaded
    'Document Download', -- File downloaded
    'Assignment',      -- Resource assigned
    'Comment',         -- Note added
    'Approval',        -- Approval action
    'Rejection'        -- Rejection action
);
```

---

## Financial ENUMs

### revenue_type
**Used By:** apparatus_revenue.revenue_type

```sql
CREATE TYPE revenue_type AS ENUM (
    'Testing',         -- Equipment testing labor
    'Travel',          -- Travel charges
    'Per Diem',        -- Daily allowances
    'Materials',       -- Material charges
    'Equipment',       -- Equipment rental
    'Engineering',     -- Engineering services
    'Report',          -- Report preparation
    'Other'            -- Miscellaneous
);
```

---

### labor_category
**Used By:** scope_labor_details.labor_category

```sql
CREATE TYPE labor_category AS ENUM (
    'Field Tech',      -- Field technician time
    'Lead Tech',       -- Lead technician time
    'Engineer',        -- Engineering time
    'Project Manager', -- PM time
    'Travel',          -- Travel time
    'Overtime',        -- OT premium
    'Double Time'      -- DT premium
);
```

---

## Reference Data ENUMs

### scope_type
**Used By:** scopes.scope_type, apparatus.apparatus_type

```sql
CREATE TYPE scope_type AS ENUM (
    'ATS',             -- Automatic Transfer Switch
    'SWGR',            -- Switchgear
    'XFMR',            -- Transformer
    'PDC',             -- Power Distribution Center
    'MCC',             -- Motor Control Center
    'CB',              -- Circuit Breaker
    'RELAY',           -- Protective Relay
    'CABLE',           -- Cable Testing
    'BATT',            -- Battery System
    'UPS',             -- UPS System
    'GEN',             -- Generator
    'VFD',             -- Variable Frequency Drive
    'CAP',             -- Capacitor Bank
    'GND',             -- Grounding System
    'OTHER'            -- Other equipment
);
```

---

## Complete SQL Script

```sql
-- =============================================================================
-- RESA Power - ENUM Type Definitions
-- Run this BEFORE table creation
-- =============================================================================

-- Project/Work Status
CREATE TYPE project_status AS ENUM ('Draft', 'Quoted', 'Won', 'Active', 'On Hold', 'Complete', 'Cancelled');
CREATE TYPE scope_status AS ENUM ('Not Started', 'In Progress', 'On Hold', 'Complete', 'Cancelled');
CREATE TYPE task_status AS ENUM ('Not Started', 'In Progress', 'On Hold', 'Complete', 'Cancelled');
CREATE TYPE apparatus_status AS ENUM ('Not Started', 'In Progress', 'Pending Review', 'Complete', 'Cancelled');
CREATE TYPE apparatus_assessment AS ENUM ('Pass', 'Fail', 'Marginal', 'Needs Repair', 'Deferred', 'Not Tested');

-- Employee/Resource
CREATE TYPE role_type AS ENUM ('Field Tech', 'Lead Tech', 'Engineer', 'Project Manager', 'Estimator', 'Admin', 'Executive');
CREATE TYPE neta_level AS ENUM ('Level I', 'Level II', 'Level III', 'Level IV');
CREATE TYPE assignment_type AS ENUM ('Primary', 'Secondary', 'Observer', 'Consultant');

-- Equipment
CREATE TYPE equipment_status AS ENUM ('Available', 'Assigned', 'Calibration', 'Maintenance', 'Retired');

-- PSS Portal
CREATE TYPE study_type AS ENUM ('Short Circuit', 'Arc Flash', 'Coordination', 'Load Flow', 'Motor Starting', 'Harmonic', 'Power Quality', 'Grounding', 'Transient', 'Comprehensive');
CREATE TYPE study_status AS ENUM ('Pending', 'Data Collection', 'In Progress', 'Review', 'Client Review', 'Revisions', 'Completed', 'On Hold', 'Cancelled');
CREATE TYPE document_type AS ENUM ('Study Report', 'One-Line Diagram', 'Data Collection', 'Calculations', 'Equipment Schedule', 'Arc Flash Labels', 'Short Circuit Report', 'Coordination Curves', 'Cover Letter', 'Appendix');
CREATE TYPE document_status AS ENUM ('Draft', 'In Review', 'Approved', 'Superseded', 'Archived');
CREATE TYPE rfi_status AS ENUM ('Open', 'In Progress', 'Pending Info', 'Answered', 'Closed', 'Void');
CREATE TYPE priority_level AS ENUM ('Critical', 'High', 'Medium', 'Low');
CREATE TYPE activity_type AS ENUM ('Created', 'Updated', 'Deleted', 'Status Change', 'Document Upload', 'Document Download', 'Assignment', 'Comment', 'Approval', 'Rejection');

-- Financial
CREATE TYPE revenue_type AS ENUM ('Testing', 'Travel', 'Per Diem', 'Materials', 'Equipment', 'Engineering', 'Report', 'Other');
CREATE TYPE labor_category AS ENUM ('Field Tech', 'Lead Tech', 'Engineer', 'Project Manager', 'Travel', 'Overtime', 'Double Time');

-- Reference
CREATE TYPE scope_type AS ENUM ('ATS', 'SWGR', 'XFMR', 'PDC', 'MCC', 'CB', 'RELAY', 'CABLE', 'BATT', 'UPS', 'GEN', 'VFD', 'CAP', 'GND', 'OTHER');

SELECT 'All ENUM types created successfully!' as message;
```

---

## Migration Notes

### From VARCHAR to ENUM

If migrating existing VARCHAR columns to ENUM:

```sql
-- Example: Migrate projects.status from VARCHAR to ENUM
ALTER TABLE projects 
    ALTER COLUMN status TYPE project_status 
    USING status::project_status;
```

### Adding New Values

```sql
-- Add a value to existing ENUM
ALTER TYPE project_status ADD VALUE 'Pending Approval' AFTER 'Won';
```

### Value Validation

ENUMs automatically reject invalid values:

```sql
-- This will ERROR:
INSERT INTO projects (project_number, project_name, status)
VALUES ('TEST-001', 'Test Project', 'InvalidStatus');
-- ERROR: invalid input value for enum project_status: "InvalidStatus"
```

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-05 | Desktop Claude | Initial creation |

---

*ENUM Definitions v1.0.0 | RESA Power Supabase Migration*
