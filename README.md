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
- `PROJECT_OVERVIEW.md` for system architecture, scope, and platform intent.
- `WORKSPACE_PROTOCOL.md` for repo operating rules and decision discipline.
- `WORKSPACE_DESIGN.md` for workspace structure and repository organization.
- `ARCHIVE_NOTICE.md` for the boundary between active and retained historical material.

## Current Delivery Posture

- Active source-of-truth material lives in the root docs and non-archive directories.
- Legacy RESA naming may still appear inside historical docs, legacy file names, and archived materials where changing it would reduce traceability.
- GitHub Actions remains intentionally unconfigured until a single active build or test entrypoint is extracted from the live repo surface.

## Platform Snapshot

- Database: Supabase PostgreSQL
- App direction: Next.js 16 + React 19
- Domain: electrical testing operations, apparatus lifecycle management, and NETA-aligned workflows
- Adjacent scope: Power System Studies coordination and reporting
