# Packet 764 Handoff - AI Managed Start Missing-Entrypoint Truthfulness Repair

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-764`
- Lane: active AI/operator boundary truthfulness
- Scope: `tools/ai/run-minimal-mcp-trio.sh`, `tools/ai/run-minimal-mcp-trio.ps1`, adjacent started-wrapper tests, and operator docs for managed-start refusal behavior
- Change type: wrapper truthfulness repair plus regression coverage

## Why This Packet
The first real host managed cold-start attempt under Packet 764 exposed a wrapper-level false-positive startup defect.

Observed host evidence:

1. host bootstrap at `/home/olares/code/apex/apex-power-ops-platform` was reachable and truthful,
2. managed `up` returned `{"status":"started"}`,
3. immediate host status showed `fs_running=false`, `db_running=false`, and `jobs_running=true`,
4. host logs showed `MODULE_NOT_FOUND` for:
   - `services/mcp/apex-fs/build/http.js`
   - `services/mcp/apex-db/build/http.js`
5. `apex-jobs` alone stayed up because its `build/http.js` entrypoint existed.

That meant the wrappers were willing to persist managed state and report `started` even when the admitted service entrypoints needed for managed startup were absent.

## What Changed
- Updated `tools/ai/run-minimal-mcp-trio.sh` to preflight the admitted managed entrypoints before spawning processes.
- Updated `tools/ai/run-minimal-mcp-trio.ps1` to do the same preflight.
- New contract:
  - when one or more required managed entrypoints are missing, `up` now returns:
    - `status = start-refused`
    - `reason = missing-service-entrypoints`
    - `missing_entrypoints = [...]`
  - the wrappers do not write managed state for that refusal path.
- Extended `tests/test_minimal_mcp_started_truthfulness.py` with Bash and PowerShell regression coverage for the missing-entrypoint refusal branch.
- Hardened the same test file against local operator drift by isolating the started-wrapper slice from repo env-file imports during these tests.
- Updated the first-slice and host cold-start runbooks to describe the new refusal behavior and the required build-entrypoint precondition.

## Validation
- Focused executable validation:
  - `./.venv/Scripts/python.exe -m pytest tests/test_minimal_mcp_started_truthfulness.py -q`
  - Result: pass (`4 passed`).
- Host diagnosis evidence from the initial Packet 764 attempt:
  - host root reachable: `/home/olares/code/apex/apex-power-ops-platform`
  - host repo clean before artifact generation
  - host build state:
    - `apex-fs=BUILD_MISSING`
    - `apex-db=BUILD_MISSING`
    - `apex-jobs=BUILD_PRESENT`
  - host logs confirmed `MODULE_NOT_FOUND` for the missing `apex-fs` and `apex-db` entrypoints.

## Outcome
Packet 764 closes the repo-side truthfulness defect, not the host build-materialization gap.

The next host managed cold-start claim is now correctly blocked on one of two truthful prerequisites:

1. publish this wrapper repair to the authoritative host mirror, and
2. ensure the admitted `apex-fs` and `apex-db` build entrypoints exist there.

Until then, a host managed-start attempt should refuse instead of emitting a false managed-start success surface.

## Boundaries Preserved
- No new MCP service admitted.
- No `ai_tasks` queue authority admitted.
- No auth, ingress, or host-query widening admitted.
- No business logic changed.
- No host-qualified validation claim was made after the missing-entrypoint evidence appeared.