# Olares AI Workflow First Slice Runbook

Date: 2026-05-06
Status: Active bounded operator surface
Scope: current admitted Olares-first AI workflow boundary for reducing relay burden without reopening broad AI-services expansion

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

## Boundary

### In Scope

1. starting and stopping the minimal MCP trio,
2. verifying the trio contract locally or from the host mirror,
3. recording AI-run context in `apex-jobs`,
4. using Claude-compatible tooling against read-only filesystem and database surfaces plus the jobs ledger.

### Out Of Scope

1. Codex admission,
2. Ollama or local-model rollout,
3. Dify or n8n rollout,
4. public ingress,
5. Gitea or canonical-hosting transition,
6. replacing packet and handoff governance with autonomous queueing by assumption.

## Current Trust Model

1. `apex-jobs` is the current operational run ledger.
2. `apex-jobs` is also the current promotion gate because `promote_packet` refuses promotion unless a successful `env=host` run exists.
3. `ai_tasks` remains a future orchestration or integration surface, not the controlling queue for this first slice.
4. Claude Code is the only admitted first-slice AI execution surface.
5. Codex remains deferred until a later explicit decision packet reopens it.

## Operator Commands

The wrappers support two bounded operating modes:

1. managed mode, where the wrapper starts the trio itself,
2. adopted mode, where the wrapper detects an already-running trio on the admitted ports and binds verification to that runtime instead of attempting duplicate listeners.

If neither `.env.dev` nor `.env.dev.template` is present, the wrappers fall back to the admitted default trio ports `8710`, `8711`, and `8712`.

### PowerShell

```powershell
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action up
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action status
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action verify -PacketId 2026-05-06-olares-dev-residency-037
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action down
```

### Bash

```bash
bash tools/ai/run-minimal-mcp-trio.sh up
bash tools/ai/run-minimal-mcp-trio.sh status
bash tools/ai/run-minimal-mcp-trio.sh verify 2026-05-06-olares-dev-residency-037
bash tools/ai/run-minimal-mcp-trio.sh down
```

## Expected Verification Shape

Verification should prove at minimum:

1. `apex-fs` initializes and can read a bounded repo file,
2. `apex-db` initializes and exposes its read-only tool contract,
3. `apex-jobs` initializes, starts a run, and ends that run successfully,
4. the ledger file is written under `.apex-data/apex-jobs-ledger.json` or the equivalent host-local path.

`apex-db` live query success depends on an available PostgreSQL connection string and running database target. That backend dependency is environment-specific and should be reported honestly rather than hidden.

Packet 038 proved the same first slice from `/home/olares/code/apex/apex-power-ops-platform` on the Olares host in adopted mode against the already-running trio on `127.0.0.1:8710-8712`.

## Next Follow-On

After this first slice is in use, the next truthful follow-on is a publication and host-mirror reconciliation gate for the Packet 035 through Packet 038 authority set, followed only later by any decision on an `ai_tasks` bridge or additional MCP admission.