# Olares Dev Residency 002 Canonical Host Residency And Toolchain Revalidation Handoff

Date: 2026-05-05
Status: Complete
Packet: `ops/agents/packets/draft/2026-05-05-olares-dev-residency-002-canonical-host-residency-and-toolchain-revalidation.json`
Scope: first bounded execution lane for proving Milestone 1 host residency baseline and minimum host-side toolchain viability

## Authority

This handoff depends on:

1. `ops/agents/packets/draft/2026-05-05-olares-dev-residency-001-developer-host-cutover-preflight-and-execution-planning.json`
2. `ops/agents/handoffs/2026-05-05-olares-dev-residency-001-developer-host-cutover-preflight-and-execution-planning-handoff.md`
3. `docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-MILESTONE-PLAN-2026-05-05.md`
4. `docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-TECHNICAL-PLAN-2026-05-05.md`
5. `docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-MILESTONE-1-ACCEPTANCE-CHECKLIST-2026-05-05.md`
6. `plan/infrastructure-olares-full-implementation-roadmap-1.md`

Packet 002 executed after Packet 001 closed affirmatively.

## Purpose

Packet 002 is the first bounded execution lane of the Olares developer-residency
phase.

Its job is not to resume feature delivery.

Its job is to prove that the canonical host path, host-local boundaries, and
minimum toolchain loop are real enough to satisfy Milestone 1 and begin
Milestone 2 without drifting back into a laptop-first posture.

## Verdict

Packet 002 is complete with a split verdict:

1. Milestone 1 host residency baseline: pass
2. minimum host-side toolchain and validation proof: blocked under no-install rules

The Olares host path, old-clone demotion, host-local boundaries, and reconnect
posture are proven well enough for Milestone 1.

The host is not yet proven ready to run the minimum application/shared-package
validation loop because required no-install tooling is missing.

## Execution Evidence

Access method:

`private-mesh SSH via olares-mesh`

Canonical host path evidence:

1. host: `olares`
2. user: `olares`
3. active implementation path: `/home/olares/code/apex/apex-power-ops-platform`
4. parent git top-level from parent root: `/home/olares/code/apex`
5. git top-level from implementation surface: `/home/olares/code/apex`
6. host mirror commit: `38b90166da7d48f4ef17334b0ea92916f6e183ee`
7. host mirror status count: `0`

Old clone observation:

1. path: `/home/olares/src/apex-power-ops-platform`
2. commit: `2836a2622309b4e146ca24f23b5bf87312c0c857`
3. status count: `30`
4. mutation: none
5. use: observe-only historical evidence

Host-local boundary evidence:

1. `/home/olares/apex-secrets` exists outside the git workspace with 2 top-level entries
2. `/home/olares/apex-data` exists outside the git workspace with 1 top-level entry
3. `/home/olares/apex-backups` exists outside the git workspace with 1 top-level entry

Reconnect evidence:

1. a second private-mesh SSH session re-entered `/home/olares/code/apex/apex-power-ops-platform`
2. that session resolved the git top-level to `/home/olares/code/apex`
3. disconnect/re-entry was tested; restart was not performed

Toolchain observation:

1. Node is present: `v18.19.1`
2. Python is present: `Python 3.12.3`
3. `pnpm` is missing from PATH
4. root `node_modules` is absent
5. `apps/operations-web/node_modules` is absent
6. `pytest` is missing from PATH

Validation attempts:

1. `apps/operations-web`: `pnpm typecheck` exited `127` because `pnpm` was not found
2. `apps/operations-web`: `npx --no-install tsc --noEmit` exited `1` because `npx --no-install` canceled rather than downloading
3. `packages/calc-engine`: `PYTHONPATH=src python3 -m pytest -q tests` exited `1` because `pytest` is not installed

The prepared host mirror ended with status count `0`.

The old clone ended with status count `30` and was not mutated.

## Milestone 1 Checklist Audit

1. Host parent-root mirror is `~/code/apex`: pass
2. Active host implementation surface is `~/code/apex/apex-power-ops-platform`: pass
3. `git rev-parse --show-toplevel` resolves to `/home/olares/code/apex`: pass
4. Operator-facing packet and technical surfaces point active host work at `~/code/apex`: pass
5. `/home/olares/src/apex-power-ops-platform` is historical evidence only: pass
6. No Milestone 1 validation or mutation ran from the old clone: pass
7. Old-clone comparison was read-only preservation evidence: pass
8. Secret-bearing material boundary exists outside git under `~/apex-secrets`: pass
9. Mutable development/application state boundary exists outside git under `~/apex-data`: pass
10. Recovery boundary exists outside git under `~/apex-backups`: pass
11. No packet evidence showed required secret, mutable state, or recovery material existing only on the field laptop: pass for the bounded proof
12. Approved reconnect path was proven through private-mesh SSH: pass
13. Host workspace was re-entered without undocumented laptop-local state: pass for reconnect
14. Target path and reconnect method were captured: pass
15. Milestone 1 proof did not reopen feature delivery, public ingress, AI-services expansion, Gitea, or canonical-hosting transition: pass
16. Milestone 1 proof did not re-establish the laptop as durable runtime anchor: pass

Milestone 1 closes for host residency baseline.

Milestone 2 toolchain and validation readiness remains blocked.

## Entry Conditions

Execute this packet only if all of the following are true:

1. Packet 001 closes affirmatively
2. GitHub remains canonical
3. `/home/olares/code/apex` remains the intended host parent-root mirror
4. `/home/olares/src/apex-power-ops-platform` remains observe-only
5. the execution session can use an approved private access path to Olares

## Required Proof

This execution lane must capture repo-visible evidence for:

1. host path authority from `/home/olares/code/apex`
2. active implementation residency at `/home/olares/code/apex/apex-power-ops-platform`
3. old-clone demotion and non-use
4. host-local boundaries for secrets, mutable state, and recovery material
5. reconnect or restart repeatability
6. one bounded application-lane validation from the host path
7. one bounded shared-package-lane validation from the host path
8. explicit audit results against every Milestone 1 checklist item

## Default Validation Targets

Use these defaults unless a narrower truthful alternate is required:

1. application lane: `apps/operations-web`
2. shared package lane: `packages/calc-engine`

Permitted alternate shared-package lanes if environment or command shape makes
them more truthful:

1. `packages/forms-engine`
2. `packages/p6-ingest`

## No-Go Boundary

This packet must not open:

1. feature delivery
2. public ingress widening
3. AI-services expansion by default
4. Gitea or canonical-hosting transition
5. promotion of the old clone back to active status
6. runtime or package churn unrelated to bounded proof

## Completion Rule

Packet 002 closes cleanly only if:

1. the Milestone 1 checklist is fully audited in repo-visible evidence
2. the host path is proven as the active residence for the bounded proof slices
3. the laptop is not the controlling runtime anchor for those proof slices
4. the result stays inside the bounded cutover scope above

If any of those conditions fail, the handoff must say so explicitly and stop the
lane without improvising wider changes.

## Next Candidate

The smallest truthful next packet is:

`Olares Dev Residency 003 - Bounded Host Toolchain Availability Decision`

That next packet should decide how to handle the missing no-install host
tooling before any claim that the host can run the minimum application and
shared-package validation loop.
