# PM Lane 199 - PM Intake Field Start Bring-Back Detail Jump Rail Handoff

## Summary

PM Lane 199 is executed as the local PM Intake Field Start Bring-Back Detail Jump Rail tranche. The `/pm-review/import-intake` workbench now adds a browser-local `Local Field Start Bring-Back Detail Jump Rail` directly after the Lane 198 summary triage strip and before the detailed bring-back review queue/lenses inside the customer/site questions panel.

The rail helps Jason move from the compact bring-back summary to the exact detail lens during phone-first review. It stays read-only and links only to existing detail lens anchors for source review, customer/site clarification, lead/resource clarification, and later bounded packet candidate review.

## Implementation

Changed `apps/operations-web/app/pm-review/import-intake/page.tsx` to derive a four-link detail jump rail from the existing Lane 198 summary triage context. The new links point only to existing browser-local anchors: source review lens, customer/site clarification lens, lead/resource clarification lens, and later bounded packet candidate lens.

Changed `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts` to prove desktop presence, 390x844 mobile visibility, jump-rail copy, four links, zero buttons, no bring-back detail jump rail localStorage key, no implied-authority link/control text, and zero mutation calls.

Updated PM status and operating-plan docs so the repo-visible PM lane context is local-current through PM Lane 199.

## Guardrails

This lane adds no meeting-note capture, export button, handler, route, backend seam, payload version, localStorage schema, hosted call, approval POST, approval row, project import, task, action item, owner/due-date field, issue, field authorization, lead selection, crew assignment, schedule/status write, customer commitment, customer report, field instruction, durable field record, production tracking row, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, service/auth/ingress change, workbook macro/writeback, or autonomous AI business-state mutation.

The section is a browser-local navigation rail only. If a returned item needs a task, action item, owner, due date, assignment, timing field, schedule/status write, customer commitment, customer report, field instruction, durable record, production tracking, export, backend route, storage key, button, or write authority, the detail lenses and guardrail copy keep that as a later bounded packet question.

## Dual-Lane Use

Read-only sidecar Lorentz was used for proof-shaping only. It recommended a link-only jump rail, link targets, no-state copy, negative storage regex, and no-write boundary. VS Code Codex narrowed the admitted implementation to four direct detail-lens jumps, then retained PM lane implementation, validation, and final integration authority.

## Validation

- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck`
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"`
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build`
- Packet JSON parse check
- PM Lane 199 guardrail `rg`
- Null-byte check on PM status docs
- `git diff --check`

## Next Recommended PM Move

PM Lane 200 should add a browser-local `Field Start Bring-Back Lens Open-Context Cue` so Jason can see which detail lens currently has populated context without creating tasks, owners, dates, assignments, reports, exports, storage keys, routes, buttons, or write paths.
