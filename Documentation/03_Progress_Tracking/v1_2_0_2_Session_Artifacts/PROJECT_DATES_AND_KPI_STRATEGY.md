# PROJECT DATES & KPI STRATEGY
## RESA Power Project Tracker - Phase 2 Enhancement

**Date:** November 14, 2025  
**Purpose:** Strategic plan for date tracking and KPI implementation  
**Status:** Design Phase - Ready for Implementation

---

## 🎯 EXECUTIVE SUMMARY

This document outlines the date field architecture and KPI/metrics strategy for the RESA Power Project Tracker, specifically tailored for NETA electrical testing projects.

**Key Additions Proposed:**
- 📅 10 date fields (5 at Scope, 5 at Project)
- 📊 15 calculated fields for schedule metrics
- 📈 12 KPI rollup fields for quality/productivity
- ⚠️ 3 deficiency tracking rollups

**Implementation Priority:**
- **Phase 2A (Now):** Core date fields + basic schedule metrics (5 hours)
- **Phase 2B (Next Week):** Quality metrics + apparatus assessment tracking (4 hours)
- **Phase 2C (Week 3):** Advanced KPIs + dashboard integration (6 hours)

---

## 📅 DATE FIELD ARCHITECTURE

### **SCOPE LEVEL - Date Fields** (5 new fields)

These track the schedule for each scope (e.g., "MTS Testing" or "ATS Switchgear")

#### **1. Date_Available** (Date field)
```
Field Name: cr950_date_available
Display Name: Date Available
Type: Date Only
Required: No
Description: Date when equipment/site is available for testing
Business Logic: Set by PM when client confirms access
```

**Use Case:** "MTS Testing can't start until Jan 15 when equipment is energized"

---

#### **2. Planned_Start_Date** (Date field)
```
Field Name: cr950_planned_start_date
Display Name: Planned Start Date
Type: Date Only
Required: Business Recommended
Description: Scheduled date to begin testing this scope
Business Logic: Set during project planning, may adjust based on Date_Available
```

**Use Case:** "We plan to start ATS Testing on Feb 1"

---

#### **3. Actual_Start_Date** (Date field)
```
Field Name: cr950_actual_start_date
Display Name: Actual Start Date
Type: Date Only
Required: No
Description: Date testing actually began for this scope
Business Logic: Auto-populated when first apparatus marked "In Progress"
Alternative: Manually set by PM when crew arrives on site
```

**Use Case:** "MTS Testing actually started Feb 3 (2 days late due to weather)"

---

#### **4. Target_Completion_Date** (Date field)
```
Field Name: cr950_target_completion_date
Display Name: Target Completion Date
Type: Date Only
Required: Business Recommended
Description: Planned completion date for this scope
Business Logic: Set during project planning, drives schedule metrics
```

**Use Case:** "ATS Testing must finish by March 15 per contract"

---

#### **5. Actual_Completion_Date** (Date field)
```
Field Name: cr950_actual_completion_date
Display Name: Actual Completion Date
Type: Date Only
Required: No
Description: Date scope was actually completed
Business Logic: Auto-populated when Percent_Complete reaches 100%
Alternative: Manually set by PM
```

**Use Case:** "MTS Testing completed March 12 (3 days early!)"

---

### **SCOPE LEVEL - Calculated Date Fields** (4 new calculated fields)

#### **6. Days_To_Start** (Whole Number - Calculated)
```
Formula: 
IF(Actual_Start_Date = NULL AND Planned_Start_Date != NULL,
   DATEDIFF(TODAY(), Planned_Start_Date, DAYS),
   NULL)

Purpose: How many days until scope starts (negative = overdue to start)
Display: "-5 days" (started 5 days ago) or "+10 days" (starts in 10 days)
```

**Dashboard Use:** "MTS Testing starts in 3 days - are crews ready?"

---

#### **7. Days_In_Progress** (Whole Number - Calculated)
```
Formula:
IF(Actual_Start_Date != NULL AND Actual_Completion_Date = NULL,
   DATEDIFF(Actual_Start_Date, TODAY(), DAYS),
   NULL)

Purpose: How many days scope has been in progress
Display: "15 days in progress"
```

**Dashboard Use:** "ATS Testing has been running for 45 days"

---

#### **8. Days_To_Target** (Whole Number - Calculated)
```
Formula:
IF(Actual_Completion_Date = NULL AND Target_Completion_Date != NULL,
   DATEDIFF(TODAY(), Target_Completion_Date, DAYS),
   NULL)

Purpose: Days remaining until target (negative = overdue)
Display: "-7 days" (7 days overdue) or "+14 days" (14 days remaining)
```

**Dashboard Use:** "⚠️ MTS Testing is 7 days behind schedule"

---

#### **9. Schedule_Variance_Days** (Whole Number - Calculated)
```
Formula:
IF(Actual_Completion_Date != NULL AND Target_Completion_Date != NULL,
   DATEDIFF(Target_Completion_Date, Actual_Completion_Date, DAYS),
   NULL)

Purpose: Actual vs planned completion (positive = early, negative = late)
Display: "+3 days" (finished 3 days early) or "-5 days" (5 days late)
```

**Dashboard Use:** "MTS completed 3 days early ✅, ATS completed 5 days late ⚠️"

---

### **PROJECT LEVEL - Date Fields** (5 new fields)

These track overall project schedule

#### **10. Contract_Award_Date** (Date field)
```
Field Name: cr950_contract_award_date
Display Name: Contract Award Date
Type: Date Only
Required: Business Recommended
Description: Date contract was awarded/signed
Business Logic: Set once during project creation
```

**Use Case:** "LASNAP16 awarded on Sept 15, 2024"

---

#### **11. Project_Planned_Start** (Date field OR Calculated Rollup)
```
Option A - Manual Field:
Field Name: cr950_project_planned_start
Display Name: Project Planned Start
Type: Date Only
Required: Business Recommended
Description: Overall project planned start date

Option B - Calculated Rollup (RECOMMENDED):
Type: Rollup (MIN)
Source: Project Scope.Planned_Start_Date
Aggregate: Earliest (MIN)
Description: Automatically uses earliest scope planned start
```

**Recommendation:** Use Rollup - automatically stays accurate as scopes adjust

---

#### **12. Project_Actual_Start** (Calculated Rollup)
```
Field Name: cr950_project_actual_start
Display Name: Project Actual Start
Type: Rollup (MIN)
Source: Project Scope.Actual_Start_Date
Aggregate: Earliest (MIN)
Description: Date first scope actually started
```

**Use Case:** "Project actually began Feb 3 when MTS Testing started"

---

#### **13. Project_Target_Completion** (Date field)
```
Field Name: cr950_project_target_completion
Display Name: Project Target Completion
Type: Date Only
Required: Business Required
Description: Contractual project completion date
Business Logic: From contract, drives all schedule metrics
```

**Use Case:** "LASNAP16 must complete by April 30 per contract"

---

#### **14. Project_Actual_Completion** (Calculated Rollup)
```
Field Name: cr950_project_actual_completion
Display Name: Project Actual Completion
Type: Rollup (MAX)
Source: Project Scope.Actual_Completion_Date
Aggregate: Latest (MAX)
Description: Date last scope completed
Alternative: Set when Project.Percent_Complete = 100%
```

**Use Case:** "Project completed April 27 (3 days early!)"

---

### **PROJECT LEVEL - Calculated Date Fields** (3 new calculated fields)

#### **15. Project_Days_To_Target** (Whole Number - Calculated)
```
Formula:
IF(Project_Actual_Completion = NULL AND Project_Target_Completion != NULL,
   DATEDIFF(TODAY(), Project_Target_Completion, DAYS),
   NULL)

Purpose: Days until contract completion (negative = overdue)
Display: Primary project schedule KPI
```

**Dashboard Use:** "⚠️ Project is 15 days behind schedule"

---

#### **16. Project_Schedule_Variance** (Whole Number - Calculated)
```
Formula:
IF(Project_Actual_Completion != NULL AND Project_Target_Completion != NULL,
   DATEDIFF(Project_Target_Completion, Project_Actual_Completion, DAYS),
   NULL)

Purpose: Final schedule performance (positive = early, negative = late)
Display: Post-project metric
```

**Dashboard Use:** "LASNAP16 finished 3 days ahead of schedule ✅"

---

#### **17. Project_Duration_Days** (Whole Number - Calculated)
```
Formula:
IF(Project_Actual_Start != NULL,
   IF(Project_Actual_Completion != NULL,
      DATEDIFF(Project_Actual_Start, Project_Actual_Completion, DAYS),
      DATEDIFF(Project_Actual_Start, TODAY(), DAYS)),
   NULL)

Purpose: How long project has been running
Display: "Project has been active for 87 days"
```

---

## 📊 QUALITY & ASSESSMENT KPIs

### **APPARATUS LEVEL - Assessment Tracking**

**You're already creating this - Perfect!** ✅

```
Field Name: cr950_apparatus_assessment
Display Name: Apparatus Assessment
Type: Choice (Global)
Required: Business Recommended
Values:
  - Acceptable (0)
  - Minor Deficiency (1)
  - Non-Serviceable (2)

Description: NETA assessment result for apparatus
```

**Critical Business Logic:**
- Set by technician after testing
- Drives deficiency tracking
- May impact revenue recognition
- Requires follow-up if not "Acceptable"

---

### **TASK LEVEL - Assessment Rollups** (3 new rollup fields)

#### **18. Acceptable_Count** (Rollup)
```
Field Name: cr950_acceptable_count
Source: Apparatus where Assessment = "Acceptable"
Aggregate: COUNT
Purpose: Number of apparatus that passed
```

---

#### **19. Minor_Deficiency_Count** (Rollup)
```
Field Name: cr950_minor_deficiency_count
Source: Apparatus where Assessment = "Minor Deficiency"
Aggregate: COUNT
Purpose: Number of apparatus with minor issues
```

---

#### **20. Non_Serviceable_Count** (Rollup)
```
Field Name: cr950_non_serviceable_count
Source: Apparatus where Assessment = "Non-Serviceable"
Aggregate: COUNT
Purpose: Number of apparatus that failed
```

---

### **TASK LEVEL - Quality Calculated Fields** (2 new calculated fields)

#### **21. Pass_Rate_Percentage** (Decimal - Calculated)
```
Formula:
IF(Total_Apparatus_Count > 0,
   (Acceptable_Count / Total_Apparatus_Count) * 100,
   0)

Purpose: What % of apparatus passed
Display: "Pass Rate: 87.5%"
```

**Dashboard Use:** "Task has 87.5% pass rate (35 of 40 items acceptable)"

---

#### **22. Deficiency_Rate_Percentage** (Decimal - Calculated)
```
Formula:
IF(Total_Apparatus_Count > 0,
   ((Minor_Deficiency_Count + Non_Serviceable_Count) / Total_Apparatus_Count) * 100,
   0)

Purpose: What % of apparatus had issues
Display: "Deficiency Rate: 12.5%"
```

**Dashboard Use:** "⚠️ Task has 12.5% deficiency rate - investigate"

---

### **SCOPE & PROJECT LEVELS - Assessment Rollups**

**Same pattern as Tasks:**
- Acceptable_Count (rollup from child tasks)
- Minor_Deficiency_Count (rollup from child tasks)
- Non_Serviceable_Count (rollup from child tasks)
- Pass_Rate_Percentage (calculated)
- Deficiency_Rate_Percentage (calculated)

**This cascades quality metrics up the hierarchy!**

---

## 📈 PRODUCTIVITY & PERFORMANCE KPIs

### **TASK LEVEL - Productivity Metrics** (2 new calculated fields)

#### **23. Hours_Per_Apparatus** (Decimal - Calculated)
```
Formula:
IF(Completed_Apparatus_Count > 0,
   Total_Actual_Hours / Completed_Apparatus_Count,
   0)

Purpose: How many hours per apparatus on average
Display: "4.2 hours/apparatus"
```

**Dashboard Use:** "Task averaging 5.5 hrs/apparatus (budgeted 4.0) - investigate"

---

#### **24. Apparatus_Per_Day** (Decimal - Calculated)
```
Formula:
IF(Days_In_Progress > 0,
   Completed_Apparatus_Count / Days_In_Progress,
   0)

Purpose: Daily completion rate
Display: "2.5 apparatus/day"
```

**Dashboard Use:** "Crew completing 2.5 items/day (need 3.0 to hit target)"

---

### **PROJECT LEVEL - Performance Dashboard Fields** (4 new calculated)

#### **25. Overall_Pass_Rate** (Decimal - Calculated)
```
Formula: (Acceptable_Count / Total_Apparatus_Count) * 100
Display: "Overall Quality: 92.3%"
```

---

#### **26. Schedule_Performance_Index** (Decimal - Calculated)
```
Formula:
Percent_Complete / Planned_Percent_Complete
Where Planned_Percent_Complete = (Days_Elapsed / Total_Days_Planned) * 100

Result:
  > 1.0 = Ahead of schedule
  = 1.0 = On schedule
  < 1.0 = Behind schedule

Display: "SPI: 1.07 (7% ahead of schedule)"
```

---

#### **27. Cost_Performance_Index** (Decimal - Calculated)
```
Formula:
Budgeted_Hours / Total_Actual_Hours

Result:
  > 1.0 = Under budget
  = 1.0 = On budget
  < 1.0 = Over budget

Display: "CPI: 0.95 (5% over budget)"
```

---

#### **28. Forecast_Completion_Date** (Date - Calculated)
```
Formula:
Current_Date + (Days_Remaining / (Percent_Complete / Days_Elapsed))

Purpose: Based on current pace, when will project finish?
Display: "Forecast: May 5 (5 days late)"
```

---

## 🎯 NETA-SPECIFIC KPIs

### **Industry-Standard Metrics for Electrical Testing**

#### **Safety Metrics** (Future Enhancement)
```
- Incident_Count (rollup from safety incidents table)
- Days_Since_Last_Incident (calculated)
- OSHA_Recordable_Rate
- Near_Miss_Count
```

**Priority:** Medium (add after core system operational)

---

#### **Documentation Compliance**
```
- Reports_Submitted_Count (vs scopes completed)
- Reports_Pending_Count
- Average_Report_Turnaround_Days
- Client_Approval_Days
```

**Priority:** Medium (add when report workflow implemented)

---

#### **Change Management**
```
- Change_Order_Count (number of scope changes)
- Change_Order_Value (dollar impact)
- Change_Order_Approval_Days
```

**Priority:** Low (nice to have)

---

## 🏗️ IMPLEMENTATION STRATEGY

### **Phase 2A - Core Dates & Schedule Metrics** (Now - 5 hours)

**Add to SCOPE table:**
1. Date_Available (date field)
2. Planned_Start_Date (date field)
3. Actual_Start_Date (date field)
4. Target_Completion_Date (date field)
5. Actual_Completion_Date (date field)
6. Days_To_Start (calculated)
7. Days_In_Progress (calculated)
8. Days_To_Target (calculated)
9. Schedule_Variance_Days (calculated)

**Add to PROJECTS table:**
10. Contract_Award_Date (date field)
11. Project_Planned_Start (rollup MIN from scopes)
12. Project_Actual_Start (rollup MIN from scopes)
13. Project_Target_Completion (date field)
14. Project_Actual_Completion (rollup MAX from scopes)
15. Project_Days_To_Target (calculated)
16. Project_Schedule_Variance (calculated)
17. Project_Duration_Days (calculated)

**Testing:** Create test project with 2 scopes, set dates, verify calculations

**Result:** Complete schedule visibility and tracking ✅

---

### **Phase 2B - Quality Metrics** (Next Week - 4 hours)

**Add to APPARATUS table:**
1. Apparatus_Assessment (choice field) - **YOU'RE DOING THIS NOW** ✅

**Add to TASKS table:**
2. Acceptable_Count (rollup)
3. Minor_Deficiency_Count (rollup)
4. Non_Serviceable_Count (rollup)
5. Pass_Rate_Percentage (calculated)
6. Deficiency_Rate_Percentage (calculated)
7. Hours_Per_Apparatus (calculated)
8. Apparatus_Per_Day (calculated)

**Add to SCOPE table:**
9-13. Same 5 quality fields (rollup from tasks)

**Add to PROJECTS table:**
14-18. Same 5 quality fields (rollup from scopes)

**Testing:** Set apparatus assessments, verify pass rates calculate correctly

**Result:** Complete quality tracking hierarchy ✅

---

### **Phase 2C - Advanced KPIs** (Week 3 - 6 hours)

**Add to PROJECTS table:**
1. Overall_Pass_Rate (calculated)
2. Schedule_Performance_Index (calculated)
3. Cost_Performance_Index (calculated)
4. Forecast_Completion_Date (calculated)

**Power BI Dashboard:**
5. Create executive dashboard with all KPIs
6. Build schedule performance charts
7. Add quality metrics visualization
8. Create productivity tracking

**Testing:** Import full project, verify dashboard displays correctly

**Result:** Executive-grade reporting and analytics ✅

---

## 📊 PRIORITY MATRIX

### **What to Add First (Priority Order)**

| Priority | Category | Fields | Time | Business Impact |
|----------|----------|--------|------|-----------------|
| **1. CRITICAL** | Core Dates | 9 scope + 8 project | 5 hrs | Schedule tracking |
| **2. HIGH** | Apparatus Assessment | 1 choice field | 15 min | **YOU'RE DOING THIS** ✅ |
| **3. HIGH** | Quality Rollups | 15 rollup/calc | 4 hrs | Deficiency tracking |
| **4. MEDIUM** | Productivity | 2 calculated | 1 hr | Performance insight |
| **5. MEDIUM** | Advanced KPIs | 4 calculated | 2 hrs | Executive dashboards |
| **6. LOW** | Safety/Compliance | Future | TBD | Nice to have |

---

## 🎯 RECOMMENDED APPROACH

### **Today (After Verification Testing):**

**Option A - Add Dates First (Recommended)**
1. Complete Phase 1 verification testing (NETA_Standard, Percent_Complete, etc.)
2. Add core date fields to Scope table (5 fields)
3. Add calculated date fields to Scope table (4 calculated)
4. Add core date fields to Projects table (5 fields)
5. Add calculated date fields to Projects table (3 calculated)
6. Test with sample dates
7. Export as v1.2.0.3

**Time:** 5 hours  
**Result:** Complete schedule tracking capability

---

**Option B - Continue with Assessment (Current Path)**
1. Finish creating Apparatus_Assessment field ✅
2. Add assessment rollups to Tasks (3 rollups)
3. Add quality calculated fields to Tasks (2 calculated)
4. Cascade same to Scope and Project
5. Test with sample data
6. Export as v1.2.0.3

**Time:** 4 hours  
**Result:** Complete quality tracking capability

---

### **My Recommendation:**

**Do BOTH in sequence:**

**Session 1 (Today - 1 hour):**
- Finish Apparatus_Assessment field
- Run verification testing from earlier checklist
- Export stable v1.2.0.3 with assessment tracking

**Session 2 (Tomorrow - 5 hours):**
- Add all date fields (Phase 2A)
- Test schedule calculations
- Export v1.2.1.0 with complete date tracking

**Session 3 (Next Week - 4 hours):**
- Add quality rollups and productivity metrics (Phase 2B)
- Export v1.2.2.0

**Result:** In 3 focused sessions, you'll have:
- ✅ 100% calculated/rollup fields (already done)
- ✅ Apparatus assessment tracking
- ✅ Complete schedule management
- ✅ Quality metrics hierarchy
- ✅ Productivity KPIs
- ✅ Ready for Canvas app development

---

## 💡 KEY INSIGHTS

### **Why These KPIs Matter for NETA Projects:**

1. **Schedule Metrics** → Contract compliance, penalty avoidance
2. **Quality Metrics** → Client satisfaction, reputation, follow-on work
3. **Productivity Metrics** → Resource optimization, accurate future bids
4. **Assessment Tracking** → Regulatory compliance, deficiency management

### **How This Differs from Generic Project Management:**

**NETA-Specific Considerations:**
- Apparatus assessment is regulatory requirement (not optional)
- Pass/fail rates impact client acceptance
- Schedule delays often due to equipment availability (not just crew)
- Deficiencies may require re-testing (cost impact)
- Reports must be NETA-certified (documentation critical)

**Your Solution Handles:**
- ✅ NETA standards (ATS/MTS) already integrated
- ✅ Apparatus-level granularity (not task-level only)
- ✅ Assessment tracking (Acceptable/Minor/Non-Serviceable)
- ✅ Hours tracking for labor-intensive testing
- ✅ Hierarchical rollups (apparatus → task → scope → project)

---

## 🚀 NEXT STEPS

### **Immediate Actions:**

1. **Finish Apparatus_Assessment field** (15 min)
   - Save and publish
   - Test on sample apparatus
   - Verify choice values work

2. **Decide: Dates or Quality first?** (Your choice)
   - Dates = better for project scheduling
   - Quality = better for client reporting
   - Both are valuable

3. **Create implementation checklist** (30 min)
   - Decide which phase to tackle first
   - List exact fields to add
   - Plan testing approach

4. **Execute Phase 2A or 2B** (4-5 hours)
   - Add fields systematically
   - Test calculations
   - Export new version

---

## 📋 FIELD COUNT SUMMARY

**Current State (v1.2.0.2):**
- 26 calculated/rollup fields ✅

**After Phase 2A (Dates):**
- +17 date-related fields
- Total: 43 advanced fields

**After Phase 2B (Quality):**
- +15 quality/productivity fields
- Total: 58 advanced fields

**After Phase 2C (Advanced KPIs):**
- +4 performance KPIs
- Total: 62 advanced fields

**This is a sophisticated enterprise system!** 🎯

---

## ✅ DECISION POINT

**Jason, you need to decide:**

### **Option 1: Dates First**
**Pros:**
- Schedule management is immediate need
- Supports current project tracking
- Contract compliance visibility
- Client status reporting

**Cons:**
- Quality metrics delayed
- Assessment tracking not fully utilized yet

**Best If:** You need schedule visibility ASAP

---

### **Option 2: Quality First**
**Pros:**
- Leverages Apparatus_Assessment you're creating now
- NETA compliance reporting ready
- Deficiency tracking operational
- Client quality metrics available

**Cons:**
- Schedule management delayed
- No date-based alerting yet

**Best If:** Client quality reporting is priority

---

### **Option 3: Hybrid (Recommended)**
**Do minimal version of both:**

**Week 1:**
- Finish Apparatus_Assessment
- Add core 5 date fields to Scope
- Add core 3 date fields to Project
- Add basic Pass_Rate calculation

**Result:** Basic schedule tracking + quality tracking

**Week 2:**
- Add all calculated date fields
- Add all quality rollups
- Add productivity metrics

**Result:** Complete Phase 2

**Best If:** You want balanced progress

---

**What's your preference?** I can create detailed implementation specs for whichever path you choose!

---

**END OF STRATEGY DOCUMENT**
