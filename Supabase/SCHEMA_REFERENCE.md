# RESA Power Supabase Schema - Quick Reference

> **Version:** 2.1.0  
> **Updated:** December 11, 2025  
> **Status:** ✅ DEPLOYED - Database live with test data + operational fields pending

---

## Schema Location

```
C:\RESA_Power_Build\Supabase\schema\
├── 00_enums.sql
├── 01_tables.sql
├── 02_relationships.sql
├── 03_triggers.sql
├── 04_views.sql
├── 05_indexes.sql
├── 06_neta_sop_tables.sql          # Resource linking tables
├── 07_equipment_project_assignment.sql
├── 08_apparatus_completion_workflow.sql
├── 09_schema_additions.sql         # ⭐ NEW: Operational fields + rollup views
└── 09b_enum_updates.sql            # ⭐ NEW: Assessment value additions
```

## 📋 Additional Documentation

- [EXCEL_TO_DATABASE_MAPPING.md](EXCEL_TO_DATABASE_MAPPING.md) - Field mapping from Excel trackers

---

## Table Summary (30 Tables)

| # | Table | Purpose | Rows |
|---|-------|---------|------|
| **Organization** ||||
| 1 | `locations` | Business units (Phoenix, Denver, Las Vegas, San Diego) | 5 |
| 2 | `clients` | Customer companies | 1 |
| 3 | `sites` | Physical locations | 1 |
| 4 | `employees` | RESA staff | 5 |
| 5 | `estimators` | Quote creators | 2 |
| **Project Hierarchy** ||||
| 6 | `projects` | Master jobs | 1 |
| 7 | `scopes` | Deliverables/phases | 4 |
| 8 | `tasks` | Work items | 12 |
| 9 | `apparatus` | Equipment being tested | 47 |
| **Equipment & Types** ||||
| 10 | `apparatus_types` | Equipment categories (MV CB, Transformer, etc.) | 15 |
| 11 | `equipment` | Company-owned test equipment | 0 |
| 12 | `equipment_assignments` | Equipment checkout history | 0 |
| **Financials** ||||
| 13 | `apparatus_revenue` | Revenue recognition per apparatus | 0 |
| 14 | `scope_labor_details` | Labor line items | 6 |
| 15 | `scope_financial_summaries` | Scope rollups (trigger-updated) | 0 |
| 16 | `project_financial_summaries` | Project rollups (trigger-updated) | 0 |
| **Resource Assignments** ||||
| 17 | `resource_assignments` | Employee-to-project/scope | 8 |
| **PSS Portal** ||||
| 18 | `pss_engineers` | External engineering vendors | 0 |
| 19 | `pss_studies` | Power System Studies | 0 |
| 20 | `pss_document_templates` | Doc checklist templates | 6 |
| 21 | `pss_documents` | Study documents | 0 |
| 22 | `pss_rfis` | Requests for Information | 0 |
| 23 | `pss_activity_log` | Audit trail | 0 |
| **NETA & Resource Linking** ||||
| 24 | `neta_procedures` | NETA standard sections (ATS/MTS/ECS/ETT) | 0 |
| 25 | `neta_test_items` | Individual test steps per procedure | 0 |
| 26 | `neta_test_templates` | Legacy test templates | 0 |
| 27 | `sops` | Company Standard Operating Procedures | 0 |
| 28 | `safety_documents` | JSAs, PPE requirements, arc flash | 0 |
| 29 | `datasheets` | Manufacturer specs, product data | 0 |
| 30 | `apparatus_type_resources` | **Junction table** linking types → resources | 0 |

---

## Resource Linking Architecture

```
┌──────────────────┐         ┌──────────────────────────────┐
│  apparatus_types │─────────│  apparatus_type_resources    │
│  (e.g., MV CB)   │    1:N  │  (junction table)            │
│  + neta_section_ │         └──────────────┬───────────────┘
│    ats/mts/ecs   │                        │
└──────────────────┘         ┌──────────────┼───────────────┐
                             │              │               │
                             ▼              ▼               ▼
                  ┌─────────────┐  ┌─────────────┐  ┌────────────┐
                  │    neta_    │  │    sops     │  │  safety_   │
                  │ procedures  │  │             │  │ documents  │
                  └──────┬──────┘  └─────────────┘  └────────────┘
                         │                                │
                         ▼                                ▼
                  ┌─────────────┐                  ┌────────────┐
                  │ neta_test_  │                  │ datasheets │
                  │   items     │                  └────────────┘
                  └─────────────┘
```

**Flow:** Apparatus → apparatus_type → apparatus_type_resources → All linked resources automatically available to techs

---

## Key Enums (Option Sets)

| Enum | Values |
|------|--------|
| `project_status` | Draft, Quoted, Won, Active, On Hold, Complete, Cancelled |
| `scope_status` | Not Started, In Progress, On Hold, Complete, Cancelled |
| `apparatus_status` | Not Started, In Progress, Pending Review, Complete, Cancelled |
| `apparatus_assessment` | Pass, Fail, Marginal, Needs Repair, Deferred, Not Tested, **Acceptable**, **Non-Serviceable**, **Minor Deficiency** |
| `apparatus_availability` | **Ready, On Hold, Not Available** ⭐ NEW |
| `revenue_type` | Testing, Travel, Per Diem, Materials, Equipment, Engineering, Report, Other |
| `neta_standard_type` | ATS, MTS, ECS, ETT |
| `neta_test_type` | visual_mechanical, electrical, optional |
| `sop_category` | safety, testing, commissioning, maintenance, documentation, quality, administrative, equipment_specific, other |
| `safety_document_type` | jsa, sds, hazard_alert, ppe_requirement, lockout_tagout, arc_flash, confined_space, hot_work, electrical_safety, environmental, other |
| `resource_type` | neta_procedure, sop, safety_document, datasheet, document, video, checklist |

---

## Apparatus Types with NETA Section Links

The `apparatus_types` table includes columns to directly link equipment categories to NETA standards:

| Column | Purpose | Example |
|--------|---------|---------|
| `neta_section_ats` | ATS (Acceptance) reference | "7.6.1" |
| `neta_section_mts` | MTS (Maintenance) reference | "7.6.1" |
| `neta_section_ecs` | ECS (Commissioning) reference | "7.6" |
| `neta_section_ett` | ETT (Technician) reference | NULL |

---

## Triggers & Automatic Features

| Trigger | Function |
|---------|----------|
| Apparatus completion | Creates `apparatus_revenue` record automatically |
| Financial rollups | Updates scope/project summaries when revenue changes |
| PSS status change | Logs to `pss_activity_log` |
| Rollup counts | Cascades: apparatus → task → scope → project |

---

## Dashboard Views

| View | Purpose |
|------|---------|
| `v_project_dashboard` | Projects with client, site, progress, revenue |
| `v_scope_dashboard` | Scopes with project context, labor rates |
| `v_apparatus_tracking` | Apparatus with full hierarchy |
| `v_pss_dashboard` | PSS studies with doc/RFI counts |

### ⭐ NEW Operational Views (09_schema_additions.sql)

| View | Purpose | Answers |
|------|---------|---------|
| `v_apparatus_operational` | Daily scheduling | What's ready to work? |
| `v_project_apparatus_summary` | Per-project KPIs | Your Excel dashboard header |
| `v_apparatus_by_category` | Category breakdown | Which equipment types need work? |
| **`v_master_operations`** | **Multi-project dashboard** | **All 10-15 projects at once** |
| `v_resource_allocation` | Staffing decisions | Where should I send people? |
| `v_equipment_needs` | Test equipment planning | What equipment goes where? |
| `v_blockers_summary` | Bottleneck identification | What's stopping us? |
| `v_schedule_health` | Risk identification | What's at risk/overdue? |
| `v_task_rollup_dates` | Task-level aggregations | Task date rollups |
| `v_scope_rollup_dates` | Scope-level aggregations | Scope date rollups |
| `v_project_rollup_dates` | Executive summary | All project rollups |

---

## ⭐ New Operational Fields (09_schema_additions.sql)

### Apparatus Table Additions
| Column | Type | Purpose |
|--------|------|---------|
| `availability` | enum | Ready/On Hold/Not Available |
| `date_due` | DATE | Target completion date |
| `designation` | VARCHAR | Equipment designation ID |
| `drawing_reference` | VARCHAR | Reference to electrical drawing |
| `datasheet_complete` | BOOLEAN | Data collection status |
| `task_delays` | INTEGER | Delay count |
| `priority` | INTEGER | Work priority (1=High) |

### Rollup Date Fields
All levels (Task, Scope, Project) now support:
- `date_due` - Target date
- `earliest_*_due` - MIN of child due dates
- `latest_*_due` - MAX of child due dates  
- `earliest_*_start` - First work started
- `latest_*_complete` - Last work finished

---

## Supabase Connection

- **Project**: resa-power-db (fxoyniqnrlkxfligbxmg)
- **API URL**: https://fxoyniqnrlkxfligbxmg.supabase.co
- **Credentials**: `.secrets/SUPABASE_CREDENTIALS.md`

---

## Next Steps - Schema Deployment

### Immediate (Run Once)
1. ✅ Core schema deployed
2. ✅ NETA data imported (66 procedures, 956 test items)
3. 🔲 **Deploy `09_schema_additions.sql`** - Operational fields + views
4. 🔲 **Deploy `09b_enum_updates.sql`** - Assessment enum values

### Data Population
1. 🔲 Link apparatus_types to NETA sections via apparatus_type_resources
2. 🔲 Add safety documents (JSAs, arc flash)
3. 🔲 Populate datasheets for common manufacturers

### Import Development
1. 🔲 Update import function with new field mappings
2. 🔲 Test with Garney tracker data
3. 🔲 Build Excel → JSON export for new fields


