# PM Lane 196 - PM Intake Field Start Lead/Resource Clarification Bring-Back Lens Handoff

## Summary

PM Lane 196 is executed as the local PM Intake Field Start Lead/Resource Clarification Bring-Back Lens tranche. The `/pm-review/import-intake` workbench now adds a browser-local `Local Field Start Lead/Resource Clarification Bring-Back Lens` directly after the customer/site clarification lens inside the customer/site questions panel.

The lens helps Jason classify returned field-start lead/resource conversation items before any later bounded packet. It stays read-only and covers lead conversation source, crew readiness, material/equipment clarification, staging/resource limits, and lead/resource authority stop-line context.

## Implementation

Changed `apps/operations-web/app/pm-review/import-intake/page.tsx` to derive a five-item lead/resource clarification lens from the existing field questions draft and field observation scratchpad. The new section links only to already-existing local review anchors: `#field-prep` and `#guardrails`.

Changed `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts` to prove desktop presence, 390x844 mobile visibility, lens copy, five links, zero buttons, no lead/resource clarification lens localStorage key, no implied-authority link/control text, and zero mutation calls.

Updated PM status and operating-plan docs so the repo-visible PM lane context is local-current through PM Lane 196.

## Guardrails

This lane adds no meeting-note capture, export button, handler, route, backend seam, payload version, localStorage schema, hosted call, approval POST, approval row, project import, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, service/auth/ingress change, workbook macro/writeback, or autonomous AI business-state mutation.

The section is a browser-local clarification lens only. If a returned lead/resource answer needs a task, action item, owner, due date, assignment, timing field, schedule/status write, durable record, production tracking, report, export, backend route, storage key, button, or write authority, the UI copy tells the PM to stop and author a later bounded packet.

## Dual-Lane Use

Read-only sidecar Volta was used for proof-shaping only. It recommended the adjacent placement, five-item lens shape, intro copy, link targets, negative storage regex, and copy-risk boundary. VS Code Codex retained PM lane implementation, validation, and final integration authority.

## Validation

- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck`
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"`
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build`
- Packet JSON parse check
- PM Lane 196 guardrail `rg`
- Null-byte check on PM status docs
- `git diff --check`

## Next Recommended PM Move

PM Lane 197 should close the fourth bring-back queue bucket with a browser-local `Field Start Later Bounded Packet Candidate Bring-Back Lens`. It should help Jason classify returned items that need a later bounded packet without creating tasks, action items, owners, due dates, assignments, schedule/status writes, durable records, production tracking, reports, exports, storage keys, routes, buttons, or write paths.
