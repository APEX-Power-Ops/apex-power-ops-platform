# Olares Dev Residency 495 - Active AI Minimal-MCP Adoption Ownership-Proof Repair Handoff

Date: 2026-05-10
Status: Complete
Packet: `2026-05-10-olares-dev-residency-495`

## Purpose

Close the next adjacent AI trust-hardening slice by preventing the minimal-MCP `up` surface from silently adopting any healthy listeners on the admitted ports when those listeners do not belong to the current repo root.

## Execution Result

Packet 495 is complete.

`tools/ai/check_apex_fs_ownership.py` now performs a bounded `apex-fs` ownership probe by initializing the live endpoint, calling `list_roots`, and comparing the served `workspace` root against the current repo root while also capturing a bounded README preview for diagnostics.

`tools/ai/run-minimal-mcp-trio.sh` and `tools/ai/run-minimal-mcp-trio.ps1` now call that ownership probe before writing adopted state. If the admitted ports are healthy but `apex-fs` is serving a different workspace root, `up` now exits with `status = adoption-refused` instead of silently binding verification to the foreign listeners.

The first-slice runbook now records that adopted mode requires ownership proof rather than only port health.

## Validation Notes

Focused validation stayed bounded to the new ownership probe and the `up` behavior on the live workstation collision already present on ports `8710` through `8712`.

Checks confirmed:

1. `tools/ai/run-minimal-mcp-trio.ps1 -Action up -PacketId 2026-05-10-olares-dev-residency-495-local-probe` now exits non-zero with `status = adoption-refused`,
2. `bash tools/ai/run-minimal-mcp-trio.sh up 2026-05-10-olares-dev-residency-495-local-probe` now exits non-zero with the same refusal class,
3. both refusal payloads reported `workspace_root = /workspace-live` instead of the current repo root, proving the wrappers are no longer adopting the foreign listener set,
4. `tools/ai/run-minimal-mcp-trio.ps1 -Action status` remained `unmanaged-running` after the refused adoption attempts, proving no adopted state was written.

All focused checks passed after one helper syntax repair during validation.

## Boundaries Preserved

This packet does not open:

1. new MCP services,
2. durable always-on trio runtime,
3. verifier-semantic changes,
4. broader host bootstrap redesign,
5. non-AI runtime or product-surface widening.

## Next Candidate

The next truthful work is the next separately packetized trust-hardening slice inside the admitted AI boundary, such as a follow-on refusal or status-classification improvement that records live foreign ownership detail on the host surface as well as the local wrapper surface.