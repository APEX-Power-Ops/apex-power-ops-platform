# RESA Power Session Protocol

**Version:** 1.0  
**Last Updated:** December 2, 2025  
**Purpose:** Standard operating procedure for Claude instances working on this project

---

## 🚀 QUICK START - Read This First

### Starting a New Session

```
1. READ: C:\RESA_Power_Build\Sessions\CLAUDE_NOTES.md    ← Quick context from last Claude
2. READ: C:\RESA_Power_Build\Sessions\CURRENT_STATE.md   ← Project state
3. READ: C:\RESA_Power_Build\Sessions\HANDOFF.md         ← Tasks assigned to you
4. ASK: "What would you like to focus on today?" (if no specific handoff)
5. UPDATE: CLAUDE_NOTES.md and CURRENT_STATE.md when session ends
```

### Resuming After Interruption

```
1. READ: C:\RESA_Power_Build\Sessions\CLAUDE_NOTES.md
2. READ: C:\RESA_Power_Build\Sessions\CURRENT_STATE.md
3. LOCATE: "Last Action" and "Next Steps" sections
4. CONTINUE: From where we left off
```

---

## 📁 Session File Structure

```
C:\RESA_Power_Build\Sessions\
├── SESSION_PROTOCOL.md      ← You are here (how to use this system)
├── CLAUDE_NOTES.md          ← Quick context from last Claude instance (READ FIRST!)
├── CURRENT_STATE.md         ← Single source of truth for project state
├── HANDOFF.md               ← Tasks to pass between Claude instances
├── SESSION_LOG.md           ← Chronological history of all sessions
├── QUICK_REFERENCE.md       ← Schema names, API endpoints, common commands
├── Templates\               ← Reusable document templates
│   ├── AUDIT_TEMPLATE.md
│   ├── BUILD_SPEC_TEMPLATE.md
│   └── SESSION_SUMMARY_TEMPLATE.md
└── Archive\                 ← Completed session summaries
```

---

## 📋 CURRENT_STATE.md Structure

This is the **most important file**. Keep it updated. It should always reflect:

```markdown
# RESA Power Project - Current State

## Quick Context (Read in 30 seconds)
- One paragraph summary of where we are
- Current version/phase
- Active environment

## Active Work Items
| Priority | Item | Status | Owner | Notes |
|----------|------|--------|-------|-------|

## Last Session
- Date:
- Duration:
- Accomplishments:
- Blockers encountered:

## Next Steps (Priority Order)
1. 
2. 
3. 

## Environment Details
- Dataverse URL:
- Solution Version:
- MCP Servers Active:

## Key File Locations
- Schema docs:
- Build specs:
- Test data:
```

---

## 🔄 HANDOFF.md Structure

Use this to pass work between Claude instances (Web Claude ↔ VS Code Claude):

```markdown
# Active Handoffs

## TO: [Target Claude Instance]
### Task: [Clear task name]
**Priority:** P0/P1/P2
**Context:** [What they need to know]
**Deliverable:** [What success looks like]
**Files to reference:**
- 
**Files to create/update:**
- 

---

## FROM: [Source Claude Instance]
### Completed: [Task name]
**Result:** [What was done]
**Files created:**
- 
**Notes for next steps:**
```

---

## 📝 Session End Protocol

Before ending any session, ALWAYS:

1. **Update CURRENT_STATE.md** with:
   - What was accomplished
   - Current blockers
   - Clear next steps

2. **Update HANDOFF.md** if:
   - Work needs to continue in another instance
   - Tasks are waiting for user action
   - Dependencies exist between Claude instances

3. **Archive if major milestone**:
   - Copy session summary to `Archive\SESSION_YYYYMMDD_summary.md`
   - Keep CURRENT_STATE.md focused on active work

---

## 🏷️ Naming Conventions

### Files
- Session archives: `SESSION_YYYYMMDD_topic.md`
- Audit reports: `AUDIT_[subject]_YYYYMMDD.md`
- Build specs: `[TABLE]_BUILD_SPEC_vX.Y.md`

### Status Tags
- `🔴 BLOCKED` - Cannot proceed without action
- `🟡 IN PROGRESS` - Actively being worked
- `🟢 COMPLETE` - Done and verified
- `⚪ NOT STARTED` - In queue
- `🔵 WAITING` - Needs user input/decision

---

## 🔧 MCP Server Reference

### Available Servers
| Server | Purpose | Key Commands |
|--------|---------|--------------|
| filesystem | File operations | read_text_file, write_file, list_directory |
| resa-dataverse | Dataverse CRUD | query_dataverse, create_record, update_record |
| windows | Desktop automation | Powershell-Tool, State-Tool |

### Dataverse Entity Map (V2 Schema)
```javascript
{
  'projects': 'cr950_projects',
  'clients': 'cr950_clients', 
  'sites': 'cr950_sites',
  'scopes': 'cr950_scopes',
  'tasks': 'cr950_tasks',
  'apparatus': 'cr950_apparatuses',
  'scopelabordetails': 'cr950_scopelabordetails',
  'estimators': 'cr950_estimators',
  'locations': 'cr950_locations'
}
```

### Environment
- **Dataverse URL:** https://org7bdbc942.crm.dynamics.com
- **Publisher Prefix:** cr950_
- **Tenant ID:** 270d5723-4b30-4f3b-b9cb-6527be741b42

---

## 📚 Key Documentation Locations

| Topic | Location |
|-------|----------|
| System Overview | `Documentation\00_START_HERE\` |
| Table Schemas | `Documentation\05_Table_Documentation\` |
| Build Specs | `Documentation\02_Implementation\` |
| Progress Tracking | `Documentation\03_Progress_Tracking\` |
| Archived Docs | `Documentation\99_Archive\` |
| Solution Exports | `Solution_Exports\` |
| MCP Servers | `MCP_Servers\` |
| CSV Templates | `CSV_Templates\` |

---

## ⚡ Common Tasks Quick Reference

### Query Dataverse Table
```
Use resa-dataverse:query_dataverse
- entityName: "cr950_projects" (use V2 plural names)
- select: "field1,field2" (no $select= prefix)
- filter: "field eq value" (no $filter= prefix)
```

### Read Project File
```
Use filesystem:read_text_file
- path: Full path starting with C:\RESA_Power_Build\
```

### Run PowerShell Command
```
Use windows:Powershell-Tool
- command: PowerShell script/command
```

### Create Documentation
```
Use filesystem:write_file
- path: Appropriate location per naming conventions
- content: Full file content
```

---

## 🚨 Important Rules

1. **Always read CURRENT_STATE.md first** - Don't start work without context
2. **Always update CURRENT_STATE.md last** - Don't end without saving state
3. **Use V2 entity names** - cr950_projects NOT cr950_projectses
4. **Save to appropriate folders** - Follow the documentation structure
5. **Archive, don't delete** - Move old docs to 99_Archive
6. **One source of truth** - Don't duplicate state across files

---

*This protocol ensures continuity across sessions and Claude instances.*
