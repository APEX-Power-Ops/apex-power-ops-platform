# Packet 736 Handoff - Verifier Blocked-Output Parent-Plus-Filename/Category Evidence Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-736`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_verify_minimal_mcp_trio_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 735 tightened blocked-output-root path evidence in the canary helper, the nearest adjacent residue was in verifier blocked-output assertions, which relied on parent-path evidence plus broad category matching only.

## What Changed
- In `test_verify_minimal_mcp_trio_preserves_fail_json_when_output_path_is_invalid`:
  - preserved normalized blocked parent-path evidence,
  - added an explicit second signal requiring either:
    - blocked output filename presence, or
    - `already exists` wording (Windows shape),
  - retained bounded category regex (`directory|exists|permission denied`).

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_verify_minimal_mcp_trio_truthfulness.py -q`
  - Result: pass (`17 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 735 to Packet 736.
- Appended Packet 736 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No verifier behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
