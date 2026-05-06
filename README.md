# Apex Power Ops

> **Unified repository for the Apex Power Ops platform, operating documentation, and Supabase-backed delivery assets**  
> Historical RESA-named artifacts remain in place where they preserve migration traceability or design history.

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](./PROJECT_STATUS.md)
[![Platform](https://img.shields.io/badge/platform-Supabase-green.svg)](https://supabase.com)
[![Framework](https://img.shields.io/badge/framework-Next.js%2016-black.svg)](https://nextjs.org)
[![License](https://img.shields.io/badge/license-Private-red.svg)]()

---

## Repository Purpose

Apex Power Ops is the operating system for electrical testing workflows, apparatus lifecycle coordination, NETA-aligned compliance work, and related Power System Studies delivery. This repository is the unified repo lane for the active platform direction, the governing documentation around it, and the archived migration context that still needs to stay attached to delivery decisions.

## Active Repo Lanes

- `Documentation/` holds application, workflow, and implementation documentation.
- `Supabase/` holds database-facing assets and platform work tied to the active PostgreSQL deployment.
- `spec/` holds structured requirements and future-state design material.
- `Sessions/` holds working-session output that still informs the current platform state.
- `Reference_Files/` holds supporting source material used by the active workstream.
- `_archive/` is intentionally historical and should not be treated as the default implementation lane.

## Start Here

- `PROJECT_STATUS.md` for current execution posture and delivery state.
- `apex-power-ops-platform/docs/architecture/OLARES-ONE-WORKSPACE-DESIGN-GOVERNANCE-AND-IMPLEMENTATION-PLAN-2026-05-06.md` for the current Olares workspace design constraints, governance rules, approved environment, tooling posture, and implementation plan.
- `apex-power-ops-platform/docs/OPERATOR-BOOTSTRAP-RUNBOOK.md` for the current operator entrypoints, including the durable-host bootstrap/status surface.
- `PROJECT_OVERVIEW.md` for system architecture, scope, and platform intent.
- `WORKSPACE_PROTOCOL.md` for historical workspace protocol context; current Olares governance is routed through the authority and runbook surfaces above.
- `WORKSPACE_DESIGN.md` for historical workspace design context; it is not the current Olares operating authority.
- `ARCHIVE_NOTICE.md` for the boundary between active and retained historical material.

## Current Delivery Posture

- Active source-of-truth material lives in the root docs and non-archive directories.
- Legacy RESA naming is expected only inside archived materials and intentionally retained historical references where changing it would reduce traceability.
- GitHub Actions remains intentionally unconfigured until a single active build or test entrypoint is extracted from the live repo surface.

## Current Olares Posture

- GitHub remains canonical and `C:/APEX Platform` remains the publication boundary.
- `/home/olares/code/apex` is the authoritative Olares host mirror and `/home/olares/code/apex/apex-power-ops-platform` is the active host implementation surface.
- The laptop is governed as a client-only surface; the historical host clone at `/home/olares/src/apex-power-ops-platform` remains observe-only.
- The current Olares-first operator boundary remains the minimal MCP trio: `apex-fs`, `apex-db`, and `apex-jobs`.

## Platform Snapshot

- Database: Supabase PostgreSQL
- App direction: Next.js 16 + React 19
- Domain: electrical testing operations, apparatus lifecycle management, and NETA-aligned workflows
- Adjacent scope: Power System Studies coordination and reporting
