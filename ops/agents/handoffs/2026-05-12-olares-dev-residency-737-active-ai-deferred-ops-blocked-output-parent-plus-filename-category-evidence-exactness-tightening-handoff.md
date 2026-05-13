# Packet 737 Handoff - Deferred-Ops Blocked-Output Parent-Plus-Filename/Category Evidence Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-737`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_deferred_ops_view_counts_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 736 hardened verifier blocked-output evidence with multi-signal path validation, the nearest adjacent residue was in deferred-ops blocked-output assertions, which still relied on parent-path evidence plus broad category matching only.

## What Changed
- In `test_check_deferred_ops_view_counts_preserves_fail_json_when_output_path_is_invalid`:
  - preserved normalized blocked parent-path evidence,
  - added explicit second signal requiring either:
    - blocked output filename presence, or
    - `already exists` wording (Windows shape),
  - retained bounded category regex (`directory|exists|permission denied`).

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_deferred_ops_view_counts_truthfulness.py -q`
  - Result: pass (`19 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 736 to Packet 737.
- Appended Packet 737 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No deferred-ops helper behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
