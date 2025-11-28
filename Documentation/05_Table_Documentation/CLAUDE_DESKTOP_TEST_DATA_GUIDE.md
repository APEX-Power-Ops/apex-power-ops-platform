# Test Data Creation Guide for Claude Desktop
## Using resa-dataverse-dev MCP Server (Verified Working)

**Created:** November 23, 2025  
**Purpose:** Step-by-step guide for Claude Desktop to create test data  
**Tool:** `resa-dataverse-dev` MCP server with `create_record` (verified working in Test 5)  
**Status:** ✅ Ready for Claude Desktop execution

---

## ✅ Tool Availability Confirmed

**Claude Desktop Config Includes:**
- `resa-dataverse-dev` - Dataverse CRUD operations ✅
- `resa-testing` - Validation and testing tools ✅
- `resa-docs` - Documentation generation ✅
- `resa-deploy` - Solution deployment ✅
- `filesystem` - File operations ✅
- `github` - GitHub operations ✅
- `postgres` - Database queries ✅
- `memory` - Knowledge graph ✅

**Confirmed:** `create_record` tool available via `resa-dataverse-dev` server

---

## 🎯 Quick Task for Claude Desktop

**Copy this message to Claude Desktop:**

```
Create test data for rollup field validation using resa-dataverse-dev MCP server.

Use create_record tool (verified working) to create this hierarchy:

1. Client:
   - Table: cr950_client (singular in create_record)
   - Data: { cr950_name: "Test Hospital", cr950_accountnumber: "TEST-2025-001" }

2. Site:
   - Table: cr950_site
   - Data: { cr950_name: "Main Campus Test", cr950_address: "123 Test St", cr950_city: "Phoenix", cr950_state: "AZ" }
   - Link to client from step 1

3. Project:
   - Table: cr950_projects (singular)
   - Data: { cr950_name: "Test Switchgear Project", cr950_projectnumber: "PHX-TEST-001" }
   - Link to client and site

4. Scope:
   - Table: cr950_projectscope (singular)
   - Data: { cr950_name: "Test Scope", cr950_scopenumber: "S01" }
   - Link to project

5. Tasks (create 3):
   - Table: cr950_tasks (singular)
   - Data: { cr950_name: "Test Task 1/2/3" }
   - Link to project and scope

6. Apparatus (create 9 total - 3 per task):
   - Table: cr950_apparatus (singular)
   - Data: Include these date fields:
     * cr950_anticipatedstartdate: "2025-12-01" (vary by +1 day each)
     * cr950_actualstartdate: "2025-12-02" (vary by +1 day each)
     * cr950_datecompleted: "2025-12-05" (only on 6 out of 9)
   - Link to task, scope, and project

After creation, wait 2-3 minutes then query to verify rollups calculated.

Reference TABLE_NAMES_REFERENCE.md for plural query names.
```

---

## 📋 Detailed Steps for Manual Execution

### **Step 1: Create Client**
```javascript
const client = await create_record("cr950_client", {
  cr950_name: "Test Hospital",
  cr950_accountnumber: "TEST-2025-001"
});
// Save client.id for next steps
```

### **Step 2: Create Site**
```javascript
const site = await create_record("cr950_site", {
  cr950_name: "Main Campus Test",
  cr950_address: "123 Test Street",
  cr950_city: "Phoenix",
  cr950_state: "AZ",
  "cr950_client@odata.bind": `/cr950_clients(${client.id})`
});
```

### **Step 3: Create Project**
```javascript
const project = await create_record("cr950_projects", {
  cr950_name: "Test Switchgear Project",
  cr950_projectnumber: "PHX-TEST-001",
  cr950_description: "Test data for rollup validation",
  "cr950_client@odata.bind": `/cr950_clients(${client.id})`,
  "cr950_site@odata.bind": `/cr950_sites(${site.id})`
});
```

### **Step 4: Create Scope**
```javascript
const scope = await create_record("cr950_projectscope", {
  cr950_name: "Main Distribution",
  cr950_scopenumber: "S01",
  cr950_description: "Test scope",
  "cr950_project@odata.bind": `/cr950_projectses(${project.id})`
});
```

### **Step 5: Create Tasks (x3)**
```javascript
const task1 = await create_record("cr950_tasks", {
  cr950_name: "Switchgear Building A",
  "cr950_project@odata.bind": `/cr950_projectses(${project.id})`,
  "cr950_projectscope@odata.bind": `/cr950_projectscopes(${scope.id})`
});

const task2 = await create_record("cr950_tasks", {
  cr950_name: "Switchgear Building B",
  "cr950_project@odata.bind": `/cr950_projectses(${project.id})`,
  "cr950_projectscope@odata.bind": `/cr950_projectscopes(${scope.id})`
});

const task3 = await create_record("cr950_tasks", {
  cr950_name: "Switchgear Building C",
  "cr950_project@odata.bind": `/cr950_projectses(${project.id})`,
  "cr950_projectscope@odata.bind": `/cr950_projectscopes(${scope.id})`
});
```

### **Step 6: Create Apparatus (x9 with dates)**
```javascript
// Task 1 - Apparatus 1 (COMPLETE)
await create_record("cr950_apparatus", {
  cr950_name: "Breaker 1A",
  cr950_apparatusnumber: "BRK-1A",
  cr950_anticipatedstartdate: "2025-12-01",
  cr950_actualstartdate: "2025-12-02",
  cr950_datecompleted: "2025-12-05",
  "cr950_task@odata.bind": `/cr950_taskses(${task1.id})`,
  "cr950_projectscope@odata.bind": `/cr950_projectscopes(${scope.id})`,
  "cr950_project@odata.bind": `/cr950_projectses(${project.id})`
});

// Task 1 - Apparatus 2 (COMPLETE)
await create_record("cr950_apparatus", {
  cr950_name: "Breaker 1B",
  cr950_apparatusnumber: "BRK-1B",
  cr950_anticipatedstartdate: "2025-12-02",
  cr950_actualstartdate: "2025-12-03",
  cr950_datecompleted: "2025-12-06",
  "cr950_task@odata.bind": `/cr950_taskses(${task1.id})`,
  "cr950_projectscope@odata.bind": `/cr950_projectscopes(${scope.id})`,
  "cr950_project@odata.bind": `/cr950_projectses(${project.id})`
});

// Task 1 - Apparatus 3 (IN PROGRESS - no completion date)
await create_record("cr950_apparatus", {
  cr950_name: "Breaker 1C",
  cr950_apparatusnumber: "BRK-1C",
  cr950_anticipatedstartdate: "2025-12-03",
  cr950_actualstartdate: "2025-12-04",
  "cr950_task@odata.bind": `/cr950_taskses(${task1.id})`,
  "cr950_projectscope@odata.bind": `/cr950_projectscopes(${scope.id})`,
  "cr950_project@odata.bind": `/cr950_projectses(${project.id})`
});

// Repeat similar pattern for task2 and task3...
// Total: 9 apparatus (6 complete, 3 in progress)
```

---

## ⏱️ Wait for Rollup Calculations

After creating all records, **WAIT 2-3 MINUTES** for background System Jobs to calculate rollups.

---

## ✅ Verify Rollups Calculated

### **Query Tasks (should show 6 date rollups)**
```javascript
const tasks = await query_dataverse("cr950_taskses", null, null, 3);

// Expected fields populated:
// - cr950_earliestanticipatedstart = "2025-12-01" (MIN from 3 apparatus)
// - cr950_latestanticipatedstart = "2025-12-03" (MAX from 3 apparatus)
// - cr950_earliestactualstart = "2025-12-02"
// - cr950_latestactualstart = "2025-12-04"
// - cr950_earliestcompletiondate = "2025-12-05" (MIN from complete only)
// - cr950_latestcompletiondate = "2025-12-06" (MAX from complete only)
```

### **Query Scope (should show 6 date rollups aggregated from Tasks)**
```javascript
const scopes = await query_dataverse("cr950_projectscopes", null, null, 1);

// Should show same pattern, aggregated from all 3 tasks
```

### **Query Project (should show 6 date rollups aggregated from Scopes)**
```javascript
const projects = await query_dataverse("cr950_projectses", null, null, 1);

// Should show top-level aggregation
```

---

## 🎯 Expected Results

### **Task 1 Rollups:**
| Field | Expected Value | Calculation |
|-------|----------------|-------------|
| Earliest Anticipated Start | 2025-12-01 | MIN(3 apparatus) |
| Latest Anticipated Start | 2025-12-03 | MAX(3 apparatus) |
| Earliest Actual Start | 2025-12-02 | MIN(3 apparatus) |
| Latest Actual Start | 2025-12-04 | MAX(3 apparatus) |
| Earliest Completion | 2025-12-05 | MIN(2 complete) |
| Latest Completion | 2025-12-06 | MAX(2 complete) |

### **Scope Rollups:**
Should aggregate across all 9 apparatus (3 tasks × 3 apparatus each)

### **Project Rollups:**
Should show same as Scope (only 1 scope in test)

---

## 🧹 Cleanup (Optional)

To remove test data after validation:

```javascript
// Delete in reverse order (child to parent)
// Delete apparatus records
// Delete task records  
// Delete scope record
// Delete project record
// Delete site record
// Delete client record
```

---

## 📝 Notes

- **Table Names:** Use singular for create_record, plural for query_dataverse
- **Lookups:** Use `@odata.bind` format with plural collection names
- **Dates:** Use ISO format "YYYY-MM-DD"
- **IDs:** Save returned IDs for linking child records
- **Wait Time:** 2-3 minutes for rollup calculations after data creation

---

**Status:** Ready for Claude Desktop execution  
**Tool:** resa-dataverse-mcp (verified working Nov 23, 2025)  
**Expected Duration:** 10-15 minutes to create + 3 minutes wait  
**Next:** Query to verify rollups, create validation report
