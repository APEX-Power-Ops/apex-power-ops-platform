# Packet 723 Handoff - Bash Minimal-Trio Verify Blocked-Output Disjunctive Assertion Elimination

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-723`
- Lane: active AI truthfulness hardening
- Scope: `tests/test_minimal_mcp_bash_verify_truthfulness.py`
- Change type: test-only assertion exactness tightening

## Why This Packet
Packet 722 closed the PowerShell verify-wrapper blocked-output disjunctive residue. The adjacent Bash sibling still had the same broad multiline `... or ...` disjunction in its blocked artifact-output failure branch.

## What Changed
- Added `import re`.
- Replaced multiline disjunctive blocked-output assertion with conjunctive proof:
  - normalized output path evidence in error text,
  - bounded category evidence (`directory|exists|permission denied`) via regex.
- Adjusted expected blocked path normalization to Bash path shape (`/mnt/<drive>/...`) before path-evidence assertion so the strict assertion matches shell-emitted truth on Windows-hosted Bash runs.

## Validation
- Initial focused run surfaced a path-shape mismatch (Windows path vs Bash `/mnt/...` path); fixed with narrow path-shape normalization.
- Final focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_minimal_mcp_bash_verify_truthfulness.py -q`
  - Result: pass (`3 passed`).
- Residue scan:
  - `assert .* or .*` on `tests/test_minimal_mcp_bash_verify_truthfulness.py`
  - Result: no matches.

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 722 to Packet 723.
- Appended Packet 723 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No runtime helper/wrapper behavior changes.
- No admitted MCP boundary changes.
- Dirty unrelated workspace changes were not touched.
