# Packet 749 Handoff - Bash State-File Parser Duplicate-Key Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-749`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_minimal_mcp_started_truthfulness.py`, `tests/test_minimal_mcp_up_adoption_truthfulness.py`
- Change type: test-only parser exactness tightening

## Why This Packet
The Bash `started` and `up-adoption` truthfulness lanes both used the same local state-file parser shape, and both parsers would silently collapse duplicate key assignments into a dictionary before exact state comparison. The shell wrapper writes one assignment per key, so the parser can require unique key cardinality.

## What Changed
- In both `_read_bash_state_values` helpers:
  - tracked the number of assignment lines encountered,
  - required `len(values) == assignment_count`,
  - preserved the rest of the parsed-state and normalized-state proof logic.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_minimal_mcp_started_truthfulness.py tests/test_minimal_mcp_up_adoption_truthfulness.py -q`
  - Result: pass (`10 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 748 to Packet 749.
- Appended Packet 749 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No wrapper behavior changes.
- No admitted AI/MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
