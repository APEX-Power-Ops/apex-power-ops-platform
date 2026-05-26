#!/usr/bin/env node

import { createServer } from "node:http"

import { callTool, getRuntimeBaseUrl, getTemplateRoot, tools } from "./runtime-client.js"

const port = Number(process.env.APEX_MCP_HTTP_PORT ?? 8714)
const basePath = process.env.APEX_MCP_BASE_PATH ?? "/mcp"

function sendJson(response: import("node:http").ServerResponse, statusCode: number, payload: unknown) {
  response.writeHead(statusCode, { "Content-Type": "application/json" })
  response.end(JSON.stringify(payload))
}

async function readBody(request: import("node:http").IncomingMessage) {
  const chunks: Buffer[] = []
  for await (const chunk of request) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
  }
  return Buffer.concat(chunks).toString("utf8")
}

createServer(async (request, response) => {
  if (!request.url) {
    sendJson(response, 400, { error: "Missing request URL" })
    return
  }

  const url = new URL(request.url, `http://127.0.0.1:${port}`)

  if (request.method === "GET" && url.pathname === "/health") {
    try {
      const result = await callTool("get_runtime_status")
      sendJson(response, 200, {
        status: "ok",
        server: "apex-forms",
        runtime: getRuntimeBaseUrl(),
        templateRoot: getTemplateRoot(),
        result,
      })
    } catch (error) {
      sendJson(response, 503, {
        status: "error",
        server: "apex-forms",
        runtime: getRuntimeBaseUrl(),
        templateRoot: getTemplateRoot(),
        error: error instanceof Error ? error.message : String(error),
      })
    }
    return
  }

  if (request.method === "GET" && url.pathname === basePath) {
    sendJson(response, 200, {
      server_name: "apex-forms",
      server_version: "0.1.0",
      transport: { type: "streamable-http", mcp_path: basePath },
    })
    return
  }

  if (request.method !== "POST" || url.pathname !== basePath) {
    sendJson(response, 404, { error: "Not found" })
    return
  }

  const rawBody = await readBody(request)
  const message = JSON.parse(rawBody) as {
    id?: string | number | null
    method?: string
    params?: { name?: string; arguments?: Record<string, unknown> }
  }

  if (message.method === "initialize") {
    sendJson(response, 200, {
      jsonrpc: "2.0",
      id: message.id ?? null,
      result: {
        protocolVersion: "2025-03-26",
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: "apex-forms", version: "0.1.0" },
      },
    })
    return
  }

  if (message.method === "tools/list") {
    sendJson(response, 200, { jsonrpc: "2.0", id: message.id ?? null, result: { tools } })
    return
  }

  if (message.method === "tools/call") {
    const params = message.params ?? {}
    try {
      const result = await callTool(String(params.name ?? ""), params.arguments ?? {})
      sendJson(response, 200, {
        jsonrpc: "2.0",
        id: message.id ?? null,
        result: {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
          structuredContent: result,
          isError: false,
        },
      })
    } catch (error) {
      sendJson(response, 200, {
        jsonrpc: "2.0",
        id: message.id ?? null,
        result: {
          content: [{ type: "text", text: error instanceof Error ? error.message : String(error) }],
          isError: true,
        },
      })
    }
    return
  }

  sendJson(response, 200, {
    jsonrpc: "2.0",
    id: message.id ?? null,
    error: { code: -32601, message: `Method not found: ${message.method ?? ""}` },
  })
}).listen(port, "0.0.0.0", () => {
  console.error(`apex-forms HTTP transport listening on ${port}`)
})
