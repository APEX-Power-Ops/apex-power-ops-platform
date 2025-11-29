# 🚀 QUICK BUILD CHECKLIST - 4 Tables

**Purpose:** Step-by-step checklist for building all 4 Dataverse tables  
**Use:** Check off as you complete each step

---

## ✅ TABLE 1: PROJECTS

### Build Steps:
- [x] Navigate to make.powerapps.com
- [x] Select "RESA Power TEST" environment
- [x] Click "Tables" → "+ New table" → "Add columns and data"
- [x] Name: "Projects"
- [ ] Add columns:
  - [ ] Job Number (text, 50 chars, required)
  - [ ] Client Name (text, 100 chars, required)
  - [ ] Location (text, 200 chars, optional)
  - [ ] Lead Technician (text, 100 chars, optional)
  - [ ] Project Status (choice: Active/On Hold/Complete/Quoted, required)
  - [ ] Start Date (date, optional)
  - [ ] Target Completion (date, optional)
- [ ] Add test record:
  - [ ] Name: LASNAP16
  - [ ] Job Number: 634414
  - [ ] Client Name: LASNAP
  - [ ] Location: Las Vegas, NV
  - [ ] Lead Technician: Brandon Valdavis
  - [ ] Project Status: Active
- [ ] Save table
- [ ] Verify record appears

**Status:** Projects table complete ✅

---

## ✅ TABLE 2: SCOPES

### Build Steps:
- [ ] Tables → "+ New table" → "Add columns and data"
- [ ] Name: "Scopes"
- [ ] Add IDENTIFICATION columns:
  - [ ] Scope Number (whole number, required)
  - [ ] Full Scope ID (text, 50 chars, optional)
  - [ ] Drawing Reference (text, 100 chars, optional)
  - [ ] **Project (Lookup → Projects, required)** ⭐
- [ ] Add FINANCIAL columns:
  - [ ] Total Apparatus Hours (decimal, required)
  - [ ] Base Rate (currency, required)
  - [ ] Commute Rate (currency, optional)
  - [ ] Commute Percent (decimal, optional)
  - [ ] PM Rate (currency, optional)
  - [ ] PM Percent (decimal, optional)
  - [ ] Daily Report Rate (currency, optional)
  - [ ] Daily Report Percent (decimal, optional)
  - [ ] Travel Rate (currency, optional)
  - [ ] Travel Percent (decimal, optional)
  - [ ] Final Report Rate (currency, optional)
  - [ ] Final Report Percent (decimal, optional)
  - [ ] Fixed Cost Travel (currency, optional)
  - [ ] Fixed Cost M&E (currency, optional)
  - [ ] Scope Multiplier (decimal, optional)
- [ ] Add STATUS column:
  - [ ] Scope Status (choice: Not Started/In Progress/Complete, optional)
- [ ] Add test record:
  - [ ] Name: PPM01
  - [ ] Scope Number: 1
  - [ ] Full Scope ID: LAS16.PPM01
  - [ ] Project: LASNAP16 (lookup/select)
  - [ ] Total Apparatus Hours: 157.8
  - [ ] Base Rate: 150
  - [ ] Daily Report Rate: 125
  - [ ] Daily Report Percent: 0.043
  - [ ] Scope Status: In Progress
- [ ] Save table
- [ ] Verify record appears with Project linked

**Status:** Scopes table complete ✅

---

## ✅ TABLE 3: TASKS

### Build Steps:
- [ ] Tables → "+ New table" → "Add columns and data"
- [ ] Name: "Tasks"
- [ ] Add columns:
  - [ ] Task Number (whole number, required)
  - [ ] **Scope (Lookup → Scopes, required)** ⭐
  - [ ] **Project (Lookup → Projects, required)** ⭐
  - [ ] Apparatus Type (text, 200 chars, required)
  - [ ] NETA Section (text, 50 chars, optional)
  - [ ] Apparatus Hours (decimal, required)
- [ ] Add test record:
  - [ ] Name: Pad Mount Transformers
  - [ ] Task Number: 2
  - [ ] Scope: PPM01 (lookup/select)
  - [ ] Project: LASNAP16 (lookup/select)
  - [ ] Apparatus Type: Transformer - Pad Mount Oil
  - [ ] NETA Section: 7.2
  - [ ] Apparatus Hours: 12
- [ ] Save table
- [ ] Verify record appears with Scope and Project linked

**Status:** Tasks table complete ✅

---

## ✅ TABLE 4: APPARATUS

### Build Steps:
- [ ] Tables → "+ New table" → "Add columns and data"
- [ ] Name: "Apparatus"
- [ ] Add IDENTIFICATION columns:
  - [ ] Apparatus Number (whole number, required)
  - [ ] Hierarchy ID (text, 50 chars, optional)
  - [ ] Apparatus Tag (text, 100 chars, optional)
- [ ] Add RELATIONSHIP columns:
  - [ ] **Task (Lookup → Tasks, required)** ⭐
  - [ ] **Scope (Lookup → Scopes, required)** ⭐
  - [ ] **Project (Lookup → Projects, required)** ⭐
- [ ] Add WORK DEFINITION columns:
  - [ ] Apparatus Type (text, 200 chars, optional)
  - [ ] Apparatus Hours (decimal, required)
  - [ ] Description (text, 500 chars, optional)
- [ ] Add FIELD TECH UPDATE columns:
  - [ ] Status (choice: Not Started/In Progress/Complete, required, default: Not Started)
  - [ ] Date Started (date, optional)
  - [ ] Date Completed (date, optional)
  - [ ] Priority (choice: High/Medium/Low, optional, default: Medium)
  - [ ] Availability (choice: Ready/On Hold/Not Available, optional, default: Ready)
  - [ ] Notes (text area, 2000 chars, optional)
- [ ] Add test record:
  - [ ] Name: XFMR-001
  - [ ] Apparatus Number: 1
  - [ ] Hierarchy ID: 1.2.1
  - [ ] Apparatus Tag: XFMR-001
  - [ ] Task: Pad Mount Transformers (lookup/select)
  - [ ] Scope: PPM01 (lookup/select)
  - [ ] Project: LASNAP16 (lookup/select)
  - [ ] Apparatus Type: Transformer - Pad Mount Oil
  - [ ] Apparatus Hours: 12
  - [ ] Status: Complete
  - [ ] Date Completed: 11/7/2025
  - [ ] Priority: High
  - [ ] Availability: Ready
- [ ] Save table
- [ ] Verify record appears with all relationships linked

**Status:** Apparatus table complete ✅

---

## 🎯 VERIFICATION STEPS

After all 4 tables built:

### 1. Check Relationships
- [ ] Open Apparatus record XFMR-001
- [ ] Verify you can see/click to:
  - [ ] Task: Pad Mount Transformers
  - [ ] Scope: PPM01
  - [ ] Project: LASNAP16
- [ ] Open PPM01 scope
- [ ] Look for "Related" tab
- [ ] Verify you can see:
  - [ ] Tasks (should show "Pad Mount Transformers")
  - [ ] Apparatus (should show "XFMR-001")

### 2. Check Data Integrity
- [ ] Projects table: 1 record (LASNAP16)
- [ ] Scopes table: 1 record (PPM01)
- [ ] Tasks table: 1 record (Pad Mount Transformers)
- [ ] Apparatus table: 1 record (XFMR-001)
- [ ] All lookups working (can navigate between records)

### 3. Test in Model-Driven App
- [ ] Create Model-Driven app
- [ ] Add all 4 tables
- [ ] Publish
- [ ] Open app
- [ ] Navigate: Projects → Scopes → Tasks → Apparatus
- [ ] Verify all data shows correctly

---

## 📊 NEXT STEPS AFTER BUILD

### Immediate:
1. Take screenshots of all 4 tables with test data
2. Verify you can navigate relationships
3. Document any issues/questions

### This Week:
1. Import 27 scopes from LASNAP16 (Scope_Labor_Rates sheet)
2. Import tasks by apparatus type
3. Import 1,905 apparatus records
4. Build Model-Driven app views

### Next Week:
1. Connect Power BI to Dataverse
2. Replicate your measures
3. Test dashboard with live data
4. Build tech mobile interface

---

## 🚨 COMMON ISSUES & FIXES

### "Can't find lookup table"
- Make sure you're in correct environment (RESA Power TEST)
- Build tables in order (Projects → Scopes → Tasks → Apparatus)
- Refresh browser if table just created

### "Lookup field not saving"
- Type first few letters, wait for search results
- Select from dropdown, don't just type
- Make sure parent record exists

### "Can't see Related records"
- Relationship may need time to activate (refresh page)
- Check in Model-Driven app instead of table editor
- Verify lookup was set correctly

### "Formula fields not working"
- Power Apps doesn't support formulas in table designer
- Will need to add these in Model-Driven app or use Power Automate
- For now, skip calculated fields, focus on core structure

---

## ✅ SUCCESS CRITERIA

You'll know you're done when:
- ✅ All 4 tables created
- ✅ One test record in each table
- ✅ All relationships working (can navigate)
- ✅ Can view in Model-Driven app
- ✅ Ready to import bulk data

**Estimated Time:** 2-3 hours for all 4 tables

---

**Document Created:** November 8, 2025  
**Purpose:** Quick reference build guide  
**Use:** Check off steps as you complete them
