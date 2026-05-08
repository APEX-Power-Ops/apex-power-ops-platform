#!/usr/bin/env node
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

function expandHome(value: string): string {
  if (value === "~") {
    return os.homedir();
  }

  if (value.startsWith("~/") || value.startsWith("~\\")) {
    return path.join(os.homedir(), value.slice(2));
  }

  return value;
}

const workspaceRoot = path.resolve(
  expandHome(process.env.APEX_MCP_WORKSPACE_ROOT ?? path.join(process.cwd(), "..", "..", "..")),
);
const dataRoot = path.resolve(
  expandHome(process.env.APEX_MCP_DATA_ROOT ?? path.join(os.homedir(), "apex-data")),
);
const port = Number(process.env.APEX_MCP_HTTP_PORT ?? 8710);
const basePath = process.env.APEX_MCP_BASE_PATH ?? "/mcp";

const roots = {
  workspace: workspaceRoot,
  data: dataRoot,
} as const;

type RootName = keyof typeof roots;

const tools = [
  {
    name: "list_roots",
    description: "List the filesystem roots exposed by the APEX MCP filesystem server.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "list_directory",
    description: "List a directory inside the workspace or apex-data root.",
    inputSchema: {
      type: "object",
      properties: {
        root: { type: "string", enum: ["workspace", "data"] },
        relativePath: { type: "string" },
      },
      required: ["root"],
    },
  },
  {
    name: "read_text_file",
    description: "Read a UTF-8 text file inside the workspace or apex-data root.",
    inputSchema: {
      type: "object",
      properties: {
        root: { type: "string", enum: ["workspace", "data"] },
        relativePath: { type: "string" },
        maxBytes: { type: "number" },
      },
      required: ["root", "relativePath"],
    },
  },
];

function resolveSafePath(rootName: RootName, relativePath = "."): string {
  const rootPath = roots[rootName];
  const resolved = path.resolve(rootPath, relativePath);

  if (resolved !== rootPath && !resolved.startsWith(`${rootPath}${path.sep}`)) {
    throw new Error(`Path escapes ${rootName} root: ${relativePath}`);
  }

  return resolved;
}

async function listDirectory(rootName: RootName, relativePath = ".") {
  const targetPath = resolveSafePath(rootName, relativePath);
  const entries = await fs.readdir(targetPath, { withFileTypes: true });
  return entries.map((entry) => ({
    name: entry.name,
    type: entry.isDirectory() ? "directory" : "file",
  }));
}

async function readTextFile(rootName: RootName, relativePath: string, maxBytes = 50000): Promise<string> {
  const targetPath = resolveSafePath(rootName, relativePath);
  const content = await fs.readFile(targetPath, "utf8");
  return content.length > maxBytes ? content.slice(0, maxBytes) : content;
}

async function callTool(
  name: string,
  args: { root?: RootName; relativePath?: string; maxBytes?: number },
): Promise<unknown> {
  switch (name) {
    case "list_roots":
      return roots;
    case "list_directory":
      return {
        root: args.root ?? "workspace",
        relativePath: args.relativePath ?? ".",
        entries: await listDirectory(args.root ?? "workspace", args.relativePath ?? "."),
      };
    case "read_text_file": {
      const rootName = args.root ?? "workspace";
      const relativePath = args.relativePath;

      if (!relativePath) {
        throw new Error("relativePath is required");
      }

      return {
        root: rootName,
        relativePath,
        content: await readTextFile(rootName, relativePath, Number(args.maxBytes ?? 50000)),
      };
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
    sendJson(response, 200, { status: "ok", server: "apex-fs" });
    return;
  }

  if (request.method === "GET" && url.pathname === basePath) {
    sendJson(response, 200, {
      server_name: "apex-fs",
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
      arguments?: { root?: RootName; relativePath?: string; maxBytes?: number };
    };
  };

  if (message.method === "initialize") {
    sendJson(response, 200, {
      jsonrpc: "2.0",
      id: message.id ?? null,
      result: {
        protocolVersion: "2025-03-26",
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: "apex-fs", version: "0.1.0" },
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
  console.error(`apex-fs HTTP transport listening on ${port}`);
});