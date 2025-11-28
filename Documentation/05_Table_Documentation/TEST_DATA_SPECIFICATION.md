# EXACT TEST DATA SPECIFICATION
## For Rollup Field Validation - November 24, 2025

**Purpose:** Precise data specification for creating test hierarchy  
**Use:** VS Code Claude OR Manual Power Apps entry  
**Goal:** Validate 18 date tracking rollup fields

---

## 🎯 COMPLETE DATA HIERARCHY

### **STEP 1: Client**
```json
{
  "entityName": "cr950_client",
  "data": {
    "cr950_name": "Test Hospital",
    "cr950_accountnumber": "TEST-2025-001"
  }
}
```
**Save as:** `clientId`

---

### **STEP 2: Site**
```json
{
  "entityName": "cr950_site",
  "data": {
    "cr950_name": "Main Campus Test",
    "cr950_address": "123 Test Street",
    "cr950_city": "Phoenix",
    "cr950_state": "AZ",
    "cr950_zipcode": "85001",
    "cr950_client@odata.bind": "/cr950_clients({clientId})"
  }
}
```
**Save as:** `siteId`

---

### **STEP 3: Project**
```json
{
  "entityName": "cr950_projects",
  "data": {
    "cr950_name": "Test Switchgear Project",
    "cr950_projectnumber": "PHX-TEST-001",
    "cr950_description": "Test data for rollup validation",
    "cr950_client@odata.bind": "/cr950_clients({clientId})",
    "cr950_site@odata.bind": "/cr950_sites({siteId})"
  }
}
```
**Save as:** `projectId`

---

### **STEP 4: Scope**
```json
{
  "entityName": "cr950_projectscope",
  "data": {
    "cr950_name": "Main Distribution",
    "cr950_scopenumber": "S01",
    "cr950_description": "Test scope for rollup validation",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})"
  }
}
```
**Save as:** `scopeId`

---

### **STEP 5: Tasks (3 records)**

#### **Task 1: Building A**
```json
{
  "entityName": "cr950_tasks",
  "data": {
    "cr950_name": "Switchgear Building A",
    "cr950_tasknumber": "T01",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})",
    "cr950_projectscope@odata.bind": "/cr950_projectscopes({scopeId})"
  }
}
```
**Save as:** `task1Id`

#### **Task 2: Building B**
```json
{
  "entityName": "cr950_tasks",
  "data": {
    "cr950_name": "Switchgear Building B",
    "cr950_tasknumber": "T02",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})",
    "cr950_projectscope@odata.bind": "/cr950_projectscopes({scopeId})"
  }
}
```
**Save as:** `task2Id`

#### **Task 3: Building C**
```json
{
  "entityName": "cr950_tasks",
  "data": {
    "cr950_name": "Switchgear Building C",
    "cr950_tasknumber": "T03",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})",
    "cr950_projectscope@odata.bind": "/cr950_projectscopes({scopeId})"
  }
}
```
**Save as:** `task3Id`

---

### **STEP 6: Apparatus (9 records with staggered dates)**

#### **Task 1 - Apparatus 1 (COMPLETE)**
```json
{
  "entityName": "cr950_apparatus",
  "data": {
    "cr950_name": "Breaker 1A",
    "cr950_apparatusnumber": "BRK-1A",
    "cr950_anticipatedstartdate": "2025-12-01",
    "cr950_actualstartdate": "2025-12-02",
    "cr950_datecompleted": "2025-12-05",
    "cr950_apparatushours": 8.5,
    "cr950_task@odata.bind": "/cr950_taskses({task1Id})",
    "cr950_projectscope@odata.bind": "/cr950_projectscopes({scopeId})",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})"
  }
}
```

#### **Task 1 - Apparatus 2 (COMPLETE)**
```json
{
  "entityName": "cr950_apparatus",
  "data": {
    "cr950_name": "Breaker 1B",
    "cr950_apparatusnumber": "BRK-1B",
    "cr950_anticipatedstartdate": "2025-12-02",
    "cr950_actualstartdate": "2025-12-03",
    "cr950_datecompleted": "2025-12-06",
    "cr950_apparatushours": 8.5,
    "cr950_task@odata.bind": "/cr950_taskses({task1Id})",
    "cr950_projectscope@odata.bind": "/cr950_projectscopes({scopeId})",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})"
  }
}
```

#### **Task 1 - Apparatus 3 (IN PROGRESS)**
```json
{
  "entityName": "cr950_apparatus",
  "data": {
    "cr950_name": "Breaker 1C",
    "cr950_apparatusnumber": "BRK-1C",
    "cr950_anticipatedstartdate": "2025-12-03",
    "cr950_actualstartdate": "2025-12-04",
    "cr950_apparatushours": 8.5,
    "cr950_task@odata.bind": "/cr950_taskses({task1Id})",
    "cr950_projectscope@odata.bind": "/cr950_projectscopes({scopeId})",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})"
  }
}
```
*Note: No cr950_datecompleted - still in progress*

#### **Task 2 - Apparatus 4 (COMPLETE)**
```json
{
  "entityName": "cr950_apparatus",
  "data": {
    "cr950_name": "Breaker 2A",
    "cr950_apparatusnumber": "BRK-2A",
    "cr950_anticipatedstartdate": "2025-12-04",
    "cr950_actualstartdate": "2025-12-05",
    "cr950_datecompleted": "2025-12-07",
    "cr950_apparatushours": 8.5,
    "cr950_task@odata.bind": "/cr950_taskses({task2Id})",
    "cr950_projectscope@odata.bind": "/cr950_projectscopes({scopeId})",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})"
  }
}
```

#### **Task 2 - Apparatus 5 (COMPLETE)**
```json
{
  "entityName": "cr950_apparatus",
  "data": {
    "cr950_name": "Breaker 2B",
    "cr950_apparatusnumber": "BRK-2B",
    "cr950_anticipatedstartdate": "2025-12-05",
    "cr950_actualstartdate": "2025-12-06",
    "cr950_datecompleted": "2025-12-08",
    "cr950_apparatushours": 8.5,
    "cr950_task@odata.bind": "/cr950_taskses({task2Id})",
    "cr950_projectscope@odata.bind": "/cr950_projectscopes({scopeId})",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})"
  }
}
```

#### **Task 2 - Apparatus 6 (IN PROGRESS)**
```json
{
  "entityName": "cr950_apparatus",
  "data": {
    "cr950_name": "Breaker 2C",
    "cr950_apparatusnumber": "BRK-2C",
    "cr950_anticipatedstartdate": "2025-12-06",
    "cr950_actualstartdate": "2025-12-07",
    "cr950_apparatushours": 8.5,
    "cr950_task@odata.bind": "/cr950_taskses({task2Id})",
    "cr950_projectscope@odata.bind": "/cr950_projectscopes({scopeId})",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})"
  }
}
```
*Note: No cr950_datecompleted - still in progress*

#### **Task 3 - Apparatus 7 (COMPLETE)**
```json
{
  "entityName": "cr950_apparatus",
  "data": {
    "cr950_name": "Breaker 3A",
    "cr950_apparatusnumber": "BRK-3A",
    "cr950_anticipatedstartdate": "2025-12-07",
    "cr950_actualstartdate": "2025-12-08",
    "cr950_datecompleted": "2025-12-09",
    "cr950_apparatushours": 8.5,
    "cr950_task@odata.bind": "/cr950_taskses({task3Id})",
    "cr950_projectscope@odata.bind": "/cr950_projectscopes({scopeId})",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})"
  }
}
```

#### **Task 3 - Apparatus 8 (COMPLETE)**
```json
{
  "entityName": "cr950_apparatus",
  "data": {
    "cr950_name": "Breaker 3B",
    "cr950_apparatusnumber": "BRK-3B",
    "cr950_anticipatedstartdate": "2025-12-08",
    "cr950_actualstartdate": "2025-12-09",
    "cr950_datecompleted": "2025-12-10",
    "cr950_apparatushours": 8.5,
    "cr950_task@odata.bind": "/cr950_taskses({task3Id})",
    "cr950_projectscope@odata.bind": "/cr950_projectscopes({scopeId})",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})"
  }
}
```

#### **Task 3 - Apparatus 9 (IN PROGRESS)**
```json
{
  "entityName": "cr950_apparatus",
  "data": {
    "cr950_name": "Breaker 3C",
    "cr950_apparatusnumber": "BRK-3C",
    "cr950_anticipatedstartdate": "2025-12-09",
    "cr950_actualstartdate": "2025-12-10",
    "cr950_apparatushours": 8.5,
    "cr950_task@odata.bind": "/cr950_taskses({task3Id})",
    "cr950_projectscope@odata.bind": "/cr950_projectscopes({scopeId})",
    "cr950_project@odata.bind": "/cr950_projectses({projectId})"
  }
}
```
*Note: No cr950_datecompleted - still in progress*

---

## 📊 EXPECTED ROLLUP VALUES

### **Task 1 (3 apparatus: 2 complete, 1 in progress)**

| Rollup Field | Expected Value | Calculation |
|--------------|----------------|-------------|
| `cr950_earliestanticipatedstart` | 2025-12-01 | MIN of 12/1, 12/2, 12/3 |
| `cr950_latestanticipatedstart` | 2025-12-03 | MAX of 12/1, 12/2, 12/3 |
| `cr950_earliestactualstart` | 2025-12-02 | MIN of 12/2, 12/3, 12/4 |
| `cr950_latestactualstart` | 2025-12-04 | MAX of 12/2, 12/3, 12/4 |
| `cr950_earliestcompletiondate` | 2025-12-05 | MIN of 12/5, 12/6 (complete only) |
| `cr950_latestcompletiondate` | 2025-12-06 | MAX of 12/5, 12/6 (complete only) |

### **Task 2 (3 apparatus: 2 complete, 1 in progress)**

| Rollup Field | Expected Value | Calculation |
|--------------|----------------|-------------|
| `cr950_earliestanticipatedstart` | 2025-12-04 | MIN of 12/4, 12/5, 12/6 |
| `cr950_latestanticipatedstart` | 2025-12-06 | MAX of 12/4, 12/5, 12/6 |
| `cr950_earliestactualstart` | 2025-12-05 | MIN of 12/5, 12/6, 12/7 |
| `cr950_latestactualstart` | 2025-12-07 | MAX of 12/5, 12/6, 12/7 |
| `cr950_earliestcompletiondate` | 2025-12-07 | MIN of 12/7, 12/8 (complete only) |
| `cr950_latestcompletiondate` | 2025-12-08 | MAX of 12/7, 12/8 (complete only) |

### **Task 3 (3 apparatus: 2 complete, 1 in progress)**

| Rollup Field | Expected Value | Calculation |
|--------------|----------------|-------------|
| `cr950_earliestanticipatedstart` | 2025-12-07 | MIN of 12/7, 12/8, 12/9 |
| `cr950_latestanticipatedstart` | 2025-12-09 | MAX of 12/7, 12/8, 12/9 |
| `cr950_earliestactualstart` | 2025-12-08 | MIN of 12/8, 12/9, 12/10 |
| `cr950_latestactualstart` | 2025-12-10 | MAX of 12/8, 12/9, 12/10 |
| `cr950_earliestcompletiondate` | 2025-12-09 | MIN of 12/9, 12/10 (complete only) |
| `cr950_latestcompletiondate` | 2025-12-10 | MAX of 12/9, 12/10 (complete only) |

### **Scope (rolls up from 3 tasks = 9 apparatus total)**

| Rollup Field | Expected Value | Calculation |
|--------------|----------------|-------------|
| `cr950_earliestanticipatedstart` | 2025-12-01 | MIN across all 9 apparatus |
| `cr950_latestanticipatedstart` | 2025-12-09 | MAX across all 9 apparatus |
| `cr950_earliestactualstart` | 2025-12-02 | MIN across all 9 apparatus |
| `cr950_latestactualstart` | 2025-12-10 | MAX across all 9 apparatus |
| `cr950_earliestcompletiondate` | 2025-12-05 | MIN of 6 complete apparatus |
| `cr950_latestcompletiondate` | 2025-12-10 | MAX of 6 complete apparatus |

### **Project (rolls up from 1 scope)**

| Rollup Field | Expected Value | Notes |
|--------------|----------------|-------|
| `cr950_earliestanticipatedstart` | 2025-12-01 | Same as scope (only 1 scope) |
| `cr950_latestanticipatedstart` | 2025-12-09 | Same as scope |
| `cr950_earliestactualstart` | 2025-12-02 | Same as scope |
| `cr950_latestactualstart` | 2025-12-10 | Same as scope |
| `cr950_earliestcompletiondate` | 2025-12-05 | Same as scope |
| `cr950_latestcompletiondate` | 2025-12-10 | Same as scope |

---

## 📋 SUMMARY

**Total Records to Create:** 15
- 1 Client
- 1 Site
- 1 Project
- 1 Scope
- 3 Tasks
- 9 Apparatus (6 complete, 3 in progress)

**Total Rollup Fields to Validate:** 18
- 6 on each Task (× 3 tasks = 18 rollup calculations)
- 6 on Scope (aggregating 18 task rollups)
- 6 on Project (aggregating scope rollups)

**Date Range:**
- Anticipated Start: Dec 1-9, 2025
- Actual Start: Dec 2-10, 2025
- Completion: Dec 5-10, 2025 (6 complete only)

---

## ⏱️ EXECUTION TIMELINE

1. **Create Records:** 10-15 minutes (VS Code Claude OR manual)
2. **Wait for Rollups:** 2-3 minutes (system background jobs)
3. **Query & Validate:** 5-10 minutes (Claude Desktop)
4. **Create Report:** 5 minutes

**Total:** ~25-35 minutes to complete validation

---

## ✅ VALIDATION QUERIES

**After 2-3 minute wait, run these queries:**

```javascript
// Query Tasks - should show 6 date fields populated per task
const tasks = await query_dataverse("cr950_taskses", null, null, 10);

// Query Scope - should show 6 date fields aggregated from all tasks
const scopes = await query_dataverse("cr950_projectscopes", null, null, 10);

// Query Project - should show 6 date fields aggregated from scope
const projects = await query_dataverse("cr950_projectses", null, null, 10);
```

---

## 🎯 SUCCESS CRITERIA

✅ All 15 records created successfully  
✅ 18 date rollup fields populated (6 × 3 tables)  
✅ Rollup values match expected calculations  
✅ MIN/MAX calculations correct  
✅ Completion dates only include complete apparatus  
✅ Hierarchical rollups working (Apparatus → Task → Scope → Project)

---

**Created:** 2025-11-24T01:40:00Z  
**Status:** Ready for execution via VS Code Claude OR manual entry  
**Next:** Create data → Wait 2-3 min → Query → Validate → Report
