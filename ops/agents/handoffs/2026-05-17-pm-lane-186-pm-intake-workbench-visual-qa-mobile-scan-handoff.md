# PM Lane 186 - PM Intake Workbench Visual QA And Mobile Scan Handoff

## Summary

PM Lane 186 adds repeatable visual and mobile-readability proof for `/pm-review/import-intake`.

The prior PM grouping lanes made the workbench easier to scan, but they also increased the number of grouped cards and long review labels on the same page. This lane keeps the PM intake workbench read-only and adds viewport proof inside the existing mocked browser smoke. The proof covers desktop, laptop, tablet, mobile, and small-mobile widths.

The first mobile run caught real horizontal overflow from long grouped workbench content. The accepted fix is layout-only: existing grid, card, notes-card, status-row, status-pill, and PM link-row primitives now shrink and wrap safely on narrow viewports.

## Implementation

- Added `expectWorkbenchViewportScan` to the PM import-intake Playwright smoke.
- Covered viewports: `1440x900`, `1366x768`, `1024x768`, `390x844`, and `360x800`.
- Asserted no horizontal `document` or `body` overflow.
- Asserted visible tracked workbench card/grid/status/link-row elements stay inside the viewport.
- Asserted the quick-jump, start-here, output-selector, command-center, workflow-map, field-prep, approval-readiness, guardrails, and guardrail-group surfaces are present and visible.
- Asserted Approval Persistence Readiness and Current PM guardrail groups keep two columns on desktop/tablet and collapse to one column on mobile.
- Added layout containment in `globals.css` for existing grids/cards/status primitives and mobile row wrapping.

## Guardrails Preserved

- No hosted service access.
- No Supabase, Render, Vercel, or Olares product action.
- No SQL or schema migration.
- No browser approval button, approval POST wiring, approval submission, or approval-row creation.
- No project import mutation.
- No field authorization, assignment, schedule/status write, durable field record, production tracking, customer report, completion evidence, billing, payroll, invoice, accounting, or external finance-system write.
- No workbook macro or writeback.
- No new export action, handler, filename, payload version, localStorage key, backend route, service/auth/ingress change, or autonomous AI business-state mutation.

## Dual-Lane Use

Read-only sidecar Lagrange reviewed the Lane 186 visual QA criteria while VS Code Codex implemented the PM lane and retained PM lane implementation authority plus final integration authority.

The sidecar recommended desktop `1440x900`, laptop `1366x768`, tablet `1024x768`, mobile `390x844`, and small-mobile `360x800` checks, with optional harsher mobile follow-up later. The sidecar also recommended the exact low-risk fix family used here if the viewport proof showed overflow: min-width containment, status-row wrapping, and long-token wrapping.

## Validation

```powershell
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web typecheck
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform/apps/operations-web" exec playwright test "browser-shell.pm-import-intake.smoke.spec.ts"
corepack pnpm --dir "C:/APEX Platform/apex-power-ops-platform" --filter @apex/operations-web build
Get-Content -LiteralPath "C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-17-pm-lane-186-pm-intake-workbench-visual-qa-mobile-scan.json" | ConvertFrom-Json | Select-Object -ExpandProperty packet_id
rg -n "PM Lane 186|expectWorkbenchViewportScan|1440x900|360x800|documentHorizontalOverflow|grid/card/status-row|mobile overflow|mutationRequests\)\.toHaveLength\(0\)" PROJECT_STATUS.md docs/operations ops/agents apps/operations-web
git diff --check
```

Result:

- PASS - operations-web typecheck passed.
- PASS - operations-web build passed after CSS containment.
- PASS - focused Playwright pm import-intake smoke passed with desktop `1440x900`, laptop `1366x768`, tablet `1024x768`, mobile `390x844`, and small-mobile `360x800` viewport checks.
- PASS - packet JSON parsed as `2026-05-17-pm-lane-186`.
- PASS - PM Lane 186 guardrail `rg` found the expected status, docs, packet, handoff, visual scan, viewport, overflow, and zero-mutation evidence.
- PASS - `git diff --check` passed with only expected CRLF warnings on touched and unrelated markdown files.

## Next Recommended PM Move

Run a mobile-first PM intake field-launch use-path tranche. The workbench now has baseline viewport safety; the next safe tranche is to prove the actual field-start path Jason would use on a phone: quick jump, daily script, field prep, field questions, observations, guardrails, and export-ready local artifacts. Browser approval submission, first approval-row creation, project import, field authorization, assignment, schedule/status, durable field records, production tracking, customer reporting, billing, payroll, invoice, accounting, and external finance-system writes remain blocked until separately admitted.
