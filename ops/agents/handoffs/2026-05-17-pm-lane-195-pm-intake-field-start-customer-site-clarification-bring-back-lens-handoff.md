# PM Lane 195 - PM Intake Field Start Customer/Site Clarification Bring-Back Lens Handoff

## Summary

PM Lane 195 is executed as the local PM Intake Field Start Customer/Site Clarification Bring-Back Lens tranche. The `/pm-review/import-intake` workbench now adds a browser-local `Local Field Start Customer/Site Clarification Bring-Back Lens` directly after the source review lens inside the customer/site questions panel.

The lens helps Jason classify returned field-start customer/site conversation items before any later bounded packet. It stays read-only and covers access/shutdown answers, escort/contact path, safety/LOTO clarification, constraint answer boundary, and customer/site promise stop-line context.

## Implementation

Changed `apps/operations-web/app/pm-review/import-intake/page.tsx` to derive a five-item customer/site clarification lens from the existing candidate, field questions draft, and field observation scratchpad. The new section links only to already-existing local review anchors: `#field-prep` and `#guardrails`.

Changed `apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts` to prove desktop presence, 390x844 mobile visibility, initial and populated lens copy, five links, zero buttons, no customer/site clarification lens localStorage key, no implied-authority link/control text, and zero mutation calls.

Updated PM status and operating-plan docs so the repo-visible PM lane context is local-current through PM Lane 195.

## Guardrails

This lane adds no meeting-note capture, export button, handler, route, backend seam, payload version, localStorage schema, hosted call, approval POST, approval row, project import, task, action item, owner/due-date field, issue, field authorization, lead/crew assignment, schedule/status write, customer commitment, customer report, durable field record, production tracking, completion evidence, billing/payroll/invoice/accounting output, Supabase/Render/Vercel/Olares action, SQL/schema migration, service/auth/ingress change, workbook macro/writeback, or autonomous AI business-state mutation.

The section is a browser-local clarification lens only. If a returned customer/site answer needs accountability, timing, customer-facing language, field direction, report, schedule/status update, durable record, or write authority, the UI copy tells the PM to stop and author a later bounded packet.

## Dual-Lane Use

Read-only sidecar Hume was used for proof-shaping only. It recommended the sibling placement, five-item lens shape, link targets, storage negative, and copy-risk boundary. VS Code Codex retained PM lane implementation, validation, and final integration authority.

## Validation

- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck`
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"`
- `corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build`
- Packet JSON parse check
- PM Lane 195 guardrail `rg`
- Null-byte check on PM status docs
- `git diff --check`

## Next Recommended PM Move

PM Lane 196 should continue the same low-risk bring-back sequence with a browser-local `Field Start Lead/Resource Clarification Bring-Back Lens`. It should help classify returned lead/resource details without adding tasks, action items, assignments, owner/due-date fields, schedule/status writes, or production tracking.
