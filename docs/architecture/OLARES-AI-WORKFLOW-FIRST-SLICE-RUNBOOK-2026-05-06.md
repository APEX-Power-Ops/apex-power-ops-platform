# Olares AI Workflow First Slice Runbook

Date: 2026-05-06
Status: Active bounded operator surface with operator-on-demand default runtime posture
Scope: current admitted Olares-first AI workflow boundary for reducing relay burden without reopening broad AI-services expansion

Companion decision surface: `OLARES-AI-ORCHESTRATION-DECISION-SURFACE-2026-05-07.md`

## Purpose

This runbook captures the current first admitted AI workflow slice for the Olares lane.

It does not install new AI services.

It uses the already-present minimal MCP trio and the `apex-jobs` ledger as the working trust boundary for AI-assisted execution.

## Admitted First-Slice Surfaces

1. `services/mcp/apex-fs/build/http.js`
2. `services/mcp/apex-db/build/http.js`
3. `services/mcp/apex-jobs/build/http.js`
4. `tools/ai/run-minimal-mcp-trio.ps1`
5. `tools/ai/run-minimal-mcp-trio.sh`
6. `tools/ai/verify_minimal_mcp_trio.py`
7. `tools/ai/check_deferred_ops_view_counts.py`
8. `tools/ai/run-olares-hold-boundary-check.ps1`
9. `tools/ai/run-olares-hold-boundary-check.sh`
10. `tools/ai/run-olares-host-bootstrap-status.sh`

## Boundary

### In Scope

1. starting and stopping the minimal MCP trio,
2. verifying the trio contract locally or from the host mirror,
3. recording AI-run context in `apex-jobs`,
4. using Claude-compatible tooling against read-only filesystem and database surfaces plus the jobs ledger.

### Out Of Scope

1. Codex integration into the minimal-trio wrapper or promotion path,
2. Ollama or local-model rollout,
3. Dify or n8n rollout,
4. public ingress,
5. Gitea or canonical-hosting transition,
6. replacing packet and handoff governance with autonomous queueing by assumption.

## Current Trust Model

1. `apex-jobs` is the current operational run ledger.
2. `apex-jobs` is also the current promotion gate because `promote_packet` refuses promotion unless a successful `env=host` run exists.
3. `ai_tasks` remains a future orchestration or integration surface, not the controlling queue for this first slice.
4. Claude Code is the current packetized first-slice AI execution surface for the minimal MCP trio.
5. Codex is an approved premium-plan interactive surface, but it is not yet bound to this wrapper or its promotion path until a later explicit packet admits that integration.

## Default Runtime Posture

Packet 095 closes the current runtime-governance question for this first slice.

The admitted trio remains operator-on-demand by default.

That means:

1. `minimal_mcp.status = not-running` on the authoritative host bootstrap surface is a valid steady-state result,
2. normal durable-host readiness does not require the trio to remain running between bounded operator sessions,
3. operators should start the trio only for bounded verification, cadence, or AI-assisted execution that actually needs the MCP endpoints online,
4. a separate later packet is required before always-on trio runtime becomes part of default host readiness.

## Operator Commands

The wrappers support two bounded operating modes:

1. managed mode, where the wrapper starts the trio itself,
2. adopted mode, where the wrapper detects an already-running trio on the admitted ports and binds verification to that runtime instead of attempting duplicate listeners.

If neither `.env.dev` nor `.env.dev.template` is present, the wrappers fall back to the admitted default trio ports `8710`, `8711`, and `8712`.

### PowerShell

```powershell
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action up
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action status
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action verify -PacketId <packet-id>
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action down
pwsh tools/ai/run-olares-hold-boundary-check.ps1 -PacketId <packet-id>
```

### Bash

```bash
bash tools/ai/run-minimal-mcp-trio.sh up
bash tools/ai/run-minimal-mcp-trio.sh status
bash tools/ai/run-minimal-mcp-trio.sh verify <packet-id>
bash tools/ai/run-minimal-mcp-trio.sh down
bash tools/ai/run-olares-hold-boundary-check.sh <packet-id>
bash tools/ai/run-olares-host-bootstrap-status.sh <packet-id>
```

## Host Bootstrap Status

`tools/ai/run-olares-host-bootstrap-status.sh` is the bounded durable-host entry surface for the current Olares development posture.

It is status-only.

It does not install packages, mutate services, or widen the current trust boundary.

If a packet id is omitted on the admitted minimal-trio, hold-boundary, or host-bootstrap wrappers, or on the direct `verify_minimal_mcp_trio.py` and `check_deferred_ops_view_counts.py` helper commands, they now prefer `APEX_PACKET_ID` and otherwise generate a fresh ad-hoc timestamped id, so current operator evidence is not written under preserved historical packet names.

On Bash surfaces, the shared Python resolver now prefers the repo-local interpreter when it is usable and otherwise falls back to native `python3` or `python`; if `APEX_PLATFORM_PYTHON` supplies a bare command name such as `python3`, the resolver materializes it to the actual command path, explicit path-style overrides must point to a real interpreter, and on Linux-style shells it rejects Windows `python.exe` overrides that cannot execute the wrappers' POSIX script paths.

It reports:

1. current host parent-root parity and status,
2. old-clone observe-only state,
3. materialized host toolchain presence, including the preferred Python path and version actually used by Bash AI surfaces,
4. minimal MCP trio readiness,
5. current hold-boundary result from the host posture.

When emitted, the composed host-bootstrap summary now also writes repo-visible JSON output to `tests/canary/host-bootstrap-status/actual/host-bootstrap-status-<packet-id>.json`; if the historical old-clone path is absent in the current environment, that field now degrades truthfully instead of crashing the whole status surface.

## Hold-Boundary Cadence

The hold-boundary wrapper combines two bounded checks:

1. minimal MCP trio verification,
2. deferred Operations Visibility live-row recheck for `v_resource_allocation` and `v_equipment_needs`.

The deferred-view helper prefers an explicit live DSN when one is intentionally supplied because the local `.env.dev` contract is a developer database and is not authoritative for the live `09` tranche hold decision.

The PowerShell wrapper now uses that explicit live DSN through the repo venv's direct Python database path.

The Bash wrapper first tries the same direct path when host Python can import `sqlalchemy`; if not, it only attempts a temporary live `apex-db` sidecar when the current mirror actually contains a runnable `services/mcp/apex-db` source tree.

If no live DSN is present, the helper returns `UNAVAILABLE` rather than a false hold decision. That is an honest operator result, not a silent pass.

When emitted, the minimal-trio verifier artifact stays in `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-<packet-id>.json` and the deferred-view helper now writes repo-visible JSON output to `tests/canary/deferred-ops-view-counts/actual/deferred-ops-view-counts-<packet-id>.json` instead of leaving that evidence only under `.tmp/ai-workflow/`.

If a live DSN is present but the current host posture lacks every usable live-query engine, the Bash wrapper also degrades back to `UNAVAILABLE` instead of failing. That is the current truthful host posture on `/home/olares/code/apex/apex-power-ops-platform`.

Packet 058 established the current authoritative verdict from the workstation posture against a governed live Supabase DSN: both deferred views still have `0` rows, so the hold decision remains `HOLD` rather than `REOPEN`.

### Live-DSN Examples

```powershell
$env:APEX_OLARES_LIVE_DSN = '<live dsn>'
pwsh tools/ai/run-olares-hold-boundary-check.ps1 -PacketId 2026-05-06-olares-dev-residency-058 -DsnEnv APEX_OLARES_LIVE_DSN
```

```bash
export APEX_OLARES_LIVE_DSN='<live dsn>'
bash tools/ai/run-olares-hold-boundary-check.sh 2026-05-06-olares-dev-residency-058 APEX_OLARES_LIVE_DSN
```

The current workstation result with a governed live DSN is `minimal_mcp=PASS` and `deferred_ops=HOLD`.

The current authoritative host-mirror result with the same live DSN remains `minimal_mcp=PASS` and `deferred_ops=UNAVAILABLE` until a separately bounded host-query engine is admitted.

## Current Hold-Boundary Verdict

1. `public.v_resource_allocation` currently has `0` live rows.
2. `public.v_equipment_needs` currently has `0` live rows.
3. The truthful current verdict is `HOLD`, not `REOPEN`.

## Expected Verification Shape

Verification should prove at minimum:

1. `apex-fs` initializes and can read a bounded repo file,
2. `apex-db` initializes and exposes its read-only tool contract,
3. `apex-jobs` initializes, starts a run, and ends that run successfully,
4. the ledger file is written under `.apex-data/apex-jobs-ledger.json` or the equivalent host-local path.

`apex-db` live query success depends on an available PostgreSQL connection string and running database target. That backend dependency is environment-specific and should be reported honestly rather than hidden.

Packet 038 proved the same first slice from `/home/olares/code/apex/apex-power-ops-platform` on the Olares host in adopted mode against the already-running trio on `127.0.0.1:8710-8712`.

## Current Follow-On

The runtime-governance lane for this first slice is now closed in favor of the lower-variance operator-on-demand posture.

The next truthful follow-on is not default-runtime widening.

Reopen this runbook's runtime posture only if:

1. repeated operator evidence shows startup overhead is now a controlling problem,
2. a bounded unattended workflow requires the trio to be online by default,
3. or a later packet explicitly admits a durable-runtime readiness proof.