# Olares Dev Residency 575 - Active AI Canary-Runner Initialize-Error Handling Repair Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-575`

## Purpose

Repair the direct canary helper so MCP initialize failures are treated as hard helper failures instead of being silently ignored.

## Execution Result

Packet 575 is complete.

Extended `tests/test_run_canary_helper_truthfulness.py` so the fake MCP seam can return an initialize error and added `test_run_canary_helper_fails_when_mcp_initialize_errors`.

That focused validation exposed a real defect: `tools/canary/run_canary.py` accepted an MCP initialize error result and continued into `tools/list`, which allowed the canary helper to complete successfully even though the MCP handshake had already failed.

Updated `tools/canary/run_canary.py` so `_mcp_tools` inspects the initialize response and raises the reported MCP error detail when the handshake result is marked as an error.

## Validation Notes

Focused validation stayed bounded to the canary helper surface.

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_run_canary_helper_truthfulness.py -q` passed after the repair.
2. `git diff --check -- tools/canary/run_canary.py tests/test_run_canary_helper_truthfulness.py` stayed clean.
3. diagnostics for `tools/canary/run_canary.py` and `tests/test_run_canary_helper_truthfulness.py` reported no issues.

## Boundaries Preserved

This packet does not open:

1. runtime health endpoint changes,
2. output artifact path changes,
3. MCP endpoint precedence changes,
4. broader canary helper refactoring.