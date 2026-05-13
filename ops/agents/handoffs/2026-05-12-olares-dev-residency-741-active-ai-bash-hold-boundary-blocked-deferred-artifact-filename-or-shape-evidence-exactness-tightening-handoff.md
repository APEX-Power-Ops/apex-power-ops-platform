# Packet 741 Handoff - Bash Hold-Boundary Blocked-Deferred-Artifact Filename-or-Shape Evidence Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-741`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_hold_boundary_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 740 completed dual-signal blocked-output coverage across verifier/deferred-ops/minimal wrappers/canary helper, the nearest adjacent residue was in the Bash hold-boundary blocked-deferred-artifact branch, which still used path evidence plus category regex only.

## What Changed
- In `test_hold_boundary_surfaces_helper_failure_when_deferred_ops_artifact_path_is_blocked`:
  - preserved normalized blocked deferred-output path evidence,
  - added explicit second signal requiring either:
    - deferred artifact filename presence, or
    - `is a directory` wording,
  - retained bounded category regex (`is a directory|errno 21`).

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_hold_boundary_truthfulness.py -q`
  - Result: pass (`6 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 740 to Packet 741.
- Appended Packet 741 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No wrapper/helper behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
