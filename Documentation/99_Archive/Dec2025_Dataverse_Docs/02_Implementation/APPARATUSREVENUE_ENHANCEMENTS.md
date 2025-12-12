# ApparatusRevenue - Field Enhancements

**Version:** 1.3.0.1  
**Created:** November 16, 2025  
**Status:** Ready for Implementation  
**Build Time:** 20-25 minutes

---

## 🎯 Overview

Adding 6 fields to existing ApparatusRevenue table to enable automated revenue recognition.

**Prerequisites:**
- ✅ ScopeLaborDetail table built (v1.3.0.1 exported)
- ✅ Global choice cr950_datasource exists
- ✅ Apparatus table has Completed_Hours and Delays fields (verified)
- ✅ Apparatus.Completed_Hours calculated when Completion_Status = "Complete"

**Existing Fields (VERIFY):**
- ✅ cr950_apparatus (Lookup → Apparatus)
- ✅ cr950_project (Lookup → Projects)
- ⏳ cr950_scope_labor_detail (Lookup → ScopeLaborDetail) - **VERIFY EXISTS, or ADD**
- ✅ cr950_apparatusrevenueid (Primary Key)

**New Fields (ADD):**
- 6 fields for revenue calculation and tracking

---

## 📊 New Fields to Add (6 Fields)

### **Category 1: Hour Tracking (2 fields)**

#### **1. Apparatus Hours**
```
Display Name: Apparatus Hours
Schema Name: cr950_apparatus_hours
Type: Decimal
Precision: 2
Min: 0
Max: 10000
Required: No
Description: Billable hours worked on this apparatus (COMPLETED hours only, when status = Complete)
Example: 45.50
Source: Copied from Apparatus.Completed_Hours (cr950_completed_hours) via Power Automate
Note: This is COMPLETED billable hours, not estimated Apparatus_Hours
```

#### **2. Delays**
```
Display Name: Delays
Schema Name: cr950_delays
Type: Decimal
Precision: 2
Min: 0
Max: 1000
Default: 0
Required: No
Description: Non-billable delay hours (travel issues, waiting, etc.)
Example: 2.25
Source: Copied from Apparatus.Delays via Power Automate
Note: Used for cost tracking, not included in billable calculations
```

---

### **Category 2: Calculated Fields (2 fields)**

#### **3. Total Hours** (Calculated)
```
Display Name: Total Hours
Schema Name: cr950_total_hours
Type: Decimal (Calculated)
Precision: 2
Behavior: Calculated
Formula:
cr950_apparatus_hours + cr950_delays

Example: 47.75 (45.50 apparatus + 2.25 delays)
Description: Total hours spent (billable completed hours + non-billable delays)
Purpose: Cost analysis and utilization tracking
Note: Matches Apparatus.Actual_Hours calculation
```

#### **4. Revenue Amount** (Calculated)
```
Display Name: Revenue Amount
Schema Name: cr950_revenue_amount
Type: Currency (Calculated)
Precision: 2
Behavior: Calculated
Formula:
cr950_apparatus_hours * cr950_effective_labor_rate

Example: $11,056.50 (45.50 hours × $243.00 rate)
Description: **PRIMARY REVENUE FIELD** - Total recognized revenue for this apparatus
Purpose: Revenue recognition, scope rollups, financial reporting
Note: Uses ONLY completed billable hours (not delays, not estimated hours)
```

---

### **Category 3: Rate & Status (2 fields)**

#### **5. Effective Labor Rate**
```
Display Name: Effective Labor Rate
Schema Name: cr950_effective_labor_rate
Type: Currency
Precision: 2
Required: No
Description: Blended rate from ScopeLaborDetail (copied at revenue recognition)
Example: $243.00
Source: Looked up from ScopeLaborDetail.cr950_effective_labor_rate
Strategy: COPY value (not lookup) to preserve historical rate even if scope rates change
Populated: Via Power Automate when apparatus completed
```

#### **6. Revenue Status**
```
Display Name: Revenue Status
Schema Name: cr950_revenue_status
Type: Choice (Option Set - LOCAL, not synced with Apparatus)
Options:
  - PENDING (Value: 1, Default) - Awaiting apparatus completion
  - RECOGNIZED (Value: 2) - Revenue recognized, hours locked
  - ADJUSTED (Value: 3) - Manual adjustment made by Finance
  - VOIDED (Value: 4) - Revenue voided (apparatus re-opened or errors)
Default: PENDING
Required: Yes
Description: Revenue recognition lifecycle state (AUTO-POPULATED by Power Automate)
Purpose: Financial audit trail, prevents double-counting, enables corrections
Populated By: Power Automate flow sets to RECOGNIZED when revenue created
User Access: Read-only on forms (Finance can manually adjust if needed)
Note: Separate from Apparatus.Completion_Status (work tracking)
```

---

## 🔧 Build Steps (Power Apps UI)

### **Step 1: Add Hour Tracking Fields (5 min)**

Navigate to: **ApparatusRevenue > Columns > + New Column**

**Field 1:**
```
Display Name: Apparatus Hours
Schema Name: cr950_apparatus_hours
Data Type: Decimal
Precision: 2
Minimum Value: 0
Maximum Value: 10000
Save
```

**Field 2:**
```
Display Name: Delays
Schema Name: cr950_delays
Data Type: Decimal
Precision: 2
Minimum Value: 0
Maximum Value: 1000
Default Value: 0
Save
```

---

### **Step 2: Add Rate & Status Fields (5 min)**

**Field 3:**
```
Display Name: Effective Labor Rate
Schema Name: cr950_effective_labor_rate
Data Type: Currency
Precision: 2
Save
```

**Field 4:**
```
Display Name: Revenue Status
Schema Name: cr950_revenue_status
Data Type: Choice
⚠️ IMPORTANT: Select "No" when asked "Sync this choice with"
   (Do NOT sync with Apparatus Completion Status - this is different)
Create New Choice (Local):
  Choice Name: Revenue Status
  Options:
    - PENDING (1) - Set as Default
    - RECOGNIZED (2)
    - ADJUSTED (3)
    - VOIDED (4)
Required: Business Required
Note: Make this field READ-ONLY on main form (auto-populated by Power Automate)
Save
```

---

### **Step 3: Add Calculated Fields (5 min)**

**IMPORTANT:** Add in this order (dependencies matter)

**Calc 1: Total Hours**
```
+ New Column
Display Name: Total Hours
Schema Name: cr950_total_hours
Data Type: Decimal
Behavior: Calculated
Formula:
cr950_apparatus_hours + cr950_delays

Save
```

**Calc 2: Revenue Amount**
```
+ New Column
Display Name: Revenue Amount
Schema Name: cr950_revenue_amount
Data Type: Currency
Behavior: Calculated
Formula:
cr950_apparatus_hours * cr950_effective_labor_rate

Save
```

---

### **Step 4: Verify/Add ScopeLaborDetail Lookup**

**Check if lookup exists:**
1. Navigate to: **ApparatusRevenue > Columns**
2. Look for "Scope Labor Detail" (cr950_scope_labor_detail)

**If EXISTS:** ✅ Skip this step (lookup already configured)

**If NOT EXISTS:** Add new lookup:
```
+ New Column
Display Name: Scope Labor Detail
Schema Name: cr950_scope_labor_detail
Data Type: Lookup
Related Table: cr950_scopelabordetail
Required: Business Required
Delete Behavior: Restrict (prevent deleting labor config if revenue exists)
Save
```

**If lookup exists but broken** (after ScopeLaborDetail rebuild):
1. Delete existing lookup column
2. Recreate using steps above

---

## ✅ Validation Test (5-10 min)

### **Create Test Record**

Navigate to: **ApparatusRevenue > + New**

**Input Values:**
```
Name: Test-Revenue-001
Apparatus: [Select any test apparatus]
Project: [Select any test project]
Scope Labor Detail: [SKIP - add after table rebuilt]

--- Hour Tracking ---
Apparatus Hours: 45.50
Delays: 2.25

--- Rate ---
Effective Labor Rate: $243.00

--- Revenue Status (Auto-populated) ---
Revenue Status: PENDING (default, will be set to RECOGNIZED by Power Automate in production)
```

### **Expected Calculated Results**

After saving, verify:

```
✓ Total Hours: 47.75
  Calculation: 45.50 + 2.25 = 47.75

✓ Revenue Amount: $11,056.50
  Calculation: 45.50 × $243.00 = $11,056.50
  
Note: Delays (2.25) NOT included in revenue (only in total hours)
```

**If calculations match:** ✅ Fields correctly configured!

---

## 🔄 Revenue Recognition Workflow (Power Automate - Build Later)

**Trigger:** When Apparatus.Completion_Status = "COMPLETED"

**Actions:**
```
1. Check if ApparatusRevenue record already exists for this Apparatus
   └─ If exists with Status = RECOGNIZED → Skip (prevent duplicates)

2. Get related Scope → ScopeLaborDetail → Effective_Labor_Rate

3. Create new ApparatusRevenue record:
   ├─ Apparatus: [Trigger Apparatus ID]
   ├─ Project: [From Apparatus.Project]
   ├─ Scope Labor Detail: [From Apparatus → Scope → ScopeLaborDetail]
   ├─ Apparatus Hours: [Apparatus.Completed_Hours] (billable hours when complete)
   ├─ Delays: [Apparatus.Delays] (non-billable)
   ├─ Effective Labor Rate: [ScopeLaborDetail.Effective_Labor_Rate] (COPY value)
   ├─ Revenue Status: RECOGNIZED
   └─ Revenue Amount: [Auto-calculated: Apparatus_Hours × Rate]

4. Update Apparatus.Revenue_Recognition_Status = "RECOGNIZED" (optional tracking field)
```

**Build this flow AFTER:**
- ScopeLaborDetail table is built
- Apparatus has Apparatus_Hours and Delays fields
- ApparatusRevenue lookup to ScopeLaborDetail is created

---

## 📋 Field Summary

| # | Field Name | Type | Required | Calculated | Formula/Source |
|---|------------|------|----------|------------|----------------|
| 1 | Apparatus Hours | Decimal | ❌ | ❌ | Copied from Apparatus |
| 2 | Delays | Decimal | ❌ | ❌ | Copied from Apparatus |
| 3 | Total Hours | Decimal | ❌ | ✅ | Apparatus_Hours + Delays |
| 4 | Effective Labor Rate | Currency | ❌ | ❌ | From ScopeLaborDetail |
| 5 | Revenue Amount | Currency | ❌ | ✅ | Apparatus_Hours × Rate |
| 6 | Revenue Status | Choice | ✅ | ❌ | Auto-populated by Power Automate |

---

## 🔗 Dependencies & Next Steps

### **Before Building ApparatusRevenue:**
- ✅ ScopeLaborDetail table built (v1.3.0.1 exported)
- ✅ Global choice cr950_datasource exists
- ✅ Apparatus table has Completed_Hours and Delays fields (verified)

### **After ApparatusRevenue Complete:**
1. **Apparatus Fields Verified** - Completed_Hours (billable), Delays (non-billable), Completion_Status exist
2. **Build Power Automate Flow** - Revenue recognition automation
3. **Test End-to-End** - Create apparatus → complete → verify revenue created
4. **Export Solution** - v1.3.0.1 with ApparatusRevenue enhancements

### **Future (Rollup Tables):**
- ScopeFinancials will rollup SUM(ApparatusRevenue.Revenue_Amount)
- ProjectFinancials will aggregate across all scopes
- MonthlyFinancialTracking for period reporting

---

## 📤 Solution Export (After Build Complete)

1. **Solutions > [Your Solution]**
2. **Overview > Version** → Keep at `1.3.0.1` (same version as ScopeLaborDetail)
3. **Export > Managed + Unmanaged**
4. Save both to: `C:\RESA_Power_Build\Solutions\v1_3_0_1\`
5. Git commit with message:
   ```
   feat: Enhanced ApparatusRevenue table v1.3.0.1 - revenue calculations
   
   - Added 6 fields for automated revenue recognition
   - Hour tracking: Apparatus_Hours, Delays, Total_Hours (calculated)
   - Revenue calculation: Effective_Labor_Rate, Revenue_Amount (calculated)
   - Lifecycle tracking: Revenue_Status (PENDING/RECOGNIZED/ADJUSTED/VOIDED)
   - Verified ScopeLaborDetail lookup exists and works
   - Historical rate preservation (copy, not lookup)
   - Separate billable (Apparatus_Hours) vs non-billable (Delays) tracking
   - Standardized terminology: "Apparatus Hours" matches domain language
   - Ready for Power Automate revenue recognition flow
   - Integrates with ScopeLaborDetail v1.3.0.1 foundation
   ```

---

## 🎯 Design Decisions

### **Why COPY Effective_Labor_Rate (not lookup)?**
**Problem:** If ScopeLaborDetail rates change for future work, old revenue records would show wrong rates.

**Solution:** Copy the rate value at revenue recognition time.
- **Historical accuracy:** Old revenue shows rate that was actually used
- **Audit trail:** Can see if rates changed over project lifecycle
- **Financial integrity:** Revenue never recalculates retroactively

### **Why Use Completed_Hours (not Apparatus_Hours)?**
**Apparatus Table Has Two "Hours" Fields:**
- **Apparatus_Hours:** Estimated hours (planning/quoting)
- **Completed_Hours:** Actual billable hours (when Completion_Status = "Complete")

**Revenue Uses Completed Hours Because:**
- ✅ Actual work performed (not estimate)
- ✅ Only populated when apparatus truly complete
- ✅ May differ from estimate (faster/slower than expected)
- ✅ Real billable time (what customer actually pays for)

**Example:**
```
Apparatus_Hours: 50.0 (estimated)
Completed_Hours: 45.5 (actual - finished faster!)
Delays: 2.25 (waiting for parts)
Actual_Hours: 47.75 (total time: completed + delays)
Revenue: $11,056.50 (45.5 × $243 - bills actual, not estimate)
```

### **Why Delays Separate from Apparatus_Hours?**
**Problem:** Need to track ALL time spent (including non-billable) for cost analysis.

**Solution:** Separate fields with different purposes:
- **Apparatus_Hours:** Billable (drives revenue calculation)
- **Delays:** Non-billable (cost tracking only)
- **Total_Hours:** Total time (utilization analysis)

**Example:**
```
Apparatus Hours: 45.50 (billable)
Delays: 2.25 (waiting for parts)
Total Hours: 47.75 (real time spent)
Revenue: $11,056.50 (45.50 × $243, delays NOT included)
```

### **Why Revenue_Status Auto-Populated Field?**
**Auto-Population Prevents:**
- ❌ Double revenue recognition (can't manually set to RECOGNIZED twice)
- ❌ Revenue on incomplete work (only Power Automate can create records)
- ❌ Human error in status tracking
- ❌ Lost audit trail

**User Interaction:**
- ✅ Default: PENDING (until apparatus completed)
- ✅ Power Automate: Sets to RECOGNIZED when creating revenue record
- ✅ Finance: Can manually adjust to ADJUSTED or VOIDED if needed
- ✅ Form: Read-only field (prevents accidental changes)
- ✅ Separate: Different from Apparatus.Completion_Status (work: Not Started/In Progress/Complete)

**Enables:**
- ✅ Finance corrections (ADJUSTED status)
- ✅ Voiding errors (VOIDED status)
- ✅ Clear lifecycle visibility
- ✅ Automated workflow integrity

---

## 📊 Usage Example

**Scenario:** Field tech completes Circuit Breaker testing

```
1. Field Tech marks Apparatus complete:
   Apparatus.Completion_Status = "COMPLETED"
   Apparatus.Completed_Hours = 45.50 (calculated when marked complete)
   Apparatus.Delays = 2.25
   Apparatus.Actual_Hours = 47.75 (auto-calculated: 45.50 + 2.25)

2. Power Automate triggers:
   Creates ApparatusRevenue record

3. System lookups:
   Apparatus → Scope → ScopeLaborDetail → Effective_Labor_Rate ($243.00)

4. ApparatusRevenue record created:
   ├─ Apparatus Hours: 45.50
   ├─ Delays: 2.25
   ├─ Total Hours: 47.75 (calculated)
   ├─ Effective Labor Rate: $243.00 (copied)
   ├─ Revenue Amount: $11,056.50 (calculated: 45.50 × $243)
   └─ Revenue Status: RECOGNIZED

5. Finance sees:
   Revenue recognized: $11,056.50
   Total time: 47.75 hours
   Efficiency: 95.3% billable (45.50/47.75)
```

---

**Ready to build? Estimated time: 20-25 minutes (excluding ScopeLaborDetail lookup)**
