# Multi-Agent Operating Model
## Date: 2026-04-12
## Status: Recommended future-state AI operating model

_Repo-owned authority copy established 2026-05-07 so the strategic multi-agent governance model lives inside the canonical repo boundary._
_Keep the parent-root `Platform-Authority` copy aligned as a historical mirror until the broader strategic-authority relocation lane is complete._

## 1. Goal

Apex Power Ops should be designed so multiple AI instances can work concurrently without relying on chat memory or one human manually restating context every time.

The system should support:
- strategic AI sessions
- implementation AI sessions
- review AI sessions
- data curation AI sessions
- automation-triggered AI work
- bounded external MCP actions

## 2. Core Rule

Chat is not state.
Tracked files, structured packets, queue state, and auditable logs are state.

## 3. Agent Roles

Recommended standing roles:

### 3.1 Platform Architect
Owns:
- target-state design
- cross-domain decisions
- repo topology
- schema authority
- system seams

### 3.2 Product Implementer
Owns:
- application code
- frontend work
- backend work inside assigned domain
- tests
- local validation

### 3.3 Data Steward
Owns:
- migrations
- staging imports
- reconciliation
- knowledge manifests
- taxonomy normalization

### 3.4 Forms And Document Engineer
Owns:
- document templates
- schema-driven generation
- render validation
- field packet outputs

### 3.5 Automation Operator
Owns:
- task queues
- workflow triggers
- MCP action wrappers
- integration jobs
- write-gated external actions

### 3.6 Reviewer And Release Gate
Owns:
- code review
- migration review
- risk analysis
- deployment readiness
- artifact acceptance

One human or AI can play multiple roles, but the task packet must still declare the active role.

## 4. Required Artifacts

The future repo should carry a formal agent operations layer under ops/agents/.

Recommended layout:

```text
ops/agents/
├── packets/
│   ├── draft/
│   ├── active/
│   ├── blocked/
│   ├── review/
│   ├── done/
│   └── archive/
├── handoffs/
├── inbox/
├── policies/
├── logs/
└── indexes/
```

## 5. Task Packet Contract

Every substantial task should have a machine-readable packet plus an optional human brief.

Recommended packet fields:
- packet_id
- title
- objective
- domain
- active_role
- repo_paths
- dependencies
- required_inputs
- constrained_outputs
- write_scope
- validation_steps
- handoff_target
- status
- created_at
- updated_at

Recommended statuses:
- draft
- ready
- claimed
- in_progress
- blocked
- review
- accepted
- archived

## 6. Branch And Change Rules

### 6.1 Branching
Recommended branch classes:
- platform/
- app/
- data/
- forms/
- automation/
- docs/

Examples:
- platform/monorepo-bootstrap
- data/future-entity-map
- forms/aha-runtime-schema

### 6.2 Write permissions
Not every agent should have equal write authority.

Recommended classes:
- read_only
- bounded_repo_write
- bounded_db_write
- external_action_write

External writes must be explicitly gated.
Examples:
- applying a migration
- deploying an edge function
- writing to a production-like Supabase project
- dispatching GitHub workflows

## 7. Handoff Model

Recommended rule:
A handoff must contain enough state that a new AI instance can continue work without reading a long chat transcript.

Required handoff fields:
- source packet
- current state
- exact blockers
- next executable step
- files changed
- validations completed
- validations still required

## 8. Environment Model

The future platform should distinguish environments cleanly.

Recommended environment classes:
- local_dev
- shared_dev
- lab
- staging
- production

Every environment should have:
- named contracts
- declared services
- declared secrets references
- declared write rules
- declared validation steps

## 9. Human Oversight Model

The human owner should act as:
- principal stakeholder
- architecture ratifier
- release approver for sensitive moves
- exception handler when business logic is ambiguous

The human should not be required to:
- manually bridge every AI session
- manually restate repo structure every time
- personally track every temporary task state in chat

## 10. Metrics

The platform should eventually measure AI operations the same way it measures engineering work.

Recommended metrics:
- packet throughput
- blocked packet age
- mean handoff quality score
- validation pass rate
- deployment rollback frequency
- schema drift incidents
- orphan artifact count

## 11. Minimal Viable Operating Model

If implementation starts tomorrow, the minimum acceptable AI operating system is:

1. one authority folder for platform decisions
2. one packet folder with machine-readable task definitions
3. one handoff folder
4. one environment contract folder
5. one migration authority lane
6. one release-readiness checklist per deployable app

## 12. Bottom Line

Multi-agent utilization should be designed as an operating system feature, not an informal habit.

If the repo structure, packet structure, and authority model are right, multiple AI instances can work in parallel safely.
If they are wrong, additional AI instances only increase drift and confusion.