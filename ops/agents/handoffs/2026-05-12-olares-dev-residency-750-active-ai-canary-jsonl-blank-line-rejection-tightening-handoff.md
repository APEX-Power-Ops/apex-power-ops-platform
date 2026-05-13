# Packet 750 Handoff - Canary JSONL Blank-Line Rejection Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-750`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_run_canary_bash_truthfulness.py`, `tests/test_run_canary_powershell_truthfulness.py`
- Change type: test-only parser exactness tightening

## Why This Packet
The Bash and PowerShell canary truthfulness lanes shared the same local JSONL reader shape, and both readers silently dropped blank lines before decoding. The fake canary child-process log writers append exactly one JSON object per line, so the reader can require nonblank raw lines rather than masking extra blank-log residue.

## What Changed
- In both `_read_json_lines` helpers:
  - captured the raw split line list,
  - required every raw line to be nonblank,
  - preserved the existing per-line JSON parsing behavior.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_canary_bash_truthfulness.py tests/test_run_canary_powershell_truthfulness.py -q`
  - Result: pass (`2 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 749 to Packet 750.
- Appended Packet 750 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No wrapper behavior changes.
- No admitted AI/MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
