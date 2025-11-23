# Manual Rollup Field Creation Guide
## Step-by-Step Checklist for Creating 32 Rollup Fields via Power Apps UI

**Created**: November 22, 2025  
**Purpose**: Detailed instructions for creating date tracking and revenue rollup fields  
**Reference**: `DATE_TRACKING_IMPLEMENTATION.md`  
**Estimated Time**: 3-5 hours total (18 date rollups + 14 revenue rollups)

---

## 🎯 Overview

This guide provides step-by-step instructions for creating 32 rollup fields in Dataverse:
- **18 Date Tracking Rollups**: Schedule visibility and KPI tracking
- **14 Revenue Rollups**: Financial summaries and reporting

**Why Manual Creation**: Dataverse Web API does not support creating rollup fields programmatically. The `RollupAttributeMetadata` type is not exposed in the OData model, requiring manual UI creation or Organization Service SDK.

---

## 📋 Prerequisites

### **Before You Begin**:
✅ All base date fields exist on Apparatus table:
- `cr950_anticipated_start` (Date and Time, User Local)
- `cr950_actual_start` (Date and Time, User Local)
- `cr950_date_completed` (Date and Time, User Local)

✅ Financial summary tables exist:
- `cr950_scopefinancialsummary`
- `cr950_projectfinancialsummary`

✅ ApparatusRevenue table has revenue fields:
- `cr950_revenueamount`
- `cr950_apparatus_hours`
- `cr950_effectivelaborrate`

✅ You have System Customizer or System Administrator role

### **Access Power Apps Maker Portal**:
1. Navigate to: https://make.powerapps.com
2. Select environment: **RESAPowerPM (Dev)** or **org99cd6c6e**
3. Go to: **Tables** in left navigation

---

## 📅 PART 1: DATE TRACKING ROLLUPS (18 Fields)

### **Tasks Table (6 Rollup Fields)**

#### **Field 1 of 18: Earliest Anticipated Start**

**Navigate**:
1. Tables → **Tasks** (`cr950_tasks`)
2. Click **Columns** tab
3. Click **+ New column**

**Configure**:
```
Display name: Earliest Anticipated Start
Name: cr950_earliest_anticipated_start
Data type: Rollup
```

**Click "Rollup" to configure**:
```
Related Entity: Apparatus (cr950_apparatus)
Aggregation:
  - Source Entity: Apparatus
  - Source Attribute: Anticipated Start (cr950_anticipated_start)
  - Aggregate Function: MIN
  - Filter: None (leave blank - include all apparatus)
```

**Save and Close**

---

#### **Field 2 of 18: Latest Anticipated Start**

**Navigate**: Tasks → Columns → + New column

**Configure**:
```
Display name: Latest Anticipated Start
Name: cr950_latest_anticipated_start
Data type: Rollup

Related Entity: Apparatus (cr950_apparatus)
Aggregation:
  - Source Entity: Apparatus
  - Source Attribute: Anticipated Start (cr950_anticipated_start)
  - Aggregate Function: MAX
  - Filter: None
```

**Save and Close**

---

#### **Field 3 of 18: Earliest Actual Start**

**Navigate**: Tasks → Columns → + New column

**Configure**:
```
Display name: Earliest Actual Start
Name: cr950_earliest_actual_start
Data type: Rollup

Related Entity: Apparatus (cr950_apparatus)
Aggregation:
  - Source Entity: Apparatus
  - Source Attribute: Actual Start (cr950_actual_start)
  - Aggregate Function: MIN
  - Filter: Actual Start is not null
```

**Filter Setup**:
1. Click "Add filter" in Rollup configuration
2. Select: `cr950_actual_start` Does Not Equal Null
3. This ensures we only consider apparatus that have actually started

**Save and Close**

---

#### **Field 4 of 18: Latest Actual Start**

**Navigate**: Tasks → Columns → + New column

**Configure**:
```
Display name: Latest Actual Start
Name: cr950_latest_actual_start
Data type: Rollup

Related Entity: Apparatus (cr950_apparatus)
Aggregation:
  - Source Entity: Apparatus
  - Source Attribute: Actual Start (cr950_actual_start)
  - Aggregate Function: MAX
  - Filter: Actual Start is not null
```

**Save and Close**

---

#### **Field 5 of 18: Earliest Completion Date**

**Navigate**: Tasks → Columns → + New column

**Configure**:
```
Display name: Earliest Completion Date
Name: cr950_earliest_completion_date
Data type: Rollup

Related Entity: Apparatus (cr950_apparatus)
Aggregation:
  - Source Entity: Apparatus
  - Source Attribute: Date Completed (cr950_date_completed)
  - Aggregate Function: MIN
  - Filter: Date Completed is not null
```

**Save and Close**

---

#### **Field 6 of 18: Latest Completion Date**

**Navigate**: Tasks → Columns → + New column

**Configure**:
```
Display name: Latest Completion Date
Name: cr950_latest_completion_date
Data type: Rollup

Related Entity: Apparatus (cr950_apparatus)
Aggregation:
  - Source Entity: Apparatus
  - Source Attribute: Date Completed (cr950_date_completed)
  - Aggregate Function: MAX
  - Filter: Date Completed is not null
```

**Save and Close**

---

### **Scopes Table (6 Rollup Fields)**

Repeat the exact same 6 fields for the **ProjectScope** (`cr950_projectscope`) table:

#### **Field 7-12 of 18: Scope Rollups**

1. **Earliest Anticipated Start** - MIN(Apparatus.Anticipated Start), no filter
2. **Latest Anticipated Start** - MAX(Apparatus.Anticipated Start), no filter
3. **Earliest Actual Start** - MIN(Apparatus.Actual Start), filter: not null
4. **Latest Actual Start** - MAX(Apparatus.Actual Start), filter: not null
5. **Earliest Completion Date** - MIN(Apparatus.Date Completed), filter: not null
6. **Latest Completion Date** - MAX(Apparatus.Date Completed), filter: not null

**Navigate**: Tables → **ProjectScope** → Columns → + New column (repeat 6 times)

**Note**: Roll up directly from Apparatus, not from Tasks. This provides more accurate data and avoids double-rollup delays.

---

### **Projects Table (6 Rollup Fields)**

For Projects, roll up from **Scopes**, not Apparatus directly:

#### **Field 13 of 18: Earliest Anticipated Start**

**Navigate**: Tables → **Projects** (`cr950_projects`) → Columns → + New column

**Configure**:
```
Display name: Earliest Anticipated Start
Name: cr950_earliest_anticipated_start
Data type: Rollup

Related Entity: ProjectScope (cr950_projectscope)
Aggregation:
  - Source Entity: ProjectScope
  - Source Attribute: Earliest Anticipated Start (cr950_earliest_anticipated_start)
  - Aggregate Function: MIN
  - Filter: None
```

**Why roll from Scopes**: Projects can have hundreds/thousands of apparatus. Rolling from Scopes (which have already aggregated from Apparatus) is more efficient.

**Save and Close**

---

#### **Field 14-18 of 18: Project Rollups**

Continue with remaining 5 fields for Projects table:

2. **Latest Anticipated Start** - MAX(Scope.Latest Anticipated Start)
3. **Earliest Actual Start** - MIN(Scope.Earliest Actual Start), filter: not null
4. **Latest Actual Start** - MAX(Scope.Latest Actual Start), filter: not null
5. **Earliest Completion Date** - MIN(Scope.Earliest Completion Date), filter: not null
6. **Latest Completion Date** - MAX(Scope.Latest Completion Date), filter: not null

---

## 💰 PART 2: REVENUE ROLLUPS (14 Fields)

### **Scope Financial Summary Table (7 Rollup Fields)**

These rollup from **ApparatusRevenue** (`cr950_apparatusrevenue`) table.

**Navigate**: Tables → **ScopeFinancialSummary** (`cr950_scopefinancialsummary`)

---

#### **Field 1 of 14: Total Revenue Recognized**

**Navigate**: ScopeFinancialSummary → Columns → + New column

**Configure**:
```
Display name: Total Revenue Recognized
Name: cr950_total_revenue_recognized
Data type: Rollup

Related Entity: ApparatusRevenue (cr950_apparatusrevenue)
Aggregation:
  - Source Entity: ApparatusRevenue
  - Source Attribute: Revenue Amount (cr950_revenueamount)
  - Aggregate Function: SUM
  - Filter: Revenue Status equals "Recognized" (value: 100000000)
```

**Filter Setup**:
1. Add filter: `cr950_revenuestatus` Equals `100000000` (Recognized)
2. This ensures we only sum revenue that has been recognized

**Save and Close**

---

#### **Field 2 of 14: Total Revenue Pending**

**Configure**:
```
Display name: Total Revenue Pending
Name: cr950_total_revenue_pending
Data type: Rollup

Related Entity: ApparatusRevenue
Aggregation:
  - Source Entity: ApparatusRevenue
  - Source Attribute: Revenue Amount (cr950_revenueamount)
  - Aggregate Function: SUM
  - Filter: Revenue Status equals "Pending" (value: 100000001)
```

**Save and Close**

---

#### **Field 3 of 14: Total Billable Hours**

**Configure**:
```
Display name: Total Billable Hours
Name: cr950_total_billable_hours
Data type: Rollup

Related Entity: ApparatusRevenue
Aggregation:
  - Source Entity: ApparatusRevenue
  - Source Attribute: Apparatus Hours (cr950_apparatus_hours)
  - Aggregate Function: SUM
  - Filter: None (sum all hours)
```

**Save and Close**

---

#### **Field 4 of 14: Total Delay Hours**

**Configure**:
```
Display name: Total Delay Hours
Name: cr950_total_delay_hours
Data type: Rollup

Related Entity: ApparatusRevenue
Aggregation:
  - Source Entity: ApparatusRevenue
  - Source Attribute: Delays (cr950_delays)
  - Aggregate Function: SUM
  - Filter: None
```

**Save and Close**

---

#### **Field 5 of 14: Apparatus Revenue Count**

**Configure**:
```
Display name: Apparatus Revenue Count
Name: cr950_apparatus_revenue_count
Data type: Rollup

Related Entity: ApparatusRevenue
Aggregation:
  - Source Entity: ApparatusRevenue
  - Source Attribute: Apparatus Revenue ID (cr950_apparatusrevenueid)
  - Aggregate Function: COUNT
  - Filter: None
```

**Purpose**: Track how many apparatus have generated revenue in this scope.

**Save and Close**

---

#### **Field 6 of 14: Average Labor Rate**

**Configure**:
```
Display name: Average Labor Rate
Name: cr950_average_labor_rate
Data type: Rollup

Related Entity: ApparatusRevenue
Aggregation:
  - Source Entity: ApparatusRevenue
  - Source Attribute: Effective Labor Rate (cr950_effectivelaborrate)
  - Aggregate Function: AVG
  - Filter: Effective Labor Rate is not null
```

**Save and Close**

---

#### **Field 7 of 14: Latest Revenue Date**

**Configure**:
```
Display name: Latest Revenue Date
Name: cr950_latest_revenue_date
Data type: Rollup

Related Entity: ApparatusRevenue
Aggregation:
  - Source Entity: ApparatusRevenue
  - Source Attribute: Date Completed (cr950_date_completed)
  - Aggregate Function: MAX
  - Filter: Date Completed is not null
```

**Purpose**: Track most recent revenue recognition date for billing period tracking.

**Save and Close**

---

### **Project Financial Summary Table (7 Rollup Fields)**

These rollup from **ScopeFinancialSummary** (cascading the scope totals).

**Navigate**: Tables → **ProjectFinancialSummary** (`cr950_projectfinancialsummary`)

---

#### **Field 8-14 of 14: Project Financial Rollups**

Create the same 7 fields, but rolling from **ScopeFinancialSummary**:

1. **Total Revenue Recognized** - SUM(ScopeFinancialSummary.Total Revenue Recognized)
2. **Total Revenue Pending** - SUM(ScopeFinancialSummary.Total Revenue Pending)
3. **Total Billable Hours** - SUM(ScopeFinancialSummary.Total Billable Hours)
4. **Total Delay Hours** - SUM(ScopeFinancialSummary.Total Delay Hours)
5. **Apparatus Revenue Count** - SUM(ScopeFinancialSummary.Apparatus Revenue Count)
6. **Average Labor Rate** - AVG(ScopeFinancialSummary.Average Labor Rate)
7. **Latest Revenue Date** - MAX(ScopeFinancialSummary.Latest Revenue Date)

**Note**: For Average Labor Rate, use AVG of scope averages (weighted by scope size implicitly).

---

## ✅ VALIDATION & TESTING

### **After Creating All Rollups**:

#### **1. Verify Rollup Fields Created**

**Check Tasks**:
```
Tables → Tasks → Columns
Filter: Data type = Rollup
Expected: 6 rollup fields
```

**Check Scopes**:
```
Tables → ProjectScope → Columns
Filter: Data type = Rollup
Expected: 6 rollup fields
```

**Check Projects**:
```
Tables → Projects → Columns
Filter: Data type = Rollup
Expected: 6 rollup fields
```

**Check Financial Tables**:
```
Tables → ScopeFinancialSummary → Columns
Expected: 7 rollup fields

Tables → ProjectFinancialSummary → Columns
Expected: 7 rollup fields
```

---

#### **2. Test Rollup Calculations**

**Create Sample Data**:

1. **Create Test Apparatus** (in existing Task/Scope):
   ```
   Apparatus 1:
   - Anticipated Start: Tomorrow
   - Actual Start: Today
   - Date Completed: [Leave blank]
   
   Apparatus 2:
   - Anticipated Start: Next week
   - Actual Start: Yesterday
   - Date Completed: Today
   ```

2. **Wait 2-5 minutes** for rollups to calculate
   - Rollups are calculated asynchronously
   - Check Task/Scope/Project records for values

3. **Verify Calculations**:
   ```
   Task should show:
   - Earliest Anticipated Start: Tomorrow
   - Latest Anticipated Start: Next week
   - Earliest Actual Start: Yesterday
   - Latest Actual Start: Today
   - Earliest Completion Date: Today
   - Latest Completion Date: Today
   ```

4. **Test Financial Rollups**:
   ```
   Create ApparatusRevenue record:
   - Revenue Amount: $1000
   - Revenue Status: Recognized
   - Apparatus Hours: 10
   - Delays: 2
   - Effective Labor Rate: $100/hr
   
   Check ScopeFinancialSummary:
   - Total Revenue Recognized: $1000
   - Total Billable Hours: 10
   - Total Delay Hours: 2
   - Average Labor Rate: $100
   ```

---

#### **3. Trigger Manual Rollup Calculation**

If rollups aren't calculating automatically:

1. Open any **Apparatus** record
2. Make a trivial change (e.g., add a note)
3. Save the record
4. This triggers recalculation of parent rollups
5. Wait 2-5 minutes, check parent records

---

#### **4. Check Rollup Job Status**

**In Power Apps**:
1. Settings (gear icon) → Advanced Settings
2. Settings → System → System Jobs
3. Filter: System Job Type = "Calculate Rollup Field"
4. Check for errors or stuck jobs

**Common Issues**:
- **"Waiting" status**: Normal, will process in background
- **"Failed" status**: Check error message, may need to recreate field
- **"Canceling" status**: System overloaded, will retry

---

## 🎨 ADD ROLLUPS TO FORMS

### **After Rollups Are Working**:

#### **Tasks Form**:
1. Tables → Tasks → Forms → Main form
2. Add new section: "Schedule Summary"
3. Add fields:
   - Earliest Anticipated Start
   - Latest Anticipated Start
   - Earliest Actual Start
   - Latest Actual Start
   - Earliest Completion Date
   - Latest Completion Date
4. Make all fields **Read-only**
5. Save and Publish

#### **Scopes Form**:
Repeat same steps for ProjectScope main form

#### **Projects Form**:
Repeat same steps for Projects main form

#### **Financial Summary Forms**:

**ScopeFinancialSummary Form**:
1. Add section: "Revenue Summary"
2. Add all 7 rollup fields
3. Format currency fields with $ symbol
4. Make all read-only

**ProjectFinancialSummary Form**:
Repeat for project financial summary

---

## 📊 CREATE KPI VIEWS

### **Date Tracking Views** (Reference: DATE_TRACKING_IMPLEMENTATION.md)

#### **View 1: Upcoming Work (Next 7 Days)**

**Navigate**: Tables → Apparatus → Views → + New view

**Configure**:
```
Name: Upcoming Work (Next 7 Days)
Filter:
  - Anticipated Start: In Next 7 Days
  - Actual Start: Is Null
  - Completion Status: Not Equal to "Complete"

Columns:
  - Apparatus Designation
  - Scope (lookup)
  - Anticipated Start
  - Assigned To
  - Status

Sort by: Anticipated Start (ascending)
```

---

#### **View 2: Overdue Starts**

**Configure**:
```
Name: Overdue Starts
Filter:
  - Anticipated Start: On or Before Today
  - Actual Start: Is Null
  - Completion Status: Not Equal to "Complete"

Columns:
  - Apparatus Designation
  - Scope
  - Anticipated Start
  - Days Overdue (calculated)
  - Assigned To

Sort by: Anticipated Start (ascending)
```

---

#### **View 3: Work In Progress**

**Configure**:
```
Name: Work In Progress
Filter:
  - Actual Start: Is Not Null
  - Date Completed: Is Null

Columns:
  - Apparatus Designation
  - Scope
  - Actual Start
  - Days In Progress
  - Assigned To
  - Completed Hours vs Apparatus Hours

Sort by: Actual Start (ascending)
```

---

#### **View 4: Recently Completed (Last 7 Days)**

**Configure**:
```
Name: Recently Completed (Last 7 Days)
Filter:
  - Date Completed: In Last 7 Days

Columns:
  - Apparatus Designation
  - Scope
  - Date Completed
  - Duration (days)
  - Schedule Variance
  - Revenue Status

Sort by: Date Completed (descending)
```

---

#### **View 5: Resource Timeline**

**Navigate**: Tables → ProjectScope → Views → + New view

**Configure**:
```
Name: Resource Timeline
Filter:
  - Project Status: Active

Columns:
  - Scope Name
  - Earliest Anticipated Start
  - Latest Anticipated Start
  - Earliest Actual Start
  - Latest Completion Date
  - Percent Complete
  - Assigned Techs

Sort by: Earliest Anticipated Start (ascending)
```

---

#### **View 6: Schedule Performance Report**

**Navigate**: Tables → ProjectScope → Views → + New view

**Configure**:
```
Name: Schedule Performance Report
Group by: Project

Columns:
  - Scope Name
  - Total Apparatus Count (rollup)
  - Completed Apparatus Count (rollup)
  - On Time Count (calculated)
  - Late Count (calculated)
  - On Time % (calculated)

Sort by: Project, then Scope Name
```

---

## 🚨 TROUBLESHOOTING

### **Issue: Rollup field not calculating**

**Check**:
1. Related records exist (e.g., Apparatus records for Task rollup)
2. Source attribute has values (not all null)
3. Relationship is correct (check related entity)
4. Wait 5-10 minutes (async calculation)

**Fix**:
- Edit a related record to trigger recalculation
- Check System Jobs for errors
- Verify relationship navigation property

---

### **Issue: "Navigation property not found" error**

**Cause**: Relationship doesn't exist between entities

**Fix**:
1. Check if relationship exists: Tables → [Table] → Relationships
2. If missing, create the relationship first
3. Then create the rollup field

---

### **Issue: Filter not working correctly**

**Check**:
1. Filter syntax: Use "Is Not Null" not "Does Not Equal Null"
2. Choice field values: Use numeric value not label
3. Date filters: Use dynamic values ("Today", "In Next 7 Days")

---

### **Issue: Rollup showing wrong value**

**Verify**:
1. Aggregate function: MIN/MAX/SUM/COUNT/AVG
2. Source attribute: Correct field selected
3. Filter logic: Review filter conditions
4. Related entity: Correct table selected

---

## 📦 EXPORT SOLUTION

### **After All Rollups Are Working**:

1. **Settings** → **Solutions**
2. Select **RESAPowerProjectTracker**
3. Click **Export**
4. Version: **1.5.0.0**
5. Export as: **Managed** (for production) or **Unmanaged** (for dev)
6. Download and save to: `Solution_Exports/v1.5.0.0/`

**Git Commit Message**:
```
feat: v1.5.0.0 - KPI rollup fields complete

- Added 18 date tracking rollup fields (Tasks, Scopes, Projects)
- Added 14 revenue rollup fields (Scope/Project Financial Summary)
- Created 6 KPI views for schedule management
- Configured forms to display rollup summaries
- All rollups tested and validated with sample data

Total: 32 rollup fields created manually via UI
Architecture: Apparatus → Tasks/Scopes → Projects (cascading aggregations)
Business Value: Schedule visibility, revenue tracking, capacity planning
```

---

## ⏱️ TIME TRACKING

| Task | Estimated Time | Notes |
|------|----------------|-------|
| Tasks rollups (6 fields) | 30 minutes | Straightforward, similar patterns |
| Scopes rollups (6 fields) | 30 minutes | Same as Tasks |
| Projects rollups (6 fields) | 30 minutes | Rolling from Scopes |
| Scope Financial rollups (7 fields) | 45 minutes | More complex filters |
| Project Financial rollups (7 fields) | 30 minutes | Rolling from Scope Financial |
| Testing & validation | 30 minutes | Sample data, verification |
| Add to forms | 30 minutes | 6 forms to update |
| Create KPI views | 60 minutes | 6 views with filters |
| **Total** | **4.5 hours** | Can be done in 2-3 sessions |

---

## 📝 CHECKLIST SUMMARY

### **Date Tracking Rollups** (18 fields):

**Tasks**:
- [ ] Earliest Anticipated Start (MIN, Apparatus)
- [ ] Latest Anticipated Start (MAX, Apparatus)
- [ ] Earliest Actual Start (MIN, Apparatus, filter: not null)
- [ ] Latest Actual Start (MAX, Apparatus, filter: not null)
- [ ] Earliest Completion Date (MIN, Apparatus, filter: not null)
- [ ] Latest Completion Date (MAX, Apparatus, filter: not null)

**Scopes**:
- [ ] Earliest Anticipated Start (MIN, Apparatus)
- [ ] Latest Anticipated Start (MAX, Apparatus)
- [ ] Earliest Actual Start (MIN, Apparatus, filter: not null)
- [ ] Latest Actual Start (MAX, Apparatus, filter: not null)
- [ ] Earliest Completion Date (MIN, Apparatus, filter: not null)
- [ ] Latest Completion Date (MAX, Apparatus, filter: not null)

**Projects**:
- [ ] Earliest Anticipated Start (MIN, Scope.Earliest Anticipated Start)
- [ ] Latest Anticipated Start (MAX, Scope.Latest Anticipated Start)
- [ ] Earliest Actual Start (MIN, Scope.Earliest Actual Start, filter: not null)
- [ ] Latest Actual Start (MAX, Scope.Latest Actual Start, filter: not null)
- [ ] Earliest Completion Date (MIN, Scope.Earliest Completion Date, filter: not null)
- [ ] Latest Completion Date (MAX, Scope.Latest Completion Date, filter: not null)

### **Revenue Rollups** (14 fields):

**Scope Financial Summary**:
- [ ] Total Revenue Recognized (SUM, filter: status=Recognized)
- [ ] Total Revenue Pending (SUM, filter: status=Pending)
- [ ] Total Billable Hours (SUM)
- [ ] Total Delay Hours (SUM)
- [ ] Apparatus Revenue Count (COUNT)
- [ ] Average Labor Rate (AVG, filter: not null)
- [ ] Latest Revenue Date (MAX, filter: not null)

**Project Financial Summary**:
- [ ] Total Revenue Recognized (SUM from Scope)
- [ ] Total Revenue Pending (SUM from Scope)
- [ ] Total Billable Hours (SUM from Scope)
- [ ] Total Delay Hours (SUM from Scope)
- [ ] Apparatus Revenue Count (SUM from Scope)
- [ ] Average Labor Rate (AVG from Scope)
- [ ] Latest Revenue Date (MAX from Scope)

### **Post-Creation**:
- [ ] Test rollups with sample data
- [ ] Add rollup fields to forms (read-only)
- [ ] Create 6 KPI views
- [ ] Export solution as v1.5.0.0
- [ ] Commit to Git

---

**READY TO START? Begin with Tasks table, Field 1 of 18!**

Good luck! 🚀
