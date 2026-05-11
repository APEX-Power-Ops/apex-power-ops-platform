# APEX Remote Target Reconciliation Decision

Date: 2026-05-07
Status: Recorded cutover decision baseline
Scope: authoritative decision for how the current `RESA-Power-Project-Management` parent-root lineage maps into the intended canonical standalone repo `jasonlswenson-sys/apex-power-ops`

Closeout interpretation note:

This reconciliation decision is already executed through the completed standalone cutover. It now serves as recorded repo-foundation baseline for how the canonical repo target was selected, not as a live unresolved cutover decision.

Current routing:

1. use `PROJECT_STATUS.md` for the latest completed residue slice and current sequencing,
2. use `docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md` for governing repo-foundation decisions,
3. use `docs/architecture/OLARES-PUBLICATION-BOUNDARY-RETIREMENT-DEPENDENCY-INVENTORY-2026-05-06.md` for the remaining post-cutover closeout queue,
4. use this decision note when the recorded remote-target mapping or cutover lineage relationship needs to be audited as historical provenance.

## Decision

`jasonlswenson-sys/apex-power-ops` is the intended canonical repo target for the standalone `apex-power-ops-platform/` boundary.

`jasonlswenson-sys/RESA-Power-Project-Management` is treated as the current live lineage source and transitional parent-root publication boundary, not as the long-term canonical remote for Apex Ops.

## Why This Decision Controls

Observed live state on 2026-05-07:

1. `C:/APEX Platform` still points at `https://github.com/jasonlswenson-sys/RESA-Power-Project-Management.git`,
2. `/home/olares/code/apex` points at the same remote and same `clean-main` HEAD SHA,
3. the workspace-attached canonical repository context for this session is `jasonlswenson-sys/apex-power-ops`,
4. the repo-structure program has already been steering toward `apex-power-ops-platform/` as the standalone canonical git root.

Without an explicit mapping decision, the cutover packet would be blocked on ambiguity about which GitHub repository should own the new canonical boundary.

## Recorded Operational Consequence

The cutover event did not repoint the current dirty parent-root git boundary in place.

Instead, the standalone boundary around `apex-power-ops-platform/` was created deliberately against `jasonlswenson-sys/apex-power-ops`, while the current `RESA-Power-Project-Management` remote remained the governed lineage source preserved in cutover evidence.

Because `jasonlswenson-sys/apex-power-ops` `clean-main` initially resolved to the same parent-root-shaped commit tree as `C:/APEX Platform`, this decision also implied a history re-root step. The standalone repo therefore had to be attached to a subtree-rooted history for `apex-power-ops-platform/`, not directly to the current parent-root-shaped `clean-main` tree.

## Historical Required Handling During Cutover

When the cutover executed, it needed to:

1. record the current `RESA-Power-Project-Management` remote as the pre-cutover lineage source,
2. materialize subtree-rooted history for `apex-power-ops-platform/` from the current parent-root lineage using a governed split or equivalent re-root method,
3. initialize or attach the standalone repo boundary for `apex-power-ops-platform/` against that subtree-rooted history,
4. point the standalone canonical `origin` at `jasonlswenson-sys/apex-power-ops`,
5. preserve governed evidence showing how the new boundary relates back to the old RESA parent-root boundary,
6. avoid silent in-place mutation of the dirty parent-root remote contract.

## Explicit Non-Decision

This document does not authorize force-pushing, rewriting, or deleting the current RESA parent-root repository.

It only resolves which repo target the new canonical standalone boundary should use.

## Relationship To Other Cutover Surfaces

1. pre-cutover evidence of the mismatch is recorded in `docs/architecture/APEX-GIT-BOUNDARY-CUTOVER-PREFLIGHT-EVIDENCE-2026-05-07.md`,
2. the execution event remains governed by `docs/architecture/APEX-GIT-BOUNDARY-CUTOVER-EXECUTION-PACKET-2026-05-07.md`,
3. the post-cutover workflow and ignore retirement steps remain governed by `docs/architecture/APEX-PARENT-ROOT-WORKFLOW-AND-IGNORE-RETIREMENT-PACKET-2026-05-07.md`.