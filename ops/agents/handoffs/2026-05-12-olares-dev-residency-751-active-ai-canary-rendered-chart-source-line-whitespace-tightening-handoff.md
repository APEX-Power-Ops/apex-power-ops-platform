# Packet 751 Handoff - Canary Rendered Chart Source-Line Whitespace Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-751`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_run_canary_helper_truthfulness.py`
- Change type: test-only parser exactness tightening

## Why This Packet
The canary helper rendered-chart source extractor normalized source lines with `strip()`, which could hide leading indentation or trailing whitespace on `# Source:` lines before comparison. The helper emits those source lines in a fixed exact format at column 1 with no trailing whitespace, so the test helper can require that exact shape.

## What Changed
- In `_rendered_chart_sources`:
  - captured raw split lines,
  - required all source-like lines to already begin with `# Source: ` at column 1,
  - required extracted source lines to have no trailing whitespace,
  - preserved the existing exact source-list comparison.

## Validation
- Focused test:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_canary_helper_truthfulness.py -k output_tree -q`
  - Result: pass (`1 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 750 to Packet 751.
- Appended Packet 751 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No helper behavior changes.
- No admitted AI/MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
