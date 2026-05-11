# Olares Dev Residency 509 - Active AI Minimal-MCP PowerShell Status-Shape Parity Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-509`

## Purpose

Close the next adjacent active AI minimal-trio operator-surface slice by aligning the PowerShell `status` payload with the flat readiness fields already exposed by the Bash wrapper.

## Execution Result

Packet 509 is complete.

`tools/ai/run-minimal-mcp-trio.ps1` now emits `fs_running`, `db_running`, `jobs_running`, `fs_endpoint`, `db_endpoint`, and `jobs_endpoint` for managed and adopted `status` responses.

Before this repair, the PowerShell wrapper returned those flat fields only for `unmanaged-running`. Once the wrapper had state for a managed or adopted trio, it switched to a different shape that kept only nested `endpoints` and `processes`, which left the PowerShell operator surface out of parity with Bash for the same command.

The repair preserves the existing nested `endpoints` and `processes` blocks, so current consumers keep their richer structure while the cross-shell flat readiness contract becomes consistent.

## Validation Notes

Focused validation stayed bounded to the PowerShell wrapper slice.

Checks confirmed:

1. a fake adopted trio now causes `pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action status` to emit `adopted-running` together with `fs_running=true`, `db_running=true`, `jobs_running=true`, and the three flat endpoint fields,
2. file diagnostics for `tools/ai/run-minimal-mcp-trio.ps1` reported no issues,
3. `git diff --check -- tools/ai/run-minimal-mcp-trio.ps1` stayed clean.

## Boundaries Preserved

This packet does not open:

1. minimal-trio start or stop behavior changes,
2. ownership-proof semantics,
3. hold-boundary decision semantics,
4. canary artifact schema changes,
5. broader orchestration or queue-admission changes.

## Next Candidate

No further adjacent current-surface defect is selected from this packet alone; the next lane should again be a genuinely current control, evidence, or operator surface that still disagrees with the admitted AI contract on present evidence.