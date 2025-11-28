# RESA Power - Test Data & Validation Plan
## November 23, 2025

**Purpose:** Manual test data creation and rollup field validation  
**Status:** 🎯 Ready to Execute  
**Prerequisites:** ✅ resa-dataverse-mcp operational (Create, Read, Delete verified)

---

## 📊 Current Status

### Tables Created
✅ All 16 tables exist in Dataverse  
✅ All tables accessible (verified with queries)  
✅ 32 rollup fields created in v1.5.0.0 (verified via solution audit)  
❌ **No test data yet** - Tables are empty

### MCP Server Capabilities (Verified Nov 23, 2025)
✅ **resa-dataverse-mcp:** Create, Read, Delete operations working  
✅ **Test 5:** Create test project record → SUCCESS  
✅ **Test 6:** Query created record → SUCCESS  
✅ **Test 7:** Delete test record → SUCCESS  
⚠️ **Known Limitation:** $select parameter fails on custom tables (use workaround)

### Test Result
```json
{
  "status": "WARNING",
  "tableName": "cr950_projectscopes",
  "recordsTested": 0,
  "summary": {
    "passed": 0,
    "failed": 0,
    "warnings": 1
  }
}
```

**Analysis:** Cannot validate rollup calculations without data

---

## 🎯 Execution Plan

### Phase 1: Manual Test Data Creation (60-90 minutes)

**Approach:** Use resa-dataverse-mcp `create_record` tool

**Why Manual:**
- ❌ No automated test data generator exists yet
- ✅ create_record verified working (Test 5 passed)
- ✅ Ensures data quality and referential integrity
- ✅ Learn the data model through hands-on creation

**Step-by-Step Record Creation:**

**Step 1: Create Supporting Records (15 min)**
```javascript
// 1. Create Business Unit (RESA location)
const businessUnit = await create_record("cr950_businessunit", {
  cr950_name: "Phoenix Office",
  cr950_code: "PHX"
});

// 2. Create Client
const client = await create_record("cr950_client", {
  cr950_name: "Test Hospital",
  cr950_accountnumber: "TEST-001"
});

// 3. Create Site
const site = await create_record("cr950_site", {
  cr950_name: "Main Campus",
  "cr950_client@odata.bind": `/cr950_clients(${client.id})`
});
```

**Step 2: Create Project Hierarchy (20 min)**
```javascript
// 4. Create Project
const project = await create_record("cr950_projects", {
  cr950_name: "Hospital Switchgear Testing",
  cr950_projectnumber: "PHX-2025-TEST01",
  "cr950_client@odata.bind": `/cr950_clients(${client.id})`,
  "cr950_site@odata.bind": `/cr950_sites(${site.id})`,
  "cr950_location@odata.bind": `/cr950_businessunits(${businessUnit.id})`
});

// 5. Create Scope
const scope = await create_record("cr950_projectscopes", {
  cr950_name: "Main Distribution",
  cr950_scopenumber: "S01",
  "cr950_project@odata.bind": `/cr950_projectses(${project.id})`
});

// 6. Create Tasks (3 tasks)
const task1 = await create_record("cr950_tasks", {
  cr950_name: "Switchgear - Building A",
  "cr950_projectscope@odata.bind": `/cr950_projectscopes(${scope.id})`,
  "cr950_project@odata.bind": `/cr950_projectses(${project.id})`
});
// Repeat for task2, task3...
```

**Step 3: Create Apparatus with Dates (25 min)**
```javascript
// 7. Create Apparatus (3 per task = 9 total)
const apparatus1 = await create_record("cr950_apparatuses", {
  cr950_name: "Breaker 1A",
  cr950_apparatusnumber: "BRK-1A",
  "cr950_task@odata.bind": `/cr950_taskses(${task1.id})`,
  "cr950_projectscope@odata.bind": `/cr950_projectscopes(${scope.id})`,
  "cr950_project@odata.bind": `/cr950_projectses(${project.id})`,
  cr950_anticipatedstartdate: "2025-12-01",
  cr950_actualstartdate: "2025-12-02",
  cr950_datecompleted: "2025-12-05"
});
// Repeat with varying dates for apparatus2-9...
```

**Alternative: Import from CSV** (If preferred)
- Use existing LASNAP16 project data
- Convert to CSV format matching Dataverse schema
- Import via Power Platform data import wizard
- More setup but provides realistic data

### Phase 2: Wait for Rollup Calculations (2-5 minutes)

⚠️ **Critical:** Rollup fields calculate asynchronously in background System Jobs

**After Creating Data:**
1. Wait 2-3 minutes for calculations
2. Check System Jobs in Power Platform Admin Center if needed
3. Refresh queries to see updated values

---

### Phase 3: Validate Rollup Fields (20-30 minutes)

**Tables with Rollup Fields (32 total in v1.5.0.0):**

**1. cr950_taskses (Tasks) - 6 Date Tracking Rollups**
   - `cr950_earliestanticipatedstart` (MIN from Apparatus)
   - `cr950_latestanticipatedstart` (MAX from Apparatus)
   - `cr950_earliestactualstart` (MIN from Apparatus)
   - `cr950_latestactualstart` (MAX from Apparatus)
   - `cr950_earliestcompletiondate` (MIN from Apparatus)
   - `cr950_latestcompletiondate` (MAX from Apparatus)
   
**2. cr950_projectscopes (Scopes) - 6 Date Tracking Rollups**
   - Same 6 fields, aggregated from Tasks
   
**3. cr950_projectses (Projects) - 6 Date Tracking Rollups**
   - Same 6 fields, aggregated from Scopes

**4. cr950_scopefinancialsummaries - 7 Revenue Rollups**
   - `cr950_totalrevenuerecognized` (SUM)
   - `cr950_totalrevenuepending` (SUM)
   - `cr950_totalbillablehours` (SUM)
   - `cr950_totaldelayhours` (SUM)
   - `cr950_apparatusrevenuecount` (COUNT)
   - `cr950_averagelaborrate` (AVG)
   - `cr950_latestrevenuedate` (MAX)

**5. cr950_projectfinancialsummaries - 7 Revenue Rollups**
   - Same 7 fields, aggregated from Scope Financial Summaries

**Manual Validation Approach:**
```javascript
// Step 1: Query parent record
const tasks = await query_dataverse("cr950_taskses", null, null, 10);

// Step 2: Manually calculate expected values
// Expected: MIN(apparatus dates) and MAX(apparatus dates)

// Step 3: Compare system values to manual calculation
// System: tasks[0].cr950_earliestanticipatedstart
// Manual: (check your created apparatus dates)

// Step 4: Document pass/fail
```

### Phase 3: Document Results (10 minutes)

**Create Validation Report:**
- Summary of tested fields
- Pass/fail status for each
- Any discrepancies found
- Recommendations for fixes

---

## 📋 Actual Rollup Fields in v1.5.0.0

**Source:** Verified via solution export audit (SOLUTION_v1.5.0.0_AUDIT_REPORT.md)

### Tasks Table (6 Date Tracking Rollups)
- `cr950_earliestanticipatedstart` - MIN(Anticipated Start from Apparatus)
- `cr950_latestanticipatedstart` - MAX(Anticipated Start from Apparatus)
- `cr950_earliestactualstart` - MIN(Actual Start from Apparatus)
- `cr950_latestactualstart` - MAX(Actual Start from Apparatus)
- `cr950_earliestcompletiondate` - MIN(Completion Date from Apparatus)
- `cr950_latestcompletiondate` - MAX(Completion Date from Apparatus)

### Project Scope Table (6 Date Tracking Rollups)
- `cr950_earliestanticipatedstart` - MIN(Anticipated Start from Tasks)
- `cr950_latestanticipatedstart` - MAX(Anticipated Start from Tasks)
- `cr950_earliestactualstart` - MIN(Actual Start from Tasks)
- `cr950_latestactualstart` - MAX(Actual Start from Tasks)
- `cr950_earliestcompletiondate` - MIN(Completion Date from Tasks)
- `cr950_latestcompletiondate` - MAX(Completion Date from Tasks)

### Projects Table (6 Date Tracking Rollups)
- `cr950_earliestanticipatedstart` - MIN(Anticipated Start from Scopes)
- `cr950_latestanticipatedstart` - MAX(Anticipated Start from Scopes)
- `cr950_earliestactualstart` - MIN(Actual Start from Scopes)
- `cr950_latestactualstart` - MAX(Actual Start from Scopes)
- `cr950_earliestcompletiondate` - MIN(Completion Date from Scopes)
- `cr950_latestcompletiondate` - MAX(Completion Date from Scopes)

### Scope Financial Summary Table (7 Revenue Rollups)
- `cr950_totalrevenuerecognized` - SUM(Revenue Recognized from Apparatus Revenue)
- `cr950_totalrevenuepending` - SUM(Revenue Pending from Apparatus Revenue)
- `cr950_totalbillablehours` - SUM(Billable Hours from Apparatus Revenue)
- `cr950_totaldelayhours` - SUM(Delay Hours from Apparatus Revenue)
- `cr950_apparatusrevenuecount` - COUNT(Apparatus Revenue records)
- `cr950_averagelaborrate` - AVG(Labor Rate from Apparatus Revenue)
- `cr950_latestrevenuedate` - MAX(Revenue Date from Apparatus Revenue)

### Project Financial Summary Table (7 Revenue Rollups)
- `cr950_totalrevenuerecognized` - SUM(from Scope Financial Summaries)
- `cr950_totalrevenuepending` - SUM(from Scope Financial Summaries)
- `cr950_totalbillablehours` - SUM(from Scope Financial Summaries)
- `cr950_totaldelayhours` - SUM(from Scope Financial Summaries)
- `cr950_apparatusrevenuecount` - SUM(from Scope Financial Summaries)
- `cr950_averagelaborrate` - AVG(from Scope Financial Summaries)
- `cr950_latestrevenuedate` - MAX(from Scope Financial Summaries)

**Total: 32 Rollup Fields** (18 date tracking + 14 revenue)

---

## 🚀 Recommended Execution Sequence

### Step 1: Generate Test Data (NOW)
```bash
# In Claude Desktop:
"Generate test data using resa-testing with medium scenario - 
2 projects, 2 scopes each, 3 tasks per scope, 10 apparatus per task, 
50% complete, include financial data"
```

**Expected Duration:** 5-10 minutes  
**Expected Records:** ~200 total records created

### Step 2: Verify Data Created
```bash
# Query each table to confirm:
"Query cr950_projectses table - how many records?"
"Query cr950_apparatuses table - how many records?"
"Query cr950_apparatusrevenues table - how many records?"
```

**Expected Results:**
- 2 projects
- 4 scopes  
- 12 tasks
- 120 apparatus
- 60 revenue records

### Step 3: Validate Rollup Fields
```bash
# Test each table with rollups:
"Validate rollup fields on cr950_projectscopes table"
"Validate rollup fields on cr950_taskses table"
"Validate rollup fields on cr950_projectses table"
```

**Expected Duration:** 15 minutes total  
**Expected Results:** Pass/fail report for each field

### Step 4: Review Results & Fix Issues
```bash
# If any failures:
"Show me the failed rollup calculations and explain the discrepancy"
```

### Step 5: Clean Up Test Data (Optional)
```bash
# After validation:
"Clean up test data generated today"
```

---

## ⚠️ Important Notes

### Data Consistency
- Test data generator ensures referential integrity
- All relationships properly linked
- Financial rates realistic ($300-400/hr range)
- Completion dates realistic

### Rollup Behavior
- Rollup fields recalculate automatically
- May take 1-2 minutes to update after data creation
- System jobs run in background
- Check "System Jobs" in Power Platform if delays

### Known Limitations
- Rollup fields don't show in resa-docs output (metadata issue)
- Field list must come from Power Apps or BUILD SPEC
- $select parameter doesn't work on custom tables (use workaround)

---

## 🎯 Success Criteria

### Test Data Generation
- ✅ All records created successfully
- ✅ No referential integrity errors
- ✅ Relationships properly linked
- ✅ Financial data realistic

### Rollup Validation
- ✅ All rollup fields calculate correctly
- ✅ Manual calculations match system calculations
- ✅ No discrepancies found
- ✅ Performance acceptable (<2 min updates)

### Documentation
- ✅ Validation report created
- ✅ Any issues documented
- ✅ Recommendations provided
- ✅ Next steps clear

---

## 📊 Expected Validation Results

### Scenario: 2 Projects, Medium Complexity

**Project 1:**
- Scope 1: 30 apparatus, 15 complete → ~130 hours
- Scope 2: 30 apparatus, 15 complete → ~130 hours
- **Project Total:** 60 apparatus, 30 complete → ~260 hours

**Project 2:**
- Scope 1: 30 apparatus, 15 complete → ~130 hours
- Scope 2: 30 apparatus, 15 complete → ~130 hours
- **Project Total:** 60 apparatus, 30 complete → ~260 hours

**Financial:**
- Rate: ~$360/hr
- Revenue per complete apparatus: ~$3,000
- Total revenue: 60 complete × $3,000 = ~$180,000

**Rollup Calculations to Verify:**
- Scope hours = Sum of apparatus hours under that scope
- Task hours = Sum of apparatus hours under that task
- Project hours = Sum of scope hours
- Revenue = Complete apparatus × hours × rate

---

## 🔧 Troubleshooting

### Issue: "No rollup fields found"
**Solution:** Verify rollup fields exist in schema via Power Apps

### Issue: "Rollup fields not calculating"
**Solution:** 
1. Check System Jobs for errors
2. Wait 2 minutes for background job
3. Manually trigger calculate rollup

### Issue: "Validation fails"
**Solution:**
1. Check manual calculation
2. Verify data relationships
3. Check rollup field formula

---

## ✅ Ready to Execute

**Prerequisites Met:**
- ✅ resa-dataverse-mcp operational (Create, Read, Delete verified)
- ✅ All 16 tables created in Dataverse
- ✅ All relationships defined
- ✅ 32 rollup fields created and verified in v1.5.0.0
- ✅ Manual data creation approach documented
- ✅ TABLE_NAMES_REFERENCE.md available for correct naming

**Prerequisites NOT Met:**
- ❌ No automated test data generator (must create manually)
- ❌ No validation functions (must validate manually)

**Execute Now:**
```
"Create test data manually using resa-dataverse-mcp create_record.
Start with: Business Unit, Client, Site, then build Project hierarchy."
```

**Reference Documents:**
- MCP Status: [MCP_STATUS_REPORT_20251123.md](../06_Implementation_Guides/MCP_STATUS_REPORT_20251123.md)
- Rollup Audit: [SOLUTION_v1.5.0.0_AUDIT_REPORT.md](../03_Progress_Tracking/SOLUTION_v1.5.0.0_AUDIT_REPORT.md)
- Table Names: [TABLE_NAMES_REFERENCE.md](../../MCP_Servers/resa-dataverse-mcp/TABLE_NAMES_REFERENCE.md)

---

**Created:** 2025-11-23T22:30:00Z  
**Updated:** 2025-11-23T22:45:00Z  
**Status:** 🎯 Ready for Manual Execution  
**Next:** Create test data manually → Wait for rollup calculations → Validate manually → Document results
