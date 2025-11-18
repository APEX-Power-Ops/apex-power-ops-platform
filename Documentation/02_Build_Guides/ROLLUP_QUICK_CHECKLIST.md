# ROLLUP FIELDS - QUICK CHECKLIST
## Print and Check Off As You Build

**Date:** November 14, 2025  
**Total:** 21 rollup fields

---

## 🎯 CRITICAL REMINDERS

**Related Entity Changes:**
- Tasks: `Apparatus (Task)`
- Project Scope: `Apparatus (Scope)`
- Projects: `Apparatus (Project)`

**Data Types:**
- SUM rollups → Decimal
- COUNT rollups → Whole Number

---

## ✅ TASKS TABLE (7 fields)

**Navigate:** Tasks → Columns → + New column

- [ ] **Total_Apparatus_Hours**
  - Decimal → Rollup | Related: Apparatus (Task) | SUM Labor_Hours

- [ ] **Total_Completed_Hours**
  - Decimal → Rollup | Related: Apparatus (Task) | SUM Completed_Hours

- [ ] **Total_Remaining_Hours**
  - Decimal → Rollup | Related: Apparatus (Task) | SUM Remaining_Hours

- [ ] **Total_Actual_Hours**
  - Decimal → Rollup | Related: Apparatus (Task) | SUM Actual_Hours

- [ ] **Total_Delays**
  - Decimal → Rollup | Related: Apparatus (Task) | SUM Delays

- [ ] **Total_Apparatus_Count**
  - Whole Number → Rollup | Related: Apparatus (Task) | COUNT Primary Key

- [ ] **Completed_Apparatus_Count**
  - Whole Number → Rollup | Related: Apparatus (Task) | COUNT Primary Key
  - ⚠️ TWO FILTERS: Task contains data + Status = Complete

---

## ✅ PROJECT SCOPE TABLE (7 fields)

**Navigate:** Project Scope → Columns → + New column

**⚠️ Related Entity = Apparatus (Scope) for ALL fields below!**

- [ ] **Total_Apparatus_Hours**
  - Decimal → Rollup | Related: Apparatus (Scope) | SUM Labor_Hours

- [ ] **Total_Completed_Hours**
  - Decimal → Rollup | Related: Apparatus (Scope) | SUM Completed_Hours

- [ ] **Total_Remaining_Hours**
  - Decimal → Rollup | Related: Apparatus (Scope) | SUM Remaining_Hours

- [ ] **Total_Actual_Hours**
  - Decimal → Rollup | Related: Apparatus (Scope) | SUM Actual_Hours

- [ ] **Total_Delays**
  - Decimal → Rollup | Related: Apparatus (Scope) | SUM Delays

- [ ] **Total_Apparatus_Count**
  - Whole Number → Rollup | Related: Apparatus (Scope) | COUNT Primary Key

- [ ] **Completed_Apparatus_Count**
  - Whole Number → Rollup | Related: Apparatus (Scope) | COUNT Primary Key
  - ⚠️ TWO FILTERS: Scope contains data + Status = Complete

---

## ✅ PROJECTS TABLE (7 fields)

**Navigate:** Projects → Columns → + New column

**⚠️ Related Entity = Apparatus (Project) for ALL fields below!**

- [ ] **Total_Apparatus_Hours**
  - Decimal → Rollup | Related: Apparatus (Project) | SUM Labor_Hours

- [ ] **Total_Completed_Hours**
  - Decimal → Rollup | Related: Apparatus (Project) | SUM Completed_Hours

- [ ] **Total_Remaining_Hours**
  - Decimal → Rollup | Related: Apparatus (Project) | SUM Remaining_Hours

- [ ] **Total_Actual_Hours**
  - Decimal → Rollup | Related: Apparatus (Project) | SUM Actual_Hours

- [ ] **Total_Delays**
  - Decimal → Rollup | Related: Apparatus (Project) | SUM Delays

- [ ] **Total_Apparatus_Count**
  - Whole Number → Rollup | Related: Apparatus (Project) | COUNT Primary Key

- [ ] **Completed_Apparatus_Count**
  - Whole Number → Rollup | Related: Apparatus (Project) | COUNT Primary Key
  - ⚠️ TWO FILTERS: Project contains data + Status = Complete

---

## 🚀 AFTER ALL 21 ROLLUPS

- [ ] Review all field names for consistency
- [ ] Click "Publish all customizations"
- [ ] Wait for publish to complete
- [ ] Proceed to calculated fields

---

**Progress Tracker:**

Tasks: ___/7 complete  
Project Scope: ___/7 complete  
Projects: ___/7 complete  

**Total: ___/21 complete**

---

**Estimated Time:** 45-60 minutes for all 21 fields
