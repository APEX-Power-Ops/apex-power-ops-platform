# Olares Dev Residency 577 - Active AI Canary-Runner Tools-List Error Handling Repair Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-577`

## Purpose

Repair the direct canary helper so MCP `tools/list` failures are treated as hard helper failures instead of being silently interpreted as an empty tool set.

## Execution Result

Packet 577 is complete.

Extended `tests/test_run_canary_helper_truthfulness.py` so the fake canary MCP seam can return a `tools/list` error and added `test_run_canary_helper_fails_when_mcp_tools_list_errors`.

That focused validation exposed a real defect: `tools/canary/run_canary.py` accepted an MCP `tools/list` error result and continued with an empty tool list, which allowed the canary helper to complete successfully even though MCP tool discovery had failed.

Updated `tools/canary/run_canary.py` so `_mcp_tools` inspects the `tools/list` response and raises the reported MCP error detail when the result is marked as an error.

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