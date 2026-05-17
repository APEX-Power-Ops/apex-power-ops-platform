# APEX PM Lane 208 - Approval First-Row Executor Prompt Refresh

Date: 2026-05-17
Status: Completed no-code PM executor-prompt lane
Scope: PM Lane 142 first-row approval executor prompt, PM Lane 207 readiness decision, and future closeout checklist

## Purpose

PM Lane 208 refreshes the first approval-row executor prompt selected by PM Lane 207.

This lane does not admit a live approval POST. It creates clearer copy/paste execution guidance for a later bounded executor so the future run has a sharp stop/proceed split before any browser approval persistence write can occur.

## Current Readiness Basis

The current repo carries this approval-prep chain:

1. PM Lane 141 defines the browser approval submission contract for `POST /api/v1/mutations/project-import-approvals`.
2. PM Lane 142 defines the exact live-write phrase and original first-row execution gate.
3. PM Lane 142A builds a local browser approval dry-run envelope without sending a request.
4. PM Lane 143 exports that envelope as local JSON review context.
5. PM Lane 144 adds a local dry-run readiness checkpoint.
6. PM Lane 145 exports that checkpoint as local JSON review context.
7. PM Lane 146 bundles the envelope plus readiness checkpoint.
8. PM Lane 147 exports the local live-gate preflight while keeping the approval POST blocked.
9. PM Lane 207 records the technical-authority decision that this chain is ready for a refreshed executor prompt only.

## Stop/Proceed Rule

The required PM Lane 142 phrase remains:

`I explicitly admit PM Lane 142 live approval POST and first approval-row creation for the current Project Miner Temp Power import candidate.`

The phrase appearing in a prompt as quoted guardrail text does not count as admission. It must be provided as an explicit current instruction by Jason or by VS Code Codex acting as coordinator.

If that explicit current instruction is absent, a future executor must stop with `STOPPED_NO_LIVE_ADMISSION` after repo-local/read-only validation and must not deploy, call hosted services, send a live approval POST, or create an approval row.

If that explicit current instruction is present, the future executor may proceed only through the bounded Lane 142 first-row path:

1. prove candidate identity, source fingerprint, shape fingerprint, warning-code set, no-go acknowledgement, decision value, and review notes,
2. prove local mocked browser behavior has zero unmocked mutation calls,
3. confirm hosted approval-status readback and approval POST registration if the future packet admits hosted checks,
4. prove pre-submit approval record count for the current candidate,
5. submit exactly one browser approval POST for the current candidate through the UI path,
6. replay the exact same payload once and prove idempotency,
7. prove approval-status readback matches the submitted decision,
8. prove project, workpackage, task, apparatus, assignment, schedule, status, durable field record, and production tracking counts are unchanged,
9. publish a secret-free closeout.

Project import remains blocked in both branches.

## Lane 208 Decision

PM Lane 208 refreshes the future executor prompt and closeout checklist.

It does not perform the future live executor run, because the exact PM Lane 142 phrase is not provided as a current admission in this lane.

The closed PM Lane 142 executor prompt is retained unchanged for provenance. Future execution should use the Lane 208 copy/paste prompt as the current refreshed prompt unless a later technical-authority packet supersedes it.

Decision: `executor_prompt_refreshed_live_write_not_admitted`.

## Orchestration Note

VS Code Codex retained PM lane technical authority and final repo integration authority. Read-only sidecar Banach was assigned to pressure-test the refreshed prompt/checklist shape against PM Lane 142, PM Lane 207, current PM status docs, and PM import-intake UI/test references while making no edits and performing no hosted or live-write action.

Banach agreed PM Lane 208 should remain a no-code executor prompt refresh and recommended the refreshed prompt include source floor checks, authoritative Lane 141 through Lane 147 and Lane 207 inputs, exact-phrase stop behavior, current candidate proof, local mocked zero-mutation proof, hosted/readback evidence, conditional one-POST/idempotent-replay/readback proof, unchanged downstream-count proof, and secret-free closeout.

The sidecar role was advisory only; final scope, edits, validation, publication, and host parity remain under VS Code Codex.

## Guardrails

PM Lane 208 adds no product code, UI control, route, backend seam, payload version, localStorage schema, sessionStorage schema, hosted call, live approval POST, approval row, project import, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, service/auth/ingress change, workbook macro/writeback, or autonomous AI business-state mutation.

## Next PM Direction

Two next moves are available:

1. If Jason wants to keep testing the orchestration layer without opening live writes, run `PM Lane 209 - Approval First-Row No-Admission Stop Drill` against the refreshed prompt and prove the future executor stops cleanly.
2. If Jason explicitly provides the exact PM Lane 142 phrase as a current instruction, run the live first-row executor packet under the refreshed prompt.

The safer default remains the no-admission stop drill.
