#!/usr/bin/env node
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

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

const roots = {
  workspace: workspaceRoot,
  data: dataRoot,
} as const;

type RootName = keyof typeof roots;

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

const server = new Server(
  {
    name: "apex-fs",
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
      name: "list_roots",
      description: "List the filesystem roots exposed by the APEX MCP filesystem server.",
      inputSchema: {
        type: "object",
        properties: {},
      },
    },
    {
      name: "list_directory",
      description: "List a directory inside the workspace or apex-data root.",
      inputSchema: {
        type: "object",
        properties: {
          root: {
            type: "string",
            enum: ["workspace", "data"],
          },
          relativePath: {
            type: "string",
          },
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
          root: {
            type: "string",
            enum: ["workspace", "data"],
          },
          relativePath: {
            type: "string",
          },
          maxBytes: {
            type: "number",
          },
        },
        required: ["root", "relativePath"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const args = (request.params.arguments ?? {}) as {
      root?: RootName;
      relativePath?: string;
      maxBytes?: number;
    };

    switch (request.params.name) {
      case "list_roots":
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(roots, null, 2),
            },
          ],
        };

      case "list_directory": {
        const rootName = args.root ?? "workspace";
        const relativePath = args.relativePath ?? ".";
        const entries = await listDirectory(rootName, relativePath);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ root: rootName, relativePath, entries }, null, 2),
            },
          ],
        };
      }

      case "read_text_file": {
        const rootName = args.root ?? "workspace";
        const relativePath = args.relativePath;

        if (!relativePath) {
          throw new Error("relativePath is required");
        }

        const maxBytes = Number(args.maxBytes ?? 50000);
        const content = await readTextFile(rootName, relativePath, maxBytes);
        return {
          content: [
            {
              type: "text",
              text: content,
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

main().catch((error) => {
  console.error(error);
  process.exit(1);
});