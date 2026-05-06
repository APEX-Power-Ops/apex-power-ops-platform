# Olares Developer Host Cutover Milestone Plan

Date: 2026-05-05
Status: Active planning baseline
Scope: program-level milestone plan for making the Olares One the authoritative always-on development workstation while reducing the field laptop to a client-only operator surface

## Purpose

This plan converts the current infrastructure constraint into a delivery sequence.

The field laptop can no longer be treated as the durable development center of gravity.

The Olares One must become the authoritative development workstation before broader product execution resumes at normal pace.

This plan does not itself reopen generic Olares implementation.

It defines the milestone order, acceptance criteria, and exit gates for the cutover phase that now precedes renewed feature delivery.

## Constraint Statement

The controlling operational constraint is:

1. the field laptop cannot remain always on, always connected, or responsible for persistent development state
2. the Olares One must hold the durable repo, tooling, validation, and run-state needed for ongoing development
3. the laptop must degrade to a portable client, approval, and emergency-intervention role

## Program Decision

The next active program phase is:

`Olares Developer Residency / Developer-Host Cutover`

This phase precedes resumed feature delivery.

The Operations Visibility MVP remains the strongest business lane after the cutover baseline is proven.

## Milestones

### Milestone 1 - Host Residency Baseline

Goal:

Make the Olares One the authoritative residence for the parent-root mirror, implementation surface, secrets boundary, and persistent operator paths.

Acceptance criteria:

1. the authoritative host parent-root mirror is `~/code/apex`
2. the active implementation surface is `~/code/apex/apex-power-ops-platform`
3. the historical clone under `/home/olares/src/apex-power-ops-platform` is explicitly non-canonical and observe-only
4. secrets and mutable data are kept outside the git workspace
5. restart and reconnect behavior for the host workspace is documented and repeatable

### Milestone 2 - Host Toolchain And Runtime Proof

Goal:

Prove that the Olares host can execute the minimum real development loop without relying on the laptop as the runtime anchor.

Acceptance criteria:

1. required host toolchains for the active delivery lanes are installed and usable on Olares
2. the canonical host path can run the approved validation commands for at least one active application lane
3. the canonical host path can run the approved validation commands for at least one shared package lane
4. required environment bootstrapping is documented and repeatable on Olares
5. the proof is captured as repo-visible evidence, not only terminal history

### Milestone 3 - Publication And Continuity Proof

Goal:

Prove that the Olares host can participate in the normal publication workflow without the laptop being the system of record.

Acceptance criteria:

1. the Olares host can fetch, inspect, branch, and validate against the GitHub-canonical repo path
2. the Olares-hosted workflow can produce a bounded change and its validation evidence
3. publication and host parity rules remain explicit and reproducible
4. no required development state exists only on the laptop

### Milestone 4 - Client-Only Laptop Posture

Goal:

Reduce the field laptop to a portable client for access, review, approval, and emergency fallback.

Acceptance criteria:

1. daily development can continue while the laptop is offline or away from the desk
2. the laptop is not the only holder of active repo state, secrets, or long-running processes
3. access from the laptop works through approved client paths such as private-mesh SSH, VS Code Remote-SSH, the browser-delivered Olares desktop UI, or browser-terminal fallback
4. the cutover does not require public ingress or a canonical-hosting transition

### Milestone 5 - Resume Product Delivery From Olares

Goal:

Resume feature delivery only after the host-residency model is proven.

Acceptance criteria:

1. one bounded real implementation or validation slice is executed from the Olares-hosted development posture
2. the slice does not depend on the laptop as the durable runtime anchor
3. the next business lane is then reopened explicitly, with Operations Visibility as the default follow-on

## No-Go Items During Cutover

The cutover phase must not be misread as approval for:

1. generic Olares reopening
2. public ingress widening
3. Gitea or canonical-hosting transition
4. AI-services expansion by default
5. package or runtime churn unrelated to developer residency
6. renewed feature delivery from the laptop-first posture

## Sequencing Rule

Use this order:

1. host residency baseline
2. host toolchain and runtime proof
3. publication and continuity proof
4. laptop client-only confirmation
5. resumed feature delivery

Do not reverse that order.

## Immediate Next Step

The smallest truthful next move is a bounded cutover preflight and execution-planning packet.

That packet should:

1. consume the current Olares post-Phase-5 authority state
2. restate the laptop constraint as a program dependency
3. classify the minimum host-residency proof slices required before renewed product delivery
4. name the first bounded execution packet for host toolchain and validation proof