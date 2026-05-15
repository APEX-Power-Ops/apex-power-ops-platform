# APEX PM Temp Power Delivery And AI Orchestration Plan

Date: 2026-05-15
Status: Active operating plan
Scope: Project Miner Temp Power PM lane delivery, Olares One orchestration posture, and capability-gap escalation rules

## Purpose

This plan sets the current target lane for the APEX Operations Platform:

Project Miner Temp Power must be able to use the new PM workflow from project intake through field execution and tracking before the late-May or early-June 2026 field start window.

Companion visual map:

`docs/operations/APEX-OPS-VISUAL-SYSTEM-MAP-2026-05-15.md`

Use the visual map when explaining the current Vercel, Render, Supabase, Olares, Project Miner intake, and AI orchestration split.

Companion acceleration lane:

`docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`

Use the acceleration lane when sequencing PM work so stakeholder time, relay burden, and workflow friction are treated as primary project constraints.

The plan also clarifies the role of Olares One. Olares should reduce operator burden and AI-to-AI relay friction, but only inside the current repo authority and trust boundaries. The platform is not assumed to provide autonomous agent coordination unless the repo admits that capability through a separate packet.

## Operating Principle

Best idea, best tool, best plan.

The delegated technical authority must actively surface constraints instead of quietly working around them. If a missing tool, missing credential, unavailable MCP server, stale deployment, inaccessible host, or weak validation surface materially reduces the quality or reliability of a tranche, that limitation must be recorded and escalated.

This includes but is not limited to:

1. Excel automation or workbook inspection gaps,
2. Render deployment or log access gaps,
3. Supabase access or permission gaps,
4. Vercel deployment or environment gaps,
5. Olares host or private-mesh access gaps,
6. browser automation or screenshot validation gaps,
7. PDF extraction or rendering gaps,
8. external Codex or Claude Code executor gaps,
9. missing MCP tools or connectors,
10. absent durable task queue or AI-to-AI relay surfaces.

Fallbacks are allowed only when they are truthful, bounded, and good enough for the current slice. Fallbacks must not become the permanent operating model by accident.

## Stakeholder Time Constraint

The Project Miner PM lane must account for the real operating constraint that Jason is already responsible for field execution, estimating, project management, and operations work.

This means the PM lane is not successful if it requires Jason to become the routine relay between agents, tools, workbooks, platforms, and deployment surfaces.

Default PM lane posture:

1. Codex advances the next safe bounded move without asking Jason to coordinate implementation details.
2. Jason is asked for source files, business decisions, credentials, exception authority, or approval of review-ready artifacts.
3. Packet, handoff, and validation machinery should be generated and summarized by Codex, not manually maintained by Jason.
4. Local read-only proof should proceed when hosted Render parity is blocked, as long as the hosted gap is recorded truthfully.
5. Every new workflow step must either reduce Jason's future burden, reduce delivery risk, or preserve a non-negotiable governance boundary.

The near-term product target is a PM flow where Jason reviews exceptions and approvals, not raw workbook mechanics or AI-to-AI handoffs.

## Current Reality

Current repo-admitted Olares capabilities:

1. GitHub remains canonical.
2. `C:/APEX Platform/apex-power-ops-platform` is the local publication boundary.
3. `/home/olares/code/apex/apex-power-ops-platform` is the authoritative Olares host mirror.
4. Olares host parity is part of normal closeout for governance, packet, and host-operating slices.
5. The admitted MCP/operator boundary is still `apex-fs`, `apex-db`, and `apex-jobs`.
6. The minimal MCP trio is operator-on-demand and may truthfully be `not-running` at rest.
7. Packet and handoff artifacts are the current relay surface between coordinator, external executors, and future sessions.

Not currently admitted:

1. autonomous `ai_tasks` queue ownership,
2. always-on orchestration service,
3. more than two active executors in one mutation lane,
4. new MCP services beyond the admitted trio,
5. public ingress widening,
6. direct AI business-state mutation,
7. Excel-to-Supabase direct write,
8. workbook macro execution as an unattended intake path.

## Target Workflow

The target workflow has two linked halves.

Project creation pipeline:

1. Source files land in the Project Miner planning folder.
2. The intake preview reads estimator, SLD/PDF, equipment, capability, data-entry, and tracker lineage.
3. The system produces an import candidate with project, workpackage, task, and apparatus rows.
4. PM or Operations reviews traceability, grouping, dedupe keys, warnings, and readiness.
5. A later admitted mutation imports the approved candidate into Supabase through Render mutation-seam.

Execution pipeline:

1. PM monitors the workfront.
2. Lead accepts and assigns imported work.
3. Field executes apparatus and checklist work.
4. Field submits progress, blockers, notes, and snapshots.
5. PM reviews escalations, snapshots, task/package status, history, schedule, and variance context.
6. PM approves, returns to lead, or escalates.

## UI Surfaces

Current intended user-facing split:

1. Vercel hosts the UI.
2. Render hosts the mutation seam/API between the UI and Supabase.
3. Supabase stores project state.
4. Olares is the durable development, validation, host-parity, and orchestration support surface.

Key UI lanes:

1. `/pm-review/workfront` for PM command center.
2. `/pm-review/approval` for PM task, workpackage, snapshot, escalation, and history review.
3. `/lead-ops` for lead execution and assignment flow.
4. `/field-tech` for apparatus-first field execution.
5. future import-candidate review surface for Temp Power intake approval.

## Olares Orchestration Role

Olares One should enhance execution by providing:

1. durable repo mirror and host validation surface,
2. private-mesh access for operator and executor work,
3. packet and handoff relay continuity,
4. host parity proof after publication,
5. a future place for admitted orchestration services only if a concrete insufficiency proves they are needed.

Near-term AI-to-AI relay should use repo-visible artifacts:

1. packet JSON for bounded objectives,
2. operator prompts for external Codex or Claude Code executors,
3. handoffs for executor results,
4. validation blocks for evidence,
5. explicit file ownership declarations,
6. coordinator closeout for acceptance,
7. host parity checks for publication truth.

This avoids Jason serving as the message bus while preserving repo authority.

## Dual-Lane Execution Pattern

Default: one executor.

Use two lanes only when the split is written first and the ownership is disjoint.

Preferred Temp Power split:

1. Lane A: PM product/runtime slice, such as import-candidate model, preview API, or UI review surface.
2. Lane B: orchestration/tooling slice, such as packet prompt, validation checklist, capability-gap register, or host evidence surface.
3. Coordinator: final authority, audit, integration, publication, host parity.

Abort the split if:

1. both lanes need the same files without a named final write owner,
2. either lane needs a new service, schema change, production write, auth change, ingress change, or business mutation not admitted by packet,
3. validation cannot be made repo-visible,
4. an executor asks Jason to relay technical context that should have been in packet/handoff artifacts.

## Temp Power Delivery Sequence

Target sequence before field start:

1. Build Temp Power import-candidate review as read-only PM lane output.
2. Restore hosted Render mutation-seam parity for current PM reads in parallel or before hosted proof is required.
3. Validate the candidate against estimator, SLD/PDF, data-entry, tracker, equipment, and capability lineage.
4. Add PM UI review for the import candidate.
5. Admit a narrow, idempotent import mutation only after the candidate and approval workflow are proven.
6. Pilot one Temp Power slice through PM, Lead, and Field workflow before importing broader Building A/B scope.

## Current Product Tranche

PM Lane 032:

`Temp Power Import Candidate Review`

Boundary:

1. read-only,
2. no Supabase write,
3. no schema migration,
4. no Render/Vercel deployment,
5. no workbook macro execution,
6. no AI assignment/status/schedule mutation.

Expected outputs:

1. import-candidate data model,
2. candidate preview command or read endpoint,
3. grouping from estimator candidates into project/workpackage/task/apparatus proposal,
4. traceability to source workbook, sheet, row, drawing, and designation,
5. duplicate and formula-warning summary,
6. review-ready JSON artifact,
7. packet/handoff evidence for the future UI and import mutation lanes.

Local PM Lane 032 proof currently produces a read-only candidate with 7 workpackages, 15 tasks, 186 apparatus candidates, 15 crew, 343 equipment inventory rows, 50 capability rows, and 2 review signals.

PM Lane 033 adds the first read-only PM UI review route:

`/pm-review/import-candidate`

The route consumes `GET /api/v1/reads/project-import-candidate`, renders required decisions and warnings before dense task rows, keeps clean rows collapsed, and exposes guardrails from the candidate payload. It does not add approval, persistence, import, assignment, schedule, status, or production write authority.

## Capability-Gap Register

Current known gaps:

1. Hosted Render mutation-seam parity remains a blocker for hosted PM live proof.
2. Excel MCP is useful for real Excel inspection, but not admitted as production runtime.
3. A durable AI-to-AI task queue is not admitted; packets and handoffs remain the relay surface.
4. The project import mutation is not admitted; import-candidate review must come first.
5. Workbook macros are not admitted for unattended intake.

Required response to new gaps:

1. record the gap in the active packet or handoff,
2. classify it as blocker, acceptable fallback, or future enhancement,
3. recommend the best tool or admission path,
4. stop if the fallback would produce untrustworthy PM business state.

## Success Standard

This plan succeeds when:

1. Temp Power can be reviewed as an import candidate from real source files,
2. PM can approve the plan before any database write,
3. Lead and Field surfaces can consume imported work,
4. Olares reduces relay and validation burden without widening authority silently,
5. tool and capability gaps are visible early enough to resolve before field execution depends on them.
