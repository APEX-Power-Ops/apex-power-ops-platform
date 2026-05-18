# PM Lane 276 - Project Miner Temp Power VS Code Copilot Render Completion Dispatch

Date: 2026-05-18

Authority: VS Code Codex technical authority for the PM lane with Jason-directed VS Code Copilot execution through authenticated Internal browser access

Decision label:

`PROJECT_MINER_TEMP_POWER_VSCODE_COPILOT_RENDER_COMPLETION_DISPATCH_NO_APPROVAL_POST`

Selected outcome:

`RENDER_COMPLETION_PACKET_AUTHORED_FOR_VSCODE_COPILOT_NO_APPROVAL_POST`

## Purpose

PM Lane 276 creates the handoff packet for VS Code Copilot to complete the remaining Render-hosted requirements that this local shell cannot complete.

The immediate goal is hosted read-only parity for the current Project Miner Temp Power import candidate before any later live approval-row retry.

Current blocker:

`STOPPED_AWAITING_RENDER_AUTHENTICATED_SOURCE_PLACEMENT_OR_SNAPSHOT_ENV_DEPLOY_NO_APPROVAL_POST`

Executor return accepted:

`RENDER_SNAPSHOT_ENV_DEPLOY_PASS_NO_APPROVAL_POST`

The accepted closeout is:

`ops/agents/handoffs/2026-05-18-pm-lane-276-vscode-copilot-render-completion-executor-closeout.md`

VS Code Copilot used Render secret-file storage with:

`APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH=/etc/secrets/candidate.json`

Fresh hosted validation confirmed the current Temp Power candidate and cleared the Render hosted-read blocker. Approval POST, approval-row creation, and project import remain blocked until a later explicit packet.

Target service:

`apex-platform-mutation-seam`

Target base URL:

`https://mutation-seam.apexpowerops.com`

## Execution Decision

VS Code Copilot may use its Internal browser to authenticate to Render, inspect the existing service, use dashboard shell or SSH/SCP where available, update non-secret runtime env vars, restart or redeploy the existing service, inspect logs, and run read-only hosted validation.

Preferred path:

1. deploy the PM Lane 275 snapshot-loader code to the existing Render service if it is not already deployed,
2. place the four PM Lane 274 runtime snapshot files on a governed hosted runtime path,
3. set `APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH` to that hosted snapshot folder,
4. restart or redeploy the existing service,
5. prove hosted readback returns the current Temp Power candidate.

Fallback path:

If the snapshot path is blocked but already-governed source-file storage is available, Copilot may complete the PM Lane 270 hosted source-files/env repair on the same existing service. The fallback still must not create approval rows or import project rows.

## Render Requirements

Current Render docs reviewed for this dispatch:

1. `https://render.com/docs/disks`
2. `https://render.com/docs/deploys`
3. `https://render.com/docs/ssh`
4. `https://render.com/docs/environment-variables`

Operational requirements from those docs:

1. service filesystem changes are ephemeral unless a persistent disk is attached,
2. preserved runtime files must live under the mounted persistent path,
3. `/var/data` is an acceptable standalone mount path pattern when the app can read from an arbitrary runtime folder,
4. file transfer can use authenticated service SSH/SCP or Render dashboard shell tooling,
5. env values are runtime strings and must use hosted paths, not Jason's Windows paths,
6. the service must be restarted or redeployed for runtime env and hosted files to be proven together.

Preferred hosted snapshot path:

`/var/data/project-import-snapshots/pm-lane-274-project-miner-temp-power-snapshot-2026-05-18`

Preferred env value:

`APEX_PROJECT_IMPORT_CANDIDATE_SNAPSHOT_PATH=/var/data/project-import-snapshots/pm-lane-274-project-miner-temp-power-snapshot-2026-05-18`

If a different existing governed Render path is used, the executor closeout must name the non-secret path.

If Render requires a new paid persistent disk, new public storage, new service, new database, new bucket, or other external file authority, Copilot must stop unless Jason explicitly approves that resource inside the authenticated flow. Use:

`BLOCKED_RENDER_STORAGE_REQUIRES_NEW_RESOURCE_NO_APPROVAL_POST`

## Runtime Snapshot Inputs

Local runtime snapshot source:

`C:/APEX Platform/runtime/pm-lane-274-project-miner-temp-power-snapshot-2026-05-18`

Files:

1. `candidate.json`
2. `admission-plan.json`
3. `manifest.json`
4. `SHA256SUMS.txt`

Expected payload hashes:

1. `candidate.json`: `813013d12cab476ffa67cfbb42d0421bc107d5e189a229e2450f490fc9022445`
2. `admission-plan.json`: `b370e6999e9beddc5ae70feca8454052c001dec47dc42fcfc19269d853ce01cd`
3. `manifest.json`: `80a05dcc70728099ee52ff0f80204feee5e6f4102334f919837016ef89b87f95`

Expected hosted readback:

1. candidate id: `pm-import-candidate-miner-temp-power`
2. workpackages: `7`
3. tasks: `15`
4. apparatus candidates: `184`
5. warning code: `PROJECT_DATA_ENTRY_FORMULA_ERRORS`
6. source stat fingerprint: `e111fdbe934bf9de07ed24c1`
7. candidate shape fingerprint: `ddc49565eb586af913ad48b2`
8. mutation authority: `not_admitted`
9. approval status remains no live approval-row execution unless a later packet creates it.

## Allowed Writes

Copilot may write:

1. Render non-secret env vars for the existing `apex-platform-mutation-seam` service,
2. hosted runtime snapshot files under a governed Render runtime or persistent path,
3. service restart or redeploy action for the existing service,
4. exactly one executor closeout file:

`ops/agents/handoffs/2026-05-18-pm-lane-276-vscode-copilot-render-completion-executor-closeout.md`

## Not Allowed

Do not:

1. send `POST /api/v1/mutations/project-import-approvals`,
2. create an approval row,
3. import project rows,
4. write to Supabase,
5. run SQL or schema migrations,
6. create a new Render service,
7. create public file storage,
8. change DNS, custom domains, CORS, auth, ingress, or service topology,
9. print, paste, store, rotate, or modify secret values such as `SEAM_DATABASE_URL` or `JWT_SECRET`,
10. commit source workbooks, source PDFs, runtime snapshots, or hosted payloads to Git,
11. read workbook/PDF contents manually,
12. run workbook macros,
13. write back to source workbooks or source PDFs,
14. mutate task, owner, due-date, resource, schedule, field, customer, production, finance, payroll, invoice, or accounting state.

## Validation Requirement

Copilot must run, record, and close out:

1. source commit tested,
2. Render service name and authenticated surface used,
3. whether snapshot env path or source-files env repair was used,
4. hosted path used, without secrets,
5. env key presence, without secret values,
6. restart or redeploy evidence,
7. deployed mutation-seam PM intake smoke result,
8. paired operations-web PM intake hosted smoke result,
9. direct hosted route readback for candidate, admission plan, and approval status,
10. final outcome label.

Final outcome must be exactly one of:

1. `RENDER_SNAPSHOT_ENV_DEPLOY_PASS_NO_APPROVAL_POST`
2. `RENDER_SOURCE_FILES_ENV_REPAIR_PASS_NO_APPROVAL_POST`
3. `BLOCKED_RENDER_AUTH_UNAVAILABLE_NO_APPROVAL_POST`
4. `BLOCKED_RENDER_STORAGE_REQUIRES_NEW_RESOURCE_NO_APPROVAL_POST`
5. `BLOCKED_RENDER_RUNTIME_FILE_TRANSFER_UNAVAILABLE_NO_APPROVAL_POST`
6. `BLOCKED_RENDER_DEPLOY_OR_RESTART_FAILED_NO_APPROVAL_POST`
7. `BLOCKED_HOSTED_SNAPSHOT_CHECKSUM_OR_AUTHORITY_MISMATCH_NO_APPROVAL_POST`
8. `BLOCKED_HOSTED_CANDIDATE_STILL_NOT_TEMP_POWER_NO_APPROVAL_POST`

## Executor Prompt

Use:

`ops/agents/handoffs/2026-05-18-pm-lane-276-vscode-copilot-render-completion-executor-copy-paste-prompt.md`

## Guardrails

PM Lane 276 is a Render completion dispatch only. It adds no product code, UI section, writable control, button, link, route, handler, backend seam, payload write version, localStorage schema, sessionStorage schema, live approval POST, approval row, project import, note, task, owner/due-date assignment, field authorization, lead/crew assignment, schedule/status write, procurement or rental commitment, customer commitment, field instruction, durable field record, production tracking row, customer report, billing/payroll/invoice/accounting output, external finance-system output, Supabase write, Vercel deploy, Olares action, SQL/schema migration, source workbook writeback, source PDF content edit, workbook content write, workbook macro/writeback, Desktop Codex PM decision authority, secret exposure, or autonomous AI business-state mutation.
