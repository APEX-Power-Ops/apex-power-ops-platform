# Olares Dev Residency 594 - Active AI PowerShell Minimal-Trio Up Adoption-Refusal Regression Coverage Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-594`

## Purpose

Add focused executable proof that the PowerShell minimal-trio `up` wrapper already preserves the ownership helper's refusal JSON and nonzero exit status when live MCP transport exists but the served workspace root does not match the current repo.

## Execution Result

Packet 594 is complete.

Extended `tests/test_minimal_mcp_up_adoption_truthfulness.py` by parameterizing the existing fake PowerShell unmanaged-trio fixture with an override workspace root and adding `test_powershell_up_refuses_adoption_when_live_trio_reports_foreign_workspace_root`.

The regression passed against current behavior without production changes: `tools/ai/run-minimal-mcp-trio.ps1 -Action up` already preserves the ownership helper's `adoption-refused` payload and exits nonzero when a live trio reports a foreign workspace root.

## Validation Notes

Focused validation stayed bounded to the minimal-trio up adoption truthfulness surface.

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_minimal_mcp_up_adoption_truthfulness.py -q` passed.
2. `git diff --check -- tests/test_minimal_mcp_up_adoption_truthfulness.py PROJECT_STATUS.md ops/agents/handoffs/2026-05-11-olares-dev-residency-594-active-ai-powershell-minimal-trio-up-adoption-refusal-regression-coverage-handoff.md` stayed clean.
3. diagnostics for `tests/test_minimal_mcp_up_adoption_truthfulness.py`, `PROJECT_STATUS.md`, and this handoff reported no issues.

## Boundaries Preserved

This packet does not open:

1. changes to minimal-trio `up` wrapper behavior,
2. changes to the ownership helper contract,
3. Bash minimal-trio `up` refusal behavior,
4. broader orchestration or admitted-boundary changes.
