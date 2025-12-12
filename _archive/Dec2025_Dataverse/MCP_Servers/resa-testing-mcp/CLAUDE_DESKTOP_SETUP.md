# Claude Desktop Setup for resa-testing-mcp

## 🎯 Quick Setup

### 1. Locate Claude Desktop Config

The configuration file is located at:
```
%APPDATA%\Claude\claude_desktop_config.json
```

Full path (typically):
```
C:\Users\[YourUsername]\AppData\Roaming\Claude\claude_desktop_config.json
```

### 2. Add resa-testing-mcp to Config

Edit `claude_desktop_config.json` and add the following to the `mcpServers` section:

```json
{
  "mcpServers": {
    "resa-testing": {
      "command": "node",
      "args": [
        "C:\\RESA_Power_Build\\MCP_Servers\\resa-testing-mcp\\build\\index.js"
      ],
      "env": {
        "DATAVERSE_URL": "https://org99cd6c6e.crm.dynamics.com",
        "AZURE_TENANT_ID": "270d5723-4b30-4f3b-b9cb-6527be741b42",
        "AZURE_CLIENT_ID": "9df3350f-b3b4-47c4-97b5-499a8b02acc7",
        "AZURE_CLIENT_SECRET": "[YOUR_CLIENT_SECRET]",
        "ENVIRONMENT": "DEVELOPMENT"
      }
    }
  }
}
```

**⚠️ Important Notes:**
- Replace `[YOUR_CLIENT_SECRET]` with your actual Azure app registration client secret
- Use double backslashes (`\\`) in Windows paths for JSON
- The `ENVIRONMENT` must be set to `DEVELOPMENT` (production is blocked)

### 3. Restart Claude Desktop

After saving the config file:
1. Completely close Claude Desktop (not just minimize)
2. Reopen Claude Desktop
3. The MCP server will connect automatically

### 4. Verify Connection

In a new Claude chat, type:
```
List available MCP tools
```

You should see 5 tools:
- `validate_rollup_fields` - Validate rollup field calculations
- `test_calculated_fields` - Test calculated field formulas
- `run_integration_tests` - Run end-to-end workflow tests
- `generate_test_data` - Create test data hierarchies
- `cleanup_test_data` - Delete test data

## 🧪 Test the Server

### Test 1: Generate Test Data

```
Use the generate_test_data tool to create a small test data scenario with 1 project
```

Expected result: A TestDataResult object with counts of created records and their IDs.

### Test 2: Validate Rollup Fields

```
Use the validate_rollup_fields tool to validate rollup fields on the cr950_projectscopes table with a sample size of 3
```

Expected result: A ValidationResult showing PASS/FAIL/WARNING status for each rollup field.

### Test 3: Run Integration Test

```
Use the run_integration_tests tool to run the apparatus_completion_flow scenario
```

Expected result: Step-by-step test results showing the complete workflow execution.

## 🔧 Troubleshooting

### Server Not Appearing

1. **Check config file syntax**: Ensure JSON is valid (no trailing commas, proper quotes)
2. **Check path**: Verify the build directory exists and contains index.js
3. **Check Claude Desktop logs**: Look for error messages in the Claude Desktop console

### Authentication Errors

1. **Verify credentials**: Ensure AZURE_CLIENT_SECRET is correct
2. **Check Azure app permissions**: Ensure app has Dynamics CRM API permissions
3. **Check environment**: Must be DEVELOPMENT (not PRODUCTION)

### Tool Execution Errors

1. **Check Dataverse connectivity**: Ensure https://org99cd6c6e.crm.dynamics.com is accessible
2. **Verify table names**: Use logical names (e.g., `cr950_projectscopes`, not display names)
3. **Check tool parameters**: Refer to tool schemas in this document

## 📚 Tool Reference

### validate_rollup_fields

Validates rollup fields by comparing system-calculated values against manual calculations.

**Parameters:**
- `tableName` (required): Logical name of table (e.g., `cr950_projectscopes`)
- `fieldNames` (optional): Array of specific field names to test
- `sampleSize` (optional): Number of records to test (default: 5)
- `compareManual` (optional): Whether to manually calculate (default: true)

**Example:**
```json
{
  "tableName": "cr950_projectscopes",
  "fieldNames": ["cr950_total_estimated_hours", "cr950_total_actual_hours"],
  "sampleSize": 3
}
```

### test_calculated_fields

Tests calculated fields by verifying formulas produce correct results.

**Parameters:**
- `tableName` (required): Logical name of table (e.g., `cr950_apparatusrevenues`)
- `fieldNames` (optional): Array of specific field names to test
- `testCases` (optional): Custom test cases with known inputs/outputs

**Example:**
```json
{
  "tableName": "cr950_apparatusrevenues",
  "fieldNames": ["cr950_totalrevenue", "cr950_marginpercentage"]
}
```

### run_integration_tests

Runs end-to-end integration tests for complete workflows.

**Parameters:**
- `scenarioName` (required): One of:
  - `apparatus_completion_flow`: Test apparatus completion workflow (5 steps)
  - `new_project_creation`: Test project creation (3 steps)
  - `rollup_propagation`: Test rollup updates
  - `bulk_operations`: Performance test with larger data
- `cleanup` (optional): Delete test data after execution (default: true)

**Example:**
```json
{
  "scenarioName": "apparatus_completion_flow",
  "cleanup": true
}
```

### generate_test_data

Generates realistic test data hierarchies.

**Parameters:**
- `scenario` (optional): Predefined scenario or `custom`
  - `small`: 1 project, 2 scopes, 10 apparatus
  - `medium`: 3 projects, 6 scopes, 50 apparatus
  - `large`: 5 projects, 10 scopes, 100 apparatus
- `projects` (optional): Number of projects (default: 1)
- `scopesPerProject` (optional): Scopes per project (default: 2)
- `tasksPerScope` (optional): Tasks per scope (default: 3)
- `apparatusPerTask` (optional): Apparatus per task (default: 10)
- `completePercentage` (optional): % to mark complete 0-100 (default: 50)
- `includeFinancialData` (optional): Create revenue records (default: true)

**Example:**
```json
{
  "scenario": "small"
}
```

### cleanup_test_data

Cleans up test data created by generate_test_data.

**Parameters:**
- `testDataResult` (required): The TestDataResult object from generate_test_data

**Example:**
```json
{
  "testDataResult": {
    "projectIds": ["..."],
    "scopeIds": ["..."],
    "taskIds": ["..."],
    "apparatusIds": ["..."],
    "revenueIds": ["..."]
  }
}
```

## 🎉 Success!

If you can see and execute these tools, congratulations! The resa-testing-mcp server is fully operational.

**Next Steps:**
- Run integration tests to validate the Dataverse solution
- Use generate_test_data to create test scenarios
- Validate rollup and calculated fields
- Build resa-docs-mcp (Week 2)

---

**Server Version:** 1.0.0  
**Build Date:** November 23, 2025  
**Status:** ✅ Production Ready (Development Environment Only)
