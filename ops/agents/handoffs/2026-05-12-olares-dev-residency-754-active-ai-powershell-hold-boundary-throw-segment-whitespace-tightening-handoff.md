# Packet 754 Handoff - PowerShell Hold-Boundary Throw-Segment Whitespace Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-754`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_hold_boundary_powershell_truthfulness.py`
- Change type: test-only parser exactness tightening

## Why This Packet
The PowerShell hold-boundary truthfulness lane carried a duplicated `_normalized_powershell_throw_message` helper that still stripped extracted `| ...` message segments before comparison. Packet 753 already proved the shared shell-resolution copy could require the raw `| ` separator contract and unpadded message content, and the hold-boundary lane exercises the same `pwsh` formatter shape on its timeout and refusal branches.

## What Changed
- In `_normalized_powershell_throw_message`:
  - preserved raw lines after ANSI-stripping,
  - partitioned on the literal `|` marker,
  - required the content side to start with exactly one space,
  - required extracted message content to already be unpadded,
  - preserved the existing joined-message exact comparison and throw/tilde filtering.

## Validation
- Focused test:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_hold_boundary_powershell_truthfulness.py -q`
  - Result: pass (`7 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 753 to Packet 754.
- Appended Packet 754 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No helper behavior changes.
- No admitted AI/MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
