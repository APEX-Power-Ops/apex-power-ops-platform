# PM Lane 166 - Local Workflow Map Grouping Handoff

## Summary

PM Lane 166 groups the existing Local PM Intake Workflow Map on `/pm-review/import-intake`.

The workflow map had seven flat advisory links. This lane keeps those same seven links, labels, hrefs, dynamic descriptions, and status pills, but groups them into Intake Review Path, Field And Executor Path, and Future Authority Boundaries so Jason can separate current review flow from future blocked authority while scanning the page.

## Implementation

- Added `Intake Review Path`, `Field And Executor Path`, and `Future Authority Boundaries` groups inside the existing workflow map.
- Preserved the existing seven advisory links:
  - Source intake.
  - Exception review.
  - Decision draft.
  - Field prep.
  - Executor closeout.
  - Approval persistence boundary.
  - Project import boundary.
- Preserved existing hrefs:
  - `#project-packet`.
  - `#import-exception-register`.
  - `#pm-operating-queue`.
  - `#field-prep`.
  - `#executor-closeout`.
  - `#approval-readiness`.
  - `#guardrails`.
- Added focused smoke assertions for workflow-map group headings, group counts of 3, 2, and 2, unchanged total link count of 7, unchanged hrefs, disclosure behavior, and no workflow-map localStorage state.

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

Read-only sidecar McClintock scouted the next safe PM ergonomics slice while VS Code Codex retained PM lane implementation authority and final integration authority.

The sidecar independently recommended Local Workflow Map Grouping with the same three groups after seeing the local Lane 166 edits already underway. That confirmed the tranche was aligned with the dual-lane model without pulling VS Code Codex away from PM lane execution.

## Validation

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
Get-Content -LiteralPath "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-17-pm-lane-166-local-workflow-map-grouping.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 166|Local PM intake workflow map groups|Intake Review Path workflow map group|Field And Executor Path workflow map group|Future Authority Boundaries workflow map group|mutationRequests\)\.toHaveLength\(0\)" PROJECT_STATUS.md docs/operations ops/agents apps/operations-web
git diff --check
```

Result:

- operations-web typecheck passed.
- operations-web build passed.
- focused Playwright PM import-intake smoke passed.
- packet JSON parsed.
- PM Lane 166 guardrail scan returned expected code, docs, packet, handoff, workflow-map group, and zero-mutation references.
- `git diff --check` passed with only expected CRLF warnings on touched and unrelated markdown files.

## Next Recommended PM Move

Continue local PM usability work before opening any write path. A safe next tranche is grouping the adjacent Open Items lens, or authoring a packet-only first field/assignment admission proof. Browser approval submission, first approval-row creation, project import, field authorization, assignment, schedule/status, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked until separately admitted.
