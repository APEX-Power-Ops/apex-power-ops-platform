# Packet 762 Handoff - AI Workstation Operator Baseline Repair

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-762`
- Lane: active AI/operator boundary hardening
- Scope: `tools/ai/run-minimal-mcp-trio.ps1`, `tools/ai/run-minimal-mcp-trio.sh`, `tools/ai/check_apex_fs_ownership.py`, `tools/ai/run-olares-hold-boundary-check.ps1`, `tools/ai/run-olares-hold-boundary-check.sh`, and adjacent truthfulness tests
- Change type: wrapper routing repair, ownership-proof exactness repair, and workstation-local operator validation

## Why This Packet
The new real-world validation matrix exposed three local operator-path defects during the first workstation baseline drill:

1. `verify` was still targeting stale inherited `APEX_*_MCP_URL` values instead of the current trio endpoints once a managed or adopted state already knew them.
2. `apex-fs` ownership adoption on the live local trio was being refused because the checker compared a 120-character README preview against the 120-byte preview shape the live service actually emits.
3. `hold-boundary` was still allowing inherited `APEX_DB_MCP_URL` to override the current trio DB endpoint, which made the deferred-ops helper fail against a stale ambient URL instead of the active local trio.

## What Changed
- Updated the PowerShell and Bash minimal-trio verify wrappers to pass explicit `--fs-url`, `--db-url`, and `--jobs-url` only when the current state file already contains live trio endpoints.
- Updated `tools/ai/check_apex_fs_ownership.py` to derive its expected README preview from the first 120 bytes of the README file, matching the live `read_text_file --maxBytes 120` contract instead of using a 120-character slice.
- Updated the PowerShell and Bash hold-boundary wrappers to pass the current trio DB endpoint as `--db-url` when no explicit live-DSN path is being used but stateful trio context already exists.
- Added regression coverage for the state-endpoint override paths in minimal-trio verify and hold-boundary wrapper truthfulness tests.
- Aligned the nearby ownership/adoption fixtures to the same 120-byte README preview contract.

## Validation
- Local build prerequisite:
  - `corepack pnpm --filter apex-fs --filter apex-db --filter apex-jobs build`
  - Result: pass.
- Focused tests:
  - `./.venv/Scripts/python.exe -m pytest tests/test_minimal_mcp_powershell_verify_truthfulness.py tests/test_minimal_mcp_bash_verify_truthfulness.py -q`
  - Result: pass (`8 passed`).
  - `./.venv/Scripts/python.exe -m pytest tests/test_apex_fs_ownership_truthfulness.py tests/test_minimal_mcp_up_adoption_truthfulness.py tests/test_minimal_mcp_powershell_verify_truthfulness.py tests/test_minimal_mcp_bash_verify_truthfulness.py -q`
  - Result: pass (`25 passed`).
  - `./.venv/Scripts/python.exe -m pytest tests/test_hold_boundary_powershell_truthfulness.py tests/test_hold_boundary_truthfulness.py -q`
  - Result: pass (`15 passed`).
- Workstation local operator drill for Packet 762:
  - `status` -> `unmanaged-running`
  - `up` -> `adopted`
  - `status` -> `adopted-running`
  - `verify` -> `PASS`
  - `hold-boundary` -> `UNAVAILABLE`
  - Repo-visible artifacts written:
    - `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-12-olares-dev-residency-762.json`
    - `tests/canary/deferred-ops-view-counts/actual/deferred-ops-view-counts-2026-05-12-olares-dev-residency-762.json`

## Result Interpretation
Packet 762 does not establish a governed live-DSN hold verdict from this workstation. It does establish that the local operator path now behaves truthfully:

1. the local trio can be adopted and verified against the repo-owned endpoints,
2. promotion guard refusal remains intact under sandbox-only proof,
3. the deferred-ops helper now reports `UNAVAILABLE` for the real reason in this environment: no governed live DSN is present, rather than stale endpoint routing or ownership-proof drift.

## Governance Updates
- Updated `PROJECT_STATUS.md` supplement from Packet 761 to Packet 762.
- Updated the executive and lane-register AI/operator packet ranges in `PROJECT_STATUS.md`.
- Appended the Packet 762 narrative entry in `PROJECT_STATUS.md`.

## Boundaries Preserved
- No new orchestration service was admitted.
- No `ai_tasks` queue ownership change was made.
- No auth, ingress, or business-logic scope changed.
- No host-qualified promotion claim was made.
- The remaining hold-boundary limitation is still the absence of governed live-DSN evidence from this workstation path, not a widened runtime or queue change.