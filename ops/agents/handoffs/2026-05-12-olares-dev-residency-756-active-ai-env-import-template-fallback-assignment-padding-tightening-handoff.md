# Packet 756 Handoff - Env-Import Template-Fallback Assignment-Padding Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-756`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_shell_common_env_import_truthfulness.py`
- Change type: test-only parser exactness tightening

## Why This Packet
The shared shell env-import truthfulness lane used a local template fallback reader that stripped full assignment lines and fields before comparison. The repo template currently stores these fallback keys as exact unpadded `KEY=value` lines, so the helper can require that exact shape instead of normalizing it away.

## What Changed
- In `_template_value`:
  - preserved existing blank/comment filtering,
  - required each parsed assignment line to already equal its stripped form,
  - split the raw line instead of the stripped line,
  - required both key and value fields to already be unpadded,
  - preserved the existing exact fallback-value lookup.

## Validation
- Focused test:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_shell_common_env_import_truthfulness.py -q`
  - Result: pass (`6 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 755 to Packet 756.
- Appended Packet 756 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No helper behavior changes.
- No admitted AI/MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
