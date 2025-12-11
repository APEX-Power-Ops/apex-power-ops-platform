# RESA Power - Session Startup Prompt

Copy and paste this into a new Claude chat to resume work:

---

```
RESA Power Project - Resume Session

Workspace: C:\RESA_Power_Build\

1. Read the state file first:
   C:\RESA_Power_Build\.claude\STATE.md

2. Confirm what you understand about current phase and next actions.

3. Then we'll continue from where we left off.
```

---

## Even Shorter Version

```
Read C:\RESA_Power_Build\.claude\STATE.md and continue RESA Power project.
```

---

## If Claude Seems Lost

```
RESA Power project workspace is at C:\RESA_Power_Build\

Key files:
- .claude/STATE.md - Current status (read this)
- .claude/SESSION_PROTOCOL.md - How to work with me
- spec/ - Specification documents
- Supabase/schema/ - SQL files

Read STATE.md and tell me what phase we're in.
```

---

## 🔥 CURRENT PRIORITY TASK: Schema & Documentation Audit

**Added**: Dec 11, 2025

```
## TASK: Schema & Documentation Audit

I need you to audit the project documentation against actual Supabase state.

### Step 1: Query Supabase
Use mcp_supabase_list_tables to get all tables with row counts.

### Step 2: Verify These Documents Match Reality
1. Supabase/SCHEMA_REFERENCE.md - Should show 34 tables
2. PROJECT_STATUS.md - Check table counts accurate
3. .claude/COORDINATION.md - Verify session summaries
4. PROJECT_OVERVIEW.md - Architecture still valid?

### Step 3: Find Discrepancies
- Compare actual tables vs documented tables
- Check row counts (resource linking tables are empty - is that noted?)
- Any features deployed but not documented?

### Step 4: Find NETA JSON Files
We need to import data into empty tables:
- neta_procedures (0 rows)
- neta_test_items (0 rows)

Look in:
- Reference_Files/
- Documentation/04_Data_Migration/
- Any *.json files

### Step 5: Fix and Report
- Update docs with correct table counts
- Note any discrepancies found
- List NETA file locations
- Add findings to COORDINATION.md

### Known State:
- 34 tables verified in Supabase
- Resource linking tables EMPTY (0 rows): neta_procedures, neta_test_items, sops, safety_documents, datasheets, apparatus_type_resources
- Core tables POPULATED: projects, scopes, tasks, apparatus (LASNAP16 test data)
```
