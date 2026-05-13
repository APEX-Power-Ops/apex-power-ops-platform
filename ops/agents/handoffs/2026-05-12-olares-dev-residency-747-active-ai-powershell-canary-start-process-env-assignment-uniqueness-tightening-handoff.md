# Packet 747 Handoff - PowerShell Canary Start-Process Env-Assignment Uniqueness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-747`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_run_canary_powershell_truthfulness.py`
- Change type: test-only normalization exactness tightening

## Why This Packet
The PowerShell canary wrapper already had exact per-process normalized payload checks, but the local Start-Process normalization helper still allowed duplicate `$env:` assignments to collapse silently into the normalized environment dictionary. That left hidden structural slack in the proof even though the wrapper constructs the environment from unique PowerShell hashtable keys.

## What Changed
- In `_normalize_start_process_entry`:
  - preserved the existing `$env:` assignment parsing,
  - added an exact uniqueness check so the count of parsed env assignments must equal the number of pre-invoke command parts,
  - kept the rest of the normalized Start-Process payload proof unchanged.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_canary_powershell_truthfulness.py -q`
  - Result: pass (`1 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 746 to Packet 747.
- Appended Packet 747 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No wrapper behavior changes.
- No admitted AI/MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
