# Claude Desktop Project Instructions

**Purpose:** Paste this into your Claude Desktop project's custom instructions  
**Last Updated:** December 2, 2025

---

## Recommended Project Instructions

Copy and paste the content below into your Claude Desktop project instructions:

```
# RESA Power Project Tracker - Session Instructions

## Session Start Protocol
ALWAYS start every session by reading the current state file:
1. Use filesystem:read_text_file to read: C:\RESA_Power_Build\Sessions\CURRENT_STATE.md
2. Check C:\RESA_Power_Build\Sessions\HANDOFF.md for any assigned tasks
3. Reference C:\RESA_Power_Build\Sessions\SESSION_PROTOCOL.md for procedures

## Session End Protocol  
ALWAYS before ending a session:
1. Update C:\RESA_Power_Build\Sessions\CURRENT_STATE.md with:
   - What was accomplished
   - Current blockers
   - Next steps
2. Update HANDOFF.md if passing work to another Claude instance
3. Add entry to SESSION_LOG.md

## Environment
- Dataverse: https://org7bdbc942.crm.dynamics.com
- Publisher Prefix: cr950_
- Schema Version: V2 (use cr950_projects NOT cr950_projectses)

## Key Directories
- Sessions: C:\RESA_Power_Build\Sessions\
- Documentation: C:\RESA_Power_Build\Documentation\
- MCP Servers: C:\RESA_Power_Build\MCP_Servers\
- Solution Exports: C:\RESA_Power_Build\Solution_Exports\

## V2 Entity Names (Use These)
- cr950_projects (not projectses)
- cr950_scopes (not projectscopes)  
- cr950_scopelabordetails (not scopelabordetailses)
- cr950_apparatuses
- cr950_tasks
- cr950_clients
- cr950_sites
- cr950_estimators
- cr950_locations

## File Naming
- Audits: AUDIT_[subject]_YYYYMMDD.md
- Build Specs: [TABLE]_BUILD_SPEC_vX.Y.md
- Session Archives: SESSION_YYYYMMDD_topic.md

## Status Tags
- 🔴 BLOCKED - Cannot proceed
- 🟡 IN PROGRESS - Actively working
- 🟢 COMPLETE - Done and verified
- ⚪ NOT STARTED - In queue
- 🔵 WAITING - Needs input

## Important
- Archive, don't delete old documents (use Documentation\99_Archive\)
- One source of truth - don't duplicate state across files
- Always verify relationships exist before creating child records
```

---

## Additional Notes

### For VS Code Claude (Cursor/Windsurf)
Add to your workspace settings or .cursorrules:
- Focus on code generation and implementation
- Reference build specs in Documentation\02_Implementation\
- Use Templates folder for consistent document structure

### For Web Claude
- Better for documentation, planning, and audits
- Can handle longer context for comprehensive analysis
- Good for creating handoffs and session summaries

---

## File System Access

Ensure these directories are accessible to Claude:
- `C:\RESA_Power_Build` (entire project folder)
- `C:\Users\jjswe\Projects` (if other projects referenced)

---

*Instructions file for reference - copy relevant sections to Claude Desktop*
