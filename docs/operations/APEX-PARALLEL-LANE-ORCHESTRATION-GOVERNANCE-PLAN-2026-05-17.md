# APEX Parallel Lane Orchestration Governance Plan

Date: 2026-05-17
Status: Reviewed governance proposal; activation pending stakeholder approval statement
Scope: Desktop Codex delegated orchestration governance, VS Code Codex PM-lane authority protection, and parallel lane admission rules

## Purpose

This plan proposes a governed parallel-lane operating model for APEX Power Ops so that the PM lane can remain the primary VS Code Codex focus while other important lanes continue to advance under Desktop Codex orchestration.

The core bottleneck is not lack of task inventory. The bottleneck is that VS Code Codex currently carries too many simultaneous roles in the PM lane:

1. repo technical authority,
2. PM lane author,
3. executor,
4. validator,
5. auditor,
6. coordinator for adjacent lanes.

That authority is intentional and useful for the time-sensitive Project Miner Temp Power work. It should not be diluted. The proposed change is to delegate orchestration governance to Desktop Codex so VS Code Codex can stay concentrated on PM lane implementation and production-readiness decisions.

## Repo Technical Authority Review

VS Code Codex reviewed this plan as repo technical authority and finds the proposed operating model acceptable for governance publication because it protects the PM lane, preserves VS Code Codex final integration authority, and keeps production/schema/credential/runtime authority outside Desktop Codex by default.

This review does not activate expanded Desktop Codex authority by implication. Activation still requires the approval statement in this document or a later packet that explicitly admits the same boundary.

Publication of this plan admits no product code change, deployment, schema change, credential handling, MCP service admission, Olares runtime change, PM business-state mutation, or autonomous queue ownership.

## Governance Ask

Approve Desktop Codex as the delegated parallel-lane orchestration governor for non-PM lanes, subject to the boundaries in this plan.

Desktop Codex would be authorized to:

1. maintain the lane board and orchestration plan,
2. draft lane packets and operator prompts,
3. assign bounded sidecar work to approved non-PM lanes,
4. collect handoffs and evidence from sidecar executors,
5. classify whether a lane is ready for VS Code Codex review,
6. keep Jason's review queue compressed to decisions, exceptions, and approvals.

Desktop Codex would not be authorized to:

1. overrule VS Code Codex repo technical authority,
2. merge or publish product changes without explicit approval,
3. mutate PM business state,
4. admit new production credentials,
5. change Supabase, Render, Vercel, Olares host, schema, auth, ingress, or runtime posture,
6. turn `ai_tasks` into an autonomous queue owner,
7. add new MCP services beyond the currently admitted boundary,
8. widen any lane beyond its approved packet.

## Operating Model

VS Code Codex remains the primary technical authority for:

1. PM lane product implementation,
2. repo architecture decisions,
3. shared product code integration,
4. production validation,
5. deployment and hosted parity decisions,
6. final acceptance of cross-lane work that touches shared surfaces.

Desktop Codex becomes the orchestration governor for:

1. lane intake,
2. packet framing,
3. executor assignment,
4. evidence collection,
5. sidecar closeout review,
6. readiness classification,
7. governance escalation when a lane needs higher authority.

Jason remains the approval authority for:

1. business decisions,
2. production credential admission,
3. production workflow mutation,
4. expanded authority,
5. lane priority changes,
6. approving this governance plan.

## Lane Classes

### Lane 1 - PM Lane

Priority: highest
Primary executor: VS Code Codex
Desktop Codex role: support only

Allowed support:

1. draft PM handoffs,
2. summarize external executor output,
3. prepare validation checklists,
4. maintain PM lane decision queue,
5. identify review burden and coordination friction.

Not allowed:

1. PM business-state mutation,
2. PM production approval,
3. Supabase writes,
4. schema migration,
5. Render or Vercel production changes,
6. final PM integration without VS Code Codex acceptance.

### Lane 2 - NETA Study Material Lane

Priority: parallel build lane
Primary executor: Desktop Codex or sidecar executor
VS Code Codex role: review only when shared repo or product surfaces are touched

Allowed work:

1. study material outline drafting,
2. source organization,
3. question bank scaffolding,
4. PDF or workbook extraction notes,
5. content QA checklists,
6. handoff packages for later review.

Approval gate:

VS Code Codex review is required only when NETA work touches shared code, package files, product UI, repo-wide docs, or publication status surfaces.

### Lane 3 - TCC Lane

Priority: parallel scout/build lane
Primary executor: Desktop Codex or sidecar executor
VS Code Codex role: architecture review at integration boundary

Allowed work:

1. requirements extraction,
2. interface mapping,
3. packet drafts,
4. isolated prototypes,
5. fixture or sample-data design,
6. risk and dependency analysis.

Approval gate:

Any shared service contract, schema, API, auth, deployment, or production workflow change requires VS Code Codex review and explicit packet approval.

### Lane 4 - Relay Lane

Priority: parallel scout/build lane
Primary executor: Desktop Codex or sidecar executor
VS Code Codex role: final authority over admitted orchestration surfaces

Allowed work:

1. relay pattern documentation,
2. handoff template improvement,
3. evidence summarization,
4. operator prompt hardening,
5. lane-board design,
6. review-burden measurement.

Not allowed:

1. autonomous queue ownership,
2. new MCP service admission,
3. always-on orchestration runtime,
4. controller widening,
5. production credential handling,
6. replacement of packet and handoff governance.

## Authority Bands

Every lane task must be assigned one authority band before execution starts.

### Band A - Research / Scout

Allowed:

1. read approved files,
2. inspect public documentation,
3. write notes or handoffs,
4. propose designs,
5. identify gaps.

Human approval needed for:

1. turning findings into product changes,
2. touching production credentials,
3. expanding lane scope.

### Band B - Draft / Build

Allowed:

1. edit lane-owned docs,
2. create isolated examples,
3. create fixtures,
4. draft tests that do not require shared integration,
5. produce review-ready artifacts.

Human or VS Code Codex approval needed for:

1. editing shared files,
2. changing package or environment files,
3. touching apps, services, schemas, or deployment configuration.

### Band C - Integration / Production

Allowed only with explicit packet approval:

1. shared product code edits,
2. schema changes,
3. deployment changes,
4. hosted validation,
5. production workflow mutation,
6. status publication.

Default owner:

VS Code Codex, unless a later approved packet names another executor and exact boundaries.

## Desktop Codex Duties

Desktop Codex should maintain an orchestration queue with these fields for each lane:

1. lane name,
2. current objective,
3. authority band,
4. executor,
5. allowed files,
6. forbidden files,
7. required reads,
8. validation evidence,
9. approval gate,
10. current status,
11. next decision needed from Jason,
12. whether VS Code Codex review is required.

Desktop Codex should compress sidecar output into one of four statuses:

1. `READY_FOR_VSCODE_REVIEW`,
2. `READY_FOR_JASON_DECISION`,
3. `BLOCKED_CAPABILITY_GAP`,
4. `ABORTED_SCOPE_WIDENING`.

## VS Code Codex Protection Rules

To keep PM lane progress moving, Desktop Codex should protect VS Code Codex from avoidable interruption:

1. Do not send raw sidecar transcripts to VS Code Codex unless requested.
2. Do not ask VS Code Codex to adjudicate non-PM lane details until a lane reaches an approval gate.
3. Do not route scout findings into PM implementation unless PM explicitly needs them.
4. Do not ask VS Code Codex to review lane work that has no shared-code, shared-doc, deployment, schema, credential, or business-state impact.
5. Batch non-urgent cross-lane review requests into a single decision queue.
6. Preserve PM as the only lane with active integration priority unless Jason explicitly changes priority.

## Required Packet Shape

Each Desktop Codex-governed lane packet must include:

1. lane name,
2. authority band,
3. owner,
4. exact files allowed to read,
5. exact files allowed to write,
6. exact files forbidden,
7. commands allowed,
8. commands forbidden,
9. credential posture,
10. validation requirement,
11. closeout artifact path,
12. stop conditions,
13. escalation target.

Packets must state whether VS Code Codex review is required before, during, or after the work.

## Stop Conditions

Desktop Codex must stop and escalate if any lane attempts to:

1. change PM business state,
2. write to Supabase,
3. run workbook macros,
4. change schema, auth, ingress, runtime, Render, Vercel, or Olares host posture,
5. add new MCP services,
6. turn `ai_tasks` into an autonomous owner,
7. touch files outside its declared set,
8. edit shared package or environment files without approval,
9. require Jason to manually relay technical context between agents,
10. require VS Code Codex review before the lane has produced a clean summary and evidence bundle.

## Initial Lane Board

| Lane | Status | Authority Band | Desktop Codex Role | VS Code Codex Role | Next Approval Gate |
| --- | --- | --- | --- | --- | --- |
| PM Temp Power | Active priority | Band C where packet-approved | Support and evidence compression | Primary executor and repo authority | Jason approval for business workflow and production state changes |
| NETA Study Material | Proposed parallel lane | Band A/B | Govern packet, delegate content/scaffold work, collect evidence | Review only if shared repo/product surfaces are touched | Approve NETA lane packet and output location |
| TCC | Proposed parallel lane | Band A first | Govern scout packet and dependency map | Architecture review at integration boundary | Approve TCC scout scope |
| Relay | Proposed parallel lane | Band A/B | Govern orchestration templates and review-burden metrics | Review before any admitted orchestration widening | Approve relay governance packet |

## First Approved Move

If this plan is approved, the first move should be a Desktop Codex-governed packet that creates the orchestration queue and three non-PM lane prompts:

1. NETA Study Material scout/build prompt,
2. TCC scout prompt,
3. Relay lane review-burden prompt.

That first packet should not change product code, deployment, schema, credentials, MCP services, Olares runtime, or PM business state.

Expected output:

1. one lane board,
2. three bounded non-PM prompts,
3. one closeout handoff,
4. a short `READY_FOR_JASON_DECISION` summary.

## Approval Statement

Recommended approval:

Approve Desktop Codex as delegated orchestration governor for non-PM parallel lanes under this plan, while preserving VS Code Codex as PM lane technical authority and final repo integration authority.

Approval does not admit autonomous production execution. Approval only admits bounded orchestration governance, packet framing, sidecar delegation, evidence collection, and readiness classification.

## Success Criteria

This governance plan is successful when:

1. PM lane progress is not slowed by NETA, TCC, or Relay coordination.
2. Non-PM lanes produce useful artifacts in parallel.
3. Jason reviews fewer raw handoffs and more decision-ready summaries.
4. VS Code Codex receives only integration-ready, evidence-backed review requests.
5. No lane widens production authority without explicit approval.
6. Olares becomes the durable workspace and relay surface without becoming an uncontrolled autonomous executor.
