# Test Scenarios - Expected Trigger Behaviors

**Purpose:** Document expected system behaviors for validation  
**Owner:** VS Code Claude  
**Date:** December 5, 2025  
**Status:** Reference for Phase 2 test data validation

---

## Rollup Trigger Scenarios

### Scenario 1: Apparatus Insert → Task Rollup Update

**Trigger:** `update_task_rollups`  
**When:** INSERT into apparatus

**Test Setup:**
```sql
-- Task T1 exists with:
--   total_apparatus_count = 2
--   completed_apparatus_count = 1
--   total_apparatus_hours = 10.0

-- Insert new apparatus:
INSERT INTO apparatus (task_id, apparatus_hours, completion_status)
VALUES ('task-uuid', 4.0, 'PLANNED');
```

**Expected Result:**
```
Task T1:
  total_apparatus_count = 3        (was 2, +1)
  completed_apparatus_count = 1    (unchanged - new is PLANNED)
  total_apparatus_hours = 14.0     (was 10, +4)
```

---

### Scenario 2: Apparatus Completion → Task + Revenue Update

**Triggers:** `update_task_rollups`, `create_revenue_on_completion`  
**When:** UPDATE apparatus SET completion_status = 'COMPLETE'

**Test Setup:**
```sql
-- Apparatus A1 exists with:
--   completion_status = 'IN_PROGRESS'
--   apparatus_hours = 4.0
--   delay_hours = 0.5
--   task_id = T1
--   scope has effective_rate = $125.00

-- Update to complete:
UPDATE apparatus 
SET completion_status = 'COMPLETE', actual_end = NOW()
WHERE id = 'apparatus-uuid';
```

**Expected Results:**
```
1. Task T1:
   completed_apparatus_count += 1

2. New apparatus_revenue record:
   apparatus_id = 'apparatus-uuid'
   total_hours = 4.5              (apparatus_hours + delay_hours)
   effective_rate = 125.00        (from scope_labor_details)
   base_revenue = 500.00          (4.0 × 125)
   delay_adjustment = 62.50       (0.5 × 125)
   revenue_amount = 562.50        (base + delay)
```

---

### Scenario 3: Task Rollup → Scope Rollup Cascade

**Trigger:** `update_scope_rollups`  
**When:** Task totals change (cascaded from apparatus change)

**Test Setup:**
```sql
-- Scope S1 has Tasks T1, T2:
--   T1: apparatus_count=5, completed=3, hours=20
--   T2: apparatus_count=3, completed=2, hours=12

-- T1 gets new apparatus (from Scenario 1)
```

**Expected Result:**
```
Scope S1:
  total_apparatus_count = 9       (5+1 + 3 = 9)
  completed_apparatus_count = 5   (3 + 2 = 5)
  total_task_hours = 36.0         (24 + 12 = 36)
  percent_complete = 55.56%       (5/9 × 100)
```

---

### Scenario 4: Scope Rollup → Project Rollup Cascade

**Trigger:** `update_project_rollups`  
**When:** Scope totals change (cascaded from task change)

**Test Setup:**
```sql
-- Project P1 has Scopes S1, S2:
--   S1: apparatus_count=9, completed=5
--   S2: apparatus_count=6, completed=6

-- S1 changes (from Scenario 3)
```

**Expected Result:**
```
Project P1:
  total_apparatus_count = 15      (9 + 6 = 15)
  completed_apparatus_count = 11  (5 + 6 = 11)
  percent_complete = 73.33%       (11/15 × 100)
```

---

## Financial Trigger Scenarios

### Scenario 5: Revenue Recognition → Scope Financial Summary

**Trigger:** `update_scope_financial_summary`  
**When:** INSERT into apparatus_revenue

**Test Setup:**
```sql
-- Scope S1 financial summary:
--   total_revenue_recognized = 5000.00
--   total_revenue_pending = 2000.00

-- New revenue from Scenario 2: 562.50
```

**Expected Result:**
```
scope_financial_summaries for S1:
  total_revenue_recognized = 5562.50    (+562.50)
  total_revenue_pending = recalculated  (remaining apparatus × rate)
```

---

### Scenario 6: Scope Financial → Project Financial Cascade

**Trigger:** `update_project_financial_summary`  
**When:** Scope financial summary changes

**Test Setup:**
```sql
-- Project P1 has Scopes S1, S2:
--   S1: revenue_recognized=5562.50
--   S2: revenue_recognized=3000.00

-- S1 changed (from Scenario 5)
```

**Expected Result:**
```
project_financial_summaries for P1:
  total_revenue_recognized = 8562.50    (5562.50 + 3000)
```

---

## Status Transition Scenarios

### Scenario 7: Project Status Auto-Update

**Trigger:** `update_project_status` (or business rule)  
**When:** All apparatus complete

**Test Setup:**
```sql
-- Project P1:
--   total_apparatus_count = 10
--   completed_apparatus_count = 9
--   status = 'IN_PROGRESS'

-- Last apparatus completes
UPDATE apparatus SET completion_status = 'COMPLETE' WHERE ...;
```

**Expected Result:**
```
Project P1:
  completed_apparatus_count = 10
  percent_complete = 100.00%
  status = 'COMPLETED' (if auto-transition enabled)
  -- OR remains 'IN_PROGRESS' for manual approval
```

---

## PSS Portal Scenarios

### Scenario 8: PSS Activity Log Auto-Creation

**Trigger:** `log_pss_activity`  
**When:** Status changes on pss_studies

**Test Setup:**
```sql
-- PSS Study exists with status = 'IN_PROGRESS'

UPDATE pss_studies 
SET status = 'REVIEW', updated_at = NOW()
WHERE id = 'study-uuid';
```

**Expected Result:**
```
New pss_activity_log record:
  study_id = 'study-uuid'
  activity_type = 'STATUS_CHANGE'
  old_value = 'IN_PROGRESS'
  new_value = 'REVIEW'
  created_at = NOW()
  created_by = current user
```

---

### Scenario 9: PSS Document Status Rollup

**Trigger:** `update_study_document_status`  
**When:** Document status changes

**Test Setup:**
```sql
-- PSS Study S1 has 5 documents:
--   3 APPROVED, 2 PENDING

-- One PENDING document approved
UPDATE pss_documents SET status = 'APPROVED' WHERE ...;
```

**Expected Result:**
```
PSS Study S1:
  documents_approved = 4
  documents_pending = 1
  document_completion_percent = 80%
```

---

## Edge Case Scenarios

### Scenario 10: Delete Apparatus → Rollup Recalculation

**Trigger:** `update_task_rollups` (on DELETE)  
**When:** DELETE from apparatus

**Test Setup:**
```sql
-- Task T1 with 5 apparatus, delete one

DELETE FROM apparatus WHERE id = 'apparatus-uuid';
```

**Expected Result:**
```
Task T1:
  total_apparatus_count = 4       (was 5, -1)
  total_apparatus_hours adjusted
  Cascade to scope and project rollups
```

---

### Scenario 11: Null Foreign Key Handling

**Test:** Apparatus without scope_labor_details rate

**Test Setup:**
```sql
-- Apparatus completes but scope has no labor rate configured

UPDATE apparatus SET completion_status = 'COMPLETE' WHERE ...;
```

**Expected Behavior:**
```
Option A: Use default rate of $0.00, log warning
Option B: Prevent completion, require rate setup
Option C: Create revenue record with NULL amounts, flag for review

Decision: [Pending - need Desktop Claude input]
```

---

### Scenario 12: Concurrent Updates

**Test:** Multiple apparatus complete simultaneously

**Expected Behavior:**
```
All rollups should be accurate regardless of order
No race conditions in financial calculations
Transaction isolation prevents double-counting
```

---

## Validation Queries

### Verify Rollup Accuracy
```sql
-- Compare calculated vs stored values
SELECT 
    t.id,
    t.total_apparatus_count as stored,
    COUNT(a.id) as calculated,
    t.total_apparatus_count = COUNT(a.id) as matches
FROM tasks t
LEFT JOIN apparatus a ON a.task_id = t.id
GROUP BY t.id;
```

### Verify Financial Accuracy
```sql
-- Compare revenue recognized vs apparatus_revenue sum
SELECT 
    sfs.scope_id,
    sfs.total_revenue_recognized as stored,
    COALESCE(SUM(ar.revenue_amount), 0) as calculated,
    sfs.total_revenue_recognized = COALESCE(SUM(ar.revenue_amount), 0) as matches
FROM scope_financial_summaries sfs
LEFT JOIN scopes s ON s.id = sfs.scope_id
LEFT JOIN tasks t ON t.scope_id = s.id
LEFT JOIN apparatus a ON a.task_id = t.id
LEFT JOIN apparatus_revenue ar ON ar.apparatus_id = a.id
GROUP BY sfs.scope_id, sfs.total_revenue_recognized;
```

---

## Test Data Requirements

| Scenario | Minimum Records Needed |
|----------|----------------------|
| 1-4 | 1 project, 2 scopes, 4 tasks, 10 apparatus |
| 5-6 | + scope_labor_details, financial summaries |
| 7 | + various completion states |
| 8-9 | + 2 PSS studies, 10 documents |
| 10-12 | Edge case variations |

**Total:** LASNAP16 test data should cover all scenarios

---

*Test scenarios for trigger validation | VS Code Claude | December 5, 2025*
