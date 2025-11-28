# CLAUDE DESKTOP SESSION PROTOCOL
## How to Start and Work with Claude Desktop on RESA Power Project

**Purpose**: This guide provides the exact protocol for starting new conversations with Claude Desktop, ensuring he has proper context and access to MCP servers.

**Last Updated**: November 23, 2025  
**Current Version**: v1.5.0.0 (32 rollup fields completed)

---

## 🚀 QUICK START - Opening Message Template

### **Standard Opening Message** (Copy/Paste This)

```
I'm working on the RESA Power Project Tracker. Please read:

1. Documentation/00_START_HERE/PROJECT_STATUS_TRACKER.md
2. Documentation/03_Progress_Tracking/[LATEST_SESSION_SUMMARY].md
3. Documentation/06_Implementation_Guides/TABLE_NAMES_REFERENCE.md

Current context:
- Solution version: v1.5.0.0
- Environment: org99cd6c6e.crm.dynamics.com (dev)
- Recent work: 32 rollup fields completed (18 date tracking + 14 revenue)
- MCP servers: resa-docs and resa-dataverse operational

Today's focus: [DESCRIBE YOUR TASK]

Please confirm you have access to the MCP servers and summarize what you understand about the current state.
```

---

## 📋 WHAT CLAUDE DESKTOP SHOULD DO NEXT

### **Step 1: Confirm MCP Server Access**

Claude Desktop should respond with:

```
✅ MCP servers detected:
   • resa-dataverse-mcp (5 tools available)
     - query_dataverse
     - create_record
     - update_record
     - delete_record
     - list_tables
   
   • resa-docs-mcp (4 tools available)
     - generate_table_documentation
     - generate_erd_diagram
     - generate_user_guide
     - generate_api_docs
   
   • resa-filesystem-mcp (file operations)
   • memory-mcp (knowledge graph - optional)
```

**If MCP servers are NOT detected:**
- Claude Desktop needs to be restarted
- Check `%APPDATA%\Claude\claude_desktop_config.json` configuration
- Verify MCP servers are running (check Task Manager for node.exe processes)

---

### **Step 2: Read Context Files**

Claude Desktop should confirm reading:

1. **PROJECT_STATUS_TRACKER.md** - Master navigation and current state
2. **Latest Session Summary** - Most recent work context
3. **TABLE_NAMES_REFERENCE.md** - Critical for correct OData queries

**Expected Response:**
```
✅ Context loaded:
   • Current version: v1.5.0.0
   • Tables: 16 RESA custom tables
   • Recent completion: 32 rollup fields (date tracking + revenue)
   • MCP Status: Both servers operational with documented limitations
   • Ready to proceed with: [YOUR TASK]
```

---

### **Step 3: Validate Understanding**

Claude Desktop should demonstrate understanding by:

1. **Table Naming Awareness**
   - Uses PLURAL EntitySetNames (cr950_projectses, NOT cr950_projects)
   - References TABLE_NAMES_REFERENCE.md for correct names

2. **MCP Server Limitations**
   - Knows about $select parameter issue on custom tables
   - Uses workaround (query without $select)

3. **Current Context**
   - Knows solution is at v1.5.0.0
   - Understands 32 rollup fields just completed
   - Aware of environment (org99cd6c6e dev)

---

## 🎯 SPECIFIC USE CASE TEMPLATES

### **Use Case 1: Validate Rollup Fields**

**Your Message:**
```
Validate that all 32 rollup fields exist in Dataverse using resa-dataverse-mcp.

Reference TABLE_NAMES_REFERENCE.md for correct table names (use PLURAL EntitySetNames).

Query these tables and list the rollup fields found:
1. cr950_taskses (expect 6 date rollups: earliest/latest anticipated start, actual start, completion date)
2. cr950_projectscopes (expect 6 date rollups: same pattern)
3. cr950_projectses (expect 6 date rollups: same pattern)
4. cr950_scopefinancialsummaries (expect 7 revenue rollups: totals, counts, averages, dates)
5. cr950_projectfinancialsummaries (expect 7 revenue rollups: same pattern)

Create a validation report comparing expected vs actual, noting any missing fields.
```

**Expected Claude Desktop Actions:**
1. Read TABLE_NAMES_REFERENCE.md
2. Query each table using correct plural names
3. List fields found (may show 0 due to $select limitation)
4. Create structured validation report
5. Note any discrepancies

---

### **Use Case 2: Generate Documentation**

**Your Message:**
```
Generate comprehensive table documentation for these RESA Power tables using resa-docs-mcp:

1. cr950_projectses (Projects)
2. cr950_projectscopes (Scopes)
3. cr950_taskses (Tasks)
4. cr950_apparatuses (Apparatus)

For each table, generate:
- Field list with types and descriptions
- Relationship map (parent/child tables)
- Code examples for CRUD operations

Note: Documentation may show [object Object] for display names - this is a known cosmetic issue.

Save output to: Documentation/07_Application_Specs/[TableName]_Documentation.md
```

**Expected Claude Desktop Actions:**
1. Use generate_table_documentation tool for each table
2. Accept [object Object] display names (known issue)
3. Format output as markdown
4. Create/update documentation files
5. Report relationships found (should find ~29 for Projects)

---

### **Use Case 3: Query Data**

**Your Message:**
```
Query the Projects table and show me all records with key fields.

Use resa-dataverse-mcp with table name: cr950_projectses (plural).

Don't use $select parameter (known issue). Retrieve all fields and filter client-side.

Show me:
- Project ID
- Project Name
- Status
- Client lookup
- Date Created

If no records exist, that's expected - we're in dev environment.
```

**Expected Claude Desktop Actions:**
1. Query cr950_projectses without $select
2. Handle empty result gracefully
3. If records exist, format key fields in table
4. Note environment (dev) for context

---

### **Use Case 4: Test Calculations**

**Your Message:**
```
Create a test project with sample data to verify rollup calculations work.

Steps:
1. Create a test project record (cr950_projectses)
2. Create a test scope linked to that project (cr950_projectscopes)
3. Create 2-3 test apparatus records with dates (cr950_apparatuses)
4. Wait 2-3 minutes for rollup calculations
5. Query the project and scope to verify rollup fields populated

Expected rollup behavior:
- Earliest dates should show minimum date from child records
- Latest dates should show maximum date from child records
- Counts should match number of child records

Report any rollups that don't calculate correctly.
```

**Expected Claude Desktop Actions:**
1. Use create_record to build test hierarchy
2. Document record IDs created
3. Wait appropriate time for calculations
4. Query parent records to check rollups
5. Report success/failure for each rollup
6. Provide cleanup instructions (delete test records)

---

## ⚠️ CRITICAL REMINDERS FOR CLAUDE DESKTOP

### **Table Naming Rules (ALWAYS ENFORCE)**

| ❌ DON'T USE (Singular) | ✅ USE THIS (Plural EntitySetName) |
|------------------------|----------------------------------|
| cr950_projects | cr950_projectses |
| cr950_apparatus | cr950_apparatuses |
| cr950_tasks | cr950_taskses |
| cr950_projectscope | cr950_projectscopes |
| cr950_scopefinancialsummary | cr950_scopefinancialsummaries |
| cr950_projectfinancialsummary | cr950_projectfinancialsummaries |

**Why**: OData API requires plural EntitySetNames. Using singular names causes 404 errors.

**Reference**: `Documentation/06_Implementation_Guides/TABLE_NAMES_REFERENCE.md`

---

### **Known MCP Server Limitations**

#### **resa-docs-mcp:**
- ✅ **Working**: Documentation generation, relationship detection (29 found for Projects)
- ⚠️ **Minor Issue**: Display names show `[object Object]` (cosmetic only)
- ⚠️ **Minor Issue**: Field count may show 0 (permissions issue)
- 🎯 **Status**: Fully operational, minor polish needed

#### **resa-dataverse-mcp:**
- ✅ **Working**: Authentication, queries, CRUD operations
- ✅ **Working**: System tables with full $select support
- ❌ **Known Issue**: $select parameter fails on custom tables (400 error)
- ✅ **Workaround**: Query without $select, filter client-side
- 🎯 **Status**: Fully operational with documented workaround

**Reference**: `Documentation/06_Implementation_Guides/MCP_STATUS_REPORT_20251123.md`

---

### **Environment Awareness**

**Development Environment:**
- URL: `org99cd6c6e.crm.dynamics.com`
- Name: Jason Swenson's Environment
- Purpose: Safe testing, MCP development
- Status: ✅ Safe for all operations

**Production Environment:**
- URL: `org04ad071f.crm.dynamics.com` (RESA production)
- Purpose: Live business operations
- Status: ❌ NEVER connect MCP servers here
- Note: Manual deployments only

**MCP Configuration Points to**: DEV ONLY ✅

---

## 📊 EXPECTED RESPONSE FORMAT

### **Good Claude Desktop Response:**

```
✅ MCP Servers Connected:
   • resa-dataverse-mcp: 5 tools available
   • resa-docs-mcp: 4 tools available

✅ Context Loaded:
   • Version: v1.5.0.0
   • Environment: org99cd6c6e (dev)
   • Recent: 32 rollup fields completed
   • Status: Both MCP servers operational

✅ Understanding Confirmed:
   • Will use PLURAL table names (cr950_projectses, not cr950_projects)
   • Will avoid $select on custom tables (known issue)
   • Will reference TABLE_NAMES_REFERENCE.md for correct names

✅ Ready to Proceed:
   [SUMMARY OF YOUR TASK]
   
Starting work...
```

### **Bad Claude Desktop Response (Needs Correction):**

```
I'll query the cr950_projects table...
```
❌ **WRONG**: Using singular name instead of plural

```
Let me get specific fields: $select=cr950_projectsid,cr950_name
```
❌ **WRONG**: Trying to use $select on custom table (will fail)

**If you see these errors, correct immediately:**
```
Stop - use cr950_projectses (plural) per TABLE_NAMES_REFERENCE.md.
Don't use $select parameter on custom tables - it's a known issue. Query all fields instead.
```

---

## 🔄 SESSION WORKFLOW

### **Typical Session Flow:**

1. **Opening** (2 minutes)
   - You provide opening message with context
   - Claude Desktop confirms MCP access
   - Claude Desktop reads context files
   - Claude Desktop validates understanding

2. **Work Phase** (varies)
   - Claude Desktop executes your task
   - Uses MCP tools appropriately
   - Follows table naming rules
   - Works around known limitations

3. **Reporting** (5 minutes)
   - Claude Desktop provides structured results
   - Notes any issues encountered
   - Suggests next steps
   - Documents findings

4. **Closing** (optional)
   - Save any documentation generated
   - Update tracking files if needed
   - Note any new issues discovered

---

## 🎯 SUCCESS CRITERIA

**Before Starting Work:**
- ✅ Claude Desktop confirms MCP server access
- ✅ Claude Desktop reads context files
- ✅ Claude Desktop demonstrates table naming awareness
- ✅ Claude Desktop acknowledges known limitations
- ✅ Task is clearly defined with specific deliverables

**During Work:**
- ✅ Uses correct plural table names
- ✅ Works around $select limitation
- ✅ Handles errors gracefully
- ✅ Provides progress updates
- ✅ Documents unexpected findings

**After Completion:**
- ✅ Delivers requested output
- ✅ Reports success/failure clearly
- ✅ Notes any discrepancies from expected
- ✅ Suggests follow-up actions if needed
- ✅ Documents any new issues found

---

## 🔧 TROUBLESHOOTING

### **Problem: MCP Servers Not Detected**

**Symptoms:**
- Claude Desktop doesn't list available tools
- "I don't have access to those servers" message

**Solutions:**
1. Restart Claude Desktop application
2. Check `%APPDATA%\Claude\claude_desktop_config.json` exists
3. Verify node.exe processes running (Task Manager)
4. Check MCP_STATUS_REPORT_20251123.md for server status

---

### **Problem: 404 Errors on Queries**

**Symptoms:**
- "Resource not found for the segment 'cr950_projects'"

**Solution:**
```
You're using the singular table name. Use the PLURAL EntitySetName:
- cr950_projects → cr950_projectses
- cr950_apparatus → cr950_apparatuses

Check TABLE_NAMES_REFERENCE.md for correct names.
```

---

### **Problem: 400 Errors with $select**

**Symptoms:**
- "Request failed with status code 400" when using field filtering

**Solution:**
```
This is a known issue with $select on custom tables. 

Use the workaround:
1. Query without $select parameter (get all fields)
2. Filter on client-side after retrieval

Reference: MCP_STATUS_REPORT_20251123.md, Issue 3
```

---

### **Problem: Empty Results**

**Symptoms:**
- Queries return `[]` (empty array)

**Explanation:**
```
This is NORMAL if:
1. We're in dev environment with no test data yet
2. Table exists but hasn't been populated
3. Filters exclude all records

This is NOT an error - it means the query worked but found no matching records.
```

---

### **Problem: Display Names Show [object Object]**

**Symptoms:**
- Documentation shows `[object Object]` instead of "Projects"

**Explanation:**
```
This is a known cosmetic issue with resa-docs-mcp.

Impact: LOW - doesn't prevent functionality
Status: Documented, fix scheduled for polish phase
Workaround: Use logical names (cr950_projects) to identify tables

Reference: MCP_STATUS_REPORT_20251123.md, Issue 1
```

---

## 📚 REFERENCE DOCUMENTS

**Essential Reading:**
1. **TABLE_NAMES_REFERENCE.md** - All 16 table names with correct EntitySetNames
2. **MCP_STATUS_REPORT_20251123.md** - Current server status and known issues
3. **MCP_VERIFICATION_REPORT_v2.md** - Independent verification results (100% alignment)
4. **PROJECT_STATUS_TRACKER.md** - Master navigation and current state

**Location:** `Documentation/06_Implementation_Guides/` and `Documentation/00_START_HERE/`

---

## 🎓 EXAMPLES OF GOOD SESSIONS

### **Example 1: Successful Validation Session**

**User Opening:**
```
Validate all 32 rollup fields exist in Dataverse.
Use resa-dataverse-mcp, reference TABLE_NAMES_REFERENCE.md for names.
```

**Claude Desktop Response:**
```
✅ MCP servers connected
✅ Read TABLE_NAMES_REFERENCE.md - will use plural names

Querying tables:
1. cr950_taskses... ✅ 6 date rollup fields found
2. cr950_projectscopes... ✅ 6 date rollup fields found
3. cr950_projectses... ✅ 6 date rollup fields found
4. cr950_scopefinancialsummaries... ✅ 7 revenue rollups found
5. cr950_projectfinancialsummaries... ✅ 7 revenue rollups found

Result: All 32 rollup fields confirmed present ✅
```

---

### **Example 2: Successful Documentation Session**

**User Opening:**
```
Generate documentation for cr950_projectses table using resa-docs-mcp.
```

**Claude Desktop Response:**
```
✅ Using resa-docs-mcp tool: generate_table_documentation

Table: cr950_projectses
Relationships found: 29 (12 parent lookups, 17 child tables)
Fields: 0 shown (known permissions issue)

Note: Display name shows as [object Object] - known cosmetic issue.

Generated documentation saved to:
Documentation/07_Application_Specs/Projects_Documentation.md

Documentation includes:
- Table metadata
- 29 relationship mappings
- CRUD code examples
- OData query patterns
```

---

## 🔄 VERSION HISTORY

| Date | Version | Changes |
|------|---------|---------|
| Nov 23, 2025 | 1.0 | Initial protocol created |
| | | Based on MCP verification session |
| | | Includes all known limitations |
| | | Example templates for common tasks |

---

**END OF PROTOCOL**

*Use this guide every time you start a new Claude Desktop session to ensure consistent, effective collaboration.*
