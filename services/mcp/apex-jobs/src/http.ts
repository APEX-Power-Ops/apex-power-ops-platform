#!/usr/bin/env node
import { createServer } from "node:http";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

type RunEnv = "sandbox" | "host";
type RunStatus = "running" | "success" | "failure" | "canceled";

type LedgerRun = {
  run_id: string;
  env: RunEnv;
  service: string;
  packet_id?: string;
  status: RunStatus;
  created_at: string;
  notes?: string;
  completed_at?: string;
};

type LedgerPromotion = {
  packet_id: string;
  promoted_at: string;
  supporting_run_ids: string[];
};

type Ledger = {
  runs: LedgerRun[];
  promotions: LedgerPromotion[];
};

type ToolArgs = {
  env?: RunEnv;
  service?: string;
  packet_id?: string;
  run_id?: string;
  status?: Exclude<RunStatus, "running">;
  notes?: string;
  since?: string;
};

function expandHome(value: string): string {
  if (value === "~") return os.homedir();
  if (value.startsWith("~/") || value.startsWith("~\\")) {
    return path.join(os.homedir(), value.slice(2));
  }
  return value;
}

const ledgerPath = path.resolve(
  expandHome(
    process.env.APEX_JOBS_LEDGER_PATH ??
      path.join(os.homedir(), "apex-data", "apex-jobs-ledger.json"),
  ),
);
const port = Number(process.env.APEX_MCP_HTTP_PORT ?? 8712);
const basePath = process.env.APEX_MCP_BASE_PATH ?? "/mcp";

const tools = [
  {
    name: "start_run",
    description: "Start a run in the APEX jobs ledger.",
    inputSchema: {
      type: "object",
      properties: {
        env: { type: "string", enum: ["sandbox", "host"] },
        service: { type: "string" },
        packet_id: { type: "string" },
      },
      required: ["env", "service"],
    },
  },
  {
    name: "end_run",
    description: "Finish a run in the APEX jobs ledger.",
    inputSchema: {
      type: "object",
      properties: {
        run_id: { type: "string" },
        status: { type: "string", enum: ["success", "failure", "canceled"] },
        notes: { type: "string" },
      },
      required: ["run_id", "status"],
    },
  },
  {
    name: "list_runs",
    description: "List runs from the APEX jobs ledger with optional filters.",
    inputSchema: {
      type: "object",
      properties: {
        env: { type: "string", enum: ["sandbox", "host"] },
        service: { type: "string" },
        packet_id: { type: "string" },
        since: { type: "string" },
        status: { type: "string", enum: ["running", "success", "failure", "canceled"] },
      },
    },
  },
  {
    name: "promote_packet",
    description: "Promote a packet only when at least one host run exists for it.",
    inputSchema: {
      type: "object",
      properties: { packet_id: { type: "string" } },
      required: ["packet_id"],
    },
  },
];

async function ensureLedger(): Promise<Ledger> {
  await fs.mkdir(path.dirname(ledgerPath), { recursive: true });

  try {
    const raw = await fs.readFile(ledgerPath, "utf8");
    return JSON.parse(raw) as Ledger;
  } catch (error) {
    if (!(error && typeof error === "object" && "code" in error && error.code === "ENOENT")) {
      throw error;
    }

    const initial: Ledger = { runs: [], promotions: [] };
    await fs.writeFile(ledgerPath, JSON.stringify(initial, null, 2));
    return initial;
  }
}

async function writeLedger(ledger: Ledger): Promise<void> {
  await fs.writeFile(ledgerPath, JSON.stringify(ledger, null, 2));
}

function createRunId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

async function callTool(name: string, args: ToolArgs): Promise<LedgerRun | LedgerPromotion | { runs: LedgerRun[] }> {
  switch (name) {
    case "start_run": {
      const ledger = await ensureLedger();
      const run: LedgerRun = {
        run_id: createRunId(),
        env: args.env ?? "sandbox",
        service: args.service ?? "unknown",
        packet_id: args.packet_id,
        status: "running",
        created_at: new Date().toISOString(),
      };
      ledger.runs.push(run);
      await writeLedger(ledger);
      return run;
    }

    case "end_run": {
      const ledger = await ensureLedger();
      const run = ledger.runs.find((entry) => entry.run_id === args.run_id);

      if (!run) {
        throw new Error(`Run not found: ${String(args.run_id)}`);
      }

      run.status = args.status ?? "failure";
      run.notes = args.notes;
      run.completed_at = new Date().toISOString();
      await writeLedger(ledger);
      return run;
    }

    case "list_runs": {
      const ledger = await ensureLedger();
      const since = args.since ? new Date(String(args.since)).toISOString() : null;
      const runs = ledger.runs.filter((run) => {
        if (args.env && run.env !== args.env) return false;
        if (args.service && run.service !== args.service) return false;
        if (args.packet_id && run.packet_id !== args.packet_id) return false;
        if (args.status && run.status !== args.status) return false;
        if (since && run.created_at < since) return false;
        return true;
      });
      return { runs };
    }

    case "promote_packet": {
      const packetId = args.packet_id;

      if (!packetId) {
        throw new Error("packet_id is required");
      }

      const ledger = await ensureLedger();
      const supportingRuns = ledger.runs.filter(
        (run) => run.packet_id === packetId && run.env === "host" && run.status === "success",
      );

      if (supportingRuns.length === 0) {
        throw new Error(`Packet ${packetId} cannot be promoted: no successful env=host run is on record.`);
      }

      const promotion: LedgerPromotion = {
        packet_id: packetId,
        promoted_at: new Date().toISOString(),
        supporting_run_ids: supportingRuns.map((run) => run.run_id),
      };
      ledger.promotions.push(promotion);
      await writeLedger(ledger);
      return promotion;
    }

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

function sendJson(response: import("node:http").ServerResponse, statusCode: number, payload: unknown): void {
  response.writeHead(statusCode, { "Content-Type": "application/json" });
  response.end(JSON.stringify(payload));
}

async function readBody(request: import("node:http").IncomingMessage): Promise<string> {
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
    await ensureLedger();
    sendJson(response, 200, { status: "ok", server: "apex-jobs", ledgerPath });
    return;
  }

  if (request.method === "GET" && url.pathname === basePath) {
    sendJson(response, 200, {
      server_name: "apex-jobs",
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
    jsonrpc?: string;
    id?: string | number | null;
    method?: string;
    params?: {
      name?: string;
      arguments?: ToolArgs;
    };
  };

  if (message.method === "initialize") {
    sendJson(response, 200, {
      jsonrpc: "2.0",
      id: message.id ?? null,
      result: {
        protocolVersion: "2025-03-26",
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: "apex-jobs", version: "0.1.0" },
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
  console.error(`apex-jobs HTTP transport listening on ${port}`);
});