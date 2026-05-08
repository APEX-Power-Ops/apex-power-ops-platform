#!/usr/bin/env node
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import pg from "pg";

const { Pool } = pg;

const port = Number(process.env.APEX_MCP_HTTP_PORT ?? 8711);
const basePath = process.env.APEX_MCP_BASE_PATH ?? "/mcp";
const connectionString = process.env.APEX_DB_CONNECTION_STRING ?? process.env.DATABASE_URL;
const pool = connectionString ? new Pool({ connectionString }) : null;

const tools = [
  {
    name: "list_tables",
    description: "List base tables available in a PostgreSQL schema.",
    inputSchema: { type: "object", properties: { schema: { type: "string" } } },
  },
  {
    name: "describe_table",
    description: "Describe the columns on a PostgreSQL table.",
    inputSchema: {
      type: "object",
      properties: { schema: { type: "string" }, table: { type: "string" } },
      required: ["table"],
    },
  },
  {
    name: "query",
    description: "Run a read-only SELECT or WITH query against PostgreSQL.",
    inputSchema: {
      type: "object",
      properties: { sql: { type: "string" }, params: { type: "array", items: {} } },
      required: ["sql"],
    },
  },
];

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

async function callTool(
  name: string,
  args: { schema?: string; table?: string; sql?: string; params?: unknown[] },
): Promise<unknown> {
  switch (name) {
    case "list_tables": {
      const schema = args.schema ?? "public";
      const rows = await query(
        "select table_name from information_schema.tables where table_schema = $1 and table_type = 'BASE TABLE' order by table_name",
        [schema],
      );
      return { schema, tables: rows };
    }
    case "describe_table": {
      const schema = args.schema ?? "public";
      const table = args.table;

      if (!table) {
        throw new Error("table is required");
      }

      const rows = await query(
        "select column_name, data_type, is_nullable, column_default from information_schema.columns where table_schema = $1 and table_name = $2 order by ordinal_position",
        [schema, table],
      );
      return { schema, table, columns: rows };
    }
    case "query": {
      const sql = args.sql;

      if (!sql) {
        throw new Error("sql is required");
      }

      const params = args.params ?? [];
      const rows = await query(sql, params);
      return { rowCount: rows.length, rows };
    }
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

function sendJson(response: ServerResponse, statusCode: number, payload: unknown): void {
  response.writeHead(statusCode, { "Content-Type": "application/json" });
  response.end(JSON.stringify(payload));
}

async function readBody(request: IncomingMessage): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of request) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf8");
}

createServer(async (request, response) => {
  if (!request.url) {
    sendJson(response, 400, { error: "Missing request URL" });
    return;
  }

  const url = new URL(request.url, `http://127.0.0.1:${port}`);

  if (request.method === "GET" && url.pathname === "/health") {
    try {
      await query("select 1 as ok");
      sendJson(response, 200, { status: "ok", server: "apex-db" });
    } catch (error) {
      sendJson(response, 503, {
        status: "error",
        error: error instanceof Error ? error.message : String(error),
      });
    }
    return;
  }

  if (request.method === "GET" && url.pathname === basePath) {
    sendJson(response, 200, {
      server_name: "apex-db",
      server_version: "0.1.0",
      transport: { type: "streamable-http", mcp_path: basePath },
    });
    return;
  }

  if (request.method !== "POST" || url.pathname !== basePath) {
    sendJson(response, 404, { error: "Not found" });
    return;
  }

  const rawBody = await readBody(request);
  const message = JSON.parse(rawBody) as {
    id?: string | number | null;
    method?: string;
    params?: {
      name?: string;
      arguments?: { schema?: string; table?: string; sql?: string; params?: unknown[] };
    };
  };

  if (message.method === "initialize") {
    sendJson(response, 200, {
      jsonrpc: "2.0",
      id: message.id ?? null,
      result: {
        protocolVersion: "2025-03-26",
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: "apex-db", version: "0.1.0" },
      },
    });
    return;
  }

  if (message.method === "tools/list") {
    sendJson(response, 200, { jsonrpc: "2.0", id: message.id ?? null, result: { tools } });
    return;
  }

  if (message.method === "tools/call") {
    const params = message.params ?? {};
    try {
      const result = await callTool(String(params.name ?? ""), params.arguments ?? {});
      sendJson(response, 200, {
        jsonrpc: "2.0",
        id: message.id ?? null,
        result: {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
          structuredContent: result,
          isError: false,
        },
      });
    } catch (error) {
      sendJson(response, 200, {
        jsonrpc: "2.0",
        id: message.id ?? null,
        result: {
          content: [{ type: "text", text: error instanceof Error ? error.message : String(error) }],
          isError: true,
        },
      });
    }
    return;
  }

  sendJson(response, 200, {
    jsonrpc: "2.0",
    id: message.id ?? null,
    error: { code: -32601, message: `Method not found: ${message.method ?? ""}` },
  });
}).listen(port, "0.0.0.0", () => {
  console.error(`apex-db HTTP transport listening on ${port}`);
});