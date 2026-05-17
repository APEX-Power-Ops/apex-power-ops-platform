# PM Lane 170 - Local Import Exception Register Grouping Handoff

## Summary

PM Lane 170 groups the existing Local Import Exception Decision Register on `/pm-review/import-intake`.

The exception register had six flat browser-local cards. This lane keeps those same six cards, labels, dynamic detail/evidence text, status pills, covered/open/blocked summary count, export content, and no-write boundary, but groups them into Source Review Signals, PM Decision Context, and Admission Boundary so Jason can scan source evidence separately from PM decision context and blocked admission boundaries.

## Implementation

- Added `Source Review Signals`, `PM Decision Context`, and `Admission Boundary` groups inside the existing Local Import Exception Decision Register.
- Preserved the existing six register cards:
  - Source freshness evidence.
  - Candidate warning signals.
  - Human decision prompts.
  - Local decision draft evidence.
  - Admission no-go checks.
  - Future write boundary.
- Preserved existing register card copy, dynamic status logic, evidence text, summary count, disclosure behavior, export content, and no-authority wording.
- Added focused smoke assertions for exception-register group headings, group counts of 2, 2, and 2, unchanged total card count of 6, unchanged card labels, disclosure behavior, and no import-exception-register localStorage state.

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

Read-only sidecar Curie scouted the next safe PM ergonomics tranche while VS Code Codex implemented Lane 170 and retained PM lane implementation authority plus final integration authority.

The sidecar recommends PM Lane 171 as Local Workflow Gates Grouping, with Source Review Gates, Approval Readiness Gates, and Future Import Boundary groups. That follow-on remains parked until Lane 170 is published and reviewed as the current PM lane increment.

## Validation

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
Get-Content -LiteralPath "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-17-pm-lane-170-local-import-exception-register-grouping.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 170|Local import exception decision register groups|Source Review Signals import exception group|PM Decision Context import exception group|Admission Boundary import exception group|mutationRequests\)\.toHaveLength\(0\)" PROJECT_STATUS.md docs/operations ops/agents apps/operations-web
git diff --check
```

Result:

- operations-web typecheck passed.
- operations-web build passed.
- focused Playwright PM import-intake smoke passed.
- packet JSON parsed.
- PM Lane 170 guardrail scan returned expected code, docs, packet, handoff, exception-register group, and zero-mutation references.
- `git diff --check` passed with only expected CRLF warnings on touched and unrelated markdown files.

## Next Recommended PM Move

Continue local PM usability work before opening any write path. The sidecar-recommended next tranche is Local Workflow Gates Grouping: Source Review Gates, Approval Readiness Gates, and Future Import Boundary. Browser approval submission, first approval-row creation, project import, field authorization, assignment, schedule/status, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked until separately admitted.
