# Olares Dev Residency 553 - Active AI PowerShell Hold-Boundary Direct-Mode Helper-Failure Propagation Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-553`

## Purpose

Restore truthful PowerShell hold-boundary wrapper behavior when the deferred-ops helper fails after selecting direct SQLAlchemy mode from a live DSN.

## Execution Result

Packet 553 is complete.

Repaired `tools/ai/run-olares-hold-boundary-check.ps1` so it respects the helper exit code after invoking `check_deferred_ops_view_counts.py` and exits immediately on helper failure instead of continuing into summary construction.

Extended `tests/test_hold_boundary_powershell_truthfulness.py` so the PowerShell wrapper regression surface now verifies that:

1. the wrapper still reports `HOLD` when deferred-operation views are empty,
2. the wrapper still reports `REOPEN` when authoritative deferred-operation views contain rows,
3. the wrapper still reports `UNAVAILABLE` when the authoritative views are absent,
4. the wrapper still refuses a missing live-DSN env before running checks,
5. the wrapper now exits with the helper's failure code and no extra stderr/stdout noise when a caller supplies an invalid live DSN that selects direct SQLAlchemy mode,
6. the minimal verifier artifact still exists for that path,
7. the deferred-ops helper artifact still exists for that path and records `mode: direct`, source `env:SEAM_DATABASE_URL`, result `FAIL`, and the SQLAlchemy URL parse error.

This packet also removes the scratch debug artifacts created during earlier reproduction of the PowerShell live-DSN branch.

## Validation Notes

Focused validation stayed bounded to the repaired wrapper and its regression file.

Checks confirmed:

1. `./.venv/Scripts/python.exe -m pytest tests/test_hold_boundary_powershell_truthfulness.py -q` passed,
2. file diagnostics for `tools/ai/run-olares-hold-boundary-check.ps1`, `tests/test_hold_boundary_powershell_truthfulness.py`, `PROJECT_STATUS.md`, and this handoff reported no issues,
3. `git diff --check -- tools/ai/run-olares-hold-boundary-check.ps1 tests/test_hold_boundary_powershell_truthfulness.py PROJECT_STATUS.md ops/agents/handoffs/2026-05-11-olares-dev-residency-553-active-ai-powershell-hold-boundary-direct-mode-helper-failure-propagation-handoff.md` stayed clean.

## Boundaries Preserved

This packet does not open:

1. changes to `check_deferred_ops_view_counts.py` behavior,
2. Bash hold-boundary wrapper behavior changes,
3. deeper PowerShell live-DSN fallback branches,
4. minimal-MCP trio helper changes,
5. broader canary or host-bootstrap surfaces.

## Next Candidate

The PowerShell hold-boundary wrapper now has proof for its primary success paths, missing-live-DSN refusal branch, and direct-mode helper-failure propagation branch, so the next adjacent uncovered slice is likely the PowerShell live-DSN fallback branch when SQLAlchemy is not available or a comparably narrow env/error branch in another helper or wrapper.