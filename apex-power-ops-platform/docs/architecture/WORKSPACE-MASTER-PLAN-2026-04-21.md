# Workspace Master Plan

Date: 2026-04-21
Status: Active live planning document
Scope: `C:/APEX Platform/apex-power-ops-platform`

## Purpose

This document defines the intended steady-state workspace shape for the active platform repo.

It is the live design document for:

1. workspace topology
2. lane purpose and promotion rules
3. governance boundaries
4. consolidation targets for sibling source-domain repos

This plan is platform-first and implementation-oriented. Strategic authority still remains above it in `C:/APEX Platform/Platform-Authority/`, but this document defines how that authority is realized inside the active repo.

## Authority Order

Use this order when making structural, migration-boundary, or workspace-governance decisions:

1. `C:/APEX Platform/Platform-Authority/`
2. `docs/authority/`
3. this document
4. `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
5. `docs/architecture/WORKSPACE-IMPLEMENTATION-ROADMAP-2026-04-21.md`
6. `README.md`
7. source-domain documentation only for bounded extraction work

## Design Principles

1. The platform repo is the default implementation surface.
2. Source-domain repos are extraction lanes, not equal operating roots.
3. Every top-level lane must have one explicit purpose.
4. Empty or reserved lanes must be documented, not silent.
5. Runtime code, authority docs, operational workflow, and knowledge assets must stay separated.
6. Legacy residue must be labeled, isolated, or removed.
7. Forward migration lanes must stay explicit and singular.
8. App proliferation is not a goal; every deployable surface must justify its existence.

## Target Workspace Shape

### `apps/`

Purpose:
- deployable runtime surfaces
- user-facing or operator-facing application entrypoints
- bounded service runtimes that cannot be reduced to shared packages

Steady-state lane model:

- `apps/control-plane-api`
  - canonical backend control plane
  - owner of bounded MCP transports, control-plane orchestration, and active API runtime
- `apps/operations-web`
  - primary operator web surface
  - preferred consolidation target for admin, PM, queue, and observability views unless a separate app is operationally required
- `apps/forms-studio`
  - intended forms authoring and rendering application
  - keep as approved placeholder until real implementation begins
- `apps/mutation-seam`
  - bounded mutation or ingestion service lane
  - keep active while it owns behavior that should not yet live in `control-plane-api`
- `apps/field-surface`
  - reserved future field runtime
  - keep as seed lane for now
  - note: target-topology naming may later prefer `field-app`

Transitional surfaces:

- `apps/integration-surface`
  - keep only if it becomes a true standalone runtime boundary
  - otherwise merge its behavior into `control-plane-api` or `mutation-seam`
- `apps/lead-surface`
  - not yet justified as a standalone deployable
  - preferred end state is merge into `operations-web` unless independent runtime needs are proven
- `apps/pm-surface`
  - not yet justified as a standalone deployable
  - preferred end state is merge into `operations-web` for UI and `control-plane-api` for backend services unless a separate deployment boundary is proven

Promotion rule:
- an app lane is considered active only when it has a README, declared runtime contract, validation path, and a non-placeholder implementation surface

### `packages/`

Purpose:
- reusable shared code
- stable contracts reused by more than one app
- code that should not be owned by a single runtime

Steady-state lane model:

- `packages/calc-engine`
  - shared calculation core
- `packages/forms-engine`
  - shared document/forms generation core
- `packages/api-contracts`
  - approved destination for shared schemas and client/server contracts
  - remains placeholder until multiple apps actually share these contracts

Promotion rule:
- code moves into `packages/` only when at least two surfaces benefit from a shared contract or shared implementation boundary

### `infra/`

Purpose:
- database migrations
- environment contracts
- deploy and infrastructure definitions

Steady-state lane model:

- `infra/database`
  - canonical platform database migration and schema mapping lane outside app-local exceptions

Exception rule:
- app-local forward migration lanes are allowed only when the app explicitly owns a separate runtime database seam
- current approved exception: `apps/control-plane-api/supabase/migrations/`

### `ops/`

Purpose:
- operator workflow
- packets, handoffs, queueing, review control, and operational registries

Steady-state lane model:

- `ops/agents`
  - active packet and handoff lane
- `ops/knowledge-control-plane`
  - control-plane operational knowledge registry
- `ops/knowledge-resource-operations`
  - operational resource and process lane

### `knowledge/`

Purpose:
- durable domain assets
- mappings, study content, and re-homed knowledge artifacts that are not process specifications

Boundary rule:
- `knowledge/` stores domain assets
- `docs/knowledge/` stores knowledge-process specifications and documentation

### `docs/`

Purpose:
- authority bridge
- architecture decisions
- process specifications
- live workspace governance docs

Steady-state lane model:

- `docs/authority`
  - bridge authority until cutover
- `docs/architecture`
  - live implementation-shape, lineage, and workspace-governance documents
- `docs/knowledge`
  - documentation about knowledge workflows and specs, not the primary knowledge payloads themselves

### `archive/`

Purpose:
- legacy material retained for lineage, auditability, or rollback context

Rule:
- archive content must never be treated as active implementation by default

## Governance Model

### Lane States

Use only these states in repo-local planning docs and READMEs:

- active
- seed
- transitional
- placeholder
- archive

### Required Lane Metadata

Every top-level lane or empty reserved lane must state:

1. current state
2. intended purpose
3. authority surfaces
4. promotion or merge criteria

### Ownership Standard

The workspace must move from implicit ownership to explicit path ownership.

Required steady-state controls:

1. `.github/CODEOWNERS`
2. a repo-level workflow and approval map
3. clear assignment of runtime, database, docs, ops, and knowledge stewardship

### Migration Standard

Current enforced rule:

1. `apps/control-plane-api/supabase/migrations/` is the canonical forward migration lane for control-plane schema changes
2. `apps/control-plane-api/migrations/` is legacy utility or replay support only

### Import Standard

Bounded extraction order:

1. import approved active slices
2. normalize them into existing target lanes
3. keep lineage references to source domains
4. archive or map legacy material rather than flattening it into active paths

## Design Decisions Enacted By This Plan

1. `operations-web` is the preferred consolidation target for operator UI surfaces.
2. `pm-surface` and `lead-surface` are not assumed to become permanent standalone apps.
3. `integration-surface` must justify itself as a deployable boundary or merge down.
4. `forms-studio` and `api-contracts` remain approved placeholders, not accidental empties.
5. `mutation-seam` remains valid only while it owns a real bounded behavior seam.
6. `docs/architecture` is the correct live home for workspace planning and status documents.

## Definition Of A Fully Implemented Workspace

The workspace is considered fully implemented when all of the following are true:

1. every top-level lane has an explicit owner and documented purpose
2. transitional app surfaces have been promoted, merged, renamed, or archived
3. placeholder lanes have either real implementation or an explicit defer decision
4. deployment and validation paths are documented for every active app
5. knowledge and docs boundaries are explicit and locally documented
6. no malformed residue or encoding-corrupted governance artifacts remain in active lanes
7. the repo can operate as the default platform root without relying on session memory or sibling-repo conventions

## Companion Documents

- `docs/architecture/WORKSPACE-CURRENT-STATUS-2026-04-21.md`
- `docs/architecture/WORKSPACE-IMPLEMENTATION-ROADMAP-2026-04-21.md`
- `docs/architecture/WORKSPACE-STRUCTURE-GOVERNANCE-AUDIT-2026-04-21.md`