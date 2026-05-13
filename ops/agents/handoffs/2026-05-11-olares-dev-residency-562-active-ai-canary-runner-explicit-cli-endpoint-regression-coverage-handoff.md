# Olares Dev Residency 562 - Active AI Canary Runner Explicit-CLI-Endpoint Regression Coverage Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-562`

## Purpose

Restore direct executable proof for the canary runner helper branch that prefers explicit command-line runtime and MCP endpoints over conflicting environment defaults.

## Execution Result

Packet 562 is complete.

Extended `tests/test_run_canary_helper_truthfulness.py` so the direct canary runner regression surface now verifies that:

1. the helper still succeeds with environment-driven runtime and MCP defaults,
2. the helper still prefers explicit MCP URL environment variables over conflicting trio port defaults,
3. the helper now also prefers explicit `--forms-runtime-url`, `--p6-runtime-url`, `--fs-mcp-url`, `--db-mcp-url`, `--jobs-mcp-url`, `--p6-mcp-url`, and `--forms-mcp-url` arguments over conflicting environment defaults.

The new proof uses deliberately invalid environment endpoints and real fake runtime and MCP surfaces supplied through CLI arguments, so the helper would fail immediately if command-line precedence were broken.

## Validation Notes

Focused validation stayed bounded to `tests/test_run_canary_helper_truthfulness.py`.

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_run_canary_helper_truthfulness.py -q` passed,
2. file diagnostics for `tests/test_run_canary_helper_truthfulness.py`, `PROJECT_STATUS.md`, and this handoff reported no issues,
3. `git diff --check -- tests/test_run_canary_helper_truthfulness.py PROJECT_STATUS.md ops/agents/handoffs/2026-05-11-olares-dev-residency-562-active-ai-canary-runner-explicit-cli-endpoint-regression-coverage-handoff.md` stayed clean.

## Boundaries Preserved

This packet does not open:

1. changes to `tools/canary/run_canary.py`,
2. canary wrapper behavior changes,
3. tracked canary artifact path changes,
4. broader runtime startup behavior,
5. non-canary helper families.

## Next Candidate

The direct canary runner helper now has focused proof for environment defaults, explicit environment MCP URL precedence, and explicit CLI endpoint precedence, so the next adjacent uncovered slice is more likely in a different helper family or a smaller remaining canary omission branch rather than this precedence surface.