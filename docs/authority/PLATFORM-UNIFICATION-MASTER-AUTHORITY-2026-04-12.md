# Platform Unification Master Authority
## Date: 2026-04-12
## Status: Active master coordination document
## Role: Entry-point authority for current state, target structure, issues, and tracked convergence work

_Repo-owned authority copy established 2026-05-07 so the master strategic unification surface lives inside the canonical repo boundary._
_Keep the parent-root `Platform-Authority` copy aligned as a historical mirror until the broader strategic-authority relocation lane is complete._

## 1. Purpose

This document should be the first planning surface for platform unification work.

It exists to do four things in one place:
- describe the current state of the source domains
- name the structural and governance issues that block naive consolidation
- define the target unified repository format
- provide a traceable bridge between current state and the migration steps required to reach the target state

This is not a replacement for the deeper authority documents.
It is the master index and execution map that connects them.

Current decision-governance companion:
- `APEX-OPS-STAKEHOLDER-DECISION-PATH-2026-04-15.md`

Current implementation posture:
- stakeholder-approved functional platform unification is now the active program authority; single-repo consolidation remains explicitly deferred until the approved acceptance criteria are met

## 2. How To Use This Document

Use this document in the following order:
1. confirm which source domains are in scope
2. confirm current-state classification and active issues
3. confirm the approved target monorepo format
4. locate the current migration phase and next bounded actions
5. jump into the linked detailed authority documents only after the governing frame is clear

## 3. Source Domains In Scope

Current unification scope:
- APEX Platform
- tcc_v5_backend
- NETA-Forms
- NETA ETT Study Material
- external product and web surfaces that are logically part of the Apex Power Ops platform but may still live outside the current workspace

Interpretation rule:
- these repositories and workspaces are source domains, not future-state architecture authority

## 4. Current-State Summary

### 4.1 APEX Platform

Current role:
- strategic redesign and staging root for the future platform

Observed state:
- now contains the canonical repo boundary at `c:/APEX Platform/apex-power-ops-platform`
- now retains the aligned historical mirror of the strategic authority stack at `c:/APEX Platform/Platform-Authority`, while the active repo-owned authority stack lives under `c:/APEX Platform/apex-power-ops-platform/docs/authority`
- already operates as the workstation umbrella around the canonical repo boundary and remaining external source lanes

Current issues:
- platform root is still only partially imported
- not all source domains have been re-homed yet
- some strategic parent-root mirrors still require continued synchronization or final demotion so operators do not treat them as the default authority entrypoint

### 4.2 tcc_v5_backend

Current role:
- source domain for the existing control-plane, MCP, API, calc, migration, and Supabase work

Observed state:
- operationally mature in several bounded areas
- already partially imported into the platform root as `apps/control-plane-api` and `packages/calc-engine`
- still contains historical implementation detail, migration utilities, and production lineage that remain useful for provenance and selective extraction

Current issues:
- legacy repo identity is stronger than desired for future-state operator clarity
- app/runtime code and historical utilities are still mixed in the source domain
- old schema assumptions can leak into redesign decisions if not actively governed

### 4.3 NETA-Forms

Current role:
- source domain for forms, document workflows, and field execution surfaces

Observed state (updated 2026-04-13 — inventory complete):
- source repo is mounted as a workspace root and fully accessible
- the first bounded forms-engine slice is now imported into the canonical repo boundary
- `apps/forms-studio` still exists only as a target placeholder, while `packages/forms-engine` now has a real imported package boundary
- **first real slice-level inventory is complete** — all 10 top-level directories and root-level assets classified against bounded-import model
- full verified source-to-target mapping: `FORMS-SOURCE-INVENTORY-AND-TARGET-MAPPING-2026-04-13.md`
- the repo is engine-heavy and template-heavy, not app-shell-heavy
- `packages/forms-engine` is the confirmed first import candidate (self-contained Python generators + JSON schemas)
- `apps/forms-studio` has no current source code; only a React prototype (`PSS_Data_Collection_Prototype.jsx`) exists as a candidate seed
- all Python generators are self-contained with zero cross-repo or external service dependencies

Current issues:
- ~~source-domain inventory pending~~ **RESOLVED 2026-04-13**
- ~~source-to-target mapping pending~~ **RESOLVED 2026-04-13**
- brand asset storage governance needed before Logos/ import (binary .ai/.eps files)
- Supabase contract boundary: SOP/AHA schema docs reference deployed tables
- maintenance template active status and MOP HTML duplication need resolution before full template import

Current interpretation:
- those remaining issues do not block the first bounded `packages/forms-engine` import
- they block broader template, branding, and integration cleanup beyond the engine-core pilot
- the bounded engine-core pilot has now completed with disposition `imported-with-runtime-gaps`
- the next forms repo-level move is dependency-environment hardening inside `packages/forms-engine`, not a broader forms-domain import

### 4.4 NETA ETT Study Material

Current role:
- source domain for standards-derived knowledge content, study assets, reference materials, and knowledge-delivery workflows

Observed state:
- large mixed-content repository with governed documentation, content assets, scripts, archived material, and development history
- important to the future knowledge domain, but not suitable for naive wholesale import into an active app-oriented monorepo

Current issues:
- active content, pipeline assets, governance docs, and archival material are mixed together
- binary and content-heavy assets need storage and retention policy before migration
- knowledge-system extraction needs an explicit packaging and indexing strategy, not a direct repo copy

### 4.5 External Product Surfaces

Current role:
- user-facing app surfaces and deployables that may currently sit outside the immediate workspace layout

Observed state:
- part of the future platform topology
- not yet fully governed from the same canonical repo boundary as the staged platform slices

Current issues:
- deployment topology and source authority are not fully consolidated
- cross-surface contracts must be normalized before cutover

## 5. Cross-Repo Structural Problems

The main problems are not just technical duplication. They are authority and operating-model problems.

Primary issues:
- mixed authority: multiple repos can still appear authoritative for overlapping domains
- mixed content classes: deployable code, reference docs, archive material, migrations, and generated assets are intermixed
- mixed schema assumptions: current Supabase and app schemas are valuable inputs but cannot be treated as the final data model
- mixed operational surfaces: some workflows still point users toward historical repo roots rather than the future platform root
- mixed provenance and execution guidance: historical lineage can be mistaken for live operator instruction if not written carefully
- mixed tooling reliability: inventory and analysis work cannot assume every shell utility or markdown-conversion tool path is consistently available
- incomplete import state: the TCC/control-plane domain is partially re-homed and the first bounded forms-engine slice is imported, but the broader docs/infra and knowledge lanes remain unlanded
- insufficient top-level traceability: current authority docs are strong, but the bridge from source-domain reality to concrete tracked migration steps was spread across multiple files

## 6. Approved Target Unified Repository Format

The future platform should converge on a monorepo with intentional domain boundaries.

Top-level target structure:
- `apps/` for deployable products and service runtimes
- `packages/` for reusable engines, schemas, clients, and shared libraries
- `infra/` for infrastructure definitions, database assets, and environment contracts
- `ops/` for operational automation, runbooks, and support workflows
- `knowledge/` for active governed knowledge assets and knowledge-system source material that remains intentionally in git
- `docs/` for authority, architecture, policy, and decision documentation
- `archive/` for retained historical material that must remain available but should not steer active implementation

Initial approved app/package direction:
- `apps/control-plane-api`
- `packages/calc-engine`
- future `apps/forms-studio`
- future `packages/forms-engine`
- future knowledge-serving and operator-facing surfaces as justified by the platform blueprint

## 7. Current Convergence Status

Status by major workstream:

### 7.1 Authority Reset

Status:
- complete enough to operate

Evidence:
- repo-owned authority stack exists, with the aligned parent-root `Platform-Authority` mirror preserved for provenance
- future-state blueprint, topology, schema strategy, operating model, and roadmap exist

### 7.2 Canonical Repo Boundary

Status:
- in progress and already usable

Evidence:
- `apex-power-ops-platform` root exists
- root toolchain and operator runbook exist
- platform-local `.venv` exists and is functioning

### 7.3 Controlled TCC Import

Status:
- active slice complete for current bounded scope

Evidence:
- control-plane runtime staged into `apps/control-plane-api`
- calc domain extracted into `packages/calc-engine`
- compatibility shims preserve legacy import paths where needed
- focused operational tests pass from the platform-local environment

### 7.4 Forms Domain Import

Status:
- first bounded import complete; follow-on hardening pending

Evidence (2026-04-13):
- first real slice-level inventory completed against mounted source repo
- every top-level source area classified against bounded-import model
- first import candidate identified: `packages/forms-engine` core
- source-to-target mapping authority: `FORMS-SOURCE-INVENTORY-AND-TARGET-MAPPING-2026-04-13.md`
- handoff: `ops/agents/handoffs/2026-04-13-forms-import-007-inventory-handoff.md`
- first-import blocker resolution: `FORMS-ENGINE-FIRST-IMPORT-BLOCKER-RESOLUTION-2026-04-13.md`
- packet `2026-04-13-forms-import-008` has now completed the bounded engine-core import pilot into `packages/forms-engine`
- one representative generator has executed successfully in the imported package boundary
- dependency-environment hardening is now complete for the imported `packages/forms-engine` boundary
- remaining forms-engine gaps are later deferred template, branding, app-shell, and database/service work rather than basic package-runtime blockage
- the APEX-root docs/infra surface is now decomposition-planned through packet `2026-04-13-apex-unification-001`
- packet `2026-04-13-knowledge-import-001` has now completed the first bounded knowledge import plan
- packet `2026-04-13-knowledge-import-001a` has now completed the first physical low-weight knowledge spine landing
- packet `2026-04-13-knowledge-import-001b` has now completed bounded published-content landing planning
- packet `2026-04-13-knowledge-import-001c` has now completed the first HTML-first published-content landing under `knowledge/published/`
- packet `2026-04-13-knowledge-import-001d` has now completed published-content inventory and manifest planning over the landed HTML assets
- packet `2026-04-13-knowledge-import-001e` has now completed serving-neutral manifest landing over the landed publication tree
- packet `2026-04-13-knowledge-import-001f` has now completed published-content catalog and source-resource crosswalk planning
- packet `2026-04-13-knowledge-import-001g` has now completed the first human-readable published-content crosswalk landing under `knowledge/catalog/published/`
- packet `2026-04-13-knowledge-import-001h` has now completed bounded published-content to KSA bridge planning
- packet `2026-04-13-knowledge-import-001i` has now completed bounded published-content to KSA bridge landing
- packet `2026-04-13-knowledge-import-001j` has now completed bounded published-content KSA tagging-guidance planning
- packet `2026-04-13-knowledge-import-001k` has now completed bounded published-content KSA candidate-tagging scaffold landing
- packet `2026-04-13-knowledge-import-001l` has now completed bounded published-content KSA entry-surface candidate-tagging expansion
- packet `2026-04-13-knowledge-import-001m` has now completed bounded published-content KSA slice-scoped candidate-tagging planning
- packet `2026-04-13-knowledge-import-001n` has now completed the first bounded Level II practice-test content-page candidate-tagging tranche
- packet `2026-04-13-knowledge-import-001o` has now completed the second bounded Level II practice-test content-page candidate-tagging tranche
- the next repo-level unification packet to author is `2026-04-13-knowledge-import-001p` for the third bounded Level II practice-test content-page candidate-tagging tranche

### 7.5 Knowledge Domain Import

Status:
- classified and retention-governed, with the low-weight knowledge spine landed, the first HTML-first publication slice landed, the manifest/index plan complete, the serving-neutral manifest landing complete, the crosswalk-boundary plan complete, the first human-readable publication crosswalk landing complete, the publication-to-KSA bridge-plan packet complete, the publication-to-KSA bridge-landing packet complete, the tagging-guidance packet complete, the candidate-tagging scaffold packet complete, the entry-surface expansion packet complete, the slice-scoped candidate-tagging plan packet complete, the first bounded content-page tagging tranche complete, the second bounded content-page tagging tranche complete, and the third bounded content-page tagging tranche ready to author

### 7.6 Future-State Data Platform

Status:
- framed strategically, not yet executed domain by domain

Current PM/work implementation planning update:
- PM Schema V2 implementation is now execution-planned in `PM-SCHEMA-V2-IMPLEMENTATION-PLAN-2026-04-13.md`
- first implementation should occur in a clean local PostgreSQL staging database, not directly in the existing active database
- local staging design is now explicit in `PM-SCHEMA-V2-LOCAL-POSTGRES-STAGING-DESIGN-2026-04-13.md`
- packet 007 SQL bundle is now authored in `infra/database/migrations/work/` with manifest and local staging runbook
- packet `2026-04-13-pm-schema-008` has now executed the bundle successfully in local PostgreSQL staging with disposition `validated-with-deferrals`
- packets `2026-04-13-pm-schema-009`, `009a`, `009b`, `009c`, `010`, `010a`, `010b`, `011`, `2026-04-14-pm-schema-011a`, `2026-04-14-pm-schema-011b`, `2026-04-14-pm-schema-011c`, `2026-04-14-pm-schema-011d`, `2026-04-14-pm-schema-011e`, and `2026-04-14-pm-schema-011f` are now complete for legacy migration planning, mapping infrastructure, source-data population, staging dry-run migration, runtime adoption planning, work-schema ORM model authoring, the read-only PM/work API surface, cross-domain dependency activation planning, org-domain schema design, org-schema DDL authoring/local validation, org seed-data population, PM/work org FK activation, PM/work org ORM alignment, and PM/work project write API surface implementation
- packet `2026-04-14-pm-schema-012a` is now complete for identity-domain schema design
- packet `2026-04-14-pm-schema-012b` is now complete for identity-schema DDL authoring and local validation
- packet `2026-04-14-pm-schema-012c` is now complete for identity seed-data population
- packet `2026-04-14-pm-schema-012d` is now complete for PM/work identity FK activation
- packet `2026-04-14-pm-schema-012e` is now complete for PM/work identity ORM alignment
- packet `2026-04-14-pm-schema-012f` is now complete for PM/work identity-joined read-surface wiring over the existing GET handlers
- packet `2026-04-14-pm-schema-012g` is now complete for real PostgreSQL-backed integration smoke over the identity joined-read surface
- packet `2026-04-14-pm-schema-012h` is now complete for org-joined read-surface wiring over the already-active org relationships
- packet `2026-04-14-pm-schema-012i` is now complete for real PostgreSQL-backed integration smoke over the org-joined read surface
- packet `2026-04-14-pm-schema-013` is now complete for bounded minimal work-package write-surface implementation
- packet `2026-04-14-pm-schema-013i` is now complete for real PostgreSQL-backed integration smoke over the work-package write surface
- packet `2026-04-14-pm-schema-013j` is now complete for bounded work-package write-response crew/org-name enrichment over the existing POST/PATCH handlers
- the next bounded PM lane is packet `2026-04-14-pm-schema-014` for minimal task POST/PATCH write-surface implementation
- completed local validation packet: `2026-04-13-pm-schema-008`
- legacy data migration and runtime adoption remain later workstreams after local execution succeeds

## 8. Tracking Model For The In-Between Steps

The migration should be tracked as explicit bounded phases with deliverables.

### Phase 0 - Authority Reset

Status:
- complete

Tracking requirement:
- maintain one explicit authority order and refuse silent reversion to source-repo assumptions

### Phase 1 - Active Inventory And Classification

Status:
- partially complete

Remaining tracking needs:
- current-state inventory table for each source domain
- active vs transitional vs archival classification
- heavy-asset retention and storage decisions

Recent completion in this phase:
- APEX docs and active infrastructure assets are now classified as bounded sub-slices in `APEX-ACTIVE-DOCS-AND-INFRA-CLASSIFICATION-2026-04-12.md`
- the remaining APEX-root `Supabase/` surface is explicitly treated as three lanes: PM/project lineage, automation/orchestration, and knowledge-schema assets
- the ETT knowledge import lane is now bounded in `ETT-GOVERNED-KNOWLEDGE-SLICE-CLASSIFICATION-2026-04-12.md`, including an explicit split between published knowledge assets, governed resource inventory, knowledge operations, shared platform residue, and archive-heavy material
- database ownership is now split explicitly in `DATABASE-OWNERSHIP-SPLIT-2026-04-12.md`, distinguishing app-local forward migrations, shared infra schema authority, lineage/validation assets, and archive-only database artifacts
- the remaining `tcc_v5_backend/migrations` utility lane is now classified per file in `TCC-LEGACY-MIGRATION-UTILITY-CLASSIFICATION-2026-04-12.md`, separating retained parity checks, retained replay/import utilities, retained staging-only assets, retained MAINT SQL lineage, and archive-next candidates
- ETT heavy source-library and archive retention is now governed in `ETT-ARCHIVE-AND-SOURCE-LIBRARY-RETENTION-POLICY-2026-04-13.md`, distinguishing active git assets from storage-governed source binaries and archive-discovery holdings
- forms-domain target boundaries are now framed in `FORMS-DOMAIN-INVENTORY-AND-BOUNDED-IMPORT-DESIGN-2026-04-13.md`, separating the future app shell from the shared forms engine
- **forms-domain source inventory is now complete** (2026-04-13): full slice-level classification in `FORMS-SOURCE-INVENTORY-AND-TARGET-MAPPING-2026-04-13.md`, covering all 10 source directories and root assets with verified target mappings; first import candidate identified as `packages/forms-engine` core

### Phase 2 - Future-State Domain Design

Status:
- partially complete

Remaining tracking needs:
- expose the forms source repo and verify the bounded import design against real source slices — **DONE for forms domain 2026-04-13**
- finalize app and package boundaries for the knowledge domain
- finalize environment contract boundaries for all deployables
- finalize domain ownership map beyond the currently imported TCC slice

### Phase 3 - Canonical Repo Boundary And Post-Cutover Convergence

Status:
- repo-boundary cutover is complete; domain-import convergence remains in progress

Remaining tracking needs:
- execute forms-engine dependency hardening after the completed first bounded import
- execute the first bounded active knowledge import tranche after the planning packet is completed
- establish cross-domain contract boundaries for database, auth, and deployment
- continue normalizing operator workflows from the canonical repo boundary

Repo-level next-packet authority now exists at:
- `UNIFIED-REPO-NEXT-PACKET-PLAN-2026-04-13.md`

Program-level stakeholder decision authority now exists at:
- `APEX-OPS-STAKEHOLDER-DECISION-PATH-2026-04-15.md`