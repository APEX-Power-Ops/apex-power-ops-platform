# PM Lane 179 - Local Field Questions Draft Grouping Handoff

## Summary

PM Lane 179 groups the existing Local Field Questions Draft panel on `/pm-review/import-intake`.

The panel already held six browser-local field-question draft inputs: drawing/source questions, site access and safety questions, crew and equipment questions, material and staging questions, customer constraint questions, and PM follow-up notes. This lane keeps those same labels, textarea values, update handlers, candidate-scoped browser storage, export inclusion, clear behavior, disclosure behavior, no-disclosure-storage posture, and no-field-authorization/no-write boundary, but groups the panel into Source and Site Questions, Crew Material and Staging Questions, and Customer Constraints and PM Follow-up so Jason can scan field questions in the order a PM/lead/site conversation naturally flows.

## Implementation

- Added `Source and Site Questions`, `Crew Material and Staging Questions`, and `Customer Constraints and PM Follow-up` groups inside the existing Local Field Questions Draft controls.
- Preserved the existing details/summary behavior, six textarea controls, local browser storage key, clear button, derived field-prep behavior, and export inclusion.
- Preserved browser-local field-question wording and the no-field-authorization/no-write boundary.
- Added focused smoke assertions for field-question group visibility, three group sections, 2/2/2 input distribution, collapse/reopen behavior, no field-questions disclosure/localStorage state, preserved draft fill behavior, clear button behavior, and existing zero-mutation guard.

## Guardrails Preserved

- No hosted service access.
- No Supabase, Render, Vercel, or Olares product action.
- No SQL or schema migration.
- No approval POST or approval-row creation.
- No project import mutation.
- No field authorization, assignment, schedule/status write, durable field record, production tracking, customer report, completion evidence, billing, payroll, invoice, accounting, or external finance-system write.
- No workbook macro or writeback.
- No new export action, handler, filename, payload version, localStorage key, backend route, service/auth/ingress change, or autonomous AI business-state mutation.

## Dual-Lane Use

Read-only sidecar Gauss reviewed the Lane 179 shape while VS Code Codex implemented the PM lane and retained PM lane implementation authority plus final integration authority.

The sidecar recommended the same three wrapper-only groups used here and called out the required preservation points: no state changes, no storage changes, no handler changes, no export changes, no hosted calls, no field authorization, no mutation authority, and the next safe packet as PM Lane 180 - Local Field Prep Queue Grouping. That recommendation was accepted.

## Validation

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
Get-Content -LiteralPath "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-17-pm-lane-179-local-field-questions-draft-grouping.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 179|Local field questions draft groups|Source and Site Questions field questions group|Crew Material and Staging Questions field questions group|Customer Constraints and PM Follow-up field questions group|mutationRequests\)\.toHaveLength\(0\)" PROJECT_STATUS.md docs/operations ops/agents apps/operations-web
git diff --check
```

Result:

- operations-web typecheck passed.
- focused Playwright PM import-intake smoke passed.
- operations-web build passed.
- packet JSON parsed.
- PM Lane 179 guardrail scan returned expected code, docs, packet, handoff, field-question group, and zero-mutation references.
- `git diff --check` passed with only expected CRLF warnings on touched and unrelated markdown files.

## Next Recommended PM Move

Continue local PM usability work before opening any write path. The next safe tranche is grouping the next field-prep/detail surface, likely Local Field Prep Queue, while preserving its derived queue cards, no-storage behavior, export references, disclosure behavior, and no field-authorization/write boundary. Browser approval submission, first approval-row creation, project import, field authorization, assignment, schedule/status, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked until separately admitted.
