# Desktop ↔ VS Code Claude Coordination

**Purpose**: Share information between Claude sessions
**Updated**: 2025-12-11 (Session 4 - Desktop Audit) by Claude Desktop

---

## ✅ SESSION 4 COMPLETE (Dec 11) - Schema Audit

### Audit Summary

**CRITICAL FINDING**: Documentation claimed 34 tables but actual count is **30 tables**.

| Source | Before Audit | Corrected |
|--------|--------------|-----------|
| Supabase (actual) | - | **30 tables** |
| SCHEMA_REFERENCE.md | "34 Tables" | ✅ Fixed to 30 |
| PROJECT_STATUS.md | "34 tables" | ✅ Fixed to 30 |
| PROJECT_OVERVIEW.md | "23 Tables" | ✅ Fixed to 30 |

### Documentation Fixes Applied

| File | Change |
|------|--------|
| `Supabase/SCHEMA_REFERENCE.md` | "34 Tables" → "30 Tables" |
| `PROJECT_STATUS.md` | Executive summary corrected to 30 |
| `PROJECT_OVERVIEW.md` | System Scale updated to 30 tables |

### Verified Table Inventory (30 tables)

| Category | Tables |
|----------|--------|
| Organization (5) | locations, clients, sites, employees, estimators |
| Project Hierarchy (4) | projects, scopes, tasks, apparatus |
| Equipment (3) | apparatus_types, equipment, equipment_assignments |
| Financials (4) | apparatus_revenue, scope_labor_details, scope_financial_summaries, project_financial_summaries |
| Resource Mgmt (1) | resource_assignments |
| PSS Portal (6) | pss_engineers, pss_studies, pss_documents, pss_rfis, pss_document_templates, pss_activity_log |
| NETA/Resources (6) | neta_procedures, neta_test_items, neta_test_templates, sops, safety_documents, datasheets |
| Junction (1) | apparatus_type_resources |

### NETA JSON Files Located

Ready for import into `neta_procedures` + `neta_test_items`:

| File | Standard | Location |
|------|----------|----------|
| ANSI_NETA_ATS-2025_Final_v2.json | ATS (Acceptance) | Reference_Files/NETA/Extracted/ |
| ANSI_NETA_MTS-2023_FINAL_v2.json | MTS (Maintenance) | Reference_Files/NETA/Extracted/ |
| ANSI_NETA_ECS-2024_v2.json | ECS (Commissioning) | Reference_Files/NETA/Extracted/ |
| ANSI_NETA_ETT-2022_FINAL_v2.json | ETT (Technician) | Reference_Files/NETA/Extracted/ |

**JSON Structure** (example from ATS):
- `document_type`: "ATS"
- `equipment_categories`: Maps section numbers to equipment types
- `sections`: Contains `visual_mechanical_tests` and `electrical_tests` arrays

### Tables with Data vs Empty

**Populated:**
- apparatus (47), tasks (12), resource_assignments (8)
- scope_labor_details (6), apparatus_types (15), pss_document_templates (6)
- locations (5), employees (5), scopes (4), estimators (2)
- projects (1), clients (1), sites (1)

**Empty (need import):**
- neta_procedures ⚠️ → Import from JSON
- neta_test_items ⚠️ → Import from JSON
- apparatus_type_resources ⚠️ → After NETA import
- sops, safety_documents, datasheets ⚠️ → Future

---

## 🔜 NEXT STEPS (Post-Audit)

### Immediate Priority: NETA Import
1. Create import script/SQL to parse NETA JSON files
2. Insert into `neta_procedures` table (one per section)
3. Insert into `neta_test_items` table (tests within each procedure)
4. Link `apparatus_types.neta_section_*` columns to procedures
5. Create `apparatus_type_resources` junction records

### VS Code Claude Tasks:
- Use ROLE_DEMO_PROMPT.md to generate v0.dev demo
- Complete project detail page
- Build apparatus completion UI

---

## 🎉 SESSION 3 COMPLETE (Dec 11)

### Major Accomplishments

| Feature | Status | Details |
|---------|--------|---------|
| UI Specification Guide | ✅ Complete | 500+ line design system document |
| Role-Based Demo | ✅ Ready | v0.dev prompt with 5-role switcher |
| PSS Module Spec | ✅ Included | Added to role demo with sample data |
| Estimates Module Spec | ✅ Included | Added to role demo |
| Reports Module Spec | ✅ Included | 3-step wizard with auto-population |
| Report Generator Demo | ✅ Created | Standalone v0.dev prompt |
| Schema Verification | ✅ Verified | All 30 tables confirmed in Supabase |
| SCHEMA_REFERENCE.md | ✅ Updated | v2.0.0 with current inventory |

### New Documents Created:
- `Documentation/07_Application_Specs/UI_SPECIFICATION_GUIDE.md`
- `Documentation/07_Application_Specs/ROLE_DEMO_PROMPT.md`
- `Documentation/07_Application_Specs/REPORT_GENERATOR_DEMO_PROMPT.md`

### Documents Updated:
- `SUPABASE_REPORT_WORKFLOW.md` - Use `employees` table not `technicians`
- `Supabase/SCHEMA_REFERENCE.md` - Updated to v2.0.0 (30 tables documented)
- `PROJECT_STATUS.md` - Session 3 status

### Database Verified:
- **30 tables** total in Supabase (verified via MCP)
- All resource linking tables deployed but **EMPTY** (0 rows each):
  - `neta_procedures` ⚠️ 0 rows
  - `neta_test_items` ⚠️ 0 rows  
  - `sops` ⚠️ 0 rows
  - `safety_documents` ⚠️ 0 rows
  - `datasheets` ⚠️ 0 rows
  - `apparatus_type_resources` ⚠️ 0 rows

### Locations Updated:
- Phoenix, Denver, Las Vegas, San Diego (was Denver, Orlando, Houston, Minneapolis)

---

## 📋 CLAUDE DESKTOP AUDIT TASK

### Task: Schema & Documentation Audit

**Priority**: High  
**Assigned To**: Claude Desktop  
**Status**: Ready for pickup

**Objective**: Reconcile documentation with actual Supabase schema state

See **STARTER PROMPT** at bottom of this file.

**Deliverables Expected**:
1. Documentation discrepancy report
2. Updated table counts across all docs
3. Identify any orphaned/missing table documentation
4. Create NETA data import task list

---

## 🔜 NEXT STEPS

### Immediate (Claude Desktop Audit):
1. **Run audit** using starter prompt below
2. **Update all docs** with accurate table counts
3. **Create NETA import plan** with file locations

### After Audit:
1. **Import NETA JSON data** - Parse extracted files into tables
2. **Map apparatus_types** - Set neta_section columns
3. **Generate v0.dev demos** - Use ROLE_DEMO_PROMPT.md

### Stakeholder Review:
1. Share v0.dev demo link with GM
2. Collect feedback on role views
3. Prioritize modules for development

---

## Previous Session (Session 2 - Dec 10, PM)

### Major Accomplishments

| Feature | Status | Details |
|---------|--------|---------|
| Equipment Project Assignment | ✅ Deployed | Track equipment by employee, project, or warehouse |
| Two-Stage Approval Workflow | ✅ Deployed | Tech submits → Lead approves → Revenue recognized |
| UI Requirements Document | ✅ Created | Mockups for stakeholder review |

### Database State After Session 2:
- **31 tables** (added `equipment_assignments`)
- **15 views** (added 5 new views)
- **38+ ENUMs**
- **3 new functions** for approval workflow

### Schema Files Created:
- `Supabase/schema/07_equipment_project_assignment.sql`
- `Supabase/schema/08_apparatus_completion_workflow.sql`

### Views Created:
- `v_equipment_current_status` - Equipment with assignment details
- `v_project_equipment` - Equipment assigned to each project
- `v_equipment_movement_history` - Full movement audit trail
- `v_apparatus_approval_queue` - Pending approvals for lead review
- `v_approval_queue_summary` - Dashboard summary by project

### Functions Created:
- `submit_apparatus_for_review()` - Tech marks complete (Pending Review)
- `approve_apparatus_completion()` - Lead approves (triggers revenue)
- `reject_apparatus_submission()` - Lead rejects (back to In Progress)

---

## 📋 KEY DOCUMENT FOR GM REVIEW

**`Documentation/07_Application_Specs/UI_REQUIREMENTS_REVIEW.md`**

Contains:
- Dashboard layout options (3 choices)
- Project detail screen options (3 choices)
- Mobile tech view options (3 choices)
- Two-stage approval workflow mockups
- Module priority ranking table
- Workflow questions for stakeholder input

**Action**: Have GM review and mark preferences before UI development begins.

---

## 🔜 NEXT STEPS

### Immediate (When Resuming):
1. **Get GM feedback** on UI Requirements doc
2. **Import NETA JSON data** - Parse extracted files into `neta_procedures`
3. **Map apparatus_types** - Set neta_section columns
4. **Test approval workflow** - Create test submissions

### Future Phases:
- Project detail page UI
- Field tech mobile app
- Lead approval queue UI
- Equipment tracking dashboard

---

## Previous Session (Dec 10, AM)

### NETA/SOP Resource Linking Complete

- Deployed 6 new tables via Supabase MCP
- `neta_procedures`, `neta_test_items`, `sops`
- `safety_documents`, `datasheets`, `apparatus_type_resources`
- Created schema file `06_neta_sop_tables.sql`

---

## Previous Session (Dec 5)

### SUPABASE SWAP COMPLETE!

- App connected to Supabase and working
- LASNAP16 test data loaded (47 apparatus)
- Trigger cascade verified working

---

## Environment Quick Reference

| Component | Location/URL |
|-----------|--------------|
| Build Repo | `C:\RESA_Power_Build` |
| Web App | `C:\Users\jjswe\Projects\resa-web-app` |
| Supabase Project | `fxoyniqnrlkxfligbxmg` |
| API URL | `https://fxoyniqnrlkxfligbxmg.supabase.co` |
| Branch | `clean-main` |

---

## 🚀 CLAUDE DESKTOP STARTER PROMPT

### Schema & Documentation Audit Task

Copy this prompt to start a Claude Desktop session:

---

```
## TASK: Schema & Documentation Audit

### Background
I've been working on the RESA Power platform with multiple Claude sessions. The Supabase database has been evolving and documentation may be out of sync with actual schema state.

### Your Task
Perform a comprehensive audit to reconcile documentation with actual Supabase state.

### Step 1: Query Supabase for Current State
Use mcp_supabase_list_tables to get all tables with row counts.

### Step 2: Check These Documents
1. Supabase/SCHEMA_REFERENCE.md - Should have 30 tables
2. PROJECT_STATUS.md - Check table counts match
3. .claude/COORDINATION.md - Check session summaries accurate
4. PROJECT_OVERVIEW.md - Check architecture still valid

### Step 3: Create Discrepancy Report
Document any differences between:
- Actual Supabase tables vs documented tables
- Row counts (especially resource linking tables - should they be empty?)
- Missing documentation for any deployed features

### Step 4: NETA Data Import Readiness
Locate the NETA JSON files that need to be imported into:
- neta_procedures (currently 0 rows)
- neta_test_items (currently 0 rows)

Check these locations:
- Reference_Files/ folder
- Documentation/04_Data_Migration/ folder
- Any *.json files with NETA data

### Step 5: Update Documentation
Fix any discrepancies found. Ensure all docs show consistent table count (30).

### Step 6: Report Back
Create a summary in COORDINATION.md with:
- Audit findings
- Fixes made
- NETA import file locations (if found)
- Next steps recommendation

### Known State (Dec 11):
- 30 tables in Supabase (verified)
- Resource linking tables exist but are EMPTY:
  - neta_procedures (0 rows)
  - neta_test_items (0 rows)
  - sops (0 rows)
  - safety_documents (0 rows)
  - datasheets (0 rows)
  - apparatus_type_resources (0 rows)
- Core data populated:
  - projects, scopes, tasks, apparatus all have test data (LASNAP16)

### Files to Start With
Read these first:
1. PROJECT_STATUS.md
2. .claude/COORDINATION.md
3. Supabase/SCHEMA_REFERENCE.md
```
