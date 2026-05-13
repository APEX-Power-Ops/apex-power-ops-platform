# Olares Dev Residency 589 - Active AI Canary-Runner Blocked Output-Root Regression Coverage Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-589`

## Purpose

Add focused executable proof that the canary helper surfaces a blocked caller-supplied `--output-root` path instead of silently assuming local artifact persistence is covered by success-only cases.

## Execution Result

Packet 589 is complete.

Extended `tests/test_run_canary_helper_truthfulness.py` with `test_run_canary_helper_fails_when_output_root_path_is_blocked`, which starts the same bounded fake runtime and MCP seams used by the existing canary helper suite, then points `--output-root` under a file-backed path so local directory creation must fail.

The regression passed against current behavior without production changes: `tools/canary/run_canary.py` already exits nonzero and surfaces the local persistence error when the requested output root is blocked by a file.

## Validation Notes

Focused validation stayed bounded to the canary helper truthfulness surface.

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_run_canary_helper_truthfulness.py -q` passed.
2. `git diff --check -- tests/test_run_canary_helper_truthfulness.py PROJECT_STATUS.md ops/agents/handoffs/2026-05-11-olares-dev-residency-589-active-ai-canary-runner-blocked-output-root-regression-coverage-handoff.md` stayed clean.
3. diagnostics for `tests/test_run_canary_helper_truthfulness.py`, `PROJECT_STATUS.md`, and this handoff reported no issues.

## Boundaries Preserved

This packet does not open:

1. changes to canary helper behavior,
2. changes to runtime or MCP endpoint semantics,
3. changes to canary artifact schema,
4. broader orchestration or wrapper changes.