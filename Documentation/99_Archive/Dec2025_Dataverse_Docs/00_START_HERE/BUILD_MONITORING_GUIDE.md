# MCP SERVER BUILD - MONITORING GUIDE
## Quick Reference for Jason

**Date:** November 23, 2025  
**Purpose:** Monitor VS Code Claude's progress building 5 MCP servers

---

## 📍 WHERE TO FIND EVERYTHING

**Build Specifications:**
- Master Spec: `Documentation\06_Implementation_Guides\MCP_ALL_SERVERS_BUILD_SPEC.md`
- VS Claude Instructions: `Documentation\00_START_HERE\VS_CLAUDE_HANDOFF.md`
- Progress Tracker: `Documentation\06_Implementation_Guides\MCP_BUILD_PROGRESS.md`

**Server Locations:**
```
C:\RESA_Power_Build\MCP_Servers\
├── resa-dataverse-mcp\      (existing - reference this)
├── resa-testing-mcp\        (build Week 1)
├── resa-docs-mcp\           (build Week 2)
├── resa-deploy-mcp\         (build Week 5)
├── microsoft-graph-mcp\     (build Week 6)
└── quickbooks-mcp\          (post-pilot)
```

---

## ✅ WEEK 1 CHECKLIST (resa-testing-mcp)

Monitor these milestones:

**Day 1-2: Project Setup**
- [ ] Folder created: `MCP_Servers\resa-testing-mcp\`
- [ ] `package.json` exists
- [ ] `tsconfig.json` configured
- [ ] Dependencies installed (check `node_modules\`)
- [ ] Folder structure created (src, src/tools, src/utils, tests)

**Day 2-3: Tool 1 (validate_rollup_fields)**
- [ ] File exists: `src\tools\validate-rollups.ts`
- [ ] Dataverse client copied from resa-dataverse-mcp
- [ ] Can query org99cd6c6e.crm.dynamics.com
- [ ] Returns PASS/FAIL results
- [ ] Tested with cr950_total_apparatus_hours

**Day 3-4: Tools 2-3**
- [ ] `src\tools\test-calculations.ts` implemented
- [ ] `src\tools\integration-tests.ts` implemented
- [ ] Can test calculated field formulas
- [ ] Can run end-to-end workflow tests

**Day 4-5: Tool 4 + Integration**
- [ ] `src\tools\generate-test-data.ts` implemented
- [ ] Can create test hierarchies (projects → apparatus)
- [ ] Built successfully (`npm run build`)
- [ ] Runs standalone: `node build\index.js`
- [ ] Added to Claude Desktop config
- [ ] Tested in Claude Desktop chat

**Success Criteria:**
```
User (in Claude Desktop): "Validate rollup fields on ProjectScope table"
Response: Should show PASS/FAIL for each field with variance details
```

---

## ✅ WEEK 2 CHECKLIST (resa-docs-mcp)

**Day 1: Project Setup**
- [ ] Folder created: `MCP_Servers\resa-docs-mcp\`
- [ ] Dependencies installed (includes handlebars, markdown-it)
- [ ] Folder structure created

**Day 2-3: Documentation Tools**
- [ ] generate_table_documentation working
- [ ] Can generate docs for cr950_projects
- [ ] Outputs clean Markdown
- [ ] Includes fields, relationships, examples

**Day 3-4: Diagram & Guide Tools**
- [ ] generate_erd_diagram working
- [ ] Produces valid Mermaid syntax
- [ ] generate_user_guide implemented
- [ ] Can create role-specific guides

**Day 5: API Docs + Integration**
- [ ] generate_api_docs working
- [ ] Built and tested
- [ ] Added to Claude Desktop
- [ ] Generated docs for all 14 tables

---

## 🔍 HOW TO CHECK PROGRESS

### **Check File Exists:**
```powershell
# From C:\RESA_Power_Build
Test-Path "MCP_Servers\resa-testing-mcp\src\tools\validate-rollups.ts"
# Should return: True
```

### **Check Build Status:**
```powershell
cd MCP_Servers\resa-testing-mcp
npm run build
# Should complete without errors
```

### **Check Server Runs:**
```powershell
node build\index.js
# Should output: "RESA Testing MCP Server running"
# Press Ctrl+C to stop
```

### **Check Claude Desktop Integration:**
```powershell
# Open Claude Desktop config
notepad %APPDATA%\Claude\claude_desktop_config.json

# Should have entry for resa-testing
# Restart Claude Desktop
# Open new chat
# Type: "List available MCP tools"
# Should see resa-testing tools
```

---

## 🚨 WARNING SIGNS

**VS Code Claude May Need Help If:**

❌ **TypeScript errors:**
```
Error: Cannot find module '@modelcontextprotocol/sdk'
Fix: npm install @modelcontextprotocol/sdk
```

❌ **Authentication fails:**
```
Error: 401 Unauthorized
Fix: Check AZURE_CLIENT_SECRET in code matches RESA-Dev-MCP-Access.txt
```

❌ **Can't query Dataverse:**
```
Error: 404 Not Found
Fix: Verify DATAVERSE_URL is https://org99cd6c6e.crm.dynamics.com
```

❌ **Claude Desktop doesn't see server:**
```
Fix: Check claude_desktop_config.json syntax (no trailing commas)
     Verify path uses double backslashes: C:\\RESA_Power_Build\\...
     Restart Claude Desktop completely
```

---

## 💬 QUESTIONS TO ASK VS CODE CLAUDE

### **Check Status:**
```
"What's your current progress on resa-testing-mcp?"
"Show me the project structure you've created"
"What tools have you completed?"
```

### **Test Functionality:**
```
"Run a test query against org99cd6c6e to verify connection"
"Show me the validate_rollup_fields implementation"
"Can you test this tool with sample data?"
```

### **Troubleshoot:**
```
"What errors are you encountering?"
"Show me the build output"
"Can you verify the Dataverse credentials?"
```

---

## 📊 EXPECTED TIMELINE

| Week | Server | Tools | Hours | Status |
|------|--------|-------|-------|--------|
| **1** | resa-testing-mcp | 4 | 20-30 | 🟡 IN PROGRESS |
| **2** | resa-docs-mcp | 4 | 15-20 | ⚪ PENDING |
| **5** | resa-deploy-mcp | 5 | 30-40 | ⚪ PENDING |
| **6** | microsoft-graph-mcp | 6 | 25-35 | ⚪ PENDING |
| **Post** | quickbooks-mcp | 4 | 35-50 | ⚪ PENDING |

**Legend:**
- 🟢 COMPLETE
- 🟡 IN PROGRESS
- 🔴 BLOCKED
- ⚪ PENDING

---

## 🎯 ACCEPTANCE TESTS

### **resa-testing-mcp is COMPLETE when:**
```
✅ Can validate rollup field: cr950_total_apparatus_hours
✅ Can test calculated field formula
✅ Can generate test data: 10 apparatus records
✅ Can run integration test: apparatus completion flow
✅ Returns structured JSON results
✅ Works in Claude Desktop chat
```

### **resa-docs-mcp is COMPLETE when:**
```
✅ Can generate table doc for cr950_projects
✅ Doc includes: fields, relationships, examples
✅ Can generate ERD diagram (Mermaid format)
✅ Can generate user guide for FieldTech role
✅ Can generate OpenAPI spec
✅ Works in Claude Desktop chat
```

---

## 📁 FILES TO REVIEW

**After Week 1, Check These Files:**

```
MCP_Servers\resa-testing-mcp\
├── package.json            (verify dependencies)
├── src\index.ts            (verify MCP server setup)
├── src\tools\
│   ├── validate-rollups.ts     (CRITICAL - review logic)
│   ├── test-calculations.ts
│   ├── integration-tests.ts
│   └── generate-test-data.ts
├── src\utils\
│   └── dataverse-client.ts     (verify auth works)
└── build\                  (compiled output)
    └── index.js
```

**Key Things to Verify:**
1. Uses org99cd6c6e.crm.dynamics.com (NOT old environments)
2. Credentials match RESA-Dev-MCP-Access.txt
3. Error handling present (try-catch blocks)
4. Returns structured results (not just raw data)
5. TypeScript compiles without errors

---

## 🔄 DAILY CHECK-IN QUESTIONS

**End of Each Day, Ask:**

1. "What did you complete today?"
2. "What's blocking you?"
3. "Can you demonstrate the tool working?"
4. "What's next for tomorrow?"
5. "Update the progress tracker"

**Example:**
```
You: "Show me progress on resa-testing-mcp"

VS Claude: "Today I completed:
✅ Project structure created
✅ Dependencies installed  
✅ Dataverse client copied and adapted
✅ Tool 1 (validate_rollup_fields) 60% complete
   - Can query Dataverse ✅
   - Can fetch rollup metadata ✅
   - Manual calculation logic - IN PROGRESS

Next: Finish manual calculation, test with real data"
```

---

## ✅ YOU'RE READY WHEN

**Week 1 Complete:**
- ✅ resa-testing-mcp validates your rollup fields
- ✅ You can test against org99cd6c6e in Claude Desktop
- ✅ Ready to create 32 rollup fields in Week 3-4

**Week 2 Complete:**
- ✅ resa-docs-mcp generates documentation for 14 tables
- ✅ Auto-generated training materials ready
- ✅ Documentation exported to markdown files

**Both Tier 1 Complete:**
- ✅ Can build v1.5.0.0 with confidence
- ✅ Can validate every change automatically
- ✅ Professional documentation for pilot
- ✅ Ready for Week 3-4 rollup field creation

---

## 📞 QUICK COMMANDS

**Check Progress:**
```powershell
dir MCP_Servers\resa-testing-mcp\src\tools\
npm run build
node build\index.js
```

**Open in VS Code:**
```powershell
code MCP_Servers\resa-testing-mcp\
```

**View Progress:**
```powershell
notepad Documentation\06_Implementation_Guides\MCP_BUILD_PROGRESS.md
```

---

**Keep this document open while VS Code Claude builds.**  
**Update the status as milestones are reached.**  
**You'll know immediately if something is blocked or needs attention.**

---

**Document:** BUILD_MONITORING_GUIDE.md  
**Created:** November 23, 2025  
**Purpose:** Monitor VS Code Claude's MCP server build progress  
**Status:** Ready to use

