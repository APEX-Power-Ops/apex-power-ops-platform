# Apparatus Date Fields - Quick Build

**Version:** 1.3.0.2  
**Purpose:** Add 3 date fields to Apparatus table for Excel MCP import testing  
**Time:** 17 minutes (includes making Date Completed read-only)  
**Priority:** CRITICAL - Blocking Excel MCP testing

---

## 🎯 Overview

**Goal:** Add minimum date fields needed for Excel estimator import.

**Why Critical:** Excel estimators have planned start dates that need to import into Dataverse. Without these fields, MCP testing cannot proceed.

**Defer Until After Testing:**
- Rollup fields to Tasks/Scopes/Projects
- Calculated fields (variance, duration, etc.)
- KPI views
- Form updates

---

## 📋 Fields to Add (3 Fields)

### **1. Anticipated Start**
```
Display Name: Anticipated Start
Schema Name: cr950_anticipated_start
Type: Date and Time
Behavior: User Local
Required: No
Description: Planned start date from Excel estimator
```

### **2. Actual Start**
```
Display Name: Actual Start
Schema Name: cr950_actual_start
Type: Date and Time
Behavior: User Local
Required: No
Description: When work actually began (field tech entry or auto-populated)
```

### **3. Date Completed**
```
Display Name: Date Completed
Schema Name: cr950_date_completed
Type: Date and Time
Behavior: User Local
Required: No
Description: When apparatus was completed (auto-populated by Power Automate)
Critical: Auto-set when Completion Status = Complete (too important for revenue)
Note: CHECK IF EXISTS FIRST - may already be in table
```

---

## 🔧 Build Steps (15 minutes)

### **Step 1: Check for Existing Date Fields (2 min)**

1. Navigate to: **Apparatus > Columns**
2. Search for: "date"
3. Look for any existing date fields

**If Date Completed EXISTS:**
- ✅ Skip creating it
- ✅ Verify schema name (cr950_date_completed or similar)
- ✅ Only add Anticipated Start and Actual Start

**If Date Completed DOES NOT EXIST:**
- ⚠️ Add all 3 fields below

---

### **Step 2: Add Anticipated Start (4 min)**

1. Navigate to: **Apparatus > Columns > + New Column**

```
Display Name: Anticipated Start
Schema Name: cr950_anticipated_start
Data Type: Date and Time
Behavior: User Local
Required: No
Searchable: Yes
Description: Planned start date from Excel estimator
Save
```

---

### **Step 3: Add Actual Start (4 min)**

```
+ New Column
Display Name: Actual Start
Schema Name: cr950_actual_start
Data Type: Date and Time
Behavior: User Local
Required: No
Searchable: Yes
Description: When work actually began
Save
```

---

### **Step 4: Add Date Completed (4 min) - IF NEEDED**

**Only if field doesn't already exist:**

```
+ New Column
Display Name: Date Completed
Schema Name: cr950_date_completed
Data Type: Date and Time
Behavior: User Local
Required: No
Searchable: Yes
Description: When apparatus was completed (auto-populated by Power Automate)
Save
```

---

### **Step 5: Make Date Completed Read-Only (2 min)**

1. Navigate to: **Apparatus > Forms > Main Form**
2. Find **Date Completed** field on form
3. Select field → **Properties**
4. **Field Properties:**
   - Read-only: **Yes**
   - Visible: **Yes**
   - Label: Add note "(Auto-set when Complete)"
5. **Save** and **Publish**

**Why:** Too critical for revenue recognition to allow manual entry. Power Automate will set this when Completion Status = Complete.

---

### **Step 6: Publish (1 min)**

1. Click **Publish All Customizations**
2. Wait for confirmation

---

## ✅ Verification (Quick Test)

1. Navigate to: **Apparatus > Data**
2. Open any test apparatus record
3. Verify you can see the 3 date fields
4. Set Anticipated Start = Tomorrow (should be editable)
5. Try to edit Date Completed (should be read-only with note)
6. Save
7. ✅ Done!

---

## 📤 Export Solution v1.3.0.2

1. **Solutions > [Your Solution]**
2. **Overview > Version** → Update to `1.3.0.2`
3. **Export > Managed + Unmanaged**
4. Save to: `C:\RESA_Power_Build\Solutions\v1_3_0_2\`

**Version History:**
- v1.3.0.0 = ScopeLaborDetail (14 fields)
- v1.3.0.1 = ApparatusRevenue (6 fields)
- v1.3.0.2 = Apparatus date fields (3 fields) ← **You are here**

---

## 🔗 Next Steps After This Build

### **Immediate (Enable Excel MCP Testing):**
1. ✅ Date fields now exist
2. ✅ Excel MCP can map "Planned Start" → Anticipated Start
3. ✅ Begin end-to-end import testing
4. ✅ Test ScopeLaborDetail import (estimator rates)
5. ✅ Test Apparatus import (equipment list with dates)

### **After Successful MCP Testing:**
1. Add Task/Scope/Project date rollups (20 min per table)
2. Add calculated fields (15 min)
3. Create KPI views (30 min)
4. Build Power Automate revenue recognition flow (30-45 min)
5. Update forms with date sections (15 min)

---

## 📋 Excel MCP Field Mappings (Reference)

**Excel Column → Dataverse Field:**
```
Estimator Sheet:
├─ "Planned Start" or "Start Date" → Apparatus.Anticipated_Start
├─ "Quantity" → Multiple Apparatus records
└─ [Continue with existing mappings]

Labor Rates Section:
├─ "Onsite Labor Total" → ScopeLaborDetail.Onsite_Labor_Total
├─ "Offsite Labor Total" → ScopeLaborDetail.Offsite_Labor_Total
├─ "Travel Total" → ScopeLaborDetail.Travel_Total
├─ "Outside Services Total" → ScopeLaborDetail.Outside_Services_Total
├─ "Total App Hours" → ScopeLaborDetail.Total_Apparatus_Hours
└─ "Scope Multiplier" → ScopeLaborDetail.Scope_Multiplier
```

**Now all fields exist for complete Excel import!**

---

## 🎯 What This Enables

### **Excel MCP Can Now Import:**
- ✅ Project header (name, location, dates)
- ✅ Scope labor rates (onsite, offsite, travel, outside services)
- ✅ Apparatus list (type, designation, hours, **anticipated start**)
- ✅ Calculate effective labor rate ($363.68/hr from example)
- ✅ Revenue recognition ready (when apparatus completed)

### **Testing Workflow:**
1. **Open Excel estimator** with test data
2. **Run MCP import** → Creates/updates records
3. **Verify ScopeLaborDetail** → Rates imported correctly
4. **Verify Apparatus** → Equipment list with dates
5. **Mark apparatus complete** → Revenue recognition (manual for now)
6. **Check ApparatusRevenue** → Revenue calculated correctly

---

## 🔍 Field Verification Checklist

Before declaring "ready for MCP testing", verify these fields exist:

### **ScopeLaborDetail Table:**
- [x] Project Scope (lookup)
- [x] Total Apparatus Hours
- [x] Onsite Labor Total
- [x] Offsite Labor Total
- [x] Travel Total
- [x] Outside Services Total
- [x] Onsite Labor Rate (calculated)
- [x] Offsite Labor Rate (calculated)
- [x] Travel Rate (calculated)
- [x] Outside Services Rate (calculated)
- [x] Effective Labor Rate (calculated)
- [x] Scope Multiplier
- [x] Source (global choice)
- [x] Notes

### **Apparatus Table:**
- [x] Apparatus_Hours (estimated)
- [x] Completed_Hours (billable)
- [x] Delays (non-billable)
- [x] Actual_Hours (calculated)
- [x] Remaining_Hours (calculated)
- [ ] **Anticipated Start** ← Adding now
- [ ] **Actual Start** ← Adding now
- [ ] **Date Completed** ← Verify exists or add

### **ApparatusRevenue Table:**
- [x] Apparatus Hours (from Completed_Hours)
- [x] Delays
- [x] Total Hours (calculated)
- [x] Effective Labor Rate
- [x] Revenue Amount (calculated)
- [x] Revenue Status (choice)
- [x] Scope Labor Detail (lookup)

---

## 🚀 Git Commit Message

```
feat: Add Apparatus date fields v1.3.0.2 - enable Excel MCP testing

- Added Anticipated Start (cr950_anticipated_start) - User Local behavior
- Added Actual Start (cr950_actual_start) - User Local behavior
- Verified/Added Date Completed (cr950_date_completed) - User Local, auto-populated
- Date Completed set to read-only (Power Automate auto-sets when Complete)
- User Local behavior: timezone-aware scheduling for multi-location teams
- All base fields now in place for Excel MCP import
- Enables end-to-end testing: Excel estimator → Dataverse → Revenue
- Deferred rollups and calculated fields until after MCP testing
- Build time: 17 minutes
- Ready for Excel import testing

Dependencies:
- ScopeLaborDetail v1.3.0.1 (rates import) ✅
- ApparatusRevenue v1.3.0.1 (revenue calc) ✅
- Apparatus date fields v1.3.0.2 (this build) ⏳

Next: Test Excel MCP end-to-end import workflow, then build Power Automate
flow to auto-set Date Completed when Completion Status = Complete
```

---

**Ready to build! 15 minutes to Excel MCP testing.**
