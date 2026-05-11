# Olares Dev Residency 504 - Active AI Canary Entrypoint Fallback-Env Alignment Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-504`

## Purpose

Close the next adjacent active AI canary-entrypoint consistency slice by making the governed canary wrappers launch child processes with the same resolved fallback ports and URLs they already use for readiness polling.

## Execution Result

Packet 504 is complete.

`tools/run-canary.ps1` and `tools/run-canary.sh` now pass resolved values into child process environment variables instead of forwarding raw `APEX_DEV_*` variables directly.

The runtime launches now set `PORT` from the resolved forms-engine and p6-ingest runtime ports, the MCP launches now set `APEX_MCP_HTTP_PORT` from the resolved MCP ports, and the `apex-forms` and `apex-p6` MCP wrappers now point at resolved runtime URLs instead of interpolating raw runtime-port env variables.

This repairs an internal mismatch introduced by the earlier readiness hardening: the wrappers already knew which ports to wait on, but a sparse or partial env configuration could still launch child processes with empty port values or empty runtime URLs because the launch block was not using those resolved fallback values.

## Validation Notes

Focused validation stayed bounded to the canary-entrypoint env-alignment slice.

Checks confirmed:

1. `pwsh -NoProfile -ExecutionPolicy Bypass -File tools/run-canary.ps1` completed successfully after the launch-env repair.
2. diagnostics for `tools/run-canary.ps1` and `tools/run-canary.sh` reported no new file-level errors.
3. `git diff --check -- tools/run-canary.ps1 tools/run-canary.sh` reported no patch-format defects beyond the pre-existing shell line-ending warning surfaced by Git.
4. the working-tree delta stayed bounded to `tools/run-canary.ps1` and `tools/run-canary.sh` before packet bookkeeping.

## Boundaries Preserved

This packet does not open:

1. readiness polling semantics,
2. canary artifact schema changes,
3. minimal-trio port or boundary changes,
4. historical packet-evidence rewrites,
5. broader orchestration or queue-admission changes.

## Next Candidate

No further adjacent current-surface defect is selected from this packet alone; the next lane should be another genuinely current control, evidence, or operator surface that still disagrees with the admitted AI contract on present evidence.