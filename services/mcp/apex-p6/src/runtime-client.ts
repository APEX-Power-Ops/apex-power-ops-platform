const runtimeBaseUrl = (process.env.APEX_P6_RUNTIME_URL ?? "http://127.0.0.1:8081").replace(/\/$/, "")

export const tools = [
  {
    name: "get_runtime_status",
    description:
      "Read the bounded p6-ingest runtime health contract exposed by the local schedule-ingest shell.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "get_stack_fixture_summary",
    description:
      "Return the admitted Stack Data Center fixture summary through the p6-ingest runtime surface.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
  {
    name: "list_stack_fixture_task_codes",
    description:
      "List the live-lane task codes currently exposed by the admitted Stack Data Center fixture summary.",
    inputSchema: {
      type: "object",
      properties: {},
    },
  },
] as const

async function fetchJson(pathname: string) {
  const response = await fetch(`${runtimeBaseUrl}${pathname}`)
  if (!response.ok) {
    throw new Error(`Request failed for ${pathname}: ${response.status} ${response.statusText}`)
  }
  return response.json()
}

export async function callTool(name: string) {
  switch (name) {
    case "get_runtime_status":
      return fetchJson("/health")
    case "get_stack_fixture_summary":
      return fetchJson("/fixtures/stack-data-center")
    case "list_stack_fixture_task_codes": {
      const summary = await fetchJson("/fixtures/stack-data-center")
      return {
        fixture: summary.fixture,
        task_codes: Array.isArray(summary?.live_lane?.task_codes) ? summary.live_lane.task_codes : [],
      }
    }
    default:
      throw new Error(`Unknown tool: ${name}`)
  }
}

export function getRuntimeBaseUrl() {
  return runtimeBaseUrl
}