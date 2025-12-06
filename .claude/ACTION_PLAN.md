# RESA Power - Focused Action Plan

**Purpose**: Get relief NOW. Not enterprise planning - immediate workload reduction.  
**Context**: PE roll-up with zero infrastructure. Phoenix/SW Region drowning.  
**Created**: 2025-12-05

---

## The Reality

You built this tracker because you had no choice:
- 16 sheets, complex formulas, billing calculations
- Works for ONE project at a time
- No visibility across projects
- No way for field techs to update from site
- Manual copy/paste to create new project trackers
- Can't answer "what's the status across all our work?"

**The goal isn't perfect - it's RELIEF.**

---

## What Your Tracker Already Does (That We Need to Preserve)

| Feature | Excel Location | Database Equivalent |
|---------|---------------|---------------------|
| Project metadata | Project_Form | `projects` + `clients` + `sites` |
| Scope breakdown | IPS, NWWRP, GWRP, SEWRP sheets | `scopes` table |
| Task/Apparatus tracking | All_Tasks | `tasks` + `apparatus` |
| Hours by apparatus type | Apparatus_List_w_Hours | `apparatus_types` |
| Status/Availability/Assessment | Dropdowns + cells | ENUMs + fields |
| Billing calculations | All_Tasks_Billing | `apparatus_revenue` + triggers |
| Labor rates per scope | Scope_Labor_Rates | `scope_labor_details` |
| Gantt/Schedule | Gantt Chart sheet | `apparatus.anticipated_start` + views |
| Summary dashboard | Project Summary | `v_projects_full` view |

**Good news**: The Supabase schema already supports all of this.

---

## Phase 1: Immediate Relief (This Week)

### 1A. Migrate This Project to Database
**Effort**: 2-3 hours  
**Result**: Garney 677562 data in Supabase, queryable

| Source Sheet | Target Table | Records |
|--------------|--------------|---------|
| Project_Form | projects, clients, sites | 1 each |
| All_Tasks rows | scopes, tasks, apparatus | ~143 apparatus |
| Scope_Labor_Rates | scope_labor_details | 4 scopes |

### 1B. Create Field Tracker View
**Effort**: 2-4 hours  
**Result**: Web view that looks like your IPS/NWWRP sheets

Must have:
- [ ] Filter by project
- [ ] Filter by scope  
- [ ] Show: Task_ID, Apparatus, Status, Availability, Assessment, Hours, Dates
- [ ] Update status/completion inline
- [ ] Mobile-friendly (field techs)

### 1C. Create Project Summary Dashboard  
**Effort**: 2-3 hours  
**Result**: See all projects at a glance

Must have:
- [ ] Total apparatus / completed / remaining
- [ ] Completion % by project
- [ ] Ready to work count
- [ ] Issues/blockers count
- [ ] Filter by PM, location, status

---

## Phase 2: Migration Path (Next 2 Weeks)

### 2A. Excel Import Tool
**Effort**: 4-6 hours  
**Result**: Upload a tracker Excel → auto-populate database

Steps:
1. Standardize tracker template (you mostly have this)
2. Build Python script to read All_Tasks sheet
3. Map to database tables
4. Handle duplicates/updates

### 2B. Migrate Active Projects
**Effort**: 1 hour per project (with tool)  
**Result**: All current projects in database

Estimate: How many active project trackers do you have?
- [ ] < 5 projects
- [ ] 5-10 projects  
- [ ] 10-20 projects
- [ ] 20+ projects

### 2C. Retire Excel for New Projects
**Result**: New projects start in database, not Excel

---

## Phase 3: Automation Wins (Month 2)

| Pain Point | Automation | Impact |
|------------|------------|--------|
| "What's ready to work?" | Dashboard filter | Save 30min/day |
| "How much have we billed?" | Revenue recognition trigger | Already in schema |
| "Who's assigned where?" | Resource calendar view | Scheduling visibility |
| "What's overdue?" | Overdue apparatus alert | Proactive not reactive |
| Status update from field | Mobile-friendly form | No more "call me with update" |

---

## Decisions Needed NOW

### Blocking (Must decide to proceed)

| # | Question | Options | Your Call |
|---|----------|---------|-----------|
| 1 | **Frontend approach** | A) Simple HTML/JS<br>B) React app<br>C) Retool/low-code<br>D) You tell me | |
| 2 | **Who updates from field?** | A) Just you/PM<br>B) Lead techs<br>C) All field techs | |
| 3 | **How many projects to migrate first?** | A) Just Garney 677562<br>B) 2-3 active projects<br>C) All active | |

### Can Wait

| Question | Notes |
|----------|-------|
| Billing integration | Nice to have, not blocking |
| RESA system integration | Explicitly deferred |
| PSS Portal | Lower priority than project tracking |
| Multi-user permissions | Start simple, add later |

---

## Immediate Next Steps

### Desktop Claude (Me)
1. [ ] Create migration script for Garney 677562 tracker
2. [ ] Document exact field mappings: Excel → Database
3. [ ] Generate sample queries for dashboard views

### VS Code Claude  
1. [ ] Finish loading test data (11, 12 SQL files)
2. [ ] Create field tracker HTML prototype
3. [ ] Create project summary dashboard prototype

### You
1. [ ] Answer the 3 blocking questions above
2. [ ] List your other active project trackers (filenames)
3. [ ] Identify who needs access (names/roles)

---

## What Success Looks Like

**Week 1**: 
- Garney project visible in web dashboard
- Can filter/view like your Excel sheets
- Field updates possible without Excel

**Week 2**:
- 3-5 projects migrated
- "All projects" view working
- PM can see status across everything

**Week 4**:
- New projects created in system (not Excel)
- Excel trackers archived
- 1-2 hours/day saved on status tracking

---

## Your Tracker → Database Mapping (Reference)

### All_Tasks columns → Database fields

| Excel Column | Database Table.Field | Notes |
|--------------|---------------------|-------|
| Scope | scopes.scope_name | |
| NETA_Standard | apparatus.apparatus_type or task field | ATS/MTS |
| Task_ID | tasks.task_number | e.g., "1.1.1" |
| Task | tasks.task_name | e.g., "SES-00-001" |
| Apparatus | apparatus.apparatus_name | |
| Designation | apparatus.apparatus_designation | |
| Drawing | Could add to apparatus or task | |
| Date Due | apparatus.anticipated_start or task.planned_end | |
| Notes | apparatus.notes | |
| Assessment | apparatus.assessment | ENUM matches |
| DATASHEET | Could add boolean field | |
| DATE COMPLETED | apparatus.actual_end | |
| NOTES2 | apparatus.notes (combine) | |
| % COMPLETION | apparatus.percent_complete | |
| TASK DELAYS | Could add field | |
| Apparatus Hours | apparatus.quoted_hours | |
| Remaining Hours | Calculated (quoted - actual) | |
| ACTUAL HOURS | apparatus.actual_hours | |
| STATUS | apparatus.status | Map to ENUM |
| AVAILABILITY | Could add field or use status | |
| PRIORITY | Could add field | |
| Apparatus Category | apparatus.equipment_type or link to apparatus_types | |

### Status Mapping

| Excel Status | Database ENUM |
|--------------|---------------|
| COMPLETED | Complete |
| IN PROGRESS | In Progress |
| NOT STARTED | Not Started |
| OVERDUE | (calculated from dates) |
| ISSUE LOG | Could use Pending Review + notes |

### Assessment Mapping  

| Excel Assessment | Database ENUM |
|------------------|---------------|
| ACCEPTABLE | Pass |
| MINOR DEFICIENCY | Marginal |
| NON-SERVICEABLE | Fail |

---

**Bottom Line**: You built something that works. Now we make it scale.

The database is ready. We need to:
1. Get your data IN
2. Give you views OUT
3. Let field update STATUS

Everything else can wait.
