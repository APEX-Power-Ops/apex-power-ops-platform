# APPARATUS HOURS TERMINOLOGY AUDIT
**Version:** 1.0.0  
**Created:** 2025-01-XX  
**Purpose:** Audit and standardize "Apparatus Hours" vs "Labor Hours" terminology across all tables and documentation

---

## AUDIT SUMMARY

### ✅ **DECISION: Standardize on "APPARATUS HOURS"**

**Rationale:**
1. **Domain Alignment:** Business is apparatus testing (equipment-centric, not human labor-centric)
2. **Excel Consistency:** Excel Estimator uses "Total App Hours" (176 hrs in example)
3. **Clarity Throughout Chain:** ScopeLaborDetail → Apparatus → ApparatusRevenue all track equipment hours
4. **Avoids Confusion:** "Labor Hours" could imply crew hours (3 techs × 5 hrs = 15 labor hours) vs apparatus hours (1 apparatus × 5 hrs = 5 apparatus hours)

**User Approval:** "Yes, We'll need to audit other tables to confirm but definitely" (2025-01-XX)

---

## TABLE-BY-TABLE AUDIT

### ✅ **1. ScopeLaborDetail** (v1.3.0.1 - COMPLETED)
**Status:** CONSISTENT - Uses "Apparatus Hours"

**Fields:**
- `Total_Apparatus_Hours` (cr950_total_apparatus_hours) ✅ CORRECT
- Description: "Total apparatus hours for this scope (denominator for rate calculations). Example: 176 hours"

**Documentation:**
- Location: `C:\RESA_Power_Build\Documentation\02_Implementation\SCOPELABORDETAIL_BUILD_SPEC.md`
- Status: ✅ Built and exported v1.3.0.1
- Terminology: Consistent throughout

---

### ✅ **2. ApparatusRevenue** (v1.3.0.1 - SPEC UPDATED)
**Status:** CONSISTENT - Uses "Apparatus Hours"

**Fields:**
- `Apparatus_Hours` (cr950_apparatus_hours) ✅ CORRECT
- `Delays` (cr950_delays) ✅ CORRECT
- `Total_Hours` (cr950_total_hours) ✅ CORRECT - Calculated: Apparatus_Hours + Delays
- `Revenue_Amount` (cr950_revenue_amount) ✅ CORRECT - Calculated: Apparatus_Hours × Rate

**Documentation:**
- Location: `C:\RESA_Power_Build\Documentation\02_Implementation\APPARATUSREVENUE_ENHANCEMENTS.md`
- Status: ✅ Spec updated v1.3.0.1 (16 replacements completed)
- Terminology: Fully standardized to "Apparatus Hours"
- Build Status: ⏳ Ready to build (6 fields, 20-25 min)

**Changes Made:**
- "Labor Hours" → "Apparatus Hours" (display name, schema name, descriptions)
- "Actual Hours" → "Total Hours" (clearer meaning: apparatus + delays)
- All formulas updated
- All build steps updated
- All validation tests updated
- Power Automate flow specs updated

---

### ✅ **3. Apparatus** (CORRECT STRUCTURE CONFIRMED)
**Status:** FIELDS VERIFIED - Correct structure in place

**Actual Field Structure:**
- ✅ `Apparatus_Hours` (cr950_apparatus_hours) - Estimated hours for this apparatus
- ✅ `Delays` (cr950_delays) - Non-billable delay hours
- ✅ `Completed_Hours` (cr950_completed_hours) - Calculated when Completion_Status = "Complete"
- ✅ `Actual_Hours` (cr950_actual_hours) - Calculated: Completed_Hours + Delays
- ✅ `Remaining_Hours` (cr950_remaining_hours) - Calculated: Apparatus_Hours - Completed_Hours

**Calculation Logic:**
```
Completed Hours = Billable hours when apparatus marked Complete
Actual Hours = Completed_Hours + Delays (total time spent)
Remaining Hours = Apparatus_Hours - Completed_Hours (work left)
```

**For Revenue Recognition:**
- ✅ Use `Completed_Hours` (billable only)
- ✅ Copy `Delays` separately (non-billable tracking)
- ✅ ApparatusRevenue.Total_Hours = Completed_Hours + Delays
- ✅ ApparatusRevenue.Revenue = Completed_Hours × Rate (NOT including delays)

**ACTION REQUIRED:**
- ✅ All fields exist correctly
- ⚠️ Update ApparatusRevenue spec to use `Completed_Hours` (not `Apparatus_Hours`)
- ⚠️ Update Power Automate to copy `Completed_Hours` (not `Apparatus_Hours`)

**Priority:** HIGH - ApparatusRevenue spec needs correction

---

### ⚠️ **4. Apparatus_Type_Master** (NEEDS AUDIT)
**Status:** INCONSISTENT - Uses "Labor Hours" terminology

**Fields (from archived spec):**
- ❌ `NETA_ATS_Labor_Hours` (cr950_neta_ats_labor_hours) - **SHOULD BE: NETA_ATS_Apparatus_Hours**
- ❌ `NETA_MTS_Labor_Hours` (cr950_neta_mts_labor_hours) - **SHOULD BE: NETA_MTS_Apparatus_Hours**

**Documentation References:**
- `RESA_Power_Project_Tracker_Master_Build_Specification_UPDATED.md` line 289: "NETA_ATS_Labor_Hours | Decimal | - | No | - | No | ⭐ Default labor hours for ATS testing"
- `RESA_Power_Project_Tracker_Master_Build_Specification_UPDATED.md` line 290: "NETA_MTS_Labor_Hours | Decimal | - | No | - | No | ⭐ Default labor hours for MTS testing"

**ACTION REQUIRED:**
1. ⚠️ Rename `NETA_ATS_Labor_Hours` → `NETA_ATS_Apparatus_Hours`
2. ⚠️ Rename `NETA_MTS_Labor_Hours` → `NETA_MTS_Apparatus_Hours`
3. ⚠️ Update all lookups/formulas that reference these fields
4. ⚠️ Update documentation to reflect "apparatus hours" (not "labor hours")

**Priority:** MEDIUM - Not blocking ApparatusRevenue build, but important for consistency

---

### ⚠️ **5. Excel MCP Server Config** (NEEDS UPDATE)
**Status:** INCONSISTENT - Uses "labor_hours" in field mappings

**References:**
- `EXCEL_MCP_QUICK_START.md` line 182: `"labor_hours": "E"` ❌ **SHOULD BE: apparatus_hours**
- `EXCEL_MCP_QUICK_START.md` line 194: `"apparatus": ["apparatus_type", "designation", "quoted_labor_hours"]` ❌ **SHOULD BE: quoted_apparatus_hours**
- `EXCEL_MCP_QUICK_START.md` line 205: `"Quoted_Labor_Hours": "quoted_labor_hours"` ❌ **SHOULD BE: Quoted_Apparatus_Hours**

**ACTION REQUIRED:**
1. ⚠️ Update field mapping: `labor_hours` → `apparatus_hours`
2. ⚠️ Update field mapping: `quoted_labor_hours` → `quoted_apparatus_hours`
3. ⚠️ Update Excel column headers expected by parser
4. ⚠️ Update MCP tool parameter names

**Priority:** LOW - Excel MCP not yet implemented (1-2 weeks out)

---

### ⚠️ **6. Projects Table** (NEEDS VERIFICATION)
**Status:** UNKNOWN - May have rollup fields

**Expected Rollup Fields (from archived spec):**
- ⚠️ `Total_Apparatus_Hours` (cr950_total_apparatus_hours) - Sum from Scopes - **SHOULD USE THIS NAME**

**Documentation References:**
- `RESA_Power_Project_Tracker_Master_Build_Specification_UPDATED.md` line 453: "Total_Apparatus_Hours | Scopes | SUM | Total_App_Hours | Sum of all apparatus hours"

**ACTION REQUIRED:**
1. ⚠️ Verify field exists and uses "Apparatus Hours" (not "Labor Hours")
2. ⚠️ Verify rollup formula sources from correct Scopes field

**Priority:** MEDIUM - Important for project-level reporting

---

### ⚠️ **7. Scopes Table** (NEEDS VERIFICATION)
**Status:** UNKNOWN - May have rollup fields

**Expected Rollup Fields (from archived spec):**
- ⚠️ `Total_Apparatus_Hours` (cr950_total_apparatus_hours) - Sum from Apparatus - **SHOULD USE THIS NAME**

**Documentation References:**
- `RESA_Power_Project_Tracker_Master_Build_Specification_UPDATED.md` line 507: "Total_Apparatus_Hours | Decimal | - | No | - | No | Sum of all apparatus hours (can be rollup)"

**ACTION REQUIRED:**
1. ⚠️ Verify field exists and uses "Apparatus Hours" (not "Labor Hours")
2. ⚠️ Verify rollup formula sources from Apparatus.Apparatus_Hours

**Priority:** MEDIUM - Important for scope-level reporting

---

### ⚠️ **8. Tasks Table** (NEEDS VERIFICATION)
**Status:** UNKNOWN - May have rollup fields

**Expected Rollup Fields (from archived spec):**
- ⚠️ `Task_Apparatus_Hours` (cr950_task_apparatus_hours) - Sum from Apparatus - **SHOULD USE THIS NAME**
- ❌ `Apparatus_Hours` (cr950_apparatus_hours) - Individual field - **VERIFY NAME**

**Documentation References:**
- `RESA_Power_Project_Tracker_Master_Build_Specification_UPDATED.md` line 625: "Apparatus_Hours | Decimal | - | No | - | No | Total estimated hours (rollup from apparatus)"
- `RESA_Power_Project_Tracker_Master_Build_Specification_UPDATED.md` line 644: "Task_Apparatus_Hours | Apparatus | SUM | Apparatus_Hours | Sum of apparatus hours"

**ACTION REQUIRED:**
1. ⚠️ Verify field exists and uses "Apparatus Hours" (not "Labor Hours")
2. ⚠️ Verify rollup formula sources from Apparatus.Apparatus_Hours

**Priority:** MEDIUM - Important for task-level tracking

---

## ROLLUP FIELD AUDIT

### **Rollup Chain Architecture (VERIFIED)**

**Four-Tier Hour Tracking:**

```
┌─────────────────────────────────────────────────────────────┐
│ APPARATUS (Data Entry Level)                                │
├─────────────────────────────────────────────────────────────┤
│ Apparatus_Hours:    50.0 (estimated)                        │
│ Completed_Hours:    45.5 (actual billable)                  │
│ Delays:              2.25 (non-billable)                     │
│ Actual_Hours:       47.75 (completed + delays, calculated)  │
│ Remaining_Hours:     4.5 (apparatus - completed, calculated)│
└─────────────────────────────────────────────────────────────┘
                         ↓ [Rollup SUM]
┌─────────────────────────────────────────────────────────────┐
│ TASK (Optional Grouping)                                     │
├─────────────────────────────────────────────────────────────┤
│ Task_Apparatus_Hours:     SUM(Apparatus.Apparatus_Hours)    │
│ Task_Completed_Hours:     SUM(Apparatus.Completed_Hours)    │
│ Task_Actual_Hours:        SUM(Apparatus.Actual_Hours)       │
│ Task_Remaining_Hours:     SUM(Apparatus.Remaining_Hours)    │
└─────────────────────────────────────────────────────────────┘
                         ↓ [Rollup SUM]
┌─────────────────────────────────────────────────────────────┐
│ SCOPE (Project Section)                                      │
├─────────────────────────────────────────────────────────────┤
│ Total_Apparatus_Hours:    SUM(Apparatus.Apparatus_Hours)    │
│ Total_Completed_Hours:    SUM(Apparatus.Completed_Hours)    │
│ Total_Actual_Hours:       SUM(Apparatus.Actual_Hours)       │
│ Total_Remaining_Hours:    SUM(Apparatus.Remaining_Hours)    │
└─────────────────────────────────────────────────────────────┘
                         ↓ [Rollup SUM]
┌─────────────────────────────────────────────────────────────┐
│ PROJECT (Top Level)                                          │
├─────────────────────────────────────────────────────────────┤
│ Total_Apparatus_Hours:    SUM(Scope.Total_Apparatus_Hours)  │
│ Total_Completed_Hours:    SUM(Scope.Total_Completed_Hours)  │
│ Total_Actual_Hours:       SUM(Scope.Total_Actual_Hours)     │
│ Total_Remaining_Hours:    SUM(Scope.Total_Remaining_Hours)  │
└─────────────────────────────────────────────────────────────┘
```

**Rollup Verification Needed:**

**Tasks Table:**
- ✅ "Total Apparatus Count" = COUNT(Apparatus)
- ✅ "Completed Apparatus Count" = COUNT(Apparatus WHERE Completion_Status = "Complete")
- ✅ "Percent Complete" = (Completed / Total) × 100 (calculated)
- ✅ "Apparatus Hours" = SUM(Apparatus.Apparatus Hours)
- ✅ "Completed Hours" = SUM(Apparatus.Completed Hours)
- ✅ "Actual Hours" = SUM(Apparatus.Actual Hours)
- ✅ "Remaining Hours" = SUM(Apparatus.Remaining Hours)

**Scopes Table (Project Scope):**
- ✅ "Total Apparatus Count" = COUNT(Apparatus)
- ✅ "Completed Apparatus Count" = COUNT(Apparatus WHERE Completion_Status = "Complete")
- ✅ "Percent Complete" = (Completed / Total) × 100 (calculated)
- ✅ "Apparatus Hours" = SUM(Apparatus.Apparatus Hours)
- ✅ "Completed Hours" = SUM(Apparatus.Completed Hours)
- ✅ "Actual Hours" = SUM(Apparatus.Actual Hours)
- ✅ "Remaining Hours" = SUM(Apparatus.Remaining Hours)

**Projects Table:**
- ✅ "Total Apparatus Count" = SUM(Scope.Total Apparatus Count)
- ✅ "Completed Apparatus Count" = SUM(Scope.Completed Apparatus Count)
- ✅ "Percent Complete" = (Completed / Total) × 100 (calculated)
- ✅ "Apparatus Hours" = SUM(Scope.Apparatus Hours)
- ✅ "Completed Hours" = SUM(Scope.Completed Hours)
- ✅ "Actual Hours" = SUM(Scope.Actual Hours)
- ✅ "Remaining Hours" = SUM(Scope.Remaining Hours)

**Why This Architecture Matters for Revenue:**
- ✅ Scope rollups show: Estimated vs Actual vs Remaining for entire scope
- ✅ Revenue uses Completed_Hours (actual billable work)
- ✅ Cost analysis uses Actual_Hours (completed + delays)
- ✅ Planning uses Apparatus_Hours (estimates)
- ✅ Remaining_Hours tracks work still to be done

---

## CALCULATED FIELD AUDIT

### **Formula Consistency Check**

**Apparatus Table:**
- ⚠️ `Actual_Hours` = `Apparatus_Hours + Delays` (verify formula uses correct field names)
- ⚠️ `Remaining_Hours` = `Apparatus_Hours - Actual_Hours` (verify formula)
- ⚠️ `Percent_Complete` = `(Actual_Hours / Apparatus_Hours) * 100` (verify formula)

**ApparatusRevenue Table:**
- ✅ `Total_Hours` = `cr950_apparatus_hours + cr950_delays` (spec updated v1.3.0.1)
- ✅ `Revenue_Amount` = `cr950_apparatus_hours * cr950_effective_labor_rate` (spec updated v1.3.0.1)

---

## POWER AUTOMATE FLOW AUDIT

### **Revenue Recognition Flow**

**Trigger:** Apparatus.Completion_Status = "COMPLETED"

**Field Mappings (MUST USE CORRECT NAMES):**
- ✅ Source: `Apparatus.Apparatus_Hours` → Target: `ApparatusRevenue.Apparatus_Hours`
- ✅ Source: `Apparatus.Delays` → Target: `ApparatusRevenue.Delays`
- ✅ Source: `ScopeLaborDetail.Effective_Labor_Rate` → Target: `ApparatusRevenue.Effective_Labor_Rate`

**Status:** ⏳ Not yet built (pending ApparatusRevenue table build)

---

## ACTION ITEMS

### **Priority 1: IMMEDIATE (Update ApparatusRevenue Spec)**
1. ✅ **Apparatus Fields Verified:**
   - ✅ Apparatus_Hours (estimated)
   - ✅ Delays (non-billable)
   - ✅ Completed_Hours (billable when complete)
   - ✅ Actual_Hours (calculated: completed + delays)
   - ✅ Remaining_Hours (calculated: apparatus - completed)
   - Time: 0 minutes (already correct!)

2. ⚠️ **Update ApparatusRevenue Spec:**
   - [ ] Change field source: Apparatus_Hours → Completed_Hours
   - [ ] Update all references to use Completed_Hours (billable)
   - [ ] Update Power Automate flow mapping
   - Time: 5 minutes

### **Priority 2: BUILD PHASE (Next Step)**
2. ✅ **Build ApparatusRevenue Enhancements:**
   - [ ] Follow spec: APPARATUSREVENUE_ENHANCEMENTS.md v1.3.0.1
   - [ ] Add 6 fields (all using "Apparatus Hours" terminology)
   - [ ] Export v1.3.0.1 solution
   - Time: 20-25 minutes

### **Priority 3: MEDIUM (After ApparatusRevenue Build)**
3. ⚠️ **Audit Apparatus_Type_Master:**
   - [ ] Check if `NETA_ATS_Labor_Hours` and `NETA_MTS_Labor_Hours` exist
   - [ ] Rename to `NETA_ATS_Apparatus_Hours` and `NETA_MTS_Apparatus_Hours` if needed
   - [ ] Update all formulas/lookups
   - Time: 15-20 minutes

4. ⚠️ **Audit Projects/Scopes/Tasks Rollup Fields:**
   - [ ] Verify `Total_Apparatus_Hours` exists in Projects
   - [ ] Verify `Total_Apparatus_Hours` exists in Scopes
   - [ ] Verify `Task_Apparatus_Hours` exists in Tasks
   - [ ] Verify all rollup formulas source from correct fields
   - Time: 15-20 minutes

### **Priority 4: LOW (Future - Before Excel MCP Build)**
5. ⚠️ **Update Excel MCP Configuration:**
   - [ ] Update field mappings to use `apparatus_hours` (not `labor_hours`)
   - [ ] Update column header expectations
   - [ ] Update MCP tool parameters
   - Time: 10-15 minutes (when implementing MCP)

---

## DOCUMENTATION UPDATES

### **Files Requiring Terminology Updates**

**✅ COMPLETED:**
1. `APPARATUSREVENUE_ENHANCEMENTS.md` v1.3.0.1 - 16 replacements completed
2. `SCOPELABORDETAIL_BUILD_SPEC.md` v1.3.0.1 - Already uses "Apparatus Hours"

**⏳ PENDING:**
1. `MASTER_BUILD_SPECIFICATION.md` - Verify Apparatus table section (line 703-856)
2. `EXCEL_MCP_QUICK_START.md` - Update field mappings (3 locations)
3. `EXCEL_MCP_IMPLEMENTATION_PLAN.md` - Update field references
4. `FIELD_TECH_APPLICATION_SPEC.md` - Update calculated field formulas (line 446)
5. `RESA_Power_Project_Tracker_Master_Build_Specification_UPDATED.md` (ARCHIVED) - Update Apparatus_Type_Master section

---

## VALIDATION CHECKLIST

### **Post-Implementation Verification**

**After All Changes:**
- [ ] Search all .md files for "labor.hours" regex (should find ZERO matches in active files)
- [ ] Search all .md files for "labor_hours" (should find ZERO matches in active files)
- [ ] Verify Excel Estimator still uses "Total App Hours" (176 hrs example)
- [ ] Verify ScopeLaborDetail uses "Total Apparatus Hours"
- [ ] Verify Apparatus uses "Apparatus Hours"
- [ ] Verify ApparatusRevenue uses "Apparatus Hours"
- [ ] Verify all rollup fields use "Apparatus Hours"
- [ ] Verify all calculated field formulas reference correct field names
- [ ] Test end-to-end: Excel import → Apparatus → ApparatusRevenue → Revenue calculation

---

## RISK ASSESSMENT

### **Impact of Inconsistent Terminology**

**HIGH RISK:**
- ❌ Calculated field formulas break if referencing wrong field name
- ❌ Power Automate flows fail if field mappings incorrect
- ❌ Rollup fields return NULL if source field doesn't exist
- ❌ Excel MCP import fails if column mappings wrong

**MEDIUM RISK:**
- ⚠️ User confusion when seeing "Labor Hours" in some places, "Apparatus Hours" in others
- ⚠️ Documentation inconsistency makes maintenance difficult
- ⚠️ Training materials conflict with actual field names

**LOW RISK:**
- 🔵 Historical archived documents retain old terminology (acceptable - marked as ARCHIVED)

---

## TERMINOLOGY STANDARD (FINAL)

### **Official Naming Convention**

**ALWAYS USE:**
- ✅ "Apparatus Hours" (display name)
- ✅ "apparatus_hours" (schema name)
- ✅ "cr950_apparatus_hours" (full schema name with prefix)
- ✅ "Total Apparatus Hours" (when aggregating multiple apparatus)

**NEVER USE:**
- ❌ "Labor Hours" (too ambiguous - crew hours vs equipment hours)
- ❌ "Test Hours" (less clear)
- ❌ "Work Hours" (less specific)
- ❌ "Man Hours" (outdated, gendered)

**EXCEPTION:**
- ✅ "Actual Hours" → Rename to "Total Hours" (Apparatus Hours + Delays) for clarity

---

## APPROVAL LOG

| Date | Person | Decision |
|------|--------|----------|
| 2025-01-XX | User | Approved "Apparatus Hours" standardization |
| 2025-01-XX | Agent | Completed ApparatusRevenue spec v1.3.0.1 (16 replacements) |

---

## NEXT STEPS

1. **IMMEDIATE:** Verify Apparatus table fields (10 min)
2. **NEXT:** Build ApparatusRevenue enhancements (20-25 min)
3. **THEN:** Audit Apparatus_Type_Master (15-20 min)
4. **THEN:** Audit Projects/Scopes/Tasks rollups (15-20 min)
5. **LATER:** Update Excel MCP config (when implementing MCP)

**Total Estimated Time:** 60-75 minutes (excluding Excel MCP updates)

---

**END OF AUDIT**
