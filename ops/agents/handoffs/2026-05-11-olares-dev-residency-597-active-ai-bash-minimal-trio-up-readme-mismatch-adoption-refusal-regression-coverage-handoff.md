# Olares Dev Residency 597 - Active AI Bash Minimal-Trio Up README-Mismatch Adoption-Refusal Regression Coverage Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-597`

## Purpose

Add focused executable proof that the Bash minimal-trio `up` wrapper already preserves the ownership helper's refusal JSON and nonzero exit status when live MCP transport exists, the served workspace root matches the current repo, and the served `README.md` preview does not.

## Execution Result

Packet 597 is complete.

Extended `tests/test_minimal_mcp_up_adoption_truthfulness.py` by parameterizing the existing fake Bash unmanaged-trio fixture with an override README preview and adding `test_bash_up_refuses_adoption_when_live_trio_reports_mismatched_readme_preview`.

The regression passed against current behavior without production changes: `tools/ai/run-minimal-mcp-trio.sh up` already preserves the ownership helper's `adoption-refused` payload and exits nonzero when repo-identity proof fails on `README.md` preview content.

## Validation Notes

Focused validation stayed bounded to the minimal-trio up adoption truthfulness surface.

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_minimal_mcp_up_adoption_truthfulness.py -q` passed.
2. `git diff --check -- tests/test_minimal_mcp_up_adoption_truthfulness.py PROJECT_STATUS.md ops/agents/handoffs/2026-05-11-olares-dev-residency-597-active-ai-bash-minimal-trio-up-readme-mismatch-adoption-refusal-regression-coverage-handoff.md` stayed clean.
3. diagnostics for `tests/test_minimal_mcp_up_adoption_truthfulness.py`, `PROJECT_STATUS.md`, and this handoff reported no issues.

## Boundaries Preserved

This packet does not open:

1. changes to minimal-trio `up` wrapper behavior,
2. changes to the ownership helper contract,
3. PowerShell minimal-trio `up` README-mismatch refusal behavior,
4. broader orchestration or admitted-boundary changes.
