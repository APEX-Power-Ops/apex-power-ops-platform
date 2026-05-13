# Olares Dev Residency 538 - Active AI Canary Runner Explicit-URL Precedence Regression Coverage Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-538`

## Purpose

Restore focused executable proof for the remaining direct canary-runner MCP URL precedence branch so explicit helper URL overrides no longer live only in implementation logic and historical Packet 498 prose.

## Execution Result

Packet 538 is complete.

`tests/test_run_canary_helper_truthfulness.py` now also covers direct helper execution with explicit MCP URL environment variables present.

The updated regression file now verifies that:

1. `tools/canary/run_canary.py` prefers explicit `APEX_FS_MCP_URL`, `APEX_DB_MCP_URL`, and `APEX_JOBS_MCP_URL` values over conflicting `APEX_DEV_MCP_*_PORT` defaults,
2. the same helper still records the explicit `APEX_P6_MCP_URL` and `APEX_FORMS_MCP_URL` values in the emitted `mcp-contract` artifact,
3. the precedence path is proven by supplying deliberately invalid conflicting trio port defaults that would fail if the helper ignored the explicit URL values.

## Validation Notes

Focused validation stayed bounded to `tests/test_run_canary_helper_truthfulness.py`.

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_run_canary_helper_truthfulness.py -q` passed,
2. file diagnostics for `tests/test_run_canary_helper_truthfulness.py` reported no issues,
3. `git diff --check -- tests/test_run_canary_helper_truthfulness.py PROJECT_STATUS.md ops/agents/handoffs/2026-05-11-olares-dev-residency-538-active-ai-canary-runner-explicit-url-precedence-regression-coverage-handoff.md` stayed clean.

## Boundaries Preserved

This packet does not open:

1. `tools/canary/run_canary.py` implementation changes,
2. canary wrapper behavior changes,
3. tracked canary artifact rewrites,
4. real runtime or MCP startup beyond the focused fake seam,
5. broader orchestration or non-canary operator surfaces.

## Next Candidate

The direct canary-runner helper now has focused proof for default resolution, output-root routing, and explicit MCP URL precedence, so the next adjacent slice should be whichever remaining current operator or evidence surface still lacks comparable focused validation inside the admitted AI boundary.