# Olares Developer Host Cutover Technical Plan

Date: 2026-05-05
Status: Active planning baseline
Scope: technical operating model and cutover architecture for making the Olares One the authoritative development host

## Purpose

This document translates the program decision into a technical cutover shape.

The problem is no longer generic Olares expansion.

The problem is split development residency:

1. the laptop currently carries too much durable development responsibility
2. the Olares host already carries some runtime, mirror, and backup authority
3. continued feature delivery will be brittle until those responsibilities are consolidated on Olares

## Target Operating Model

### Authoritative Surfaces

1. GitHub remains canonical origin
2. `C:/APEX Platform` remains the authoritative publication boundary
3. `/home/olares/code/apex` is the authoritative host mirror of that parent-root boundary
4. `/home/olares/code/apex/apex-power-ops-platform` is the authoritative host implementation surface
5. `/home/olares/src/apex-power-ops-platform` remains historical evidence only and is never promoted back to canonical status

### Role Split

Olares host responsibilities:

1. durable repo mirror
2. durable toolchains and validation runtimes
3. long-running development-side services that must survive laptop disconnects
4. durable secrets and mutable data boundaries outside git
5. bounded developer validation and publication proof

Laptop responsibilities:

1. private-mesh client
2. VS Code Remote-SSH or browser-terminal client
3. review and approval surface
4. emergency fallback terminal

The laptop is not the durable runtime anchor.

## Host Filesystem Model

Use the following host paths as the operating baseline:

1. `~/code/apex` for the parent-root mirror
2. `~/code/apex/apex-power-ops-platform` for active implementation
3. `~/apex-data` for mutable development and application data
4. `~/apex-secrets` for local secret-bearing material not stored in git
5. `~/apex-backups` for bounded host-side recovery artifacts

Rules:

1. no required secret should exist only on the laptop
2. no required mutable runtime state should exist only in the git workspace
3. no new active development should target `/home/olares/src/apex-power-ops-platform`

## Technical Cutover Slices

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