# PM Lane 276 - VS Code Copilot Render Completion Dispatch Handoff

Date: 2026-05-18

Decision label:

`PROJECT_MINER_TEMP_POWER_VSCODE_COPILOT_RENDER_COMPLETION_DISPATCH_NO_APPROVAL_POST`

Selected outcome:

`RENDER_COMPLETION_PACKET_AUTHORED_FOR_VSCODE_COPILOT_NO_APPROVAL_POST`

## Objective

Delegate the remaining Render-authenticated work to VS Code Copilot, using its Internal browser to complete and test hosted read-only Temp Power candidate parity.

Current blocker:

`STOPPED_AWAITING_RENDER_AUTHENTICATED_SOURCE_PLACEMENT_OR_SNAPSHOT_ENV_DEPLOY_NO_APPROVAL_POST`

Executor return:

`RENDER_SNAPSHOT_ENV_DEPLOY_PASS_NO_APPROVAL_POST`

Accepted closeout:

`ops/agents/handoffs/2026-05-18-pm-lane-276-vscode-copilot-render-completion-executor-closeout.md`

The Render hosted-read blocker is cleared. Future approval POST, approval-row creation, and project import still require a later explicit live-write packet.

## Executor Prompt

Use:

`ops/agents/handoffs/2026-05-18-pm-lane-276-vscode-copilot-render-completion-executor-copy-paste-prompt.md`

## Preferred Path

Use the PM Lane 275 snapshot-loader path first:

1. confirm the existing Render service `apex-platform-mutation-seam` is deployed at the PM Lane 275 code floor or newer,
2. place the PM Lane 274 runtime snapshot files under a governed hosted runtime or persistent path,
3. set `APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH` to that hosted path,
4. restart or redeploy the existing service,
5. prove hosted candidate and admission-plan reads match Temp Power.

Preferred hosted path:

`/var/data/project-import-snapshots/pm-lane-274-project-miner-temp-power-snapshot-2026-05-18`

## Fallback Path

If snapshot env deployment is blocked but governed source-file storage is already available, Copilot may complete the PM Lane 270 source-files/env repair using the same existing Render service.

The fallback still must stop before approval POST, approval-row creation, project import, Supabase write, SQL, or any PM business-state mutation.

## Required Readback

The executor closeout must prove:

1. candidate id `pm-import-candidate-miner-temp-power`,
2. 7 workpackages,
3. 15 tasks,
4. 184 apparatus candidates,
5. warning code `PROJECT_DATA_ENTRY_FORMULA_ERRORS`,
6. source fingerprint `e111fdbe934bf9de07ed24c1`,
7. shape fingerprint `ddc49565eb586af913ad48b2`,
8. mutation authority `not_admitted`,
9. approval status remains read-only, with no new approval row unless a later packet explicitly creates one.

## Closeout

Copilot must create exactly one closeout:

`ops/agents/handoffs/2026-05-18-pm-lane-276-vscode-copilot-render-completion-executor-closeout.md`

The closeout must include the final outcome label, non-secret Render evidence, validation outputs, and guardrail confirmation.

## Guardrails

This handoff admits Render completion and read-only hosted validation only. It does not admit approval POST, approval row creation, project import, Supabase write, SQL/schema migration, new service creation, public storage, source workbook/PDF commits, workbook/PDF edits, macros, secret exposure, Desktop Codex PM decision authority, or PM business-state mutation.
