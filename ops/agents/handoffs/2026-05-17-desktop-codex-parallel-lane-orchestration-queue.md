# Desktop Codex Parallel Lane Orchestration Queue

Date: 2026-05-17
Status: Active governance framework under VS Code Codex technical authority; Relay and NETA source-map proofs accepted

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
| NETA Study Material | Prepare Level II Electrical Fundamentals pilot content audit decision after source-map closeout | Band A/B | Desktop Codex or sidecar executor | One future closeout only if pilot audit packet is admitted | Shared code, package files, product UI, repo-wide status, credentials, hosted services, macros | Pilot file map, pass/warn/block audit table, citation/KSA/schema gap list | VS Code Codex review only if shared repo/product surfaces are touched | READY_FOR_JASON_DECISION for Level II pilot audit | Decide whether to admit NETA Level II pilot content audit | Conditional |
| TCC | Produce a scout packet that maps requirements, interfaces, dependencies, and integration risks | Band A | Desktop Codex or sidecar executor | A future lane-owned handoff only unless separately admitted | Shared service contract changes, schema, API, auth, deployment, production workflow, credentials | Requirements map, interface map, dependency/risk list | VS Code Codex architecture review at integration boundary | HOLD_NOT_ADMITTED until NETA pilot audit proof is accepted or Jason reprioritizes TCC | Wait for NETA pilot audit closeout before default assignment | Conditional |
| Relay | Measure relay burden and improve handoff/prompt governance without admitting autonomous runtime | Band A/B | Desktop Codex or sidecar executor | `ops/agents/handoffs/2026-05-17-desktop-codex-relay-review-burden-closeout.md` only | Autonomous queue ownership, new MCP services, always-on runtime, controller widening, credentials | Burden observations, template recommendations, stop-condition checklist | VS Code Codex review before orchestration widening | Accepted by VS Code Codex | Use closeout recommendation to admit NETA next | Required before widening |

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

Desktop Codex Relay proof, first NETA scout proof, and NETA source-map/artifact-backlog proof are accepted. The next recommended non-PM move is a NETA Level II Electrical Fundamentals pilot content audit, not broad content generation or source-domain editing. TCC remains `HOLD_NOT_ADMITTED` until that pilot audit proves the same relay-load reduction and evidence-compression pattern or Jason explicitly reprioritizes TCC.
