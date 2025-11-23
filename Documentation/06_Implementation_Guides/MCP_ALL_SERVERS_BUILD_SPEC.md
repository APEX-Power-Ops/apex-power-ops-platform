# MCP SERVER BUILD SPECIFICATION - ALL 5 SERVERS
## Master Implementation Guide for VS Code Claude

**Created:** November 23, 2025  
**Purpose:** Complete build instructions for all 5 RESA Power MCP servers  
**Build Order:** Priority-based (Tier 1 → Tier 2 → Tier 3)  
**Total Timeline:** 6 weeks  
**Target Completion:** January 3, 2026

---

## 🎯 ENVIRONMENT CONFIGURATION (USE FOR ALL SERVERS)

**Single Active Environment:**
```
DATAVERSE_URL=https://org99cd6c6e.crm.dynamics.com
AZURE_TENANT_ID=270d5723-4b30-4f3b-b9cb-6527be741b42
AZURE_CLIENT_ID=9df3350f-b3b4-47c4-97b5-499a8b02acc7
AZURE_CLIENT_SECRET=uAs8Q~NedRt8yRWqOjSr9izIuePpRzHNKVse5a9k
ENVIRONMENT=DEVELOPMENT
```

**Critical:** All 5 servers use the SAME Dataverse credentials above.

---

## 📋 BUILD ORDER & TIMELINE

| Priority | Server | Week | Hours | ROI/Year | Purpose |
|----------|--------|------|-------|----------|---------|
| **#1** | resa-testing-mcp | Week 1 | 20-30 | $24,800-$47,000 | Automated testing & validation |
| **#2** | resa-docs-mcp | Week 2 | 15-20 | $41,700-$47,600 | Documentation automation |
| **#3** | resa-deploy-mcp | Week 5 | 30-40 | $13,400-$20,500 | Deployment automation |
| **#4** | microsoft-graph-mcp | Week 6 | 25-35 | $52,000+ | Microsoft 365 integration |
| **#5** | quickbooks-mcp | Post-Pilot | 35-50 | $18,000-$24,000 | Financial integration |

**Build Tier 1 (#1-2) immediately, Tier 2 (#3-4) pre-pilot, Tier 3 (#5) post-pilot.**

---

## 🏗️ COMMON STRUCTURE FOR ALL SERVERS

Each MCP server follows this standard structure:

```
server-name-mcp/
├── package.json
├── tsconfig.json
├── .gitignore
├── README.md
├── src/
│   ├── index.ts              # MCP server entry point
│   ├── tools/                # Tool implementations
│   │   ├── tool1.ts
│   │   ├── tool2.ts
│   │   └── tool3.ts
│   └── utils/                # Shared utilities
│       ├── dataverse-client.ts   # Reuse from resa-dataverse-mcp
│       ├── auth.ts
│       ├── config.ts
│       └── logger.ts
├── tests/                    # Test files
│   ├── unit/
│   └── integration/
└── build/                    # Compiled output (gitignored)
```

---

## 📦 COMMON DEPENDENCIES FOR ALL SERVERS

**Base Dependencies (All Servers):**
```bash
npm install @modelcontextprotocol/sdk axios @azure/identity @azure/msal-node
npm install -D typescript @types/node ts-node
```

**Additional per Server:**
- resa-testing-mcp: `lodash`, `date-fns`
- resa-docs-mcp: `handlebars`, `markdown-it`, `mermaid`
- resa-deploy-mcp: `adm-zip`, `fs-extra`
- microsoft-graph-mcp: `@microsoft/microsoft-graph-client`
- quickbooks-mcp: `node-quickbooks`

---

## 🔧 COMMON CONFIGURATION FILES

### **tsconfig.json (Use for All Servers):**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ES2020",
    "moduleResolution": "node",
    "outDir": "./build",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "build", "tests"]
}
```

### **package.json Template (Adapt for Each Server):**
```json
{
  "name": "server-name-mcp",
  "version": "1.0.0",
  "type": "module",
  "description": "MCP server for [purpose]",
  "main": "build/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node build/index.js",
    "dev": "npm run build && npm start",
    "test": "jest"
  },
  "keywords": ["mcp", "resa-power", "dataverse"],
  "author": "Jason Swenson",
  "license": "MIT"
}
```

### **.gitignore (Use for All Servers):**
```
node_modules/
build/
.env
*.log
.DS_Store
```

---

# 1️⃣ RESA-TESTING-MCP (WEEK 1 - PRIORITY #1)

## Purpose
Automated testing and validation framework for Dataverse development.

## Tools to Implement (4 tools)

### **Tool 1: validate_rollup_fields**
```typescript
// src/tools/validate-rollups.ts

export async function validateRollupFields(params: {
  tableName: string;
  fieldNames?: string[];
  sampleSize?: number;
  compareManual?: boolean;
}): Promise<ValidationResult> {
  // 1. Get rollup field metadata from Dataverse
  // 2. Query sample records
  // 3. Manually calculate expected values
  // 4. Compare system values vs manual calculations
  // 5. Report PASS/FAIL with variance details
  
  return {
    status: "PASS" | "FAIL" | "WARNING",
    fields: [
      {
        fieldName: "cr950_total_apparatus_hours",
        expected: 42.5,
        actual: 42.5,
        variance: 0,
        status: "PASS"
      }
    ]
  };
}
```

**Implementation Steps:**
1. Query EntityDefinitions for rollup field metadata
2. Get related entity data (e.g., all tasks for a scope)
3. Calculate expected rollup value manually
4. Compare to actual field value
5. Allow tolerance of <0.01 variance

**Test Cases:**
- Validate cr950_total_apparatus_hours on ProjectScope
- Validate cr950_total_actual_hours on ProjectScope
- Validate cr950_total_revenue on Projects
- Validate date rollups (earliest/latest)

### **Tool 2: test_calculated_fields**
```typescript
// src/tools/test-calculations.ts

export async function testCalculatedFields(params: {
  tableName: string;
  fieldNames?: string[];
  testCases?: TestCase[];
}): Promise<TestResult> {
  // 1. Get calculated field formulas
  // 2. Create test scenarios with known inputs
  // 3. Verify outputs match expectations
  // 4. Report pass/fail for each formula
  
  return {
    tested: 30,
    passed: 29,
    failed: 1,
    details: [...]
  };
}
```

**Test Coverage:**
- Projects: 6 calculated fields
- ProjectScope: 5 calculated fields
- Tasks: 5 calculated fields
- Apparatus: 3 calculated fields
- ApparatusRevenue: 11 calculated fields

### **Tool 3: run_integration_tests**
```typescript
// src/tools/integration-tests.ts

export async function runIntegrationTests(params: {
  scenarioName: string;
  cleanup?: boolean;
}): Promise<IntegrationTestResult> {
  // Test complete workflows:
  // 1. Create project → scope → task → apparatus
  // 2. Mark apparatus complete
  // 3. Verify revenue record created
  // 4. Verify rollups updated
  // 5. Clean up test data
  
  return {
    scenario: "apparatus_completion_flow",
    steps: 5,
    passed: 5,
    duration: "2.3s"
  };
}
```

**Test Scenarios:**
1. New project creation workflow
2. Apparatus completion → revenue recognition
3. NETA standard changes
4. Bulk operations
5. Multi-user simulation

### **Tool 4: generate_test_data**
```typescript
// src/tools/generate-test-data.ts

export async function generateTestData(params: {
  scenario: string;
  projects?: number;
  scopesPerProject?: number;
  tasksPerScope?: number;
  apparatusPerTask?: number;
  completePercentage?: number;
  includeFinancialData?: boolean;
}): Promise<TestDataResult> {
  // Create realistic test hierarchy:
  // 1. Generate projects with scopes
  // 2. Create tasks and apparatus
  // 3. Set completion status based on percentage
  // 4. Create financial records if requested
  // 5. Return IDs for cleanup
  
  return {
    created: {
      projects: 3,
      scopes: 6,
      tasks: 18,
      apparatus: 180,
      revenue: 108
    },
    projectIds: ["guid1", "guid2", "guid3"]
  };
}
```

## Build Steps

```bash
# 1. Create project
cd C:\RESA_Power_Build\MCP_Servers
mkdir resa-testing-mcp
cd resa-testing-mcp

# 2. Initialize
npm init -y
npm install @modelcontextprotocol/sdk axios @azure/identity @azure/msal-node lodash date-fns
npm install -D typescript @types/node @types/lodash ts-node jest @types/jest

# 3. Create structure
mkdir src src\tools src\utils tests tests\unit tests\integration

# 4. Copy Dataverse client
# Copy from: ..\resa-dataverse-mcp\src\index.ts
# Extract: getAccessToken(), queryDataverse(), createRecord()
# Save to: src\utils\dataverse-client.ts

# 5. Create tools
# Implement 4 tools in src\tools\

# 6. Create index.ts
# Set up MCP server with 4 tools

# 7. Build
npm run build

# 8. Test
node build/index.js
# Should output: "RESA Testing MCP Server running"
```

## Claude Desktop Config
```json
{
  "resa-testing": {
    "command": "node",
    "args": ["C:\\RESA_Power_Build\\MCP_Servers\\resa-testing-mcp\\build\\index.js"],
    "env": {
      "DATAVERSE_URL": "https://org99cd6c6e.crm.dynamics.com",
      "AZURE_TENANT_ID": "270d5723-4b30-4f3b-b9cb-6527be741b42",
      "AZURE_CLIENT_ID": "9df3350f-b3b4-47c4-97b5-499a8b02acc7",
      "AZURE_CLIENT_SECRET": "uAs8Q~NedRt8yRWqOjSr9izIuePpRzHNKVse5a9k",
      "ENVIRONMENT": "DEVELOPMENT"
    }
  }
}
```

---

# 2️⃣ RESA-DOCS-MCP (WEEK 2 - PRIORITY #2)

## Purpose
Automated documentation generation from Dataverse schema.

## Tools to Implement (4 tools)

### **Tool 1: generate_table_documentation**
```typescript
// src/tools/generate-table-docs.ts

export async function generateTableDocumentation(params: {
  tableName: string;
  includeFields?: boolean;
  includeRelationships?: boolean;
  includeBusinessRules?: boolean;
  outputFormat?: "markdown" | "html" | "pdf";
}): Promise<DocumentationResult> {
  // 1. Query EntityDefinition for table metadata
  // 2. Get all field definitions
  // 3. Get all relationships
  // 4. Generate formatted documentation
  
  return {
    tableName: "cr950_projects",
    documentation: "# Projects Table\n\n...",
    fields: 19,
    relationships: 5
  };
}
```

**Template Structure:**
```markdown
# [Table Display Name]

**Logical Name:** cr950_projects  
**Schema Name:** cr950_projects  
**Primary Key:** cr950_projectsid  
**Created:** 2025-11-19

## Description
[Table description from metadata]

## Fields (19)

| Display Name | Logical Name | Type | Required | Description |
|--------------|--------------|------|----------|-------------|
| Project Name | cr950_name | String(100) | Yes | Primary name field |
| ... | ... | ... | ... | ... |

## Relationships (5)

| Name | Related Table | Type | Description |
|------|---------------|------|-------------|
| Projects_Client | Client | N:1 | Client lookup |
| ... | ... | ... | ... |

## Business Rules

- Rule 1: [Description]
- Rule 2: [Description]

## Usage Examples

```javascript
// Query projects
const projects = await queryDataverse("cr950_projectses", 
  "cr950_name,cr950_projectnumber", 
  "statecode eq 0",
  10
);
```
```

### **Tool 2: generate_erd_diagram**
```typescript
// src/tools/generate-erd.ts

export async function generateERDiagram(params: {
  tables?: string[];
  includeAllRelationships?: boolean;
  format?: "mermaid" | "plantuml";
}): Promise<DiagramResult> {
  // 1. Query entity metadata
  // 2. Get all relationships
  // 3. Generate Mermaid ERD syntax
  // 4. Return diagram code
  
  return {
    format: "mermaid",
    code: "erDiagram\n  PROJECTS ||--o{ PROJECTSCOPE : contains\n...",
    tables: 14,
    relationships: 19
  };
}
```

### **Tool 3: generate_user_guide**
```typescript
// src/tools/generate-user-guide.ts

export async function generateUserGuide(params: {
  role: "FieldTech" | "JobLead" | "PM" | "Billing" | "Executive";
  includeScreenshots?: boolean;
  outputFormat?: "markdown" | "docx" | "pdf";
}): Promise<UserGuideResult> {
  // Generate role-specific user guides
  // Based on schema and business rules
  
  return {
    role: "FieldTech",
    sections: 12,
    pages: 25,
    content: "..."
  };
}
```

**Guide Structure:**
- Introduction
- How to log in
- Common tasks for role
- Step-by-step workflows
- Troubleshooting
- FAQ

### **Tool 4: generate_api_docs**
```typescript
// src/tools/generate-api-docs.ts

export async function generateAPIDocumentation(params: {
  format?: "openapi" | "markdown";
  includeExamples?: boolean;
}): Promise<APIDocResult> {
  // Generate OpenAPI 3.0 spec from Dataverse schema
  
  return {
    format: "openapi",
    version: "3.0.0",
    spec: {...},
    endpoints: 56
  };
}
```

## Build Steps

```bash
# 1. Create project
cd C:\RESA_Power_Build\MCP_Servers
mkdir resa-docs-mcp
cd resa-docs-mcp

# 2. Initialize
npm init -y
npm install @modelcontextprotocol/sdk axios @azure/identity @azure/msal-node handlebars markdown-it mermaid
npm install -D typescript @types/node ts-node

# 3. Create structure
mkdir src src\tools src\utils src\templates tests

# 4. Copy Dataverse client from resa-testing-mcp

# 5. Create documentation templates
# Create Handlebars templates in src\templates\

# 6. Implement 4 tools

# 7. Build and test
npm run build
node build/index.js
```

---

# 3️⃣ RESA-DEPLOY-MCP (WEEK 5 - PRIORITY #3)

## Purpose
Safe, repeatable solution deployment automation.

## Tools to Implement (5 tools)

### **Tool 1: export_solution**
```typescript
// src/tools/export-solution.ts

export async function exportSolution(params: {
  solutionName: string;
  version?: string;
  managed?: boolean;
  outputPath?: string;
}): Promise<ExportResult> {
  // 1. Call Dataverse export API
  // 2. Poll for completion
  // 3. Download zip file
  // 4. Save to specified path
  
  return {
    solutionName: "RESAPowerProjectTracker",
    version: "1.5.0.0",
    size: "2.3 MB",
    path: "C:\\RESA_Power_Build\\Solution_Exports\\v1.5.0.0\\managed.zip"
  };
}
```

### **Tool 2: import_solution**
```typescript
// src/tools/import-solution.ts

export async function importSolution(params: {
  zipPath: string;
  environment: "dev" | "test" | "prod";
  upgradeMode?: "Update" | "Stage";
  publishWorkflows?: boolean;
}): Promise<ImportResult> {
  // 1. Validate environment (never allow prod!)
  // 2. Upload solution zip
  // 3. Trigger import
  // 4. Monitor import job
  // 5. Return status
  
  return {
    status: "Success",
    duration: "45s",
    components: 127
  };
}
```

### **Tool 3: compare_environments**
```typescript
// src/tools/compare-environments.ts

export async function compareEnvironments(params: {
  sourceEnv: string;
  targetEnv: string;
  solutionName: string;
}): Promise<ComparisonResult> {
  // Compare solution versions between environments
  
  return {
    source: "v1.5.0.0",
    target: "v1.4.0.0",
    differences: [
      { type: "table", name: "cr950_employee", status: "missing_in_target" },
      { type: "field", name: "cr950_total_revenue", status: "different_formula" }
    ]
  };
}
```

### **Tool 4: rollback_solution**
```typescript
// src/tools/rollback-solution.ts

export async function rollbackSolution(params: {
  solutionName: string;
  targetVersion: string;
  createBackup?: boolean;
}): Promise<RollbackResult> {
  // Rollback to previous version
  // Safety: Only works on dev environment!
  
  return {
    rolledBackFrom: "v1.5.0.0",
    rolledBackTo: "v1.4.0.0",
    backupPath: "...",
    status: "Success"
  };
}
```

### **Tool 5: validate_deployment**
```typescript
// src/tools/validate-deployment.ts

export async function validateDeployment(params: {
  solutionName: string;
  checks?: string[];
}): Promise<ValidationResult> {
  // Post-deployment validation:
  // 1. All tables present
  // 2. All fields present
  // 3. Relationships intact
  // 4. Formulas correct
  // 5. Security roles assigned
  
  return {
    passed: 127,
    failed: 0,
    warnings: 2,
    details: [...]
  };
}
```

## Build Steps

```bash
# Similar structure to previous servers
cd C:\RESA_Power_Build\MCP_Servers
mkdir resa-deploy-mcp
cd resa-deploy-mcp

npm init -y
npm install @modelcontextprotocol/sdk axios @azure/identity @azure/msal-node adm-zip fs-extra
npm install -D typescript @types/node ts-node

# Create structure and implement tools
```

---

# 4️⃣ MICROSOFT-GRAPH-MCP (WEEK 6 - PRIORITY #4)

## Purpose
Deep Microsoft 365 integration for notifications, calendar, Teams.

## Tools to Implement (6 tools)

### **Tool 1: send_email_notification**
```typescript
// src/tools/send-email.ts

export async function sendEmailNotification(params: {
  to: string[];
  subject: string;
  body: string;
  bodyType?: "text" | "html";
  attachments?: Attachment[];
}): Promise<EmailResult> {
  // Send email via Microsoft Graph
  
  return {
    messageId: "AAMk...",
    status: "Sent",
    recipients: 3
  };
}
```

**Use Cases:**
- Apparatus completion notifications
- Project milestone alerts
- Resource assignment notifications

### **Tool 2: create_calendar_event**
```typescript
// src/tools/create-calendar-event.ts

export async function createCalendarEvent(params: {
  subject: string;
  start: string;
  end: string;
  attendees?: string[];
  location?: string;
  body?: string;
}): Promise<EventResult> {
  // Create calendar event
  
  return {
    eventId: "AAMk...",
    webLink: "https://outlook.office.com/..."
  };
}
```

**Use Cases:**
- Project kickoff meetings
- Site visit scheduling
- Milestone deadlines

### **Tool 3: post_to_teams_channel**
```typescript
// src/tools/post-to-teams.ts

export async function postToTeamsChannel(params: {
  channelId: string;
  message: string;
  mentions?: string[];
  attachments?: any[];
}): Promise<TeamsResult> {
  // Post to Teams channel
  
  return {
    messageId: "1234567890",
    timestamp: "2025-11-25T10:30:00Z"
  };
}
```

**Use Cases:**
- Daily progress updates
- Completion notifications
- Issue alerts

### **Tool 4: get_user_profile**
### **Tool 5: search_users**
### **Tool 6: manage_sharepoint_files**

## Build Steps

```bash
cd C:\RESA_Power_Build\MCP_Servers
mkdir microsoft-graph-mcp
cd microsoft-graph-mcp

npm init -y
npm install @modelcontextprotocol/sdk @microsoft/microsoft-graph-client @azure/identity
npm install -D typescript @types/node ts-node

# Implement 6 tools
```

---

# 5️⃣ QUICKBOOKS-MCP (POST-PILOT - PRIORITY #5)

## Purpose
Financial system integration for invoicing and accounting.

## Tools to Implement (4 tools)

### **Tool 1: create_invoice**
### **Tool 2: sync_revenue_data**
### **Tool 3: get_payment_status**
### **Tool 4: reconcile_accounts**

## Build Steps

```bash
cd C:\RESA_Power_Build\MCP_Servers
mkdir quickbooks-mcp
cd quickbooks-mcp

npm init -y
npm install @modelcontextprotocol/sdk node-quickbooks
npm install -D typescript @types/node ts-node

# Implement after pilot success
```

---

## 🎯 TESTING PROTOCOL FOR ALL SERVERS

After building each server:

### **1. Unit Tests**
```bash
npm test
```

### **2. Manual Connection Test**
```bash
npm run build
node build/index.js
# Should output: "[Server Name] MCP Server running"
```

### **3. Claude Desktop Integration**
1. Add to `claude_desktop_config.json`
2. Restart Claude Desktop
3. Test in new chat:
```
User: "List available MCP tools"
# Should see new server's tools

User: "Test [tool_name] with sample data"
# Should get results
```

### **4. Dataverse Integration Test**
```
User: "Query the Projects table"
# Should return actual data

User: "[Use specific tool functionality]"
# Should work against org99cd6c6e
```

---

## 📊 PROGRESS TRACKING

Create a progress tracker file:

```markdown
# MCP Server Build Progress

## Tier 1 (Week 1-2)
- [ ] resa-testing-mcp
  - [ ] Project created
  - [ ] Dependencies installed
  - [ ] validate_rollup_fields implemented
  - [ ] test_calculated_fields implemented
  - [ ] run_integration_tests implemented
  - [ ] generate_test_data implemented
  - [ ] Tested with Claude Desktop
  - [ ] Validated against v1.4.0.0

- [ ] resa-docs-mcp
  - [ ] Project created
  - [ ] Dependencies installed
  - [ ] generate_table_documentation implemented
  - [ ] generate_erd_diagram implemented
  - [ ] generate_user_guide implemented
  - [ ] generate_api_docs implemented
  - [ ] Tested with Claude Desktop
  - [ ] Generated docs for 14 tables

## Tier 2 (Week 5-6)
- [ ] resa-deploy-mcp (5 tools)
- [ ] microsoft-graph-mcp (6 tools)

## Tier 3 (Post-Pilot)
- [ ] quickbooks-mcp (4 tools)
```

---

## 🚨 CRITICAL REMINDERS

### **For All Servers:**

1. **Environment Protection**
   - NEVER connect to production (org04ad071f - if it exists)
   - ONLY use org99cd6c6e.crm.dynamics.com
   - All servers use DEVELOPMENT mode

2. **Code Reuse**
   - Copy Dataverse client from resa-dataverse-mcp
   - Share authentication logic
   - Use common utilities

3. **Error Handling**
   - Wrap all API calls in try-catch
   - Return meaningful error messages
   - Log errors for debugging

4. **Configuration**
   - Use environment variables
   - Never hardcode credentials
   - Support .env files

5. **Testing**
   - Test each tool individually
   - Test against actual Dataverse
   - Verify output formats

---

## 📁 FILE LOCATIONS

**Build all servers in:**
```
C:\RESA_Power_Build\MCP_Servers\
├── resa-dataverse-mcp\     (existing)
├── resa-testing-mcp\       (build first)
├── resa-docs-mcp\          (build second)
├── resa-deploy-mcp\        (build third)
├── microsoft-graph-mcp\    (build fourth)
└── quickbooks-mcp\         (build last)
```

**Update this file:**
```
C:\RESA_Power_Build\Documentation\06_Implementation_Guides\MCP_BUILD_PROGRESS.md
```

**Reference:**
```
C:\RESA_Power_Build\MCP_Servers\resa-dataverse-mcp\src\index.ts
# For Dataverse client code examples
```

---

## ✅ COMPLETION CRITERIA

Each server is complete when:
- [x] All tools implemented and working
- [x] Built successfully (no TypeScript errors)
- [x] Runs standalone (`node build/index.js`)
- [x] Integrates with Claude Desktop
- [x] Tested against org99cd6c6e.crm.dynamics.com
- [x] Documentation generated (README.md)
- [x] Progress tracker updated

---

## 🎯 SUCCESS METRICS

**By End of Week 2:**
- ✅ resa-testing-mcp validating rollup fields
- ✅ resa-docs-mcp generating table documentation
- ✅ Ready to create 32 rollup fields with confidence

**By End of Week 6:**
- ✅ All Tier 1 and Tier 2 servers operational
- ✅ Ready for pilot rollout
- ✅ Professional documentation generated
- ✅ Safe deployment process established

---

**Document Version:** 1.0  
**Created:** November 23, 2025  
**For:** VS Code Claude  
**Purpose:** Complete build specification for all 5 MCP servers  
**Status:** Ready for implementation

