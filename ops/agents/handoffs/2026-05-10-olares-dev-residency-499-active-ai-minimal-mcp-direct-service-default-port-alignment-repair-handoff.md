# Olares Dev Residency 499 - Active AI Minimal-MCP Direct-Service Default-Port Alignment Repair Handoff

Date: 2026-05-10
Status: Complete
Packet: `2026-05-10-olares-dev-residency-499`

## Purpose

Close the next adjacent AI trust-hardening slice by aligning the direct MCP service runtime defaults with the rebounded operator trio ports.

## Execution Result

Packet 499 is complete.

The direct HTTP service entrypoints for `apex-fs`, `apex-db`, and `apex-jobs` now default `APEX_MCP_HTTP_PORT` to `8810`, `8811`, and `8812` instead of `8710`, `8711`, and `8712` when those services are launched without explicit port overrides.

The live service contract READMEs under `services/mcp/apex-fs`, `services/mcp/apex-db`, and `services/mcp/apex-jobs` now describe the same defaults, and the generated `build/http.js` outputs were rebuilt from the updated TypeScript sources.

## Validation Notes

Focused validation stayed bounded to the affected MCP service tree.

Checks confirmed:

1. `corepack pnpm --filter apex-fs build` passed,
2. `corepack pnpm --filter apex-db build` passed,
3. `corepack pnpm --filter apex-jobs build` passed,
4. no remaining `8710`, `8711`, or `8712` default-port references remain under `services/mcp/**`,
5. `get_errors` reported no errors for the touched source, README, or generated build files,
6. `git diff --check` passed for the bounded Packet 499 file set.

All focused checks passed.

## Boundaries Preserved

This packet does not open:

1. new MCP services,
2. operator wrapper behavior changes,
3. verifier semantic changes,
4. historical evidence rewriting,
5. broader orchestration or runtime-boundary redesign.

## Next Candidate

The next truthful work is the next separately packetized active surface that still presents pre-rebind minimal-MCP defaults as current rather than historical, if any remain outside the now-aligned service tree.