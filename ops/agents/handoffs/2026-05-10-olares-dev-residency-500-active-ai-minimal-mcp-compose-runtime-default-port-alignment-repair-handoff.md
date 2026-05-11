# Olares Dev Residency 500 - Active AI Minimal-MCP Compose Runtime Default-Port Alignment Repair Handoff

Date: 2026-05-10
Status: Complete
Packet: `2026-05-10-olares-dev-residency-500`

## Purpose

Close the next adjacent AI trust-hardening slice by aligning the compose-managed minimal MCP trio runtime with the rebounded default ports.

## Execution Result

Packet 500 is complete.

`infra/compose.dev.yml` now configures the compose-managed `apex-mcp-fs`, `apex-mcp-db`, and `apex-mcp-jobs` services to run on internal ports `8810`, `8811`, and `8812` instead of `8710`, `8711`, and `8712`.

The compose host bindings for those same services now target `127.0.0.1:${APEX_DEV_MCP_FS_PORT}:8810`, `127.0.0.1:${APEX_DEV_MCP_DB_PORT}:8811`, and `127.0.0.1:${APEX_DEV_MCP_JOBS_PORT}:8812`, keeping the compose runtime aligned with the rebounded operator defaults and the now-aligned direct service entrypoints.

## Validation Notes

Focused validation stayed bounded to the compose runtime surface.

Checks confirmed:

1. `docker compose -f infra/compose.dev.yml config` resolved successfully after the rebind,
2. the resulting warnings were limited to expected missing development environment variables outside a populated `.env.dev` context,
3. `get_errors` reported no errors for `infra/compose.dev.yml`,
4. `git diff --check` passed for the compose file,
5. no additional current docs were found that still present the old trio as a live compose default rather than historical proof.

All focused checks passed.

## Boundaries Preserved

This packet does not open:

1. new compose services,
2. operator wrapper behavior changes,
3. always-on runtime claims,
4. historical evidence rewriting,
5. broader orchestration or infrastructure redesign.

## Next Candidate

The next truthful work is the next separately packetized active surface, if any, that still presents pre-rebind minimal-MCP defaults as current runtime contract rather than historical proof context.