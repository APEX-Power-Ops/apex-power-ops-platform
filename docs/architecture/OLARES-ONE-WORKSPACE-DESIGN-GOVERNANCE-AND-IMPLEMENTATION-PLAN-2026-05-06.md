# Olares One Workspace Design, Governance, And Operating Model

Date: 2026-05-06
Status: Active authority surface
Scope: current Olares One workspace constraints, governance rules, target environment, operator process, and bounded closeout routing

## Purpose

This document is the current stakeholder-facing authority for the Olares One workspace operating model.

It consolidates the current truth that is otherwise split across the Olares workspace framework, the post-closure Olares roadmap, the developer-host cutover plans, and the active packet chain.

Use this document when the question is:

1. what the Olares One workspace is supposed to be now,
2. what is constrained or forbidden,
3. which tools and processes are approved,
4. what remains to be aligned or improved,
5. how execution should continue without reopening already-closed lanes,
6. where the compact current lane register lives.

Repo-structure authority companion:

`docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md`

Use that document when the decision is about the permanent repo shell, git boundary, authority relocation, or parent-root cutover.

Companion surface:

`docs/architecture/APEX-PM-LANE-OPERATING-COCKPIT-2026-05-06.md`

Use that cockpit for rapid lane selection and validation routing. It does not override the authority order below.

Front-door workspace companions:

1. `docs/authority/WORKSPACE-REGISTRY-2026-05-23.md`
2. `docs/authority/REPO-PASSPORT-STANDARD-2026-05-23.md`
3. `REPO_PASSPORT.md`

## Current Program Decision

The Olares One is the durable development anchor for APEX.

That anchor is now also the governing migration direction for the whole program.

Repo structure now has explicit first priority inside that migration direction.

The remaining parent-root publication residue is now signed-off closeout provenance to preserve, demote further when needed, or later archive by explicit packet; it is not an acceptable steady-state repository model.

**Substrate-currency update (added 2026-05-26 PM cycle 3 via matrix #31 + #65):** Matrix #31 closed 2026-05-26 with parent-root `apps/+packages/` archived to `_archive/Apr2026_PreTranche/` (canonical operating boundary is now `apex-power-ops-platform/` nested inner repo + `source-domains/*`). Matrix #65 PM Schema Foundation Plan v2 hybrid synthesis dispatch was authored 2026-05-26 (Codex Cloud executor; ~8-15 hr execution; PATTERN-005 inaugural application) and will reconcile current PM substrate (foundation plan v1 dated 2026-05-26) against live `public.*` (125 tables) and `seam.*` (28 tables; Lane 411 Rev A-C revrec architecture with "recognition firewall" principle) Supabase schemas. When matrix #65 v2 plan lands, this OLARES-ONE plan SHOULD be revisited for substrate-currency refresh (tracked as matrix #69; Tier 3 deferred).

At the current repo-owned evidence floor, that residue no longer blocks the laptop-to-Olares migration signoff.

All Apex Ops work top to bottom should converge on Olares-resident governance, execution, validation, toolchains, and operator context so the field laptop no longer carries durable project risk or accumulates divergent workspace practice.

That does not mean Olares is the canonical source of truth.

The current transitional authoritative split is:

1. GitHub remains the canonical origin.
2. `C:/APEX Platform/apex-power-ops-platform` is the canonical publication boundary for active Apex Ops repo work.
3. `/home/olares/code/apex/apex-power-ops-platform` is the authoritative host implementation surface.
4. `C:/APEX Platform` and `/home/olares/code/apex` are umbrella containers around that repo boundary rather than the default git roots.
5. `/home/olares/src/apex-power-ops-platform` is historical only and must remain observe-only.
6. The laptop is a client surface, not the durable runtime anchor.

## Design Constraints

### Workspace boundary constraints

1. Treat `apex-power-ops-platform` as the independent git root for active repo operations.
2. Scope staging and publication to bounded repo-relative paths unless a deliberate broad repo publication is intended.
3. Do not mutate the historical host clone at `/home/olares/src/apex-power-ops-platform`.
4. Keep secrets, mutable runtime data, and recovery artifacts outside the git workspace.

### Runtime and trust constraints

1. The admitted Olares-first AI/operator boundary remains `apex-fs`, `apex-db`, and `apex-jobs`.
2. `apex-jobs` remains the run ledger and promotion gate.
3. Do not widen into `ai_tasks`, broader executor admission, or speculative AI-services rollout without a separate packet.
4. Preserve the distinction between local sandbox proof, workstation proof, and host proof.
5. Prefer truthful `HOLD`, `UNAVAILABLE`, or dormancy outcomes over fabricated readiness.

### Exposure and governance constraints

1. Keep Olares-hosted development and private-lane services behind the approved private or authenticated access model.
2. Do not use this workspace plan to authorize public ingress widening, canonical-hosting changes, or identity-model changes.
3. Keep GitHub canonical; Gitea remains mirror-only unless a separate transition packet approves otherwise.
4. Do not reopen dormant Olares branches without their published triggers.

## Governance Rules

### Authority order

Use this order when documents conflict:

1. `docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`
2. `docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md`
3. `docs/architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md`
4. `plan/infrastructure-olares-full-implementation-roadmap-1.md`
5. `docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-TECHNICAL-PLAN-2026-05-05.md`
6. `docs/architecture/OLARES-DEVELOPER-HOST-CUTOVER-MILESTONE-PLAN-2026-05-05.md`
7. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md`
8. packet and handoff artifacts under `ops/agents/`

### Execution rules

1. All new Olares scope must be packetized when it changes tooling, runtime, install surfaces, hosting posture, or trust boundaries.
2. Each packet must define what changed, what was validated, what stayed deferred, and what boundaries were preserved.
3. Publication is not complete until `origin/clean-main` is updated from the standalone repo root and `/home/olares/code/apex/apex-power-ops-platform` is restored to clean parity.
4. Host proof is preferred for Olares-first claims whenever a bounded host validation exists.
5. Old evidence remains reference only after newer packet authority supersedes it.

### Operational truth rules

1. If the minimal MCP trio is not running, status surfaces must report that truth instead of implying readiness.
2. If deferred Operations Visibility views remain empty, the correct result is hold or dormancy, not synthetic consumer work.
3. If a host capability is absent and not required by current business truth, keep the lane closed instead of solving speculative gaps.
4. Do not normalize laptop-only or split-residency exceptions into the default Apex Ops operating model; every active lane should converge toward Olares-resident execution.
5. Treat any remaining parent-root publication language as historical residue, not as the desired permanent home for durable project practice.

### PM cockpit companion

1. Use `docs/architecture/APEX-PM-LANE-OPERATING-COCKPIT-2026-05-06.md` as the compact whole-project lane register and session-start routing surface.
2. If the cockpit conflicts with a governing document, the authority order above wins.

## Optimal Workspace Environment

### Host environment

The optimal current workspace environment is an Olares-hosted, GitHub-canonical, standalone-repo-rooted development model.

The governing target is a whole-project Olares-first operating model with GitHub still canonical while the remaining umbrella-residue and documentation debt are retired one by one.

Authoritative host paths:

1. `/home/olares/code/apex/apex-power-ops-platform`
2. `/home/olares/apex-data`
3. `/home/olares/apex-secrets`
4. `/home/olares/apex-backups`

Required host characteristics:

1. durable repo mirror,
2. durable toolchain placement outside git,
3. stable private-mesh access,
4. host-resident validation capability for bounded slices,
5. recovery artifacts and operator surfaces that survive laptop disconnects.

### Client environment

The laptop should provide:

1. private-mesh SSH access,
2. VS Code Remote-SSH,
3. browser-delivered Olares desktop or browser-terminal fallback,
4. client access, review, approval, and emergency intervention only.

The laptop should not be the sole holder of:

1. active repo state,
2. long-running toolchains,
3. secrets,
4. mutable development state,
5. completion-critical validation context.

## Approved Tooling Stack

### Core development and validation tools

1. GitHub on `clean-main` as canonical origin.
2. VS Code plus Remote-SSH as the normal editing surface.
3. PowerShell on the workstation and Bash on the Olares host as operator shells.
4. Host-materialized `pnpm` under `/home/olares/apex-data/toolchains/pnpm-10.0.0/node_modules/.bin/pnpm`.
5. Host-materialized calc-engine Python under `/home/olares/apex-data/toolchains/calc-engine-venv/bin/python`.

### Approved Olares-first operator surfaces

1. `tools/ai/run-minimal-mcp-trio.ps1`
2. `tools/ai/run-minimal-mcp-trio.sh`
3. `tools/ai/run-olares-hold-boundary-check.ps1`
4. `tools/ai/run-olares-hold-boundary-check.sh`
5. `tools/ai/run-olares-host-bootstrap-status.sh`

### Approved AI boundary

1. `apex-fs`
2. `apex-db`
3. `apex-jobs`

### Default admitted AI runtime posture

1. The admitted minimal MCP trio remains operator-on-demand by default.
2. Normal Olares durable-host readiness does not require `apex-fs`, `apex-db`, and `apex-jobs` to remain running at rest between bounded operator sessions.
3. `tools/ai/run-olares-host-bootstrap-status.sh` is the controlling readiness surface for this posture: a clean authoritative mirror plus truthful `minimal_mcp.status = not-running` is a valid ready state, not a defect.
4. Open a separate durable-runtime admission packet only if a concrete operator insufficiency, unattended workflow requirement, or new validation obligation proves that operator-on-demand is no longer sufficient.

Not approved by this plan:

1. broader AI-services expansion,
2. `ai_tasks` bridge widening,
3. speculative orchestration-service rollout,
4. canonical code-hosting transition.

## Approved Operating Process

### Standard Olares-first change flow

1. Start from the current authority docs and latest packet frontier.
2. Select the smallest bounded slice that changes one real operator, workflow, or business constraint.
3. Implement only what that slice needs.
4. Validate the slice with the narrowest truthful executable check.
5. Publish bounded commits to `origin/clean-main`.
6. Restore `/home/olares/code/apex/apex-power-ops-platform` to clean parity.
7. Record the outcome in packet, handoff, roadmap, and status surfaces.

### Standard host-readiness flow

1. Run `Olares host bootstrap status` or `bash apex-power-ops-platform/tools/ai/run-olares-host-bootstrap-status.sh` from `/home/olares/code/apex`.
2. Or run `Olares host bootstrap status` or `bash tools/ai/run-olares-host-bootstrap-status.sh` from `/home/olares/code/apex/apex-power-ops-platform`.
3. Confirm canonical mirror head and clean status.
4. Confirm the old clone remains preserved and non-canonical.
5. Confirm materialized toolchains are present.
6. Confirm minimal MCP and hold-boundary posture before deciding whether a new packet is necessary.

### Standard AI-runtime decision rule

1. Treat `not-running` as the default steady-state posture for the admitted trio unless a later packet explicitly widens runtime expectations.
2. Use `run-minimal-mcp-trio` only for bounded operator sessions, verification, or cadence checks that actually need the trio online.
3. Do not promote the trio to always-on host baseline merely because the wrappers and host proof exist.
4. Reopen runtime admission only from concrete evidence, not convenience or drift anxiety.

## Current Implemented State

The following are already implemented and validated:

1. Olares host mirror and client-only laptop posture,
2. bounded host toolchain materialization,
3. resumed host-side validation slices,
4. minimal MCP trio operator surface and host proof,
5. hold-boundary cadence surface with truthful workstation live-DSN proof and host graceful-degrade behavior,
6. host bootstrap/status operator surface with published host proof,
7. packetized publication and host parity discipline,
8. default runtime governance that keeps the admitted minimal MCP trio operator-on-demand until a separate durable-runtime packet is justified.

## Post-Signoff Routing

### Phase 1: Keep the durable host baseline explicit

1. keep the host bootstrap/status surface as the first operator entry point,
2. keep packet, roadmap, and status authority aligned after each bounded slice,
3. prevent historical conceptual docs from being mistaken for current Olares governance.

### Phase 2: Open follow-on hardening only where real friction remains

Candidate follow-ons must be chosen by evidence, not by aspiration.

Allowed next-slice classes:

1. docs-and-task discoverability improvements,
2. bounded host validation ergonomics,
3. truthful status or readiness surfaces,
4. publication/parity hygiene improvements,
5. compact lane-frontier surfaces that reduce repeated session-start reconstruction without widening scope.

Disallowed by default:

1. installs without a separate authority packet,
2. runtime/service mutation for convenience alone,
3. AI boundary widening,
4. generic infrastructure expansion.

### Phase 3: Reopen other lanes only on trigger

1. reopen deferred Operations Visibility only on live-data change or separately justified need,
2. reopen simultaneous-worker planning only on new evidence satisfying its trigger framework,
3. reopen hosting, Gitea, or broader AI-services only by separate packet.

## PM Routing Rule

The current PM rule is:

1. treat Olares as an active but bounded developer-residency and operator-hardening lane,
2. do not treat it as an always-open infrastructure epic,
3. execute adjacent workflow-hardening slices only when they reduce real operator burden or improve durable host correctness,
4. keep business delivery lanes separate from host-governance hardening unless a packet intentionally bridges them.

## Success Standard

This plan is implemented successfully when:

1. the Olares host remains the durable development anchor,
2. the laptop remains client-only,
3. the approved operator surfaces expose current truth without hidden dependencies,
4. every new Olares-first change is packetized, validated, published, and host-resynced cleanly,
5. no stale document can reasonably be mistaken for the current Olares operating model.