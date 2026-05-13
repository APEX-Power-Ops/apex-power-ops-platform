# Packet 758 Handoff - Bash Helper Single-Line Output Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-758`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_host_bootstrap_ready_truthfulness.py`, `tests/test_minimal_mcp_stale_state_truthfulness.py`
- Change type: test-only helper exactness tightening

## Why This Packet
Two adjacent truthfulness lanes duplicated the same `_bash_output` helper and each helper collapsed command stdout through `strip()`. That allowed leading or trailing whitespace and accidental multi-line output to disappear before exact comparisons, even though the callers model single-line Bash command results or deliberate empty output.

## What Changed
- Replaced `completed.stdout.strip()` in both duplicated `_bash_output` helpers.
- Normalized CRLF to LF for comparison.
- Allowed either zero lines or exactly one logical output line.
- Required every returned line to already equal its stripped form.
- Returned the single raw line when present, or the empty string when stdout is empty.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_host_bootstrap_ready_truthfulness.py -q`
  - Result: pass (`6 passed`).
  - `.\.venv\Scripts\python.exe -m pytest tests/test_minimal_mcp_stale_state_truthfulness.py -q`
  - Result: pass (`19 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 757 to Packet 758.
- Appended Packet 758 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No production helper behavior changes.
- No admitted AI/MCP boundary changes.
- No `.env.dev` overwrite semantics changed.
- Dirty unrelated workspace changes were not touched.
