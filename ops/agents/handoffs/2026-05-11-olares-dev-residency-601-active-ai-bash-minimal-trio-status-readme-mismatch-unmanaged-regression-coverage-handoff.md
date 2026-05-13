# Olares Dev Residency 601 - Active AI Bash Minimal-Trio Status README-Mismatch Unmanaged Regression Coverage Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-601`

## Purpose

Add focused executable proof that the Bash minimal-trio `status` wrapper remains transport-based and `unmanaged-running` when live MCP listeners occupy the admitted ports, the served workspace root matches, and the served `README.md` preview does not.

## Execution Result

Packet 601 is complete.

Extended `tests/test_minimal_mcp_stale_state_truthfulness.py` by enriching the existing fake unmanaged-trio fixture with an optional README preview override and adding `test_bash_status_keeps_readme_mismatched_live_trio_unmanaged`.

The regression passed against current behavior without production changes: `tools/ai/run-minimal-mcp-trio.sh status` already stays `unmanaged-running` and does not write wrapper state when repo identity content mismatches on `README.md` preview.

## Validation Notes

Focused validation stayed bounded to the stale-state truthfulness surface.

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_minimal_mcp_stale_state_truthfulness.py -q` passed.
2. `git diff --check -- tests/test_minimal_mcp_stale_state_truthfulness.py PROJECT_STATUS.md ops/agents/handoffs/2026-05-11-olares-dev-residency-601-active-ai-bash-minimal-trio-status-readme-mismatch-unmanaged-regression-coverage-handoff.md` stayed clean.
3. diagnostics for `tests/test_minimal_mcp_stale_state_truthfulness.py`, `PROJECT_STATUS.md`, and this handoff reported no issues.

## Boundaries Preserved

This packet does not open:

1. changes to minimal-trio `status` wrapper behavior,
2. changes to ownership helper semantics,
3. host-bootstrap ownership-enrichment behavior,
4. broader orchestration or admitted-boundary changes.
