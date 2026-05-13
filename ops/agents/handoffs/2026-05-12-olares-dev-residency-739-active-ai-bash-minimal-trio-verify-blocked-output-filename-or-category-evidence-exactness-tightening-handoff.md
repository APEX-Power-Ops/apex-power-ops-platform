# Packet 739 Handoff - Bash Minimal-Trio Verify Blocked-Output Filename-or-Category Evidence Exactness Tightening

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-739`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_minimal_mcp_bash_verify_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
After Packet 738 tightened the PowerShell minimal-trio verify blocked-output branch, the nearest adjacent sibling residue was in the Bash wrapper blocked-artifact assertion, which still lacked explicit second-signal evidence beyond path membership and category matching.

## What Changed
- In the Bash blocked verify-artifact test, preserved normalized output-path evidence and added explicit second signal requiring either:
  - output filename presence, or
  - `already exists` wording (Windows shape).
- Retained bounded category regex (`directory|exists|permission denied`) and stderr exactness expectation.

## Validation
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_minimal_mcp_bash_verify_truthfulness.py -q`
  - Result: pass (`3 passed`).

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 738 to Packet 739.
- Appended Packet 739 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No wrapper/helper behavior changes.
- No admitted MCP boundary changes.
- Pre-existing `.env.dev` drift was observed and left untouched.
- Dirty unrelated workspace changes were not touched.
