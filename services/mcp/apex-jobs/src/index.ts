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

import {
  optionalPacketId,
  optionalRunEnv,
  optionalRunStatus,
  optionalService,
  optionalSince,
  requireClosedRunStatus,
  requirePacketId,
  requireRunEnv,
  requireRunId,
  requireService,
  type RunEnv,
  type RunStatus,
} from "./validation.js";

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

function expandHome(value: string): string {
  if (value === "~") {
    return os.homedir();
  }

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

const server = new Server(
  {
    name: "apex-jobs",
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
      name: "start_run",
      description: "Start a run in the APEX jobs ledger.",
      inputSchema: {
        type: "object",
        properties: {
          env: {
            type: "string",
            enum: ["sandbox", "host"],
          },
          service: {
            type: "string",
          },
          packet_id: {
            type: "string",
          },
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
          run_id: {
            type: "string",
          },
          status: {
            type: "string",
            enum: ["success", "failure", "canceled"],
          },
          notes: {
            type: "string",
          },
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
          env: {
            type: "string",
            enum: ["sandbox", "host"],
          },
          service: {
            type: "string",
          },
          packet_id: {
            type: "string",
          },
          since: {
            type: "string",
          },
          status: {
            type: "string",
            enum: ["running", "success", "failure", "canceled"],
          },
        },
      },
    },
    {
      name: "promote_packet",
      description: "Promote a packet only when at least one host run exists for it.",
      inputSchema: {
        type: "object",
        properties: {
          packet_id: {
            type: "string",
          },
        },
        required: ["packet_id"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const args = (request.params.arguments ?? {}) as {
      env?: unknown;
      service?: unknown;
      packet_id?: unknown;
      run_id?: unknown;
      status?: unknown;
      notes?: string;
      since?: unknown;
    };

    switch (request.params.name) {
      case "start_run": {
        const ledger = await ensureLedger();
        const run: LedgerRun = {
          run_id: createRunId(),
          env: requireRunEnv(args.env),
          service: requireService(args.service),
          packet_id: optionalPacketId(args.packet_id),
          status: "running",
          created_at: new Date().toISOString(),
        };
        ledger.runs.push(run);
        await writeLedger(ledger);
        return {
          content: [{ type: "text", text: JSON.stringify(run, null, 2) }],
        };
      }

      case "end_run": {
        const ledger = await ensureLedger();
        const runId = requireRunId(args.run_id);
        const run = ledger.runs.find((entry) => entry.run_id === runId);

        if (!run) {
          throw new Error(`Run not found: ${runId}`);
        }

        run.status = requireClosedRunStatus(args.status);
        run.notes = args.notes;
        run.completed_at = new Date().toISOString();
        await writeLedger(ledger);
        return {
          content: [{ type: "text", text: JSON.stringify(run, null, 2) }],
        };
      }

      case "list_runs": {
        const ledger = await ensureLedger();
        const env = optionalRunEnv(args.env);
        const service = optionalService(args.service);
        const packetId = optionalPacketId(args.packet_id);
        const status = optionalRunStatus(args.status);
        const since = optionalSince(args.since);
        const runs = ledger.runs.filter((run) => {
          if (env && run.env !== env) return false;
          if (service && run.service !== service) return false;
          if (packetId && run.packet_id !== packetId) return false;
          if (status && run.status !== status) return false;
          if (since && run.created_at < since) return false;
          return true;
        });

        return {
          content: [{ type: "text", text: JSON.stringify({ runs }, null, 2) }],
        };
      }

      case "promote_packet": {
        const packetId = requirePacketId(args.packet_id);

        const ledger = await ensureLedger();
        const supportingRuns = ledger.runs.filter(
          (run) => run.packet_id === packetId && run.env === "host" && run.status === "success",
        );

        if (supportingRuns.length === 0) {
          throw new Error(
            `Packet ${packetId} cannot be promoted: no successful env=host run is on record.`,
          );
        }

        const promotion: LedgerPromotion = {
          packet_id: packetId,
          promoted_at: new Date().toISOString(),
          supporting_run_ids: supportingRuns.map((run) => run.run_id),
        };
        ledger.promotions.push(promotion);
        await writeLedger(ledger);
        return {
          content: [{ type: "text", text: JSON.stringify(promotion, null, 2) }],
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
              ledgerPath,
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