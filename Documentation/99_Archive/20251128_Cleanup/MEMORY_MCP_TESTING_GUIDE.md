# MEMORY MCP TESTING GUIDE
## How to Test and Verify Memory MCP in Fresh Chat Sessions

**Purpose**: Step-by-step guide to test Memory MCP availability and store project facts  
**Created**: November 19, 2025  
**Status**: Ready for next fresh session

---

## 🎯 QUICK TEST (30 Seconds)

### **When Starting a Fresh Chat Session**:

**Step 1: Simple Test Query**
```
Ask: "Can you create a memory entity for this project?"
```

**Expected Results**:

✅ **If Memory MCP is Available**:
- AI will respond showing it has memory tools available
- May ask what you want to store
- Tools like `create_entities`, `create_relations`, `search_nodes` will be accessible

❌ **If Memory MCP is NOT Available**:
- AI will explain Memory MCP tools are not currently loaded
- This is expected and normal for sessions where MCP didn't initialize
- File-based documentation provides full continuity (no impact on work)

---

## 📋 FULL MEMORY MCP TEST PROTOCOL

### **Test 1: Check Tool Availability**

**What to Ask**:
```
"What memory tools do you have available?"
```

**Expected Response** (if loaded):
- `create_entities` - Store facts as memory entities
- `create_relations` - Create relationships between stored facts
- `search_nodes` - Search stored memories
- `open_nodes` - Retrieve specific memory by ID
- `delete_entities` - Remove outdated memories

---

### **Test 2: Store Simple Test Entity**

**What to Ask**:
```
"Create a test memory entity with the name 'RESA Test' and observation 'Testing Memory MCP on Nov 19, 2025'"
```

**Expected Result** (if loaded):
- AI creates entity successfully
- Returns entity ID
- Confirms storage

---

### **Test 3: Retrieve Stored Memory**

**What to Ask**:
```
"Search for memories related to 'RESA Test'"
```

**Expected Result** (if loaded):
- Finds the test entity you just created
- Shows the observation
- Confirms memory persistence

---

### **Test 4: Clean Up Test**

**What to Ask**:
```
"Delete the test memory entity we just created"
```

**Expected Result** (if loaded):
- Entity deleted successfully
- Confirms removal

---

## ✅ IF MEMORY MCP IS AVAILABLE

### **Immediately Execute Project Storage**:

```
Store these facts to Memory MCP:

1. Project: RESA Power Project Tracker, Dataverse v1.3.0.4, org99cd6c6e.crm.dynamics.com (RESA-Dev Sandbox)
2. Repository: https://github.com/jasonlswenson-sys/RESA-Power-Project-Management (branch: clean-main)
3. Technical: 8 tables, 137+ fields, 30 formulas, 9 choice fields, 1 Power Automate flow
4. Tables: BusinessUnit, Projects, ProjectScope, Tasks, Apparatus, ApparatusRevenue, ScopeLaborDetail, ApparatusTypeMaster
5. Critical: BusinessUnit = multi-location (Phoenix/Vegas/Denver/San Diego), NOT unused despite 0 records
6. Status: v1.3.0.4 production ready, auditing enabled Nov 19, clean slate environment (safe for changes)
7. Ready to Implement: Date Tracking (18 rollup fields, 2.5-3 hrs, HIGH value) - spec complete
8. In Planning: Revenue Rollups (needs KPI requirements), Master Build Spec completion (30 min)
9. Key Docs: PROJECT_STATUS_TRACKER.md (navigation), MASTER_BUILD_SPECIFICATION.md v2.0, SESSION_RESUME_CHECKLIST.md
10. Latest Session: Documentation alignment Nov 19 - corrected table names (Location→BusinessUnit, Scope_Financial_Config→ScopeLaborDetail)
```

### **Verification**:

After storage, ask:
```
"Search for RESA Power Project Tracker facts"
```

Should return all 10 facts stored above.

---

## ❌ IF MEMORY MCP IS NOT AVAILABLE

### **This is NORMAL and OKAY**

**What This Means**:
- Memory MCP server is running (checked via Task Manager)
- Configuration exists in `Documentation/claude_desktop_config.json`
- MCP only loads for NEW chat sessions (not mid-session)

**Your Continuity is Still Protected**:
1. ✅ **Git Repository**: All work committed to https://github.com/jasonlswenson-sys/RESA-Power-Project-Management
2. ✅ **Session Summaries**: In `Documentation/03_Progress_Tracking/`
3. ✅ **Status Tracker**: `Documentation/00_START_HERE/PROJECT_STATUS_TRACKER.md`
4. ✅ **Resume Checklist**: `Documentation/00_START_HERE/SESSION_RESUME_CHECKLIST.md`

**Next Steps**:
- Continue work using file-based documentation
- Try Memory MCP again in next fresh chat
- No impact on project continuity

---

## 🔄 WHEN TO TEST AGAIN

### **Trigger Points**:

1. **Next Fresh Chat Session** (Recommended)
   - Close current Claude Desktop
   - Reopen Claude Desktop
   - Start NEW chat
   - Run quick test

2. **After MCP Configuration Changes**
   - If you edit `claude_desktop_config.json`
   - Restart Claude Desktop
   - Start fresh chat
   - Test availability

3. **After System Restart**
   - Memory MCP server auto-starts via Windows shortcut
   - Verify in Task Manager: `memory-mcp.exe` running
   - Start fresh Claude chat
   - Test availability

---

## 📊 MEMORY MCP vs FILE-BASED DOCUMENTATION

### **When to Use Memory MCP**:
- ✅ Quick facts that need to survive session restart
- ✅ Critical "never forget" information
- ✅ Project identity and key decisions
- ✅ Supplement to documentation (not replacement)

### **When to Use File-Based Documentation** (Primary System):
- ✅ Detailed technical specifications
- ✅ Session work logs and progress tracking
- ✅ Implementation guides and checklists
- ✅ Version control and change history
- ✅ Shareable with team members
- ✅ Portable across AI systems
- ✅ Reviewable by humans

**Verdict**: 
- Memory MCP = Nice to have (convenience)
- File Documentation = Must have (reliability)

---

## 🛠️ TROUBLESHOOTING

### **Problem: "Memory MCP never available, even in fresh chats"**

**Check 1: Is Server Running?**
```powershell
Get-Process | Where-Object { $_.ProcessName -like "*node*" }
```

Expected: Multiple `node.exe` processes (MCP servers run via Node.js/npx)

**Check 2: Is Config File Correct?**
```powershell
Get-Content "C:\Users\jjswe\AppData\Roaming\Claude\claude_desktop_config.json"
```

Should show:
```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory"
      ]
    }
  }
}
```

**Check 3: Restart Claude Desktop**
1. Close ALL Claude Desktop windows
2. Wait 10 seconds
3. Reopen Claude Desktop
4. Start FRESH chat (not continuing old chat)
5. Test again

---

### **Problem: "I stored memories but can't retrieve them"**

**Solution 1: Verify Storage**
```
"List all memory entities you have stored"
```

**Solution 2: Search by Project Name**
```
"Search for memories containing 'RESA Power'"
```

**Solution 3: Check Memory Location**
- Memories stored by MCP server (location managed automatically)
- Data persists across Claude Desktop sessions

---

### **Problem: "Memory MCP worked before, stopped working now"**

**Likely Causes**:
1. Continuing old chat (not fresh) - Memory tools only in NEW chats
2. Server crashed - Check Task Manager, restart if needed
3. Config file corrupted - Verify JSON syntax

**Solution**:
1. Close Claude Desktop completely
2. Verify Node.js is installed: `node --version`
3. Check that npx is available: `npx --version`
4. Reopen Claude Desktop (will auto-start MCP servers via npx)
5. Start FRESH chat (critical!)
6. Test availability

---

## ✅ SUCCESS CRITERIA

**Memory MCP is Working When**:
- ✅ Fresh chat shows memory tools available
- ✅ Can create test entity successfully
- ✅ Can retrieve stored entities via search
- ✅ Project facts persist across chat sessions
- ✅ Can update/delete entities as needed

**Project Continuity is Protected When** (with or without Memory MCP):
- ✅ All work committed to Git repository
- ✅ Session summaries created for each major session
- ✅ PROJECT_STATUS_TRACKER.md kept current
- ✅ SESSION_RESUME_CHECKLIST.md followed at session start
- ✅ Key documents updated with decisions/changes

---

## 📚 REFERENCE DOCUMENTS

**If Memory MCP Unavailable**:
1. **Start Here**: `SESSION_RESUME_CHECKLIST.md`
2. **Current Status**: `PROJECT_STATUS_TRACKER.md`
3. **Latest Work**: Most recent file in `03_Progress_Tracking/`
4. **System Design**: `MASTER_BUILD_SPECIFICATION.md`

**Memory MCP Configuration**:
- Config: `Documentation/claude_desktop_config.json` (copy of actual config at `%APPDATA%\Claude\claude_desktop_config.json`)
- Server: Runs via `npx @modelcontextprotocol/server-memory` (auto-downloaded)
- Startup: Automatic when Claude Desktop starts (no separate startup needed)

---

## 🎯 QUICK REFERENCE

**Test Command** (copy-paste in fresh chat):
```
Can you create a memory entity for this project?
```

**Storage Command** (if available):
```
Store these facts to Memory MCP:

1. Project: RESA Power Project Tracker, Dataverse v1.3.0.4, org99cd6c6e.crm.dynamics.com (RESA-Dev Sandbox)
2. Repository: https://github.com/jasonlswenson-sys/RESA-Power-Project-Management (branch: clean-main)
3. Technical: 8 tables, 137+ fields, 30 formulas, 9 choice fields, 1 Power Automate flow
4. Tables: BusinessUnit, Projects, ProjectScope, Tasks, Apparatus, ApparatusRevenue, ScopeLaborDetail, ApparatusTypeMaster
5. Critical: BusinessUnit = multi-location (Phoenix/Vegas/Denver/San Diego), NOT unused despite 0 records
6. Status: v1.3.0.4 production ready, auditing enabled Nov 19, clean slate environment (safe for changes)
7. Ready to Implement: Date Tracking (18 rollup fields, 2.5-3 hrs, HIGH value) - spec complete
8. In Planning: Revenue Rollups (needs KPI requirements), Master Build Spec completion (30 min)
9. Key Docs: PROJECT_STATUS_TRACKER.md (navigation), MASTER_BUILD_SPECIFICATION.md v2.0, SESSION_RESUME_CHECKLIST.md
10. Latest Session: Documentation alignment Nov 19 - corrected table names (Location→BusinessUnit, Scope_Financial_Config→ScopeLaborDetail)
```

**Retrieval Command**:
```
Search for RESA Power Project Tracker facts
```

---

**END OF TESTING GUIDE**

*Use this guide at the start of fresh chat sessions to verify Memory MCP availability.*
