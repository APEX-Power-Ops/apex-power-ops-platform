# Packet 732 Handoff - PowerShell Canary Wrapper Python-Log Payload Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-732`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_run_canary_powershell_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 731 hardened the Bash canary wrapper invocation proof, the nearest adjacent weak assertion was in the PowerShell sibling: python-log verification only checked argv and left tracked env fields unproven.

## What Changed
- Tightened final python-log assertion from argv-only projection to full payload equality.
- New exact expected payload now asserts:
  - `argv == ["tools/canary/run_canary.py"]`
  - tracked runtime env fields are all `None` for this direct canary invocation path.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_canary_powershell_truthfulness.py -q`
  - Result: pass (`1 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 731 to Packet 732.
- Appended Packet 732 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No wrapper/runtime behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
