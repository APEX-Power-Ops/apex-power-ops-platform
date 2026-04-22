# Apex Power Ops Platform Agent Instructions

This repository is the active local implementation surface for Apex Power Ops platform consolidation work.

## Primary Working Rule

Start here first:
- `C:/APEX Platform/apex-power-ops-platform`

Do not assume sibling legacy repositories are the default execution surface.

## Current Local Layout

The local machine is now organized under the APEX parent root:
- active platform repo: `C:/APEX Platform/apex-power-ops-platform`
- strategic authority lane: `C:/APEX Platform/Platform-Authority`
- source domains: `C:/APEX Platform/source-domains/`

Current source-domain paths:
- `C:/APEX Platform/source-domains/tcc_v5_backend`
- `C:/APEX Platform/source-domains/neta-ett-study-material`
- `C:/APEX Platform/source-domains/neta-forms`

These source domains remain useful, but they are no longer the default workspace entrypoints.

## Authority Order

When work touches structure, topology, or migration boundaries, consult sources in this order:

1. `C:/APEX Platform/Platform-Authority/`
2. `docs/authority/`
3. this repository's root `README.md`
4. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md`
5. source-domain docs only when a slice has not yet been re-homed

Do not let older source-repo conventions override current platform authority.

## Execution Rules

- treat this repo as the primary implementation target
- treat source-domain repos as bounded extraction and lineage lanes
- do not import sibling repos wholesale into this repo
- move only approved slices into `apps/`, `packages/`, `infra/`, `ops/`, `knowledge/`, `docs/`, or `archive/`
- keep archive-heavy and binary-heavy material out of active implementation paths unless a bounded decision explicitly promotes it

## Environment Rules

Preferred local Python environment:
- `C:/APEX Platform/apex-power-ops-platform/.venv`

If using workspace tasks, prefer the platform-local interpreter or set:
- `APEX_PLATFORM_PYTHON`

Use PowerShell and direct file reads as reliable fallbacks when shell tooling is uneven.

## Common Starting Reads

For a fresh GPT or agent session, read these first:
- `README.md`
- `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md`
- `docs/authority/`

If the work involves source-lane extraction, also inspect the relevant sibling lane under:
- `../source-domains/`

## Validation Preference

After making changes, prefer focused validation in this order:

1. the smallest relevant test slice
2. the narrowest lint or typecheck slice
3. a targeted runbook or smoke command
4. diff-only inspection if no executable validation exists

## Transition Intent

This repo should feel like the default home base even before final cutover.

That means:
- instructions should prefer platform-root paths
- new automation and docs should assume APEX-first layout
- old workspace files and stale source paths should be treated as transition residue