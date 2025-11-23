# VS CODE CLAUDE - MCP SERVER BUILD INSTRUCTIONS
## Immediate Action Items

**Date:** November 23, 2025  
**Priority:** Build 5 MCP servers in order  
**Timeline:** 6 weeks (Week 1 = Most Critical)

---

## 📋 QUICK START - DO THIS FIRST

### **Step 1: Read Master Spec (5 minutes)**
```
Location: C:\RESA_Power_Build\Documentation\06_Implementation_Guides\MCP_ALL_SERVERS_BUILD_SPEC.md

This file contains:
- Complete build instructions for all 5 servers
- Tool specifications with code examples
- Common structure and dependencies
- Testing protocols
- Environment configuration (org99cd6c6e.crm.dynamics.com)
```

### **Step 2: Verify Environment (2 minutes)**
```bash
# Confirm Dataverse credentials
Get-Content C:\RESA_Power_Build\RESA-Dev-MCP-Access.txt

# Should see:
# Environment URL: org99cd6c6e.crm.dynamics.com
# Application ID: 9df3350f-b3b4-47c4-97b5-499a8b02acc7
# Tenant ID: 270d5723-4b30-4f3b-b9cb-6527be741b42
```

### **Step 3: Check Existing Reference (3 minutes)**
```bash
# Examine existing working MCP server
code C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp\src\index.ts

# Copy the Dataverse authentication logic from here
# You'll reuse this in all 5 new servers
```

---

## 🎯 BUILD ORDER (MUST FOLLOW THIS SEQUENCE)

### **TIER 1 - CRITICAL (Weeks 1-2)**

#### **Week 1: resa-testing-mcp** ⭐ START HERE
```bash
cd C:\RESA_Power_Build\MCP_Servers
mkdir resa-testing-mcp
cd resa-testing-mcp
npm init -y
npm install @modelcontextprotocol/sdk axios @azure/identity @azure/msal-node lodash date-fns
npm install -D typescript @types/node ts-node
```

**Implement 4 Tools:**
1. `validate_rollup_fields` - Validate 32 rollup fields
2. `test_calculated_fields` - Test 30 calculated field formulas
3. `run_integration_tests` - End-to-end workflow tests
4. `generate_test_data` - Create test hierarchies

**Why Critical:** Jason needs this to validate 32 rollup fields he's about to create in Week 3-4.

**Success Criteria:**
- Can validate existing rollup field (cr950_total_apparatus_hours)
- Can generate test data (10 apparatus records)
- Runs in Claude Desktop

---

#### **Week 2: resa-docs-mcp**
```bash
cd C:\RESA_Power_Build\MCP_Servers
mkdir resa-docs-mcp
cd resa-docs-mcp
npm init -y
npm install @modelcontextprotocol/sdk axios @azure/identity @azure/msal-node handlebars markdown-it
npm install -D typescript @types/node ts-node
```

**Implement 4 Tools:**
1. `generate_table_documentation` - Auto-generate table docs
2. `generate_erd_diagram` - Create Mermaid ERDs
3. `generate_user_guide` - Role-based user guides
4. `generate_api_docs` - OpenAPI 3.0 specs

**Why Critical:** Jason needs documentation for pilot rollout (20+ users need training).

---

### **TIER 2 - PRE-PILOT (Weeks 5-6)**

#### **Week 5: resa-deploy-mcp**
5 tools for safe deployment automation

#### **Week 6: microsoft-graph-mcp**
6 tools for Microsoft 365 integration

---

### **TIER 3 - POST-PILOT**

#### **After Pilot: quickbooks-mcp**
4 tools for financial system integration

---

## 🔧 COMMON TEMPLATE FOR ALL SERVERS

### **Project Structure:**
```
server-name-mcp/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts          # MCP server entry point
│   ├── tools/            # Tool implementations
│   └── utils/            # Shared utilities
└── tests/
```

### **index.ts Template:**
```typescript
#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

// Import your tools
import { tool1 } from "./tools/tool1.js";
import { tool2 } from "./tools/tool2.js";

// Environment config
const DATAVERSE_URL = process.env.DATAVERSE_URL || "https://org99cd6c6e.crm.dynamics.com";
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID || "270d5723-4b30-4f3b-b9cb-6527be741b42";
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || "9df3350f-b3b4-47c4-97b5-499a8b02acc7";
const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET || "";

// Create server
const server = new Server({
  name: "server-name-mcp",
  version: "1.0.0",
}, {
  capabilities: { tools: {} }
});

// List tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "tool_name",
        description: "Tool description",
        inputSchema: {
          type: "object",
          properties: {
            param1: { type: "string", description: "Param description" }
          },
          required: ["param1"]
        }
      }
    ]
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  switch (request.params.name) {
    case "tool_name":
      const result = await tool1(request.params.arguments);
      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }]
      };
    default:
      throw new Error(`Unknown tool: ${request.params.name}`);
  }
});

// Start server
async function main() {
  console.error("Server Name MCP Server starting...");
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Server Name MCP Server running");
}

main().catch(console.error);
```

---

## 🔑 ENVIRONMENT CONFIGURATION (SAME FOR ALL)

**Use these exact credentials in ALL 5 servers:**

```typescript
const DATAVERSE_URL = "https://org99cd6c6e.crm.dynamics.com";
const AZURE_TENANT_ID = "270d5723-4b30-4f3b-b9cb-6527be741b42";
const AZURE_CLIENT_ID = "9df3350f-b3b4-47c4-97b5-499a8b02acc7";
const AZURE_CLIENT_SECRET = "REDACTED-AZURE-AD-CLIENT-SECRET-2026-05-27-1";
```

**Claude Desktop Config Template:**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["C:\\RESA_Power_Build\\MCP_Servers\\server-name-mcp\\build\\index.js"],
      "env": {
        "DATAVERSE_URL": "https://org99cd6c6e.crm.dynamics.com",
        "AZURE_TENANT_ID": "270d5723-4b30-4f3b-b9cb-6527be741b42",
        "AZURE_CLIENT_ID": "9df3350f-b3b4-47c4-97b5-499a8b02acc7",
        "AZURE_CLIENT_SECRET": "REDACTED-AZURE-AD-CLIENT-SECRET-2026-05-27-1",
        "ENVIRONMENT": "DEVELOPMENT"
      }
    }
  }
}
```

---

## ✅ TESTING CHECKLIST (FOR EACH SERVER)

After building each server:

```bash
# 1. Build
npm run build

# 2. Test standalone
node build/index.js
# Should output: "[Server Name] MCP Server running"

# 3. Add to Claude Desktop config
# Edit: %APPDATA%\Claude\claude_desktop_config.json

# 4. Restart Claude Desktop

# 5. Test in new chat
User: "List available MCP tools"
# Should see new server's tools

# 6. Test actual functionality
User: "Test [tool_name] against org99cd6c6e"
# Should work with real Dataverse data
```

---

## 📊 PROGRESS TRACKING

**Update this file as you go:**
```
C:\RESA_Power_Build\Documentation\06_Implementation_Guides\MCP_BUILD_PROGRESS.md
```

**Template:**
```markdown
# MCP Server Build Progress

## Week 1: resa-testing-mcp
- [ ] Project created (2025-11-25)
- [ ] Dependencies installed
- [ ] Tool 1: validate_rollup_fields ✅
- [ ] Tool 2: test_calculated_fields
- [ ] Tool 3: run_integration_tests
- [ ] Tool 4: generate_test_data
- [ ] Claude Desktop integration
- [ ] Tested against v1.4.0.0 data

## Week 2: resa-docs-mcp
- [ ] Project created
- [ ] Tool 1: generate_table_documentation
- [ ] Tool 2: generate_erd_diagram
- [ ] Tool 3: generate_user_guide
- [ ] Tool 4: generate_api_docs
- [ ] Generated docs for 14 tables

## Status: IN PROGRESS
## Current Focus: resa-testing-mcp Tool 1
## Next: Complete Tool 1, then Tool 2
```

---

## 🎯 CRITICAL SUCCESS FACTORS

### **Week 1 (resa-testing-mcp) MUST HAVE:**
1. ✅ validate_rollup_fields working
2. ✅ Can test against org99cd6c6e
3. ✅ Returns PASS/FAIL results
4. ✅ Tested with at least 2 existing rollup fields

**Why:** Jason creates 32 rollup fields in Week 3-4. Without this validation tool, he has no way to verify they work correctly.

### **Week 2 (resa-docs-mcp) MUST HAVE:**
1. ✅ generate_table_documentation working
2. ✅ Can generate docs for all 14 tables
3. ✅ Outputs clean Markdown format
4. ✅ Includes fields, relationships, examples

**Why:** Pilot needs training materials for 20+ users. Auto-generated docs save 20-30 hours of manual work.

---

## 🚨 CRITICAL WARNINGS

### **DO NOT:**
- ❌ Connect to production (if org04ad071f exists)
- ❌ Hardcode credentials in source files
- ❌ Skip testing before moving to next server
- ❌ Change the build order (must follow priority)

### **ALWAYS:**
- ✅ Use org99cd6c6e.crm.dynamics.com
- ✅ Test each tool individually
- ✅ Update progress tracker
- ✅ Copy Dataverse client from resa-dataverse-mcp

---

## 💡 TIPS FOR SUCCESS

### **Reuse Code:**
```bash
# Copy authentication from existing server
cp ../resa-dataverse-mcp/src/index.ts ./src/utils/dataverse-client.ts
# Then extract just the auth functions
```

### **Test Incrementally:**
```typescript
// Don't build all 4 tools at once
// Build and test one at a time:

// 1. Implement Tool 1
// 2. Test Tool 1
// 3. If works, implement Tool 2
// 4. Test Tool 2
// ... etc
```

### **Use Existing Patterns:**
```typescript
// Look at resa-dataverse-mcp for examples:
// - How to query Dataverse
// - How to handle errors
// - How to structure responses
```

---

## 📁 KEY REFERENCES

**Master Specification:**
`C:\RESA_Power_Build\Documentation\06_Implementation_Guides\MCP_ALL_SERVERS_BUILD_SPEC.md`

**Existing Working Server:**
`C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp\src\index.ts`

**Environment Config:**
`C:\RESA_Power_Build\RESA-Dev-MCP-Access.txt`

**Progress Tracking:**
`C:\RESA_Power_Build\Documentation\06_Implementation_Guides\MCP_BUILD_PROGRESS.md`

---

## 🎯 YOUR IMMEDIATE NEXT STEPS

1. **Read** MCP_ALL_SERVERS_BUILD_SPEC.md (10 minutes)
2. **Create** resa-testing-mcp project (5 minutes)
3. **Copy** Dataverse client from resa-dataverse-mcp (5 minutes)
4. **Implement** validate_rollup_fields tool (2-3 hours)
5. **Test** against org99cd6c6e (30 minutes)
6. **Update** progress tracker (5 minutes)
7. **Continue** with remaining 3 tools

**Expected Completion:** End of Week 1 (November 29, 2025)

---

## ✅ HANDOFF COMPLETE

VS Code Claude has:
- ✅ Complete build specification for all 5 servers
- ✅ Environment configuration (org99cd6c6e only)
- ✅ Code templates and examples
- ✅ Testing protocols
- ✅ Progress tracking system
- ✅ Clear priority order
- ✅ Success criteria defined

**Start with resa-testing-mcp Tool 1 (validate_rollup_fields).**

**This is the highest value tool - Jason needs it by Week 3!**

---

**Document:** VS_CLAUDE_HANDOFF.md  
**Created:** November 23, 2025  
**Status:** Ready for VS Code Claude to start building  
**First Task:** Build resa-testing-mcp (Week 1)

