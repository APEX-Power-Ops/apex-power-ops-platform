# apex-fs

Bounded filesystem bridge for the admitted Olares AI backbone.

This lane is the canonical source-owned contract for the `apex-fs` service name.
Generated `build/` output is local runtime material, not the authoritative source surface.

## Runtime Contract

- `APEX_MCP_HTTP_PORT`: HTTP port for the MCP bridge. Defaults to `8810`.
- `APEX_MCP_BASE_PATH`: MCP HTTP path. Defaults to `/mcp`.
- `APEX_MCP_WORKSPACE_ROOT`: workspace root exposed as the `workspace` filesystem root.
- `APEX_MCP_DATA_ROOT`: data root exposed as the `data` filesystem root.

## Current Tool Surface

- `list_roots`: shows the admitted filesystem roots.
- `list_directory`: lists entries under the admitted `workspace` or `data` roots.
- `read_text_file`: reads UTF-8 text under those same bounded roots.

## Build

```powershell
corepack pnpm install --filter apex-fs
corepack pnpm --filter apex-fs build
```