# Packet 755 Handoff - Minimal-MCP Verify Env-Assignment Padding Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-755`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_minimal_mcp_powershell_verify_truthfulness.py`, `tests/test_minimal_mcp_bash_verify_truthfulness.py`
- Change type: test-only parser exactness tightening

## Why This Packet
The duplicated minimal-MCP verify truthfulness lanes both used a local `.env.dev` URL reader that stripped full assignment lines before splitting them, which could hide leading or trailing padding around env URL assignments. This repo intentionally preserves last-value-wins semantics for duplicated MCP URL keys in `.env.dev`, so the safe tightening was field-padding exactness rather than duplicate-key rejection.

## What Changed
- In both `_read_env_urls` helpers:
  - preserved the existing comment/blank filtering,
  - required each parsed assignment line to already equal its stripped form,
  - split the raw line instead of the stripped line,
  - required both key and value fields to already be unpadded,
  - preserved the existing last-value-wins dict behavior for duplicated URL keys.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_minimal_mcp_powershell_verify_truthfulness.py tests/test_minimal_mcp_bash_verify_truthfulness.py -q`
  - Result: pass (`6 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 754 to Packet 755.
- Appended Packet 755 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No helper behavior changes.
- No admitted AI/MCP boundary changes.
- `.env.dev` duplicate-key last-value semantics were preserved.
- Dirty unrelated workspace changes were not touched.
