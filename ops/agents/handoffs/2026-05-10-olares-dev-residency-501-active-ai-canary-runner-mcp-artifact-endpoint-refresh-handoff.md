# Olares Dev Residency 501 - Active AI Canary-Runner MCP Artifact Endpoint Refresh Handoff

Date: 2026-05-10
Status: Complete
Packet: `2026-05-10-olares-dev-residency-501`

## Purpose

Close the next adjacent AI evidence-refresh slice by updating the live canary-runner MCP artifact to the rebounded default trio endpoints.

## Execution Result

Packet 501 is complete.

The governed canary entry surface was rerun through `tools/run-canary.ps1`, and the tracked canary-runner output `tests/canary/mcp-contract/actual/mcp-tool-lists.json` now records the admitted trio endpoints as `http://127.0.0.1:8810/mcp`, `http://127.0.0.1:8811/mcp`, and `http://127.0.0.1:8812/mcp`.

No packet-scoped historical proof artifacts were rewritten. The refresh stayed limited to the generic canary-runner MCP tool-list artifact that active documentation still cites as a current surface.

## Validation Notes

Focused validation stayed bounded to the canary-runner evidence surface.

Checks confirmed:

1. `pwsh -NoProfile -ExecutionPolicy Bypass -File tools/run-canary.ps1` completed successfully,
2. the resulting tracked artifact delta was limited to `tests/canary/mcp-contract/actual/mcp-tool-lists.json`,
3. the refreshed artifact now shows `8810`, `8811`, and `8812` for `apex-fs`, `apex-db`, and `apex-jobs`,
4. remaining `8710` through `8712` hits under `tests/canary/**` are packet-scoped historical proof artifacts rather than the generic current canary-runner output.

All focused checks passed.

## Boundaries Preserved

This packet does not open:

1. canary contract changes,
2. operator wrapper behavior changes,
3. historical evidence rewriting beyond the generic current artifact,
4. compose or direct-service runtime changes,
5. broader orchestration or proof-routing redesign.

## Next Candidate

The next truthful work is the next separately packetized active surface, if any, that still presents pre-rebind minimal-MCP defaults as current evidence rather than historical proof.