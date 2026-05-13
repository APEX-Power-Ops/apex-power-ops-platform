# Packet 760 Handoff - Bash Fake-Server Port Line Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-760`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_host_bootstrap_ready_truthfulness.py`, `tests/test_minimal_mcp_stale_state_truthfulness.py`
- Change type: test-only helper exactness tightening

## Why This Packet
Two adjacent truthfulness lanes duplicated the same fake-server port reader pattern and each reader collapsed the first stdout line through `strip()`. That allowed leading or trailing whitespace on the emitted port line to disappear before exact comparison, even though the fixture servers intentionally print one exact port line followed by a newline.

## What Changed
- Replaced `readline().strip()` in both duplicated fake-server port readers.
- Normalized CRLF to LF for comparison.
- Required the captured port line to be newline-terminated.
- Required the retained port value to already equal its stripped form.
- Preserved the existing empty-output failure branch after extracting the raw validated line.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_host_bootstrap_ready_truthfulness.py -q`
  - Result: pass (`6 passed`).
  - `.\.venv\Scripts\python.exe -m pytest tests/test_minimal_mcp_stale_state_truthfulness.py -q`
  - Result: pass (`19 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 759 to Packet 760.
- Appended Packet 760 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No production helper behavior changes.
- No admitted AI/MCP boundary changes.
- No `.env.dev` overwrite semantics changed.
- Dirty unrelated workspace changes were not touched.
