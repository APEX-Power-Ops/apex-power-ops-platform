---
goal: Updated Olares Full Implementation Roadmap For Post-Closure Operation And Expansion Control
version: 1.0
date_created: 2026-04-25
last_updated: 2026-05-03
owner: Platform Architecture / Olares Execution Lane
status: In progress
tags: [infrastructure, architecture, olares, roadmap, operations]
---

# Introduction

![Status: In progress](https://img.shields.io/badge/status-In%20progress-yellow)

This roadmap replaces the older first-run Olares sequencing posture with the current 2026-04-25 execution reality. The first governed Olares workstation lane, storage baseline, offline escrow follow-through, `forms-engine` installed proof, `p6-ingest` installed proof, and friendly alias ingress cleanup are complete. As of 2026-05-02, the bounded host-only private personal lane is also operationally closed through the authenticated browser-terminal bring-up, restored mesh SSH path, validated browser tunnel, tested local backup and restore path for `personal-notes`, workstation-held backup export, workstation-mediated OneDrive mirror, and validated daily backup automation. Remaining work is no longer a generic Olares bring-up effort; it is a bounded mix of regression readiness, publication hygiene, known platform limitations, explicit gatekeeping for any future Olares scope expansion, and preserving the current private-lane boundary without silently promoting it into the governed installed-app set.

For this workspace snapshot, the current on-disk evidence floor is the restored
runtime and rerun surface captured in
`ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md`
plus the surviving publication scope and blocker handoffs from 2026-04-25, the
private-lane bring-up and recovery record in
`ops/agents/handoffs/2026-05-01-olares-private-stack-browser-terminal-bring-up-handoff.md`,
and the bounded design and first-run notes under
`docs/architecture/OLARES-PRIVATE-STACK-BLUEPRINT-2026-05-01.md` and
`docs/architecture/OLARES-PRIVATE-STACK-FIRST-RUN-CHECKLIST-2026-05-01.md`.

## Executive Summary

Current posture:

1. the first governed Olares workstation lane is closed
2. the first `forms-engine` and `p6-ingest` host-installed proof lanes are closed
3. the friendly alias cleanup lane is closed
4. the bounded private personal lane is operationally closed in host-only scope, includes validated daily backup automation, and remains outside the governed installed-app set
5. Olares is now a regression, publication-hygiene, and scope-gating concern rather than the repo's primary delivery frontier

Items requiring attention:

1. publish the workstation-synced governed surfaces through the normal repo publication path
2. keep workstation, installed-service, and backup restore rerun paths active and current
3. preserve the known Settings API limitation for Helm-managed Olares apps
4. preserve the current private-lane boundary: host-only or mesh-tunneled access, local snapshot recovery, and no silent promotion into the governed installed-app or public-ingress surface
5. keep GitHub canonical unless an explicit Gitea transition packet is approved
6. create a bounded assessment lane for whether a future Olares One dev workspace expansion should become the center of gravity for APEX development, including Codex, Claude Code, and AI orchestration integration surfaces

Approved next-step rule:

1. do not reopen generic Olares bring-up work
2. execute only the bounded post-closure items in Phase 2 or a later explicitly authorized Olares packet
3. treat any future Olares One dev workspace migration exploration as an assessment-first lane until a later packet explicitly opens implementation

## 1. Requirements & Constraints

- **REQ-001**: Treat `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md` plus the surviving 2026-04-25 publication scope/blocker handoffs as the current on-disk authority surface for this workspace snapshot.
- **REQ-002**: Preserve the approved claim that the first governed Olares lane is closed for workstation, storage, backup, escrow, installed-service proof, and ingress alias cleanup.
- **REQ-003**: Distinguish closed baseline work from future Olares expansion work; do not represent them as one continuous open lane.
- **REQ-004**: Use rerun and regression surfaces already present in `docs/architecture/OLARES-WORKSTATION-BRING-UP-CHECKLIST-2026-04-23.md` and `docs/architecture/SERVICE-HOST-INSTALLED-PROOF-CHECKLIST-2026-04-23.md` before authoring new first-run material.
- **REQ-005**: Preserve the current 2026-05-01 private personal lane as a bounded host-only or mesh-tunneled service posture, not as a new governed Olares-installed app or public service publication claim.
- **ATT-001**: Publish the governed workstation-synced surfaces through the normal repo publication path because the workstation closure explicitly does not prove branch publication state.
- **ATT-002**: Preserve the known Settings API limitation for Helm-managed apps: friendly aliases are live, but the supported Settings API still lacks matching `ApplicationManager` resources for `forms-engine` and `p6-ingest`.
- **ATT-003**: Keep regression evidence current for private access, workstation-hosted stack health, local/offsite backup restore, and installed-route health.
- **ATT-004**: Keep GitHub canonical during MVP-era hosting; any Gitea use remains mirror-only until a separate transition packet is approved.
- **ATT-005**: Assess, but do not yet execute, whether the Olares One should become the primary daily APEX dev workspace for AI-assisted work across Claude Code, Codex, and orchestration services.
- **SEC-001**: Do not widen public exposure, identity behavior, or destructive data operations through roadmap execution alone.
- **SEC-002**: Keep Olares-hosted dev and service validation bound to the approved private-mesh or host-installed paths already documented.
- **SEC-003**: Do not treat assessment of Codex, Claude Code, Dify, n8n, Gitea, or other AI-assist surfaces as approval to install, promote, or make them canonical without a later packet.
- **CON-001**: The older `C:/APEX Platform/Infrastructure/Olares_MVP_Execution_Roadmap.md` remains sequencing context, not standalone governance.
- **CON-002**: Do not reopen Olares implementation as the repo’s primary frontier unless the reopen criteria in the 2026-04-25 authority transition handoff are met.
- **GUD-001**: Prefer updating repo-visible handoffs, rerun checklists, and validation surfaces over inventing new planning artifacts for already-closed first-run slices.
- **GUD-002**: Future Olares work must be packetized when it introduces a new host, a new app-install method, a new service, or a new canonical hosting posture.
- **PAT-001**: Maintain the trust model that separates sandbox proof, workstation proof, and host-installed proof.
- **PAT-002**: Use dated handoffs that are actually present in the workspace snapshot as the evidence floor for roadmap updates.

## 2. Implementation Steps

### Implementation Phase 1

- GOAL-001: Preserve the closed baseline for the first governed Olares scope and keep the roadmap aligned to the 2026-04-25 closure evidence.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Preserve the first workstation closure as complete through the restored local evidence floor captured in `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md` plus the surviving publication scope and blocker handoffs. | ✅ | 2026-04-25 |
| TASK-002 | Preserve the completed storage and backup baseline through `docs/architecture/OLARES-FIRST-STORAGE-BRING-UP-RUNBOOK-2026-04-23.md` and the restored local evidence floor in `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md`. | ✅ | 2026-04-25 |
| TASK-003 | Preserve the first host-installed proof for `forms-engine` through the restored runtime, canary, and manifest evidence floor in `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md`. | ✅ | 2026-04-25 |
| TASK-004 | Preserve the first host-installed proof for `p6-ingest` through the restored runtime, canary, and manifest evidence floor in `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md`. | ✅ | 2026-04-25 |
| TASK-005 | Preserve the alias and ingress cleanup outcome and the Settings API limitation boundary through `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md`. | ✅ | 2026-04-25 |
| TASK-006 | Keep `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md` referenced as the current local transition and evidence point in future Olares planning surfaces. | ✅ | 2026-05-01 |

### Implementation Phase 2

- GOAL-002: Close the remaining attention items that still matter operationally after first-run Olares proof has already passed.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-007 | Publish the local-only Olares/TCC authority-sync tranche first using `ops/agents/handoffs/2026-04-25-parent-root-olares-tcc-authority-surface-publication-handoff.md`, then publish the broader governed workstation-synced repo surfaces through the normal repo publication path using `ops/agents/packets/draft/2026-04-25-olares-workstation-002-governed-surface-publication-follow-through.json`. The first publication-control tranche landed on `clean-main` in commit `9db2efd`; the broader packet-002 lane is currently blocked per `ops/agents/handoffs/2026-04-25-olares-workstation-002-publication-follow-through-blocker-handoff.md`. |  |  |
| TASK-008 | Maintain a rerun path for workstation regression using `docs/architecture/OLARES-WORKSTATION-BRING-UP-CHECKLIST-2026-04-23.md` instead of reopening first-run planning. |  |  |
| TASK-009 | Maintain a rerun path for service regression using `docs/architecture/SERVICE-HOST-INSTALLED-PROOF-CHECKLIST-2026-04-23.md` and `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md` as the current local evidence floor. |  |  |
| TASK-010 | Keep backup and restore readiness operational by rerunning the local/offsite Restic validation from `docs/architecture/OLARES-FIRST-STORAGE-BRING-UP-RUNBOOK-2026-04-23.md` on a defined cadence after host, storage, or credential drift. |  |  |
| TASK-011 | Preserve the documented limitation that the supported Settings API does not currently manage Helm-installed `forms-engine` and `p6-ingest` aliases due to missing `ApplicationManager` resources; route future alias work through explicit platform packets rather than ad hoc retries. |  |  |
| TASK-011A | Preserve the bounded private personal lane through `ops/agents/handoffs/2026-05-01-olares-private-stack-browser-terminal-bring-up-handoff.md`, `docs/architecture/OLARES-PRIVATE-STACK-BLUEPRINT-2026-05-01.md`, `docs/architecture/OLARES-PRIVATE-STACK-FIRST-RUN-CHECKLIST-2026-05-01.md`, `infra/private/run-personal-stack-remote.ps1`, and `infra/private/personal-notes-backup-schedule.ps1`; keep it host-only or mesh-tunneled, with local snapshot backup/restore, workstation-held backup export, workstation-mediated offsite mirror, daily backup automation, and no silent promotion into the governed installed-app set or public ingress. | ✅ | 2026-05-02 |
| TASK-011B | Execute `ops/agents/packets/draft/2026-05-02-olares-private-003-host-owned-encrypted-offsite-backup-execution.json` to land the governed helper surfaces for host-owned encrypted offsite backup and restore-drill hardening over the existing Notes archive root. That lane is now closed with live proof: the helper wrote the host-local env file, `status` confirmed the existing Backblaze-backed Restic repository is reachable, `init` confirmed it was already initialized, `backup` wrote a fresh tagged Notes snapshot, and `restore-drill` recovered and validated that snapshot in the isolated drill root without touching the live Notes runtime. | ✅ | 2026-05-02 |
| TASK-011C | Execute `ops/agents/packets/draft/2026-05-02-olares-private-004-host-owned-offsite-backup-automation-execution.json` to add a bounded host-native recurring cadence for the already-live encrypted offsite lane. That lane is now closed with live proof: the helper deployed `/home/olares/code/personal/run-personal-notes-offsite-backup-host.sh`, installed `apex-personal-notes-offsite-backup.service` plus `apex-personal-notes-offsite-backup.timer`, registered daily `03:30 UTC` execution, and `run-now` completed successfully with Restic snapshot `76b8155c` and retention prune. | ✅ | 2026-05-02 |
| TASK-011D | Execute `ops/agents/packets/draft/2026-05-02-olares-private-005-restore-drill-cadence-and-timer-hardening-execution.json` to add recurring restore-drill automation and harden the deployed backup timer behavior. That lane is now closed with live proof: the shared helper now supports `backup` and `restore-drill` profiles, the deployed backup unit has `RandomizedDelaySec=20m`, `StartLimitIntervalSec=6h`, `StartLimitBurst=2`, and rotated append-only file logs, and the new weekly restore-drill timer completed a live `run-now` that restored snapshot `76b8155c` into the isolated drill root while validating recovered archive integrity. | ✅ | 2026-05-02 |

### Implementation Phase 3

- GOAL-003: Keep future Olares work tightly gated so the repo does not regress into an always-open infrastructure frontier.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-012 | Reopen Olares execution only if one of the explicit regressions occurs: private access failure, storage or backup regression, installed-route regression, or intentionally approved new host/app capability scope. |  |  |
| TASK-013 | Keep GitHub canonical and treat `docs/architecture/GIT-HOSTING-AND-GITEA-TRANSITION-CHECKLIST-2026-04-23.md` as the gating checklist for any mirror-only or future canonical-hosting proposal. |  |  |
| TASK-014 | Require a new packet before onboarding any new Olares-installed service beyond `forms-engine` and `p6-ingest`. |  |  |
| TASK-015 | Require a new packet before changing auth posture, public exposure, or canonical publication behavior for Olares-hosted services. |  |  |
| TASK-015A | Require a new packet before promoting the private personal lane into an Olares-installed app, shared-auth surface, or public route. |  |  |
| TASK-015B | Use `ops/agents/packets/draft/2026-05-01-olares-private-001-private-lane-promotion-gate-planning.json` as the first explicit planning packet for any future decision to promote the private personal lane beyond its current host-only or mesh-tunneled posture. That packet is now executed and its current ruling is recorded in `ops/agents/handoffs/2026-05-01-olares-private-001-promotion-gate-planning-handoff.md`: keep the lane private unless a later implementation packet intentionally opens one specific promotion path. | ✅ | 2026-05-01 |
| TASK-015C | Use `ops/agents/packets/draft/2026-05-02-olares-private-002-backup-governance-hardening-planning.json` as the next explicit planning packet for any future move from the current host-local snapshot, workstation-held export, workstation-mediated offsite mirror, and bounded daily automation posture toward stronger backup governance. That packet is now executed and its ruling is recorded in `ops/agents/handoffs/2026-05-02-olares-private-002-backup-governance-hardening-planning-handoff.md`: keep the runtime private, but approve a later implementation packet for host-owned encrypted offsite backup and restore-drill hardening before any wider promotion path. | ✅ | 2026-05-02 |

### Implementation Phase 4

- GOAL-004: Align Olares follow-on work to the repo’s broader platform priorities rather than treating Olares itself as the active delivery epic.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-016 | Keep the Olares roadmap subordinate to broader platform execution priorities named in `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`: bounded source-domain re-home, `apps/operations-web` promoted-host browser proof, and lane-marker normalization. |  |  |
| TASK-017 | Use Olares reruns only when those broader platform lanes depend on host validation, installed service regression checks, or future approved host-scope additions. |  |  |
| TASK-018 | Update this roadmap only when a new Olares packet is opened or when a dated closure, regression, or hosting decision materially changes the live Olares boundary. |  |  |

### Implementation Phase 5

- GOAL-005: Create a bounded assessment lane for a possible future Olares One dev-workspace expansion without reopening generic Olares implementation.

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-019 | Assess the current Olares platform state against the intended three-zone design in `C:/APEX Platform/Infrastructure/Olares_Workspace_Authority_Framework.md` and `C:/APEX Platform/Infrastructure/Olares_Build_Guide.md`, including dev-zone, services-zone, and staging-zone reality versus design intent. Recorded in `ops/agents/handoffs/2026-05-03-olares-phase-5-step-1-dev-workspace-state-and-access-assessment-handoff.md`. | ✅ | 2026-05-03 |
| TASK-020 | Assess the current trusted access model for daily development on the Olares One, including private-mesh SSH, VS Code Remote-SSH, browser-terminal fallback, and whether the present path is credible as the primary editing posture for APEX work. Recorded in `ops/agents/handoffs/2026-05-03-olares-phase-5-step-1-dev-workspace-state-and-access-assessment-handoff.md`. | ✅ | 2026-05-03 |
| TASK-021 | Assess whether the current repo authority and publication model can support an Olares-first daily development posture without changing the parent git root, and document the remaining friction between `C:/APEX Platform` as publication boundary and the Olares-hosted repo clone as implementation surface. Closed by `ops/agents/handoffs/2026-05-03-olares-phase-5-post-005-reconciliation-handoff.md` with a negative readiness verdict: Packet 004 restored trusted SSH and Packet 005 captured host clone evidence, but the host clone `/home/olares/src/apex-power-ops-platform` is older, dirty, and remote-divergent from the workstation publication boundary at `C:/APEX Platform`. Technical SSH viability is real; repo-authority readiness is not. A later bounded repo-clone reconciliation packet is warranted before any Olares-first daily development migration packet. | ✅ | 2026-05-03 |
| TASK-022 | Assess the intended AI toolchain shape on Olares against current repo truth, including Claude Code, Codex, local models, MCP fabric, `apex-jobs` ledger expectations, and the existing AI orchestration protocol under `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md`. Recorded in `ops/agents/handoffs/2026-05-03-olares-phase-5-step-2-ai-toolchain-and-codex-role-assessment-handoff.md`. | ✅ | 2026-05-03 |
| TASK-023 | Assess the intended services-zone stack for AI orchestration and supporting tools on Olares, including Ollama, Open WebUI, Dify, n8n, Qdrant, Syncthing, Restic, and optional Gitea, and classify each as current-state, design-intent, deferred, or not yet governed. Closed by `ops/agents/handoffs/2026-05-03-olares-phase-5-post-005-reconciliation-handoff.md` as an assessment with residual risks: Packet 005 directly inventoried Docker, K3s, Helm, installed apps, ports, volumes, networks, and timer surfaces; `forms-engine` and `p6-ingest` are running as Olares Applications, Deployments, Services, Pods, and Helm releases; host Docker has real `apex-dev`, `private`, and `windows-lab` projects; private-lane backup and restore-drill timers are enabled. Residual risks remain: broader AI-service entries are AppImage catalog/design intent rather than observed running Applications; `forms-engine` and `p6-ingest` AppImage CRs report `failed` while runtime surfaces are healthy; the missing Gitea transition gate remains unresolved. | ✅ | 2026-05-03 |
| TASK-024 | Assess the correct role of Codex in the Olares-hosted workflow using the unresolved orchestration questions already present in `.claude/DECISION_LOG.md`, and produce a bounded recommendation for when Codex should be local executor, remote batch worker, or left out of the first expansion slice. Recorded in `ops/agents/handoffs/2026-05-03-olares-phase-5-step-2-ai-toolchain-and-codex-role-assessment-handoff.md`. | ✅ | 2026-05-03 |
| TASK-025 | Assess whether a future Olares One dev-workspace expansion should be treated as: (a) workstation-only migration, (b) AI-services-zone expansion, (c) Gitea or code-hosting mirror enhancement, or (d) a broader canonical-hosting transition, and explicitly keep those decisions split instead of collapsing them into one “move to Olares” bucket. Closed by `ops/agents/handoffs/2026-05-03-olares-phase-5-post-005-reconciliation-handoff.md` as a split-path assessment: (a) is technically reachable but not repo-authority ready, (b) is not supported by observed running AI services and remains blocked by Step 2 decisions, (c) is blocked by missing hosting authority plus host clone divergence, and (d) remains no-go. None of (a), (b), (c), or (d) is currently READY. | ✅ | 2026-05-03 |
| TASK-026 | Produce a packet-ready decision surface for future Olares expansion containing: current-state findings, intended-design findings, gap classification, recommended smallest next packet, explicit no-go items, and a statement of what remains GitHub-canonical versus Olares-hosted only. Closed by `ops/agents/handoffs/2026-05-03-olares-phase-5-step-3-expansion-decision-surface-handoff.md`; later refined by Packet 003 research in `ops/agents/handoffs/2026-05-03-olares-phase-5-003-termpass-needslogin-blocker-audit-and-recovery-path-research-handoff.md`, which recommends an interactive local LarePass profile-rehydration and mesh-validation packet first, with browser-terminal host inventory as the explicit fallback. | ✅ | 2026-05-03 |

## 3. Alternatives

- **ALT-001**: Update `C:/APEX Platform/Infrastructure/Olares_MVP_Execution_Roadmap.md` as the only roadmap surface. Rejected because that file is retained as sequencing context and is not the best repo-local execution surface for post-closure status tracking.
- **ALT-002**: Treat the Olares lane as still actively open and continue running generic bring-up tasks. Rejected because the 2026-04-25 transition decision explicitly closes the first governed Olares lane.
- **ALT-003**: Collapse all Olares follow-on work into the general workspace roadmap with no dedicated Olares plan. Rejected because the repo still needs one bounded planning surface for regression, scope gating, and future packet triggers.
- **ALT-004**: Reopen generic Olares implementation immediately to start migrating daily development, AI tooling, and hosting onto the One. Rejected because the current need is assessment and packet-ready scoping, not unconstrained execution.

## 4. Dependencies

- **DEP-001**: `C:/APEX Platform/Infrastructure/APEX_Platform_Operating_Model_and_Governance.md`
- **DEP-002**: `C:/APEX Platform/Infrastructure/Olares_Workspace_Authority_Framework.md`
- **DEP-003**: `C:/APEX Platform/Infrastructure/Olares_MVP_Execution_Roadmap.md`
- **DEP-004**: `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md`
- **DEP-004A**: `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-05-01-olares-private-stack-browser-terminal-bring-up-handoff.md`
- **DEP-005**: `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-04-25-olares-workstation-001-publication-follow-through-scope-handoff.md`
- **DEP-006**: `C:/APEX Platform/apex-power-ops-platform/ops/agents/handoffs/2026-04-25-olares-workstation-002-publication-follow-through-blocker-handoff.md`
- **DEP-007**: `C:/APEX Platform/apex-power-ops-platform/docs/architecture/OLARES-WORKSTATION-BRING-UP-CHECKLIST-2026-04-23.md`
- **DEP-008**: `C:/APEX Platform/apex-power-ops-platform/docs/architecture/SERVICE-HOST-INSTALLED-PROOF-CHECKLIST-2026-04-23.md`
- **DEP-009**: `C:/APEX Platform/apex-power-ops-platform/docs/architecture/OLARES-WORKSTATION-BRING-UP-CHECKLIST-2026-04-23.md`
- **DEP-010**: `C:/APEX Platform/apex-power-ops-platform/docs/architecture/SERVICE-HOST-INSTALLED-PROOF-CHECKLIST-2026-04-23.md`
- **DEP-011**: `C:/APEX Platform/Infrastructure/Olares_Build_Guide.md`
- **DEP-012**: `C:/APEX Platform/.claude/DECISION_LOG.md`
- **DEP-013**: `C:/APEX Platform/Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md`
- **DEP-014**: `C:/APEX Platform/apex-power-ops-platform/docs/architecture/TCC-RELAY-GOVERNANCE-INDEX-2026-05-03.md`

## 5. Files

- **FILE-001**: `plan/infrastructure-olares-full-implementation-roadmap-1.md` - repo-local post-closure roadmap for current Olares status, attention items, and next-step gates.
- **FILE-002**: `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md` - current local evidence floor for restored runtime, canary, chart, and rerun surfaces.
- **FILE-002A**: `ops/agents/handoffs/2026-05-01-olares-private-stack-browser-terminal-bring-up-handoff.md` - current local evidence floor for the bounded private personal lane, restored mesh SSH path, tested backup/restore, and one-command status proof surface.
- **FILE-003**: `ops/agents/handoffs/2026-04-25-olares-workstation-001-publication-follow-through-scope-handoff.md` - surviving publication-scope evidence for workstation follow-through.
- **FILE-004**: `ops/agents/handoffs/2026-04-25-olares-workstation-002-publication-follow-through-blocker-handoff.md` - surviving blocker evidence for the broader workstation publication packet.
- **FILE-005**: `docs/architecture/OLARES-WORKSTATION-BRING-UP-CHECKLIST-2026-04-23.md` - rerun and regression checklist for workstation scope.
- **FILE-006**: `docs/architecture/SERVICE-HOST-INSTALLED-PROOF-CHECKLIST-2026-04-23.md` - rerun and regression checklist for installed-service scope.
- **FILE-007**: `docs/architecture/OLARES-FIRST-STORAGE-BRING-UP-RUNBOOK-2026-04-23.md` - rerun and recovery runbook for storage and backup scope.
- **FILE-008**: `docs/architecture/GIT-HOSTING-AND-GITEA-TRANSITION-CHECKLIST-2026-04-23.md` - hosting transition gate for any future mirror or canonical cutover proposal. NOTE 2026-05-03: file does not exist on disk in this workspace snapshot per the Step 3 expansion-decision-surface handoff; any TASK-013 or TASK-025 (c) work must first author or restate this gating authority before proceeding.
- **FILE-009**: `ops/agents/packets/draft/2026-05-01-olares-private-001-private-lane-promotion-gate-planning.json` - first explicit planning packet for any future private-lane promotion into public routing, shared auth, or installed-app posture.
- **FILE-010**: `ops/agents/handoffs/2026-05-01-olares-private-001-promotion-gate-planning-handoff.md` - executed planning decision record reaffirming that the private lane remains host-only or mesh-tunneled unless a later implementation packet opens a specific promotion path.
- **FILE-011**: `ops/agents/packets/draft/2026-05-02-olares-private-002-backup-governance-hardening-planning.json` - explicit planning packet for the next private-lane follow-on: stronger backup governance without widening auth, ingress, or installed-app posture.
- **FILE-012**: `ops/agents/handoffs/2026-05-02-olares-private-002-backup-governance-hardening-planning-handoff.md` - executed planning decision record approving host-owned encrypted offsite backup hardening as the next packetized follow-on while keeping the current runtime posture unchanged.
- **FILE-013**: `ops/agents/packets/draft/2026-05-02-olares-private-003-host-owned-encrypted-offsite-backup-execution.json` - bounded implementation packet for the host-owned encrypted offsite helper and restore-drill lane.
- **FILE-014**: `ops/agents/handoffs/2026-05-02-olares-private-003-host-owned-encrypted-offsite-backup-execution-handoff.md` - implementation handoff recording the landed helper surfaces plus the live `status`, `init`, `backup`, and `restore-drill` proof against the existing Backblaze-backed Restic repository.
- **FILE-015**: `infra/private/run-personal-notes-offsite-backup-remote.ps1` plus `infra/private/.env.personal-offsite-backup.template` - governed operator surface and machine-local template for host-owned encrypted offsite backup, retention, and restore-drill operations, now proven live on the real host.
- **FILE-016**: `ops/agents/packets/draft/2026-05-02-olares-private-004-host-owned-offsite-backup-automation-execution.json` - bounded implementation packet for host-native recurring automation over the already-live encrypted offsite lane.
- **FILE-017**: `ops/agents/handoffs/2026-05-02-olares-private-004-host-owned-offsite-backup-automation-execution-handoff.md` - implementation handoff recording the landed host runner, systemd service and timer, and live `install`, `status`, and `run-now` proof.
- **FILE-018**: `infra/private/run-personal-notes-offsite-backup-host.sh` plus `infra/private/personal-notes-offsite-backup-schedule.ps1` - governed host-native runner and operator helper for recurring encrypted offsite backup cadence through systemd on the Olares host.
- **FILE-019**: `ops/agents/packets/draft/2026-05-02-olares-private-005-restore-drill-cadence-and-timer-hardening-execution.json` - bounded implementation packet for weekly restore-drill cadence and deployed timer hardening over the live encrypted offsite lane.
- **FILE-020**: `ops/agents/handoffs/2026-05-02-olares-private-005-restore-drill-cadence-and-timer-hardening-execution-handoff.md` - implementation handoff recording the restore-drill timer, live drill proof, and deployed backup timer hardening fields.
- **FILE-021**: `infra/private/run-personal-notes-offsite-restore-drill-host.sh` plus the updated `infra/private/personal-notes-offsite-backup-schedule.ps1` - governed host-native restore-drill runner and multi-profile operator helper for recurring encrypted offsite backup and recovery proof cadence through systemd on the Olares host.
- **FILE-022**: `.claude/DECISION_LOG.md` - unresolved orchestration and Codex-role questions that must be reconciled before AI-toolchain expansion on Olares is packetized.
- **FILE-023**: `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md` - existing orchestration-role and handoff model that future Olares-hosted agent tooling must either reuse or explicitly supersede.
- **FILE-024**: `Infrastructure/Olares_Build_Guide.md` - intended blue-sky design for services-zone, AI, MCP, and remote-workspace posture.
- **FILE-025**: `ops/agents/packets/draft/2026-05-03-olares-phase-5-001-access-and-runtime-revalidation.json` - the authored access-and-runtime revalidation packet. Its shape remains valid for runtime inventory, but it closed partial because access remained blocked and host runtime could not be directly inspected.
- **FILE-026**: `ops/agents/handoffs/2026-05-03-olares-phase-5-step-2-ai-toolchain-and-codex-role-assessment-handoff.md` - bounded assessment record for the intended Olares AI toolchain shape and Codex role, concluding that Claude Code is the only first-slice-ready AI surface and Codex remains excluded pending trust-boundary and authority closure.
- **FILE-027**: `ops/agents/handoffs/2026-05-03-olares-phase-5-next-task-and-prompt-routing-handoff.md` - copy-paste routing surface updated through Packet 004 completion and pointing to Packet `2026-05-03-olares-phase-5-005`; now superseded by Packet 005 execution evidence in FILE-036.
- **FILE-028**: `ops/agents/handoffs/2026-05-03-olares-phase-5-001-access-and-runtime-revalidation-handoff.md` - Packet 001 closure handoff (status `partial`); private-mesh access was blocked and host runtime was not directly inspected at that point. NOTE 2026-05-03: Packet 004 restored mesh SSH and Packet 005 satisfied the host-runtime inventory gap through direct Olares host inspection.
- **FILE-029**: `ops/agents/handoffs/2026-05-03-olares-phase-5-step-3-expansion-decision-surface-handoff.md` - Step 3 packet-ready decision surface synthesizing Step 1, Step 2, and Packet 001; closes TASK-026; preserves the four-way TASK-025 split with per-path readiness; documents GitHub-canonical versus Olares-hosted-only boundary; recommends a bounded access-recovery packet as the smallest next move.
- **FILE-030**: `ops/agents/packets/draft/2026-05-03-olares-phase-5-002-access-recovery-and-runtime-inventory.json` - the authored access-recovery packet. It closed blocked after the local TermiPass path remained `NeedsLogin` with zero node key, no mesh IP, and no usable `100.64.*` route, so no host runtime inventory was captured.
- **FILE-031**: `ops/agents/packets/draft/2026-05-03-olares-phase-5-003-termpass-needslogin-blocker-audit-and-recovery-path-research.json` - completed research packet. It closed on 2026-05-03 with the ruling that the likely blocker is local LarePass or TermiPass profile state rather than basic Headscale reachability, reinforced by an official Olares source cross-check; it also tightened the config evidence the next packet must capture.
- **FILE-032**: `ops/agents/packets/draft/2026-05-03-olares-phase-5-004-interactive-larepass-profile-rehydration-and-mesh-validation.json` - preferred execution packet authored from the Packet 003 result and executed on 2026-05-03. It restored the workstation private mesh through operator-mediated LarePass profile rehydration and validated `olares-mesh` SSH over `100.64.0.1`; host runtime inventory remains a separate follow-on.
- **FILE-033**: `ops/agents/packets/draft/2026-05-03-olares-phase-5-004b-browser-terminal-host-runtime-inventory.json` - explicit fallback next packet authored from the Packet 003 result for the case where operator interaction is unavailable and the immediate need is host runtime truth through authenticated browser-terminal access.
- **FILE-034**: `ops/agents/handoffs/2026-05-03-olares-phase-5-004-interactive-larepass-profile-rehydration-and-mesh-validation-handoff.md` - Packet 004 closure handoff (status `complete - pass`); TermiPass moved to `BackendState: Running`, workstation mesh IP `100.64.0.2`, Headscale shows node ID `2` online for `Jason_Swenson`, `100.64.0.1:22` succeeds over `TermiPass`, and `olares-mesh` SSH is viable. It recommends a narrow SSH-based host runtime inventory packet next and keeps Olares-first daily development, services-zone expansion, Gitea, and canonical-hosting decisions separate.
- **FILE-035**: `ops/agents/packets/draft/2026-05-03-olares-phase-5-005-ssh-host-runtime-inventory.json` - authored execution packet for read-only host runtime inventory over the restored mesh SSH path, including Docker, K3s or Helm, installed-app, private-lane timer, and host repo-clone evidence without host mutation.
- **FILE-036**: `ops/agents/handoffs/2026-05-03-olares-phase-5-005-ssh-host-runtime-inventory-handoff.md` - Packet 005 closure handoff (status `complete - pass`); mesh SSH remained healthy, host fingerprint matched the trusted ED25519 fingerprint, Docker/K3s/Helm/app/port/volume/network/timer evidence was directly captured, Packet 001's inventory gap is now satisfied, VS Code Remote-SSH is technically viable through `olares-mesh`, and post-005 reconciliation is warranted before any migration, services-zone expansion, Gitea, or canonical-hosting packet opens.
- **FILE-037**: `ops/agents/handoffs/2026-05-03-olares-phase-5-post-005-reconciliation-handoff.md` - post-005 repo-authority reconciliation handoff; closes TASK-021, TASK-023, and TASK-025 as assessments only, keeps all migration/AI-services/Gitea/canonical-hosting paths not ready, classifies the `forms-engine` and `p6-ingest` AppImage CR mismatch as governance/documentation mismatch rather than runtime failure, and recommends a later bounded repo-clone reconciliation planning packet.
- **FILE-038**: `ops/agents/handoffs/2026-05-03-olares-phase-5-006-host-repo-clone-reconciliation-planning-handoff.md` - Packet 006 planning handoff; decides that `/home/olares/src/apex-power-ops-platform` should be preserved as historical runtime evidence rather than refreshed in place or promoted as the intended dev path, retires the old 2026-04-25 packet-002 publication scope as an execution lane, and narrows any later implementation packet to separate canonical host dev path preparation while keeping migration, AI-services expansion, Gitea/code-hosting, and canonical-hosting paths not ready.
- **FILE-039**: `ops/agents/handoffs/2026-05-03-olares-phase-5-007-canonical-host-dev-path-preparation-handoff.md` - Packet 007 bounded host-path preparation handoff; preserves `/home/olares/src/apex-power-ops-platform` intact as historical runtime evidence, prepares `/home/olares/code/apex` as a clean `clean-main` clone of the GitHub-canonical parent repository `jasonlswenson-sys/RESA-Power-Project-Management.git`, validates the implementation surface at `/home/olares/code/apex/apex-power-ops-platform` over `olares-mesh`, and concludes the path supports a narrow readiness reassessment but not migration until authority restatement and a bounded host dev-loop smoke test pass.
- **FILE-040**: `ops/agents/handoffs/2026-05-03-olares-phase-5-post-007-readiness-reassessment-handoff.md` - post-007 authority reassessment handoff; confirms `/home/olares/code/apex` as the correct host parent-root mirror, records the landed authority-doc restatement in `Infrastructure/Olares_Workspace_Authority_Framework.md` and `Infrastructure/Olares_Build_Guide.md`, keeps TASK-021, TASK-023, and TASK-025 closed with no readiness upgrade, and concludes that the next truthful move is a bounded host dev-loop smoke validation packet.
- **FILE-041**: `ops/agents/packets/draft/2026-05-03-olares-phase-5-008-canonical-host-dev-loop-smoke-validation.json` - authored validation packet for bounded host dev-loop proof against `/home/olares/code/apex`, including mesh reachability, workspace-open evidence, repo-parity checks, and basic editing ergonomics without reopening migration, mutating the preserved old clone, or changing services.
- **FILE-042**: `ops/agents/handoffs/2026-05-03-olares-phase-5-008-canonical-host-dev-loop-smoke-handoff.md` - Packet 008 bounded smoke-validation handoff; confirms `/home/olares/code/apex` remains reachable over `olares-mesh`, clean at committed HEAD `0926fb369d32fd4a98db9e6afb4e3adc9b8717f3`, correctly rooted as the host parent mirror, and usable for equivalent workspace-open and terminal/file-navigation ergonomics, while recording that current uncommitted Phase 5 authority artifacts remain workstation-only until published or synchronized. It supports a later narrow migration readiness reassessment after repo-parity housekeeping, but keeps migration, AI-services expansion, Gitea/code-hosting, and canonical-hosting not ready.
- **FILE-043**: `ops/agents/handoffs/2026-05-03-olares-phase-5-post-008-migration-readiness-reassessment-handoff.md` - post-008 authority reassessment handoff; concludes that Packet 008 closed the bounded host-validation question and that the remaining blocker is now repo-parity and publication-state governance, not host-path viability. It keeps migration, AI-services expansion, Gitea/code-hosting, and canonical-hosting not ready and routes the lane to repo-parity housekeeping plus migration-gate planning.
- **FILE-044**: `ops/agents/packets/draft/2026-05-03-olares-phase-5-009-post-smoke-repo-parity-housekeeping-and-migration-gate-planning.json` - authored planning packet for classifying current workstation-only Phase 5 artifacts into commit/publish, defer, or comparison-only buckets and defining what publication-state conditions must be satisfied before any later workstation-migration readiness reassessment opens.
- **FILE-045**: `ops/agents/handoffs/2026-05-03-olares-phase-5-009-post-smoke-repo-parity-housekeeping-and-migration-gate-planning-handoff.md` - Packet 009 planning closure handoff; writes the repo-parity gate explicitly by classifying current Phase 5 handoffs, packet JSON files, roadmap/routing updates, and authority-doc restatements as the minimum bounded commit/publish set; defers implementation scaffolding, AI-services, Gitea/code-hosting, canonical-hosting, service mutation, ingress, and auth work; keeps the old `/home/olares/src/apex-power-ops-platform` clone and older 2026-04-25 packet records as comparison-only evidence; and concludes that a later workstation-migration readiness reassessment is only conditionally warranted after parent-root publication plus `/home/olares/code/apex` host-mirror synchronization.
- **FILE-046**: `ops/agents/packets/draft/2026-05-03-olares-phase-5-010-parent-root-publication-and-host-mirror-sync-gate.json` - authored execution packet for the next bounded repo-parity follow-through; requires a limited parent-root publication commit from `C:/APEX Platform`, excludes unrelated parent-root changes and deferred implementation scaffolding, synchronizes only `/home/olares/code/apex` through a non-destructive fast-forward-only method, preserves `/home/olares/src/apex-power-ops-platform` as historical evidence, and records whether the repo-parity gate is then satisfied strongly enough to permit a later separate workstation-migration readiness reassessment.

## 6. Testing

- **TEST-001**: Verify that the roadmap’s closed-baseline statements match `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md` and the surviving 2026-04-25 scope/blocker handoffs.
- **TEST-002**: Verify that the roadmap’s workstation status does not claim publication state that the blocker handoff explicitly leaves open.
- **TEST-003**: Verify that the roadmap’s service status matches the current runtime and canary evidence floor described in `ops/agents/handoffs/2026-05-01-olares-runtime-surface-restoration-handoff.md`.
- **TEST-004**: Verify that the roadmap preserves the Settings API limitation boundary captured in the 2026-05-01 restoration handoff.
- **TEST-005**: Verify that the roadmap preserves the private-lane boundary as host-only or mesh-tunneled and does not imply governed installed-app or public-ingress promotion.
- **TEST-006**: Verify that no roadmap task reopens Olares bring-up without satisfying the reopen criteria listed in the post-closure checklist.
- **TEST-007**: Verify that Phase 5 tasks remain assessment-only and do not silently authorize new host installs, public exposure, code-hosting changes, or canonical-hosting transition.
- **TEST-008**: Verify that Phase 5 keeps workstation migration, AI-services expansion, orchestration design, and code-hosting questions split into separate decision surfaces rather than one blended “move to Olares” task.

## 7. Risks & Assumptions

- **RISK-001**: Operators may continue using the older MVP roadmap as if it were the live frontier and accidentally reopen already-closed first-run tasks.
- **RISK-002**: Repo publication ambiguity may cause confusion between workstation-proven surfaces and authoritative branch state until TASK-007 is completed.
- **RISK-003**: The supported Settings API gap for Helm-managed apps may be misread as a service failure even though the friendly aliases are already live.
- **RISK-004**: Gitea installation on the workstation could be misinterpreted as canonical hosting transition before the required governance packet exists.
- **RISK-005**: The bounded private personal lane could be misread as an approved new Olares-installed app or public service if its host-only and mesh-tunneled boundary is not kept explicit in roadmap updates.
- **RISK-006**: The desired Olares One dev-workspace expansion could be misread as already approved implementation if assessment tasks are not clearly marked as packet-preparatory only.
- **RISK-007**: AI toolchain exploration could collapse distinct questions about Claude Code, Codex, local models, Dify, n8n, MCP, and Gitea into one vague lane, producing architecture drift instead of a packet-ready decision surface.
- **RISK-008**: The old Olares host clone could be misread as the future canonical dev surface because SSH and VS Code Remote-SSH are technically viable, even though Packet 006 classifies that clone as stale evidence to preserve and replace later rather than refresh in place.
- **RISK-009**: The newly prepared `/home/olares/code/apex` path could be misread as migration approval even though Packet 007 only validates a bounded parent-root mirror and explicitly keeps daily-development migration, AI-services expansion, Gitea/code-hosting, and canonical-hosting not ready.
- **RISK-010**: Even after authority restatement, path reachability and parent-root mirror correctness could be misread as practical daily-development readiness before a bounded host dev-loop smoke packet proves workspace-open behavior, repo parity, and basic editing ergonomics on the prepared host path.
- **RISK-011**: Packet 008 proves the prepared host mirror is reachable, clean, and ergonomically viable at the committed parent-root HEAD, but current uncommitted workstation-only Phase 5 artifacts are not yet present on `/home/olares/code/apex`; any later migration reassessment that ignores this publication gap could treat the host mirror as more current than it is.
- **RISK-012**: Once host-path viability is proven, operators may prematurely skip the repo-parity gate and treat workstation-only handoffs, packet JSON files, and authority-doc edits as if they were already committed and synchronized authority on the prepared host mirror.
- **RISK-013**: If the Packet 009 publication set is committed with unrelated parent-root changes or synchronized to `/home/olares/code/apex` before the GitHub-canonical publication boundary advances, the host mirror could become technically current but governance-ambiguous.
- **ASSUMPTION-001**: The restored 2026-05-01 handoff plus the surviving 2026-04-25 scope/blocker handoffs remain the correct evidence floor unless later regression evidence supersedes them.
- **ASSUMPTION-002**: The 2026-05-01 private-lane runtime, tunnel access, backup, restore, and status proof remain valid unless later host or access regression evidence supersedes them.
- **ASSUMPTION-003**: Broader platform execution remains the primary repo frontier, so Olares follow-on work stays subordinate unless new host scope is explicitly approved.
- **ASSUMPTION-004**: The right immediate next move for Olares expansion is assessment and packetization, not direct migration of the daily APEX development center of gravity.
- **ASSUMPTION-005**: Any later host dev path implementation must preserve the parent-root publication boundary or explicitly restate it before the new path is treated as daily-development-ready.
- **ASSUMPTION-006**: The controlling infrastructure docs now restate `/home/olares/code/apex` as the Olares host parent-root mirror of `C:/APEX Platform`, with active implementation under `/home/olares/code/apex/apex-power-ops-platform`; any later smoke or migration reassessment must preserve that meaning.
- **ASSUMPTION-007**: Packet 008 establishes enough host dev-loop evidence to justify a later narrow migration readiness reassessment, but only after repo-parity housekeeping determines how the current Phase 5 handoffs, packet JSON, and authority-doc changes should be committed, published, and synchronized into the prepared host parent-root mirror.
- **ASSUMPTION-008**: The next truthful lane after Packet 008 is repo-parity housekeeping and migration-gate planning; no later workstation-migration readiness reassessment should run until that publication-state model is explicitly written.
- **ASSUMPTION-009**: Packet 009 closes the planning question by defining the publication-state gate; the smallest truthful next packet is bounded parent-root publication and `/home/olares/code/apex` host-mirror synchronization, after which a separate workstation-migration readiness reassessment may be considered without approving migration by default.

## 8. Related Specifications / Further Reading

- `C:/APEX Platform/Infrastructure/APEX_Platform_Operating_Model_and_Governance.md`
- `C:/APEX Platform/Infrastructure/Olares_Workspace_Authority_Framework.md`
- `C:/APEX Platform/Infrastructure/Olares_MVP_Execution_Roadmap.md`
- `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
- `docs/architecture/OLARES-WORKSTATION-BRING-UP-CHECKLIST-2026-04-23.md`
- `docs/architecture/SERVICE-HOST-INSTALLED-PROOF-CHECKLIST-2026-04-23.md`
- `docs/architecture/OLARES-PRIVATE-STACK-BLUEPRINT-2026-05-01.md`
- `docs/architecture/OLARES-PRIVATE-STACK-FIRST-RUN-CHECKLIST-2026-05-01.md`
- `docs/architecture/GIT-HOSTING-AND-GITEA-TRANSITION-CHECKLIST-2026-04-23.md`
- `.claude/DECISION_LOG.md`
- `Supabase/docs/AI_ORCHESTRATION_PROTOCOL.md`
