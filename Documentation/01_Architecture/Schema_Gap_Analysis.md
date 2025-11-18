# Schema Gap Analysis - Built vs. Checklist
**Comparing:** Current Dataverse tables vs. Build_Checklist_4_Tables.md

---

## ✅ APPARATUS TABLE - Gap Analysis

### ✅ Fields You HAVE Built
- ✅ Apparatus Designation (Text, 850 char, Required) ← NAME field
- ✅ Apparatus Number (Whole Number, Required)
- ✅ Apparatus Type (Text, 100 char, Optional)
- ✅ Apparatus Hours (Decimal, Optional)
- ✅ Project (Lookup → Projects, Required)
- ✅ Scope (Lookup → Scopes, Optional) ⚠️ **Should be Required per checklist**
- ✅ Status/Priority/Availability (Choice fields)
- ✅ Actual Hours (Decimal, Optional)

### ❌ Fields MISSING from Checklist
- ❌ **Hierarchy ID** (text, 50 chars, optional)
- ❌ **Apparatus Tag** (text, 100 chars, optional)
- ❌ **Description** (text, 500 chars, optional)
- ❌ **Date Started** (date, optional)
- ❌ **Date Completed** (date, optional)
- ❌ **Notes** (text area, 2000 chars, optional)

### ⚠️ Differences
- Apparatus Type: Built as 100 char (checklist says 200 char)
- Scope lookup: Built as Optional (checklist says Required)

---

## ✅ TASKS TABLE - Gap Analysis

### ✅ Fields You HAVE Built
- ✅ Task Name (Text, 850 char, Required) ← NAME field
- ✅ Task Number (Whole Number, Required)
- ✅ NETA Type (Text, 100 char, Required)
- ✅ Scope (Lookup → Scopes, Required)
- ✅ Project (Lookup → Projects, Required)
- ✅ Task Apparatus Hours (Decimal)
- ✅ Task Actual Hours (Decimal)
- ✅ Task Remaining Hours (Decimal)
- ✅ Task Status/Priority/Availability (Choice fields)

### ⚠️ Differences
- **Apparatus Type** field: Checklist shows this (text, 200 chars), but you have "NETA Type" instead
  - Are these the same thing or different?
- **NETA Section** field: Missing (text, 50 chars, optional)

---

## ✅ SCOPES TABLE - Gap Analysis

### ✅ Fields You HAVE Built
- ✅ Full Scope ID (Text, 850 char, Required) ← NAME field
- ✅ Scope Number (Whole Number, Required)
- ✅ Drawing Reference (Text, 100 char, Optional)
- ✅ Project (Lookup → Projects, Required)
- ✅ Total Apparatus Hours (Decimal, Required)
- ✅ Labor Rate (Currency, Required) ← Matches "Base Rate" in checklist
- ✅ Scope Status (Choice, Optional)

### ✅ Enhanced Beyond Checklist
You have MANY more rate fields than the checklist specified:
- ✅ Daily Commute Rate & Percent
- ✅ Mobilization Rate & Percent
- ✅ Onsite PM Rate & Percent
- ✅ PM Office Rate & Percent
- ✅ Onsite LOTO Rate & Percent
- ✅ Onsite Miscellaneous Rate & Percent
- ✅ Report Rate & Percent
- ✅ Fixed Costs Travel
- ✅ Fix Cost M&E
- ✅ Scope Multiplier
- ✅ Scope Adjusted Total
- ✅ Actual Hours (Decimal)
- ✅ Scope Priority & Availability (Choice)

### 🤔 Checklist Fields vs Built Fields
Your checklist mentioned these rate fields:
- Base Rate → You have "Labor Rate" ✅
- Commute Rate → You have "Daily Commute Rate" ✅
- Commute Percent → You have "Daily Commute Percent" ✅
- PM Rate → You have "Onsite PM Rate" + "PM Office Rate" ✅
- PM Percent → You have "Onsite PM Percent" + "PM Office Percent" ✅
- Daily Report Rate → You have "Report Rate" ✅
- Daily Report Percent → You have "Report Percent" ✅
- Travel Rate → **MISSING** (checklist says "currency")
- Travel Percent → **MISSING** (checklist says "decimal")
- Final Report Rate → **MISSING** (checklist says "currency")
- Final Report Percent → **MISSING** (checklist says "decimal")
- Fixed Cost Travel → You have "Fixed Costs Travel" ✅
- Fixed Cost M&E → You have "Fix Cost M&E" ✅

### ❓ Questions
1. Is "Daily Commute" the same as checklist's "Commute"?
2. Is "Report Rate" the same as "Daily Report Rate"?
3. Do you need separate "Travel" rate vs "Commute" rate?
4. Do you need "Final Report" separate from "Report"?

---

## ✅ PROJECTS TABLE - Gap Analysis

### ✅ Fields You HAVE Built
- ✅ Name (Text, 850 char, Required)
- ✅ Job Number (Text, 100 char, Required)
- ✅ Client Name (Text, 100 char, Required)
- ✅ Location (Text, 100 char, Optional)
- ✅ Lead Technician (Text, 100 char, Optional)
- ✅ Project Status (Choice, Required)
- ✅ Start Date (DateTime, Optional)
- ✅ Target Completion (DateTime, Optional)

### ⚠️ Differences
- Start Date & Target Completion: Built as DateTime (checklist says "date")
  - DateTime is better (includes time if needed)
  - This is fine ✅

### ✅ Perfect Match!
Your Projects table matches the checklist exactly!

---

## 📊 SUMMARY

| Table | Fields Match | Missing Fields | Extra Fields | Issues |
|-------|--------------|----------------|--------------|---------|
| **Projects** | ✅ 100% | 0 | 0 | None |
| **Scopes** | ✅ 90% | 3-4 (travel/final report rates) | 10+ (enhanced rate structure) | Minor naming differences |
| **Tasks** | ✅ 95% | 1 (NETA Section) | 0 | NETA Type vs Apparatus Type question |
| **Apparatus** | ⚠️ 60% | 6 (Hierarchy ID, Tag, Description, Dates, Notes) | 0 | Scope lookup not Required |

---

## 🎯 RECOMMENDED ACTIONS

### Priority 1: Critical Fixes
1. **Apparatus → Scope lookup:** Change from Optional to Required
2. **Add missing date fields to Apparatus:**
   - Date Started (date)
   - Date Completed (date)

### Priority 2: Important Additions
3. **Add text fields to Apparatus:**
   - Hierarchy ID (text, 50 chars) - For nested equipment like 1.2.1
   - Apparatus Tag (text, 100 chars) - For equipment tags like "XFMR-001"
   - Description (text, 500 chars) - Equipment description
   - Notes (text area, 2000 chars) - Field tech notes

4. **Add NETA Section to Tasks:**
   - NETA Section (text, 50 chars) - Like "7.2"

### Priority 3: Clarifications Needed
5. **Resolve Scopes rate field naming:**
   - Is "Daily Commute" different from "Commute"?
   - Do you need "Travel Rate/Percent" separate from commute?
   - Do you need "Final Report Rate/Percent" separate from daily report?

6. **Tasks: Apparatus Type vs NETA Type**
   - Checklist shows "Apparatus Type" as a field on Tasks
   - You have "NETA Type" instead
   - Are these the same? Should Tasks have BOTH?

---

## 🔄 IMPORT IMPLICATIONS

### If You Import LASNAP16 NOW:
- ❌ Can't import Date Started/Completed for apparatus (fields don't exist)
- ❌ Can't import Hierarchy ID for apparatus (field doesn't exist)
- ❌ Can't import Notes from apparatus (field doesn't exist)
- ⚠️ Scope lookup on Apparatus could be blank (shouldn't be allowed)

### Recommendation:
**Add the missing fields BEFORE importing data** so you don't have to reimport later.

---

## 💭 FIELD NAMING OBSERVATIONS

I noticed your field names are very clean and professional:
- "Apparatus Designation" (not "Name" or "ApparatusName")
- "Full Scope ID" (not just "ScopeID")
- "Task Apparatus Hours" (very clear what it is)

This is excellent! Consistent naming will help when building apps and reports.

**One minor suggestion:**
- "Fix Cost M&E" → Consider "Fixed Cost M&E" for consistency
  (You have "Fixed Costs Travel" with full word)

---

## ❓ QUESTIONS FOR YOU

1. **Should we add the 6 missing Apparatus fields now?**
   - Hierarchy ID, Apparatus Tag, Description, Date Started, Date Completed, Notes

2. **Do you want to add the missing Scopes rate fields?**
   - Travel Rate, Travel Percent, Final Report Rate, Final Report Percent

3. **Should we clarify the Tasks field?**
   - Add "Apparatus Type" as separate from "NETA Type"?
   - Or rename "NETA Type" to "Apparatus Type"?
   - Or add "NETA Section" and keep both?

4. **Do you want any calculated or rollup fields?**
   - Remaining Hours = Apparatus Hours - Actual Hours
   - Percent Complete = Actual Hours / Apparatus Hours
   - Scope: Total Actual Hours (rollup from children)

5. **Are you happy with Choice column values?**
   - Can't see the actual options from the XML export
   - Should we review what values are in Status, Priority, Availability dropdowns?

---

**What would you like to tackle first?**
