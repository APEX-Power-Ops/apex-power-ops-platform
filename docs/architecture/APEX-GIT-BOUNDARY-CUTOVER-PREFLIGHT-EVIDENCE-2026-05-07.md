# APEX Git-Boundary Cutover Preflight Evidence

Date: 2026-05-07
Status: Recorded preflight evidence with post-cutover closeout addendum
Scope: captured pre-cutover evidence plus the final canonical-promotion and host-parity proof for the standalone git-boundary event

## Purpose

This note records the pre-cutover evidence that was captured directly from the live parent-root and Olares parent-root boundaries, plus the final post-cutover state that closed the event.

It exists to keep the original blocker and the final resolution grounded in observed state rather than assumption.

## Local Parent-Root Evidence

Captured from `C:/APEX Platform`:

1. `git rev-parse --show-toplevel` -> `C:/APEX Platform`
2. `git branch --show-current` -> `clean-main`
3. `git rev-parse HEAD` -> `3a5b3bb99bd581bed67cd89e739cf41c19c193d1`
4. `git remote -v` -> `origin` and `public` both point at `https://github.com/jasonlswenson-sys/RESA-Power-Project-Management.git`

## Olares Parent-Root Evidence

Captured from `/home/olares/code/apex`:

1. `git rev-parse --show-toplevel` -> `/home/olares/code/apex`
2. `git rev-parse HEAD` -> `3a5b3bb99bd581bed67cd89e739cf41c19c193d1`
3. `git remote -v` -> `origin` points at `https://github.com/jasonlswenson-sys/RESA-Power-Project-Management.git`

## Verified Preflight Finding

The current live parent-root boundary is not yet aligned to the attached canonical repo target.

Observed mismatch:

1. the intended canonical repo target for this workspace session is `jasonlswenson-sys/apex-power-ops`,
2. the live local parent-root boundary still points at `RESA-Power-Project-Management`,
3. the live Olares parent-root mirror points at the same `RESA-Power-Project-Management` remote,
4. both boundaries share the same `clean-main` HEAD SHA, which means the mismatch is consistent rather than a one-sided workstation anomaly.

Additional topology finding:

1. `git ls-remote --heads https://github.com/jasonlswenson-sys/apex-power-ops.git` shows `refs/heads/clean-main` at the same SHA `3a5b3bb99bd581bed67cd89e739cf41c19c193d1`,
2. `git ls-tree --name-only HEAD` from `C:/APEX Platform` shows parent-root entries such as `.claude`, `Infrastructure`, `Platform-Authority`, `apex-power-ops-platform`, `apps`, `packages`, and `spec`,
3. that means the intended target repo is currently reachable but still reflects the parent-root topology rather than a repo root re-homed to `apex-power-ops-platform/`.

Generated subtree-root candidate:

1. `git -C "C:/APEX Platform" subtree split --prefix=apex-power-ops-platform clean-main` completed successfully,
2. the resulting subtree-rooted history candidate is commit `dd781695006f159f204ab20eaa20adf5e296772c`,
3. that candidate proves a non-destructive re-root path exists for the `apex-power-ops-platform/` history even though the current target `clean-main` branch is still parent-root-shaped,
4. the candidate has now been published non-destructively to `jasonlswenson-sys/apex-power-ops` as branch `clean-main-cutover-subtree-candidate-2026-05-07`.

Materialized local standalone boundary:

1. `C:/APEX Platform/apex-power-ops-platform/.git` now exists,
2. the local standalone boundary was first attached to branch `clean-main-cutover-subtree-candidate-2026-05-07`,
3. that staging attach proved the repo root at `C:/APEX Platform/apex-power-ops-platform`,
4. the workspace later advanced to canonical branch `clean-main` at the same subtree-root commit `dd781695006f159f204ab20eaa20adf5e296772c`.

Captured Olares host boundary evidence:

1. host path proof from the live Olares Control Hub terminal confirmed `/home/olares/code/apex/apex-power-ops-platform` is present,
2. the same host proof confirmed `/home/olares/src/apex-power-ops-platform` remains present as the observe-only clone,
3. `/home/olares/code/apex/apex-power-ops-platform/.git` was absent before host reattachment,
4. `/home/olares/src/apex-power-ops-platform/.git` was already present and, when checked as user `olares`, resolves to repo root `/home/olares/src/apex-power-ops-platform` on branch `clean-main` with `origin` at `https://github.com/jasonlswenson-sys/apex-power-ops.git`,
5. `/home/olares/code/apex/apex-power-ops-platform` has now been initialized non-destructively as its own standalone git boundary,
6. that host implementation boundary now resolves to repo root `/home/olares/code/apex/apex-power-ops-platform`,
7. its first attached branch was `clean-main-cutover-subtree-candidate-2026-05-07`,
8. its `origin` points at `https://github.com/jasonlswenson-sys/apex-power-ops.git`,
9. the first observed host working-tree delta after attachment was `?? .tmp/`,
10. that host implementation surface now tracks canonical `clean-main` at `dd781695006f159f204ab20eaa20adf5e296772c` without repurposing the observe-only clone.

## Post-Cutover Closeout Addendum

Canonical promotion and host alignment are now complete.

Observed closing state:

1. `git ls-remote --heads https://github.com/jasonlswenson-sys/apex-power-ops.git clean-main clean-main-cutover-subtree-candidate-2026-05-07 clean-main-parent-root-pre-cutover-2026-05-07` now shows `clean-main` and the staging branch both at `dd781695006f159f204ab20eaa20adf5e296772c`,
2. backup branch `clean-main-parent-root-pre-cutover-2026-05-07` preserves the old parent-root-shaped head at `3a5b3bb99bd581bed67cd89e739cf41c19c193d1`,
3. the workstation standalone repo at `C:/APEX Platform/apex-power-ops-platform` now resolves to branch `clean-main`, `origin` at `https://github.com/jasonlswenson-sys/apex-power-ops.git`, and HEAD `dd781695006f159f204ab20eaa20adf5e296772c`,
4. the Olares implementation repo at `/home/olares/code/apex/apex-power-ops-platform` now resolves to branch `clean-main`, HEAD `dd781695006f159f204ab20eaa20adf5e296772c`, and current observed host delta `?? .tmp/`,
5. the observe-only clone at `/home/olares/src/apex-power-ops-platform` remains preserved on `clean-main` at `2836a2622309b4e146ca24f23b5bf87312c0c857` and was not repurposed.

## Historical No-Go Conclusion

Standalone git-boundary cutover must not proceed until both remote-target reconciliation and topology reconciliation are explicit.

Specifically, the cutover event still lacks the authoritative answer to this question:

How should the current `RESA-Power-Project-Management` lineage boundary map into the intended standalone canonical repo `jasonlswenson-sys/apex-power-ops`, and how should the parent-root-shaped `clean-main` history be re-rooted so `apex-power-ops-platform/` becomes the actual repo root?

Until that mapping is explicit, the cutover event risks preserving the wrong remote lineage, silently switching canonical history targets without a governed record, or attaching a subtree-root working directory to a branch whose commit tree still expects the full parent-root layout.

That blocker is now closed: canonical branch promotion is complete and the parent-root publication boundary is demoted to historical or umbrella residue.

## Remaining Closeout Note

The earlier non-interactive SSH gap was bypassed by the authenticated Olares browser surfaces and later confirmed with direct host-shell parity checks. The remaining work is no longer git-topology proof; it is residual documentation hygiene and ongoing focused validation from the canonical repo root.