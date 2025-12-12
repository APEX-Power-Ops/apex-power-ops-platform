#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// Import tools
import { generateTableDocumentation } from "./tools/generate-table-docs.js";
import { generateERDiagram } from "./tools/generate-erd-diagram.js";
import { generateUserGuide } from "./tools/generate-user-guide.js";
import { generateAPIDocumentation } from "./tools/generate-api-docs.js";

// Create MCP server
const server = new Server(
  {
    name: "resa-docs-mcp",
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
        name: "generate_table_documentation",
        description:
          "Generate comprehensive documentation for a Dataverse table including fields, relationships, calculated fields, rollup fields, and usage examples. Outputs formatted Markdown or HTML.",
        inputSchema: {
          type: "object",
          properties: {
            tableName: {
              type: "string",
              description:
                "Logical name of the table (e.g., 'cr950_projectses', 'cr950_projectscopes')",
            },
            includeFields: {
              type: "boolean",
              description: "Include field definitions (default: true)",
            },
            includeRelationships: {
              type: "boolean",
              description: "Include relationship metadata (default: true)",
            },
            includeBusinessRules: {
              type: "boolean",
              description: "Include business rules (default: true)",
            },
            outputFormat: {
              type: "string",
              enum: ["markdown", "html"],
              description: "Output format (default: markdown)",
            },
          },
          required: ["tableName"],
        },
      },
      {
        name: "generate_erd_diagram",
        description:
          "Generate Entity Relationship Diagram (ERD) from Dataverse schema in Mermaid or PlantUML format. Shows tables, fields, and relationships visually.",
        inputSchema: {
          type: "object",
          properties: {
            tables: {
              type: "array",
              items: { type: "string" },
              description:
                "Optional: specific tables to include. If omitted, includes all custom tables (cr950_*)",
            },
            includeAllRelationships: {
              type: "boolean",
              description:
                "Include relationships to system tables (default: true)",
            },
            format: {
              type: "string",
              enum: ["mermaid", "plantuml"],
              description: "Diagram format (default: mermaid)",
            },
          },
        },
      },
      {
        name: "generate_user_guide",
        description:
          "Generate role-specific user guide with workflows, permissions, and step-by-step instructions. Available roles: FieldTech, JobLead, PM, Billing, Executive.",
        inputSchema: {
          type: "object",
          properties: {
            role: {
              type: "string",
              enum: ["FieldTech", "JobLead", "PM", "Billing", "Executive"],
              description: "User role to generate guide for",
            },
            includeScreenshots: {
              type: "boolean",
              description:
                "Include screenshot placeholders (default: false)",
            },
            outputFormat: {
              type: "string",
              enum: ["markdown", "docx", "pdf"],
              description: "Output format (default: markdown)",
            },
          },
          required: ["role"],
        },
      },
      {
        name: "generate_api_docs",
        description:
          "Generate OpenAPI 3.0 specification for the Dataverse REST API. Includes all CRUD endpoints, schemas, authentication, and examples.",
        inputSchema: {
          type: "object",
          properties: {
            format: {
              type: "string",
              enum: ["openapi", "markdown"],
              description: "Documentation format (default: openapi)",
            },
            includeExamples: {
              type: "boolean",
              description: "Include example requests/responses (default: true)",
            },
          },
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    switch (request.params.name) {
      case "generate_table_documentation": {
        const result = await generateTableDocumentation(
          request.params.arguments as any
        );
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "generate_erd_diagram": {
        const result = await generateERDiagram(
          request.params.arguments as any
        );
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "generate_user_guide": {
        const result = await generateUserGuide(
          request.params.arguments as any
        );
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "generate_api_docs": {
        const result = await generateAPIDocumentation(
          request.params.arguments as any
        );
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
        throw new Error(`Unknown tool: ${request.params.name}`);
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              error: error.message,
              stack: error.stack,
            },
            null,
            2
          ),
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  console.error("RESA Docs MCP Server starting...");
  console.error(
    `Environment: ${process.env.ENVIRONMENT || "DEVELOPMENT"}`
  );
  console.error(
    `Dataverse URL: ${
      process.env.DATAVERSE_URL ||
      "https://org99cd6c6e.crm.dynamics.com"
    }`
  );

  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error("RESA Docs MCP Server running");
  console.error("Available tools:");
  console.error(
    "  - generate_table_documentation: Generate table documentation"
  );
  console.error("  - generate_erd_diagram: Generate ERD diagrams");
  console.error("  - generate_user_guide: Generate role-specific user guides");
  console.error("  - generate_api_docs: Generate OpenAPI specifications");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
