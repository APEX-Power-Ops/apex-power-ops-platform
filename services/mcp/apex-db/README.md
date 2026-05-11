# apex-db

Read-only PostgreSQL bridge for the admitted Olares AI backbone.

This lane is the canonical source-owned contract for the `apex-db` service name.
Generated `build/` output is local runtime material, not the authoritative source surface.

## Runtime Contract

- `APEX_MCP_HTTP_PORT`: HTTP port for the MCP bridge. Defaults to `8811`.
- `APEX_MCP_BASE_PATH`: MCP HTTP path. Defaults to `/mcp`.
- `APEX_DB_CONNECTION_STRING`: preferred read-only PostgreSQL connection string.
- `DATABASE_URL`: fallback PostgreSQL connection string when the explicit APEX variable is absent.

## Current Tool Surface

- `list_tables`: lists base tables inside a selected schema.
- `describe_table`: describes a table's column surface.
- `query`: executes bounded read-only `SELECT` or `WITH` SQL.

## Safety Contract

`apex-db` rejects mutating SQL. The admitted backbone currently allows only read-only query shapes.

## Build

```powershell
corepack pnpm install --filter apex-db
corepack pnpm --filter apex-db build
```