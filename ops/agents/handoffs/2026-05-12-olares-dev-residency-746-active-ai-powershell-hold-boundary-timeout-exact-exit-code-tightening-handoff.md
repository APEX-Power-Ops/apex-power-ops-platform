# Packet 746 Handoff - PowerShell Hold-Boundary Timeout Exact Exit-Code Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-746`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_hold_boundary_powershell_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
The PowerShell hold-boundary live-DSN timeout branch already had exact normalized timeout-message proof and exact child-artifact assertions, but its failure exit check still accepted any nonzero code. The wrapper throws directly on timeout, so the process exit status should be exact.

## What Changed
- In the PowerShell hold-boundary live-DSN timeout test:
  - replaced `assert result.returncode != 0` with `assert result.returncode == 1`,
  - preserved the exact normalized timeout message and artifact checks.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_hold_boundary_powershell_truthfulness.py -q`
  - Result: pass (`7 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 745 to Packet 746.
- Appended Packet 746 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No wrapper behavior changes.
- No admitted AI/MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
