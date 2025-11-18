# ARCHITECTURE CLEANUP GUIDE - v1.2.0.3

**Date**: November 15, 2025  
**Purpose**: Remove unused elements from v1.2.0.3 solution based on data verification findings  
**Environment**: RESAPower_PM (org04ad071f.crm.dynamics.com)  
**Time Estimate**: 15-20 minutes

---

## 🎯 CLEANUP OBJECTIVES

Based on data verification (all tables empty), we can safely remove unused architectural elements:

1. ❌ **BusinessUnit Entity** - Never used, undocumented (5 min)
2. ❌ **Projects.Location Field** - Lookup to BusinessUnit (2 min)
3. ❌ **3 Unused Option Sets** - No fields using them (8 min)

**Total Elements to Remove**: 1 entity + 1 field + 3 option sets = 5 items

---

## 📋 STEP-BY-STEP CLEANUP INSTRUCTIONS

### **STEP 1: Remove BusinessUnit Entity** (5 minutes)

**Why**: Undocumented entity, never populated, no fields reference it (after we remove Location field)

**Navigation**:
1. Open Power Apps (make.powerapps.com)
2. Select **RESAPower_PM** environment
3. Go to **Solutions** → **RESA Power Project Tracker** (or your solution name)
4. Navigate to **Tables**
5. Find **cr950_businessunit** (BusinessUnit)

**Actions**:
1. ✅ **Verify no dependencies** (should only show Projects.Location - we'll remove that first)
2. ✅ **Remove from solution**:
   - Click on BusinessUnit table
   - Click **"Remove from this solution"** (⋯ menu)
3. ✅ **Delete the table** (optional - can also just remove from solution):
   - If you want to permanently delete: Go to **Tables** → **All** → Find BusinessUnit
   - Click **Delete** (only if no other solutions reference it)

**Verification**:
- [ ] BusinessUnit no longer appears in solution
- [ ] No errors or warnings

---

### **STEP 2: Remove Projects.Location Field** (2 minutes)

**Why**: Lookup to BusinessUnit entity (which we're removing)

**Navigation**:
1. In solution, go to **Tables** → **cr950_projects** (Projects)
2. Click **Columns** tab
3. Find **cr950_location** field

**Actions**:
1. ✅ **Verify field is empty** (should be - we verified Projects table empty)
2. ✅ **Remove column**:
   - Select **cr950_location** column
   - Click **Delete** (⋯ menu)
   - Confirm deletion

**Verification**:
- [ ] Location field no longer in Projects table
- [ ] No form references to Location field (we'll verify in Phase 3)

---

### **STEP 3: Remove Unused Option Sets** (8 minutes)

**Why**: 3 option sets defined but no fields use them

#### **3A: Remove cr950_scopestatus** (2-3 min)

**Details**:
- Option Set: cr950_scopestatus
- Values: Not Started (0), In Progress (1), Completed (2), On Hold (3)
- **Issue**: ProjectScope has no "Scope_Status" field using this
- **Alternative**: ProjectScope uses Percent_Complete (calculated) instead

**Navigation**:
1. In solution, go to **Choices** (or **Option Sets**)
2. Find **cr950_scopestatus**

**Actions**:
1. ✅ **Verify no fields use it**:
   - Click on the option set
   - Check **"Where it's used"** - should be empty
2. ✅ **Delete option set**:
   - Click **Delete**
   - Confirm deletion

**Verification**:
- [ ] cr950_scopestatus removed
- [ ] No errors

---

#### **3B: Remove cr950_availability** (2-3 min)

**Details**:
- Option Set: cr950_availability
- Values: Available (0), In Use (1), Out of Service (2), Reserved (3)
- **Issue**: No entity has an "Availability" field

**Navigation**:
1. In solution, go to **Choices**
2. Find **cr950_availability**

**Actions**:
1. ✅ **Verify no fields use it**
2. ✅ **Delete option set**

**Verification**:
- [ ] cr950_availability removed
- [ ] No errors

---

#### **3C: Remove cr950_priority** (2-3 min)

**Details**:
- Option Set: cr950_priority
- Values: Low (0), Medium (1), High (2), Urgent (3)
- **Issue**: Neither Tasks nor Apparatus has a "Priority" field

**Navigation**:
1. In solution, go to **Choices**
2. Find **cr950_priority**

**Actions**:
1. ✅ **Verify no fields use it**:
   - Check **"Where it's used"** - should be empty
2. ✅ **Delete option set**:
   - Click **Delete**
   - Confirm deletion

**Verification**:
- [ ] cr950_priority removed
- [ ] No errors

---

## 🔄 ALTERNATIVE: If You Want to KEEP Option Sets

**Scenario**: "I might want Priority/Availability/ScopeStatus later"

**Option**: Leave them in solution but document as "reserved for future use"

**Trade-off**:
- ✅ **Pro**: Available if needed later
- ❌ **Con**: Clutters choice list, adds confusion
- ❌ **Con**: Not following "you aren't gonna need it" (YAGNI) principle

**Recommendation**: **Remove now, add back later if needed** (5 min to recreate)

---

## 📊 CLEANUP CHECKLIST

### **Pre-Cleanup Verification**

- [x] Data verification complete (all tables empty)
- [x] Backup solution exported (v1.2.0.3 zip in version control)
- [ ] Logged into Power Apps (make.powerapps.com)
- [ ] RESAPower_PM environment selected
- [ ] Solution opened (RESA Power Project Tracker)

### **Cleanup Tasks**

- [ ] **Remove Projects.Location field** (2 min)
- [ ] **Remove BusinessUnit entity** (5 min)
- [ ] **Remove cr950_scopestatus option set** (2 min)
- [ ] **Remove cr950_availability option set** (2 min)
- [ ] **Remove cr950_priority option set** (2 min)

### **Post-Cleanup Verification**

- [ ] No errors in solution checker
- [ ] All remaining entities load correctly
- [ ] Forms still display properly (quick check)
- [ ] Export updated solution as v1.2.0.4 (or v1.3.0.0)

---

## 🚨 TROUBLESHOOTING

### **Issue: "Cannot delete - dependencies exist"**

**Solution**:
1. Click **"Show dependencies"**
2. Remove dependencies first (likely form controls)
3. Then delete the element

### **Issue: "BusinessUnit has relationships"**

**Solution**:
1. Remove Projects.Location field FIRST
2. Then remove BusinessUnit entity

### **Issue: "Option set is in use"**

**Solution**:
1. Check if any fields actually use it
2. If found, assess if field is needed
3. If not needed, remove field first
4. Then remove option set

---

## 📝 DOCUMENTATION UPDATES

After cleanup, update:

1. ✅ **V1_2_0_3_COMPLETE_FIELD_CATALOG.md**:
   - Remove BusinessUnit section
   - Remove Projects.Location from Projects entity
   - Update field counts: Projects (19 → 18)

2. ✅ **CHOICE_FIELDS_OPTIONSETS.md**:
   - Remove cr950_scopestatus section
   - Remove cr950_availability section
   - Remove cr950_priority section
   - Update option set count: 8 → 5

3. ✅ **GAP_ANALYSIS_FINAL_REPORT.md**:
   - Mark cleanup items as COMPLETED
   - Update "Cleanup Opportunities" section

4. ✅ **customizations.xml** (in next solution export):
   - BusinessUnit entity removed
   - Location field removed
   - 3 option sets removed

---

## 🎯 SUCCESS CRITERIA

**Cleanup Complete When**:

✅ **All 5 elements removed**:
- BusinessUnit entity ✓
- Projects.Location field ✓
- cr950_scopestatus option set ✓
- cr950_availability option set ✓
- cr950_priority option set ✓

✅ **No errors**:
- Solution checker shows no issues
- All forms load correctly
- All views load correctly

✅ **Solution exported**:
- New version number assigned (v1.2.0.4 or v1.3.0.0)
- Exported as managed + unmanaged
- Saved to version control

---

## 🔄 ROLLBACK PLAN

**If Something Goes Wrong**:

1. **Immediate Rollback**:
   - Go to **Solutions** → **History**
   - Restore previous version (v1.2.0.3)

2. **Re-import from Backup**:
   - Import v1.2.0.3 solution zip
   - Select **Upgrade** option
   - Restores all removed elements

3. **Manual Restore**:
   - Recreate option sets from CHOICE_FIELDS_OPTIONSETS.md
   - Recreate BusinessUnit entity (5 fields documented)
   - Recreate Location field on Projects

---

## 📋 NEXT STEPS AFTER CLEANUP

1. **Export cleaned solution**:
   - Version: v1.2.0.4 (or v1.3.0.0 if breaking change)
   - Both managed and unmanaged
   - Save to Git repository

2. **Update documentation**:
   - Field catalog (remove BusinessUnit, update counts)
   - Choice fields doc (remove 3 option sets)
   - Gap analysis (mark cleanup complete)

3. **Proceed to Phase 2d**:
   - Complete ApparatusRevenue automation
   - Add 5 calculation fields
   - Build Power Automate flow

---

## ⏱️ TIME TRACKING

| Task | Estimated | Actual |
|------|-----------|--------|
| Remove Projects.Location | 2 min | ___ min |
| Remove BusinessUnit | 5 min | ___ min |
| Remove cr950_scopestatus | 2 min | ___ min |
| Remove cr950_availability | 2 min | ___ min |
| Remove cr950_priority | 2 min | ___ min |
| Export solution | 3 min | ___ min |
| Update docs | 4 min | ___ min |
| **TOTAL** | **20 min** | **___ min** |

---

## 🏁 COMPLETION SIGN-OFF

**Cleanup Completed By**: ________________  
**Date**: ________________  
**Time**: ________________  

**Verification**:
- [ ] All 5 elements removed
- [ ] No solution errors
- [ ] Solution exported (v1.2.0.4)
- [ ] Documentation updated
- [ ] Ready for Phase 2d

**Notes**:
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________

---

**STATUS**: Ready to execute  
**NEXT**: After cleanup → Phase 2d (Revenue Automation)
