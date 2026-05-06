# Olares Dev Residency 036 - AI Workflow Boundary And Relay-Reduction First-Slice Planning Handoff

Date: 2026-05-06
Status: Complete
Packet: `2026-05-06-olares-dev-residency-036`

## Outcome

The first bounded Olares-first AI workflow slice is selected.

Packet 036 chooses the already-present minimal MCP trio plus the `apex-jobs` run ledger as the first execution surface for relay reduction.

## Decision

Packet 036 selects:

`select_minimal_mcp_trio_and_apex_jobs_operator_surface_execution`

## Basis

1. The repo already contains executable `apex-fs`, `apex-db`, and `apex-jobs` HTTP bridges.
2. The canary surfaces already prove the tool list for that trio and preserve it as repo-visible evidence.
3. `apex-jobs` already implements the env boundary and `promote_packet` refusal logic that the earlier AI assessment needed to see before an admitted first slice could open.
4. Claude Code remains the only first-slice-ready AI surface.
5. Codex, local models, Dify, n8n, and broader AI-services expansion remain outside the first slice.

## Execution Boundary For The Next Packet

The next packet may execute only:

1. a minimal operator surface for starting, stopping, checking, and verifying `apex-fs`, `apex-db`, and `apex-jobs`,
2. a repo-visible runbook that explains the current bounded Olares AI workflow posture,
3. a written restatement of the current `ai_tasks` versus `apex-jobs` boundary and the open Codex decision.

The next packet must not open:

1. Codex admission,
2. broad AI-services installation,
3. Gitea or canonical-hosting transition,
4. public-ingress widening.

## Next Packet Candidate

The next packet is:

`Olares Dev Residency 037 - Minimal MCP Trio Operator Surface And AI Boundary Restatement Execution`