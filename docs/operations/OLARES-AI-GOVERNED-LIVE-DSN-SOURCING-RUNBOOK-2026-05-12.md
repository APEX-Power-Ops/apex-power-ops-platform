# Olares AI Governed Live-DSN Sourcing Runbook

Date: 2026-05-12
Status: Active bounded operator credential-sourcing runbook
Scope: one governed non-git path for making a live DSN available to the workstation and host AI/operator validation surfaces

## Purpose

This runbook turns the live-DSN prerequisite in the current AI/operator validation matrix into one explicit operator step.

It does not widen orchestration.

It exists to answer four practical operator questions:

1. where the governed live DSN may live,
2. which environment variable names the current wrappers actually honor,
3. how to materialize the credential without committing it to git,
4. how to confirm presence without printing the secret value.

Use this file with:

1. `OLARES-AI-WORKSTATION-LIVE-DSN-BASELINE-RUNBOOK-2026-05-12.md`,
2. `OLARES-AI-HOST-MANAGED-COLD-START-DRILL-RUNBOOK-2026-05-12.md`,
3. `OLARES-AI-OPERATOR-REAL-WORLD-VALIDATION-MATRIX-2026-05-12.md`,
4. `../authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`,
5. `../architecture/APEX-PM-LANE-OPERATING-COCKPIT-2026-05-06.md`.

## Credential Boundary

Use these rules as hard boundaries:

1. secrets never live inside the git workspace,
2. `.secrets/` remains outside the repo contract,
3. the live DSN must be loaded explicitly for the bounded operator session,
4. the operator may confirm presence, but should not print the secret value into terminal history, repo files, packet text, or handoffs.

For the host posture, the existing authority surface already names `~/apex-secrets/` as the non-git secret boundary.

For the workstation posture, use a local non-git secret source such as:

1. a per-session environment assignment,
2. a PowerShell profile or local secret-loader script that is not committed to the repo,
3. a host-local or workstation-local credential file outside the repo boundary.

## Approved Variable Names

Use these names in this order:

1. `APEX_OLARES_LIVE_DSN` as the operator-facing validation variable,
2. `SEAM_DATABASE_URL` as the authoritative live-query variable already named in the Operations Visibility lane,
3. `APEX_DB_CONNECTION_STRING` or `DATABASE_URL` only as fallback compatibility inputs when a bounded session already uses them and the operator is certain they point to the governed live target.

Current wrapper behavior:

1. `run-olares-hold-boundary-check.ps1` and `.sh` accept a named DSN env variable and route its value into `SEAM_DATABASE_URL`,
2. `run-minimal-mcp-trio.ps1` and `.sh` will prefer `APEX_OLARES_LIVE_DSN`, then `SEAM_DATABASE_URL`, then `APEX_DB_CONNECTION_STRING`, then `DATABASE_URL` when resolving the database connection string.

That means the cleanest operator pattern is:

1. set `APEX_OLARES_LIVE_DSN` for the packet,
2. let the minimal-trio wrappers consume that operator-facing variable directly for managed workstation runs,
3. call the hold-boundary wrapper with `-DsnEnv APEX_OLARES_LIVE_DSN` or the Bash equivalent,
4. let the hold-boundary wrapper map the governed value into the lower-level variable it needs.

## Workstation Materialization

### PowerShell Session-Only Pattern

Use this for one bounded workstation packet without leaving the value in the repo:

```powershell
$env:APEX_OLARES_LIVE_DSN = '<live dsn>'
```

Then run the packet from the workstation baseline runbook.

When the session ends, the value disappears with that process.

### PowerShell Non-Git Loader Pattern

If the credential must be reused across bounded operator sessions, store it outside the repo in one local-only file and source it explicitly:

```powershell
$secretPath = "$HOME/apex-secrets/olares/ai-live-dsn.ps1"
. $secretPath
```

Example content for the non-git loader file:

```powershell
$env:APEX_OLARES_LIVE_DSN = '<live dsn>'
```

Do not place that file under `C:/APEX Platform/apex-power-ops-platform`.

## Host Materialization

For host-side validation, keep the credential outside the repo and load it explicitly from the non-git secret boundary:

```bash
source ~/apex-secrets/olares/ai-live-dsn.env
export APEX_OLARES_LIVE_DSN
```

Example content for the non-git host loader file:

```bash
export APEX_OLARES_LIVE_DSN='<live dsn>'
```

Do not commit that file and do not move it under `/home/olares/code/apex/apex-power-ops-platform`.

## Presence Checks Without Disclosure

Use these checks when a packet needs to prove the credential is loaded without printing the value.

PowerShell:

```powershell
[pscustomobject]@{
  has_live_dsn = [string]::IsNullOrWhiteSpace($env:APEX_OLARES_LIVE_DSN) -eq $false
} | ConvertTo-Json
```

Bash:

```bash
if [[ -n "${APEX_OLARES_LIVE_DSN:-}" ]]; then
  printf '{"has_live_dsn":true}\n'
else
  printf '{"has_live_dsn":false}\n'
fi
```

## Stop Conditions

Stop rather than improvising if any of the following are true:

1. the only available DSN source is a repo-tracked file,
2. the operator cannot tell whether `DATABASE_URL` or `APEX_DB_CONNECTION_STRING` points to the governed live target,
3. the credential would need to be copied into a packet, handoff, or repo-owned evidence file,
4. the session would need a broader secret-management change outside this bounded validation lane.

## Current Recommendation

For workstation validation, prefer a session-only `APEX_OLARES_LIVE_DSN` assignment or one non-git loader file sourced explicitly before the packet starts.

For host validation, prefer an explicit loader under `~/apex-secrets/`.

Do not reopen the validation lane by inventing new variable names or by treating repo-local `.env.dev` as authoritative live proof.