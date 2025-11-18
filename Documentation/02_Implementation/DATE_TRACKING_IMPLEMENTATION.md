# Date Tracking Implementation Spec

**Version:** 1.0.0  
**Created:** November 16, 2025  
**Purpose:** Add date tracking fields across all tables (Apparatus → Tasks → Scopes → Projects) for PM and Operations visibility

---

## 🎯 Overview

**Goal:** Enable schedule tracking, variance analysis, and workload forecasting through consistent date fields at all levels.

**Architecture:** Date fields at Apparatus level roll up to Tasks, Scopes, and Projects using MIN/MAX rollups with filters.

**KPIs Enabled:**
- Schedule variance (anticipated vs actual)
- On-time completion percentage
- Work in progress (started but not complete)
- Upcoming work (anticipated but not started)
- Duration analysis (actual start → completion)
- Resource timeline visibility

---

## 📋 Field Definitions

### **Apparatus Table (3 New Fields)**

#### **1. Anticipated Start**
```
Display Name: Anticipated Start
Schema Name: cr950_anticipated_start
Type: Date and Time
Behavior: User Local
Required: No
Description: When work is planned to begin on this apparatus
Usage: PM sets during project planning
Visibility: PM, Operations, Field Techs
Note: User Local ensures timezone-aware scheduling for multi-location teams
```

#### **2. Actual Start**
```
Display Name: Actual Start
Schema Name: cr950_actual_start
Type: Date and Time
Behavior: User Local
Required: No
Description: When work actually began on this apparatus
Usage: Field tech sets when starting work (or auto-populated by Power Automate)
Visibility: All users
Auto-populate Option: Power Automate sets to NOW() when Completion Status changes from "Not Started"
Note: Captures exact start time in field tech's timezone
```

#### **3. Date Completed**
```
Display Name: Date Completed
Schema Name: cr950_date_completed
Type: Date and Time
Behavior: User Local
Required: No
Description: When work was finished on this apparatus (auto-populated)
Usage: Auto-set by Power Automate when Completion Status = "Complete"
Visibility: All users (read-only on forms)
Auto-populate: Power Automate flow sets to NOW() when status = Complete
Critical: Too important for revenue recognition to rely on manual entry
Override: Finance can manually adjust if needed for corrections
Note: May already exist - verify before adding
```

---

## 📊 Rollup Architecture

### **Tasks Table (6 Rollup Fields)**

#### **Rollup 1: Earliest Anticipated Start**
```
Display Name: Earliest Anticipated Start
Schema Name: cr950_earliest_anticipated_start
Type: Date Only (Rollup)
Related Entity: Apparatus
Rollup Field: Anticipated Start
Aggregate: MIN
Filter: None (all apparatus in task)
Description: Earliest planned start date among all apparatus in this task
Usage: Task scheduling, workload planning
```

#### **Rollup 2: Latest Anticipated Start**
```
Display Name: Latest Anticipated Start
Schema Name: cr950_latest_anticipated_start
Type: Date Only (Rollup)
Related Entity: Apparatus
Rollup Field: Anticipated Start
Aggregate: MAX
Filter: None
Description: Latest planned start date among all apparatus in this task
Usage: Task duration visibility
```

#### **Rollup 3: Earliest Actual Start**
```
Display Name: Earliest Actual Start
Schema Name: cr950_earliest_actual_start
Type: Date Only (Rollup)
Related Entity: Apparatus
Rollup Field: Actual Start
Aggregate: MIN
Filter: Actual Start IS NOT NULL
Description: When work actually began on this task (first apparatus started)
Usage: Schedule variance analysis
```

#### **Rollup 4: Latest Actual Start**
```
Display Name: Latest Actual Start
Schema Name: cr950_latest_actual_start
Type: Date Only (Rollup)
Related Entity: Apparatus
Rollup Field: Actual Start
Aggregate: MAX
Filter: Actual Start IS NOT NULL
Description: Most recent apparatus start date in this task
Usage: Work progression tracking
```

#### **Rollup 5: Earliest Completion Date**
```
Display Name: Earliest Completion Date
Schema Name: cr950_earliest_completion_date
Type: Date Only (Rollup)
Related Entity: Apparatus
Rollup Field: Date Completed
Aggregate: MIN
Filter: Date Completed IS NOT NULL
Description: First apparatus completed in this task
Usage: Task progress visibility
```

#### **Rollup 6: Latest Completion Date**
```
Display Name: Latest Completion Date
Schema Name: cr950_latest_completion_date
Type: Date Only (Rollup)
Related Entity: Apparatus
Rollup Field: Date Completed
Aggregate: MAX
Filter: Date Completed IS NOT NULL
Description: When task was fully completed (last apparatus finished)
Usage: Task completion tracking, duration analysis
```

---

### **Scopes Table (6 Rollup Fields)**

#### **Same Structure as Tasks:**
1. **Earliest Anticipated Start** = MIN(Apparatus.Anticipated_Start)
2. **Latest Anticipated Start** = MAX(Apparatus.Anticipated_Start)
3. **Earliest Actual Start** = MIN(Apparatus.Actual_Start WHERE NOT NULL)
4. **Latest Actual Start** = MAX(Apparatus.Actual_Start WHERE NOT NULL)
5. **Earliest Completion Date** = MIN(Apparatus.Date_Completed WHERE NOT NULL)
6. **Latest Completion Date** = MAX(Apparatus.Date_Completed WHERE NOT NULL)

**Alternative Rollup Source:** Could roll up from Tasks instead of Apparatus:
- MIN(Task.Earliest_Anticipated_Start)
- MAX(Task.Latest_Completion_Date)
- Recommendation: Roll up directly from Apparatus (more accurate, avoids double-rollup delays)

---

### **Projects Table (6 Rollup Fields)**

#### **Rollup from Scopes:**
1. **Earliest Anticipated Start** = MIN(Scope.Earliest_Anticipated_Start)
2. **Latest Anticipated Start** = MAX(Scope.Latest_Anticipated_Start)
3. **Earliest Actual Start** = MIN(Scope.Earliest_Actual_Start WHERE NOT NULL)
4. **Latest Actual Start** = MAX(Scope.Latest_Actual_Start WHERE NOT NULL)
5. **Earliest Completion Date** = MIN(Scope.Earliest_Completion_Date WHERE NOT NULL)
6. **Latest Completion Date** = MAX(Scope.Latest_Completion_Date WHERE NOT NULL)

**Why Roll Up from Scopes (not Apparatus):**
- Projects can have hundreds/thousands of apparatus records
- Scopes provide logical grouping
- Reduces rollup calculation load
- Maintains hierarchy: Apparatus → Scope → Project

---

## 📐 Calculated Fields (Optional Enhancements)

### **Apparatus Level:**

#### **Schedule Variance (Days)**
```
Type: Whole Number (Calculated)
Formula: DATEDIFF(cr950_anticipated_start, cr950_actual_start, Days)
Example: Anticipated: Jan 10, Actual: Jan 15 = 5 days late
Display: 
  - Positive number = late
  - Negative number = early
  - NULL = not yet started
```

#### **Duration (Days)**
```
Type: Whole Number (Calculated)
Formula: DATEDIFF(cr950_actual_start, cr950_date_completed, Days)
Example: Started Jan 10, Completed Jan 17 = 7 days
Display: NULL if not completed
```

#### **Is Overdue**
```
Type: Yes/No (Calculated)
Formula: 
  cr950_anticipated_start < TODAY() 
  AND cr950_actual_start IS NULL 
  AND cr950_completion_status <> "Complete"
Description: Work should have started but hasn't
Usage: Alerts, overdue reports
```

#### **Is In Progress**
```
Type: Yes/No (Calculated)
Formula: 
  cr950_actual_start IS NOT NULL 
  AND cr950_date_completed IS NULL
Description: Work started but not finished
Usage: Active work tracking
```

---

### **Task/Scope/Project Level:**

#### **Planned Duration (Days)**
```
Type: Whole Number (Calculated)
Formula: DATEDIFF(Earliest_Anticipated_Start, Latest_Anticipated_Start, Days)
Description: Planned span of work across all apparatus
```

#### **Actual Duration (Days)**
```
Type: Whole Number (Calculated)
Formula: DATEDIFF(Earliest_Actual_Start, Latest_Completion_Date, Days)
Description: Actual span from first start to last completion
```

#### **Schedule Performance**
```
Type: Whole Number (Calculated)
Formula: DATEDIFF(Earliest_Anticipated_Start, Earliest_Actual_Start, Days)
Description: How early/late work actually began
```

---

## 🎨 KPI Dashboard Views

### **For Project Managers:**

#### **View 1: Upcoming Work (Next 7 Days)**
**Filter:**
- Anticipated Start <= TODAY + 7 days
- Actual Start IS NULL
- Completion Status <> "Complete"

**Columns:**
- Apparatus Designation
- Scope
- Anticipated Start
- Assigned To
- Status

**Purpose:** See what's starting soon, ensure resources ready

---

#### **View 2: Overdue Starts**
**Filter:**
- Anticipated Start < TODAY
- Actual Start IS NULL
- Completion Status <> "Complete"

**Columns:**
- Apparatus Designation
- Scope
- Anticipated Start
- Days Overdue (calculated)
- Assigned To

**Purpose:** Identify schedule slippage, reallocate resources

---

#### **View 3: Work In Progress**
**Filter:**
- Actual Start IS NOT NULL
- Date Completed IS NULL

**Columns:**
- Apparatus Designation
- Scope
- Actual Start
- Days In Progress
- Assigned To
- Completed Hours vs Apparatus Hours

**Purpose:** Track active work, identify stalled items

---

#### **View 4: Recently Completed (Last 7 Days)**
**Filter:**
- Date Completed >= TODAY - 7 days

**Columns:**
- Apparatus Designation
- Scope
- Date Completed
- Duration (days)
- Schedule Variance
- Revenue Status

**Purpose:** Completion tracking, revenue recognition verification

---

### **For Operations:**

#### **View 5: Resource Timeline (Gantt-style data)**
**Filter:** Active projects

**Columns:**
- Scope Name
- Earliest Anticipated Start
- Latest Anticipated Start
- Earliest Actual Start
- Latest Completion Date
- Percent Complete
- Assigned Techs

**Purpose:** Workload visualization, capacity planning

---

#### **View 6: Schedule Performance Report**
**Group By:** Scope or Project

**Columns:**
- Scope Name
- Total Apparatus Count
- Completed Apparatus Count
- On Time Count (Actual Start <= Anticipated Start)
- Late Count (Actual Start > Anticipated Start)
- On Time % (calculated)

**Purpose:** Schedule adherence metrics

---

## 🔧 Implementation Steps

### **Phase 1: Add Apparatus Date Fields (15 min)**

1. Navigate to: **Apparatus > Columns**
2. Check if `Date Completed` already exists
   - If YES: Skip to step 3
   - If NO: Add field as defined above

3. Add **Anticipated Start**:
   ```
   + New Column
   Display Name: Anticipated Start
   Data Type: Date and Time
   Behavior: User Local
   Required: No
   Description: When work is planned to begin
   Save
   ```

4. Add **Actual Start**:
   ```
   + New Column
   Display Name: Actual Start
   Data Type: Date and Time
   Behavior: User Local
   Required: No
   Description: When work actually began
   Save
   ```

5. Add **Date Completed** (if doesn't exist):
   ```
   + New Column
   Display Name: Date Completed
   Data Type: Date and Time
   Behavior: User Local
   Required: No
   Description: When work was finished (auto-populated by Power Automate)
   Save
   ```

6. Make **Date Completed read-only** on Apparatus form:
   ```
   Open Apparatus main form
   Select Date Completed field
   Properties > Read-only: Yes
   Note: "Auto-populated by Power Automate when Complete"
   Save and Publish
   ```

---

### **Phase 2: Add Task Rollup Fields (20 min)**

1. Navigate to: **Tasks > Columns**

2. Add 6 rollup fields (use template):
   ```
   + New Column
   Display Name: [Field Name]
   Data Type: Rollup
   Related Table: Apparatus
   Rollup Field: [Source Field]
   Aggregate Function: [MIN or MAX]
   Filter: [If needed: Field IS NOT NULL]
   Save
   ```

3. Repeat for all 6 fields (Earliest/Latest for Anticipated, Actual, Completed)

---

### **Phase 3: Add Scope Rollup Fields (20 min)**

1. Navigate to: **Scopes > Columns**
2. Add same 6 rollup fields as Tasks
3. Source: Roll up from **Apparatus** (not Tasks)

---

### **Phase 4: Add Project Rollup Fields (20 min)**

1. Navigate to: **Projects > Columns**
2. Add 6 rollup fields
3. Source: Roll up from **Scopes** (not Apparatus directly)

---

### **Phase 5: Add Calculated Fields (Optional, 15 min)**

Add at Apparatus level:
- Schedule Variance
- Duration
- Is Overdue
- Is In Progress

Add at Task/Scope/Project level:
- Planned Duration
- Actual Duration
- Schedule Performance

---

### **Phase 6: Create KPI Views (30 min)**

1. Create 6 views as defined above
2. Test filters work correctly
3. Share with PM and Operations teams

---

### **Phase 7: Form Updates (15 min)**

1. **Apparatus Main Form:**
   - Add "Schedule" section
   - Fields: Anticipated Start, Actual Start, Date Completed
   - Add calculated fields if created

2. **Task/Scope/Project Forms:**
   - Add "Schedule Summary" section (read-only)
   - Show earliest/latest dates
   - Show calculated performance metrics

---

## ✅ Validation Tests

### **Test 1: Basic Date Entry**
1. Create test Apparatus
2. Set Anticipated Start = Tomorrow
3. Verify rollup appears in Task/Scope/Project

### **Test 2: Actual Start Tracking**
1. Set Actual Start = Today on test Apparatus
2. Verify Earliest Actual Start updates in Task/Scope/Project
3. Verify "Is In Progress" = Yes

### **Test 3: Completion Tracking**
1. Set Completion Status = "Complete"
2. Verify Date Completed auto-populated by Power Automate (within seconds)
3. Verify Latest Completion Date updates in parents
4. Verify "Is In Progress" = No
5. Try to manually edit Date Completed on form (should be read-only)

### **Test 4: Schedule Variance**
1. Apparatus 1: Anticipated = Jan 10, Actual = Jan 8 (2 days early)
2. Apparatus 2: Anticipated = Jan 15, Actual = Jan 18 (3 days late)
3. Verify calculated variance shows correctly

### **Test 5: Overdue Detection**
1. Set Anticipated Start = Yesterday
2. Leave Actual Start = NULL
3. Set Completion Status = "Not Started"
4. Verify "Is Overdue" = Yes
5. Verify appears in "Overdue Starts" view

---

## 📊 Example Data Flow

**Scenario:** Circuit Breaker Testing Project

```
APPARATUS LEVEL:
┌─────────────────────────────────────────────────────────────┐
│ CB-001 (Circuit Breaker)                                     │
├─────────────────────────────────────────────────────────────┤
│ Anticipated Start:  Jan 10, 2025                            │
│ Actual Start:       Jan 12, 2025 (2 days late)              │
│ Date Completed:     Jan 17, 2025                            │
│ Schedule Variance:  +2 days (late)                          │
│ Duration:           5 days (Jan 12 → Jan 17)                │
└─────────────────────────────────────────────────────────────┘

│ CB-002 (Circuit Breaker)                                     │
├─────────────────────────────────────────────────────────────┤
│ Anticipated Start:  Jan 15, 2025                            │
│ Actual Start:       Jan 14, 2025 (1 day early)              │
│ Date Completed:     Jan 20, 2025                            │
│ Schedule Variance:  -1 day (early)                          │
│ Duration:           6 days (Jan 14 → Jan 20)                │
└─────────────────────────────────────────────────────────────┘
                         ↓ [Rollup MIN/MAX]
TASK LEVEL:
┌─────────────────────────────────────────────────────────────┐
│ Task: Circuit Breaker Testing                                │
├─────────────────────────────────────────────────────────────┤
│ Earliest Anticipated:  Jan 10 (from CB-001)                 │
│ Latest Anticipated:    Jan 15 (from CB-002)                 │
│ Earliest Actual:       Jan 12 (from CB-001)                 │
│ Latest Actual:         Jan 14 (from CB-002)                 │
│ Earliest Completed:    Jan 17 (from CB-001)                 │
│ Latest Completed:      Jan 20 (from CB-002)                 │
│ Planned Duration:      5 days (Jan 10 → Jan 15)             │
│ Actual Duration:       8 days (Jan 12 → Jan 20)             │
│ Schedule Performance:  +2 days late start                    │
└─────────────────────────────────────────────────────────────┘
                         ↓ [Rollup MIN/MAX]
SCOPE LEVEL:
┌─────────────────────────────────────────────────────────────┐
│ Scope: Primary Switchgear                                    │
├─────────────────────────────────────────────────────────────┤
│ (Aggregates across all apparatus in scope)                   │
│ Shows earliest planned start, latest completion              │
│ Used for scope-level schedule tracking                       │
└─────────────────────────────────────────────────────────────┘
                         ↓ [Rollup MIN/MAX]
PROJECT LEVEL:
┌─────────────────────────────────────────────────────────────┐
│ Project: ABC Substation                                      │
├─────────────────────────────────────────────────────────────┤
│ (Aggregates across all scopes)                               │
│ Project start/end visibility                                 │
│ Overall schedule performance                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Business Value

### **For Project Managers:**
- ✅ See upcoming work 7 days out (resource planning)
- ✅ Identify overdue starts immediately (proactive intervention)
- ✅ Track work in progress (capacity management)
- ✅ Measure schedule adherence (KPI reporting)

### **For Operations:**
- ✅ Timeline visibility across all projects (Gantt-style data)
- ✅ Workload forecasting (what's starting when)
- ✅ Capacity planning (how many techs needed when)
- ✅ Performance metrics (on-time %, duration trends)

### **For Field Techs:**
- ✅ Know when work is planned to start (preparation)
- ✅ See their upcoming assignments (7-day view)
- ✅ Simple date entry (Actual Start button)

### **For Finance:**
- ✅ Revenue timing (completed dates drive recognition)
- ✅ Billing cycles (monthly completion reports)
- ✅ Project cost tracking (duration × labor rate)

---

## 📤 Solution Export

After implementation, export as v1.4.0.0:

**Version Numbering:**
- v1.3.0.1 = ScopeLaborDetail + ApparatusRevenue
- v1.4.0.0 = Date tracking fields across all tables

**Git Commit Message:**
```
feat: Date tracking system v1.4.0.0 - schedule visibility

- Added 3 date fields to Apparatus (Anticipated Start, Actual Start, Date Completed)
- Added 6 rollup fields to Tasks (earliest/latest for all dates)
- Added 6 rollup fields to Scopes (earliest/latest for all dates)
- Added 6 rollup fields to Projects (earliest/latest aggregates)
- Added calculated fields: Schedule Variance, Duration, Is Overdue, Is In Progress
- Created 6 KPI views (Upcoming, Overdue, In Progress, Completed, Timeline, Performance)
- Updated forms with Schedule sections
- Enables PM/Operations visibility: workload forecasting, capacity planning, schedule adherence
- Architecture: Apparatus → Tasks → Scopes → Projects rollups with MIN/MAX aggregates
- Total: 21 new fields (3 base + 18 rollups) + 4 calculated + 6 views
```

---

## 🔄 Integration with Revenue Recognition

**Date Completed triggers revenue:**
1. Field tech sets Completion Status = "Complete"
2. Power Automate flow triggers:
   a. Sets Date Completed = NOW() (exact completion timestamp)
   b. Creates ApparatusRevenue record with:
   - Apparatus Hours (from Completed_Hours)
   - Delays
   - Effective Labor Rate (from ScopeLaborDetail)
   - Revenue Status = RECOGNIZED
   - **Date Completed** (for billing period tracking)

**Revenue Reporting by Period:**
- Monthly Revenue = SUM(ApparatusRevenue WHERE Date_Completed in month)
- Completion trends = COUNT(Apparatus WHERE Date_Completed in period)
- Billing cycles aligned with completion dates

---

## ⏱️ Time Estimates

| Phase | Task | Time |
|-------|------|------|
| 1 | Add Apparatus date fields | 15 min |
| 2 | Add Task rollup fields | 20 min |
| 3 | Add Scope rollup fields | 20 min |
| 4 | Add Project rollup fields | 20 min |
| 5 | Add calculated fields (optional) | 15 min |
| 6 | Create KPI views | 30 min |
| 7 | Update forms | 15 min |
| 8 | Testing | 15 min |
| 9 | Export solution | 10 min |
| **Total** | **Full implementation** | **2.5-3 hours** |

**Minimum viable (skip calculated fields and some views):** 90 minutes

---

## 🎨 Next Steps After Implementation

1. **Train PM/Operations** on new views and reports
2. **Establish data entry discipline** - set Anticipated Start during planning
3. **Create Power BI dashboards** using date data
4. **Build alerts** - notify PM of overdue starts
5. **Add mobile form** - quick Actual Start button for field techs
6. **Trend analysis** - historical schedule performance by scope type

---

**Ready to implement? Start with Phase 1 (Apparatus date fields) - 15 minutes.**
