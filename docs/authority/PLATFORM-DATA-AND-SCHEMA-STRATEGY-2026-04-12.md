# Platform Data And Schema Strategy
## Date: 2026-04-12
## Status: Recommended future-state data strategy

_Repo-owned authority copy established 2026-05-07 so platform data and schema strategy lives inside the canonical repo boundary._
_Keep the parent-root `Platform-Authority` copy aligned as a historical mirror until the broader strategic-authority relocation lane is complete._

## 1. Core Position

The current Supabase schema should be treated as a valuable prototype and migration input, not as the immutable future platform schema.

The future-state data design should be greenfield-first:
- define the correct bounded contexts
- define the correct system-of-record boundaries
- then decide what current tables, columns, and data deserve migration

## 1.1 Technical Authority Gate

Schema review and schema design require explicit technical authority review and approval before they are treated as implementation-ready.

That gate applies to:
- canonical entity definitions
- future-state schema boundaries
- implementation-ready schema specs
- SQL authoring readiness
- migration-path approval for production-bound data

Working schema drafts remain design material until that review and approval is recorded.

## 2. Recommended Data Topology

### 2.1 Operational Principle
Separate operational truth from ingestion and research.

Recommended data layers:

1. Core transactional platform database
2. Knowledge and search layer
3. Object storage for governed files
4. Analytics and reporting layer when justified

### 2.2 Practical recommendation
Start with one primary PostgreSQL platform for transactions and one explicitly separated ingestion or lab surface.

Recommended naming:
- apex_core
- apex_lab

#### apex_core
Purpose:
- production-bound platform data
- transactional workflows
- user-facing app data
- approved automation state

#### apex_lab
Purpose:
- imports
- staging
- one-time reconciliation
- schema experiments
- historical lift-and-shift validation
- agent-assisted normalization work

Do not mix exploratory ingestion tables into the same active authority lane as production transactional entities.

## 3. Recommended Domain Schemas

Within the future transactional platform, use explicit schemas or equally explicit module boundaries.

Recommended logical domains:
- identity
- org
- work
- safety
- asset
- engineering
- knowledge
- document
- automation
- integration
- audit

These can be implemented as PostgreSQL schemas, or as one schema with strict module ownership if operational simplicity wins.

## 4. Canonical Entity Model

### 4.1 Identity
Owns:
- users
- roles
- teams
- crews
- permissions
- agent identities
- service accounts

### 4.2 Org
Owns:
- companies
- business units
- clients
- sites
- contacts
- contractual relationships

### 4.3 Work
Owns:
- projects
- work packages
- tasks
- assignments
- statuses
- schedules
- dependencies
- execution evidence

### 4.4 Safety
Owns:
- SOP definitions
- AHA definitions and instances
- MOP definitions and instances
- hazard libraries
- PPE policies
- safety acknowledgments

### 4.5 Asset
Owns:
- asset taxonomy
- asset classes
- manufacturer/model master data
- installed assets
- asset components
- location hierarchy
- asset-resource applicability

### 4.6 Engineering
Owns:
- calculation scenarios
- TCC families
- settings libraries
- engineering outputs
- versioned calculation results
- study artifacts

### 4.7 Knowledge
Owns:
- standards references
- extraction records
- study content
- KSA definitions
- question banks
- mappings to asset classes and procedures

### 4.8 Document
Owns:
- document templates
- generated documents
- render jobs
- evidence uploads
- version histories
- metadata

### 4.9 Automation
Owns:
- task packets
- agent tasks
- workflow executions
- MCP action logs
- queue state
- handoffs

### 4.10 Integration
Owns:
- external system bindings
- secrets references
- outbound jobs
- sync ledgers
- import batches
- reconciliation status

### 4.11 Audit
Owns:
- append-only events
- status transitions
- approval history
- write provenance

## 5. Primary Operational Object Model

Recommended top-level execution chain:

```text
Client
  -> Site
    -> Project
      -> Work Package
        -> Task
          -> Execution Step
            -> Evidence
```

Recommended technical chain:

```text
Asset Class
  -> Procedure Set
  -> Safety Package
  -> Knowledge Package
  -> Engineering Rules
```

Recommended live assignment chain:

```text
Work Package
  -> Assigned Crew
  -> Required Asset Context
  -> Required Procedure Context
  -> Required Safety Context
  -> Required Knowledge Context
  -> Required Tools And Equipment
```

This model is stronger than centering everything directly on a project or directly on an apparatus row.

## 6. Schema Design Rules

1. system-of-record tables must be distinct from staging and import tables
2. all state transitions that matter operationally must be evented or auditable
3. cross-domain joins should happen through explicit linking entities, not ad hoc overloaded columns
4. documents should store metadata and lifecycle state in the database but large binaries should live in object storage
5. knowledge extraction lineage must be preserved without allowing source-file chaos to pollute operational tables
6. engineering outputs should be versioned and reproducible, not overwritten in place
7. AI-generated content must carry provenance and review status
8. future-state schema definitions and implementation-ready review gates must record technical authority review and approval before SQL or migration commitments are authorized

## 7. Migration Philosophy

### 7.1 Preserve meaning, not table names
Do not migrate because a table exists.
Migrate because the domain meaning is still valid.

### 7.2 Promote curated data only
Data should move from current systems into apex_lab first when uncertain, then be promoted into apex_core after validation.

### 7.3 Keep transformation explicit
Every migration from existing schema to future schema should have:
- source definition
- target definition
- transform logic
- validation report
- rollback or re-run story

## 8. Specific Recommendations For Current Domains

### 8.1 Current APEX schema
Keep as input material for:
- org hierarchy ideas
- work management ideas
- safety table relationships
- knowledge linkage patterns

Do not preserve blindly:
- exploratory table naming
- mixed concerns in one table family
- early assumptions about what the platform is centered on

### 8.2 Current TCC schema
Keep as authoritative input for:
- engineering calculation domain knowledge
- current family behavior and migration evidence
- control-plane and auth lessons

Do not make it the primary overall platform schema.
It should become a bounded engineering domain inside the larger platform.

### 8.3 Current NETA-Forms structures
Keep as authoritative input for:
- template semantics
- document generation structure
- field-level document logic

Promote the best template schemas into the document domain.
Do not keep document structure scattered across standalone generators without a platform metadata model.

### 8.4 Current knowledge/study-material structures
Keep as authoritative input for:
- manifests
- extraction coverage
- taxonomy work
- resource lifecycle lessons

Do not allow raw source accumulation to become the defining shape of the engineering monorepo.

## 9. Recommended Early Data Deliverables

Before major repo consolidation, define and submit for technical authority review and approval:

1. Future canonical entity map
2. Future event model for work package lifecycle
3. Future document generation model
4. Future asset taxonomy model
5. Future engineering result model
6. Future knowledge lineage model
7. Future automation and task packet model

## 10. Recommended Database Execution Model

### Short term
- continue operating current systems where needed
- stop treating current schema as the future-state authority
- create future-state entity definitions and migration mappings
- keep schema design in review state until technical authority approval is explicit

### Medium term
- stand up apex_lab for imports and design validation
- stand up apex_core for future-state transactional design
- start porting one domain at a time

### Long term
- retire old mixed-purpose tables
- migrate stable operational apps to apex_core
- keep apex_lab as the permanent import and experimentation boundary

## 11. Bottom Line

The serious version of this platform should not inherit a single monolithic draft schema as its destiny.
It should inherit:
- proven domain knowledge
- validated data
- working calculation logic
- document semantics
- operational lessons

Then it should be redesigned into a cleaner, more explicit platform data architecture.