# Packet 752 Handoff - Shared Shell Helper Bash Terminal-Line Whitespace Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-752`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_shell_common_python_resolution_truthfulness.py`
- Change type: test-only parser exactness tightening

## Why This Packet
The shared shell helper Bash failure lane used `_last_nonempty_line` to extract the terminal stderr line, but that helper normalized each nonempty line with `strip()` before comparison. The Bash helper emits exact single-line stderr messages with no surrounding whitespace, so the test helper can require raw lines to already match that emitted shape.

## What Changed
- In `_last_nonempty_line`:
  - preserved raw nonempty lines after newline normalization,
  - required every nonempty line to already equal its stripped form,
  - preserved the existing last-line exact comparison.

## Validation
- Focused test:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_shell_common_python_resolution_truthfulness.py -q`
  - Result: pass (`6 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 751 to Packet 752.
- Appended Packet 752 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No helper behavior changes.
- No admitted AI/MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
