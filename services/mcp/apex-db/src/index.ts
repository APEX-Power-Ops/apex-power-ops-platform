#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import pg from "pg";

const { Pool } = pg;

const connectionString = process.env.APEX_DB_CONNECTION_STRING ?? process.env.DATABASE_URL;

if (!connectionString) {
  console.error("APEX_DB_CONNECTION_STRING or DATABASE_URL is required for apex-db.");
}

const pool = connectionString ? new Pool({ connectionString }) : null;

function assertReadOnly(sql: string): void {
  const trimmed = sql.trim();
  if (!/^(select|with)\b/i.test(trimmed)) {
    throw new Error("Only SELECT and WITH queries are allowed.");
  }

  if (/\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|comment|copy)\b/i.test(trimmed)) {
    throw new Error("Mutating SQL is not allowed by apex-db.");
  }
}

async function query(sql: string, params: unknown[] = []): Promise<Record<string, unknown>[]> {
  if (!pool) {
    throw new Error("Database connection is not configured.");
  }

  assertReadOnly(sql);
  const result = await pool.query(sql, params);
  return result.rows as Record<string, unknown>[];
}

const server = new Server(
  {
    name: "apex-db",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "list_tables",
      description: "List base tables available in a PostgreSQL schema.",
      inputSchema: {
        type: "object",
        properties: {
          schema: {
            type: "string",
          },
        },
      },
    },
    {
      name: "describe_table",
      description: "Describe the columns on a PostgreSQL table.",
      inputSchema: {
        type: "object",
        properties: {
          schema: {
            type: "string",
          },
          table: {
            type: "string",
          },
        },
        required: ["table"],
      },
    },
    {
      name: "query",
      description: "Run a read-only SELECT or WITH query against PostgreSQL.",
      inputSchema: {
        type: "object",
        properties: {
          sql: {
            type: "string",
          },
          params: {
            type: "array",
            items: {},
          },
        },
        required: ["sql"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const args = (request.params.arguments ?? {}) as {
      schema?: string;
      table?: string;
      sql?: string;
      params?: unknown[];
    };

    switch (request.params.name) {
      case "list_tables": {
        const schema = args.schema ?? "public";
        const rows = await query(
          `
          select table_name
          from information_schema.tables
          where table_schema = $1 and table_type = 'BASE TABLE'
          order by table_name
          `,
          [schema],
        );
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ schema, tables: rows }, null, 2),
            },
          ],
        };
      }

      case "describe_table": {
        const schema = args.schema ?? "public";
        const table = args.table;

        if (!table) {
          throw new Error("table is required");
        }

        const rows = await query(
          `
          select
            column_name,
            data_type,
            is_nullable,
            column_default
          from information_schema.columns
          where table_schema = $1 and table_name = $2
          order by ordinal_position
          `,
          [schema, table],
        );
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ schema, table, columns: rows }, null, 2),
            },
          ],
        };
      }

      case "query": {
        const sql = args.sql;

        if (!sql) {
          throw new Error("sql is required");
        }

        const params = args.params ?? [];
        const rows = await query(sql, params);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ rowCount: rows.length, rows }, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${request.params.name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              error: error instanceof Error ? error.message : String(error),
            },
            null,
            2,
          ),
        },
      ],
      isError: true,
    };
  }
});

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(async (error) => {
  console.error(error);
  await pool?.end();
  process.exit(1);
});