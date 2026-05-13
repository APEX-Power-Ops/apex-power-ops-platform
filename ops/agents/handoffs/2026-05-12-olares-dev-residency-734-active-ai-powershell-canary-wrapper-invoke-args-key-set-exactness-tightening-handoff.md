# Packet 734 Handoff - PowerShell Canary Wrapper Invoke-Args Key-Set Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-734`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_run_canary_powershell_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 733 tightened the Bash canary wrapper Node launch key-set closure, the nearest adjacent symmetry residue was in the PowerShell canary wrapper Start-Process launch map, which still relied on call count plus per-key payload lookups.

## What Changed
- Added exact invoke-args key-set assertion over `normalized_by_invoke` requiring only:
  - `("-m", "apex_forms_engine.runtime")`
  - `("services/mcp/apex-db/build/http.js",)`
  - `("services/mcp/apex-fs/build/http.js",)`
  - `("services/mcp/apex-jobs/build/http.js",)`
  - `("services/mcp/apex-forms/build/http.js",)`
  - `("services/mcp/apex-p6/build/http.js",)`
  - `("-m", "apex_p6_ingest.runtime")`
- Kept all existing per-key payload equality assertions unchanged.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_canary_powershell_truthfulness.py -q`
  - Result: pass (`1 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 733 to Packet 734.
- Appended Packet 734 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No wrapper/runtime behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
