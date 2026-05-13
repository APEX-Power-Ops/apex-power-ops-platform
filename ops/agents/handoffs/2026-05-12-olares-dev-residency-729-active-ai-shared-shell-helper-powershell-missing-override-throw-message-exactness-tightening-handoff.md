# Packet 729 Handoff - Shared Shell Helper PowerShell Missing-Override Throw-Message Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-729`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_shell_common_python_resolution_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 728 canary source-list hardening, the next low-risk weak assertion shape was in PowerShell shared-helper missing-override tests, which used split substring checks across formatted stderr output.

## What Changed
- Added normalized PowerShell throw-message helper in test surface:
  - strips ANSI sequences,
  - extracts pipe-prefixed throw message lines,
  - joins logical message text.
- Tightened two failure assertions from split substring checks to exact normalized message equality:
  - missing command override,
  - missing path override.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_shell_common_python_resolution_truthfulness.py -q`
  - Result: pass (`6 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 728 to Packet 729.
- Appended Packet 729 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No runtime helper changes.
- No wrapper behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
