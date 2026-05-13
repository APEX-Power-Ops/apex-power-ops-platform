# Olares AI Host Managed Cold-Start Drill Runbook

Date: 2026-05-12
Status: Active bounded operator validation runbook
Scope: one copy-paste host-side drill for the managed cold-start scenario in the repo-owned AI/operator validation matrix

## Purpose

This runbook turns the host managed cold-start row in the current AI/operator validation matrix into one executable surface.

It does not widen orchestration.

It exists to answer four practical operator questions:

1. what exact packet id and host root should be used,
2. what command order should be run from the Olares host posture,
3. what artifacts must exist at the end,
4. what outcomes are a truthful pass, degradation, or stop.

Use this file with:

1. `OLARES-AI-OPERATOR-REAL-WORLD-VALIDATION-MATRIX-2026-05-12.md`,
2. `../architecture/OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md`,
3. `../OPERATOR-BOOTSTRAP-RUNBOOK.md`,
4. `OLARES-AI-GOVERNED-LIVE-DSN-SOURCING-RUNBOOK-2026-05-12.md`,
5. `../../plan/OLARES-AI-ORCHESTRATION-EXECUTION-PLAN-2026-05-10.md`,
6. `../../PROJECT_STATUS.md`.

## Scenario Goal

The goal is to prove that the authoritative host mirror can start the admitted trio from rest, emit repo-visible bootstrap and verifier evidence, and report the current hold-boundary result truthfully.

The goal is not to prove a host-side live-query widening.

`deferred_ops=UNAVAILABLE` is still a truthful host outcome unless a separately admitted host live-query path exists and works.

## Preconditions

Before running the drill, confirm all of the following:

1. the working host root is `/home/olares/code/apex/apex-power-ops-platform`,
2. the admitted MCP family is still only `apex-fs`, `apex-db`, and `apex-jobs`,
3. the host mirror is clean enough for bounded validation work and not carrying unpublished drift on the controlling wrapper, shell-helper, status-ledger, or runbook surfaces,
4. one explicit packet id has been chosen,
5. the admitted managed service entrypoints exist under `services/mcp/apex-fs/build/http.js`, `services/mcp/apex-db/build/http.js`, and `services/mcp/apex-jobs/build/http.js`,
6. a governed live DSN variable is available only if the drill is meant to exercise the deferred-ops query path.

If the authoritative host root is behind the current published `clean-main` commit or carries unpublished changes on those controlling files, stop and restore host parity first instead of treating the resulting bootstrap or cold-start output as canonical proof.

If the host mirror is missing those build entrypoints because the workspace dependencies were never materialized there, install and build the bounded MCP services before retrying the drill instead of treating the failure as verifier drift.

Recommended packet-id shape:

```text
2026-05-12-olares-dev-residency-<packet>
```

Packet ids are now rejected unless they match `^[A-Za-z0-9][A-Za-z0-9._-]*$`. Do not pass whitespace, shell-escaped placeholders, slashes, or backslashes, because the wrappers now fail fast instead of writing malformed repo-visible artifact paths.

## Host Command Sequence

### SSH Entry

Use one bounded shell on the host:

```powershell
ssh olares-mesh
```

Then switch to the authoritative repo root:

```bash
cd /home/olares/code/apex/apex-power-ops-platform
```

### Packet Setup

Choose one packet id and keep it fixed across all commands below:

```bash
export APEX_PACKET_ID=<packet-id>
```

If this drill is intentionally using a governed live DSN, export it now under the approved variable name:

```bash
export APEX_OLARES_LIVE_DSN='<live dsn>'
```

Use `OLARES-AI-GOVERNED-LIVE-DSN-SOURCING-RUNBOOK-2026-05-12.md` when the host credential has not yet been loaded from the non-git secret boundary.

If the packet is being driven through one bounded noninteractive SSH command, source the non-git loader file or export `APEX_OLARES_LIVE_DSN` inside that same command chain. Do not assume another host shell already exported it for you.

If no governed live DSN is present, do not fabricate one and do not expect a host-side deferred hold verdict.

### Drill Commands

1. Baseline bootstrap from rest:

```bash
bash tools/ai/run-olares-host-bootstrap-status.sh "$APEX_PACKET_ID"
```

2. Start the admitted trio in managed mode:

```bash
bash tools/ai/run-minimal-mcp-trio.sh up
```

3. Confirm the running state explicitly:

```bash
bash tools/ai/run-minimal-mcp-trio.sh status
```

4. Verify the minimal trio under the same packet id:

```bash
bash tools/ai/run-minimal-mcp-trio.sh verify "$APEX_PACKET_ID"
```

5. Run hold-boundary with or without the governed live DSN path:

With live DSN:

```bash
bash tools/ai/run-olares-hold-boundary-check.sh "$APEX_PACKET_ID" APEX_OLARES_LIVE_DSN
```

Without live DSN:

```bash
bash tools/ai/run-olares-hold-boundary-check.sh "$APEX_PACKET_ID"
```

6. Stop the managed trio cleanly:

```bash
bash tools/ai/run-minimal-mcp-trio.sh down
```

7. Optionally confirm clean teardown:

```bash
bash tools/ai/run-minimal-mcp-trio.sh status
```

## Expected Truthful Outcomes

Interpret the drill narrowly:

1. the initial bootstrap may truthfully report `minimal_mcp = NOT_RUNNING` before startup,
2. the managed `up` path should produce a running managed trio only after all three admitted endpoints answer transport `initialize`, or a truthful refusal such as `start-refused` when required entrypoints are missing or the services do not become ready,
3. `verify` should return `PASS` only if the admitted trio and `apex-jobs` ledger path actually work,
4. `deferred_ops=UNAVAILABLE` on the host remains a truthful pass when no admitted host live-query path exists,
5. `HOLD` or `REOPEN` should be claimed only when a governed live DSN is present and the helper actually returns that result.

Stop rather than over-interpret the run if:

1. the host root is wrong,
2. the bootstrap artifact cannot be written,
3. the trio verifies against foreign ownership,
4. the run would require a new orchestration service, auth widening, or business-logic mutation,
5. the packet id diverges across emitted artifacts,
6. the authoritative host mirror is behind the current published repo state or dirty on the controlling wrapper, shell-helper, status-ledger, or runbook files.

## Required Evidence

At minimum, the drill should leave these repo-visible artifacts for the same packet id:

1. `tests/canary/host-bootstrap-status/actual/host-bootstrap-status-<packet-id>.json`,
2. `tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-<packet-id>.json`,
3. `tests/canary/deferred-ops-view-counts/actual/deferred-ops-view-counts-<packet-id>.json` when hold-boundary was run,
4. the corresponding packet or handoff closeout entry.

If the deferred-ops helper is not run, record that omission explicitly rather than implying a host hold verdict.

## Closeout Template

Use this result skeleton in the packet or handoff:

```text
packet_id: <packet-id>
root: /home/olares/code/apex/apex-power-ops-platform
bootstrap: <NOT_RUNNING|HOLD|REOPEN|UNAVAILABLE block summary>
up: <started|adopted|refused>
verify: <PASS|FAIL>
deferred_ops: <HOLD|REOPEN|UNAVAILABLE|not-run>
down: <stopped status>
artifacts:
  - tests/canary/host-bootstrap-status/actual/host-bootstrap-status-<packet-id>.json
  - tests/canary/mcp-contract/actual/verify-minimal-mcp-trio-<packet-id>.json
  - tests/canary/deferred-ops-view-counts/actual/deferred-ops-view-counts-<packet-id>.json
boundary_preserved:
  - no new MCP service admitted
  - no ai_tasks queue ownership admitted
  - no auth or ingress widening
  - no host-complete promotion claim without env=host evidence
```

## Current Recommendation

Use this runbook for the first host managed cold-start packet after the workstation baseline is already understood.

Do not treat this runbook as permission to widen host query authority or to skip the workstation comparison point when a governed live DSN becomes available again.