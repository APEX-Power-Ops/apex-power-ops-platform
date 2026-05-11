# Olares Dev Residency 503 - Active AI Canary Entrypoint Readiness Hardening Handoff

Date: 2026-05-11
Status: Complete
Packet: `2026-05-11-olares-dev-residency-503`

## Purpose

Close the next adjacent active AI canary-entrypoint reliability slice by replacing the governed canary wrappers' blind fixed sleep with bounded readiness polling.

## Execution Result

Packet 503 is complete.

`tools/run-canary.ps1` and `tools/run-canary.sh` now wait explicitly for the forms-engine and p6-ingest runtimes to answer `/health`, and for the MCP transports to answer on `/mcp`, before handing off to `tools/canary/run_canary.py`.

The first implementation pass incorrectly waited on MCP `/health` for every service; focused validation exposed that `apex-db` uses `/health` as a live query probe and therefore failed readiness when no connection string was supplied by the wrapper. The packet was repaired in-slice by switching MCP readiness to `/mcp`, which matches what the canary runner itself uses for initialization and tool discovery.

This hardens the current canary entry surface against startup races without changing the canary runner's artifact contract or reopening the closed default-port lane.

## Validation Notes

Focused validation stayed bounded to the canary-entrypoint slice.

Checks confirmed:

1. `pwsh -NoProfile -ExecutionPolicy Bypass -File tools/run-canary.ps1` now completes successfully with readiness polling in place.
2. `git diff --check -- tools/run-canary.ps1 tools/run-canary.sh` reported no patch-format defects.
3. diagnostics for `tools/run-canary.ps1` and `tools/run-canary.sh` reported no new file-level errors.
4. the working-tree delta stayed bounded to `tools/run-canary.ps1` and `tools/run-canary.sh` for the code change itself.

## Boundaries Preserved

This packet does not open:

1. canary artifact schema changes,
2. minimal-trio port or boundary changes,
3. historical packet-evidence rewrites,
4. compose runtime redesign,
5. broader orchestration or queue-admission changes.

## Next Candidate

No further adjacent current-surface defect is selected from this packet alone; the next lane should be another genuinely current control, evidence, or operator surface that still disagrees with the admitted AI contract on present evidence.