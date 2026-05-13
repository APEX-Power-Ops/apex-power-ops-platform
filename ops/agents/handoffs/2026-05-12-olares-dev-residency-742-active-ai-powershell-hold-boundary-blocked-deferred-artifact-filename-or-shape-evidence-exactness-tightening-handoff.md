# Packet 742 Handoff - PowerShell Hold-Boundary Blocked-Deferred-Artifact Filename-or-Shape Evidence Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-742`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_hold_boundary_powershell_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 741 hardened the Bash hold-boundary blocked-deferred-artifact branch, the nearest adjacent sibling residue was the PowerShell branch, which still used path evidence plus category regex only.

## What Changed
- In the PowerShell blocked-deferred-artifact test:
  - preserved normalized blocked deferred-output path evidence,
  - added explicit second signal requiring either:
    - deferred artifact filename presence, or
    - `access to the path` wording,
  - retained bounded category regex (`permission denied|errno 13`).

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_hold_boundary_powershell_truthfulness.py -q`
  - Result: pass (`7 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 741 to Packet 742.
- Appended Packet 742 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No wrapper/helper behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
