# Olares Dev Residency 511 - Active AI Minimal-MCP PowerShell Up-Output Parity Correction Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-511`

## Purpose

Close the next adjacent active AI minimal-trio wrapper-parity slice by correcting the PowerShell `up` result contract so it matches the Bash wrapper's stable status payloads.

## Execution Result

Packet 511 is complete.

`tools/ai/run-minimal-mcp-trio.ps1` now returns `{"status":"adopted"}` when live adopted listeners already satisfy the ownership proof and `{"status":"started"}` when it launches a fresh managed trio.

Only the managed process-backed reuse path now returns `{"status":"already-running"}`.

Before this correction, the PowerShell wrapper still returned raw persisted state objects for adopted and started outcomes, which did not match Bash. Packet 510 then tightened the wrong branch by assuming repeated adopted `up` should become `already-running`, but the Bash wrapper actually returns `adopted` again for live adopted listeners because it re-runs the live MCP ownership probe instead of trusting adopted state.

## Validation Notes

Focused validation stayed bounded to the PowerShell wrapper slice.

Checks confirmed:

1. a first `pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action up` call against a fake owned trio now returns `status = adopted`,
2. a second `pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action up` call against that same still-live adopted trio also returns `status = adopted`, matching Bash,
3. file diagnostics for `tools/ai/run-minimal-mcp-trio.ps1` reported no issues,
4. `git diff --check -- tools/ai/run-minimal-mcp-trio.ps1` stayed clean.

## Boundaries Preserved

This packet does not open:

1. ownership-proof semantics,
2. status payload shape beyond the `up` result contract,
3. hold-boundary decision semantics,
4. canary artifact schema changes,
5. broader orchestration or queue-admission changes.

## Next Candidate

No further adjacent current-surface defect is selected from this packet alone; the next lane should again be a genuinely current control, evidence, or operator surface that still disagrees with the admitted AI contract on present evidence.