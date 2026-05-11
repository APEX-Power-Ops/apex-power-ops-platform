# Olares Dev Residency 458 - Active AI Bash Preferred Python Resolution Repair Handoff

Date: 2026-05-10
Status: Complete
Packet: `2026-05-10-olares-dev-residency-458`

## Purpose

Close the next adjacent bounded AI Bash operator defect by repairing Python interpreter resolution in the Bash wrappers so they prefer the shared repo-local resolver without selecting unusable Windows `python.exe` paths on Linux-style shells.

## Execution Result

Packet 458 is complete.

`tools/shell/common.sh` now exposes a preferred-Python helper that:

1. uses the repo-local Python when it is usable in the current shell,
2. falls back to native `python3` or `python` when no usable repo-local interpreter exists,
3. skips Windows `python.exe` paths on Linux-style shells where those interpreters cannot execute the wrappers' POSIX script paths.

`tools/ai/run-minimal-mcp-trio.sh`, `tools/ai/run-olares-hold-boundary-check.sh`, and `tools/ai/run-olares-host-bootstrap-status.sh` now use that helper instead of bare `python` or `python3` calls.

## Validation Notes

Focused validation stayed bounded to the shared shell helper, the three Bash wrapper surfaces above, the AI workflow runbook note, the Packet 458 ledger text in `PROJECT_STATUS.md`, and this handoff.

Equivalent execution surfaces used for proof:

1. `bash -lc 'source tools/shell/common.sh; get_apex_preferred_python'`
2. `bash tools/ai/run-minimal-mcp-trio.sh up`
3. `bash tools/ai/run-minimal-mcp-trio.sh status`
4. `bash tools/ai/run-minimal-mcp-trio.sh verify`
5. `bash tools/ai/run-olares-hold-boundary-check.sh`
6. `bash tools/ai/run-olares-host-bootstrap-status.sh`
7. `bash tools/ai/run-minimal-mcp-trio.sh down`

Checks confirmed:

1. the preferred Python resolves to native `/usr/bin/python3` on the current Linux-style Bash shell,
2. the Bash minimal-trio wrapper still returns `PASS` on `verify`,
3. the Bash hold-boundary wrapper still returns truthful `UNAVAILABLE` and emits the repo-visible deferred-ops artifact,
4. the Bash host-bootstrap wrapper still returns truthful `UNAVAILABLE` and emits the repo-visible host-bootstrap artifact,
5. the touched files open without diagnostics,
6. no formatting issues were introduced in the touched helper, wrappers, runbook, or handoff surfaces.

The first validation attempt surfaced the local defect this packet repaired: Bash had selected `/mnt/c/.../.venv/Scripts/python.exe`, which failed to execute the wrappers' POSIX script paths. The repaired resolver eliminated that failure and the same validation rerun then passed cleanly.

## Boundaries Preserved

This packet does not open:

1. new orchestration services,
2. `ai_tasks` queue ownership,
3. auth or ingress widening,
4. Python interpreter policy beyond truthful Bash-side resolution,
5. broader runtime redesign beyond this shell-resolution repair.

## Next Candidate

The next truthful work is either the next adjacent active repo-owned surface whose routing or posture still implies a stale non-canonical dependency, or the next separately packetized scaffold-maintenance or parallel-hardening slice that closes a fresh canary-capture or active-surface defect beyond current example-surface placeholder truth and Bash-path interpreter truth inside the admitted AI backbone.