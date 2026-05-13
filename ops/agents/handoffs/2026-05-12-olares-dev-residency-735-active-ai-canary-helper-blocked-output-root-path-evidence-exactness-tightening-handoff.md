# Packet 735 Handoff - Canary Helper Blocked-Output-Root Path-Evidence Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-735`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_run_canary_helper_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 734 launch key-set closure, the nearest adjacent residue in the direct canary helper blocked-output branch was parent-only path evidence. The assertion did not require the blocked `--output-root` path itself.

## What Changed
- In `test_run_canary_helper_fails_when_output_root_path_is_blocked`, tightened path evidence assertion:
  - from parent path membership (`blocked_parent`)
  - to blocked output-root path membership (`output_root`)
- Kept bounded error-category regex (`directory|exists|permission denied`) unchanged.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_canary_helper_truthfulness.py -q`
  - Result: pass (`9 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 734 to Packet 735.
- Appended Packet 735 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No helper/runtime behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
