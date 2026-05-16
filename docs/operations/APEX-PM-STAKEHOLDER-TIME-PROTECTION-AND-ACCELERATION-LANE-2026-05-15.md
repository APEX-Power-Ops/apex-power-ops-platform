# APEX PM Stakeholder Time Protection And Acceleration Lane

Date: 2026-05-15
Status: Active acceleration overlay
Scope: Project Miner PM lane execution, AI orchestration, and Temp Power delivery sequencing

## Purpose

This lane records a practical operating constraint: Jason is responsible for managing real field, estimating, project management, and operations work, and the Project Miner PM modernization cannot depend on large amounts of extra unpaid coordination time.

The platform must therefore reduce stakeholder burden as a primary success requirement. Governance still matters, but it must run mostly behind the scenes through repo-visible evidence, packets, validation, and closeout. It must not become another manual workload.

## Governing Principle

Jason is the business owner, exception authority, and approval checkpoint. He is not the message bus, manual QA department, packet clerk, or AI-to-AI relay surface.

Codex, as delegated technical repo authority and PM coordinator, must optimize every PM lane tranche for:

1. fewer stakeholder touchpoints,
2. fewer manual copy/paste relay steps,
3. fewer separate tools Jason must open,
4. fewer decisions before there is a concrete artifact to review,
5. default-safe automation before optional process ceremony,
6. fast local proof before broader hosted or production proof when hosted access is the bottleneck,
7. concise human review surfaces instead of raw implementation detail.

## Required Operating Shift

The PM acceleration lane changes the default posture from "ask Jason to coordinate" to "Codex advances the next safe bounded move and escalates only material decisions."

Jason should normally be asked for only:

1. source-file placement or missing source files,
2. business-rule decisions that affect real project outcomes,
3. credential or platform access that Codex cannot obtain,
4. approval of a review-ready import candidate before any production write,
5. exception decisions when guardrails would otherwise stop the tranche.

Codex should normally own:

1. task packet authorship,
2. executor prompt authorship,
3. local implementation,
4. external executor delegation when useful,
5. handoff review,
6. validation,
7. evidence summarization,
8. commit, push, and host parity closeout,
9. capability-gap tracking,
10. next-slice recommendation.

## Practical Touchpoint Budget

For PM lane work, the desired interaction pattern is:

1. one short stakeholder checkpoint before a tranche only when the business rule is ambiguous,
2. one review-ready artifact after the tranche,
3. one explicit approval gate only before a real production write or field-facing process change.

If a lane requires Jason to repeatedly pass messages between tools, agents, tabs, files, or platforms, that is a process defect to be fixed, not the expected operating model.

## Minimum Viable Day-To-Day Workflow

The target day-to-day workflow must converge on this shape:

1. Source files land in one Project Miner planning folder.
2. A single command or UI action produces a read-only intake snapshot.
3. The snapshot produces a review-ready import candidate with warnings, duplicates, traceability, and proposed grouping.
4. PM/Ops reviews exceptions and approves, returns, or edits the candidate.
5. A later admitted mutation imports approved project, workpackage, task, and apparatus rows through Render.
6. Lead and Field users work from simple role-specific surfaces.
7. PM reviews blockers, snapshots, exceptions, and closeout from the PM workfront.

Any extra step must justify itself by reducing risk, reducing future workload, or preserving a non-negotiable governance boundary.

## Acceleration Priorities

Immediate PM lane priority order:

1. Restore hosted Render parity for the new PM intake read endpoints so the Vercel UI can consume current backend data.
2. Prepare and review the approval contract as its own bounded gate, without importing rows or persisting approval.
3. Prepare and review the approval storage plan as its own bounded gate, without schema changes or persisting approval.
4. Admit approval persistence only after the storage decision and hosted read parity are proven.
5. Admit the narrow import mutation only after the review and approval flow is proven.
6. Pilot one bounded Temp Power execution slice before expanding to the larger Building A/B scope.

Immediate orchestration priority order:

1. Stop cycling templates unless a real executor-friction signal exists.
2. Use one executor by default.
3. Use two lanes only when it saves time and file ownership is disjoint.
4. Generate handoffs and review summaries that Jason can skim quickly.
5. Surface missing tools, credentials, or MCP capability as early blockers or accelerators.

## Tooling Expectations

The best tool is the tool that reduces total burden without weakening trust.

Expected accelerators:

1. deterministic Python readers for repeatable Excel/PDF intake,
2. Excel MCP or spreadsheet tooling when visual workbook inspection materially saves time,
3. browser automation for UI proof when routes are available,
4. Render, Vercel, and Supabase connectors or credentials when hosted proof is the blocker,
5. Olares host parity for publication truth,
6. packet and handoff generation templates only when they reduce relay work.

Current acceptable fallback:

1. use local deterministic preview and import-candidate artifacts while hosted Render parity remains blocked,
2. record hosted parity as a blocker for hosted proof, not as a reason to delay all local PM candidate development,
3. keep Excel MCP as an operator accelerator, not a production runtime requirement.

## Governance Compression Rules

Governance remains required, but it should be compressed around actual risk.

Use full packet discipline when a tranche touches:

1. production data,
2. schema,
3. auth,
4. public ingress,
5. deployment control,
6. AI business-state mutation,
7. workbook macro execution,
8. new service admission,
9. irreversible import or field-facing workflow changes.

Use lighter repo-visible closeout when a tranche is:

1. read-only,
2. documentation-only,
3. local preview-only,
4. deterministic test-only,
5. a review artifact with no production write path.

Even lightweight closeout must still preserve:

1. explicit file scope,
2. validation result,
3. no unrelated staging,
4. capability-gap disclosure,
5. commit, push, and host parity when governance truth changes.

## Stop Conditions

Stop and escalate instead of pushing through when:

1. the only available path would require Jason to become a repeated manual relay,
2. a production write is needed before there is a reviewable candidate,
3. a missing credential or tool makes validation untrustworthy,
4. an AI executor needs business context that should have been captured in packet or handoff form,
5. the process adds more work for Jason than the feature removes.

## Next Bounded Implementation Move

The current product tranche is:

`Temp Power Import Candidate Review`

It creates a read-only review artifact and endpoint that group the current Project Miner Temp Power source files into proposed project, workpackage, task, and apparatus rows with source traceability and warnings.

The current UI tranche is:

`Import Candidate PM UI Review`

It surfaces the candidate at `/pm-review/import-candidate` with required decisions, warnings, proposed structure, source traceability, resource context, and guardrails before any approval or import mutation is admitted.

The current hardening tranche is:

`Import Candidate Review Hardening`

It adds source stat freshness, warning filters, browser-only JSON export, and local PM questions draft to the same route. These are designed to reduce review burden while preserving the no-production-write boundary.

The current admission-planning tranche is:

`Import Admission Plan`

It adds `/pm-review/import-admission-plan` and `GET /api/v1/reads/project-import-admission-plan` so the future import gate is visible before it can write. The PM can review what approval, idempotency, diff checks, no-go checks, and target row counts will require, while approval persistence and import mutation remain unadmitted.

The current hosted-proof tranche is:

`Hosted PM Intake UI Promotion And Render Parity Blocker`

It promotes `/pm-review/import-candidate` and `/pm-review/import-admission-plan` to `https://operations.apexpowerops.com`, adds repeatable hosted smoke coverage, and records the remaining blocker truthfully: Render mutation-seam is healthy but stale for the new PM intake reads, and Render-authenticated redeploy/log inspection is required before hosted PM intake live-data parity can be claimed.

The current Render-auth packet is:

`Render-Authenticated PM Intake Mutation-Seam Redeploy Gate`

PM Lane 037 refreshes the older Render-authenticated packet around the current PM intake routes. It adds backend-only `--include-pm-intake` smoke coverage and a copy/paste executor prompt for a Render-authenticated Codex or Claude Code lane. This keeps Jason out of the relay loop while making the missing credential/tool gap explicit.

The completed approval-contract tranche is:

`Import Candidate Approval Persistence Design`

PM Lane 038 implements the no-write version of that design as `GET /api/v1/reads/project-import-approval-contract`. It gives Codex and a future PM UI a machine-checkable approval packet shape: required fields, permitted decisions, expected candidate/source/shape/idempotency values, warning-code acceptance, human-acceptance no-go acknowledgement, non-overridable blocked checks, and a future mutation contract placeholder.

The sidecar recommendation was accepted in bounded form: this tranche stays out of the mutation pipeline and store adapters, validates approval payload shape locally, extends the deployed-seam smoke so hosted parity checks all current PM intake reads, and does not import project, workpackage, task, or apparatus rows.

The current storage-design tranche is:

`Import Candidate Approval Persistence Storage Decision`

PM Lane 039 implements the no-write version of that storage decision as `GET /api/v1/reads/project-import-approval-storage-plan`. It chooses a future dedicated insert-only `seam.pm_import_candidate_approvals` table and `/api/v1/mutations/project-import-approvals` route, while leaving schema, approval persistence, and import rows blocked.

The sidecar recommendation was accepted in bounded form again: actual persistence is deferred because the mutation-seam store defaults to Supabase-backed collections, no approval collection exists, and the generic mutation pipeline does not own `pm_import_candidate_approval`. The storage plan rejects audit-log-only approval storage, reuse of issue/task/workpackage rows, browser-local storage as canonical approval, generic PgDict upsert without an adapter, and direct Supabase writes from Excel or UI.

The current approval-readiness UI tranche is:

`Import Approval Readiness PM UI Review`

PM Lane 040 implements the no-write UI version of the approval contract and storage decision at `/pm-review/import-approval-readiness`. It consumes only the existing approval-contract and approval-storage-plan read seams, keeps the route separate from the current `/pm-review/approval` mutation workflow, and gives Jason one inspection surface for required approval fields, permitted decisions, human-acceptance policy, validation checks, future route/table, adapter requirements, rejected storage shortcuts, future admission sequence, and guardrails.

The sidecar recommendation was accepted in bounded form again: this route is read-only and has no forms, local drafts, approval controls, persistence controls, import controls, or production write authority.

The current hosted-parity tranche is:

`Hosted PM Intake Parity Refresh And Blocker Classification`

PM Lane 041 refreshes the hosted proof boundary after Lane 040. Hosted operations-web still serves import-candidate and import-admission-plan, but does not yet serve `/pm-review/import-approval-readiness`. Hosted mutation-seam is healthy, but OpenAPI is missing all four current PM intake reads, those reads return `404`, and schedule reads still return `500`.

The sidecar recommendation was accepted in bounded form: do not begin approval persistence schema or adapter work yet. First execute or delegate the hosted parity refresh through two strict executor lanes: Vercel-authenticated existing operations-web promotion and Render-authenticated existing mutation-seam redeploy/classification.

Those two executor lanes now have separate packets, handoffs, and a dispatch board so the coordinator can assign either or both without Jason manually translating between AI sessions.

PM Lane 042 adds the closeout intake contract for those hosted executor lanes. Executors should return completed closeout handoffs using `ops/agents/handoffs/templates/pm-hosted-executor-closeout-template.md`, which lets the coordinator audit exact evidence, blockers, and guardrails without Jason becoming the relay.

The current local PM acceleration tranche is:

`Project Miner Import Intake Workbench`

PM Lane 043 adds `/pm-review/import-intake` as one read-only starting point for candidate review, admission planning, approval contract review, and approval storage-plan review. It reduces Jason's day-to-day navigation burden by showing source freshness, proposed counts, warning signals, required PM decisions, workflow gates, future table/route, hosted-parity status, and guardrails in one place.

The sidecar recommendation was accepted in bounded form: use `/pm-review/import-intake` so the route fits the existing import route cluster while staying review-only. The route has no approve, persist, submit, import, assignment, schedule, schema, or status controls.

The current orchestration refresh tranche is:

`Hosted PM Intake Route Scope Refresh`

PM Lane 044 updates the hosted smoke scripts, 041A Vercel handoff, 041 parent packet, dispatch board, and closeout template so an authenticated Vercel executor proves both `/pm-review/import-approval-readiness` and `/pm-review/import-intake`. Render remains bounded to the existing four read seams; no backend endpoint, schema, or mutation scope is added for the workbench.

The current PM handoff compression tranche is:

`Project Miner PM Intake Brief Export`

PM Lane 045 adds an `Export PM Brief` action to `/pm-review/import-intake`. The brief is downloaded as Markdown from the already-loaded read-only intake packet and can be used as a concise reviewer or executor context handoff. This is explicitly not approval, persistence, import, assignment, schedule, status, or production state.

The current local review-prep tranche is:

`Project Miner PM Intake Local Review Checklist`

PM Lane 046 adds a candidate-scoped browser-local checklist to `/pm-review/import-intake` for source freshness, warning review, PM decision capture, admission no-go review, approval storage understanding, hosted-parity awareness, and write-guardrail confirmation. The checklist appears in the exported Markdown PM brief so Jason or an executor can see what was reviewed without converting the screen into approval, persistence, import, assignment, schedule, status, or production state.

The current local decision-prep tranche is:

`Project Miner PM Intake Approval-Decision Draft`

PM Lane 047 adds a candidate-scoped browser-local approval-decision draft to `/pm-review/import-intake`. It uses the permitted decisions from the read-only approval contract, captures PM review notes, requires a local-only attestation, and includes the result in the Markdown PM brief. This reduces future packet relay work without creating an approval record, persisting data, importing rows, assigning work, scheduling, changing status, or mutating production state.

The current local packet-prep tranche is:

`Project Miner PM Intake Approval Packet Preview Export`

PM Lane 048 adds a browser-only `Export Approval Preview JSON` action to `/pm-review/import-intake`. It combines the current candidate identity, approval contract, storage plan, local review checklist, local approval-decision draft, and future packet boundary into one structured artifact. This gives the later admitted approval-persistence lane a precise input shape while keeping Jason out of the relay loop and still creating no approval record, persistence, import, assignment, schedule, status, hosted proof, or production mutation.

The current design-admission tranche is:

`Import Candidate Approval Persistence Schema And Adapter Admission - Design Only`

PM Lane 049 authors the design-only packet and handoff for the future `seam.pm_import_candidate_approvals` table and explicit insert-only approval adapter. It uses the Lane 048 preview JSON shape as the input contract and records columns, constraints, adapter validation, evidence requirements, hosted-parity blockers, and guardrails. This reduces later executor ambiguity while still creating no SQL file, schema migration, backend route, approval record, import mutation, assignment, schedule, status, hosted proof, or production mutation.

The current UI acceleration tranche is:

`Project Miner Approval Persistence Readiness Gates`

PM Lane 050 adds an `Approval Persistence Readiness` panel to `/pm-review/import-intake` so Jason does not have to infer the current approval-persistence blockers from packet documents alone. The workbench now shows local preview context and checklist evidence as ready-able gates, while hosted parity closeout, schema authority, approval persistence authority, and import mutation authority remain visibly blocked.

This reduces relay burden for the later persistence executor while still creating no approval record, SQL, schema migration, backend route, import mutation, assignment, schedule, status, hosted proof, or production mutation.

The current day-to-day queue tranche is:

`Project Miner Local PM Operating Queue`

PM Lane 051 adds a browser-local `Local PM Operating Queue` near the top of `/pm-review/import-intake`. The queue derives complete, next, and blocked PM review moves from the local checklist, local approval-decision draft, and approval-persistence readiness gates. This gives Jason a practical first-pass work order without creating live tasks or requiring another chat relay.

This still creates no approval record, SQL, schema migration, backend route, import mutation, assignment, schedule, status, hosted proof, or production mutation.

The next persistence tranche is:

`Import Candidate Approval Persistence Schema And Adapter Implementation`

That future tranche should add the dedicated schema and adapter only after hosted reads are current or the Render blocker is precisely classified and the Lane 049 admission packet is explicitly accepted. It must still avoid project, workpackage, task, apparatus, assignment, schedule, and status writes.

The success standard is not just technical correctness. The candidate must reduce Jason's review burden by showing:

1. what the system thinks the project is,
2. what tasks and apparatus it proposes,
3. what source rows and drawings each proposal came from,
4. what looks duplicated or risky,
5. what needs a human decision before import.

## Success Standard

This acceleration lane succeeds when Jason can move a real project from intake toward field execution by reviewing exceptions and approving bounded artifacts, rather than manually coordinating agents, interpreting raw workbook structure, translating between platforms, or rebuilding project state by hand.
