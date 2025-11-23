# APPARATUS DATE FIELDS - CLEANUP DECISION
**Date**: November 23, 2025  
**Status**: ⚠️ **CRITICAL - DUPLICATES CONFIRMED**  
**Action Required**: Delete duplicate fields before rollup implementation

---

## 🔍 VERIFIED DUPLICATE FIELDS

### **3 Sets of Duplicates Identified:**

#### **Set 1: Anticipated Start**
| Field Name | Schema Name | Required Level | Description | Status |
|---|---|---|---|---|
| cr950_anticipated_start | cr950_anticipated_start | None | When work is planned to begin on this apparatus | 🟡 Older (underscore) |
| cr950_anticipatedstart | cr950_AnticipatedStart | **Recommended** | When work is planned to begin on this apparatus | ✅ **Recommended (PascalCase)** |

#### **Set 2: Actual Start**
| Field Name | Schema Name | Required Level | Description | Status |
|---|---|---|---|---|
| cr950_actual_start | cr950_actual_start | None | When work actually began on this apparatus (can be auto-populated by Power Automate) | 🟡 Older (underscore) |
| cr950_actualstart | cr950_ActualStart | **Recommended** | When work actually began on this apparatus | ✅ **Recommended (PascalCase)** |

#### **Set 3: Date Completed**
| Field Name | Schema Name | Required Level | Description | Status |
|---|---|---|---|---|
| cr950_date_completed | cr950_date_completed | None | When work was finished on this apparatus (auto-populated by Power Automate) | 🟡 Older (underscore) |
| cr950_datecompleted | cr950_DateCompleted | **Recommended** | (no description) | ✅ **Recommended (PascalCase)** |

---

## 💡 ANALYSIS & RECOMMENDATION

### **Pattern Identified:**

Two versions of each date field exist:
1. **Older Version**: Lowercase with underscores (e.g., `cr950_actual_start`)
   - RequiredLevel: None
   - Better descriptions (mentions Power Automate integration)
   - Appears to be from earlier development

2. **Newer Version**: PascalCase without underscores (e.g., `cr950_ActualStart`)
   - RequiredLevel: **Recommended**
   - Shorter/missing descriptions
   - Appears to be more recent creation

### **Which Fields to KEEP:**

✅ **RECOMMENDATION: Keep the PascalCase versions (cr950_AnticipatedStart, cr950_ActualStart, cr950_DateCompleted)**

**Rationale:**
1. ✅ **RequiredLevel = Recommended** (newer standard, enforces data quality)
2. ✅ **PascalCase schema names** (cr950_ActualStart) match Dataverse naming conventions
3. ✅ **Logical names match display names** (easier to reference in formulas/rollups)
4. ✅ **Likely the fields currently referenced** in existing formulas
5. ✅ **Consistent with other Dataverse entities** (standard practice)

### **Which Fields to DELETE:**

❌ **DELETE: Lowercase with underscore versions**
- cr950_actual_start (cr950_actual_start)
- cr950_anticipated_start (cr950_anticipated_start)
- cr950_date_completed (cr950_date_completed)

**Why Delete These:**
1. RequiredLevel = None (less strict, allows empty values)
2. Inconsistent naming with Dataverse standards
3. Appears to be superseded by newer fields
4. Keeping both causes confusion in formulas and rollups

---

## ⚠️ VERIFICATION REQUIRED BEFORE DELETION

### **Critical Check: Which Fields Are Referenced in Existing Formulas?**

Your solution has **30 formulas**. We need to verify which date fields they reference.

**Formula Files to Check:**
```
Solution_Exports/v1.4.0.0/Formulas/
├── cr950_apparatus-cr950_completed_hours.xaml
├── cr950_apparatus-cr950_remaining_hours.xaml
├── cr950_projects-*.xaml (8 formulas)
├── cr950_projectscope-*.xaml (8 formulas)
├── cr950_tasks-*.xaml (8 formulas)
└── cr950_scopelabordetails-*.xaml (5 formulas)
```

**What to Look For:**
- References to `cr950_actual_start` vs `cr950_actualstart`
- References to `cr950_anticipated_start` vs `cr950_anticipatedstart`
- References to `cr950_date_completed` vs `cr950_datecompleted`

---

## 📋 CLEANUP PROCEDURE

### **Step 1: Verify Formula References** (5 minutes)

Search formula files for date field references:
```powershell
# Run this command to search all formulas
Get-ChildItem "Solution_Exports\v1.4.0.0\Formulas\*.xaml" | Select-String -Pattern "actual_start|actualstart|anticipated_start|anticipatedstart|date_completed|datecompleted" | Select-Object -Unique
```

### **Step 2: Check Rollup Guide** (2 minutes)

Verify which field names are referenced in:
- `Documentation/06_Implementation_Guides/MANUAL_ROLLUP_FIELD_CREATION_GUIDE.md`

### **Step 3: Delete Unused Fields** (10 minutes)

**Via Power Apps Maker Portal:**
1. Navigate to: https://make.powerapps.com
2. Select RESAPowerPM (Dev) environment
3. Go to: Tables → Apparatus → Columns
4. For each OLD field (with underscores):
   - Click the column name
   - Select "Delete column"
   - Confirm deletion

**Fields to Delete:**
- [ ] cr950_actual_start
- [ ] cr950_anticipated_start
- [ ] cr950_date_completed

### **Step 4: Update Documentation** (15 minutes)

**Files to Update:**
1. ✅ **MANUAL_ROLLUP_FIELD_CREATION_GUIDE.md**
   - Part 1: Date Tracking Rollups
   - Ensure all references use:
     - `cr950_anticipatedstart` (NOT cr950_anticipated_start)
     - `cr950_actualstart` (NOT cr950_actual_start)
     - `cr950_datecompleted` (NOT cr950_date_completed)

2. ✅ **DATE_TRACKING_IMPLEMENTATION.md**
   - Update field specifications with correct logical names

3. ✅ **SOLUTION_v1.4.0.0_AUDIT_REPORT.md**
   - Mark duplicate field issue as RESOLVED
   - Document which fields were kept/deleted

4. ✅ **PROJECT_CONTEXT.json**
   - Add critical fact about field cleanup

### **Step 5: Re-verify** (2 minutes)

Run verification script again to confirm:
```powershell
.\Scripts\PowerShell\Verify-ApparatusDateFields.ps1
```

Should show **8 date fields** (down from 11):
- ✅ cr950_anticipatedstart
- ✅ cr950_actualstart
- ✅ cr950_datecompleted
- ✅ cr950_deletedon
- ✅ cr950_lastsyncdate
- ✅ createdon
- ✅ modifiedon
- ✅ overriddencreatedon

### **Step 6: Test Formulas** (5 minutes)

Verify existing formulas still work after field deletion:
- Open any Project/Task/Scope record
- Check that calculated fields (Total Hours, Percent Complete, etc.) still display correctly

---

## 🎯 CORRECTED FIELD NAMES FOR ROLLUP IMPLEMENTATION

### **For MANUAL_ROLLUP_FIELD_CREATION_GUIDE.md:**

**Part 1: Date Tracking Rollups**

All rollup fields should reference these **source attribute** names:

| Rollup Type | Source Attribute (Correct) | ❌ WRONG (Don't Use) |
|---|---|---|
| Earliest Anticipated Start | `cr950_anticipatedstart` | ~~cr950_anticipated_start~~ |
| Latest Anticipated Start | `cr950_anticipatedstart` | ~~cr950_anticipated_start~~ |
| Earliest Actual Start | `cr950_actualstart` | ~~cr950_actual_start~~ |
| Latest Actual Start | `cr950_actualstart` | ~~cr950_actual_start~~ |
| Earliest Completion Date | `cr950_datecompleted` | ~~cr950_date_completed~~ |
| Latest Completion Date | `cr950_datecompleted` | ~~cr950_date_completed~~ |

---

## ✅ POST-CLEANUP VERIFICATION CHECKLIST

- [ ] Formula files checked for field references
- [ ] Rollup guide checked for field name references
- [ ] 3 duplicate fields deleted via Power Apps UI
- [ ] Verification script re-run (confirms 8 fields remaining)
- [ ] Documentation updated with correct field names
- [ ] Existing formulas tested and working
- [ ] SOLUTION_v1.4.0.0_AUDIT_REPORT.md updated
- [ ] PROJECT_CONTEXT.json updated with cleanup fact
- [ ] Solution exported as v1.4.0.1 (cleanup version)

---

## 🚨 CRITICAL WARNING

**DO NOT proceed with rollup field implementation until:**
1. ✅ Duplicate fields are deleted
2. ✅ Rollup guide is updated with correct field names
3. ✅ Existing formulas are verified still working

**Risk if rollups are created with wrong field names:**
- Rollup fields will aggregate empty/null values (from unused fields)
- KPI views will show incorrect data
- Extensive rework required to fix rollup configurations

---

## 📊 IMPACT ASSESSMENT

**Tables Affected:**
- Apparatus (3 fields deleted)

**Formulas Affected:** 
- Unknown (need to verify - likely minimal/none if referencing PascalCase versions)

**Rollup Fields Blocked:**
- 18 date tracking rollups (Part 1 of guide)
- Cannot proceed until cleanup complete

**Time to Resolve:**
- Verification: 5-10 minutes
- Cleanup: 10 minutes
- Documentation Update: 15 minutes
- Testing: 5 minutes
- **Total: 35-40 minutes**

---

**Status**: ⚠️ **BLOCKER - Must resolve before v1.5.0.0**  
**Priority**: 🔴 **CRITICAL**  
**Owner**: User  
**Due**: Before rollup field implementation

**Created**: November 23, 2025  
**Next Action**: Verify formula references, then delete duplicate fields
