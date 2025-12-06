# RESA Supabase Schema Merge - Parallel Execution Plan

**Created:** December 5, 2025  
**Status:** APPROVED - Ready for Execution  
**Stakeholders:** Jason (Owner), Desktop Claude, VS Code Claude

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Tables | 25 |
| Total Files | 10 SQL + 1 README |
| Estimated Time | 2-3 hours parallel execution |
| Target Location | `C:\RESA_Power_Build\Supabase\` |

---

## Phase 1: Schema Generation (Parallel)

### Track A: Desktop Claude - Core Schema & Automation
**Strengths:** Triggers, computed columns, ENUMs, views, RLS

| Task | File | Est. | Dependencies |
|------|------|------|--------------|
| A1 | `00_enums.sql` | 10 min | None |
| A2 | `01_core_schema.sql` | 30 min | A1 |
| A3 | `03_triggers_functions.sql` | 20 min | A2 |
| A4 | `04_views.sql` | 15 min | A2 |
| A5 | `05_rls_policies.sql` | 10 min | A2 |
| A6 | `10_seed_data.sql` | 15 min | A2 |

**Track A Total:** ~100 minutes

### Track B: VS Code Claude - PSS Schema & Test Data
**Strengths:** PSS tables, test data, documentation, pss_* naming

| Task | File | Est. | Dependencies |
|------|------|------|--------------|
| B1 | `02_pss_schema.sql` | 20 min | A1 (needs enums) |
| B2 | `11_test_data.sql` | 25 min | A2 (needs core tables) |
| B3 | `12_pss_test_data.sql` | 20 min | B1 |
| B4 | `README.md` | 30 min | A3 (needs trigger docs) |

**Track B Total:** ~95 minutes

---

## Execution Timeline (Parallel)

```
TIME    DESKTOP CLAUDE (Track A)          VS CODE CLAUDE (Track B)
─────   ───────────────────────────────   ─────────────────────────────
0:00    A1: 00_enums.sql                  [waiting for A1]
0:10    A2: 01_core_schema.sql            B1: 02_pss_schema.sql (uses A1)
0:40    A3: 03_triggers_functions.sql     B2: 11_test_data.sql (uses A2)
1:00    A4: 04_views.sql                  B3: 12_pss_test_data.sql
1:15    A5: 05_rls_policies.sql           B4: README.md (uses A3)
1:25    A6: 10_seed_data.sql              [reviewing A files]
1:40    [reviewing B files]               [complete]
─────   ───────────────────────────────   ─────────────────────────────
2:00    CHECKPOINT: Cross-review complete
```

---

## File Specifications

### 00_enums.sql (Desktop Claude)
```
Contents:
- 18 PostgreSQL ENUMs
- project_status, project_type, scope_status, scope_type
- task_status, task_availability, completion_status
- apparatus_assessment, checklist_status, revenue_status
- pss_status, pss_study_type, document_status
- rfi_status, rfi_priority, contact_type
- portal_role, employee_department, skill_level
- equipment_status (NEW)
```

### 01_core_schema.sql (Desktop Claude)
```
Contents:
- Organization: locations, clients, sites, employees, contacts, portal_users
- Equipment Ref: apparatus_types, neta_test_templates (NEW), equipment (NEW)
- Projects: projects, scopes, scope_labor_details, tasks, apparatus
- Revenue: apparatus_revenue, scope_financial_summaries, project_financial_summaries
- Operations: resource_assignments (NEW), estimators
- All computed/generated columns
- All indexes
- Updated_at triggers

Tables: 19
```

### 02_pss_schema.sql (VS Code Claude)
```
Contents:
- pss_engineers
- pss_studies (linked to projects table)
- pss_document_templates
- pss_documents
- pss_rfis
- pss_activity_log
- PSS-specific indexes
- Uses ENUMs from 00_enums.sql

Tables: 6
```

### 03_triggers_functions.sql (Desktop Claude)
```
Contents:
- update_updated_at_column()
- track_pss_status_change()
- create_revenue_on_completion()
- update_task_rollups()
- update_scope_rollups()
- update_project_rollups()
- update_scope_financial_summary()
- update_project_financial_summary()
- generate_project_number()
- generate_rfi_number()

Functions: 10
```

### 04_views.sql (Desktop Claude)
```
Contents:
- v_project_dashboard
- v_scope_dashboard
- v_apparatus_tracking
- v_pss_dashboard
- v_revenue_summary
- v_outstanding_documents
- v_open_rfis
- v_resource_utilization (NEW)

Views: 8
```

### 05_rls_policies.sql (Desktop Claude)
```
Contents:
- Enable RLS on all sensitive tables
- RESA staff: full access policies
- Clients: own projects only
- Engineers: assigned studies only
- Anon: no access

Policies: ~15
```

### 10_seed_data.sql (Desktop Claude)
```
Contents:
- 5 locations (Phoenix, Dallas, Austin, LA, Denver)
- 35 apparatus_types with NETA hours
- 12 pss_document_templates
- 3 pss_engineers (Shaw, Power Studies Inc, Electrical Consultants)
- NETA test templates (linked to apparatus_types)

Records: ~60
```

### 11_test_data.sql (VS Code Claude)
```
Contents:
- 5 clients with realistic names
- 6 sites linked to clients
- 3 estimators
- 5 employees with rates/skills
- LASNAP16 project (Active)
- TIC-2025-001 project (Quoted)
- SWM-2024-003 project (Complete)
- MPS-2025-001 project (Active)
- 6+ scopes for LASNAP16
- 10+ tasks
- 20+ apparatus with mixed status
- Resource assignments

Records: ~80
```

### 12_pss_test_data.sql (VS Code Claude)
```
Contents:
- PSS contacts (Chad Sheffield, Paul Shaw, client contacts)
- 5 PSS studies from requirements:
  - 629266 SWA Tech Ops (Partial Documents)
  - 630145 Hydro (In Progress)
  - 628901 K2 Electric (RFI Pending)
  - 627555 DP Electric (Report Approved)
  - 631000 Swain Electric (New Request)
- Documents per study
- Sample RFIs
- Activity log entries

Records: ~50
```

### README.md (VS Code Claude)
```
Contents:
- Quick Start (15 min setup)
- Supabase account creation
- Script execution order
- Connection details
- API examples (JS, Python, PowerShell)
- NocoDB integration
- Trigger behavior documentation (NEW)
- View descriptions (NEW)
- Troubleshooting
- Migration from Dataverse
```

---

## Phase 2: Validation

### Validation Checklist

| Test | Owner | Method |
|------|-------|--------|
| Schema executes without errors | Both | Run in fresh Supabase |
| All 25 tables created | Desktop | `SELECT count(*) FROM information_schema.tables` |
| All 18 enums created | Desktop | `SELECT typname FROM pg_type WHERE typtype = 'e'` |
| All 10 triggers fire | Desktop | Insert test apparatus, verify rollups |
| All 8 views return data | Desktop | `SELECT * FROM v_project_dashboard` |
| RLS blocks unauthorized | Desktop | Test as different roles |
| Test data loads | VS Code | Run 11 + 12, verify counts |
| README steps work | VS Code | Follow guide on fresh project |

---

## Phase 3: Cleanup

### Files to Archive
```
C:\RESA_Power_Build\Database_Setup\
├── 01_supabase_schema.sql      → Archive
├── 02_test_data.sql            → Archive (merged into 11)
├── 03_pss_portal_tables.sql    → Archive (merged into 02)
├── 04_pss_portal_test_data.sql → Archive (merged into 12)
└── README.md                   → Archive (superseded)
```

### Files to Archive (Supabase folder)
```
C:\RESA_Power_Build\Supabase\
├── 001_complete_schema.sql     → Archive (split into 00-05)
├── 001_schema.sql              → Delete (old partial)
└── QUICKSTART.md               → Delete (superseded by README)
```

### Archive Location
```
C:\RESA_Power_Build\Archive\Database_Schemas_Pre_Merge\
```

---

## Stakeholder Checkpoints

### Checkpoint 1: Schema Files Complete
**When:** After A1-A6 and B1 complete  
**Review:** Jason confirms file structure looks correct  
**Gate:** Proceed to test data only if schema approved

### Checkpoint 2: Full Package Ready
**When:** All 11 files complete  
**Review:** Both Claudes cross-review each other's files  
**Gate:** Proceed to Supabase deployment only if both approve

### Checkpoint 3: Deployment Verified
**When:** Schema running in Supabase  
**Review:** Jason tests via Supabase dashboard  
**Gate:** Archive old files, update documentation

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| FK constraint errors in test data | Use fixed UUIDs, verify parent records exist |
| Trigger cascade performance | Test with LASNAP16 data, monitor query time |
| Enum mismatch between files | Desktop creates all enums first, VS Code references |
| RLS blocks test queries | Create service role for admin testing |
| README steps outdated | VS Code validates against fresh Supabase |

---

## Success Criteria

- [ ] All 25 tables created
- [ ] All 18 enums defined
- [ ] All 10 triggers functional
- [ ] All 8 views return data
- [ ] LASNAP16 project fully populated
- [ ] 5 PSS studies with documents/RFIs
- [ ] RLS policies enforced
- [ ] README walkthrough works end-to-end
- [ ] Old files archived
- [ ] Jason confirms "ready for app development"

---

## Next Steps After Merge

1. **Supabase Project Creation** - Jason creates resa-power-dev
2. **Schema Deployment** - Run files 00-12 in order
3. **API Key Configuration** - Store in environment variables
4. **Web App Update** - Replace Dataverse client with Supabase client
5. **NocoDB Connection** - Optional quick UI for data entry
6. **PSS Portal Development** - Build client/engineer interfaces

---

**READY TO EXECUTE**

Jason - Confirm "GO" and we begin parallel generation.

---

*Plan created by Desktop Claude | Approved by VS Code Claude | December 5, 2025*
