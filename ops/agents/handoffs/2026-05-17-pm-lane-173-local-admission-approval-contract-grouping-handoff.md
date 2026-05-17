# PM Lane 173 - Local Admission and Approval Contract Grouping Handoff

## Summary

PM Lane 173 groups the existing Admission and Approval Contract panel on `/pm-review/import-intake`.

The panel already had three top-level contract cards. This lane keeps those same three cards, admission plan values, target-row and no-go readback, approval contract values, storage table and mutation route values, approval-status readback, the status-readback no-write sentence, export behavior, no-storage posture, and no-write boundary, but groups them into Admission Shape Context, Approval Contract Context, and Approval Status Context so Jason can scan admission shape, approval contract, and current approval status separately.

## Implementation

- Added `Admission Shape Context`, `Approval Contract Context`, and `Approval Status Context` groups inside the existing Admission and Approval Contract disclosure.
- Preserved the existing three top-level contract cards:
  - Admission Shape.
  - Approval Contract.
  - Approval Status Readback.
- Preserved admission plan values, target rows, no-go count, approval contract id, record type, authority values, storage table, future route, approval-status classification, storage/read route values, disclosure behavior, export behavior, and no-authority wording.
- Added focused smoke assertions for contract group headings, group counts of 1, 1, and 1, unchanged total contract card count of 3, unchanged fixture admission/approval/status text, the status-readback no-write sentence, disclosure behavior, and no admission/approval-contract localStorage state.

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

Read-only sidecar Bacon reviewed the Lane 173 shape while VS Code Codex implemented the PM lane and retained PM lane implementation authority plus final integration authority.

The sidecar confirmed the existing three-card panel was already safe and recommended preserving the card text, disclosure behavior, no-storage posture, and zero-mutation boundary. It also recommended hardening the focused smoke around the status-readback no-write sentence. VS Code Codex used that review as a guardrail and limited the implementation to a presentation-only grouping layer with no new state, controls, routes, exports, storage, or write authority.

## Validation

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
Get-Content -LiteralPath "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-17-pm-lane-173-local-admission-approval-contract-grouping.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 173|Admission and approval contract groups|Admission Shape Context contract group|Approval Contract Context contract group|Approval Status Context contract group|mutationRequests\)\.toHaveLength\(0\)" PROJECT_STATUS.md docs/operations ops/agents apps/operations-web
git diff --check
```

Result:

- operations-web typecheck passed.
- operations-web build passed.
- focused Playwright PM import-intake smoke passed.
- packet JSON parsed.
- PM Lane 173 guardrail scan returned expected code, docs, packet, handoff, admission/approval contract group, and zero-mutation references.
- `git diff --check` passed with only expected CRLF warnings on touched and unrelated markdown files.

## Next Recommended PM Move

Continue local PM usability work before opening any write path. The next safe tranche is grouping the next approval-prep detail surface, likely Local Review Checklist, while preserving its seven checklist items, checkbox behavior, candidate-scoped browser storage, clear behavior, export inclusion, no-storage disclosure posture, and no-write boundary. Browser approval submission, first approval-row creation, project import, field authorization, assignment, schedule/status, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked until separately admitted.
