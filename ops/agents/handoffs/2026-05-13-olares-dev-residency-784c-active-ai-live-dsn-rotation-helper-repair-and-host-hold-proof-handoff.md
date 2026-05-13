# Packet 784c Handoff - Active AI Live-DSN Rotation, Helper Repair, And Host Hold Proof

## Packet
- Packet ID: `2026-05-13-olares-dev-residency-784c`
- Lane: active AI/operator boundary validation and operational recovery
- Scope: rotate the compromised governed live DSN, update dependent runtime surfaces, repair deferred-ops MCP row-shape handling, and rerun authoritative-host hold proof
- Change type: operational secret rotation, bounded helper repair, runtime revalidation, and host evidence publication

## Why This Packet
A real pooler DSN was exposed and had to be replaced across the governed workstation boundary, the authoritative host boundary, and Render.

The first authoritative-host rerun under Packet `2026-05-13-olares-dev-residency-784` proved that the same-shell host secret path was now present and that the managed trio still verified cleanly, but it also exposed one narrower defect: `tools/ai/check_deferred_ops_view_counts.py` assumed the deferred-ops query result was always a list of row dictionaries.

That assumption was wrong for the MCP query path, which returns a structured payload with `rowCount` and `rows`.

## What Changed
- Rotated the governed live DSN and replaced the persisted secret on the workstation loader, the authoritative-host loader, and Render `DATABASE_URL`.
- Triggered a Render rebuild after the secret update and verified the public health endpoint returned `200` with `{"status":"ok"}`.
- Patched `tools/ai/check_deferred_ops_view_counts.py` so the deferred-ops helper now normalizes both direct-SQL row lists and MCP `rowCount` plus `rows` payloads.
- Synced the patched helper to `/home/olares/code/apex/apex-power-ops-platform` before the host rerun.
- Reran the authoritative-host managed cold-start and hold-boundary path under Packet `2026-05-13-olares-dev-residency-784c`.
- Updated `PROJECT_STATUS.md` through Packet 784c.

## Validation
### Initial host proof before repair
Packet `2026-05-13-olares-dev-residency-784` on the authoritative host produced:
- same-shell host secret proof: `{"has_live_dsn":true}`
- host bootstrap from rest: `minimal_mcp = NOT_RUNNING`
- managed trio verify: `PASS`
- deferred ops: `FAIL` with `string indices must be integers, not 'str'`

That failure was truthful and is preserved in the published artifact set.

### Focused helper repair validation
Executed locally through the wrapper path with the governed workstation secret loaded:
- `tools/ai/run-minimal-mcp-trio.ps1 -Action up`
- `tools/ai/run-olares-hold-boundary-check.ps1 -PacketId 2026-05-13-olares-dev-residency-784-localprobe -DsnEnv APEX_OLARES_LIVE_DSN`
- observed result: `deferred_ops = HOLD`

The local probe artifacts were deleted after validation so the published artifact set stays focused on the authoritative host packet family.

### Render runtime revalidation
- Render deploy id: `dep-d827cpjtqb8s73cbc700`
- deploy finished successfully
- public health check: `https://control.apexpowerops.com/health` -> `200` and `{"status":"ok"}`

### Final authoritative-host proof after repair
Packet `2026-05-13-olares-dev-residency-784c` on `/home/olares/code/apex/apex-power-ops-platform` produced:
- same-shell host secret proof: `{"has_live_dsn":true}`
- bootstrap from rest: `minimal_mcp = NOT_RUNNING`, `deferred_ops = UNAVAILABLE`
- managed startup: `started`
- explicit running state: `managed-running`
- minimal trio verify: `PASS`
- hold-boundary: `HOLD`
- authoritative live counts:
  - `v_equipment_needs = 0`
  - `v_resource_allocation = 0`
- teardown: `stopped`
- post-run host rest-state confirmation: `{"status":"not-running"}`

## Repo-Visible Evidence
- `tests/canary/host-bootstrap-status/actual/host-bootstrap-status-2026-05-13-olares-dev-residency-784.json`
- `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-13-olares-dev-residency-784.json`
- `tests/canary/deferred-ops-view-counts/actual/deferred-ops-view-counts-2026-05-13-olares-dev-residency-784.json`
- `tests/canary/host-bootstrap-status/actual/host-bootstrap-status-2026-05-13-olares-dev-residency-784c.json`
- `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-2026-05-13-olares-dev-residency-784c.json`
- `tests/canary/deferred-ops-view-counts/actual/deferred-ops-view-counts-2026-05-13-olares-dev-residency-784c.json`

## Outcome
The governed live-DSN blocker is now closed as an operational dependency.

The truthful current live verdict is still `HOLD`, but for the right reason now: the authoritative deferred Operations Visibility seams remain empty, not because the governed credential path is absent.

The next bounded AI/operator gate is no longer credential recovery. It is the first promotion-eligible `env=host` evidence slice, such as an adopted-runtime host packet routed through the same packet, artifact, and handoff governance path.

## Boundaries Preserved
- No new MCP service was admitted.
- No `ai_tasks` queue ownership was admitted.
- No auth or ingress scope widened.
- No promotion claim was made without `env=host` evidence.
- The initial Packet 784 failure artifacts were preserved as truthful evidence instead of being discarded.
