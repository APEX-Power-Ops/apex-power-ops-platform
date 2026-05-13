# Packet 757 Handoff - Bash Hold-Boundary Env-Assignment Padding Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-757`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_hold_boundary_truthfulness.py`
- Change type: test-only parser exactness tightening

## Why This Packet
The Bash hold-boundary truthfulness lane used a local `.env.dev` last-value reader that stripped full assignment lines and fields before comparison. This repo intentionally preserves last-value-wins semantics for duplicated MCP URL keys in `.env.dev`, so the safe tightening was assignment-padding exactness rather than duplicate-key rejection.

## What Changed
- In `_env_file_last_value`:
  - preserved existing blank/comment filtering,
  - required each parsed assignment line to already equal its stripped form,
  - split the raw line instead of the stripped line,
  - required both key and value fields to already be unpadded,
  - preserved the existing last-value-wins behavior for duplicated env keys.

## Validation
- Focused test:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_hold_boundary_truthfulness.py -q`
  - Result: pass (`6 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 756 to Packet 757.
- Appended Packet 757 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No helper behavior changes.
- No admitted AI/MCP boundary changes.
- `.env.dev` duplicate-key last-value semantics were preserved.
- Dirty unrelated workspace changes were not touched.
