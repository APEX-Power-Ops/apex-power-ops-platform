# resa-testing-mcp

**Automated Testing & Validation MCP Server for RESA Power Dataverse Solution**

Model Context Protocol (MCP) server providing automated testing, validation, and test data generation for the RESA Power Project Tracker Dataverse solution.

## 🎯 Purpose

This server enables Claude Desktop to:
- **Validate rollup fields** by comparing system calculations vs manual calculations
- **Test calculated fields** by verifying formulas produce correct results
- **Run integration tests** for end-to-end workflow validation
- **Generate test data** hierarchies for testing and development

## 📦 Installation

### Prerequisites
- Node.js 18+ installed
- Access to org99cd6c6e.crm.dynamics.com (Development environment)
- Azure app registration credentials

### Setup

1. **Install dependencies:**
   ```powershell
   cd C:\RESA_Power_Build\MCP_Servers\resa-testing-mcp
   npm install
   ```

2. **Build TypeScript:**
   ```powershell
   npm run build
   ```

3. **Configure environment variables:**
   Create a `.env` file (optional, defaults are hardcoded):
   ```env
   DATAVERSE_URL=https://org99cd6c6e.crm.dynamics.com
   AZURE_TENANT_ID=270d5723-4b30-4f3b-b9cb-6527be741b42
   AZURE_CLIENT_ID=9df3350f-b3b4-47c4-97b5-499a8b02acc7
   AZURE_CLIENT_SECRET=[your_client_secret]
   ENVIRONMENT=DEVELOPMENT
   ```

4. **Add to Claude Desktop:**
   See [CLAUDE_DESKTOP_SETUP.md](./CLAUDE_DESKTOP_SETUP.md) for detailed instructions.

## 🛠️ Available Tools

### 1. validate_rollup_fields

Validates rollup fields by comparing system-calculated values against manual calculations.

**Use Case:** Ensure rollup field formulas are calculating correctly across all records.

**How It Works:**
1. Queries EntityDefinitions to identify rollup fields
2. Fetches sample records from the table
3. Manually calculates expected values by querying related records
4. Compares system values vs manual calculations
5. Returns PASS/FAIL/WARNING status for each field

**Supported Tables:**
- `cr950_projectscopes`: cr950_total_estimated_hours, cr950_total_actual_hours, cr950_total_apparatus_count
- `cr950_projectses`: cr950_project_total_estimated_hours, cr950_project_total_actual_hours
- `cr950_apparatus`: (placeholder for future rollups)

**Example:**
```javascript
{
  tableName: "cr950_projectscopes",
  fieldNames: ["cr950_total_estimated_hours"],
  sampleSize: 5,
  compareManual: true
}
```

### 2. test_calculated_fields

Tests calculated fields by verifying their formulas produce correct results.

**Use Case:** Validate that calculated field formulas are working as expected with real data.

**How It Works:**
1. Retrieves calculated field definitions (hardcoded from v1.4.0.0 schema)
2. Fetches sample records with calculated fields
3. Extracts input values for each test scenario
4. Manually calculates expected output
5. Compares with actual field value (tolerance < 0.01)

**Known Calculated Fields:**
- **Projects**: cr950_completion_percentage
- **ProjectScope**: cr950_scope_completion_percentage
- **ApparatusRevenue**: cr950_totalrevenue, cr950_totalmargin, cr950_marginpercentage

**Test Scenarios:**
- `percentage_calculation`: (numerator / denominator) * 100
- `simple_sum`: field1 + field2
- `simple_subtraction`: field1 - field2

**Example:**
```javascript
{
  tableName: "cr950_apparatusrevenues",
  fieldNames: ["cr950_totalrevenue", "cr950_marginpercentage"]
}
```

### 3. run_integration_tests

Runs end-to-end integration tests for complete workflows.

**Use Case:** Validate entire business processes from start to finish.

**Available Scenarios:**

#### apparatus_completion_flow (5 steps)
Tests the complete apparatus completion workflow:
1. Create test hierarchy (1 project, 1 scope, 1 task, 5 apparatus)
2. Verify apparatus created
3. Mark apparatus complete
4. Verify revenue record created
5. Verify rollups updated

#### new_project_creation (3 steps)
Tests project creation with multiple scopes:
1. Create project structure (1 project, 3 scopes, 9 tasks, 90 apparatus)
2. Verify project created
3. Verify scope count matches expected (3)

#### rollup_propagation
Tests rollup field updates when related records change.

#### bulk_operations
Performance test with larger data volumes (2 projects, 600 apparatus total).

**Example:**
```javascript
{
  scenarioName: "apparatus_completion_flow",
  cleanup: true
}
```

### 4. generate_test_data

Generates realistic hierarchical test data for testing.

**Use Case:** Create test data hierarchies quickly without manual data entry.

**Hierarchy Created:**
```
Projects
  └─ Scopes
      └─ Tasks
          └─ Apparatus
              └─ Revenue (for completed apparatus)
```

**Predefined Scenarios:**
- **small**: 1 project, 2 scopes, 10 apparatus total
- **medium**: 3 projects, 6 scopes, 50 apparatus total
- **large**: 5 projects, 10 scopes, 100 apparatus total
- **custom**: Specify your own dimensions

**Naming Convention:**
- Projects: `TEST-Project-{n}-{timestamp}`
- Scopes: `TEST-Scope-{proj}-{scope}`
- Tasks: `TEST-Task-{proj}-{scope}-{task}`
- Apparatus: `TEST-APP-{proj}-{scope}-{task}-{app}`
- Revenue: `TEST-REV-{timestamp}`

**Example:**
```javascript
{
  scenario: "small"
}
```

Or custom:
```javascript
{
  scenario: "custom",
  projects: 2,
  scopesPerProject: 3,
  tasksPerScope: 5,
  apparatusPerTask: 20,
  completePercentage: 75,
  includeFinancialData: true
}
```

### 5. cleanup_test_data

Cleans up test data created by generate_test_data.

**Use Case:** Remove test data after testing is complete.

**How It Works:**
Deletes all created records in reverse order to maintain referential integrity:
1. Revenue records
2. Apparatus records
3. Task records
4. Scope records
5. Project records

**Example:**
```javascript
{
  testDataResult: {
    projectIds: ["..."],
    scopeIds: ["..."],
    taskIds: ["..."],
    apparatusIds: ["..."],
    revenueIds: ["..."]
  }
}
```

## 🏗️ Architecture

### Project Structure

```
resa-testing-mcp/
├── src/
│   ├── index.ts                    # MCP server entry point
│   ├── tools/
│   │   ├── validate-rollups.ts     # Rollup field validation (400+ lines)
│   │   ├── test-calculated-fields.ts # Calculated field testing (300+ lines)
│   │   ├── run-integration-tests.ts  # Integration test scenarios (340+ lines)
│   │   └── generate-test-data.ts   # Test data generator (250+ lines)
│   └── utils/
│       └── dataverse-client.ts     # Dataverse API wrapper (280 lines)
├── build/                          # Compiled JavaScript output
├── tests/                          # Unit tests (future)
├── package.json
├── tsconfig.json
├── .gitignore
├── README.md
└── CLAUDE_DESKTOP_SETUP.md
```

### Key Components

#### Dataverse Client (utils/dataverse-client.ts)

Reusable Dataverse API wrapper with 9 functions:
- `getAccessToken()`: OAuth token management with caching
- `queryDataverse()`: OData queries with $select/$filter/$top/$expand
- `getRecord()`: Fetch single record by ID
- `createRecord()`: Create record, returns GUID
- `updateRecord()`: PATCH update existing record
- `deleteRecord()`: Delete record by ID
- `queryMetadata()`: Query EntityDefinitions for schema
- `executeBatch()`: Batch multiple operations
- `config`: Export environment configuration

**Token Caching:** Access tokens are cached and reused until 5 minutes before expiry.

**Safety:** Development environment check on startup (production is blocked).

## 🚀 Development

### Build

```powershell
npm run build
```

Compiles TypeScript to JavaScript in the `./build` directory.

### Run Standalone

```powershell
npm start
```

Starts the MCP server in stdio mode for testing.

### Development Mode

```powershell
npm run dev
```

Builds and starts the server in one command.

### Testing

```powershell
npm test
```

Runs Jest unit tests (not yet implemented).

## 📊 Tool Output Examples

### validate_rollup_fields Output

```json
{
  "status": "PASS",
  "recordsTested": 5,
  "fields": [
    {
      "fieldName": "cr950_total_estimated_hours",
      "results": [
        {
          "recordId": "abc123...",
          "recordName": "Project Scope 1",
          "expected": 100.00,
          "actual": 100.00,
          "variance": 0.00,
          "percentageOff": 0.00,
          "status": "PASS"
        }
      ],
      "passed": 5,
      "failed": 0,
      "warnings": 0
    }
  ],
  "summary": "All rollup fields validated successfully"
}
```

### test_calculated_fields Output

```json
{
  "tested": 3,
  "passed": 3,
  "failed": 0,
  "warnings": 0,
  "tests": [
    {
      "fieldName": "cr950_totalrevenue",
      "testName": "simple_sum",
      "inputs": { "neta": 500, "additional": 100 },
      "expected": 600,
      "actual": 600,
      "variance": 0,
      "status": "PASS"
    }
  ]
}
```

### run_integration_tests Output

```json
{
  "scenario": "apparatus_completion_flow",
  "status": "PASS",
  "steps": 5,
  "passed": 5,
  "failed": 0,
  "duration": 3250,
  "testResults": [
    {
      "stepNumber": 1,
      "stepName": "Create test hierarchy",
      "status": "PASS",
      "duration": 850,
      "message": "Created 1 project, 1 scope, 1 task, 5 apparatus"
    }
  ]
}
```

### generate_test_data Output

```json
{
  "scenario": "small",
  "projectsCreated": 1,
  "scopesCreated": 2,
  "tasksCreated": 6,
  "apparatusCreated": 60,
  "revenueCreated": 30,
  "projectIds": ["abc123..."],
  "scopeIds": ["def456...", "ghi789..."],
  "taskIds": ["..."],
  "apparatusIds": ["..."],
  "revenueIds": ["..."],
  "timestamp": "2025-11-23T20:30:00.000Z"
}
```

## ⚠️ Important Notes

### Environment Restrictions

**DEVELOPMENT ONLY**: This server is configured to run only in the development environment (org99cd6c6e.crm.dynamics.com). Attempts to run in production will fail with an error.

### Authentication

Uses Azure app registration with service principal authentication:
- **Tenant ID**: 270d5723-4b30-4f3b-b9cb-6527be741b42
- **Client ID**: 9df3350f-b3b4-47c4-97b5-499a8b02acc7
- **Required Permissions**: Dynamics CRM API (user_impersonation)

### Test Data Naming

All generated test data uses the prefix `TEST-` to distinguish it from production data. This makes cleanup and identification easier.

### Cleanup Recommendations

Always clean up test data after testing:
1. Use `cleanup_test_data` tool with the TestDataResult from `generate_test_data`
2. Or manually delete records with names starting with `TEST-`

## 🐛 Troubleshooting

### Authentication Errors

**Problem:** "401 Unauthorized" errors  
**Solution:** Verify Azure client secret is correct in environment variables

### Table Not Found Errors

**Problem:** "404 Not Found" for table queries  
**Solution:** Use logical names (e.g., `cr950_projectscopes`), not display names

### Rollup Field Validation Failures

**Problem:** Many rollup fields showing FAIL status  
**Solution:** This may indicate actual data quality issues. Investigate variance details in results.

### Build Errors

**Problem:** TypeScript compilation errors  
**Solution:** Ensure all dependencies are installed: `npm install`

## 📝 Version History

### 1.0.0 (November 23, 2025)
- ✅ Initial release
- ✅ 4 tools implemented (validate_rollup_fields, test_calculated_fields, run_integration_tests, generate_test_data)
- ✅ Dataverse client utility with 9 API functions
- ✅ TypeScript build configuration
- ✅ Claude Desktop integration

## 🔗 Related Documentation

- [CLAUDE_DESKTOP_SETUP.md](./CLAUDE_DESKTOP_SETUP.md) - Setup instructions for Claude Desktop
- [MCP_BUILD_PROGRESS.md](../../Documentation/06_Implementation_Guides/MCP_BUILD_PROGRESS.md) - Build progress tracker
- [Dataverse Schema Documentation](../../Documentation/) - RESA Power solution schema

## 👤 Author

**Jason Swenson**  
RESA Power Project Tracker Development Team

## 📄 License

Internal use only - RESA Power organization

---

**Status:** ✅ Production Ready (Development Environment Only)  
**Version:** 1.0.0  
**Build Date:** November 23, 2025  
**Target Completion:** November 29, 2025 - **COMPLETED AHEAD OF SCHEDULE**
