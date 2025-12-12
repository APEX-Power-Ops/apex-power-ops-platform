# Session Notes: December 11, 2025 - Schema & Operations Discussion

## Session Summary
Deep dive into Excel tracker data structure, operational visibility requirements, and schema additions needed to support multi-project operations management.

---

## ⭐ Why This Session Matters

This discussion captured the **requirements discovery** that should happen at project start - answers to fundamental questions:

1. **What are the pain points?** → Connecteam shows WHO/WHERE/WHEN but not WHAT/WHY
2. **What's the current workaround?** → Excel trackers built to fill visibility gaps
3. **What's changed?** → Scaling from 5 to 15 projects broke "fits in your head" approach
4. **What does success look like?** → Centralized visibility of everything, real-time
5. **What's MVP?** → Operations dashboard that answers resource allocation questions

These answers ARE the requirements foundation. Everything else flows from them.

---

## Key Insights Captured

### 1. The Scaling Problem
> "We got big enough where memory and existing methods become failure points."

- 5 projects → fits in your head
- 10-15 projects → requires system support
- Current tools (Connecteam, PowerDB, CRM) don't answer operational questions

### 2. What Connecteam Lacks
- Shows: WHO is WHERE, WHEN (schedule)
- Missing: WHAT can be worked, WHY blocked, HOW to prioritize, WHAT equipment needed
- No decision support for resource allocation

### 3. The Excel Tracker Value
- You built the visibility that didn't exist
- Data collection → actionable metrics → resource decisions
- But it's Excel = fragile, single-user, not real-time

### 4. Schema Drives Visibility
> "The views aren't available if the fields and schema doesn't provide for them."

---

## Files Created This Session

| File | Purpose | Status |
|------|---------|--------|
| `Supabase/schema/09_schema_additions.sql` | New fields + operational views | ✅ Created |
| `Supabase/schema/09b_enum_updates.sql` | Assessment enum alignment | ✅ Created |
| `Supabase/EXCEL_TO_DATABASE_MAPPING.md` | Field transformation guide | ✅ Created |
| `Supabase/SCHEMA_REFERENCE.md` | Updated with new views | ✅ Updated |

---

## Schema Additions (09_schema_additions.sql)

### New Apparatus Fields
- [ ] `availability` - Ready / On Hold / Not Available (CRITICAL for operations)
- [ ] `date_due` - Schedule tracking
- [ ] `designation` - Equipment ID
- [ ] `drawing_reference` - Reference to electrical drawing
- [ ] `datasheet_complete` - Progress indicator
- [ ] `task_delays` - Delay count
- [ ] `priority` - Work prioritization (1=High, 2=Med, 3=Low)

### Rollup Date Pattern (from Dataverse)
All levels (Task, Scope, Project) get:
- [ ] `date_due` - Target date
- [ ] `earliest_*_due` - MIN of child due dates
- [ ] `latest_*_due` - MAX of child due dates
- [ ] `earliest_*_start` - First work started
- [ ] `latest_*_complete` - Last work finished

### New Operational Views
- [ ] `v_apparatus_operational` - Daily scheduling
- [ ] `v_project_apparatus_summary` - Per-project KPIs (your Excel dashboard)
- [ ] `v_apparatus_by_category` - Category breakdown table
- [ ] `v_master_operations` - **THE GOD VIEW** - All projects at once
- [ ] `v_resource_allocation` - Where to send people
- [ ] `v_equipment_needs` - Test equipment planning
- [ ] `v_blockers_summary` - What's stopping us
- [ ] `v_schedule_health` - At-risk identification
- [ ] `v_task_rollup_dates` - Task aggregations
- [ ] `v_scope_rollup_dates` - Scope aggregations
- [ ] `v_project_rollup_dates` - Executive rollups

---

## Excel Tracker Analysis (Garney)

### Data Examined
- File: `Garney- Central Mesa Reuse Tracker #677562.xlsm`
- Table: `tbl_PowerBI_Data` - 2,249 rows, 48 columns
- Real operational data showing field usage patterns

### Key Field Mappings Identified
| Excel | Database | Notes |
|-------|----------|-------|
| STATUS | apparatus.status | Case normalize |
| AVAILABILITY | apparatus.availability | NEW - Ready/On Hold/Not Available |
| Assessment | apparatus.assessment | Add NETA values to enum |
| Date Due | apparatus.date_due | NEW - Excel serial → DATE |
| DATASHEET | apparatus.datasheet_complete | NEW - boolean |
| Notes | apparatus.notes | Direct |

### Assessment Values Discovered
- ACCEPTABLE → Acceptable (add to enum)
- NON-SERVICEABLE → Non-Serviceable (add to enum)
- MINOR DEFICIENCY → Minor Deficiency (add to enum)

---

## TODO Items for Next Session

### High Priority - Deploy Schema
1. [ ] Review `09_schema_additions.sql` for any adjustments
2. [ ] Deploy to Supabase (run SQL)
3. [ ] Verify views work with existing data
4. [ ] Test with sample queries

### Medium Priority - Data Import
5. [ ] Update import function with new field mappings
6. [ ] Add value transformation functions (status, availability, assessment)
7. [ ] Add Excel date conversion function
8. [ ] Test import with Garney tracker data

### Lower Priority - Refinements
9. [ ] Review enum values - are current options complete?
10. [ ] Consider billing structure (20+ Excel columns → derived views?)
11. [ ] PSS status views (similar pattern to project operations)
12. [ ] Document registry table (mentioned as gap)

---

## Questions to Resolve

1. **Assessment enum** - Keep both old values (Pass/Fail) AND new (Acceptable/Non-Serviceable)?
2. **Billing calculations** - Store vs derive? (Excel has 20+ billing columns)
3. **Priority values** - Integer (1,2,3) or enum (High/Medium/Low)?
4. **CRM integration** - Manual Job # entry or API query possible?

---

## Key Quotes from Session

> "Visibility internally is the critical aspect. Centralized visibility of everything."

> "Priority is managing what we have... these are exactly what I expect, real questions to real gaps"

> "The idea behind the tracker in the field is to gather data, status, details that become actionable, insightful metrics or KPIs for the visibility layer we lack"

> "Scheduling, resource allocation, due dates - all of these things are missing from our day to day operational view"

> "These things we're building will fundamentally change how we do things"

---

## Dashboard Concept (From Your Excel Screenshot)

### KPI Header
```
READY TO WORK | TOTAL APPARATUS | COMPLETED | REMAINING | COMPLETION % | ISSUES | PAST DUE
     12       |      143        |     99    |    44     |   61.26%     |   4    |    0
```

### Category Breakdown
```
Apparatus Category    | Total | Completed | Remaining | % Complete | Ready | Blocked
Instrument Transformers|  36  |    36     |     0     |   100%     |   0   |    0
Conductors            |  32  |    16     |    16     |    50%     |   0   |   16
Protective Relay      |  11  |     1     |    10     |     9%     |   0   |   10
...
```

This IS the MVP dashboard. Schema supports it. Views generate it.

---

## Next Session Checklist

- [ ] Read this file first
- [ ] Check PROJECT_STATUS.md for overall context
- [ ] Deploy 09_schema_additions.sql if not done
- [ ] Work through TODO items above
