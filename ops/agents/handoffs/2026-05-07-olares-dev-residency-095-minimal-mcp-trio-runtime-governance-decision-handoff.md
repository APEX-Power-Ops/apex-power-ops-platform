# Olares Dev Residency 095 - Minimal MCP Trio Runtime Governance Decision Handoff

Date: 2026-05-07
Status: Complete
Packet: `2026-05-07-olares-dev-residency-095`

## Outcome

The current minimal MCP trio runtime question is now closed as a bounded governance decision.

The admitted trio `apex-fs`, `apex-db`, and `apex-jobs` remains operator-on-demand by default.

This packet does not widen the runtime baseline to require the trio to remain continuously online on the authoritative Olares host.

## Decision Basis

The controlling live proof was the clean authoritative host bootstrap packet run immediately before this decision:

1. authoritative host mirror path: `/home/olares/code/apex/apex-power-ops-platform`
2. authoritative host head: `7f64c651a6b17f1aef2867d643d755b39ea2425b`
3. authoritative host `status_count`: `0`
4. `minimal_mcp.status`: `not-running`
5. `hold_boundary.deferred_ops_decision`: `minimal_mcp_not_running`

That posture is truthful and acceptable because:

1. the published wrappers already support bounded `up`, `status`, `verify`, and `down` execution when the trio is actually needed,
2. adopted-mode proof already exists for an already-running trio,
3. no current validation lane or business lane requires the trio to stay online between bounded operator sessions,
4. current remaining friction is governance and provenance routing residue, not trio runtime insufficiency.

## Boundary Preserved

This packet does not admit:

1. always-on trio runtime as default host baseline,
2. `ai_tasks` bridge widening,
3. broader AI-services rollout,
4. wrapper-level Codex integration,
5. unattended orchestration-service admission,
6. host runtime mutation by implication.

## Updated Governing Interpretation

Use these rules until a later packet proves otherwise:

1. `tools/ai/run-olares-host-bootstrap-status.sh` is the controlling readiness surface.
2. `minimal_mcp.status = not-running` is a valid default steady-state result.
3. Start the trio only for bounded operator sessions, verification, or cadence checks that actually need MCP availability.
4. Open a separate durable-runtime admission packet only when a concrete insufficiency, unattended workflow requirement, or new validation obligation makes operator-on-demand insufficient.

## Next Packet Candidate

The next truthful follow-on is:

`Olares Dev Residency 096 - Historical Parent-Root Helper And Task Demotion Planning`

That later packet should inventory the remaining parent-root helper, task, and routing residue that can still misdirect delegated execution after the standalone repo cutover, then select one smallest demotion or relabeling slice.