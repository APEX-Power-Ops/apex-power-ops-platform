# NETA ETT Study Material

Certification exam preparation materials, platform planning, and governance artifacts for NETA Electrical Testing Technician Levels II, III, and IV.

This repository is now part of a broader unified technician platform effort that also includes the local `tcc_v5_backend` application repository. The repos remain separate, and the accepted daily operating model is one coordinated workspace with one documented governance contract.

---

## Start Here

Use this README as repository orientation, not as a parallel startup checklist.

For live session startup, defer to the governed hub-and-lane chain:

1. `GOVERNANCE-FRAMEWORK.md`
2. `Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md`
3. `Development/Control-Plane/EXECUTION-TASKS-CURRENT.md`
4. `Development/Control-Plane/SESSION-LANE-PROTOCOL.md`

After that chain, declare the active lane, primary repo, cross-repo seam, and working terminal root, then read the matching current lane resume before treating any supporting surface as current startup authority.

Use `MASTER-STANDARDS.md`, the relevant `Build-Specs/` document, and any needed architecture or platform surfaces only after the startup chain has routed the session into the correct lane.

Do not use `.claude/CURRENT_STATE.md` as an entry point. That workflow is obsolete and that file is not maintained.

---

## Repository Mission

The project serves two connected purposes:

1. Build durable exam-prep materials that teach electrical testing concepts, not just answers.
2. Provide the governance, data, and platform-planning layer for the larger Supabase-backed technician platform that now spans ETT content and TCC workflow work.

The operating philosophy remains the same: create lasting value, prefer systems over one-off fixes, and treat published standards as a floor rather than a ceiling.

---

## Current Operating Model

This repository is the accepted home for:

- ETT content and content infrastructure
- governance, standards, audits, and coordination docs
- build specifications and process guidance
- shared platform planning for the unified ETT + TCC direction

The local `tcc_v5_backend` repository remains the accepted home for:

- FastAPI application code
- TCC demo and backend implementation
- migrations, services, tests, and runtime wiring

The accepted baseline is one multi-root VS Code workspace, two repositories, and one shared platform contract.

For TCC-related work, the governed architecture source of truth is the paired authority stack in `Development/Architecture/TCC-MASTER-SCHEMA-AUTHORITY.md` and `Development/Architecture/TCC-DLL-ARCHITECTURE-AUTHORITY.md`. Backend implementation must align to that stack rather than creating its own competing interpretation.

Target-state workspace design:

- `Development/Architecture/WORKSPACE-TARGET-STATE.md` - end-state structure, documentation framework, and migration direction for the workspace model

---

## Top-Level Structure

| Path | Role |
| --- | --- |
| `Build-Specs/` | Authoritative implementation specs for study guides, staging, templates, tests, and infrastructure planning |
| `Development/` | Active control plane: task docs, audits, scripts, staging, migration planning, and coordination artifacts |
| `NETA-2/`, `NETA-3/`, `NETA-4/` | Student-facing or delivery-target content by certification level |
| `Process-Guides/` | Workflow references and legacy process documentation; use with the current governance model, not as a replacement for it |
| `Resources/` | Source materials, extractions, catalogs, and supporting reference assets |
| `Archive/` | Historical, superseded, deprecated, or reference-only material |

---

## Active Session Contract

### Primary control-plane documents

| Document | Purpose |
| --- | --- |
| `GOVERNANCE-FRAMEWORK.md` | Authority hierarchy, routing rules, checkpoint model, and escalation |
| `MASTER-STANDARDS.md` | Structural and formatting standards |
| `Development/Control-Plane/GOVERNANCE-SESSION-RESUME.md` | Current platform/content state and recent decisions |
| `Development/Control-Plane/EXECUTION-TASKS-CURRENT.md` | Active execution task queue |
| `Development/Control-Plane/SESSION-LANE-PROTOCOL.md` | Startup lane declaration, lane switching, and resume-routing rules |
| `Development/Control-Plane/RESUME-ETT-CONTENT-CURRENT.md` | Current lane resume for ETT content and standards work |
| `Development/Control-Plane/RESUME-TCC-RUNTIME-CURRENT.md` | Current lane resume for TCC runtime and backend work |
| `Development/Control-Plane/RESUME-WORKSPACE-GOVERNANCE-CURRENT.md` | Current lane resume for workspace-governance and protocol work |
| `Development/Architecture/REPOSITORY-REGISTRY.md` | Repository boundaries, ownership, and local-path contract |
| `Development/Architecture/UNIFIED-PLATFORM-ARCHITECTURE.md` | Shared ETT + TCC platform model |
| `Development/Architecture/SHARED-PLATFORM-CONTRACT.md` | Explicit shared seam for tables, routes, ownership, and change coordination |

### Session-end expectation

When work materially changes state:

1. Update the relevant task doc or tracker in `Development/`.
2. Update platform or architecture docs if boundaries changed.
3. Log important governance or structure decisions in the active control-plane documents.
4. Preserve archive discipline instead of leaving superseded guidance in active paths.

---

## Current Program Focus

The accepted implementation baseline is the TCC demo path that completed readiness, persistence, integration, and release-hardening work against the shared Supabase seam.

Current active coordination surface:

- `Development/Control-Plane/EXECUTION-TASKS-CURRENT.md`

Current workspace buildout thread:

- unify governance, standards, organization, and protocol around the checked-in two-repository workspace model
- keep `neta-ett-study-material` as the governance/content home and `tcc_v5_backend` as the runtime implementation home
- harden shared-contract documentation before any broader structural consolidation

Program path and acceptance docs:

- `Development/Platform/NETA-DEMO-PROJECT-COMPLETION-PATH.md`
- `Development/Platform/NETA-DEMO-PROJECT-VERIFICATION-CHECKLIST.md`
- `Development/Platform/TCC/TCC-DEMO-TO-PRODUCTION-READINESS-LADDER.md`
- `Development/Platform/TCC/TCC-NAMESPACE-CLEANUP-CLOSEOUT-2026-03-21.md`

TCC namespace entry points:

- `Development/Platform/TCC/README.md`
- `Development/Platform/TCC/specs-and-staging/README.md`
- `Development/Platform/TCC/local-execution/README.md`

Workspace and integration audit:

- `Development/Audits/AUDIT-UNIFIED-WORKSPACE-TCC-INTEGRATION-2026-03-21.md`

---

## Content and Quality Standards

The detailed requirements still live in `Build-Specs/`, but the short version is unchanged:

- study guides must be technically accurate, structurally consistent, and useful beyond exam day
- practice tests must follow the defined format and analytics requirements
- content and platform work should improve portability, reuse, and future database alignment

Use the applicable spec before creating or revising deliverables. If a spec and current operating reality differ, follow the newer governance/task documents and correct the stale spec entry point rather than guessing.

---

## Multi-Repo Workspace Notes

The checked-in workspace file now supports a multi-root setup that includes this repository and the local TCC backend path:

- `.`
- `../Projects/tcc_v5_backend`

This checked-in workspace file is the standard daily entry point when both repositories are available on the local machine.

If the second folder does not exist on a given machine, remove or adjust that workspace entry locally. The source of truth for expected local repository layout is `Development/Architecture/REPOSITORY-REGISTRY.md`.

---

## Legacy Note

The `.claude/` folder is retained only as a historical artifact. Do not treat it as the active coordination system. Current work is coordinated from `Development/` under the governance framework.

---

Last updated: March 21, 2026
