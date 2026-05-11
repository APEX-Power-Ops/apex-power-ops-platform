# Olares Dev Residency 464 - Active PowerShell Python Override Normalization Repair Handoff

Date: 2026-05-10
Status: Complete
Packet: `2026-05-10-olares-dev-residency-464`

## Purpose

Close the next adjacent bounded PowerShell interpreter defect by normalizing `APEX_PLATFORM_PYTHON` overrides in `tools/shell/common.ps1` so bare command names resolve truthfully and missing explicit paths fail fast.

## Execution Result

Packet 464 is complete.

`tools/shell/common.ps1` now treats `APEX_PLATFORM_PYTHON` more truthfully on PowerShell surfaces:

1. a bare command name such as `python` resolves to the executable path returned by `Get-Command`,
2. an explicit path override must exist and is normalized through `Resolve-Path`,
3. missing explicit paths or missing commands now fail fast instead of being passed through as opaque strings.

`docs/OPERATOR-BOOTSTRAP-RUNBOOK.md` now states that PowerShell accepts either an explicit path or a command already present on `PATH`, and that the shared helper materializes or rejects that value truthfully.

## Validation Notes

Focused validation stayed bounded to `tools/shell/common.ps1`, the operator bootstrap runbook note, the Packet 464 ledger text in `PROJECT_STATUS.md`, and this handoff.

Equivalent execution surfaces used for proof:

1. `pwsh -NoProfile -Command '. tools/shell/common.ps1; $env:APEX_PLATFORM_PYTHON = "python"; Get-ApexRepoPython'`
2. `pwsh -NoProfile -Command '. tools/shell/common.ps1; $env:APEX_PLATFORM_PYTHON = "C:/missing/python.exe"; Get-ApexRepoPython'`
3. `pwsh -NoProfile -Command '. tools/shell/common.ps1; Get-ApexRepoPython'`

Checks confirmed:

1. the bare-command override now resolves to `C:\APEX Platform\apex-power-ops-platform\.venv\Scripts\python.exe` on the current session,
2. the missing explicit-path override now fails fast with `Configured APEX_PLATFORM_PYTHON path not found: C:/missing/python.exe`,
3. the default repo-local branch still resolves to `C:\APEX Platform\apex-power-ops-platform\.venv\Scripts\python.exe`,
4. the touched files open without diagnostics,
5. no formatting issues were introduced in the touched helper, runbook, or handoff surfaces.

All checks passed.

## Boundaries Preserved

This packet does not open:

1. new orchestration services,
2. `ai_tasks` queue ownership,
3. auth or ingress widening,
4. PowerShell runtime-policy changes beyond truthful override handling,
5. broader canary or AI-runner redesign beyond this shared-helper normalization.

## Next Candidate

The next truthful work is either the next adjacent active repo-owned surface whose routing or posture still implies a stale non-canonical dependency, or the next separately packetized scaffold-maintenance or parallel-hardening slice that closes a fresh canary-capture or active-surface defect beyond current example-surface placeholder truth, Bash-path interpreter truth, host-bootstrap preferred-Python reporting truth, Bash override-normalization truth, explicit-path override rejection truth, preferred-python failure-path truth, Bash canary preferred-python alignment truth, and PowerShell override-normalization truth inside the admitted AI backbone.