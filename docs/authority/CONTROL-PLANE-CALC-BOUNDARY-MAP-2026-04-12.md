# Control Plane And Calc Boundary Map

This document defines the current bounded mapping between the imported platform runtime and the extracted calc-domain package.

Purpose in this phase:
- normalize runtime identity away from legacy repo names
- make the control-plane app consume the extracted calc package for active calculation paths
- constrain the next schema-alignment effort to the control-plane and calc surfaces rather than the full historical TCC domain at once

## Runtime Identity Normalization

The active runtime should now be interpreted as a platform service, not a legacy component service.

Current platform-facing names:
- FastAPI root service: `apex-platform-control-plane-api`
- MCP control-plane surface: `apex-platform-governed-control-plane`
- Supabase MCP surface: `apex-platform-supabase-operations`
- GitHub MCP surface: `apex-platform-github-repository-operations`
- Render service target name: `apex-platform-control-plane-api`

Deferred for later cutover:
- GitHub repository dispatch defaults
- historical migration script titles and provenance text
- route-level functional names tied to NETA and TCC workflows

## Active Runtime Boundary

### App Shell

`apps/control-plane-api` currently owns:
- FastAPI application assembly
- auth and OAuth discovery surfaces
- MCP transports and control-plane endpoints
- NETA workflow endpoints and demo assets
- deployment metadata and runtime env contract

### Shared Calc Package

`packages/calc-engine` currently owns:
- ETU pickup calculations
- IEEE inverse-time curve solving
- LTD curve generation
- TMT curve generation
- ETU merge utilities
- the minimal ORM model slice required by those calculation modules

### Active Dependency Edge

The app shell should consume calc logic from `apex_calc_engine` for live calculation paths.

That dependency edge now applies to:
- `apps/control-plane-api/services/calc_engine/router.py`
- `apps/control-plane-api/services/neta/router.py`
- `apps/control-plane-api/services/calc_engine/__init__.py` as a compatibility re-export layer

## Narrow Planning Surface For Step 3

The next schema/function alignment effort should focus only on the surfaces below.

### Control-Plane Surface

- task-packet queueing and review decisions
- job run state and validation artifacts
- governed local action execution boundaries
- public OAuth and MCP metadata exposure

### Calc Surface

- ETU sensor and plug lookup
- ETU pickup method tables and tolerances
- LTD parameter and band resolution
- STD and GFD equation resolution
- TMT frame, class, amp, and thermal-adj data

### Functional Boundary

Out of scope for this narrower mapping pass:
- broader project-management entity redesign
- forms generation domain alignment
- knowledge/study-content entity normalization
- archive migration and historical utility reconciliation

## Immediate Implication

When planning schema alignment next, treat the control-plane runtime and calc package as two bounded consumers of a future platform data model, not as architecture authority in themselves.
