# Olares Post-Closure Execution Checklist

Date: 2026-04-25
Status: Active bounded follow-through checklist
Scope: remaining Olares attention items after the first governed workstation and installed-service lanes closed

## Purpose

Use this checklist for the Olares work that remained intentionally open after the 2026-04-25 closure decision.

This checklist is not a first-run bring-up surface.

It exists to keep the remaining post-closure work bounded, executable, and separate from the broader platform roadmap.

## Authority And Status Baseline

Use these files first:

1. `ops/agents/handoffs/2026-04-25-olares-lane-authority-approval-and-transition-decision.md`
2. `plan/infrastructure-olares-full-implementation-roadmap-1.md`
3. `ops/agents/handoffs/2026-04-25-olares-workstation-001-dev-stack-and-mcp-validation-closure-handoff.md`
4. `ops/agents/handoffs/2026-04-25-olares-one-friendly-alias-and-ingress-follow-up-handoff.md`
5. `docs/architecture/OLARES-WORKSTATION-BRING-UP-CHECKLIST-2026-04-23.md`
6. `docs/architecture/SERVICE-HOST-INSTALLED-PROOF-CHECKLIST-2026-04-23.md`

Approved status baseline:

1. the first governed Olares workstation lane is closed
2. the first installed-proof lanes for `forms-engine` and `p6-ingest` are closed
3. the friendly alias cleanup lane is closed
4. Olares is not the current primary execution frontier for the repo

## Allowed Uses

Use this checklist when one of the following is true:

1. governed workstation-synced repo surfaces need publication follow-through
2. a workstation regression rerun is needed
3. an installed-service regression rerun is needed
4. backup or restore drift needs a bounded rerun
5. the Settings API limitation for Helm-managed apps needs to be preserved explicitly in nearby docs or packets

Do not use this checklist to claim:

1. that generic Olares bring-up is still open
2. that future services may be installed on Olares without a new packet
3. that GitHub canonical hosting has changed

## Checklist

### 1. Repo Publication Follow-Through

- [x] confirm which workstation-synced governed surfaces remain unpublished from the normal authoritative branch state using `ops/agents/handoffs/2026-04-25-olares-workstation-001-publication-follow-through-scope-handoff.md`
- [x] bound the local-only Olares and TCC authority-sync tranche for parent-root publication using `ops/agents/handoffs/2026-04-25-parent-root-olares-tcc-authority-surface-publication-handoff.md`
- [ ] publish or explicitly block only the bounded 11-file publication-control tranche described in `ops/agents/handoffs/2026-04-25-parent-root-olares-tcc-authority-surface-publication-handoff.md`
- [ ] publish only the bounded governed workstation surfaces that were explicitly synced to clear the host blocker, using `ops/agents/packets/draft/2026-04-25-olares-workstation-002-governed-surface-publication-follow-through.json`
- [ ] record the publication result in a dated handoff or existing closure note update
- [ ] do not treat workstation proof alone as equivalent to authoritative branch publication

Exit condition:

- the authority-sync tranche and the broader workstation-synced governed surfaces are each either published through the normal repo path or covered by an explicit blocker handoff

### 2. Workstation Regression Rerun Readiness

- [ ] keep `docs/architecture/OLARES-WORKSTATION-BRING-UP-CHECKLIST-2026-04-23.md` current as the rerun surface for private access, storage baseline, backup baseline, offline escrow, workstation-hosted compose, and governed MCP proof
- [ ] rerun the workstation lane only when private access, storage, backup, compose, or governed MCP evidence regresses
- [ ] record any rerun result in a dated handoff instead of reopening the original first-run packet informally

Exit condition:

- workstation regressions can be rerun through the existing checklist and closure stack without ambiguity

### 3. Installed-Service Regression Rerun Readiness

- [ ] keep `docs/architecture/SERVICE-HOST-INSTALLED-PROOF-CHECKLIST-2026-04-23.md` current as the rerun surface for `forms-engine` and `p6-ingest`
- [ ] use the 2026-04-25 installed-proof closure handoffs as the current evidence floor for both services
- [ ] rerun installed proof only when route health, installed behavior, chart drift, ingress drift, or host drift justifies it

Exit condition:

- installed-service regressions can be rerun through the existing checklist and closure records without restating first-run scope

### 4. Backup And Restore Operational Readiness

- [ ] keep `docs/architecture/OLARES-FIRST-STORAGE-BRING-UP-RUNBOOK-2026-04-23.md` as the authoritative rerun source for bounded backup and restore validation
- [ ] rerun local and offsite Restic smoke after storage, credential, host, or backup-target drift
- [ ] record the result in a dated handoff whenever the rerun materially changes the known recovery posture

Exit condition:

- local and offsite backup restore readiness remains evidence-backed after any meaningful drift

### 5. Helm-Managed Settings API Limitation Preservation

- [ ] preserve the known limitation that `forms-engine` and `p6-ingest` friendly aliases are live even though the supported Settings API lacks matching `ApplicationManager` resources for those Helm-managed apps
- [ ] do not route future alias work through ad hoc Settings API retries unless a new explicit packet is opened for that platform behavior
- [ ] cite `ops/agents/handoffs/2026-04-25-olares-one-friendly-alias-and-ingress-follow-up-handoff.md` when documenting this limitation elsewhere

Exit condition:

- operator docs and future packets do not misclassify the Settings API limitation as a reopened service failure

## Reopen Gate

Do not reopen generic Olares execution without a new explicit packet unless one of the following occurs:

1. private workstation access regresses
2. storage, backup, or restore proof regresses
3. installed `forms-engine` or `p6-ingest` routes regress on the real host
4. a new Olares host, install method, or Olares-scoped capability is intentionally approved

## Current Recommendation

1. treat this checklist as the bounded follow-through surface for the remaining Olares items
2. keep broader execution priority on the main platform roadmap
3. author a new explicit packet before any future Olares expansion beyond the closed baseline captured on 2026-04-25