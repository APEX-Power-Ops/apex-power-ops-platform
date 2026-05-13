# Packet 733 Handoff - Bash Canary Wrapper Node-Invocation Key-Set Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-733`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_run_canary_bash_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 732 tightened the PowerShell canary python-log payload proof, the nearest adjacent weak assertion was in the Bash canary wrapper Node launch surface, which validated expected targets individually but did not prove exact key-set closure.

## What Changed
- Added exact Node invocation target key-set assertion over `node_by_target`:
  - `services/mcp/apex-fs/build/http.js`
  - `services/mcp/apex-db/build/http.js`
  - `services/mcp/apex-jobs/build/http.js`
  - `services/mcp/apex-p6/build/http.js`
  - `services/mcp/apex-forms/build/http.js`
- Kept existing per-target payload equality assertions unchanged.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_canary_bash_truthfulness.py -q`
  - Result: pass (`1 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 732 to Packet 733.
- Appended Packet 733 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No wrapper/runtime behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
