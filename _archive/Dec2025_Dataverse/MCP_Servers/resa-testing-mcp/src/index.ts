#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// Import tools
import { validateRollupFields } from "./tools/validate-rollups.js";
import { testCalculatedFields } from "./tools/test-calculated-fields.js";
import { runIntegrationTests } from "./tools/run-integration-tests.js";
import { generateTestData, cleanupTestData } from "./tools/generate-test-data.js";

// Create MCP server
const server = new Server(
  {
    name: "resa-testing-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "validate_rollup_fields",
        description: "Validate rollup fields by comparing system-calculated values against manual calculations. Tests accuracy of rollup field formulas on real data.",
        inputSchema: {
          type: "object",
          properties: {
            tableName: {
              type: "string",
              description: "Logical name of the table (e.g., 'cr950_projectscopes', 'cr950_projectses')",
            },
            fieldNames: {
              type: "array",
              items: { type: "string" },
              description: "Optional: specific rollup field names to test. If omitted, tests all rollup fields on the table.",
            },
            sampleSize: {
              type: "number",
              description: "Number of records to test (default: 5)",
            },
            compareManual: {
              type: "boolean",
              description: "Whether to manually calculate expected values (default: true)",
            },
          },
          required: ["tableName"],
        },
      },
      {
        name: "test_calculated_fields",
        description: "Test calculated fields by verifying their formulas produce correct results. Validates 30 calculated field formulas across all tables.",
        inputSchema: {
          type: "object",
          properties: {
            tableName: {
              type: "string",
              description: "Logical name of the table (e.g., 'cr950_projectses', 'cr950_apparatusrevenues')",
            },
            fieldNames: {
              type: "array",
              items: { type: "string" },
              description: "Optional: specific calculated field names to test",
            },
            testCases: {
              type: "array",
              description: "Optional: custom test cases with known inputs/outputs",
            },
          },
          required: ["tableName"],
        },
      },
      {
        name: "run_integration_tests",
        description: "Run end-to-end integration tests for complete workflows. Tests entire business processes from start to finish including apparatus completion, project creation, rollup propagation, and bulk operations.",
        inputSchema: {
          type: "object",
          properties: {
            scenarioName: {
              type: "string",
              enum: [
                "apparatus_completion_flow",
                "new_project_creation",
                "rollup_propagation",
                "bulk_operations",
              ],
              description: "Test scenario to run",
            },
            cleanup: {
              type: "boolean",
              description: "Whether to clean up test data after execution (default: true)",
            },
          },
          required: ["scenarioName"],
        },
      },
      {
        name: "generate_test_data",
        description: "Generate realistic test data hierarchies (projects → scopes → tasks → apparatus → revenue). Creates complete data structures for testing rollup fields and workflows.",
        inputSchema: {
          type: "object",
          properties: {
            scenario: {
              type: "string",
              enum: ["small", "medium", "large", "custom"],
              description: "Predefined scenario or 'custom' for manual configuration",
            },
            projects: {
              type: "number",
              description: "Number of projects to create (default: 1)",
            },
            scopesPerProject: {
              type: "number",
              description: "Number of scopes per project (default: 2)",
            },
            tasksPerScope: {
              type: "number",
              description: "Number of tasks per scope (default: 3)",
            },
            apparatusPerTask: {
              type: "number",
              description: "Number of apparatus per task (default: 10)",
            },
            completePercentage: {
              type: "number",
              description: "Percentage of apparatus to mark complete 0-100 (default: 50)",
            },
            includeFinancialData: {
              type: "boolean",
              description: "Whether to create revenue records for completed apparatus (default: true)",
            },
          },
        },
      },
      {
        name: "cleanup_test_data",
        description: "Clean up test data created by generate_test_data. Deletes all records in reverse order (revenue → apparatus → tasks → scopes → projects) to maintain referential integrity.",
        inputSchema: {
          type: "object",
          properties: {
            testDataResult: {
              type: "object",
              description: "The TestDataResult object returned by generate_test_data containing record IDs to delete",
            },
          },
          required: ["testDataResult"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    switch (request.params.name) {
      case "validate_rollup_fields": {
        const result = await validateRollupFields(request.params.arguments as any);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "test_calculated_fields": {
        const result = await testCalculatedFields(request.params.arguments as any);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "run_integration_tests": {
        const result = await runIntegrationTests(request.params.arguments as any);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "generate_test_data": {
        const result = await generateTestData(request.params.arguments as any);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "cleanup_test_data": {
        const args = request.params.arguments as any;
        await cleanupTestData(args.testDataResult);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                status: "success",
                message: "Test data cleaned up successfully",
                timestamp: new Date().toISOString(),
              }, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${request.params.name}`);
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: error.message,
            stack: error.stack,
          }, null, 2),
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  console.error("RESA Testing MCP Server starting...");
  console.error(`Environment: ${process.env.ENVIRONMENT || "DEVELOPMENT"}`);
  console.error(`Dataverse URL: ${process.env.DATAVERSE_URL || "https://org99cd6c6e.crm.dynamics.com"}`);
  
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error("RESA Testing MCP Server running");
  console.error("Available tools:");
  console.error("  - validate_rollup_fields: Validate rollup field calculations");
  console.error("  - test_calculated_fields: Test calculated field formulas");
  console.error("  - run_integration_tests: Run end-to-end workflow tests");
  console.error("  - generate_test_data: Create test data hierarchies");
  console.error("  - cleanup_test_data: Delete test data");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
