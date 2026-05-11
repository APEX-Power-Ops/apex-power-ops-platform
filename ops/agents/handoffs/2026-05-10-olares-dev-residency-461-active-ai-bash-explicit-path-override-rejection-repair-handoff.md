# Olares Dev Residency 461 - Active AI Bash Explicit Path Override Rejection Repair Handoff

Date: 2026-05-10
Status: Complete
Packet: `2026-05-10-olares-dev-residency-461`

## Purpose

Close the next adjacent bounded AI Bash interpreter defect by making explicit path-style `APEX_PLATFORM_PYTHON` overrides fail fast when the configured interpreter path does not exist.

## Execution Result

Packet 461 is complete.

`tools/shell/common.sh` now rejects explicit path-style `APEX_PLATFORM_PYTHON` overrides that do not point at a real interpreter file. Instead of passing a nonexistent path downstream as a successful selection, the shared helper now returns a truthful failure immediately.

That keeps wrapper execution and host-bootstrap reporting from inheriting bogus path-style interpreter selections that could only fail later during actual command execution.

`docs/architecture/OLARES-AI-WORKFLOW-FIRST-SLICE-RUNBOOK-2026-05-06.md` now states that explicit path-style overrides must point to a real interpreter.

## Validation Notes

Focused validation stayed bounded to `tools/shell/common.sh`, the active AI workflow runbook note, the Packet 461 ledger text in `PROJECT_STATUS.md`, and this handoff.

Equivalent execution surfaces used for proof:

1. `bash -lc 'export APEX_PLATFORM_PYTHON=python3; source tools/shell/common.sh; get_apex_preferred_python'`
2. `bash -lc 'export APEX_PLATFORM_PYTHON=python3; bash tools/ai/run-olares-host-bootstrap-status.sh'`
3. `bash -lc 'export APEX_PLATFORM_PYTHON=/tmp/missing-apex-python; source tools/shell/common.sh; get_apex_repo_python'`

Checks confirmed:

1. `APEX_PLATFORM_PYTHON=python3` still resolves to `/usr/bin/python3` on the current Linux-style Bash shell,
2. the host-bootstrap artifact still reports that same preferred Python path and version under the bare-command override,
3. `APEX_PLATFORM_PYTHON=/tmp/missing-apex-python` now fails fast with a truthful path-not-found message instead of returning success,
4. the touched files open without diagnostics,
5. no formatting issues were introduced in the touched helper, runbook, or handoff surfaces.

All checks passed.

## Boundaries Preserved

This packet does not open:

1. new orchestration services,
2. `ai_tasks` queue ownership,
3. auth or ingress widening,
4. broader Python policy changes beyond truthful explicit-path override handling,
5. runtime redesign beyond this shared helper rejection repair.

## Next Candidate

The next truthful work is either the next adjacent active repo-owned surface whose routing or posture still implies a stale non-canonical dependency, or the next separately packetized scaffold-maintenance or parallel-hardening slice that closes a fresh canary-capture or active-surface defect beyond current example-surface placeholder truth, Bash-path interpreter truth, host-bootstrap preferred-Python reporting truth, Bash override-normalization truth, and explicit-path override rejection truth inside the admitted AI backbone.