# PM Lane 172 - Local Exception and Decision Detail Grouping Handoff

## Summary

PM Lane 172 groups the existing Exception Review and PM Decisions panel on `/pm-review/import-intake`.

The panel already had two top-level detail cards. This lane keeps those same two cards, warning rendering, decision rendering, warning severity/code pills, decision prompt and recommended-action text, fallback empty states, export behavior, no-storage posture, and no-write boundary, but groups them into Exception Signals and PM Decision Context so Jason can scan warning evidence separately from decision prompts.

## Implementation

- Added `Exception Signals` and `PM Decision Context` groups inside the existing Exception Review and PM Decisions disclosure.
- Preserved the existing two top-level detail cards:
  - Exception Review.
  - PM Decisions.
- Preserved warning severity pills, warning code pills, warning messages, decision id labels, prompt text, recommended action text, fallback empty states, disclosure behavior, export behavior, and no-authority wording.
- Added focused smoke assertions for exception/decision group headings, group counts of 1 and 1, unchanged top-level card count of 2, unchanged fixture warning and decision text, disclosure behavior, and no exception-review/pm-decision localStorage state.

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

Read-only sidecar Ampere reviewed the Lane 172 shape while VS Code Codex implemented the PM lane and retained PM lane implementation authority plus final integration authority.

The sidecar confirmed the same safe grouping shape: Exception Signals and PM Decision Context. It also confirmed the focused smoke assertions should prove group visibility, group counts of 1 and 1, unchanged top-level cards of 2, unchanged warning and decision text, no exception-review/pm-decision localStorage state, and existing zero-mutation proof.

## Validation

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
Get-Content -LiteralPath "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-17-pm-lane-172-local-exception-decision-detail-grouping.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 172|Exception and PM decision detail groups|Exception Signals detail group|PM Decision Context detail group|mutationRequests\)\.toHaveLength\(0\)" PROJECT_STATUS.md docs/operations ops/agents apps/operations-web
git diff --check
```

Result:

- operations-web typecheck passed.
- operations-web build passed.
- focused Playwright PM import-intake smoke passed.
- packet JSON parsed.
- PM Lane 172 guardrail scan returned expected code, docs, packet, handoff, exception/decision detail group, and zero-mutation references.
- `git diff --check` passed with only expected CRLF warnings on touched and unrelated markdown files.

## Next Recommended PM Move

Continue local PM usability work before opening any write path. The next safe tranche is grouping the next flat approval-prep detail panel, likely Admission and Approval Contract, while preserving its three-card shape, approval/admission/status rendering, export behavior, no-storage posture, and no-write boundary. Browser approval submission, first approval-row creation, project import, field authorization, assignment, schedule/status, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked until separately admitted.
