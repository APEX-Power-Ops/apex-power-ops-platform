# Packet 765 Handoff - AI Managed Start Readiness Barrier And Host Proof

## Packet
- Packet ID: `2026-05-12-olares-dev-residency-765`
- Lane: active AI/operator boundary truthfulness
- Scope: `tools/ai/run-minimal-mcp-trio.sh`, `tools/ai/run-minimal-mcp-trio.ps1`, adjacent started-wrapper tests, operator docs, and authoritative-host managed cold-start validation
- Change type: wrapper readiness-barrier repair plus real host proof

## Why This Packet
Packet 764 closed the missing-entrypoint false-positive startup defect, but the next real host rerun exposed one more adjacent truthfulness gap.

Observed host evidence from the first Packet 765 attempt:

1. bounded host dependency install and bounded `apex-fs` plus `apex-db` builds succeeded,
2. managed `up` still returned `{"status":"started"}`,
3. immediate `status` reported `managed-running`,
4. immediate `verify` still failed with `connection refused`,
5. moments later the host logs showed all three services listening and a second `verify` passed.

That meant managed startup could still claim ready state before transport readiness was actually true.

## What Changed
- Updated `tools/ai/run-minimal-mcp-trio.sh` so managed `up` now waits for all three admitted endpoints to answer transport `initialize` before writing managed state and returning `started`.
- Updated `tools/ai/run-minimal-mcp-trio.ps1` with the same readiness barrier.
- Updated both wrappers so managed `status` now requires live endpoint readiness rather than only PID survival.
- Added structured managed-start refusal for the readiness barrier:
  - `status = start-refused`
  - `reason = services-not-ready`
- Extended `tests/test_minimal_mcp_started_truthfulness.py` with Bash and PowerShell startup-timeout refusal coverage and replaced the started-path fake-node shims with transport-ready HTTP shims.
- Updated the first-slice and host cold-start runbooks to describe the readiness barrier and the new `services-not-ready` refusal branch.

## Validation
- Focused executable validation:
  - `./.venv/Scripts/python.exe -m pytest tests/test_minimal_mcp_started_truthfulness.py -q`
  - Result: pass (`6 passed`).
- Authoritative-host bounded build materialization:
  - `/home/olares/apex-data/toolchains/pnpm-10.0.0/node_modules/.bin/pnpm install --filter apex-fs --filter apex-db`
  - `/home/olares/apex-data/toolchains/pnpm-10.0.0/node_modules/.bin/pnpm --filter apex-fs --filter apex-db build`
  - Result: pass.
- Authoritative-host Packet 765 rerun after copying the repaired wrappers to `/home/olares/code/apex/apex-power-ops-platform/tools/ai/`:
  - `bootstrap`: `minimal_mcp = NOT_RUNNING`
  - `up`: `{"status":"started"}`
  - `status`: `managed-running` with all three endpoints ready
  - `verify`: `PASS`
  - `hold-boundary`: `minimal_mcp = PASS`, `deferred_ops = UNAVAILABLE`
  - `down`: `{"status":"stopped"}`
  - final `status`: `{"status":"not-running"}`

## Outcome
Packet 765 closes the next wrapper-level truthfulness defect and produces the first truthful authoritative-host managed cold-start proof in this lane.

The remaining limits are explicit:

1. publication parity is still open because the host proof currently depends on a bounded unpublished working-tree repair on the authoritative mirror,
2. `deferred_ops = UNAVAILABLE` remains the truthful host result until a governed live DSN is present.

## Boundaries Preserved
- No new MCP service admitted.
- No `ai_tasks` queue authority admitted.
- No auth, ingress, or query-scope widening admitted.
- No business logic changed.
- No host `HOLD` or `REOPEN` claim was made without a governed live DSN.