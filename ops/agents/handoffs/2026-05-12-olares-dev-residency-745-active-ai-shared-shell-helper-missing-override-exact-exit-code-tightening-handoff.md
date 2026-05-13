# Packet 745 Handoff - Shared Shell Helper Missing-Override Exact Exit-Code Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-745`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_shell_common_python_resolution_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packets 729 and 730 made the Bash and PowerShell missing-override message proofs exact, the remaining residue in that same local branch was failure exit validation that still accepted any nonzero code. The owning helper implementations already return `1` in Bash and surface a terminating error that exits `pwsh` with code `1`, so the tests could be tightened further.

## What Changed
- In the shared shell helper missing-command and missing-path tests:
  - replaced `assert completed.returncode != 0` with `assert completed.returncode == 1` for Bash and PowerShell,
  - preserved the existing exact message checks.

## Validation
- Focused code-path probe:
  - direct Bash helper invocation returned exit code `1`.
  - direct PowerShell helper invocation exited with code `1`.
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_shell_common_python_resolution_truthfulness.py -q`
  - Result: pass (`6 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 744 to Packet 745.
- Appended Packet 745 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No helper behavior changes.
- No admitted AI/MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
