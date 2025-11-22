#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";

// Environment configuration
const DATAVERSE_URL = process.env.DATAVERSE_URL || "";
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID || "";
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || "";
const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET || "";
const ENVIRONMENT = process.env.ENVIRONMENT || "PRODUCTION";

// Safety check
if (ENVIRONMENT === "PRODUCTION" && DATAVERSE_URL.includes("org04ad071f")) {
  throw new Error("FATAL: Cannot connect MCP to RESA production environment!");
}

// Token management
let accessToken: string | null = null;
let tokenExpiry: number = 0;

async function getAccessToken(): Promise<string> {
  const now = Date.now();
  
  // Reuse token if still valid (with 5 minute buffer)
  if (accessToken && tokenExpiry > now + 300000) {
    return accessToken;
  }
  
  const tokenUrl = `https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token`;
  const params = new URLSearchParams({
    client_id: AZURE_CLIENT_ID,
    scope: `${DATAVERSE_URL}/.default`,
    client_secret: AZURE_CLIENT_SECRET,
    grant_type: "client_credentials",
  });
  
  try {
    const response = await axios.post(tokenUrl, params.toString(), {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    
    accessToken = response.data.access_token;
    tokenExpiry = now + (response.data.expires_in * 1000);
    
    return accessToken!;
  } catch (error: any) {
    throw new Error(`Authentication failed: ${error.message}`);
  }
}

async function queryDataverse(
  entityName: string,
  select?: string,
  filter?: string,
  top?: number
): Promise<any> {
  const token = await getAccessToken();
  
  let url = `${DATAVERSE_URL}/api/data/v9.2/${entityName}`;
  const params: string[] = [];
  
  if (select) params.push(`$select=${select}`);
  if (filter) params.push(`$filter=${filter}`);
  if (top) params.push(`$top=${top}`);
  
  if (params.length > 0) {
    url += `?${params.join("&")}`;
  }
  
  const response = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      Accept: "application/json",
    },
  });
  
  return response.data.value;
}

async function createRecord(entityName: string, data: any): Promise<string> {
  const token = await getAccessToken();
  const url = `${DATAVERSE_URL}/api/data/v9.2/${entityName}`;
  
  const response = await axios.post(url, data, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      "Content-Type": "application/json; charset=utf-8",
      Accept: "application/json",
      Prefer: "return=representation",
    },
  });
  
  return response.headers["odata-entityid"] || response.data["@odata.id"] || "created";
}

async function updateRecord(
  entityName: string,
  recordId: string,
  data: any
): Promise<void> {
  const token = await getAccessToken();
  const url = `${DATAVERSE_URL}/api/data/v9.2/${entityName}(${recordId})`;
  
  await axios.patch(url, data, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      "Content-Type": "application/json; charset=utf-8",
    },
  });
}

async function deleteRecord(entityName: string, recordId: string): Promise<void> {
  const token = await getAccessToken();
  const url = `${DATAVERSE_URL}/api/data/v9.2/${entityName}(${recordId})`;
  
  await axios.delete(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
    },
  });
}

// Create MCP server
const server = new Server(
  {
    name: "resa-dataverse-mcp",
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
        name: "query_dataverse",
        description: "Query records from a Dataverse table",
        inputSchema: {
          type: "object",
          properties: {
            entityName: {
              type: "string",
              description: "Logical name of the table (e.g., 'cr950_projectses', 'cr950_apparatus')",
            },
            select: {
              type: "string",
              description: "Comma-separated list of fields to retrieve",
            },
            filter: {
              type: "string",
              description: "OData filter expression",
            },
            top: {
              type: "number",
              description: "Maximum number of records to return (default: 50)",
            },
          },
          required: ["entityName"],
        },
      },
      {
        name: "create_record",
        description: "Create a new record in Dataverse",
        inputSchema: {
          type: "object",
          properties: {
            entityName: {
              type: "string",
              description: "Logical name of the table",
            },
            data: {
              type: "object",
              description: "Record data as JSON object",
            },
          },
          required: ["entityName", "data"],
        },
      },
      {
        name: "update_record",
        description: "Update an existing record in Dataverse",
        inputSchema: {
          type: "object",
          properties: {
            entityName: {
              type: "string",
              description: "Logical name of the table",
            },
            recordId: {
              type: "string",
              description: "GUID of the record to update",
            },
            data: {
              type: "object",
              description: "Fields to update as JSON object",
            },
          },
          required: ["entityName", "recordId", "data"],
        },
      },
      {
        name: "delete_record",
        description: "Delete a record from Dataverse",
        inputSchema: {
          type: "object",
          properties: {
            entityName: {
              type: "string",
              description: "Logical name of the table",
            },
            recordId: {
              type: "string",
              description: "GUID of the record to delete",
            },
          },
          required: ["entityName", "recordId"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    switch (request.params.name) {
      case "query_dataverse": {
        const { entityName, select, filter, top } = request.params.arguments as any;
        const results = await queryDataverse(entityName, select, filter, top || 50);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(results, null, 2),
            },
          ],
        };
      }
      
      case "create_record": {
        const { entityName, data } = request.params.arguments as any;
        const recordId = await createRecord(entityName, data);
        return {
          content: [
            {
              type: "text",
              text: `Record created successfully. ID: ${recordId}`,
            },
          ],
        };
      }
      
      case "update_record": {
        const { entityName, recordId, data } = request.params.arguments as any;
        await updateRecord(entityName, recordId, data);
        return {
          content: [
            {
              type: "text",
              text: "Record updated successfully",
            },
          ],
        };
      }
      
      case "delete_record": {
        const { entityName, recordId } = request.params.arguments as any;
        await deleteRecord(entityName, recordId);
        return {
          content: [
            {
              type: "text",
              text: "Record deleted successfully",
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
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  console.error("RESA Dataverse MCP Server starting...");
  console.error(`Environment: ${ENVIRONMENT}`);
  console.error(`Dataverse URL: ${DATAVERSE_URL}`);
  
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error("RESA Dataverse MCP Server running");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
