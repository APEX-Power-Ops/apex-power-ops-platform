# Packet 740 Handoff - Canary Helper Blocked-Output-Root Filename-or-Category Evidence Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-740`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_run_canary_helper_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packets 736-739 established dual-signal blocked-output evidence across verifier/deferred-ops/minimal-trio wrapper siblings, the nearest adjacent residue remained in direct canary helper blocked-output-root assertions, which had path evidence plus category matching but no explicit second bounded signal.

## What Changed
- In `test_run_canary_helper_fails_when_output_root_path_is_blocked`:
  - preserved normalized blocked output-root path evidence,
  - added explicit second signal requiring either:
    - output-root filename presence, or
    - `already exists` wording (Windows shape),
  - retained bounded category regex (`directory|exists|permission denied`).

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_canary_helper_truthfulness.py -q`
  - Result: pass (`9 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 739 to Packet 740.
- Appended Packet 740 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No helper behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
