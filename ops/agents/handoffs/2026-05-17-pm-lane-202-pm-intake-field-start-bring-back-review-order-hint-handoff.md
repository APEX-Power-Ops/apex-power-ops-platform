# PM Lane 202 - PM Intake Field Start Bring-Back Review Order Hint Handoff

## Summary

PM Lane 202 is executed as the local PM Intake Field Start Bring-Back Review Order Hint tranche. The `/pm-review/import-intake` workbench now adds a browser-local `Review order hint` inside the existing `Local Field Start Bring-Back Detail Jump Rail`, directly after the Lane 200 open-context cue and before the Lane 201 status legend and Lane 199 lens links.

The hint explains the local review order before Jason opens a bring-back detail lens: source review first, then customer/site clarification, then lead/resource clarification, with later bounded packet candidate used only to classify a future packet question. It is display-only and creates no workflow action, meeting note, localStorage key, sessionStorage key, export artifact, backend route, link, button, task, action item, owner, due date, assignment, customer commitment, report, field instruction, durable field record, production tracking row, hosted write claim, or write path.

## Changed Files

- `apps/operations-web/app/pm-review/import-intake/page.tsx`
- `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts`
- `PROJECT_STATUS.md`
- `docs/operations/APEX-PM-STAKEHOLDER-TIME-PROTECTION-AND-ACCELERATION-LANE-2026-05-15.md`
- `docs/operations/APEX-PM-TEMP-POWER-DELIVERY-AND-ORCHESTRATION-PLAN-2026-05-15.md`
- `docs/operations/PM-LANE-PROJECT-MINER-INTAKE-WORKFLOW-2026-05-15.md`
- `ops/agents/packets/draft/2026-05-17-pm-lane-202-pm-intake-field-start-bring-back-review-order-hint.json`
- `ops/agents/handoffs/2026-05-17-pm-lane-202-pm-intake-field-start-bring-back-review-order-hint-handoff.md`

## Validation

- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck`
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"`
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build`
- PM Lane 202 packet JSON parse
- PM Lane 202 guardrail `rg`
- Null-byte check on PM status docs
- `git diff --check`

Result: operations-web typecheck passed; focused Playwright PM import-intake smoke passed cleanly with the review order hint, `390x844` mobile proof, zero review order hint links, zero review order hint buttons, no localStorage or sessionStorage review order hint keys, no implied-authority link/control text, and zero mutation calls; operations-web production build passed with `/pm-review/import-intake` in the route output. Packet JSON parsed as `2026-05-17-pm-lane-202`; PM Lane 202 guardrail `rg` passed; null-byte check passed on PM status docs; `git diff --check` passed with only expected LF-to-CRLF warnings on touched and unrelated files.

## Sidecar Use

Read-only sidecar Aristotle inspected the current PM import-intake page/test surfaces and recommended a static display-only hint inside the existing detail jump rail, after the open-context cue and before the status legend. VS Code Codex accepted that placement, implemented the bounded slice, and retained PM lane implementation and final integration authority.

## Guardrails

- No meeting-note capture.
- No localStorage key/schema or sessionStorage key/schema.
- No export artifact, link, button, handler, backend route, read seam, write seam, SQL, schema migration, hosted service call, approval POST, approval row, project import, field authorization, lead selection, crew assignment, schedule/status write, field instruction, durable field record, production tracking row, customer report, billing/payroll/invoice/accounting output, workbook macro/writeback, or autonomous AI business-state mutation.

## Next Recommended Lane

PM Lane 203 should add a browser-local future packet boundary reminder only if the later bounded packet candidate lens still needs a clearer stop-line. It should remain display-only and must not create notes, links, buttons, tasks, owners, dates, assignments, reports, exports, storage keys, routes, or write paths.
