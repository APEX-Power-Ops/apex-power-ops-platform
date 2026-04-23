# Parent-Root Residual Archive Formula Pair Publication Handoff
## Date: 2026-04-22
## Updated by: GitHub Copilot (GPT-5.4)
## Scope: Historical record for the final residual archive-only formula pair under `C:/APEX Platform/apex-power-ops-platform`

## 1. Summary

The live `apex-unification` packet family is now fully advanced through `apex-unification-001i`.

The only remaining untracked residue under `apex-power-ops-platform` was a two-file archived Dataverse formula pair inside the legacy `v1.5.0.3` export. This tranche was the truthful next bounded follow-on because it was the last untracked content in the platform subtree and it staged cleanly as an explicit pair when `git` was invoked with `core.longpaths=true`.

Publication outcome:

1. committed on parent-root `clean-main` as `b5b231c`
2. pushed to `origin/clean-main` on 2026-04-22
3. closed as the published residual archive formula pair tranche

## 2. Why This Tranche Is Next

Measured from the parent git root at `C:/APEX Platform` on 2026-04-22 after the post-`001i` reevaluation refresh:

1. remaining untracked top-level distribution under `apex-power-ops-platform` is `apps` 0, `archive` 2, `knowledge` 0, `ops` 0
2. the remaining `ops/agents` backlog under `apex-power-ops-platform` is `handoffs` 0 and `packets` 0
3. the only residual untracked paths are these two archived formula files:
   - `archive/legacy-repos/apex-platform/root-archive/_archive/Dec2025_Dataverse/Solution_Exports/Archive/v1.5.0.3/Entities/cr950_projectfinancialsummary/Formulas/cr950_projectfinancialsummary-cr950_apparatusrevenuecount.xaml`
   - `archive/legacy-repos/apex-platform/root-archive/_archive/Dec2025_Dataverse/Solution_Exports/Archive/v1.5.0.3/Entities/cr950_projectfinancialsummary/Formulas/cr950_projectfinancialsummary-cr950_totalrevenuerecognized.xaml`
4. plain `git add` fails on this pair in the Windows worktree because the paths cross the filename-length boundary
5. `git -c core.longpaths=true add -n --` stages the pair cleanly, proving the residual tranche is publishable without widening into the rest of `archive/`

## 3. Tranche Intent

Use this tranche to introduce exactly the last two residual archive-only formula assets under the live platform subtree:

1. `cr950_projectfinancialsummary-cr950_apparatusrevenuecount.xaml`
2. `cr950_projectfinancialsummary-cr950_totalrevenuerecognized.xaml`

## 4. Exact Tranche Contents

From the parent git root at `C:/APEX Platform`, the bounded paths are:

1. `apex-power-ops-platform/archive/legacy-repos/apex-platform/root-archive/_archive/Dec2025_Dataverse/Solution_Exports/Archive/v1.5.0.3/Entities/cr950_projectfinancialsummary/Formulas/cr950_projectfinancialsummary-cr950_apparatusrevenuecount.xaml`
2. `apex-power-ops-platform/archive/legacy-repos/apex-platform/root-archive/_archive/Dec2025_Dataverse/Solution_Exports/Archive/v1.5.0.3/Entities/cr950_projectfinancialsummary/Formulas/cr950_projectfinancialsummary-cr950_totalrevenuerecognized.xaml`

Published contents: 2 files.

## 5. Why This Tranche Is Bounded Correctly

This tranche is intentionally narrow:

1. it introduces only the final residual archived Dataverse formula pair under the live platform subtree
2. it does not widen into the rest of the archive tree or reopen active runtime, docs, knowledge, or operator packet lanes
3. it closes the last measured untracked residue under `apex-power-ops-platform`
4. it uses explicit path staging and an explicit long-path override rather than broad subtree staging

## 6. Historical Execution Path

Preferred task path from `C:/APEX Platform/apex-power-ops-platform`:

1. run `Preview parent-root residual archive formula pair`
2. run `Stage parent-root residual archive formula pair` only when the preview is correct
3. run `Parent-root residual archive formula pair staged diff`

Direct parent-root path if tasks are not used:

```powershell
Set-Location 'C:/APEX Platform'
git -c core.longpaths=true add -n -- apex-power-ops-platform/archive/legacy-repos/apex-platform/root-archive/_archive/Dec2025_Dataverse/Solution_Exports/Archive/v1.5.0.3/Entities/cr950_projectfinancialsummary/Formulas/cr950_projectfinancialsummary-cr950_apparatusrevenuecount.xaml apex-power-ops-platform/archive/legacy-repos/apex-platform/root-archive/_archive/Dec2025_Dataverse/Solution_Exports/Archive/v1.5.0.3/Entities/cr950_projectfinancialsummary/Formulas/cr950_projectfinancialsummary-cr950_totalrevenuerecognized.xaml
git -c core.longpaths=true add -- apex-power-ops-platform/archive/legacy-repos/apex-platform/root-archive/_archive/Dec2025_Dataverse/Solution_Exports/Archive/v1.5.0.3/Entities/cr950_projectfinancialsummary/Formulas/cr950_projectfinancialsummary-cr950_apparatusrevenuecount.xaml apex-power-ops-platform/archive/legacy-repos/apex-platform/root-archive/_archive/Dec2025_Dataverse/Solution_Exports/Archive/v1.5.0.3/Entities/cr950_projectfinancialsummary/Formulas/cr950_projectfinancialsummary-cr950_totalrevenuerecognized.xaml
git diff --cached -- apex-power-ops-platform/archive/legacy-repos/apex-platform/root-archive/_archive/Dec2025_Dataverse/Solution_Exports/Archive/v1.5.0.3/Entities/cr950_projectfinancialsummary/Formulas/cr950_projectfinancialsummary-cr950_apparatusrevenuecount.xaml apex-power-ops-platform/archive/legacy-repos/apex-platform/root-archive/_archive/Dec2025_Dataverse/Solution_Exports/Archive/v1.5.0.3/Entities/cr950_projectfinancialsummary/Formulas/cr950_projectfinancialsummary-cr950_totalrevenuerecognized.xaml
```

## 7. Validation Expectation

Before commit, the smallest relevant checks are:

1. `git -c core.longpaths=true add -n` preview of the exact pair
2. staged diff review for those two archive formula files only

This tranche is archival formula XML, so bounded diff discipline matters more than executable validation.

## 8. Do Not Do

1. do not widen this tranche into the rest of `archive/`
2. do not restage the pair without the long-path override in this Windows worktree
3. do not reopen active packet-family selection while this last measured subtree residue remains unpublished

## 9. Follow-On After This Tranche

If this tranche lands cleanly, refresh the queue to a zero-frontier platform-subtree checkpoint because no untracked paths remain under `apex-power-ops-platform`.