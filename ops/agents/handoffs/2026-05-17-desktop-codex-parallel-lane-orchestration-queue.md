# Desktop Codex Parallel Lane Orchestration Queue

Date: 2026-05-17
Status: Active governance framework under VS Code Codex technical authority; Relay proof admitted first

## Authority Model

VS Code Codex remains technical authority over all APEX Ops lanes, including PM, NETA, TCC, Relay, Olares, hosted services, schema, credentials, and repo integration.

Desktop Codex is admitted as delegated orchestration governor for non-PM parallel lanes only. The role is queue maintenance, packet framing, bounded prompt drafting, sidecar delegation, evidence collection, and readiness classification.

Desktop Codex does not own final repo integration, PM business-state decisions, production execution, schema changes, credentials, hosted services, Olares runtime, MCP admission, or autonomous queue ownership.

## Queue Status Values

- `READY_FOR_VSCODE_REVIEW`
- `READY_FOR_JASON_DECISION`
- `BLOCKED_CAPABILITY_GAP`
- `ABORTED_SCOPE_WIDENING`
- `IN_PROGRESS_GOVERNED_SCOUT`
- `HOLD_NOT_ADMITTED`

## Lane Board

| Lane | Current Objective | Authority Band | Executor | Allowed Writes | Forbidden Surfaces | Validation Evidence | Approval Gate | Status | Next Decision | VS Code Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PM Temp Power | Keep Project Miner PM lane moving toward first governed approval-row execution and field-ready workflow | Band C only where packet-approved | VS Code Codex primary; Desktop Codex support only | Only packet-approved PM support notes or handoffs | PM business-state mutation, Supabase writes, schema, hosted deploy, approval POST, import mutation, schedule/status writes | PM lane packet validations and hosted smokes owned by VS Code Codex | Jason approval for business workflow and live writes | Active priority | Continue PM lane under VS Code Codex | Always required |
| NETA Study Material | Produce a bounded scout/build package for study material organization and question-bank scaffolding | Band A/B | Desktop Codex or sidecar executor | A future lane-owned handoff only unless separately admitted | Shared code, package files, product UI, repo-wide status, credentials, hosted services, macros | Source inventory summary, proposed artifact map, risk list | VS Code Codex review only if shared repo/product surfaces are touched | HOLD_NOT_ADMITTED until Relay proof is accepted | Wait for Relay closeout before assignment | Conditional |
| TCC | Produce a scout packet that maps requirements, interfaces, dependencies, and integration risks | Band A | Desktop Codex or sidecar executor | A future lane-owned handoff only unless separately admitted | Shared service contract changes, schema, API, auth, deployment, production workflow, credentials | Requirements map, interface map, dependency/risk list | VS Code Codex architecture review at integration boundary | HOLD_NOT_ADMITTED until Relay proof is accepted | Wait for Relay closeout before assignment | Conditional |
| Relay | Measure relay burden and improve handoff/prompt governance without admitting autonomous runtime | Band A/B | Desktop Codex or sidecar executor | `ops/agents/handoffs/2026-05-17-desktop-codex-relay-review-burden-closeout.md` only | Autonomous queue ownership, new MCP services, always-on runtime, controller widening, credentials | Burden observations, template recommendations, stop-condition checklist | VS Code Codex review before orchestration widening | READY_FOR_JASON_DECISION for first assignment | Assign Relay prompt as first proof | Required before widening |

## Desktop Codex Stop Conditions

Desktop Codex must stop and return `ABORTED_SCOPE_WIDENING` or `BLOCKED_CAPABILITY_GAP` if work attempts to:

1. change PM business state,
2. write to Supabase,
3. run workbook macros,
4. change schema, auth, ingress, runtime, Render, Vercel, or Olares host posture,
5. add new MCP services,
6. turn `ai_tasks` into an autonomous owner,
7. touch files outside an approved packet,
8. edit shared package or environment files without approval,
9. require Jason to relay raw technical context between agents,
10. require VS Code Codex review before a clean summary and evidence bundle exists.

## Current READY_FOR_JASON_DECISION Summary

Desktop Codex governance is approved to start with the Relay review-burden prompt only. NETA and TCC remain `HOLD_NOT_ADMITTED` until Relay returns a clean, concise closeout that actually reduces Jason's relay load and avoids early VS Code Codex interruption.
