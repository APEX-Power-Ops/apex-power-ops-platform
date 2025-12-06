# RESA Power Platform - Supabase Database

This directory contains the PostgreSQL/Supabase database schema and data for the RESA Power project management platform.

## Directory Structure

```
Supabase/
├── schema/                     # Database schema files (run in order)
│   ├── 00_enums.sql           # ENUM type definitions (18 types)
│   ├── 01_tables.sql          # Table definitions (25 tables)
│   ├── 02_relationships.sql   # Foreign key constraints
│   ├── 03_triggers.sql        # Trigger functions (12 functions)
│   ├── 04_views.sql           # Database views (15 views)
│   └── 05_indexes.sql         # Performance indexes (~50 indexes)
├── data/                       # Data files (run after schema)
│   ├── 10_seed_data.sql       # Reference data (locations, apparatus_types)
│   ├── 11_test_data.sql       # LASNAP16 test project data
│   └── 12_pss_test_data.sql   # PSS portal test data
└── docs/                       # Documentation
    ├── README.md              # This file
    └── QUICK_START.md         # Quick start guide
```

## Schema Overview

### Core Tables (10)
| Table | Description | Records in Test |
|-------|-------------|-----------------|
| `locations` | RESA branch offices | 5 |
| `clients` | Customer companies | 1 |
| `sites` | Client facility locations | 1 |
| `employees` | RESA staff members | 5 |
| `projects` | Main project tracking | 1 |
| `scopes` | Project phases/work packages | 4 |
| `tasks` | Work items within scopes | 12 |
| `apparatus` | Equipment being tested | 47 |
| `equipment` | Company-owned test equipment | 0 |
| `resource_assignments` | Employee-project assignments | 8 |

### Financial Tables (6)
| Table | Description |
|-------|-------------|
| `estimators` | Quote creators |
| `apparatus_revenue` | Revenue recognition per apparatus |
| `scope_labor_details` | Labor line items per scope |
| `scope_financial_summaries` | Aggregated scope financials |
| `project_financial_summaries` | Aggregated project financials |
| `neta_test_templates` | Standard NETA test procedures |

### Reference Tables (2)
| Table | Description |
|-------|-------------|
| `apparatus_types` | Equipment type master list |

### PSS Portal Tables (6)
| Table | Description | Records in Test |
|-------|-------------|-----------------|
| `pss_engineers` | External PSS engineers | 3 |
| `pss_document_templates` | Document templates | 8 |
| `pss_studies` | Power System Studies | 5 |
| `pss_documents` | Study documents | 14 |
| `pss_rfis` | Requests for Information | 10 |
| `pss_activity_log` | Audit trail | 25 |

## ENUM Types (18)

- `project_status` - Project lifecycle states
- `scope_status` - Scope/phase states
- `task_status` - Task states
- `apparatus_status` - Testing states
- `apparatus_assessment` - Test result classifications
- `role_type` - Employee role categories
- `neta_level` - NETA certification levels
- `assignment_type` - Resource assignment roles
- `equipment_status` - Company equipment states
- `study_type` - PSS study classifications
- `study_status` - PSS study lifecycle
- `document_type` - Document classifications
- `document_status` - Document review states
- `rfi_status` - RFI lifecycle states
- `priority_level` - Priority classifications
- `activity_type` - Audit log types
- `revenue_type` - Revenue categories
- `labor_category` - Labor cost categories
- `scope_type` - Equipment/scope type codes

## Triggers (12 Functions)

| Trigger | Purpose |
|---------|---------|
| `update_updated_at_column()` | Auto-update timestamps on all tables |
| `update_task_apparatus_count()` | Rollup apparatus count to tasks |
| `update_scope_apparatus_counts()` | Rollup apparatus counts to scopes |
| `update_project_apparatus_counts()` | Rollup apparatus counts to projects |
| `update_scope_hours_from_tasks()` | Rollup hours from tasks to scopes |
| `update_scope_hours_from_apparatus()` | Rollup hours from apparatus to scopes |
| `update_project_counts_from_scopes()` | Rollup scope stats to projects |
| `create_revenue_on_apparatus_complete()` | Auto-create revenue records |
| `update_scope_financial_summary()` | Recalculate scope financials |
| `update_project_financial_summary()` | Recalculate project financials |
| `log_pss_study_status_change()` | Audit log for PSS status changes |
| `log_pss_document_upload()` | Audit log for document uploads |

## Views (15)

| View | Purpose |
|------|---------|
| `v_projects_full` | Complete project info with rollups |
| `v_projects_summary` | Lightweight project listing |
| `v_projects_active` | Active projects only |
| `v_scopes_full` | Complete scope info |
| `v_tasks_full` | Complete task info |
| `v_apparatus_full` | Complete apparatus info |
| `v_apparatus_testing_status` | Testing status dashboard |
| `v_scope_financials` | Scope financial summary |
| `v_project_financials` | Project financial summary |
| `v_revenue_by_apparatus` | Revenue recognition detail |
| `v_employees_full` | Employee info with certs |
| `v_resource_assignments_full` | Assignment details |
| `v_pss_studies_full` | Complete PSS study info |
| `v_pss_dashboard` | PSS portal dashboard |
| `v_branch_summary` | Branch-level summary |
| `mv_project_kpis` | Materialized KPI view |

## Deployment

### Full Fresh Install

```sql
-- Run in order:
\i schema/00_enums.sql
\i schema/01_tables.sql
\i schema/02_relationships.sql
\i schema/03_triggers.sql
\i schema/04_views.sql
\i schema/05_indexes.sql

-- Then load data:
\i data/10_seed_data.sql
\i data/11_test_data.sql
\i data/12_pss_test_data.sql
```

### Via Supabase Dashboard

1. Go to SQL Editor
2. Copy contents of each file
3. Execute in order (00 → 05, then 10 → 12)

### Via psql CLI

```bash
# Connect to Supabase
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres"

# Run schema files
\i C:/RESA_Power_Build/Supabase/schema/00_enums.sql
# ... continue with remaining files
```

## Test Data Summary

### LASNAP16 Project
- **Client**: Louisiana Snap Foods Corporation
- **Site**: Main Manufacturing Plant, Baton Rouge, LA
- **Project**: Annual Maintenance Testing 2016
- **Contract Value**: $187,500
- **4 Scopes**: Main Substation, Transformers, MCC Building A, MCC Building B
- **47 Apparatus**: Switchgear, breakers, relays, transformers, MCCs

### PSS Portal Data
- **3 Engineers**: Patterson, Rodriguez, Chang
- **5 Studies**: Arc Flash (Complete), Coordination (In Progress), Short Circuit (Pending), Load Flow (Data Collection), Template (On Hold)
- **14 Documents**: Reports, one-lines, data forms, coordination curves
- **10 RFIs**: Various statuses demonstrating workflow

## UUID Conventions

Test data uses predictable UUIDs for debugging:

### Seed Data (10_seed_data.sql)
| Prefix | Entity |
|--------|--------|
| `10000000-...` | locations (RESA branches) |
| `20000000-...` | apparatus_types |
| `30000000-...` | neta_test_templates |

### Test Data (11_test_data.sql, 12_pss_test_data.sql)
| Prefix | Entity |
|--------|--------|
| `11111111-...` | clients |
| `22222222-...` | sites |
| `33333333-...` | projects |
| `44444444-...` | scopes |
| `55555555-...` | tasks |
| `66666666-...` | apparatus |
| `77777777-...` | employees |
| `88888888-...` | resource_assignments |
| `99999999-...` | apparatus_revenue |
| `AAAAAAAA-...` | scope_labor_details |
| `BBBBBBBB-...` | pss_engineers |
| `CCCCCCCC-...` | pss_document_templates |
| `DDDDDDDD-...` | pss_studies |
| `EEEEEEEE-...` | pss_documents |
| `FFFFFFFF-...` | pss_rfis |

## Related Documentation

- `/spec/DATA_DICTIONARY.md` - Complete field definitions
- `/spec/ENUM_DEFINITIONS.md` - ENUM value descriptions
- `/spec/ENTITY_RELATIONSHIPS.md` - FK relationships
- `/spec/TRIGGER_FLOWS.md` - Trigger logic details
- `/spec/VIEW_DEFINITIONS.md` - View SQL and purposes

---

*Generated: December 5, 2025*  
*Version: 1.0.0*
