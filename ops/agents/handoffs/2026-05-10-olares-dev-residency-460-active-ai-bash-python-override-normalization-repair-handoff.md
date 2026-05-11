# Olares Dev Residency 460 - Active AI Bash Python Override Normalization Repair Handoff

Date: 2026-05-10
Status: Complete
Packet: `2026-05-10-olares-dev-residency-460`

## Purpose

Close the next adjacent bounded AI Bash interpreter defect by normalizing `APEX_PLATFORM_PYTHON` overrides in the shared shell helper so successful bare-command overrides resolve truthfully and unusable Windows interpreter overrides fail fast on Linux-style shells.

## Execution Result

Packet 460 is complete.

`tools/shell/common.sh` now treats `APEX_PLATFORM_PYTHON` more truthfully on Bash surfaces:

1. a bare command name such as `python3` resolves to its materialized command path,
2. explicit path-style overrides still pass through as the configured interpreter selection,
3. Windows `python.exe` overrides are rejected on Linux-style shells instead of appearing to resolve successfully.

That keeps wrapper execution and host-bootstrap reporting aligned when operators use `APEX_PLATFORM_PYTHON` to steer Bash-side interpreter selection.

`docs/architecture/OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md` now states that bare-command overrides are materialized to the actual command path and that Linux-style shells reject unusable Windows `.exe` overrides.

## Validation Notes

Focused validation stayed bounded to `tools/shell/common.sh`, the active AI workflow runbook note, the Packet 460 ledger text in `PROJECT_STATUS.md`, and this handoff.

Equivalent execution surfaces used for proof:

1. `bash -lc 'export APEX_PLATFORM_PYTHON=python3; source tools/shell/common.sh; get_apex_preferred_python'`
2. `bash -lc 'export APEX_PLATFORM_PYTHON=python3; bash tools/ai/run-olares-host-bootstrap-status.sh'`
3. `bash -lc 'export APEX_PLATFORM_PYTHON=C:/fake/python.exe; source tools/shell/common.sh; get_apex_repo_python'`

Checks confirmed:

1. `APEX_PLATFORM_PYTHON=python3` now resolves to `/usr/bin/python3` on the current Linux-style Bash shell,
2. the host-bootstrap artifact now reports that same materialized preferred Python path and version under the bare-command override,
3. `APEX_PLATFORM_PYTHON=C:/fake/python.exe` now fails fast with a truthful Linux-shell rejection message instead of returning success,
4. the touched files open without diagnostics,
5. no formatting issues were introduced in the touched helper, runbook, or handoff surfaces.

All checks passed.

## Boundaries Preserved

This packet does not open:

1. new orchestration services,
2. `ai_tasks` queue ownership,
3. auth or ingress widening,
4. broader Python policy changes beyond truthful Bash override handling,
5. runtime redesign beyond this shared helper normalization.

## Next Candidate

The next truthful work is either the next adjacent active repo-owned surface whose routing or posture still implies a stale non-canonical dependency, or the next separately packetized scaffold-maintenance or parallel-hardening slice that closes a fresh canary-capture or active-surface defect beyond current example-surface placeholder truth, Bash-path interpreter truth, host-bootstrap preferred-Python reporting truth, and Bash override-normalization truth inside the admitted AI backbone.