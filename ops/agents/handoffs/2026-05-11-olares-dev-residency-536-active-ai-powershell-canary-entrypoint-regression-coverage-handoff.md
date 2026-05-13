# Olares Dev Residency 536 - Active AI PowerShell Canary Entrypoint Regression Coverage Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-536`

## Purpose

Restore focused executable proof for the PowerShell side of the canary entrypoint readiness and fallback-env contract so the Packet 503 and 504 behavior no longer lives only in wrapper diffs and status prose.

## Execution Result

Packet 536 is complete.

`tests/test_run_canary_powershell_truthfulness.py` now covers `tools/run-canary.ps1` through a focused PowerShell interception seam.

The new regression file now verifies that:

1. `tools/run-canary.ps1` waits for the default forms-engine and p6-ingest `/health` endpoints when the canary port variables are omitted,
2. the same wrapper waits for the default admitted MCP transport `/mcp` endpoints for `apex-fs`, `apex-db`, `apex-jobs`, `apex-p6`, and `apex-forms`,
3. the wrapper launches background PowerShell child commands with resolved fallback runtime ports and MCP ports instead of forwarding empty raw `APEX_DEV_*` values,
4. the wrapper still hands off to `tools/canary/run_canary.py` through the resolved repo Python path after the readiness checks succeed.

## Validation Notes

Focused validation stayed bounded to `tests/test_run_canary_powershell_truthfulness.py`.

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_run_canary_powershell_truthfulness.py -q` passed,
2. file diagnostics for `tests/test_run_canary_powershell_truthfulness.py` reported no issues,
3. `git diff --check -- tests/test_run_canary_powershell_truthfulness.py PROJECT_STATUS.md ops/agents/handoffs/2026-05-11-olares-dev-residency-536-active-ai-powershell-canary-entrypoint-regression-coverage-handoff.md` stayed clean.

## Boundaries Preserved

This packet does not open:

1. `tools/run-canary.ps1` implementation changes,
2. `tools/run-canary.sh` behavior changes,
3. `tools/canary/run_canary.py` artifact or MCP contract changes,
4. real runtime or MCP startup beyond the focused interception seam,
5. broader orchestration or non-canary operator surfaces.

## Next Candidate

The current canary entrypoint pair now has focused proof on both Bash and PowerShell for the default readiness and fallback-env path, so the next adjacent slice should be whichever remaining current operator or evidence surface still lacks comparable focused validation inside the admitted AI boundary.