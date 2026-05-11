# APEX Git-Boundary Cutover Execution Packet

Date: 2026-05-07
Status: Recorded cutover execution baseline with closeout state
Scope: controlled execution packet for converting `apex-power-ops-platform/` into the canonical standalone git root while preserving lineage, maintaining GitHub as canonical, and restoring Olares parity against the new boundary

Closeout interpretation note:

This cutover event is already complete. This packet now preserves the executed boundary-mutation method and recorded evidence as post-cutover baseline provenance, not as a live execution packet for a future repo-boundary event.

Current routing:

1. use `PROJECT_STATUS.md` for the latest completed residue slice and current sequencing,
2. use `docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md` for governing repo-foundation decisions,
3. use `docs/architecture/OLARES-PUBLICATION-BOUNDARY-RETIREMENT-DEPENDENCY-INVENTORY-2026-05-06.md` for the remaining post-cutover closeout queue,
4. use this packet when the executed cutover method, captured boundary evidence, or rollback logic needs to be audited as historical provenance.

## Purpose

This packet preserves the executed repo-boundary cutover method as a recorded operator event.

It exists to answer four concrete questions before anyone mutates the git boundary:

1. what exact prerequisites must be true,
2. what exact evidence must be captured before and after the move,
3. what command sequence performs the cutover without silently absorbing parent-root residue,
4. what rollback path restores the old boundary if validation fails.

## Execution Result

This cutover event is now materially complete.

Recorded result:

1. `apex-power-ops-platform/` is now the standalone git root on both workstation and Olares implementation surfaces,
2. canonical `clean-main` in `jasonlswenson-sys/apex-power-ops` now points at subtree-root commit `dd781695006f159f204ab20eaa20adf5e296772c`,
3. backup branch `clean-main-parent-root-pre-cutover-2026-05-07` preserves the pre-cutover parent-root-shaped head `3a5b3bb99bd581bed67cd89e739cf41c19c193d1`,
4. the workstation repo and the Olares implementation repo both now track canonical `clean-main`,
5. the observe-only clone at `/home/olares/src/apex-power-ops-platform` remains preserved and non-canonical.

## Governing Constraints

1. GitHub remains canonical throughout the event.
2. Olares remains the durable development anchor.
3. `C:/APEX Platform` is now workstation-umbrella residue rather than the active publication boundary for this repo.
4. The cutover must not flatten workstation-local, archive, secret, cache, or binary-heavy parent-root material into the standalone repo.
5. The old observe-only clone at `/home/olares/src/apex-power-ops-platform` remains non-canonical and must not be repurposed as the cutover target.

## Historical Required Access Before Execution

Before the cutover event executed, the operator performing it had to have:

1. local write access to `C:/APEX Platform` and `C:/APEX Platform/apex-power-ops-platform`,
2. GitHub push rights for `jasonlswenson-sys/apex-power-ops`,
3. Olares shell access for `/home/olares/code/apex` and the ability to create or reattach the new repo boundary there,
4. enough authority to preserve or archive the old parent-root `.git/` lineage rather than deleting it ad hoc,
5. the remote-target reconciliation decision defined in `docs/architecture/APEX-REMOTE-TARGET-RECONCILIATION-DECISION-2026-05-07.md`.

## Historical Entry Criteria

Before the cutover event executed, all of the following had to be true:

1. `docs/architecture/APEX-CANONICAL-REPO-CUTOVER-CHECKLIST-2026-05-07.md` is current and the unresolved blockers are explicit.
2. `docs/architecture/APEX-PARENT-ROOT-CLASSIFICATION-MATRIX-2026-05-07.md` still reflects the true disposition of all parent-root top-level lanes.
3. The repo-owned workflow set under `apex-power-ops-platform/.github/workflows/` is the intended canonical workflow set.
4. The remaining parent-root task debt is limited to the historical draft-packet helper tail plus still-live publication-boundary residue.
5. The repo-owned authority chain is sufficient for daily operator work without requiring new parent-root-only guidance.
6. The remote-target mismatch captured in `docs/architecture/APEX-GIT-BOUNDARY-CUTOVER-PREFLIGHT-EVIDENCE-2026-05-07.md` is resolved by the decision in `docs/architecture/APEX-REMOTE-TARGET-RECONCILIATION-DECISION-2026-05-07.md` before any boundary mutation.
7. The actual cutover plan accounts for the fact that the current target repo `clean-main` still reflects parent-root topology and therefore requires subtree-rooted history rather than a naive direct attach.

## Historical Inputs Captured Before Mutation

The closing packet was required to record all of the following before changing the git boundary:

1. parent-root `git status --short` from `C:/APEX Platform`,
2. bounded subtree `git status --short -- apex-power-ops-platform/` from `C:/APEX Platform`,
3. parent-root `git remote -v`,
4. parent-root `git rev-parse --show-toplevel`,
5. current `clean-main` HEAD SHA,
6. Olares host status for `/home/olares/code/apex`,
7. Olares host path proof for `/home/olares/code/apex/apex-power-ops-platform`,
8. observe-only clone proof for `/home/olares/src/apex-power-ops-platform`,
9. explicit record of the pre-cutover remote-target mismatch if the live boundary still points at `RESA-Power-Project-Management`.
10. explicit record that the standalone canonical target is `jasonlswenson-sys/apex-power-ops` while the current RESA remote is preserved as lineage source.

## Historical Pre-Cutover Evidence Commands

Windows parent-root evidence capture:

```powershell
Set-Location 'C:/APEX Platform'
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git rev-parse HEAD
git status --short
git status --short -- apex-power-ops-platform/
git diff --stat -- apex-power-ops-platform/
```

Olares host evidence capture:

```bash
ssh olares-mesh 'cd /home/olares/code/apex && pwd && git rev-parse --show-toplevel && git branch --show-current && git rev-parse HEAD && git status --short'
ssh olares-mesh 'test -d /home/olares/code/apex/apex-power-ops-platform && echo host-platform-surface-present'
ssh olares-mesh 'test -d /home/olares/src/apex-power-ops-platform && echo observe-only-clone-present'
```

Current captured preflight evidence is recorded in `docs/architecture/APEX-GIT-BOUNDARY-CUTOVER-PREFLIGHT-EVIDENCE-2026-05-07.md`.

The target-repo mapping decision is recorded in `docs/architecture/APEX-REMOTE-TARGET-RECONCILIATION-DECISION-2026-05-07.md`.

## Cutover Objective

At the end of the event:

1. `C:/APEX Platform/apex-power-ops-platform` is its own git root,
2. `origin` for that standalone repo points at `jasonlswenson-sys/apex-power-ops`,
3. normal `status`, `diff`, `branch`, and `push` flow start from the repo root,
4. `/home/olares/code/apex/apex-power-ops-platform` is reattached to the standalone boundary,
5. `C:/APEX Platform` is demoted to workstation umbrella status rather than publication boundary status.

The retained phase sequence below is now historical execution provenance for the completed event, not a current live operator checklist.

## Historical Controlled Execution Sequence

### Phase 1: Freeze Publication Inputs

1. Stop new parent-root publication work while the event is active.
2. Ensure all in-flight changes intended for cutover are already present in `apex-power-ops-platform/`.
3. Confirm no additional parent-root-only files need promotion before the boundary changes.

### Phase 2: Snapshot Lineage And Residue

1. Capture the evidence listed above.
2. Archive the parent-root `.git/` lineage in a governed way before any destructive move.
3. Record the exact parent-root lanes that must remain outside the standalone repo after cutover.

### Phase 3: Materialize The Standalone Repo Boundary

Do not directly attach `C:/APEX Platform/apex-power-ops-platform` to the current `jasonlswenson-sys/apex-power-ops` `clean-main` branch as if it were already subtree-rooted.

Current preflight evidence shows that `apex-power-ops` `clean-main` still points at the same parent-root-shaped commit tree as `C:/APEX Platform`.

That means the cutover event must first produce subtree-rooted history for prefix `apex-power-ops-platform/` from the current lineage boundary.

Minimum required shape of this phase:

1. generate subtree-rooted history for `apex-power-ops-platform/` using a governed split or equivalent re-root operation,
2. publish or stage that subtree-rooted history to the canonical target in a controlled way,
3. only then initialize or attach the standalone repo boundary against the subtree-rooted branch.

Current known candidate from preflight work on 2026-05-07:

1. subtree split command: `git -C "C:/APEX Platform" subtree split --prefix=apex-power-ops-platform clean-main`
2. resulting candidate commit: `dd781695006f159f204ab20eaa20adf5e296772c`
3. published staging branch on `jasonlswenson-sys/apex-power-ops`: `clean-main-cutover-subtree-candidate-2026-05-07`

Illustrative local preparation command:

```powershell
Set-Location 'C:/APEX Platform'
git subtree split --prefix=apex-power-ops-platform clean-main
```

The initial publication step is now proven:

```powershell
git -C "C:/APEX Platform" push https://github.com/jasonlswenson-sys/apex-power-ops.git dd781695006f159f204ab20eaa20adf5e296772c:refs/heads/clean-main-cutover-subtree-candidate-2026-05-07
```

The standalone repo-boundary attach step is now proven on both active implementation surfaces and should be recorded in the closing packet. If the canonical remote must use HTTPS instead of SSH, record that deviation explicitly as well.

### Phase 4: Reconcile Canonical Tracking

From the standalone repo root after subtree-rooted history exists:

```powershell
Set-Location 'C:/APEX Platform/apex-power-ops-platform'
git branch --set-upstream-to=origin/clean-main clean-main
git status --short
git rev-parse --show-toplevel
git remote -v
```

Confirm the standalone root, branch, and remote all point at the intended canonical boundary before any push or pull.

Current local proof on 2026-05-07:

1. repo root resolves to `C:/APEX Platform/apex-power-ops-platform`,
2. local standalone branch now tracks canonical `clean-main`,
3. `origin` points at `https://github.com/jasonlswenson-sys/apex-power-ops.git`,
4. HEAD now resolves to `dd781695006f159f204ab20eaa20adf5e296772c`, which is the promoted canonical subtree-root commit.

### Phase 5: Reattach Olares Host Against The New Boundary

The host reattachment method must preserve `/home/olares/code/apex` as the authoritative host mirror while making `/home/olares/code/apex/apex-power-ops-platform` the real git boundary.

Minimum required proof after host reattachment:

```bash
ssh olares-mesh 'cd /home/olares/code/apex/apex-power-ops-platform && git rev-parse --show-toplevel && git remote -v && git branch --show-current && git status --short'
```

Current host proof on 2026-05-07:

1. `/home/olares/code/apex/apex-power-ops-platform` was confirmed present from the live Olares Control Hub terminal,
2. `/home/olares/src/apex-power-ops-platform` remains present as the observe-only clone and, under user `olares`, resolves to branch `clean-main` with `origin` at `https://github.com/jasonlswenson-sys/apex-power-ops.git`,
3. `/home/olares/code/apex/apex-power-ops-platform` now resolves to repo root `/home/olares/code/apex/apex-power-ops-platform`,
4. its current branch is canonical `clean-main`,
5. its `origin` points at `https://github.com/jasonlswenson-sys/apex-power-ops.git`,
6. current observed host working-tree delta is `?? .tmp/`,
7. HEAD now resolves to `dd781695006f159f204ab20eaa20adf5e296772c`,
8. that means host reattachment and canonical-branch promotion are materially complete.

### Phase 6: Validate Default Operator Workflow

Run all validation from the standalone repo root or its Olares mirror, not from `C:/APEX Platform`.

Minimum validation set:

1. repo-root `git rev-parse --show-toplevel`,
2. repo-root `git status --short`,
3. repo-root diff check on the touched slice,
4. repo-root task and runbook spot-check proving operator guidance no longer requires the parent-root git boundary,
5. Olares host parity proof against the standalone repo root.

## Historical No-Go Conditions During Execution

During the live event, execution had to stop immediately if any of the following occurred:

1. the standalone repo root resolves to any directory other than `C:/APEX Platform/apex-power-ops-platform`,
2. the remote points anywhere other than the intended GitHub canonical target,
3. cutover steps would require importing parent-root-only archive, local, or binary-heavy lanes into the standalone repo,
4. Olares reattachment would force the old observe-only clone into active service,
5. operator validation still depends on parent-root `.github/workflows/` or `.gitignore` as hidden prerequisites,
6. the current live remote lineage still points at `RESA-Power-Project-Management` and the transition into `jasonlswenson-sys/apex-power-ops` is not being executed according to `docs/architecture/APEX-REMOTE-TARGET-RECONCILIATION-DECISION-2026-05-07.md`.
7. the operator attempts to attach the subtree working directory directly to a branch whose commit tree still expects the full parent-root layout.

## Historical Rollback Strategy

If validation had failed after boundary creation:

1. stop all publication from the new standalone boundary,
2. preserve the failed standalone `.git/` state for forensic review,
3. restore the old parent-root boundary as the active publication surface,
4. record the exact failed validation point,
5. do not retry until the checklist and dependency inventory are updated to address the failure mode.

Rollback is complete only when:

1. `C:/APEX Platform` is again the active `git rev-parse --show-toplevel` for publication work,
2. the standalone repo state is preserved but inactive,
3. Olares host parity is restored to the pre-cutover posture,
4. the closing packet records why the event was aborted.

## Closing Evidence Packet Requirements

The cutover closeout must capture:

1. pre-cutover and post-cutover top-level git roots,
2. pre-cutover and post-cutover remotes,
3. pre-cutover and post-cutover branch and HEAD SHAs,
4. Olares host pre/post proof,
5. observe-only clone preserved proof,
6. list of parent-root surfaces still intentionally outside the standalone repo,
7. validation command output proving the new repo root is operational,
8. confirmation that parent-root `.github/workflows/` and `.gitignore` are no longer hidden execution dependencies.

## Immediate Follow-On Work After Successful Cutover

1. continue residual lane-by-lane doc hygiene so no active surface revives parent-root publication assumptions,
2. relabel or retire the historical draft-packet helper tail in `.vscode/tasks.json` when that provenance lane is next touched,
3. keep Olares host parity and observe-only clone checks in the focused validation cadence,
4. demote any remaining parent-root compatibility shims that were needed only before the boundary moved.