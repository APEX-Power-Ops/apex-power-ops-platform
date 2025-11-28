# Revenue Recognition Power Automate Flow

**Version:** 1.5.0.1  
**Last Updated:** November 28, 2025  
**Original Created:** November 16, 2025  
**Status:** ✅ PRODUCTION - Flow tested and verified working  
**Flow Last Modified:** November 27, 2025  
**Last Test:** November 27, 2025 - PASSED ✅

---

## 📋 Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.3.0.2 | Nov 16, 2025 | Initial specification |
| 1.3.0.3 | Nov 17, 2025 | Debugging fixes: concat() for OData bindings |
| 1.5.0.0 | Nov 27, 2025 | Added Revenue Recognition Date field, documented fixes |
| 1.5.0.1 | Nov 28, 2025 | **CORRECTED** empty() condition fix - verified working |

---

## 🎯 Overview

**Goal:** Automate revenue recognition when field techs mark apparatus complete. Single flow handles date stamping, revenue record creation, and financial tracking.

**Business Value:**
- ✅ Eliminates manual revenue entry errors
- ✅ Ensures Date Completed accuracy for billing periods
- ✅ Instant revenue visibility when work completes
- ✅ Audit trail with separate operational and financial timestamps
- ✅ Finance can override if corrections needed

### Architecture

```
Field Tech Action:
  └─→ Sets Apparatus.Completion_Status = "Complete" (value = 2)
       │
Power Automate Flow Triggers:
  ├─→ Step 1: Check if Date_Completed is empty (using empty() function)
  │   └─→ If empty: Set Date_Completed = utcNow()
  ├─→ Step 2: Get related Scope record
  ├─→ Step 3: List ScopeLaborDetail for this Scope
  ├─→ Step 4: Check ScopeLaborDetail exists (terminate if not)
  ├─→ Step 5: List existing ApparatusRevenue (duplicate prevention)
  └─→ Step 6: If no existing revenue, create ApparatusRevenue:
       ├─→ Apparatus lookup (OData bind format)
       ├─→ Project lookup (OData bind format)
       ├─→ ScopeLaborDetail lookup (OData bind format)
       ├─→ Apparatus_Hours = Completed_Hours
       ├─→ Delays = Delays
       ├─→ Effective_Labor_Rate = from ScopeLaborDetail
       ├─→ Revenue_Status = RECOGNIZED (2)
       └─→ Revenue_Recognition_Date = utcNow()
```

---

## ⚠️ CRITICAL FIXES (Verified Working)

These fixes have been tested and verified. **DO NOT revert these patterns.**

### Fix 1: Null Checking with empty() - CORRECTED Nov 27, 2025

**Problem:** Date_Completed never populated. Flow failed with "InvalidTemplate" error:
> "The template language function 'contains' expects its first argument 'collection' to be a dictionary (object), an array or a string. The provided value is of type 'Null'."

**Root Cause:** The `contains()` function cannot operate on null values. When `cr950_datecompleted` is null, `contains(null, ...)` throws an error.

**❌ WRONG - contains() fails on null:**
```
contains(triggerOutputs()?['body/cr950_datecompleted'], null)
```

**✅ CORRECT - empty() handles null properly:**
```
empty(triggerOutputs()?['body/cr950_datecompleted']) is equal to true
```

**In Power Automate UI:**
1. Set condition operator to **"is equal to"**
2. Left side - click **Expression** tab and enter:
   ```
   empty(triggerOutputs()?['body/cr950_datecompleted'])
   ```
3. Right side: `true`

**Tested & Verified:** November 27, 2025 ✅

---

### Fix 2: OData Binding Format for Lookups

**Problem:** Flow failed with "URL was not parsed due to ODataUriParser error".

**Root Cause:** Lookup fields used plain GUID format instead of OData binding format.

**Solution:** Use `concat()` to build proper OData binding:

```json
// ❌ WRONG - Plain GUID
"item/cr950_Apparatus": "@triggerOutputs()?['body/cr950_apparatusid']"

// ✅ CORRECT - OData bind format with concat()
"item/cr950_Apparatus@odata.bind": "@concat('cr950_apparatuses(',triggerOutputs()?['body/cr950_apparatusid'],')')"
```

**Entity Set Names (Dataverse Pluralization):**
| Table | Entity Set Name |
|-------|-----------------|
| cr950_apparatus | cr950_apparatuses |
| cr950_projects | cr950_projectses |
| cr950_scopelabordetails | cr950_scopelabordetailses |
| cr950_apparatusrevenue | cr950_apparatusrevenues |

---

### Fix 3: Calculated Field Data Dependencies

**Problem:** "Cannot recognize revenue: No labor rates defined" even when ScopeLaborDetail existed.

**Root Cause:** Effective_Labor_Rate = $0 because source fields were null.

**Solution:** Ensure ScopeLaborDetail has populated financial data:
- Total_Apparatus_Hours > 0
- At least one of: Onsite_Labor_Total, Offsite_Labor_Total, Travel_Total, Outside_Services_Total

---

## 🆕 Enhancement: Revenue Recognition Date (v1.5.0.0)

**Field:** `cr950_revenuerecognitiondate` on ApparatusRevenue table

**Purpose:** Separate operational completion from financial recognition.

- **Date_Completed** = When field tech marked work done (on Apparatus)
- **Revenue_Recognition_Date** = When system recognized revenue (on ApparatusRevenue)

**Implementation:**
```json
"item/cr950_revenuerecognitiondate": "@utcNow()"
```

---

## 🧪 Test Results - November 27, 2025

**Test Apparatus:** Switchgear - Medium Voltage (877a924f-c3cb-f011-bbd2-6045bd0391a9)

| Field | Result |
|-------|--------|
| Date Completed | 2025-11-28T04:17:47Z ✅ |
| Revenue Created | Yes ✅ |
| Apparatus Hours | 2.5 |
| Effective Rate | $347.85/hr |
| Revenue Amount | $869.63 ✅ |
| Revenue Status | RECOGNIZED (2) ✅ |
| Recognition Date | 2025-11-28T04:17:49Z ✅ |

**Calculation Verified:** 2.5 hrs × $347.85 = $869.63 ✅

---

## 📐 Flow Definition

### Trigger Configuration

| Parameter | Value | Purpose |
|-----------|-------|---------|
| message | 3 | Modified rows only |
| entityname | cr950_apparatus | Apparatus table |
| filteringattributes | cr950_completion_status | Only trigger on this field |
| filterexpression | cr950_completion_status eq 2 | Only when Complete |

---

## ❌ Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| "InvalidTemplate - contains expects collection" | Using contains() on null value | Change to `empty(...) is equal to true` |
| "No labor rates defined" | ScopeLaborDetail missing or $0 rate | Create ScopeLaborDetail with financial data |
| "ODataUriParser error" | Plain GUID in lookup | Use concat() OData bind format |
| Flow doesn't trigger | Status not = 2 | Verify choice value |

---

## ✅ Pre-Deployment Checklist

- [x] ScopeLaborDetail exists for all active Scopes
- [x] Effective_Labor_Rate > $0 for all ScopeLaborDetails
- [x] Condition uses `empty()` not `contains()` for null check
- [x] Lookup fields use OData bind format with concat()
- [x] Test apparatus completion in dev environment
- [x] Verify ApparatusRevenue record created correctly
- [x] Check Revenue_Recognition_Date populated
- [x] Confirm no duplicate records on re-completion

---

## 📁 File Locations

| Item | Location |
|------|----------|
| This Spec | `Documentation/02_Implementation/REVENUE_RECOGNITION_FLOW_SPEC.md` |
| Flow JSON | `Solution_Exports/v1.5.0.0_extracted/Workflows/RevenueRecognitiononApparatusCompletion-*.json` |
| Nov 17 Debug Session | `Documentation/03_Progress_Tracking/SESSION_SUMMARY_NOV17_REVENUE_RECOGNITION_COMPLETION.md` |

---

**Document Owner:** Jason Swenson  
**Last Verified:** November 27, 2025 - All tests passed ✅
