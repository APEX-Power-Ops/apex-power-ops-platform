# PM Lane 165 - Local Handoff Guide Grouping Handoff

## Summary

PM Lane 165 groups the existing Local PM Intake Handoff Guide on `/pm-review/import-intake`.

The handoff guide had five flat advisory links. This lane keeps those same five links, labels, hrefs, and dynamic descriptions, but groups them into Review Context, Field And Executor Context, and Approval Boundary Context so the next context lane is easier to choose during day-to-day PM review.

## Implementation

- Added `Review Context`, `Field And Executor Context`, and `Approval Boundary Context` groups inside the existing handoff guide.
- Preserved the existing five advisory links:
  - Jason local review.
  - Field conversation prep.
  - Bounded executor context.
  - Hosted readiness context.
  - Future approval-persistence packet boundary.
- Preserved existing hrefs:
  - `#import-exception-register`.
  - `#field-prep`.
  - `#executor-closeout`.
  - `#approval-readiness`.
  - `#approval-readiness`.
- Added focused smoke assertions for handoff guide group headings, group counts of 1, 2, and 2, unchanged total link count of 5, unchanged hrefs, disclosure behavior, and no handoff-guide localStorage state.

## Guardrails Preserved

- No hosted service access.
- No Supabase, Render, Vercel, or Olares action.
- No SQL or schema migration.
- No approval POST or approval-row creation.
- No project import mutation.
- No field authorization, assignment, schedule/status write, durable field record, production tracking, customer report, completion evidence, billing, payroll, invoice, accounting, or external finance-system write.
- No workbook macro or writeback.
- No new export action, handler, filename, payload version, localStorage key, backend route, service/auth/ingress change, or autonomous AI business-state mutation.

## Dual-Lane Use

Read-only sidecar Aquinas scouted the next safe PM ergonomics slice while VS Code Codex retained PM lane implementation authority and final integration authority.

The sidecar recommended Local Handoff Guide Grouping because PM Lane 163 grouped Output Actions and PM Lane 164 mirrored that grouping in the Output Selector, leaving the adjacent Handoff Guide as the next flat advisory panel. The accepted recommendation was to group the existing links only.

## Validation

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
Get-Content -LiteralPath "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-17-pm-lane-165-local-handoff-guide-grouping.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 165|Local PM intake handoff guide groups|Review Context handoff guide group|Field And Executor Context handoff guide group|Approval Boundary Context handoff guide group|mutationRequests\)\.toHaveLength\(0\)" PROJECT_STATUS.md docs/operations ops/agents apps/operations-web
git diff --check
```

Result:

- operations-web typecheck passed.
- operations-web build passed.
- focused Playwright PM import-intake smoke passed.
- packet JSON parsed.
- PM Lane 165 guardrail scan returned expected code, docs, packet, handoff, handoff-guide group, and zero-mutation references.
- `git diff --check` passed with only expected CRLF warnings on touched and unrelated markdown files.

## Next Recommended PM Move

Continue local PM usability work before opening any write path. A safe next tranche is grouping another adjacent helper panel such as the Workflow Map or Open Items lens, or authoring a packet-only first field/assignment admission proof. Browser approval submission, first approval-row creation, project import, field authorization, assignment, schedule/status, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked until separately admitted.
