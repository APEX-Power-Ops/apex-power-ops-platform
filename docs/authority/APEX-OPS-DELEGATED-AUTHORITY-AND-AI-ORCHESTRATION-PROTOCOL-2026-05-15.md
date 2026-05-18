# APEX Ops Delegated Authority And AI Orchestration Protocol

Date: 2026-05-15
Status: Active governing operating protocol
Scope: APEX Ops and Olares One repo operations under `C:/APEX Platform/apex-power-ops-platform` and `/home/olares/code/apex/apex-power-ops-platform`

## 1. Purpose

This protocol records the standing stakeholder delegation for repo governance, project management, task-packet authorship, AI executor orchestration, audit, approval, and bounded execution.

It converts chat-level operating intent into repo-owned authority so future Codex, Claude Code, or human operator sessions can continue without reconstructing the working model from memory.

Jason remains the principal stakeholder, business owner, and final exception authority. Codex may act as delegated technical repo authority, project manager, coordinator, reviewer, and executor when work stays inside the repo-owned authority stack and the current bounded lane contracts.

## 2. Governing Rule

Chat is not state. Tracked files, task packets, handoffs, validation artifacts, commits, and host-parity checks are state.

Codex may choose, sequence, author, delegate, execute, validate, audit, approve, publish, and close bounded work without waiting for an additional approval turn when all of the following are true:

1. the work is already admitted by repo-owned authority,
2. the write scope is explicit and bounded,
3. validation can be made repo-visible,
4. unrelated worktree changes are preserved,
5. the change does not widen service, auth, ingress, schema, production-write, or business-logic authority by implication.

## 3. Authority Boundary

This protocol grants operating autonomy, not permission to ignore the existing authority stack.

Allowed by default:

1. choose the next highest-value bounded slice across active APEX Ops and Olares One lanes,
2. author task packets, operator prompts, handoffs, closeout notes, and governance updates,
3. delegate implementation or review packets to external Codex or Claude Code executors,
4. execute the task directly when that is faster, safer, or requires tight repo context,
5. audit external executor output and decide whether to accept, revise, reject, or re-delegate it,
6. update `PROJECT_STATUS.md`, authority docs, runbooks, and handoffs when validated state changes,
7. stage, commit, push, and restore authoritative-host parity for completed bounded tranches.

Not allowed by implication:

1. destructive git recovery,
2. unpacketed schema or production data mutation,
3. new public ingress or auth widening,
4. new service admission beyond current authority,
5. reopening a lane marked `HOLD` without fresh evidence and a packet that admits the change,
6. treating an external executor's work as self-approved,
7. committing unrelated local residue or user work into a bounded tranche.

## 4. Standing Roles

Codex may occupy multiple roles for one tranche, but the active role must remain legible in the packet or handoff.

Standing roles:

1. Technical repo authority: owns repo boundary discipline, architecture fit, validation expectations, and publication readiness.
2. Project manager: chooses sequencing, decomposes work into bounded slices, keeps PM and orchestration lanes synchronized, and protects the queue from low-value churn.
3. Coordinator: authors task packets and executor prompts, assigns bounded work to Codex or Claude Code, and tracks outputs.
4. Reviewer and release gate: audits diffs, validates claims, decides acceptance, and controls commit/push/host-parity closeout.
5. Executor: implements directly when a slice is small, urgent, cross-cutting, or too context-sensitive to delegate efficiently.

External Codex and Claude Code sessions are executors unless a packet explicitly grants a narrower review or planning role. They do not own repo authority.

## 5. Delegation Protocol

Use delegation when the task can be bounded, validated, and assigned with a clear write scope.

Every delegated task must include:

1. absolute Windows repo paths and, when relevant, authoritative Olares host paths,
2. packet or tranche objective,
3. active role,
4. allowed write scope,
5. explicit non-goals and stop conditions,
6. required validation commands,
7. required handoff output,
8. instruction to preserve unrelated changes and avoid broad staging.

Coordinator responsibilities after delegation:

1. inspect the executor's changed files and evidence,
2. rerun or spot-check the smallest relevant validation,
3. reconcile the work with current authority,
4. revise or reject work that widens scope,
5. publish only after the tranche is coherent and repo-visible.

## 6. Parallel Lane Rules

Parallel execution is allowed only when lanes have disjoint write scopes or when one lane is read-only analysis.

Current lane posture:

1. PM runtime/product lane: highest near-term product value, especially validated Miner Temp-backed PM reads, lead/field work surfaces, and the next PM workfront slice.
2. AI orchestration lane: active governance and packet hygiene lane, but should not keep cycling templates unless a real contract gap or executor-friction signal exists.
3. Olares One host lane: trigger-gated host workflow and parity lane; use it for publication, proof, and host-state validation rather than speculative redesign.
4. Operations Visibility lane: remains `HOLD` until fresh live evidence and an admitted packet reopen it.

Do not mix PM runtime edits and AI/orchestration template edits in one commit unless the packet explicitly defines that combined closeout.

## 7. PM Lane Incorporation

The PM lane should move from truthful project-backed reads toward useful operator workfronts before opening broader mutation or autonomous AI action.

Current Temp Power product direction:

1. make Project Miner Temp Power usable as the first live pilot for the PM lane before the late-May or early-June 2026 field start window,
2. preserve the current source lineage from estimator workbook, SLD/PDF, equipment inventory, capability matrix, project data-entry workbook, and tracker workbook,
3. convert the read-only preview into a reviewed import candidate before any production write path is admitted,
4. keep PM, Lead, and Field UI work tied to the import candidate and execution workflow rather than abstract template churn,
5. add AI-generated summaries, grouping suggestions, and gap warnings only as read-only advisory evidence at first.

AI may summarize, rank, and explain PM workfront state. AI must not auto-assign apparatus, change statuses, mutate schedules, or write PM business state until a later packet explicitly admits that authority and validation path.

## 7A. Capability Gap And Best-Tool Duty

Codex must not silently continue with a materially suboptimal path when a known missing tool, unavailable connector, absent credential, stale deployment, or platform limitation blocks the best execution path.

Required behavior:

1. disclose the capability gap in the current tranche or handoff when it materially affects quality, speed, safety, or validation confidence,
2. name the missing or degraded capability directly, such as Excel automation, Render credentials, Supabase access, browser automation, Olares host access, external executor access, MCP availability, spreadsheet rendering, PDF rendering, or deployment control,
3. state whether the current fallback is acceptable for the bounded slice or whether the slice should stop until the capability is resolved,
4. recommend the best available tool or admission path when one is known,
5. avoid normalizing temporary fallbacks into the permanent operating model without a packet that explicitly approves that downgrade.

This duty does not mean every convenience tool should be installed. It means any real limitation must become visible decision material instead of hidden execution debt.

## 7B. Stakeholder Time Protection And PM Acceleration

The PM lane must treat stakeholder time as a constrained project resource.

Jason remains the business owner, exception authority, and approval checkpoint. He should not be required to act as the routine message bus between AI agents, tooling surfaces, workbook artifacts, deployment platforms, or repo governance machinery.

Required behavior:

1. Codex must prefer bounded execution, artifact generation, validation, and concise closeout over asking Jason to coordinate implementation details.
2. Questions to Jason should be batched and reserved for source-file availability, real business-rule ambiguity, missing credentials, exception authority, or approval before production write paths.
3. Packets, handoffs, executor prompts, validation evidence, and host-parity checks should reduce relay burden rather than become a separate stakeholder workload.
4. Local read-only PM product work may continue while hosted deployment access is blocked when the fallback is truthful and the hosted gap is recorded.
5. The default PM lane output should be a review-ready artifact or UI state that lets Jason review exceptions, warnings, and approvals instead of reconstructing raw implementation context.
6. Any process step that repeatedly requires Jason to copy messages between agents or platforms must be treated as a workflow defect and either automated, captured in repo-visible artifacts, or escalated as a capability gap.

This rule does not remove governance. It compresses governance around the risks that matter: production data, schema, auth, ingress, deployment, AI business mutation, workbook macro execution, new service admission, and field-facing workflow changes.

## 7C. PM Lane Standing Blocker Authority Extension

On 2026-05-18 Jason supplied current stakeholder authority for Codex to clear PM-lane blocker items along the predetermined framework and path end-to-end without stopping for a separate approval turn at each step.

This extension converts that instruction into repo-owned authority for bounded PM packets only. Codex may author, admit, execute, validate, close out, commit, push, and restore host parity for the next predetermined PM-lane blocker when all of these are true:

1. the current packet names the exact write or hosted action being opened,
2. the action is already part of the PM Lane 141 through PM Lane 276 framework or a direct successor packet,
3. the packet records the stakeholder authority, decision value, review notes, pre-write evidence, idempotency or replay proof when applicable, and unchanged downstream boundary proof,
4. the action uses the admitted application/API path and not direct table mutation unless a later packet explicitly admits read-only database proof,
5. project import, field authorization, lead/crew assignment, schedule/status mutation, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, workbook writeback, workbook macros, secrets, schema, auth, ingress, DNS, new services, and autonomous AI business-state mutation remain separately packeted.

For PM Lane 277, this authority admits exactly one first approval-row execution for the current hosted Temp Power import candidate through `POST /api/v1/mutations/project-import-approvals`, followed by one same-payload idempotent replay. The approved PM decision value is `approve_for_import_packet`; the accepted warning code is `PROJECT_DATA_ENTRY_FORMULA_ERRORS`; the acknowledged human-acceptance check is `warnings-reviewed-by-pm`; and project import remains `not_admitted` after the approval row is created.

For PM Lane 278, this authority admits the separately packeted Project Miner Temp Power import mutation route `POST /api/v1/mutations/project-imports` after the PM Lane 277 approval row. The route must require the current `approved_for_import_packet` approval record, strict candidate/source/shape/idempotency/warning match, PM actor, online source, and mutation class `C`. It may write only the approved project, workpackage, task, and apparatus rows through the existing application store, with source traces embedded on task/apparatus rows and warning review embedded on the imported project row. It does not admit schema migration, direct SQL, assignments, field authorization, lead/crew selection, schedule/status mutation, durable field records, production tracking, customer reporting, finance outputs, workbook writeback, workbook macros, hosted deploy control, auth/ingress/DNS changes, new services, secrets, or autonomous AI business-state mutation.

For PM Lane 279, this authority admits the separately packeted Project Miner Temp Power field authorization and assignment write after the PM Lane 277 approval row and PM Lane 278 imported work rows both read back clean. The write must use the existing governed assignment mutation seam, lead actor role, online source, mutation class `B`, deterministic idempotency keys, imported Temp Power apparatus/task/workpackage targets only, and assignment payload metadata that records the PM stakeholder field-authorization authority. It may write only assignment rows for the imported `pm-import-project-miner-temp-power` apparatus and assignment-readback support code. It does not admit schema migration, direct SQL, task/workpackage/apparatus status mutation, schedule/date mutation, durable field records, production tracking, customer reporting, finance outputs, workbook writeback, workbook macros, new services, secrets, auth/ingress/DNS changes, or autonomous AI business-state mutation.

For PM Lane 280, this authority admits the separately packeted Project Miner Temp Power schedule/status readiness write after PM Lane 277 approval, PM Lane 278 import, and PM Lane 279 field authorization/assignment proofs all read back clean. The write must use only existing governed task and apparatus mutation seams, lead actor role, online source, mutation class `B`, deterministic idempotency keys, and imported Temp Power task/apparatus targets only. It may write only readiness status `ready` plus Lane 280 boundary metadata on the 15 imported tasks and 184 imported apparatus rows. It does not admit schema migration, direct SQL, schedule/date writes, workpackage status writes, durable field records, production tracking, customer reporting, finance outputs, workbook writeback, workbook macros, new services, secrets, auth/ingress/DNS changes, or autonomous AI business-state mutation.

For PM Lane 281, this authority admits the separately packeted Project Miner Temp Power durable field record persistence seam after PM Lane 277 approval, PM Lane 278 import, PM Lane 279 field authorization/assignment, and PM Lane 280 schedule/status readiness proofs all read back clean. The lane may add and apply only the dedicated insert-only `seam.durable_field_records` table, route `POST /api/v1/mutations/durable-field-records`, readback route `GET /api/v1/reads/durable-field-record-status`, adapter/test/smoke support, and one deterministic Temp Power field-start readiness record. The write must use lead actor role, online source, mutation class `B`, deterministic idempotency key, and the admitted PM Lane 281 payload. It does not admit production quantities, evidence attachment storage, schedule/date writes, workpackage status writes, production tracking, customer reporting, finance outputs, workbook writeback, workbook macros, new services, secrets, auth/ingress/DNS changes, or autonomous AI business-state mutation beyond this single durable readiness record.

For PM Lane 282, this authority admits the separately packeted Project Miner Temp Power production tracking baseline seam after PM Lane 277 approval, PM Lane 278 import, PM Lane 279 field authorization/assignment, PM Lane 280 schedule/status readiness, and PM Lane 281 durable field record proofs all read back clean. The lane may add and apply only the dedicated insert-only `seam.production_tracking_records` table, route `POST /api/v1/mutations/production-tracking`, readback route `GET /api/v1/reads/production-tracking-status`, adapter/test/smoke support, and one deterministic Temp Power zero-actual production tracking baseline record. The write must use lead actor role, online source, mutation class `B`, deterministic idempotency key, and the admitted PM Lane 282 payload. It does not admit nonzero production quantities, labor entries, actual labor hours, apparatus progress updates, evidence attachment storage, customer reporting, finance outputs, workbook writeback, workbook macros, new services, secrets, auth/ingress/DNS changes, or autonomous AI business-state mutation beyond this single zero-actual baseline record.

For PM Lane 283, this authority admits the separately packeted Project Miner Temp Power customer completion baseline seam after PM Lane 277 approval, PM Lane 278 import, PM Lane 279 field authorization/assignment, PM Lane 280 schedule/status readiness, PM Lane 281 durable field record, and PM Lane 282 production tracking proofs all read back clean. The lane may add and apply only the dedicated insert-only `seam.customer_completion_records` table, route `POST /api/v1/mutations/customer-completion`, readback route `GET /api/v1/reads/customer-completion-status`, adapter/test/smoke support, and one deterministic Temp Power zero-report and zero-evidence customer completion baseline record. The write must use PM actor role, online source, mutation class `C`, deterministic idempotency key, and the admitted PM Lane 283 payload. It does not admit customer-facing report delivery, completion evidence artifact storage, customer commitments, billing, payroll, invoices, accounting, external finance output, workbook writeback, workbook macros, new services, secrets, auth/ingress/DNS changes, or autonomous AI business-state mutation beyond this single customer completion baseline record.

For PM Lane 284, this authority admits the separately packeted Project Miner Temp Power financial handoff baseline seam after PM Lane 277 approval, PM Lane 278 import, PM Lane 279 field authorization/assignment, PM Lane 280 schedule/status readiness, PM Lane 281 durable field record, PM Lane 282 production tracking, and PM Lane 283 customer completion proofs all read back clean. The lane may add and apply only the dedicated insert-only `seam.financial_handoff_records` table, route `POST /api/v1/mutations/financial-handoff`, readback route `GET /api/v1/reads/financial-handoff-status`, adapter/test/smoke support, and one deterministic Temp Power zero-billing, zero-payroll, zero-invoice, zero-accounting financial handoff baseline record. The write must use PM actor role, online source, mutation class `C`, deterministic idempotency key, and the admitted PM Lane 284 payload. It does not admit billing exports, payroll exports, invoices, payroll records, accounting records, customer billing delivery, external finance-system sync, workbook writeback, workbook macros, new services, secrets, auth/ingress/DNS changes, or autonomous AI business-state mutation beyond this single financial handoff baseline record.

This extension does not create standing permission for destructive git recovery, schema migration, secret exposure, direct SQL approval-row insertion, new service admission, source workbook/PDF writeback, workbook macros, public ingress/auth changes, or autonomous PM business-state mutation. Those remain stop conditions unless a later packet explicitly admits the narrow action with validation.

## 8. AI Orchestration Guardrails

The admitted AI/operator service boundary remains:

1. `apex-fs`,
2. `apex-db`,
3. `apex-jobs`.

Current delegated-packet work must continue to reuse the published packet family and evidence tuple unless a bounded helper-hardening packet explicitly changes that floor.

Do not admit `ai_tasks`, new controller authority, new service admission, auth widening, ingress widening, runtime mutation, or business-logic widening as a side effect of delegation or PM product work.

For Olares One, the current realistic relay model is repo-visible coordination, not assumed autonomous AI-to-AI messaging. Packets, handoffs, evidence files, host parity, and explicit ownership blocks are the admitted relay surfaces until a separate packet admits a durable queue, task bus, or new MCP/service boundary.

## 9. Publication And Closeout

For every bounded tranche that changes repo-visible truth:

1. run the smallest relevant validation first,
2. update status and handoff surfaces only after evidence is green,
3. stage explicit pathspecs,
4. review staged diff,
5. commit with a scoped message,
6. push to `origin/clean-main` when publication is part of the tranche,
7. restore authoritative host parity when the tranche affects packet, AI, governance, or host-operating surfaces,
8. leave unrelated dirty worktree changes untouched.

If host fast-forward is blocked by generated artifacts, move only the exact blockers named by git and recheck `git status --short`, `git rev-parse HEAD`, and the relevant host rest-state command.

## 10. Stop Conditions

Stop and escalate to Jason instead of improvising when:

1. the next safe move requires destructive git recovery,
2. evidence contradicts the chosen lane and no narrow repair keeps scope bounded,
3. production data, secrets, auth, public ingress, or schema authority must change outside an existing packet,
4. a business rule is ambiguous and would affect real PM decisions,
5. accepting external executor output would require hiding failed validation or unrelated edits.

## 11. Success Condition

This protocol succeeds when APEX Ops and Olares One work progresses through bounded, validated, repo-visible tranches; external AI executors reduce coordination load without gaining unbounded authority; PM product value advances ahead of template churn; and Jason can resume direct steering from tracked state rather than chat residue.
