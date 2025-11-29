# MCP SERVER TROUBLESHOOTING GUIDE
## Fixing resa-docs and resa-dataverse-dev

**Created:** November 23, 2025  
**Purpose:** Step-by-step fixes for 2 partially operational MCP servers  
**Estimated Time:** 1.5-2 hours total  
**Priority:** MEDIUM (not blocking critical path)

---

## 🎯 SERVERS REQUIRING FIXES

| Server | Issue | Time | Priority |
|--------|-------|------|----------|
| **resa-docs** | Missing template files | 1 hour | HIGH |
| **resa-dataverse-dev** | Query 400 error | 30 min | MEDIUM |

---

# 1️⃣ FIX: resa-docs-mcp (Missing Templates)

## Problem Summary

**Error:**
```
ENOENT: no such file or directory
Path: C:\RESA_Power_Build\MCP_Servers\resa-docs-mcp\build\templates\table-documentation.hbs
```

**Root Cause:** TypeScript compiler doesn't copy non-.ts files (like .hbs templates) to build directory

**Impact:** Cannot generate documentation until templates exist in build folder

---

## Solution Steps

### **Step 1: Verify Current State (2 minutes)**

```powershell
cd C:\RESA_Power_Build\MCP_Servers\resa-docs-mcp

# Check if templates folder exists in build
dir build\templates

# Check if templates exist in source
dir src\templates
```

---

### **Step 2: Update Build Script (5 minutes)**

**✅ COMPLETED - Build script already updated**

The `package.json` has been updated to automatically copy templates during build:

```json
"scripts": {
  "prebuild": "node -e \"require('fs').rmSync('build', {recursive: true, force: true})\"",
  "build": "tsc && node -e \"require('fs').cpSync('src/templates', 'build/templates', {recursive: true})\"",
  "start": "node build/index.js",
  "dev": "npm run build && npm start"
}
```

**What this does:**
1. **prebuild**: Cleans the build directory before compiling
2. **build**: Runs TypeScript compiler AND copies templates from src to build
3. Templates are now automatically included in every build

---

### **Step 3: Rebuild the Server (2 minutes)**

### **Step 3: Rebuild the Server (2 minutes)**

```powershell
cd C:\RESA_Power_Build\MCP_Servers\resa-docs-mcp

# Rebuild with new build script
npm run build
```

**✅ COMPLETED - Server rebuilt successfully**

The templates directory is now created and populated automatically:
- `build/templates/table-documentation.hbs` ✅

---

### **Step 4: Verify Templates Exist (1 minute)**

```powershell
# Check templates were copied
dir build\templates

# Should show:
# table-documentation.hbs
```

---

### **Step 5: Test in Claude Desktop (5 minutes)**

```handlebars
# {{displayName}}

**Logical Name:** `{{logicalName}}`  
**Schema Name:** `{{schemaName}}`  
**Primary Key:** `{{primaryIdAttribute}}`  
**Created:** {{createdOn}}  
**Type:** {{entitySetName}}

---

## 📋 Description

{{#if description}}
{{description}}
{{else}}
_No description provided_
{{/if}}

---

## 📊 Fields ({{fieldCount}})

| Display Name | Logical Name | Type | Required | Description |
|--------------|--------------|------|----------|-------------|
{{#each fields}}
| {{this.displayName}} | `{{this.logicalName}}` | {{this.type}} | {{#if this.required}}✅ Yes{{else}}No{{/if}} | {{#if this.description}}{{this.description}}{{else}}_No description_{{/if}} |
{{/each}}

---

## 🔗 Relationships ({{relationshipCount}})

{{#if relationships}}
| Name | Type | Related Table | Description |
|------|------|---------------|-------------|
{{#each relationships}}
| {{this.name}} | {{this.type}} | {{this.relatedTable}} | {{#if this.description}}{{this.description}}{{else}}_No description_{{/if}} |
{{/each}}
{{else}}
_No relationships defined_
{{/if}}

---

## 📝 Business Rules

{{#if businessRules}}
{{#each businessRules}}
### {{this.name}}
- **Scope:** {{this.scope}}
- **Description:** {{this.description}}
{{/each}}
{{else}}
_No business rules configured_
{{/if}}

---

## 💻 Usage Examples

### Query Records

\`\`\`javascript
// Query {{logicalName}} records
const records = await queryDataverse(
  "{{logicalCollectionName}}",
  "$select={{primaryIdAttribute}},{{sampleFields}}",
  "$filter=statecode eq 0",
  10
);

console.log(\`Found \${records.length} records\`);
\`\`\`

### Create Record

\`\`\`javascript
// Create new {{logicalName}} record
const newRecord = await createRecord(
  "{{logicalCollectionName}}",
  {
    {{#each sampleCreateFields}}
    "{{this.logicalName}}": "{{this.sampleValue}}"{{#unless @last}},{{/unless}}
    {{/each}}
  }
);

console.log(\`Created record: \${newRecord.id}\`);
\`\`\`

### Update Record

\`\`\`javascript
// Update existing {{logicalName}} record
await updateRecord(
  "{{logicalCollectionName}}",
  recordId,
  {
    {{#each sampleUpdateFields}}
    "{{this.logicalName}}": "{{this.sampleValue}}"{{#unless @last}},{{/unless}}
    {{/each}}
  }
);
\`\`\`

---

## 📚 Related Tables

{{#if relatedTables}}
{{#each relatedTables}}
- [{{this.displayName}}](./{{this.logicalName}}.md)
{{/each}}
{{else}}
_No related tables_
{{/if}}

---

**Generated:** {{timestamp}}  
**Generator:** RESA Docs MCP Server v1.0  
**Environment:** org99cd6c6e.crm.dynamics.com
```

**Save and close Notepad**

---

#### **File 2: erd-diagram.hbs**

```bash
notepad build\templates\erd-diagram.hbs
```

**Paste this content:**

```handlebars
# Entity Relationship Diagram
## {{title}}

**Generated:** {{timestamp}}  
**Tables:** {{tableCount}}  
**Relationships:** {{relationshipCount}}

---

## Mermaid Diagram

\`\`\`mermaid
erDiagram
{{#each relationships}}
    {{this.fromTable}} {{this.relationshipType}} {{this.toTable}} : "{{this.name}}"
{{/each}}

{{#each tables}}
    {{this.logicalName}} {
        {{#each this.keyFields}}
        {{this.type}} {{this.logicalName}} {{#if this.isPrimaryKey}}"PK"{{/if}}
        {{/each}}
    }
{{/each}}
\`\`\`

---

## Tables Included

{{#each tables}}
### {{this.displayName}} (`{{this.logicalName}}`)

{{#if this.description}}
{{this.description}}
{{/if}}

**Key Fields:**
{{#each this.keyFields}}
- `{{this.logicalName}}` ({{this.type}}){{#if this.isPrimaryKey}} - Primary Key{{/if}}
{{/each}}

---
{{/each}}

## Relationships

{{#each relationships}}
### {{this.name}}

- **From:** {{this.fromTable}} ({{this.fromField}})
- **To:** {{this.toTable}} ({{this.toField}})
- **Type:** {{this.relationshipType}}
- **Cardinality:** {{this.cardinality}}

---
{{/each}}
```

**Save and close**

---

#### **File 3: user-guide.hbs**

```bash
notepad build\templates\user-guide.hbs
```

**Paste this content:**

```handlebars
# {{role}} User Guide
## RESA Power Project Tracker

**Version:** 1.0  
**Generated:** {{timestamp}}  
**For Role:** {{role}}

---

## 🎯 Overview

This guide provides step-by-step instructions for {{role}} users of the RESA Power Project Tracker system.

### Your Responsibilities

{{#each responsibilities}}
- {{this}}
{{/each}}

### Tables You'll Use

{{#each tables}}
- **{{this.displayName}}**: {{this.description}}
{{/each}}

---

## 📱 Getting Started

### 1. Accessing the System

1. Open your web browser
2. Navigate to: https://make.powerapps.com
3. Sign in with your RESA credentials
4. Select the **RESA-Dev** environment

### 2. Opening the Project Tracker

1. Click **Apps** in the left navigation
2. Find **RESA Power Project Tracker**
3. Click to open the app

---

## 📋 Common Tasks

{{#each commonTasks}}
### {{this.title}}

**Frequency:** {{this.frequency}}

#### Steps:

{{#each this.steps}}
{{@index}}. {{this}}
{{/each}}

{{#if this.notes}}
**Notes:**
{{#each this.notes}}
- {{this}}
{{/each}}
{{/if}}

---
{{/each}}

## 🔍 Finding Information

### Search for Projects

1. Click **Projects** in the navigation
2. Use the search box to find specific projects
3. Use filters to narrow results:
   - Status
   - Location
   - Date Range

### View Project Details

1. Click on a project name
2. Review the following tabs:
   - **Details**: Basic project information
   - **Scopes**: Work breakdown structure
   - **Tasks**: Task assignments
   - **Apparatus**: Equipment testing status

---

## ✅ Best Practices

{{#each bestPractices}}
### {{this.title}}

{{this.description}}

**Why it matters:** {{this.why}}

{{#if this.tips}}
**Tips:**
{{#each this.tips}}
- {{this}}
{{/each}}
{{/if}}

---
{{/each}}

## 🆘 Troubleshooting

{{#each troubleshooting}}
### {{this.problem}}

**Solution:** {{this.solution}}

{{#if this.preventingFuture}}
**To prevent this in the future:** {{this.preventingFuture}}
{{/if}}

---
{{/each}}

## 📞 Getting Help

**IT Support:**
- Email: support@resapower.com
- Phone: (555) 123-4567
- Hours: Monday-Friday, 8 AM - 5 PM MST

**Questions about this guide?**
Contact your Project Manager or Location Manager.

---

**Document Version:** 1.0  
**Last Updated:** {{timestamp}}  
**Generated by:** RESA Docs MCP Server
```

**Save and close**

---

#### **File 4: api-docs.hbs**

```bash
notepad build\templates\api-docs.hbs
```

**Paste this content:**

```handlebars
# RESA Power Project Tracker API Documentation

**Version:** {{version}}  
**Generated:** {{timestamp}}  
**Base URL:** {{baseUrl}}  
**Format:** OpenAPI 3.0

---

## Authentication

All API requests require OAuth 2.0 authentication with Azure AD.

\`\`\`
Authorization: Bearer {access_token}
\`\`\`

**Token Endpoint:** https://login.microsoftonline.com/{{tenantId}}/oauth2/v2.0/token

---

## Available Endpoints

{{#each endpoints}}
### {{this.method}} {{this.path}}

**Description:** {{this.description}}

**Request:**

{{#if this.parameters}}
**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
{{#each this.parameters}}
| {{this.name}} | {{this.type}} | {{#if this.required}}Yes{{else}}No{{/if}} | {{this.description}} |
{{/each}}
{{/if}}

{{#if this.requestBody}}
**Request Body:**
\`\`\`json
{{json this.requestBody}}
\`\`\`
{{/if}}

**Response:**

\`\`\`json
{{json this.responseExample}}
\`\`\`

**Status Codes:**
{{#each this.statusCodes}}
- **{{this.code}}**: {{this.description}}
{{/each}}

---
{{/each}}

## Examples

{{#each examples}}
### {{this.title}}

{{this.description}}

\`\`\`http
{{this.method}} {{this.url}}
{{#each this.headers}}
{{this.name}}: {{this.value}}
{{/each}}

{{#if this.body}}
{{this.body}}
{{/if}}
\`\`\`

**Response:**

\`\`\`json
{{json this.response}}
\`\`\`

---
{{/each}}

## Error Handling

All errors follow this format:

\`\`\`json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  }
}
\`\`\`

**Common Error Codes:**

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

---

**Generated by:** RESA Docs MCP Server  
**Documentation Version:** 1.0
```

**Save and close**

---

### **Step 4: Verify Templates Created (1 minute)**

```bash
cd C:\RESA_Power_Build\MCP_Servers\resa-docs-mcp

dir build\templates

# Should show 4 files:
# - table-documentation.hbs
# - erd-diagram.hbs
# - user-guide.hbs
# - api-docs.hbs
```

---

### **Step 5: Rebuild MCP Server (2 minutes)**

```bash
# Rebuild to ensure templates are included
npm run build

# Should complete without errors
```

---

### **Step 6: Test in Claude Desktop (5 minutes)**

1. **Restart Claude Desktop** (important!)
2. Open new chat
3. Test command:

```
Generate table documentation for cr950_projects table
```

**Expected Result:**
- Should return formatted Markdown documentation
- No "ENOENT" error
- Includes fields, relationships, examples

---

### **Step 7: Verify All Tools (5 minutes)**

Test each documentation tool:

```
1. "Generate table documentation for cr950_projectscope"
2. "Generate ERD diagram for RESA Power tables"
3. "Generate user guide for FieldTech role"
4. "Generate API documentation"
```

Each should return formatted documentation without errors.

---

## ✅ Success Criteria - resa-docs

- [ ] Templates folder exists: `build\templates\`
- [ ] 4 template files created (.hbs files)
- [ ] `npm run build` completes without errors
- [ ] generate_table_documentation returns formatted docs
- [ ] No "ENOENT" errors
- [ ] Can generate docs for all 14 tables

**Time to fix:** ~1 hour  
**Difficulty:** EASY (just creating text files)

---

# 2️⃣ FIX: resa-dataverse-dev (Query 400 Error)

## Problem Summary

**Error:**
```
Request failed with status code 400
Query: cr950_projectses table
```

**Root Cause:** OData query syntax issue or incorrect table name

**Impact:** Cannot query Dataverse tables

---

## Solution Steps

### **Step 1: Verify Table Names (5 minutes)**

The issue is likely the table name format. Dataverse has specific naming conventions.

```bash
# Open Claude Desktop (or continue in this chat)
# Test with resa-deploy to get actual table names

"List all solutions and show me the RESAPowerProjectTracker solution details"
```

**Common Issue:** Entity names vs. Entity Set Names
- Entity Name: `cr950_projects`
- Entity Set Name (Plural): `cr950_projectses`
- OData queries require the **EntitySetName** (plural)

---

### **Step 2: Test Different Table Name Formats (10 minutes)**

Try these variations in Claude Desktop:

#### **Test 1: Use Plural Form (EntitySetName)**

```javascript
// Try plural form with 'es' suffix
query_dataverse(
  "cr950_projectses",
  "$select=cr950_projectsid,cr950_name",
  null,
  1
)
```

#### **Test 2: Use Singular Form**

```javascript
// Try singular form
query_dataverse(
  "cr950_projects",
  "$select=cr950_projectsid,cr950_name",
  null,
  1
)
```

#### **Test 3: Query System Table (Known to Work)**

```javascript
// Test with system table to verify connection
query_dataverse(
  "systemusers",
  "$select=systemuserid,fullname",
  null,
  1
)
```

**Expected:** At least one of these should work

---

### **Step 3: Fix OData Syntax in Code (15 minutes)**

Open the resa-dataverse-dev source code:

```bash
cd C:\RESA_Power_Build\MCP_Servers\resa-dataverse-dev

# Open the main file
code src\index.ts
```

**Find the query function** (around line 50-100):

```typescript
// CURRENT CODE (may look like this):
async function queryDataverse(
  entityName: string,
  select: string,
  filter?: string,
  top?: number
) {
  const url = `${DATAVERSE_URL}/api/data/v9.2/${entityName}?$select=${select}`;
  // ...
}
```

**Replace with corrected version:**

```typescript
async function queryDataverse(
  entityName: string,
  select?: string,
  filter?: string,
  top?: number
) {
  // Build OData URL properly
  let url = `${DATAVERSE_URL}/api/data/v9.2/${entityName}`;
  
  const params = [];
  
  if (select) {
    params.push(`$select=${select}`);
  }
  
  if (filter) {
    params.push(`$filter=${filter}`);
  }
  
  if (top) {
    params.push(`$top=${top}`);
  }
  
  if (params.length > 0) {
    url += '?' + params.join('&');
  }
  
  console.error(`Querying: ${url}`);
  
  // Rest of the function...
}
```

**Key fixes:**
1. Make `select` parameter optional
2. Build URL with proper parameter joining
3. Add logging to see actual URL
4. Handle cases where no parameters provided

---

### **Step 4: Update Tool Schema (5 minutes)**

In the same file, find the tool schema definition:

```typescript
// FIND THIS (around line 200-250):
{
  name: "query_dataverse",
  description: "Query records from a Dataverse table",
  inputSchema: {
    type: "object",
    properties: {
      entityName: {
        type: "string",
        description: "Logical name of the table"
      },
      select: {
        type: "string",
        description: "Comma-separated list of fields"  // ❌ OLD
      },
      // ...
    },
    required: ["entityName", "select"]  // ❌ OLD
  }
}
```

**Replace with:**

```typescript
{
  name: "query_dataverse",
  description: "Query records from a Dataverse table",
  inputSchema: {
    type: "object",
    properties: {
      entityName: {
        type: "string",
        description: "Logical name of the table (e.g., 'cr950_projectses', 'cr950_apparatus')"
      },
      select: {
        type: "string",
        description: "OData $select clause - comma-separated field names (optional)"
      },
      filter: {
        type: "string",
        description: "OData $filter clause (optional, e.g., 'statecode eq 0')"
      },
      top: {
        type: "number",
        description: "Maximum number of records to return (default: 50)"
      }
    },
    required: ["entityName"]  // ✅ Only entityName required
  }
}
```

**Key changes:**
1. Only `entityName` required
2. `select`, `filter`, `top` are optional
3. Better descriptions with examples

---

### **Step 5: Rebuild and Test (5 minutes)**

```bash
cd C:\RESA_Power_Build\MCP_Servers\resa-dataverse-dev

# Rebuild
npm run build

# Test standalone
node build\index.js
# Should start without errors
```

---

### **Step 6: Test in Claude Desktop (5 minutes)**

1. **Restart Claude Desktop**
2. Open new chat
3. Test queries:

```
Test 1: "Query the cr950_projectses table, return just the first record"

Test 2: "Query cr950_apparatus table, select cr950_designation and cr950_completionstatus"

Test 3: "Query systemusers table to verify connection"
```

**Expected:** Should return records without 400 errors

---

### **Step 7: Create Reference Document (5 minutes)**

Create a quick reference for correct table names:

```bash
notepad C:\RESA_Power_Build\MCP_Servers\resa-dataverse-dev\TABLE_NAMES_REFERENCE.md
```

**Paste:**

```markdown
# Dataverse Table Names Reference

## RESA Power Project Tracker Tables

| Display Name | Entity Name | Entity Set Name (Use This!) |
|--------------|-------------|----------------------------|
| Projects | cr950_projects | cr950_projectses |
| Project Scope | cr950_projectscope | cr950_projectscopes |
| Tasks | cr950_tasks | cr950_taskses |
| Apparatus | cr950_apparatus | cr950_apparatuses |
| Apparatus Revenue | cr950_apparatusrevenue | cr950_apparatusrevenues |
| Scope Labor Detail | cr950_scopelabordetail | cr950_scopelabordetails |
| Apparatus Type Master | cr950_apparatustypemaster | cr950_apparatustypemasters |
| Client | cr950_client | cr950_clients |
| Site | cr950_site | cr950_sites |
| Employee | cr950_employee | cr950_employees |
| Quote | cr950_quote | cr950_quotes |
| Resource Assignment | cr950_resourceassignment | cr950_resourceassignments |
| Equipment | cr950_equipment | cr950_equipments |
| Business Unit | cr950_businessunit | cr950_businessunits |

## Query Examples

```javascript
// Correct ✅
query_dataverse("cr950_projectses", "$select=cr950_name,cr950_projectnumber")

// Incorrect ❌
query_dataverse("cr950_projects", "$select=cr950_name,cr950_projectnumber")
```

## Rule: Always use EntitySetName (plural form) for OData queries
```

**Save and close**

---

## ✅ Success Criteria - resa-dataverse-dev

- [ ] Code updated with proper OData URL construction
- [ ] `select` parameter made optional
- [ ] Rebuilt successfully
- [ ] Can query systemusers table
- [ ] Can query cr950_projectses table
- [ ] Can query cr950_apparatus table
- [ ] No 400 errors
- [ ] TABLE_NAMES_REFERENCE.md created

**Time to fix:** ~30 minutes  
**Difficulty:** MEDIUM (requires code changes)

---

## 🎯 COMPLETION CHECKLIST

### **Both Servers Fixed:**

**resa-docs:**
- [ ] 4 template files created
- [ ] Rebuild successful
- [ ] Can generate table docs
- [ ] Can generate ERD diagrams
- [ ] Can generate user guides
- [ ] Can generate API docs

**resa-dataverse-dev:**
- [ ] Code updated with proper OData
- [ ] Rebuild successful
- [ ] Can query system tables
- [ ] Can query RESA tables
- [ ] TABLE_NAMES_REFERENCE.md created
- [ ] No 400 errors

### **Testing:**
- [ ] Tested all resa-docs tools in Claude Desktop
- [ ] Tested all resa-dataverse-dev queries
- [ ] Both servers running without errors
- [ ] Documentation updated

---

## 📊 EXPECTED OUTCOME

**After These Fixes:**

| Server | Before | After |
|--------|--------|-------|
| resa-dataverse-dev | 🟡 PARTIAL | 🟢 OPERATIONAL |
| resa-docs | 🟡 PARTIAL | 🟢 OPERATIONAL |

**Total Operational Servers:** 4 out of 4 Dataverse servers ✅

---

## 🚀 NEXT STEPS

Once both servers are fixed:

1. **Generate documentation** for all 14 tables using resa-docs
2. **Test rollup validation** using resa-testing
3. **Export solution** using resa-deploy for backup
4. **Update progress tracker** to show all servers operational

---

**Document:** MCP_TROUBLESHOOTING_GUIDE.md  
**Created:** November 23, 2025, 9:05 PM  
**Estimated Time:** 1.5-2 hours total  
**Difficulty:** EASY-MEDIUM  
**Status:** Ready for implementation

