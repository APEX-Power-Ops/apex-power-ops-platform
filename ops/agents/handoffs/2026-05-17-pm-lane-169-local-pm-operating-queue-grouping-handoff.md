# PM Lane 169 - Local PM Operating Queue Grouping Handoff

## Summary

PM Lane 169 groups the existing Local PM Operating Queue on `/pm-review/import-intake`.

The operating queue had seven flat browser-local cards. This lane keeps those same seven cards, labels, dynamic detail text, status pills, complete/next/blocked summary count, export references, and no-write boundary, but groups them into Local Review Moves, Approval Submission Boundary, and Future Import Boundary so Jason can scan today's local review moves separately from later approval and import boundaries.

## Implementation

- Added `Local Review Moves`, `Approval Submission Boundary`, and `Future Import Boundary` groups inside the existing Local PM Operating Queue.
- Preserved the existing seven queue cards:
  - Review source and exceptions.
  - Prepare local decision draft.
  - Export review artifacts.
  - Hosted approval gate complete.
  - Browser approval submission packet.
  - Approval row creation.
  - Project import packet.
- Preserved existing queue card copy, dynamic status logic, summary count, disclosure behavior, export references, and no-authority wording.
- Added focused smoke assertions for operating-queue group headings, group counts of 3, 3, and 1, unchanged total card count of 7, unchanged card labels, disclosure behavior, and no operating-queue localStorage state.

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

Read-only sidecar Anscombe scouted the next safe PM ergonomics tranche while VS Code Codex implemented Lane 169 and retained PM lane implementation authority plus final integration authority.

The sidecar recommends PM Lane 170 as Local Import Exception Register Grouping, with Source Review Signals, PM Decision Context, and Admission Boundary groups. That follow-on remains parked until Lane 169 is published and reviewed as the current PM lane increment.

## Validation

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
Get-Content -LiteralPath "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-17-pm-lane-169-local-pm-operating-queue-grouping.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 169|Local PM operating queue groups|Local Review Moves operating queue group|Approval Submission Boundary operating queue group|Future Import Boundary operating queue group|mutationRequests\)\.toHaveLength\(0\)" PROJECT_STATUS.md docs/operations ops/agents apps/operations-web
git diff --check
```

Result:

- operations-web typecheck passed.
- operations-web build passed.
- focused Playwright PM import-intake smoke passed.
- packet JSON parsed.
- PM Lane 169 guardrail scan returned expected code, docs, packet, handoff, operating-queue group, and zero-mutation references.
- `git diff --check` passed with only expected CRLF warnings on touched and unrelated markdown files.

## Next Recommended PM Move

Continue local PM usability work before opening any write path. The sidecar-recommended next tranche is Local Import Exception Register Grouping: Source Review Signals, PM Decision Context, and Admission Boundary. Browser approval submission, first approval-row creation, project import, field authorization, assignment, schedule/status, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked until separately admitted.
