# MCP_TOPOLOGY.md

This file declares the repo's relationship to the three MCP surfaces. No credential values, no API keys, no OAuth tokens. Pointer-shaped only.

## 1. Per-user stdio MCPs

Location: `~/.claude.json` `mcpServers`
Scope: operator/user scoped
Repo propagation: no

Common server-name examples: `MCP_DOCKER`, `playwright`, `tcc-fidelity-staging`, `mcp-db-server-local`, `supabase`

## 2. Repo-root HTTP MCPs

Location: `<repo-root>/.mcp.json`
Present in this repo: no
Advertised server ids: none

(The NETA ETT source-domain repo advertises `supabase` at its root `.mcp.json`; this platform substrate repo does not currently advertise repo-root HTTP MCPs.)

## 3. Claude.ai OAuth-brokered integrations

Location: `~/.claude/mcp-needs-auth-cache.json` and related user cache
Scope: user scoped
Repo propagation: no

Common integration examples: Box, Figma, Vercel, Supabase, Mermaid Chart

## 4. Disjointness rule

Server names should remain disjoint across surfaces. If a same-name collision occurs in future, repo-root config wins for that repo.

No credential values belong in this file.
