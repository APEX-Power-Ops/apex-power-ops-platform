# Olares AI Workstation Live-DSN Baseline Runbook

Date: 2026-05-12
Status: Active bounded operator validation runbook
Scope: one copy-paste workstation-side drill for the live-DSN baseline scenario in the repo-owned AI/operator validation matrix

## Purpose

This runbook turns the workstation live-DSN baseline row in the current AI/operator validation matrix into one executable surface.

It does not widen orchestration.

It exists to answer four practical operator questions:

1. what exact packet id and local repo root should be used,
2. what command order should be run from the workstation posture,
3. what artifacts must exist at the end,
4. what outcomes are a truthful pass, hold, degradation, or stop.

Use this file with:

1. `OLARES-AI-OPERATOR-REAL-WORLD-VALIDATION-MATRIX-2026-05-12.md`,
2. `../architecture/OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md`,
3. `APEX-JOBS-TRUST-AND-PROMOTION-CONTRACT-2026-05-08.md`,
4. `../../plan/OLARES-AI-ORCHESTRATION-EXECUTION-PLAN-2026-05-10.md`,
5. `../../PROJECT_STATUS.md`.

## Scenario Goal

The goal is to prove that the workstation posture still provides the authoritative comparison point for the admitted minimal MCP trio and the deferred Operations Visibility hold-boundary result when a governed live DSN is intentionally supplied.

The goal is not to widen host query authority or to treat a workstation result as host-qualified promotion proof.

The authoritative workstation verdict remains `minimal_mcp=PASS` and `deferred_ops=HOLD` unless the live business rows have genuinely changed.

## Preconditions

Before running the drill, confirm all of the following:

1. the local repo root is `C:/APEX Platform/apex-power-ops-platform`,
2. the admitted MCP family is still only `apex-fs`, `apex-db`, and `apex-jobs`,
3. the repo-local Python environment is available for the bounded wrapper and helper paths,
4. one explicit packet id has been chosen,
5. a governed live DSN is available under the approved variable name,
6. no scenario widens auth, public ingress, queue ownership, or business logic scope.

Recommended packet-id shape:

```text
2026-05-12-olares-dev-residency-<packet>
```

Packet ids are now rejected unless they match `^[A-Za-z0-9][A-Za-z0-9._-]*$`. Do not pass whitespace, shell-escaped placeholders, slashes, or backslashes, because the wrappers now fail fast instead of writing malformed repo-visible artifact paths.

## PowerShell Command Sequence

Open one bounded PowerShell session at the repo root:

```powershell
cd 'C:\APEX Platform\apex-power-ops-platform'
$env:APEX_PACKET_ID = '<packet-id>'
$env:APEX_OLARES_LIVE_DSN = '<live dsn>'
```

Run the scenario in this order:

1. Start the admitted trio in managed mode:

```powershell
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action up
```

2. Confirm the running state explicitly:

```powershell
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action status
```

3. Verify the minimal trio under the same packet id:

```powershell
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action verify -PacketId $env:APEX_PACKET_ID
```

4. Run the hold-boundary check against the governed live DSN:

```powershell
pwsh tools/ai/run-olares-hold-boundary-check.ps1 -PacketId $env:APEX_PACKET_ID -DsnEnv APEX_OLARES_LIVE_DSN
```

5. Stop the managed trio cleanly:

```powershell
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action down
```

6. Optionally confirm clean teardown:

```powershell
pwsh tools/ai/run-minimal-mcp-trio.ps1 -Action status
```

## Bash Command Sequence

Use this only when the workstation shell is intentionally running the Bash wrappers with a valid local interpreter path:

```bash
cd /mnt/c/APEX\ Platform/apex-power-ops-platform
export APEX_PACKET_ID='<packet-id>'
export APEX_OLARES_LIVE_DSN='<live dsn>'
bash tools/ai/run-minimal-mcp-trio.sh up
bash tools/ai/run-minimal-mcp-trio.sh status
bash tools/ai/run-minimal-mcp-trio.sh verify "$APEX_PACKET_ID"
bash tools/ai/run-olares-hold-boundary-check.sh "$APEX_PACKET_ID" APEX_OLARES_LIVE_DSN
bash tools/ai/run-minimal-mcp-trio.sh down
bash tools/ai/run-minimal-mcp-trio.sh status
```

If the Bash posture would require a Windows `python.exe` override that cannot execute the POSIX script paths, stop and use the PowerShell sequence instead of treating that mismatch as orchestration drift.

## Expected Truthful Outcomes

Interpret the drill narrowly:

1. `up` should produce a managed-running trio only after all three admitted endpoints answer transport `initialize`, or a truthful refusal such as `start-refused` when the services cannot become ready,
2. `verify` should return `PASS` only if the admitted trio and the `apex-jobs` ledger path actually work,
3. the hold-boundary result should return `HOLD` when both governed deferred views still have `0` live rows,
4. `REOPEN` should be claimed only when the governed live query path actually reports reopened business rows,
5. the workstation result is the authoritative comparison point for later host-side interpretation, but it is not host-qualified promotion proof.

Stop rather than over-interpret the run if:

1. the governed live DSN is missing,
2. the trio verifies against foreign ownership or stale state,
3. the helper degrades to `UNAVAILABLE` because the live-query path is not actually available in the chosen workstation posture,
4. the packet id diverges across emitted artifacts,
5. the run would require a new orchestration service, auth widening, or business-logic mutation.

## Required Evidence

At minimum, the drill should leave these repo-visible artifacts for the same packet id:

1. `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-<packet-id>.json`,
2. `tests/canary/deferred-ops-view-counts/actual/deferred-ops-view-counts-<packet-id>.json`,
3. the corresponding packet or handoff validation block,
4. the resulting `apex-jobs` run id when the verifier records it.

If the live DSN was not intentionally supplied, do not treat the result as a completed workstation baseline. Record that the scenario was not run as designed.

## Closeout Template

Use this result skeleton in the packet or handoff:

```text
packet_id: <packet-id>
root: C:/APEX Platform/apex-power-ops-platform
posture: workstation
up: <started|adopted|refused>
verify: <PASS|FAIL>
deferred_ops: <HOLD|REOPEN|UNAVAILABLE>
down: <stopped status>
artifacts:
  - tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-<packet-id>.json
  - tests/canary/deferred-ops-view-counts/actual/deferred-ops-view-counts-<packet-id>.json
boundary_preserved:
  - no new MCP service admitted
  - no ai_tasks queue ownership admitted
  - no auth or ingress widening
  - no host-qualified promotion claim made from workstation evidence
```

## Current Recommendation

Use this runbook before any host managed cold-start or adopted-runtime drill is interpreted as a boundary change.

Do not skip this baseline when a governed live DSN is available, because the workstation result is the comparison point that explains whether later host differences are expected boundary behavior or genuine drift.
