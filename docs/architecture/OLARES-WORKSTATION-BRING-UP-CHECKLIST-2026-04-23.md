# Olares Workstation Bring-Up Checklist

Date: 2026-04-23
Status: Active rerun surface
Scope: bounded workstation rerun for local Olares-aligned dev runtime, MCP proof, and canary evidence refresh

## Purpose

Use this checklist only for bounded workstation reruns after drift in the local
Olares-aligned development shell.

This is not a new-service onboarding surface.

## Current Evidence Floor

Treat these files as the current workstation evidence floor in this workspace
snapshot:

1. `infra/compose.dev.yml`
2. `tools/run-canary.ps1`
3. `tools/run-canary.sh`
4. `tools/canary/run_canary.py`
5. `tools/shell/common.ps1`
6. `tools/shell/common.sh`
7. `packages/forms-engine/src/apex_forms_engine/runtime.py`
8. `packages/p6-ingest/src/apex_p6_ingest/runtime.py`
9. `services/mcp/*/build/http.js`
10. `tests/canary/**/actual/*`
11. `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md`

## Preconditions

1. `.env.dev` exists for machine-local overrides, or `.env.dev.template` remains usable as the bounded default env source
2. Node.js is available for the MCP HTTP bridges under `services/mcp/*/build/`
3. `C:/APEX Platform/.venv/Scripts/python.exe` is available for the bounded Python runtime shells
4. the admitted schedule fixture remains present at `apps/mutation-seam/app/schedule/fixtures/stack_data_center_baseline_sanitized.xer`

## Rerun Steps

1. verify that `infra/compose.dev.yml`, `tools/run-canary.ps1`, `tools/run-canary.sh`, and `tools/canary/run_canary.py` are present and readable
2. verify that the MCP HTTP bridges remain present under `services/mcp/apex-fs/build/http.js`, `services/mcp/apex-db/build/http.js`, `services/mcp/apex-jobs/build/http.js`, `services/mcp/apex-forms/build/http.js`, and `services/mcp/apex-p6/build/http.js`
3. verify that the forms runtime shell remains present under `packages/forms-engine/src/apex_forms_engine/runtime.py`
4. verify that the p6 runtime shell remains present under `packages/p6-ingest/src/apex_p6_ingest/runtime.py`
5. run `pwsh -NoProfile -File tools/run-canary.ps1` on Windows or `bash tools/run-canary.sh` on POSIX hosts
6. confirm that the rerun refreshed these runtime-proof outputs:
   - `tests/canary/forms-engine-dev-runtime/actual/health.json`
   - `tests/canary/p6-ingest-dev-runtime/actual/health.json`
   - `tests/canary/p6-ingest-dev-runtime/actual/summary.json`
   - `tests/canary/mcp-contract/actual/mcp-tool-lists.json`
7. confirm that the rerun refreshed these staging outputs:
   - `tests/canary/forms-engine-staging-manifest/actual/OlaresManifest.yaml`
   - `tests/canary/forms-engine-staging-render/actual/rendered-chart.yaml`
   - `tests/canary/p6-ingest-staging-manifest/actual/OlaresManifest.yaml`
   - `tests/canary/p6-ingest-staging-render/actual/rendered-chart.yaml`

## Exit Condition

The workstation rerun remains valid when the canary wrapper completes without
error and the runtime-proof plus staging outputs refresh under `tests/canary/`
without widening outside the bounded Olares surface.
