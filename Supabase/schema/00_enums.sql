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
