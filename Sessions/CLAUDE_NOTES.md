# Claude Notes - Cross-Instance Communication

**Purpose:** Quick context notes from one Claude instance to the next  
**Rule:** Each session, read this first and update it before ending

---

## 📝 Latest Note

**From:** VS Code Claude (Claude Opus 4.5)  
**Date:** December 2, 2025, ~10:00 PM  
**Session Focus:** Revenue Architecture Rebuild

### What I Did
- Decided on Financial/Operations separation pattern (3 dedicated financial tables)
- Created ApparatusRevenue, ScopeFinancialSummary, ProjectFinancialSummary tables via API
- Added `cr950_completion_status` (Choice field) to Apparatus for reliable flow triggers
- Discovered API limitation: lookup fields can't be created via Web API (must use Power Apps UI)
- Created comprehensive session documentation (decisions log, build status, session summary)

### What I Learned
- Schema naming changed significantly from v1.5.x: `projectscope` → `scope`, EntitySetNames differ
- The old Revenue Recognition flow from v1.5.1.3 can be used as logic reference but NOT imported directly
- MCP server at `MCP_Servers/resa-dataverse-mcp/` is working well for queries and creates

### What's Blocking
- **7 lookup fields** must be added manually in Power Apps UI (API limitation)
- Can't build flows until lookups are established (flows need relationships)

### What You Should Know
- Jason chose separation pattern because "it keeps things simple" and allows role-based visibility
- The pattern was already proven in v1.5.x - we're re-implementing, not inventing
- v1.0.0.5 solution export is in `Solution_Exports/v1.0.0.5/` for schema review
- I created a `Sessions/` folder structure per your schema review suggestions

### Suggested Next Focus
1. Schema comparison (v1.0.0.5 vs v1.5.1.3) to find all gaps
2. Review session protocol improvements (this new folder structure)
3. Help Jason add lookups via Power Apps guidance if needed

---

## 📜 Previous Notes (Keep Last 5)

*No previous notes yet - this is the first entry*

---

## How to Use This File

### On Session Start
1. Read the "Latest Note" section
2. Note who wrote it and when
3. Use context to avoid asking questions that were already answered

### On Session End
1. Move current "Latest Note" to "Previous Notes"
2. Write new "Latest Note" with your session context
3. Be concise but include the "What You Should Know" insights
4. Commit to git with other session files

### What to Include
- **What I Did** - Actions taken, not just topics discussed
- **What I Learned** - Discoveries that save time for the next Claude
- **What's Blocking** - Issues that couldn't be resolved
- **What You Should Know** - Insights, user preferences, gotchas
- **Suggested Next Focus** - Your recommendation based on context

### What NOT to Include
- Detailed technical specs (put those in proper docs)
- Full conversation summaries (that's SESSION_LOG.md)
- Duplicate info from CURRENT_STATE.md

---

## Note Template

```markdown
**From:** [VS Code Claude / Claude Desktop / Web Claude]  
**Date:** [Date, Time]  
**Session Focus:** [2-4 word topic]

### What I Did
- 

### What I Learned
- 

### What's Blocking
- 

### What You Should Know
- 

### Suggested Next Focus
1. 
```

---

*This file bridges the gap between formal documentation and quick context sharing*
