# APEX Ops Visual System Map

Date: 2026-05-15
Status: Active orientation aid
Scope: Visual explanation of the current APEX Ops, PM lane, Olares One, and AI orchestration split

## Purpose

This page is the visual starting point for understanding how the current pieces fit together.

The short version:

1. Vercel is the user-facing app.
2. Render is the governed API and mutation boundary.
3. Supabase is the database.
4. The Project Miner planning folder is the real project-intake source for Temp Power.
5. Olares One is the development, host-validation, private workspace, and AI relay support surface.
6. GitHub remains the canonical publication surface.
7. AI executors work from packets and handoffs; they do not directly own business state.

## Plain-English Legend

| Piece | What it is for | What it is not for |
| --- | --- | --- |
| Vercel | The web app people click through: PM, Lead, Field, and review screens. | Not the database and not a second backend authority. |
| Render | The API/mutation seam between the UI and Supabase. It enforces governed reads and admitted writes. | Not a duplicate of Vercel, and not a free-for-all database bridge. |
| Supabase | The durable Postgres-backed project state. | Not the primary user workflow surface. |
| Project Miner planning folder | The source packet: estimator workbooks, PDFs, inventory, capability, and tracker lineage. | Not production state until reviewed and imported through an admitted path. |
| Local repo | The active implementation surface on this workstation. | Not a place to commit unrelated residue or unreviewed generated state. |
| GitHub | Canonical repo publication and branch history. | Not the AI task queue by itself. |
| Olares One | Host mirror, private workspace, validation surface, and future orchestration home. | Not currently admitted as autonomous AI-to-AI task ownership. |
| External Codex / Claude Code | Bounded executors for clearly scoped packet work. | Not repo authority, PM authority, or release authority. |

## Current Platform Split

```mermaid
---
id: 333df061-b7a1-4188-81a7-22aa18b63452
---
flowchart LR
  Users["PM / Operations / Lead / Field users"]
  Vercel["Vercel<br/>user-facing UI<br/>pm-review, lead-ops, field-tech"]
  Render["Render<br/>mutation seam / API<br/>governed reads and admitted writes"]
  Supabase["Supabase<br/>Postgres project state"]

  Planning["Project Miner planning folder<br/>Excel, PDFs, inventory, capability, trackers"]
  LocalRepo["Local repo<br/>C:/APEX Platform/apex-power-ops-platform"]
  GitHub["GitHub<br/>canonical clean-main publication"]
  Olares["Olares One<br/>host mirror, private workspace, validation, relay support"]
  AI["External Codex / Claude Code<br/>bounded packet executors"]

  Users --> Vercel
  Vercel --> Render
  Render --> Supabase

  Planning --> LocalRepo
  LocalRepo --> GitHub
  GitHub --> Olares
  Olares --> LocalRepo

  LocalRepo --> AI
  AI --> LocalRepo
  AI -. "handoff evidence" .-> Olares

  classDef human fill:#fff7d6,stroke:#9a7b00,color:#1b1b1b
  classDef runtime fill:#dff0ff,stroke:#1f6f9e,color:#1b1b1b
  classDef data fill:#e5f6e8,stroke:#2e7d32,color:#1b1b1b
  classDef governance fill:#f0e8ff,stroke:#6f42c1,color:#1b1b1b
  classDef source fill:#ffe8df,stroke:#b55326,color:#1b1b1b

  class Users human
  class Vercel,Render runtime
  class Supabase data
  class LocalRepo,GitHub,Olares,AI governance
  class Planning source
```

Read this as two connected lanes:

1. The product lane is `Users -> Vercel -> Render -> Supabase`.
2. The build/governance lane is `Planning folder -> local repo -> GitHub -> Olares -> repo-visible evidence`.

## Project Miner PM Lane Flow

```mermaid
---
id: 0392806f-7143-4549-80aa-f2068b08d2cf
---
flowchart TD
  L0["Level 0<br/>Source intake<br/>Planning folder exists and files resolve"]
  L1["Level 1<br/>Scope extraction<br/>Estimator rows, PDFs, designations, source rows"]
  L2["Level 2<br/>Task plan shaping<br/>Import candidate for workpackages, tasks, apparatus"]
  L3["Level 3<br/>Resource context<br/>Equipment inventory and tech capability"]
  L4["Level 4<br/>PM workfront<br/>Review readiness, blockers, unassigned rows"]
  L5["Level 5<br/>Lead and field execution<br/>Assignments, apparatus work, checklists, snapshots"]
  L6["Level 6<br/>PM review and closeout<br/>Approve, return, escalate, archive evidence"]

  SourceFiles["Temp Power source files<br/>Estimator R3, SLD PDF, equipment, capability, trackers"]
  Preview["Read-only preview command<br/>No macros, no database write"]
  Candidate["Import candidate review<br/>Human-readable proposed project plan"]
  Approved["PM approval<br/>Candidate accepted or returned for correction"]
  Import["Later admitted import mutation<br/>Idempotent write through Render"]
  Runtime["Runtime project state<br/>Supabase rows consumed by UI"]

  SourceFiles --> L0 --> Preview --> L1 --> L2 --> Candidate
  L2 --> L3
  Candidate --> L4 --> Approved
  Approved --> Import --> Runtime --> L5 --> L6

  classDef source fill:#ffe8df,stroke:#b55326,color:#1b1b1b
  classDef readonly fill:#e7f1ff,stroke:#276fa3,color:#1b1b1b
  classDef review fill:#fff7d6,stroke:#9a7b00,color:#1b1b1b
  classDef write fill:#e8f7e8,stroke:#2e7d32,color:#1b1b1b

  class SourceFiles source
  class Preview,L0,L1,L2,L3 readonly
  class Candidate,L4,Approved review
  class Import,Runtime,L5,L6 write
```

The important idea: the first live Temp Power move is not "dump Excel into the database." It is "turn real source files into a reviewable import candidate, let PM/Ops approve it, then admit the narrow write path."

## Day-To-Day PM Operation

```mermaid
---
id: 3bc990b1-0a52-4a9c-a9ad-015a32887c77
---
sequenceDiagram
  participant Est as Estimator / Source Folder
  participant Ops as PM / Operations
  participant Repo as APEX Repo Tools
  participant UI as Vercel PM UI
  participant API as Render Mutation Seam
  participant DB as Supabase
  participant Field as Lead / Field Team

  Est->>Repo: Place estimator, SLD, inventory, capability, trackers
  Ops->>Repo: Run read-only preview
  Repo-->>Ops: Show counts, warnings, traceability, candidate rows
  Ops->>UI: Review import candidate
  UI->>API: Request governed reads
  API->>DB: Read current project/workfront state
  DB-->>API: Return state
  API-->>UI: Display review context
  Ops->>UI: Approve candidate when ready
  UI->>API: Later admitted import mutation
  API->>DB: Write project/workpackage/task/apparatus rows
  Field->>UI: Execute assigned work and submit updates
  UI->>API: Governed field mutations
  API->>DB: Persist status, snapshots, blockers, history
```

## AI Orchestration Split

```mermaid
---
id: 01aa8299-ad7a-47df-bf17-8a7014d28d37
---
flowchart LR
  Stakeholder["Stakeholder intent<br/>business priority and exception authority"]
  Coordinator["Codex coordinator<br/>repo authority, PM sequencing, audit, release gate"]
  Packet["Packet JSON<br/>objective, scope, ownership, validation"]
  LaneA["Lane A<br/>PM product/runtime slice<br/>for example import-candidate model or UI"]
  LaneB["Lane B<br/>orchestration/tooling slice<br/>for example prompt, checklist, host evidence"]
  HandoffA["Lane A handoff<br/>diff summary and validation evidence"]
  HandoffB["Lane B handoff<br/>diff summary and validation evidence"]
  Audit["Coordinator audit<br/>accept, revise, reject, or re-delegate"]
  Publish["Commit, push, and host parity<br/>repo-visible closeout"]
  Host["Olares host mirror<br/>rest-state and parity proof"]

  Stakeholder --> Coordinator --> Packet
  Packet --> LaneA --> HandoffA --> Audit
  Packet --> LaneB --> HandoffB --> Audit
  Audit --> Publish --> Host
  Host --> Coordinator

  classDef authority fill:#f0e8ff,stroke:#6f42c1,color:#1b1b1b
  classDef lane fill:#e7f1ff,stroke:#276fa3,color:#1b1b1b
  classDef evidence fill:#e8f7e8,stroke:#2e7d32,color:#1b1b1b

  class Stakeholder,Coordinator,Audit authority
  class Packet,LaneA,LaneB lane
  class HandoffA,HandoffB,Publish,Host evidence
```

The default is one executor. Two lanes are only useful when the work is clearly split and the files do not collide.

## Current Authority Boundary

```mermaid
---
id: e71dab8f-dfd5-4085-9b2b-0b3044cb7f04
---
flowchart TB
  subgraph Current["Admitted now"]
    C1["Read-only planning-folder preview"]
    C2["Import-candidate modeling and review"]
    C3["PM / Lead / Field UI reads"]
    C4["Packets, handoffs, validation evidence"]
    C5["Olares host parity proof"]
    C6["Excel MCP or spreadsheet tooling as operator aid only"]
  end

  subgraph Future["Future only after explicit packet admission"]
    F1["Supabase import mutation"]
    F2["Schema migration"]
    F3["Workbook macro execution"]
    F4["AI status changes or apparatus assignment"]
    F5["Durable AI-to-AI task queue"]
    F6["New public ingress or new MCP services"]
  end

  C1 --> C2 --> C3
  C4 --> C5
  C6 -. "helps inspect source files" .-> C1
  C2 -. "approval evidence can justify" .-> F1
  F1 --> F2
  F5 -. "may replace manual relay later" .-> C4

  classDef admitted fill:#e8f7e8,stroke:#2e7d32,color:#1b1b1b
  classDef future fill:#fff1e5,stroke:#c05621,color:#1b1b1b

  class C1,C2,C3,C4,C5,C6 admitted
  class F1,F2,F3,F4,F5,F6 future
```

This is the key safety line: AI can help explain, group, summarize, and warn. AI cannot silently mutate real PM business state.

## Where To Start

For the current Temp Power PM lane work, start here:

1. Treat the original import-candidate and PM-intake parity branches as completed background, not as the current blocker.
2. Use the controlling actuals-branch admission phrase `ADMIT_TEMP_POWER_ACTUALS_CUSTOMER_CAPTURE_REVIEW_FIRST_WRITE_PACKET_ONLY`.
3. Treat authenticated Render redeploy as completed proof, not as the current blocker.
4. Treat PM Lane 314 publication as completed proof: commit `3d47834eb32aa29b80152df3973f91d7c62a2e30` is live on the existing mutation-seam service.
5. Treat PM Lane 315 publication as completed proof: commit `666f649d020d19cc24d1a5e57b9a1796928f45d8` is live on the existing mutation-seam service.
6. Both hosted seam URLs now pass the bounded `--include-temp-power-actuals-review` and `--include-temp-power-customer-preview-review` smoke, so the admitted actuals plus customer-preview review first-write slice is complete within current scope.
7. Treat PM Lane 316 as the next-boundary marker: any follow-on lane starts with customer delivery and durable proof admission, not finance or source writeback.
8. Treat PM Lane 317 as the current design marker: the next delivery/proof work is design-first contract work, not direct implementation.
9. Treat PM Lane 318 as the current review-design marker: the next delivery/proof work is an inspection-only PM surface, while storage and runtime admission stay deferred.
10. Treat PM Lane 319 as the current storage-design marker: the next delivery/proof work is readback design, while schema and runtime admission stay deferred.
11. Treat PM Lane 320 as the current readback-design marker: the next delivery/proof work is route/payload design, while schema and runtime admission stay deferred.
12. Treat PM Lane 321 as the current request-contract marker: the next delivery/proof work is a separate execution gate, while schema and runtime admission stay deferred.

For AI orchestration work, start here:

1. Decide whether one executor is enough.
2. If two lanes are useful, declare disjoint file ownership first.
3. Put the scope, stop conditions, and validation commands into a packet.
4. Require handoff evidence.
5. Coordinator audits before publication.

## Primary Source Documents

1. `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
2. `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
3. `docs/authority/APEX-OPS-DELEGATED-AUTHORITY-AND-AI-ORCHESTRATION-PROTOCOL-2026-05-15.md`
4. `docs/authority/OLARES-WORKSPACE-AUTHORITY-FRAMEWORK.md`
5. `docs/operations/OLARES-AI-DELEGATED-DUAL-LANE-EXECUTION-CHECKLIST-2026-05-13.md`
