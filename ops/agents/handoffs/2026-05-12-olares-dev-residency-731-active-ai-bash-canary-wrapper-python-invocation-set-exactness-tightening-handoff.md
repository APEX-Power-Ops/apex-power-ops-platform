# Packet 731 Handoff - Bash Canary Wrapper Python-Invocation Set Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-731`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_run_canary_bash_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 730 shared-shell-helper hardening, the nearest adjacent weak assertion in canary wrapper truthfulness was a membership-only check for canary script invocation in the Bash surface.

## What Changed
- Replaced membership assertion:
  - from: `("tools/canary/run_canary.py",) in python_by_invocation`
  - to: exact invocation-key set equality over all expected Python launches.
- Exact set now requires only:
  - `("-m", "apex_forms_engine.runtime")`
  - `("-m", "apex_p6_ingest.runtime")`
  - `("tools/canary/run_canary.py",)`

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_canary_bash_truthfulness.py -q`
  - Result: pass (`1 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 730 to Packet 731.
- Appended Packet 731 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No wrapper/runtime behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
