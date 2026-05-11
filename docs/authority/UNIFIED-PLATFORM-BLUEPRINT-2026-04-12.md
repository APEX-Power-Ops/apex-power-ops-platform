# Unified Platform Blueprint
## Date: 2026-04-12
## Owner: APEX Power Operations, LLC
## Status: Active authority for future-state platform design

_Repo-owned authority copy established 2026-05-07 so the strategic platform blueprint lives inside the canonical repo boundary._
_Keep the parent-root `Platform-Authority` copy aligned as a historical mirror until the broader strategic-authority relocation lane is complete._

## 1. Executive Position

Apex Power Ops should be treated as a platform company, not a collection of side projects.

The future product is not:
- a RESA-only tool
- a TCC backend with attachments
- a forms repo with some SQL nearby
- a documentation archive with an app next to it

The future product is:
- an integrated operating system for electrical testing, field execution, safety documentation, technical knowledge delivery, reporting, and automation
- owned by Apex Power Ops as an internal product platform that can first support RESA operations and later support other operating models

## 2. North Star

Build a platform where one work object can drive everything else.

Recommended primary work object:
- Work Package

A Work Package is the canonical unit of operational execution.
It can represent a project-phase-apparatus bundle, a study task, a maintenance activity, a commissioning packet, or a field assignment.

Everything should be attachable to a Work Package directly or through a canonical linked entity:
- client
- site
- asset or equipment instance
- asset class
- test procedure
- SOP
- AHA
- MOP
- report packet
- TCC scenario
- required skills and knowledge
- assigned personnel
- required tools and test equipment
- uploaded evidence
- AI tasks and automation runs

## 3. Platform Capabilities

The platform should be intentionally designed as six integrated capability domains.

### 3.1 Operations Core
Owns:
- organizations
- clients
- sites
- projects
- work packages
- schedules
- crews
- assignments
- status tracking
- execution evidence

### 3.2 Safety And Procedure System
Owns:
- SOP libraries
- AHA generation and execution
- MOP generation and approval
- hazard models
- PPE rules
- lockout and isolation logic
- NFPA 70E and company policy references

### 3.3 Asset Intelligence
Owns:
- equipment taxonomy
- asset classes
- installed assets
- manufacturer/model libraries
- equipment relationships
- test applicability rules
- asset-linked procedures and resources

### 3.4 Technical Knowledge System
Owns:
- standards extraction
- study content
- KSA mappings
- reference sheets
- question banks
- learning pathways
- contextual field guidance
- search and vector retrieval

### 3.5 Calculation And Engineering Services
Owns:
- TCC libraries
- ETU/TMT/EMT and future families
- coordination studies
- engineering calculators
- result persistence
- curve rendering
- reportable calculation outputs

### 3.6 Automation And Control Plane
Owns:
- task packets
- AI orchestration
- agent permissions
- workflow queues
- MCP surfaces
- integration runners
- audit trails
- deployment validations
- external-system actions

## 4. Product Surfaces

The platform should expose multiple deployable products, all sourced from one authority stack.

### 4.1 Operations Web App
Purpose:
- PM, scheduler, lead tech, executive, admin workflows

### 4.2 Field Execution App
Purpose:
- mobile-friendly technician execution
- work package guidance
- checklists
- evidence capture
- safety acknowledgment
- offline-first synchronization

### 4.3 Forms Studio
Purpose:
- maintain branded document templates
- generate PDF and print outputs
- manage structured document schemas
- preview and test report generation

### 4.4 Technical Calculation API
Purpose:
- TCC and related engineering services
- internal and external API consumers

### 4.5 Control Plane And Automation Hub
Purpose:
- manage agent work
- integration tasks
- repository automations
- controlled external actions

### 4.6 Knowledge Console
Purpose:
- operate the standards and study-content system
- inspect extraction coverage
- curate mappings
- manage search relevance and learning packages

## 5. Principles

### 5.1 Existing Is Draft
Nothing in the current repos is foundational by default.
All current schema, layout, and repo boundaries are draft material unless re-ratified in the future-state design.

### 5.2 One Authority Per Concern
There must be one explicit authority for:
- repo topology
- schema migration lane
- environment contracts
- agent task protocol
- document template system
- asset taxonomy

### 5.3 Separate System Of Record From Ingestion
Do not let raw imports, exploratory tables, historical loaders, and production data coexist without explicit boundaries.

### 5.4 Independent Deployables, Shared Authority
One repo is acceptable. One release train for everything is not.
Each app or service should deploy independently.

### 5.5 Heavy Reference Material Is Not Normal Source Code
Large PDFs, historical exports, and evidence packs should be governed and indexed, but not allowed to distort the active engineering repo.

### 5.6 AI Work Must Be Operable
Multi-agent work should be treated like distributed operations:
- explicit roles
- explicit task ownership
- machine-readable handoffs
- audit history
- bounded write permissions

## 6. Strategic Decisions

### Decision A
Apex Power Ops should move to a platform monorepo.

Rationale:
- stronger architectural coherence
- easier shared contracts
- simpler cross-domain changes
- better AI orchestration
- cleaner packaging of IP as one product organization

### Decision B
The future monorepo should not be formed by simply choosing one current repo as root and nesting the others unchanged.

Rationale:
- current repos were optimized for different phases and responsibilities
- APEX is too mixed between active work, authority docs, archives, and reference material
- TCC is a deployable runtime, not a platform root
- NETA-Forms is a template asset domain, not a platform shell

### Decision C
The future operational database should be treated as a redesign opportunity, not a preservation exercise.

Rationale:
- current schema reflects staged exploration and tactical progress
- platform-level bounded contexts are now clearer than when the schema started
- production-scale usability depends on better domain seams than the current organic growth path guarantees

## 7. Recommended Technical Baseline

### Core stack
- GitHub monorepo
- VS Code workspace rooted at the monorepo
- Python services where Python is already strong
- TypeScript for web apps, shared contracts, and tooling where suitable
- PostgreSQL as the primary transactional store
- Supabase only if it continues to serve the operational model better than a custom Postgres stack; treat it as a platform choice, not dogma

### Supporting stack
- pgvector or equivalent semantic search where justified
- object storage for generated documents and governed source assets
- Git LFS only for a limited class of version-worthy binaries, not as a dumping ground
- path-scoped CI pipelines
- centralized environment contract management

## 8. What Should Happen Next

1. ratify the target monorepo topology
2. define the future-state data architecture before porting more schema forward
3. isolate active code from archives and heavy source libraries
4. formalize the multi-agent operating model and task packet structure
5. stand up a new platform root and import current domains deliberately rather than recursively copying trees