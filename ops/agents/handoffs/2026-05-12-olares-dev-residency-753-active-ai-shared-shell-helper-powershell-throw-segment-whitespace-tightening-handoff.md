# Packet 753 Handoff - Shared Shell Helper PowerShell Throw-Segment Whitespace Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-753`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_shell_common_python_resolution_truthfulness.py`
- Change type: test-only parser exactness tightening

## Why This Packet
The shared shell helper PowerShell failure lane used `_normalized_powershell_throw_message` to extract message segments from `pwsh` error output, but that helper stripped the extracted `| ...` segments before comparison. A direct capture of the missing-command failure showed the raw formatter already emits message lines with a single `| ` separator and unpadded content, so the helper can require that exact shape.

## What Changed
- In `_normalized_powershell_throw_message`:
  - preserved raw lines after ANSI-stripping,
  - partitioned on the literal `|` marker,
  - required the content side to start with exactly one space,
  - required the extracted message content to already be unpadded,
  - preserved the existing joined-message exact comparison and throw/tilde filtering.

## Validation
- Focused test:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_shell_common_python_resolution_truthfulness.py -q`
  - Result: pass (`6 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 752 to Packet 753.
- Appended Packet 753 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No helper behavior changes.
- No admitted AI/MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
