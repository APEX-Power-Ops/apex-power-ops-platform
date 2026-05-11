# Olares Dev Residency 463 - Active Canary Bash Preferred Python Alignment Repair Handoff

Date: 2026-05-10
Status: Complete
Packet: `2026-05-10-olares-dev-residency-463`

## Purpose

Close the next adjacent bounded canary Bash defect by aligning `tools/run-canary.sh` with the shared preferred Python resolver contract already repaired across the adjacent Bash operator surfaces.

## Execution Result

Packet 463 is complete.

`tools/run-canary.sh` now resolves its Python interpreter through `get_apex_preferred_python` instead of strict `get_apex_repo_python`.

That keeps the Bash canary entrypoint aligned with the hardened Bash helper contract already used by the AI operator surfaces, so the canary shell no longer fails immediately on POSIX hosts that have a usable native `python3` or `python` but no repo-local `.venv/bin/python`.

`docs/architecture/OLARES-WORKSTATION-BRING-UP-CHECKLIST-2026-04-23.md` now states the current Windows versus POSIX Python precondition truthfully instead of preserving the retired parent-root interpreter path.

## Validation Notes

Focused validation stayed bounded to `tools/run-canary.sh`, the shared shell helper contract, the workstation bring-up checklist note, the Packet 463 ledger text in `PROJECT_STATUS.md`, and this handoff.

Equivalent execution surfaces used for proof:

1. pre-edit defect proof: `bash -lc 'unset APEX_PLATFORM_PYTHON; bash tools/run-canary.sh'`
2. post-edit file check: `tools/run-canary.sh` now calls `get_apex_preferred_python`
3. post-edit helper proof: `bash -lc 'unset APEX_PLATFORM_PYTHON; source tools/shell/common.sh; get_apex_preferred_python'`

Checks confirmed:

1. the pre-edit Bash canary entrypoint failed immediately with `No repo-local Python interpreter found under /mnt/c/APEX Platform/apex-power-ops-platform/.venv.` on the current shell,
2. the post-edit Bash canary entrypoint now points at the preferred resolver instead of the strict repo-local resolver,
3. the preferred resolver returns `/usr/bin/python3` on the current shell, which is the usable interpreter the old canary entrypoint failed to adopt,
4. the touched files open without diagnostics,
5. no formatting issues were introduced in the touched script, checklist, or handoff surfaces.

All checks passed.

## Boundaries Preserved

This packet does not open:

1. new orchestration services,
2. `ai_tasks` queue ownership,
3. auth or ingress widening,
4. broader canary-runner redesign beyond truthful Bash interpreter selection,
5. runtime-policy changes outside the repaired shared-helper contract.

## Next Candidate

The next truthful work is either the next adjacent active repo-owned surface whose routing or posture still implies a stale non-canonical dependency, or the next separately packetized scaffold-maintenance or parallel-hardening slice that closes a fresh canary-capture or active-surface defect beyond current example-surface placeholder truth, Bash-path interpreter truth, host-bootstrap preferred-Python reporting truth, Bash override-normalization truth, explicit-path override rejection truth, preferred-python failure-path truth, and Bash canary preferred-python alignment truth inside the admitted AI backbone.