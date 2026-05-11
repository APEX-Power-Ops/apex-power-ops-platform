# Olares Dev Residency 498 - Active AI Minimal-MCP Default-Port Rebind Repair Handoff

Date: 2026-05-10
Status: Complete
Packet: `2026-05-10-olares-dev-residency-498`

## Purpose

Close the next adjacent AI trust-hardening slice by moving the admitted default minimal-MCP trio off the Docker-contended workstation port range.

## Execution Result

Packet 498 is complete.

The committed operator defaults now use host ports `8810`, `8811`, and `8812` instead of `8710`, `8711`, and `8712`.

That rebind landed in `.env.dev.template`, the local workstation `.env.dev`, `tools/ai/run-minimal-mcp-trio.sh`, `tools/ai/run-minimal-mcp-trio.ps1`, `tools/ai/verify_minimal_mcp_trio.py`, `tools/canary/run_canary.py`, `tools/ai/check_deferred_ops_view_counts.py`, and the current first-slice runbook.

The verifier and canary helpers now derive default MCP URLs from `APEX_DEV_MCP_*_PORT` when explicit `APEX_*_MCP_URL` values are absent, so the operator and helper surfaces stay aligned on the rebounded trio.

## Validation Notes

Focused validation stayed bounded to the default operator path after the port rebind.

Checks confirmed:

1. `tools/ai/run-minimal-mcp-trio.ps1 -Action status` now returns `status = not-running` on the current workstation instead of `unmanaged-running`,
2. the verifier helper now resolves default MCP URLs to `http://127.0.0.1:8810/mcp`, `http://127.0.0.1:8811/mcp`, and `http://127.0.0.1:8812/mcp`,
3. the candidate replacement ports were free on both the workstation and Olares before selection,
4. after publication and host mirror sync, the host bootstrap surface also returns the truthful at-rest baseline on the rebounded defaults.

All focused checks passed.

## Boundaries Preserved

This packet does not open:

1. new MCP services,
2. always-on trio runtime,
3. verifier semantic changes,
4. broader orchestration or host-bootstrap redesign,
5. non-AI runtime widening beyond the admitted default port range.

## Next Candidate

The next truthful work is the next separately packetized trust-hardening slice inside the admitted AI boundary, such as cleaning up current-status surfaces that still describe `8710` through `8712` as the live default rather than historical proof context.