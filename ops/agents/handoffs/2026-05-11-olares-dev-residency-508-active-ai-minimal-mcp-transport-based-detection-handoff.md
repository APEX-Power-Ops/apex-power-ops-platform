# Olares Dev Residency 508 - Active AI Minimal-MCP Transport-Based Detection Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-508`

## Purpose

Close the next adjacent active AI minimal-trio detection slice by making adopted and unmanaged listener classification depend on the MCP transport itself rather than deeper service `/health` endpoints.

## Execution Result

Packet 508 is complete.

`tools/ai/run-minimal-mcp-trio.sh` and `tools/ai/run-minimal-mcp-trio.ps1` now probe each admitted `/mcp` endpoint with a lightweight `initialize` request when deciding whether an already-running trio should be classified as unmanaged or adopted.

Before this repair, both wrappers required `/health` to succeed for `apex-fs`, `apex-db`, and `apex-jobs` before they would report `unmanaged-running` or bind adopted mode. That was stricter than the operator-facing MCP contract and allowed dependency-sensitive endpoints such as `apex-db` to suppress truthful listener detection even when the MCP transport itself was live.

The active first-slice runbook now matches the repaired behavior by describing adopted-mode detection as an MCP transport `initialize` proof rather than generic healthy ports.

## Validation Notes

Focused validation stayed bounded to the minimal-trio wrapper slice.

Checks confirmed:

1. `pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action status` now reports `unmanaged-running` against a fake trio that serves `/mcp` correctly while leaving `/health` unavailable,
2. `pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action up` now adopts that same fake trio when the `apex-fs` ownership proof matches,
3. `bash tools/ai/run-minimal-mcp-trio.sh status` now reports `unmanaged-running` against the same MCP-only fake trio when executed inside the Bash runtime boundary,
4. `bash tools/ai/run-minimal-mcp-trio.sh up` now adopts that same fake trio when the `apex-fs` ownership proof matches,
5. diagnostics reported no file-level issues for the touched wrapper files.

## Boundaries Preserved

This packet does not open:

1. managed trio start or stop behavior changes,
2. ownership-proof semantics beyond reusing the existing `apex-fs` check,
3. hold-boundary decision semantics,
4. canary artifact schema changes,
5. broader orchestration or queue-admission changes.

## Next Candidate

No further adjacent current-surface defect is selected from this packet alone; the next lane should again be a genuinely current control, evidence, or operator surface that still disagrees with the admitted AI contract on present evidence.