# Desktop Codex Parallel Lane Orchestration Queue

Date: 2026-05-17
Status: Active governance framework under VS Code Codex technical authority; Relay, NETA source-map, Resources cleanup/archive, and external archive policy scout proofs accepted

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
| PM Temp Power | Keep Project Miner PM lane moving toward first governed approval-row execution and field-ready workflow | Band C only where packet-approved | VS Code Codex primary; Desktop Codex support only | Only packet-approved PM support notes or handoffs | PM business-state mutation, Supabase writes, schema, hosted deploy, approval POST, import mutation, schedule/status writes | PM lane packet validations and hosted smokes owned by VS Code Codex | Jason approval for business workflow and live writes | Active priority | STOPPED at `STOPPED_AWAITING_RENDER_AUTHENTICATED_SOURCE_PLACEMENT_OR_SNAPSHOT_ENV_DEPLOY_NO_APPROVAL_POST`; PM Lane 275 implements the env-gated snapshot loader fallback. Next movement requires authenticated Render source placement or hosted snapshot env deployment/readback proof | Always required |
| NETA Study Material | Apply README-only external governed source archive policy wording after approved Resources cleanup/archive findings; topic-spine comparative audit remains parked behind this policy patch | Band B | Desktop Codex or sidecar executor | `Resources/README.md` and one executor closeout only | Shared code, package files, product UI, repo-wide status, credentials, hosted services, macros, source PDF/workbook contents, manifest regeneration, restore/delete work | Resources docs/manifest approval, Box archive filename/count reconciliation, proposed archive policy wording, VS Code approval for README-only patch | VS Code Codex review required after README patch closeout and before any commit/publish | READY_FOR_JASON_DECISION for README-only policy patch dispatch | Dispatch `Desktop Codex NETA External Source Archive README Policy Patch Executor` | Required after source-domain edit |
| TCC | Produce a scout packet that maps requirements, interfaces, dependencies, and integration risks | Band A | Desktop Codex or sidecar executor | A future lane-owned handoff only unless separately admitted | Shared service contract changes, schema, API, auth, deployment, production workflow, credentials | Requirements map, interface map, dependency/risk list | VS Code Codex architecture review at integration boundary | HOLD_NOT_ADMITTED until NETA comparative audit proof is accepted or Jason reprioritizes TCC | Wait for NETA comparative audit closeout before default assignment | Conditional |
| Relay | Measure relay burden and improve handoff/prompt governance without admitting autonomous runtime | Band A/B | Desktop Codex or sidecar executor | `ops/agents/handoffs/2026-05-17-desktop-codex-relay-review-burden-closeout.md` only | Autonomous queue ownership, new MCP services, always-on runtime, controller widening, credentials | Burden observations, template recommendations, stop-condition checklist | VS Code Codex review before orchestration widening | Accepted by VS Code Codex | Use closeout recommendation to admit NETA next | Required before widening |

## PM Support Dispatch Register

Desktop Codex PM support remains subordinate to VS Code Codex technical authority. PM support dispatches are not non-PM orchestration governance and do not grant PM decision authority.

| Support Item | Objective | Authority Band | Executor | Allowed Writes | Forbidden Surfaces | Validation Evidence | Approval Gate | Status | Next Decision | VS Code Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PM-256-SCOUT | Review PM Lane 256 state selector for exact-label gate clarity, cue-saturation risk, relay-burden reduction, and authority-boundary risk | Band A PM support | Desktop Codex support only | `ops/agents/handoffs/2026-05-17-desktop-codex-pm-lane-256-state-review-next-move-selector-scout-closeout.md` only | Product code, tests, docs, packet files, other handoffs, hosted services, workbook/PDF content, macros, PM decisions, warning acceptance, approval/import, resources, schedule/status, business-state mutation | PM Lane 257 dispatch packet plus PM Lane 258 no-closeout intake hold, PM Lane 259 active-return register, PM Lane 260 continuation loop guard, PM Lane 261 return-kit refresh, PM Lane 262 exact-label intake, PM Lane 263 evidence gate, PM Lane 264 revised non-blocking acceptance intake, PM Lane 265 accepted-warning approval-readiness ledger, PM Lane 266 true live-admission blocker packet, PM Lane 267 hosted candidate mismatch hold, PM Lane 268 hosted source strategy decision review, PM Lane 269 continuation classifier, PM Lane 270 source-files/env repair dispatch, PM Lane 271 delegated no-live blocker authority plus signed snapshot scout, PM Lane 272 exporter design, PM Lane 273 local exporter script, PM Lane 274 runtime snapshot export, and PM Lane 275 snapshot loader fallback | VS Code Codex review after closeout | IN_PROGRESS_GOVERNED_SCOUT_AWAITING_CLOSEOUT | Await the PM Lane 256 read-only scout closeout separately; PM Lane 275 does not infer a Desktop Codex result and does not grant Desktop Codex PM decision authority | Required |

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

Desktop Codex Relay proof, first NETA scout proof, revised NETA source-map/artifact-backlog proof, NETA Resources cleanup/archive findings, and NETA external source archive policy scout are accepted. The next approved non-PM move is a README-only `Desktop Codex NETA External Source Archive README Policy Patch Executor`, not content generation, restore work, delete work, manifest regeneration, archive indexing, or cleanup commit. The previously recommended `NETA Topic Spine Comparative Audit - Electrical Fundamentals` remains parked until the README-only policy patch returns clean or Jason explicitly reprioritizes. TCC remains `HOLD_NOT_ADMITTED` until NETA proves the same relay-load reduction and evidence-compression pattern or Jason explicitly reprioritizes TCC.
