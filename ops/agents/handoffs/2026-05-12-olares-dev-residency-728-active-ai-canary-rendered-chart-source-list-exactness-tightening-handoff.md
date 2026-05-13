# Packet 728 Handoff - Canary Rendered-Chart Source-List Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-728`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_run_canary_helper_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 727 closed blocked-output category parity, the next practical weak assertion residue was in canary rendered-chart proof where six independent substring checks validated `# Source:` markers. This shape can pass with partial drift and does not prove source-list structure exactly.

## What Changed
- Added helper `_rendered_chart_sources(rendered_chart: str) -> list[str]` to extract normalized `# Source:` lines.
- Replaced six independent substring checks with exact list equality assertions for:
  - forms-engine rendered chart sources,
  - p6-ingest rendered chart sources.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_run_canary_helper_truthfulness.py -q`
  - Result: pass (`9 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 727 to Packet 728.
- Appended Packet 728 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No runtime helper changes.
- No wrapper behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
