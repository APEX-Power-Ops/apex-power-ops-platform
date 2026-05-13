# Packet 727 Handoff - Blocked-Output Category Parity Bounded Cross-Platform Error-Category Exactness

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-727`
- Lane: active AI truthfulness hardening
- Scope:
  - `tests/test_verify_minimal_mcp_trio_truthfulness.py`
  - `tests/test_deferred_ops_view_counts_truthfulness.py`
  - `tests/test_run_canary_helper_truthfulness.py`
- Change type: test-only assertion parity tightening

## Why This Packet
After packets 722-726 hardened blocked-output and blocked-artifact OS-shaped assertion leaves, one nearby parity gap remained: direct verifier, deferred-ops helper, and canary helper blocked-output category checks still used `directory|exists`, while wrapper siblings already used the bounded cross-platform matcher including `permission denied`.

## What Changed
- Updated blocked-output category regex in three adjacent truthfulness files from:
  - `directory|exists`
- To:
  - `directory|exists|permission denied`
- Path-evidence checks and normalized-separator handling were kept unchanged.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_verify_minimal_mcp_trio_truthfulness.py tests/test_deferred_ops_view_counts_truthfulness.py tests/test_run_canary_helper_truthfulness.py -q`
  - Result: pass (`45 passed`).
- Residue scan:
  - `assert .* or .*` on touched files
  - Result: no matches.

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 726 to Packet 727.
- Appended Packet 727 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No runtime helper changes.
- No wrapper behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
