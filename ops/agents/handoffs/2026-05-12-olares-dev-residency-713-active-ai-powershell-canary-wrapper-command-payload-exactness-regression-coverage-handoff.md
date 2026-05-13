# Olares Dev Residency 713 - Active AI PowerShell Canary Wrapper Command-Payload Exactness Regression Coverage Handoff

Date: 2026-05-12
Status: Complete
Packet: `2026-05-12-olares-dev-residency-713`

## Purpose

Close the remaining piecemeal command-fragment assertions in the PowerShell canary wrapper truthfulness surface by tightening the fallback-port branch to exact parsed command-payload equality.

## Execution Result

Packet 713 is complete.

Extended `tests/test_run_canary_powershell_truthfulness.py` so the fallback-port wrapper path now normalizes each logged `Start-Process` command into an exact payload containing:

1. exported environment variables,
2. working directory,
3. invoked executable, and
4. invoked argument list.

The updated test proves the full child-launch command content exactly for:

1. both Python runtime launches, and
2. all Node-backed MCP process launches.

This replaces the prior command-substring assertions with exact parsed payload comparisons while preserving the wrapper-backed wait-order and canary-invocation checks.

## Validation Notes

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_run_canary_powershell_truthfulness.py -q` passed after the parsed-command exactness update.
2. a residue scan found no remaining `"$env:..." in ...command` style assertions in `tests/test_run_canary_powershell_truthfulness.py`.

## Boundaries Preserved

This packet does not open:

1. changes to `tools/run-canary.ps1`,
2. changes to `tools/canary/run_canary.py`,
3. runtime or MCP process behavior changes, or
4. broader admitted-boundary changes.
