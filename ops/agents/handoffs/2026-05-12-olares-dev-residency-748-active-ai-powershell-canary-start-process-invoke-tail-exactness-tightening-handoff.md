# Packet 748 Handoff - PowerShell Canary Start-Process Invoke-Tail Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-748`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_run_canary_powershell_truthfulness.py`
- Change type: test-only normalization exactness tightening

## Why This Packet
After Packet 747 closed duplicate env-assignment slack in the PowerShell canary Start-Process normalizer, the same local parser still allowed unquoted residue in the invoke-argument tail because it extracted quoted args with `re.findall()` and ignored anything unmatched. The wrapper builds the invoke tail from fully quoted arguments, so the parser can require exact tail reconstruction.

## What Changed
- In `_normalize_start_process_entry`:
  - preserved the existing invoke-file and invoke-arg parsing,
  - captured the raw invoke-argument tail,
  - required that tail to exactly equal the recovered quoted argument sequence,
  - kept the rest of the normalized Start-Process payload proof unchanged.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_canary_powershell_truthfulness.py -q`
  - Result: pass (`1 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 747 to Packet 748.
- Appended Packet 748 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No wrapper behavior changes.
- No admitted AI/MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
