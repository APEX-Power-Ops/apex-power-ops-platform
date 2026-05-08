# apex-jobs

Run-ledger and promotion-gate bridge for the admitted Olares AI backbone.

This lane is the canonical source-owned contract for the `apex-jobs` service name.
Generated `build/` output is local runtime material, not the authoritative source surface.

## Runtime Contract

- `APEX_MCP_HTTP_PORT`: HTTP port for the MCP bridge. Defaults to `8712`.
- `APEX_MCP_BASE_PATH`: MCP HTTP path. Defaults to `/mcp`.
- `APEX_JOBS_LEDGER_PATH`: absolute or home-relative ledger path. Defaults to `~/apex-data/apex-jobs-ledger.json`.

## Current Tool Surface

- `start_run`: records a new run with `env`, `service`, and optional `packet_id`.
- `end_run`: closes a run with final status and optional notes.
- `list_runs`: filters the run ledger by env, service, packet, status, or time.
- `promote_packet`: refuses unless at least one successful `env=host` run exists for the packet.

## Build

```powershell
corepack pnpm install
corepack pnpm --filter apex-jobs build
```