# Packet 730 Handoff - Shared Shell Helper Bash Missing-Override Terminal-Line Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-730`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_shell_common_python_resolution_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 729 hardened PowerShell missing-override assertions, the nearest adjacent weak assertion surface was the Bash sibling checks that still relied on broad contains-style stderr assertions.

## What Changed
- Reused existing `_last_nonempty_line` helper for deterministic stderr line extraction.
- Tightened two Bash failure assertions from contains checks to exact terminal-line equality:
  - missing command override,
  - missing path override.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_shell_common_python_resolution_truthfulness.py -q`
  - Result: pass (`6 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 729 to Packet 730.
- Appended Packet 730 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No runtime helper changes.
- No wrapper behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
