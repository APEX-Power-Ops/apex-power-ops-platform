# Olares Developer Host Cutover Technical Plan

Date: 2026-05-05
Status: Executed technical cutover baseline with closeout-routing context
Scope: technical operating model and cutover architecture for making the Olares One the authoritative development host

Closeout interpretation note:

The developer-host cutover this plan describes is now materially complete. This document remains the technical baseline for the host-residency transition, but it is no longer a live pre-cutover planning surface.

Current routing:

1. use `PROJECT_STATUS.md` for the current residue-retirement lane and latest completed packets,
2. use `docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md` for the current active authority chain,
3. use `docs/architecture/OLARES-PUBLICATION-BOUNDARY-RETIREMENT-DEPENDENCY-INVENTORY-2026-05-06.md` for the remaining post-cutover boundary closeout queue.

## Purpose

This document records the technical cutover shape that translated the program decision into an executable host-residency model.

The problem is no longer generic Olares expansion.

The governing direction is now explicit: all Apex Ops related work top to bottom should migrate to Olares-first governance and execution so workspace governance, protocol, and operator method do not fragment across host and field laptop surfaces.

The problem is split development residency:

1. the laptop currently carries too much durable development responsibility
2. the Olares host already carries some runtime, mirror, and backup authority
3. continued feature delivery will be brittle until those responsibilities are consolidated on Olares

## Target Operating Model

### Authoritative Surfaces

1. GitHub remains canonical origin
2. `C:/APEX Platform/apex-power-ops-platform` is now the canonical local repo boundary
3. `/home/olares/code/apex/apex-power-ops-platform` is now the authoritative host mirror and implementation surface for the standalone repo boundary
4. `/home/olares/code/apex/apex-power-ops-platform` is the authoritative host implementation surface
5. `/home/olares/src/apex-power-ops-platform` remains historical evidence only and is never promoted back to canonical status

During the transition captured here, GitHub and the current parent-root boundary stayed canonical. After cutover, GitHub remains canonical while the standalone repo boundary and Olares host implementation root are the controlling operator contract.

### Role Split

Olares host responsibilities:

1. durable repo mirror
2. durable toolchains and validation runtimes
3. long-running development-side services that must survive laptop disconnects
4. durable secrets and mutable data boundaries outside git
5. bounded developer validation and publication proof

Laptop responsibilities:

1. private-mesh client
2. VS Code Remote-SSH, browser-delivered Olares desktop UI, or browser-terminal client
3. review and approval surface
4. emergency fallback terminal

The laptop is not the durable runtime anchor.

No new lane should adopt a laptop-first durable workflow when an Olares-resident equivalent can be packetized and proven instead.

## Host Filesystem Model

Use the following host paths as the operating baseline:

1. `~/code/apex` for the host umbrella containing the canonical repo mirror
2. `~/code/apex/apex-power-ops-platform` for active implementation
3. `~/apex-data` for mutable development and application data
4. `~/apex-secrets` for local secret-bearing material not stored in git
5. `~/apex-backups` for bounded host-side recovery artifacts

Rules:

1. no required secret should exist only on the laptop
2. no required mutable runtime state should exist only in the git workspace
3. no new active development should target `/home/olares/src/apex-power-ops-platform`

## Recorded Technical Cutover Slices

### Slice A - Host Residency And Path Authority

Objective:

Reconfirm the intended host path and enforce non-canonical status for the old clone.

Proof required:

1. host mirror path exists and is reachable
2. active implementation path exists and is reachable
3. old clone remains observe-only
4. operator docs point to the correct host path

### Slice B - Toolchain Parity

Objective:

Prove that Olares can execute the minimum real development commands for active lanes.

Minimum proof targets:

1. `apps/operations-web`
2. one shared package lane such as `packages/forms-engine`, `packages/p6-ingest`, or `packages/calc-engine`

Proof required:

1. host Node or pnpm path is usable where needed
2. host Python path is usable where needed
3. required environment templates or local env materialization paths are documented
4. bounded validation commands run from the host implementation path

### Slice C - Validation Residency

Objective:

Move validation dependence off the laptop.

Proof required:

1. at least one application validation path runs from Olares
2. at least one package validation path runs from Olares
3. evidence is recorded as repo-visible handoff or packet output
4. laptop disconnect does not destroy the validation context

### Slice D - Publication Continuity

Objective:

Prove that the Olares-hosted workflow can support normal bounded publication practice without making Olares canonical.

Proof required:

1. the host can fetch and inspect the canonical origin safely
2. the host can support bounded git validation and publication preparation
3. the publication boundary remains `C:/APEX Platform`
4. no remote rewrite, Gitea cutover, or canonical-hosting change occurs in this slice

### Slice E - Client-Only Laptop Confirmation

Objective:

Prove the laptop is now a client rather than the durable workstation.

Proof required:

1. the laptop can attach to Olares over approved access paths
2. the laptop is not needed to keep runtimes alive
3. the laptop is not the only holder of active repo, secret, or validation state
4. if Olares exposes its own browser-delivered desktop UI, that UI is treated as an admitted host-supported client surface rather than as a contradictory laptop-first runtime anchor

### Slice F - Publication Boundary Retirement Readiness

Objective:

Identify and retire the remaining split-residency dependencies that still keep `C:/APEX Platform` active as the transitional publication boundary.

Proof required:

1. remaining Windows-bound publication and operator surfaces are inventoried,
2. the next highest-leverage retirement target is selected explicitly,
3. the retirement sequence preserves GitHub canonical status unless a later separate hosting packet changes it,
4. retirement is driven by concrete dependency closure rather than by assertion.

## Explicit Exclusions

This cutover plan excludes:

1. public ingress changes
2. AI-services expansion by default
3. Gitea or canonical-hosting transition
4. generic feature delivery from the old laptop-first posture
5. runtime or package churn not needed for host residency proof

## Recommended First Execution Packet

The first execution packet after planning should be:

`Olares Dev Residency 002 - Canonical Host Residency And Toolchain Revalidation`

That packet should be bounded to:

1. authoritative host-path verification
2. read-only or minimally invasive toolchain verification on the canonical host path
3. bounded validation commands for one application lane and one shared package lane
4. explicit proof that the laptop is not the controlling runtime anchor for those checks

That packet should not open:

1. feature delivery
2. product-scope runtime changes
3. AI-services-zone expansion
4. code-hosting transition

## Cutover Exit Rule

Do not resume broader product delivery until:

1. the host-residency slices are proven in repo-visible evidence, and
2. one bounded real development or validation slice is completed from the Olares-hosted posture.

After that, the default business follow-on remains the Operations Visibility MVP.