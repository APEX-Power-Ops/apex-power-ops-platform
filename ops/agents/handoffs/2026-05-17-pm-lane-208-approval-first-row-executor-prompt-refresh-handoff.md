# PM Lane 208 - Approval First-Row Executor Prompt Refresh Handoff

## Summary

PM Lane 208 is executed as a no-code executor-prompt refresh lane. It updates the future first approval-row copy/paste prompt and closeout checklist selected by PM Lane 207 while keeping the live approval POST unopened.

The exact PM Lane 142 phrase remains required before any future live approval POST or first approval-row creation.

Current decision: `executor_prompt_refreshed_live_write_not_admitted`.

## Changed Files

- `PROJECT_STATUS.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `docs/operations/APEX-PM-LANE-208-APPROVAL-FIRST-ROW-EXECUTOR-PROMPT-REFRESH-2026-05-17.md`
- `ops/agents/packets/draft/2026-05-17-pm-lane-208-approval-first-row-executor-prompt-refresh.json`
- `ops/agents/handoffs/2026-05-17-pm-lane-208-approval-first-row-executor-prompt-refresh-handoff.md`
- `ops/agents/handoffs/2026-05-17-pm-lane-208-approval-first-row-executor-prompt-refresh-copy-paste-prompt.md`

## Refreshed Executor Boundary

The refreshed prompt makes the stop/proceed branch explicit:

- If the exact PM Lane 142 phrase is absent as a current instruction, the executor must stop with `STOPPED_NO_LIVE_ADMISSION`.
- If the exact PM Lane 142 phrase is present as a current instruction, the future executor may proceed only through the bounded first-row browser approval path: one approval POST, one same-payload idempotent replay, approval-status readback, unchanged downstream counts, and secret-free closeout.

The phrase appearing inside prompt guardrail text does not count as admission.

The closed PM Lane 142 executor prompt is retained unchanged for provenance. The Lane 208 copy/paste prompt is the refreshed future-executor surface unless a later technical-authority packet supersedes it.

## Validation

- PM Lane 208 packet JSON parse
- PM Lane 208 guardrail `rg`
- Null-byte check on PM status docs and PM Lane 208 artifacts
- `git diff --check`

Result: PASS.

## Sidecar Use

Read-only sidecar Banach pressure-tested the refreshed prompt/checklist shape against PM Lane 142, PM Lane 207, current PM status docs, and PM import-intake UI/test references. Banach agreed PM Lane 208 should remain a no-code executor prompt refresh and recommended the prompt/checklist include source floor checks, authoritative Lane 141 through Lane 147 and Lane 207 inputs, exact-phrase stop behavior, current candidate proof, local mocked zero-mutation proof, hosted/readback evidence, conditional one-POST/idempotent-replay/readback proof, unchanged downstream-count proof, and secret-free closeout.

VS Code Codex retained PM lane technical authority and final integration authority.

## Guardrails

- No product code or UI element.
- No localStorage key/schema or sessionStorage key/schema.
- No export artifact in the product UI, link, button, input, textarea, select, handler, backend route, read seam, write seam, SQL, schema migration, hosted service call, live approval POST, approval row, project import, field authorization, lead selection, crew assignment, schedule/status write, field instruction, durable field record, production tracking row, customer report, billing/payroll/invoice/accounting output, workbook macro/writeback, or autonomous AI business-state mutation.

## Next Recommended Lane

Default safe next move:

`PM Lane 209 - Approval First-Row No-Admission Stop Drill`

That lane would test the refreshed prompt by proving a future executor stops cleanly when the exact PM Lane 142 phrase is absent.

Live first-row execution remains available only if Jason explicitly provides the exact PM Lane 142 phrase as current admission.
