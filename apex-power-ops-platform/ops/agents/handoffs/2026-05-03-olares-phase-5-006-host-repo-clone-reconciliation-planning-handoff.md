# Olares Phase 5 Packet 006 Host Repo-Clone Reconciliation Planning Handoff

Date: 2026-05-03
Status: Complete - read-only planning pass
Packet: `ops/agents/packets/draft/2026-05-03-olares-phase-5-006-host-repo-clone-reconciliation-planning.json`
Scope: host repo-clone reconciliation planning before any Olares-first daily development migration packet

## Authority

This handoff executes Prompt 8 from:

1. `ops/agents/handoffs/2026-05-03-olares-phase-5-next-task-and-prompt-routing-handoff.md`
2. `ops/agents/packets/draft/2026-05-03-olares-phase-5-006-host-repo-clone-reconciliation-planning.json`
3. `ops/agents/handoffs/2026-05-03-olares-phase-5-post-005-reconciliation-handoff.md`
4. `ops/agents/handoffs/2026-05-03-olares-phase-5-005-ssh-host-runtime-inventory-handoff.md`
5. `ops/agents/handoffs/2026-05-03-olares-phase-5-step-3-expansion-decision-surface-handoff.md`
6. `ops/agents/handoffs/2026-04-25-olares-workstation-001-publication-follow-through-scope-handoff.md`
7. `ops/agents/handoffs/2026-04-25-olares-workstation-002-publication-follow-through-blocker-handoff.md`
8. `Infrastructure/Olares_Workspace_Authority_Framework.md`
9. `Infrastructure/Olares_Build_Guide.md`
10. `plan/infrastructure-olares-full-implementation-roadmap-1.md`

This handoff does not reopen generic Olares implementation. It does not approve Olares-first daily development, AI-services expansion, Gitea/code-hosting work, or canonical-hosting transition.

No git pull, git reset, git clean, branch switch, remote rewrite, clone deletion, host runtime mutation, install, ingress change, auth change, service restart, code-hosting cutover, or publication-boundary change was performed.

## Executive Verdict

The host clone should not be refreshed in place and should not become the intended Olares dev path.

Decision:

1. preserve `/home/olares/src/apex-power-ops-platform` as historical runtime evidence and a salvage-reference surface for now
2. replace it later with a new canonical host dev path if Olares-first daily development remains a candidate
3. retire the old 2026-04-25 packet-002 publication lane as an execution packet
4. carry forward the old packet-002 path list only as comparison input for a later host-clone replacement packet

The next packet, if opened, should be a bounded implementation packet to prepare a canonical host repo path without deleting or rewriting the existing host clone.

Readiness result:

1. Olares-first daily development remains not ready
2. AI-services-zone expansion remains not ready
3. Gitea/code-hosting mirror enhancement remains not ready
4. canonical-hosting transition remains no-go

## Evidence Compared

### Host Clone Evidence

Observed during Packet 005 over the restored `olares-mesh` SSH path:

| Surface | Host evidence |
| --- | --- |
| path | `/home/olares/src/apex-power-ops-platform` |
| git top-level | `/home/olares/src/apex-power-ops-platform` |
| branch | `clean-main` |
| commit | `2836a2622309b4e146ca24f23b5bf87312c0c857` |
| latest commit summary | `2836a26 2026-04-24T18:01:21-07:00 Track Olares storage first-run scripts` |
| remote | `https://github.com/jasonlswenson-sys/apex-power-ops.git` |
| cleanliness | dirty |

Packet 005 recorded host modified or untracked surfaces including storage scripts, package files, forms-engine files, `infra/compose.dev.yml`, `infra/olares/charts/`, `infra/private/`, `packages/p6-ingest/`, `services/`, `tests/canary/`, and `tools/`.

Interpretation:

The host clone is real host evidence, but it is not authoritative for daily development. It is older, dirty, path-divergent, and remote-divergent from the current workstation publication boundary.

### Workstation Publication Boundary

Observed locally during this Packet 006 planning pass:

| Surface | Workstation evidence |
| --- | --- |
| git top-level | `C:/APEX Platform` |
| implementation prefix | `apex-power-ops-platform/` |
| branch | `clean-main` |
| commit | `0020fb291595f597b52fe120b8bb2b081d717f90` |
| latest commit summary | `0020fb2 2026-05-03T18:12:57-07:00 docs(olares): author packet 006 clone planning` |
| remotes | `origin` and `public` both point to `https://github.com/jasonlswenson-sys/RESA-Power-Project-Management.git` |

Interpretation:

The controlling publication boundary is still the parent git root at `C:/APEX Platform`. The current canonical GitHub remote is `jasonlswenson-sys/RESA-Power-Project-Management.git`, not the host clone's `jasonlswenson-sys/apex-power-ops.git`.

### Authority Framework Evidence

`Infrastructure/Olares_Workspace_Authority_Framework.md` states:

1. `C:/APEX Platform/apex-power-ops-platform` is the canonical implementation workspace intended for Olares hosting
2. the parent git root at `C:/APEX Platform` remains the publication boundary until deliberate repo cutover
3. intended host source path is `~/code/apex/`
4. source code should live in `~/code/apex/` only
5. Olares transition work should use bounded parent-root pathspecs until cutover

`Infrastructure/Olares_Build_Guide.md` also points the Olares filesystem model at `~/code/apex` for source and `~/apex-data` for mutable state, while preserving GitHub as canonical and treating Gitea as optional mirror-only.

Interpretation:

The current host path `/home/olares/src/apex-power-ops-platform` does not match the authority-defined source path. It should not be blessed as the future path merely because it exists.

## Host Clone Disposition

Decision: preserve as evidence now; replace for future development.

Do not:

1. refresh it in place
2. clean it in place
3. rewrite its remote
4. switch its branch
5. delete it as part of planning
6. treat it as the canonical host dev path

Why not refresh in place:

1. it points at a different GitHub repository than the workstation publication boundary
2. it is rooted at the wrong host path for the current Olares authority model
3. it contains dirty/untracked runtime-era surfaces that may still have evidentiary value
4. in-place repair would blur salvage, publication, and migration into one risky operation

What it is:

1. a stale runtime artifact
2. a useful evidence source for what was deployed or tested on-host
3. a later salvage-comparison input

What it is not:

1. the future migration target
2. a canonical implementation workspace
3. proof that Olares-first daily development is ready

## Intended Host Dev Path Decision

`/home/olares/src/apex-power-ops-platform` should not become the intended host dev path.

A later canonical host path should be prepared. The authority model currently points to `~/code/apex`, but the parent-root publication boundary creates one implementation ambiguity that must be resolved inside the later packet:

1. either prepare a host parent-root mirror from `jasonlswenson-sys/RESA-Power-Project-Management.git` and work under its `apex-power-ops-platform/` prefix
2. or explicitly restate how `~/code/apex` can be used as a subworkspace clone without changing the parent-root publication boundary

Until that ambiguity is resolved, the safest wording is:

1. keep `C:/APEX Platform` as publication authority
2. keep GitHub canonical at `jasonlswenson-sys/RESA-Power-Project-Management.git`
3. prepare a new host path later rather than mutating `/home/olares/src/apex-power-ops-platform`
4. do not claim that any host path is ready for primary daily development

## Packet-002 Publication Scope Reconciliation

The 2026-04-25 packet-002 publication scope should be retired as an execution packet, not restated as-is.

Reason:

1. `ops/agents/handoffs/2026-04-25-olares-workstation-001-publication-follow-through-scope-handoff.md` identified a bounded set of workstation-synced surfaces that were not yet branch-published at that point
2. `ops/agents/handoffs/2026-04-25-olares-workstation-002-publication-follow-through-blocker-handoff.md` later found that the broader packet-002 scope was no longer present as one coherent, stageable lane
3. the branch has since moved through the Phase 5 assessment chain
4. Packet 005 now shows similar-looking surfaces as dirty/untracked on the host clone, but that is host-clone divergence evidence, not proof that the old workstation publication packet should be forced forward

Retirement decision:

1. retire old packet-002 as a publication-follow-through execution lane
2. preserve the two April handoffs as evidence
3. carry forward the old path list as a comparison checklist for a later host clone replacement or salvage packet
4. do not stage only partial residue under the old packet-002 name
5. do not widen into unrelated repo paths to make the old packet shape appear coherent

## Later Implementation Packet Recommendation

A later implementation packet is warranted only if the operator wants to keep Olares-first daily development as a candidate.

Recommended packet name:

`Olares Phase 5 007 - Canonical Host Dev Path Preparation`

Required mutation scope:

1. preflight read-only check of current workstation parent-root branch, commit, remotes, and dirty state
2. preflight read-only check of current host clone path, branch, commit, remote, and dirty/untracked files
3. write an evidence snapshot of the old host clone before any replacement action
4. create a separate canonical host source path, not by editing `/home/olares/src/apex-power-ops-platform`
5. populate the new path from the GitHub-canonical repository or from another explicitly approved parent-root-preserving method
6. configure no public ingress and no auth changes
7. perform no Gitea/canonical-hosting cutover
8. leave the old host clone in place until a later retirement packet explicitly decides deletion or archival
9. validate that VS Code Remote-SSH can open the new path over `olares-mesh`
10. record whether the new path preserves the parent-root publication boundary or intentionally restates it

Explicitly out of scope for that later packet unless separately authorized:

1. deleting the old host clone
2. running `git reset`, `git clean`, branch switches, or remote rewrites on the old clone
3. changing the canonical GitHub repository
4. installing or configuring Gitea
5. moving daily development center of gravity to Olares
6. promoting loopback Docker services
7. changing Kubernetes, Helm, Olares apps, auth, ingress, Headscale, or public routes

## Decision Surface Impact

Workstation migration:

Not ready. Packet 006 sharpens the repo-authority blocker and recommends a separate canonical host path preparation packet before any migration discussion.

AI-services-zone expansion:

Not ready. This packet does not add running AI-services evidence and does not resolve Step 2 orchestration decisions.

Gitea/code-hosting mirror:

Not ready. GitHub remains canonical, the Gitea transition gate is still missing or unrestated, and host clone remote divergence makes mirror work riskier, not easier.

Canonical-hosting transition:

No-go. This packet preserves parent-root and GitHub-canonical authority.

## Explicit No-Go Items Preserved

1. no generic Olares reopening
2. no Olares-first daily development migration
3. no host clone mutation from this planning packet
4. no host clone deletion
5. no git pull, reset, clean, branch switch, or remote rewrite
6. no Gitea install or mirror packet
7. no canonical-hosting transition
8. no public ingress, auth, Headscale, SSH trust, Kubernetes, Helm, systemd, or Olares app changes
9. no claim that VS Code Remote-SSH viability equals repo-authority readiness
10. no use of the old packet-002 scope to sweep unrelated worktree paths

## Validation Performed

Validation completed without host or runtime mutation:

1. read Packet 006 JSON
2. read post-005 reconciliation handoff and confirmed it warrants repo-clone reconciliation planning
3. read Packet 005 host runtime inventory handoff for host clone evidence
4. read the April packet-001 and packet-002 publication follow-through handoffs
5. read the Olares authority framework
6. checked current workstation parent-root branch, commit, and remotes
7. checked that the Packet 006 handoff did not already exist before this write
8. updated the roadmap only to record this planning result and the narrowed later implementation packet shape

## Final Recommendation

Assessment supports opening a narrow next packet only if the operator wants to keep Olares-first daily development under consideration.

The next packet should be canonical host dev path preparation, not migration.

Final readiness state:

1. host clone disposition: preserve as evidence now, replace later for dev
2. old packet-002 publication scope: retire as execution lane
3. later implementation packet: warranted for separate canonical host path preparation
4. migration: not ready
5. AI-services expansion: not ready
6. Gitea/code-hosting mirror: not ready
7. canonical-hosting transition: no-go
