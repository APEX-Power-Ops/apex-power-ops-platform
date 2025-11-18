# RESA Power Hours Architecture Guide
## Complete Hours Flow Analysis

**Version:** 1.0  
**Date:** November 10, 2025  
**Purpose:** Define how labor hours flow through the entire system hierarchy

---

## 📊 CURRENT STATE ANALYSIS

### What You Have Now:

| Table | Field | Type | Current Category | Should Be |
|-------|-------|------|------------------|-----------|
| **Apparatus** | cr950_laborhours | Decimal | Simple Field | ✅ CORRECT - Data Entry |
| **Tasks** | (none) | - | - | ❌ MISSING - Needs 3 rollup fields |
| **Scopes** | cr950_totalapparatushours | Decimal | Simple Field | ⚠️ WRONG TYPE - Should be ROLLUP |
| **Projects** | (none) | - | - | ❌ MISSING - Needs 3 rollup fields |
| **Apparatus_Revenue** | cr950_laborhours | Decimal | Simple Field | ✅ CORRECT - Copy from Apparatus |

---

## 🏗️ HOURS ARCHITECTURE - THE HIERARCHY

### How Hours Flow Through Your System:

```
┌─────────────────────────────────────────────────────────────────┐
│ APPARATUS (Individual Equipment)                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Labor_Hours = 12.5 hrs                    [DATA ENTRY]      │ │
│ │ Completion_Status = "Complete"                              │ │
│ │ Completed_By = "John Smith"                                 │ │
│ └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Rolls up to ↓
┌─────────────────────────────────────────────────────────────────┐
│ TASK (Group of Similar Equipment)                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Total_Labor_Hours = SUM(Apparatus.Labor_Hours)   [ROLLUP]  │ │
│ │   = 12.5 + 8.0 + 15.0 = 35.5 hrs                           │ │
│ │                                                             │ │
│ │ Completed_Hours = SUM where Status="Complete"    [ROLLUP]  │ │
│ │   = 12.5 + 8.0 = 20.5 hrs                                  │ │
│ │                                                             │ │
│ │ Remaining_Hours = Total - Completed          [CALCULATED]  │ │
│ │   = 35.5 - 20.5 = 15.0 hrs                                 │ │
│ └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Rolls up to ↓
┌─────────────────────────────────────────────────────────────────┐
│ SCOPE (Major Work Breakdown)                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Total_Apparatus_Hours = SUM(Apparatus.Labor_Hours) [ROLLUP]│ │
│ │   = 35.5 + 42.0 + 18.5 = 96.0 hrs                          │ │
│ │                                                             │ │
│ │ Completed_Hours = SUM where Status="Complete"    [ROLLUP]  │ │
│ │   = 20.5 + 42.0 = 62.5 hrs                                 │ │
│ │                                                             │ │
│ │ Remaining_Hours = Total - Completed          [CALCULATED]  │ │
│ │   = 96.0 - 62.5 = 33.5 hrs                                 │ │
│ │                                                             │ │
│ │ Percent_Complete = (Completed / Total) * 100 [CALCULATED]  │ │
│ │   = (62.5 / 96.0) * 100 = 65.1%                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Rolls up to ↓
┌─────────────────────────────────────────────────────────────────┐
│ PROJECT (Entire Job)                                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Total_Apparatus_Hours = SUM(Apparatus.Labor_Hours) [ROLLUP]│ │
│ │   = 96.0 + 142.5 + 88.0 = 326.5 hrs                        │ │
│ │                                                             │ │
│ │ Completed_Hours = SUM where Status="Complete"    [ROLLUP]  │ │
│ │   = 62.5 + 142.5 + 50.0 = 255.0 hrs                        │ │
│ │                                                             │ │
│ │ Remaining_Hours = Total - Completed          [CALCULATED]  │ │
│ │   = 326.5 - 255.0 = 71.5 hrs                               │ │
│ │                                                             │ │
│ │ Percent_Complete = (Completed / Total) * 100 [CALCULATED]  │ │
│ │   = (255.0 / 326.5) * 100 = 78.1%                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 DETAILED FIELD SPECIFICATIONS

### **APPARATUS TABLE** (Bottom of Hierarchy - Data Entry Level)

#### Field 1: Labor_Hours (ALREADY EXISTS ✅)
```
Name: cr950_laborhours
Type: Decimal
Category: Simple Field (Data Entry)
Decimals: 2
Required: No (can be blank until testing starts)
Source: Imported from Excel OR manually entered
Purpose: Standard hours to test this specific apparatus

Example Values:
- Transformer (NETA ATS): 12.5 hours
- Circuit Breaker (NETA MTS): 2.5 hours
- Switchgear (NETA ATS): 18.0 hours
```

**How it gets populated:**
1. **During Import:** Excel estimator has hours per apparatus type
2. **Import Process:** Looks at Scope's NETA_Standard (ATS or MTS)
3. **Import Process:** Gets hours from Apparatus_Type_Master based on standard
4. **Result:** Each apparatus has appropriate test hours

**Field Tech Usage:**
- Field techs SEE this field (read-only)
- Shows them how many hours are budgeted for this test
- Used for scheduling and work planning

---

#### Field 2: Completion_Status (ALREADY EXISTS ✅)
```
Name: cr950_completionstatus
Type: Choice
Options: Not Started, In Progress, Complete, On Hold, Incomplete
Purpose: Tracks testing completion status

This field TRIGGERS revenue recognition when set to "Complete"
```

---

#### Field 3: Remaining_Hours (NEEDS TO BE ADDED - Calculated)
```
Name: cr950_remaininghours
Type: Decimal
Category: CALCULATED FIELD
Formula: If(cr950_completionstatus = Complete, 0, cr950_laborhours)

Purpose: Shows hours remaining for this apparatus
- If complete: 0 hours
- If not complete: original labor hours

✅ XML already generated in apparatus_calculated_fields.xml
```

---

#### Field 4: Percent_Complete (NEEDS TO BE ADDED - Calculated)
```
Name: cr950_percentcomplete
Type: Whole Number
Category: CALCULATED FIELD
Formula: If(cr950_completionstatus = Complete, 100, 0)

Purpose: Binary completion indicator (0% or 100%)
- Complete = 100%
- Anything else = 0%

✅ XML already generated in apparatus_calculated_fields.xml
```

---

### **TASKS TABLE** (Mid-Level Aggregation)

Tasks group similar apparatus together for technician assignment.

#### Field 1: Total_Labor_Hours (NEEDS TO BE ADDED - Rollup)
```
Name: cr950_totallaborhours
Type: Decimal
Category: ROLLUP FIELD
Source Entity: Apparatus
Aggregation: SUM
Field: cr950_laborhours
Filter: Task_ID matches this task

Purpose: Total budgeted hours for all apparatus in this task

Example:
Task: "Transformer Testing - Building A"
Contains:
  - Transformer T-001: 12.5 hrs
  - Transformer T-002: 12.5 hrs
  - Transformer T-003: 15.0 hrs
Total: 40.0 hrs
```

---

#### Field 2: Completed_Hours (NEEDS TO BE ADDED - Rollup)
```
Name: cr950_completedhours
Type: Decimal
Category: ROLLUP FIELD
Source Entity: Apparatus
Aggregation: SUM
Field: cr950_laborhours
Filter: Task_ID matches AND Completion_Status = "Complete"

Purpose: Hours completed so far

Example:
Task: "Transformer Testing - Building A"
  - T-001: Complete (12.5 hrs) ✅
  - T-002: Complete (12.5 hrs) ✅
  - T-003: Not Started (15.0 hrs) ❌
Completed: 25.0 hrs
```

---

#### Field 3: Remaining_Hours (NEEDS TO BE ADDED - Calculated)
```
Name: cr950_remaininghours
Type: Decimal
Category: CALCULATED FIELD
Formula: cr950_totallaborhours - cr950_completedhours

Purpose: Hours still to be completed

Example:
Total: 40.0 hrs
Completed: 25.0 hrs
Remaining: 15.0 hrs
```

---

#### Field 4: Percent_Complete (NEEDS TO BE ADDED - Calculated)
```
Name: cr950_percentcomplete
Type: Decimal
Category: CALCULATED FIELD
Formula: If(IsBlank(cr950_totallaborhours) || cr950_totallaborhours = 0, 0, 
           (cr950_completedhours / cr950_totallaborhours) * 100)

Purpose: Task completion percentage

Example:
Completed: 25.0 hrs
Total: 40.0 hrs
Percent: 62.5%
```

---

### **SCOPES TABLE** (Scope-Level Aggregation)

Scopes represent major work breakdown areas (e.g., "Building A", "Substation 1").

#### Field 1: Total_Apparatus_Hours (ALREADY EXISTS - WRONG TYPE ⚠️)
```
Current State:
Name: cr950_totalapparatushours
Type: Decimal
Category: Simple Field (manual entry)

Should Be:
Name: cr950_totalapparatushours
Type: Decimal
Category: ROLLUP FIELD
Source Entity: Apparatus
Aggregation: SUM
Field: cr950_laborhours
Filter: Scope_ID matches this scope

⚠️ ACTION REQUIRED:
1. DELETE current simple field
2. CREATE new rollup field with same name
3. Configure rollup to sum Apparatus.Labor_Hours
```

**Why This Matters:**
- Current field is MANUAL (someone has to type in the total)
- Should be AUTOMATIC (sums up all apparatus automatically)
- When apparatus added/removed, total updates automatically

**Example:**
```
Scope: "Building A - Electrical Room"
Apparatus:
  - T-001: 12.5 hrs
  - CB-001: 2.5 hrs
  - CB-002: 2.5 hrs
  - SW-001: 18.0 hrs
  - ... (50 more apparatus)
  
Total: 285.5 hrs (automatically calculated)
```

---

#### Field 2: Completed_Hours (NEEDS TO BE ADDED - Rollup)
```
Name: cr950_completedhours
Type: Decimal
Category: ROLLUP FIELD
Source Entity: Apparatus
Aggregation: SUM
Field: cr950_laborhours
Filter: Scope_ID matches AND Completion_Status = "Complete"

Purpose: Hours completed in this scope

Example:
Scope: "Building A - Electrical Room"
Total: 285.5 hrs
Completed: 180.0 hrs (30 apparatus complete)
Remaining: 105.5 hrs
```

---

#### Field 3: Remaining_Hours (NEEDS TO BE ADDED - Calculated)
```
Name: cr950_remaininghours
Type: Decimal
Category: CALCULATED FIELD
Formula: cr950_totalapparatushours - cr950_completedhours

Purpose: Hours remaining in scope
```

---

#### Field 4: Percent_Complete (NEEDS TO BE ADDED - Calculated)
```
Name: cr950_percentcomplete
Type: Decimal
Category: CALCULATED FIELD
Formula: If(IsBlank(cr950_totalapparatushours) || cr950_totalapparatushours = 0, 0,
           (cr950_completedhours / cr950_totalapparatushours) * 100)

Purpose: Scope completion percentage

Used for:
- Earned Value Management
- Progress reporting
- S-curve tracking
- Invoicing milestones
```

---

### **PROJECTS TABLE** (Top-Level Aggregation)

Projects represent entire jobs (e.g., "LASNAP16 - Las Vegas Substation").

#### Field 1: Total_Apparatus_Hours (NEEDS TO BE ADDED - Rollup)
```
Name: cr950_totalapparatushours
Type: Decimal
Category: ROLLUP FIELD
Source Entity: Apparatus
Aggregation: SUM
Field: cr950_laborhours
Filter: Project_ID matches this project

Purpose: Total budgeted hours for entire project

Example:
Project: LASNAP16
Total Apparatus: 1,847 items
Total Hours: 2,456.5 hrs
```

---

#### Field 2: Completed_Hours (NEEDS TO BE ADDED - Rollup)
```
Name: cr950_completedhours
Type: Decimal
Category: ROLLUP FIELD
Source Entity: Apparatus
Aggregation: SUM
Field: cr950_laborhours
Filter: Project_ID matches AND Completion_Status = "Complete"

Purpose: Hours completed so far

Example:
Project: LASNAP16
Total: 2,456.5 hrs
Completed: 1,850.0 hrs (75.3% complete)
Remaining: 606.5 hrs
```

---

#### Field 3: Remaining_Hours (NEEDS TO BE ADDED - Calculated)
```
Name: cr950_remaininghours
Type: Decimal
Category: CALCULATED FIELD
Formula: cr950_totalapparatushours - cr950_completedhours

Purpose: Hours remaining in project
```

---

#### Field 4: Percent_Complete (NEEDS TO BE ADDED - Calculated)
```
Name: cr950_percentcomplete
Type: Decimal
Category: CALCULATED FIELD
Formula: If(IsBlank(cr950_totalapparatushours) || cr950_totalapparatushours = 0, 0,
           (cr950_completedhours / cr950_totalapparatushours) * 100)

Purpose: Overall project completion percentage

Critical for:
- Executive dashboards
- Customer reporting
- Payment applications
- Earned value analysis
```

---

## 💰 HOURS → REVENUE CONNECTION

### How Hours Drive Revenue Recognition:

```
1. APPARATUS COMPLETED
   └─> Field tech marks Completion_Status = "Complete"
   └─> Enters Completed_By and Completion_Date
   └─> Labor_Hours field contains budgeted hours (e.g., 12.5)

2. POWER AUTOMATE FLOW TRIGGERS
   └─> Detects Apparatus completion
   └─> Reads Labor_Hours from Apparatus (12.5 hrs)
   └─> Looks up Scope_Financial_Configuration
   └─> Gets Base_Labor_Rate ($85/hr)
   └─> Calculates: 12.5 hrs × $85/hr × multipliers = $1,250.00
   
3. APPARATUS_REVENUE RECORD CREATED
   └─> Labor_Hours: 12.5 (copied from Apparatus)
   └─> Base_Labor_Rate: $85.00
   └─> Calculated_Revenue: $1,250.00
   └─> Revenue_Recognized_Date: Today()
   
4. REVENUE ROLLS UP
   └─> Task.Task_Earned_Revenue = SUM(Apparatus_Revenue)
   └─> Scope.Total_Earned_Revenue = SUM(Apparatus_Revenue)
   └─> Project.Total_Earned_Revenue = SUM(Apparatus_Revenue)
```

**Key Point:** Hours are the DRIVER of revenue. Without accurate hours tracking, revenue recognition fails.

---

## 🔧 IMPLEMENTATION PRIORITY

### Phase 1: Fix Scopes.Total_Apparatus_Hours (CRITICAL)

**Current Problem:**
```
Field: cr950_totalapparatushours
Type: Decimal (simple field)
Problem: Manual entry, doesn't auto-update
```

**Fix Required:**
```
1. In Power Apps, open Scopes table
2. DELETE cr950_totalapparatushours field
3. CREATE new field with same name:
   - Name: Total_Apparatus_Hours
   - Type: Rollup
   - Source: Apparatus table
   - Aggregate: SUM
   - Field: cr950_laborhours
   - Filter: Where Scope_ID = this scope
4. Save and publish
```

**Time:** 30 minutes  
**Impact:** 🔴 CRITICAL - Enables accurate scope-level hour tracking

---

### Phase 2: Add Task Hours Rollups (HIGH)

**Create 2 rollup fields in Tasks table:**

1. **Total_Labor_Hours** - SUM(Apparatus.Labor_Hours)
2. **Completed_Hours** - SUM(Apparatus.Labor_Hours WHERE Complete)

**Then add calculated fields:**

3. **Remaining_Hours** = Total - Completed
4. **Percent_Complete** = (Completed / Total) × 100

**Time:** 1 hour  
**Impact:** 🟡 HIGH - Enables task-level progress tracking

---

### Phase 3: Add Project Hours Rollups (HIGH)

**Create 2 rollup fields in Projects table:**

1. **Total_Apparatus_Hours** - SUM(Apparatus.Labor_Hours)
2. **Completed_Hours** - SUM(Apparatus.Labor_Hours WHERE Complete)

**Then add calculated fields:**

3. **Remaining_Hours** = Total - Completed
4. **Percent_Complete** = (Completed / Total) × 100

**Time:** 1 hour  
**Impact:** 🟡 HIGH - Enables project-level earned value management

---

### Phase 4: Add Scope Calculated Fields (MEDIUM)

**Create calculated fields in Scopes:**

1. **Remaining_Hours** = Total_Apparatus_Hours - Completed_Hours
2. **Percent_Complete** = (Completed / Total) × 100

**Time:** 30 minutes  
**Impact:** 🟢 MEDIUM - Completes scope-level hour analytics

---

## 📊 HOURS DASHBOARD VIEW

Once all fields are implemented, you'll be able to create dashboards like:

```
PROJECT: LASNAP16 - Las Vegas Substation
═══════════════════════════════════════════════════════════
Total Hours: 2,456.5 hrs        Percent Complete: 75.3%
Completed:   1,850.0 hrs        Remaining: 606.5 hrs
Earned Revenue: $385,420.00     Estimated Final: $511,500.00

SCOPE BREAKDOWN:
┌────────────────────────┬───────┬───────┬───────┬──────┐
│ Scope                  │ Total │ Done  │ Remain│  %   │
├────────────────────────┼───────┼───────┼───────┼──────┤
│ Building A - Switchgear│ 285.5 │ 285.5 │   0.0 │ 100% │
│ Building B - Transform │ 425.0 │ 380.0 │  45.0 │ 89%  │
│ Outdoor Substation     │ 890.0 │ 650.0 │ 240.0 │ 73%  │
│ Underground Feeders    │ 856.0 │ 534.5 │ 321.5 │ 62%  │
└────────────────────────┴───────┴───────┴───────┴──────┘

TASK BREAKDOWN (Building B):
┌────────────────────────┬───────┬───────┬───────┬──────┐
│ Task                   │ Total │ Done  │ Remain│  %   │
├────────────────────────┼───────┼───────┼───────┼──────┤
│ Transformers (3 units) │  40.0 │  40.0 │   0.0 │ 100% │
│ Switchgear (2 lineups) │  36.0 │  36.0 │   0.0 │ 100% │
│ Circuit Breakers (48)  │ 120.0 │  96.0 │  24.0 │ 80%  │
│ Panel Boards (15)      │  45.0 │  30.0 │  15.0 │ 67%  │
│ Final Testing          │ 184.0 │ 178.0 │   6.0 │ 97%  │
└────────────────────────┴───────┴───────┴───────┴──────┘
```

---

## ⚠️ COMMON MISTAKES TO AVOID

### Mistake 1: Making Hours Fields Manual Entry Above Apparatus Level
```
❌ WRONG: Manually entering total hours in Scopes/Projects
✅ RIGHT: Use rollup fields that auto-calculate from Apparatus
```

### Mistake 2: Using Simple Calculated Fields Instead of Rollups
```
❌ WRONG: Calculated field trying to sum child records
✅ RIGHT: Rollup field properly aggregating child records
```

### Mistake 3: Not Having Completed Hours Tracking
```
❌ WRONG: Only tracking total hours
✅ RIGHT: Track both total AND completed hours for progress
```

### Mistake 4: Forgetting Remaining Hours Calculations
```
❌ WRONG: Only showing total and completed
✅ RIGHT: Also calculate and show remaining hours
```

---

## 🎯 SUMMARY - HOURS FIELD CHECKLIST

### ✅ WHAT YOU HAVE (CORRECT):
- [x] Apparatus.Labor_Hours (data entry field)
- [x] Apparatus_Revenue.Labor_Hours (copy from Apparatus)

### ⚠️ WHAT NEEDS FIXING:
- [ ] Scopes.Total_Apparatus_Hours (change from simple to rollup)

### ❌ WHAT'S MISSING:

**Apparatus Table:**
- [ ] Remaining_Hours (calculated)
- [ ] Percent_Complete (calculated)

**Tasks Table:**
- [ ] Total_Labor_Hours (rollup)
- [ ] Completed_Hours (rollup)
- [ ] Remaining_Hours (calculated)
- [ ] Percent_Complete (calculated)

**Scopes Table:**
- [ ] Completed_Hours (rollup)
- [ ] Remaining_Hours (calculated)
- [ ] Percent_Complete (calculated)

**Projects Table:**
- [ ] Total_Apparatus_Hours (rollup)
- [ ] Completed_Hours (rollup)
- [ ] Remaining_Hours (calculated)
- [ ] Percent_Complete (calculated)

**Total:** 15 hours-related fields to add/fix

---

## 💡 RECOMMENDED APPROACH

### Option A: Fix Critical Scopes Field First
```
1. Fix Scopes.Total_Apparatus_Hours (change to rollup)
   Time: 30 minutes
   Impact: Immediate improvement in scope tracking
```

### Option B: Complete One Table at a Time
```
1. Fix Scopes completely (1 rollup fix + 2 new rollups + 2 calculated)
   Time: 2 hours
   Impact: Scopes table fully functional
   
2. Then do Projects table (2 rollups + 2 calculated)
   Time: 1.5 hours
   
3. Then do Tasks table (2 rollups + 2 calculated)
   Time: 1.5 hours
   
4. Finally add Apparatus calculated fields (XML)
   Time: 30 minutes
```

### Option C: Do All Calculated Fields First (XML)
```
1. Add calculated fields to Apparatus (XML import)
   Time: 30 minutes
   Impact: Apparatus table shows remaining hours
   
2. Then tackle rollups table-by-table
   Time: 4-5 hours total
```

---

## ❓ QUESTIONS FOR YOU

1. **Do you want to start with the critical Scopes.Total_Apparatus_Hours fix?**
   - This is the biggest immediate problem

2. **Should we create ONE example rollup field manually so you can see how it works?**
   - Then extract the XML pattern for automation

3. **Do you understand why some fields are rollups vs calculated?**
   - Rollups aggregate from child records
   - Calculated use formulas on same record

**Let me know which approach you prefer, and I'll guide you step-by-step!**

---

**Document Version:** 1.0  
**Last Updated:** November 10, 2025  
**Purpose:** Complete guide to hours architecture in RESA Power system
