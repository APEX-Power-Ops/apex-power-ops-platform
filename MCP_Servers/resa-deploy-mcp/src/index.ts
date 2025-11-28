#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";

// Import deployment tools
import { exportSolution, listSolutions } from "./tools/export-solution.js";
import { importSolution } from "./tools/import-solution.js";
import { compareSolutions } from "./tools/compare-solutions.js";
import { backupSolution, listBackups, getBackupMetadata } from "./tools/backup-solution.js";
import { deploySolution, rollbackDeployment } from "./tools/deploy-solution.js";

// Create server instance
const server = new Server(
  {
    name: "resa-deploy-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool definitions
const TOOLS = [
  {
    name: "export_solution",
    description:
      "Export a Dataverse solution to a zip file. Supports both managed and unmanaged exports with full customization settings.",
    inputSchema: {
      type: "object",
      properties: {
        solutionName: {
          type: "string",
          description: "Unique name of the solution to export (e.g., 'ResaPowerBuild')",
        },
        version: {
          type: "string",
          description: "Version number for the export (optional, uses current version if not specified)",
        },
        managed: {
          type: "boolean",
          description: "Export as managed solution (true) or unmanaged (false). Default: false",
          default: false,
        },
        outputPath: {
          type: "string",
          description: "Output directory path. Default: C:\\RESA_Power_Build\\Solution_Exports",
        },
      },
      required: ["solutionName"],
    },
  },
  {
    name: "import_solution",
    description:
      "Import a solution zip file into Dataverse. Monitors the import job and reports progress and any errors.",
    inputSchema: {
      type: "object",
      properties: {
        filePath: {
          type: "string",
          description: "Full path to the solution zip file to import",
        },
        overwriteUnmanagedCustomizations: {
          type: "boolean",
          description: "Overwrite unmanaged customizations with managed solution. Default: false",
          default: false,
        },
        publishWorkflows: {
          type: "boolean",
          description: "Publish workflows after import. Default: true",
          default: true,
        },
        skipProductUpdateDependencies: {
          type: "boolean",
          description: "Skip checking product update dependencies. Default: false",
          default: false,
        },
      },
      required: ["filePath"],
    },
  },
  {
    name: "compare_solutions",
    description:
      "Compare two solutions to identify differences in components. Shows added, modified, and removed components between source and target.",
    inputSchema: {
      type: "object",
      properties: {
        sourceSolution: {
          type: "string",
          description: "Unique name of the source solution",
        },
        targetSolution: {
          type: "string",
          description: "Unique name of the target solution to compare against",
        },
        componentTypes: {
          type: "array",
          items: { type: "string" },
          description: "Optional array of component type codes to filter comparison (e.g., ['1', '29'] for entities and workflows)",
        },
      },
      required: ["sourceSolution", "targetSolution"],
    },
  },
  {
    name: "backup_solution",
    description:
      "Create a complete backup of a solution (both managed and unmanaged versions) with metadata. Essential before deployments.",
    inputSchema: {
      type: "object",
      properties: {
        solutionName: {
          type: "string",
          description: "Unique name of the solution to backup",
        },
        backupPath: {
          type: "string",
          description: "Backup directory path. Default: C:\\RESA_Power_Build\\Solution_Exports\\Backups",
        },
        notes: {
          type: "string",
          description: "Optional notes about this backup",
        },
      },
      required: ["solutionName"],
    },
  },
  {
    name: "deploy_solution",
    description:
      "Execute a complete deployment workflow: backup, export, import, and verify. Provides rollback capability if deployment fails.",
    inputSchema: {
      type: "object",
      properties: {
        solutionName: {
          type: "string",
          description: "Unique name of the solution to deploy",
        },
        createBackup: {
          type: "boolean",
          description: "Create pre-deployment backup. Default: true",
          default: true,
        },
        verifyImport: {
          type: "boolean",
          description: "Run post-deployment verification. Default: true",
          default: true,
        },
        overwriteUnmanagedCustomizations: {
          type: "boolean",
          description: "Overwrite unmanaged customizations. Default: false",
          default: false,
        },
        publishWorkflows: {
          type: "boolean",
          description: "Publish workflows after deployment. Default: true",
          default: true,
        },
      },
      required: ["solutionName"],
    },
  },
  {
    name: "list_solutions",
    description:
      "List all visible solutions in the Dataverse environment with their versions and managed status.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "list_backups",
    description:
      "List all available solution backups with metadata, sorted by timestamp (newest first).",
    inputSchema: {
      type: "object",
      properties: {
        solutionName: {
          type: "string",
          description: "Filter backups by solution name (optional)",
        },
        backupPath: {
          type: "string",
          description: "Backup directory path. Default: C:\\RESA_Power_Build\\Solution_Exports\\Backups",
        },
      },
    },
  },
  {
    name: "rollback_deployment",
    description:
      "Rollback a failed deployment by restoring from a backup. Requires backup ID from previous backup or deployment.",
    inputSchema: {
      type: "object",
      properties: {
        backupId: {
          type: "string",
          description: "Backup ID to restore from (timestamp-based ID from list_backups)",
        },
        solutionName: {
          type: "string",
          description: "Unique name of the solution",
        },
      },
      required: ["backupId", "solutionName"],
    },
  },
];

// List tools handler
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

// Call tool handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const { name, arguments: args } = request.params;

    if (!args) {
      throw new McpError(ErrorCode.InvalidParams, "Missing arguments");
    }

    switch (name) {
      case "export_solution": {
        const result = await exportSolution({
          solutionName: args.solutionName as string,
          version: args.version as string | undefined,
          managed: args.managed as boolean | undefined,
          outputPath: args.outputPath as string | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "import_solution": {
        const result = await importSolution({
          filePath: args.filePath as string,
          overwriteUnmanagedCustomizations: args.overwriteUnmanagedCustomizations as boolean | undefined,
          publishWorkflows: args.publishWorkflows as boolean | undefined,
          skipProductUpdateDependencies: args.skipProductUpdateDependencies as boolean | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "compare_solutions": {
        const result = await compareSolutions({
          sourceSolution: args.sourceSolution as string,
          targetSolution: args.targetSolution as string,
          componentTypes: args.componentTypes as string[] | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "backup_solution": {
        const result = await backupSolution({
          solutionName: args.solutionName as string,
          backupPath: args.backupPath as string | undefined,
          notes: args.notes as string | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "deploy_solution": {
        const result = await deploySolution({
          solutionName: args.solutionName as string,
          createBackup: args.createBackup as boolean | undefined,
          verifyImport: args.verifyImport as boolean | undefined,
          overwriteUnmanagedCustomizations: args.overwriteUnmanagedCustomizations as boolean | undefined,
          publishWorkflows: args.publishWorkflows as boolean | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "list_solutions": {
        const result = await listSolutions();
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "list_backups": {
        const result = await listBackups({
          solutionName: args.solutionName as string | undefined,
          backupPath: args.backupPath as string | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "rollback_deployment": {
        const result = await rollbackDeployment({
          backupId: args.backupId as string,
          solutionName: args.solutionName as string,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      default:
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${name}`
        );
    }
  } catch (error: any) {
    console.error(`Error executing tool: ${error.message}`);
    throw new McpError(
      ErrorCode.InternalError,
      `Tool execution failed: ${error.message}`
    );
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("resa-deploy-mcp server started");
  console.error("Available tools:");
  console.error("  - export_solution: Export Dataverse solutions to zip");
  console.error("  - import_solution: Import solution zips to Dataverse");
  console.error("  - compare_solutions: Compare two solutions for differences");
  console.error("  - backup_solution: Create backups (managed + unmanaged)");
  console.error("  - deploy_solution: Full deployment workflow with rollback");
  console.error("  - list_solutions: List all solutions in environment");
  console.error("  - list_backups: List all available backups");
  console.error("  - rollback_deployment: Restore from backup");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
