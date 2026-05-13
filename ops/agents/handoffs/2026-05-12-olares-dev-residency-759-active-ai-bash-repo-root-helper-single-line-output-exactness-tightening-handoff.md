# Packet 759 Handoff - Bash Repo-Root Helper Single-Line Output Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-759`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_host_bootstrap_ready_truthfulness.py`, `tests/test_minimal_mcp_stale_state_truthfulness.py`
- Change type: test-only helper exactness tightening

## Why This Packet
Two adjacent truthfulness lanes duplicated the same `_wsl_repo_root` helper and each helper collapsed `pwd -P` stdout through `strip()`. That allowed leading or trailing whitespace and accidental multi-line output to disappear before exact comparisons, even though the callers model one exact workspace-root line.

## What Changed
- Replaced `check_output(...).strip()` in both duplicated `_wsl_repo_root` helpers.
- Normalized CRLF to LF for comparison.
- Required exactly one logical output line from `pwd -P`.
- Required the retained line to already equal its stripped form.
- Returned the raw single repo-root line once validated.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_host_bootstrap_ready_truthfulness.py -q`
  - Result: pass (`6 passed`).
  - `.\.venv\Scripts\python.exe -m pytest tests/test_minimal_mcp_stale_state_truthfulness.py -q`
  - Result: pass (`19 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 758 to Packet 759.
- Appended Packet 759 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No production helper behavior changes.
- No admitted AI/MCP boundary changes.
- No `.env.dev` overwrite semantics changed.
- Dirty unrelated workspace changes were not touched.
