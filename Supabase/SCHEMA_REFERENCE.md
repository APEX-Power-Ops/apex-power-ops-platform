# RESA Power Supabase Schema - Quick Reference

> **Version:** 1.1.0  
> **Created:** December 5, 2025  
> **Source:** Merged from Dataverse V1.5.1.3 + V2 + PSS Portal Requirements

---

## Schema Location

```
C:\RESA_Power_Build\Supabase\001_complete_schema.sql
```

**File Stats:** ~2,000 lines, 64KB

---

## Table Summary (30 Tables)

| # | Table | Purpose | Key Fields |
|---|-------|---------|------------|
| **Organization** ||||
| 1 | `locations` | Business units | name, code, region |
| 2 | `clients` | Customer companies | name, code, address |
| 3 | `sites` | Physical locations | name, client_id, address |
| 4 | `employees` | RESA staff | full_name, email, department |
| 5 | `contacts` | External people | full_name, client_id, contact_type |
| 6 | `portal_users` | Auth & access | email, role, auth_user_id |
| **Equipment** ||||
| 7 | `apparatus_types` | Equipment categories | name, default_hours, neta_section |
| **Project Hierarchy** ||||
| 8 | `projects` | Master jobs | project_number, client_id, status |
| 9 | `scopes` | Deliverables | scope_number, project_id, status |
| 10 | `scope_labor_details` | Rate config | scope_id, effective_rate |
| 11 | `tasks` | Work items | task_number, scope_id, status |
| 12 | `apparatus` | Equipment items | name, scope_id, completion_status |
| 13 | `apparatus_revenue` | Revenue records | apparatus_id, revenue_amount |
| 14 | `scope_financial_summaries` | Scope rollups | scope_id, total_revenue_* |
| 15 | `project_financial_summaries` | Project rollups | project_id, total_revenue_* |
| **PSS Portal** ||||
| 16 | `engineers` | Engineering vendors | company_name, code |
| 17 | `pss_studies` | PSS projects | project_id, pss_status |
| 18 | `document_templates` | Doc checklist | name, study_types |
| 19 | `pss_documents` | Doc tracking | pss_study_id, status |
| 20 | `rfis` | Info requests | rfi_number, status |
| 21 | `activity_log` | History | activity_type, description |
| **Import** ||||
| 22 | `estimators` | SharePoint import | file_name, scope_json |

---

## Key Enums (Option Sets)

| Enum | Values |
|------|--------|
| `project_status` | NOT_STARTED, IN_PROGRESS, ON_HOLD, COMPLETED, CANCELLED |
| `project_type` | FIELD_TESTING, PSS_STUDY, ARC_FLASH_STUDY, MAINTENANCE, etc. |
| `completion_status` | PLANNED, IN_PROGRESS, COMPLETE, DEFERRED, CANCELLED |
| `apparatus_assessment` | ACCEPTABLE, MINOR_DEFICIENCY, MAJOR_DEFICIENCY, NON_SERVICEABLE |
| `revenue_status` | PENDING, RECOGNIZED, INVOICED, PAID, ADJUSTED |
| `pss_status` | NEW_REQUEST → AWAITING_DOCUMENTS → ... → CLOSED |
| `document_status` | NOT_REQUESTED, REQUESTED, RECEIVED, ACCEPTED, REJECTED |
| `portal_role` | RESA_ADMIN, RESA_PM, RESA_TECH, CLIENT, ENGINEER |

---

## Automatic Features

### Triggers

| Trigger | Function |
|---------|----------|
| Apparatus completion | Creates `apparatus_revenue` record automatically |
| PSS status change | Logs to `activity_log`, updates `last_status_change` |
| Rollup updates | Cascades counts/hours up: apparatus → task → scope → project |
| Financial summaries | Updates when revenue records change |

### Computed Columns

- `percent_complete` on projects, scopes, tasks
- `effective_rate` on scope_labor_details
- `revenue_amount` on apparatus_revenue
- `days_in_current_status` on pss_studies
- `days_outstanding` on pss_documents
- `days_open` on rfis

---

## Dashboard Views

| View | Purpose |
|------|---------|
| `v_project_dashboard` | Projects with client, site, progress, revenue |
| `v_scope_dashboard` | Scopes with project context, labor rates |
| `v_apparatus_tracking` | Apparatus with full hierarchy, revenue status |
| `v_pss_dashboard` | PSS studies with doc/RFI counts |
| `v_revenue_summary` | Revenue aggregates by project |
| `v_outstanding_documents` | Awaiting PSS documents |
| `v_open_rfis` | Open RFIs sorted by priority |

---

## Seed Data Included

- **5 Locations:** Phoenix, Dallas, Austin, LA, Denver
- **35 Apparatus Types:** Switchgear, breakers, transformers, cables, etc. with standard hours
- **12 Document Templates:** SLD, utility bill, transformer nameplate, etc.
- **3 Engineers:** Shaw Engineering, Power Studies Inc, Electrical Consultants

---

## Deployment Steps

### 1. Create Supabase Project
- Go to [supabase.com](https://supabase.com)
- Create new project
- Note the project URL and anon key

### 2. Run Schema
- Open SQL Editor in Supabase Dashboard
- Copy contents of `001_complete_schema.sql`
- Execute (takes ~5 seconds)

### 3. Verify
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;
```
Should return 30 Tables.

### 4. Configure Auth
- Enable Email auth in Supabase Dashboard
- (Optional) Add Azure AD OAuth provider

### 5. Connect Web App
- Install `@supabase/supabase-js`
- Create `supabase.ts` client
- Replace Dataverse API calls with Supabase queries

---

## Migration Notes

### From Dataverse V2

| Dataverse Table | Supabase Table | Notes |
|-----------------|----------------|-------|
| cr950_clients | clients | Same fields, different format |
| cr950_sites | sites | Same fields |
| cr950_projects | projects | Added rollup fields |
| cr950_scopes | scopes | Added rollup fields |
| cr950_tasks | tasks | Added rollup fields |
| cr950_apparatuses | apparatus | Added computed columns |
| cr950_estimators | estimators | Same structure |
| cr950_apparatusrevenues | apparatus_revenue | Computed revenue |
| cr950_scopelabordetails | scope_labor_details | Computed effective_rate |
| cr950_scopefinancialsummaries | scope_financial_summaries | Trigger-updated |
| cr950_projectfinancialsummaries | project_financial_summaries | Trigger-updated |
| cr950_locations | locations | Same structure |

### From V1.5.1.3 (Restored)

| Feature | V1.5.1.3 | Supabase |
|---------|----------|----------|
| Rollup fields | Power Platform rollup | PostgreSQL triggers |
| Calculated fields | Dataverse formulas | Generated columns |
| Option sets | Global choice | PostgreSQL enums |
| Revenue flow | Power Automate | Database triggers |

---

## Next Steps

1. ✅ Schema created
2. 🔲 Create Supabase project
3. 🔲 Run migration script
4. 🔲 Migrate existing data (1 client, 1 estimator)
5. 🔲 Update web app to use Supabase client
6. 🔲 Build PSS Portal UI
7. 🔲 Import PSS tracker data


