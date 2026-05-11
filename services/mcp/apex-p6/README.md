# apex-p6

Thin MCP bridge over the bounded `packages/p6-ingest` runtime.

This lane is the canonical source-owned bridge contract for the `apex-p6` service name.
Generated `build/` output is local runtime material, not the authoritative source surface.

## Runtime Contract

- `APEX_MCP_HTTP_PORT`: HTTP port for the MCP bridge. Defaults to `8713`.
- `APEX_MCP_BASE_PATH`: MCP HTTP path. Defaults to `/mcp`.
- `APEX_P6_RUNTIME_URL`: base URL for the backing `p6-ingest` runtime. Defaults to `http://127.0.0.1:8081`.

## Build

```powershell
corepack pnpm install
corepack pnpm build
```