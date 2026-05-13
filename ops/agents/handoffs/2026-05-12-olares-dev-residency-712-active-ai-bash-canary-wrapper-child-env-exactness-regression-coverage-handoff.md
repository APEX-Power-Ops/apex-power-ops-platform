# Olares Dev Residency 712 - Active AI Bash Canary Wrapper Child-Env Exactness Regression Coverage Handoff

Date: 2026-05-12
Status: Complete
Packet: `2026-05-12-olares-dev-residency-712`

## Purpose

Close the remaining piecemeal child-launch environment assertions in the Bash canary wrapper truthfulness surface by tightening the fallback-port branch to exact log-entry equality.

## Execution Result

Packet 712 is complete.

Extended `tests/test_run_canary_bash_truthfulness.py` so the fallback-port wrapper path now proves exact child-launch log entries for:

1. Bash-started MCP Node processes, and
2. Bash-started Python runtime processes.

The updated test now models the deterministic wrapper exports exactly, including:

1. repo-root and data-root wiring for `apex-fs`,
2. jobs ledger wiring for `apex-jobs`,
3. runtime URL exports for `apex-forms` and `apex-p6`,
4. runtime artifact and fixture paths for the Python child processes, and
5. imported OIDC placeholder defaults from `.env.dev.template`.

This replaces earlier port-only leaf assertions with exact helper-backed log-entry comparisons.

## Validation Notes

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_run_canary_bash_truthfulness.py -q` passed after the exactness helper update.
2. the wrapper-backed curl wait assertions still proved the expected fallback endpoint order exactly.

## Boundaries Preserved

This packet does not open:

1. changes to `tools/run-canary.sh`,
2. changes to `tools/canary/run_canary.py`,
3. runtime or MCP process behavior changes, or
4. broader admitted-boundary changes.
