# Olares Dev Residency 510 - Active AI Minimal-MCP PowerShell Already-Running Parity Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-510`

## Purpose

Close the next adjacent active AI minimal-trio wrapper-parity slice by making repeated PowerShell `up` calls return the same stable `already-running` result that Bash already exposes.

## Execution Result

Packet 510 is complete.

`tools/ai/run-minimal-mcp-trio.ps1` now returns `{"status":"already-running"}` when the wrapper finds an existing active trio state and all tracked processes are still running.

Before this repair, the PowerShell wrapper returned the raw persisted state object in that path. Bash already returned a stable `already-running` status instead, so the same operator action produced two different response contracts across shells.

## Validation Notes

Focused validation stayed bounded to the PowerShell wrapper slice.

Checks confirmed:

1. a first `pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action up` call against a fake owned trio still returned adopted mode,
2. a second `pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action up` call in that same state now returns `status = already-running`,
3. file diagnostics for `tools/ai/run-minimal-mcp-trio.ps1` reported no issues,
4. `git diff --check -- tools/ai/run-minimal-mcp-trio.ps1` stayed clean.

## Boundaries Preserved

This packet does not open:

1. trio adoption or ownership-proof semantics,
2. status payload shape beyond the repeated-`up` return contract,
3. hold-boundary decision semantics,
4. canary artifact schema changes,
5. broader orchestration or queue-admission changes.

## Next Candidate

No further adjacent current-surface defect is selected from this packet alone; the next lane should again be a genuinely current control, evidence, or operator surface that still disagrees with the admitted AI contract on present evidence.