# Olares Dev Residency 535 - Active AI Bash Canary Entrypoint Regression Coverage Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-535`

## Purpose

Restore focused executable proof for the Bash side of the canary entrypoint readiness and fallback-env contract so the Packet 503 and 504 behavior no longer lives only in wrapper diffs and status prose.

## Execution Result

Packet 535 is complete.

`tests/test_run_canary_bash_truthfulness.py` now covers `tools/run-canary.sh` through a fake-runtime seam.

The new regression file now verifies that:

1. `tools/run-canary.sh` waits for the default forms-engine and p6-ingest `/health` endpoints when the canary port variables are omitted,
2. the same wrapper waits for the default admitted MCP transport `/mcp` endpoints for `apex-fs`, `apex-db`, `apex-jobs`, `apex-p6`, and `apex-forms`,
3. the wrapper passes the resolved fallback ports and runtime URLs into the child `node` MCP surfaces instead of forwarding empty raw `APEX_DEV_*` values,
4. the Bash wrapper also passes the resolved fallback runtime ports into the child Python runtime invocations before handing off to `tools/canary/run_canary.py`.

## Validation Notes

Focused validation stayed bounded to `tests/test_run_canary_bash_truthfulness.py`.

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_run_canary_bash_truthfulness.py -q` passed,
2. file diagnostics for `tests/test_run_canary_bash_truthfulness.py` reported no issues,
3. `git diff --check -- tests/test_run_canary_bash_truthfulness.py PROJECT_STATUS.md ops/agents/handoffs/2026-05-11-olares-dev-residency-535-active-ai-bash-canary-entrypoint-regression-coverage-handoff.md` stayed clean.

## Boundaries Preserved

This packet does not open:

1. `tools/run-canary.sh` implementation changes,
2. `tools/run-canary.ps1` parity work,
3. `tools/canary/run_canary.py` artifact or MCP contract changes,
4. real runtime or MCP startup beyond the fake Bash shim seam,
5. broader orchestration or non-canary operator surfaces.

## Next Candidate

The Bash canary entrypoint now has focused proof for the default readiness and fallback-env path, so the next adjacent slice should again be whichever current PowerShell canary or adjacent operator surface still lacks comparable focused validation inside the admitted AI boundary.